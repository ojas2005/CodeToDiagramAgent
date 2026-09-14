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


SCRIPT_IMPORT = re.compile(r"(?:\bfrom\s*|\brequire\s*\(\s*)['\"]([^'\"]+)['\"]")
SCRIPT_ROUTE = re.compile(r"\b(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)['\"]")
SCRIPT_REQUEST = re.compile(r"\b(?:fetch|axios\.(?:get|post|put|patch|delete))\s*\(\s*['\"]([^'\"]+)['\"]")
SCRIPT_SERVICES = {"redis": ("Redis", "cache"), "pg": ("PostgreSQL", "database"),
                   "@prisma/client": ("Database", "database"),
                   "openai": ("OpenAI API", "external API"),
                   "stripe": ("Stripe API", "external API")}


def line_number(content: str, offset: int) -> int:
    return content.count("\n", 0, offset) + 1


def script_imports(path: str, content: str, architecture: Architecture,
                   files: Dict[str, str]):
    components = architecture.diagrams["components"]
    for match in SCRIPT_IMPORT.finditer(content):
        imported = match.group(1)
        line = line_number(content, match.start())
        target = script_target(path, imported, files)
        if target and target != path:
            components.add_edge("file:" + path, "file:" + target, "imports",
                                evidence=evidence(path, line))
        for key, (label, kind) in SCRIPT_SERVICES.items():
            if imported == key or imported.startswith(key + "/"):
                add_dependency(architecture, label, kind, path, line)


def extract_script(path: str, content: str, architecture: Architecture,
                   files: Dict[str, str], requests: list):
    script_imports(path, content, architecture, files)
    for match in SCRIPT_ROUTE.finditer(content):
        line = line_number(content, match.start())
        add_api_route(architecture, path, line, match.group(1), match.group(2),
                      PurePosixPath(path).stem)
    for match in SCRIPT_REQUEST.finditer(content):
        requests.append((path, line_number(content, match.start()), match.group(1)))


def connect_requests(architecture: Architecture, requests: list):
    api = architecture.diagrams["api"]
    for path, line, url in requests:
        route = url.split("?", 1)[0]
        matches = [id for id, node in api.nodes.items() if node.kind == "endpoint"
                   and id.endswith(":" + route)]
        client = "client:" + path
        api.add_node(client, path, "client", evidence(path, line))
        for target in matches:
            api.add_edge(client, target, "calls", evidence=evidence(path, line))
        if not matches:
            api.notes.append("Unmatched request in {}:{}: {}".format(path, line, url))


def extract_prisma(path: str, content: str, architecture: Architecture):
    er = architecture.diagrams["er"]
    current = None
    for line, raw in enumerate(content.splitlines(), 1):
        opening = re.match(r"\s*model\s+(\w+)\s*\{", raw)
        if opening:
            current = opening.group(1)
            er.add_node("table:" + current, current, "model", evidence(path, line))
            continue
        if current and raw.strip().startswith("}"):
            current = None
            continue
        if not current:
            continue
        field = re.match(r"\s*(\w+)\s+(\w+)(?:\[\])?\??\s*(.*)", raw)
        if not field:
            continue
        name, type_name, rest = field.groups()
        er.add_node("table:" + current, current, "model", evidence(path, line), [name + ": " + type_name])
        if "@relation" in rest or type_name in [node.label for node in er.nodes.values()]:
            if type_name != current and type_name not in {"String", "Int", "DateTime", "Boolean", "Float", "Decimal", "Json", "Bytes"}:
                target = "table:" + type_name
                er.add_node(target, type_name, "model", evidence(path, line))
                er.add_edge("table:" + current, target, "relation", evidence=evidence(path, line))


def extract_sql(path: str, content: str, architecture: Architecture):
    er = architecture.diagrams["er"]
    for match in re.finditer(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`]?([\w.]+)[\"`]?\s*\((.*?)\)\s*;",
                             content, re.IGNORECASE | re.DOTALL):
        table = match.group(1)
        start_line = line_number(content, match.start())
        fields = []
        for raw in match.group(2).splitlines():
            column = re.match(r"\s*[\"`]?([A-Za-z_]\w*)[\"`]?\s+(\w+)", raw)
            if column and column.group(1).upper() not in {"PRIMARY", "FOREIGN", "CONSTRAINT", "UNIQUE", "CHECK"}:
                fields.append(column.group(1) + ": " + column.group(2))
        source = "table:" + table
        er.add_node(source, table, "table", evidence(path, start_line), fields)
        for foreign in re.finditer(r"REFERENCES\s+[\"`]?([\w.]+)", match.group(2), re.IGNORECASE):
            target_name = foreign.group(1)
            target = "table:" + target_name
            ref_line = line_number(content, match.start(2) + foreign.start())
            er.add_node(target, target_name, "table", evidence(path, ref_line))
            er.add_edge(source, target, "foreign key", evidence=evidence(path, ref_line))


def extract_manifest(path: str, content: str, architecture: Architecture):
    lower = content.lower()
    if path.endswith("package.json"):
        try:
            package = json.loads(content)
        except json.JSONDecodeError:
            return
        dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
        for name, (label, kind) in SCRIPT_SERVICES.items():
            if name in dependencies:
                add_dependency(architecture, label, kind, path, 1)
    for marker, label, kind in [
        ("postgresql://", "PostgreSQL", "database"),
        ("postgres://", "PostgreSQL", "database"),
        ("redis://", "Redis", "cache"),
    ]:
        if marker in lower:
            line = next(i for i, value in enumerate(content.splitlines(), 1) if marker in value.lower())
            add_dependency(architecture, label, kind, path, line)


def build_auth_sequence(snapshot: SourceSnapshot, architecture: Architecture):
    auth = architecture.diagrams["auth"]
    api = architecture.diagrams["api"]
    routes = [node for node in api.nodes.values() if node.kind == "endpoint" and
              any(word in node.label.lower() for word in ("login", "auth", "token", "session"))]
    if not routes:
        auth.notes.append("No authentication endpoint was detected")
        return
    route = routes[0]
    ref = route.evidence[0]
    auth.add_node("client", "Client", "actor")
    auth.add_node("api", route.label, "api", ref)
    auth.add_edge("client", "api", "request", route.label, ref)
    text = snapshot.files.get(ref.path, "")
    helper = re.search(r"\b(authenticate|verify_password|check_password)\s*\(", text)
    if helper:
        line = line_number(text, helper.start())
        auth.add_node("auth", "Authentication logic", "service", evidence(ref.path, line))
        auth.add_edge("api", "auth", "call", helper.group(1), evidence(ref.path, line))
        auth.add_edge("auth", "api", "result", "authentication result", evidence(ref.path, line))
    if re.search(r"\b(create_session|create_token|jwt\.encode)\s*\(", text):
        match = re.search(r"\b(create_session|create_token|jwt\.encode)\s*\(", text)
        line = line_number(text, match.start())
        auth.add_node("token", "Token/session helper", "service", evidence(ref.path, line))
        auth.add_edge("api", "token", "call", match.group(1), evidence(ref.path, line))
        auth.add_edge("token", "api", "result", "token/session", evidence(ref.path, line))
    auth.add_edge("api", "client", "response", "HTTP response", ref)
    auth.notes.append("Sequence is inferred from static call sites; branch order and runtime behavior require source review")

