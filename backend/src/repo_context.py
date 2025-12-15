from src.github_client import GitHubClient
from datetime import datetime, timezone


_DEFAULT_TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".css",
    ".html",
    ".htm",
    ".sh",
    ".ps1",
    ".sql",
    ".java",
    ".kt",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
}


def _normalize_path(path: str) -> str:
    return (path or "").replace("\\", "/")


def _get_extension(path: str) -> str:
    path = _normalize_path(path)
    if "." not in path:
        return ""
    return "." + path.rsplit(".", 1)[-1].lower()


def _is_text_candidate(path: str, allowed_extensions: set[str]) -> bool:
    path = _normalize_path(path)
    if not path or path.endswith("/"):
        return False
    lowered = path.lower()
    if any(
        lowered.startswith(prefix)
        for prefix in (
            ".git/",
            "node_modules/",
            "dist/",
            "build/",
            "coverage/",
            "__pycache__/",
            ".venv/",
            "venv/",
        )
    ):
        return False
    return _get_extension(path) in allowed_extensions


class RepositoryContextService:
    def __init__(self, owner: str, repo: str):
        self.client = GitHubClient()
        self.owner = owner
        self.repo = repo

    def fetch_repo_metadata(self):
        endpoint = f"/repos/{self.owner}/{self.repo}"
        return self.client.get(endpoint)

    def fetch_languages(self):
        endpoint = f"/repos/{self.owner}/{self.repo}/languages"
        return self.client.get(endpoint)

    def fetch_topics(self):
        endpoint = f"/repos/{self.owner}/{self.repo}/topics"
        return self.client.get(endpoint)

    def fetch_readme_text(self):
        endpoint = f"/repos/{self.owner}/{self.repo}/readme"
        return self.client.get_text(endpoint, headers={"Accept": "application/vnd.github.raw"})

    def fetch_file_text(self, path: str, ref: str | None = None):
        path = _normalize_path(path)
        endpoint = f"/repos/{self.owner}/{self.repo}/contents/{path}"
        params = {"ref": ref} if ref else None
        return self.client.get_text(endpoint, params=params, headers={"Accept": "application/vnd.github.raw"})

    def fetch_default_branch_tree(self, recursive: bool = True):
        meta = self.fetch_repo_metadata()
        default_branch = meta.get("default_branch")
        if not default_branch:
            return {"default_branch": None, "tree": []}

        branch = self.client.get(f"/repos/{self.owner}/{self.repo}/branches/{default_branch}")
        commit_sha = branch.get("commit", {}).get("sha")
        if not commit_sha:
            return {"default_branch": default_branch, "tree": []}

        git_commit = self.client.get(f"/repos/{self.owner}/{self.repo}/git/commits/{commit_sha}")
        tree_sha = git_commit.get("tree", {}).get("sha")
        if not tree_sha:
            return {"default_branch": default_branch, "tree": []}

        tree = self.client.get(
            f"/repos/{self.owner}/{self.repo}/git/trees/{tree_sha}",
            params={"recursive": 1 if recursive else 0},
        )
        return {"default_branch": default_branch, "tree": tree.get("tree", [])}

    def fetch_recent_commits(self, per_page: int = 20):
        endpoint = f"/repos/{self.owner}/{self.repo}/commits"
        commits = self.client.get(endpoint, params={"per_page": per_page})
        return [
            {
                "sha": c.get("sha"),
                "message": (c.get("commit") or {}).get("message"),
                "author": ((c.get("commit") or {}).get("author") or {}).get("name"),
                "date": ((c.get("commit") or {}).get("author") or {}).get("date"),
            }
            for c in commits
            if isinstance(c, dict)
        ]

    def fetch_repository_context(self, max_readme_chars: int = 8000, max_tree_entries: int = 300):
        meta = self.fetch_repo_metadata()
        languages = self.fetch_languages()

        topics = []
        try:
            topics_resp = self.fetch_topics()
            if isinstance(topics_resp, dict):
                topics = topics_resp.get("names", []) or []
        except Exception:
            topics = []

        readme = ""
        try:
            readme = self.fetch_readme_text() or ""
        except Exception:
            readme = ""

        tree_info = {"default_branch": meta.get("default_branch"), "tree": []}
        try:
            tree_info = self.fetch_default_branch_tree(recursive=True)
        except Exception:
            tree_info = {"default_branch": meta.get("default_branch"), "tree": []}

        commits = []
        try:
            commits = self.fetch_recent_commits(per_page=20)
        except Exception:
            commits = []

        tree_entries = tree_info.get("tree", []) or []
        file_paths = [
            t.get("path")
            for t in tree_entries
            if isinstance(t, dict) and t.get("type") == "blob" and t.get("path")
        ][:max_tree_entries]

        return {
            "full_name": meta.get("full_name"),
            "description": meta.get("description"),
            "default_branch": tree_info.get("default_branch") or meta.get("default_branch"),
            "topics": topics,
            "languages": languages,
            "readme": readme[:max_readme_chars],
            "file_paths": file_paths,
            "recent_commits": commits,
        }

    def build_ai_context_json(
        self,
        *,
        include_file_contents: bool = True,
        max_total_chars: int = 120_000,
        max_file_chars: int = 8_000,
        max_files_with_content: int = 60,
        allowed_extensions: set[str] | None = None,
        include_tree_entries: int = 2000,
    ):
        """Build a single JSON-serializable payload that can be sent to an LLM.

        Notes:
        - GitHub API + LLM prompt sizes are limited; we cap total chars.
        - We only include content for likely-text files by extension.
        """
        allowed_extensions = allowed_extensions or set(_DEFAULT_TEXT_EXTENSIONS)

        repo_context = self.fetch_repository_context(
            max_readme_chars=min(8000, max_total_chars),
            max_tree_entries=include_tree_entries,
        )

        # Attempt to re-fetch the full tree details for richer metadata.
        tree_info = {"default_branch": repo_context.get("default_branch"), "tree": []}
        try:
            tree_info = self.fetch_default_branch_tree(recursive=True)
        except Exception:
            tree_info = tree_info

        tree_entries = tree_info.get("tree", []) or []
        files = []
        for entry in tree_entries:
            if not isinstance(entry, dict):
                continue
            files.append(
                {
                    "path": entry.get("path"),
                    "type": entry.get("type"),
                    "size": entry.get("size"),
                    "sha": entry.get("sha"),
                    "mode": entry.get("mode"),
                }
            )

        # Deterministic ordering.
        files = sorted(
            [f for f in files if f.get("path")],
            key=lambda x: str(x.get("path")).lower(),
        )

        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo": {
                "full_name": repo_context.get("full_name"),
                "description": repo_context.get("description"),
                "default_branch": repo_context.get("default_branch"),
                "topics": repo_context.get("topics"),
                "languages": repo_context.get("languages"),
            },
            "high_level": {
                "readme": repo_context.get("readme"),
                "recent_commits": repo_context.get("recent_commits"),
            },
            "structure": {
                "files": files[:include_tree_entries],
            },
            "content": {
                "files": {},
            },
            "limits": {
                "include_file_contents": include_file_contents,
                "max_total_chars": max_total_chars,
                "max_file_chars": max_file_chars,
                "max_files_with_content": max_files_with_content,
                "allowed_extensions": sorted(list(allowed_extensions)),
                "include_tree_entries": include_tree_entries,
            },
        }

        if not include_file_contents:
            return payload

        budget_remaining = max_total_chars
        readme_text = (payload.get("high_level", {}).get("readme") or "")
        budget_remaining -= len(readme_text)

        default_branch = payload.get("repo", {}).get("default_branch")
        picked = 0

        for f in files:
            if picked >= max_files_with_content:
                break
            if budget_remaining <= 0:
                break

            path = _normalize_path(str(f.get("path") or ""))
            if not path or f.get("type") != "blob":
                continue
            if not _is_text_candidate(path, allowed_extensions):
                continue

            try:
                text = self.fetch_file_text(path, ref=default_branch) or ""
            except Exception:
                continue

            if len(text) > max_file_chars:
                text = text[:max_file_chars] + "\n...<truncated>"

            if len(text) > budget_remaining:
                # Not enough budget to include this file.
                continue

            payload["content"]["files"][path] = text
            budget_remaining -= len(text)
            picked += 1

        payload["limits"]["chars_used"] = max_total_chars - max(budget_remaining, 0)
        payload["limits"]["files_included_with_content"] = picked
        return payload
