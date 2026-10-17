#!/bin/bash
# Detached benchmark of the OpenCode lane: audits, re-run the 16 CME research issues at a fixed
# per-agent concurrency, sample Mac load every 15 s, then measure and rebuild the CME digest.
# Usage: lane_bench.sh <per-agent concurrency> <queue item> <claude transcript jsonl>
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; B=/Users/jeremyyork/Projects/multica/server/bin/multica
OUT=/Users/jeremyyork/Cosmos/artifacts/multica/efficacy; mkdir -p "$OUT"
C=$1; QN=$2; TR=$3; S="$OUT/samples-$(date +%Y%m%d-%H%M).csv"
p(){ psql -h 127.0.0.1 -p 5442 -U multica -d multica -Atc "$1"; }

# Containment gate: every audit line must pass before any assignment.
AUD=pass
"$DIR/audit_oc_sandbox.sh" >"$OUT/audit-sandbox.txt" 2>&1; awk 'NF && $1!="ok"{f=1} END{exit f}' "$OUT/audit-sandbox.txt" || AUD=fail
"$DIR/audit_multica_stack.sh" >"$OUT/audit-stack.txt" 2>&1; awk 'NF && $1!="ok"{f=1} END{exit f}' "$OUT/audit-stack.txt" || AUD=fail
"$DIR/audit_task_token_scope.sh" >"$OUT/audit-token.txt" 2>&1
awk '/mint PAT \(real\)/ && $1=="REACH"{f=1} END{exit f}' "$OUT/audit-token.txt" || AUD=fail
echo "$(date '+%H:%M:%S') audits $AUD" >>"$OUT/bench.log"
[ "$AUD" = pass ] || exit 1

ids=$($B agent list --output json | python3 -c 'import sys,json; print(" ".join(a["id"] for a in json.load(sys.stdin) if a["name"] in ("OC-Bunny","OC-Longcat")))')
for id in $ids; do $B agent update "$id" --max-concurrent-tasks "$C" >/dev/null; done
SINCE=$(date -u +%Y-%m-%dT%H:%M:%S+00:00)
for n in $(seq 7 22); do $B issue rerun "COSMOS-$n" >/dev/null 2>>"$OUT/bench.log"; done
echo "$(date '+%H:%M:%S') rerun 16 at concurrency $C/agent since $SINCE" >>"$OUT/bench.log"

echo "ts,procs,rss_mb,cpu_pct,free_mb,load1" >"$S"
dl=$(( $(date +%s) + 150*60 ))
while [ "$(date +%s)" -lt "$dl" ]; do
  read -r procs rss cpu < <(ps -axo rss=,%cpu=,command= | awk '/opencode/ && !/awk/ {n++; r+=$1; c+=$2} END{printf "%d %.0f %.1f\n", n, r/1024, c}')
  free=$(vm_stat | awk '/Pages free|Pages inactive/ {gsub("\\.","",$NF); s+=$NF} END{printf "%.0f", s*16384/1048576}')
  echo "$(date +%s),$procs,$rss,$cpu,$free,$(sysctl -n vm.loadavg | awk '{print $2}')" >>"$S"
  open=$(p "select count(*) from agent_task_queue t join issue i on i.id=t.issue_id where i.number between 7 and 22 and t.created_at >= '$SINCE' and t.status not in ('completed','failed','cancelled')")
  [ "${open:-1}" = 0 ] && break
  sleep 15
done
for id in $ids; do $B agent update "$id" --max-concurrent-tasks 2 >/dev/null; done
echo "$(date '+%H:%M:%S') settled; open=$open" >>"$OUT/bench.log"

python3 "$DIR/measure_lane_efficacy.py" --since "$SINCE" --samples "$S" --transcript "$TR" --audits "$AUD" >>"$OUT/bench.log" 2>&1
DEADLINE_MIN=0 "$DIR/cme_options_chain.sh" "$QN" >>"$OUT/bench.log" 2>&1
echo "$(date '+%H:%M:%S') done" >>"$OUT/bench.log"
