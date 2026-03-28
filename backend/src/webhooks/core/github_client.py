import httpx
import requests
import base64
import asyncio
import logging
from config import config

logger = logging.getLogger("agenticpr.github")

# This hidden signature allows us to find our own comments
BOT_SIGNATURE = "<!-- SapientPR-Review AXIOM_ULTRA -->"
FILE_SIGNATURE_PREFIX = "<!-- SapientPR-File:"  # For file-specific comments

class GitHubClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

    async def _request_with_backoff(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Executes httpx request with exponential backoff for GitHub rate limits."""
        max_retries = 5
        base_delay = 2
        
        async with httpx.AsyncClient() as client:
            for attempt in range(max_retries):
                resp = await client.request(method, url, **kwargs)
                
                # Check for rate limiting (403 with specific header or 429)
                if resp.status_code == 429 or (resp.status_code == 403 and "x-ratelimit-remaining" in resp.headers and resp.headers.get("x-ratelimit-remaining") == "0") or (resp.status_code == 403 and "secondary rate limit" in resp.text.lower()):
                    
                    delay = base_delay * (2 ** attempt)
                    # Check if GitHub provided a Retry-After header
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        delay = max(delay, int(retry_after))
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"GitHub Rate Limit hit on {url}. Backing off for {delay}s...")
                        await asyncio.sleep(delay)
                        continue
                        
                resp.raise_for_status()
                return resp
        raise Exception(f"Failed after {max_retries} attempts")

    async def get_pr_diff(self, repo: str, pr_number: int) -> str:
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
        headers = self.headers.copy()
        headers["Accept"] = "application/vnd.github.v3.diff"
        resp = await self._request_with_backoff("GET", url, headers=headers)
        return resp.text

    # --- NEW: Smart Commenting Logic ---
    async def post_or_update_comment(self, repo: str, pr_number: int, body: str):
        # 1. Append Signature so we can find this later
        signed_body = f"{body}\n\n{BOT_SIGNATURE}"
        
        # 2. Check for existing comment
        existing_comment_id = await self._find_bot_comment(repo, pr_number)
        
        if existing_comment_id:
            print(f" Updating existing comment {existing_comment_id}...")
            await self._update_comment(repo, existing_comment_id, signed_body)
        else:
            print(f" Creating new comment...")
            await self._post_comment(repo, pr_number, signed_body)

    async def _find_bot_comment(self, repo: str, pr_number: int) -> int:
        """Finds the first comment on the PR containing our signature."""
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        try:
            resp = await self._request_with_backoff("GET", url, headers=self.headers)
        except Exception:
            return None
            
            comments = resp.json()
            for comment in comments:
                # Check if the comment body contains our hidden signature
                if comment.get("body") and BOT_SIGNATURE in comment["body"]:
                    return comment["id"]
            return None

    async def _post_comment(self, repo: str, pr_number: int, body: str):
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        await self._request_with_backoff("POST", url, json={"body": body}, headers=self.headers)

    async def _update_comment(self, repo: str, comment_id: int, body: str):
        url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
        await self._request_with_backoff("PATCH", url, json={"body": body}, headers=self.headers)

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
                
                print(f" Creating new comment for {filepath}...")
                await self._post_comment(repo, pr_number, signed_body)

    # --- NEW: Inline Review Comments (Coderabbit-style) ---
    async def post_inline_review(self, repo: str, pr_number: int, commit_sha: str,
                                  inline_comments: list, summary_body: str = "",
                                  event: str = "COMMENT"):
        """
        Posts a PR review with inline comments on specific diff lines.
        """
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
        payload = {
            "commit_id": commit_sha,
            "body": f"{summary_body}\n\n{BOT_SIGNATURE}" if summary_body else BOT_SIGNATURE,
            "event": event,
            "comments": inline_comments
        }
        
        try:
            resp = await self._request_with_backoff("POST", url, json=payload, headers=self.headers)
            
            if resp.status_code in (200, 201):
                logger.info(f"Posted inline review: {len(inline_comments)} inline comment(s), event={event}")
                return True
            
            if resp.status_code == 422 and "request changes on your own pull request" in resp.text:
                logger.warning(f"Cannot request changes on own PR. Retrying with COMMENT event...")
                payload["event"] = "COMMENT"
                resp = await self._request_with_backoff("POST", url, json=payload, headers=self.headers)
                if resp.status_code in (200, 201):
                    logger.info(f"Retry success: Posted as COMMENT.")
                    return True
            
        except Exception as e:
            logger.warning(f"Inline review failed: {e}")
            
        # Fallback: post as regular issue comment
        fallback = summary_body + "\n\n" if summary_body else ""
        if inline_comments:
            fallback += "###  Inline Comments (Fallback)\n"
            for c in inline_comments:
                fallback += f"- **{c.get('path', 'unknown')}** (Line {c.get('line', '?')}): {c.get('body', '')}\n"
        
        await self.post_or_update_comment(repo, pr_number, fallback)
        return False

    async def add_label(self, repo: str, pr_number: int, label: str):
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels"
        await self._request_with_backoff("POST", url, json={"labels": [label]}, headers=self.headers)

    async def get_file_content(self, repo: str, path: str, ref: str) -> str:
        url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={ref}"
        try:
            resp = await self._request_with_backoff("GET", url, headers=self.headers)
            data = resp.json()
            return base64.b64decode(data["content"]).decode("utf-8")
        except Exception:
            return None

    # --- NEW: Commit Status Updates ---
    async def set_commit_status(self, repo: str, sha: str, state: str, description: str, context: str = "AgenticPR Review"):
        """
        Updates the GitHub commit status (pending, success, error, failure).
        """
        url = f"https://api.github.com/repos/{repo}/statuses/{sha}"
        payload = {
            "state": state,  # "pending", "success", "error", "failure"
            "description": description[:140],  # GitHub max description length is 140
            "context": context
        }
        try:
            await self._request_with_backoff("POST", url, json=payload, headers=self.headers)
            logger.info(f"Set commit status for {sha[:7]} to {state}: {description}")
        except Exception as e:
            logger.error(f"Failed to set commit status: {e}")

    # --- NEW: Synchronous Batch Review (for sync Agents) ---
    def post_batch_review(self, repo: str, pr_number: int, commit_id: str, summary: str, comments: list, action: str = "COMMENT"):
        """
        Synchronous wrapper for posting a batch review.
        """
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
        
        payload = {
            "commit_id": commit_id,
            "body": summary + f"\n\n{BOT_SIGNATURE}",
            "event": action,
            "comments": comments
        }
        
        try:
            resp = requests.post(url, json=payload, headers=self.headers, timeout=30)
            
            if resp.status_code in (200, 201):
                print(f"[OK] Batch review posted: {len(comments)} comments, Action={action}")
                return True
            
            # Handle Self-Review Restriction
            if resp.status_code == 422 and "request changes on your own pull request" in resp.text:
                print(f"[WARN] Cannot request changes on own PR. Retrying with COMMENT event...")
                payload["event"] = "COMMENT"
                resp = requests.post(url, json=payload, headers=self.headers, timeout=30)
                if resp.status_code in (200, 201):
                    print(f"[OK] Retry success: Posted as COMMENT.")
                    return True

            print(f"[FAIL] Batch review failed ({resp.status_code}): {resp.text[:500]}")
            return False
        except Exception as e:
            print(f"[ERR] Batch review exception: {e}")
            return False