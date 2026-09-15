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

    diff = commands.add_parser("diff", help="Compare two commits and update changed diagrams")
    diff.add_argument("--repo", required=True, type=Path)
    diff.add_argument("--base", required=True, help="Base Git revision")
    diff.add_argument("--head", required=True, help="Head Git revision")
    diff.add_argument("--out", type=Path, help="Output directory (default: repo/docs/diagrams)")
    diff.add_argument("--max-files", type=int, default=400)
    diff.add_argument("--max-bytes", type=int, default=256000)
    return top


def generate(args):
    repo = args.repo.resolve()
    snapshot = (read_revision(repo, args.revision, args.max_files, args.max_bytes)
                if args.revision else read_worktree(repo, args.max_files, args.max_bytes))
    architecture = build_architecture(snapshot)
    out = args.out or repo / "docs" / "diagrams"
    write_diagrams(architecture, out, repo)
    print("Wrote five diagrams to {}".format(out))
    return 0


def diff_revisions(args):
    repo = args.repo.resolve()
    base = build_architecture(read_revision(repo, args.base, args.max_files, args.max_bytes))
    head = build_architecture(read_revision(repo, args.head, args.max_files, args.max_bytes))
    changes = compare(base, head)
    out = args.out or repo / "docs" / "diagrams"
    updated = update_changed_diagrams(head, changes, out, repo)
    (out / "CHANGES.md").write_text(render_change_report(base, head, changes), encoding="utf-8")
    print("Updated {} diagrams in {}".format(len(updated), out))
    return 0


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        return generate(args) if args.command == "generate" else diff_revisions(args)
    except (DiagramError, OSError) as exc:
        print("code-to-diagram: {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
