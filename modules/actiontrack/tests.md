# actiontrack tests

**Version:** v1.0 FINAL (2026-11-24). Written from `spec.md` v1.0. Verify command: `python -m pytest` (NFR-7).

**Levels:** U = unit (pure function, no I/O), I = integration (real SQLite in a temp dir, real note files in a temp dir), E = e2e (CLI via `python -m actiontrack` on the sample `notes/`).
**Oracles:** the requirements and spec rules (user-confirmed), the sample notes' own text, and a recorded golden output for the report and the email. "The code's own output" is never an oracle; goldens are written by hand from the rules.
**Faked:** the clock (`--today` / injected date), the `claude` subprocess (fake runner), the filesystem (temp dirs). Nothing touches Gmail or the network.

## Rule coverage

| Test | Rule / AC | Lvl | Setup | Expected |
|---|---|---|---|---|
| T-01 only-md | R1, AC-1.1 | I | folder with `a.md`, `b.txt`, sub-folder `s/c.md` | only `a.md` read; others ignored, not in report as errors |
| T-02 bad-folder | R2, AC-1.3 | E | `ingest nope/` | exit 1, `AT-E003`, no traceback |
| T-03 no-crash-sample | R2, NFR-5 | E | ingest `notes/` | exit 0, report lists skips for the 0-byte `2026-09-09-notes-final-v2.md` (empty), `scratch.md` (not-text), `2026-10-03-sales-pipeline.md` (bad-date), `untitled.md` (no-header); `.txt` absent from errors |
| T-04 idempotent | R3, AC-1.4 | I | ingest twice, `done 1` between | second ingest adds 0, item 1 still done |
| T-05 headers | R4, AC-2.1 | U | markdown header note; frontmatter note (`2026-09-16-standup.md`) | both parse date and attendees |
| T-06 dates | R5, AC-2.5 | U | `2026-09-14`, `9 September 2026`, `Monday, 14 September 2026`, `sometime last week` | first three = right date; last = `bad-date` |
| T-07 skip-reasons | R5, AC-9.1/9.2 | U | empty text; bytes `\x89PNG..`; text with no header | `empty`, `not-text`, `no-header`; none raise |
| T-08 non-items | R6, AC-2.4 | U | blockquote item, fenced block item, HTML-comment item (from `2026-09-21`, `2026-10-09` notes) | none stored; Karan refund quoted line absent |
| T-09 item-forms | R7, AC-2.2/2.3 | U | `-`,`*`,`+` with ` `/`x`/`X`; `ACTION:` line; table row (`2026-09-30-q4-offsite.md`) | all found; x/X = done; table row owner Anita due 2026-10-09 |
| T-10 no-owner-sep | R8 | U | `- [ ] Update the CRM notes` | unassigned, task = whole text, in report |
| T-11 owner-forms | R9, AC-3.1/3.6 | U | `Priya N.`, `@anita`, `Anita & Rahul to agree...`, `Lena (with Priya) to collect...` | Priya N. -> initial N; `@anita` -> Anita; `&` -> two items; `(with ...)` -> Lena only |
| T-12 owner-resolve | R10, AC-3.2..3.4 | U | attendees Priya Nair + Priya Shah; `Priya`; `Priya N.`; no-attendee note with `Rahul`; no-attendee note with `Sam` | `Priya` ambiguous; `Priya N.` = Priya Nair; `Rahul` ambiguous (two known); `Sam` = Sam Okafor |
| T-13 group-owners | R11, AC-3.5 | U | `Everyone to submit...` with 9 attendees; `TBD to write...`; `Team to decide...` | 9 items (one per attendee); TBD unassigned; Team expands |
| T-14 due-prefix | R12, AC-4.4 (v1.1 adds `for` and trailing forms, see T-38) | U | `Everybody should look Friday` in prose, `to send slides by Friday` | prose ignored; second resolves |
| T-15 due-table | R13, AC-4.1..4.5, A-6, ADR-002 | U | table-driven over the section 2 phrases with `M = 2026-10-05 (Mon)` and `M = 2026-09-04 (Fri)` | each equals the hand-computed date: Fri-on-Fri = same day; `next Tuesday` = 2026-10-13; `end of next week` from 2026-09-03 = 2026-09-11; `end of month` = 2026-09-30; `mid-October` unresolved |
| T-16 due-default | R13, AC-4.5/6.2 | I | item with no due, meeting 2026-09-23 | `due` NULL, `due_defaulted` 1, effective 2026-09-30, list shows `(default)` |
| T-17 dedup-acme | R14, AC-5.1..5.3, ADR-001 | I | ingest 09-01, 09-08, 09-15 notes (quote to Acme x3) | one item for Priya Nair, 3 sources, done (09-15 has `[x]`), due 2026-09-11 (09-08 meeting's "by Friday"); 09-15 states no due and does not erase it (**Assumption S-5**: AC-5.3 means the latest meeting that states a due date) |
| T-18 no-reopen | R14, AC-5.2 | I | `[x]` in an early note, `[ ]` in a later one | stays done |
| T-19 dedup-distinct | R14, AC-5.1 | U | `share first wireframes` vs `share updated wireframes` | two items |
| T-20 overdue | R15, AC-6.2 | I | `--today 2026-10-01`; items with due 09-30 open, 09-30 done, none | only the open one is overdue |
| T-21 list-filters | R16, AC-6.1 | I | owner + status + `--due-before` combined | AND semantics; order by effective due then id |
| T-22 list-ambiguous | R16, AC-6.4 | I | `list --owner Priya` with two Priyas | stderr names Priya Nair and Priya Shah, exit 2, no rows; `--owner "Priya Nair"` works; `--owner unassigned` works |
| T-23 done | R17, AC-7.1..7.3 | I | `done 1`, `done 1`, `done 9999` | ok; already-done exit 0; unknown exit 1 `AT-E001`; ids unchanged after re-ingest |
| T-24 followup-draft | R18, AC-8.1/8.2 | I | owner with 1 overdue + 1 open + 1 done | overdue first, then open, done absent; golden subject and (v1.5) plain-text body |
| T-51 followup-html | R23, AC-8.7 | U | owner with 1 overdue, 1 open (one with no due date), task text `<b>x</b> & y` | html has both sections, counts, escaped task, `assumed` wording, no `<script`, no external link; plain text matches the section 6 layout |
| T-25 followup-empty | R18, AC-8.2 | I | owner with only done items | message, no file written, exit 0 |
| T-26 followup-ambiguous | R18, AC-8.3 | I | `followup Rahul --to x@example.invalid` | exit 2, no draft |
| T-27 followup-needs-to | R18, AC-8.5 | E | no `--to` | exit 2 usage |
| T-28 no-send | R19, AC-8.4 | U | scan source text of `actiontrack/` for `send`/`messages.send`/`drafts.send`; inspect `DraftSink` | no send operation; protocol has only `create_draft` |
| T-29 sink-fail | R19, AC-8.6 | I | fake sink raising | full draft printed, `AT-E004`, exit 3 |
| T-30 claude-sink-argv | R19, ADR-0002 | U | fake runner captures argv | fixed list, no shell, only create-draft tool allowed, no send tool |
| T-31 file-sink | R19, ADR-0002 | I | `--sink file --drafts-dir tmp` | JSON file `<owner>-<date>.json` with to, subject, body |

## Non-functional tests

| Test | NFR | Lvl | Expected |
|---|---|---|---|
| T-32 offline | NFR-2 | I | ingest/list/done run with sockets disabled (monkeypatched `socket`) | pass |
| T-33 deterministic | NFR-3 | E | same notes + `--today` twice, fresh db each | identical stdout bytes |
| T-34 order-independent | NFR-3, spec 2 | I | ingest notes copied in two different file orders | identical items |
| T-35 speed | NFR-4 | E | ingest sample folder | under 2 s |
| T-36 stdlib-only | NFR-1 | U | parse imports in package | only stdlib |
| T-37 repo-clean | NFR-6 | U | `.gitignore` covers `*.db`, `drafts/`, `.env*` | present |

## Coverage check

Every rule R1-R19 and every AC (1.1-1.4, 2.1-2.6, 3.1-3.6, 4.1-4.5, 5.1-5.3, 6.1-6.5, 7.1-7.3, 8.1-8.6, 9.1-9.2) appears above. AC-2.6 (item keeps owner, task, due, status, source, meeting date) is checked inside T-17 and T-24.

## v1.1 additions

| Test | Rule / AC | Lvl | Setup | Expected |
|---|---|---|---|---|
| T-38 due-for-and-trailing | R12, AC-4.4 | U | `schedule cutover for Saturday 10 Oct` (meeting 2026-09-29); `circulate the summary tomorrow` (meeting 2026-09-30); prose `Everybody should look Friday` | due 2026-10-10; due 2026-10-01; prose still no due |
| T-39 report-unique | AC-1.2 | I | `Everyone to ...` with several attendees | each ambiguous / no-due line appears once in the report |

## v1.2 additions (launcher)

| Test | Rule / AC | Lvl | Setup | Expected |
|---|---|---|---|---|
| T-40 menu-flow | R20, AC-10.1..10.3, 10.6 | I | scripted input: accept first-launch load, list, done 1, follow-up (file sink), quit; temp db/notes/drafts | notes loaded, list shows items, item 1 done, draft file written, exit 0 |
| T-41 passthrough | R20, AC-10.4 | I | `run.main(["--db", tmp, "list"])` | same output and exit code as the CLI (`no items`, 0) |
| T-42 clean-exit | R20, AC-10.5 | I | input raises EOFError / KeyboardInterrupt | returns 0, no traceback |
| T-43 bad-input | R20, AC-10.2 | I | menu: non-numeric id, bad email, unknown choice | message shown, menu continues |
| T-44 launchers | AC-10.1, 10.7 | U | `run.bat`, `run.sh` exist and call `run.py`; README has a quick-start with `run.py` | present |

## v1.3 additions (HTML report)

| Test | Rule / AC | Lvl | Setup | Expected |
|---|---|---|---|---|
| T-45 report-content | R21, AC-11.1 | I | ingest 3 items (overdue, open, done) then `report --out tmp.html` | file written; counts match; every task text present; filter controls present |
| T-46 report-escapes | R21, AC-11.2 | U | task text `<script>alert(1)</script>` and owner `A&B` | rendered as `&lt;script&gt;...`; no raw `<script>alert` |
| T-47 report-asof | R21, AC-11.3 | I | `--today 2026-10-01` | as-of date shown; overdue count uses it |
| T-48 menu-report | R21, AC-11.4 | I | menu option 7 with the browser opener faked | report file exists, opener called once |
| T-50 report-auto | R22, AC-11.6 | I | run `ingest`, `list`, `done`; then `followup`; then with `--no-report`; then an unwritable `--report` | file exists and reflects the data after each of the first three; unchanged mtime after `followup`; not created with `--no-report`; unwritable path gives `AT-W001` and exit code unchanged |
| T-49 summary-build | R21, AC-11.5 | I | `build_summary.build(run_tests=False)` on the real repo | HTML has the test, notes-run, coverage, SDD-trail and open-items sections |
