import io
import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actiontrack import cli  # noqa: E402
from actiontrack.store import Store  # noqa: E402

SAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "notes")


def write_note(folder, name, day, attendees, lines):
    body = f"# Meeting: T\nDate: {day}\nAttendees: {', '.join(attendees)}\n\n## Action items\n" + "\n".join(lines) + "\n"
    (folder / name).write_text(body, encoding="utf-8")


@pytest.fixture
def store(tmp_path):
    s = Store(str(tmp_path / "t.db"))
    yield s
    s.close()


def run_cli(tmp_path, *args, today="2026-10-01", db=None, sink_factory=None):
    out, err = io.StringIO(), io.StringIO()
    argv = ["--db", db or str(tmp_path / "cli.db"), "--today", today, *args]
    code = cli.main(argv, out=out, err=err, sink_factory=sink_factory)
    return code, out.getvalue(), err.getvalue()


TODAY = date(2026, 10, 1)


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    """Commands write report.html in the working directory; keep the repo clean."""
    import run
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(run, "REPORT", str(tmp_path / "report.html"))
