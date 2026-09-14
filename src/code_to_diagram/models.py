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

