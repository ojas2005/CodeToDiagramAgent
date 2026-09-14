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

