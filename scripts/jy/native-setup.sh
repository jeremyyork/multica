#!/usr/bin/env bash
# Native (no Docker) setup for this Mac: dedicated PostgreSQL 18 cluster on its own port,
# isolated from the shared postgresql@16 on 5432. Idempotent.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PGBIN=/opt/homebrew/opt/postgresql@18/bin
PGDATA="${MULTICA_PGDATA:-$HOME/Projects/multica-pgdata}"
PGPORT="${MULTICA_PGPORT:-5442}"
ENV_FILE="$ROOT/.env"

# 1. cluster
if [ ! -f "$PGDATA/PG_VERSION" ]; then
  "$PGBIN/initdb" -D "$PGDATA" -U multica --auth=trust -E UTF8 >/dev/null
  echo "listen_addresses = '127.0.0.1'" >> "$PGDATA/postgresql.conf"
  echo "port = $PGPORT" >> "$PGDATA/postgresql.conf"
fi
"$PGBIN/pg_ctl" -D "$PGDATA" status >/dev/null 2>&1 || "$PGBIN/pg_ctl" -D "$PGDATA" -l "$PGDATA/server.log" -w start
"$PGBIN/psql" -h 127.0.0.1 -p "$PGPORT" -U multica -d postgres -Atqc "SELECT 1 FROM pg_database WHERE datname='multica'" | grep -q 1 \
  || "$PGBIN/createdb" -h 127.0.0.1 -p "$PGPORT" -U multica multica

# 2. env file (JWT secret generated once, never printed)
if [ ! -f "$ENV_FILE" ]; then
  cp "$ROOT/.env.example" "$ENV_FILE"
  sed -i '' -E "s#^POSTGRES_PORT=.*#POSTGRES_PORT=$PGPORT#; s#^DATABASE_URL=.*#DATABASE_URL=postgres://multica@127.0.0.1:$PGPORT/multica?sslmode=disable#; s#^JWT_SECRET=.*#JWT_SECRET=$(openssl rand -hex 32)#" "$ENV_FILE"
  grep -q '^DO_NOT_TRACK=' "$ENV_FILE" || echo "DO_NOT_TRACK=1" >> "$ENV_FILE"
fi

# 3. deps (skip browser/electron binaries: disk is tight, desktop not needed) + migrations + binaries
cd "$ROOT"
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 ELECTRON_SKIP_BINARY_DOWNLOAD=1 GOTOOLCHAIN=auto
npx -y pnpm@10.28.2 install --frozen-lockfile
set -a; . "$ENV_FILE"; set +a
(cd server && go run ./cmd/migrate up)
make build
echo "native setup OK: db 127.0.0.1:$PGPORT, binaries in server/bin"
