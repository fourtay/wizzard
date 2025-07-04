#!/usr/bin/env python3
"""
Select the best strategy out of latest back-test runs + current champion.

Logic:
  * Filter to docs in Firestore collection `backtest_results`
      where runTimestamp >= RUN_START (passed in as env)
  * Compute a single fitness score:
        fitness = sharpeRatio - maxDrawdown * 2
    (Drawdown is penalised; tune weight later).
  * If a child beats the old champion, overwrite champion.json
"""
import os, json, sys, datetime as dt
from google.cloud import firestore

COLL = "backtest_results"
RUN_START = os.getenv("RUN_START")            # ISO string from evolve.yml
OUT_FILE = "champion.json"

db = firestore.Client()
query = db.collection(COLL)
if RUN_START:
    ts = dt.datetime.fromisoformat(RUN_START)
    query = query.where("createdAt", ">", ts)

docs = list(query.stream())
if not docs:
    print("No new back-tests found; exit.")
    sys.exit(0)

def fitness(stat):
    """Higher is better."""
    sharpe = float(stat.get("sharpeRatio", 0))
    dd     = float(stat.get("drawdown", 1))   # 0.092 -> 9.2 %
    return sharpe - dd * 2.0

best_doc = max(docs, key=lambda d: fitness(d.get("statistics", {})))
best_stat = best_doc.get("statistics", {})
best_fit  = fitness(best_stat)

print(f"🏆  Top candidate {best_doc.id}  fitness={best_fit:.3f}")

# compare to current champion (if exists)
if os.path.exists(OUT_FILE):
    with open(OUT_FILE) as f:
        champ = json.load(f)
    champ_fit = fitness(champ["statistics"])
    if champ_fit >= best_fit:
        print("Current champion is still better. Keep it.")
        sys.exit(0)

# promote newcomer
new_champ = {
    "backtestId": best_doc.id,
    "statistics": best_stat,
    "parameters": best_doc.get("parameters", {})   # store for next gen
}
with open(OUT_FILE, "w") as f:
    json.dump(new_champ, f, indent=2)
print("🎉  New champion saved to champion.json")
