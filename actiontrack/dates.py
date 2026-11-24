"""Pure date helpers: due-phrase resolution (spec section 2) and header dates."""
from __future__ import annotations

import re
from datetime import date, timedelta

WEEKDAYS = {
    "mon": 0, "monday": 0, "tue": 1, "tues": 1, "tuesday": 1,
    "wed": 2, "wednesday": 2, "thu": 3, "thur": 3, "thurs": 3, "thursday": 3,
    "fri": 4, "friday": 4, "sat": 5, "saturday": 5, "sun": 6, "sunday": 6,
}
MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}
_WD = "|".join(sorted(WEEKDAYS, key=len, reverse=True))
_MON = "|".join(sorted(MONTHS, key=len, reverse=True))
_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_DAY_MONTH = re.compile(rf"^(?:(?:{_WD}) )?(\d{{1,2}})(?:st|nd|rd|th)? ({_MON})(?: (\d{{4}}))?$")
_MONTH_DAY = re.compile(rf"^(?:(?:{_WD}) )?({_MON}) (\d{{1,2}})(?:st|nd|rd|th)?(?: (\d{{4}}))?$")
_NEXT_WD = re.compile(rf"^next ({_WD})$")
_BARE_WD = re.compile(rf"^({_WD})$")
_LEAD_KEYWORD = re.compile(r"^(?:by|due|before|until|from|on)\s+")


def weekday_on_or_after(meeting: date, weekday: int) -> date:
    return meeting + timedelta(days=(weekday - meeting.weekday()) % 7)


def weekday_next_week(meeting: date, weekday: int) -> date:
    monday_next = meeting - timedelta(days=meeting.weekday()) + timedelta(days=7)
    return monday_next + timedelta(days=weekday)


def _clean(phrase: str) -> str:
    p = phrase.strip().lower().replace(",", " ")
    p = re.sub(r"^[\s—–-]+", "", p)
    p = re.sub(r"[.;:!\s]+$", "", p)
    p = re.sub(r"\s+", " ", p)
    return p


def _with_year(day: int, month: int, year: int | None, meeting: date | None) -> date | None:
    try:
        if year is not None:
            return date(year, month, day)
        if meeting is None:
            return None
        d = date(meeting.year, month, day)
        if d < meeting - timedelta(days=183):
            d = date(meeting.year + 1, month, day)
        return d
    except ValueError:
        return None


def _absolute(p: str, meeting: date | None) -> date | None:
    m = _ISO.match(p)
    if m:
        try:
            return date(int(m[1]), int(m[2]), int(m[3]))
        except ValueError:
            return None
    m = _DAY_MONTH.match(p)
    if m:
        return _with_year(int(m[1]), MONTHS[m[2]], int(m[3]) if m[3] else None, meeting)
    m = _MONTH_DAY.match(p)
    if m:
        return _with_year(int(m[2]), MONTHS[m[1]], int(m[3]) if m[3] else None, meeting)
    return None


def parse_header_date(text: str) -> date | None:
    """Header `Date:` value. A year is required."""
    p = _clean(text)
    return _absolute(p, None)


def resolve_due(phrase: str, meeting: date) -> date | None:
    """Resolve a due phrase relative to the meeting date. None when unresolvable."""
    p = _LEAD_KEYWORD.sub("", _clean(phrase))
    if p in ("eod", "today", "eod today"):
        return meeting
    if p in ("tomorrow", "eod tomorrow"):
        return meeting + timedelta(days=1)
    d = _absolute(p, meeting)
    if d:
        return d
    m = _NEXT_WD.match(p)
    if m:
        return weekday_next_week(meeting, WEEKDAYS[m[1]])
    m = _BARE_WD.match(p)
    if m:
        return weekday_on_or_after(meeting, WEEKDAYS[m[1]])
    if p == "end of next week":
        return weekday_next_week(meeting, 4)
    if p in ("end of week", "end of the week"):
        return weekday_on_or_after(meeting, 4)
    if p in ("end of month", "end of the month"):
        nxt = date(meeting.year + (meeting.month == 12), meeting.month % 12 + 1, 1)
        return nxt - timedelta(days=1)
    return None


_KEYWORD = re.compile(r"\b(?:by|due|before|until|from|for)\b|\s[—–-]+\s")
_TRAILING = re.compile(r"\s((?:eod )?tomorrow|eod|today)[.\s]*$", re.IGNORECASE)


def split_due(text: str, meeting: date) -> tuple[str, date | None]:
    """Split `task text` into (task without its due clause, resolved due or None).

    A due phrase is read only after by/due/before/until/from or a dash (R12), taking the
    earliest keyword whose remainder resolves. `on <ISO date>` is also accepted (S-6).
    """
    candidates = [(m.start(), text[m.end():]) for m in _KEYWORD.finditer(text)]
    for m in re.finditer(r"\bon\s+(\d{4}-\d{2}-\d{2})\b", text):
        candidates.append((m.start(), m.group(1)))
    t = _TRAILING.search(text)                      # v1.1: trailing "tomorrow" / "today" / "EOD"
    if t:
        candidates.append((t.start(), t.group(1)))
    for start, rest in sorted(candidates, key=lambda c: c[0]):
        d = resolve_due(rest, meeting)
        if d:
            task = re.sub(r"[\s,;—–-]+$", "", text[:start])
            return task, d
    return text.strip(), None


def effective_due(due: date | None, latest_meeting: date) -> date:
    return due if due else latest_meeting + timedelta(days=7)
