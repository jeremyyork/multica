#!/bin/bash
# Stack exposure audit: listeners loopback-only, signup closed, telemetry off, token file private.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; fail=0
chk() { if eval "$2"; then echo "ok   $1"; else echo "FAIL $1"; fail=1; fi; }
pids=$(pgrep -f "multica-pgdata|server/bin/server|next dev|multica daemon" | tr '\n' ',')
pub=$(lsof -nP -a -p "${pids%,}" -iTCP -sTCP:LISTEN 2>/dev/null | awk 'NR>1{print $9}' | grep -vE '^(127\.0\.0\.1|\[::1\]|localhost):' )
chk "every Multica listener is loopback-only" '[ -z "$pub" ]'
[ -n "$pub" ] && echo "     public: $pub"
chk "ALLOW_SIGNUP=false in .env" 'grep -q "^ALLOW_SIGNUP=false" "$ROOT/.env"'
chk "DO_NOT_TRACK=1 in .env" 'grep -q "^DO_NOT_TRACK=1" "$ROOT/.env"'
chk "MULTICA_DEV_VERIFICATION_CODE unset" '! grep -qE "^MULTICA_DEV_VERIFICATION_CODE=.+" "$ROOT/.env"'
chk "posthog key empty (no product analytics)" 'curl -s http://127.0.0.1:8080/api/config | grep -q "\"posthog_key\":\"\""'
chk "~/.multica/config.json mode 600" '[ "$(stat -f %Lp ~/.multica/config.json)" = 600 ]'
chk ".env mode 600" '[ "$(stat -f %Lp "$ROOT/.env")" = 600 ]'
est=$(lsof -nP -a -p "${pids%,}" -iTCP -sTCP:ESTABLISHED 2>/dev/null | awk 'NR>1{print $9}' | grep -vE '127\.0\.0\.1|\[::1\]|localhost' | sort -u)
chk "no non-loopback connections from the stack (snapshot)" '[ -z "$est" ]'
[ -n "$est" ] && echo "     outbound: $est"
exit $fail
