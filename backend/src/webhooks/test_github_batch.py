
# Verification Script for GitHub Batch Commenting
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Load .env explicitly for GITHUB_TOKEN
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from core.github_client import GitHubClient, BOT_SIGNATURE

class TestGitHubBatch(unittest.TestCase):
    def setUp(self):
        self.client = GitHubClient()
        self.repo = "owner/repo"
        self.pr_number = 1
        self.commit_id = "sha123"

    @patch("core.github_client.requests.post")
    def test_post_batch_review(self, mock_post):
        print("\n  Testing Batch Review Posting...")
        
        # Mock Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"message": "Review Submitted"}'
        mock_post.return_value = mock_response

        # Test Data
        summary = "Unit Test Summary"
        comments = [
            {"path": "file1.py", "line": 10, "body": "Comment 1", "side": "RIGHT"},
            {"path": "file2.py", "line": 20, "body": "Comment 2", "side": "RIGHT"},
            {"path": "file3.py", "line": 30, "body": "Comment 3", "side": "RIGHT"}
        ]
        action = "COMMENT"

        # Execute
        result = self.client.post_batch_review(
            self.repo, self.pr_number, self.commit_id, summary, comments, action
        )

        # Assertions
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Verify Arguments
        args, kwargs = mock_post.call_args
        url = args[0]
        payload = kwargs['json']
        
        print(f"  [PASS] Called URL: {url}")
        self.assertIn("/pulls/1/reviews", url)
        
        print(f"  [PASS] Payload Event: {payload['event']}")
        self.assertEqual(payload['event'], action)
        
        print(f"  [PASS] Payload Comments: {len(payload['comments'])} items")
        self.assertEqual(len(payload['comments']), 3)
        
        print(f"  [PASS] Payload Body contains Signature: {BOT_SIGNATURE in payload['body']}")
        self.assertIn(BOT_SIGNATURE, payload['body'])

if __name__ == "__main__":
    print("============================================================")
    print("  Part 11: GitHub Batching Verification")
    print("============================================================")
    unittest.main()
