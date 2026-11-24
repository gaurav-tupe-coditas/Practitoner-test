"""Self-contained HTML report (stdlib only, ADR-ACTIONTRACK-005).

Pure functions returning strings. Every value that came from a note goes through `esc`,
because notes are untrusted input. No external fonts, scripts or links.
"""
from __future__ import annotations

import html
from datetime import date

from . import service

CSS = """
:root{--bg:#f5f6f8;--surface:#fff;--ink:#14181f;--muted:#566070;--line:#e1e5eb;--accent:#2457d6;
--ok:#17794a;--ok-bg:#e1f3ea;--warn:#8f5200;--warn-bg:#fcefd6;--bad:#b3261e;--bad-bg:#fbe4e2;--info:#2457d6;--info-bg:#e5ecfb}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f1319;--surface:#171c24;--ink:#e8ecf2;--muted:#9aa5b5;--line:#2a3240;--accent:#7aa2ff;
--ok:#5fd39a;--ok-bg:#12281e;--warn:#f0b455;--warn-bg:#2e2412;--bad:#ff8a80;--bad-bg:#32181a;--info:#7aa2ff;--info-bg:#18233b}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1120px;margin:0 auto;padding:0 16px 56px}
header.top{padding:32px 0 8px}
h1{font-size:28px;line-height:1.2;margin:0 0 6px;letter-spacing:-.01em}
h2{font-size:20px;margin:36px 0 12px;padding-top:8px}
h3{font-size:16px;margin:20px 0 8px}
p.sub{color:var(--muted);margin:0 0 4px}
nav.toc{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 0}
nav.toc a{font-size:13px;color:var(--accent);text-decoration:none;border:1px solid var(--line);background:var(--surface);padding:4px 10px;border-radius:999px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:16px 0}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.card .v{font-size:26px;font-weight:650;line-height:1.1}
.card .l{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin-top:4px}
.card.ok .v{color:var(--ok)}.card.bad .v{color:var(--bad)}.card.warn .v{color:var(--warn)}.card.info .v{color:var(--info)}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px;margin:12px 0}
.badge{display:inline-block;font-size:12px;font-weight:600;padding:2px 9px;border-radius:999px;white-space:nowrap}
.b-ok{background:var(--ok-bg);color:var(--ok)}.b-bad{background:var(--bad-bg);color:var(--bad)}
.b-warn{background:var(--warn-bg);color:var(--warn)}.b-info{background:var(--info-bg);color:var(--info)}
.b-muted{background:var(--line);color:var(--muted)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);background:var(--bg);position:sticky;top:0}
tr:last-child td{border-bottom:0}
tr[hidden]{display:none}
td.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.dim{color:var(--muted)}.it{font-style:italic;color:var(--muted)}
code{font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--bg);border:1px solid var(--line);padding:1px 5px;border-radius:5px}
.controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0 12px}
.controls input{flex:1 1 220px;min-width:0;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink);font:inherit}
.controls button{padding:7px 12px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink);font:inherit;cursor:pointer}
.controls button[aria-pressed="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}
.grid-t{display:grid;grid-template-columns:repeat(auto-fill,minmax(88px,1fr));gap:6px}
.grid-t span{font-size:12px;text-align:center;padding:5px 2px;border-radius:6px}
details{margin:8px 0}summary{cursor:pointer;color:var(--accent)}
ul.clean{margin:6px 0;padding-left:20px}
.tl{list-style:none;margin:0;padding:0;border-left:2px solid var(--line)}
.tl li{padding:2px 0 10px 16px;position:relative}
.tl li::before{content:"";position:absolute;left:-6px;top:8px;width:10px;height:10px;border-radius:50%;background:var(--accent)}
footer{color:var(--muted);font-size:13px;margin-top:40px}
@media (max-width:600px){h1{font-size:23px}th,td{padding:8px}}
"""

_JS = """
(function(){var q=document.getElementById('q');if(!q)return;
var btns=document.querySelectorAll('[data-filter]'),rows=document.querySelectorAll('#items tbody tr'),f='all';
function apply(){var t=q.value.toLowerCase(),n=0;rows.forEach(function(r){
var ok=(f==='all'||r.dataset.status===f||(f==='flag'&&r.dataset.flag==='1'))&&r.dataset.text.indexOf(t)>-1;
r.hidden=!ok;if(ok)n++});document.getElementById('count').textContent=n}
q.addEventListener('input',apply);
btns.forEach(function(b){b.addEventListener('click',function(){f=b.dataset.filter;
btns.forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false')});apply()})});apply()})();
"""


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def badge(text, kind: str = "muted") -> str:
    return f'<span class="badge b-{kind}">{esc(text)}</span>'


def cards(entries) -> str:
    """entries: (label, value, kind) with kind in ok|bad|warn|info|''."""
    inner = "".join(
        f'<div class="card {esc(kind)}"><div class="v">{esc(value)}</div><div class="l">{esc(label)}</div></div>'
        for label, value, kind in entries)
    return f'<div class="cards">{inner}</div>'


def stats(items, today: date) -> dict:
    overdue = [i for i in items if service.is_overdue(i, today)]
    return {
        "total": len(items),
        "overdue": len(overdue),
        "open": sum(1 for i in items if i.status == "open") - len(overdue),
        "done": sum(1 for i in items if i.status == "done"),
        "unassigned": sum(1 for i in items if i.owner_status == "unassigned"),
        "ambiguous": sum(1 for i in items if i.owner_status == "ambiguous"),
        "defaulted": sum(1 for i in items if i.due is None),
    }


def items_section(items, today: date) -> str:
    rows = []
    for i in items:
        overdue = service.is_overdue(i, today)
        status = "overdue" if overdue else i.status
        kind = {"overdue": "bad", "open": "info", "done": "ok"}[status]
        if i.owner_status == "unassigned":
            owner = '<span class="it">(unassigned)</span>'
        elif i.owner_status == "ambiguous":
            owner = f'{esc(i.owner)} {badge("ambiguous", "warn")}'
        else:
            owner = esc(i.owner)
        due = esc(service.effective(i).isoformat()) + (f' {badge("default", "muted")}' if i.due is None else "")
        src = esc(i.sources[0]) + (f' <span class="dim">+{len(i.sources) - 1}</span>' if len(i.sources) > 1 else "") if i.sources else "-"
        flag = "1" if (i.owner_status != "resolved") else "0"
        text = " ".join(str(x or "") for x in (i.id, status, i.owner, i.task, " ".join(i.sources))).lower()
        rows.append(
            f'<tr data-status="{esc(status)}" data-flag="{flag}" data-text="{esc(text)}">'
            f'<td class="num">{i.id}</td><td>{badge(status, kind)}</td><td>{owner}</td>'
            f'<td>{esc(i.task)}</td><td class="num">{due}</td><td>{src}</td></tr>')
    body = "".join(rows) or '<tr><td colspan="6" class="dim">No items.</td></tr>'
    return (
        '<div class="controls"><input id="q" type="search" placeholder="Search person, task or file" aria-label="Search items">'
        '<button data-filter="all" aria-pressed="true">All</button>'
        '<button data-filter="overdue" aria-pressed="false">Overdue</button>'
        '<button data-filter="open" aria-pressed="false">Open</button>'
        '<button data-filter="done" aria-pressed="false">Done</button>'
        '<button data-filter="flag" aria-pressed="false">Needs a look</button>'
        '<span class="dim">Showing <b id="count">%d</b></span></div>'
        '<div class="tablewrap"><table id="items"><thead><tr><th>ID</th><th>Status</th><th>Owner</th><th>Task</th>'
        '<th>Due</th><th>Source</th></tr></thead><tbody>%s</tbody></table></div>' % (len(items), body))


def page(title: str, subtitle: str, body: str, toc=None, extra_js: str = _JS) -> str:
    nav = ""
    if toc:
        nav = '<nav class="toc">' + "".join(f'<a href="#{esc(a)}">{esc(t)}</a>' for a, t in toc) + "</nav>"
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)}</title><style>{CSS}</style></head><body><div class=\"wrap\">"
        f'<header class="top"><h1>{esc(title)}</h1><p class="sub">{esc(subtitle)}</p>{nav}</header>'
        f"{body}</div><script>{extra_js}</script></body></html>")


def render_report(items, today: date) -> str:
    s = stats(items, today)
    body = (
        cards([("Items", s["total"], ""), ("Overdue", s["overdue"], "bad"), ("Open", s["open"], "info"),
               ("Done", s["done"], "ok"), ("Unassigned", s["unassigned"], "warn"), ("Ambiguous owner", s["ambiguous"], "warn")])
        + f'<p class="dim">Overdue means not done and past its due date. {s["defaulted"]} items state no due date; '
          "their due date is the meeting date + 7 days (marked <i>default</i>). “Needs a look” shows items with no owner or an ambiguous owner.</p>"
        + items_section(items, today))
    return page("actiontrack report", f"As of {today.isoformat()}. Generated from the local tracker; nothing here was sent anywhere.", body)
