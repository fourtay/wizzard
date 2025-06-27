# store_results.py (Final Version - Using LEAN CLI Output)
import os
import json
from google.cloud import firestore
import sys

# --- Settings ---
RESULTS_FILE_PATH = "backtest_results.json"

# --- Get Credentials from GitHub Secrets ---
try:
    GCP_SA_KEY_JSON = os.environ["GCP_SA_KEY"]
except KeyError:
    print("ERROR: GCP_SA_KEY secret not set.")
    sys.exit(1)

# --- Authenticate with Google Cloud ---
try:
    with open("gcp_key.json", "w") as f:
        f.write(GCP_SA_KEY_JSON)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
    db = firestore.Client()
    print("Successfully connected to Google Firestore.")
except Exception as e:
    print(f"ERROR: Failed to connect to Firestore: {e}")
    sys.exit(1)


# --- 1. Read the Local JSON Results File ---
print(f"Reading results from '{RESULTS_FILE_PATH}'...")
try:
    with open(RESULTS_FILE_PATH, "r") as f:
        results_data = json.load(f)
except FileNotFoundError:
    print(f"ERROR: Results file not found at '{RESULTS_FILE_PATH}'. Did the backtest step fail?")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"ERROR: Could not decode JSON from '{RESULTS_FILE_PATH}'. The file may be empty or corrupt.")
    sys.exit(1)

# The backtest ID is now inside the results file
backtest_id = results_data.get("backtestId")
if not backtest_id:
    print("ERROR: 'backtestId' not found in results JSON.")
    sys.exit(1)

# --- 2. Prepare and Upload Data to Firestore ---
# The structure of the results from LEAN CLI is the same as the API
statistics = results_data.get("statistics", {})
charts = results_data.get("charts", {})

if not statistics:
    print("ERROR: No 'statistics' block found in results JSON.")
    sys.exit(1)

data_to_upload = {
    "name": results_data.get("name"),
    "createdAt": firestore.SERVER_TIMESTAMP,
    "statistics": statistics,
    "charts": charts
}

print(f"Uploading results for backtest {backtest_id} to Firestore...")
doc_ref = db.collection("backtest_results").document(backtest_id)
doc_ref.set(data_to_upload)

print("Successfully uploaded results to Firestore!")
print("store_results.py script finished.")
