---
name: code-review
description: "Use when reviewing a branch, pull or merge request, commit range, staged changes, working tree, or branch journal. Produce evidence-based findings and a verdict without editing or posting unless separately authorized."
---

# Code Review

## Scope

Resolve repository, head, base, and included working-tree changes. For a branch or review request, compare its head to the merge base with the verified target branch. For a branch journal, use the integration branch, not a same-feature tracking branch. For a commit/range, review exactly that range. For working-tree review, include staged/unstaged changes against HEAD and clearly relevant untracked files.

If plausible bases would materially change scope and no target can be verified, ask before proceeding. Record the reviewed head. Review does not authorize edits or remote actions.

## Context And Inspection

1. Read [root instructions](../../../AGENTS.md), any governing nested instructions, and [repository review concerns](../../../docs/agents/CODE_REVIEWS.md).
2. Inspect status, changed files, diff statistics, scoped commits, and complete scoped diff. Read direct callers/tests/contracts only to resolve concrete concerns.
3. Load triggered security, testing, design, or ADR guidance, not unrelated plans by default.
4. Review correctness, ordering, concurrency, defaults, partial failure, security/disclosure, operational safety, compatibility, focused coverage, and applicable accessibility.
5. Trace each candidate through the real controlling path and check guards/callers that might disprove it. Establish a realistic trigger and impact. Run a cheap isolated check when useful; never hit the owner's real instance.

## Findings

Report only actionable introduced or worsened defects, not pre-existing issues or formatter preferences. Each finding needs severity, exact location, evidence, impact/trigger, and the smallest safe correction plus missing regression coverage when clear. If the fix requires a product/security decision, name that decision instead of inventing it. Use the true code location even if outside the diff; do not anchor to an unrelated line.

- **Critical:** exploitable high-impact boundary failure, unrecoverable data loss, or broad outage; block and escalate.
- **High:** reachable defect with substantial correctness/security/operational impact; blocks approval.
- **Medium:** bounded real defect or material regression risk; blocks unless explicitly accepted.
- **Low:** concrete small defect or maintainability risk; normally non-blocking.

Unproven concerns are open questions, not findings. Do not manufacture findings to fill a quota.

## Output And Authorization

Present severity-ordered findings first, then open questions, concise summary/checks, and one verdict: Approve, Approve with non-blocking notes, Changes required, or Escalate for specialist review. If no findings, say so and identify test gaps/residual risk.

Do not edit, post, approve, resolve, merge, trigger CI, or publish without separate exact authorization. Before authorized remote posting, reconfirm the head, deduplicate discussions, and verify each write response.