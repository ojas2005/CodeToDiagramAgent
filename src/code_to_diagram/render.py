"""Mermaid and Markdown output with source references."""

import json
import os
import re
from pathlib import Path
from urllib.parse import quote

from .models import Architecture, Diagram


def safe_label(value: str) -> str:
    return value.replace("\n", " ").replace('"', "'").replace("[", "(").replace("]", ")")[:120]


def mermaid_id(index: int) -> str:
    return "n{}".format(index)


def render_flowchart(diagram: Diagram) -> str:
    lines = ["flowchart LR"]
    identifiers = {key: mermaid_id(index) for index, key in enumerate(sorted(diagram.nodes), 1)}
    for key in sorted(diagram.nodes):
        node = diagram.nodes[key]
        lines.append('  {}["{}"]'.format(identifiers[key], safe_label(node.label)))
    for key in sorted(diagram.edges):
        edge = diagram.edges[key]
        label = ' |{}|'.format(safe_label(edge.label or edge.kind))
        lines.append('  {} -->{} {}'.format(identifiers[edge.source], label,
                                           identifiers[edge.target]))
    if not diagram.nodes:
        lines.append("  %% No source evidence detected")
    return "\n".join(lines) + "\n"


def er_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value)
    return cleaned if cleaned and cleaned[0].isalpha() else "T_" + cleaned


def render_er(diagram: Diagram) -> str:
    lines = ["erDiagram"]
    identifiers = {key: er_id(key[6:] if key.startswith("table:") else key) for key in diagram.nodes}
    for key in sorted(diagram.nodes):
        node = diagram.nodes[key]
        lines.append("  {} {{".format(identifiers[key]))
        for field in sorted(set(node.fields)):
            name, _, type_name = field.partition(":")
            data_type = er_id(type_name.strip() or "unknown")
            lines.append("    {} {}".format(data_type, er_id(name.strip())))
        lines.append("  }")
    for key in sorted(diagram.edges):
        edge = diagram.edges[key]
        lines.append('  {} }}o--|| {} : "{}"'.format(
            identifiers[edge.source], identifiers[edge.target], safe_label(edge.label or edge.kind)))
    if not diagram.nodes:
        lines.append("  %% No table or model evidence detected")
    return "\n".join(lines) + "\n"


def render_sequence(diagram: Diagram) -> str:
    lines = ["sequenceDiagram"]
    identifiers = {key: mermaid_id(index) for index, key in enumerate(diagram.nodes, 1)}
    for key, node in diagram.nodes.items():
        lines.append('  participant {} as {}'.format(identifiers[key], safe_label(node.label)))
    for edge in diagram.edges.values():
        lines.append('  {}->>{}: {}'.format(identifiers[edge.source], identifiers[edge.target],
                                           safe_label(edge.label or edge.kind)))
    if not diagram.nodes:
        lines.append("  %% No authentication sequence evidence detected")
    return "\n".join(lines) + "\n"


def render_mermaid(diagram: Diagram) -> str:
    if diagram.kind == "er":
        return render_er(diagram)
    if diagram.kind == "auth":
        return render_sequence(diagram)
    return render_flowchart(diagram)


def render_markdown(diagram: Diagram, source_prefix: str = ".") -> str:
    title = {"components": "Component diagram", "api": "API interactions",
             "er": "Database ER diagram", "auth": "Authentication sequence",
             "dependencies": "Service dependencies"}[diagram.kind]
    lines = ["# " + title, "", "```mermaid", render_mermaid(diagram).rstrip(), "```", "",
             "## Evidence", ""]
    refs = {item for node in diagram.nodes.values() for item in node.evidence}
    refs.update(item for edge in diagram.edges.values() for item in edge.evidence)
    for ref in sorted(refs):
        relative = Path(source_prefix) / ref.path
        link = quote(relative.as_posix(), safe="/.") + "#L{}".format(ref.line)
        lines.append("- [{}:{}]({}){}".format(ref.path, ref.line, link,
                     " — " + ref.detail if ref.detail else ""))
    if not refs:
        lines.append("- No source references found.")
    if diagram.notes:
        lines.extend(["", "## Limits", ""])
        lines.extend("- " + note for note in diagram.notes)
    return "\n".join(lines) + "\n"


def write_diagrams(architecture: Architecture, out_dir: Path, source_root: Path):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = os.path.relpath(Path(source_root).resolve(), out_dir.resolve())
    for kind, diagram in architecture.diagrams.items():
        (out_dir / (kind + ".mmd")).write_text(render_mermaid(diagram), encoding="utf-8")
        (out_dir / (kind + ".md")).write_text(render_markdown(diagram, prefix), encoding="utf-8")
    (out_dir / "architecture.json").write_text(
        json.dumps(architecture.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
