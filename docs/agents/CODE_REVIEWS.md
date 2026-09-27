# Repository Review Concerns

Use the [code-review skill](../../.claude/skills/code-review/SKILL.md). Load security, testing, design, or decision guidance only when the diff triggers it.

Prioritize:

- CLI option/default/config precedence and compatibility for both entry points.
- Global config/client initialization, shared caches, rate limits, thread pools, and interrupt behavior.
- Partial failures hidden by exception logging, ignored subprocess return codes, or misleading success summaries.
- Import/upload duplicates, sidecars, source cleanup, relations, safety handling, and remote API effects.
- Credential/log disclosure, cookie assets, outbound request trust, path confinement, and argv validation.
- Docker mount permissions, non-root execution, image extras, GPU fallbacks, cron behavior, and release-tag effects.
- Tests isolated from real home config, accounts, model downloads, and non-disposable data.

For future web changes, review immutable profile snapshots, transactionally claimed jobs, state recovery, process-tree cancellation, no automatic mutation replay, and stale confirmation races. UI auth is not authorization. Inspect all API, streaming, file, thumbnail, and log access paths.

Review generated API drift, migrations, same-origin routing, and actual production asset serving once present. Check responsive layout, focus, labels, keyboard interaction, high zoom, and loading/error/empty/denied states.

Report only introduced or materially worsened defects, with severity, true location, evidence, realistic impact, and a correction when clear. Label uncertainty as a question. A request to review authorizes neither remediation nor remote posting.