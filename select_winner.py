# tools/algogen/select_winner.py
"""
Pick the highest-performing back-test from the most recent batch
based on its Out-of-Sample (OOS) performance.
Save its doc ID so the next generation can inherit it.
"""
import sys
from typing import Any, Dict, List
from google.cloud import firestore

COLLECTION       = "backtest_results"
STATE_DOC_PATH   = "evolve_state/parent"
LOOKBACK_DOCS    = 25

# --- The key change is here: Point to the Out-of-Sample metric ---
# We are using "OOS Net Profit" as it's the most reliable metric
# we implemented without a complex Sharpe Ratio calculation.
METRIC_PATH      = ("statistics", "OOS Net Profit")
FALLBACK_METRIC_VALUE  = -999999.0
# -------------------------------------------------------------

def pull_metric(d: Dict[str, Any]) -> float:
    """Safely extracts a nested metric from the backtest result document."""
    try:
        node = d
        for key in METRIC_PATH:
            node = node[key]
        # The value is stored as a string, so convert it to float
        return float(node)
    except (KeyError, TypeError, ValueError) as e:
        # print(f"Warning: Could not pull metric for doc. Error: {e}", file=sys.stderr)
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
    print(f"------------------------")

    # If no strategy made a profit in the OOS period, maybe don't promote a new one.
    if wscore <= 0:
        print("⚠️  No candidate had positive out-of-sample performance. Not promoting a new champion.")
        # You might choose to exit here or let it continue with the old champion.
        # For evolution, it's often better to pick the "least bad" one.

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
