"""One-command demo for a reviewer. Safe: throwaway database, file drafts only, no Gmail, no network.

    python tools/demo.py [--out demo-output] [--open]

Walks through the brief's four commands and its edge cases on the sample notes/, with a fixed
"today" so the output is always the same, then leaves two files to look at:
    <out>/report.html          the item report
    <out>/drafts/*.html        the follow-up email as it would look
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from actiontrack import cli  # noqa: E402

TODAY = "2026-10-01"


def step(title: str, argv: list[str], db: str, shown: str, limit: int = 14) -> int:
    print(f"\n=== {title}\n$ actiontrack {shown}")
    import io
    out, err = io.StringIO(), io.StringIO()
    code = cli.main(["--db", db, "--today", TODAY, "--no-report", *argv], out=out, err=err)
    lines = (out.getvalue() + err.getvalue()).rstrip().splitlines()
    for line in lines[:limit]:
        print("  " + line)
    if len(lines) > limit:
        print(f"  ... ({len(lines) - limit} more lines)")
    print(f"  [exit {code}]")
    return code


def run(out_dir: str) -> int:
    os.makedirs(out_dir, exist_ok=True)
    drafts = os.path.join(out_dir, "drafts")
    notes = os.path.join(ROOT, "notes")
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "demo.db")
        step("1. ingest: malformed notes are skipped and reported, never a crash", ["ingest", notes], db, "ingest notes/")
        step("2. list: overdue items for one person (today = " + TODAY + ")",
             ["list", "--owner", "Sam Okafor", "--status", "overdue"], db, 'list --owner "Sam Okafor" --status overdue')
        step("3. list: a first name shared by two people is flagged, never guessed",
             ["list", "--owner", "Rahul"], db, "list --owner Rahul")
        step("4. done: mark an item done",
             ["done", "6"], db, "done 6")
        step("5. followup: ONE draft per person, saved as files. Nothing is ever sent",
             ["followup", "Sam Okafor", "--to", "person@example.invalid", "--sink", "file", "--drafts-dir", drafts],
             db, 'followup "Sam Okafor" --to person@example.invalid')
        code = step("6. report: the same items as a searchable HTML page",
                    ["report", "--out", os.path.join(out_dir, "report.html")], db, "report")
    print(f"\nOpen these in a browser:\n  {os.path.join(out_dir, 'report.html')}")
    if os.path.isdir(drafts):
        for name in sorted(os.listdir(drafts)):
            if name.endswith(".html"):
                print(f"  {os.path.join(drafts, name)}   (the follow-up email)")
    return code


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", default=os.path.join(ROOT, "demo-output"))
    p.add_argument("--open", action="store_true", help="open the report in the browser")
    args = p.parse_args(argv)
    code = run(args.out)
    if args.open:
        webbrowser.open("file:///" + os.path.join(args.out, "report.html").replace(os.sep, "/"))
    return code


if __name__ == "__main__":
    sys.exit(main())
