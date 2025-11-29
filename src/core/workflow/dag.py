"""
DAG (Directed Acyclic Graph)

Data structures for workflow definition.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class NodeType(Enum):
    """Types of workflow nodes."""
    TASK = "task"  # Execute an agent task
    CONDITION = "condition"  # Conditional branching
    PARALLEL = "parallel"  # Parallel execution
    WAIT = "wait"  # Wait for condition
    TRANSFORM = "transform"  # Data transformation
    NOTIFY = "notify"  # Send notification


class NodeStatus(Enum):
    """Node execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Node:
    """A node in the workflow DAG."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: NodeType = NodeType.TASK
    
    # Task configuration
    action: str = ""
    agent: Optional[str] = None
    payload: dict[str, Any] = field(default_factory=dict)
    
    # Execution settings
    timeout: int = 300
    retry_count: int = 0
    retry_delay: int = 5
    continue_on_failure: bool = False
    
    # Condition (for CONDITION nodes)
    condition: Optional[str] = None  # Python expression
    condition_fn: Optional[Callable[[dict], bool]] = None
    
    # Transform (for TRANSFORM nodes)
    transform_fn: Optional[Callable[[dict], dict]] = None
    
    # Runtime state
    status: NodeStatus = NodeStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "action": self.action,
            "agent": self.agent,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class Edge:
    """An edge connecting two nodes."""
    source: str  # Source node ID
    target: str  # Target node ID
    condition: Optional[str] = None  # Optional condition for this edge


class DAG:
    """
    Directed Acyclic Graph for workflow definition.
    
    Provides:
    - Node and edge management
    - Topological sorting
    - Cycle detection
    - Dependency resolution
    """
    
    def __init__(self, name: str = "workflow"):
        self.name = name
        self.id = str(uuid.uuid4())
        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []
        self._adjacency: dict[str, list[str]] = {}  # node -> children
        self._reverse_adj: dict[str, list[str]] = {}  # node -> parents
    
    def add_node(self, node: Node) -> str:
        """Add a node to the DAG."""
        self._nodes[node.id] = node
        self._adjacency[node.id] = []
        self._reverse_adj[node.id] = []
        return node.id
    
    def add_edge(self, source: str, target: str, condition: Optional[str] = None) -> None:
        """Add an edge between nodes."""
        if source not in self._nodes:
            raise ValueError(f"Source node not found: {source}")
        if target not in self._nodes:
            raise ValueError(f"Target node not found: {target}")
        
        edge = Edge(source=source, target=target, condition=condition)
        self._edges.append(edge)
        self._adjacency[source].append(target)
        self._reverse_adj[target].append(source)
        
        # Validate no cycles
        if self._has_cycle():
            self._edges.remove(edge)
            self._adjacency[source].remove(target)
            self._reverse_adj[target].remove(source)
            raise ValueError("Adding this edge would create a cycle")
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        return self._nodes.get(node_id)
    
    def get_children(self, node_id: str) -> list[str]:
        """Get child node IDs."""
        return self._adjacency.get(node_id, [])
    
    def get_parents(self, node_id: str) -> list[str]:
        """Get parent node IDs."""
        return self._reverse_adj.get(node_id, [])
    
    def get_root_nodes(self) -> list[str]:
        """Get nodes with no parents (entry points)."""
        return [nid for nid, parents in self._reverse_adj.items() if not parents]
    
    def get_leaf_nodes(self) -> list[str]:
        """Get nodes with no children (exit points)."""
        return [nid for nid, children in self._adjacency.items() if not children]
    
    def topological_sort(self) -> list[str]:
        """Return nodes in topological order."""
        visited = set()
        result = []
        
        def visit(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            
            for child in self._adjacency.get(node_id, []):
                visit(child)
            
            result.append(node_id)
        
        for node_id in self._nodes:
            visit(node_id)
        
        return list(reversed(result))
    
    def _has_cycle(self) -> bool:
        """Check if the graph has a cycle."""
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = {nid: WHITE for nid in self._nodes}
        
        def dfs(node_id: str) -> bool:
            colors[node_id] = GRAY
            
            for child in self._adjacency.get(node_id, []):
                if colors[child] == GRAY:
                    return True
                if colors[child] == WHITE and dfs(child):
                    return True
            
            colors[node_id] = BLACK
            return False
        
        for node_id in self._nodes:
            if colors[node_id] == WHITE:
                if dfs(node_id):
                    return True
        
        return False
    
    def validate(self) -> list[str]:
        """Validate the DAG and return list of issues."""
        issues = []
        
        # Check for empty DAG
        if not self._nodes:
            issues.append("DAG has no nodes")
        
        # Check for disconnected nodes
        roots = self.get_root_nodes()
        if len(roots) == 0 and self._nodes:
            issues.append("DAG has no root nodes")
        
        # Check for cycles (should be caught earlier, but double-check)
        if self._has_cycle():
            issues.append("DAG contains a cycle")
        
        # Check task nodes have actions
        for node in self._nodes.values():
            if node.type == NodeType.TASK and not node.action:
                issues.append(f"Task node {node.name or node.id} has no action")
        
        return issues
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [{"source": e.source, "target": e.target} for e in self._edges],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DAG":
        """Create DAG from dictionary."""
        dag = cls(name=data.get("name", "workflow"))
        dag.id = data.get("id", dag.id)
        
        # Add nodes
        for node_data in data.get("nodes", []):
            node = Node(
                id=node_data["id"],
                name=node_data.get("name", ""),
                type=NodeType(node_data.get("type", "task")),
                action=node_data.get("action", ""),
                agent=node_data.get("agent"),
                payload=node_data.get("payload", {}),
            )
            dag.add_node(node)
        
        # Add edges
        for edge_data in data.get("edges", []):
            dag.add_edge(edge_data["source"], edge_data["target"])
        
        return dag
