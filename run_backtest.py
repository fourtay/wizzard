# run_backtest.py (Corrected Version 2)
import os
import requests
import time
import json
import hashlib

# --- Settings ---
# IMPORTANT: Make sure this is your actual QuantConnect Project ID
QC_PROJECT_ID = 23708106 # This should be your real Project ID
QC_API_URL = "https://www.quantconnect.com/api/v2"

# --- Get Credentials from GitHub Secrets ---
try:
    QC_USER_ID = os.environ["QC_USER_ID"]
    QC_API_TOKEN = os.environ["QC_API_TOKEN"]
except KeyError:
    print("ERROR: Make sure QC_USER_ID and QC_API_TOKEN are set.")
    exit(1)

# --- 1. Create a New Backtest ---
# NOTE: The API creates the backtest and handles the compile in one step.
# The correct endpoint is /backtests/create
backtest_url = f"{QC_API_URL}/backtests/create"
backtest_name = f"Automated AI Backtest - {time.strftime('%Y-%m-%d %H:%M:%S')}"

backtest_payload = {
    "projectId": QC_PROJECT_ID,
    "name": backtest_name
}

# --- Create Authentication Headers ---
timestamp = int(time.time())
signature = hashlib.sha256(f"{QC_API_TOKEN}:{timestamp}".encode()).hexdigest()
headers = {
    "Accept": "application/json",
    "Timestamp": str(timestamp)
}

print(f"Creating backtest for project {QC_PROJECT_ID}...")
backtest_response = requests.post(
    backtest_url,
    json=backtest_payload,
    headers=headers,
    auth=(QC_USER_ID, signature)
)

response_json = backtest_response.json()

if not response_json.get("success"):
    print("ERROR: Backtest creation failed.")
    print(response_json)
    exit(1)

# The compile ID is part of the backtest creation response
compile_id = response_json.get("compileId")
backtest_id = response_json.get("backtestId")

print(f"Successfully created compile job: {compile_id}")
print(f"Successfully created backtest job: {backtest_id}")

# --- 2. Save Backtest ID for the next script ---
print("Saving backtest ID to file for next step.")
with open("backtest_id.txt", "w") as f:
    f.write(backtest_id)

print("run_backtest.py script finished.")
