# tools/algogen/select_winner.py
"""
Pick a winner from the most recent batch by finding the most stable
and profitable "cluster" of parameters.
Saves the winner's doc ID so the next generation can inherit it.
"""
import sys
import math
from typing import Any, Dict, List
from google.cloud import firestore

COLLECTION       = "backtest_results"
STATE_DOC_PATH   = "evolve_state/parent"
LOOKBACK_DOCS    = 25 # The number of recent backtests to evaluate

# --- Metric to judge performance ---
METRIC_PATH      = ("statistics", "OOS Net Profit")
FALLBACK_METRIC_VALUE  = -999999.0

# --- Clustering parameters ---
# How close params need to be to be considered "neighbors"
NEIGHBOR_TOLERANCE_FAST = 2
NEIGHBOR_TOLERANCE_SLOW = 5

def pull_metric(d: Dict[str, Any]) -> float:
    """Safely extracts a nested metric from the backtest result document."""
    try:
        node = d
        for key in METRIC_PATH:
            node = node[key]
        return float(node)
    except (KeyError, TypeError, ValueError):
        return FALLBACK_METRIC_VALUE

def get_params(d: Dict[str, Any]) -> Dict[str, Any]:
    """Safely extracts the parameters dictionary."""
    return d.get("params", {})

def main():
    db = firestore.Client()
    print(f"🔍 Looking at last {LOOKBACK_DOCS} docs in '{COLLECTION}'…")
    print(f"🏆 Selecting winner based on stable clusters of: '{' -> '.join(METRIC_PATH)}'")

    recent_docs: List[Any] = list(
        db.collection(COLLECTION)
          .order_by("createdAt", direction=firestore.Query.DESCENDING)
          .limit(LOOKBACK_DOCS)
          .stream()
    )
    if not recent_docs:
        print("⚠️  No documents found; nothing to score.")
        sys.exit(0)

    # --- Convert Firestore docs to a more usable list of dictionaries ---
    candidates = []
    for doc in recent_docs:
        data = doc.to_dict()
        candidates.append({
            "id": doc.id,
            "score": pull_metric(data),
            "params": get_params(data)
        })

    best_candidate_id = None
    max_cluster_score = -float('inf')

    # --- Find the best "cluster" instead of just the single best score ---
    for cand in candidates:
        cand_params = cand.get("params")
        if not cand_params: continue

        # Find all neighbors of the current candidate
        neighbors = []
        for other in candidates:
            if cand["id"] == other["id"]: continue
            other_params = other.get("params")
            if not other_params: continue

            # Check if symbols match and periods are within tolerance
            if cand_params.get("SYMBOL") == other_params.get("SYMBOL"):
                fast_dist = abs(cand_params.get("FAST_PERIOD", 0) - other_params.get("FAST_PERIOD", 0))
                slow_dist = abs(cand_params.get("SLOW_PERIOD", 0) - other_params.get("SLOW_PERIOD", 0))
                if fast_dist <= NEIGHBOR_TOLERANCE_FAST and slow_dist <= NEIGHBOR_TOLERANCE_SLOW:
                    neighbors.append(other)

        # Score the cluster (average score of the candidate and its neighbors)
        if not neighbors: continue # Skip candidates with no neighbors
        
        cluster_scores = [cand["score"]] + [n["score"] for n in neighbors]
        avg_cluster_score = sum(cluster_scores) / len(cluster_scores)

        # Promote the candidate from the best-performing, stable neighborhood
        if avg_cluster_score > max_cluster_score:
            max_cluster_score = avg_cluster_score
            best_candidate_id = cand["id"]

    if not best_candidate_id:
        print("⚠️  Could not find any stable clusters. Promoting the single best score as a fallback.")
        # Fallback to picking the single best if no clusters are found
        winner = max(candidates, key=lambda c: c['score'])
        best_candidate_id = winner['id']

    # --- Get final winner data and save it ---
    winner_doc = db.collection(COLLECTION).document(best_candidate_id).get()
    wdata = winner_doc.to_dict()
    wscore = pull_metric(wdata)

    print(f"\n--- 👑 New Champion Selected ---")
    print(f"Winner Doc ID: {winner_doc.id}")
    print(f"Winning Score: {wscore:.2f}")
    if max_cluster_score > -float('inf'):
        print(f"Cluster Score : {max_cluster_score:.2f} (This indicates stability)")
    print(f"Parameters    : {wdata.get('params', {})}")
    print(f"---------------------------------")

    db.document(STATE_DOC_PATH).set(
        {
            "winner_doc": winner_doc.id,
            "metric":     wscore,
            "params":     wdata.get("params", {}),
            "updatedAt":  firestore.SERVER_TIMESTAMP
        },
        merge=True,
    )
    print(f"\n✅ Saved winner info to Firestore document: {STATE_DOC_PATH}")

if __name__ == "__main__":
    main()
