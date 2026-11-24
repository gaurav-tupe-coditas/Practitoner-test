# actiontrack: System specification

**Version:** v1.0 FINAL (confirmed 2026-11-24). OQ-1 decided: option A, see `docs/adr/ADR-0002-draft-sink-port.md`.
**Date:** 2026-11-24
**Cites:** `docs/requirements.md` v1.0 (FR-x, AC-x.y, NFR-x)

## 1. Architecture (ADR-0001, Accepted by default per sdd-epic section 6)

Single module, layered: `cli` -> `service` -> `store` (SQLite), with pure helpers (`parser`, `dates`, `owners`, `draft`) that do no I/O. One external port: `DraftSink`. The service never talks to SQLite or Gmail directly.

```
actiontrack/
  __main__.py     entry: python -m actiontrack
  cli.py          argparse, exit codes, printing only
  service.py      ingest / list / done / followup use-cases; transaction boundary
  store.py        SQLite repository (only file that imports sqlite3)
  parser.py       note text -> Note(date, attendees, raw_items) or MalformedNote(reason)   [pure]
  dates.py        resolve_due(phrase, meeting_date) -> date | None                         [pure]
  owners.py       resolve_owner(raw, attendees, known_people) -> Owner                      [pure]
  draft.py        build_draft(owner, items, today) -> Draft; DraftSink port                 [pure]
  sinks.py        FileDraftSink, ClaudeGmailDraftSink (adapters of the port)
tests/            pytest, one file per module, plus an end-to-end test over notes/
```

Rules: only `store.py` imports `sqlite3`; only `sinks.py` runs subprocesses; `parser`, `dates`, `owners`, `draft` take values and return values (NFR-3, NFR-5). "Today" is passed in by `cli.py`, never read inside the lower layers (AC-6.3).

## 2. Ingest flow (FR-1, FR-2, FR-9, NFR-3)

Two passes so the result does not depend on file order:
1. **Scan:** list `*.md` in the folder (non-recursive, sorted by name). Parse each into a `Note` or a `MalformedNote`. Collect every attendee full name into the **people registry**.
2. **Resolve and store:** for each `Note` in meeting-date order: resolve owners (using that note's attendees, then the registry), resolve due dates against the meeting date, expand `Everyone`/`Team`/`All` per attendee, compute the dedup key, upsert, record the source. One SQLite transaction for the whole ingest; a failure rolls back everything.

Ingest prints the report from AC-1.2: files read, skipped (name + reason), items added/updated, ambiguous owners, unresolved or defaulted due dates. Exit 0 unless the folder path is invalid.

## 3. Parsing rules (FR-2)

- Header: markdown (`# Meeting:`, `Date:`, `Attendees:`) or YAML frontmatter (`title`, `date`, `attendees: [...]`). No header -> malformed. No parseable date -> malformed. Empty or non-UTF-8 -> malformed (AC-9.1).
- Before scanning for items, blank out fenced code blocks, HTML comments and blockquote lines (AC-2.4).
- Item line patterns: checkbox bullet `[-*+] [ xX]`, any indent (nesting is flat); `ACTION:` prefix (open); table rows under a header containing Owner, Action and Due columns.
- Item text splits as `<owner> to <task> [<due phrase>]`. A line with no ` to ` splits at the first verb-like gap is **not** guessed: it is stored with no owner and the whole text as task (reported). (Assumption S-1)
- A due phrase is only read after `by`, `due`, `before`, `until`, `from`, or a dash (AC-4.4), plus a leading `Owner to <task> by <phrase>`.

## 4. Owner resolution (FR-3)

`resolve_owner` returns `(name, status)` with status `resolved | ambiguous | unassigned`:
1. Strip `@`, trailing initial (`Priya N.`), and `(with X)`; split `A & B` into several owners.
2. `Everyone`/`Team`/`All` -> one owner per attendee; `Someone`/`TBD`/empty -> unassigned.
3. Match the first name against the note's attendees; one match -> resolved full name; initial narrows; several -> ambiguous.
4. No attendee list -> match against the registry; exactly one -> resolved, else ambiguous.

Ambiguous owners keep the first name as the stored owner and `owner_status = ambiguous`. `list --owner <first>` shows them as ambiguous rows (section 6). `followup` never drafts for an ambiguous owner: it asks for a full name (exit 2).

## 5. Data model (FR-5, FR-7)

```
people(full_name PRIMARY KEY)
items(
  id            INTEGER PRIMARY KEY AUTOINCREMENT,   -- stable id (AC-7.3)
  owner         TEXT,                                 -- full name, first name if ambiguous, NULL if unassigned
  owner_status  TEXT NOT NULL CHECK (owner_status IN ('resolved','ambiguous','unassigned')),
  task          TEXT NOT NULL,                        -- display text of the latest occurrence
  task_key      TEXT NOT NULL,                        -- normalised text, dedup key (A-8)
  due           TEXT,                                 -- ISO date or NULL (as stated)
  due_defaulted INTEGER NOT NULL DEFAULT 0,           -- 1 when effective due = meeting + 7 (A-9)
  status        TEXT NOT NULL CHECK (status IN ('open','done')),
  done_at       TEXT,
  latest_meeting TEXT NOT NULL,
  UNIQUE (owner, owner_status, task_key)
)
item_sources(item_id REFERENCES items(id), file TEXT, meeting_date TEXT, PRIMARY KEY (item_id, file))
```

Re-ingest upserts on the unique key: adds sources, applies the latest meeting's due date (AC-5.3), turns an item done on any `[x]` and never reopens it (AC-5.2, AC-1.4). The store path defaults to `./actiontrack.db`, overridable with `--db` (git-ignored, NFR-6).

## 6. List and done (FR-6, FR-7)

- Effective due = `due` or `latest_meeting + 7 days` when `due_defaulted`. Overdue = open and effective due < today.
- `--owner <name>`: full name matches exactly; a first name matching two or more known people prints the candidates and exits 2 (AC-6.4); `unassigned` lists items with no owner. Ambiguous-status items match their first name only.
- Output: fixed-width table, columns id, status, owner, task, due (`(default)` marker), source file(s); sorted by effective due then id. Exit 0 with a "no items" line when empty.
- `done <id>`: unknown id exits 1; already done exits 0 with a message; else sets `status='done'`, `done_at=today`.

## 7. Follow-up and the Gmail port (FR-8, OQ-1)

`service.followup(owner, to_address, today, sink)`:
1. Resolve owner as in section 6 (exit 2 on ambiguity). Collect open items, split overdue first then open (AC-8.1). None -> message, no draft (AC-8.2).
2. `draft.build_draft` returns `Draft(to, subject, body)`; pure and golden-testable.
3. `sink.create_draft(draft)`. **The port has one method only, `create_draft`; no send method exists anywhere** (AC-8.4).
4. Sink failure -> print the full draft text, a clear error, exit 3 (AC-8.6).

**OQ-1 options** (a CLI cannot call an MCP connector itself):
- **A. Port + two adapters (Recommended):** `FileDraftSink` (writes `drafts/<owner>-<date>.json`, always works, used by tests and as the safe default) and `ClaudeGmailDraftSink` (runs the `claude` CLI headless with the Gmail connector's create-draft tool as the only allowed tool, so it cannot send). Needs `claude` installed and the connector authorised; cannot be verified live until then.
- **B. File only:** the CLI always writes the draft file; a Claude session turns it into a Gmail draft by hand. Fully testable, but not automatic.
- **C. Gmail API directly:** automatic, but it is not the MCP connector the brief names, and adds credentials to handle.

Recipient: `--to <email>` is required (notes hold no emails, AC-8.5). It is passed per run and never stored.

## 8. Cross-cutting

- **Errors and exit codes:** 0 ok; 1 not found / invalid folder; 2 ambiguous owner or bad usage; 3 draft sink failure. No traceback reaches the user (NFR-5): `cli.py` catches `Exception` at the top, prints a one-line error, exits 1.
- **Security:** no network in `ingest`/`list`/`done` (NFR-2); the only subprocess is in `ClaudeGmailDraftSink`, with a fixed argument list (no shell); `--to` is validated as a plain address; no secrets read or stored (NFR-6).
- **Privacy:** no real names or addresses are embedded in code or docs; tests use the fictional sample notes only.
- **Observability:** the ingest report is the audit trail; each run is one transaction.
- **Performance:** all work in memory over 34 small files; budget 2 s (NFR-4), measured in a test.

## 9. Assumptions and open items

- **S-1** A task line with no " to " separator is stored unassigned, whole text as task, and reported.
- **S-2** `drafts/` is git-ignored.
- **OQ-1** Gmail adapter choice: see section 7, needs the user's decision.
