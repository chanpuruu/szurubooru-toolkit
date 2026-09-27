# Agent Guidance

## Scope And Execution

This is a Python 3.11+ CLI package managed with uv, with a read-only Vue/FastAPI [web scaffold](docs/WEB_UI.md). Jobs, auth, profiles, and the other operational features in [WEB_UI_PLAN.md](WEB_UI_PLAN.md) remain unimplemented. Read that plan and the [decision backlog](docs/decisions/backlog.md) before web architecture work. Implement only the authorized slice; the plan is not blanket authorization.

Preserve unrelated and concurrent changes. Start from the nearest controlling code and a falsifiable behavior check; after the first substantive edit, run that check before widening scope. Reuse existing helpers and tests. Do not weaken tests or validation to obtain a pass.

Pause for scope review if a task spans independently testable behaviors, crosses an unresolved public contract, or two bounded approaches fail without new evidence. Do not create branches, commit, push, trigger CI, post remote reviews, publish, deploy, or perform destructive operations without authorization for that exact action. Read [publishing guidance](docs/agents/PUBLISHING.md) before requesting or executing one.

Perform routine work directly. Read [delegation guidance](docs/agents/DELEGATION.md) before delegating; assign independent, bounded work and verify returned evidence.

## Repository Boundaries

- [src/szurubooru_toolkit/](src/szurubooru_toolkit/): Python clients, configuration, utilities, and CLI scripts. Config, clients, logging, and several caches are process-global; do not execute concurrent web jobs in this interpreter.
- [tests/](tests/): pytest tests, generally using fixtures and mocked HTTP clients.
- [frontend/](frontend/): npm-managed Vue shell, generated API types, and browser tests; follow its scoped guidance.
- [src/szurubooru_toolkit/web/](src/szurubooru_toolkit/web/): optional read-only API/SPA serving, independent of toolkit config and clients; follow its scoped guidance.
- [Dockerfile](Dockerfile), [entrypoint.sh](entrypoint.sh), [docker-compose.yml](docker-compose.yml): current cron-based runtime, mounts, optional GPU, and PUID/PGID behavior.
- Browser extensions and the legacy local HTTP bridge still exist. Removal belongs to the authorized web implementation, not tooling setup.
- [coding_agent_helpers/](coding_agent_helpers/): retained source kit, not a second set of active instructions. Installed guidance here is authoritative.

Read [coding standards](docs/agents/CODING_STANDARDS.md) before public API, config, compatibility, dependency, generated-file, or documentation changes. Keep CLI/PyPI behavior intact unless the task explicitly changes it. Use the web commands in [docs/WEB_UI.md](docs/WEB_UI.md); do not invent job, auth, or migration authorities that do not exist yet.

## Safety And Verification

Never run a mutating CLI command against an implicitly discovered config: home config can target a real instance. Read [testing guidance](docs/agents/TESTING.md) and the [run-szurubooru-toolkit skill](.claude/skills/run-szurubooru-toolkit/SKILL.md) before CLI integration runs. Use the fake API with isolated configuration, not the owner's instance.

Read [security guidance](docs/agents/SECURITY.md) before secrets, auth, external requests, subprocesses, uploads, paths, or destructive changes. Szurubooru enforces remote API permissions today; the toolkit has no built-in web login. Never treat the legacy bridge as LAN-safe authentication.

Run commands from the repository root. Start with a selected test such as `uv run pytest -q tests/test_config.py`, then broaden to `uv run pytest -q` for shared behavior. For changed Python files use `uv run black --check`, `uv run isort --check-only`, and `uv run flake8` followed by the specific paths. See [testing guidance](docs/agents/TESTING.md) for docs, build, and integration checks.

Read [design principles](docs/agents/DESIGN_PRINCIPLES.md) before UI/UX work. The target is a workflow-oriented Vue SPA, not server-rendered pages or a terminal wrapper; verify responsive, keyboard, error, and denied states when it exists.

## Reviews And Decisions

For reviews, use the [code-review skill](.claude/skills/code-review/SKILL.md) and [repository review concerns](docs/agents/CODE_REVIEWS.md). Review requests do not authorize fixes or remote posting.

Use [the ADR index](docs/decisions/README.md). Read [ADR-0000](docs/decisions/0000-record-architecture-decisions.md) before recording architecture choices. Merge accepted architecture records with implementation and validation; keep unimplemented choices in the backlog.

Read [ADR-0001](docs/decisions/0001-read-only-web-scaffold.md) before changing frontend/API ownership, schema generation, or scaffold serving.

Report changed behavior, checks run, checks not run, and residual risks concisely. File placement is not proof that an agent platform loaded instructions or invoked a skill.