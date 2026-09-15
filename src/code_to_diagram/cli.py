"""Command-line generation and revision comparison."""

import argparse
import sys
from pathlib import Path

from .diff import compare, render_change_report, update_changed_diagrams
from .extract import build_architecture
from .models import DiagramError
from .render import write_diagrams
from .source import read_revision, read_worktree


def parser():
    top = argparse.ArgumentParser(prog="code-to-diagram",
                                  description="Generate source-linked repository architecture diagrams")
    commands = top.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate", help="Generate all five diagrams")
    generate.add_argument("--repo", required=True, type=Path)
    generate.add_argument("--revision", help="Git revision instead of the worktree")
    generate.add_argument("--out", type=Path, help="Output directory (default: repo/docs/diagrams)")
    generate.add_argument("--max-files", type=int, default=400)
    generate.add_argument("--max-bytes", type=int, default=256000)
    return top

