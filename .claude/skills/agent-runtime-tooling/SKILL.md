---
name: agent-runtime-tooling
description: >
  Review dimensions: agent-system runtime behavior — tool side effects,
  workflow state/partial failure, retrieval boundaries, memory write-back.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Agent Runtime & Tooling

Apply these four review dimensions to the diff you're given. Only relevant for agent-system PRs (LLMs, agents, prompts, tools, retrieval, memory, workflows).

## Tool Side Effects

- Is the tool read-only or write-capable?
- Is confirmation required?
- Is retry safe?
- Is idempotency guaranteed?
- Is output validated?
- Are permissions enforced at the tool boundary?

## Workflow State and Partial Failure

- Is the graph bounded?
- Can it terminate?
- Can it resume?
- What happens after partial success?
- Are handoffs explicit?
- Is deterministic code used where appropriate?

## Retrieval and Context

- Is retrieval scoped correctly?
- Is provenance preserved?
- Are permissions respected?
- Is stale or conflicting context handled?
- Can external content influence a sensitive sink? (Prompt injection via retrieved or external content is the named threat class here.)

## Memory Write-Back

- What is persisted?
- Is it fact, inference, or model output?
- Can it be corrected?
- Is confidence stored?
- Is approval required?
- Can bad runs contaminate future cases?
