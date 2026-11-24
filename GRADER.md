# Grader guide: actiontrack

One page: what was built, why it was built this way, and where the full evidence is.

## What it is
A CLI (`ingest`, `list`, `done`, `followup`, plus `report`) that reads markdown meeting notes, tracks action items in SQLite and drafts follow-up emails for human review. Python 3.13, standard library at runtime, pytest for tests. It **never sends email**: it only creates drafts.

## Check it in 2 minutes
```
python -m pytest                     # all tests green
python run.py                        # menu; option 7 opens the HTML report
python tools/build_summary.py        # rebuilds docs/summary.html from real runs
```
`docs/summary.html` is the fastest overview: test result, a run over `notes/` (31 files read, 4 malformed skipped and reported), test-plan coverage, the spec-driven trail, brief-vs-delivered and open items.

## Why it was done this way
| Choice | Why | Evidence |
|---|---|---|
| Spec first, one confirmed gate per file (requirements, specification, module analysis, spec, tests, plan, code) | The task was a spec-driven (SDD/EPIC) build; every change has to trace to a requirement | `docs/sdd-log.md` (every stage and change), git history |
| The brief is truncated, so gaps were inferred from `notes/` and each is marked **Assumption** | Never invent requirements; let the user veto | `docs/requirements.md` sections 6-8, `docs/baseReq.md` |
| Follow-up drafts only, no send code path | The brief says "it never sends" | AC-8.4, test T-28 scans the package for send calls, ADR-ACTIONTRACK-008 |
| Draft goes through a port with a file sink and a `claude` CLI sink | A Python CLI cannot call an MCP connector itself | `docs/adr/ADR-0002`, `actiontrack/sinks.py`; tool name verified against the live connector (spec S-3) |
| Ambiguous owners (two Priyas, two Rahuls) flagged, never guessed | Brief edge case | AC-3.3, tests T-11..T-13 |
| Malformed notes skipped and reported, never a crash | Brief edge case | AC-9.x, tests T-03, T-07 |
| Duplicates merged on normalised text; "today" injectable | Brief edge case; reproducible tests and demos | ADR-ACTIONTRACK-001, AC-6.3 |
| HTML report and summary built by stdlib, escaped, offline | Easier to read results; notes are untrusted input | AC-11.x, ADR-ACTIONTRACK-005/006, tests T-45..T-50 |
| Follow-up email is HTML with a plain-text fallback, no CSS backgrounds | Recipients found the plain email ugly; the live Gmail check showed Gmail strips backgrounds | AC-8.7, ADR-ACTIONTRACK-007, test T-51 |
| No organisation or personal names or emails anywhere in the repo; conversation exports are masked | Hard rule in `CLAUDE.md` | `tools/export_conversations.py`, `tests/test_export.py` |

## Where the full documents are
- `docs/baseReq.md` original brief (truncated) -> `docs/requirements.md` (v1.5, FR-1..FR-11) -> `docs/specification.md`
- `modules/actiontrack/`: `spec_task.md`, `analysis.md`, `adr.md` (ADR-001..008), `spec.md` (R1..R23), `tests.md` (T-01..T-51), `plan.md`, `tasks.md`
- `docs/sdd-log.md` the run log, one row per stage and change
- `docs/summary.html` generated summary; `docs/conversations/` masked transcripts of both working sessions
- `CLAUDE.md` project rules (workflow, commit format, privacy, sending switch)

## Things to know (stated plainly)
- **One send happened.** During a manual check the assistant, on the user's explicit instruction, sent two test emails through the Gmail connector, outside the app. It is logged in `docs/sdd-log.md` (18:10). Afterwards sending was switched off by default (`ACTIONTRACK_ALLOW_SEND`, ADR-ACTIONTRACK-008); the later improved emails were created as **drafts only** for a human to review and send.
- Assumptions S-5 and S-6 (which due date wins on duplicates; what `list --status open` shows) were not explicitly confirmed by the user.
- Email appearance was checked in the Gmail draft data, not in every mail client.
- Recipient addresses used in the live check are deliberately recorded nowhere in the repo.
