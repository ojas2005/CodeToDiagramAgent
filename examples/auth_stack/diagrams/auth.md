# Authentication sequence

```mermaid
sequenceDiagram
  participant n1 as Client
  participant n2 as POST /login
  participant n3 as Authentication logic
  participant n4 as Token/session helper
  n1->>n2: POST /login
  n2->>n3: authenticate
  n3->>n2: authentication result
  n2->>n4: create_session
  n4->>n2: token/session
  n2->>n1: HTTP response
```

## Evidence

- [backend/app/routes.py:7](../backend/app/routes.py#L7)
- [backend/app/routes.py:9](../backend/app/routes.py#L9)
- [backend/app/routes.py:12](../backend/app/routes.py#L12)

## Limits

- Sequence is inferred from static call sites; branch order and runtime behavior require source review
