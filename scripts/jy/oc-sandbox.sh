#!/bin/bash
# MULTICA_OPENCODE_PATH target: runs OpenCode with a scrubbed environment, an isolated
# HOME (no ~/.claude, ~/.config/opencode or vault env), and the oc-sandbox.sb profile.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; SB=/Users/jeremyyork/.oc-sandbox
# The profile denies the rest of the home tree; a run from elsewhere (the daemon's version probe) starts in the sandbox home.
case "$PWD" in /Users/jeremyyork/multica_workspaces*|"$SB"*) ;; *) cd "$SB/home" ;; esac
keep=()
while IFS='=' read -r k _; do
  case "$k" in MULTICA_*|OPENCODE_*) keep+=("$k=${!k}");; esac
done < <(env)
exec env -i PATH=/Users/jeremyyork/.oc-sandbox/bin:/Users/jeremyyork/.opencode/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  HOME="$SB/home" XDG_CONFIG_HOME="$SB/home/.config" XDG_DATA_HOME="$SB/home/.local/share" \
  XDG_CACHE_HOME="$SB/home/.cache" XDG_STATE_HOME="$SB/home/.local/state" TMPDIR="$SB/tmp" \
  LANG=en_US.UTF-8 TERM=dumb ${keep[@]+"${keep[@]}"} \
  OPENCODE_DISABLE_CLAUDE_CODE=1 OPENCODE_DISABLE_AUTOUPDATE=1 OPENCODE_DISABLE_DEFAULT_PLUGINS=1 \
  /usr/bin/sandbox-exec -f "$DIR/oc-sandbox.sb" /Users/jeremyyork/.opencode/bin/opencode "$@"
