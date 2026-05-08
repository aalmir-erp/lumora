"""Best-effort idempotent Railway service setup for the scraper.

Reads RAILWAY_TOKEN from env. Creates (or reuses) a service named
SCRAPER_SERVICE_NAME in project PID, configures source + dockerfile path,
upserts non-secret env vars, generates a domain, and triggers a deploy.

Defensive: Railway's GraphQL schema has shipped under slightly different
input/field names over time. Each call has a primary form and a fallback.
On any unrecoverable failure the script writes a clear manual-fallback
message to DEPLOYED.md and exits non-zero so the workflow surface is
unambiguous.

Secrets (GOOGLE_API_KEY, ANTHROPIC_API_KEY, LOCAL_AGENT_TOKEN) are propagated
ONLY if present in the env. They live in GitHub repo secrets, never in code.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.error


API = "https://backboard.railway.com/graphql/v2"
PID = os.environ.get("PROJECT_ID", "15485030-5fc0-44e4-afc7-02f2cdc1d22f")
ENV_NAME = os.environ.get("RAILWAY_ENV_NAME", "production")
SERVICE_NAME = os.environ.get("SCRAPER_SERVICE_NAME", "scraper")
REPO = os.environ.get("GITHUB_REPO", "aalmir-erp/lumora")
BRANCH = os.environ.get("DEPLOY_BRANCH", "main")
ROOT_DIR = "services/scraper"


def gql(query: str, variables: dict | None = None) -> dict:
    token = os.environ["RAILWAY_TOKEN"]
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        API, data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"errors": [{"message": f"HTTP {e.code}: {e.read().decode()[:500]}"}]}
    except Exception as e:
        return {"errors": [{"message": f"network: {e}"}]}


def _err(res: dict) -> str | None:
    if "errors" in res and res["errors"]:
        return "; ".join(str(e.get("message", e)) for e in res["errors"])
    return None


def write_report(status: str, domain: str, extra: str = "") -> None:
    lines = [
        "# Scraper deploy",
        "",
        f"- **Service:** `{SERVICE_NAME}`",
        f"- **Status:** `{status}`",
        f"- **URL:** https://{domain}" if domain else "- **URL:** (no domain — generate from Railway dashboard)",
        f"- **Health:** https://{domain}/healthz" if domain else "",
        f"- **Diagnostics:** https://{domain}/api/diag" if domain else "",
        "",
    ]
    if extra:
        lines += ["", "## Notes", extra, ""]
    lines += [
        "## What to do next",
        "1. Add `GOOGLE_API_KEY` and (optionally) `ANTHROPIC_API_KEY` as **GitHub repo secrets** —",
        "   then re-run the workflow to propagate them to Railway, OR paste them directly into",
        "   the Railway service Variables tab.",
        "2. Visit `/api/diag` on the service URL — it tells you exactly what's missing.",
        "3. On your Windows PC: run `services/scraper/local_agent/install_windows.bat` once,",
        "   then double-click `run_windows.bat` whenever you want the local agent online.",
    ]
    os.makedirs("services/scraper", exist_ok=True)
    with open("services/scraper/DEPLOYED.md", "w") as f:
        f.write("\n".join(lines))


def fail(msg: str, domain: str = "") -> None:
    print(f"\n[railway_deploy] FAIL: {msg}", file=sys.stderr)
    write_report("FAILED", domain, extra=f"Automation failed: `{msg}`. "
                 f"Manual fallback: Railway dashboard → New Service → GitHub Repo `{REPO}` → "
                 f"Settings → Watch path=`{ROOT_DIR}`, Dockerfile path=`{ROOT_DIR}/Dockerfile`. "
                 "Then add env vars from QUICKSTART.md.")
    sys.exit(1)


def find_environment() -> str:
    res = gql("""query($id:String!){ project(id:$id){ environments{ edges{ node{ id name } } } } }""",
              {"id": PID})
    if (e := _err(res)): fail(f"project(): {e}")
    edges = (((res.get("data") or {}).get("project") or {}).get("environments") or {}).get("edges") or []
    for ed in edges:
        if ed["node"]["name"] == ENV_NAME:
            return ed["node"]["id"]
    fail(f"environment '{ENV_NAME}' not found in project {PID}")
    return ""


def find_service() -> str | None:
    res = gql("""query($id:String!){ project(id:$id){ services{ edges{ node{ id name } } } } }""",
              {"id": PID})
    if _err(res): return None
    edges = (((res.get("data") or {}).get("project") or {}).get("services") or {}).get("edges") or []
    for ed in edges:
        if ed["node"]["name"] == SERVICE_NAME:
            return ed["node"]["id"]
    return None


def create_service() -> str:
    """Try modern then legacy serviceCreate input shapes."""
    forms = [
        {"projectId": PID, "name": SERVICE_NAME, "source": {"repo": REPO}},
        {"projectId": PID, "name": SERVICE_NAME, "branch": BRANCH, "source": {"repo": REPO}},
    ]
    last_err = ""
    for inp in forms:
        res = gql("""mutation($input:ServiceCreateInput!){ serviceCreate(input:$input){ id name } }""",
                  {"input": inp})
        if not _err(res):
            return res["data"]["serviceCreate"]["id"]
        last_err = _err(res) or ""
    fail(f"serviceCreate: {last_err}")
    return ""


def configure_service(service_id: str, env_id: str) -> str:
    """Set source + rootDirectory. Try multiple input shapes."""
    forms = [
        {"source": {"repo": REPO}, "rootDirectory": ROOT_DIR, "branch": BRANCH},
        {"source": {"repo": REPO, "rootDirectory": ROOT_DIR}, "branch": BRANCH},
        {"source": {"repo": REPO}, "rootDirectory": ROOT_DIR},
    ]
    last_err = ""
    for inp in forms:
        res = gql("""mutation($s:String!,$e:String!,$i:ServiceInstanceUpdateInput!){
                       serviceInstanceUpdate(serviceId:$s, environmentId:$e, input:$i)
                     }""", {"s": service_id, "e": env_id, "i": inp})
        if not _err(res):
            return ""
        last_err = _err(res) or ""
    return f"warning: serviceInstanceUpdate failed all forms: {last_err}"


def upsert_var(service_id: str, env_id: str, key: str, value: str | None) -> None:
    if not value:
        return
    res = gql("""mutation($i:VariableUpsertInput!){ variableUpsert(input:$i) }""",
              {"i": {"projectId": PID, "environmentId": env_id, "serviceId": service_id,
                     "name": key, "value": value}})
    if e := _err(res):
        print(f"[warn] variableUpsert {key}: {e}", file=sys.stderr)
    else:
        print(f"[ok] var {key} set")


def generate_or_query_domain(service_id: str, env_id: str) -> str | None:
    res = gql("""mutation($i:ServiceDomainCreateInput!){ serviceDomainCreate(input:$i){ domain } }""",
              {"i": {"serviceId": service_id, "environmentId": env_id}})
    if not _err(res):
        d = res.get("data", {}).get("serviceDomainCreate", {}).get("domain")
        if d: return d
    res = gql("""query($s:String!,$e:String!){
                   domains(serviceId:$s, environmentId:$e){ serviceDomains{ domain } }
                 }""", {"s": service_id, "e": env_id})
    if _err(res): return None
    sd = (((res.get("data") or {}).get("domains") or {}).get("serviceDomains") or [])
    return sd[0]["domain"] if sd else None


def trigger_deploy(service_id: str, env_id: str) -> None:
    res = gql("""mutation($s:String!,$e:String!){
                   serviceInstanceRedeploy(serviceId:$s, environmentId:$e)
                 }""", {"s": service_id, "e": env_id})
    if e := _err(res):
        print(f"[warn] redeploy: {e}", file=sys.stderr)


def wait_for_deploy(service_id: str) -> str:
    q = """query($pid:String!,$sid:String!){
             deployments(input:{projectId:$pid, serviceId:$sid}, first:1){
               edges{ node{ id status createdAt } }
             }
           }"""
    last = "UNKNOWN"
    for i in range(48):
        time.sleep(10)
        res = gql(q, {"pid": PID, "sid": service_id})
        edges = (((res.get("data") or {}).get("deployments") or {}).get("edges") or [])
        if not edges:
            continue
        last = edges[0]["node"]["status"]
        print(f"[deploy {i:02d}] status={last}")
        if last in ("SUCCESS", "DEPLOYED", "FAILED", "CRASHED", "REMOVED"):
            return last
    return f"TIMEOUT (last seen: {last})"


def health_check(domain: str) -> bool:
    if not domain: return False
    try:
        with urllib.request.urlopen(f"https://{domain}/healthz", timeout=10) as r:
            ok = b'"ok":true' in r.read()
            print(f"[health] {'OK' if ok else 'NOT OK'}")
            return ok
    except Exception as e:
        print(f"[health] {e}", file=sys.stderr)
        return False


def main() -> None:
    if not os.environ.get("RAILWAY_TOKEN"):
        fail("RAILWAY_TOKEN not set")
    env_id = find_environment()
    print(f"environment: {env_id}")

    service_id = find_service()
    if service_id:
        print(f"service exists: {service_id}")
    else:
        service_id = create_service()
        print(f"created service: {service_id}")

    cfg_warn = configure_service(service_id, env_id)
    if cfg_warn:
        print(cfg_warn, file=sys.stderr)

    upsert_var(service_id, env_id, "DEFAULT_BACKEND", os.environ.get("DEFAULT_BACKEND", "gemini-pro"))
    upsert_var(service_id, env_id, "DEFAULT_RUNTIME", os.environ.get("DEFAULT_RUNTIME", "hybrid"))
    upsert_var(service_id, env_id, "FORCE_LOCAL_HOSTS", os.environ.get("FORCE_LOCAL_HOSTS",
                                                                       "web.whatsapp.com,*.whatsapp.com"))
    upsert_var(service_id, env_id, "STATUS_WEBHOOK_URL", os.environ.get("STATUS_WEBHOOK_URL"))
    upsert_var(service_id, env_id, "GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY"))
    upsert_var(service_id, env_id, "ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY"))
    upsert_var(service_id, env_id, "LOCAL_AGENT_TOKEN", os.environ.get("LOCAL_AGENT_TOKEN"))

    domain = generate_or_query_domain(service_id, env_id) or ""
    if domain:
        print(f"domain: https://{domain}")

    trigger_deploy(service_id, env_id)
    status = wait_for_deploy(service_id)
    healthy = health_check(domain)

    write_report(status, domain,
                 extra="" if healthy else "Service deployed but `/healthz` did not return ok yet — "
                       "Railway may still be warming up; check again in 30s.")
    print(f"\nDONE. status={status}, healthy={healthy}, url=https://{domain}" if domain else f"DONE. status={status}")
    if status not in ("SUCCESS", "DEPLOYED"):
        sys.exit(1)


if __name__ == "__main__":
    main()
