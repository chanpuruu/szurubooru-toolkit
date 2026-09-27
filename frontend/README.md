# Toolkit Web Frontend

Read-only Vue 3/TypeScript/Vite system view. See [the setup guide](../docs/WEB_UI.md) for backend, local development, Docker, and verification instructions, and [scoped guidance](AGENTS.md) before editing.

With Node 22.12+ (22 LTS), run from this directory:

```sh
npm ci
npm run lint
npm test
npm run build
```

Start the backend from the repository root and use `npm run dev` here for hot reload. `npm run api:generate` and `npm run api:check` require uv and the synced optional Python `web` extra. `npm run test:e2e` requires a build and Playwright Chromium; it starts its own backend.

The shell includes Router, TanStack Vue Query, PrimeVue, Lucide icons, and locally bundled fonts. PrimeVue 4.3.9 and PrimeUI themes 1.2.3 are pinned to verified MIT-licensed releases; check licensing and browser output before upgrading. No login or command execution is implemented.

