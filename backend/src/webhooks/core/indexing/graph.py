"""
Part 5: Symbol Graph
====================
Builds a network of code relationships (Callers & Callees).
Allows the bot to say: "Change X might break Y because Y calls X".
"""

import networkx as nx
from typing import List, Dict, Any, Set
from .parser import CodeNode

class SymbolGraph:
    """
    A directed graph representing code dependencies.
    Nodes = Functions/Classes
    Edges = "Calls" relationships
    """

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, node: CodeNode):
        """Add a symbol to the graph."""
        # We use the name as the ID for now. 
        # In a real system, we might want a fully qualified name (module.class.method).
        # For this MVP, we assume names are relatively unique or we just care about local context.
        
        # Store metadata
        self.graph.add_node(
            node.name, 
            type=node.type,
            filepath=node.filepath,
            start_line=node.start_line
        )

    def add_dependency(self, caller: str, callee: str):
        """Register that 'caller' invokes 'callee'."""
        self.graph.add_edge(caller, callee)

    def build_from_nodes(self, nodes: List[CodeNode]):
        """
        Constructs the graph from a list of parsed nodes.
        1. Add all nodes first.
        2. Then add edges based on `node.calls`.
        """
        # 1. Add all nodes
        available_symbols: Set[str] = set()
        for node in nodes:
            self.add_node(node)
            available_symbols.add(node.name)

        # 2. Add edges
        for node in nodes:
            for called_func_name in node.calls:
                # Only add edge if the callee actually exists in our codebase
                # (We don't want to graph calls to 'print' or 'len')
                if called_func_name in available_symbols:
                    self.add_dependency(node.name, called_func_name)

    def get_context(self, symbol_name: str) -> Dict[str, List[str]]:
        """
        Returns the neighborhood of a symbol:
        - callers: functions that call THIS symbol (Predecessors)
        - callees: functions that THIS symbol calls (Successors)
        """
        if symbol_name not in self.graph:
            return {"callers": [], "callees": []}

        try:
            callers = list(self.graph.predecessors(symbol_name))
            callees = list(self.graph.successors(symbol_name))
            return {
                "callers": callers,
                "callees": callees
            }
        except Exception:
            # Safety net for networkx errors
            return {"callers": [], "callees": []}

    def remove_file_nodes(self, file_path: str):
        """
        Removes all nodes associated with a specific file from the graph.
        Crucial for incremental indexing to prevent ghost nodes.
        """
        nodes_to_remove = []
        try:
            # Identify nodes belonging to this file
            for node, data in self.graph.nodes(data=True):
                if data.get("filepath") == file_path:
                    nodes_to_remove.append(node)
            
            if nodes_to_remove:
                self.graph.remove_nodes_from(nodes_to_remove)
                
        except Exception as e:
            print(f"⚠️ Failed to remove nodes for {file_path}: {e}")
