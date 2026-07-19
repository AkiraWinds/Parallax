---
name: architecture-docs
description: >
  Review dimensions: architecture/maintainability and documentation
  accuracy (docs-vs-code drift, stale paths and capability claims).
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Architecture & Documentation

Apply these two review dimensions to the diff you're given.

## Architecture and Maintainability

- boundaries
- dependency direction
- coupling
- abstraction
- duplication
- evolution
- rollback
- long-term contract

## Documentation Accuracy

- Do existing docs (`CLAUDE.md`, `README.md`, architecture docs, any capability/status tables the project maintains) still describe the code accurately after this diff?
- Do file paths, module references, or capability claims in project docs still resolve to something real?
- This is distinct from a Definition-of-Done check ("did this diff update its own docs") — it catches pre-existing or diff-introduced drift between docs and code, not just missing updates for the current change.
