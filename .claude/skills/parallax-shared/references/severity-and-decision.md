# Severity and Decision

Do not collapse source severity and merge impact — they are separate
fields in the canonical schema (main spec Section 11.1:
`source_semantics.native_severity` vs. `review_assessment.merge_impact`).

## Source severity

Owned by the source system that produced the finding.

Examples:

- SANYI: `blocker | warning | info | notice`
- Parallax-native: your own subagent's internal risk assessment

Never invent or rewrite a source system's severity — if you're the
`sanyi-review` subagent, use SANYI's codes and severities exactly as
SANYI's own taxonomy assigns them.

## Merge impact

Owned by Parallax (the orchestrator, during Stage 7 synthesis — but every
subagent should still propose an initial merge-impact assessment on its
own findings before returning them, since the subagent has the context to
judge it).

Values:

- **blocker** — should not merge
- **important** — must be addressed or consciously accepted
- **question** — missing context prevents judgment
- **suggestion** — meaningful improvement but not required
- **nit** — minor polish

## Decision outcomes

The orchestrator's final recommendation is one of:

- `approve`
- `comment`
- `request_changes`
- `insufficient_context`

## Example mappings

```text
SANYI BY-2 blocker
→ canonical source severity: blocker
→ canonical merge impact: blocker
→ final decision influence: request changes
```

```text
SANYI JY-2 warning
→ canonical source severity: warning
→ canonical merge impact: important or suggestion
→ human decision required
```
