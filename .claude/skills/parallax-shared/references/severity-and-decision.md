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

If you're the `sanyi-review` subagent proposing an initial merge impact
for one of your own findings, get the default from the CLI rather than
re-deriving this table from memory — it's a starting suggestion the
orchestrator (or a human) may still override per Section 14.2, not a
rule to skip:

```bash
echo '{"severity": "warning"}' \
  | parallax-cli sanyi-default-impact
```

## Display cap on nit/suggestion findings

Every nit/suggestion finding still gets the same rigor when it's found and
classified — the cap below is a display convention, not a change to
evidence classification or merge-impact assignment. In the rendered
report body, the Suggestions section shows only the top N (default 5, by
merge-impact/confidence order) suggestion-level findings via
`parallax-cli cap-suggestions`; `ReviewReport.suggestions_omitted_count`
carries the remainder, and `render-report` turns it into a one-line note
(e.g. "+3 additional minor suggestions omitted") rather than silently
dropping the count. The omitted findings themselves are not written to
`.parallax/review-report.md` — that artifact only ever contains the
capped set. They remain visible earlier in the review conversation
(Stage 7's dedup/bucket output), but there is currently no separate
persisted file holding the full, uncapped finding set — don't claim one
exists when writing up a report.
