#!/usr/bin/env python3
"""
Delete Firestore docs older than N days or outside the last K runs.

• TARGET_COLL  – name of results collection
• KEEP_DAYS    – minimum age to keep (e.g. 14)
• KEEP_LATEST  – always keep the newest K docs, even if older than KEEP_DAYS
"""
import os, sys, datetime as dt
from google.cloud import firestore

TARGET_COLL = "backtest_results"
KEEP_DAYS   = int(os.getenv("KEEP_DAYS", 14))
KEEP_LATEST = int(os.getenv("KEEP_LATEST", 200))

cutoff = dt.datetime.utcnow() - dt.timedelta(days=KEEP_DAYS)

db   = firestore.Client()
coll = db.collection(TARGET_COLL)

docs = list(coll.order_by("createdAt").stream())
if len(docs) <= KEEP_LATEST:
    print("Nothing to prune – below KEEP_LATEST threshold")
    sys.exit(0)

victims = [
    d for d in docs[:-KEEP_LATEST]     # keep youngest KEEP_LATEST docs
    if d.get("createdAt") and d.get("createdAt") < cutoff
]

print(f"🧹  Purging {len(victims)} docs older than {KEEP_DAYS} days…")
batch = db.batch()
for doc in victims:
    batch.delete(doc.reference)
batch.commit()
print("✅  Prune finished")
