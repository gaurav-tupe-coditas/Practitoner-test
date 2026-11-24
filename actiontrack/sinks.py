"""DraftSink adapters (ADR-0002). Only this module starts subprocesses. No send operation exists."""
from __future__ import annotations

import json
import os
import re
import subprocess

from .draft import Draft

# Gmail connector tool allowed to the headless claude run: create-draft only (S-3: name unverified
# until the connector is authorised; only this constant would change).
GMAIL_CREATE_DRAFT_TOOL = "mcp__claude_ai_Gmail__create_draft"


class SinkError(Exception):
    pass


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "unassigned"


class FileDraftSink:
    def __init__(self, directory: str = "drafts"):
        self.directory = directory

    def create_draft(self, draft: Draft) -> None:
        os.makedirs(self.directory, exist_ok=True)
        path = os.path.join(self.directory, f"{_slug(draft.owner)}-{draft.day.isoformat()}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"to": draft.to, "subject": draft.subject, "body": draft.body}, fh, indent=2)
        self.path = path


class ClaudeGmailDraftSink:
    def __init__(self, runner=subprocess.run):
        self.runner = runner

    def argv(self, draft: Draft) -> list[str]:
        prompt = (
            "Create a Gmail DRAFT only. Do not send anything.\n"
            f"To: {draft.to}\nSubject: {draft.subject}\n\n{draft.body}"
        )
        return ["claude", "-p", prompt, "--allowedTools", GMAIL_CREATE_DRAFT_TOOL]

    def create_draft(self, draft: Draft) -> None:
        try:
            result = self.runner(self.argv(draft), capture_output=True, text=True, timeout=120, shell=False)
        except (OSError, subprocess.SubprocessError) as exc:
            raise SinkError(str(exc)) from exc
        if result.returncode != 0:
            raise SinkError((result.stderr or "claude exited non-zero").strip())
