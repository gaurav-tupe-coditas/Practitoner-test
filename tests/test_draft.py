"""Follow-up email content (tests.md T-51)."""
import re
from datetime import date

from actiontrack.draft import build_draft
from actiontrack.store import Item


def item(i, task, due, status="open"):
    return Item(i, "Sam Okafor", "resolved", task, "k", due, due is None, status, None, date(2026, 9, 1), ["f<1>.md"])


def test_html_email():  # T-51
    overdue = [item(1, "<b>x</b> & y", date(2026, 9, 10))]
    rest = [item(2, "no date thing", None)]
    d = build_draft("Sam Okafor", "s@example.invalid", overdue, rest, date(2026, 10, 1))
    h = d.html
    assert "Hi Sam," in h and "Overdue" in h and "Open" in h
    assert "&lt;b&gt;x&lt;/b&gt; &amp; y" in h and "<b>x</b>" not in h and "f&lt;1&gt;.md" in h
    assert "assumed" in h and "10 Sep 2026" in h and "8 Sep 2026" in h      # stated date, and meeting + 7 days
    assert "<script" not in h and not re.search(r"https?://|<link |<img", h)
    assert "style=" in h and "<style" not in h                               # inline styles only
    assert "background" not in h and "#ffffff" not in h                      # Gmail strips backgrounds: no white-on-white
    assert d.body.splitlines()[0] == "Hi Sam," and "OVERDUE (1)" in d.body and "OPEN (1)" in d.body
    assert "(assumed: no date was set)" in d.body and "(default)" not in d.body


def test_html_omits_empty_sections():  # T-51
    d = build_draft("Sam Okafor", "s@example.invalid", [], [item(2, "only open", date(2026, 10, 20))], date(2026, 10, 1))
    assert "Overdue" not in d.html and "OVERDUE" not in d.body and "OPEN (1)" in d.body
