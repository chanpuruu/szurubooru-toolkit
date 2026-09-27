---
status: accepted
date: 2026-09-27
deciders: "Repository maintainer"
tags: [process, documentation]
trigger: "Before recording or promoting an architecture decision"
---

# 0000. Record Architecture Decisions

## Context And Problem Statement

The toolkit has an extensive future web plan but no versioned decision system. Plans must remain distinguishable from implemented guarantees, and agents should not load every design discussion on every task.

## Decision Drivers

Keep rationale available across sessions and hosts, make status explicit, preserve alternatives, and keep always-loaded instructions concise.

## Considered Options

- Repository-owned Markdown ADRs: reviewable alongside implementation and tests.
- All rationale in root instructions: excessive context and weak distinction between current and future behavior.
- Chat/issues only: not reliably available with the checkout.

## Decision Outcome

Use this directory for numbered Markdown ADRs and an index with explicit read triggers. Use four-digit increasing numbers and kebab-case titles; never reuse a number. Retain superseded records with reciprocal replacement links.

Each record has YAML fields `status`, `date`, `deciders`, `tags`, and `trigger`, followed by the sections shown in the [outline](architecture-decision.md). Status is proposed, accepted, deprecated, or superseded. Dates use ISO calendar notation.

Choices earn records only when they have real alternatives and durable consequences. Keep conventions in coding standards. Merge accepted decisions with the implementation and validation that make them true. Keep unimplemented choices in the [backlog](backlog.md), without accepted ADR numbers. Label reconstructed decisions and cite their evidence.

## Validation

The `agent-guidance` pre-commit hook validates Markdown links, YAML parsing, and unresolved markers. Index/status agreement, required sections, numbering, reciprocal supersession, real alternatives, and implementation evidence require review; the validator does not enforce them all.

For each future runtime ADR, name a behavior test, schema guard, drift check, or operator procedure that verifies the decision. Root instructions must link it with a trigger when it is load-bearing.

## More Information

This process is enacted by the installed index, outline, backlog, [root guidance](../../AGENTS.md), and [validation tooling](../agents/TESTING.md). It does not declare the web plan implemented.