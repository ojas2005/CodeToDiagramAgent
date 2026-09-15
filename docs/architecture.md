# Architecture

```text
worktree or Git revision
        |
        v
bounded SourceSnapshot
        |
        v
static extractors -> Architecture (five diagrams, source evidence)
        |                         |
        v                         v
Mermaid + Markdown + JSON    revision comparison
                                 |
                                 v
                        change report + selective updates
```

`source.py` skips common dependency/build directories, symlinks, secrets, oversized files, and binary files. Git snapshots are read with `git ls-tree` and `git show` after the revision resolves to a commit. The working tree is not modified during comparison.

`extract.py` creates module, endpoint, table, and service nodes from conservative source patterns. It joins local imports and literal frontend requests to discovered targets. Authentication steps are inferred from login endpoints and helper calls. Every edge points to at least one selected line. A diagram with no evidence remains empty and carries a note.

`models.py` supplies stable IDs, deduplication, and deterministic JSON. `render.py` maps those IDs to Mermaid identifiers and lists source references beside each diagram. `diff.py` compares structural node properties and edge keys between revisions, then rewrites only changed diagram types. Evidence-only line changes do not count as a structural change; regenerate all diagrams when exact citation positions matter.

The extractors do not evaluate source code, install a scanned project's dependencies, call project services, or infer runtime behavior from tests.
