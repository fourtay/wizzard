# run_backtest.py
import os
import requests
import time
import json

# --- Settings ---
# IMPORTANT: Replace 1234567 with your actual QuantConnect Project ID
QC_PROJECT_ID = 23708106
QC_API_URL = "https://www.quantconnect.com/api/v2"

# --- Get Credentials from GitHub Secrets ---
try:
    QC_USER_ID = os.environ["QC_USER_ID"]
    QC_API_TOKEN = os.environ["QC_API_TOKEN"]
except KeyError:
    print("ERROR: Make sure you have set QC_USER_ID and QC_API_TOKEN in your repository's secrets.")
    exit(1)

# --- API Headers ---
headers = {
    "Accept": "application/json",
    "Authorization": f"Basic {requests.auth._basic_auth_str(QC_USER_ID, QC_API_TOKEN)}"
}

# --- 1. Compile the Project ---
compile_url = f"{QC_API_URL}/projects/{QC_PROJECT_ID}/compile"
print(f"Submitting compile request for project {QC_PROJECT_ID}...")
compile_response = requests.post(compile_url, headers=headers)

if not compile_response.json().get("success"):
    print("ERROR: Compile request failed.")
    print(compile_response.text)
    exit(1)

compile_id = compile_response.json()["compileId"]
print(f"Successfully submitted compile job with ID: {compile_id}")

# --- 2. Wait for Compile to Complete ---
while True:
    status_url = f"{QC_API_URL}/compiles/read?compileId={compile_id}"
    status_response = requests.get(status_url, headers=headers).json()
    state = status_response.get("state")
    print(f"Compile state is: {state}")
    if state in ["Success", "Error"]:
        if state == "Error":
            print("ERROR: Compilation failed.")
            print(status_response)
            exit(1)
        break
    time.sleep(5)

print("Compilation successful!")

# --- 3. Create a New Backtest ---
backtest_name = f"Automated AI Backtest - {time.strftime('%Y-%m-%d %H:%M:%S')}"
backtest_url = f"{QC_API_URL}/backtests/create"
backtest_payload = {
    "projectId": QC_PROJECT_ID,
    "compileId": compile_id,
    "name": backtest_name
}

print(f"Creating backtest named: '{backtest_name}'")
backtest_response = requests.post(backtest_url, json=backtest_payload, headers=headers)

if not backtest_response.json().get("success"):
    print("ERROR: Backtest creation failed.")
    print(backtest_response.text)
    exit(1)

backtest_id = backtest_response.json()["backtestId"]
print(f"Successfully created backtest with ID: {backtest_id}")

# --- 4. Save Backtest ID for the next script ---
print("Saving backtest ID to file for next step.")
with open("backtest_id.txt", "w") as f:
    f.write(backtest_id)

print("run_backtest.py script finished.")
