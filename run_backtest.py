# run_backtest.py (Final Version - With Cloud Pull)
import os
import subprocess
import sys

# --- Settings ---
# This is the name of your project in the QuantConnect cloud.
# It can be the number from the URL or a name if you've changed it.
QC_PROJECT_NAME = "23708106"
OUTPUT_FILE_PATH = f"./{QC_PROJECT_NAME}/backtest_results.json"

# --- Get Credentials from GitHub Secrets ---
try:
    QC_USER_ID = os.environ["QC_USER_ID"]
    QC_API_TOKEN = os.environ["QC_API_TOKEN"]
except KeyError:
    print("ERROR: Make sure QC_USER_ID and QC_API_TOKEN are set.")
    sys.exit(1)

# --- 1. Log in to LEAN CLI ---
print("Logging into LEAN CLI...")
login_command = [
    "lean", "login",
    "--user-id", QC_USER_ID,
    "--api-token", QC_API_TOKEN
]
subprocess.run(login_command, check=True, capture_output=True, text=True)
print("Successfully logged in.")

# --- 2. Pull Cloud Project to Local Environment ---
# This is the new, critical step. It downloads the project files.
print(f"Pulling cloud project '{QC_PROJECT_NAME}'...")
pull_command = [
    "lean", "cloud", "pull",
    "--project", QC_PROJECT_NAME
]
try:
    subprocess.run(pull_command, check=True, capture_output=True, text=True)
    print("Successfully pulled project files.")
except subprocess.CalledProcessError as e:
    print(f"ERROR: Failed to pull cloud project '{QC_PROJECT_NAME}'.")
    print("Return Code:", e.returncode)
    print("Output:", e.stdout)
    print("Error Output:", e.stderr)
    sys.exit(1)

# --- 3. Run the Backtest on the Local Project Files ---
# Now that the folder exists locally, this command will work.
print(f"Starting cloud backtest for project '{QC_PROJECT_NAME}'...")
backtest_command = [
    "lean", "backtest",
    QC_PROJECT_NAME,  # This now correctly refers to the local folder we just created
    "--output", OUTPUT_FILE_PATH,
    "--detach",
    "--no-update"
]

try:
    process = subprocess.run(
        backtest_command,
        check=True,
        capture_output=True,
        text=True
    )
    print("Successfully submitted backtest to QuantConnect Cloud.")
    print("LEAN CLI Output:", process.stdout)
    print("run_backtest.py finished.")

except subprocess.CalledProcessError as e:
    print("ERROR: The 'lean backtest' command failed.")
    print("Return Code:", e.returncode)
    print("Output:", e.stdout)
    print("Error Output:", e.stderr)
    sys.exit(1)
