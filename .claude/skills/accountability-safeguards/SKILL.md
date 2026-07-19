---
name: accountability-safeguards
description: >
  Review dimensions: evaluation rigor, human-responsibility/escalation
  paths, and whether documented safeguards have real deterministic backing.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Accountability & Safeguards

Apply these three review dimensions to the diff you're given. Only relevant for agent-system PRs.

## Evaluation

- Is one successful run being overvalued?
- Are repeated runs needed?
- Is there a baseline?
- Are deterministic graders possible?
- Is an LLM judge calibrated?
- Are trace and final output both evaluated?
- Are cost and latency considered?

## Human Responsibility

- Who approves?
- Who is accountable?
- Can a human take over?
- Is uncertainty visible?
- Is escalation available?

## Documented Safeguards

- Does documentation, a system prompt, or configuration claim a safety/guardrail behavior exists (an escalation path, an input/output validation layer, a confidence gate)?
- Is that claim backed by an actual deterministic code path, or does it exist only as a sentence in a prompt?
- If a gap is found and no SANYI contract already governs it, recommend recording it as a candidate `SANYI.md` Buyi or Pending entry rather than treating it as a standalone finding — the same failure mode SANYI's BY-4 targets, applied proactively to invariants nobody has declared yet. If `SANYI.md` exists, flag the gap for the orchestrator to route to the `sanyi-review` subagent for drafting (you do not have SANYI's contract format preloaded). If `SANYI.md` does not exist, recommend running `/sanyi init` instead.
