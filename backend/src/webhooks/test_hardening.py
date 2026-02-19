
# Verification Script for Production Hardening
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.security import SecretScanner
from core.feedback import FeedbackManager
from agents.reviewer import ReviewerAgent

class TestHardening(unittest.TestCase):
    def test_secret_redaction(self):
        print("\n  [INFO] Testing Secret Redaction...")
        scanner = SecretScanner()
        
        # Test Cases
        unsafe_text = """
        const apiKey = "sk-1234567890abcdef12345678";
        const awsKey = "AKIA1234567890ABCDEF";
        const dbUrl = "postgres://user:mypassword@localhost:5432/db";
        """
        
        redacted = scanner.redact(unsafe_text)
        
        print(f"  Input: {unsafe_text.strip()}")
        print(f"  Output: {redacted.strip()}")
        
        self.assertNotIn("sk-12345", redacted)
        self.assertIn("[REDACTED_API_KEY]", redacted)
        
        self.assertNotIn("AKIA", redacted)
        self.assertIn("[REDACTED_AWS_KEY]", redacted)
        
        self.assertNotIn(":mypassword@", redacted)
        self.assertIn(":[REDACTED_PASSWORD]@", redacted)
        print("  [PASS] Secrets successfully redacted.")

    def test_feedback_loop(self):
        print("\n  [INFO] Testing Feedback Loop...")
        # Use a temp log file
        test_log = "test_feedback.json"
        if os.path.exists(test_log):
            os.remove(test_log)
            
        feedback_mgr = FeedbackManager(log_file=test_log)
        
        # 1. Log a false positive
        feedback_mgr.log_feedback("src/auth.py", 10, "Bad comment", "This is a false positive")
        
        # 2. Retrieve constraints
        constraints = feedback_mgr.get_negative_constraints()
        
        print(f"  Constraints Generated: {ascii(constraints)}")
        self.assertIn("src/auth.py", constraints)
        self.assertIn("FEEDBACK HISTORY", constraints)
        
        # Cleanup
        if os.path.exists(test_log):
            os.remove(test_log) # Clean up path relative to feedback.py
            # Actually feedback manager uses relative path to itself
            # So we should probably let it be or try to find it. 
            # For this test, it writes to backend/src/webhooks/core/test_feedback.json
            full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core", test_log)
            if os.path.exists(full_path):
                os.remove(full_path)
                
        print("  [PASS] Feedback logged and retrieved.")

    @patch("agents.reviewer.ContextBuilder.build_context")
    def test_error_fallback(self, mock_build_context):
        print("\n  [INFO] Testing Error Fallback...")
        # Simulate Crash in Context Builder (e.g. Qdrant down)
        mock_build_context.side_effect = Exception("Connection Refused")
        
        agent = ReviewerAgent()
        
        # Mock LLM to avoid real call
        agent.llm.client.chat.completions.create = MagicMock(return_value=MagicMock(choices=[MagicMock(message=MagicMock(content='{"summary": "Fallback worked", "files": {}}'))]))
        agent.planner.analyze_pr_complexity = MagicMock(return_value={"review_strategy": "quick", "high_risk_files": [], "ignore_files": []})
        agent.github.post_batch_review = MagicMock()

        # Run Review
        # We need to pass repo_path to trigger context building
        bs_diff = "diff --git a/file.py b/file.py\nindex 123..456 100644\n--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-foo\n+bar"
        
        # Create a dummy file for it to find
        with open("dummy_test_file.py", "w") as f:
            f.write("foo")
            
        try:
            result = agent.run_inline_review(bs_diff, "Title", "Inst", repo_path=".")
            print("  [PASS] Review generated despite ContextBuilder failure.")
        except Exception as e:
            self.fail(f"Reviewer crashed on fallback: {e}")
        finally:
            if os.path.exists("dummy_test_file.py"):
                 os.remove("dummy_test_file.py")

if __name__ == "__main__":
    print("============================================================")
    print("  Part 12: Production Hardening Verification")
    print("============================================================")
    unittest.main()
