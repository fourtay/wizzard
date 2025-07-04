#!/usr/bin/env python3
"""
Compare the just-finished back-test against the current champion.
If the candidate’s Sharpe Ratio is higher, tell GitHub Actions to promote it
and overwrite the champion document in Firestore.

Required env vars
-----------------
GCP_SA_KEY      – JSON for the service-account (already used by store_results.py)
BACKTEST_ID     – same value we used when saving the candidate’s results
FIRESTORE_PROJECT – your GCP project ID
"""

import os, json, sys, tempfile
from google.cloud import firestore

# ---------------- helper ------------------------------------------------------
def log(msg): print(f"🔎  {msg}", flush=True)

def get_stats(doc):
    """Return Sharpe Ratio (float) and dict of statistics from a Firestore doc"""
    stats = doc.to_dict().get("statistics", {})
    try:
        sharpe = float(stats.get("sharpeRatio") or stats.get("Sharpe Ratio") or 0)
    except ValueError:
        sharpe = 0
    return sharpe, stats

# ---------------- auth --------------------------------------------------------
try:
    sa_json = os.environ["GCP_SA_KEY"]
    project_id = os.environ["FIRESTORE_PROJECT"]
    backtest_id = os.environ["BACKTEST_ID"]
except KeyError as ke:
    log(f"Missing env var: {ke}")
    sys.exit(1)

with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
    tmp.write(sa_json)
    cred_path = tmp.name

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
db = firestore.Client(project=project_id)
log("Connected to Firestore.")

# ---------------- fetch docs --------------------------------------------------
cand_ref = db.collection("backtest_results").document(backtest_id)
cand_doc = cand_ref.get()
if not cand_doc.exists:
    log(f"Candidate result {backtest_id} not found.")
    sys.exit(1)

champ_ref = db.collection("backtest_results").document("champion")
champ_doc = champ_ref.get()

cand_sharpe, cand_stats = get_stats(cand_doc)
champ_sharpe, champ_stats = get_stats(champ_doc) if champ_doc.exists else (0, {})

log(f"Candidate Sharpe:  {cand_sharpe}")
log(f"Champion  Sharpe:  {champ_sharpe}")

promote = cand_sharpe > champ_sharpe
log(f"Promote? {'YES' if promote else 'no'}")

# ---------------- output for GitHub Actions -----------------------------------
github_output = os.environ.get("GITHUB_OUTPUT")
if github_output:
    with open(github_output, "a") as fh:
        fh.write(f"promote={'true' if promote else 'false'}\n")

# ---------------- update champion doc if better ------------------------------
if promote:
    champ_ref.set({
        **cand_doc.to_dict(),
        "promotedFrom": backtest_id
    })
    log("Champion document updated.")

log("Evaluation complete.")
