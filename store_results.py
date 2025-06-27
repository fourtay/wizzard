# store_results.py
import os
import json
import time
import requests
from google.cloud import firestore

# --- Settings ---
QC_API_URL = "https://www.quantconnect.com/api/v2"

# --- Get Credentials from GitHub Secrets ---
try:
    QC_USER_ID = os.environ["QC_USER_ID"]
    QC_API_TOKEN = os.environ["QC_API_TOKEN"]
    # We need the service account key to talk to Firestore
    GCP_SA_KEY_JSON = os.environ["GCP_SA_KEY"]
except KeyError:
    print("ERROR: Make sure QC_USER_ID, QC_API_TOKEN, and GCP_SA_KEY are set in secrets.")
    exit(1)

# --- Authenticate with Google Cloud ---
# Write the key to a temporary file for the library to use
with open("gcp_key.json", "w") as f:
    f.write(GCP_SA_KEY_JSON)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"

# Now we can initialize the Firestore client
db = firestore.Client()
print("Successfully connected to Google Firestore.")

# --- API Headers ---
headers = {
    "Accept": "application/json",
    "Authorization": f"Basic {requests.auth._basic_auth_str(QC_USER_ID, QC_API_TOKEN)}"
}

# --- 1. Read the Backtest ID from the file ---
try:
    with open("backtest_id.txt", "r") as f:
        backtest_id = f.read()
    print(f"Read backtest ID: {backtest_id}")
except FileNotFoundError:
    print("ERROR: backtest_id.txt not found. Did the previous script fail?")
    exit(1)

# --- 2. Poll for Backtest Completion ---
while True:
    read_url = f"{QC_API_URL}/backtests/read?backtestId={backtest_id}"
    read_response = requests.get(read_url, headers=headers).json()
    progress = read_response.get("progress")
    print(f"Backtest progress: {progress * 100:.2f}%")
    if read_response.get("completed"):
        print("Backtest has completed.")
        break
    time.sleep(10)

# --- 3. Fetch Final Backtest Results ---
print("Fetching final backtest results...")
# Add a small delay to ensure results are fully available
time.sleep(5)
results_response = requests.get(read_url, headers=headers).json()
statistics = results_response.get("statistics", {})

if not statistics:
    print("ERROR: Could not retrieve backtest statistics.")
    print(results_response)
    exit(1)

# --- 4. Prepare and Upload Data to Firestore ---
# Extract key performance indicators
data_to_upload = {
    "name": results_response.get("name"),
    "createdAt": firestore.SERVER_TIMESTAMP,
    "statistics": statistics,
    "charts": results_response.get("charts", {}) # Optionally save charts too
}

print(f"Uploading results for backtest {backtest_id} to Firestore...")
# Use the backtest ID as the unique document ID in Firestore
doc_ref = db.collection("backtest_results").document(backtest_id)
doc_ref.set(data_to_upload)

print("Successfully uploaded results to Firestore!")
print("store_results.py script finished.")
