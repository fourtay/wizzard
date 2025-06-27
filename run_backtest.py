# run_backtest.py (Corrected Version 4 - Diagnostic)
import os
import requests
import time
import json

# --- Settings ---
QC_PROJECT_ID = 23708106 # This is your real Project ID
QC_API_URL = "https://www.quantconnect.com/api/v2"

# --- Get Credentials from GitHub Secrets ---
try:
    QC_USER_ID = os.environ["QC_USER_ID"]
    QC_API_TOKEN = os.environ["QC_API_TOKEN"]
except KeyError:
    print("ERROR: Make sure QC_USER_ID and QC_API_TOKEN are set.")
    exit(1)


# --- 1. Create a Compile Job ---
compile_create_url = f"{QC_API_URL}/compiles/create"
compile_payload = { "projectId": QC_PROJECT_ID }

print(f"Submitting compile request for project {QC_PROJECT_ID}...")
# --- DEBUG: We will now print the raw server response ---
try:
    # Using simple HTTP Basic Authentication with the User ID and API Token
    response = requests.post(
        compile_create_url,
        json=compile_payload,
        auth=requests.auth.HTTPBasicAuth(QC_USER_ID, QC_API_TOKEN)
    )

    # --- DIAGNOSTIC PRINTS ---
    print("--- SERVER RESPONSE ---")
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: '{response.text}'")
    print("-----------------------")

    # Raise an error if the status code is bad (e.g., 401, 403, 404)
    response.raise_for_status()
    
    # Try to decode the JSON
    compile_create_response = response.json()

except requests.exceptions.RequestException as e:
    print(f"ERROR: A network request error occurred: {e}")
    exit(1)
except json.JSONDecodeError as e:
    print(f"ERROR: Failed to decode JSON. The server response was not valid JSON.")
    exit(1)


if not compile_create_response.get("success"):
    print("ERROR: Compile creation request failed.")
    print(compile_create_response)
    exit(1)

compile_id = compile_create_response["compileId"]
print(f"Successfully submitted compile job with ID: {compile_id}")

# The rest of the script is paused for now until we solve the connection.
# For safety, we will exit here after the first successful call.
print("Initial connection successful. Exiting debug script for now.")
exit(0)

# --- The rest of the script remains for when we remove the exit() ---

# --- 2. Wait for Compile to Complete ---
# ... (code will be re-enabled later)

# --- 3. Create a New Backtest (with the compileId) ---
# ... (code will be re-enabled later)
