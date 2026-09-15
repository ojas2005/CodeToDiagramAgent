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
    identifiers = {key: er_id(key.removeprefix("table:")) for key in diagram.nodes}
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

