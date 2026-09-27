# Design Principles

Read before UI, UX, information architecture, or product-design work.

The browser extensions are retired. The target interface in [the web plan](../plans/web-ui.md) is a Vue 3 SPA for one administrator on an Unraid-hosted trusted LAN. Only a read-only scaffold exists; do not treat planned workflows as installed.

- Build a working operator console, not a landing page or shell-command textbox. Organize all 13 operational commands into import/upload, tagging, organization, maintenance, jobs, and profiles.
- Follow the planned Vue/TypeScript/Vite, PrimeVue, and Lucide choices when scaffolding. Keep server state in TanStack Vue Query and reserve Pinia for genuinely client-owned state; avoid duplicate session/data authorities.
- Use explicit typed workflow forms with shared field primitives. Do not replace the chosen workflow-oriented UI with generic descriptor forms solely because the source kit suggests them.
- Keep layouts compact and predictable, with clear job state, profile selection, risk, progress, and recoverable errors. Do not imply that cancellation reverses completed work.
- Preserve input on recoverable errors. Handle loading, empty, partial, stale, disconnected, denied, read-only, and successful states.
- Use semantic controls, labels, keyboard navigation, managed dialog focus, and non-color status cues. Support mobile monitoring, touch, high zoom, reduced motion, and WCAG AA contrast.
- Keep control/progress dimensions stable. Verify desktop/mobile screenshots and actual interaction; automated accessibility checks do not replace keyboard review.
- Build production SPA assets in the image/CI pipeline once established, not from an undocumented developer-local bundle. Test same-origin API and SPA history fallback boundaries.

Future framework commands, generated client ownership, and component conventions must be added alongside the scaffolding that makes them real.