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

