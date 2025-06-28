import os
import json
from google.cloud import firestore
import sys

# --- Settings ---
RESULTS_FILE_PATH = "backtest-results.json"

# --- Get Credentials ---
try:
    GCP_SA_KEY_JSON = os.environ["GCP_SA_KEY"]
    BACKTEST_ID = os.environ["BACKTEST_ID"]
except KeyError:
    print("ERROR: Required secret or env var not set (GCP_SA_KEY or BACKTEST_ID).")
    sys.exit(1)

# --- Authenticate with Firestore ---
try:
    with open("gcp_key.json", "w") as f:
        f.write(GCP_SA_KEY_JSON)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
    db = firestore.Client()
    print("Successfully connected to Google Firestore.")
except Exception as e:
    print(f"ERROR: Failed to connect to Firestore: {e}")
    sys.exit(1)

# --- Read Results File ---
print(f"Reading results from '{RESULTS_FILE_PATH}'...")
try:
    with open(RESULTS_FILE_PATH, "r") as f:
        results_data = json.load(f)
        print("=== FULL BACKTEST JSON ===")
        print(json.dumps(results_data, indent=2))
        print("=== END ===")
except FileNotFoundError:
    print(f"ERROR: File '{RESULTS_FILE_PATH}' not found.")
    sys.exit(1)
except json.JSONDecodeError:
    print("ERROR: Invalid JSON format.")
    sys.exit(1)

# --- Extract actual data ---
results_section = results_data.get("results", {})
print("DEBUG: Top-level keys inside 'results':", results_section.keys())

statistics = results_section.get("statistics", {})
charts = results_section.get("charts", {})

if not statistics:
    print("ERROR: No 'statistics' found in results['statistics'].")
    print("DEBUG: 'results' section was:")
    print(json.dumps(results_section, indent=2))
    sys.exit(1)

# --- Upload to Firestore ---
data_to_upload = {
    "name": results_data.get("name", "Unknown"),
    "createdAt": firestore.SERVER_TIMESTAMP,
    "statistics": statistics,
    "charts": charts
}

print(f"Uploading results to Firestore with document ID: {BACKTEST_ID}")
doc_ref = db.collection("backtest_results").document(BACKTEST_ID)
doc_ref.set(data_to_upload)

print("✅ Successfully uploaded backtest results to Firestore!")
