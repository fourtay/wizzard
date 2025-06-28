import os, sys, json, pathlib
from collections import deque
from google.cloud import firestore

# ──────────────────────────── CONSTANTS ────────────────────────────
RESULTS_FILE = pathlib.Path("backtest-results.json")   # LEAN CLI output
COLLECTION    = "backtest_results"                    # Firestore collection
# ────────────────────────── ENV-VAR CHECKS ─────────────────────────
try:
    SERVICE_KEY = os.environ["GCP_SA_KEY"]            # GitHub secret
    BACKTEST_ID = os.environ["BACKTEST_ID"]           # set in workflow
except KeyError:
    print("❌  Missing env vars GCP_SA_KEY or BACKTEST_ID"); sys.exit(1)

# ────────────────────────── FIRESTORE LOGIN ───────────────────────
with open("gcp_key.json", "w") as f:
    f.write(SERVICE_KEY)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
db = firestore.Client()
print("✅  Connected to Firestore")

# ────────────────────────── LOAD RESULT JSON ──────────────────────
if not RESULTS_FILE.exists():
    print(f"❌  {RESULTS_FILE} not found"); sys.exit(1)

with RESULTS_FILE.open() as f:
    try:
        data = json.load(f)
    except json.JSONDecodeError:
        print("❌  results file is not valid JSON"); sys.exit(1)

# ------------------------------------------------------------------
#  UTIL: breadth–first search for first dict containing key pattern
# ------------------------------------------------------------------
def find_section(root: dict, candidate_keys: list[str]) -> dict | None:
    queue = deque([root])
    while queue:
        node = queue.popleft()
        if isinstance(node, dict):
            if any(k in node for k in candidate_keys):
                return node
            queue.extend(node.values())
        elif isinstance(node, list):
            queue.extend(node)
    return None

# ────────────────────── EXTRACT STATISTICS / CHARTS ───────────────
# Keys we accept as "statistics"
STAT_KEYS = [
    "statistics",
    "portfolioStatistics",
    "totalNetProfit",     # leaf-level heuristics
    "sharpeRatio",
]

section = find_section(data, STAT_KEYS)

if not section:
    print("❌  Could not locate statistics block in JSON – aborting."); sys.exit(1)

# Normalise what we found ──────────────────────────────────────────
statistics = (
    section.get("statistics")
    or section.get("portfolioStatistics")
    or {k: section[k] for k in section if isinstance(section[k], (int, float, str))}
)

charts = section.get("charts") or data.get("charts") or {}

print("📊  Statistics keys found:", list(statistics.keys())[:10], "…")

# ──────────────────────── UPLOAD TO FIRESTORE ─────────────────────
payload = {
    "name"      : data.get("name", "Unnamed Backtest"),
    "createdAt" : firestore.SERVER_TIMESTAMP,
    "statistics": statistics,
    "charts"    : charts,
}

print(f"⬆️  Uploading document '{BACKTEST_ID}' to '{COLLECTION}' …")
db.collection(COLLECTION).document(BACKTEST_ID).set(payload)
print("🎉  Backtest results uploaded successfully!")
