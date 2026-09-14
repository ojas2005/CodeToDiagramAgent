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

