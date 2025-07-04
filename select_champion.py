#!/usr/bin/env python3
"""
select_champion.py – pick the best-performing child algo
"""

import os, sys, json, datetime
from google.cloud import firestore

COLL = "backtest_results"          # Firestore collection
METRIC = "Net Profit"              # ← change if you prefer Sharpe etc.

#
# 0. secrets
#
try:
    with open("gcp_key.json", "w") as fh:
        fh.write(os.environ["GCP_SA_KEY"])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
except KeyError:
    print("missing GCP_SA_KEY"); sys.exit(1)

db = firestore.Client()

#
# 1. read latestgeneration’s docs
#
today = datetime.date.today()
docs = list(db.collection(COLL).where(
            "createdAt", ">=", datetime.datetime(today.year, today.month, today.day)
        ).stream())

if not docs:
    print("no today docs – abort"); sys.exit(0)

#
# 2. pick champion
#
def score(d):      # higher is better
    return float(d["statistics"].get(METRIC, 0))

champ = max(docs, key=lambda d: score(d.to_dict()))
cdata = champ.to_dict()

print("🏆  champion", champ.id, score(cdata))

#
# 3. write artefact
#
with open("champion.json", "w") as fh:
    json.dump(cdata, fh, indent=2)
# also overwrite parent seed
with open("parent_algo.json", "w") as fh:
    json.dump(cdata["algo"], fh, indent=2)     # assumes you stored algo params under 'algo'
