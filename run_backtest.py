#!/usr/bin/env python3
"""
For every folder in wizard/children/, start a cloud back-test and
store QC 'backtestId' in backtests.json so we can poll later.

Requires env var:
  • QC_API_TOKEN
"""
import os, json, subprocess, pathlib

QC_TOKEN = os.getenv("QC_API_TOKEN")
assert QC_TOKEN, "QC_API_TOKEN not set"

CHILD_DIR = pathlib.Path(__file__).parent / "children"
OUT_F     = pathlib.Path(__file__).parent / "backtests.json"
PROJECT_ID = "23708106"        # ← your QC project ID

records = {}
for child in CHILD_DIR.iterdir():
    if not child.is_dir():
        continue
    print(f"🚀  launching {child.name}")
    cmd = [
        "lean", "cloud", "backtest", str(PROJECT_ID),
        "--push", str(child),
        "--name", child.name,
        "--wait", "--output", str(child / "backtest.json"),
        "--json", "--token", QC_TOKEN,
    ]
    res = subprocess.run(cmd, text=True, capture_output=True)
    if res.returncode != 0:
        print("❌  QC error:", res.stderr.strip())
        continue
    # lean prints json when --json; parse id
    payload = json.loads(res.stdout)
    bt_id = payload["backtestId"]
    records[child.name] = bt_id

with open(OUT_F, "w") as f:
    json.dump(records, f, indent=2)
print(f"💾 wrote {OUT_F}")
