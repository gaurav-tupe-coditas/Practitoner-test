# actiontrack

Reads markdown meeting notes, tracks the action items in a local SQLite file, and drafts follow-up emails. It never sends email.

Python 3.13, standard library only (pytest for tests).

## Quick start

Run one file. It checks Python, then shows a menu that walks you through everything.

- **Windows:** double-click `run.bat`, or run `python run.py`
- **macOS / Linux:** run `./run.sh`, or `python3 run.py`

Menu: 1) load notes, 2) show items, 3) mark an item done, 4) draft a follow-up email, 5) self-test, 6) help. On first launch it offers to load the `notes/` folder for you. Follow-ups are saved as draft files in `drafts/` and are never sent.

Nothing needs installing to use the app (only the optional self-test needs `pip install pytest`).

## Commands (for power users)

Everything the menu does is also available as a command. Run them with `python run.py <command>` or `python -m actiontrack <command>`.

```
python -m actiontrack ingest notes/                      # parse every .md note, print a report
python -m actiontrack list --status overdue              # filters: --owner NAME, --status open|done|overdue, --due-before DATE
python -m actiontrack done 12                            # mark item 12 done
python -m actiontrack followup "Sam Okafor" --to sam@example.com    # draft one email per owner
```

Global options (before the command): `--db PATH` (default `actiontrack.db`), `--today YYYY-MM-DD` (or env `ACTIONTRACK_TODAY`) so overdue results are reproducible.

`followup` writes a draft file to `drafts/` by default. `--sink claude` asks the `claude` CLI to create a Gmail draft through the Gmail connector (create-draft only; needs the connector authorised).

Exit codes: 0 ok, 1 not found or invalid input, 2 ambiguous owner or bad usage, 3 draft sink failure.

## Tests

```
python -m pytest
```

## Spec-driven docs

`docs/requirements.md` -> `docs/specification.md` -> `modules/actiontrack/` (spec_task, analysis, adr, spec, tests, plan, tasks). The run log is `docs/sdd-log.md`.
