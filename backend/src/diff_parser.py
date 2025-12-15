from src.github_client import GitHubClient

class DiffService:
    def __init__(self, owner, repo):
        self.client = GitHubClient()
        self.owner = owner
        self.repo = repo

    def fetch_pr_files(self, pr_number):
        endpoint = f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}/files"
        return self.client.get(endpoint)


def parse_diff(patch):
    added = []
    removed = []

    if not patch:
        return added, removed

    for line in patch.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])

    return added, removed
