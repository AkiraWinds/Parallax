---
name: intent-correctness
description: >
  Review dimensions: PR intent/product behavior, correctness and contracts
  (including cross-usage schema consistency), and test coverage.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Intent, Correctness & Testing

Apply these three review dimensions to the diff you're given.

## Intent and Product Behavior

- Does the PR solve the intended problem?
- Is user-visible behavior clear?
- Is the scope appropriate?
- Does it solve the cause or only the symptom?
- Is the implementation unnecessarily complex?

## Correctness and Contracts

- Inputs
- outputs
- schemas
- state transitions
- invariants
- edge cases
- ordering
- concurrency
- compatibility
- **cross-usage consistency**: when the diff modifies a shared schema/type, check all of its usages across the repo, not only the diff's own callers.

## Testing

- unit
- integration
- contract
- regression
- end-to-end
- negative paths
- useful assertions
- failure-before-fix evidence
