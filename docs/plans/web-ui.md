# Web Interface Plan: Docker Web Control Plane

Build a workflow-oriented Vue 3 SPA and FastAPI backend for the complete szurubooru-toolkit command set. The reference deployment is one Unraid-friendly Docker container: FastAPI serves the compiled SPA, SQLite persists authentication, profiles, jobs, and history, an embedded dispatcher runs one isolated CLI subprocess at a time, and SSE delivers logs and progress. Existing CLI behavior remains supported; Redis, distributed workers, schedules, and multi-user roles are explicitly deferred.

## Implementation Status

As of 2026-09-27, no numbered phase is complete. The separately authorized read-only scaffold implements portions of steps 7, 29, and 38, plus a separate Docker foundation. Phase 1 command contracts, authentication, persistence, and all operational workflows remain unimplemented.

Structural cleanup retired the extensions and legacy bridge early, as explicitly approved in [ADR-0002](../decisions/0002-retire-legacy-browser-bridge.md). Step 28's removal portion is complete; the new CLI web launcher and replacement import workflows are still pending. Examples now live under `examples/`, the cron helper under `docker/`, and this plan under `docs/plans/`. Existing runtime mount paths are unchanged.

See [the scaffold guide](../WEB_UI.md) for currently runnable commands. The phases below describe the remaining target, not an authorization to implement everything at once.

The first Python cleanup extracted the existing thread-pool helper into `concurrency.py`, retaining the old `utils.run_concurrently` import and behavior. Explicit runtime ownership and further utility decomposition remain incremental follow-up work; this extraction does not implement Phase 1 execution events or outcome normalization.

## Recommended Architecture

- **Frontend:** Vue 3, TypeScript, Vite, Vue Router, TanStack Vue Query, Pinia for session/UI preferences only, PrimeVue accessible primitives with a restrained operator-console theme, Lucide Vue icons, and OpenAPI-generated API types.
- **Backend:** FastAPI + Pydantic, SQLAlchemy 2/Alembic over SQLite, Uvicorn with exactly one process, Argon2 password hashing, encrypted profile secrets, multipart streaming uploads, and same-origin REST/SSE APIs.
- **Execution:** A durable SQLite queue and one async dispatcher inside FastAPI. Every toolkit operation runs via `sys.executable -m szurubooru_toolkit.scripts.szuru_toolkit` as an argv list without a shell. Top-level jobs are serialized because individual commands already create thread pools/processes and can contend for GPU, files, and rate limits.
- **Deployment:** One image/container in `TOOLKIT_MODE=web`; compiled SPA and all web dependencies are included in every existing image variant. `/data` holds SQLite, keys, logs, and staged uploads on local Unraid appdata storage; separate allowlisted media mounts expose server-side files. Existing cron mode remains available but is not run inside the web-mode container.
- **Streaming:** REST for commands/state and SSE for one-way job state, structured progress, and log tailing. WebSockets are unnecessary for this interaction model.

## Phase 1: Stabilize Command Contracts

1. Add an explicit `--config-file` global CLI option and update `Config`/`setup_config` so a job can select a generated profile snapshot without changing cwd or exposing credentials in process arguments. Preserve the existing config search order when the option is absent.
2. Introduce a shared, explicit command registry for the 13 operational commands: `auto-tagger`, `preview-tags`, `find-duplicates`, `create-relations`, `fix-relations`, `fix-sankaku-sources`, `create-tags`, `delete-posts`, `import-from-booru`, `import-from-url`, `reset-posts`, `tag-posts`, and `upload-media`. Record typed inputs, defaults, config sections, required extras, filesystem needs, risk level, dry-run support, result shape, and an argv builder. Do not accept arbitrary command names, flags, or shell text.
3. Keep Click as the canonical CLI execution path, but add parity tests between Click options, config defaults, and the web registry. Resolve current metadata defects while doing so, including the duplicated `--limit` declaration on `import-from-booru`.
4. Add an opt-in JSONL execution-event channel activated only by a job environment variable. Make it a no-op for normal CLI runs. Define versioned events for job start, total/progress, item result/error, summary, and result artifacts; make writes thread-safe.
5. Update `run_concurrently` and each sequential command to emit accurate totals, progress, per-item outcomes, and final summaries. Normalize fatal exception/exit behavior so subprocess exit codes are reliable despite current `@logger.catch` and per-item exception swallowing; preserve human-readable CLI logs.
6. Add command-specific structured results: tag diffs/safety for auto-tagger dry runs, score rows for preview-tags, duplicate clusters, relation/tag changes, source rewrites, mutation counts, and import/upload post IDs with duplicate/skipped/error reasons. Store large item sets incrementally rather than as one response.

## Phase 2: Backend Foundation And Persistence

7. Create `src/szurubooru_toolkit/web/` with an application factory, settings loader, protected OpenAPI setup, versioned routers, exception mapping, and SPA static/fallback serving. Keep `/healthz` minimal and unauthenticated; make `/readyz` verify the database, dispatcher, writable data paths, and static assets.
8. Add Alembic-managed SQLite tables for schema versioning, the single admin, sessions, named profiles, jobs, job items/results, upload sets/files, destructive-operation preflights, and audit events. Enable foreign keys, busy timeout, and WAL; enforce one dispatcher claim transaction at a time.
9. Recover durable state on startup: retain queued jobs, mark formerly running/cancelling jobs `interrupted`, never replay mutating work automatically, and expose an explicit rerun action that creates a new job.
10. Implement first-run setup using a one-time bootstrap token printed to container logs or supplied by environment. Store only an Argon2 password hash; use opaque server-side sessions with HttpOnly/SameSite cookies, configurable Secure cookies, idle/absolute expiry, login throttling, and CSRF tokens on every state-changing API request.
11. Generate and persist a 0600 master key under `/data` unless one is supplied as a Docker secret/environment file. Encrypt profile credentials/config snapshots at rest, redact secrets from all responses/audit records/logs, and document that encryption does not protect against a compromised Docker host.
12. Implement named profile CRUD, duplicate, connection test, import from existing `config.toml`, and redacted export. Validate every current config section with Pydantic, merge profile defaults with per-job overrides, snapshot the effective config when queuing, and materialize a private per-job TOML file only for subprocess execution.

## Phase 3: Queue, Execution, And Live Status

13. Implement a repository-backed FIFO dispatcher with one active top-level job. Keep queue and executor interfaces independent of FastAPI so a separate worker/Redis implementation can replace them later without changing API contracts.
14. Launch each job in a new Linux process group with unbuffered, non-colorized output and `hide_progress=true`; stream stdout/stderr to a per-job log while consuming JSONL events into job progress/item rows. Delete private generated config files after terminal completion.
15. Implement cancellation as SIGINT to the process group, followed by configurable SIGTERM and SIGKILL grace periods. Record `cancelled`, `failed`, `succeeded`, `succeeded_with_errors`, and `interrupted` distinctly; do not retry automatically.
16. Add job APIs to create/list/filter/get/cancel/rerun jobs, paginate item results, download sanitized logs, and stream state/progress/log events over reconnectable SSE. Bound history/log retention and provide manual cleanup without touching mounted source media.
17. Add capability detection for installed extras, ffmpeg, ONNX execution providers, and writable mount roots. Reject unsupported jobs server-side and expose reasons so the SPA can disable only the affected controls.
18. Keep cron and ad-hoc CLI compatibility, but prevent accidental competition by documenting web mode as the sole orchestrator for that container. If cron is run in another container, require an explicitly shared lock and warn that cross-process SauceNAO limits remain uncoordinated.

## Phase 4: Files And Destructive-Operation Safety

19. Add named, environment-configured filesystem roots. Return opaque root/path IDs to the browser, resolve all paths server-side with `Path.resolve()`/`relative_to()`, reject symlink escapes and special files, and distinguish read-only mounts from roots where cleanup is allowed.
20. Implement streaming browser upload sets with sanitized relative paths, duplicate-name handling, configurable per-file/total limits, checksums, sidecar pairing, cancellation, and quotas. Stage them under `/data/uploads`; retain failed uploads briefly for rerun and remove successful/expired staging data independently of `upload-media --cleanup`.
21. Support mounted-folder selection for large batches and browser files/directories for convenience. Handle tag files, URL-list files, preview media, and gallery-dl cookie files as typed assets; keep cookie assets private and never serve them back as plain text.
22. Add profile-scoped read-only preflight APIs for query validation, target count/sample, and connection checks using short-lived clients rather than global toolkit clients. Proxy thumbnails only through an authenticated, bounded endpoint if direct Szurubooru URLs cannot render.
23. Require a short-lived preflight token bound to profile, command, query, options, and target hash for destructive operations. Use typed confirmation for `delete-posts` and `reset-posts`; require normal confirmation for overwrite/relation/source mutations. Revalidate immediately before launch and block if the target set changed.

## Phase 5: Complete Command Workflows

24. Implement import/upload workflows in parallel after phases 1-4: URL import with multiple URLs/list asset/range/private cookie asset; booru import with source and limit; media upload from staging or mounted root with sidecars, transforms, safety, duplicate behavior, cleanup, and optional auto-tagging.
25. Implement tagging workflows in parallel: auto-tagger with dry-run-first flow and WD/SauceNAO/MD5 controls; preview-tags with score tables and threshold markers; tag-posts with query preview, add/remove tags, source, mode, implications, and workers.
26. Implement tag/relation workflows in parallel: create-tags as explicit single/file/query modes; create-relations and fix-relations with target previews, thresholds, mutation summaries, and confirmations.
27. Implement maintenance workflows in parallel: find-duplicates with cluster result tables and optional relation action; fix-sankaku-sources with dry-run comparison; reset-posts and delete-posts with exact risk treatment and per-item outcomes.
28. Extension directories, their documentation, the unauthenticated endpoints, and the old `webserver` command were removed during structural cleanup. Add a new `web` CLI launcher when its runtime contract is implemented; do not register it as a job or restore the old bridge. Replacement import workflows remain required.

## Phase 6: Vue SPA

29. Scaffold `frontend/` with Vue 3 `<script setup>`, TypeScript strict mode, Vite, Router, TanStack Vue Query, Pinia, PrimeVue, Lucide Vue, generated OpenAPI types, Vitest/Vue Testing Library/MSW, and Playwright. Fail CI when generated API types drift.
30. Build a direct operator dashboard rather than a landing page: persistent navigation; active profile and health/capability status; current queue; recent jobs; and quick access to imports, uploads, tagging, organization, maintenance, profiles, jobs, and system status.
31. Create explicit typed forms for every workflow instead of a generic dynamic command form. Reuse field primitives for Szurubooru queries, tag lists, worker counts, thresholds, media transforms, safety, server paths, uploads, dry-run controls, and risk confirmations; backend validation remains authoritative.
32. Build a job detail view with stable status/progress dimensions, elapsed time, cancel/rerun actions, searchable live log tail, downloadable logs, summary metrics, and command-specific paginated result tables. Reconnect SSE using event IDs and fall back to status polling after network interruption.
33. Use a restrained, desktop-first operational layout with compact tables/forms, semantic warning/danger states, no nested decorative cards, keyboard-complete interactions, focus-managed dialogs, labelled native semantics, WCAG AA contrast, and responsive job monitoring on mobile. Do not expose secrets or arbitrary filesystem paths in the DOM.

## Phase 7: Docker, Unraid, Release, And Documentation

34. Add a Node build stage to `Dockerfile`, copy the compiled SPA into the Python runtime, install the `web` optional dependency for every image variant, and keep the runtime free of Node/npm. Add a CPU+Pixiv `-all` image and a CUDA+Pixiv `-all-cuda` image so every optional toolkit feature has a web-capable Docker choice.
35. Refactor `docker/entrypoint.sh` into explicit `cron`, `web`, and one-shot command modes while preserving existing defaults. In web mode initialize/chown `/data` and allowed writable mounts, drop to PUID/PGID, and exec one Uvicorn process so signals reach the dispatcher and its child process group.
36. Add an Unraid-oriented compose/example configuration: configurable host port (container 8080), `/data` on local cache-backed appdata, one or more named media mounts, optional config import mount, persistent Hugging Face cache, PUID/PGID/TZ, reverse-proxy base URL/cookie security, upload limits, and optional NVIDIA GPU exposure. Do not place SQLite on SMB/NFS; media mounts may be remote.
37. Add container health checks and startup diagnostics without leaking secrets. Preserve the five current image tags, add `-all-cuda`, and update the Docker publishing matrix; build/test the SPA before each image and before any wheel that advertises the web extra.
38. Add PR CI for Python lint/tests, frontend lint/typecheck/unit/build, OpenAPI client drift, Playwright smoke tests, and a slim Docker build. Keep tag-triggered PyPI/Docker publishing, and include built frontend assets in the web-capable wheel only if native `szuru-toolkit web` is advertised.
39. Update README and add dedicated web/Unraid/security documentation covering first-run setup, profiles, mounts, reverse-proxy TLS, image selection, backups, cancellation/restart semantics, retention, config import/export, and migration from the removed extensions. Mark the release as breaking because extension code/endpoints are removed.

## API Surface

- `/api/v1/auth/*`: setup, login, logout, session, CSRF.
- `/api/v1/profiles/*`: CRUD, test, import/export, redacted schema/defaults.
- `/api/v1/system/*`: capabilities and authenticated diagnostics; `/healthz` and `/readyz` remain minimal.
- `/api/v1/files/*` and `/api/v1/uploads/*`: allowlisted browsing and staged upload lifecycle.
- `/api/v1/preflights/*`: query previews and bound confirmation tokens.
- `/api/v1/commands` and `/api/v1/jobs/*`: metadata, enqueue, history, details, result items, cancel, rerun, logs, and SSE.
- Non-API routes serve the Vue assets and history fallback; CORS is disabled by default because the SPA is same-origin.

## Relevant Files

- `src/szurubooru_toolkit/scripts/szuru_toolkit.py`: global config-file option, web launcher, command parity, and current Click definitions.
- `src/szurubooru_toolkit/config.py`: explicit config path and profile-generated TOML compatibility.
- `src/szurubooru_toolkit/utils.py`: concurrent execution summaries/progress and gallery-dl failure propagation.
- `src/szurubooru_toolkit/scripts/*.py`: command-specific structured events/results and reliable fatal exits.
- `src/szurubooru_toolkit/execution_events.py`: new no-op-by-default JSONL protocol.
- `src/szurubooru_toolkit/web/`: new FastAPI app, API, auth, persistence, profiles, files, preflights, dispatcher, executor, and generated static assets.
- `frontend/`: new Vue application and browser tests.
- `pyproject.toml` and `uv.lock`: optional web dependencies and lock updates.
- `Dockerfile`, `docker/entrypoint.sh`, and `docker-compose.yml`: multi-stage build, modes, persistent mounts, port/GPU/health configuration.
- `.github/workflows/`: PR validation and release matrix updates.
- `tests/` and `.claude/skills/run-szurubooru-toolkit/driver.py`: backend, command-contract, and fake-Szurubooru integration coverage.
- Legacy extensions and their HTTP bridge: retired; replacement import workflows remain unimplemented.
- `README.md`, `docs/WEB_UI.md`, and `docs/UNRAID.md`: usage, security, deployment, and migration guidance.

## Verification

1. Run existing CLI tests and the committed fake-server smoke driver; verify every old CLI command still resolves defaults/options and no job-only event output appears in terminal mode.
2. Add registry parity tests for all 13 commands, generated argv tests that prove shell metacharacters remain single arguments, config snapshot/redaction tests, and structured-event/exit-code tests including partial failures.
3. Test database migrations, single-claim FIFO semantics, startup recovery, no automatic replay, process-tree cancellation, log/event reconnect, retention cleanup, and profile deletion with queued snapshot jobs.
4. Test bootstrap/login/logout/session expiry/rate limiting/CSRF, secret encryption and redaction, query/preflight expiry and target-change rejection, path traversal/symlink escape, upload limits, malicious filenames, and unauthorized media/log access.
5. Exercise every command API against mocks/fakes; extend the committed fake Szurubooru driver for tags/uploads/relations as needed. Never target the owner's real configured instance.
6. Run frontend lint, strict typecheck, unit/component tests with MSW, production build, and Playwright workflows for login, profile setup, every command form, upload/mounted selection, destructive confirmation, queueing, SSE reconnect, cancellation, and result tables at desktop and mobile viewports.
7. Build and start the slim web image, verify health/readiness and first-run setup, run a fake-server job end to end, restart during a job and confirm `interrupted`, verify PUID/PGID writes, and confirm secrets are absent from process lists, API payloads, logs, and browser storage.
8. Build/smoke the WD CPU, WD CUDA, Pixiv, all, and all-cuda variants; verify capability reporting and graceful UI disabling when optional modules/GPU providers are absent.
9. Validate on Unraid with `/data` on local appdata/cache, a read-only media share, a cleanup-enabled writable share, large streamed uploads, reverse-proxy HTTPS, backup/restore of `/data`, and NVIDIA exposure where applicable.

## Decisions And Scope Boundaries

- Vue 3 SPA is required; there is no server-rendered UI.
- FastAPI is preferred over Flask because typed Pydantic contracts, OpenAPI generation, async streaming/uploads, and dependency injection fit the SPA/job boundary; Django adds unnecessary ORM/admin/runtime scope.
- SQLite persists app state and the queue; it is not a distributed broker. One embedded dispatcher and one active top-level job are deliberate because scripts already parallelize internally.
- Redis/Celery/RQ and a separate worker become justified only for multiple web replicas/hosts, multiple active queue consumers, independent API/worker availability, or materially higher multi-user throughput.
- All 13 operational commands ship in the first web release. A future `web` CLI command launches the app and is not a selectable job; the legacy `webserver` command is retired.
- Named web profiles are authoritative for web jobs; existing `config.toml` remains authoritative for normal CLI/cron and can be imported/exported.
- Browser uploads and allowlisted mounted folders are included. Arbitrary server paths and arbitrary shell commands are excluded.
- Built-in single-admin authentication is included for trusted-LAN use. Multi-user roles, SSO/trusted-proxy auth, and internet-hardening beyond reverse-proxy TLS guidance are excluded.
- Browser extensions and their unauthenticated endpoints were retired during structural cleanup, before replacement workflows. This is an unreleased breaking change and warrants a breaking/major release when published.
- Web-managed recurring schedules are deferred. The queue's origin metadata and executor boundary should allow a later scheduler to enqueue the same immutable job requests without introducing Redis.
- Jobs are never automatically retried or resumed because many commands mutate remote state and are not transactional/idempotent.