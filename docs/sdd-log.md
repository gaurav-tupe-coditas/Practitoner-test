# SDD log

Running log of the spec-driven (sdd-epic) run for **actiontrack**. One row per stage event. Newest last. Committed with the rest of the SDD files.

**Time box:** 30 minutes. Clock started 2026-11-24 16:14 (project folder created); target finish 16:44.

## Decisions on how we work (2026-11-24)

| # | Decision | By |
|---|---|---|
| W-1 | Collapsed structure: one module (`actiontrack`), no `contracts.md`, no phases file | User |
| W-2 | Stack: Python + SQLite (stdlib argparse / sqlite3, pytest) | User |
| W-3 | `baseReq.md` is truncated: infer gaps from `notes/`, mark each as an Assumption, user vetoes at the requirements gate | User |
| W-4 | Commits: Claude commits each confirmed stage itself, no per-commit ask. Format below. Env/secret files never committed (global rule) | User |
| W-5 | Full gates: every SDD file waits for user confirmation before the next starts | sdd-epic skill |
| W-6 | No organisation, employer, client or personal names/emails in any file, log or commit. Git identity for this repo is generic. This run also checks for such leaks | User |

**Commit format:** `docs(sdd): <stage> - <one-line summary>` for SDD files, `feat|test|fix(actiontrack): <summary>` for code. Body lists the decisions made. Trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Stage log

| Time | Stage | File | Event |
|---|---|---|---|
| 16:19 | Orient | - | No SDD structure, not a git repo. `docs/baseReq.md` is truncated. Notes folder inspected (34 files). Repo initialised. |
| 16:22 | Requirements | `docs/requirements.md` | v0.9 draft written, sent for confirmation |
| 16:25 | Privacy | repo + git history | User rule W-6: no org or personal details anywhere. Audit found a leak in the log and the git author identity; fixed, commit rewritten, generic identity set |
| 16:28 | Requirements | `docs/requirements.md` | Rev 2: A-6 on-or-after, A-9 meeting date + 7 days, A-4 Everyone = every attendee, A-10 kept. User confirmed final, frozen at v1.0 |
| 16:31 | Specification | `docs/specification.md`, `docs/adr/ADR-0001`, `ADR-0002` | Spec written and confirmed. OQ-1 decided: option A (port + file sink + claude CLI sink). User chose short module files to fit the time box |
| 16:33 | Module brief | `modules/actiontrack/{spec_task,analysis,adr}.md` | T1 dedup = normalised text (ADR-ACTIONTRACK-001); T2 next/end-of phrases = following calendar week (ADR-ACTIONTRACK-002). Confirmed |
| 16:36 | Module spec | `modules/actiontrack/spec.md` | Rules R1-R19, due table, CLI shapes, exit codes. Confirmed final |
| 16:39 | Module tests | `modules/actiontrack/tests.md` | T-01..T-37 cover R1-R19 and all ACs; S-5 added. Confirmed final |
| 16:42 | Plan | `modules/actiontrack/plan.md`, `tasks.md` | 7 phases, test-first, trunk on main. Approved; build started |
| 16:47 | Build | `actiontrack/`, `tests/` | Phases 1-7 built test-first; `python -m pytest` = 61 passed. Sample ingest: 31 read, 4 skipped with reasons, 6 ambiguous owners flagged. Live Gmail not tested (connector unauthorised); claude sink covered by fake-runner test |
| 16:55 | Change | `requirements.md` v1.1, `spec.md` R12, `tests.md` T-38/T-39, ADR-ACTIONTRACK-003 | User-requested: `for` and trailing tomorrow/today/EOD read as due phrases; ingest report de-duplicated; tasks.md filename fixed |
| 17:00 | Change | `requirements.md` v1.2 (FR-10), `spec.md` R20, `tests.md` T-40..T-44, ADR-ACTIONTRACK-004 | User-requested: one-file launcher with a menu; README quick-start |
| 17:05 | Fix | `service.followup`, `cli.py` | Found by the launcher tests: follow-up for a name not in the data said "matches several people: ." Now `AT-E001 no one named ... found`, exit 1 |
