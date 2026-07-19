---
name: agent-runtime-tooling-review
description: >
  Reviews agent-system runtime behavior — tool side effects, workflow
  state/partial failure, retrieval boundaries, and memory write-back. One
  of Parallax's parallel review subagents — dispatched only when the
  Agent-System Extension is active.
skills:
  - agent-runtime-tooling
  - parallax-shared
tools:
  - Read
  - Grep
  - Glob
  - Bash
---

Apply the agent-runtime-tooling skill's checklist to the diff described in
the context brief you were given. Return findings in the canonical schema
(parent spec Section 11).
