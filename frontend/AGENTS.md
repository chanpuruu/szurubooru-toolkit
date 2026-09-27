# Frontend Guidance

Read [root guidance](../AGENTS.md) and [design principles](../docs/agents/DESIGN_PRINCIPLES.md) before UI work. This is a read-only scaffold, not a job dashboard. Do not add operational API calls until authentication and execution contracts are authorized and implemented.

Vue 3/TypeScript/Vite use npm and [package-lock.json](package-lock.json). Node 22.12+ in the 22 LTS line is the reference runtime. Use Router for routes, TanStack Vue Query for server state, PrimeVue for controls, and `@lucide/vue` for icons. Pinia is deferred until client-owned state needs it. The stylesheet owns the current operator-console theme; fonts and the toolkit icon are bundled assets.

Run from this directory: `npm ci`, `npm run lint`, `npm test`, `npm run build`. `npm run typecheck` checks TypeScript alone. Tests live alongside bounded behavior; integrated browser tests live in [e2e/](e2e/).

After `uv sync --extra web --python 3.11` at the root, run `npm run api:generate` here to regenerate [src/api.generated.ts](src/api.generated.ts) from the backend. Never hand-edit it. `npm run api:check` checks drift without rewriting. The generator exports OpenAPI offline; there is no public OpenAPI endpoint.

`npm run dev` serves loopback on port 5173 and proxies the API to loopback port 8080. `npm run test:e2e` requires a production build plus `npx playwright install chromium`; it starts its own FastAPI instance on port 8081 and does not reuse an arbitrary running server. Do not point tests at real toolkit instances.

Keep client routes in [src/router.ts](src/router.ts) aligned with the backend's explicit SPA routes. Do not turn unknown API or asset paths into HTML fallback. Verify desktop/mobile, keyboard, error/recovery, image loading, and overflow when changing the shell.