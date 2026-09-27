# Publishing And Human Review

Read before requesting authorization for or executing a protected action.

Local edits, local tests/builds, and read-only Git inspection are allowed within the active task. Branch creation, commits, pushes, remote issue/review edits, CI triggers, merges, releases, publishing, deployment, and destructive operations require explicit authorization for the exact action. Permission for one is not permission for the next.

Current release workflows are [Docker publishing](../../.github/workflows/deploy-to-docker-hub.yml) and [PyPI publishing](../../.github/workflows/deploy-to-pypi.yml), both tag-triggered. Pushing a tag can publish artifacts; do not use a tag as a harmless test. Do not change remote permissions, branch protection, registries, or hosting simply because the user syncs through GitLab.

Before an authorized operation, inspect status, diff, current branch, intended remote, and staged contents. Exclude secrets, unrelated work, generated noise, and unapproved lockfile changes. Report checks and residual risks, then name the exact operation awaiting approval.

Preserve existing image tags, extras, CLI entry points, and cron/PUID/PGID behavior unless the active task authorizes migration. Extension/bridge retirement is an unreleased breaking change authorized during structural cleanup; it does not authorize publishing or claim operational web deployment is ready.

Before remote review posting, confirm the reviewed revision, deduplicate existing discussions, anchor findings to relevant code, and verify the write result. A review request alone grants no remote-write permission.