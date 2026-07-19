````markdown
# GitHub Comment Template

Used only when the user has explicitly authorized posting comments
(main spec Section 24 — read-only by default).

One finding → one comment, using the canonical finding's `communication`
fields directly:

```markdown
**[{{comment_type}}]** {{claim.title}}

{{claim.observation}}

**Failure scenario:** {{claim.failure_scenario}}

**Impact:** {{claim.impact}}

{{#if recommendation}}
**Recommendation:** {{recommendation.options.0.description}}
({{recommendation.options.0.tradeoffs}})
{{/if}}

<sub>Source: {{source.system}}{{#if source.source_id}} ({{source.source_id}}){{/if}} · Confidence: {{status.confidence}} · {{status.evidence_state}}</sub>
```
````

- `comment_type` is one of `request_change | question | suggestion | nit` —
  never post a `blocker`-level finding as anything other than
  `request_change`.
- Never post a Hypothesis or Question phrased as a confirmed defect — the
  template's evidence_state tag exists specifically so the reader can see
  this at a glance.

```

```
