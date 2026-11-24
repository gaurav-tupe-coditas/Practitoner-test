from datetime import date

import pytest

from actiontrack.dates import effective_due, parse_header_date, resolve_due, split_due

MON = date(2026, 10, 5)   # Monday
FRI = date(2026, 9, 4)    # Friday
THU = date(2026, 9, 3)    # Thursday


@pytest.mark.parametrize("phrase,meeting,expected", [
    ("2026-09-08", MON, date(2026, 9, 8)),
    ("10 Sep", THU, date(2026, 9, 10)),
    ("Oct 3rd", date(2026, 9, 30), date(2026, 10, 3)),
    ("2 Oct", date(2026, 9, 24), date(2026, 10, 2)),
    ("15 October", date(2026, 9, 30), date(2026, 10, 15)),
    ("Wed 16 Sep", date(2026, 9, 14), date(2026, 9, 16)),
    ("tomorrow", MON, date(2026, 10, 6)),
    ("EOD tomorrow", MON, date(2026, 10, 6)),
    ("EOD", MON, MON),
    ("Friday", FRI, FRI),                      # A-6: on or after, same day counts
    ("Friday", MON, date(2026, 10, 9)),
    ("Mon", FRI, date(2026, 9, 7)),
    ("Wed", date(2026, 9, 1), date(2026, 9, 2)),
    ("next Tuesday", MON, date(2026, 10, 13)),  # ADR-002
    ("end of next week", THU, date(2026, 9, 11)),
    ("end of month", date(2026, 9, 14), date(2026, 9, 30)),
    ("end of month", date(2026, 12, 3), date(2026, 12, 31)),
    ("5 Jan", date(2026, 12, 28), date(2027, 1, 5)),  # year roll
    ("mid-October", MON, None),
    ("whenever", MON, None),
    ("31 Feb", MON, None),
])
def test_resolve_due(phrase, meeting, expected):  # T-15
    assert resolve_due(phrase, meeting) == expected


def test_header_dates():
    assert parse_header_date("2026-09-14") == date(2026, 9, 14)
    assert parse_header_date("9 September 2026") == date(2026, 9, 9)
    assert parse_header_date("Monday, 14 September 2026") == date(2026, 9, 14)
    assert parse_header_date("sometime last week") is None


def test_split_due_keywords_only():
    task, due = split_due("send slides by Friday", MON)
    assert (task, due) == ("send slides", date(2026, 10, 9))
    # weekday words in prose are not dates (R12)
    assert split_due("hold the Friday demo slot", MON) == ("hold the Friday demo slot", None)


def test_split_due_dash_and_iso():
    assert split_due("send revised quote to Acme — by Friday", THU) == ("send revised quote to Acme", date(2026, 9, 4))
    task, due = split_due("cut cloud costs by 10% — proposal by 2026-10-09", MON)
    assert due == date(2026, 10, 9)
    assert split_due("demo the portal to Acme on 2026-10-14", MON)[1] == date(2026, 10, 14)


def test_effective_due_default():
    assert effective_due(None, date(2026, 9, 23)) == date(2026, 9, 30)
    assert effective_due(date(2026, 9, 1), date(2026, 9, 23)) == date(2026, 9, 1)


def test_for_and_trailing_forms():  # T-38 (v1.1)
    assert split_due("schedule cutover for Saturday 10 Oct", date(2026, 9, 29)) == ("schedule cutover", date(2026, 10, 10))
    assert split_due("circulate the summary tomorrow", date(2026, 9, 30)) == ("circulate the summary", date(2026, 10, 1))
    assert split_due("Everybody should look Friday", MON)[1] is None
    assert split_due("prepare for 5 customers", MON)[1] is None
    assert split_due("run tests for invoice rounding by end of next week", THU)[1] == date(2026, 9, 11)
