"""
Part 6: Context Builder
=======================
Orchestrates the "Eyes" (Parser), "Memory" (Vector DB), and "Logic" (Graph)
to build the perfect context for the LLM.
"""

import os
import re
import tiktoken
from typing import Dict, Any, List, Set, Tuple
from .indexing.vector_store import CodeVectorStore
from .indexing.graph import SymbolGraph
from .indexing.parser import UniversalParser, CodeNode

class ContextBuilder:
    """
    Assembles context for a code change by combining:
    1. The code itself (Parser)
    2. Similar code / examples (Vector Store)
    3. Dependency impact (Symbol Graph)
    """

    def __init__(self, vector_store: CodeVectorStore = None, graph: SymbolGraph = None):
        self.parser = UniversalParser()
        # Allow injection or lazy load
        self.vector_store = vector_store if vector_store else CodeVectorStore()
        self.graph = graph if graph else SymbolGraph()
        
        # Tiktoken encoder for token counting (approximate for context window)
        try:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        except:
            self.encoder = None

    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken or simple fallback."""
        if not text:
            return 0
        if self.encoder:
            return len(self.encoder.encode(text))
        return len(text.split())  # Rough fallback

    def _parse_diff_changed_lines(self, diff_text: str) -> List[int]:
        """
        Parses a unified diff to find line numbers of added/modified lines in the new file.
        Returns a list of 1-based line numbers.
        """
        changed_lines = []
        current_line = 0
        
        # Regex for chunk header: @@ -old_start,old_len +new_start,new_len @@
        hunk_header_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

        for line in diff_text.splitlines():
            match = hunk_header_re.match(line)
            if match:
                current_line = int(match.group(1)) - 1 # We'll start incrementing immediatelly
                continue
            
            if line.startswith("+++") or line.startswith("---"):
                continue
                
            if line.startswith("+"):
                current_line += 1
                changed_lines.append(current_line)
            elif line.startswith("-"):
                # Deleted line, doesn't exist in new file, so doesn't advance current_line
                pass
            else:
                # Context line
                current_line += 1
                
        return changed_lines

    def build_context(self, file_path: str, full_file_content: str, diff_text: str = "") -> Dict[str, Any]:
        """
        Analyzes a changed file and builds context for the LLM.
        Priority:
        1. Changed Nodes (Impact Analysis)
        2. Changed Nodes (Source Code)
        3. Similar Code (Vector Search) - Pruned if tokens > 8000
        """
        context = {
            "file_path": file_path,
            "analysis": [],
            "formatted_prompt": ""
        }

        # 1. Parsing & Diff Analysis
        nodes = self.parser.parse_code(full_file_content, file_path)
        
        # Update ephemeral graph
        self.graph.build_from_nodes(nodes)

        changed_lines = self._parse_diff_changed_lines(diff_text) if diff_text else []
        
        # Identify changed nodes
        # If no diff provided, treat everything as "changed" (or nothing? Let's assume all for now if empty diff)
        # But usually empty diff means no changes. If diff_text is empty, maybe we just analyze the whole file?
        # For safety, if diff is empty, we might skip contextualization or treat all as relevant.
        # Let's assume if diff is empty, we process significant nodes.
        
        relevant_nodes = []
        if not changed_lines:
            # Fallback: Process all functions/classes
            relevant_nodes = [n for n in nodes if n.type in ["function", "method", "class"]]
        else:
            # Find nodes overlapping with changed lines
            for node in nodes:
                if node.type not in ["function", "method", "class"]:
                    continue
                # Check overlap
                node_range = range(node.start_line, node.end_line + 1)
                if any(line in node_range for line in changed_lines):
                    relevant_nodes.append(node)

        # 2. Gather Context (Tri-Directional)
        impact_sections = []
        code_sections = []
        similar_sections = []

        total_tokens = 0
        TOKEN_LIMIT = 8000

        for node in relevant_nodes:
            # A. Impact (Graph) - Highest Priority (cheap in tokens, high value)
            graph_context = self.graph.get_context(node.name)
            callers = graph_context["callers"]
            callees = graph_context["callees"]
            
            impact_msg = f"Symbol: {node.name} ({node.type})\n"
            if callers:
                impact_msg += f"  - Called By: {', '.join(callers)}\n"
            if callees:
                impact_msg += f"  - Calls: {', '.join(callees)}\n"
            
            if callers or callees:
                impact_sections.append(impact_msg)
                total_tokens += self._count_tokens(impact_msg)

            # B. Self (Source) - High Priority
            code_msg = f"--- {node.name} ---\n{node.content}\n"
            code_sections.append(code_msg)
            total_tokens += self._count_tokens(code_msg)

            # C. Similar Code (Vector) - Lower Priority
            query = f"{node.name} {node.docstring}"
            try:
                similar_hits = self.vector_store.search(query, limit=2)
                for hit in similar_hits:
                    # Don't include self
                    if hit["symbol_name"] == node.name:
                        continue
                        
                    sim_msg = f"Example: {hit['symbol_name']} (Score: {hit['score']:.2f})\n"
                    sim_msg += f"{hit['content']}\n"
                    similar_sections.append(sim_msg)
            except Exception:
                pass # Vector store might fail or be empty

        # 3. Pruning & Assembly
        final_prompt = "## Context Analysis\n\n"
        
        # Add Impact
        if impact_sections:
            final_prompt += "### 1. Impact Analysis (Dependencies)\n"
            final_prompt += "\n".join(impact_sections) + "\n\n"
            
        # Add Changed Code
        if code_sections:
            final_prompt += "### 2. Changed Code Context\n"
            final_prompt += "\n".join(code_sections) + "\n\n"
            
        # Add Similar Code (if budget allows)
        if similar_sections:
            final_prompt += "### 3. Related Code Examples\n"
            for sim_msg in similar_sections:
                sim_tokens = self._count_tokens(sim_msg)
                if total_tokens + sim_tokens < TOKEN_LIMIT:
                    final_prompt += sim_msg + "\n"
                    total_tokens += sim_tokens
                else:
                    final_prompt += "\n[...Matched code omitted due to token limit...]\n"
                    break

        context["formatted_prompt"] = final_prompt
        # Keep raw analysis for debugging/structured use
        context["analysis"] = [n.name for n in relevant_nodes]
        
        return context
