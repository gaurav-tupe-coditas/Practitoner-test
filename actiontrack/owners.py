"""Pure owner resolution (spec section 4, R9-R11)."""
from __future__ import annotations

import re
from dataclasses import dataclass

RESOLVED, AMBIGUOUS, UNASSIGNED = "resolved", "ambiguous", "unassigned"
EXPAND = {"everyone", "team", "all"}
NO_OWNER = {"someone", "tbd", ""}


@dataclass(frozen=True)
class Owner:
    name: str | None
    status: str


def _first(full: str) -> str:
    return full.split()[0].lower()


def _match(token: str, initial: str | None, people: list[str]) -> list[str]:
    t = token.lower()
    if len(token.split()) > 1:
        return [p for p in people if p.lower() == t]
    hits = [p for p in people if _first(p) == t]
    if initial:
        narrowed = [p for p in hits if len(p.split()) > 1 and p.split()[-1][0].lower() == initial.lower()]
        hits = narrowed or hits
    return hits


def _resolve_one(raw: str, attendees: list[str], registry: set[str]) -> Owner:
    name = re.sub(r"^@", "", raw.strip()).strip(" :")
    initial = None
    m = re.match(r"^(\w+)\s+([A-Za-z])\.?$", name)
    if m:
        name, initial = m.group(1), m.group(2)
    if name.lower() in NO_OWNER:
        return Owner(None, UNASSIGNED)
    for pool in (sorted(set(attendees)), sorted(registry)):
        hits = _match(name, initial, pool)
        if len(hits) == 1:
            return Owner(hits[0], RESOLVED)
        if len(hits) > 1:
            return Owner(name.title(), AMBIGUOUS)
    return Owner(name.title(), RESOLVED)  # unknown person, keep the name as written


def resolve_owner(raw: str | None, attendees: list[str], registry: set[str]) -> list[Owner]:
    """One Owner per resulting item (A & B and Everyone expand)."""
    if raw is None:
        return [Owner(None, UNASSIGNED)]
    cleaned = re.sub(r"\(.*?\)", "", raw).strip()          # `A (with B)` -> A
    if cleaned.lower() in EXPAND:
        if not attendees:
            return [Owner(None, UNASSIGNED)]
        return [Owner(a, RESOLVED) for a in attendees]
    parts = [p for p in re.split(r"\s*&\s*|\s+and\s+", cleaned) if p.strip()]
    if not parts:
        return [Owner(None, UNASSIGNED)]
    return [_resolve_one(p, attendees, registry) for p in parts]
