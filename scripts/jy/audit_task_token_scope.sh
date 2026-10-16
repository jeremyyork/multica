#!/bin/bash
# Probes what an agent's task-scoped token (mat_) can reach on the local Multica API.
# Plants a 5-minute task_token row bound to the latest finished task, sends each probe,
# then deletes the row. Write probes send a malformed body, so a reachable handler
# answers 400 and changes nothing; 401/403 means the route refuses agent tokens.
# One real PAT mint (revoked at once) proves or disproves token escalation.
# Output: one line per probe, "REACH" (agent can use it) or "DENY"; exit 0 always.
set -euo pipefail
API=http://127.0.0.1:8080
PSQL=(psql -h 127.0.0.1 -p 5442 -U multica -d multica -Atq)
TOK="mat_$(openssl rand -hex 20)"
HASH=$(printf %s "$TOK" | shasum -a 256 | cut -d' ' -f1)
ROW=$("${PSQL[@]}" -c "insert into task_token (token_hash, task_id, agent_id, workspace_id, user_id, expires_at)
  select '$HASH', t.id, t.agent_id, a.workspace_id, a.owner_id, now() + interval '5 minutes'
  from agent_task_queue t join agent a on a.id = t.agent_id
  where t.status in ('completed','failed','cancelled') order by t.created_at desc limit 1
  returning id || ' ' || agent_id || ' ' || workspace_id")
read -r ROWID AGENT WS <<<"$ROW"
trap '"${PSQL[@]}" -c "delete from task_token where id = '"'$ROWID'"'" >/dev/null' EXIT
H=(-H "Authorization: Bearer $TOK" -H "X-Workspace-ID: $WS" -H "Content-Type: application/json")

probe() { # label method path [body]
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' -X "$2" "${H[@]}" ${4:+--data "$4"} "$API$3")
  case "$code" in 401|403) v=DENY;; *) v=REACH;; esac
  printf '%-5s %s  %-38s %s %s\n' "$v" "$code" "$1" "$2" "$3"
}
BAD='{'
probe "read own token context"        GET    /api/me
probe "list workspace issues"         GET    "/api/issues?workspace_id=$WS"
probe "list agents"                   GET    /api/agents
probe "list runtimes"                 GET    /api/runtimes
probe "list members"                  GET    "/api/workspaces/$WS/members"
probe "list owner PATs"               GET    /api/tokens
probe "read agent env"                GET    "/api/agents/$AGENT/env"
probe "update agent env"              PUT    "/api/agents/$AGENT/env" "$BAD"
probe "update agent (instr/model)"    PUT    "/api/agents/$AGENT" "$BAD"
probe "create agent"                  POST   /api/agents "$BAD"
probe "add MCP server to agent"       POST   "/api/agents/$AGENT/mcp-servers" "$BAD"
probe "set agent skills"              PUT    "/api/agents/$AGENT/skills" "$BAD"
probe "update workspace"              PATCH  "/api/workspaces/$WS" "$BAD"
probe "invite member"                 POST   "/api/workspaces/$WS/members" "$BAD"
probe "create issue"                  POST   /api/issues "$BAD"
probe "mint PAT (malformed)"          POST   /api/tokens "$BAD"
# Real mint: a 201 proves an agent can convert its task token into a lasting owner token.
resp=$(curl -s -X POST "${H[@]}" --data '{"name":"audit-task-token-probe","expires_in_days":1}' "$API/api/tokens")
pid=$(printf %s "$resp" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("id",""))
except Exception: print("")')
if [ -n "$pid" ]; then
  echo "REACH 201  mint PAT (real)                        token minted id=$pid; revoking"
  "${PSQL[@]}" -c "delete from personal_access_token where id = '$pid'" >/dev/null && echo "      revoked (row deleted)"
else
  echo "DENY  -    mint PAT (real)                        no token returned"
fi
