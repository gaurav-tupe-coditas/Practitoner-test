"""Phase 9: HTML report and project summary (tests.md T-45..T-49)."""
import builtins
import os
import re
import sys
import webbrowser
from datetime import date

import pytest

import run
from actiontrack import report
from actiontrack.store import Item
from conftest import run_cli, write_note

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AT = ["Sam Okafor", "Rahul Mehta"]


def card(html_text, label):
    m = re.search(r'<div class="v">(\d+)</div><div class="l">%s</div>' % re.escape(label), html_text)
    assert m, f"no card {label}"
    return int(m.group(1))


def seed(folder, extra=()):
    write_note(folder, "1.md", "2026-09-01", AT, [
        "- [ ] Sam to overdue thing by 2026-09-10",
        "- [ ] Sam to open thing by 2026-10-20",
        "- [x] Sam to done thing by 2026-09-05", *extra])
    return str(folder)


def test_report_content(tmp_path, monkeypatch):  # T-45
    notes = tmp_path / "n"
    notes.mkdir()
    seed(notes)
    db = str(tmp_path / "r.db")
    assert run_cli(tmp_path, "ingest", str(notes), db=db)[0] == 0
    monkeypatch.chdir(tmp_path)
    code, out, err = run_cli(tmp_path, "report", db=db)          # default file name
    assert code == 0 and err == ""
    text = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert (card(text, "Items"), card(text, "Overdue"), card(text, "Open"), card(text, "Done")) == (3, 1, 1, 1)
    for task in ("overdue thing", "open thing", "done thing"):
        assert task in text
    assert 'id="q"' in text and 'data-filter="overdue"' in text           # search + status filters
    assert text.count("<tr data-status=") == 3                            # all rows present without scripting
    assert "hidden" not in re.findall(r"<tr [^>]*>", text)[0]
    assert re.search(r"https?://|<link |src=", text) is None              # offline, no external references
    assert sorted(os.listdir(tmp_path)) == ["n", "r.db", "report.html"]   # nothing else written
    out_file = tmp_path / "sub.html"
    assert run_cli(tmp_path, "report", "--out", str(out_file), db=db)[0] == 0 and out_file.exists()


def test_report_bad_out_path(tmp_path):  # T-45 (error path)
    code, out, err = run_cli(tmp_path, "report", "--out", str(tmp_path / "nope" / "r.html"))
    assert code == 1 and "AT-E005" in err and "Traceback" not in err


def test_report_escapes(tmp_path):  # T-46
    notes = tmp_path / "n"
    notes.mkdir()
    seed(notes, ["- [ ] Sam to <script>alert(1)</script> & <b>bold</b> by 2026-10-20"])
    db = str(tmp_path / "e.db")
    run_cli(tmp_path, "ingest", str(notes), db=db)
    out_file = tmp_path / "e.html"
    assert run_cli(tmp_path, "report", "--out", str(out_file), db=db)[0] == 0
    text = out_file.read_text(encoding="utf-8")
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in text and "&lt;b&gt;bold&lt;/b&gt;" in text
    assert "<script>alert" not in text and "<b>bold" not in text
    # owner and source names are escaped too (unit level, no parser involved)
    item = Item(1, "A&B", "resolved", '"><img src=x onerror=1>', "k", None, True, "open", None, date(2026, 9, 1), ["f<1>.md"])
    html_text = report.render_report([item], date(2026, 10, 1))
    assert "A&amp;B" in html_text and "<img" not in html_text and "f&lt;1&gt;.md" in html_text


def test_report_asof(tmp_path):  # T-47
    notes = tmp_path / "n"
    notes.mkdir()
    seed(notes)
    db = str(tmp_path / "a.db")
    run_cli(tmp_path, "ingest", str(notes), db=db)
    early, late = tmp_path / "early.html", tmp_path / "late.html"
    run_cli(tmp_path, "report", "--out", str(early), today="2026-09-05", db=db)
    run_cli(tmp_path, "report", "--out", str(late), today="2026-10-01", db=db)
    e, l = early.read_text(encoding="utf-8"), late.read_text(encoding="utf-8")
    assert "As of 2026-09-05" in e and "As of 2026-10-01" in l
    assert card(e, "Overdue") == 0 and card(l, "Overdue") == 1


def test_menu_report(tmp_path, monkeypatch, capsys):  # T-48
    notes = tmp_path / "notes"
    notes.mkdir()
    seed(notes)
    monkeypatch.setattr(run, "DB", str(tmp_path / "m.db"))
    monkeypatch.setattr(run, "NOTES", str(notes))
    monkeypatch.setattr(run, "REPORT", str(tmp_path / "report.html"))
    monkeypatch.setenv("ACTIONTRACK_TODAY", "2026-10-01")
    opened = []
    monkeypatch.setattr(webbrowser, "open", lambda url, *a, **k: opened.append(url) or True)
    answers = iter(["y", "7", "0"])
    prompts = []
    monkeypatch.setattr(builtins, "input", lambda prompt="": prompts.append(prompt) or next(answers))
    assert run.main([]) == 0
    assert (tmp_path / "report.html").exists()
    assert len(opened) == 1 and opened[0].startswith("file:") and opened[0].endswith("report.html")
    out = capsys.readouterr().out
    assert "7) Open report" in out and any("Choose 0-7" in p for p in prompts)


def test_summary_build():  # T-49
    sys.path.insert(0, ROOT)
    from tools import build_summary
    page = build_summary.build(run_tests=False)
    for section in ("tests", "notes", "coverage", "sdd", "open"):
        assert f'id="{section}"' in page, section
    assert "T-01" in page and "ADR-ACTIONTRACK-005" in page and "docs(sdd)" in page
    assert re.search(r"https?://|<link |src=", page) is None
    assert "prefers-color-scheme:dark" in page
    for name in ("skipped scratch.md", "untitled.md"):
        assert name.split()[-1] in page


def test_report_auto_refresh(tmp_path):  # T-50
    notes = tmp_path / "n"
    notes.mkdir()
    seed(notes)
    rep = tmp_path / "auto.html"
    db = str(tmp_path / "x.db")

    import io
    from actiontrack import cli

    def call(*args):
        out, err = io.StringIO(), io.StringIO()
        code = cli.main(["--db", db, "--today", "2026-10-01", *args], out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    assert call("--report", str(rep), "ingest", str(notes))[0] == 0
    assert card(rep.read_text(encoding="utf-8"), "Items") == 3
    rep.unlink()
    code, out, err = call("--report", str(rep), "list")
    assert code == 0 and rep.exists() and f"report updated: {rep}" in out
    assert call("--report", str(rep), "done", "1")[0] == 0
    assert card(rep.read_text(encoding="utf-8"), "Done") == 2
    stamp = rep.stat().st_mtime_ns
    call("--report", str(rep), "followup", "Sam Okafor", "--to", "x@example.invalid", "--drafts-dir", str(tmp_path / "d"))
    assert rep.stat().st_mtime_ns == stamp                                   # followup does not refresh
    rep.unlink()
    assert call("--report", str(rep), "--no-report", "list")[0] == 0 and not rep.exists()
    bad = tmp_path / "nope" / "r.html"
    code, out, err = call("--report", str(bad), "list")
    assert code == 0 and "AT-W001" in err and "Traceback" not in err
