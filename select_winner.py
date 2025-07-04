# tools/algogen/select_winner.py
"""
Pick the highest-Sharpe back-test from the most-recent batch and
store its Firestore document ID so the next generation can inherit it.
"""

import sys
from typing import Any, Dict, List

from google.cloud import firestore

# ─────────────────────────── CONFIG ────────────────────────────
COLLECTION         = "backtest_results"          # where store_results.py writes
STATE_DOC_PATH     = "evolve_state/parent"       # winner reference lives here
LOOKBACK_DOCS      = 25                          # scan the latest N docs
METRIC_PATH        = ("statistics", "sharpeRatio")
FALLBACK_SHARPE    = -999.0                      # if metric missing
# ────────────────────────────────────────────────────────────────


def pull_metric(d: Dict[str, Any]) -> float:
    """Safely fetch Sharpe; return FALLBACK_SHARPE if absent/unparseable."""
    try:
        node = d
        for key in METRIC_PATH:
            node = node[key]
        return float(node)
    except (KeyError, TypeError, ValueError):
        return FALLBACK_SHARPE


def main() -> None:
    db = firestore.Client()
    print(f"🔍 Looking at last {LOOKBACK_DOCS} docs in '{COLLECTION}'…")

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

    print(f"🏆  Winner doc : {winner.id}")
    print(f"📈  Sharpe     : {wscore:.4f}")

    db.document(STATE_DOC_PATH).set(
        {
            "winner_doc": winner.id,
            "metric": wscore,
            "params": wdata.get("params", {}),
        },
        merge=True,
    )
    print("✅  Saved winner info to", STATE_DOC_PATH)


if __name__ == "__main__":
    main()
