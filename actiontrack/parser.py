"""Pure note parser: bytes -> Note | Malformed (spec R4-R9, R12)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from .dates import parse_header_date, resolve_due, split_due


@dataclass
class RawItem:
    owner_raw: str | None
    task: str
    due: date | None
    done: bool


@dataclass
class Note:
    file: str
    date: date
    attendees: list[str]
    items: list[RawItem] = field(default_factory=list)


@dataclass
class Malformed:
    file: str
    reason: str  # empty | not-text | no-header | bad-date


_CHECKBOX = re.compile(r"^\s*[-*+]\s+\[([ xX])\]\s+(.*\S)\s*$")
_ACTION = re.compile(r"^\s*ACTION:\s*(.*\S)\s*$")
_OWNER_TO = re.compile(r"^(?P<owner>.+?)\s+to\s+(?P<task>.+)$", re.IGNORECASE)
_HANDLE = re.compile(r"^(@\w+):?\s+(?P<task>.+)$")
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_MAX_OWNER_WORDS = 5


def _split_names(value: str) -> list[str]:
    value = value.strip().strip("[]")
    return [n.strip() for n in value.split(",") if n.strip()]


def _parse_header(text: str) -> tuple[dict, str] | None:
    """Return ({'date': str|None, 'attendees': [..]}, body) or None if no header."""
    lines = text.splitlines()
    first = next((i for i, l in enumerate(lines) if l.strip()), None)
    if first is None:
        return None
    if lines[first].strip() == "---":
        end = next((i for i in range(first + 1, len(lines)) if lines[i].strip() == "---"), None)
        if end is None:
            return None
        meta: dict = {"date": None, "attendees": []}
        for l in lines[first + 1:end]:
            key, _, val = l.partition(":")
            key = key.strip().lower()
            if key == "date":
                meta["date"] = val.strip()
            elif key == "attendees":
                meta["attendees"] = _split_names(val)
        return meta, "\n".join(lines[end + 1:])
    if not re.match(r"^#\s*Meeting:", lines[first], re.IGNORECASE):
        return None
    meta = {"date": None, "attendees": []}
    for l in lines[first + 1:]:
        m = re.match(r"^\s*Date:\s*(.+?)\s*$", l, re.IGNORECASE)
        if m and meta["date"] is None:
            meta["date"] = m.group(1)
        m = re.match(r"^\s*Attendees:\s*(.+?)\s*$", l, re.IGNORECASE)
        if m and not meta["attendees"]:
            meta["attendees"] = _split_names(m.group(1))
    return meta, "\n".join(lines[first + 1:])


def _strip_non_items(body: str) -> list[str]:
    body = _COMMENT.sub("", body)
    out, in_fence = [], False
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or s.startswith(">"):
            continue
        out.append(line)
    return out


def _item_from_text(text: str, done: bool, meeting: date) -> RawItem:
    text = text.strip()
    h = _HANDLE.match(text)
    owner, task = None, text
    if h:
        owner, task = h.group(1), h.group("task")
    else:
        m = _OWNER_TO.match(text)
        if m and len(m.group("owner").split()) <= _MAX_OWNER_WORDS:
            owner, task = m.group("owner"), m.group("task")
    task, due = split_due(task, meeting)
    return RawItem(owner, task, due, done)


def _table_items(lines: list[str], meeting: date) -> tuple[list[RawItem], set[int]]:
    items, used = [], set()
    i = 0
    while i < len(lines):
        cells = [c.strip().lower() for c in lines[i].strip().strip("|").split("|")]
        if lines[i].strip().startswith("|") and {"owner", "action", "due"} <= set(cells):
            idx = {name: cells.index(name) for name in ("owner", "action", "due")}
            used.add(i)
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                used.add(j)
                row = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                if row and not re.fullmatch(r"[-: ]+", "".join(row)) and len(row) > max(idx.values()):
                    due = resolve_due(row[idx["due"]], meeting)
                    items.append(RawItem(row[idx["owner"]] or None, row[idx["action"]], due, False))
                j += 1
            i = j
        else:
            i += 1
    return items, used


def parse_note(file: str, data: bytes) -> Note | Malformed:
    if not data.strip():
        return Malformed(file, "empty")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return Malformed(file, "not-text")
    if "\x00" in text:
        return Malformed(file, "not-text")
    header = _parse_header(text)
    if header is None:
        return Malformed(file, "no-header")
    meta, body = header
    meeting = parse_header_date(meta["date"]) if meta["date"] else None
    if meeting is None:
        return Malformed(file, "bad-date")
    lines = _strip_non_items(body)
    items, table_rows = _table_items(lines, meeting)
    for i, line in enumerate(lines):
        if i in table_rows:
            continue
        m = _CHECKBOX.match(line)
        if m:
            items.append(_item_from_text(m.group(2), m.group(1) in "xX", meeting))
            continue
        m = _ACTION.match(line)
        if m:
            items.append(_item_from_text(m.group(1), False, meeting))
    return Note(file, meeting, meta["attendees"], items)
