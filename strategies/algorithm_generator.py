import os, random, subprocess, pathlib, datetime, textwrap

# ----- Repo paths -----------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parent
STRATS = ROOT / "strategies"
TEMPLATE = STRATS / "template_algo.py"

# Make sure the directory exists
STRATS.mkdir(exist_ok=True)

# ----- Pick parent ----------------------------------------------------------
parents = sorted(STRATS.glob("algo_*.py"))
parent = parents[-1] if parents else TEMPLATE

with open(parent) as f:
    code = f.read()

# ----- Very small mutation --------------------------------------------------
# look for the RSI_PERIOD line and tweak it
for line in code.splitlines():
    if line.strip().startswith("RSI_PERIOD"):
        current = int(line.split("=")[1])
        new_period = max(3, min(30, current + random.choice([-2, -1, 1, 2])))
        code = code.replace(line, f"RSI_PERIOD = {new_period}")
        break

# ----- Prepend metadata ------------------------------------------------------
ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
header = textwrap.dedent(f"""
    # AUTO-GENERATED {ts}
    # parent: {parent.name}
""")
code = header + code

# ----- Write child -----------------------------------------------------------
child = STRATS / f"algo_{ts}.py"
child.write_text(code)
print(f"📝  Wrote {child.relative_to(ROOT)} (RSI_PERIOD={new_period})")

# ----- Commit & push ---------------------------------------------------------
subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
subprocess.run(["git", "config", "user.name", "GitHub Action"], check=True)
subprocess.run(["git", "add", str(child)], check=True)
subprocess.run(["git", "commit", "-m", f"chore: evolve strategy {child.name}"], check=True)
subprocess.run(["git", "push"], check=True)
print("🚀  Pushed; back-test workflow will trigger.")
