"""Reviewer demo runs end to end and writes its two files (tools/demo.py)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import demo  # noqa: E402


def test_demo_runs(tmp_path, capsys):
    assert demo.main(["--out", str(tmp_path / "o")]) == 0
    out = capsys.readouterr().out
    assert "skipped scratch.md: not-text" in out and "AT-E002" in out and "draft created for Sam Okafor" in out
    assert (tmp_path / "o" / "report.html").exists()
    assert list((tmp_path / "o" / "drafts").glob("*.html"))
    assert "Traceback" not in out
