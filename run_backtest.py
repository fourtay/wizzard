# run_backtest.py (Final Version - Using LEAN CLI)
import os
import subprocess
import sys

# --- Settings ---
# Go to your project on QuantConnect, and in the URL, you will see something like:
# https://www.quantconnect.com/project/23708106
# The project name is the part of the URL *after* your username.
# Often, it's a number, but it can be a name if you changed it.
# For this example, we assume the project is named "23708106"
QC_PROJECT_NAME = "23708106"
OUTPUT_FILE_PATH = "backtest_results.json"

# --- Get Credentials from GitHub Secrets ---
try:
    QC_USER_ID = os.environ["QC_USER_ID"]
    QC_API_TOKEN = os.environ["QC_API_TOKEN"]
except KeyError:
    print("ERROR: Make sure QC_USER_ID and QC_API_TOKEN are set.")
    sys.exit(1)

# --- 1. Log in to LEAN CLI ---
# This command configures the CLI with your credentials.
print("Logging into LEAN CLI...")
login_command = [
    "lean", "login",
    "--user-id", QC_USER_ID,
    "--api-token", QC_API_TOKEN
]
# We run it but don't need to see the output unless there's an error.
subprocess.run(login_command, check=True, capture_output=True, text=True)
print("Successfully logged in.")

# --- 2. Run the Backtest via LEAN CLI ---
# This single command handles everything: pulling the project, compiling, and running.
# --output specifies where to save the results JSON.
# --detach runs it on QuantConnect's cloud.
# --no-update tells it not to self-update, for stability in automation.
print(f"Starting cloud backtest for project '{QC_PROJECT_NAME}'...")
backtest_command = [
    "lean", "backtest",
    QC_PROJECT_NAME,
    "--output", OUTPUT_FILE_PATH,
    "--detach",
    "--no-update"
]

try:
    process = subprocess.run(
        backtest_command,
        check=True,  # This will raise an error if the command fails
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
