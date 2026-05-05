#!/usr/bin/env bash
# Watch the latest TWA workflow run, dump full logs of any failed step.
# Used for the autonomous fix loop — polls every 30s, exits 0 on success,
# exits 1 with the failing log on failure.
set -euo pipefail
cd "$(dirname "$0")/.."

TOKEN=$(git remote get-url origin | sed 's|.*x-access-token:||' | sed 's|@github.*||')
REPO=aalmir-erp/lumora
WORKFLOW=build-android-twa.yml
HDR=(-H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json")

api() { curl -fsSL "${HDR[@]}" "$@"; }

# Which run are we waiting for? Take the newest by created_at.
RUN_ID=$(api "https://api.github.com/repos/$REPO/actions/workflows/$WORKFLOW/runs?per_page=1" \
  | python3 -c 'import sys,json; print(json.loads(sys.stdin.read())["workflow_runs"][0]["id"])')

echo ">>> Watching run $RUN_ID — https://github.com/$REPO/actions/runs/$RUN_ID"

while :; do
  R=$(api "https://api.github.com/repos/$REPO/actions/runs/$RUN_ID")
  STATUS=$(echo "$R" | python3 -c 'import sys,json; d=json.loads(sys.stdin.read()); print(d["status"])')
  CONCLUSION=$(echo "$R" | python3 -c 'import sys,json; d=json.loads(sys.stdin.read()); print(d["conclusion"] or "")')
  echo ">>> $(date -u +%H:%M:%S) status=$STATUS conclusion=$CONCLUSION"
  if [ "$STATUS" = "completed" ]; then
    if [ "$CONCLUSION" = "success" ]; then
      echo ">>> SUCCESS — artifacts:"
      api "https://api.github.com/repos/$REPO/actions/runs/$RUN_ID/artifacts" \
        | python3 -c 'import sys,json
d = json.loads(sys.stdin.read())
for a in d.get("artifacts", []):
    print(f"  {a[\"name\"]} | {a[\"size_in_bytes\"]} bytes | {a[\"archive_download_url\"]}")'
      exit 0
    fi
    echo ">>> FAILURE — fetching failing step's logs"
    JOB=$(api "https://api.github.com/repos/$REPO/actions/runs/$RUN_ID/jobs" \
      | python3 -c 'import sys,json
d = json.loads(sys.stdin.read())
j = d["jobs"][0]
fail = next((s for s in j["steps"] if s.get("conclusion") == "failure"), None)
print(j["id"], fail["number"] if fail else "", fail["name"] if fail else "")')
    JOB_ID=$(echo "$JOB" | awk "{print \$1}")
    STEP_NUM=$(echo "$JOB" | awk "{print \$2}")
    STEP_NAME=$(echo "$JOB" | cut -d' ' -f3-)
    echo ">>> Failed step #$STEP_NUM: $STEP_NAME"
    echo "================================================================"
    # Grab full job log, extract last 200 lines (the failure region)
    api "https://api.github.com/repos/$REPO/actions/jobs/$JOB_ID/logs" 2>&1 | tail -200 || true
    echo "================================================================"
    exit 1
  fi
  sleep 30
done
