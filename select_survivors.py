# wizard/select_survivors.py
"""
Pick the best Sharpe-ratio children from Firestore and write them into
parents.txt so the next generation knows who to mutate.
"""
import os, pathlib, sys, tempfile
from google.cloud import firestore

COLLECTION      = os.getenv("BACKTEST_COLLECTION", "backtest_results")
NUM_SURVIVORS   = int(os.getenv("NUM_SURVIVORS", "2"))

# ---- Firestore auth (reuse the existing secret) ----
with tempfile.NamedTemporaryFile("w", delete=False) as f:
    f.write(os.environ["GCP_SA_KEY"])
    cred_path = f.name
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
db = firestore.Client()
print("🔑  Firestore authenticated")

# ---- Pull recent back-tests ----
docs = (db.collection(COLLECTION)
          .order_by("createdAt", direction=firestore.Query.DESCENDING)
          .stream())

candidates = []
for d in docs:
    data   = d.to_dict()
    stats  = data.get("statistics", {})
    sharpe = float(stats.get("sharpeRatio") or 0)
    path   = data.get("algoPath")           # we saved this earlier
    if path:
        candidates.append((sharpe, path))
    if len(candidates) > 100:               # look at most recent 100
        break

if not candidates:
    sys.exit("❌  No back-test docs found")

candidates.sort(reverse=True)               # best Sharpe first
survivors = [p for _, p in candidates[:NUM_SURVIVORS]]
print("🏆  Survivors picked:", survivors)

# ---- Write the survivor list ----
path = pathlib.Path("parents.txt")
path.write_text("\n".join(survivors) + "\n")
print("📝  parents.txt updated")
