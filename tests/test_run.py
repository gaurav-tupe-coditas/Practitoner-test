import builtins
import os

import pytest

import run
from conftest import write_note

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AT = ["Sam Okafor", "Rahul Mehta", "Rahul Verma"]


def feed(monkeypatch, answers):
    it = iter(answers)

    def fake(prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise EOFError
    monkeypatch.setattr(builtins, "input", fake)


@pytest.fixture
def env(tmp_path, monkeypatch):
    notes = tmp_path / "notes"
    notes.mkdir()
    write_note(notes, "1.md", "2026-09-01", AT, ["- [ ] Sam to overdue thing by 2026-09-10", "- [ ] Rahul to shared name thing"])
    monkeypatch.setattr(run, "DB", str(tmp_path / "t.db"))
    monkeypatch.setattr(run, "NOTES", str(notes))
    monkeypatch.setattr(run, "DRAFTS", str(tmp_path / "drafts"))
    monkeypatch.setenv("ACTIONTRACK_TODAY", "2026-10-01")
    return tmp_path


def test_menu_flow(env, monkeypatch, capsys):  # T-40
    feed(monkeypatch, ["", "2", "", "overdue", "", "3", "1", "4", "Sam Okafor", "s@example.invalid", "", "0"])
    assert run.main([]) == 0
    out = capsys.readouterr().out
    assert "First launch" in out and "added 2" in out
    assert "overdue thing" in out and "item 1 marked done" in out
    # follow-up for Sam: the item was just marked done, so nothing is open and no draft is written
    assert "no draft created" in out
    assert not os.path.exists(env / "drafts")


def test_menu_followup_writes_draft(env, monkeypatch, capsys):  # T-40
    feed(monkeypatch, ["n", "1", "", "4", "Sam Okafor", "s@example.invalid", "file", "0"])
    assert run.main([]) == 0
    out = capsys.readouterr().out
    assert "draft created for Sam Okafor" in out and "nothing was sent" in out
    assert (env / "drafts" / "sam-okafor-2026-10-01.json").exists()


def test_passthrough(tmp_path, capsys):  # T-41
    assert run.main(["--db", str(tmp_path / "p.db"), "list"]) == 0
    assert "no items" in capsys.readouterr().out


@pytest.mark.parametrize("exc", [EOFError, KeyboardInterrupt])
def test_clean_exit(env, monkeypatch, capsys, exc):  # T-42
    def boom(prompt=""):
        raise exc
    monkeypatch.setattr(builtins, "input", boom)
    assert run.main([]) == 0
    assert "Traceback" not in capsys.readouterr().err


def test_bad_input_keeps_menu_running(env, monkeypatch, capsys):  # T-43
    feed(monkeypatch, ["y", "9", "3", "abc", "4", "Sam Okafor", "not-an-email", "2", "", "sometimes", "", "4", "Rahul", "r@example.invalid", "file", "0"])
    assert run.main([]) == 0
    cap = capsys.readouterr()
    out, err = cap.out, cap.err
    assert "Please type a number from 0 to 7" in out
    assert "Please type the ID number" in out
    assert "does not look like an email" in out
    assert "Status must be open, done or overdue" in out
    assert "AT-E002" in err and "Rahul Mehta" in err and "Rahul Verma" in err   # shared first name asks for a full name


def test_launchers_and_readme():  # T-44
    assert "run.py" in open(os.path.join(ROOT, "run.bat"), encoding="utf-8").read()
    assert "run.py" in open(os.path.join(ROOT, "run.sh"), encoding="utf-8").read()
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    assert "Quick start" in readme and "run.py" in readme.split("##")[1]


def test_followup_unknown_person_is_a_clear_error(env, monkeypatch, capsys):
    feed(monkeypatch, ["n", "4", "Nobody", "n@example.invalid", "file", "0"])
    assert run.main([]) == 0
    err = capsys.readouterr().err
    assert "AT-E001" in err and "Nobody" in err and "matches several" not in err
