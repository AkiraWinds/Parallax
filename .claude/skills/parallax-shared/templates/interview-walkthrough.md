````markdown
# Interview Walkthrough Template

Produced only when interview mode is active (main spec Section 10, Stage
10; Section 23).

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
````

The three "Main Concern" slots are the top three findings by merge impact
across all dispatched subagents, not per-subagent — this is why only the
orchestrator assembles this document (main spec Section 23;
`references/interview-mode.md`).
