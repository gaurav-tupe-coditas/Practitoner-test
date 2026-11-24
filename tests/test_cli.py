import json
import os
import re
import subprocess
import sys
import time
from datetime import date

import pytest

from actiontrack import service
from actiontrack.draft import Draft, build_draft
from actiontrack.sinks import ClaudeGmailDraftSink, FileDraftSink, SinkError
from conftest import SAMPLE, TODAY, run_cli, write_note

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AT = ["Priya Nair", "Priya Shah", "Rahul Mehta", "Rahul Verma", "Sam Okafor"]


def seed(tmp_path):
    write_note(tmp_path, "1.md", "2026-09-01", AT, [
        "- [ ] Sam to overdue thing by 2026-09-10", "- [ ] Sam to open thing by 2026-10-20", "- [x] Sam to done thing by 2026-09-05",
        "- [ ] Rahul to ambiguous thing", "- [ ] Priya N. to nair thing by 2026-09-10"])
    return str(tmp_path)


def test_bad_folder_and_no_traceback(tmp_path):  # T-02
    code, out, err = run_cli(tmp_path, "ingest", str(tmp_path / "nope"))
    assert code == 1 and "AT-E003" in err and "Traceback" not in err


def test_sample_notes_report(tmp_path):  # T-03
    code, out, err = run_cli(tmp_path, "ingest", SAMPLE)
    assert code == 0 and "Traceback" not in err
    for line in ("skipped 2026-09-09-notes-final-v2.md: empty", "skipped scratch.md: not-text",
                 "skipped 2026-10-03-sales-pipeline.md: bad-date", "skipped untitled.md: no-header"):
        assert line in out
    assert "offsite-draft" not in out                       # .txt ignored silently
    assert "read 31 files" in out


def test_done_via_cli(tmp_path):  # T-23
    seed(tmp_path)
    db = str(tmp_path / "d.db")
    run_cli(tmp_path, "ingest", str(tmp_path), db=db)
    assert run_cli(tmp_path, "done", "1", db=db)[0] == 0
    assert "already done" in run_cli(tmp_path, "done", "1", db=db)[1]
    code, _, err = run_cli(tmp_path, "done", "9999", db=db)
    assert code == 1 and "AT-E001" in err


def test_list_ambiguous_exit2(tmp_path):  # T-22
    seed(tmp_path)
    db = str(tmp_path / "d.db")
    run_cli(tmp_path, "ingest", str(tmp_path), db=db)
    code, out, err = run_cli(tmp_path, "list", "--owner", "Rahul", db=db)
    assert code == 2 and "Rahul Mehta" in err and "Rahul Verma" in err and out == ""
    assert run_cli(tmp_path, "list", "--owner", "Priya Nair", db=db)[0] == 0


class RecordingSink:
    def __init__(self):
        self.drafts = []

    def create_draft(self, draft):
        self.drafts.append(draft)


def test_followup_draft_golden(tmp_path):  # T-24
    seed(tmp_path)
    db = str(tmp_path / "d.db")
    run_cli(tmp_path, "ingest", str(tmp_path), db=db)
    sink = RecordingSink()
    code, out, _ = run_cli(tmp_path, "followup", "Sam", "--to", "sam@example.invalid", db=db, sink_factory=lambda a: sink)
    assert code == 0
    d = sink.drafts[0]
    assert d.to == "sam@example.invalid" and d.subject == "Action items for Sam Okafor: 1 overdue, 1 open"
    assert d.body == (
        "Hi Sam,\n\nHere are your action items from recent meetings.\n\n"
        "Overdue:\n- overdue thing (due 2026-09-10) from 2026-09-01 1.md\n\n"
        "Open:\n- open thing (due 2026-10-20) from 2026-09-01 1.md\n\nPlease reply with any updates.\n")
    assert "done thing" not in d.body


def test_followup_empty_and_ambiguous_and_needs_to(tmp_path):  # T-25, T-26, T-27
    seed(tmp_path)
    db = str(tmp_path / "d.db")
    run_cli(tmp_path, "ingest", str(tmp_path), db=db)
    run_cli(tmp_path, "done", "1", db=db), run_cli(tmp_path, "done", "2", db=db)
    sink = RecordingSink()
    code, out, _ = run_cli(tmp_path, "followup", "Sam", "--to", "sam@example.invalid", db=db, sink_factory=lambda a: sink)
    assert code == 0 and "no draft" in out and sink.drafts == []
    assert run_cli(tmp_path, "followup", "Rahul", "--to", "r@example.invalid", db=db, sink_factory=lambda a: sink)[0] == 2
    assert run_cli(tmp_path, "followup", "Sam", db=db)[0] == 2


def test_no_send_path():  # T-28
    pkg = os.path.join(ROOT, "actiontrack")
    text = "\n".join(open(os.path.join(pkg, f), encoding="utf-8").read() for f in os.listdir(pkg) if f.endswith(".py"))
    assert not re.search(r"\bsend_(message|draft|email)|messages\.send|drafts\.send|def send\b|\.send\(", text)
    assert [m for m in dir(FileDraftSink) if not m.startswith("_")] == ["create_draft"]


class FailingSink:
    def create_draft(self, draft):
        raise SinkError("connector not authorised")


def test_sink_failure_prints_draft(tmp_path):  # T-29
    seed(tmp_path)
    db = str(tmp_path / "d.db")
    run_cli(tmp_path, "ingest", str(tmp_path), db=db)
    code, out, err = run_cli(tmp_path, "followup", "Sam", "--to", "s@example.invalid", db=db, sink_factory=lambda a: FailingSink())
    assert code == 3 and "AT-E004" in err and "Hi Sam," in out


def test_claude_sink_argv_and_failure():  # T-30
    calls = []

    class R:
        returncode = 0
        stderr = ""

    def runner(argv, **kw):
        calls.append((argv, kw))
        return R()

    d = Draft("Sam Okafor", "s@example.invalid", "S", "B", date(2026, 10, 1))
    ClaudeGmailDraftSink(runner).create_draft(d)
    argv, kw = calls[0]
    assert argv[0] == "claude" and kw["shell"] is False
    assert argv[argv.index("--allowedTools") + 1].endswith("create_draft") and "send" not in " ".join(argv).split("Do not send")[0].lower()
    R.returncode, R.stderr = 1, "no auth"
    with pytest.raises(SinkError):
        ClaudeGmailDraftSink(runner).create_draft(d)


def test_file_sink(tmp_path):  # T-31
    d = Draft("Sam Okafor", "s@example.invalid", "Subj", "Body", date(2026, 10, 1))
    FileDraftSink(str(tmp_path / "dr")).create_draft(d)
    data = json.load(open(tmp_path / "dr" / "sam-okafor-2026-10-01.json", encoding="utf-8"))
    assert data == {"to": "s@example.invalid", "subject": "Subj", "body": "Body"}


def test_offline(tmp_path, monkeypatch):  # T-32
    import socket

    def boom(*a, **k):
        raise AssertionError("network used")
    monkeypatch.setattr(socket, "socket", boom)
    seed(tmp_path)
    db = str(tmp_path / "d.db")
    for args in (("ingest", str(tmp_path)), ("list",), ("done", "1")):
        assert run_cli(tmp_path, *args, db=db)[0] == 0


def test_deterministic_and_speed(tmp_path):  # T-33, T-35
    outs = []
    t0 = time.time()
    for n in (1, 2):
        db = str(tmp_path / f"{n}.db")
        run_cli(tmp_path, "ingest", SAMPLE, db=db)
        outs.append(run_cli(tmp_path, "list", db=db, today="2026-10-01")[1])
    assert outs[0] == outs[1] and outs[0].count("\n") > 50
    assert time.time() - t0 < 4          # two ingests; each well under the 2 s budget (NFR-4)


def test_stdlib_only():  # T-36
    pkg = os.path.join(ROOT, "actiontrack")
    allowed = set(sys.stdlib_module_names) | {"actiontrack"}
    for f in os.listdir(pkg):
        if f.endswith(".py"):
            for m in re.findall(r"^(?:from|import)\s+(\.?\w+)", open(os.path.join(pkg, f), encoding="utf-8").read(), re.M):
                assert m.startswith(".") or m in allowed, (f, m)


def test_gitignore_covers_secrets_and_data():  # T-37
    text = open(os.path.join(ROOT, ".gitignore"), encoding="utf-8").read()
    for pat in ("*.db", "drafts/", ".env"):
        assert pat in text


def test_module_entrypoint(tmp_path):
    r = subprocess.run([sys.executable, "-m", "actiontrack", "--db", str(tmp_path / "e.db"), "list"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0 and "no items" in r.stdout
