"""Masking in the conversation exporter (privacy rule in CLAUDE.md). Fake data only."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import export_conversations as ex  # noqa: E402

BS = chr(92)


def test_mask_everything_personal():
    addr = "jordan.rivera" + "@" + "acme-corp.test"
    path = BS.join(["C:", "Users", "Someone-Admin", "Documents"])
    text = f"mail {addr}, Jordan wrote to Rivera at {path} and /c/Users/other/x; Acme won; safe: sam@example.com"
    out = ex.mask(text)
    assert "@acme" not in out and "jordan.rivera" not in out
    for word in ("Jordan", "Rivera", "Someone", "other", "Acme", "acme-corp"):
        assert word not in out, word
    assert "[email masked]" in out
