
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch
import unittest

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.types import PRMetadata
from core.orchestrator import Orchestrator

class TestEndToEnd(unittest.IsolatedAsyncioTestCase):
    
    @patch("core.orchestrator.GitHubClient")
    @patch("core.orchestrator.RepoManager")
    @patch("core.orchestrator.DockerRunner")
    @patch("core.orchestrator.IndexManager")
    @patch("core.orchestrator.AsyncSession") # Mock DB session context manager
    @patch("core.orchestrator.engine")
    async def test_full_flow(self, mock_engine, mock_session_cls, mock_indexer_cls, mock_docker_cls, mock_repo_cls, mock_gh_cls):
        print("\n  [INFO] Starting End-to-End Flow Test...")
        
        # 1. Setup Mocks
        mock_gh = mock_gh_cls.return_value
        mock_gh.get_pr_diff = AsyncMock(return_value="diff --git a/test.py b/test.py\nindex 123..456 100644\n--- a/test.py\n+++ b/test.py\n@@ -1 +1 @@\n-old\n+new")
        mock_gh.set_commit_status = AsyncMock()
        mock_gh.post_inline_review = AsyncMock()
        mock_gh.post_or_update_comment = AsyncMock()
        mock_gh.add_label = AsyncMock()  # FIXED: Was missing

        # Mocking config loader
        with patch("core.custom_checks.CustomCheckLoader.load_from_repo", new_callable=AsyncMock) as mock_config:
            mock_config.return_value = {"custom_instructions": "Review carefully."}
            
            mock_repo = mock_repo_cls.return_value
            mock_repo.clone_and_checkout.return_value = "/tmp/mock_repo"
            
            mock_docker = mock_docker_cls.return_value
            mock_docker.run_checks_in_container = AsyncMock(return_value={"lint": {}, "security": {}}) # Fixed: static method mock structure might be tricky, but wrapper calls it.
            # Actually Orchestrator calls DockerRunner.run_checks_in_container (static). 
            # We mocked the class, so we need to mock the static method on the class itself, not instance.
            mock_docker_cls.run_checks_in_container = AsyncMock(return_value={"lint": {}, "security": {}})
            
            mock_indexer = mock_indexer_cls.return_value
            mock_indexer.process_diff = MagicMock() # Sync method

            # Mock DB
            mock_session = mock_session_cls.return_value
            mock_session.__aenter__.return_value = mock_session
            mock_session.get = AsyncMock(return_value=MagicMock(id=1)) # Mock Job
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock() # FIXED: Was missing

            # Mock Reviewer Agent (to avoid Real LLM calls)
            with patch("core.orchestrator.ReviewerAgent") as mock_agent_cls:
                mock_agent = mock_agent_cls.return_value
                mock_agent.run_inline_review.return_value = {
                    "summary": "Mock Review Summary",
                    "inline_comments": [],
                    "verdict": "APPROVE",
                    "clean_files": ["test.py"]
                }
                
                # 2. Initialize Orchestrator
                orch = Orchestrator()
                # Inject mocked instances if __init__ created real ones (it did)
                orch.gh = mock_gh
                orch.indexer = mock_indexer
                orch.reviewer = mock_agent
                
                # 3. Create Metadata
                metadata = PRMetadata(
                    repo_full_name="owner/repo",
                    pr_number=123,
                    commit_sha="sha123",
                    title="Test PR",
                    description="Testing E2E",
                    branch_name="feature-branch"
                )
                
                # 4. Run Process
                await orch.process_pr(metadata, job_id=1)
                
                # 5. Verify Steps
                print("  [PASS] Orchestrator started.")
                mock_gh.set_commit_status.assert_called()
                print("  [PASS] Commit status set (Pending).")
                
                mock_repo.clone_and_checkout.assert_called()
                print("  [PASS] Repo cloned.")
                
                mock_indexer.process_diff.assert_called()
                print("  [PASS] IndexManager called for incremental update.")
                
                mock_agent.run_inline_review.assert_called()
                print("  [PASS] ReviewerAgent called.")
                
                mock_gh.add_label.assert_called_with("owner/repo", 123, "ReviewedBySapientPR")
                print("  [PASS] PR Label added.")
                
                # Check Database Interaction
                mock_session.commit.assert_called()
                print("  [PASS] Database constraints saved (Job status updated).")

if __name__ == "__main__":
    unittest.main()
