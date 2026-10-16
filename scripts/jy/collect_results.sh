#!/bin/bash
# Wait (deadline in minutes) for the given issues to settle, then write their last comments to artifacts.
B=/Users/jeremyyork/Projects/multica/server/bin/multica; OUT=/Users/jeremyyork/Cosmos/artifacts/multica; dl=$(( $(date +%s) + ${DEADLINE_MIN:-40}*60 ))
while [ "$(date +%s)" -lt "$dl" ]; do
  open=0; for k in "$@"; do s=$($B issue get "$k" --output json 2>/dev/null | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status"))'); case $s in in_review|done|blocked|cancelled) ;; *) open=1;; esac; done
  [ $open = 0 ] && break; sleep 30
done
for k in "$@"; do { echo "# $k ($($B issue get "$k" --output json | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status"))'))  UNVERIFIED free-model output"; $B issue comment list "$k" --output json | python3 -c 'import sys,json; d=json.load(sys.stdin); d=d if isinstance(d,list) else d.get("comments",d); print(d[-1].get("content","") if d else "(no comment)")'; } > "$OUT/result-$k.md"; done
echo "$(date '+%H:%M') collected $*" >> "$OUT/collect.log"
