# run_backtest.py (Corrected Version 6 - Definitive Auth)
import os
import requests
import time
import json
import hashlib

# --- Settings ---
QC_PROJECT_ID = 23708106 # Your real Project ID
QC_API_URL = "https://www.quantconnect.com/api/v2"

# --- Get Credentials from GitHub Secrets ---
try:
    QC_USER_ID = os.environ["QC_USER_ID"]
    QC_API_TOKEN = os.environ["QC_API_TOKEN"]
except KeyError:
    print("ERROR: Make sure QC_USER_ID and QC_API_TOKEN are set.")
    exit(1)

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
# 1. Create a Compile Job
compile_create_url = f"{QC_API_URL}/compiles/create"
compile_payload = { "projectId": QC_PROJECT_ID }
print(f"Submitting compile request for project {QC_PROJECT_ID}...")

try:
    auth, headers = get_auth_and_headers()
    compile_response = requests.post(
        compile_create_url,
        json=compile_payload,
        headers=headers,
        auth=auth
    )
    compile_response.raise_for_status()
    compile_json = compile_response.json()
except Exception as e:
    print(f"ERROR during compile creation: {e}")
    if 'compile_response' in locals():
        print(f"Response text: {compile_response.text}")
    exit(1)

if not compile_json.get("success"):
    print("ERROR: Compile creation failed.")
    print(compile_json)
    exit(1)

compile_id = compile_json["compileId"]
print(f"Successfully submitted compile job with ID: {compile_id}")

# 2. Wait for Compile to Complete
compile_read_url = f"{QC_API_URL}/compiles/read"
while True:
    read_payload = { "compileId": compile_id }
    try:
        auth, headers = get_auth_and_headers()
        status_response = requests.get(
            compile_read_url,
            params=read_payload,
            headers=headers,
            auth=auth
        )
        status_response.raise_for_status()
        status_json = status_response.json()
    except Exception as e:
        print(f"ERROR reading compile status: {e}")
        exit(1)

    state = status_json.get("state")
    progress = status_json.get("progress", 0)
    print(f"Compile state is: {state} ({progress * 100:.1f}%)")
    if state == "Success":
        print("Compilation successful!")
        break
    if state == "Error":
        print("ERROR: Compilation failed.")
        print(status_json)
        exit(1)
    time.sleep(5)

# 3. Create a New Backtest
backtest_create_url = f"{QC_API_URL}/backtests/create"
backtest_name = f"Automated AI Backtest - {time.strftime('%Y-%m-%d %H:%M:%S')}"
backtest_payload = {
    "projectId": QC_PROJECT_ID,
    "compileId": compile_id,
    "name": backtest_name
}
print(f"Creating backtest named: '{backtest_name}'")

try:
    auth, headers = get_auth_and_headers()
    backtest_response = requests.post(
        backtest_create_url,
        json=backtest_payload,
        headers=headers,
        auth=auth
    )
    backtest_response.raise_for_status()
    backtest_json = backtest_response.json()
except Exception as e:
    print(f"ERROR during backtest creation: {e}")
    if 'backtest_response' in locals():
        print(f"Response text: {backtest_response.text}")
    exit(1)

if not backtest_json.get("success"):
    print("ERROR: Backtest creation failed.")
    print(backtest_json)
    exit(1)

backtest_id = backtest_json["backtestId"]
print(f"Successfully created backtest with ID: {backtest_id}")

# 4. Save Backtest ID
with open("backtest_id.txt", "w") as f:
    f.write(backtest_id)
print("run_backtest.py script finished.")
