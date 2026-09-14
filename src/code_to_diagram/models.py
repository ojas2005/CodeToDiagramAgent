"""Stable diagram contracts and source evidence."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

DIAGRAM_TYPES = ("components", "api", "er", "auth", "dependencies")


class DiagramError(ValueError):
    """An input or diagram could not be interpreted safely."""


@dataclass(frozen=True, order=True)
class Evidence:
    path: str
    line: int
    detail: str = ""

    def to_dict(self):
        return {"path": self.path, "line": self.line, "detail": self.detail}


@dataclass
class Node:
    id: str
    label: str
    kind: str
    fields: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)

    def add_evidence(self, item: Optional[Evidence]):
        if item is not None and item not in self.evidence:
            self.evidence.append(item)

    def to_dict(self):
        return {"id": self.id, "label": self.label, "kind": self.kind,
                "fields": sorted(set(self.fields)),
                "evidence": [item.to_dict() for item in sorted(self.evidence)]}


@dataclass
class Edge:
    source: str
    target: str
    kind: str
    label: str = ""
    evidence: List[Evidence] = field(default_factory=list)

    @property
    def key(self) -> Tuple[str, str, str, str]:
        return self.source, self.target, self.kind, self.label

    def add_evidence(self, item: Optional[Evidence]):
        if item is not None and item not in self.evidence:
            self.evidence.append(item)

    def to_dict(self):
        return {"source": self.source, "target": self.target, "kind": self.kind,
                "label": self.label,
                "evidence": [item.to_dict() for item in sorted(self.evidence)]}


@dataclass
class Diagram:
    kind: str
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: Dict[Tuple[str, str, str, str], Edge] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def add_node(self, id: str, label: str, kind: str,
                 evidence: Optional[Evidence] = None, fields=None) -> Node:
        if id not in self.nodes:
            self.nodes[id] = Node(id, label, kind)
        node = self.nodes[id]
        node.add_evidence(evidence)
        for value in fields or []:
            if value not in node.fields:
                node.fields.append(value)
        return node

    def add_edge(self, source: str, target: str, kind: str,
                 label: str = "", evidence: Optional[Evidence] = None) -> Edge:
        if source not in self.nodes or target not in self.nodes:
            raise DiagramError("Edge endpoints must exist before adding a relationship")
        key = source, target, kind, label
        if key not in self.edges:
            self.edges[key] = Edge(source, target, kind, label)
        self.edges[key].add_evidence(evidence)
        return self.edges[key]

    def to_dict(self):
        return {"kind": self.kind,
                "nodes": [self.nodes[key].to_dict() for key in sorted(self.nodes)],
                "edges": [self.edges[key].to_dict() for key in sorted(self.edges)],
                "notes": list(self.notes)}


@dataclass
class Architecture:
    repository: str
    revision: str
    diagrams: Dict[str, Diagram] = field(default_factory=lambda: {
        kind: Diagram(kind) for kind in DIAGRAM_TYPES})

    def to_dict(self):
        return {"repository": self.repository, "revision": self.revision,
                "diagrams": {kind: self.diagrams[kind].to_dict() for kind in DIAGRAM_TYPES}}
