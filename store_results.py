#!/usr/bin/env python3
"""
Push a single Lean back-test JSON file (backtest-results*.json) to Firestore.

Handles both old and new QC schemas:
  • {"results": {"statistics": …}}
  • {"backtest": {"statistics": …}}
"""

import json, os, sys, glob
from datetime import datetime
from google.cloud import firestore

# ───────────────────────────────────────────
# 1. Locate newest back-test JSON
# ───────────────────────────────────────────
candidates = sorted(glob.glob("backtest-results*.json"), key=os.path.getmtime)
if not candidates:
    print("❌  No backtest-results*.json found")
    sys.exit(1)

LATEST = candidates[-1]
print(f"📖  Using {LATEST}")

with open(LATEST, "r") as f:
    data = json.load(f)

# ───────────────────────────────────────────
# 2. Extract statistics & charts (works for both schemas)
# ───────────────────────────────────────────
def extract(d: dict):
    if "results" in d:      # old CLI
        return d["results"].get("statistics"), d["results"].get("charts", {})
    if "backtest" in d:     # new CLI
        b = d["backtest"]
        return b.get("statistics"), b.get("charts", {})
    return None, None

statistics, charts = extract(data)
if not statistics:
    print("❌  statistics block missing – aborting")
    print(f"Top-level keys: {list(data.keys())}")
    sys.exit(1)

# ───────────────────────────────────────────
# 3. Firestore – connect
# ───────────────────────────────────────────
GCP_SA_KEY = os.getenv("GCP_SA_KEY")
BACKTEST_ID = os.getenv("BACKTEST_ID")  # set in evolve.yml

if not (GCP_SA_KEY and BACKTEST_ID):
    print("❌  GCP_SA_KEY or BACKTEST_ID env var missing")
    sys.exit(1)

with open("gcp_key.json", "w") as f:
    f.write(GCP_SA_KEY)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"

db = firestore.Client()
print("✅  Firestore ready")

# ───────────────────────────────────────────
# 4. Upload
# ───────────────────────────────────────────
doc = {
    "name": data.get("name", "Unnamed Backtest"),
    "createdAt": firestore.SERVER_TIMESTAMP,
    "statistics": statistics,
    "charts": charts,
}

db.collection("backtest_results").document(BACKTEST_ID).set(doc)
print(f"✨  Uploaded stats for {BACKTEST_ID}")
