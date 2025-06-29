import os, sys, json
from google.cloud import firestore

# ---------- constants ----------
RESULTS_FILE = "backtest-results.json"
COLLECTION    = "backtest_results"        # 1 collection for all runs

# ---------- env vars ----------
try:
    gcp_key      = os.environ["GCP_SA_KEY"]
    BACKTEST_ID  = os.environ["BACKTEST_ID"]
except KeyError:
    print("❌  GCP_SA_KEY or BACKTEST_ID not set"); sys.exit(1)

# ---------- Firestore auth ----------
with open("gcp_key.json", "w") as f:
    f.write(gcp_key)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"

db = firestore.Client()
print("✅  Connected to Firestore")

# ---------- read results ----------
try:
    with open(RESULTS_FILE, "r") as f:
        payload = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"❌  Reading {RESULTS_FILE}: {e}"); sys.exit(1)

print("📖  Parsing backtest JSON …")

# ----- locate statistics no matter which schema -----
stats  = {}
charts = {}

# Lean v2.5+ places everything under 'results'
if "results" in payload:
    inner = payload["results"]
    stats  = inner.get("statistics") or inner.get("portfolioStatistics") or {}
    charts = inner.get("charts", {})
else:                              # older dumps put stats top-level
    stats  = payload.get("statistics", {})
    charts = payload.get("charts", {})

if not stats:
    print("❌  Could not locate statistics block in JSON. Aborting."); sys.exit(1)

doc = {
    "name"      : payload.get("name", "Unnamed Backtest"),
    "createdAt" : firestore.SERVER_TIMESTAMP,
    "statistics": stats,
    "charts"    : charts
}

# ---------- upload ----------
print(f"⏫  Writing document id={BACKTEST_ID} …")
db.collection(COLLECTION).document(BACKTEST_ID).set(doc)
print("🎉  Done!  Statistics + charts are now in Firestore.")
