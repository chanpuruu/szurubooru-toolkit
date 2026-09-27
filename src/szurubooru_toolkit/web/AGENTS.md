# Web Scaffold Guidance

Read [root guidance](../../../AGENTS.md) and [security boundaries](../../../docs/agents/SECURITY.md) before API changes.

The application factory in [app.py](app.py) serves only a minimal read-only status API, health/readiness, built assets, and explicit SPA routes. It must not initialize toolkit config or clients, execute commands, discover home credentials, or make outbound requests. No auth, database, profiles, dispatcher, uploads, or job routes exist yet. Readiness describes the scaffold bundle only, not future operational readiness.

FastAPI/uvicorn are optional `web` dependencies. Core modules must not depend on this package. Run from the root with `uv sync --extra web --python 3.11` then `uv run --no-sync pytest -q tests/test_web.py`. Apply Black/isort/flake8 to this directory and its tests.

The standalone launcher defaults to loopback. Production assets are selected by `TOOLKIT_WEB_STATIC_DIR` or an adjacent ignored `static` directory. Static asset confinement uses Starlette's default no-symlink-escape policy. Only `/` and `/system` receive SPA HTML. API/docs/missing assets must remain errors; never mount the repository root as static content.

OpenAPI is exported by [schema.py](schema.py) without a network listener. After schema changes, regenerate the frontend types with `npm run api:generate` in the frontend directory and run its drift check.

Keep [the backlog](../../../docs/decisions/backlog.md) authoritative about unfinished architecture. Add auth and durable execution in separately verified slices rather than exposing temporary unauthenticated mutation endpoints.