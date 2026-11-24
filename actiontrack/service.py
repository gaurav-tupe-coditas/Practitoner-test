"""Use-cases: ingest, list, done, followup (spec sections 2, 6, 7)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date

from .dates import effective_due
from .draft import Draft, build_draft
from .owners import AMBIGUOUS, RESOLVED, UNASSIGNED, resolve_owner
from .parser import Malformed, Note, parse_note
from .store import Item, Store

_ARTICLES = {"a", "an", "the"}


class NotFound(Exception):
    pass


class AmbiguousOwner(Exception):
    def __init__(self, name: str, candidates: list[str]):
        super().__init__(name)
        self.name, self.candidates = name, candidates


class InvalidFolder(Exception):
    pass


def task_key(task: str) -> str:
    """ADR-ACTIONTRACK-001: lower-case, no punctuation, no articles, collapsed spaces."""
    words = re.sub(r"[^\w\s]", " ", task.lower()).split()
    return " ".join(w for w in words if w not in _ARTICLES)


@dataclass
class Report:
    read: int = 0
    skipped: list[tuple[str, str]] = field(default_factory=list)
    added: int = 0
    updated: int = 0
    ambiguous: list[str] = field(default_factory=list)
    no_due: list[str] = field(default_factory=list)

    def lines(self) -> list[str]:
        out = [f"read {self.read} files"]
        out += [f"skipped {f}: {why}" for f, why in self.skipped]
        out += [f"added {self.added}", f"updated {self.updated}"]
        out += [f"ambiguous owner: {a}" for a in dict.fromkeys(self.ambiguous)]   # unique, in order
        out += [f"no/defaulted due: {n}" for n in dict.fromkeys(self.no_due)]
        return out


def ingest(store: Store, folder: str) -> Report:
    if not os.path.isdir(folder):
        raise InvalidFolder(folder)
    report = Report()
    notes: list[Note] = []
    for name in sorted(os.listdir(folder)):                       # pass 1: scan
        path = os.path.join(folder, name)
        if not name.lower().endswith(".md") or not os.path.isfile(path):
            continue
        try:
            with open(path, "rb") as fh:
                parsed = parse_note(name, fh.read())
        except OSError as exc:
            parsed = Malformed(name, f"unreadable ({exc.__class__.__name__})")
        if isinstance(parsed, Malformed):
            report.skipped.append((parsed.file, parsed.reason))
        else:
            report.read += 1
            notes.append(parsed)
    registry = {p for n in notes for p in n.attendees}
    notes.sort(key=lambda n: (n.date, n.file))
    with store.transaction():                                      # pass 2: resolve + store
        store.add_people(registry)
        registry |= set(store.people())
        for note in notes:
            for raw in note.items:
                for o in resolve_owner(raw.owner_raw, note.attendees, registry):
                    _upsert(store, report, note, raw, o)
    return report


def _upsert(store: Store, report: Report, note: Note, raw, owner) -> None:
    key = task_key(raw.task)
    label = f"{note.file}: {raw.task}"
    if owner.status == AMBIGUOUS:
        report.ambiguous.append(f"{note.file}: {owner.name} ({raw.task})")
    if raw.due is None:
        report.no_due.append(label)
    existing = store.find(owner.name, owner.status, key)
    if existing is None:
        item_id = store.insert(owner.name, owner.status, raw.task, key, raw.due, raw.due is None,
                               "done" if raw.done else "open", note.date if raw.done else None, note.date)
        store.add_source(item_id, note.file, note.date)
        report.added += 1
        return
    due, defaulted = existing.due, existing.due_defaulted
    if raw.due is not None and note.date >= existing.latest_meeting:   # S-5: latest stated due wins
        due, defaulted = raw.due, False
    status, done_at = existing.status, existing.done_at
    if raw.done and status == "open":                                   # any [x] closes; never reopen
        status, done_at = "done", note.date
    meeting = max(existing.latest_meeting, note.date)
    task = raw.task if note.date >= existing.latest_meeting else existing.task
    changed = store.add_source(existing.id, note.file, note.date)
    if (due, defaulted, status, done_at, meeting, task) != (
            existing.due, existing.due_defaulted, existing.status, existing.done_at, existing.latest_meeting, existing.task):
        store.update(existing.id, task, due, defaulted, status, done_at, meeting)
        changed = True
    if changed:
        report.updated += 1


# ---- list / done / followup ----

def effective(item: Item) -> date:
    return effective_due(item.due, item.latest_meeting)


def is_overdue(item: Item, today: date) -> bool:
    return item.status == "open" and effective(item) < today


def resolve_owner_arg(store: Store, name: str) -> tuple[str, str | None]:
    """Return ('unassigned'|'name', value). Raises AmbiguousOwner for a shared first name."""
    n = name.strip()
    if n.lower() == "unassigned":
        return UNASSIGNED, None
    known = store.people()
    full = [p for p in known if p.lower() == n.lower()]
    if full:
        return RESOLVED, full[0]
    if " " not in n:
        hits = store.people_by_first_name(n)
        if len(hits) > 1:
            raise AmbiguousOwner(n, hits)
        if len(hits) == 1:
            return RESOLVED, hits[0]
    return AMBIGUOUS, n.title()      # only ambiguous-status rows can match


def list_items(store: Store, today: date, owner: str | None = None, status: str | None = None,
               due_before: date | None = None) -> list[Item]:
    items = store.all_items()
    if owner:
        kind, value = resolve_owner_arg(store, owner)
        if kind == UNASSIGNED:
            items = [i for i in items if i.owner_status == UNASSIGNED]
        elif kind == RESOLVED:
            items = [i for i in items if i.owner == value]
        else:
            items = [i for i in items if i.owner_status == AMBIGUOUS and (i.owner or "").lower() == value.lower()]
    if status == "open":
        items = [i for i in items if i.status == "open"]
    elif status == "done":
        items = [i for i in items if i.status == "done"]
    elif status == "overdue":
        items = [i for i in items if is_overdue(i, today)]
    if due_before:
        items = [i for i in items if effective(i) < due_before]
    return sorted(items, key=lambda i: (effective(i), i.id))


def mark_done(store: Store, item_id: int, today: date) -> bool:
    """True if newly marked done, False if it already was. Raises NotFound."""
    item = store.get(item_id)
    if item is None:
        raise NotFound(item_id)
    if item.status == "done":
        return False
    store.mark_done(item_id, today)
    return True


def followup(store: Store, owner: str, to: str, today: date, sink) -> Draft | None:
    kind, value = resolve_owner_arg(store, owner)
    if kind == AMBIGUOUS:
        raise AmbiguousOwner(owner, store.people_by_first_name(owner.split()[0]))
    items = [i for i in list_items(store, today, owner=owner) if i.status == "open"]
    if not items:
        return None
    overdue = [i for i in items if is_overdue(i, today)]
    rest = [i for i in items if not is_overdue(i, today)]
    draft = build_draft(value or "unassigned", to, overdue, rest, today)
    sink.create_draft(draft)
    return draft
