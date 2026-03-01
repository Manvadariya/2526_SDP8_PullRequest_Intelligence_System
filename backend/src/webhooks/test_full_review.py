
# Verification Script for Full Intelligent Review
import sys
import os
import json
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Load .env explicitly for GITHUB_TOKEN
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from agents.reviewer import ReviewerAgent

def main():
    print("============================================================")
    print("  Part 8: Intelligent Agent Integration Verification")
    print("============================================================")

    # 1. Initialize Agent
    print("  Initializing ReviewerAgent...")
    try:
        agent = ReviewerAgent()
    except Exception as e:
        print(f"  [FAIL] Initialization error: {e}")
        sys.exit(1)

    # 2. Setup Context
    # We use the current repo path as the target
    repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # src/webhooks -> src -> backend
    # Actually, let's just point to the folder containing 'agents/reviewer.py'
    # The agent expects repo_path to be the root where 'filepath' is relative from.
    # reviewer.py is in backend/src/webhooks/agents/reviewer.py
    # if diff filepath is 'agents/reviewer.py', repo_path should be 'backend/src/webhooks'
    repo_path = os.path.join(os.path.dirname(__file__))

    target_file = "agents/reviewer.py"
    full_target_path = os.path.join(repo_path, target_file)
    
    if not os.path.exists(full_target_path):
        print(f"  [FAIL] Target file not found: {full_target_path}")
        # Try adjusting repo_path
        # If script is in webhooks/, and reviewer.py is in webhooks/agents/reviewer.py
        # then absolute path is correct.
        pass

    # 3. Simulate Diff
    # We simulate a semantic change to run_inline_review
    # We need to find the line number
    with open(full_target_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    line_num = 0
    for i, line in enumerate(content.splitlines()):
        if "def run_inline_review" in line:
            line_num = i + 1
            break
            
    if line_num == 0: line_num = 100

    print(f"  Simulating change to {target_file} at line {line_num}...")
    
    # Fake diff used by DiffParser
    fake_diff = f"""diff --git a/{target_file} b/{target_file}
index 1234567..890abcd 100644
--- a/{target_file}
+++ b/{target_file}
@@ -{line_num},1 +{line_num},1 @@
-    def run_inline_review(self, raw_diff: str, pr_title: str, custom_instructions: str, custom_checks: list = None, repo_path: str = None) -> dict:
+    def run_inline_review_modified(self, raw_diff: str, pr_title: str, custom_instructions: str, custom_checks: list = None, repo_path: str = None) -> dict:
"""

    # 4. Run Review (Dry Run - we verify the PROMPT mainly, but here we run it)
    # Since we can't easily intercept the prompt without mocking LLM, 
    # we will rely on the fact that if it runs without error, the context builder worked.
    # ideally we would use a mock LLM.
    
    # Let's mock the LLM client to just print the prompt and return dummy JSON
    class MockLLMClient:
        def __init__(self):
            self.chat = self
            self.completions = self
        
        def create(self, model, messages):
            prompt = messages[0]["content"]
            print("\n  [INFO] Intercepted Prompt (Preview):\n")
            print("-" * 40)
            # Find the context section
            if "INTELLIGENT CONTEXT" in prompt:
                start = prompt.find("INTELLIGENT CONTEXT")
                print(prompt[start:start+1000] + "\n...[clipped]...")
                print("-" * 40)
                print("\n  [PASS] 'INTELLIGENT CONTEXT' section found in prompt!")
                
                if "Impact Analysis" in prompt:
                     print("  [PASS] 'Impact Analysis' found.")
                else:
                     print("  [FAIL] 'Impact Analysis' NOT found.")
            else:
                 print("-" * 40)
                 print(prompt[:1000]) # Print start if not found
                 print("-" * 40)
                 print("\n  [FAIL] 'INTELLIGENT CONTEXT' section MISSING in prompt.")

            # Return dummy response object
            class Choice:
                class Message:
                    content = json.dumps({
                        "summary": "Mock review",
                        "files": {
                            target_file: {"status": "clean", "comments": []}
                        },
                        "verdict": "APPROVE"
                    })
                message = Message()
            
            class Response:
                choices = [Choice()]
            
            return Response()

    # Inject Mock
    print("  Injecting Mock LLM...")
    agent.llm.client = MockLLMClient()

    print("  Running inline review...")
    result = agent.run_inline_review(
        raw_diff=fake_diff,
        pr_title="Refactor Reviewer",
        custom_instructions="Verify integration",
        repo_path=repo_path
    )

    print("\n" + "-" * 60)
    print("  Full Review Verification: DONE")
    print("-" * 60)

if __name__ == "__main__":
    main()
