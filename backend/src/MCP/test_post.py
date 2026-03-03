import asyncio
import os
import sys

WEBHOOKS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "webhooks"))
sys.path.insert(0, WEBHOOKS_PATH)

from core.github_client import GitHubClient

async def test_post():
    gh = GitHubClient()
    
    repo = "shubham-vaishnav-13/Test-Agent"
    pr_number = 14
    commit_sha = "" # Let's get actual commit sha
    
    # Just trying a standard comment
    print("Testing post_or_update_comment...")
    try:
        await gh.post_or_update_comment(repo, pr_number, "Test simple comment via MCP debug")
        print("Success!")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_post())
