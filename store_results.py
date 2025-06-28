import os, json, sys
from google.cloud import firestore

# ───────────────────────── CONSTANTS ──────────────────────────
RESULTS_FILE_PATH = "backtest-results.json"      # file created by the workflow
COLLECTION_NAME  = "backtest_results"            # Firestore collection name
# ───────────────────────── ENV VARIABLES ──────────────────────
try:
    GCP_SA_KEY_JSON = os.environ["GCP_SA_KEY"]   # secret from GitHub
    BACKTEST_ID     = os.environ["BACKTEST_ID"]  # set in the workflow
except KeyError:
    print("❌  GCP_SA_KEY or BACKTEST_ID env-var missing"); sys.exit(1)

# ───────────────────────── FIRESTORE LOGIN ────────────────────
with open("gcp_key.json", "w") as f:              # write key file
    f.write(GCP_SA_KEY_JSON)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
db = firestore.Client()
print("✅  Connected to Firestore")

# ───────────────────────── READ RESULT FILE ───────────────────
print(f"📖  Reading {RESULTS_FILE_PATH} …")
try:
    with open(RESULTS_FILE_PATH, "r") as f:
        data = json.load(f)
except FileNotFoundError:
    print("❌  results file not found"); sys.exit(1)
except json.JSONDecodeError:
    print("❌  results file is not valid JSON"); sys.exit(1)

# ───────────────────────── EXTRACT STATISTICS ─────────────────
"""
Different LEAN CLI versions write stats in slightly different places.
We try the known patterns in order until we find one that works.
"""
statistics = {}
charts     = {}

# pattern 1: top-level "statistics"
if "statistics" in data and data["statistics"]:
    statistics = data["statistics"]
    charts     = data.get("charts", {})

# pattern 2: inside "results" -> "statistics"
elif "results" in data and isinstance(data["results"], dict):
    inner = data["results"]
    if "statistics" in inner and inner["statistics"]:
        statistics = inner["statistics"]
        charts     = inner.get("charts", {})

# pattern 3: inside "results" -> "portfolioStatistics"
elif "results" in data and "portfolioStatistics" in data["results"]:
    statistics = data["results"]["portfolioStatistics"]
    charts     = data["results"].get("charts", {})

# add more fallbacks here if necessary …

if not statistics:
    print("❌  Could not locate statistics block in JSON. Aborting.")
    sys.exit(1)

# ───────────────────────── UPLOAD TO FIRESTORE ────────────────
payload = {
    "name"      : data.get("name", "Unnamed Backtest"),
    "createdAt" : firestore.SERVER_TIMESTAMP,
    "statistics": statistics,
    "charts"    : charts
}

print(f"⬆️  Uploading document ID '{BACKTEST_ID}' to '{COLLECTION_NAME}' …")
db.collection(COLLECTION_NAME).document(BACKTEST_ID).set(payload)
print("🎉  Backtest results uploaded successfully!")
