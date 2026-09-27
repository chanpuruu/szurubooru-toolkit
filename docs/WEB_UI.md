# Web Scaffold

The repository now contains a runnable Vue 3 + TypeScript + Vite shell and an optional FastAPI package. This is **read-only development scaffolding**, not the complete web application in [the plan](plans/web-ui.md). It does not run toolkit commands, load toolkit config, contact Szurubooru, or offer login, profiles, uploads, jobs, SQLite, or scheduling. Ordinary CLI and cron behavior remain supported.

**Unreleased breaking change:** Chrome/Firefox extensions and their `szuru-toolkit webserver` bridge were retired during structural cleanup, before their replacement. Use the normal CLI `import-from-url` command for URL imports. The scaffold deliberately rejects `/import-from-url` and `/import-from-all-tabs`; it cannot accept browser imports yet.

## Toolchain

Use Python 3.11+, uv, and Node 22.12+ in the Node 22 LTS line. npm owns [the frontend lockfile](../frontend/package-lock.json); uv owns [the Python lockfile](../uv.lock). TypeScript 5.9 is selected for compatibility with the OpenAPI generator. No global Node or Python installation is performed by repository scripts.

From the repository root:

```sh
uv sync --extra web --python 3.11
cd frontend
npm ci
npm run api:check
npm test
npm run lint
npm run build
```

API types are generated offline from FastAPI's schema. Run `npm run api:generate` in the frontend directory after changing the API and commit the generated result with its source. No running server or credentials are needed. The generator uses the already-synced environment (`--no-sync`).

## Development

From the root, run `uv run --no-sync python -m szurubooru_toolkit.web`. In a second terminal, run `npm run dev` from the frontend directory. Open `http://127.0.0.1:5173`. Vite proxies only API and health paths to port 8080; no permissive CORS configuration is needed.

To serve the production bundle through FastAPI, set `TOOLKIT_WEB_STATIC_DIR=frontend/dist` in the launching environment after building, then run the same Python command from the root. PowerShell uses `$env:TOOLKIT_WEB_STATIC_DIR = 'frontend/dist'`; POSIX shells use `export TOOLKIT_WEB_STATIC_DIR=frontend/dist`. Open `http://127.0.0.1:8080/system`.

The launcher defaults to loopback and accepts `--host` and `--port`. `/healthz` reports API liveness; `/readyz` returns 503 without a built frontend and otherwise indicates scaffold readiness only. `/api/v1/system/status` exposes minimal non-secret status. Public docs/OpenAPI endpoints are disabled. Unknown API and asset paths do not receive SPA HTML.

## Docker Foundation

From the root:

```sh
docker compose -f compose.web.yml up --build
```

Open `http://127.0.0.1:8080`. [Dockerfile.web](../Dockerfile.web) builds assets in Node and runs Python without Node/npm in the runtime stage. [compose.web.yml](../compose.web.yml) uses a read-only container, numeric non-root user, loopback port publication, and no media/config mounts. It is separate from the existing cron deployment. The image has no optional tagging/GPU extras or Unraid PUID/PGID initialization yet because it executes no jobs and writes no app data.

Do not deploy this as the full LAN administration service. Authentication, `/data` persistence, Unraid templates, profiles, worker lifecycle, media access, and image-variant integration belong to later verified slices. Never mount real credentials into this scaffold.

## Verification

From the root, run `uv run --no-sync pytest -q tests/test_web.py` and Black/isort/flake8 on the web directory and test file. The web tests skip when the optional FastAPI dependency is absent; web CI installs the extra and runs them explicitly. Windows may skip the symlink test without symlink privileges; Linux CI must run it.

From the frontend directory, run `npx playwright install chromium` once, then `npm run test:e2e` after a build. It starts FastAPI itself on port 8081 against the production bundle, tests desktop/mobile, keyboard navigation and error recovery, and stores screenshots in ignored test results. It does not reuse an existing listener or connect to real Szurubooru. If the managed browser download is unavailable, set `PLAYWRIGHT_CHANNEL=chrome` or `msedge` to use that locally installed browser; the default remains managed Chromium.

PrimeVue 4.3.9 and PrimeUI themes 1.2.3 are pinned to verified MIT-licensed releases. Check licensing before upgrading these dependencies.

[Web scaffold CI](../.github/workflows/web-scaffold.yml) configures these checks plus a Docker build for relevant pull requests. Local verification is not proof that remote CI or Unraid deployment ran.