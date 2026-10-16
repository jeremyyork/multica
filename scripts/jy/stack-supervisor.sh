#!/bin/bash
# launchd entry (com.jeremyyork.multica-stack): bring up db + API + web (idempotent), then run the
# agent daemon in the foreground so launchd restarts it on exit. OpenCode always runs through
# oc-sandbox.sh; the daemon gets a minimal environment (no vault/provider keys).
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$DIR/../.." && pwd)"
export PATH=/Users/jeremyyork/.opencode/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
"$DIR/start.sh" || echo "$(date) start.sh not UP; daemon starts anyway" >&2
exec env -i PATH="$PATH" HOME="$HOME" USER="$USER" LANG=en_US.UTF-8 \
  MULTICA_OPENCODE_PATH="$DIR/oc-sandbox.sh" MULTICA_CODEX_PATH=/nonexistent/codex-disabled \
  "$ROOT/server/bin/multica" daemon start --foreground
