# Decision Backlog

These choices were selected during planning but are not implemented architecture. The full scope remains in [the web plan](../plans/web-ui.md). The maintainer owns each candidate. Promote only with the relevant implementation and guard; do not treat this list as authorization to build every item.

The Vue/FastAPI read-only foundation and offline API generation are implemented in [ADR-0001](0001-read-only-web-scaffold.md). Operational interfaces, SSE, authentication and all candidates below remain pending.

The maintainer brought extension/bridge retirement forward into structural cleanup in [ADR-0002](0002-retire-legacy-browser-bridge.md). Removal is complete, but this does not complete the replacement import workflow.

| Candidate | Alternatives and consequence | Promotion trigger and evidence |
| --- | --- | --- |
| One Unraid container, SQLite dispatcher, one active child job | Separate workers/Redis add operations without current distribution needs. Scripts already parallelize internally and hold process-global state. | Durable claim/recovery tests, process-tree cancellation, no replay; appdata on local storage, not SMB/NFS. |
| Single-admin login and encrypted named profiles | Proxy-only auth or config-only operation; built-in auth and web profiles selected for trusted LAN. | Auth/CSRF/denial/redaction tests, key recovery procedure, immutable job snapshot and isolated config tests. |
| Browser upload and allowlisted mounted roots | Browser-only or mounted-only reduces flexibility. Cleanup is destructive; network/media paths are not appdata. | Streaming limits, path/symlink denial, cookie secrecy, source-cleanup and retention tests. |
| All 13 command workflows with structured results | Thin terminal wrapper was rejected. CLI failure/progress contracts must first be reliable. | Registry parity, item/result events, preflight and execution-target tests, browser flows for each command. |
| Docker packaging across extras, future scheduling deferred | Node only at build time; CPU and CUDA ONNX extras cannot coexist. Existing CPU/Pixiv all image remains; all-cuda is planned. | Image builds, capability reporting, health/PUID/GPU tests; future schedules enqueue through the same dispatcher. |

## Scaffolding Handoff

Request branch creation separately. The read-only foundation now has scoped instructions and documented scripts. Continue with separately authorized command-contract and operational slices, not every feature at once. Add migration/auth/job guidance only with those implementations.

Before security-sensitive scaffolding, resolve execution-target races, bootstrap token retention, credential/key backup, redirect/SSRF policy, and cancellation's partial-effect semantics. The plan is a design input, not proof those risks are already solved.