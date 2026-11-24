# actiontrack

Reads markdown meeting notes, tracks the action items in a local SQLite file, and drafts follow-up emails. It never sends email.

Python 3.13, standard library only (pytest for tests).

## Commands

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
