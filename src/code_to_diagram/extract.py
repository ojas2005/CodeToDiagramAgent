"""Conservative static architecture extraction."""

import ast
import json
import posixpath
import re
from pathlib import PurePosixPath
from typing import Dict, Optional

from .models import Architecture, Evidence
from .source import SourceSnapshot

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
CODE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx"}
DEPENDENCY_IMPORTS = {
    "redis": ("Redis", "cache"),
    "psycopg": ("PostgreSQL", "database"),
    "psycopg2": ("PostgreSQL", "database"),
    "asyncpg": ("PostgreSQL", "database"),
    "sqlalchemy": ("Database", "database"),
    "openai": ("OpenAI API", "external API"),
    "boto3": ("AWS", "external service"),
    "stripe": ("Stripe API", "external API"),
}


def evidence(path: str, line: int, detail: str = "") -> Evidence:
    return Evidence(path, line, detail)


def module_index(files: Dict[str, str]) -> Dict[str, str]:
    found = {}
    for path in files:
        if path.endswith(".py"):
            module = path[:-3].replace("/", ".")
            if module.endswith(".__init__"):
                module = module[:-9]
            found[module] = path
    return found


def relative_python_import(path: str, module: str, level: int) -> str:
    if not level:
        return module
    parent = path[:-3].split("/")[:-1]
    keep = max(0, len(parent) - level + 1)
    return ".".join(parent[:keep] + ([module] if module else []))


def script_target(path: str, imported: str, files: Dict[str, str]) -> Optional[str]:
    if not imported.startswith("."):
        return None
    base = posixpath.normpath(posixpath.join(posixpath.dirname(path), imported))
    for candidate in [base, *(base + suffix for suffix in (".ts", ".tsx", ".js", ".jsx")),
                      *(base + "/index" + suffix for suffix in (".ts", ".tsx", ".js", ".jsx"))]:
        if candidate in files:
            return candidate
    return None

