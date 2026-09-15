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

