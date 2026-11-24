# actiontrack plan

**Version:** v0.9 DRAFT. Inputs: `spec.md` v1.0, `tests.md` v1.0, ADR-0001/0002, ADR-ACTIONTRACK-001/002.

## Approach
Test-first, bottom-up: pure helpers first (they carry the risk and need no database), then the store and ingest service, then the CLI commands, then the draft sink. Each phase ends with `python -m pytest` green and one commit. Trunk-based on `main`, one session, no worktree.

## Order and why
1. **Skeleton + dates** (T-14, T-15): the due-phrase table is the most intricate pure logic.
2. **Parser** (T-05..T-09, T-10): headers, malformed reasons, item forms, non-items.
3. **Owners** (T-11..T-13): needs the parser's attendee lists and the registry.
4. **Store + ingest** (T-01..T-04, T-16..T-19, T-34): two-pass ingest, dedup, never reopen.
5. **list + done** (T-20..T-23): overdue, filters, ambiguity, exit codes.
6. **followup + sinks** (T-24..T-31): draft builder, file sink, claude sink argv, no-send scan.
7. **Non-functional + e2e** (T-02, T-03, T-32, T-33, T-35..T-37): sample folder end to end, determinism, speed.

## Risks
| Risk | Mitigation |
|---|---|
| Due-phrase edge cases (weekday vs prose word) | table-driven tests with hand-computed dates; weekday words only read inside a due phrase (R12) |
| Owner ambiguity wrongly resolved | tests built from the sample notes with two Priyas and two Rahuls; ambiguity is the default when unsure |
| `claude` CLI flags unknown (S-3) | isolated in `sinks.py`; argv covered by a fake-runner test; live use is optional |
| Time box | phases are independently shippable; unfinished phases are reported, not faked |
| Leaking org or personal details | pre-commit scan of staged diff and `git log` authors; generic git identity (CLAUDE.md) |

## Verify command
`python -m pytest` from the repo root, exit 0.
