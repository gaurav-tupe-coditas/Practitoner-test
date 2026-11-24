# Module brief: actiontrack

## Goal
Deliver the four CLI commands (`ingest`, `list`, `done`, `followup`) over the sample `notes/` folder, per `docs/requirements.md` v1.0 and `docs/specification.md` v1.0.

## Scope
**In:** everything in FR-1..FR-9 and NFR-1..NFR-7. **Out:** sending email, editing items, syncing, UI, non-`.md` notes.

## Sources
Requirements FR-1..9, AC-x.y, NFR-1..7. Specification sections 1-8. ADR-0001, ADR-0002.

## Provides / depends on
Provides the `python -m actiontrack` CLI and the `DraftSink` port. Depends on: Python 3.13 stdlib, pytest, and (optional, live only) the `claude` CLI with an authorised Gmail connector.

## `spec.md` must cover
- Enforceable rules per requirement, citing AC ids
- Exact grammar for item lines, header styles, due phrases, owner forms
- Table DDL, queries, transaction boundary (one per ingest)
- CLI argument shapes, output formats, exit codes
- Error codes and constants
- Dedup key definition and due-phrase resolution table
- Contract requests (none expected: single module), assumptions

## Open decisions
See `analysis.md` topics T1 and T2 (answered in `adr.md`).

## Definition of done
`python -m pytest` exits 0; every AC has a test; ingest of `notes/` runs clean with a report; `followup` writes a draft file and never sends; no org or personal details in any file or commit.
