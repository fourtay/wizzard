#!/usr/bin/env python3
"""
store_results.py – upload QC back-test JSON to Firestore
"""

import os, json, sys
from google.cloud import firestore

RESULTS_FILE_PATH = "backtest-results.json"

# ────────────────────────────────────────────────────────────
#  1. Pull secrets from env
# ────────────────────────────────────────────────────────────
try:
    GCP_SA_KEY_JSON = os.environ["GCP_SA_KEY"]
    BACKTEST_ID     = os.environ["BACKTEST_ID"]
except KeyError as err:
    print(f"❌  Missing env var: {err}")
    sys.exit(1)

# ────────────────────────────────────────────────────────────
#  2. Firestore client
# ────────────────────────────────────────────────────────────
with open("gcp_key.json", "w") as fh:
    fh.write(GCP_SA_KEY_JSON)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
db = firestore.Client()
print("✅  Firestore ready")

# ────────────────────────────────────────────────────────────
#  3. Load results JSON
# ────────────────────────────────────────────────────────────
try:
    with open(RESULTS_FILE_PATH, "r") as fh:
        data = json.load(fh)
except FileNotFoundError:
    print(f"❌  {RESULTS_FILE_PATH} not found")
    sys.exit(1)
except json.JSONDecodeError as err:
    print(f"❌  Bad JSON – {err}")
    sys.exit(1)

# ────────────────────────────────────────────────────────────
#  4. Locate statistics + charts
# ────────────────────────────────────────────────────────────
statistics = charts = None

if "statistics" in data:           # legacy format
    statistics = data["statistics"]
    charts     = data.get("charts", {})
    print("ℹ️  found statistics at root")
elif "backtest" in data and "statistics" in data["backtest"]:
    statistics = data["backtest"]["statistics"]
    charts     = data["backtest"].get("charts", {})
    print("ℹ️  found statistics under backtest → statistics")

if not statistics:
    print("❌  statistics block missing")
    sys.exit(1)

# ────────────────────────────────────────────────────────────
#  5. Upload
# ────────────────────────────────────────────────────────────
doc = {
    "name":        data.get("name", "Unnamed Backtest"),
    "createdAt":   firestore.SERVER_TIMESTAMP,
    "statistics":  statistics,
    "charts":      charts,
}
db.collection("backtest_results").document(BACKTEST_ID).set(doc)
print(f"✅  Uploaded ➜ backtest_results/{BACKTEST_ID}")
