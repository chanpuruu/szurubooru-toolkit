---
status: accepted
date: 2026-09-27
deciders: "Repository maintainer"
tags: [compatibility, security, web]
trigger: "Changing legacy browser import compatibility or adding replacement import endpoints"
---

# 0002. Retire The Legacy Browser Bridge

## Context And Problem Statement

The original web plan deferred extension retirement until replacement workflows existed. During scaffold cleanup the maintainer explicitly selected retirement now, accepting a gap in browser-driven imports.

## Decision Drivers

Remove obsolete browser clients and their unauthenticated HTTP mutation surface while keeping ordinary CLI imports and the read-only scaffold independent.

## Considered Options

- Retain extensions until the replacement works: preserves browser convenience but retains the old bridge.
- Retire now: selected by the maintainer; simpler maintained surface with an explicit compatibility break.
- Redirect legacy calls to the scaffold: rejected because the scaffold has no authenticated job execution.

## Decision Outcome

Delete both extension directories, their documentation, the legacy HTTP handler, and its Click registration. Do not add an alias that silently substitutes the read-only server. The normal `import-from-url` CLI remains available. New web import workflows and a future CLI web launcher remain separate work.

This is an unreleased breaking change, not authorization to publish. Existing installations are unaffected until upgraded. Browser import functionality is unavailable in this checkout until the replacement is implemented.

## Validation

[CLI tests](../../tests/test_cli.py) reject the removed command without initializing config/clients and retain URL-import help. [API tests](../../tests/test_web.py) reject both legacy endpoints. Existing URL-import tests preserve ordinary import behavior.

## More Information

See [the updated plan](../plans/web-ui.md), [scaffold boundaries](0001-read-only-web-scaffold.md), and [the user-facing migration notice](../../README.md).
