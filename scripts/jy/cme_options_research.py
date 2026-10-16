#!/usr/bin/env python3
"""CME options strategy research on the OpenCode lane: dispatch one public-research issue per strategy
family, then build ONE document (markdown for Fable, HTML for the owner) from the collected results.

  cme_options_research.py dispatch   create the issues (OC-Bunny / OC-Longcat alternately), record their keys
  cme_options_research.py build      render ~/Cosmos/artifacts/multica/cme-options/cme-options-strategies.md and
                                     ~/Downloads/cme-options-strategies-research_<stamp>ET.html (supersedes)
The issue text is public: no Cosmos code, paths, strategies or account data. Output is UNVERIFIED free-model text.
"""
import html
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_lane_architecture_report import CSS  # noqa: E402  (one house style)

CLI = str(Path(__file__).resolve().parents[2] / "server/bin/multica")
ART = Path.home() / "Cosmos/artifacts/multica"
OUT = ART / "cme-options"
KEYS = OUT / "issues.json"
ET = ZoneInfo("America/New_York")
AGENTS = ["OC-Bunny", "OC-Longcat"]

STRATEGIES = [
    ("Options on futures: mechanics primer", "How CME options on futures differ from equity options: exercise into the underlying future, American vs European styles by product, premium and margining (SPAN / SPAN 2), automatic exercise and abandonment rules, expiration and settlement, weekly/daily expiries, Globex user-defined spreads (UDS) and covered (options-with-futures) spreads."),
    ("Long calls and long puts", "Outright long calls and long puts on CME futures (E-mini S&P 500, Nasdaq-100, WTI crude, gold, Treasury, corn/soy)."),
    ("Covered calls, buy-writes and protective puts", "Covered calls / buy-writes and protective puts using a futures position as the underlying (e.g. E-mini S&P 500 buy-write, producer hedges)."),
    ("Vertical spreads", "Bull call, bear put, bull put (credit) and bear call (credit) vertical spreads on CME futures options."),
    ("Straddles", "Long and short straddles; their use around scheduled events (FOMC, CPI, EIA, USDA reports)."),
    ("Strangles", "Long and short strangles, including short strangles as a premium-selling program and their tail risk."),
    ("Butterflies", "Call and put butterflies, iron butterflies and broken-wing butterflies."),
    ("Condors and iron condors", "Long and short condors and iron condors on CME index, energy and metals options."),
    ("Calendar and diagonal spreads", "Horizontal (calendar) and diagonal spreads, including CME calendar spread options (CSO) in crude oil, natural gas and grains, and the complication that different expiries may reference different futures months."),
    ("Ratio spreads and backspreads", "Ratio call/put spreads (front spreads) and ratio backspreads."),
    ("Collars, fences, risk reversals and seagulls", "Hedger structures: zero-cost collars, three-way fences/seagulls, risk reversals, as used by producers and consumers in energy, metals and agriculture."),
    ("Synthetics, conversions, reversals and box spreads", "Put-call parity on futures options, synthetic long/short futures, conversions and reversals, box spreads (including box spreads as financing), and what limits these arbitrages on CME."),
    ("Volatility trading: gamma scalping, skew and CVOL", "Delta-hedged option positions (long-gamma scalping, short-gamma premium harvest), skew/smile trades, the volatility risk premium on futures options, and the CME Group Volatility Index (CVOL) methodology."),
    ("Short-dated options: weeklies and daily (0DTE)", "CME weekly and daily-expiry options on E-mini S&P 500 and Nasdaq-100, WTI weeklies and Treasury weeklies: contract mechanics, strategies traders use with them, and event trades."),
    ("Interest-rate options: SOFR, mid-curves, Treasury futures options", "SOFR options and SOFR mid-curve options, options on Treasury futures (ZT/ZF/ZN/ZB/UB): typical structures (cap/floor analogues, curve and policy-path trades, weekly options around FOMC) and their mechanics."),
    ("Spread and intercommodity options", "CME-listed spread options: crack spread options, calendar spread options, and agricultural/intercommodity spread options; how they price and why hedgers use them."),
]

BRIEF = """Public research task: {title}.

Scope: {scope}

Use ONLY public sources you actually read now: CME Group (cmegroup.com contract specs, education pages, rulebook), OCC "Characteristics and Risks of Standardized Options", CFTC/SEC, exchange white papers, peer-reviewed papers or standard textbooks (cite them). Put the URL and the read date (today) beside every fact. Never invent a number: a figure not read from a cited source is not written; write UNRESOLVED where no source states a fact.

Post ONE comment, markdown, at most about 1500 words, beginning with the heading "## {title}", with these sections:
1. Construction (legs, ratios, strikes, expiries)
2. Market view and when it is used
3. Payoff at expiry: max profit, max loss, breakeven formulas (symbolic, with premium terms)
4. Greeks profile (sign of delta, gamma, theta, vega over the life)
5. CME specifics: which CME products it is commonly applied to (product names and codes from CME specs), exercise style, expiry cycle, how it is entered on Globex (UDS / covered spreads), margin treatment (SPAN / SPAN 2, qualitative unless CME states a figure)
6. Risks: assignment/early exercise, pin risk, gap risk, liquidity, margin calls, tail risk
7. Documented evidence: published empirical studies on its performance (author, year, title, URL; summarize the finding as the paper states it)
8. Sources (numbered list of URLs with read date)

Do not run code that touches anything outside this workdir. If the task looks unsafe for a public free model, comment "BLOCKED: not safe for a free model" instead."""


def cli(*args, stdin=None):
    r = subprocess.run([CLI, *args], input=stdin, capture_output=True, text=True, check=True)
    return r.stdout


def dispatch():
    OUT.mkdir(parents=True, exist_ok=True)
    ids = {a["name"]: a["id"] for a in json.loads(cli("agent", "list", "--output", "json"))}
    for a in AGENTS:
        cli("agent", "update", ids[a], "--max-concurrent-tasks", "8")
    keys = []
    for i, (title, scope) in enumerate(STRATEGIES):
        body = BRIEF.format(title=title, scope=scope)
        out = json.loads(cli("issue", "create", "--title", f"CME options research: {title}", "--description-stdin",
                             "--assignee", AGENTS[i % 2], "--output", "json", stdin=body))
        keys.append({"key": out.get("identifier") or out.get("key"), "title": title, "agent": AGENTS[i % 2]})
        print(keys[-1]["key"], AGENTS[i % 2], title)
    KEYS.write_text(json.dumps(keys, indent=1))


# ---------- minimal markdown -> HTML (headings, tables, lists, links, bold, code, paragraphs) ----------
def inline(s):
    s = html.escape(s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"(?<![\"'>=])(https?://[^\s<)|]+)", r'<a href="\1">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def md_html(md):
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            hdr = [c.strip() for c in l.strip().strip("|").split("|")]
            out.append('<div class="wrap"><table><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in hdr) + "</tr></thead><tbody>")
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                out.append("<tr>" + "".join(f"<td>{inline(c.strip())}</td>" for c in lines[i].strip().strip("|").split("|")) + "</tr>")
                i += 1
            out.append("</tbody></table></div>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", l)
        if m:
            lvl = min(len(m.group(1)) + 1, 4)
            out.append(f'<h{lvl} class="sec">{inline(m.group(2))}</h{lvl}>')
        elif re.match(r"^\s*([-*]|\d+\.)\s+", l):
            tag = "ol" if re.match(r"^\s*\d+\.", l) else "ul"
            out.append(f"<{tag}>")
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                out.append("<li>" + inline(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i])) + "</li>")
                i += 1
            out.append(f"</{tag}>")
            continue
        elif l.strip():
            out.append(f"<p>{inline(l)}</p>")
        i += 1
    return "\n".join(out)


def build():
    keys = json.loads(KEYS.read_text())
    now = datetime.now(ET)
    parts, rows = [], []
    for k in keys:
        f = ART / f"result-{k['key']}.md"
        raw = f.read_text() if f.exists() else f"# {k['key']} (not collected)\n"
        first, _, body = raw.partition("\n")
        status = re.search(r"\(([^)]+)\)", first)
        st = status.group(1) if status else "unknown"
        ok = st in ("in_review", "done") and "BLOCKED" not in body and "exited with error" not in body
        rows.append((k, st, ok))
        parts.append((k, st, ok, body.strip() if ok else f"_No usable result: status {st}. {body.strip()[:200]}_"))
    n_ok = sum(1 for r in rows if r[2])
    md = [f"# CME options trading strategies: research digest for Fable",
          f"Printed {now:%b %d, %Y %H:%M:%S} ET. {n_ok} of {len(rows)} strategy families delivered. "
          "Source: OpenCode free-model agents on the Multica lane, public sources only. "
          "EVERY STATEMENT IS UNVERIFIED free-model output until its cited URL is checked; nothing here is a Cosmos result.", ""]
    md += ["| Issue | Agent | Strategy family | Status |", "|---|---|---|---|"]
    md += [f"| {k['key']} | {k['agent']} | {k['title']} | {'delivered' if ok else st} |" for k, st, ok in rows]
    for k, st, ok, body in parts:
        md += ["", f"<!-- {k['key']} · {k['agent']} · {st} -->", body if body.startswith("## ") or not ok else f"## {k['title']}\n\n{body}"]
    md_text = "\n".join(md) + "\n"
    (OUT / "cme-options-strategies.md").write_text(md_text)
    body_html = md_html(md_text.split("\n", 2)[2])
    toc = "".join(f'<li>{html.escape(k["title"])} <span class="pill c-{"done" if ok else "failed"}">{html.escape(k["key"])} · {"delivered" if ok else html.escape(st)}</span></li>'
                  for k, st, ok in rows)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CME Options Strategies</title><style>{CSS} h3.sec{{border-bottom:1px solid var(--rule);padding-bottom:4px;margin-top:34px}} a{{color:var(--accent)}}</style></head><body><main>
<header><h1>CME options trading strategies · research digest.</h1>
<div class="sub">Printed {now:%b %d, %Y %H:%M:%S} ET · OpenCode free-model agents (Multica lane), public sources only · markdown for Fable: ~/Cosmos/artifacts/multica/cme-options/cme-options-strategies.md</div>
<div class="chips"><span class="chip c-done"><b>{n_ok}</b>of {len(rows)} strategy families delivered</span><span class="chip c-failed"><b>UNVERIFIED</b>until each cited URL is checked</span></div></header>
<div class="callout"><b>Status of this text.</b> Every statement below was written by a free model from public sources and is unverified until its cited source is read. It holds no Cosmos result and no performance figure of ours.</div>
<ol>{toc}</ol>
{body_html}
<footer>Trade Secret · Property of Jeremy York and Tomer Condon-Siegal · © 2026 · printed {now:%b %d, %Y %H:%M:%S} ET</footer></main></body></html>"""
    out = Path.home() / "Downloads" / f"cme-options-strategies-research_{now:%Y-%m-%d_%H%M}ET.html"
    out.write_text(page)
    subprocess.run([str(Path.home() / ".claude/scripts/supersede_report_prints.py"), str(out.parent), "--apply"],
                   stdout=subprocess.DEVNULL, check=False)
    print(out)


if __name__ == "__main__":
    {"dispatch": dispatch, "build": build}[sys.argv[1]]()
