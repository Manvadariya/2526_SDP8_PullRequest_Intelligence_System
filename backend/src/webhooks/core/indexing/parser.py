"""
Part 2: AST-Based Code Parser
==============================
Uses Tree-Sitter (the same technology as GitHub & NeoVim) to parse source code
into structured CodeNode objects for vector embedding and graph analysis.

Supports: Python, JavaScript, TypeScript, Java, Go, C++
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import tree_sitter_languages


# ─── Data Model ───────────────────────────────────────────────────────────────

@dataclass
class CodeNode:
    """A single extractable unit of code (function, method, or class)."""

    type: str  # "function", "method", "class"
    name: str  # e.g. "process_payment", "<anonymous>"
    content: str  # full source text of the node
    start_line: int
    end_line: int
    docstring: str = ""  # extracted separately for embedding weight
    complexity: int = 0  # basic cyclomatic-complexity estimate
    calls: List[str] = field(default_factory=list)  # functions called by this node
    language: str = ""
    filepath: str = ""

    def __repr__(self) -> str:
        tag = f"{self.type}:{self.name}"
        lines = f"L{self.start_line}-{self.end_line}"
        cx = f"cx={self.complexity}" if self.complexity else ""
        doc = "has-doc" if self.docstring else "no-doc"
        cal = f"calls={len(self.calls)}" if self.calls else ""
        parts = [tag, lines, doc, cx, cal]
        return f"<CodeNode {' '.join(filter(None, parts))}>"


# ─── Language Configuration ───────────────────────────────────────────────────

# Maps file extension -> Tree-Sitter language name
_EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
}

# Tree-Sitter S-expression queries per language
# Each query captures: @name (identifier) and @definition (full node)
_LANGUAGE_QUERIES = {
    "python": """
        (function_definition
            name: (identifier) @name) @definition

        (class_definition
            name: (identifier) @name) @definition
    """,

    "javascript": """
        (function_declaration
            name: (identifier) @name) @definition

        (class_declaration
            name: (identifier) @name) @definition

        (method_definition
            name: (property_identifier) @name) @definition

        (arrow_function) @definition

        (variable_declarator
            name: (identifier) @name
            value: (arrow_function)) @definition
    """,

    "typescript": """
        (function_declaration
            name: (identifier) @name) @definition

        (class_declaration
            name: (type_identifier) @name) @definition

        (method_definition
            name: (property_identifier) @name) @definition

        (arrow_function) @definition

        (variable_declarator
            name: (identifier) @name
            value: (arrow_function)) @definition
    """,

    "java": """
        (method_declaration
            name: (identifier) @name) @definition

        (class_declaration
            name: (identifier) @name) @definition

        (constructor_declaration
            name: (identifier) @name) @definition
    """,

    "go": """
        (function_declaration
            name: (identifier) @name) @definition

        (method_declaration
            name: (field_identifier) @name) @definition
    """,

    "cpp": """
        (function_definition
            declarator: (function_declarator
                declarator: (identifier) @name)) @definition

        (function_definition
            declarator: (function_declarator
                declarator: (qualified_identifier) @name)) @definition

        (class_specifier
            name: (type_identifier) @name) @definition
    """,

    "c": """
        (function_definition
            declarator: (function_declarator
                declarator: (identifier) @name)) @definition
    """,
}

# Queries to find FUNCTION CALLS within a node
_CALL_QUERIES = {
    "python": """
        (call function: (identifier) @func_name)
        (call function: (attribute attribute: (identifier) @method_name))
    """,
    "javascript": """
        (call_expression function: (identifier) @func_name)
        (call_expression function: (member_expression property: (property_identifier) @method_name))
    """,
    "typescript": """
        (call_expression function: (identifier) @func_name)
        (call_expression function: (member_expression property: (property_identifier) @method_name))
    """,
    "java": """
        (method_invocation name: (identifier) @func_name)
    """,
    "go": """
        (call_expression function: (identifier) @func_name)
        (call_expression function: (selector_expression field: (field_identifier) @method_name))
    """,
    "cpp": """
        (call_expression function: (identifier) @func_name)
        (call_expression function: (field_expression field: (field_identifier) @method_name))
    """,
    "c": """
        (call_expression function: (identifier) @func_name)
    """
}

# Node types that represent classes vs functions per language
_CLASS_TYPES = {
    "python": {"class_definition"},
    "javascript": {"class_declaration"},
    "typescript": {"class_declaration"},
    "java": {"class_declaration"},
    "go": set(),  # Go has no classes
    "cpp": {"class_specifier"},
    "c": set(),
}

# Node types that represent anonymous constructs
_ANON_TYPES = {"arrow_function", "lambda"}

# Field names for the body of a function/method per language
_BODY_FIELDS = {
    "python": "body",
    "javascript": "body",
    "typescript": "body",
    "java": "body",
    "go": "body",
    "cpp": "body",
    "c": "body",
}



# ─── Complexity Estimator ─────────────────────────────────────────────────────

# Keywords / patterns that increase cyclomatic complexity
_COMPLEXITY_PATTERNS = {
    "python": re.compile(
        r"\b(if|elif|for|while|except|and|or|assert)\b"
    ),
    "javascript": re.compile(
        r"\b(if|else if|for|while|catch|switch|case|\?\?|\|\||&&)\b"
    ),
    "typescript": re.compile(
        r"\b(if|else if|for|while|catch|switch|case|\?\?|\|\||&&)\b"
    ),
    "java": re.compile(
        r"\b(if|else if|for|while|catch|switch|case|&&|\|\|)\b"
    ),
    "go": re.compile(
        r"\b(if|for|select|case|&&|\|\|)\b"
    ),
    "cpp": re.compile(
        r"\b(if|else if|for|while|catch|switch|case|&&|\|\|)\b"
    ),
    "c": re.compile(
        r"\b(if|else if|for|while|switch|case|&&|\|\|)\b"
    ),
}


def _estimate_complexity(code: str, language: str) -> int:
    """
    Basic cyclomatic complexity: 1 + count of branching keywords.
    Not exact, but very useful as a heuristic for prioritising review.
    """
    pattern = _COMPLEXITY_PATTERNS.get(language)
    if not pattern:
        return 1
    return 1 + len(pattern.findall(code))


# ─── Docstring Extraction ────────────────────────────────────────────────────

def _extract_docstring_python(node) -> str:
    """Extract Python docstring from the first expression_statement child."""
    for child in node.children:
        if child.type == "block":
            for stmt in child.children:
                if stmt.type == "expression_statement":
                    for expr in stmt.children:
                        if expr.type == "string":
                            raw = expr.text.decode("utf-8")
                            # Strip triple-quotes
                            for q in ('"""', "'''"):
                                if raw.startswith(q) and raw.endswith(q):
                                    raw = raw[3:-3]
                                    break
                            return textwrap.dedent(raw).strip()
                # Only check the very first statement
                break
    return ""


def _extract_docstring_jsdoc(source_code: str, start_byte: int) -> str:
    """Look for a JSDoc /** ... */ comment immediately preceding the node."""
    preceding = source_code[:start_byte].rstrip()
    if preceding.endswith("*/"):
        idx = preceding.rfind("/**")
        if idx != -1:
            raw = preceding[idx:]
            # Clean JSDoc: remove /**, */, and leading *
            lines = raw.split("\n")
            cleaned = []
            for line in lines:
                line = line.strip()
                line = line.lstrip("/*").rstrip("*/").strip()
                if line:
                    cleaned.append(line)
            return "\n".join(cleaned)
    return ""


def _extract_docstring(node, language: str, source_code: str) -> str:
    """Language-aware docstring extraction."""
    if language == "python":
        return _extract_docstring_python(node)
    elif language in ("javascript", "typescript", "java", "cpp", "c", "go"):
        return _extract_docstring_jsdoc(source_code, node.start_byte)
    return ""


# ─── Universal Parser ────────────────────────────────────────────────────────

class UniversalParser:
    """
    Polyglot AST parser using Tree-Sitter.

    Extracts functions, methods, and classes from source code with:
      - Semantic docstring separation
      - Basic cyclomatic complexity estimation
      - Fault-tolerant parsing (can parse valid parts even with syntax errors)
    """

    def __init__(self):
        self._parsers = {}
        self._languages = {}
        self._queries = {}

    def _get_parser(self, language: str):
        """Lazy-initialise parser and query for a language."""
        if language not in self._parsers:
            self._parsers[language] = tree_sitter_languages.get_parser(language)
            self._languages[language] = tree_sitter_languages.get_language(language)

            query_src = _LANGUAGE_QUERIES.get(language, "")
            if query_src.strip():
                self._queries[language] = self._languages[language].query(query_src)
            else:
                self._queries[language] = None

        return self._parsers[language]

    @staticmethod
    def detect_language(filename: str) -> Optional[str]:
        """Detect language from file extension."""
        ext = Path(filename).suffix.lower()
        return _EXT_TO_LANG.get(ext)

    @staticmethod
    def supported_extensions() -> list[str]:
        """Return all supported file extensions."""
        return list(_EXT_TO_LANG.keys())

    def parse_code(self, code: str, filename: str) -> List[CodeNode]:
        """
        Parse source code into a list of CodeNode objects.

        Args:
            code: The full source code string.
            filename: Filename (used to detect language from extension).

        Returns:
            List of CodeNode objects extracted from the code.
        """
        language = self.detect_language(filename)
        if language is None:
            return []

        parser = self._get_parser(language)
        query = self._queries.get(language)
        if query is None:
            return []

        source_bytes = code.encode("utf-8")
        tree = parser.parse(source_bytes)

        nodes: List[CodeNode] = []
        seen_ranges = set()  # avoid duplicates

        # Run the query
        captures = query.captures(tree.root_node)

        # Group captures: each @definition may have an associated @name
        i = 0
        while i < len(captures):
            cap_node, cap_name = captures[i]

            if cap_name == "definition":
                definition_node = cap_node
                name = "<anonymous>"

                # Check if the previous capture was a @name for this definition
                if i > 0:
                    prev_node, prev_name = captures[i - 1]
                    if prev_name == "name" and self._is_child_of(prev_node, definition_node):
                        name = prev_node.text.decode("utf-8")

                # Check if the next capture is a @name for this definition
                if name == "<anonymous>" and i + 1 < len(captures):
                    next_node, next_name = captures[i + 1]
                    if next_name == "name" and self._is_child_of(next_node, definition_node):
                        name = next_node.text.decode("utf-8")
                        i += 1  # skip the name capture

                # Dedup by byte range
                node_range = (definition_node.start_byte, definition_node.end_byte)
                if node_range in seen_ranges:
                    i += 1
                    continue
                seen_ranges.add(node_range)

                # Determine type
                node_type_str = definition_node.type
                class_types = _CLASS_TYPES.get(language, set())
                if node_type_str in class_types:
                    code_type = "class"
                elif node_type_str in _ANON_TYPES:
                    code_type = "function"
                elif "method" in node_type_str:
                    code_type = "method"
                else:
                    code_type = "function"

                # Extract content
                content = definition_node.text.decode("utf-8")
                content = textwrap.dedent(content)

                # Extract docstring
                docstring = _extract_docstring(definition_node, language, code)

                # Estimate complexity
                complexity = _estimate_complexity(content, language)

                # SEMANTIC DEDUPLICATION: Create Skeleton Class
                if code_type == "class":
                    skeleton = self._create_class_skeleton(definition_node, language, source_bytes)
                    if skeleton:
                        content = skeleton

                # NEW: Extract function calls
                calls = self._extract_calls(definition_node, language, source_bytes)

                start_line = definition_node.start_point[0] + 1  # 1-indexed
                end_line = definition_node.end_point[0] + 1

                nodes.append(CodeNode(
                    type=code_type,
                    name=name,
                    content=content,
                    start_line=start_line,
                    end_line=end_line,
                    docstring=docstring,
                    complexity=complexity,
                    calls=calls,
                    language=language,
                    filepath=filename,
                ))

            i += 1

        return nodes

    def _extract_calls(self, node, language: str, source_bytes: bytes) -> List[str]:
        """Finds all function calls within the given node's scope."""
        query_scm = _CALL_QUERIES.get(language)
        if not query_scm:
            return []
            
        try:
            lang_obj = tree_sitter_languages.get_language(language)
            query = lang_obj.query(query_scm)
            # captures() on a node searches that node's subtree
            captures = query.captures(node)
            
            calls = set()
            for captured_node, tag in captures:
                if tag in ["func_name", "method_name"]:
                    call_name = source_bytes[captured_node.start_byte:captured_node.end_byte].decode("utf8")
                    calls.add(call_name)
            
            return list(calls)
        except Exception as e:
            # Fail silently on extraction errors to avoid breaking the whole parse
            return []

    @staticmethod
    def _is_child_of(child_node, parent_node) -> bool:
        """Check if child_node is a direct or indirect child of parent_node."""
        return (
            child_node.start_byte >= parent_node.start_byte
            and child_node.end_byte <= parent_node.end_byte
        )

    def _create_class_skeleton(self, class_node, language: str, source_bytes: bytes) -> Optional[str]:
        """
        Creates a 'skeleton' version of the class with method bodies masked.
        Returns the modified source string, or None if failed.
        """
        if language not in _BODY_FIELDS:
            return None

        # internal helper to check if a node is a method/function
        def is_method_like(node_type):
            return any(x in node_type for x in ["method", "function", "constructor"])

        # Identify ranges to mask
        mask_ranges = []
        
        # Traverse children to find methods
        # We use a cursor or direct children iteration. 
        # Direct children check is safer strictly for top-level methods of the class.
        cursor = class_node.walk()
        visited_children = False
        if cursor.goto_first_child():
            visited_children = True
            while visited_children:
                child = cursor.node
                
                # Check if it's a method definition
                if is_method_like(child.type):
                    # Exclude __init__ / constructor
                    # We need to find the name node of this child
                    name = ""
                    child_cursor = child.walk()
                    if child_cursor.goto_first_child():
                        while True:
                            if "name" in child_cursor.field_name or "identifier" in child_cursor.node.type:
                                name = child_cursor.node.text.decode("utf-8", errors="ignore")
                                break
                            if not child_cursor.goto_next_sibling():
                                break
                    
                    is_constructor = name == "__init__" or name == "constructor" or child.type == "constructor_declaration"
                    
                    if not is_constructor:
                        # Find body to mask
                        body = child.child_by_field_name(_BODY_FIELDS.get(language, "body"))
                        if body:
                            mask_ranges.append((body.start_byte, body.end_byte))
                
                if not cursor.goto_next_sibling():
                    break

        if not mask_ranges:
            return None

        # sort descending to replace safely
        mask_ranges.sort(key=lambda x: x[0], reverse=True)

        # We work on the CLASS content bytes
        # BUT the ranges are absolute file offsets.
        # We need to map them to the class content string.
        
        class_start = class_node.start_byte
        class_end = class_node.end_byte
        
        # Create a mutable bytearray of the class content
        class_bytes = bytearray(source_bytes[class_start:class_end])
        
        for start, end in mask_ranges:
            # Shift offsets to be relative to class start
            if start < class_start or end > class_end:
                continue
            
            rel_start = start - class_start
            rel_end = end - class_start
            
            # Replacement: ... or pass
            replacement = b" ..." 
            if language == "python":
                replacement = b" ..." # or pass
            
            # Replace
            class_bytes[rel_start:rel_end] = replacement

        return class_bytes.decode("utf-8")



# ─── Convenience ──────────────────────────────────────────────────────────────

def parse_file(filepath: str) -> List[CodeNode]:
    """Parse a file from disk and return its CodeNodes."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    code = path.read_text(encoding="utf-8", errors="replace")
    parser = UniversalParser()
    return parser.parse_code(code, path.name)
