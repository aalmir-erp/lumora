"""v1.24.85 — generate manifest.json for an e2e-shots run folder.
Used by .github/workflows/e2e-heavy.yml. Args: out_dir."""
import json, os, glob, datetime, sys

out = sys.argv[1] if len(sys.argv) > 1 else "_e2e-shots/unknown"
shots = sorted(os.path.basename(p) for p in glob.glob(os.path.join(out, "*.png")))
findings = {}
try:
    findings = json.load(open("/tmp/findings.json"))
except Exception:
    pass

manifest = {
    "run_number": os.environ.get("GITHUB_RUN_NUMBER", ""),
    "run_id":     os.environ.get("GITHUB_RUN_ID", ""),
    "commit_sha": (os.environ.get("GITHUB_SHA", "") or "")[:8],
    "created_at": datetime.datetime.utcnow().isoformat() + "Z",
    "pass": findings.get("pass", 0),
    "warn": findings.get("warn", 0),
    "fail": findings.get("fail", 0),
    "skip": findings.get("skip", 0),
    "shots": shots,
    "workflow_run_url": (
        "https://github.com/" + os.environ.get("GITHUB_REPOSITORY", "") +
        "/actions/runs/" + os.environ.get("GITHUB_RUN_ID", "")
    ),
}
with open(os.path.join(out, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)
print(f"manifest written: run #{manifest['run_number']} ({len(shots)} shots)")
