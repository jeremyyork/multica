#!/bin/bash
# Proves the OpenCode sandbox: every sensitive read/exec/connect must be DENIED and
# every required one ALLOWED. Prints one line per check; exit 1 on any failure.
DIR="$(cd "$(dirname "$0")" && pwd)"; fail=0
run() { /usr/bin/sandbox-exec -f "$DIR/oc-sandbox.sb" /bin/bash -c "$1" >/dev/null 2>&1; }
deny()  { if run "$2"; then echo "FAIL (allowed) $1"; fail=1; else echo "ok   denied  $1"; fi; }
allow() { if run "$2"; then echo "ok   allowed $1"; else echo "FAIL (denied) $1"; fail=1; fi; }
deny  "read ~/.claude/CLAUDE.md"            "head -c1 /Users/jeremyyork/.claude/CLAUDE.md"
deny  "read ~/.claude memory dir"           "ls /Users/jeremyyork/.claude/projects"
deny  "read ~/Jake/memory.md"               "head -c1 /Users/jeremyyork/Jake/memory.md"
deny  "read ~/.config/opencode"             "ls /Users/jeremyyork/.config/opencode"
deny  "read ~/.openbao"                     "ls /Users/jeremyyork/.openbao"
deny  "list ~/Cosmos"                       "ls /Users/jeremyyork/Cosmos"
deny  "list ~/Worktree"                     "ls /Users/jeremyyork/Worktree"
deny  "read ~/.ssh"                         "ls /Users/jeremyyork/.ssh"
deny  "read ~/.multica (CLI token)"         "ls /Users/jeremyyork/.multica"
deny  "read ~/Library/Keychains"            "ls /Users/jeremyyork/Library/Keychains"
deny  "read ~/Downloads"                    "ls /Users/jeremyyork/Downloads"
deny  "read Claude scratchpads"             "ls /private/tmp/claude-501"
deny  "write ~/ (home)"                     "touch /Users/jeremyyork/.oc-probe"
deny  "exec security (keychain)"            "/usr/bin/security list-keychains"
deny  "exec gh"                             "/opt/homebrew/bin/gh --version"
deny  "exec ssh"                            "/usr/bin/ssh -V"
deny  "connect vault 127.0.0.1:8210"        "exec 3<>/dev/tcp/127.0.0.1/8210"
deny  "connect postgres 127.0.0.1:5432"     "exec 3<>/dev/tcp/127.0.0.1/5432"
deny  "connect multica db 127.0.0.1:5442"   "exec 3<>/dev/tcp/127.0.0.1/5442"
allow "read+write ~/multica_workspaces"     "ls /Users/jeremyyork/multica_workspaces && touch /Users/jeremyyork/multica_workspaces/.oc-probe && rm /Users/jeremyyork/multica_workspaces/.oc-probe"
allow "read+write ~/.oc-sandbox"            "touch /Users/jeremyyork/.oc-sandbox/tmp/p && rm /Users/jeremyyork/.oc-sandbox/tmp/p"
allow "exec opencode (sandbox HOME)"         "cd /Users/jeremyyork/multica_workspaces && HOME=/Users/jeremyyork/.oc-sandbox/home XDG_CONFIG_HOME=/Users/jeremyyork/.oc-sandbox/home/.config XDG_DATA_HOME=/Users/jeremyyork/.oc-sandbox/home/.local/share XDG_CACHE_HOME=/Users/jeremyyork/.oc-sandbox/home/.cache XDG_STATE_HOME=/Users/jeremyyork/.oc-sandbox/home/.local/state /Users/jeremyyork/.opencode/bin/opencode --version"
allow "HTTPS egress (opencode.ai)"          "/usr/bin/curl -sS -o /dev/null --max-time 10 https://opencode.ai"
allow "Multica API 127.0.0.1:8080"          "exec 3<>/dev/tcp/127.0.0.1/8080"
exit $fail
