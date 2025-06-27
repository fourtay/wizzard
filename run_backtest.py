# run_backtest.py (Corrected Version 3 - Definitive)
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

# --- Create Authentication Headers Function ---
def create_auth_headers():
    timestamp = int(time.time())
    signature = hashlib.sha256(f"{QC_API_TOKEN}:{timestamp}".encode()).hexdigest()
    return {
        "Accept": "application/json",
        "Timestamp": str(timestamp)
    }, (QC_USER_ID, signature)

# --- 1. Create a Compile Job ---
# The correct endpoint to create a compile is /compiles/create
compile_create_url = f"{QC_API_URL}/compiles/create"
compile_payload = { "projectId": QC_PROJECT_ID }

print(f"Submitting compile request for project {QC_PROJECT_ID}...")
headers, auth = create_auth_headers()
compile_create_response = requests.post(
    compile_create_url,
    json=compile_payload,
    headers=headers,
    auth=auth
).json()

if not compile_create_response.get("success"):
    print("ERROR: Compile creation request failed.")
    print(compile_create_response)
    exit(1)

compile_id = compile_create_response["compileId"]
print(f"Successfully submitted compile job with ID: {compile_id}")

# --- 2. Wait for Compile to Complete ---
compile_read_url = f"{QC_API_URL}/compiles/read?compileId={compile_id}"
while True:
    headers, auth = create_auth_headers()
    status_response = requests.get(compile_read_url, headers=headers, auth=auth).json()
    state = status_response.get("state")
    progress = status_response.get("progress", 0)
    print(f"Compile state is: {state} ({progress * 100:.1f}%)")

    if state == "Success":
        print("Compilation successful!")
        break
    if state == "Error":
        print("ERROR: Compilation failed.")
        print(status_response)
        exit(1)

    time.sleep(5)

# --- 3. Create a New Backtest (with the compileId) ---
backtest_create_url = f"{QC_API_URL}/backtests/create"
backtest_name = f"Automated AI Backtest - {time.strftime('%Y-%m-%d %H:%M:%S')}"
backtest_payload = {
    "projectId": QC_PROJECT_ID,
    "compileId": compile_id,  # <--- This is the required parameter we were missing
    "name": backtest_name
}

print(f"Creating backtest named: '{backtest_name}'")
headers, auth = create_auth_headers()
backtest_create_response = requests.post(
    backtest_create_url,
    json=backtest_payload,
    headers=headers,
    auth=auth
).json()

if not backtest_create_response.get("success"):
    print("ERROR: Backtest creation failed.")
    print(backtest_create_response)
    exit(1)

backtest_id = backtest_create_response["backtestId"]
print(f"Successfully created backtest with ID: {backtest_id}")

# --- 4. Save Backtest ID for the next script ---
print("Saving backtest ID to file for next step.")
with open("backtest_id.txt", "w") as f:
    f.write(backtest_id)

print("run_backtest.py script finished.")
