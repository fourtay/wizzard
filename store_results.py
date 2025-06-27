# store_results.py (Corrected Version 4 - Definitive Auth)
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

# --- Definitive Authentication Function ---
def get_auth_and_headers():
    timestamp = str(int(time.time()))
    signature = hashlib.sha256(f"{QC_API_TOKEN}:{timestamp}".encode()).hexdigest()
    headers = {
        "Accept": "application/json",
        "Timestamp": timestamp  # Timestamp must be in the headers
    }
    # The auth tuple is the UserID and the generated HASH
    auth = (QC_USER_ID, signature)
    return auth, headers

# --- Main Script ---
# 1. Read the Backtest ID
try:
    with open("backtest_id.txt", "r") as f:
        backtest_id = f.read().strip()
    print(f"Read backtest ID: {backtest_id}")
except FileNotFoundError:
    print("ERROR: backtest_id.txt not found.")
    exit(1)

# 2. Poll for Backtest Completion
backtest_read_url = f"{QC_API_URL}/backtests/read"
results_response = None
while True:
    read_payload = { "backtestId": backtest_id }
    try:
        auth, headers = get_auth_and_headers()
        response = requests.post(
            backtest_read_url,
            json=read_payload,
            headers=headers,
            auth=auth
        )
        response.raise_for_status()
        read_json = response.json()
    except Exception as e:
        print(f"ERROR reading backtest status: {e}")
        if 'response' in locals():
            print(f"Response Text: {response.text}")
        exit(1)

    if not read_json.get("success"):
        print("ERROR: Reading backtest status failed.")
        print(read_json)
        exit(1)

    progress = read_json.get("progress", 0)
    print(f"Backtest progress: {progress * 100:.2f}%")

    if read_json.get("completed"):
        print("Backtest has completed.")
        results_response = read_json
        break
    if read_json.get("error") or read_json.get("stacktrace"):
        print("ERROR: Backtest failed during execution.")
        print(f"Error: {read_json.get('error')}")
        print(f"Stacktrace: {read_json.get('stacktrace')}")
        exit(1)
    time.sleep(10)

# 3. Prepare and Upload Data to Firestore
if results_response is None:
    print("ERROR: Loop finished without getting final results.")
    exit(1)

statistics = results_response.get("statistics", {})
if not statistics:
    print("ERROR: Could not retrieve backtest statistics.")
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
