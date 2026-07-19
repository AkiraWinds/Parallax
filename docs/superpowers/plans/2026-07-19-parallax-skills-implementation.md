# Parallax Skills & Agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Materialize Parallax's designed architecture — 6 dimension skills, the `parallax-shared` cross-cutting skill, a copied-in `sanyi` skill, and 8 agent definitions (7 subagents + the orchestrator) — as real files Claude Code can discover and preload, per `docs/documents/Evidence_Driven_PR_Review_System_Spec.md` and `docs/documents/Parallax_Subagent_Architecture.md`.

**Architecture:** Every skill lives at `.claude/skills/<name>/SKILL.md` (plus `references/` and/or `templates/` where the skill bundles more than a short checklist); every agent lives at `.claude/agents/<name>.md` with a `skills:` field that preloads its skill(s) at startup. This is the only pair of locations Claude Code actually discovers skills and agents from (main spec Section 33.12) — nothing here should end up anywhere else.

**Tech Stack:** Markdown + YAML frontmatter only. No application code, no dependencies, no test framework — verification steps check structural correctness (valid frontmatter, required fields, line-count guidance), not program behavior.

## Global Constraints

- Skills live at `.claude/skills/<name>/SKILL.md`; agents live at `.claude/agents/<name>.md`. No other location is discovered by Claude Code (spec Section 33.12) — do not create a top-level `skills/` or `agents/` folder.
- Every `SKILL.md` frontmatter block is delimited by `---` on its own line at the very top and end of the frontmatter, and must include `name:` and `description:`. Skill frontmatter uses `allowed-tools:`; agent frontmatter uses `tools:` (and, where applicable, `skills:`) — never mix these keys up (spec Section 33 — this exact mix-up was a review finding on an earlier draft).
- Keep every `SKILL.md` well under the ~500-line progressive-disclosure guideline. If a skill needs more than a short checklist, split detail into `references/*.md`, following SANYI's own `SKILL.md` + `references/*.md` structure (this is why `parallax-shared` has `references/` and the six dimension skills don't need any).
- Every subagent's `skills:` list includes its own dimension (or `sanyi`) skill **and** `parallax-shared` — except `parallax.md` (the orchestrator), which preloads only `parallax-shared` and dispatches the others by name rather than preloading their skills itself.
- Dimension-skill checklist content (the "Owns" bullets) must match `docs/documents/Parallax_Subagent_Architecture.md` Section 3 verbatim — do not paraphrase or drop bullets.
- SANYI's copied files (`SKILL.md`, `references/*.md`) must be byte-identical to the source in `~/Desktop/personal/SANYI/`, except for one added provenance comment noting the source commit and copy date (spec Section 33.12) — do not edit SANYI's actual instructions.
- No placeholders anywhere — every file's content is given in full in this plan; if something doesn't fit in a step's code block, that's a gap in this plan, not license to invent content.

---

### Task 1: Copy SANYI's skill in verbatim

**Files:**

- Create: `.claude/skills/sanyi/SKILL.md`
- Create: `.claude/skills/sanyi/references/contract-spec.md`
- Create: `.claude/skills/sanyi/references/interview-guide.md`
- Create: `.claude/skills/sanyi/references/violations.md`

**Interfaces:**

- Consumes: `~/Desktop/personal/SANYI/SKILL.md` and `~/Desktop/personal/SANYI/references/*.md` (read-only source, outside this repo — do not modify it).
- Produces: a skill named `sanyi` (per its own `name:` frontmatter field), which Task 5's `sanyi-review.md` and Task 6's dispatch logic reference by that name.

- [ ] **Step 1: Record the source commit**

```bash
git -C ~/Desktop/personal/SANYI rev-parse HEAD
```

Note the output (a 40-character commit hash) — you'll use it in Step 3.

- [ ] **Step 2: Copy the files**

```bash
mkdir -p .claude/skills/sanyi/references
cp ~/Desktop/personal/SANYI/SKILL.md .claude/skills/sanyi/SKILL.md
cp ~/Desktop/personal/SANYI/references/contract-spec.md .claude/skills/sanyi/references/contract-spec.md
cp ~/Desktop/personal/SANYI/references/interview-guide.md .claude/skills/sanyi/references/interview-guide.md
cp ~/Desktop/personal/SANYI/references/violations.md .claude/skills/sanyi/references/violations.md
```

- [ ] **Step 3: Add the provenance comment**

Open `.claude/skills/sanyi/SKILL.md`. Immediately after the closing `---` of
the frontmatter (before the `# SANYI (三易)` heading), insert this line
(replace `<COMMIT>` with the hash from Step 1, and `<DATE>` with today's
date in `YYYY-MM-DD` form):

```markdown
<!-- Vendored from ~/Desktop/personal/SANYI @ <COMMIT>, <DATE>. Not a
     submodule — see Parallax spec Section 33.12. Re-copy manually if
     SANYI is updated upstream; this file is not auto-synced. -->
```

Do not change anything else in the file.

- [ ] **Step 4: Verify structure**

```bash
head -20 .claude/skills/sanyi/SKILL.md
grep -c "^name: sanyi" .claude/skills/sanyi/SKILL.md
ls .claude/skills/sanyi/references/
```

Expected: the frontmatter's `name:` field reads `sanyi`; the provenance
comment appears once, right after the frontmatter; all three reference
files are present; `diff` against the source (excluding the one comment
line you added) shows no other changes:

```bash
diff <(tail -n +2 ~/Desktop/personal/SANYI/SKILL.md) <(tail -n +2 .claude/skills/sanyi/SKILL.md | grep -v '^<!-- Vendored' | grep -v '^     SANYI is updated' | grep -v '^ *submodule')
```

(A small amount of diff noise from the multi-line comment is expected —
confirm by eye that nothing else differs.)

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/sanyi/
git commit -m "vendor: copy SANYI skill into .claude/skills/sanyi"
```

---

### Task 2: Create the six dimension skills

**Files:**

- Create: `.claude/skills/intent-correctness/SKILL.md`
- Create: `.claude/skills/reliability-operations/SKILL.md`
- Create: `.claude/skills/security-privacy-data/SKILL.md`
- Create: `.claude/skills/architecture-docs/SKILL.md`
- Create: `.claude/skills/agent-runtime-tooling/SKILL.md`
- Create: `.claude/skills/accountability-safeguards/SKILL.md`

**Interfaces:**

- Produces: six skills named `intent-correctness`, `reliability-operations`, `security-privacy-data`, `architecture-docs`, `agent-runtime-tooling`, `accountability-safeguards` — each referenced by name in Task 5's corresponding `.claude/agents/*.md` `skills:` list.

- [ ] **Step 1: Create `intent-correctness/SKILL.md`**

```bash
mkdir -p .claude/skills/intent-correctness
```

```yaml
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
```

Save the above as `.claude/skills/intent-correctness/SKILL.md`.

- [ ] **Step 2: Create `reliability-operations/SKILL.md`**

```bash
mkdir -p .claude/skills/reliability-operations
```

```yaml
---
name: reliability-operations
description: >
  Review dimensions: reliability (retries, idempotency, partial failure,
  recovery) and operational readiness (logging, rollout, rollback).
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Reliability & Operations

Apply these two review dimensions to the diff you're given.

## Reliability

- retries
- timeouts
- idempotency
- partial failures
- fallback
- cancellation
- recovery
- cleanup
- consistency

## Operations and Delivery

- logging
- metrics
- tracing
- deployment
- rollout
- rollback
- migration
- documentation
- handoff
```

Save the above as `.claude/skills/reliability-operations/SKILL.md`.

- [ ] **Step 3: Create `security-privacy-data/SKILL.md`**

```bash
mkdir -p .claude/skills/security-privacy-data
```

```yaml
---
name: security-privacy-data
description: >
  Review dimensions: security, privacy, and data/state handling
  (authn/authz, PII, secrets, validation, provenance, migration).
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Security, Privacy & Data

Apply these two review dimensions to the diff you're given.

## Security and Privacy

- authn
- authz
- tenant isolation
- PII
- secrets
- injection
- unsafe writes
- auditability

## Data and State

- validation
- provenance
- migration
- serialization
- stale data
- duplicated state
- source of truth
```

Save the above as `.claude/skills/security-privacy-data/SKILL.md`.

- [ ] **Step 4: Create `architecture-docs/SKILL.md`**

```bash
mkdir -p .claude/skills/architecture-docs
```

```yaml
---
name: architecture-docs
description: >
  Review dimensions: architecture/maintainability and documentation
  accuracy (docs-vs-code drift, stale paths and capability claims).
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Architecture & Documentation

Apply these two review dimensions to the diff you're given.

## Architecture and Maintainability

- boundaries
- dependency direction
- coupling
- abstraction
- duplication
- evolution
- rollback
- long-term contract

## Documentation Accuracy

- Do existing docs (`CLAUDE.md`, `README.md`, architecture docs, any capability/status tables the project maintains) still describe the code accurately after this diff?
- Do file paths, module references, or capability claims in project docs still resolve to something real?
- This is distinct from a Definition-of-Done check ("did this diff update its own docs") — it catches pre-existing or diff-introduced drift between docs and code, not just missing updates for the current change.
```

Save the above as `.claude/skills/architecture-docs/SKILL.md`.

- [ ] **Step 5: Create `agent-runtime-tooling/SKILL.md`**

```bash
mkdir -p .claude/skills/agent-runtime-tooling
```

```yaml
---
name: agent-runtime-tooling
description: >
  Review dimensions: agent-system runtime behavior — tool side effects,
  workflow state/partial failure, retrieval boundaries, memory write-back.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Agent Runtime & Tooling

Apply these four review dimensions to the diff you're given. Only relevant for agent-system PRs (LLMs, agents, prompts, tools, retrieval, memory, workflows).

## Tool Side Effects

- Is the tool read-only or write-capable?
- Is confirmation required?
- Is retry safe?
- Is idempotency guaranteed?
- Is output validated?
- Are permissions enforced at the tool boundary?

## Workflow State and Partial Failure

- Is the graph bounded?
- Can it terminate?
- Can it resume?
- What happens after partial success?
- Are handoffs explicit?
- Is deterministic code used where appropriate?

## Retrieval and Context

- Is retrieval scoped correctly?
- Is provenance preserved?
- Are permissions respected?
- Is stale or conflicting context handled?
- Can external content influence a sensitive sink? (Prompt injection via retrieved or external content is the named threat class here.)

## Memory Write-Back

- What is persisted?
- Is it fact, inference, or model output?
- Can it be corrected?
- Is confidence stored?
- Is approval required?
- Can bad runs contaminate future cases?
```

Save the above as `.claude/skills/agent-runtime-tooling/SKILL.md`.

- [ ] **Step 6: Create `accountability-safeguards/SKILL.md`**

```bash
mkdir -p .claude/skills/accountability-safeguards
```

```yaml
---
name: accountability-safeguards
description: >
  Review dimensions: evaluation rigor, human-responsibility/escalation
  paths, and whether documented safeguards have real deterministic backing.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Accountability & Safeguards

Apply these three review dimensions to the diff you're given. Only relevant for agent-system PRs.

## Evaluation

- Is one successful run being overvalued?
- Are repeated runs needed?
- Is there a baseline?
- Are deterministic graders possible?
- Is an LLM judge calibrated?
- Are trace and final output both evaluated?
- Are cost and latency considered?

## Human Responsibility

- Who approves?
- Who is accountable?
- Can a human take over?
- Is uncertainty visible?
- Is escalation available?

## Documented Safeguards

- Does documentation, a system prompt, or configuration claim a safety/guardrail behavior exists (an escalation path, an input/output validation layer, a confidence gate)?
- Is that claim backed by an actual deterministic code path, or does it exist only as a sentence in a prompt?
- If a gap is found and no SANYI contract already governs it, recommend recording it as a candidate `SANYI.md` Buyi or Pending entry rather than treating it as a standalone finding — the same failure mode SANYI's BY-4 targets, applied proactively to invariants nobody has declared yet. If `SANYI.md` exists, flag the gap for the orchestrator to route to the `sanyi-review` subagent for drafting (you do not have SANYI's contract format preloaded). If `SANYI.md` does not exist, recommend running `/sanyi init` instead.
```

Save the above as `.claude/skills/accountability-safeguards/SKILL.md`.

- [ ] **Step 7: Verify structure**

```bash
for f in intent-correctness reliability-operations security-privacy-data architecture-docs agent-runtime-tooling accountability-safeguards; do
  echo "=== $f ==="
  wc -l ".claude/skills/$f/SKILL.md"
  grep -c "^name: $f" ".claude/skills/$f/SKILL.md"
  grep -c "^allowed-tools:" ".claude/skills/$f/SKILL.md"
done
```

Expected: each file well under 500 lines; each `name:` grep returns `1`;
each `allowed-tools:` grep returns `1`.

- [ ] **Step 8: Commit**

```bash
git add .claude/skills/intent-correctness/ .claude/skills/reliability-operations/ .claude/skills/security-privacy-data/ .claude/skills/architecture-docs/ .claude/skills/agent-runtime-tooling/ .claude/skills/accountability-safeguards/
git commit -m "feat: add six Parallax dimension skills"
```

---

### Task 3: Create `parallax-shared`'s `SKILL.md` and `references/*.md`

**Files:**

- Create: `.claude/skills/parallax-shared/SKILL.md`
- Create: `.claude/skills/parallax-shared/references/evidence-model.md`
- Create: `.claude/skills/parallax-shared/references/severity-and-decision.md`
- Create: `.claude/skills/parallax-shared/references/definition-of-done.md`
- Create: `.claude/skills/parallax-shared/references/communication-and-handoff.md`
- Create: `.claude/skills/parallax-shared/references/interview-mode.md`

**Interfaces:**

- Produces: a skill named `parallax-shared`, preloaded by every one of the 8 agent files created in Tasks 5–6.

- [ ] **Step 1: Create the references directory and its five files**

```bash
mkdir -p .claude/skills/parallax-shared/references
```

`.claude/skills/parallax-shared/references/evidence-model.md`:

```markdown
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

The orchestrator does not re-verify your findings from scratch — it only
reconciles cases where two subagents' findings conflict, or where
verification requires combining two subagents' outputs. Assigning the
correct `evidence_state` is your responsibility, not the orchestrator's.
```

`.claude/skills/parallax-shared/references/severity-and-decision.md`:

````markdown
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
````

`.claude/skills/parallax-shared/references/definition-of-done.md`:

````markdown
# Definition of Done

Default fallback checklist:

- intended behavior complete
- important edge cases handled
- tests sufficient
- evaluation sufficient
- documentation updated
- observability present
- migration handled
- rollout understood
- rollback understood
- security reviewed
- handoff complete
- limitations recorded

## Priority

```text
Repository-specific DoD
→ Team/project DoD
→ Skill default (this file)
```
````

Check the target repo for its own Definition of Done (a `CONTRIBUTING.md`
section, a PR template checklist, or similar) before falling back to the
default list above. A repository-specific DoD always wins over this
file's defaults.

````

`.claude/skills/parallax-shared/references/communication-and-handoff.md`:

```markdown
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
````

`.claude/skills/parallax-shared/references/interview-mode.md`:

````markdown
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
````

Only the orchestrator produces the final walkthrough (it needs every
subagent's findings to pick the top three concerns) — an individual
subagent contributes candidate concerns from its own dimension, not the
assembled document.

````

- [ ] **Step 2: Create `SKILL.md`**

```yaml
---
name: parallax-shared
description: >
  Cross-cutting rules every Parallax review subagent and the orchestrator
  need: evidence classification, severity vs. merge-impact separation,
  communication format, Definition of Done, and interview-mode output.
  Preloaded by every subagent alongside its own dimension (or SANYI) skill.
allowed-tools:
  - Read
---

# Parallax Shared Rules

Cross-cutting rules that apply across every review dimension. Every
subagent and the orchestrator preload this skill alongside their own.

## Evidence classification (operational summary)

Every candidate finding must be classified before it's returned:

- **Verified** — directly confirmed by code, test, reproduction, explicit
  contract, trace, or other deterministic evidence.
- **Supported** — strong evidence exists, but one external assumption
  remains.
- **Hypothesis** — plausible risk without enough evidence. Must not be
  phrased as a confirmed defect.
- **Question** — missing context prevents judgment. Must be phrased as a
  clarification request, not a finding.

Full detail: `references/evidence-model.md`.

## Severity vs. merge impact (operational summary)

Never collapse a source system's own severity (e.g. SANYI's
blocker/warning/info/notice) with Parallax's merge-impact classification
(`blocker | important | question | suggestion | nit`). They answer
different questions — how bad the source system says this is, vs. whether
*this specific PR* should merge because of it.

Full detail: `references/severity-and-decision.md`.

## Definition of Done (operational summary)

Assess: behavior, tests, evaluation, documentation, observability,
migration, rollout, rollback, security, handoff, known limitations.
Priority: repository-specific DoD, then team/project DoD, then this
skill's default.

Full detail: `references/definition-of-done.md`.

## Communication (operational summary)

Do not maximize comment count. Every finding needs a clear claim,
evidence, and (if actionable) a recommendation with trade-offs. Findings
phrased as hypotheses or questions must say so explicitly, not read like
confirmed defects.

Full detail: `references/communication-and-handoff.md`.

## Interview mode (operational summary)

When interview mode is active, add a 60-second summary, top three
concerns with blocking rationale, alternatives/trade-offs, and a final
merge recommendation — see `references/interview-mode.md` for the full
output shape.

## References — load on demand

| File | Read when |
| --- | --- |
| `references/evidence-model.md` | classifying a candidate finding |
| `references/severity-and-decision.md` | assigning merge impact, or reconciling source severity with it |
| `references/definition-of-done.md` | assessing whether the PR is ready to merge |
| `references/communication-and-handoff.md` | writing up a finding or the final report |
| `references/interview-mode.md` | interview mode is requested |

## Templates

| File | Used by |
| --- | --- |
| `templates/context-brief.md` | orchestrator, Stage 0–2 output passed to every subagent |
| `templates/review-report.md` | orchestrator, final unified report |
| `templates/github-comment.md` | orchestrator, when posting a finding as a PR comment (requires explicit authorization) |
| `templates/interview-walkthrough.md` | orchestrator, interview mode output |
````

Save the above as `.claude/skills/parallax-shared/SKILL.md`.

- [ ] **Step 3: Verify structure**

```bash
wc -l .claude/skills/parallax-shared/SKILL.md
ls .claude/skills/parallax-shared/references/
grep -c "^name: parallax-shared" .claude/skills/parallax-shared/SKILL.md
```

Expected: `SKILL.md` well under 500 lines; five reference files present
(`evidence-model.md`, `severity-and-decision.md`, `definition-of-done.md`,
`communication-and-handoff.md`, `interview-mode.md`); `name:` grep returns `1`.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/parallax-shared/SKILL.md .claude/skills/parallax-shared/references/
git commit -m "feat: add parallax-shared skill (SKILL.md + references)"
```

---

### Task 4: Create `parallax-shared`'s `templates/*.md`

**Files:**

- Create: `.claude/skills/parallax-shared/templates/context-brief.md`
- Create: `.claude/skills/parallax-shared/templates/review-report.md`
- Create: `.claude/skills/parallax-shared/templates/github-comment.md`
- Create: `.claude/skills/parallax-shared/templates/interview-walkthrough.md`

**Interfaces:**

- Consumes: `parallax-shared/SKILL.md`'s Templates table (Task 3), which names exactly these four files.
- Produces: the template files Task 6's orchestrator agent references directly by path.

- [ ] **Step 1: Create the templates directory and its four files**

```bash
mkdir -p .claude/skills/parallax-shared/templates
```

`.claude/skills/parallax-shared/templates/context-brief.md`:

````markdown
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
````

Missing context is not a code defect (main spec Section 10, Stage 0) — if
a field above is unknown, write "unknown" rather than guessing, and let
the general review's Intent dimension raise it as a question.

`.claude/skills/parallax-shared/templates/review-report.md`:

````markdown
# Review Report Template

Produced once by the orchestrator after Stage 7–10, over every dispatched
subagent's combined canonical findings.

```markdown
# PR Review

## 1. Overall Understanding

## 2. Review Contract

## 3. Change and Execution Map

## 4. What Looks Strong

## 5. Blocking Findings

## 6. Important Findings

## 7. Questions and Unverified Hypotheses

## 8. Suggestions

## 9. Testing and Evaluation Assessment

## 10. Definition of Done Assessment

## 11. Source-System Summary

### Subagent Dispatch

- A (Intent, Correctness & Testing): dispatched / completed | failed after retries
- B (Reliability & Operations): dispatched / completed | failed after retries
- C (Security, Privacy & Data): dispatched / completed | failed after retries
- D (Architecture & Documentation): dispatched / completed | failed after retries
- E (Agent Runtime & Tooling): dispatched | skipped (Agent-System Extension not active) / completed | failed after retries
- F (Accountability & Safeguards): dispatched | skipped (Agent-System Extension not active) / completed | failed after retries
- G (SANYI): dispatched | skipped (no SANYI.md) / completed | failed after retries

### SANYI

- contract found:
- review invoked:
- source verdict:
- findings imported:

## 12. Suggested Merge Decision

approve | comment | request_changes | insufficient_context
```
````

`.claude/skills/parallax-shared/templates/github-comment.md`:

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

`.claude/skills/parallax-shared/templates/interview-walkthrough.md`:

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

- [ ] **Step 2: Verify structure**

```bash
ls .claude/skills/parallax-shared/templates/
```

Expected: exactly the four files listed above.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/parallax-shared/templates/
git commit -m "feat: add parallax-shared report/interview/comment templates"
```

---

### Task 5: Create the seven subagent agent definitions

**Files:**

- Create: `.claude/agents/intent-correctness.md`
- Create: `.claude/agents/reliability-operations.md`
- Create: `.claude/agents/security-privacy-data.md`
- Create: `.claude/agents/architecture-docs.md`
- Create: `.claude/agents/agent-runtime-tooling.md`
- Create: `.claude/agents/accountability-safeguards.md`
- Create: `.claude/agents/sanyi-review.md`

**Interfaces:**

- Consumes: the seven skills from Tasks 1–3 (`intent-correctness`, `reliability-operations`, `security-privacy-data`, `architecture-docs`, `agent-runtime-tooling`, `accountability-safeguards`, `sanyi`) and `parallax-shared` — every `skills:` field below must name a skill that exists after Tasks 1–4.
- Produces: seven named agents (`intent-correctness-review`, `reliability-operations-review`, `security-privacy-data-review`, `architecture-docs-review`, `agent-runtime-tooling-review`, `accountability-safeguards-review`, `sanyi-review`), dispatched by name from Task 6's orchestrator.

- [ ] **Step 1: Create `intent-correctness.md`**

```yaml
---
name: intent-correctness-review
description: >
  Reviews PR intent, correctness/contracts (including cross-usage schema
  consistency), and test coverage. One of Parallax's parallel review
  subagents — dispatched on every PR.
skills:
  - intent-correctness
  - parallax-shared
tools:
  - Read
  - Grep
  - Glob
  - Bash
---
Apply the intent-correctness skill's checklist to the diff described in the
context brief you were given. Return findings in the canonical schema
(parent spec Section 11).

If you notice agent-system signals (LLM SDK imports, prompt files, agent
framework code, etc.) not already accounted for, flag this explicitly in
your returned output rather than staying silent because it's outside your
assigned dimension — the orchestrator may dispatch Subagents E and F as a
corrective follow-up (parent spec Section 16.6).
```

Save as `.claude/agents/intent-correctness.md`.

- [ ] **Step 2: Create `reliability-operations.md`**

```yaml
---
name: reliability-operations-review
description: >
  Reviews reliability (retries, idempotency, partial failure, recovery) and
  operational readiness (logging, rollout, rollback). One of Parallax's
  parallel review subagents — dispatched on every PR.
skills:
  - reliability-operations
  - parallax-shared
tools:
  - Read
  - Grep
  - Glob
  - Bash
---
Apply the reliability-operations skill's checklist to the diff described in
the context brief you were given. Return findings in the canonical schema
(parent spec Section 11).

If you notice agent-system signals (LLM SDK imports, prompt files, agent
framework code, etc.) not already accounted for, flag this explicitly in
your returned output rather than staying silent because it's outside your
assigned dimension — the orchestrator may dispatch Subagents E and F as a
corrective follow-up (parent spec Section 16.6).
```

Save as `.claude/agents/reliability-operations.md`.

- [ ] **Step 3: Create `security-privacy-data.md`**

```yaml
---
name: security-privacy-data-review
description: >
  Reviews security, privacy, and data/state handling (authn/authz, PII,
  secrets, validation, provenance, migration). One of Parallax's parallel
  review subagents — dispatched on every PR.
skills:
  - security-privacy-data
  - parallax-shared
tools:
  - Read
  - Grep
  - Glob
  - Bash
---
Apply the security-privacy-data skill's checklist to the diff described in
the context brief you were given. Return findings in the canonical schema
(parent spec Section 11).

If you notice agent-system signals (LLM SDK imports, prompt files, agent
framework code, etc.) not already accounted for, flag this explicitly in
your returned output rather than staying silent because it's outside your
assigned dimension — the orchestrator may dispatch Subagents E and F as a
corrective follow-up (parent spec Section 16.6).
```

Save as `.claude/agents/security-privacy-data.md`.

- [ ] **Step 4: Create `architecture-docs.md`**

```yaml
---
name: architecture-docs-review
description: >
  Reviews architecture/maintainability and documentation accuracy
  (docs-vs-code drift, stale paths and capability claims). One of
  Parallax's parallel review subagents — dispatched on every PR.
skills:
  - architecture-docs
  - parallax-shared
tools:
  - Read
  - Grep
  - Glob
  - Bash
---
Apply the architecture-docs skill's checklist to the diff described in the
context brief you were given. Return findings in the canonical schema
(parent spec Section 11).

If you notice agent-system signals (LLM SDK imports, prompt files, agent
framework code, etc.) not already accounted for, flag this explicitly in
your returned output rather than staying silent because it's outside your
assigned dimension — the orchestrator may dispatch Subagents E and F as a
corrective follow-up (parent spec Section 16.6).
```

Save as `.claude/agents/architecture-docs.md`.

- [ ] **Step 5: Create `agent-runtime-tooling.md`**

```yaml
---
name: agent-runtime-tooling-review
description: >
  Reviews agent-system runtime behavior — tool side effects, workflow
  state/partial failure, retrieval boundaries, and memory write-back. One
  of Parallax's parallel review subagents — dispatched only when the
  Agent-System Extension is active.
skills:
  - agent-runtime-tooling
  - parallax-shared
tools:
  - Read
  - Grep
  - Glob
  - Bash
---
Apply the agent-runtime-tooling skill's checklist to the diff described in
the context brief you were given. Return findings in the canonical schema
(parent spec Section 11).
```

Save as `.claude/agents/agent-runtime-tooling.md`. (No agent-system-signal
flagging instruction here — this subagent already is one of the
agent-system ones.)

- [ ] **Step 6: Create `accountability-safeguards.md`**

```yaml
---
name: accountability-safeguards-review
description: >
  Reviews evaluation rigor, human-responsibility/escalation paths, and
  whether documented safeguards have real deterministic backing. Feeds
  candidate SANYI.md entries when it finds undeclared invariants. One of
  Parallax's parallel review subagents — dispatched only when the
  Agent-System Extension is active.
skills:
  - accountability-safeguards
  - parallax-shared
tools:
  - Read
  - Grep
  - Glob
  - Bash
---
Apply the accountability-safeguards skill's checklist to the diff described
in the context brief you were given. Return findings in the canonical
schema (parent spec Section 11). If you find an undeclared safeguard gap,
flag it as a SANYI.md candidate (parent spec Section 19.7) — describe the
gap clearly, but do not attempt to draft SANYI.md syntax yourself; you do
not have SANYI's contract format preloaded. The orchestrator will route
this to Subagent G in a follow-up dispatch if `SANYI.md` exists.
```

Save as `.claude/agents/accountability-safeguards.md`.

- [ ] **Step 7: Create `sanyi-review.md`**

```yaml
---
name: sanyi-review
description: >
  Applies SANYI's change-contract taxonomy to the diff. One of Parallax's
  parallel review subagents — dispatched only when SANYI.md exists in the
  target repo.
skills:
  - sanyi
  - parallax-shared
tools:
  - Read
  - Grep
  - Glob
  - Bash
---
Apply sanyi's preloaded taxonomy to the diff described in the context brief
you were given, exactly as SANYI's own review mode would (parent spec
Section 17.1). Return findings in the canonical schema (parent spec Section
11), preserving SANYI's native codes and severities without inventing or
rewriting them.

If the orchestrator routes you a follow-up request containing Subagent F's
Documented Safeguards finding (parent spec Section 19.7), draft a
properly-formatted candidate `SANYI.md` Buyi or Pending entry for it, using
your preloaded SANYI contract format. This draft is a recommendation only —
never write it into `SANYI.md` yourself; that requires explicit human
approval (parent spec Section 24).
```

Save as `.claude/agents/sanyi-review.md`.

- [ ] **Step 8: Verify structure**

```bash
for f in intent-correctness reliability-operations security-privacy-data architecture-docs agent-runtime-tooling accountability-safeguards; do
  echo "=== $f.md ==="
  grep "^skills:" -A2 ".claude/agents/$f.md"
done
grep "^skills:" -A2 .claude/agents/sanyi-review.md
```

Expected: every one of the six dimension-subagent files lists its own
dimension skill and `parallax-shared` under `skills:`; `sanyi-review.md`
lists `sanyi` and `parallax-shared`.

- [ ] **Step 9: Commit**

```bash
git add .claude/agents/
git commit -m "feat: add seven Parallax review subagents"
```

---

### Task 6: Create the `parallax` orchestrator agent

**Files:**

- Create: `.claude/agents/parallax.md`

**Interfaces:**

- Consumes: `parallax-shared` (Task 3–4) via `skills:`, and dispatches the seven named subagents from Task 5 by name (not via `skills:` preloading — the orchestrator does not preload their skills itself).
- Produces: the entry point a human invokes to run a full Parallax review.

- [ ] **Step 1: Create `parallax.md`**

```yaml
---
name: parallax
description: >
  Evidence-driven PR review orchestrator. Dispatches parallel subagents
  for each applicable review dimension, then merges, deduplicates, and
  produces one unified report. Use for reviewing PRs, diffs, or
  merge-readiness questions.
skills:
  - parallax-shared
tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Agent
---

# Parallax Orchestrator

You coordinate Parallax's evidence-driven PR review. You do not review
code yourself — you dispatch subagents that do, then merge their results.

## Stage 0 — Establish Review Contract

Ask the human directly whether this is a general software PR or an
agent-system PR if it isn't already obvious or stated (this is the
preferred, most reliable way to activate the Agent-System Extension —
simpler than waiting on automatic signal detection). Fill in
`templates/context-brief.md`'s Review Contract section from: PR title,
PR description, linked issue, design doc, user instructions, repository
instructions, current branch, base branch, time budget, and the stated
(or to-be-detected) review profile.

Missing context is not a code defect — record it as "unknown," don't guess.

## Stage 1–2 — Collect Context and Build Change Map

Fill in the rest of `templates/context-brief.md` (Repository Context,
Change Map) exactly once. This brief is what every dispatched subagent
receives — they must not re-derive it themselves.

## Dispatch

Always dispatch, in parallel, with the context brief:

- `intent-correctness-review`
- `reliability-operations-review`
- `security-privacy-data-review`
- `architecture-docs-review`

If the review profile is agent-system (explicitly stated, or detected from
high-confidence signals — LLM SDK imports, agent framework imports,
prompt files, tool schemas, MCP, retrieval, vector database, memory,
workflow orchestration, graders, eval scenarios, model configuration,
human-agent handoffs, agent traces), also dispatch:

- `agent-runtime-tooling-review`
- `accountability-safeguards-review`

If `SANYI.md` exists in the target repository, also dispatch:

- `sanyi-review`

### Partial-failure handling

There is no per-subagent wall-clock timer you can enforce. If a dispatched
subagent does not return output that validates against the canonical
schema — errored, or returned something malformed — retry it up to two
times. If it still fails, proceed without it; record this in the report's
Subagent Dispatch section (`templates/review-report.md`) rather than
silently omitting the gap.

### Corrective follow-up dispatch

If any always-dispatched subagent (`intent-correctness-review`,
`reliability-operations-review`, `security-privacy-data-review`,
`architecture-docs-review`) flags agent-system signals in its returned
output that Stage 0's detection missed, and `agent-runtime-tooling-review`
/ `accountability-safeguards-review` were not already dispatched, dispatch
them now as a corrective follow-up round.

If `accountability-safeguards-review` flags an undeclared safeguard gap
and `SANYI.md` exists, dispatch `sanyi-review` (if not already dispatched)
as a follow-up with that finding as input, asking it to draft a
properly-formatted candidate `SANYI.md` entry. Never write the draft into
`SANYI.md` yourself without explicit human approval.

## Merge (Stage 7)

Every subagent returns findings in the canonical schema with its own
`PR-<letter>-NNN` ID prefix.

1. Deterministic pre-filter: group findings whose file paths and line
   ranges overlap, and whose `lens.category` matches (or whose
   `location.symbols` overlap).
2. Within each such cluster, judge whether the findings are actually the
   same underlying issue or merely touch the same code for unrelated
   reasons. Only merge if they're the same issue.
3. When merged, preserve all source references, use the most precise
   root-cause description, retain SANYI contract semantics if present, and
   assign merge impact and communication yourself.

## Stages 8–10

Assess Definition of Done (`references/definition-of-done.md`), then
produce the unified report (`templates/review-report.md`), and — only if
interview mode is active — the interview walkthrough
(`templates/interview-walkthrough.md`).

## Safety

Default to read-only (`references/communication-and-handoff.md`). Do not
edit files, apply patches, run `SANYI --fix`, commit, push, post GitHub
comments, approve, request changes, delete files, modify configuration, or
write a SANYI.md candidate entry, unless the user explicitly authorizes it.
```

Save as `.claude/agents/parallax.md`.

- [ ] **Step 2: Verify structure**

```bash
grep "^skills:" -A1 .claude/agents/parallax.md
grep "^name: parallax$" .claude/agents/parallax.md
```

Expected: `skills:` lists only `parallax-shared`; `name:` is exactly `parallax`.

- [ ] **Step 3: Verify every dispatched name resolves to a real agent**

```bash
for n in intent-correctness-review reliability-operations-review security-privacy-data-review architecture-docs-review agent-runtime-tooling-review accountability-safeguards-review sanyi-review; do
  grep -l "^name: $n$" .claude/agents/*.md || echo "MISSING: $n"
done
```

Expected: every name is found in exactly one file; no `MISSING` lines.

- [ ] **Step 4: Commit**

```bash
git add .claude/agents/parallax.md
git commit -m "feat: add parallax orchestrator agent"
```

---

## Self-Review

**Spec coverage:**

- SANYI vendoring by copy (not submodule), with provenance comment → Task 1 (spec Section 33.12).
- Six dimension skills, content matching companion doc Section 3 verbatim → Task 2.
- `parallax-shared` skill: evidence model, severity/decision, DoD, communication, interview mode → Task 3 (spec Sections 20/21/22/23/24, companion doc Section 33.11).
- `parallax-shared` templates: context brief, review report (with Subagent Dispatch section), GitHub comment, interview walkthrough → Task 4 (spec Sections 10, 22, 23).
- Seven subagent agent files, each `skills:` = [own skill, parallax-shared] (or [sanyi, parallax-shared]), agent-system-signal flagging on A–D, SANYI-candidate handoff on F and G → Task 5 (spec Sections 4.4, 16.6, 19.7, companion doc Section 3).
- Orchestrator: Stage 0 explicit profile question, conditional dispatch, partial-failure retry-twice, corrective follow-up dispatch (missed detection and SANYI-candidate draft), two-pass dedup, safety defaults → Task 6 (spec Sections 9.2, 10, 13, 16.1–16.6, 24).
- All locations under `.claude/skills/` and `.claude/agents/` per the discovery-path finding → Global Constraints + every task.

**Placeholder scan:** no TBD/TODO markers; every file's complete content is given inline in its task.

**Type/name consistency:** every `skills:` reference in Tasks 5–6 names a skill actually created in Tasks 1–4; every agent name Task 6 dispatches is created in Task 5. Checked via Task 6 Step 3's verification loop.
