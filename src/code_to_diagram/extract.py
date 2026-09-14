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


def add_module(architecture: Architecture, path: str):
    diagram = architecture.diagrams["components"]
    suffix = PurePosixPath(path).suffix
    kind = "frontend" if suffix in {".jsx", ".tsx"} else "module"
    diagram.add_node("file:" + path, path, kind, evidence(path, 1))


def add_dependency(architecture: Architecture, name: str, kind: str,
                   path: str, line: int):
    diagram = architecture.diagrams["dependencies"]
    diagram.add_node("app", architecture.repository, "application")
    target = "service:" + name.lower().replace(" ", "-")
    diagram.add_node(target, name, kind, evidence(path, line))
    diagram.add_edge("app", target, "uses", evidence=evidence(path, line))


def add_api_route(architecture: Architecture, path: str, line: int,
                  method: str, route: str, handler: str):
    diagram = architecture.diagrams["api"]
    route_id = "route:{}:{}".format(method.upper(), route)
    handler_id = "handler:{}:{}".format(path, handler)
    ref = evidence(path, line)
    diagram.add_node(route_id, "{} {}".format(method.upper(), route), "endpoint", ref)
    diagram.add_node(handler_id, "{} in {}".format(handler, path), "handler", ref)
    diagram.add_edge(route_id, handler_id, "handled by", evidence=ref)

