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

