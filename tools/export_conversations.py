"""Export Claude Code session transcripts to readable, masked text files.

    python tools/export_conversations.py            # the two largest sessions of this project
    python tools/export_conversations.py ID1 ID2    # chosen session ids

Writes docs/conversations/session-<n>-conversation.txt. Everything that identifies a person or an
organisation is masked FULLY (hard rule in CLAUDE.md): e-mail addresses, account and organisation names,
home-folder names. Thinking blocks are not exported. Tool results are shortened.
"""
from __future__ import annotations

import getpass
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "conversations")
MAX_RESULT = 1200

_EMAIL = re.compile(r"[\w.+%-]+@[\w-]+(?:\.[\w-]+)+")
_SEP = chr(92) + "/"                                   # backslash and slash
_HOME = re.compile(r"(?i)(?<=users[" + re.escape(_SEP) + r"])[^" + re.escape(_SEP) + r"\s\"']+")
_SAFE_DOMAINS = ("example.com", "example.invalid", "anthropic.com")
_STOP = {"admin", "info", "team", "test", "mail", "noreply", "support", "hello", "user", "users", "name", "dev", "root"}


def learn_words(text: str) -> set[str]:
    """Names to mask are learned from the data (e-mail parts, OS user), never written in this file."""
    words: set[str] = set()
    for addr in _EMAIL.findall(text):
        local, _, domain = addr.rpartition("@")
        if domain.lower().endswith(_SAFE_DOMAINS):
            continue
        words |= set(re.split(r"[._%+-]+", local)) | set(re.split(r"[.-]+", domain)[:-1])
    try:
        words |= set(re.split(r"[._\W]+", getpass.getuser()))
    except Exception:
        pass
    words |= set(filter(None, os.environ.get("ACTIONTRACK_MASK_WORDS", "").split(",")))
    return {w for w in words if len(w) >= 4 and w.lower() not in _STOP}


def mask(text: str, extra=()) -> str:
    words = learn_words(text) | set(extra)
    text = _EMAIL.sub("[email masked]", text)
    text = _HOME.sub("[user]", text)
    if words:
        text = re.sub("(?i)" + "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True)), "[masked]", text)
    return text


def project_dir() -> str:
    slug = re.sub(r"[^A-Za-z0-9]", "-", ROOT)
    return os.path.join(os.path.expanduser("~"), ".claude", "projects", slug)


def _blocks(content):
    return [{"type": "text", "text": content}] if isinstance(content, str) else (content or [])


def _result_text(block) -> str:
    c = block.get("content")
    if isinstance(c, list):
        c = " ".join(b.get("text", "") for b in c if isinstance(b, dict))
    c = str(c or "")
    return c if len(c) <= MAX_RESULT else c[:MAX_RESULT] + f" ...[{len(c) - MAX_RESULT} more chars cut]"


def render(path: str) -> str:
    out = []
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        kind = d.get("type")
        if kind not in ("user", "assistant"):
            continue
        for b in _blocks((d.get("message") or {}).get("content")):
            t = b.get("type")
            if t == "text" and b.get("text", "").strip():
                out.append(f"[{'USER' if kind == 'user' else 'CLAUDE'}] {b['text'].strip()}")
            elif t == "tool_use":
                out.append(f"[TOOL] {b.get('name')} {json.dumps(b.get('input'), ensure_ascii=False)[:400]}")
            elif t == "tool_result":
                out.append(f"[RESULT] {_result_text(b)}")
    return mask("\n\n".join(out)) + "\n"


def main(ids: list[str]) -> int:
    folder = project_dir()
    if ids:
        files = [os.path.join(folder, f"{i}.jsonl") for i in ids]
    else:
        files = sorted(glob.glob(os.path.join(folder, "*.jsonl")), key=os.path.getsize, reverse=True)[:2]
        files.sort(key=os.path.getmtime)                       # oldest first = session 1
    os.makedirs(OUT, exist_ok=True)
    for n, f in enumerate(files, 1):
        target = os.path.join(OUT, f"session-{n}-conversation.txt")
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(render(f))
        print(f"wrote {os.path.relpath(target, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
