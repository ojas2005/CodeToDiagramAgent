# Service dependencies

```mermaid
flowchart LR
  n1["auth_stack"]
  n2["Database"]
  n3["PostgreSQL"]
  n4["Redis"]
  n1 -->|uses| n2
  n1 -->|uses| n3
  n1 -->|uses| n4
```

## Evidence

- [backend/.env.example:1](../backend/.env.example#L1)
- [backend/.env.example:2](../backend/.env.example#L2)
- [backend/app/models.py:1](../backend/app/models.py#L1)
