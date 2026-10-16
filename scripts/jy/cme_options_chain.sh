#!/bin/bash
# Detached: wait for the CME options research issues, build the digest, post its pointer on the queue item.
# Usage: cme_options_chain.sh <queue-item-number>
DIR="$(cd "$(dirname "$0")" && pwd)"; Q=/Users/jeremyyork/Worktree/admin-et-remaining/scripts/queue_item.py
KEYS=$(python3 -c 'import json;print(" ".join(k["key"] for k in json.load(open("/Users/jeremyyork/Cosmos/artifacts/multica/cme-options/issues.json"))))')
DEADLINE_MIN=${DEADLINE_MIN:-90} "$DIR/collect_results.sh" $KEYS
HTML=$(python3 "$DIR/cme_options_research.py" build) || { python3 "$Q" set "$1" blocked "digest build failed; see cme-options-chain.log" --by jeremyyork-25; exit 1; }
N=$(grep -c '^| COSMOS-.*delivered |' /Users/jeremyyork/Cosmos/artifacts/multica/cme-options/cme-options-strategies.md)
python3 "$Q" set "$1" owner "CME options digest ready for Fable: ~/Cosmos/artifacts/multica/cme-options/cme-options-strategies.md (owner HTML $HTML); $N of 16 strategy families delivered; free-model text, UNVERIFIED until each cited URL is checked" --by jeremyyork-25
