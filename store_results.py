import os, json, sys, re
from google.cloud import firestore

RESULTS_FILE_PATH = "backtest-results.json"

# --- cred ---
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

# --- read results ---
try:
    with open(RESULTS_FILE_PATH) as f:
        raw = json.load(f)
except Exception as e:
    print(f"❌  Cannot read {RESULTS_FILE_PATH}: {e}")
    sys.exit(1)

# --- helper: str → float ------------------------------------------------------
import re
_pct = re.compile(r"^\s*([-+]?\d*\.?\d+)\s*%?\s*$")
def to_float(x):
    if isinstance(x, (int, float)):
        return float(x)
    m = _pct.match(str(x))
    if not m:
        raise ValueError
    return float(m.group(1))

# --- harvest statistics regardless of nesting --------------------------------
stats = {}

def walk(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.startswith("statistics."):
                try:
                    stats[k.split(".", 1)[1]] = to_float(v)
                except ValueError:
                    pass                         # skip non-numeric
            walk(v)
    elif isinstance(obj, list):
        for item in obj:
            walk(item)

walk(raw)

if not stats:
    print("❌  No statistics.* fields found anywhere in JSON")
    print("Top-level keys:", list(raw.keys())[:10])
    sys.exit(1)

# --- upload ------------------------------------------------------------------
db.collection("backtest_results").document(BACKTEST_ID).set({
    "name"      : raw.get("name", "Unnamed Backtest"),
    "createdAt" : firestore.SERVER_TIMESTAMP,
    "statistics": stats,
})
print(f"✅  Uploaded {len(stats)} numeric fields for {BACKTEST_ID}")
