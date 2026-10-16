#!/usr/bin/env bash
# Graceful stop (SIGTERM) of API and web; database left running unless --db.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; set -a; . "$ROOT/.env"; set +a
for p in "$PORT" "$FRONTEND_PORT"; do lsof -nP -iTCP:"$p" -sTCP:LISTEN -t | xargs -r kill -TERM; done
[ "${1:-}" = "--db" ] && /opt/homebrew/opt/postgresql@18/bin/pg_ctl -D "${MULTICA_PGDATA:-$HOME/Projects/multica-pgdata}" -m fast stop
echo stopped
