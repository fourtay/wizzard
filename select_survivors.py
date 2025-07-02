#!/usr/bin/env python3
"""
Load every results.json, compute Sharpe, keep top NUM_SURVIVORS,
write their folder names into parents.txt (one per line).
Also push summary stats to Firestore for Looker.
"""
import json, os, pathlib, operator
from google.cloud import firestore

NUM_SURVIVORS = int(os.getenv("NUM_SURVIVORS", "2"))
COLLECTION    = os.getenv("BACKTEST_COLLECTION", "backtest_results")
GCP_SA_KEY    = os.environ["GCP_SA_KEY"]

# Firestore auth
open("gcp_key.json", "w").write(GCP_SA_KEY)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
db = firestore.Client()

ROOT = pathlib.Path(__file__).parent / "children"
scores = []

for child in ROOT.iterdir():
    fn = child / "results.json"
    if not fn.exists():
        continue
    data = json.loads(fn.read_text())
    stats = data["backtest"]["portfolioStatistics"]
    sharpe = float(stats["sharpeRatio"])
    scores.append((child.name, sharpe, stats))

# pick winners
scores.sort(key=operator.itemgetter(1), reverse=True)
survivors   = scores[:NUM_SURVIVORS]
with open("parents.txt", "w") as f:
    f.writelines(name + "\n" for name, _, _ in survivors)
print("🏆  survivors:", [s[0] for s in survivors])

# upload each to Firestore
for name, sharpe, stats in survivors:
    doc = {
        "child": name,
        "sharpe": sharpe,
        "stats": stats
    }
    db.collection(COLLECTION).add(doc)
    print(f"☁️  pushed {name} to Firestore")
