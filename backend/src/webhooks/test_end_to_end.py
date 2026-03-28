import os
import sys
import unittest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "webhooks"))
sys.path.append(os.path.join(os.path.dirname(__file__)))

from workers.fetch import FetchWorker
from workers.analyze import AnalyzeWorker
from workers.review import ReviewWorker
from workers.publish import PublishWorker
from core.types import PRMetadata
from models import JobStatus

class TestAsyncWorkerFlow(unittest.IsolatedAsyncioTestCase):
    """
    End-to-End Test Suite for the distributed async Redis worker pipeline.
    Mocks GitHub API, Docker Runner, and LLM to prevent external execution.
    """
    
    @patch("core.github_client.GitHubClient")
    @patch("core.docker_runner.DockerRunner")
    @patch("core.indexing.manager.IndexManager")
    @patch("agents.reviewer.ReviewerAgent")
    async def test_full_pipeline_flow(self, mock_reviewer_agent, mock_indexer, mock_docker_runner, mock_github_client):
        print("\n[INFO] Starting Async Distributed Pipeline E2E Test...")
        
        # --- 1. MOCK SETUP ---
        # Mock GitHub
        gh_instance = mock_github_client.return_value
        gh_instance.get_pr_diff = AsyncMock(return_value="diff --git a/main.py b/main.py\n+print('hello')\n")
        gh_instance.set_commit_status = AsyncMock()
        gh_instance.post_inline_review = AsyncMock()
        gh_instance.add_label = AsyncMock()

        # Mock Docker Runner
        mock_docker_runner.run_checks_in_container = AsyncMock(return_value={
            "lint": {"summary": "Mock Lint Pass", "details": []},
            "security": {"summary": "Mock Security Pass", "details": []}
        })

        # Mock Index Manager
        indexer_instance = mock_indexer.return_value
        indexer_instance.process_diff = MagicMock()

        # Mock LLM Reviewer Agent
        agent_instance = mock_reviewer_agent.return_value
        agent_instance.review = MagicMock(return_value={
            "inline_comments": [
                {"path": "main.py", "line": 2, "body": "Mock inline comment"}
            ],
            "summary": "Mock Review Summary",
        })

        # Mock Queue Manager & DB Session Factory
        mock_queue = AsyncMock()
        mock_db_session_factory = MagicMock()
        
        # Database context manager mock
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        
        # Mocking the `Job` SQLAlchemy model lookup
        mock_job = MagicMock()
        mock_job.id = 999
        mock_job.status = JobStatus.QUEUED

        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.execute.return_value.scalars.return_value.first.return_value = mock_job
        mock_db_session_factory.return_value = mock_session

        # Initial Payload simulating Webhook Reception
        initial_data = {
            "job_id": 999,
            "repo_full_name": "test/repo",
            "pr_number": 42,
            "commit_sha": "abcdef123456",
            "title": "Mock PR",
            "description": "Mock PR Description",
            "retry_count": 0
        }

        # --- 2. EXECUTE FETCHER ---
        print("[INFO] Simulating Fetch Worker...")
        fetch_worker = FetchWorker(mock_queue, mock_db_session_factory)
        
        # Mock clone dir
        with patch("core.repo_manager.RepoManager.clone_and_checkout", return_value="/tmp/mock_repo"):
            fetch_result = await fetch_worker.process(initial_data)
        
        self.assertIsNotNone(fetch_result, "FetchWorker should return context data")
        self.assertIn("diff_text", fetch_result)
        self.assertEqual(fetch_result["changed_files"], ["main.py"])
        # Pipeline forwards aggregate data to next stage
        analyze_data = {**initial_data, **fetch_result}

        # --- 3. EXECUTE ANALYZER ---
        print("[INFO] Simulating Analyze Worker...")
        analyze_worker = AnalyzeWorker(mock_queue, mock_db_session_factory)
        analyze_result = await analyze_worker.process(analyze_data)
        
        self.assertIsNotNone(analyze_result)
        self.assertIn("static_findings", analyze_result)
        self.assertIn("context_pack", analyze_result)
        review_data = {**analyze_data, **analyze_result}

        # --- 4. EXECUTE REVIEWER ---
        print("[INFO] Simulating Review Worker (LLM)...")
        review_worker = ReviewWorker(mock_queue, mock_db_session_factory)
        
        # Mock Token Bucket inside ReviewWorker to return True
        with patch("core.rate_limiter.TokenBucketRateLimiter") as mock_tb:
            mock_tb_instance = mock_tb.return_value
            mock_tb_instance.acquire = AsyncMock(return_value=True)
            
            review_result = await review_worker.process(review_data)
        
        self.assertIsNotNone(review_result)
        self.assertEqual(review_result["findings_count"], 1)
        publish_data = {**review_data, **review_result}

        # --- 5. EXECUTE PUBLISHER ---
        print("[INFO] Simulating Publish Worker...")
        publish_worker = PublishWorker(mock_queue, mock_db_session_factory)
        publish_result = await publish_worker.process(publish_data)

        # Publisher is terminal and returns None
        self.assertIsNone(publish_result)
        
        # --- 6. ASSERTIONS ---
        print("[INFO] Verifying Network Boundary Calls...")
        
        # Assert GitHub Client interacted properly
        gh_instance.post_inline_review.assert_called_once()
        gh_instance.add_label.assert_called_with("test/repo", 42, "pr-reviewed")

        print("[OK] Async Pipeline passed flawlessly.")

if __name__ == "__main__":
    unittest.main()
