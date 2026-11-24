"""Pure draft builder and the DraftSink port (ADR-0002). The port has no send method."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class Draft:
    owner: str
    to: str
    subject: str
    body: str
    day: date


class DraftSink(Protocol):
    def create_draft(self, draft: Draft) -> None: ...


def _line(item) -> str:
    from .dates import effective_due
    due = item.due if item.due else effective_due(None, item.latest_meeting)
    mark = " (default)" if item.due is None else ""
    src = item.sources[-1] if item.sources else "?"
    return f"- {item.task} (due {due.isoformat()}{mark}) from {item.latest_meeting.isoformat()} {src}"


def build_draft(owner: str, to: str, overdue: list, open_: list, today: date) -> Draft:
    first = owner.split()[0]
    parts = [f"Hi {first},", "", "Here are your action items from recent meetings."]
    if overdue:
        parts += ["", "Overdue:"] + [_line(i) for i in overdue]
    if open_:
        parts += ["", "Open:"] + [_line(i) for i in open_]
    parts += ["", "Please reply with any updates.", ""]
    subject = f"Action items for {owner}: {len(overdue)} overdue, {len(open_)} open"
    return Draft(owner, to, subject, "\n".join(parts), today)
