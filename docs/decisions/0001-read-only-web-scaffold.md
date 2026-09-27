---
status: accepted
date: 2026-09-27
deciders: "Repository maintainer"
tags: [web, frontend, api]
trigger: "Changing the frontend/API boundary, schema generation, or scaffold serving"
---

# 0001. Read-Only Web Scaffold

## Context And Problem Statement

The maintainer selected a Vue SPA and FastAPI in the web plan, then authorized a runnable frontend/API/Docker foundation without login or jobs. Existing process-global toolkit configuration must not become request-local state by accident.

## Decision Drivers

Preserve CLI and cron behavior, establish a typed same-origin boundary, enable portable local verification, and distinguish scaffolding from operational readiness.

## Considered Options

- Vue 3/TypeScript/Vite with optional FastAPI: selected stack, typed contracts, independently testable UI.
- Server-rendered UI or extending the legacy extension bridge: rejected for the planned interactive workflows and weak ownership boundary.
- Full job/auth implementation during scaffolding: rejected as outside this bounded task.

## Decision Outcome

Use an npm-managed Vue shell with Router, PrimeVue, Lucide, and TanStack Vue Query. Defer Pinia until there is client-owned state. Export OpenAPI offline from the optional FastAPI app factory and generate checked-in TypeScript with a drift check.

The factory exposes minimal status, liveness and bundle-readiness endpoints. It never initializes toolkit config/clients or exposes mutations. Serve built assets and only declared SPA paths on the same origin; unknown API/asset paths remain errors. The launcher defaults to loopback. A separate Docker scaffold definition leaves the cron image untouched; this record does not accept the future operational Unraid runtime.

Auth, profiles, persistence, uploads and jobs remain in the backlog. Extension retirement was subsequently brought forward during structural cleanup; see [the updated plan](../plans/web-ui.md). Public docs endpoints are disabled, not a substitute for future authentication.

## Validation

[Backend tests](../../tests/test_web.py) guard config/client isolation, readiness, routes, mutation denial, CORS and static confinement. [API generation](../../frontend/scripts/generate-api.mjs) checks schema drift. Frontend component tests, type/build checks, and [browser tests](../../frontend/e2e/system.spec.ts) cover real same-origin serving, desktop/mobile, keyboard and error recovery.

Locally these checks passed using Python 3.11 and installed Chrome. Windows skipped the symlink test for missing privileges; managed Chromium download timed out. Docker build and Linux symlink behavior require the configured CI or a Docker-enabled host; Docker was unavailable locally. No remote CI was triggered.

## More Information

See [setup and verification](../WEB_UI.md), [the plan](../plans/web-ui.md), and [remaining decisions](backlog.md).
