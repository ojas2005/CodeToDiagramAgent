# Auth stack fixture

A compact repository for exercising the diagram generator. It is source evidence,
not a production-ready application. The frontend calls a FastAPI login route.
The backend reads a user record, creates a session, and declares data models.
Run `code-to-diagram generate --repo examples/auth_stack --out examples/auth_stack/diagrams`
to regenerate its architecture artifacts.
