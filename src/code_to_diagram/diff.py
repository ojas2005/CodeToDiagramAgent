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


def render_change_report(base: Architecture, head: Architecture,
                         changes: Dict[str, DiagramChange]) -> str:
    lines = ["# Architecture changes", "", "Base: `{}`".format(base.revision),
             "Head: `{}`".format(head.revision), ""]
    for kind in DIAGRAM_TYPES:
        item = changes[kind]
        lines.extend(["## " + kind.title(), ""])
        if not item.changed:
            lines.extend(["No detected structural changes.", ""])
            continue
        for label, values in (("Added nodes", item.added_nodes),
                              ("Removed nodes", item.removed_nodes),
                              ("Changed nodes", item.changed_nodes),
                              ("Added relationships", item.added_edges),
                              ("Removed relationships", item.removed_edges)):
            if values:
                lines.append("### " + label)
                lines.extend("- `" + value + "`" for value in values)
                lines.append("")
    lines.append("Changes reflect detected structure; review the source for behavior changes.")
    return "\n".join(lines) + "\n"


def update_changed_diagrams(head: Architecture, changes: Dict[str, DiagramChange],
                            out_dir: Path, source_root: Path) -> List[str]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = os.path.relpath(Path(source_root).resolve(), out_dir.resolve())
    updated = []
    for kind in DIAGRAM_TYPES:
        if not changes[kind].changed:
            continue
        diagram = head.diagrams[kind]
        (out_dir / (kind + ".mmd")).write_text(render_mermaid(diagram), encoding="utf-8")
        (out_dir / (kind + ".md")).write_text(render_markdown(diagram, prefix), encoding="utf-8")
        updated.append(kind)
    (out_dir / "changes.json").write_text(json.dumps(
        {kind: changes[kind].to_dict() for kind in DIAGRAM_TYPES}, indent=2) + "\n", encoding="utf-8")
    return updated
