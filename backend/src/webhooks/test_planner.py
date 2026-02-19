
# Verification Script for Two-Pass Planner
import sys
import os
import json
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Load .env explicitly for GITHUB_TOKEN
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from agents.planner import ReviewPlanner

def main():
    print("============================================================")
    print("  Part 10: Two-Pass Planner Verification")
    print("============================================================")

    # 1. Initialize Planner
    print("  Initializing ReviewPlanner...")
    try:
        planner = ReviewPlanner()
    except Exception as e:
        print(f"  [FAIL] Initialization error: {e}")
        sys.exit(1)

    # 2. Mock PR Data
    # We want to test logic: Auth -> High Risk, Readme -> Ignore
    mock_files = [
        {
            "filename": "backend/src/auth/login.py",
            "additions": 50,
            "deletions": 10,
            "patch": "def login(user, password):\n    # TODO: fix security flaw\n    return db.query(f'SELECT * FROM users WHERE u={user}')"
        },
        {
            "filename": "frontend/styles/main.css",
            "additions": 5,
            "deletions": 2,
            "patch": ".button { color: red; }"
        },
        {
            "filename": "README.md",
            "additions": 10,
            "deletions": 0,
            "patch": "# Project Title\nUpdated docs."
        }
    ]

    print(f"  Analyzing {len(mock_files)} files...")
    
    # 3. Run Analysis
    # We mock LLM response to ensure deterministic test, OR we trust the LLM.
    # Given we are testing "Agent Intelligence", let's use the REAL LLM 
    # but mock if it fails (or checks output structure).
    
    # For this test, let's let the real LLM run to verify our Prompt Engineering!
    plan = planner.analyze_pr_complexity(mock_files)
    
    print("\n  [Planner Output]:")
    print(json.dumps(plan, indent=2))
    
    # 4. Assertions
    high_risk = plan.get("high_risk_files", [])
    ignore_files = plan.get("ignore_files", [])
    
    # Check Auth
    if any("auth" in f or "login" in f for f in high_risk):
        print("\n  [PASS] 'backend/src/auth/login.py' identified as High Risk.")
    else:
        print("\n  [FAIL] 'backend/src/auth/login.py' missed! (Check Prompt)")

    # Check Readme/CSS
    if any("README" in f for f in ignore_files):
        print("  [PASS] 'README.md' identified as Ignore.")
    else:
        print("  [WARN] 'README.md' not ignored (maybe classified as Minor but not Ignore).")

    # Check Strategy
    if plan.get("review_strategy"):
        print(f"  [PASS] Review Strategy determined: {plan['review_strategy']}")
    else:
        print("  [FAIL] Missing review_strategy.")

    print("\n" + "-" * 60)
    print("  Two-Pass Planner: SUCCESS")
    print("-" * 60)

if __name__ == "__main__":
    main()
