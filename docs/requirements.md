# actiontrack: Requirements

**Version:** v1.1 (2026-11-24). v1.0 was frozen the same day; v1.1 is a user-requested change to AC-4.4 only.
**Date:** 2026-11-24
**Source:** `docs/baseReq.md` (truncated; gaps inferred from `notes/` and marked **Assumption**)

## 1. Problem

Team meeting notes pile up as markdown files. Action items get lost and follow-up emails are written late or not at all. `actiontrack` is a small CLI that reads the notes, tracks the action items, and drafts follow-up emails for human review.

## 2. Actors

| Actor | Role |
|---|---|
| Team member (CLI user) | Runs the four commands. Reviews and sends drafts by hand. |
| Gmail MCP connector | Receives the draft. Never sends. |

## 3. Scope

**MVP (this build):** `ingest`, `list`, `done`, `followup`, a local SQLite store, an ingest report.
**Out of scope:** sending email, editing items beyond marking done, syncing with a task tracker, web UI, multi-user or shared store, recurring or scheduled runs, `.txt` or other non-markdown notes.

## 4. Functional requirements

### FR-1 Ingest
`actiontrack ingest <folder>` parses every `.md` file in the folder and stores the action items found.
- AC-1.1 Only files ending `.md` are read. Other files (e.g. `.txt`) are ignored silently. Sub-folders are not scanned. (**Assumption A-1**)
- AC-1.2 Ingest prints a report: files read, files skipped (with reason), items added, items updated, items with unresolved owner or due date.
- AC-1.3 Ingest exits 0 even when files are skipped. A bad folder path is a usage error (non-zero).
- AC-1.4 Ingest is idempotent: running it twice on the same folder changes nothing the second time, and never reverts an item the user marked done.

### FR-2 Note parsing
Each note has a date, attendees and free-form discussion. Action items are checkbox lines.
- AC-2.1 Two header styles are accepted: a markdown header (`# Meeting: ...`, `Date: ...`, `Attendees: a, b`) and YAML frontmatter (`title`, `date`, `attendees: [a, b]`). (inferred from notes)
- AC-2.2 Checkbox bullets `-`, `*`, `+` with `[ ]` (open) and `[x]` or `[X]` (done) are items. Nested checkboxes are items too.
- AC-2.3 A line starting `ACTION:` is an item. A table with columns Owner / Action / Due yields one item per row. (inferred from `2026-09-30-q4-offsite.md`) (**Assumption A-2**)
- AC-2.4 Lines inside blockquotes (`>`), fenced code blocks and HTML comments are never items (`2026-09-21-incident-review.md`, `2026-10-09-security-review.md`).
- AC-2.5 Dates are accepted as `2026-09-14`, `9 September 2026`, `Monday, 14 September 2026`. Anything else (e.g. `sometime last week`) makes the note malformed (see FR-9).
- AC-2.6 Each item keeps: owner, task text, due date, status, source file, source meeting date.

### FR-3 Owner resolution
- AC-3.1 An owner is the name before "to" in `<Name> to <task>`. Accepted forms: first name (`Priya`), name with initial (`Priya N.`), `@handle` (`@anita`).
- AC-3.2 A first name is resolved to a full name using the meeting's attendee list. If exactly one attendee matches, the owner is that full name. An initial narrows it (`Priya N.` -> Priya Nair).
- AC-3.3 If more than one attendee matches (two Priyas, two Rahuls) and no initial helps, the owner is stored as **ambiguous** (first name kept, flagged) and listed in the ingest report. It is never guessed.
- AC-3.4 If the note has no attendee list, the first name is resolved against all known full names from other notes only when it matches exactly one person; otherwise ambiguous. (**Assumption A-3**)
- AC-3.5 `Everyone` creates one item per attendee of that meeting (each deduplicated per FR-5). If the note has no attendee list, it is stored unassigned. `Someone` and `TBD` mean no owner: stored unassigned. (**Decided 2026-11-24, A-4**) `Team` and `All` are treated like `Everyone`. (**Assumption A-4b**)
- AC-3.6 `A & B to <task>` creates one item per named owner. `A (with B)` is owned by A only; the text is kept in the task. (**Assumption A-5**)

### FR-4 Due dates
- AC-4.1 Due dates are resolved to a real date relative to the **meeting date**, not the ingest date.
- AC-4.2 Supported phrases: ISO date; `10 Sep`, `Oct 3rd`, `2 Oct`, `Wed 16 Sep`; weekday names (`by Friday`, `Wed`, `Mon`); `tomorrow`; `by tomorrow`; `EOD` (same day); `next Tuesday`; `end of month`; `end of next week`.
- AC-4.3 A bare weekday means the first such weekday **on or after** the meeting date: a Friday meeting saying "by Friday" means that same day. (**Decided 2026-11-24, A-6**)
- AC-4.4 `by Friday` style phrases are only read after `by`, `due`, `before`, `until`, `from`, `for` or a dash, or as a trailing `tomorrow`, `today` or `EOD` at the end of the line, so other words in the task text are not mistaken for dates. (v1.1: `for` and the trailing forms added at user request, 2026-11-24)
- AC-4.5 Vague or missing due dates (`mid-October`, none) are never guessed from the text. The stored due date stays empty, the item is listed in the ingest report, and the **effective due date** is the meeting date + 7 days (see AC-6.2). (**Decided 2026-11-24, A-9; A-7**)

### FR-5 Duplicates
The same action repeats across meetings (e.g. "Priya N. to send the revised quote to Acme" on 09-01, 09-08, 09-15).
- AC-5.1 Items are the same when owner and normalised task text match (case, punctuation, trailing "by <date>" ignored). One stored item, with every source file kept. (**Assumption A-8**)
- AC-5.2 If any occurrence is checked `[x]`, the item is done. A later `[ ]` repeat does not reopen a done item.
- AC-5.3 When duplicates carry different due dates, the latest meeting's due date wins.

### FR-6 List
`actiontrack list` shows items.
- AC-6.1 Filters: `--owner <name>`, `--status open|done|overdue`, `--due-before <date>`. Filters combine with AND.
- AC-6.2 **Overdue** = open, with an effective due date earlier than today. The effective due date is the stated due date, or meeting date + 7 days when none was stated. Done items are never overdue. Rows with a defaulted date are shown marked `(default)`. `--due-before` and ordering use the effective due date. (**Decided 2026-11-24, A-9**; the `(default)` marker and filter behaviour are **Assumption A-9b**)
- AC-6.3 "Today" can be set with `--today <date>` (or env var `ACTIONTRACK_TODAY`) so output is reproducible. Default is the system date.
- AC-6.4 `--owner` with a first name that matches two people lists the candidates and exits non-zero without printing items; a full name works. `--owner unassigned` lists items with no owner.
- AC-6.5 Each row shows id, status, owner, task, due date, source file. Order: due date ascending (no due date last), then id.

### FR-7 Done
- AC-7.1 `actiontrack done <id>` marks the item done and records when.
- AC-7.2 Unknown id: error message, non-zero exit. Already done: message, exit 0.
- AC-7.3 Item ids are stable integers that never change on re-ingest.

### FR-8 Follow-up
`actiontrack followup <owner>` drafts one email for that owner covering their open and overdue items, and creates a Gmail draft through the Gmail MCP connector. **It never sends.**
- AC-8.1 The draft lists overdue items first, then open items, each with task, due date and source meeting.
- AC-8.2 Done items are never included. An owner with nothing open gets no draft (message instead).
- AC-8.3 Ambiguous first name: same behaviour as AC-6.4.
- AC-8.4 No code path calls a send operation. Only draft creation is allowed. This is tested.
- AC-8.5 The recipient email address is not in the notes. How it is supplied is **open question OQ-1**.
- AC-8.6 If the connector is unavailable or not authorised, the CLI prints the full draft text and a clear message, and exits non-zero. Nothing is lost.

### FR-9 Malformed notes
- AC-9.1 A note is malformed when it is empty, not valid UTF-8 text, has no recognisable date, or has no recognisable header. Examples in `notes/`: the 0-byte `2026-09-09-notes-final-v2.md`, binary `scratch.md`, undated `2026-10-03-sales-pipeline.md`, headerless `untitled.md`.
- AC-9.2 Malformed notes are skipped whole, reported with file name and reason, and never crash the run. Their items are not stored. (**Assumption A-10**: items from an undated note are dropped rather than stored without a base date.)

## 5. Non-functional requirements

| ID | Requirement | Budget / check |
|---|---|---|
| NFR-1 | Python 3.13, standard library only for runtime; pytest for tests | no runtime deps |
| NFR-2 | `ingest`, `list`, `done` work fully offline | no network call in those commands |
| NFR-3 | Deterministic: same notes + same `--today` gives byte-identical output | golden test |
| NFR-4 | Ingest of the 34-file sample folder | under 2 seconds |
| NFR-5 | Never crash on bad input: no unhandled traceback from any note file | fuzz-style test over the sample folder |
| NFR-6 | No secrets, tokens or email addresses committed; store file `*.db` git-ignored | repo check |
| NFR-7 | One verify command runs all tests and exits non-zero on failure | `python -m pytest` |

## 6. Decided items

| Date | Decision | By |
|---|---|---|
| 2026-11-24 | Python + SQLite, one module | User |
| 2026-11-24 | Gaps in `baseReq.md` inferred and marked Assumption | User |
| 2026-11-24 | A-6: bare weekday resolves on or after the meeting date | User |
| 2026-11-24 | A-9: no due date means effective due = meeting date + 7 days | User |
| 2026-11-24 | A-4: `Everyone` = one item per attendee | User |
| 2026-11-24 | A-10: undated note is skipped whole and reported | User |
| 2026-11-24 | A-3, A-5, A-8 kept as written | User |

## 7. Assumptions to veto (A-1 to A-10)

Listed inline above. A-6, A-9, A-4 and A-10 were decided on 2026-11-24 (see section 6). Still open to veto: **A-3**, **A-5**, **A-8** (duplicate = same owner + normalised task), plus the small follow-on rules **A-4b** and **A-9b**.

## 8. Open questions

- **OQ-1 Gmail MCP from a CLI.** A Python CLI cannot itself call an MCP connector, and no recipient emails exist in the notes. Options belong in the module analysis. (Gmail connector also needs authorising in claude.ai settings before it can be tested live.)
- **OQ-2 Reference "today".** Every sample item is overdue against the real date (2026-11-24). Default is the system date; `--today` makes demos meaningful.
