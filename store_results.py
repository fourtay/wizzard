import os, json, sys, re
from google.cloud import firestore

RESULTS_FILE_PATH = "backtest-results.json"

# ---------- creds ----------
try:
    GCP_SA_KEY_JSON = os.environ["GCP_SA_KEY"]
    BACKTEST_ID     = os.environ["BACKTEST_ID"]
except KeyError as e:
    print(f"❌  Missing env var: {e}")
    sys.exit(1)

with open("gcp_key.json", "w") as f:
    f.write(GCP_SA_KEY_JSON)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
db = firestore.Client()
print("✅  Firestore connected")

# ---------- read ----------
try:
    with open(RESULTS_FILE_PATH) as f:
        raw = json.load(f)
except Exception as e:
    print(f"❌  Cannot read {RESULTS_FILE_PATH}: {e}")
    sys.exit(1)

# ---------- locate the first dict literally called “statistics” -------------
def locate_stats(obj):
    if isinstance(obj, dict):
        if "statistics" in obj and isinstance(obj["statistics"], dict):
            return obj["statistics"]
        for v in obj.values():
            found = locate_stats(v)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = locate_stats(item)
            if found:
                return found
    return None

stats = locate_stats(raw)
if not stats:
    print("❌  Could not locate any 'statistics' dict")
    print("Top-level keys:", list(raw.keys())[:10])
    sys.exit(1)

# ---------- clean numbers (strip %) -----------------------------------------
_pct = re.compile(r"^\s*([-+]?\d*\.?\d+)\s*%?\s*$")
cleaned = {}
for k, v in stats.items():
    try:
        if isinstance(v, (int, float)):
            cleaned[k] = float(v)
        else:
            cleaned[k] = float(_pct.match(str(v)).group(1))
    except Exception:
        pass                        # skip non-numeric

# ---------- upload ----------
db.collection("backtest_results").document(BACKTEST_ID).set({
    "name"      : raw.get("name", "Unnamed Backtest"),
    "createdAt" : firestore.SERVER_TIMESTAMP,
    "statistics": cleaned,
})
print(f"✅  Uploaded {len(cleaned)} stats fields for {BACKTEST_ID}")
