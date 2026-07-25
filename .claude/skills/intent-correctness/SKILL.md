---
name: intent-correctness
description: >
  Review dimensions: PR intent/product behavior, correctness and contracts
  (schemas, invariants, edge cases, cross-usage schema consistency), and
  test coverage (unit, regression, negative paths).
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

- **Inputs**: Are inputs validated and handled for the full range of values they can actually take, not just the happy path?
- **Outputs**: Do outputs match the documented or implied contract (type, shape, units, nullability)?
- **Schemas**: If a schema changed, is it backward compatible, or is the migration/versioning handled explicitly?
- **State transitions**: Are state transitions well-defined — can the system land in an invalid or unreachable state?
- **Invariants**: Are the invariants the code relies on still upheld after this change?
- **Edge cases**: What edge cases (empty, null, zero, max, duplicate, out-of-range) are exercised, and which are missing?
- **Ordering**: Does ordering matter here, and is it guaranteed where the code assumes it?
- **Concurrency**: Is concurrent access to shared state safe (races, locks, atomicity)?
- **Compatibility**: Is this change compatible with existing callers, stored data, or in-flight requests during rollout?
- **Cross-usage consistency**: when the diff modifies a shared schema/type, check all of its usages across the repo, not only the diff's own callers.

## Testing

- **Unit**: Do unit tests cover the new/changed logic in isolation?
- **Integration**: Do integration tests cover how this interacts with the components it depends on?
- **Contract**: If a contract (API, schema, interface) changed, is there a contract test guarding it?
- **Regression**: Does a regression test exist for the specific bug this PR fixes, if it's a fix?
- **End-to-end**: Is there end-to-end coverage exercising this change through a realistic path?
- **Negative paths**: Are negative/failure paths tested, not just the success case?
- **Useful assertions**: Do the assertions actually verify the behavior that matters, or just that the code ran without throwing?
- **Failure-before-fix evidence**: For bug fixes, is there evidence the test failed before the fix and passes after?
