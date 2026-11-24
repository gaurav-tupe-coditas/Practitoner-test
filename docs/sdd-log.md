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
| 17:20 | Change | `requirements.md` v1.3 (FR-11), `spec.md` R21, `tests.md` T-45..T-49, ADR-ACTIONTRACK-005 | User-requested: HTML report in the app, and a generated project summary in docs |
| 17:25 | Handoff | `modules/NEW-SESSION-PROMPTS.md` | Phase 9 started (`report.py` written, rest pending). Work saved for a new session so the Gmail connector can be checked live |
| 17:30 | Export | `.gitignore` | Raw conversation exports are git-ignored; only a sanitised `docs/conversation.md` may be committed (the raw transcript holds machine paths and account names) |
| 17:40 | Check | `actiontrack/sinks.py`, `spec.md` S-3, `tests/test_cli.py` | Live Gmail connector lists create-draft as `mcp__claude_ai_Gmail__create_draft`, same as `GMAIL_CREATE_DRAFT_TOOL`; no constant change. S-3 note updated, exact-argv test added. End-to-end draft still pending the user's test address |
| 17:50 | Build | `actiontrack/cli.py`, `run.py`, `tools/build_summary.py`, `tests/test_report.py`, `docs/summary.html` | Phase 9 done test-first: `report` command, menu option 7, summary builder from real runs. T-45..T-49 added; the summary's coverage check found T-15 untagged in tests, tag added |
| 18:00 | Check | `docs/baseReq.md`, `docs/requirements.md` | User re-pasted the brief: identical to the file in the repo (it is the full text they hold, cut mid-sentence). Nothing new to diff, no behaviour change, no version bump. Header corrected to v1.3. S-5, S-6 still await explicit user confirmation; live Gmail draft awaits the user's test address |
| 18:10 | Live check | `followup --sink claude`, `spec.md` S-3 | Two Gmail drafts created through the connector (exit 0), confirmed label DRAFT and none in Sent. Recipients supplied by the user at run time and deliberately not recorded in any file. Then, on the user's explicit instruction, those two drafts were sent once through the connector (outside the app, which stays draft-only) |
| 18:25 | Change | `requirements.md` v1.4 (AC-11.6), `spec.md` R22, `tests.md` T-50, ADR-ACTIONTRACK-006, `cli.py`, `run.py`, `tests/conftest.py` | User-requested: the HTML is created every time a command runs. Claude chose ingest, list, done (not followup). Tests now run in an isolated working directory so the repo is never written. 79 tests pass |
| 18:40 | Change | `requirements.md` v1.5 (AC-8.7), `spec.md` section 6 + R23, `tests.md` T-51, ADR-ACTIONTRACK-007, `draft.py`, `sinks.py` | User-requested: follow-up emails were ugly. Now an HTML email (cards, counts, overdue/open sections) with a tidy plain-text fallback; `claude` sink sends both to Gmail as a draft; file sink also writes an .html preview. 81 tests pass |
| 18:45 | Decision | `CLAUDE.md`, `.env.example`, ADR-ACTIONTRACK-008 | User: sending must stay off so the requirements are not contradicted. `ACTIONTRACK_ALLOW_SEND` master switch (default 0) for the assistant; the app has no send path. Beautified drafts were created for review and are left for the human to send from Gmail; the assistant did not send them |
| 19:00 | Change | `draft.py`, `tests/test_draft.py`, ADR-ACTIONTRACK-007 | Live Gmail data showed backgrounds are stripped (white text would vanish); email layout reworked to use only text colour and borders, test added. Two review drafts recreated; none sent by the assistant |
| 19:05 | Docs | `GRADER.md`, `docs/conversations/`, `tools/export_conversations.py` | Grader summary and masked transcripts of both sessions added. Exporter masks emails, names, home folders fully; its test caught a Windows-path leak, fixed |
