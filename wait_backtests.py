#!/usr/bin/env python3
"""
Poll QuantConnect API until every back-test in backtests.json
finishes; dump final JSON into each child folder as 'results.json'.
"""
import time, json, os, pathlib, requests

QC_TOKEN = os.environ["QC_API_TOKEN"]
HEADERS = {"Authorization": f"Bearer {QC_TOKEN}"}

ROOT  = pathlib.Path(__file__).parent
with open(ROOT / "backtests.json") as f:
    jobs = json.load(f)

pending = dict(jobs)
while pending:
    for child, bt_id in list(pending.items()):
        url = f"https://www.quantconnect.com/api/v2/backtests/read?id={bt_id}"
        r   = requests.get(url, headers=HEADERS)
        j   = r.json()
        status = j["backtest"]["status"]
        if status == "Completed":
            (ROOT / "children" / child / "results.json").write_text(json.dumps(j, indent=2))
            print(f"✅ {child} finished")
            pending.pop(child)
        elif status == "Error":
            print(f"❌ {child} errored: {j}")
            pending.pop(child)
    if pending:
        time.sleep(30)
