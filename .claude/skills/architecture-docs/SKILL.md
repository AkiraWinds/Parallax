---
name: architecture-docs
description: >
  Review dimensions: architecture/maintainability (boundaries, coupling,
  abstraction, long-term contracts) and documentation accuracy (docs-vs-code
  drift, stale paths and capability claims).
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Architecture & Documentation

Apply these two review dimensions to the diff you're given.

## Architecture and Maintainability

- **Boundaries**: Are module/service boundaries respected, or does the diff reach across a layer it shouldn't?
- **Dependency direction**: Does the dependency direction stay consistent (e.g., does a lower-level module now import from a higher-level one)?
- **Coupling**: Is coupling increased in a way that makes future changes harder, or kept loose where it matters?
- **Abstraction**: Is the abstraction at the right level — not over-engineered for a one-off, not leaking implementation details it shouldn't?
- **Duplication**: Is logic duplicated that already exists elsewhere in the codebase?
- **Evolution**: Does this change make future evolution easier or harder — does it paint the codebase into a corner?
- **Rollback**: Can this change be rolled back cleanly if it needs to be reverted?
- **Long-term contract**: Does this diff commit the codebase to a long-term contract (public API, schema, interface) it may come to regret?

## Documentation Accuracy

- Do existing docs (`CLAUDE.md`, `README.md`, architecture docs, any capability/status tables the project maintains) still describe the code accurately after this diff?
- Do file paths, module references, or capability claims in project docs still resolve to something real?
- This is distinct from a Definition-of-Done check ("did this diff update its own docs") — it catches pre-existing or diff-introduced drift between docs and code, not just missing updates for the current change.
