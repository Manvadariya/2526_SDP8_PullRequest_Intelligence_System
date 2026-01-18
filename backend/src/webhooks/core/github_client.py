import httpx
import base64
from config import config

# This hidden signature allows us to find our own comments
BOT_SIGNATURE = ""
FILE_SIGNATURE_PREFIX = "<!-- SapientPR-File:"  # For file-specific comments

class GitHubClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

    async def get_pr_diff(self, repo: str, pr_number: int) -> str:
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
        headers = self.headers.copy()
        headers["Accept"] = "application/vnd.github.v3.diff"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text

    # --- NEW: Smart Commenting Logic ---
    async def post_or_update_comment(self, repo: str, pr_number: int, body: str):
        # 1. Append Signature so we can find this later
        signed_body = f"{body}\n\n{BOT_SIGNATURE}"
        
        # 2. Check for existing comment
        existing_comment_id = await self._find_bot_comment(repo, pr_number)
        
        if existing_comment_id:
            print(f"📝 Updating existing comment {existing_comment_id}...")
            await self._update_comment(repo, existing_comment_id, signed_body)
        else:
            print(f"📝 Creating new comment...")
            await self._post_comment(repo, pr_number, signed_body)

    async def _find_bot_comment(self, repo: str, pr_number: int) -> int:
        """Finds the first comment on the PR containing our signature."""
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code != 200:
                return None
            
            comments = resp.json()
            for comment in comments:
                # Check if the comment body contains our hidden signature
                if comment.get("body") and BOT_SIGNATURE in comment["body"]:
                    return comment["id"]
            return None

    async def _post_comment(self, repo: str, pr_number: int, body: str):
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"body": body}, headers=self.headers)

    async def _update_comment(self, repo: str, comment_id: int, body: str):
        url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
        async with httpx.AsyncClient() as client:
            await client.patch(url, json={"body": body}, headers=self.headers)

    # --- NEW: Post multiple file-specific comments ---
    async def post_file_reviews(self, repo: str, pr_number: int, file_reviews: dict):
        """
        Posts separate comments for each file.
        file_reviews = {
            "src/app.py": "review content...",
            "src/utils.py": "review content..."
        }
        """
        if len(file_reviews) > 8:
            # If more than 8 files, combine into one comment
            combined_body = "## 📦 Combined Review (Multiple Files)\n\n"
            for filepath, review in file_reviews.items():
                combined_body += f"### 📄 `{filepath}`\n\n{review}\n\n---\n\n"
            
            # Always create new comment (never update)
            await self._post_comment(repo, pr_number, combined_body + "\n" + BOT_SIGNATURE)
        else:
            # Post separate comment for each file (always new)
            for filepath, review in file_reviews.items():
                file_signature = f"{FILE_SIGNATURE_PREFIX} {filepath} -->"
                signed_body = f"## 📄 Review for `{filepath}`\n\n{review}\n\n{file_signature}"
                
                print(f"📝 Creating new comment for {filepath}...")
                await self._post_comment(repo, pr_number, signed_body)

    # --- Standard Utils (Unchanged) ---
    async def add_label(self, repo: str, pr_number: int, label: str):
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"labels": [label]}, headers=self.headers)

    async def get_file_content(self, repo: str, path: str, ref: str) -> str:
        url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={ref}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code == 404:
                return None
            data = resp.json()
            return base64.b64decode(data["content"]).decode("utf-8")

    async def set_commit_status(self, repo: str, sha: str, state: str, description: str, target_url: str = ""):
        url = f"https://api.github.com/repos/{repo}/statuses/{sha}"
        payload = {
            "state": state,
            "description": description[:140],
            "context": "SapientPR Reviewer"
        }
        if target_url:
            payload["target_url"] = target_url
            
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, headers=self.headers)