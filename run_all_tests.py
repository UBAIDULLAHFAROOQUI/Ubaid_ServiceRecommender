"""
Master test runner — runs every test suite in the module in one shot.
    python run_all_tests.py
Use this before each submission to prove the whole AI module passes.
"""
import subprocess, sys

SUITES = [
    ("Service Recommender", "test_recommender.py"),
    ("Price Estimator", "test_price_estimator.py"),
    ("Sentiment Analysis", "test_sentiment.py"),
]

print("=" * 60)
print("CELINE ESTHETIQUE — AI MODULE TEST RUN")
print("=" * 60)

failed = []
for label, path in SUITES:
    print(f"\n>>> {label}  ({path})")
    print("-" * 60)
    r = subprocess.run([sys.executable, path], capture_output=True, text=True)
    out = r.stdout.strip()
    print(out if out else "(no output)")
    if r.returncode != 0 or "FAIL" in out:
        failed.append(label)

print("\n" + "=" * 60)
if failed:
    print("RESULT: FAILURES in -> " + ", ".join(failed))
    sys.exit(1)
print("RESULT: ALL SUITES PASSED ✅")
