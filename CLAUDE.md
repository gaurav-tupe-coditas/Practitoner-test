# actiontrack

CLI that reads markdown meeting notes, tracks action items in SQLite, and drafts follow-up emails (Gmail draft via MCP, never sent). Built spec-first with the `sdd-epic` workflow as a 30-minute evaluation.

## Stack and commands
- Python 3.13, standard library at runtime (argparse, sqlite3, datetime). pytest for tests.
- Verify: `python -m pytest` (must exit 0 before anything is called done).
- Run: `python -m actiontrack <ingest|list|done|followup> ...`

## Workflow rules
- Spec first. Order: requirements -> specification -> module analysis -> spec -> tests -> plan/tasks -> code. The user confirms each file before the next starts.
- Single module: `modules/actiontrack/`. No `contracts.md`, no phases file.
- Every decision goes in `modules/actiontrack/adr.md` and a row in `docs/sdd-log.md`.
- Assumptions are marked **Assumption** in the doc. Never invent requirements.
- `docs/requirements.md` freezes at v1.0; later changes are new versions.

## Commits
- Claude commits each confirmed stage itself (user authorised 2026-11-24).
- SDD files: `docs(sdd): <stage> - <summary>`. Code: `feat|test|fix(actiontrack): <summary>`.
- Trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Before each commit run `git diff --cached --name-only`. Never stage `.env*`, keys, `*.db`, or real email addresses/tokens.

## No org or personal details (hard rule)
- No organisation, employer, client or personal names, emails or paths may appear in any file, log, ADR, test or commit message. This run is also a leak check.
- Git identity for this repo is local and generic (`git config --local user.name/user.email`); never rely on the global identity.
- Before every commit: `git diff --cached` scan for names/emails, and check `git log --format='%an %ae'`.

## Sending master switch (decided 2026-11-24)
- Env `ACTIONTRACK_ALLOW_SEND` (default `0`/unset = OFF). The requirements say the tool never sends, so the app has no send path (AC-8.4, tested by T-28) and no switch can add one.
- Claude (the assistant) creates drafts only. It does not send email through the Gmail connector unless the switch is `1` in the environment. The human reviews and sends drafts by hand (requirements, actors table). Drafts are always allowed.
- `.env.example` holds the placeholder; real env files are never committed.

## Business rules (see requirements.md)
- `followup` only creates drafts. No send path may exist.
- Ambiguous owners (two Priyas, two Rahuls) are flagged, never guessed.
- Malformed notes are skipped and reported, never a crash.
- "Today" is injectable (`--today` / `ACTIONTRACK_TODAY`) so tests and demos are deterministic.

## File map
- `docs/baseReq.md` original brief (truncated). `docs/requirements.md` what/why. `docs/specification.md` system how. `docs/sdd-log.md` run log.
- `notes/` sample input (34 files, several deliberately malformed).
