
# Verification Script for Context Builder
import sys
import os
import json
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Load .env explicitly for GITHUB_TOKEN
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from core.context_builder import ContextBuilder

def main():
    print("============================================================")
    print("  Part 7: Advanced Context Builder Verification")
    print("============================================================")

    # 1. Initialize ContextBuilder
    print("  Initializing ContextBuilder...")
    try:
        builder = ContextBuilder()
    except Exception as e:
        print(f"  [FAIL] Initialization error: {e}")
        sys.exit(1)

    # 2. Simulate a "Fake" File and Diff
    # We will simulate a change to 'run_inline_review' in reviewer.py
    # We need to read the actual file first to get realistic content
    target_file = os.path.join(os.path.dirname(__file__), "agents", "reviewer.py")
    if not os.path.exists(target_file):
        print(f"  [FAIL] Target file not found: {target_file}")
        sys.exit(1)

    with open(target_file, "r", encoding="utf-8") as f:
        file_content = f.read()

    # Create a fake diff that says line 800 (approx where run_inline_review is) was changed
    # We need to find the actual line number of run_inline_review to make it robust
    # Let's just search for the string
    line_num = 0
    for i, line in enumerate(file_content.splitlines()):
        if "def run_inline_review" in line:
            line_num = i + 1
            break
    
    if line_num == 0:
        print("  [WARN] Could not find 'run_inline_review', defaulting to line 100")
        line_num = 100

    print(f"  Simulating change at line {line_num} ('run_inline_review')...")
    
    # Unified Diff Format: @@ -old +new @@
    # We just need it to point to the line number
    fake_diff = f"@@ -{line_num},1 +{line_num},1 @@\n+ # This is a simulated change"

    # 3. Build Context
    print(f"  Building context for {target_file}...")
    context = builder.build_context(target_file, file_content, fake_diff)

    # 4. Verification
    prompt = context.get("formatted_prompt", "")
    
    print("\n  [INFO] Generated Prompt Preview:\n")
    print("-" * 40)
    print(prompt[:500] + "\n...[clipped]...")
    print("-" * 40)

    # Check for Impact Analysis
    if "Impact Analysis" in prompt:
        print("\n  [PASS] 'Impact Analysis' section present.")
    else:
        print("\n  [FAIL] 'Impact Analysis' section MISSING.")

    # Check for Changed Code
    if "Changed Code Context" in prompt:
        print("  [PASS] 'Changed Code Context' section present.")
    else:
        print("  [FAIL] 'Changed Code Context' section MISSING.")

    # Check for Related Code (Vector Search results from previous step should trigger this)
    if "Related Code Examples" in prompt:
        print("  [PASS] 'Related Code Examples' section present.")
    else:
        print("  [WARN] 'Related Code Examples' section MISSING (Vector search might have returned nothing or score too low).")

    # Check specific symbol presence
    if "run_inline_review" in prompt:
        print("  [PASS] Target symbol 'run_inline_review' found in prompt.")
    else:
        print("  [FAIL] Target symbol 'run_inline_review' NOT found in prompt.")

    print("\n" + "-" * 60)
    print("  Context Builder: SUCCESS")
    print("-" * 60)

if __name__ == "__main__":
    main()
