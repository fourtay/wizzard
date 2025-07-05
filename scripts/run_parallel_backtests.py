#!/usr/bin/env python3
"""
Orchestrates running multiple backtests in parallel on QuantConnect.

This script finds all generated child parameter files, creates isolated directories
for each, and launches a Lean cloud backtest for each one using subprocess.

It captures the `backtestId` from each run and saves them to `backtests.json`.
"""
import os
import json
import subprocess
import pathlib
import shutil

# The root directory of the project
ROOT = pathlib.Path(__file__).parent.parent
CHILDREN_DIR = ROOT / "children"
TMP_DIR = ROOT / ".tmp_children"

def main():
    """Main execution function."""
    if not CHILDREN_DIR.exists():
        print(f"❌ Children directory not found at: {CHILDREN_DIR}")
        return

    # Clean up any previous temporary directories
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    TMP_DIR.mkdir()

    processes = []
    child_files = list(CHILDREN_DIR.glob("*.json"))

    if not child_files:
        print("🤷 No child strategy files found to backtest.")
        return

    print(f"🚀 Found {len(child_files)} children. Preparing to launch backtests in parallel...")

    for child_json in child_files:
        child_id = child_json.stem
        child_dir = TMP_DIR / child_id
        child_dir.mkdir()

        # Copy necessary source files to the isolated directory
        shutil.copy(ROOT / "main.py", child_dir)
        shutil.copy(ROOT / "parameter_schema.json", child_dir)
        shutil.copytree(ROOT / "strategies", child_dir / "strategies")
        shutil.copy(child_json, child_dir / "params.json")

        # Construct a unique name for the backtest
        params = json.load(open(child_dir / "params.json"))
        strategy_module = params.get("STRATEGY_MODULE", "unknown")
        symbol = params.get("SYMBOL", "unknown")
        backtest_name = f"Evolve-{child_id}-{strategy_module}-{symbol}"

        # Command to run the backtest using the lean CLI
        cmd = [
            "lean", "cloud", "backtest", str(child_dir),
            "--name", backtest_name,
            "--json",  # Output results as JSON to capture the backtestId
            "--no-output" # Don't save the full results.json here
        ]
        
        print(f"  -> Launching: {backtest_name}")
        # Launch the backtest process in the background
        proc = subprocess.Popen(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append((child_id, proc))

    # --- Wait for all processes to complete and collect results ---
    backtest_ids = {}
    print("\n✅ All backtests submitted. Waiting for QuantConnect to return IDs...")
    for child_id, proc in processes:
        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            try:
                result_json = json.loads(stdout)
                backtest_id = result_json.get("backtestId")
                if backtest_id:
                    print(f"  ✔️ {child_id} -> Backtest ID: {backtest_id}")
                    backtest_ids[child_id] = backtest_id
                else:
                    print(f"  ❌ {child_id} -> Failed to get backtestId from output: {stdout}")
            except json.JSONDecodeError:
                print(f"  ❌ {child_id} -> Failed to decode JSON from output: {stdout}")
        else:
            print(f"  ❌ {child_id} -> Process failed with error: {stderr}")

    # Save the mapping of child names to backtest IDs
    with open("backtests.json", "w") as f:
        json.dump(backtest_ids, f, indent=2)

    print("\n📝 Wrote all backtest IDs to backtests.json")

if __name__ == "__main__":
    main()
