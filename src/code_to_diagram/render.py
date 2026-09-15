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

