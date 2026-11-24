# actiontrack tasks

**Branch:** `main` (trunk-based, single session, no worktree). One task = one commit, `feat|test(actiontrack): <summary>`.

## Phase 1: skeleton and dates
- [x] 1.1 Package skeleton, `pyproject.toml`-free layout, `tests/` and `conftest.py` with sample-notes fixture. Files: `actiontrack/__init__.py`, `__main__.py`, `tests/conftest.py`. Tests: none yet. Done: `python -m pytest` runs (0 tests ok).
- [x] 1.2 `dates.py` `resolve_due(phrase, meeting)` per spec section 2, and `effective_due`. Files: `actiontrack/dates.py`, `tests/test_dates.py`. Tests: T-15, T-16 (unit part). Done: table-driven tests green.

## Phase 2: parser
- [x] 2.1 Header + date parsing and malformed reasons. Files: `parser.py`, `tests/test_parser.py`. Tests: T-05, T-06, T-07.
- [x] 2.2 Item scanning: strip quotes/fences/comments, checkbox/`ACTION:`/table forms, `owner to task [by due]` split, no-owner case. Tests: T-08, T-09, T-10, T-14.

## Phase 3: owners
- [x] 3.1 `owners.py` `resolve_owner`: forms, initials, `&`, `(with ...)`, group owners, attendee and registry matching. Files: `owners.py`, `tests/test_owners.py`. Tests: T-11, T-12, T-13.

## Phase 4: store and ingest
- [x] 4.1 `store.py` DDL and queries per spec section 5, `known_people_by_first_name`. Tests: store round-trip in T-04.
- [x] 4.2 `service.ingest`: two-pass, normalised dedup key, due-wins (S-5), never reopen, report. Files: `service.py`, `tests/test_service.py`. Tests: T-01, T-03 (service level), T-04, T-17, T-18, T-19, T-34.

## Phase 5: list and done
- [x] 5.1 `service.list_items`, `service.mark_done`, `cli.py` `list` and `done`, exit codes and `AT-E` messages. Tests: T-20, T-21, T-22, T-23.

## Phase 6: followup and sinks
- [x] 6.1 `draft.py` `build_draft` + golden subject/body. Tests: T-24, T-25.
- [x] 6.2 `sinks.py` `DraftSink` (one method), `FileDraftSink`, `ClaudeGmailDraftSink` with injectable runner. Tests: T-29, T-30, T-31.
- [x] 6.3 `cli.py` `followup` (`--to`, `--sink`), ambiguity exit 2, sink failure exit 3. Tests: T-26, T-27, T-28.

## Phase 7: end to end
- [x] 7.1 E2E over `notes/`: T-02, T-03, T-32, T-33, T-35, T-36, T-37. Done: `python -m pytest` exit 0, ingest report matches the skip list in T-03.
- [x] 7.2 Final leak scan (files, `git log` authors) and log entry in `docs/sdd-log.md`.

## Phase 8: launcher (v1.2)
- [x] 8.1 `run.py` menu + pass-through, `run.bat`, `run.sh`, README quick-start. Tests: T-40..T-44.

## Coverage: every test T-01..T-37 is assigned to a task above.
