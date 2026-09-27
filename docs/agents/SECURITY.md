# Security Boundaries

Read for secrets, authentication, authorization, external requests, parsing, uploads, filesystem paths, subprocesses, cryptography, or destructive operations.

## Current Authorities

Szurubooru's remote API enforces the configured account's permissions. The toolkit config selects the endpoint and credentials; it is not a multi-user authorization service. The unauthenticated legacy extension bridge is retired. Keep the new scaffold read-only until authorization is implemented.

Configuration, cookie files, logs, downloads, and images can contain private data. Do not read or print real secrets to investigate setup. Never put tokens in examples, fixtures, command lines, Git, or review output. Use fake credentials and isolated configs for tests.

For external calls, verify destination/redirect trust, timeouts, bounded retries, payload sizes, and failure behavior. Preserve argv-based subprocess invocation without a shell. Validate arguments as well as avoiding shell interpolation; option injection and unsafe downloader configuration remain risks.

Uploads and metadata are untrusted. Resolve paths against explicit roots, reject traversal/symlink escapes and special files, and test denied paths. Source cleanup is destructive and requires explicit intent, not a hidden default.

## Web Implementation Requirements

The [plan](../plans/web-ui.md) proposes a single-admin authenticated backend and encrypted profiles; neither exists yet. Implement authorization at every API/data access boundary, not only in navigation or disabled buttons. Protect unsafe cookie-authenticated requests against CSRF and avoid persistent browser credential storage.

Use maintained session, password-hashing, and encryption libraries. Keep the bootstrap secret lifecycle explicit. Encrypt profile secrets and private snapshots, restrict key/config file permissions, redact logs and events, and include key backup/recovery rules. Host compromise is outside what a co-located encryption key can prevent.

Constrain outbound importer destinations as well as file paths. The configured local Szurubooru endpoint is a deliberate exception to generic private-network restrictions, not permission for arbitrary SSRF. Validate redirects and resource limits at the actual network boundary.

Cancellation cannot undo remote mutations. Do not promise rollback or exactly-once execution. Revalidate authorization and target identity at execution time; test alternate entry points and stale confirmation races.

Security-sensitive changes need permitted, denied, malformed, stale, bypass, and information-disclosure tests. Escalate unresolved identity, cryptographic, sandbox, or destructive-data design questions to the maintainer before inventing policy.