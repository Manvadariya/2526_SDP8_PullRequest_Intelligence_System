"""
Test Script: Post an inline review comment on a GitHub PR (Coderabbit-style).

This script verifies that the inline review comment system works by:
1. Fetching a real PR's diff
2. Finding the first changed file and line
3. Posting a test inline comment on that exact line

Usage:
    python test_inline_review.py <owner/repo> <pr_number>
    
Example:
    python test_inline_review.py shubham-vaishnav-13/Test-Agent 5
"""

import asyncio
import httpx
import sys
import os

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from core.diff_parser import DiffParser


async def test_inline_review(repo: str, pr_number: int):
    headers = {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    async with httpx.AsyncClient(timeout=30) as client:
        # ── Step 1: Get PR info ──────────────────────────────────────
        print(f"\n{'='*60}")
        print(f"  SapientPR — Inline Review Comment Test")
        print(f"{'='*60}\n")
        
        pr_resp = await client.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}",
            headers=headers
        )
        if pr_resp.status_code != 200:
            print(f"❌ Failed to fetch PR: {pr_resp.status_code} — {pr_resp.text[:200]}")
            return False
        
        pr_data = pr_resp.json()
        commit_sha = pr_data["head"]["sha"]
        print(f"  PR #{pr_number}: {pr_data['title']}")
        print(f"  Commit SHA: {commit_sha[:12]}")
        print(f"  State: {pr_data['state']}")

        # ── Step 2: Get the diff ─────────────────────────────────────
        diff_headers = headers.copy()
        diff_headers["Accept"] = "application/vnd.github.v3.diff"
        diff_resp = await client.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}",
            headers=diff_headers
        )
        if diff_resp.status_code != 200:
            print(f"❌ Failed to fetch diff: {diff_resp.status_code}")
            return False

        raw_diff = diff_resp.text
        file_diffs = DiffParser.parse_diff(raw_diff)

        if not file_diffs:
            print("❌ No files changed in this PR!")
            return False

        print(f"\n  Changed files ({len(file_diffs)}):")
        for fp in file_diffs:
            valid = DiffParser.get_valid_right_lines(file_diffs[fp])
            print(f"    • {fp} ({len(valid)} commentable lines)")

        # ── Step 3: Pick first file + line ───────────────────────────
        target_file = None
        target_line = None
        for fp, diff_content in file_diffs.items():
            valid_lines = DiffParser.get_valid_right_lines(diff_content)
            if valid_lines:
                target_file = fp
                target_line = min(valid_lines)
                break

        if not target_file:
            print("❌ No valid lines found for inline commenting!")
            return False

        print(f"\n  📍 Target: {target_file} line {target_line}")

        # ── Step 4: Post inline review comment ───────────────────────
        print(f"\n  Posting inline review comment...")
        
        payload = {
            "commit_id": commit_sha,
            "event": "COMMENT",
            "body": (
                "## 🤖 SapientPR — Inline Review Test\n\n"
                "This is a **test** inline review comment.\n"
                "If you see this as an inline comment anchored to a specific line in the "
                "**Files Changed** tab, the Coderabbit-style review system is working!\n\n"
                f"**Files scanned:** {len(file_diffs)} | **Inline comments:** 1"
            ),
            "comments": [
                {
                    "path": target_file,
                    "line": target_line,
                    "side": "RIGHT",
                    "body": (
                        "💡 **TEST**: This is a test inline comment from SapientPR.\n\n"
                        "This comment is anchored to a specific line in your code diff — "
                        "just like Coderabbit.\n\n"
                        "```suggestion\n"
                        "// SapientPR inline review is working!\n"
                        "```"
                    )
                }
            ]
        }

        resp = await client.post(
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews",
            json=payload,
            headers=headers
        )

        # ── Step 5: Report result ────────────────────────────────────
        if resp.status_code in (200, 201):
            review_data = resp.json()
            print(f"\n  ✅ SUCCESS! Inline review posted!")
            print(f"     Review ID: {review_data.get('id')}")
            print(f"     Comment on: {target_file} (line {target_line})")
            print(f"\n  → Check it: https://github.com/{repo}/pull/{pr_number}/files")
            print(f"{'='*60}\n")
            return True
        else:
            error = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            print(f"\n  ❌ FAILED ({resp.status_code})")
            print(f"     Error: {str(error)[:300]}")
            print(f"{'='*60}\n")
            return False


async def test_annotated_diff(repo: str, pr_number: int):
    """Bonus: Show annotated diff with line numbers (what the LLM sees)."""
    headers = {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff"
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}",
            headers=headers
        )
        raw_diff = resp.text
        file_diffs = DiffParser.parse_diff(raw_diff)

        print(f"\n{'='*60}")
        print(f"  Annotated Diff Preview (what the LLM sees)")
        print(f"{'='*60}\n")

        for filepath, diff_content in file_diffs.items():
            annotated = DiffParser.annotate_diff_with_line_numbers(diff_content)
            print(f"── {filepath} ──")
            # Show first 30 lines
            lines = annotated.split('\n')
            for line in lines[:30]:
                print(f"  {line}")
            if len(lines) > 30:
                print(f"  ... ({len(lines) - 30} more lines)")
            print()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("\nUsage: python test_inline_review.py <owner/repo> <pr_number>")
        print("Example: python test_inline_review.py shubham-vaishnav-13/Test-Agent 5\n")
        sys.exit(1)

    repo = sys.argv[1]
    pr_number = int(sys.argv[2])

    print("\n[1/2] Testing annotated diff parsing...")
    asyncio.run(test_annotated_diff(repo, pr_number))

    print("[2/2] Testing inline review comment posting...")
    success = asyncio.run(test_inline_review(repo, pr_number))
    
    sys.exit(0 if success else 1)
