# actiontrack module spec

**Version:** v1.0 FINAL (2026-11-24). Cites `docs/requirements.md` v1.0, `docs/specification.md` v1.0 (table DDL and flows live there), ADR-0001, ADR-0002, ADR-ACTIONTRACK-001/002.

## 1. Rules (each testable; ids are used by tests.md)

| Rule | Statement | Cites |
|---|---|---|
| R1 | Only `*.md` files directly in the folder are read, in name order. Other files and sub-folders are ignored. | AC-1.1 |
| R2 | Ingest never raises for a bad note: it returns a skip with a reason. Folder missing or not a directory: exit 1. | AC-1.3, AC-9.2, NFR-5 |
| R3 | Re-ingest of the same folder changes no row; a done item stays done. | AC-1.4, AC-5.2 |
| R4 | Header: `# Meeting: <title>` + `Date:` + optional `Attendees:`, or YAML frontmatter `---` with `date`, optional `attendees: [..]`. Anything else: malformed `no-header`. | AC-2.1 |
| R5 | Date formats: `YYYY-MM-DD`, `D Month YYYY`, `Weekday, D Month YYYY`. Else malformed `bad-date`. Empty file `empty`, undecodable `not-text`. | AC-2.5, AC-9.1 |
| R6 | Blockquote lines, fenced code blocks and HTML comments are removed before item scanning. | AC-2.4 |
| R7 | Items: `[-*+] [ xX] text` at any indent; `ACTION: text`; table rows whose header has Owner, Action, Due. `x`/`X` = done. | AC-2.2, AC-2.3 |
| R8 | Item text `<owner> to <task>`; without ` to `: unassigned, whole text as task, reported. | S-1 |
| R9 | Owner forms: `Priya`, `Priya N.`, `@anita`, `A & B` (one item each), `A (with B)` (owner A). | AC-3.1, AC-3.6 |
| R10 | Owner resolved against attendees (initial narrows); several matches: `ambiguous`; no attendees: registry, unique match or ambiguous. | AC-3.2..3.4 |
| R11 | `Everyone`/`Team`/`All`: one item per attendee (unassigned if no attendees). `Someone`/`TBD`: unassigned. | AC-3.5 |
| R12 | Due phrase read only after `by`, `due`, `before`, `until`, `from`, `for`, or a dash, or as a trailing `tomorrow`/`today`/`EOD` at end of line (v1.1); table Due cell is read whole. | AC-4.4 |
| R13 | Due resolution: see section 2. No phrase or unresolvable: `due` NULL, `due_defaulted=1`, effective due = meeting + 7 days. | AC-4.1..4.5 |
| R14 | Dedup key per ADR-ACTIONTRACK-001. Duplicates: add source, latest meeting's due wins, any `[x]` makes it done, never reopen. | AC-5.1..5.3 |
| R15 | Overdue = open and effective due < today. Done never overdue. | AC-6.2 |
| R16 | `list` filters AND together; `--owner` first name with 2+ known people: print candidates to stderr, exit 2. Order: effective due, then id. | AC-6.1, 6.4, 6.5 |
| R17 | `done <id>`: unknown exit 1; already done exit 0; ids stable. | AC-7.1..7.3 |
| R18 | `followup`: overdue first, then open; none: message, no draft; ambiguous owner exit 2; `--to` required. | AC-8.1..8.3, 8.5 |
| R19 | `DraftSink` has only `create_draft`; no send path exists in the code base. Sink failure prints the draft, exit 3. | AC-8.4, 8.6 |

| R20 | `run.py` (v1.2): no arguments -> version check (3.10+) then menu; with arguments -> same as `python -m actiontrack`. Menu data lives next to the launcher (`actiontrack.db`, `drafts/`, `notes/`), so it works from any folder. Offers to load `notes/` when no data file exists. EOF or Ctrl+C exits 0. Menu calls `cli.main` in-process; the only subprocess is the optional self-test (`pytest`). | AC-10.1..10.6 |

| R21 | `report.py` (v1.3): pure functions that return an HTML string; every note-derived value goes through `html.escape`; no external fonts, scripts or links; light and dark colours via `prefers-color-scheme`. CLI `report` writes only the `--out` file. `tools/build_summary.py` reuses `report.py` and writes `docs/summary.html`. | AC-11.1..11.5 |
| R22 | CLI global options `--report FILE` (default `report.html`) and `--no-report`. After a successful `ingest`, `list` or `done` the CLI writes the full report (all items, same `today`) and prints `report updated: <file>`. `followup` and failed commands do not. A write failure prints `AT-W001 could not update report: ...` to stderr and keeps the exit code. The launcher passes `--report` pointing at its own folder. | AC-11.6 |

## 2. Due-phrase resolution (base = meeting date `M`)

| Phrase | Result |
|---|---|
| ISO `2026-09-08` | that date |
| `10 Sep`, `Oct 3rd`, `2 Oct`, `15 October`, `Wed 16 Sep` | day + month, year of `M` (roll to next year if > 6 months before `M`) |
| `tomorrow`, `by tomorrow`, `EOD tomorrow` | `M` + 1 |
| `EOD`, `today` | `M` |
| `Mon`..`Sun`, full names | first such weekday on or after `M` (A-6) |
| `next <weekday>` | that weekday in the following Mon-Sun week (ADR-002) |
| `end of next week` | Friday of the following week |
| `end of week` / `end of the week` | Friday of `M`'s week (on or after `M`) |
| `end of month` | last day of `M`'s month |
| `mid-<month>`, `next month`, anything else | unresolved (R13 default) |

A weekday word is a date only inside a due phrase (R12), so "Friday demo slot" in prose is ignored.

## 3. CLI shapes and exit codes

```
actiontrack [--db PATH] [--today YYYY-MM-DD] ingest <folder>
actiontrack [--db PATH] [--today YYYY-MM-DD] list [--owner NAME] [--status open|done|overdue] [--due-before YYYY-MM-DD]
actiontrack [--db PATH] [--today YYYY-MM-DD] done <id>
actiontrack [--db PATH] [--today YYYY-MM-DD] followup <owner> --to EMAIL [--sink file|claude] [--drafts-dir DIR]
```
`--db` default `./actiontrack.db`; `--today` default env `ACTIONTRACK_TODAY`, else system date. Default sink `file`.
Exit codes: 0 ok, 1 not found / invalid input, 2 ambiguous owner or usage, 3 draft sink failure.

`list` row: `ID  STATUS  OWNER  TASK  DUE  SOURCE`, a `(default)` suffix on defaulted dues, `overdue` shown as status when applicable.

Ingest report lines: `read N files`, `skipped <file>: <reason>`, `added N`, `updated N`, `ambiguous owner: <file>: <name>`, `no/defaulted due: <file>: <task>`.

## 4. Queries and transactions

Store methods: `upsert_item(...)`, `add_source`, `get_item(id)`, `mark_done(id, today)`, `query(owner, status, due_before, today)`, `people()`, `known_people_by_first_name(first)`. One transaction wraps a whole ingest (spec section 2); `done` is its own transaction.

## 5. Constants

- Statuses: `open`, `done`. Owner statuses: `resolved`, `ambiguous`, `unassigned`.
- Skip reasons: `empty`, `not-text`, `no-header`, `bad-date`.
- Error prefixes: `AT-E001` not found, `AT-E002` ambiguous owner, `AT-E003` invalid folder, `AT-E004` draft sink failure, `AT-E005` usage.
- Group owners: `everyone`, `team`, `all` (expand); `someone`, `tbd` (unassigned).

## 6. Followup email format

Subject: `Action items for <owner>: <n> overdue, <m> open`. Body: greeting with owner's first name, an "Overdue" list, an "Open" list (each `- <task> (due <date>) from <meeting date> <source file>`), closing line. Plain text, no personal data beyond names in the notes.

## 7. Non-functional

NFR-1..7 apply as written. `ClaudeGmailDraftSink` runs `claude` with a fixed argv list, no shell, only the Gmail create-draft tool allowed.

## 8. Contract requests / open questions / assumptions

- Contract requests: none (single module).
- **Assumption S-3:** the `claude` CLI flag set for allowing a single tool is checked at implementation time; if it differs, only `sinks.py` changes. **Checked 2026-11-24 against the live Gmail connector:** the create-draft tool is `mcp__claude_ai_Gmail__create_draft`, identical to `GMAIL_CREATE_DRAFT_TOOL`; no code change needed. **End-to-end run 2026-11-24:** `followup --sink claude` created Gmail drafts (label DRAFT, none in Sent), exit 0. Recipients are deliberately not recorded anywhere in the repo.
- **Assumption S-4:** `list` truncates nothing; long tasks wrap is not handled (plain columns).
- **Assumption S-5:** AC-5.3 "latest meeting's due wins" means the latest meeting that states a due date; a repeat with no due date does not erase an earlier one (see T-17).
- **Assumption S-6:** `list --status open` shows every not-done item (overdue ones included, shown with status `overdue`); `--status overdue` narrows to the overdue ones. A task's due phrase is also read after `on` only when it is a full ISO date.
