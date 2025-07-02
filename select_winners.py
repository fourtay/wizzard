#!/usr/bin/env python3
# wizard/select_winners.py
"""
Fetch back-test docs for *this* generation, rank them, and print the top N.

Env vars expected:
    GCP_SA_KEY   – service-account JSON (already in secrets)
    GENERATION   – e.g. 'evolve-20240331-gen01'
    TOP_K        – how many winners to keep (default 2)
    METRIC       – which stats field to sort DESC on (default 'sharpeRatio')
"""
import os, json, sys, tempfile, operator
from google.cloud import firestore

GEN = os.environ.get("GENERATION")
TOP_K = int(os.environ.get("TOP_K", 2))
METRIC = os.environ.get("METRIC", "sharpeRatio")

if not GEN:
    sys.exit("GENERATION env var missing")

# ───── connect
with tempfile.NamedTemporaryFile("w", delete=False) as f:
    f.write(os.environ["GCP_SA_KEY"])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
db = firestore.Client()

coll = db.collection("backtest_results")
docs = coll.where(firestore.FieldPath.document_id(), ">=", GEN) \
           .where(firestore.FieldPath.document_id(), "<",  GEN + "~") \
           .stream()

candidates = []
for d in docs:
    stats = d.to_dict().get("statistics", {})
    val = float(stats.get(METRIC, 0))
    candidates.append((val, d.id, stats))
if not candidates:
    sys.exit("No docs found for generation " + GEN)

# sort DESC by metric
winners = sorted(candidates, key=operator.itemgetter(0), reverse=True)[:TOP_K]
print("🏆  Winners:", winners)

# emit a winners.json for the workflow
with open("winners.json", "w") as f:
    json.dump(
        [{"id": doc_id, METRIC: val} for (val, doc_id, _) in winners],
        f, indent=2)
print("Wrote winners.json")
