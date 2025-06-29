import os, sys, json
from pathlib import Path
from typing import Any, Dict, Optional

from google.cloud import firestore

# ────────── constants ──────────
RESULTS_FILE = Path("backtest-results.json")
COLLECTION   = "backtest_results"          # one collection for every run
TARGET_KEYS  = {"statistics", "portfolioStatistics"}  # names Lean might use


# ────────── helpers ──────────
def find_stats(node: Any) -> Optional[Dict]:
    """
    Depth-first search through *any* JSON structure and return the first
    dict that contains one of TARGET_KEYS.  Returns None if nothing found.
    """
    if isinstance(node, dict):
        if TARGET_KEYS & node.keys():
            return node
        for v in node.values():
            hit = find_stats(v)
            if hit:
                return hit
    elif isinstance(node, list):
        for item in node:
            hit = find_stats(item)
            if hit:
                return hit
    return None


# ────────── env vars ──────────
try:
    gcp_key     = os.environ["GCP_SA_KEY"]
    BACKTEST_ID = os.environ["BACKTEST_ID"]
except KeyError:
    print("❌  GCP_SA_KEY or BACKTEST_ID env var missing"); sys.exit(1)

# ────────── Firestore auth ──────────
with open("gcp_key.json", "w") as fh:
    fh.write(gcp_key)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"

db = firestore.Client()
print("✅  Connected to Firestore")

# ────────── read JSON file ──────────
if not RESULTS_FILE.exists():
    print(f"❌  {RESULTS_FILE} not found"); sys.exit(1)

try:
    payload = json.loads(RESULTS_FILE.read_text())
except json.JSONDecodeError as err:
    print(f"❌  Invalid JSON: {err}"); sys.exit(1)

print("📖  Parsing backtest JSON …")

# ────────── locate statistics block ──────────
stats_holder = find_stats(payload)
if not stats_holder:
    print("❌  Could not locate statistics or portfolioStatistics anywhere. Aborting.")
    sys.exit(1)

stats  = stats_holder.get("statistics") or stats_holder.get("portfolioStatistics")
charts = payload.get("charts", {})  # charts have always been top-level so far

# ────────── Firestore doc ──────────
doc = {
    "name"      : payload.get("name", "Unnamed Backtest"),
    "createdAt" : firestore.SERVER_TIMESTAMP,
    "statistics": stats,
    "charts"    : charts,
}

print(f"⏫  Writing doc id={BACKTEST_ID} …")
db.collection(COLLECTION).document(BACKTEST_ID).set(doc)
print("🎉  Done! statistics + charts are now in Firestore.")
