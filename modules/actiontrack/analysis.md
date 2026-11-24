# Kick-off analysis: actiontrack

Greenfield: no existing code. Every claim below is backed by a sample note under `notes/` (the only real input) or a requirement.

## What the module must deliver
Parse the 34 sample files into tracked items with resolved owners and due dates, dedupe repeats, and support list/done/followup. About 60 raw checkbox lines exist; the interesting ones are duplicates (quote to Acme x3), two Priyas and two Rahuls, and lines that look like items but are not.

## T1: What counts as "the same item" (AC-5.1, A-8). Decided: ADR-ACTIONTRACK-001

1. **Requirement:** same action repeated across meetings is one item.
2. **Today:** nothing. Evidence of the problem: `2026-09-01-...kickoff.md` says "send the revised quote to Acme", `2026-09-08-...weekly.md` says "send revised quote to Acme", `2026-09-15-...weekly.md` ticks "send the revised quote to Acme". Exact text match would miss the 09-08 repeat ("the" dropped).
3. **Options:** (a) exact text; (b) lower-case, drop punctuation, drop articles `a/an/the`, collapse spaces, drop trailing due phrase; (c) fuzzy similarity score.
4. **Problems:** (a) leaves visible duplicates; (c) can merge different tasks ("share first wireframes" vs "share updated wireframes" are different items) and is hard to test; (b) still misses reworded repeats, which stay as two items.
5. **Recommendation:** (b). Predictable, testable, never merges distinct tasks.
6. **Consequence:** a handful of reworded repeats stay separate; users can mark each done.
7. **Impact:** `parser`/`service` normalise function, `store` unique key. Depends on nothing else.
8. **Question:** see below.

## T2: Relative due phrases beyond "by Friday" (AC-4.2). Decided: ADR-ACTIONTRACK-002

1. **Requirement:** resolve to a real date relative to the meeting date.
2. **Today:** the notes use `next Tuesday` (`2026-10-05-onboarding-retro.md`), `end of next week` (`2026-09-03-billing-migration-sync.md`), `end of month` (`2026-09-14-...`), `tomorrow`, `EOD`, `mid-October` (offsite), and dates without a year (`10 Sep`, `Oct 3rd`).
3. **Options:** (a) `next <weekday>` = that weekday in the **following calendar week**; `end of next week` = Friday of the following week; `end of month` = last day of the meeting's month; (b) `next <weekday>` = first such weekday after the meeting (same as bare weekday); (c) leave all these unresolved.
4. **Problems:** (a) is an interpretation, wrong for a reader who means "the coming Tuesday"; (b) makes `next Tuesday` identical to `Tuesday`; (c) pushes many items to the +7-day default.
5. **Recommendation:** (a). Matches everyday usage and keeps dates real. Year-less dates take the meeting's year, rolling to next year only if that lands more than 6 months before the meeting.
6. **Consequence:** `next Tuesday` said on Mon 2026-10-05 gives 2026-10-13, not 10-06.
7. **Impact:** `dates.py` only; about 12 sample items depend on it.
8. **Question:** see below.

## Impact summary

| Topic | Files touched | Dependents | Depends on |
|---|---|---|---|
| T1 dedup key | `service.py`, `store.py` | list, followup counts | requirements A-8 |
| T2 due phrases | `dates.py` | list order, overdue, followup | requirements A-6, A-9 |

## Parked (out of scope, noticed)
- Items nested under another item are treated as flat.
- Reworded repeats are not merged.
- Quoted or commented lines in two sample notes are deliberate traps; covered by AC-2.4 tests.
