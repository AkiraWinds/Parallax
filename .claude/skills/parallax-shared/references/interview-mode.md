# Interview Mode

When interview mode is active, in addition to your normal findings,
contribute your dimension's material toward this structure — assembled by
the orchestrator into one walkthrough (`templates/interview-walkthrough.md`):

```markdown
# PR Review Interview Walkthrough

## 60-Second Summary

## How I Approached the Review

## What the PR Does Well

## Main Concern 1

- observation
- scenario
- impact
- recommendation
- validation
- blocking status

## Main Concern 2

## Main Concern 3

## Clarifying Questions

## Alternative Designs and Trade-Offs

## Testing and Evaluation Strategy

## How New Constraints Would Change My Decision

## Final Merge Recommendation
```

Only the orchestrator produces the final walkthrough (it needs every
subagent's findings to pick the top three concerns) — an individual
subagent contributes candidate concerns from its own dimension, not the
assembled document.
