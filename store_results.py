# store_results.py (Corrected Version 2)
import os
import json
import time
import requests
import hashlib
from google.cloud import firestore

# --- Settings ---
QC_API_URL = "https://www.quantconnect.com/api/v2"

# --- Get Credentials from GitHub Secrets ---
try:
    QC_USER_ID = os.environ["QC_USER_ID"]
    QC_API_TOKEN = os.environ["QC_API_TOKEN"]
    GCP_SA_KEY_JSON = os.environ["GCP_SA_KEY"]
except KeyError:
    print("ERROR: Make sure all required secrets are set.")
    exit(1)

# --- Authenticate with Google Cloud ---
with open("gcp_key.json", "w") as f:
    f.write(GCP_SA_KEY_JSON)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
db = firestore.Client()
print("Successfully connected to Google Firestore.")

# --- 1. Read the Backtest ID from the file ---
try:
    with open("backtest_id.txt", "r") as f:
        backtest_id = f.read().strip()
    print(f"Read backtest ID: {backtest_id}")
except FileNotFoundError:
    print("ERROR: backtest_id.txt not found.")
    exit(1)

# --- 2. Poll for Backtest Completion ---
# The correct endpoint to read results is /backtests/read
read_url = f"{QC_API_URL}/backtests/read"
read_payload = { "backtestId": backtest_id }

while True:
    timestamp = int(time.time())
    signature = hashlib.sha256(f"{QC_API_TOKEN}:{timestamp}".encode()).hexdigest()
    headers = {
        "Accept": "application/json",
        "Timestamp": str(timestamp)
    }

    read_response = requests.post(read_url, json=read_payload, headers=headers, auth=(QC_USER_ID, signature)).json()

    if not read_response.get("success"):
        print("ERROR: Reading backtest status failed.")
        print(read_response)
        # Exit if we can't even read the status
        exit(1)

    progress = read_response.get("progress", 0)
    print(f"Backtest progress: {progress * 100:.2f}%")

    if read_response.get("completed"):
        print("Backtest has completed.")
        # This is the final successful response, so we can break and process it
        results_response = read_response
        break

    # If the backtest is still running, check for errors
    if read_response.get("error") or read_response.get("stacktrace"):
        print("ERROR: Backtest failed during execution.")
        print(f"Error: {read_response.get('error')}")
        print(f"Stacktrace: {read_response.get('stacktrace')}")
        exit(1)

    time.sleep(10)

# --- 3. Prepare and Upload Data to Firestore ---
statistics = results_response.get("statistics", {})

if not statistics:
    print("ERROR: Could not retrieve backtest statistics from final response.")
    print(results_response)
    exit(1)

data_to_upload = {
    "name": results_response.get("name"),
    "createdAt": firestore.SERVER_TIMESTAMP,
    "statistics": statistics,
    "charts": results_response.get("charts", {})
}

print(f"Uploading results for backtest {backtest_id} to Firestore...")
doc_ref = db.collection("backtest_results").document(backtest_id)
doc_ref.set(data_to_upload)

print("Successfully uploaded results to Firestore!")
print("store_results.py script finished.")
