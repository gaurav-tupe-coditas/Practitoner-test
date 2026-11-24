# Module ADRs: actiontrack

Central ADRs: `docs/adr/ADR-0001`, `ADR-0002`. Newest last.

### ADR-ACTIONTRACK-001: Duplicate items match on normalised text
- **Status:** Accepted
- **Date:** 2026-11-24
- **Decided by:** User (analysis T1, recommended option)
- **Context:** The same action repeats across meetings, sometimes with small wording changes (articles dropped, trailing due phrase added).
- **Decision:** Dedup key = (owner, owner_status, normalised task). Normalised = lower-case, punctuation removed, articles `a/an/the` removed, whitespace collapsed, trailing due phrase removed. No fuzzy matching.
- **Consequences:** Predictable and testable. Reworded repeats stay separate items.

### ADR-ACTIONTRACK-002: "next" and "end of" due phrases use the following calendar week
- **Status:** Accepted
- **Date:** 2026-11-24
- **Decided by:** User (analysis T2, recommended option)
- **Context:** Notes use `next Tuesday`, `end of next week`, `end of month`, and dates without a year.
- **Decision:** `next <weekday>` = that weekday in the following Monday-to-Sunday week. `end of next week` = Friday of the following week. `end of month` = last day of the meeting's month. A year-less date takes the meeting's year, rolling to the next year only if it would land more than 6 months before the meeting. `mid-<month>` and similar stay unresolved (effective due = meeting + 7 days, per requirements A-9).
- **Consequences:** `next Tuesday` said on Monday 2026-10-05 resolves to 2026-10-13. Some readers may mean 2026-10-06; this is a documented interpretation.

### ADR-ACTIONTRACK-003: Read `for` and trailing tomorrow/today/EOD as due phrases
- **Status:** Accepted
- **Date:** 2026-11-24
- **Decided by:** User (asked for the due-date misses to be fixed)
- **Context:** Sample notes say `schedule cutover for Saturday 10 Oct` and `circulate the summary tomorrow`; R12 left both undated, so they fell back to meeting + 7 days.
- **Decision:** Add `for` to the due keywords and accept a trailing `tomorrow`, `today` or `EOD` at the end of the line. A candidate must resolve completely to count, so `for 5 customers` or `for invoice rounding` stay undated. Requirements bumped to v1.1 (AC-4.4 only).
- **Consequences:** Two sample items get real dates. Small risk: `for Friday` in prose now reads as a due date.
