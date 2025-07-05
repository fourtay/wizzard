#!/usr/bin/env python3
"""
store_results.py
Reads `backtests.json` to get a list of backtest IDs, fetches the full
results for each from the QuantConnect API, and pushes them to Google Firestore.
"""
import json
import os
import sys
import time
import requests
import hashlib
from pathlib import Path
from google.cloud import firestore

# --- Settings ---
BACKTESTS_FILE_PATH = Path("backtests.json")
PARAMS_DIR = Path(".tmp_children")

# --- Grab QC secrets ---
try:
    QC_USER_ID = os.environ["QC_USER_ID"]
    QC_API_TOKEN = os.environ["QC_API_TOKEN"]
except KeyError as missing:
    print(f"❌ Required QuantConnect secret not set: {missing.args[0]} (Set in GitHub Secrets)")
    sys.exit(1)

# --- Firestore auth ---
try:
    GCP_SA_KEY_JSON = os.environ["GCP_SA_KEY"]
    with open("gcp_key.json", "w") as fh:
        fh.write(GCP_SA_KEY_JSON)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
    db = firestore.Client()
    print("✅ Firestore ready")
except KeyError as missing:
    print(f"❌ Required env var not set: {missing.args[0]}")
    sys.exit(1)
except Exception as exc:
    print(f"❌ Firestore auth failed: {exc}")
    sys.exit(1)

def get_backtest_results(backtest_id: str) -> dict:
    """Fetches a single backtest result from the QC API."""
    timestamp = str(int(time.time()))
    signature = hashlib.sha256(f"{QC_API_TOKEN}:{timestamp}".encode()).hexdigest()
    headers = {"Accept": "application/json", "Timestamp": timestamp}
    auth = (QC_USER_ID, signature)
    
    response = requests.post(
        "https://www.quantconnect.com/api/v2/backtests/read",
        json={"backtestId": backtest_id},
        headers=headers,
        auth=auth,
    )
    if response.status_code != 200:
        print(f"  -> Failed to fetch {backtest_id}: {response.text}")
        return None
        
    data = response.json()
    if not data.get("success"):
        print(f"  -> API call for {backtest_id} unsuccessful: {data}")
        return None
        
    return data

# --- Main Logic ---
if not BACKTESTS_FILE_PATH.exists():
    print(f"🤷 {BACKTESTS_FILE_PATH} not found. Nothing to store.")
    sys.exit(0)

with open(BACKTESTS_FILE_PATH) as f:
    backtests_to_fetch = json.load(f)

print(f"Found {len(backtests_to_fetch)} backtests to process.")

for child_id, backtest_id in backtests_to_fetch.items():
    print(f"--- Processing {child_id} (ID: {backtest_id}) ---")
    results_json = get_backtest_results(backtest_id)
    if not results_json:
        continue

    # Load the parameters used for this specific run
    params_path = PARAMS_DIR / child_id / "params.json"
    try:
        with open(params_path) as f:
            params = json.load(f)
    except FileNotFoundError:
        print(f"  -> WARNING: Could not find params file at {params_path}")
        params = {}

    # Structure the payload for Firestore
    payload = {
        "name": results_json.get("name", "Unnamed Backtest"),
        "createdAt": firestore.SERVER_TIMESTAMP,
        "statistics": results_json.get("statistics", {}),
        "charts": results_json.get("charts", {}),
        "params": params  # Include the parameters that generated this result
    }

    print(f"  -> Uploading document {backtest_id}…")
    db.collection("backtest_results").document(backtest_id).set(payload)

print("\n✅ Successfully processed all backtests.")
