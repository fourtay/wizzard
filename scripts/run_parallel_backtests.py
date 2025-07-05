#!/usr/bin/env python3
"""
Orchestrates running multiple backtests in parallel on QuantConnect.
"""
import os
import sys
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
    lean_executable = shutil.which("lean")
    if not lean_executable:
        print("❌ Critical Error: 'lean' executable not found.")
        sys.exit(1)
    print(f"✅ Found lean executable at: {lean_executable}")

    try:
        qc_user_id = os.environ["QC_USER_ID"]
        qc_api_token = os.environ["QC_API_TOKEN"]
    except KeyError as e:
        print(f"❌ Critical Error: Missing secret {e}. Ensure it's set in the workflow env.")
        sys.exit(1)

    if not CHILDREN_DIR.exists():
        print(f"❌ Children directory not found at: {CHILDREN_DIR}")
        return

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

        shutil.copy(ROOT / "main.py", child_dir)
        shutil.copy(ROOT / "parameter_schema.json", child_dir)
        shutil.copytree(ROOT / "strategies", child_dir / "strategies")
        shutil.copy(child_json, child_dir / "params.json")

        params = json.load(open(child_dir / "params.json"))
        backtest_name = f"Evolve-{child_id}-{params.get('STRATEGY_MODULE', 'n/a')}-{params.get('SYMBOL', 'n/a')}"

        # --- THIS IS THE FIX ---
        # Add the --verbose flag to get detailed logs from the LEAN CLI
        cmd = [
            lean_executable, "cloud", "backtest", str(child_dir),
            "--name", backtest_name,
            "--json",
            "--no-output",
            "--user-id", qc_user_id,
            "--api-token", qc_api_token,
            "--verbose"
        ]
        # --- END FIX ---
        
        print(f"  -> Launching: {backtest_name}")
        proc = subprocess.Popen(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append((child_id, proc))

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
                    print(f"  ❌ {child_id} -> Failed to get backtestId from output. STDOUT: {stdout.strip()}, STDERR: {stderr.strip()}")
            except json.JSONDecodeError:
                print(f"  ❌ {child_id} -> Failed to decode JSON from output. STDOUT: {stdout.strip()}, STDERR: {stderr.strip()}")
        else:
            # Print both stdout and stderr for better debugging
            print(f"  ❌ {child_id} -> Process failed. STDOUT: {stdout.strip()}, STDERR: {stderr.strip()}")

    with open("backtests.json", "w") as f:
        json.dump(backtest_ids, f, indent=2)

    print("\n📝 Wrote all backtest IDs to backtests.json")

if __name__ == "__main__":
    main()
