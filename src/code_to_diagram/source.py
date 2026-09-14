"""Bounded source snapshots from a worktree or Git revision."""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .models import DiagramError

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "coverage",
             "vendor", "target", ".next", "__pycache__", ".idea", ".vscode"}
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".prisma", ".sql",
                   ".toml", ".json", ".yaml", ".yml"}
SPECIAL_NAMES = {"Dockerfile", "requirements.txt", "Pipfile", ".env.example"}
SECRET_NAMES = {".env", "secrets.json", "credentials.json", ".npmrc", ".pypirc"}


@dataclass
class SourceSnapshot:
    name: str
    revision: str
    files: Dict[str, str]
    skipped: int = 0


def eligible(path: str) -> bool:
    parts = Path(path).parts
    name = parts[-1] if parts else ""
    if any(part in SKIP_DIRS for part in parts[:-1]):
        return False
    if name in SECRET_NAMES or name.startswith(".env") and name != ".env.example":
        return False
    if Path(name).suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
        return False
    return Path(name).suffix.lower() in SOURCE_SUFFIXES or name in SPECIAL_NAMES


def decode(data: bytes) -> str:
    if b"\0" in data:
        return ""
    return data.decode("utf-8", errors="replace")

