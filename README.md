# Code-to-Diagram Agent

Generate source-linked architecture diagrams from an existing repository.

## Install and generate

Requires Python 3.9+ and Git for revision comparison. Runtime scanning and rendering use only the Python standard library; there is no API key or external model call.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
code-to-diagram generate --repo /path/to/repository
```

By default this writes `docs/diagrams/` in the target repository: five `.mmd` Mermaid files, five Markdown pages with line-linked source evidence, and `architecture.json`. Use `--out /path/to/output` to choose another directory. Use `--revision HEAD` to analyze a committed snapshot instead of the worktree.

Try the included [auth stack fixture](examples/auth_stack/README.md):

```bash
code-to-diagram generate --repo examples/auth_stack --out examples/auth_stack/diagrams
```

The checked [API interaction diagram](examples/auth_stack/diagrams/api.md) and [authentication sequence](examples/auth_stack/diagrams/auth.md) show the output. Other diagrams cover components, database entities, and service dependencies.

## Compare revisions

```bash
code-to-diagram diff \
  --repo /path/to/repository \
  --base HEAD~1 \
  --head HEAD \
  --out /path/to/repository/docs/diagrams
```

`diff` reads both commits without checking either one out. It writes `CHANGES.md` and `changes.json`, and refreshes only diagram types whose detected nodes or relationships changed. This can be run in CI after each push to keep diagram artifacts current. It does not commit generated files for you.

## Detection and limits

The scanner recognizes local Python and JavaScript/TypeScript imports, decorated Python and Express HTTP routes, literal frontend requests, SQLAlchemy/Prisma/SQL tables, and common database, cache, and service imports or URLs. The authentication sequence uses detected endpoint and helper call sites. Every relationship carries a source file and line number in JSON and Markdown.

This is static inference. Dynamic routing, runtime configuration, generated code, and indirect calls can be missed. The sequence is a map of visible call sites, not a guarantee of runtime branch order. Unsupported or empty diagrams say what evidence was missing. Review source before relying on a generated diagram for changes.

The scanner skips symlinks, common secret files, dependencies, build directories, and binary files. It defaults to 400 supported files and 256 KB per file; `--max-files` and `--max-bytes` adjust those bounds. JSON and configuration files may contain sensitive values, so review output before sharing it. The tool does not send repository content to a network service.

## Development

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

MIT licensed; see [LICENSE](LICENSE).
