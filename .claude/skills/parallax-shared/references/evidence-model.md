# Evidence Model

Every candidate finding must be classified into exactly one of these
states before a subagent returns it. This corresponds to the canonical
schema's `status.evidence_state` field (main spec Section 11.1).

## Verified

Directly confirmed by:

- code
- test
- reproduction
- explicit contract
- trace
- deterministic evidence

## Supported

Strong evidence exists, but one external assumption remains.

## Hypothesis

Plausible risk without enough evidence.

Must not be phrased as a confirmed defect.

## Question

Missing context prevents judgment.

Must be phrased as a clarification request.

## Self-verification (Stage 6)

Before returning your findings, verify your own candidate findings using
the evidence available to you:

- inspect code
- inspect contracts
- inspect callers
- inspect tests
- run safe checks (`Bash`, scoped to the safe-commands list in
  `references/communication-and-handoff.md` — never edit, commit, or push)
- create minimal reproduction when appropriate
- inspect traces
- run repeated scenarios for nondeterministic behavior
- downgrade unsupported claims to Hypothesis or Question rather than
  asserting them as Verified
- validate each finding's JSON against the canonical schema before
  returning it — don't just eyeball it:

  ```bash
  echo '<your finding, as JSON>' \
    | parallax-cli validate-finding
  ```

  A finding that doesn't come back `{"valid": true}` is malformed, not
  just weakly evidenced — fix the JSON (e.g. a `review_finding_id` not
  namespaced as `PR-<your letter>-NNN`) before returning it, the same way
  you'd fix an unsupported claim rather than return it as-is.

The orchestrator does not re-verify your findings from scratch — it only
reconciles cases where two subagents' findings conflict, or where
verification requires combining two subagents' outputs. Assigning the
correct `evidence_state` is your responsibility, not the orchestrator's.
