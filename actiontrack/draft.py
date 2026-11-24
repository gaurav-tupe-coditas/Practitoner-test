"""Pure draft builder and the DraftSink port (ADR-0002). The port has no send method.

v1.5 (AC-8.7, ADR-ACTIONTRACK-007): every draft has a plain-text body laid out for reading and an
email-safe HTML version (inline styles, table layout, no scripts or external resources).
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from .dates import effective_due

_ASSUMED = "assumed: no date was set"


@dataclass(frozen=True)
class Draft:
    owner: str
    to: str
    subject: str
    body: str
    day: date
    html: str = ""


class DraftSink(Protocol):
    def create_draft(self, draft: Draft) -> None: ...


def _fmt(d: date) -> str:
    return f"{d.day} {d.strftime('%b %Y')}"


def _facts(item) -> tuple[str, bool, str, str]:
    due = item.due if item.due else effective_due(None, item.latest_meeting)
    src = item.sources[-1] if item.sources else "?"
    return _fmt(due), item.due is None, _fmt(item.latest_meeting), src


def _text_section(title: str, items: list) -> list[str]:
    lines = ["", f"{title} ({len(items)})"]
    for n, item in enumerate(items, 1):
        due, assumed, meeting, src = _facts(item)
        lines += [f"  {n}. {item.task}",
                  f"     Due {due}{f' ({_ASSUMED})' if assumed else ''} - from the {meeting} meeting ({src})"]
    return lines


def _card(item, accent: str) -> str:
    e = html.escape
    due, assumed, meeting, src = _facts(item)
    note = f' <span style="color:#8a6d1d">({e(_ASSUMED)})</span>' if assumed else ""
    return (
        f'<tr><td style="padding:0 0 10px 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="border:1px solid #d5dbe6;border-left:5px solid {accent};border-radius:6px">'
        f'<tr><td style="padding:12px 14px">'
        f'<div style="font-size:15px;font-weight:600;color:#1b2230;line-height:1.4">{e(item.task)}</div>'
        f'<div style="font-size:13px;color:#4a5568;margin-top:4px">Due <b style="color:{accent}">{e(due)}</b>{note}</div>'
        f'<div style="font-size:12px;color:#8590a2;margin-top:2px">From the {e(meeting)} meeting &middot; {e(src)}</div>'
        f'</td></tr></table></td></tr>')


def _html_section(title: str, items: list, accent: str) -> str:
    if not items:
        return ""
    head = (f'<tr><td style="padding:18px 0 8px 0;font-size:12px;font-weight:700;letter-spacing:.08em;'
            f'text-transform:uppercase;color:{accent}">{html.escape(title)} &middot; {len(items)}</td></tr>')
    return head + "".join(_card(i, accent) for i in items)


def _chip(count: int, label: str, color: str) -> str:
    return (f'<td style="padding-right:8px"><div style="border:1px solid {color};color:{color};border-radius:999px;'
            f'padding:4px 12px;font-size:13px;font-weight:700">{count} {label}</div></td>')


def _html(first: str, overdue: list, open_: list) -> str:
    e = html.escape
    chips = _chip(len(overdue), "overdue", "#b3261e") + _chip(len(open_), "open", "#1f4fc4")
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:16px 8px">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;'
        'font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif">'
        '<tr><td style="padding:0 0 12px 0;border-bottom:3px solid #1f4fc4">'
        '<div style="font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#6b7690">Action items</div>'
        '<div style="font-size:22px;font-weight:700;color:#1f2d4d;margin-top:2px">Your follow-up</div></td></tr>'
        '<tr><td style="padding:18px 0 0 0">'
        f'<div style="font-size:16px;color:#1b2230;margin-bottom:6px">Hi {e(first)},</div>'
        '<div style="font-size:14px;color:#4a5568;margin-bottom:14px">Here is where your action items from recent meetings stand.</div>'
        f'<table role="presentation" cellpadding="0" cellspacing="0"><tr>{chips}</tr></table>'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
        f'{_html_section("Overdue", overdue, "#b3261e")}{_html_section("Open", open_, "#1f4fc4")}</table>'
        '<div style="font-size:14px;color:#4a5568;margin-top:18px">Please reply with any updates.</div>'
        '</td></tr>'
        '<tr><td style="padding:16px 0 0 0;font-size:11px;color:#8590a2;border-top:1px solid #d5dbe6;margin-top:16px">'
        'Drafted by actiontrack from meeting notes. Dates marked &ldquo;assumed&rdquo; had no due date in the notes.</td></tr>'
        '</table></td></tr></table>')


def build_draft(owner: str, to: str, overdue: list, open_: list, today: date) -> Draft:
    first = owner.split()[0]
    lines = [f"Hi {first},", "",
             f"Here is where your action items stand: {len(overdue)} overdue, {len(open_)} open."]
    if overdue:
        lines += _text_section("OVERDUE", overdue)
    if open_:
        lines += _text_section("OPEN", open_)
    lines += ["", "Please reply with any updates.", ""]
    subject = f"Action items for {owner}: {len(overdue)} overdue, {len(open_)} open"
    return Draft(owner, to, subject, "\n".join(lines), today, _html(first, overdue, open_))
