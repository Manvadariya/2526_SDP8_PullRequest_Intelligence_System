from .github_client import GitHubClient

class PullRequestService:
    def __init__(self, owner, repo):
        self.client = GitHubClient()
        self.owner = owner
        self.repo = repo

    def fetch_pull_requests(self, state="open"):
        endpoint = f"/repos/{self.owner}/{self.repo}/pulls"
        params = {
            "state": state,
            "per_page": 10
        }
        return self.client.get(endpoint, params)
