# ADR-0001: Layered single module with pure helpers

- **Status:** Accepted
- **Date:** 2026-11-24

## Context
Small CLI, 30-minute time box, requirements FR-1..FR-9. The riskiest logic (note parsing, due dates, owner resolution) must be testable with no database and no clock.

## Decision
One Python package, layers `cli -> service -> store`. `parser`, `dates`, `owners`, `draft` are pure functions. Only `store.py` imports `sqlite3`; only `sinks.py` starts subprocesses. "Today" is injected from `cli.py`.

## Consequences
- Pure helpers are unit-testable and give deterministic output (NFR-3, NFR-5).
- No `contracts.md` or phases file needed (single module).
- Replacing SQLite or the draft sink touches one file each.
