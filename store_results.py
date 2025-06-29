import os, sys, json
from google.cloud import firestore

# ────────── constants ──────────
RESULTS_FILE = "backtest-results.json"
COLLECTION   = "backtest_results"          # single collection for every run

# ────────── env vars ──────────
try:
    gcp_key     = os.environ["GCP_SA_KEY"]
    BACKTEST_ID = os.environ["BACKTEST_ID"]
except KeyError:
    print("❌  GCP_SA_KEY or BACKTEST_ID not set"); sys.exit(1)

# ────────── Firestore auth ──────────
with open("gcp_key.json", "w") as fh:
    fh.write(gcp_key)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"

db = firestore.Client()
print("✅  Connected to Firestore")

# ────────── read JSON file ──────────
try:
    with open(RESULTS_FILE, "r") as fh:
        payload = json.load(fh)
except (FileNotFoundError, json.JSONDecodeError) as err:
    print(f"❌  {RESULTS_FILE}: {err}"); sys.exit(1)

print("📖  Parsing backtest JSON …")

# ────────── locate statistics block (works for every Lean schema) ──────────
stats  = {}
charts = {}

# try top-level first
stats  = payload.get("statistics") or payload.get("portfolioStatistics") or {}
charts = payload.get("charts", {})

# if not found, drill into payload["results"] (Lean ≥2.4)
if not stats and isinstance(payload.get("results"), dict):
    inner   = payload["results"]
    stats   = inner.get("statistics") or inner.get("portfolioStatistics") or {}
    charts  = inner.get("charts", charts)

if not stats:
    print("❌  Could not locate statistics block in JSON. Aborting."); sys.exit(1)

# ────────── Firestore doc ──────────
doc = {
    "name"      : payload.get("name", "Unnamed Backtest"),
    "createdAt" : firestore.SERVER_TIMESTAMP,
    "statistics": stats,
    "charts"    : charts
}

print(f"⏫  Writing document id={BACKTEST_ID} …")
db.collection(COLLECTION).document(BACKTEST_ID).set(doc)
print("🎉  Done! statistics + charts are now in Firestore.")
