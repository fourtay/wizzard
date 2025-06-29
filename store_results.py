import os, json, sys, re
from google.cloud import firestore

# ---------- Settings ----------
RESULTS_FILE_PATH = "backtest-results.json"

# ---------- Credentials ----------
try:
    GCP_SA_KEY_JSON = os.environ["GCP_SA_KEY"]
    BACKTEST_ID     = os.environ["BACKTEST_ID"]
except KeyError:
    print("❌  GCP_SA_KEY or BACKTEST_ID env-var missing")
    sys.exit(1)

with open("gcp_key.json", "w") as f:
    f.write(GCP_SA_KEY_JSON)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
db = firestore.Client()
print("✅  Connected to Firestore")

# ---------- Read results ----------
try:
    with open(RESULTS_FILE_PATH, "r") as f:
        raw = json.load(f)
except Exception as e:
    print(f"❌  Cannot read {RESULTS_FILE_PATH}: {e}")
    sys.exit(1)

# ---------- Helpers ----------
pct_re = re.compile(r"^\s*([-+]?\d*\.?\d+)\s*%?\s*$")     # grabs the number, ignores a trailing %
def to_number(val: str) -> float:
    """
    "12.93%"  -> 12.93
    "0.145"   -> 0.145
    42        -> 42
    """
    if isinstance(val, (int, float)):
        return float(val)
    m = pct_re.match(str(val))
    if not m:
        raise ValueError(f"Cannot convert '{val}' to float")
    return float(m.group(1))

# ---------- Clean statistics ----------
stats_src = raw.get("statistics") or raw.get("results", {}).get("statistics")
if not stats_src:
    print("❌  'statistics' block not found")
    sys.exit(1)

statistics = {}
for k, v in stats_src.items():
    try:
        statistics[k] = to_number(v)
    except ValueError:
        print(f"⚠️  Skipping non-numeric field {k}: {v}")

# ---------- Upload ----------
doc_ref = db.collection("backtest_results").document(BACKTEST_ID)
doc_ref.set({
    "name"      : raw.get("name", "Unnamed Backtest"),
    "createdAt" : firestore.SERVER_TIMESTAMP,
    "statistics": statistics,
    "charts"    : raw.get("charts", {})
})
print("✅  Uploaded numeric stats for", BACKTEST_ID)
