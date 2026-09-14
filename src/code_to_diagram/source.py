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


def read_worktree(root: Path, max_files: int = 400, max_bytes: int = 256000) -> SourceSnapshot:
    root = Path(root).resolve()
    if not root.is_dir() or max_files < 1 or max_bytes < 1:
        raise DiagramError("Repository and scan limits must be valid")
    files = {}
    skipped = 0
    for folder, directories, names in os.walk(root, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in SKIP_DIRS
                                and not (Path(folder) / name).is_symlink())
        for name in sorted(names):
            path = Path(folder) / name
            relative = path.relative_to(root).as_posix()
            if not eligible(relative) or path.is_symlink() or not path.is_file():
                continue
            try:
                if path.stat().st_size > max_bytes:
                    skipped += 1
                    continue
                content = decode(path.read_bytes())
            except OSError:
                skipped += 1
                continue
            if not content:
                continue
            if len(files) >= max_files:
                skipped += 1
                continue
            files[relative] = content
    if not files:
        raise DiagramError("No supported source files found")
    return SourceSnapshot(root.name, "worktree", files, skipped)

