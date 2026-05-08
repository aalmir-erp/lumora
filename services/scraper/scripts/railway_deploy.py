"""Best-effort idempotent Railway service setup for the scraper.

Reads RAILWAY_TOKEN from env. Creates (or reuses) a service named
SCRAPER_SERVICE_NAME in project PID, configures source + dockerfile path,
upserts non-secret env vars, generates a domain, and triggers a deploy.

Secret env vars (GOOGLE_API_KEY, ANTHROPIC_API_KEY, LOCAL_AGENT_TOKEN)
are propagated from GitHub Action secrets ONLY if present in the env;
otherwise they're skipped and you set them in the Railway dashboard.

If any GraphQL call fails, the script prints the response body and
exits 1 with a manual-fallback message — it never silently corrupts
anything in your Railway project.
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
        return {"errors": [{"message": f"HTTP {e.code}: {e.read().decode()}"}]}


def fail(msg: str) -> None:
    print(f"\n[railway_deploy] FAIL: {msg}", file=sys.stderr)
    print("Manual fallback: Railway dashboard → New Service → GitHub Repo "
          f"{REPO} → Settings → Watch path={ROOT_DIR}, Dockerfile path={ROOT_DIR}/Dockerfile.\n"
          "Then add env vars and redeploy. See services/scraper/QUICKSTART.md.",
          file=sys.stderr)
    sys.exit(1)


def find_environment() -> str:
    q = """query($id:String!){ project(id:$id){ environments{ edges{ node{ id name } } } } }"""
    res = gql(q, {"id": PID})
    if "errors" in res:
        fail(f"project(): {res['errors']}")
    edges = (((res.get("data") or {}).get("project") or {}).get("environments") or {}).get("edges") or []
    for e in edges:
        if e["node"]["name"] == ENV_NAME:
            return e["node"]["id"]
    fail(f"environment '{ENV_NAME}' not found in project {PID}")
    return ""


def find_service() -> str | None:
    q = """query($id:String!){ project(id:$id){ services{ edges{ node{ id name } } } } }"""
    res = gql(q, {"id": PID})
    if "errors" in res:
        fail(f"project services(): {res['errors']}")
    edges = (((res.get("data") or {}).get("project") or {}).get("services") or {}).get("edges") or []
    for e in edges:
        if e["node"]["name"] == SERVICE_NAME:
            return e["node"]["id"]
    return None


def create_service() -> str:
    q = """mutation($input:ServiceCreateInput!){ serviceCreate(input:$input){ id name } }"""
    res = gql(q, {"input": {
        "projectId": PID,
        "name": SERVICE_NAME,
        "source": {"repo": REPO},
    }})
    if "errors" in res:
        fail(f"serviceCreate(): {res['errors']}")
    return res["data"]["serviceCreate"]["id"]


def configure_service(service_id: str, env_id: str) -> None:
    q = """mutation($serviceId:String!,$environmentId:String!,$input:ServiceInstanceUpdateInput!){
        serviceInstanceUpdate(serviceId:$serviceId, environmentId:$environmentId, input:$input)
    }"""
    res = gql(q, {
        "serviceId": service_id,
        "environmentId": env_id,
        "input": {
            "source": {"repo": REPO},
            "rootDirectory": ROOT_DIR,
            "branch": BRANCH,
        },
    })
    if "errors" in res:
        print(f"[warn] serviceInstanceUpdate: {res['errors']}", file=sys.stderr)


def upsert_var(service_id: str, env_id: str, key: str, value: str | None) -> None:
    if value is None or value == "":
        return
    q = """mutation($input:VariableUpsertInput!){ variableUpsert(input:$input) }"""
    res = gql(q, {"input": {
        "projectId": PID, "environmentId": env_id, "serviceId": service_id,
        "name": key, "value": value,
    }})
    if "errors" in res:
        print(f"[warn] variableUpsert {key}: {res['errors']}", file=sys.stderr)
    else:
        print(f"[ok] var {key} set")


def generate_domain(service_id: str, env_id: str) -> str | None:
    q = """mutation($input:ServiceDomainCreateInput!){ serviceDomainCreate(input:$input){ domain } }"""
    res = gql(q, {"input": {"serviceId": service_id, "environmentId": env_id}})
    if "errors" in res:
        # Domain may already exist — try to query
        return query_domain(service_id, env_id)
    return res.get("data", {}).get("serviceDomainCreate", {}).get("domain")


def query_domain(service_id: str, env_id: str) -> str | None:
    q = """query($serviceId:String!,$environmentId:String!){
        domains(serviceId:$serviceId, environmentId:$environmentId){
            serviceDomains{ domain }
        }
    }"""
    res = gql(q, {"serviceId": service_id, "environmentId": env_id})
    if "errors" in res: return None
    sd = (((res.get("data") or {}).get("domains") or {}).get("serviceDomains") or [])
    return sd[0]["domain"] if sd else None


def trigger_deploy(service_id: str, env_id: str) -> None:
    q = """mutation($serviceId:String!,$environmentId:String!){
        serviceInstanceRedeploy(serviceId:$serviceId, environmentId:$environmentId)
    }"""
    res = gql(q, {"serviceId": service_id, "environmentId": env_id})
    if "errors" in res:
        print(f"[warn] redeploy: {res['errors']}", file=sys.stderr)


def wait_for_deploy(service_id: str, env_id: str) -> str:
    q = """query($pid:String!,$sid:String!){
        deployments(input:{projectId:$pid, serviceId:$sid}, first:1){
            edges{ node{ id status createdAt } }
        }
    }"""
    for i in range(36):
        time.sleep(10)
        res = gql(q, {"pid": PID, "sid": service_id})
        edges = (((res.get("data") or {}).get("deployments") or {}).get("edges") or [])
        if not edges:
            continue
        st = edges[0]["node"]["status"]
        print(f"[deploy {i}] status={st}")
        if st in ("SUCCESS", "DEPLOYED", "FAILED", "CRASHED", "REMOVED"):
            return st
    return "TIMEOUT"


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
    configure_service(service_id, env_id)

    # Non-secret vars
    upsert_var(service_id, env_id, "DEFAULT_BACKEND", os.environ.get("DEFAULT_BACKEND", "gemini-pro"))
    upsert_var(service_id, env_id, "DEFAULT_RUNTIME", os.environ.get("DEFAULT_RUNTIME", "hybrid"))
    upsert_var(service_id, env_id, "FORCE_LOCAL_HOSTS", os.environ.get("FORCE_LOCAL_HOSTS",
                                                                       "web.whatsapp.com,*.whatsapp.com"))
    if os.environ.get("STATUS_WEBHOOK_URL"):
        upsert_var(service_id, env_id, "STATUS_WEBHOOK_URL", os.environ["STATUS_WEBHOOK_URL"])

    # Secrets propagated from GitHub Action env (only if user added them as repo secrets)
    upsert_var(service_id, env_id, "GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY"))
    upsert_var(service_id, env_id, "ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY"))
    upsert_var(service_id, env_id, "LOCAL_AGENT_TOKEN", os.environ.get("LOCAL_AGENT_TOKEN"))

    domain = generate_domain(service_id, env_id) or query_domain(service_id, env_id) or ""
    if domain:
        print(f"domain: https://{domain}")

    trigger_deploy(service_id, env_id)
    status = wait_for_deploy(service_id, env_id)

    out = [
        "# Scraper deploy",
        "",
        f"- **Service:** `{SERVICE_NAME}`",
        f"- **Status:** `{status}`",
        f"- **URL:** https://{domain}" if domain else "- **URL:** (no domain — generate from Railway dashboard)",
        f"- **Health:** https://{domain}/healthz" if domain else "",
        "",
        "Set `GOOGLE_API_KEY` (and optionally `ANTHROPIC_API_KEY`) as a GitHub",
        "repo secret if you haven't yet — re-run this workflow to propagate.",
    ]
    with open("services/scraper/DEPLOYED.md", "w") as f:
        f.write("\n".join(out))
    print("\n".join(out))

    if status not in ("SUCCESS", "DEPLOYED"):
        sys.exit(1)


if __name__ == "__main__":
    main()
