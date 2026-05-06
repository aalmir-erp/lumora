"""Format /tmp/findings.json into TEST_RESULTS_HEAVY.md."""
import json
import sys

try:
    with open("/tmp/findings.json") as f:
        d = json.load(f)
except Exception as e:
    print(f"parse failed: {e}", file=sys.stderr)
    sys.exit(0)

md = "# E2E Heavy Test Results\n\n"
md += f"- ✅ Pass: {d.get('pass', 0)}\n"
md += f"- ⚠️ Warn: {d.get('warn', 0)}\n"
md += f"- ❌ Fail: {d.get('fail', 0)}\n"
md += f"- ⏭ Skip: {d.get('skip', 0)}\n\n## Items\n\n"
ICONS = {"pass": "✅", "warn": "⚠️", "fail": "❌", "skip": "⏭"}
for item in d.get("items", []):
    icon = ICONS.get(item.get("status"), "•")
    md += f"- {icon} **[{item.get('id', '?')}] {item.get('name', '?')}**"
    detail = item.get("detail", "")
    if detail:
        md += f" — {detail}"
    md += "\n"

with open("TEST_RESULTS_HEAVY.md", "w") as f:
    f.write(md)
print(f"pass={d.get('pass', 0)} warn={d.get('warn', 0)} fail={d.get('fail', 0)}")
