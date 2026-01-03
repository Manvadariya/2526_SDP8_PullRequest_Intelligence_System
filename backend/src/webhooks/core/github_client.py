import httpx
from config import config

class GitHubClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

    async def post_comment(self, repo: str, pr_number: int, body: str):
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={"body": body}, headers=self.headers)
            if resp.status_code not in [200, 201]:
                print(f"Failed to comment: {resp.text}")

    async def add_label(self, repo: str, pr_number: int, label: str):
        # GitHub API uses the "issues" endpoint for PR labels
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"labels": [label]}, headers=self.headers)

    async def get_pr_diff(self, repo: str, pr_number: int) -> str:
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
        headers = self.headers.copy()
        headers["Accept"] = "application/vnd.github.v3.diff"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            return resp.text