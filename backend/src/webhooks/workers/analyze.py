"""
Analyze Worker — Stage 2: Static analysis + context building + index update.

Responsibilities:
  - Run linters (if Docker checks enabled)
  - Build project context (structure, dependencies)
  - Update repo-scoped vector index
  - Assemble the context pack for LLM review
"""

import os
import logging
from typing import Dict, Any, Optional

from workers.base import BaseWorker

logger = logging.getLogger("agenticpr.worker.analyze")


class AnalyzeWorker(BaseWorker):
    QUEUE_NAME = "review:analyze"
    GROUP_NAME = "cg_analyze"
    STAGE_NAME = "analyzing"
    MAX_RETRIES = 2
    TIMEOUT_SECONDS = 300
    BACKOFF_SECONDS = [10, 30]
    NEXT_QUEUE = "review:llm"
    NEXT_STAGE_STATUS = "reviewing"
    
    async def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run static analysis and build context for LLM review."""
        job_id = data["job_id"]
        repo_full_name = data["repo_full_name"]
        diff_text = data.get("diff_text", "")
        changed_files = data.get("changed_files", [])
        workspace_dir = data.get("workspace_dir", "")
        clone_success = data.get("clone_success", False)
        
        logger.info(f"[analyze] Job {job_id}: Analyzing {len(changed_files)} files in {repo_full_name}")
        
        context_parts = []
        static_findings = []
        
        # --- 1. Run Docker-based static checks (if enabled and clone succeeded) ---
        from config import config
        if config.ENABLE_DOCKER_CHECKS and clone_success and workspace_dir:
            try:
                docker_results = await self._run_docker_checks(workspace_dir, changed_files)
                static_findings.extend(docker_results)
                logger.info(f"[analyze] Job {job_id}: Docker checks found {len(docker_results)} issues")
            except Exception as e:
                logger.warning(f"[analyze] Job {job_id}: Docker checks failed: {e}")
        
        # --- 2. Build project context ---
        if clone_success and workspace_dir and os.path.exists(workspace_dir):
            try:
                project_context = await self._build_project_context(workspace_dir, changed_files)
                context_parts.append(project_context)
            except Exception as e:
                logger.warning(f"[analyze] Job {job_id}: Context building failed: {e}")
        
        # --- 3. Update repo-scoped vector index ---
        try:
            relevant_context = await self._update_index(
                repo_full_name, workspace_dir, changed_files, clone_success
            )
            if relevant_context:
                context_parts.append(relevant_context)
        except Exception as e:
            logger.warning(f"[analyze] Job {job_id}: Indexing failed: {e} (review proceeds without vector context)")
        
        return {
            "context_pack": "\n\n---\n\n".join(context_parts),
            "static_findings": static_findings,
        }
    
    async def _run_docker_checks(self, workspace_dir: str, changed_files: list) -> list:
        """Run linter and security checks via Docker container."""
        findings = []
        
        try:
            from agents.linter import LinterAgent
            linter = LinterAgent()
            
            for filepath in changed_files[:20]:  # Limit to 20 files
                if filepath.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                    result = linter.analyze_file(os.path.join(workspace_dir, filepath))
                    if result:
                        findings.extend(result)
        except Exception as e:
            logger.debug(f"Linter not available: {e}")
        
        return findings
    
    async def _build_project_context(self, workspace_dir: str, changed_files: list) -> str:
        """Build project structure context for LLM."""
        context = "## Project Context\n\n"
        
        # File tree (limited depth)
        try:
            tree_lines = []
            for root, dirs, files in os.walk(workspace_dir):
                depth = root.replace(workspace_dir, "").count(os.sep)
                if depth > 3:
                    dirs.clear()
                    continue
                indent = "  " * depth
                dirname = os.path.basename(root)
                if dirname.startswith('.'):
                    dirs.clear()
                    continue
                tree_lines.append(f"{indent}{dirname}/")
                for f in files[:10]:
                    tree_lines.append(f"{indent}  {f}")
            
            if tree_lines:
                context += "### File Structure\n```\n"
                context += "\n".join(tree_lines[:50])
                context += "\n```\n\n"
        except Exception:
            pass
        
        # Adjacent file content (files in same directory as changed files)
        adjacent_content = []
        seen_dirs = set()
        for filepath in changed_files[:5]:
            dir_path = os.path.dirname(os.path.join(workspace_dir, filepath))
            if dir_path in seen_dirs:
                continue
            seen_dirs.add(dir_path)
            
            if os.path.exists(dir_path):
                for f in os.listdir(dir_path)[:5]:
                    full_path = os.path.join(dir_path, f)
                    if os.path.isfile(full_path) and os.path.getsize(full_path) < 10000:
                        try:
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                                content = fh.read()
                            adjacent_content.append(f"### {filepath}\n```\n{content[:3000]}\n```")
                        except Exception:
                            pass
        
        if adjacent_content:
            context += "### Related Files\n" + "\n\n".join(adjacent_content[:3])
        
        return context
    
    async def _update_index(
        self, repo_full_name: str, workspace_dir: str,
        changed_files: list, clone_success: bool
    ) -> str:
        """Update repo-scoped vector index and retrieve relevant context."""
        if not clone_success or not workspace_dir:
            return ""
        
        try:
            from core.indexing.manager import IndexManager
            
            # Use repo-scoped collection name
            collection_name = f"repo__{repo_full_name.replace('/', '__')}"
            
            manager = IndexManager(collection_name=collection_name)
            
            # Index changed files
            indexed_count = 0
            for filepath in changed_files[:30]:
                full_path = os.path.join(workspace_dir, filepath)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    try:
                        manager.index_file(full_path, filepath)
                        indexed_count += 1
                    except Exception:
                        pass
            
            logger.info(f"[analyze] Indexed {indexed_count} files in collection {collection_name}")
            
            # Query for relevant context
            relevant = []
            for filepath in changed_files[:5]:
                try:
                    results = manager.query(f"What does {filepath} do?", top_k=3)
                    for r in results:
                        relevant.append(r.get("text", ""))
                except Exception:
                    pass
            
            if relevant:
                return "## Relevant Codebase Context\n\n" + "\n\n".join(relevant[:5])
                
        except Exception as e:
            logger.debug(f"Index update not available: {e}")
        
        return ""
