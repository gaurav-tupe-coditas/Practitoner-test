"""Build docs/summary.html from real runs (AC-11.5, ADR-ACTIONTRACK-005).

    python tools/build_summary.py            runs pytest, runs the app over notes/, writes docs/summary.html

Everything except BRIEF and OPEN below is measured, not typed. Reuses actiontrack/report.py.
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from actiontrack import report, service  # noqa: E402
from actiontrack.store import Store  # noqa: E402

DEMO_TODAY = date(2026, 10, 1)      # fixed so the page is reproducible (spec: "today" is injectable)

# Hand-written: the original brief against what was delivered.
BRIEF = [
    ("ingest parses every .md note (date, attendees, checkbox items)", "ok", "FR-1, FR-2"),
    ("items stored with owner, task, due date (resolved), source file, status", "ok", "FR-2, FR-4, SQLite"),
    ("list with --owner, --status open|done|overdue, --due-before", "ok", "FR-6"),
    ("done <id>", "ok", "FR-7"),
    ("followup: one email per owner, open and overdue items, never sends", "ok", "FR-8; no send path exists, tested"),
    ("Gmail draft through the Gmail MCP connector", "ok", "claude CLI sink; live drafts created and confirmed unsent (2026-11-24)"),
    ("duplicates across meetings", "ok", "FR-5, ADR-001"),
    ("items with no owner or no due date", "ok", "FR-3, FR-4, flagged in report"),
    ("two people with the same first name", "ok", "flagged ambiguous, never guessed"),
    ("malformed notes skipped and reported, no crash", "ok", "FR-9"),
    ("sample notes/ folder with 30+ files", "ok", "see the notes run below"),
    ("extras asked for later: launcher menu, HTML report, this summary", "ok", "FR-10, FR-11"),
]
OPEN = [
    ("warn", "docs/baseReq.md is truncated", "Behaviour was inferred from notes/ and marked Assumption; to be diffed against the full brief."),
    ("warn", "Assumptions S-5 and S-6", "Awaiting user confirmation."),
    ("info", "Summary freshness", "Rebuild with python tools/build_summary.py after any change."),
]


def _git(*args) -> list[str]:
    try:
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=30)
        return r.stdout.splitlines() if r.returncode == 0 else []
    except (OSError, subprocess.SubprocessError):
        return []


def _read(*parts) -> str:
    try:
        with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def _table(headers, rows) -> str:
    head = "".join(f"<th>{report.esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tablewrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


# ---- measured sections ----

def run_pytest() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = os.path.join(tmp, "junit.xml")
        proc = subprocess.run([sys.executable, "-m", "pytest", "-q", f"--junitxml={xml_path}"],
                              cwd=ROOT, capture_output=True, text=True)
        suite = ET.parse(xml_path).getroot()
        suite = suite if suite.tag == "testsuite" else suite[0]
        cases = [(c.get("classname", ""), c.get("name", ""), "fail" if c.find("failure") is not None or c.find("error") is not None
                  else "skip" if c.find("skipped") is not None else "pass") for c in suite.iter("testcase")]
    return {"exit": proc.returncode, "time": float(suite.get("time", 0)), "cases": cases}


def tests_section(result) -> str:
    if result is None:
        return '<p class="dim">Test run skipped in this build (<code>run_tests=False</code>). Run <code>python tools/build_summary.py</code> for a real result.</p>'
    cases = result["cases"]
    passed = sum(1 for c in cases if c[2] == "pass")
    failed = sum(1 for c in cases if c[2] == "fail")
    by_file: dict[str, list[int]] = {}
    for cls, _, st in cases:
        f = cls.split(".")[1] if "." in cls else cls
        by_file.setdefault(f, [0, 0])[0 if st == "pass" else 1] += 1
    return (report.cards([("Tests", len(cases), "info"), ("Passed", passed, "ok"), ("Failed", failed, "bad" if failed else "ok"),
                          ("Seconds", f'{result["time"]:.1f}', "")])
            + f'<p><code>python -m pytest</code> exit code {result["exit"]} ' + report.badge("green" if result["exit"] == 0 else "RED", "ok" if result["exit"] == 0 else "bad") + "</p>"
            + _table(["Test file", "Passed", "Not passed"], [(report.esc(f), n[0], n[1]) for f, n in sorted(by_file.items())]))


def run_notes(today: date = DEMO_TODAY):
    folder = os.path.join(ROOT, "notes")
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(os.path.join(tmp, "summary.db"))
        try:
            rep = service.ingest(store, folder)
            items = service.list_items(store, today)
        finally:
            store.close()
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".md"))
    return folder, files, rep, items


def notes_section() -> str:
    folder, files, rep, items = run_notes()
    skipped = dict(rep.skipped)
    per_file = {f: 0 for f in files}
    for i in items:
        for s in i.sources:
            per_file[s] = per_file.get(s, 0) + 1
    s = report.stats(items, DEMO_TODAY)
    dedup = [i for i in items if len(i.sources) > 1]
    rows = [(report.esc(f), report.badge("skipped: " + skipped[f], "bad") if f in skipped else report.badge("read", "ok"),
             "-" if f in skipped else per_file.get(f, 0)) for f in files]
    amb = sorted(set(rep.ambiguous))
    return (
        f'<p class="dim">Real run of the app over <code>notes/</code>, as of {DEMO_TODAY.isoformat()} (fixed demo date).</p>'
        + report.cards([("Files", len(files), ""), ("Read", rep.read, "ok"), ("Skipped", len(rep.skipped), "bad"),
                        ("Items", s["total"], "info"), ("Overdue", s["overdue"], "bad"), ("Merged duplicates", len(dedup), "warn"),
                        ("Ambiguous owners", len(amb), "warn"), ("Unassigned", s["unassigned"], "warn")])
        + "<h3>Per file</h3>" + _table(["File", "Result", "Items"], rows)
        + "<h3>Ambiguous owners (flagged, never guessed)</h3>"
        + ('<ul class="clean">' + "".join(f"<li>{report.esc(a)}</li>" for a in amb) + "</ul>" if amb else '<p class="dim">None.</p>')
        + "<h3>Items found in several meetings (deduplicated)</h3>"
        + (_table(["ID", "Owner", "Task", "Seen in"], [(i.id, report.esc(i.owner or "(unassigned)"), report.esc(i.task), report.esc(", ".join(i.sources))) for i in dedup])
           if dedup else '<p class="dim">None.</p>')
        + "<h3>All items</h3>" + report.items_section(items, DEMO_TODAY))


def coverage_section() -> str:
    planned = sorted(set(re.findall(r"^\|\s*(T-\d+)", _read("modules", "actiontrack", "tests.md"), re.M)))
    used: set[str] = set()
    for path in glob.glob(os.path.join(ROOT, "tests", "*.py")):
        with open(path, encoding="utf-8") as fh:
            used |= set(re.findall(r"T-\d+", fh.read()))
    covered = [t for t in planned if t in used]
    missing = [t for t in planned if t not in used]
    grid = "".join(f'<span class="badge b-{"ok" if t in used else "bad"}">{t}</span>' for t in planned)
    return (report.cards([("Planned tests", len(planned), "info"), ("Referenced in tests/", len(covered), "ok"),
                          ("Not referenced", len(missing), "bad" if missing else "ok")])
            + f'<div class="panel"><div class="grid-t">{grid}</div></div>'
            + '<p class="dim">A T-id counts as covered when a file in <code>tests/</code> cites it. Presence, not proof of quality.</p>')


def sdd_section() -> str:
    log = _read("docs", "sdd-log.md")
    stages = re.findall(r"^\|\s*(\d\d:\d\d)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]+?)\s*\|$", log, re.M)
    timeline = '<ul class="tl">' + "".join(
        f"<li><b>{report.esc(t)}</b> {report.badge(stage)} <span class=\"dim\">{report.esc(files)}</span><br>{report.esc(event)}</li>"
        for t, stage, files, event in stages) + "</ul>"
    adrs = []
    for path in sorted(glob.glob(os.path.join(ROOT, "modules", "*", "adr.md"))):
        adrs += re.findall(r"^### (ADR-[A-Z]+-\d+): (.+)$", open(path, encoding="utf-8").read(), re.M)
    for path in sorted(glob.glob(os.path.join(ROOT, "docs", "adr", "ADR-*.md"))):
        first = open(path, encoding="utf-8").readline().lstrip("# ").strip()
        adrs.append((os.path.basename(path)[:9], first))
    commits = [ln.split("\t", 2) for ln in _git("log", "--reverse", "--format=%h\t%ad\t%s", "--date=short")]
    return (f"<h3>Stage log ({len(stages)} entries)</h3>{timeline}"
            f"<h3>Decisions ({len(adrs)} ADRs)</h3>"
            + _table(["ADR", "Decision"], [(report.esc(a), report.esc(b)) for a, b in adrs])
            + f"<h3>Git history ({len(commits)} commits)</h3>"
            + _table(["Commit", "Date", "Subject"], [(f"<code>{report.esc(h)}</code>", report.esc(d), report.esc(s)) for h, d, s in commits if s]
                     or [("-", "-", "git history not available")]))


def brief_section() -> str:
    mark = {"ok": report.badge("delivered", "ok"), "warn": report.badge("partly", "warn")}
    return _table(["Brief item", "Status", "Where"], [(report.esc(t), mark[k], report.esc(w)) for t, k, w in BRIEF])


def open_section() -> str:
    return "<ul class=\"clean\">" + "".join(
        f"<li>{report.badge('open', k)} <b>{report.esc(t)}</b> <span class=\"dim\">{report.esc(d)}</span></li>" for k, t, d in OPEN) + "</ul>"


def build(run_tests: bool = True) -> str:
    result = run_pytest() if run_tests else None
    sections = [("tests", "Tests", tests_section(result)), ("notes", "Run over notes/", notes_section()),
                ("coverage", "Test-plan coverage", coverage_section()), ("sdd", "Spec-driven trail", sdd_section()),
                ("brief", "Brief vs delivered", brief_section()), ("open", "Open items", open_section())]
    body = "".join(f'<section id="{i}"><h2>{report.esc(t)}</h2>{b}</section>' for i, t, b in sections)
    body += "<footer>Generated by tools/build_summary.py from real runs. Nothing was sent anywhere.</footer>"
    return report.page("actiontrack summary", "What was built, how it was checked, and what is still open.",
                       body, toc=[(i, t) for i, t, _ in sections])


def main() -> int:
    out = os.path.join(ROOT, "docs", "summary.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
