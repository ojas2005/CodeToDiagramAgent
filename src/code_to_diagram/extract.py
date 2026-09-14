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


def python_imports(tree, path: str, architecture: Architecture, modules: Dict[str, str]):
    components = architecture.diagrams["components"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [relative_python_import(path, node.module or "", node.level)]
        else:
            continue
        for name in names:
            root = name.split(".")[0]
            if root in DEPENDENCY_IMPORTS:
                label, kind = DEPENDENCY_IMPORTS[root]
                add_dependency(architecture, label, kind, path, node.lineno)
            target = modules.get(name)
            if target and target != path:
                components.add_edge("file:" + path, "file:" + target, "imports",
                                    evidence=evidence(path, node.lineno))


def python_routes(tree, path: str, architecture: Architecture):
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            method = decorator.func.attr.lower()
            if method not in HTTP_METHODS or not decorator.args:
                continue
            route = decorator.args[0]
            if isinstance(route, ast.Constant) and isinstance(route.value, str):
                add_api_route(architecture, path, decorator.lineno, method,
                              route.value, node.name)


def python_tables(tree, path: str, architecture: Architecture):
    er = architecture.diagrams["er"]
    for klass in [node for node in tree.body if isinstance(node, ast.ClassDef)]:
        table = None
        for statement in klass.body:
            if isinstance(statement, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id == "__tablename__"
                    for target in statement.targets):
                if isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
                    table = statement.value.value
        if not table:
            continue
        table_id = "table:" + table
        fields = []
        relationships = []
        for statement in klass.body:
            if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                value = statement.value
                if not value or not isinstance(value, ast.Call):
                    continue
                call_name = getattr(value.func, "id", getattr(value.func, "attr", ""))
                if call_name not in {"Column", "mapped_column", "relationship"}:
                    continue
                for target in targets:
                    if isinstance(target, ast.Name):
                        fields.append(target.id)
                for sub in ast.walk(value):
                    if isinstance(sub, ast.Call) and getattr(sub.func, "id", "") == "ForeignKey":
                        if sub.args and isinstance(sub.args[0], ast.Constant) and isinstance(sub.args[0].value, str):
                            relationships.append((sub.args[0].value.split(".")[0], statement.lineno))
        er.add_node(table_id, table, "table", evidence(path, klass.lineno), fields)
        for target, line in relationships:
            target_id = "table:" + target
            er.add_node(target_id, target, "table", evidence(path, line))
            er.add_edge(table_id, target_id, "foreign key", evidence=evidence(path, line))


def extract_python(path: str, content: str, architecture: Architecture,
                   modules: Dict[str, str]):
    try:
        tree = ast.parse(content, filename=path)
    except SyntaxError:
        architecture.diagrams["components"].notes.append("Could not parse " + path)
        return
    python_imports(tree, path, architecture, modules)
    python_routes(tree, path, architecture)
    python_tables(tree, path, architecture)

