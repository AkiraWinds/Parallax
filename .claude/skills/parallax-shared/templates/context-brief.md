# Context Brief Template

Produced once by the orchestrator (Stage 0–2), passed to every dispatched
subagent. A subagent should never need to re-derive any of this itself.

```markdown
# Review Context Brief

## Review Contract (Stage 0)

- Intended change:
- Expected behavior:
- Scope:
- Out of scope:
- Constraints:
- Confirmed facts:
- Inferred assumptions:
- Unknowns:
- Initial risk areas:
- Review profile: general | agent-system (stated by user, if given —
  see main spec Section 9.2/10)
- Time budget:

## Repository Context (Stage 1)

- Repository structure:
- CLAUDE.md summary:
- AGENTS.md summary (if present):
- CONTRIBUTING.md summary (if present):
- README.md summary:
- Relevant PR template fields:
- CI workflow summary:
- Changed files:
- Nearby files:
- Callers and callees of changed symbols:
- Relevant historical changes:

## Change Map (Stage 2)

- Input:
- Validation:
- Transformation:
- State transition:
- External systems:
- Tools:
- Side effects:
- Persistence:
- Output:
- Error path:
- Human handoff:
- Evaluation path:
- Memory write-back:
```

Missing context is not a code defect (main spec Section 10, Stage 0) — if
a field above is unknown, write "unknown" rather than guessing, and let
the general review's Intent dimension raise it as a question.
