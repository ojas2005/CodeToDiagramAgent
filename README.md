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
