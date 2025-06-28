import os
import requests
import time
import json
import hashlib

QC_PROJECT_ID = "23708106"
QC_API_URL = "https://www.quantconnect.com/api/v2"

try:
    QC_USER_ID = os.environ["QC_USER_ID"]
    QC_API_TOKEN = os.environ["QC_API_TOKEN"]
    BACKTEST_ID = os.environ["BACKTEST_ID"]
except KeyError:
    print("Missing secrets or env vars (QC_USER_ID, QC_API_TOKEN, BACKTEST_ID)")
    exit(1)

# Timestamp and signature
timestamp = str(int(time.time()))
signature = hashlib.sha256(f"{QC_API_TOKEN}:{timestamp}".encode()).hexdigest()

headers = {
    "Accept": "application/json",
    "Timestamp": timestamp
}

auth = (QC_USER_ID, signature)

# Request backtest result
print(f"Downloading results for backtest ID: {BACKTEST_ID}")
response = requests.post(
    f"{QC_API_URL}/backtests/read",
    json={"backtestId": BACKTEST_ID},
    headers=headers,
    auth=auth
)

if response.status_code != 200:
    print("Failed to fetch backtest result:", response.text)
    exit(1)

data = response.json()

if not data.get("success"):
    print("Backtest read failed:", data)
    exit(1)

with open("backtest-results.json", "w") as f:
    json.dump(data, f)

print("Backtest results saved to backtest-results.json")
