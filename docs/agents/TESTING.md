# Testing And Tooling

Read before changing test infrastructure, fixtures, migrations, or running integration/browser tests. All commands below run from the repository root.

## Existing Commands

| Purpose | Command |
| --- | --- |
| Install development dependencies | `uv sync` |
| Selected existing test | `uv run pytest -q tests/test_config.py` |
| Full Python suite | `uv run pytest -q` |
| Format check, selected file | `uv run black --check src/szurubooru_toolkit/config.py` |
| Import check, selected file | `uv run isort --check-only src/szurubooru_toolkit/config.py` |
| Lint, selected file | `uv run flake8 src/szurubooru_toolkit/config.py` |
| Build distribution | `uv build` |
| Existing pre-commit checks | `uv run pre-commit run --all-files` |
| Installed guidance validation | `uv run --no-project --with-requirements coding_agent_helpers/checks/requirements.txt python coding_agent_helpers/checks/validate_docs.py AGENTS.md docs/agents docs/decisions .claude/skills/code-review WEB_UI_PLAN.md` |
| Guidance hook only, including untracked guidance | `uv run --no-project --with pre-commit pre-commit run agent-guidance --files AGENTS.md` |
| Validator regression tests | `uv run --no-project --with pytest --with-requirements coding_agent_helpers/checks/requirements.txt python -m pytest -q coding_agent_helpers/checks/test_validate_docs.py` |

Replace the selected Python path with the touched file/test. No frontend package scripts, static type checker, migrations, or API code generator exist yet. Document and test those commands with scaffolding rather than guessing them.

## Isolation

Use existing pytest fixtures and httpx mocks. Control clocks, randomness, network, and concurrency. Assert observable behavior, including malformed input, errors, and rejection paths; avoid sleeps and test-order dependencies.

Before a CLI smoke test read [the existing skill](../../.claude/skills/run-szurubooru-toolkit/SKILL.md). Run `uv run python .claude/skills/run-szurubooru-toolkit/driver.py smoke` against its isolated fake server/config. Do not run a bare mutating command: config discovery can fall back to the owner's home configuration. Tests must never depend on real credentials or hosted accounts.

WD CPU and CUDA extras conflict. Select only the needed extra; never use `--all-extras`. Model downloads and GPU/ffmpeg checks require explicit environment preparation. A fake API smoke test does not validate real booru services or GPU inference.

## Future Gates

When implementing the web plan, cover every command's API mapping, structured result/error semantics, process-tree cancellation, queued-state recovery, no automatic replay, profile snapshots, secret redaction, upload/path confinement, authorization, CSRF, and stale confirmations. Recheck or bind the execution target itself; a preflight followed by a fresh unbounded query is not an atomic safety guarantee.

Add component and Playwright checks with the frontend scripts. Exercise production-style same-origin routing, live-event reconnect, responsive layouts, keyboard operation, and loading/error/empty/denied states. Test migrations and backup/restore against disposable SQLite data.

## Enforcement Status

The local `agent-guidance` pre-commit hook runs the retained kit validator in strict installed-guidance mode. It checks links, parsed YAML frontmatter, and unresolved markers; it does not prove architectural correctness or platform activation. The kit is deliberately excluded from this strict installed scan.

Hook configuration is versioned, but installing a Git hook in a developer checkout is separate (`uv run pre-commit install`). Existing CI is release-only; this installation does not add remote CI enforcement. Do not trigger release workflows to test docs.

Validate narrow to broad, inspect the final diff, and report skipped checks and unrelated failures. Verify instruction/skill discovery in a clean agent session when possible; otherwise report activation unverified.