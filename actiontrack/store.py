"""SQLite repository. The only module that imports sqlite3 (ADR-0001)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

SCHEMA = """
CREATE TABLE IF NOT EXISTS people(full_name TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS items(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner TEXT,
  owner_status TEXT NOT NULL CHECK (owner_status IN ('resolved','ambiguous','unassigned')),
  task TEXT NOT NULL,
  task_key TEXT NOT NULL,
  due TEXT,
  due_defaulted INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK (status IN ('open','done')),
  done_at TEXT,
  latest_meeting TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS items_key ON items(COALESCE(owner,''), owner_status, task_key);
CREATE TABLE IF NOT EXISTS item_sources(
  item_id INTEGER NOT NULL REFERENCES items(id),
  file TEXT NOT NULL,
  meeting_date TEXT NOT NULL,
  PRIMARY KEY (item_id, file)
);
"""


@dataclass
class Item:
    id: int
    owner: str | None
    owner_status: str
    task: str
    task_key: str
    due: date | None
    due_defaulted: bool
    status: str
    done_at: date | None
    latest_meeting: date
    sources: list[str]


def _d(v: str | None) -> date | None:
    return date.fromisoformat(v) if v else None


class Store:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def transaction(self):
        return self.conn  # `with store.transaction():` commits or rolls back

    def add_people(self, names) -> None:
        self.conn.executemany("INSERT OR IGNORE INTO people(full_name) VALUES (?)", [(n,) for n in names])

    def people(self) -> list[str]:
        return [r[0] for r in self.conn.execute("SELECT full_name FROM people ORDER BY full_name")]

    def people_by_first_name(self, first: str) -> list[str]:
        return [p for p in self.people() if p.split()[0].lower() == first.lower()]

    def _row_to_item(self, r: sqlite3.Row) -> Item:
        src = [s[0] for s in self.conn.execute(
            "SELECT file FROM item_sources WHERE item_id=? ORDER BY meeting_date, file", (r["id"],))]
        return Item(r["id"], r["owner"], r["owner_status"], r["task"], r["task_key"], _d(r["due"]),
                    bool(r["due_defaulted"]), r["status"], _d(r["done_at"]), _d(r["latest_meeting"]), src)

    def find(self, owner: str | None, owner_status: str, task_key: str) -> Item | None:
        r = self.conn.execute(
            "SELECT * FROM items WHERE COALESCE(owner,'')=COALESCE(?,'') AND owner_status=? AND task_key=?",
            (owner, owner_status, task_key)).fetchone()
        return self._row_to_item(r) if r else None

    def get(self, item_id: int) -> Item | None:
        r = self.conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        return self._row_to_item(r) if r else None

    def all_items(self) -> list[Item]:
        return [self._row_to_item(r) for r in self.conn.execute("SELECT * FROM items ORDER BY id")]

    def insert(self, owner, owner_status, task, task_key, due, defaulted, status, done_at, meeting) -> int:
        cur = self.conn.execute(
            "INSERT INTO items(owner,owner_status,task,task_key,due,due_defaulted,status,done_at,latest_meeting)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (owner, owner_status, task, task_key, _s(due), int(defaulted), status, _s(done_at), meeting.isoformat()))
        return cur.lastrowid

    def update(self, item_id: int, task, due, defaulted, status, done_at, meeting) -> None:
        self.conn.execute(
            "UPDATE items SET task=?, due=?, due_defaulted=?, status=?, done_at=?, latest_meeting=? WHERE id=?",
            (task, _s(due), int(defaulted), status, _s(done_at), meeting.isoformat(), item_id))

    def add_source(self, item_id: int, file: str, meeting: date) -> bool:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO item_sources(item_id,file,meeting_date) VALUES (?,?,?)",
            (item_id, file, meeting.isoformat()))
        return cur.rowcount > 0

    def mark_done(self, item_id: int, today: date) -> None:
        with self.conn:
            self.conn.execute("UPDATE items SET status='done', done_at=? WHERE id=?", (today.isoformat(), item_id))


def _s(d: date | None) -> str | None:
    return d.isoformat() if d else None
