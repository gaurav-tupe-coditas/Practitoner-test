#!/usr/bin/env python3
"""actiontrack launcher: run this one file.

    python run.py                 opens a menu that walks you through everything
    python run.py <command> ...   same as: python -m actiontrack <command> ...

Needs only Python 3.10+ (tested on 3.13). Nothing to install for the app itself.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DB = os.path.join(HERE, "actiontrack.db")
NOTES = os.path.join(HERE, "notes")
DRAFTS = os.path.join(HERE, "drafts")
REPORT = os.path.join(HERE, "report.html")

MENU = """
actiontrack - track action items from meeting notes
---------------------------------------------------
  1) Load notes            read the .md meeting notes into the tracker
  2) Show items            filter by person, status or due date
  3) Mark an item done     by its ID number
  4) Draft a follow-up     one email per person (saved as a draft, never sent)
  5) Run self-test         check the app works on this computer
  6) Help                  what each option does
  7) Open report           pretty HTML view of all items, opens in your browser
  0) Quit
"""

HELP = """
Typical order: 1 (load notes) -> 2 (show items) -> 3 (mark done) -> 4 (draft a follow-up).

  Load notes      Reads every .md file in a folder. Notes that cannot be read are skipped and
                  listed with a reason. Running it again is safe: nothing is duplicated and
                  items you marked done stay done.
  Show items      Leave a question blank to skip that filter. Status: open, done or overdue.
                  Overdue = not done and past its due date (no due date counts as meeting + 7 days).
  Mark done       Use the ID number from the list.
  Report          Writes report.html (searchable table of every item) and opens it in your browser.
  Follow-up       Creates ONE draft for a person covering their open and overdue items.
                  Drafts are saved in the 'drafts' folder. Nothing is ever sent.
                  If two people share a first name, use the full name.

Power users: python run.py list --status overdue    (any CLI command works after run.py)
"""


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or default


def call(args: list[str]) -> int:
    from actiontrack import cli
    code = cli.main(["--db", DB, *args])
    print()
    return code


def do_ingest() -> None:
    folder = ask("Notes folder", NOTES)
    call(["ingest", folder])


def do_list() -> None:
    args = ["list"]
    owner = ask("Person (blank = everyone, 'unassigned' = no owner)")
    status = ask("Status: open / done / overdue (blank = all)")
    before = ask("Due before date YYYY-MM-DD (blank = any)")
    if owner:
        args += ["--owner", owner]
    if status:
        if status not in ("open", "done", "overdue"):
            print("Status must be open, done or overdue.\n")
            return
        args += ["--status", status]
    if before:
        args += ["--due-before", before]
    call(args)


def do_done() -> None:
    raw = ask("Item ID number")
    if not raw.isdigit():
        print("Please type the ID number shown in the list (for example 12).\n")
        return
    call(["done", raw])


def do_followup() -> None:
    owner = ask("Person to draft a follow-up for (full name if two people share a first name)")
    if not owner:
        print("A name is required.\n")
        return
    to = ask("Their email address")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", to):
        print("That does not look like an email address.\n")
        return
    sink = ask("Where to save the draft: file / claude (claude = Gmail draft, needs the Gmail connector)", "file")
    if sink not in ("file", "claude"):
        print("Choose file or claude.\n")
        return
    code = call(["followup", owner, "--to", to, "--sink", sink, "--drafts-dir", DRAFTS])
    if code == 0 and sink == "file":
        print(f"Drafts are saved in: {DRAFTS}  (nothing was sent)\n")


def do_selftest() -> None:
    try:
        import pytest  # noqa: F401
    except ImportError:
        print("The self-test needs pytest. Install it with:  python -m pip install pytest\n")
        return
    subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=HERE)
    print()


def do_report() -> None:
    if call(["report", "--out", REPORT]) != 0:
        return
    try:
        webbrowser.open(pathlib.Path(REPORT).resolve().as_uri())
    except webbrowser.Error:
        pass
    print(f"Report saved at: {REPORT}  (open it in a browser if it did not appear)\n")


ACTIONS = {"1": do_ingest, "2": do_list, "3": do_done, "4": do_followup, "5": do_selftest,
           "6": lambda: print(HELP), "7": do_report}


def menu() -> int:
    try:
        if not os.path.exists(DB) and os.path.isdir(NOTES):
            print("First launch: no data yet, but a 'notes' folder was found.")
            if ask("Load the sample notes now? (y/n)", "y").lower().startswith("y"):
                call(["ingest", NOTES])
        while True:
            print(MENU)
            choice = ask("Choose 0-7")
            if choice == "0":
                return 0
            action = ACTIONS.get(choice)
            if action is None:
                print("Please type a number from 0 to 7.\n")
                continue
            action()
    except (EOFError, KeyboardInterrupt):
        print("\nBye.")
        return 0


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 10):
        print(f"actiontrack needs Python 3.10 or newer (you have {sys.version.split()[0]}).")
        return 1
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        from actiontrack import cli
        return cli.main(argv)
    return menu()


if __name__ == "__main__":
    sys.exit(main())
