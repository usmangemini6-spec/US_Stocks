"""
build_cycles.py - builds the Cycles pages of the website into website\\US_Stocks\\cycles\\.
Reads the data in scripts\\cycles_data\\ (run download_cycle_data.py first) and forecast_calls.json.
Run:  python cycles_builder\\build_cycles.py     (or RUN_CYCLES.bat)
"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(HERE, "work"), exist_ok=True)
STEPS = [("cycle models", "build3.py"), ("long-term cycles", "longterm.py"), ("forecast vs actual", "lw.py"),
         ("combined S&P forecast", "fc.py"), ("AI bubble gauge", "dev.py"),
         ("tested cycle signals", "sigbuild.py"), ("pages", "gen.py")]
for label, script in STEPS:
    print(f"- {label} ...")
    r = subprocess.run([sys.executable, "-X", "utf8", script], cwd=HERE)
    if r.returncode:
        print(f"*** {script} failed ***")
        sys.exit(1)
print("Done: website\\US_Stocks\\cycles\\ (open cycles\\index.html)")
