# New-session prompts

Open this project folder in a NEW Claude Code session (so the Gmail connector is loaded), then paste the prompt below.

## Prompt: live Gmail check, then finish the HTML report

```
This is the actiontrack project (spec-driven build, already working: 71 tests pass).
Read CLAUDE.md first (it has hard rules), then docs/sdd-log.md, modules/actiontrack/tasks.md and README.md.

Rules that always apply:
- No organisation, employer, client or personal names/emails in any file, log or commit. Git identity is already set locally to a generic one; do not change it, and scan staged diffs and `git log` authors before every commit.
- Commits are allowed without asking (format in CLAUDE.md). Never stage env files, keys or *.db.
- followup creates drafts only. Never send an email.

Task 1: live Gmail check.
a) List the Gmail connector tools available in this session and tell me the exact name of the create-draft tool.
b) Compare it with GMAIL_CREATE_DRAFT_TOOL in actiontrack/sinks.py (spec assumption S-3). If it differs, fix the constant, add a unit test for the argv, update the S-3 note in modules/actiontrack/spec.md, and log it in docs/sdd-log.md.
c) Creating a draft writes to my real mailbox, so ask me for the recipient address first (I will type it; use my own test address, do not guess one). Then run:
   python run.py --today 2026-10-01 ingest notes
   python run.py --today 2026-10-01 followup "Sam Okafor" --to <MY_TEST_ADDRESS> --sink claude
   Confirm a DRAFT exists in Gmail (not sent). If it fails, show me the error; the CLI should exit 3 and print the full draft.
d) Commit the result.

Task 2: finish Phase 9 (HTML report), already specified in docs/requirements.md FR-11, modules/actiontrack/spec.md R21, tests.md T-45..T-49, ADR-ACTIONTRACK-005.
Done already: actiontrack/report.py (pure HTML builders, escaping).
To do, test-first:
- `actiontrack report [--out FILE]` command in actiontrack/cli.py (writes report.html, uses the same --today as list).
- Menu option 7 in run.py: generate the report and open it in the browser (webbrowser, faked in tests); update the "0-6" texts to "0-7".
- tools/build_summary.py: builds docs/summary.html from REAL runs: the pytest result (junit xml), a run of the app over notes/ (per-file read/skip result, item counts, ambiguous owners, deduplicated items, items table), test-plan coverage (T-ids in tests.md vs tests/*.py), the SDD trail (git log + docs/sdd-log.md timeline + ADR list), the brief-vs-delivered checklist and open items. Reuse actiontrack/report.py. Self-contained HTML, no external links, light and dark colours.
- tests T-45..T-49 in tests/test_report.py (include an escaping test with a <script> task), README section, tick Phase 9 in tasks.md, log entry, commit.
Run python -m pytest at the end and show me the result.

Task 3 (needs me): I will paste the full, untruncated docs/baseReq.md text and confirm assumptions S-5 and S-6. When I do, diff the behaviour against it, list any difference, and fix them through the normal gates (requirements version bump, spec, tests, code).
```
