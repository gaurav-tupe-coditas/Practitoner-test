"""argparse front end: printing and exit codes only (spec section 3)."""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date

from . import service
from .sinks import ClaudeGmailDraftSink, FileDraftSink, SinkError
from .store import Store

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _iso(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date: {value}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="actiontrack")
    p.add_argument("--db", default="actiontrack.db")
    p.add_argument("--today", type=_iso, default=None)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ingest").add_argument("folder")
    ls = sub.add_parser("list")
    ls.add_argument("--owner")
    ls.add_argument("--status", choices=["open", "done", "overdue"])
    ls.add_argument("--due-before", type=_iso)
    sub.add_parser("done").add_argument("id", type=int)
    fu = sub.add_parser("followup")
    fu.add_argument("owner")
    fu.add_argument("--to", required=True)
    fu.add_argument("--sink", choices=["file", "claude"], default="file")
    fu.add_argument("--drafts-dir", default="drafts")
    return p


def _today(args) -> date:
    if args.today:
        return args.today
    env = os.environ.get("ACTIONTRACK_TODAY")
    return date.fromisoformat(env) if env else date.today()


def _print_table(items, today, out) -> None:
    rows = [("ID", "STATUS", "OWNER", "TASK", "DUE", "SOURCE")]
    for i in items:
        status = "overdue" if service.is_overdue(i, today) else i.status
        due = service.effective(i).isoformat() + (" (default)" if i.due is None else "")
        owner = i.owner or "(unassigned)"
        if i.owner_status == "ambiguous":
            owner += " (ambiguous)"
        src = i.sources[0] + (f" +{len(i.sources) - 1}" if len(i.sources) > 1 else "") if i.sources else "-"
        rows.append((str(i.id), status, owner, i.task, due, src))
    widths = [max(len(r[c]) for r in rows) for c in range(6)]
    for r in rows:
        print("  ".join(v.ljust(w) for v, w in zip(r, widths)).rstrip(), file=out)


def main(argv=None, out=None, err=None, sink_factory=None) -> int:
    out, err = out or sys.stdout, err or sys.stderr
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0) if exc.code != 0 else 0
    try:
        return _run(args, out, err, sink_factory)
    except Exception as exc:  # NFR-5: never a traceback
        print(f"AT-E005 unexpected error: {exc.__class__.__name__}: {exc}", file=err)
        return 1


def _run(args, out, err, sink_factory) -> int:
    today = _today(args)
    if args.cmd == "ingest" and not os.path.isdir(args.folder):
        print(f"AT-E003 not a folder: {args.folder}", file=err)
        return 1
    store = Store(args.db)
    try:
        if args.cmd == "ingest":
            for line in service.ingest(store, args.folder).lines():
                print(line, file=out)
            return 0
        if args.cmd == "list":
            try:
                items = service.list_items(store, today, args.owner, args.status, args.due_before)
            except service.AmbiguousOwner as exc:
                print(f"AT-E002 '{exc.name}' matches several people: {', '.join(exc.candidates)}. Use a full name.", file=err)
                return 2
            if not items:
                print("no items", file=out)
            else:
                _print_table(items, today, out)
            return 0
        if args.cmd == "done":
            try:
                newly = service.mark_done(store, args.id, today)
            except service.NotFound:
                print(f"AT-E001 no item with id {args.id}", file=err)
                return 1
            print(f"item {args.id} marked done" if newly else f"item {args.id} was already done", file=out)
            return 0
        return _followup(args, store, today, out, err, sink_factory)
    finally:
        store.close()


def _followup(args, store, today, out, err, sink_factory) -> int:
    if not _EMAIL.match(args.to):
        print("AT-E005 --to must be an email address", file=err)
        return 2
    sink = sink_factory(args) if sink_factory else (
        ClaudeGmailDraftSink() if args.sink == "claude" else FileDraftSink(args.drafts_dir))

    class Capture:
        draft = None

        def create_draft(self, draft):
            Capture.draft = draft
            sink.create_draft(draft)

    try:
        draft = service.followup(store, args.owner, args.to, today, Capture())
    except service.AmbiguousOwner as exc:
        print(f"AT-E002 '{exc.name}' matches several people: {', '.join(exc.candidates)}. Use a full name.", file=err)
        return 2
    except SinkError as exc:
        print(f"AT-E004 could not create the draft: {exc}", file=err)
        if Capture.draft:
            print(f"Subject: {Capture.draft.subject}\n\n{Capture.draft.body}", file=out)
        return 3
    if draft is None:
        print(f"nothing open for {args.owner}; no draft created", file=out)
        return 0
    print(f"draft created for {draft.owner}: {draft.subject}", file=out)
    return 0
