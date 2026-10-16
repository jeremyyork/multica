#!/usr/bin/env bash
# Start the native stack (db, API, web) bound to 127.0.0.1, detached; logs under ~/Cosmos/artifacts/multica.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; LOG="$HOME/Cosmos/artifacts/multica"; mkdir -p "$LOG"
PGBIN=/opt/homebrew/opt/postgresql@18/bin; PGDATA="${MULTICA_PGDATA:-$HOME/Projects/multica-pgdata}"
"$PGBIN/pg_ctl" -D "$PGDATA" status >/dev/null 2>&1 || "$PGBIN/pg_ctl" -D "$PGDATA" -l "$PGDATA/server.log" -w start >/dev/null 2>&1 </dev/null
cd "$ROOT"; set -a; . ./.env; set +a; export MULTICA_BIND_HOST=127.0.0.1
(cd server && ./bin/migrate up >/dev/null)
lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t >/dev/null || nohup server/bin/server >"$LOG/api.log" 2>&1 </dev/null &
lsof -nP -iTCP:"$FRONTEND_PORT" -sTCP:LISTEN -t >/dev/null || \
  (cd apps/web && nohup ./node_modules/.bin/next dev --webpack --port "$FRONTEND_PORT" -H 127.0.0.1 </dev/null >"$LOG/web.log" 2>&1 &)
for i in $(seq 1 90); do curl -fsS -o /dev/null "http://127.0.0.1:$PORT/health" 2>/dev/null && curl -fsS -o /dev/null "http://127.0.0.1:$FRONTEND_PORT" 2>/dev/null && { echo "UP api=:$PORT web=:$FRONTEND_PORT"; exit 0; }; sleep 2; done
echo "NOT UP after 180 s; see $LOG"; exit 1
