#!/usr/bin/env python3
"""
store_results.py
----------------
Reads Lean’s back-test JSON (backtest-results.json) and pushes the key
statistics + charts to Google Firestore.

• Expects the following env vars (already set by the workflow):
    - BACKTEST_ID   – document id to use in the collection
    - GCP_SA_KEY    – service-account JSON (base64-safe string)

• Firestore collection: backtest_results
"""

import json
import os
import sys
from pathlib import Path

from google.cloud import firestore

# ── Settings ──────────────────────────────────────────────────────────────
RESULTS_FILE_PATH = Path("backtest-results.json")

# ── Grab secrets ──────────────────────────────────────────────────────────
try:
    GCP_SA_KEY_JSON = os.environ["GCP_SA_KEY"]
    BACKTEST_ID = os.environ["BACKTEST_ID"]
except KeyError as missing:
    print(f"❌  Required env var not set: {missing.args[0]}")
    sys.exit(1)

# ── Firestore auth ────────────────────────────────────────────────────────
try:
    with open("gcp_key.json", "w") as fh:
        fh.write(GCP_SA_KEY_JSON)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
    db = firestore.Client()
    print("✅  Firestore ready")
except Exception as exc:
    print(f"❌  Firestore auth failed: {exc}")
    sys.exit(1)

# ── Load JSON ─────────────────────────────────────────────────────────────
print("📖  Parsing backtest JSON …")
if not RESULTS_FILE_PATH.exists():
    print(f"❌  {RESULTS_FILE_PATH} not found")
    sys.exit(1)

try:
    results_json = json.loads(RESULTS_FILE_PATH.read_text())
except json.JSONDecodeError as exc:
    print(f"❌  Invalid JSON: {exc}")
    sys.exit(1)

# ── Helpers to locate statistics / charts anywhere in the tree ───────────
def find_stats(node: dict):
    """Depth-first search for the statistics dict, no matter where Lean put it."""
    if not isinstance(node, dict):
        return None
    # Heuristic: a real stats block contains several well-known keys
    REQUIRED_KEYS = {"Total Fees", "Net Profit", "Sharpe Ratio"}
    if REQUIRED_KEYS.intersection(node.keys()) and len(node) > 5:
        return node
    for v in node.values():
        if isinstance(v, dict):
            found = find_stats(v)
            if found:
                return found
    return None

def find_charts(node: dict):
    if not isinstance(node, dict):
        return None
    if "charts" in node and isinstance(node["charts"], dict):
        return node["charts"]
    for v in node.values():
        if isinstance(v, dict):
            found = find_charts(v)
            if found is not None:
                return found
    return {}

statistics = find_stats(results_json)
charts      = find_charts(results_json) or {}

if not statistics:
    print("❌  statistics block missing")
    print("Top-level keys:", list(results_json.keys()))
    sys.exit(1)

# Back-test name, if present
name = (
    results_json.get("name")
    or results_json.get("backtest", {}).get("name")
    or "Unnamed Backtest"
)

# ── Upload ────────────────────────────────────────────────────────────────
payload = {
    "name": name,
    "createdAt": firestore.SERVER_TIMESTAMP,
    "statistics": statistics,
    "charts": charts,
}

print(f"⬆️  Uploading document {BACKTEST_ID} …")
doc_ref = db.collection("backtest_results").document(BACKTEST_ID)
doc_ref.set(payload)
print("✅  Successfully uploaded backtest results to Firestore!")
