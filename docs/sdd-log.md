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
| 16:34 | Specification | `docs/specification.md`, `docs/adr/ADR-0001`, `ADR-0002` | Spec written and confirmed. OQ-1 decided: option A (port + file sink + claude CLI sink). User chose short module files to fit the time box |
