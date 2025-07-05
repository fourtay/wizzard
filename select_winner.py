# tools/algogen/select_winner.py
"""
Pick the highest-performing back-test from the most recent batch and
save its doc ID so the next generation can inherit it.
"""
import sys
import os
from typing import Any, Dict, List
from google.cloud import firestore

# --- ADD THIS AUTHENTICATION BLOCK ---
try:
    GCP_SA_KEY_JSON = os.environ["GCP_SA_KEY"]
    with open("gcp_key.json", "w") as fh:
        fh.write(GCP_SA_KEY_JSON)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"
except KeyError:
    print("❌ GCP_SA_KEY secret not set in GitHub Secrets.")
    sys.exit(1)
# --- END BLOCK ---


COLLECTION       = "backtest_results"
STATE_DOC_PATH   = "evolve_state/parent"
LOOKBACK_DOCS    = 25
METRIC_PATH      = ("statistics", "OOS Net Profit")
FALLBACK_METRIC_VALUE  = -999999.0

def pull_metric(d: Dict[str, Any]) -> float:
    """Safely extracts a nested metric from the backtest result document."""
    try:
        node = d
        for key in METRIC_PATH:
            node = node[key]
        return float(node)
    except (KeyError, TypeError, ValueError):
        return FALLBACK_METRIC_VALUE

def main():
    db = firestore.Client()
    print(f"Looking at last {LOOKBACK_DOCS} docs in '{COLLECTION}'…")
    print(f"Selecting winner based on: '{' -> '.join(METRIC_PATH)}'")

    recent: List[Any] = list(
        db.collection(COLLECTION)
          .order_by("createdAt", direction=firestore.Query.DESCENDING)
          .limit(LOOKBACK_DOCS)
          .stream()
    )
    if not recent:
        print("⚠️  No documents found; nothing to score.")
        sys.exit(0)

    winner = max(recent, key=lambda d: pull_metric(d.to_dict()))
    wdata  = winner.to_dict()
    wscore = pull_metric(wdata)

    print(f"--- Champion Candidate ---")
    print(f"Winner doc : {winner.id}")
    print(f"Metric Score: {wscore:.4f}")
    print(f"Parameters    : {wdata.get('params', {})}")
    print(f"------------------------")


    db.document(STATE_DOC_PATH).set(
        {
            "winner_doc": winner.id,
            "metric":     wscore,
            "params":     wdata.get("params", {}),
            "updatedAt":  firestore.SERVER_TIMESTAMP
        },
        merge=True,
    )
    print(f"✅ Saved winner info to Firestore document: {STATE_DOC_PATH}")

if __name__ == "__main__":
    main()
