# Decision Backlog

These choices were selected during planning but are not implemented architecture. The full scope remains in [WEB_UI_PLAN.md](../../WEB_UI_PLAN.md). The maintainer owns each candidate. Promote only with the relevant implementation and guard; do not treat this list as authorization to build every item.

| Candidate | Alternatives and consequence | Promotion trigger and evidence |
| --- | --- | --- |
| Vue 3 + TypeScript + Vite SPA | React/Svelte or server rendering; maintainer selected Vue SPA. Planned Router, PrimeVue, Lucide, TanStack Query and limited Pinia use. | Frontend scaffold, real scripts/lockfile, component/type/build tests; API client generation added with schema ownership. |
| FastAPI versioned same-origin API | Flask/Django or extension bridge; typed contracts and SSE fit the SPA. Core CLI must not depend on web code. | API scaffold, route/auth boundaries, OpenAPI tests, SPA serving checks. |
| One Unraid container, SQLite dispatcher, one active child job | Separate workers/Redis add operations without current distribution needs. Scripts already parallelize internally and hold process-global state. | Durable claim/recovery tests, process-tree cancellation, no replay; appdata on local storage, not SMB/NFS. |
| Single-admin login and encrypted named profiles | Proxy-only auth or config-only operation; built-in auth and web profiles selected for trusted LAN. | Auth/CSRF/denial/redaction tests, key recovery procedure, immutable job snapshot and isolated config tests. |
| Browser upload and allowlisted mounted roots | Browser-only or mounted-only reduces flexibility. Cleanup is destructive; network/media paths are not appdata. | Streaming limits, path/symlink denial, cookie secrecy, source-cleanup and retention tests. |
| All 13 command workflows with structured results | Thin terminal wrapper was rejected. CLI failure/progress contracts must first be reliable. | Registry parity, item/result events, preflight and execution-target tests, browser flows for each command. |
| Immediate extension retirement in web release | Deprecation window or archived bridge rejected by maintainer. Existing code remains until that release is implemented. | SPA import replacement, legacy endpoint removal tests, breaking-release docs; preserve ordinary CLI usage. |
| Docker packaging across extras, future scheduling deferred | Node only at build time; CPU and CUDA ONNX extras cannot coexist. Existing CPU/Pixiv all image remains; all-cuda is planned. | Image builds, capability reporting, health/PUID/GPU tests; future schedules enqueue through the same dispatcher. |

## Scaffolding Handoff

Request branch creation separately. Begin with the plan's command contracts and one coherent scaffold slice, not every feature at once. Add scoped instructions only when real frontend/API boundaries exist. Record actual package scripts, migration/generation commands, and CI checks with their implementations.

Before security-sensitive scaffolding, resolve execution-target races, bootstrap token retention, credential/key backup, redirect/SSRF policy, and cancellation's partial-effect semantics. The plan is a design input, not proof those risks are already solved.