#!/usr/bin/env python3
"""
Select the best child in the last generation and mark it as the champion.
"""

import os, sys, json, datetime
from google.cloud import firestore

METRIC = "compoundingAnnualReturn"         # ← change if you prefer
GEN_WINDOW_MINUTES = 40                    # any doc newer than this is "this gen"

def main():
    db = firestore.Client()

    since = datetime.datetime.utcnow() - datetime.timedelta(minutes=GEN_WINDOW_MINUTES)

    docs = (
        db.collection("backtest_results")
          .where("createdAt", ">", since)
          .stream()
    )

    best_doc = None
    best_val = float("-inf")

    for d in docs:
        stats = d.to_dict().get("statistics", {})
        val   = float(stats.get(METRIC, "0") or 0)
        if val > best_val:
            best_val  = val
            best_doc  = d

    if not best_doc:
        print("No docs found in this generation window; exiting 0.")
        return

    # Mark champion in Firestore
    best_doc.reference.update({"isChampion": True})
    print(f"🏆 Champion is {best_doc.id} with {METRIC}={best_val}")

    # write params locally for algo_gen.py
    params = best_doc.to_dict().get("params", {})
    with open("champion.json", "w") as f:
        json.dump(params, f, indent=2)

if __name__ == "__main__":
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
    main()
