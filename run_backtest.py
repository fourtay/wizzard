# run_backtest.py (Final Version - Clean Workspace)
import os
import subprocess
import sys

# --- Settings ---
QC_PROJECT_NAME = "23708106"
WORKSPACE_DIR = "lean_workspace"
# The output path is now inside the workspace directory
OUTPUT_FILE_PATH = f"{WORKSPACE_DIR}/{QC_PROJECT_NAME}/backtest-results.json"

# --- Get Credentials from GitHub Secrets ---
try:
    QC_USER_ID = os.environ["QC_USER_ID"]
    QC_API_TOKEN = os.environ["QC_API_TOKEN"]
except KeyError:
    print("ERROR: Make sure QC_USER_ID and QC_API_TOKEN are set.")
    sys.exit(1)

# --- 1. Create and move into a clean workspace directory ---
print(f"Creating clean workspace at ./{WORKSPACE_DIR}")
os.makedirs(WORKSPACE_DIR, exist_ok=True)
# All subsequent commands will run from inside this directory
os.chdir(WORKSPACE_DIR)

# --- 2. Log in to LEAN CLI ---
print("Logging into LEAN CLI...")
login_command = ["lean", "login", "--user-id", QC_USER_ID, "--api-token", QC_API_TOKEN]
subprocess.run(login_command, check=True, capture_output=True, text=True)
print("Successfully logged in.")

# --- 3. Initialize the LEAN Workspace ---
# This will now run in an empty directory, preventing the prompt.
print("Initializing LEAN workspace...")
init_command = ["lean", "init"]
try:
    subprocess.run(init_command, check=True, capture_output=True, text=True)
    print("Successfully initialized workspace.")
except subprocess.CalledProcessError as e:
    print(f"ERROR: 'lean init' failed unexpectedly.")
    print("Output:", e.stdout)
    print("Error Output:", e.stderr)
    sys.exit(1)

# --- 4. Pull Cloud Project into the Workspace ---
print(f"Pulling cloud project '{QC_PROJECT_NAME}'...")
pull_command = ["lean", "cloud", "pull", "--project", QC_PROJECT_NAME]
try:
    subprocess.run(pull_command, check=True, capture_output=True, text=True)
    print("Successfully pulled project files.")
except subprocess.CalledProcessError as e:
    print(f"ERROR: Failed to pull cloud project '{QC_PROJECT_NAME}'.")
    print("Output:", e.stdout)
    print("Error Output:", e.stderr)
    sys.exit(1)

# --- 5. Run the Backtest ---
print(f"Starting cloud backtest for project '{QC_PROJECT_NAME}'...")
# The output path needs to be relative to the workspace now
relative_output_path = f"{QC_PROJECT_NAME}/backtest-results.json"
backtest_command = [
    "lean", "backtest",
    QC_PROJECT_NAME,
    "--output", relative_output_path,
    "--detach",
    "--no-update"
]
try:
    process = subprocess.run(backtest_command, check=True, capture_output=True, text=True)
    print("Successfully submitted backtest to QuantConnect Cloud.")
    print("LEAN CLI Output:", process.stdout)
    print("run_backtest.py finished.")
except subprocess.CalledProcessError as e:
    print("ERROR: The 'lean backtest' command failed.")
    print("Output:", e.stdout)
    print("Error Output:", e.stderr)
    sys.exit(1)
