#!/usr/bin/env python3
"""Print the Multica + OpenCode lane architecture report (house HTML style) to ~/Downloads.

Every check table is rendered from the latest audit prints in ~/Cosmos/artifacts/multica
(audit-oc-sandbox-*, audit-stack-*, audit-task-token-*); the diagrams are drawn from the
committed layout in scripts/jy. Older prints of the same report are superseded.
Usage: build_lane_architecture_report.py
"""
import html
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ART = Path.home() / "Cosmos/artifacts/multica"
OUT_DIR = Path.home() / "Downloads"
ET = ZoneInfo("America/New_York")
NOW = datetime.now(ET)
E = html.escape


def prints(prefix):
    return sorted(ART.glob(f"{prefix}-*.txt"))


def stamp_of(p):
    d = datetime.strptime(p.stem.rsplit("-", 2)[-2] + p.stem.rsplit("-", 1)[-1], "%Y%m%d%H%M")
    return d.strftime("%b %d, %Y %H:%M ET")


def lines(p):
    return [l.rstrip("\n") for l in p.read_text().splitlines() if l.strip()]


# ---------- SVG helpers ----------
def box(x, y, w, h, title, sub="", cls="n"):
    t = f'<g class="bx {cls}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
    t += f'<text x="{x + 10}" y="{y + 20}" class="bt">{E(title)}</text>'
    for i, s in enumerate(sub.split("|") if sub else []):
        t += f'<text x="{x + 10}" y="{y + 37 + i * 14}" class="bs">{E(s)}</text>'
    return t + "</g>"


def zone(x, y, w, h, label, cls="z"):
    return (f'<g class="{cls}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/>'
            f'<text x="{x + 12}" y="{y + 18}" class="zl">{E(label)}</text></g>')


def arrow(pts, label="", cls="a", lx=None, ly=None):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    t = f'<path d="{d}" class="{cls}" marker-end="url(#m-{cls})"/>'
    if label:
        if lx is None:
            (x1, y1), (x2, y2) = pts[0], pts[1]
            lx, ly = (x1 + x2) / 2 + 4, (y1 + y2) / 2 - 4
        t += f'<text x="{lx}" y="{ly}" class="al">{E(label)}</text>'
    return t


def svg(w, h, body, title):
    marks = "".join(
        f'<marker id="m-{c}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" class="mk-{c}"/></marker>' for c in ("a", "d", "s"))
    return (f'<div class="gwrap"><svg class="dg" viewBox="0 0 {w} {h}" role="img" aria-label="{E(title)}">'
            f"<defs>{marks}</defs>{body}</svg></div>")


# ---------- Diagram 1: complete architecture ----------
def d_overview():
    b = zone(250, 30, 450, 400, "MULTICA STACK · 127.0.0.1 ONLY")
    b += zone(730, 30, 440, 400, "macOS SANDBOX · sandbox-exec oc-sandbox.sb", "zs")
    b += zone(240, 470, 490, 150, "DENIED TO THE AGENT (proven by audit)", "zd")
    b += box(20, 50, 200, 62, "Owner · Chrome", "web UI 127.0.0.1:3000|sign-in code from api.log", "o")
    b += box(20, 150, 200, 76, "Claude Code sessions", "multica CLI, owner PAT|~/.multica/config.json 0600|issue create / assign", "o")
    b += box(20, 270, 200, 76, "launchd LaunchAgent", "com.jeremyyork.multica-stack|RunAtLoad · KeepAlive|throttle 30 s", "o")
    b += box(20, 400, 200, 62, "collect_results.sh", "detached · deadline 40 min|result-<ISSUE>.md UNVERIFIED", "o")
    b += box(20, 520, 200, 62, "~/Cosmos/artifacts/multica", "logs · audits · results|pointers on queue item", "o")
    b += box(270, 55, 190, 62, "Web · next dev :3000", "Next.js · webpack|loopback bind", "n")
    b += box(270, 160, 190, 76, "API · server :8080", "Go · Chi · WebSocket|signup closed · telemetry off|pprof :6060 loopback", "n")
    b += box(270, 290, 190, 62, "PostgreSQL 18 :5442", "~/Projects/multica-pgdata|db multica · trust, loopback", "n")
    b += box(490, 160, 190, 76, "Agent daemon", "multica daemon --foreground|env -i · mdt_ daemon token|mints mat_ per task", "n")
    b += box(490, 290, 190, 62, "stack-supervisor.sh", "start.sh: db, migrate,|API, web (idempotent)", "n")
    b += box(750, 55, 200, 62, "oc-sandbox.sh", "env -i scrub · isolated HOME|per-task data dir", "s")
    b += box(750, 160, 200, 76, "OpenCode 1.18", "run --model <free>|provider: opencode only|CLAUDE.md import disabled", "s")
    b += box(970, 160, 180, 62, "multica CLI (copy)", "~/.oc-sandbox/bin|auth: mat_ task token", "s")
    b += box(750, 290, 200, 62, "~/multica_workspaces", "per-task workdir|read/write allowed", "s")
    b += box(970, 290, 180, 62, "~/.oc-sandbox/home", "opencode.json: share off,|external_directory deny", "s")
    b += box(820, 520, 300, 62, "OpenCode Zen · free models", "space-bunny-free · longcat-2.5-preview-free|zero retention, no training (provider claim)", "x")
    b += box(252, 500, 152, 104, "Owner files", "~/.claude · ~/Jake|~/Cosmos · ~/Worktree|~/.ssh · ~/.multica|Keychains · /Volumes", "d")
    b += box(412, 500, 152, 104, "Loopback ports", "vault 8210 / 8211|postgres 5432 (v4+v6)|multica db 5442|pprof 6060 · 50505", "d")
    b += box(572, 500, 148, 104, "Executables", "security (keychain)|gh · bao · railway|ssh · scp · psql", "d")
    b += arrow([(220, 81), (270, 86)], "", "a")
    b += arrow([(365, 117), (365, 160)], "REST + WS", "a")
    b += arrow([(220, 188), (270, 198)], "owner PAT", "a", 222, 186)
    b += arrow([(365, 236), (365, 290)], "SQL", "a")
    b += arrow([(490, 198), (460, 198)], "", "a")
    b += arrow([(460, 210), (490, 210)], "", "a")
    b += '<text x="463" y="230" class="al">mdt_ · WS</text>'
    b += arrow([(220, 308), (490, 321)], "launch", "a", 226, 304)
    b += arrow([(585, 290), (585, 236)], "exec env -i", "a", 590, 268)
    b += arrow([(680, 186), (750, 86)], "spawn + mat_", "a", 700, 160)
    b += arrow([(850, 117), (850, 160)], "sandbox-exec", "a", 855, 145)
    b += arrow([(950, 191), (970, 191)], "", "a")
    b += arrow([(1060, 160), (1060, 120), (470, 120), (460, 175)], "CLI → 127.0.0.1:8080 (only open port)", "s", 478, 112)
    b += arrow([(850, 236), (850, 290)], "rw", "a")
    b += arrow([(900, 236), (970, 590 - 70)], "HTTPS", "a", 930, 400)
    b += arrow([(760, 236), (700, 500)], "denied", "d", 706, 400)
    b += arrow([(120, 400), (300, 236)], "owner CLI poll", "a", 140, 380)
    b += arrow([(120, 462), (120, 520)], "writes", "a")
    return svg(1190, 640, b, "Complete architecture of the Multica and OpenCode lane")


# ---------- Diagram 2: task trace path ----------
def d_trace():
    cols = [("Claude / Owner", 80), ("API :8080", 260), ("PostgreSQL", 420), ("Daemon", 580),
            ("oc-sandbox.sh", 740), ("OpenCode", 900), ("Zen free model", 1070)]
    b = ""
    for name, x in cols:
        b += f'<g class="bx n"><rect x="{x - 70}" y="16" width="140" height="30" rx="6"/><text x="{x}" y="36" class="bt" text-anchor="middle">{E(name)}</text></g>'
        b += f'<line x1="{x}" y1="46" x2="{x}" y2="610" class="ll"/>'
    X = dict(cols)
    steps = [
        ("Claude / Owner", "API :8080", "1 issue create --assignee OC-Bunny (public text only)"),
        ("API :8080", "PostgreSQL", "2 issue + agent_task_queue row"),
        ("Daemon", "API :8080", "3 claim task (mdt_ daemon token, WS wake-up)"),
        ("API :8080", "PostgreSQL", "4 mint task_token: sha256 stored, TTL bound"),
        ("API :8080", "Daemon", "5 task + mat_ token (task, agent, workspace)"),
        ("Daemon", "oc-sandbox.sh", "6 spawn in per-task workdir, MULTICA_* env"),
        ("oc-sandbox.sh", "OpenCode", "7 env -i, isolated HOME, sandbox-exec"),
        ("OpenCode", "Zen free model", "8 prompt over HTTPS (~8-12k tokens)"),
        ("OpenCode", "API :8080", "9 multica CLI: comment result (mat_)"),
        ("Daemon", "API :8080", "10 task done → task_token rows deleted"),
        ("Claude / Owner", "API :8080", "11 collector polls, writes UNVERIFIED result file"),
    ]
    for i, (a, c, lbl) in enumerate(steps):
        y = 78 + i * 48
        x1, x2 = X[a], X[c]
        cls = "s" if a == "OpenCode" and c == "API :8080" else "a"
        b += arrow([(x1, y), (x2 + (-6 if x2 > x1 else 6), y)], "", cls)
        tx = min(x1, x2) + 8
        b += f'<text x="{tx}" y="{y - 7}" class="al">{E(lbl)}</text>'
    return svg(1160, 620, b, "Trace path of one task")


# ---------- Diagram 3: processes ----------
def d_procs():
    b = box(20, 30, 220, 62, "launchd (gui/501)", "com.jeremyyork.multica-stack|KeepAlive restarts on exit", "o")
    b += box(300, 30, 240, 62, "stack-supervisor.sh", "PATH pinned|start.sh, then exec daemon", "n")
    b += box(600, 10, 250, 50, "pg_ctl → postgres 18", "127.0.0.1:5442 · detached", "n")
    b += box(600, 70, 250, 50, "server/bin/server", "127.0.0.1:8080 · pprof 6060 · nohup", "n")
    b += box(600, 130, 250, 50, "node_modules/.bin/next dev", "127.0.0.1:3000 · nohup", "n")
    b += box(300, 200, 240, 62, "multica daemon --foreground", "replaces the supervisor (exec)|registers runtime: opencode only", "n")
    b += box(600, 210, 250, 62, "per task: oc-sandbox.sh", "→ sandbox-exec → opencode run|exits when the task ends", "s")
    b += box(900, 210, 240, 62, "multica CLI (sandbox copy)", "invoked by the model's tools|mat_ token, :8080 only", "s")
    b += box(20, 200, 220, 62, "collect_results.sh", "detached · registry row|exits at settle or deadline", "o")
    b += arrow([(240, 61), (300, 61)], "", "a")
    b += arrow([(540, 50), (600, 35)], "", "a")
    b += arrow([(540, 61), (600, 95)], "", "a")
    b += arrow([(540, 72), (600, 155)], "", "a")
    b += arrow([(420, 92), (420, 200)], "exec", "a", 426, 150)
    b += arrow([(540, 241), (600, 241)], "", "a")
    b += arrow([(850, 241), (900, 241)], "", "s")
    return svg(1160, 290, b, "Process tree")


# ---------- Diagram 4: containment layers ----------
def d_layers():
    b = ""
    layers = [
        (20, 20, 760, 330, "L1 · macOS sandbox-exec (oc-sandbox.sb): home tree, scratchpads, /Volumes denied; 8 tools denied; loopback default-deny except :8080", "zd"),
        (50, 70, 700, 260, "L2 · oc-sandbox.sh: env -i scrub (no vault or provider keys), isolated HOME, per-task data dir", "zs"),
        (80, 120, 640, 190, "L3 · OpenCode config: opencode provider only, share off, external_directory deny", "z"),
        (110, 170, 580, 120, "L4 · Agent instructions: public material only; otherwise comment BLOCKED", "zo"),
    ]
    for x, y, w, h, lbl, cls in layers:
        b += f'<g class="{cls}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/><text x="{x + 12}" y="{y + 20}" class="zl">{E(lbl)}</text></g>'
    b += box(300, 215, 200, 56, "Free model", "sees only the issue text|and the task workdir", "x")
    b += box(820, 120, 320, 110, "L5 · API authorization (server)", "mat_ task token: one task, deleted at end|human-only: tokens, agent config, env,|MCP servers, skills, workspace admin|(fork patch 23ef8439, probe 16:07 ET)", "n")
    b += arrow([(690, 230), (820, 176)], "only door out: :8080", "s", 752, 250)
    return svg(1160, 370, b, "Containment layers")


# ---------- Diagram 5: network ----------
def d_net():
    b = box(20, 120, 220, 70, "OpenCode (sandboxed)", "network-outbound policy|later rule wins", "s")
    allowed = [("HTTPS to the internet", "opencode.ai model endpoint"), ("127.0.0.1:8080", "Multica API (mat_ token)")]
    denied = [("127.0.0.1:8210 / 8211", "macOS OpenBao vault"), ("127.0.0.1 + ::1 :5432", "shared PostgreSQL 16"),
              ("127.0.0.1:5442", "Multica PostgreSQL 18"), ("127.0.0.1:6060", "API pprof"),
              ("127.0.0.1:50505", "poller"), ("127.0.0.1:3000", "Next dev (open advisories)"), ("every other loopback port", "Lima, Google, others")]
    for i, (t, s) in enumerate(allowed):
        y = 40 + i * 80
        b += box(380, y, 260, 56, t, s, "x")
        b += arrow([(240, 155), (380, y + 28)], "allow", "a", 290, 125 + i * 40)
    for i, (t, s) in enumerate(denied):
        y = 10 + i * 52
        b += box(780, y, 300, 46, t, s, "d")
        b += arrow([(240, 160), (780, y + 23)], "", "d")
    b += '<text x="560" y="330" class="al">deny (localhost:*)</text>'
    return svg(1100, 380, b, "Network policy of the sandbox")


# ---------- tables ----------
def table(head, rows, caption=""):
    t = '<div class="wrap"><table><thead><tr>' + "".join(f"<th>{E(h)}</th>" for h in head) + "</tr></thead><tbody>"
    for r in rows:
        t += "<tr>" + "".join(f"<td{(' class=' + chr(34) + c + chr(34)) if c else ''}>{v}</td>" for v, c in r) + "</tr>"
    t += "</tbody></table></div>"
    return t + (f'<div class="cap">{E(caption)}</div>' if caption else "")


def sandbox_rows(p):
    rows = []
    for l in lines(p):
        st, rest = l[:4].strip(), l[5:].strip()
        verb, _, what = rest.partition(" ")
        pill = "done" if st == "ok" else "failed"
        rows.append(((f'<span class="pill c-{pill}">{E(st.upper())}</span>', ""), (E(verb), "id"), (E(what), "")))
    return rows


def token_rows(before, after):
    def parse(p):
        out = {}
        for l in lines(p):
            if l.startswith(("REACH", "DENY")):
                v, code, rest = l[:5].strip(), l[6:10].strip(), l[11:]
                out[rest[:38].strip()] = (v, code, rest[38:].strip())
        return out
    b, a = parse(before), parse(after)
    rows = []
    for k, (va, ca, route) in a.items():
        vb, cb, _ = b.get(k, ("-", "-", ""))
        cls = lambda v: "done" if v == "DENY" else "running"
        changed = vb != va
        rows.append(((E(k), ""), (E(route.split("?")[0]), "id"),
                     (f'<span class="pill c-{"failed" if vb == "REACH" and changed else cls(vb)}">{vb} {cb}</span>', ""),
                     (f'<span class="pill c-{cls(va)}">{va} {ca}</span>', "")))
    return rows


def main():
    sb, st, tk = prints("audit-oc-sandbox"), prints("audit-stack"), prints("audit-task-token")
    head = subprocess.run(["git", "-C", str(Path(__file__).resolve().parents[2]), "rev-parse", "--short=8", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    stack_rows = [((f'<span class="pill c-{"done" if l.startswith("ok") else "failed"}">{E(l.split()[0].upper())}</span>', ""),
                   (E(l.split(None, 1)[1] if " " in l else ""), "")) for l in lines(st[-1])]
    sbr = sandbox_rows(sb[-1])
    n_ok = sum(1 for l in lines(sb[-1]) if l.startswith("ok"))
    tkr = token_rows(tk[0] if len(tk) > 1 else tk[-1], tk[-1])
    css = CSS
    body = f"""
<header><h1>Multica + OpenCode lane · architecture.</h1>
<div class="sub">Environment enhancement project · printed {NOW:%b %d, %Y %H:%M:%S} ET · fork github.com/jeremyyork/multica branch jy/native-mac at {E(head)} · every check table renders from the audit prints in ~/Cosmos/artifacts/multica</div>
<div class="chips"><span class="chip c-done"><b>{n_ok}</b>sandbox checks passed ({E(stamp_of(sb[-1]))})</span>
<span class="chip c-done"><b>{sum(1 for l in lines(st[-1]) if l.startswith('ok'))}</b>stack checks ok ({E(stamp_of(st[-1]))})</span>
<span class="chip c-done"><b>{sum(1 for r in tkr if 'DENY' in r[3][0])}</b>agent-token routes denied ({E(stamp_of(tk[-1]))})</span>
<span class="chip c-token"><b>$0</b>model spend: free zero-retention models only</span></div></header>
{d_overview()}
<p class="lead">The lane lets Claude sessions hand cheap, public-only research and tooling tasks to free OpenCode models. Multica is the task board and scheduler; its daemon runs each task through a wrapper that strips the environment, swaps in an isolated home and starts OpenCode inside a macOS sandbox. The only way out of the sandbox, besides HTTPS to the model provider, is the Multica API on 127.0.0.1:8080, and the token the agent carries there is bound to one task and refused on every configuration route.</p>

<h2 class="sec">1 · Trace path of one task</h2>
{d_trace()}
<p>Free-model output is UNVERIFIED until the item owner checks the cited sources. The issue text is the whole prompt payload: it is written with public content only, never Cosmos code, paths, item evidence or account names.</p>

<h2 class="sec">2 · Processes and autostart</h2>
{d_procs()}
<ul><li>launchd starts the chain at login and restarts the daemon on exit; Multica's own <code>daemon autostart</code> stays disabled because it cannot carry the sandbox wrapper.</li>
<li>Restart: <code>launchctl kickstart -k gui/$(id -u)/com.jeremyyork.multica-stack</code>. Stop all: <code>launchctl bootout gui/$(id -u)/com.jeremyyork.multica-stack; scripts/jy/stop.sh --db</code>.</li>
<li>Only the OpenCode runtime registers: Codex is pointed at a nonexistent path and Claude is not on the supervisor's PATH.</li></ul>

<h2 class="sec">3 · Containment layers</h2>
{d_layers()}
<h3 class="sec">Sandbox audit · {E(stamp_of(sb[-1]))}</h3>
{table(["Result", "Kind", "Check"], sbr, "scripts/jy/audit_oc_sandbox.sh · every deny has an unsandboxed control that succeeds · " + sb[-1].name)}

<h2 class="sec">4 · Network</h2>
{d_net()}
<p>Loopback is default-deny inside the sandbox since this print's fork head; earlier profiles denied four named ports and left the API's pprof listener, the poller and Next dev reachable.</p>

<h2 class="sec">5 · What the agent's token can do</h2>
<p>Probe method: a five-minute task token is planted for the latest finished task, each route is called with a malformed body (a reachable handler answers 400 and changes nothing), and one real token mint is attempted and revoked. Left column: before the fork patch; right: after.</p>
{table(["Capability", "Route", "Before (" + stamp_of(tk[0]) + ")", "After (" + stamp_of(tk[-1]) + ")"], tkr, "scripts/jy/audit_task_token_scope.sh · " + tk[0].name + " → " + tk[-1].name)}
<div class="callout"><b>Finding, fixed.</b> Upstream Multica v0.6.3 let a task token mint a lasting owner token (201 on POST /api/tokens), then edit agent instructions and models, create agents, change the workspace and invite members. Agent-env and MCP-server routes were already human-only. The fork now applies RequireHumanActor to the token, agent-configuration and workspace-admin routes. Reads of the workspace and issue creation stay open by design: the workspace holds public task text only.</div>

<h2 class="sec">6 · Stack posture · {E(stamp_of(st[-1]))}</h2>
{table(["Result", "Check"], stack_rows, "scripts/jy/audit_multica_stack.sh · " + st[-1].name)}

<h2 class="sec">7 · Residual risks</h2>
<ul><li><b>Web dependencies.</b> pnpm audit (Oct 16, 2026 14:38 ET, pnpm-audit.json): 5 critical, 87 high, 119 moderate, 22 low, among them a Next.js image-optimizer RCE. Mitigation: loopback bind, and the sandbox now refuses :3000. The agent path is the Go daemon; govulncheck on the Go server and daemon found no vulnerabilities (govulncheck.txt).</li>
<li><b>HTTPS egress is open.</b> A model could send the contents of its own workdir anywhere; the workdir holds only the public task text and its own output.</li>
<li><b>Provider retention is a provider claim.</b> Zero retention and no training for the two allowlisted models are read from opencode.ai/docs/zen (Oct 16, 2026), unverified.</li>
<li><b>Workspace reads and issue creation stay open to agents.</b> An agent can read every issue in the Cosmos workspace and create issues that wake other agents; both run under the same sandbox at $0.</li>
<li><b>pprof on :6060.</b> Loopback only and denied to the agent; any local owner process can still read it.</li></ul>

<h2 class="sec">8 · Incident on record</h2>
<p>Oct 16, 2026 14:1x-14:27 ET: two test prompts run before the wrapper existed carried ~/.claude/CLAUDE.md and ~/Jake/*.md (no credential values; Railway IDs, vault paths, two IPv4 addresses and directives) to space-bunny-free. Rotation was not required. The wrapper and the import switch-off were the fix; a trivial prompt now measures about 7.8k input tokens. Memory: incident-opencode-sent-global-instructions-to-free-model-2026-10-16.</p>

<h2 class="sec">9 · Files</h2>
{table(["Path", "Role"], [((E(p), "id"), (E(r), "")) for p, r in [
    ("scripts/jy/native-setup.sh", "PG18 cluster, .env (signup off, telemetry off), install, migrate, build"),
    ("scripts/jy/start.sh · stop.sh", "idempotent start of db, API, web; graceful stop"),
    ("scripts/jy/stack-supervisor.sh", "launchd entry; execs the daemon under env -i"),
    ("scripts/jy/oc-sandbox.sh · oc-sandbox.sb", "the OpenCode wrapper and its sandbox profile"),
    ("scripts/jy/audit_oc_sandbox.sh", "sandbox deny/allow proof"),
    ("scripts/jy/audit_multica_stack.sh", "loopback, signup, telemetry, file modes, connections"),
    ("scripts/jy/audit_task_token_scope.sh", "what a task token can reach"),
    ("scripts/jy/collect_results.sh", "detached result collector"),
    ("scripts/jy/build_lane_architecture_report.py", "this report"),
    ("server/cmd/server/main.go · router.go", "MULTICA_BIND_HOST; human-only routes for task tokens"),
    ("~/Library/LaunchAgents/com.jeremyyork.multica-stack.plist", "autostart"),
]])}
<footer>Trade Secret · Property of Jeremy York · © 2026 · printed {NOW:%b %d, %Y %H:%M:%S} ET · memory: reference-multica-opencode-lane</footer>
"""
    out = OUT_DIR / f"multica-opencode-lane-architecture_{NOW:%Y-%m-%d_%H%M}ET.html"
    out.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Multica OpenCode Architecture</title><style>{css}</style></head><body>
<button class="toggle" type="button" aria-label="Toggle theme" onclick="tg()">◐</button><main>{body}</main>
<script>function tg(){{var r=document.documentElement,d=r.getAttribute('data-theme')==='dark'||(!r.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme: dark)').matches);r.setAttribute('data-theme',d?'light':'dark');try{{localStorage.setItem('theme',r.getAttribute('data-theme'))}}catch(e){{}}}}
try{{var t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t)}}catch(e){{}}</script></body></html>""")
    subprocess.run([str(Path.home() / ".claude/scripts/supersede_report_prints.py"), str(OUT_DIR), "--apply"], check=False,
                   stdout=subprocess.DEVNULL)
    print(out)


CSS = """:root{--bg:#f7f2e7;--panel:#fffaf0;--ink:#2a2620;--muted:#6d6457;--rule:#d9cfbd;--accent:#8a5a14;--soft:#f0e2c4;
--done:#3e6b3a;--running:#2f5d86;--failed:#8c3b2e;--token:#5b4a86;--deny:#8c3b2e;--sbx:#2f5d86;--ext:#3e6b3a;
--serif:"DejaVu Serif",Georgia,serif;--mono:"DejaVu Sans Mono",Menlo,monospace;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#17150f;--panel:#201d16;--ink:#ece4d4;--muted:#a89e8c;
--rule:#3a3428;--accent:#d9a85a;--soft:#3a2d17;--done:#9cc58f;--running:#8db6dc;--failed:#e19a8b;--token:#b9a8e6;--deny:#e19a8b;--sbx:#8db6dc;--ext:#9cc58f;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#17150f;--panel:#201d16;--ink:#ece4d4;--muted:#a89e8c;--rule:#3a3428;--accent:#d9a85a;--soft:#3a2d17;
--done:#9cc58f;--running:#8db6dc;--failed:#e19a8b;--token:#b9a8e6;--deny:#e19a8b;--sbx:#8db6dc;--ext:#9cc58f;color-scheme:dark}
*{box-sizing:border-box}html,body{background:var(--bg)}body{margin:0;color:var(--ink);font:15px/1.55 var(--serif)}
main{max-width:1240px;margin:0 auto;padding:28px 16px 56px}h1{margin:0;font-size:1.8rem}
.sub{font:12px var(--mono);color:var(--muted);margin-top:4px}header{border-bottom:2px solid var(--accent);padding-bottom:14px;margin-bottom:18px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 4px}.chip{font:12px var(--mono);border:1px solid var(--c);color:var(--c);border-radius:999px;padding:3px 10px;background:var(--panel)}
.chip b{font-size:14px;margin-right:4px}.c-done{--c:var(--done)}.c-running{--c:var(--running)}.c-failed{--c:var(--failed)}.c-token{--c:var(--token)}
p,li{text-align:justify;hyphens:auto}p.lead{font-size:15px}ul{margin:6px 0 4px 18px}li{margin:5px 0}code{font:12.5px var(--mono);background:var(--soft);padding:1px 4px;border-radius:4px}
h2.sec{font-size:1.15rem;margin:30px 0 6px;border-bottom:1px solid var(--rule);padding-bottom:4px}h3.sec{font-size:1rem;margin:20px 0 4px}
.gwrap{overflow-x:auto;border:1px solid var(--rule);border-radius:10px;background:var(--panel);padding:8px;margin:10px 0 18px}
svg.dg{display:block;min-width:980px;width:100%;height:auto}svg.dg text{font-family:var(--mono)}
.bx rect{fill:var(--bg);stroke:var(--c);stroke-width:1.4}.bx .bt{font-size:12px;font-weight:bold;fill:var(--ink)}.bx .bs{font-size:10.5px;fill:var(--muted)}
.bx.n{--c:var(--accent)}.bx.o{--c:var(--muted)}.bx.s{--c:var(--sbx)}.bx.x{--c:var(--ext)}.bx.d{--c:var(--deny)}.bx.d rect{stroke-dasharray:5 3}
.z rect,.zs rect,.zd rect,.zo rect{fill:none;stroke-width:1.2}.z rect{stroke:var(--accent)}.zs rect{stroke:var(--sbx);fill:var(--soft);fill-opacity:.35}
.zd rect{stroke:var(--deny);stroke-dasharray:6 4}.zo rect{stroke:var(--done)}.zl{font-size:10.5px;letter-spacing:.06em;fill:var(--muted)}
path.a,path.s,path.d{fill:none;stroke-width:1.5}path.a{stroke:var(--accent)}path.s{stroke:var(--sbx);stroke-width:2}path.d{stroke:var(--deny);stroke-dasharray:5 4}
.mk-a{fill:var(--accent)}.mk-s{fill:var(--sbx)}.mk-d{fill:var(--deny)}.al{font-size:10px;fill:var(--ink)}
.ll{stroke:var(--rule);stroke-dasharray:3 4}
.wrap{overflow-x:auto;border:1px solid var(--rule);border-radius:10px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:7px 10px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}
th{font:11px var(--mono);text-transform:uppercase;letter-spacing:.05em;color:var(--muted);background:var(--soft);white-space:nowrap}
td.id{font-family:var(--mono);font-size:12px;white-space:nowrap}.cap{font:11px var(--mono);color:var(--muted);margin:4px 2px 14px}
.pill{font:11px var(--mono);border-radius:999px;padding:2px 8px;border:1px solid var(--c);color:var(--c);white-space:nowrap}
.callout{border-left:3px solid var(--failed);background:var(--soft);padding:10px 14px;border-radius:0 8px 8px 0;margin:14px 0}
button{appearance:none;background:var(--panel);color:var(--ink);border:1px solid var(--rule);border-radius:8px;height:30px;padding:0 12px;font:13px var(--mono);cursor:pointer}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}.toggle{position:fixed;top:12px;right:12px}
footer{margin-top:36px;border-top:1px solid var(--rule);padding-top:10px;font:11px var(--mono);color:var(--muted)}"""

if __name__ == "__main__":
    main()
