"""Detect architecture changes between Git revisions."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .models import Architecture, DIAGRAM_TYPES
from .render import render_markdown, render_mermaid


@dataclass
class DiagramChange:
    kind: str
    added_nodes: List[str]
    removed_nodes: List[str]
    changed_nodes: List[str]
    added_edges: List[str]
    removed_edges: List[str]

    @property
    def changed(self) -> bool:
        return any((self.added_nodes, self.removed_nodes, self.changed_nodes,
                    self.added_edges, self.removed_edges))

    def to_dict(self):
        return {"kind": self.kind, "changed": self.changed,
                "added_nodes": self.added_nodes, "removed_nodes": self.removed_nodes,
                "changed_nodes": self.changed_nodes, "added_edges": self.added_edges,
                "removed_edges": self.removed_edges}


def edge_label(edge) -> str:
    return "{} -> {} ({})".format(edge.source, edge.target, edge.label or edge.kind)


def compare(base: Architecture, head: Architecture) -> Dict[str, DiagramChange]:
    changes = {}
    for kind in DIAGRAM_TYPES:
        old = base.diagrams[kind]
        new = head.diagrams[kind]
        old_nodes, new_nodes = set(old.nodes), set(new.nodes)
        old_edges, new_edges = set(old.edges), set(new.edges)
        changed_nodes = [key for key in sorted(old_nodes & new_nodes)
                         if (old.nodes[key].label, old.nodes[key].kind, sorted(old.nodes[key].fields)) !=
                            (new.nodes[key].label, new.nodes[key].kind, sorted(new.nodes[key].fields))]
        changes[kind] = DiagramChange(
            kind, sorted(new_nodes - old_nodes), sorted(old_nodes - new_nodes), changed_nodes,
            [edge_label(new.edges[key]) for key in sorted(new_edges - old_edges)],
            [edge_label(old.edges[key]) for key in sorted(old_edges - new_edges)])
    return changes

