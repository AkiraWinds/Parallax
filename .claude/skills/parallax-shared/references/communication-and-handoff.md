# Communication and Handoff

## Principles

- Do not optimize for the largest number of comments (main spec Section
  2). A surface-level review that produces many low-value comments about
  naming or formatting is a documented failure mode, not a feature.
- Reconstruct intent, trace behavioral change, identify material risks,
  verify claims with evidence, and support an explainable merge decision.
- Hypotheses are not defects — phrase them as hypotheses.
- Communication is part of correctness: a correct finding that's phrased
  as a certainty when it's only a hypothesis is itself a defect in the
  review.

## Per-finding communication

Every finding you return should be usable as a PR comment on its own:

- `comment_type`: `request_change | question | suggestion | nit`
- a `proposed_comment` that states the claim, references the evidence
  location, and (if actionable) a recommendation with trade-offs — not
  just "this looks wrong."

## Read-only default

Default to read-only. Do not:

- edit files
- apply patches
- run SANYI `--fix`
- commit
- push
- post GitHub comments
- approve
- request changes
- delete files
- modify configuration
- write an approved SANYI.md candidate entry (drafting one and surfacing
  it in the report requires no authorization; writing it into `SANYI.md`
  does)

unless the user explicitly authorizes it.

Safe commands (usable via `Bash` without authorization):

- reading files
- grep/search
- `git diff`
- `git status`
- test discovery
- known project checks (e.g. running the existing test suite)

Unknown scripts must be inspected before execution.
