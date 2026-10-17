#!/usr/bin/env python3
"""Measure the Multica + OpenCode free-model lane: delivery, quality, speed, Mac load, Claude overhead.

Usage: measure_lane_efficacy.py --since <ISO instant> --samples <csv> --transcript <claude session jsonl>
Reads every OC-Bunny / OC-Longcat task from the Multica database (all history, plus the benchmark
window that starts at --since), the delivered comment of each benchmark issue, the resource samples
written by lane_bench.sh, and the Claude token usage of the session that built and runs the lane.
Each cited URL is fetched (HEAD, then GET when HEAD is refused) at one request per second per host.
Writes ~/Cosmos/artifacts/multica/efficacy/efficacy-<stamp>.json and the owner HTML in ~/Downloads.

The acceptance gates are pre-registered here, before the benchmark data exists (2026-10-17 11:3x ET);
the lane is a significant advantage only if every gate passes. Shutting it down is the owner's call.
"""
import argparse, csv, html, json, re, statistics, subprocess, sys, time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
from build_lane_architecture_report import CSS  # noqa: E402

ET = ZoneInfo("America/New_York")
NOW = datetime.now(ET)
ART = Path.home() / "Cosmos/artifacts/multica/efficacy"
OUT_DIR = Path.home() / "Downloads"
CLI = str(Path.home() / "Projects/multica/server/bin/multica")
SECTIONS = ["Construction", "Market view", "Payoff", "Greeks", "CME specifics", "Risks", "Documented evidence", "Sources"]
GATES = {  # name: (description, threshold, comparison)
    "delivery_rate": ("Benchmark tasks that delivered a document", 0.80, ">="),
    "section_completeness": ("Required sections present, mean over delivered documents", 0.90, ">="),
    "url_live_rate": ("Cited URLs that resolve (2xx/3xx), over URLs that answered", 0.90, ">="),
    "median_task_minutes": ("Median wall time of a delivered task, minutes", 15.0, "<="),
    "containment": ("Sandbox, stack and task-token audits all pass at benchmark start", 1, ">="),
}


def psql(sql):
    out = subprocess.run(["psql", "-h", "127.0.0.1", "-p", "5442", "-U", "multica", "-d", "multica", "-Atc", sql],
                         capture_output=True, text=True, timeout=60, check=True).stdout.strip()
    return json.loads(out) if out else []


def tasks():
    return psql("""select coalesce(json_agg(r order by r.created_at), '[]') from (
      select a.name agent, i.number, i.title, t.status, t.failure_reason, t.created_at, t.started_at, t.completed_at,
             extract(epoch from (t.completed_at - t.started_at)) secs
      from agent_task_queue t join agent a on a.id = t.agent_id left join issue i on i.id = t.issue_id
      where a.name in ('OC-Bunny','OC-Longcat')) r""")


def last_comment(n):
    r = subprocess.run([CLI, "issue", "comment", "list", f"COSMOS-{n}", "--output", "json"],
                       capture_output=True, text=True, timeout=60)
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return ""
    d = d if isinstance(d, list) else d.get("comments", [])
    agent = [c for c in d if c.get("author_type") == "agent"] or d
    return agent[-1].get("content", "") if agent else ""


def check_urls(urls):
    last, res = defaultdict(float), {}
    for u in urls:
        host = urlparse(u).netloc
        time.sleep(max(0.0, 1.0 - (time.time() - last[host])))
        code = "000"
        for method in (["-I"], []):
            r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-L", "--max-time", "15", "-A", "Mozilla/5.0 (lane-audit)",
                                "-w", "%{http_code}", *method, u], capture_output=True, text=True)
            code = r.stdout.strip() or "000"
            if code not in ("403", "405", "000"):
                break
        last[host] = time.time()
        res[u] = code
    return res


def classify(code):
    c = int(code) if code.isdigit() else 0
    return "live" if 200 <= c < 400 else "dead" if c in (404, 410) else "unknown"


def samples(path):
    rows = list(csv.DictReader(open(path))) if path and Path(path).exists() else []
    f = lambda k: [float(r[k]) for r in rows if r.get(k)]
    return {"n": len(rows), "peak_procs": max(f("procs"), default=None), "peak_rss_mb": max(f("rss_mb"), default=None),
            "peak_cpu_pct": max(f("cpu_pct"), default=None), "min_free_mb": min(f("free_mb"), default=None),
            "peak_load1": max(f("load1"), default=None),
            "rss_per_proc_mb": max((float(r["rss_mb"]) / float(r["procs"]) for r in rows if float(r.get("procs") or 0) > 0), default=None)}


def claude_tokens(path):
    tot, seen = defaultdict(int), set()
    for line in open(path):
        try:
            m = json.loads(line).get("message") or {}
        except ValueError:
            continue
        u, mid = m.get("usage"), m.get("id")
        if not u or mid in seen:
            continue
        seen.add(mid)
        for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
            tot[k] += int(u.get(k) or 0)
    tot["assistant_messages"] = len(seen)
    return dict(tot)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True)
    ap.add_argument("--samples")
    ap.add_argument("--transcript")
    ap.add_argument("--audits", default="unknown", help="pass|fail from lane_bench.sh")
    a = ap.parse_args()
    since = datetime.fromisoformat(a.since)

    allt = tasks()
    bench = [t for t in allt if t["number"] and 7 <= t["number"] <= 22 and datetime.fromisoformat(t["created_at"]) >= since]
    hist = defaultdict(lambda: defaultdict(int))
    for t in allt:
        hist[t["failure_reason"] or t["status"]][t["agent"]] += 1

    docs, all_urls = [], set()
    for t in bench:
        text = last_comment(t["number"]) if t["status"] == "completed" else ""
        ok = t["status"] == "completed" and len(text.split()) >= 200 and "BLOCKED" not in text[:200]
        urls = sorted({u.rstrip(".,);]>*") for u in re.findall(r"https?://[^\s)\]>\"'`]+", text)}) if ok else []
        all_urls.update(urls)
        low = text.lower()
        docs.append({"n": t["number"], "title": t["title"], "agent": t["agent"], "status": t["status"],
                     "failure": t["failure_reason"], "minutes": round(t["secs"] / 60, 1) if t["secs"] else None,
                     "delivered": ok, "words": len(text.split()) if ok else 0,
                     "sections": sum(s.lower() in low for s in SECTIONS) if ok else 0,
                     "unresolved": low.count("unresolved") if ok else 0, "urls": urls})
    codes = check_urls(sorted(all_urls))
    for d in docs:
        k = [classify(codes[u]) for u in d["urls"]]
        d.update(live=k.count("live"), dead=k.count("dead"), unknown=k.count("unknown"))

    dl = [d for d in docs if d["delivered"]]
    live, dead = sum(d["live"] for d in dl), sum(d["dead"] for d in dl)
    m = {
        "delivery_rate": len(dl) / len(docs) if docs else None,
        "section_completeness": statistics.mean(d["sections"] / len(SECTIONS) for d in dl) if dl else None,
        "url_live_rate": live / (live + dead) if live + dead else None,
        "median_task_minutes": statistics.median(d["minutes"] for d in dl if d["minutes"]) if dl else None,
        "containment": 1 if a.audits == "pass" else 0,
    }
    gates = {k: {"desc": g[0], "threshold": g[1], "op": g[2], "value": m[k],
                 "pass": m[k] is not None and (m[k] >= g[1] if g[2] == ">=" else m[k] <= g[1])} for k, g in GATES.items()}
    wall = None
    if bench:
        ends = [datetime.fromisoformat(t["completed_at"]) for t in bench if t["completed_at"]]
        wall = round((max(ends) - min(datetime.fromisoformat(t["created_at"]) for t in bench)).total_seconds() / 60, 1) if ends else None
    rec = {"measured_at": NOW.isoformat(), "since": a.since, "bench_tasks": len(docs), "delivered": len(dl),
           "batch_wall_minutes": wall, "urls_checked": len(codes), "url_codes": codes, "docs": docs, "gates": gates,
           "verdict": "significant advantage" if all(g["pass"] for g in gates.values()) else "not a significant advantage",
           "history": {k: dict(v) for k, v in hist.items()}, "history_total": len(allt),
           "resources": samples(a.samples), "claude_tokens": claude_tokens(a.transcript) if a.transcript else None}
    ART.mkdir(parents=True, exist_ok=True)
    jp = ART / f"efficacy-{NOW:%Y%m%d-%H%M}.json"
    jp.write_text(json.dumps(rec, indent=1, default=str))
    print(jp)
    print(render(rec, jp))


def fmt(v, pct=False):
    if v is None:
        return "UNRESOLVED"
    return f"{v:.0%}" if pct else (f"{v:,.1f}" if isinstance(v, float) else f"{v:,}")


def table(head, rows):
    h = "".join(f"<th>{html.escape(x)}</th>" for x in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def render(r, jp):
    e = html.escape
    pct = {"delivery_rate", "section_completeness", "url_live_rate"}
    g = table(["Gate", "Measured", "Threshold", "Result"],
              [[e(v["desc"]), fmt(v["value"], k in pct), f'{v["op"]} {fmt(v["threshold"], k in pct)}',
                f'<b style="color:var(--{"done" if v["pass"] else "failed"})">{"PASS" if v["pass"] else "FAIL"}</b>']
               for k, v in r["gates"].items()])
    d = table(["Issue", "Strategy", "Agent", "Status", "Min", "Words", "Sections", "URLs live / dead / ?", "UNRESOLVED"],
              [[f'COSMOS-{x["n"]}', e(x["title"] or ""), x["agent"], e(x["failure"] or x["status"]), fmt(x["minutes"]),
                x["words"], f'{x["sections"]}/{len(SECTIONS)}', f'{x.get("live",0)} / {x.get("dead",0)} / {x.get("unknown",0)}',
                x["unresolved"]] for x in r["docs"]])
    h = table(["Outcome", "OC-Bunny", "OC-Longcat"],
              [[e(k), v.get("OC-Bunny", 0), v.get("OC-Longcat", 0)] for k, v in sorted(r["history"].items())])
    s = r["resources"]
    res = table(["Measure", "Value"], [["Samples (15 s)", s["n"]], ["Peak concurrent OpenCode processes", fmt(s["peak_procs"])],
                                        ["Peak OpenCode RSS, MB", fmt(s["peak_rss_mb"])], ["Peak RSS per process, MB", fmt(s["rss_per_proc_mb"])],
                                        ["Peak OpenCode CPU, %", fmt(s["peak_cpu_pct"])], ["Minimum free + inactive memory, MB", fmt(s["min_free_mb"])],
                                        ["Peak 1-minute load", fmt(s["peak_load1"])]])
    c = r["claude_tokens"] or {}
    ct = table(["Claude usage, building + operating session", "Tokens"], [[e(k), f"{v:,}"] for k, v in c.items()])
    body = f"""<h1>OpenCode Lane Efficacy</h1>
<p class="muted">Measured {NOW:%b %d, %Y %H:%M} ET by <code>scripts/jy/measure_lane_efficacy.py</code>; record <code>{e(str(jp))}</code>.
Benchmark: the 16 CME options research issues re-run at 2 tasks per agent (4 concurrent), after the 16-way burst of Oct 16 19:06 ET delivered 0 of 16.</p>
<h2>Verdict: {e(r["verdict"])}</h2>
<p>Gates were pre-registered in the script before the benchmark ran. Delivered {r["delivered"]} of {r["bench_tasks"]};
batch wall time {fmt(r["batch_wall_minutes"])} min; {r["urls_checked"]} distinct cited URLs fetched.
A live URL proves the page exists, not that it states the cited fact; every document stays UNVERIFIED.</p>
{g}<h2>Benchmark tasks</h2>{d}<h2>Mac load during the benchmark</h2>{res}
<h2>All lane tasks since Oct 16 14:27 ET ({r["history_total"]})</h2>{h}
<h2>Claude cost of the lane</h2><p>Every token this Claude session spent on the lane: build, security audit, architecture report,
dispatch, diagnosis and this measurement. The counterfactual (Claude writing the same documents itself) was not measured: UNRESOLVED.</p>{ct}
<footer><p class="muted">Trade Secret · Property of Jeremy York · © 2026</p></footer>"""
    out = OUT_DIR / f"opencode-lane-efficacy_{NOW:%Y-%m-%d_%H%M}ET.html"
    out.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OpenCode Lane Efficacy</title><style>{CSS}</style></head><body>
<button class="toggle" type="button" aria-label="Toggle theme" onclick="tg()">◐</button><main>{body}</main>
<script>function tg(){{var r=document.documentElement,d=r.getAttribute('data-theme')==='dark'||(!r.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme: dark)').matches);r.setAttribute('data-theme',d?'light':'dark');try{{localStorage.setItem('theme',r.getAttribute('data-theme'))}}catch(e){{}}}}
try{{var t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t)}}catch(e){{}}</script></body></html>""")
    subprocess.run([str(Path.home() / ".claude/scripts/supersede_report_prints.py"), str(OUT_DIR), "--apply"],
                   check=False, stdout=subprocess.DEVNULL)
    return out


if __name__ == "__main__":
    main()
