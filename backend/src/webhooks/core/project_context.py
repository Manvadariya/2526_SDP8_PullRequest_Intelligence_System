import os
import asyncio
import logging
import fnmatch
from pathlib import Path
from typing import List, Set, Optional, Tuple
from pydantic import BaseModel, Field


logger = logging.getLogger("pr_agent.context")


class ContextConfig(BaseModel):
    """Strict controls to keep context bounded and safe."""

    max_token_budget: int = 6000
    max_file_size_bytes: int = 20_000
    max_tree_depth: int = 4
    allowed_extensions: Set[str] = Field(
        default_factory=lambda: {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".java",
            ".go",
            ".rs",
            ".cpp",
            ".md",
            ".json",
            ".toml",
            ".yml",
            ".yaml",
            ".jsx",
            ".txt",
        }
    )
    ignore_patterns: Set[str] = Field(
        default_factory=lambda: {
            ".git",
            "node_modules",
            "venv",
            ".venv",
            "__pycache__",
            "dist",
            "build",
            "*.lock",
            "*.min.js",
            "package-lock.json",
            "yarn.lock",
            ".idea",
            ".vscode",
            ".pytest_cache",
            ".mypy_cache",
        }
    )


class ContextOutput(BaseModel):
    repo_map: str
    file_summaries: str
    token_count: int
    is_truncated: bool


class TokenizerUtil:
    _encoding = None
    _checked = False

    @classmethod
    def count(cls, text: str) -> int:
        if not text:
            return 0
        if not cls._checked:
            cls._checked = True
            try:
                module = __import__("tiktoken")
                cls._encoding = module.get_encoding("cl100k_base")
            except Exception:
                cls._encoding = None

        if cls._encoding is None:
            return max(1, len(text) // 4)
        return len(cls._encoding.encode(text))


def is_safe_path(base: Path, target: Path) -> bool:
    try:
        base_resolved = base.resolve()
        target_resolved = target.resolve()
        return base_resolved == target_resolved or base_resolved in target_resolved.parents
    except Exception:
        return False


class ProductionContextBuilder:
    """Build a token-bounded repository mental map for LLM review prompts."""

    def __init__(self, config: Optional[ContextConfig] = None):
        self.config = config or ContextConfig()

    async def build(self, repo_path: str) -> ContextOutput:
        root = Path(repo_path)
        if not root.exists():
            raise FileNotFoundError(f"Repo not found at {repo_path}")

        tree_str, file_paths = await asyncio.to_thread(self._generate_tree_and_list, root)

        current_tokens = TokenizerUtil.count(tree_str)
        remaining_budget = max(0, self.config.max_token_budget - current_tokens)

        priority_files = self._prioritize_files(file_paths)
        file_contents: List[str] = []
        is_truncated = False

        for rel_path in priority_files:
            if remaining_budget <= 0:
                is_truncated = True
                break

            full_path = root / rel_path
            content = await self._read_file_safe(root, full_path)
            if not content:
                continue

            entry = f"\nFile: {rel_path}\n```\n{content}\n```\n"
            entry_tokens = TokenizerUtil.count(entry)

            if remaining_budget - entry_tokens < 0:
                is_truncated = True
                break

            file_contents.append(entry)
            remaining_budget -= entry_tokens

        used_tokens = self.config.max_token_budget - remaining_budget
        return ContextOutput(
            repo_map=tree_str,
            file_summaries="".join(file_contents),
            token_count=used_tokens,
            is_truncated=is_truncated,
        )

    def _generate_tree_and_list(self, root: Path) -> Tuple[str, List[str]]:
        output_lines: List[str] = []
        collected_files: List[str] = []

        def _scan(directory: Path, prefix: str = "", depth: int = 0):
            if depth > self.config.max_tree_depth:
                return

            try:
                entries = sorted(list(os.scandir(directory)), key=lambda e: (not e.is_dir(), e.name.lower()))
            except (PermissionError, FileNotFoundError, OSError):
                return

            entries = [
                e
                for e in entries
                if not any(fnmatch.fnmatch(e.name, p) for p in self.config.ignore_patterns)
            ]

            for i, entry in enumerate(entries):
                is_last = i == len(entries) - 1
                connector = "└── " if is_last else "├── "
                output_lines.append(f"{prefix}{connector}{entry.name}")

                entry_path = Path(entry.path)
                if not is_safe_path(root, entry_path):
                    continue

                if entry.is_dir(follow_symlinks=False):
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    _scan(entry_path, new_prefix, depth + 1)
                elif entry.is_file(follow_symlinks=False):
                    if entry_path.suffix.lower() in self.config.allowed_extensions:
                        try:
                            rel_path = entry_path.relative_to(root)
                            collected_files.append(str(rel_path).replace("\\", "/"))
                        except ValueError:
                            continue

        output_lines.append(root.name + "/")
        _scan(root)
        return "\n".join(output_lines), collected_files

    def _prioritize_files(self, file_paths: List[str]) -> List[str]:
        def score(path_str: str) -> int:
            p = path_str.lower()
            if "readme" in p:
                return 0
            if "project.md" in p or "architecture" in p:
                return 1
            if any(x in p for x in ["package.json", "requirements.txt", "dockerfile", "cargo.toml", "pyproject.toml"]):
                return 2
            if "src/" in p or "/app" in p or p.startswith("src"):
                return 3
            return 4

        return sorted(file_paths, key=score)

    async def _read_file_safe(self, root: Path, path: Path) -> Optional[str]:
        try:
            if not path.exists() or not is_safe_path(root, path):
                return None

            stats = await asyncio.to_thread(path.stat)
            if stats.st_size > self.config.max_file_size_bytes:
                return f"[Skipped: File too large ({stats.st_size} bytes)]"

            content = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="ignore")
            if "\0" in content:
                return None

            return content
        except Exception as exc:
            logger.warning("Error reading %s: %s", path, exc)
            return None


class ProjectContextBuilder:
    """Compatibility wrapper that returns a prompt-ready context block string."""

    @classmethod
    async def build(
        cls,
        repo_path: str,
        repo_full_name: str,
        pr_title: str,
        changed_files: Optional[List[str]] = None,
    ) -> str:
        try:
            builder = ProductionContextBuilder()
            context = await builder.build(repo_path)

            changed_files = changed_files or []
            changed_preview = "\n".join(f"- {file_path}" for file_path in changed_files[:25]) or "- None"
            if len(changed_files) > 25:
                changed_preview += f"\n- ... and {len(changed_files) - 25} more"

            truncation_note = "Yes" if context.is_truncated else "No"
            return f"""## Project Context
Repository: {repo_full_name}
PR Title: {pr_title}
Token Budget Used: {context.token_count}/{builder.config.max_token_budget}
Truncated: {truncation_note}

### Repository Map
```text
{context.repo_map}
```

### Changed Files in This PR
{changed_preview}

### Key File Summaries
{context.file_summaries if context.file_summaries else "No readable key files found within current budget."}
"""
        except Exception as exc:
            return f"## Project Context\nCould not build detailed context: {exc}"
