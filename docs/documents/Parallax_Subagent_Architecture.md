# Parallax Subagent Architecture

## 0. Purpose and Scope

This is the detailed companion to `Evidence_Driven_PR_Review_System_Spec.md`
Section 16 ("Parallax Agent"). That section stays a short overview; this
document carries the full breakdown of how Section 18 (General Review
Dimensions) and Section 19 (Agent-System Decision Dimensions) are
distributed across parallel subagents, and exactly which skill each
subagent preloads.

Kept separate on purpose: an implementation session working on one
subagent's skill only needs this document plus that subagent's own section
below — not the entire parent spec (problem statement, schema design,
testing strategy, evaluation metrics, etc.) that has nothing to do with that
task. This mirrors the same "load on demand" discipline SANYI itself uses
for its `references/*.md` files.

Every dimension bullet below is reproduced **verbatim** from the parent
spec's Section 18/19 — nothing here should be treated as a paraphrase or a
replacement for the parent spec. If the two ever disagree, the parent
spec's Section 18/19 is the source of truth for dimension _content_; this
document is the source of truth for dimension _assignment_ (which subagent
owns which dimension).

Each subagent A–G is backed by **two separate files**, not one, both under
`.claude/` — the only location Claude Code actually discovers skills and
agents from (Section 5; parent spec Section 33.12):

- `.claude/skills/<name>/SKILL.md` — the skill itself: the dimension
  checklist and instructions, with `allowed-tools` frontmatter. This is
  knowledge/content, and could in principle be invoked by anything.
- `.claude/agents/<name>.md` — the subagent that actually runs: `tools`
  (its own tool access) plus `skills: [<name>]`, the field that preloads
  the skill's full content into this subagent's context at startup
  (Section 4.4 of the parent spec). This is the file that makes preloading
  actually happen — without it, the skill is just a file nobody preloads.

An earlier version of this document only showed one YAML block per
subagent, style-matching neither file consistently and never actually
demonstrating the `skills:` field for A–F (only G had it). That was a real
gap: the one mechanism the whole design is built around (Section 4.4,
33.2, 33.3 of the parent spec) was undemonstrated for six of the seven
subagents. Fixed below — every subagent now shows both files.

This follows Claude Code's own skill-authoring guidance — progressive
disclosure: keep `SKILL.md` concise (well under the ~500-line guideline),
with detailed reference material split into `references/` and data files
into what the open standard calls `assets/`. The two skill types here sit
at opposite ends of that guidance:

- Each **dimension skill**'s `SKILL.md` body is exactly its "Owns"
  checklist reproduced in Section 3 below — a handful of bullets per
  dimension, short enough that no internal `references/` split is needed.
- **`parallax-shared`** (Section 5) is the opposite case: it bundles five
  distinct reference topics plus report templates, so it gets its own
  `references/` and `templates/` subfolders — `templates/` here is
  Parallax's more specific name for what the standard calls `assets/`
  (data files, not necessarily images) — mirroring SANYI's own
  `SKILL.md` + `references/*.md` structure rather than being one flat
  file.

---

## 1. Orchestration Model

```text
parallax (orchestrator)
  │
  ├─ Stage 0–2 (once): review contract, context, change map
  │    → produces context-brief.md, passed to every dispatched subagent
  │
  ├─ dispatch (parallel, per Section 2 below):
  │    A  Intent, Correctness & Testing        (always)
  │    B  Reliability & Operations             (always)
  │    C  Security, Privacy & Data             (always)
  │    D  Architecture & Documentation         (always)
  │    E  Agent Runtime & Tooling              (if Agent-System Extension triggers)
  │    F  Accountability & Safeguards          (if Agent-System Extension triggers)
  │    G  SANYI                                (if SANYI.md exists)
  │
  ├─ each subagent returns findings pre-formatted in the canonical schema
  │    (Section 11 of the parent spec)
  │
  └─ Stage 6–10 (once, in the orchestrator): evidence verification,
       deduplication, prioritization, Definition of Done, unified report,
       interview mode
```

The orchestrator does the context-gathering and the final synthesis exactly
once. Subagents never re-derive "what is this diff" independently — they
receive the context brief and work only within their assigned dimensions.

---

## 2. Dispatch Rules

- **A, B, C, D** are dispatched on every review (General Profile, Section
  9.1 of the parent spec — always active).
- **E, F** are dispatched only when the parent spec's Section 9.2
  (Agent-System Extension) triggers. If it doesn't trigger, these two are
  not dispatched at all — not dispatched-and-return-empty.
- **G** is dispatched only when `SANYI.md` exists in the target repo
  (parent spec Section 17.1). If it doesn't exist, G is not dispatched;
  the orchestrator may still recommend `/sanyi init` per Section 17.2,
  particularly if F's Documented Safeguards check (19.7) surfaces an
  undeclared invariant.

---

## 3. Subagent Definitions

### Subagent A — Intent, Correctness & Testing

**Rationale:** you cannot judge correctness without understanding intent,
and tests are the evidence for correctness claims — one reviewer mental
model: "does it work, and is that proven?"

**Owns — 18.1 Intent and Product Behavior:**

- Does the PR solve the intended problem?
- Is user-visible behavior clear?
- Is the scope appropriate?
- Does it solve the cause or only the symptom?
- Is the implementation unnecessarily complex?

**Owns — 18.2 Correctness and Contracts:**

- Inputs;
- outputs;
- schemas;
- state transitions;
- invariants;
- edge cases;
- ordering;
- concurrency;
- compatibility;
- cross-usage consistency: when the diff modifies a shared schema/type,
  check all of its usages across the repo, not only the diff's own callers.

**Owns — 18.8 Testing:**

- unit;
- integration;
- contract;
- regression;
- end-to-end;
- negative paths;
- useful assertions;
- failure-before-fix evidence.

```yaml
# .claude/skills/intent-correctness/SKILL.md
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
```

```yaml
# .claude/agents/intent-correctness.md
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

---

### Subagent B — Reliability & Operations

**Rationale:** same failure-mode lens — "what breaks, and how does it
recover or roll back?" — whether the break happens at runtime (Reliability)
or at deploy/rollout time (Operations).

**Owns — 18.3 Reliability:**

- retries;
- timeouts;
- idempotency;
- partial failures;
- fallback;
- cancellation;
- recovery;
- cleanup;
- consistency.

**Owns — 18.9 Operations and Delivery:**

- logging;
- metrics;
- tracing;
- deployment;
- rollout;
- rollback;
- migration;
- documentation;
- handoff.

```yaml
# .claude/skills/reliability-operations/SKILL.md
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
```

```yaml
# .claude/agents/reliability-operations.md
---
name: reliability-operations-review
description: >
  Reviews reliability and operational readiness. One of Parallax's parallel
  review subagents — dispatched on every PR.
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

---

### Subagent C — Security, Privacy & Data

**Rationale:** trust-boundary lens — what's allowed to read, write, or
persist, and what's exposed.

**Owns — 18.4 Security and Privacy:**

- authn;
- authz;
- tenant isolation;
- PII;
- secrets;
- injection;
- unsafe writes;
- auditability.

**Owns — 18.5 Data and State:**

- validation;
- provenance;
- migration;
- serialization;
- stale data;
- duplicated state;
- source of truth.

```yaml
# .claude/skills/security-privacy-data/SKILL.md
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
```

```yaml
# .claude/agents/security-privacy-data.md
---
name: security-privacy-data-review
description: >
  Reviews security, privacy, and data/state handling. One of Parallax's
  parallel review subagents — dispatched on every PR.
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

---

### Subagent D — Architecture & Documentation

**Rationale:** zoomed-out system-coherence lens, distinct from "does this
diff work" — does the system's structure and its own self-description stay
coherent over time.

**Owns — 18.6 Architecture and Maintainability:**

- boundaries;
- dependency direction;
- coupling;
- abstraction;
- duplication;
- evolution;
- rollback;
- long-term contract.

**Owns — 18.7 Documentation Accuracy:**

- Do existing docs (`CLAUDE.md`, `README.md`, architecture docs, any
  capability/status tables the project maintains) still describe the code
  accurately after this diff?
- Do file paths, module references, or capability claims in project docs
  still resolve to something real?
- This is distinct from the parent spec's Section 21 Definition-of-Done
  check ("did this diff update its own docs") — it catches pre-existing or
  diff-introduced drift between docs and code, not just missing updates for
  the current change.

```yaml
# .claude/skills/architecture-docs/SKILL.md
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
```

```yaml
# .claude/agents/architecture-docs.md
---
name: architecture-docs-review
description: >
  Reviews architecture/maintainability and documentation accuracy. One of
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

---

### Subagent E — Agent Runtime & Tooling

**Dispatch condition:** only when the Agent-System Extension triggers
(parent spec Section 9.2).

**Rationale:** all four dimensions are about how the agent actually
executes at runtime — tool calls, graph state, retrieval, and memory are
different facets of the same "what does this agent do when it runs"
question.

**Owns — 19.1 Tool Side Effects:**

- Is the tool read-only or write-capable?
- Is confirmation required?
- Is retry safe?
- Is idempotency guaranteed?
- Is output validated?
- Are permissions enforced at the tool boundary?

**Owns — 19.2 Workflow State and Partial Failure:**

- Is the graph bounded?
- Can it terminate?
- Can it resume?
- What happens after partial success?
- Are handoffs explicit?
- Is deterministic code used where appropriate?

**Owns — 19.3 Retrieval and Context:**

- Is retrieval scoped correctly?
- Is provenance preserved?
- Are permissions respected?
- Is stale or conflicting context handled?
- Can external content influence a sensitive sink? (prompt injection via
  retrieved or external content is the named threat class here.)

**Owns — 19.4 Memory Write-Back:**

- What is persisted?
- Is it fact, inference, or model output?
- Can it be corrected?
- Is confidence stored?
- Is approval required?
- Can bad runs contaminate future cases?

```yaml
# .claude/skills/agent-runtime-tooling/SKILL.md
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
```

```yaml
# .claude/agents/agent-runtime-tooling.md
---
name: agent-runtime-tooling-review
description: >
  Reviews agent-system runtime behavior. One of Parallax's parallel review
  subagents — dispatched only when the Agent-System Extension is active.
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

---

### Subagent F — Accountability & Safeguards

**Dispatch condition:** only when the Agent-System Extension triggers
(parent spec Section 9.2).

**Rationale:** all three dimensions are about whether a check-and-balance
exists and is real — Evaluation is the automated check, Human
Responsibility is the manual one, Documented Safeguards verifies that
claimed checks actually have code behind them. This is also the subagent
most likely to produce candidate SANYI entries, so keeping its output as
one focused stream makes that hand-off easy to wire up.

**Owns — 19.5 Evaluation:**

- Is one successful run being overvalued?
- Are repeated runs needed?
- Is there a baseline?
- Are deterministic graders possible?
- Is an LLM judge calibrated?
- Are trace and final output both evaluated?
- Are cost and latency considered?

**Owns — 19.6 Human Responsibility:**

- Who approves?
- Who is accountable?
- Can a human take over?
- Is uncertainty visible?
- Is escalation available?

**Owns — 19.7 Documented Safeguards:**

- Does documentation, a system prompt, or configuration claim a
  safety/guardrail behavior exists (an escalation path, an input/output
  validation layer, a confidence gate)?
- Is that claim backed by an actual deterministic code path, or does it
  exist only as a sentence in a prompt?
- If a gap is found and no SANYI contract already governs it, recommend
  recording it as a candidate `SANYI.md` Buyi or Pending entry (parent spec
  Section 17.2) rather than treating it as a standalone PR Review finding
  — this is the same failure mode SANYI's BY-4 targets, applied proactively
  to invariants nobody has declared yet.

```yaml
# .claude/skills/accountability-safeguards/SKILL.md
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
```

```yaml
# .claude/agents/accountability-safeguards.md
---
name: accountability-safeguards-review
description: >
  Reviews evaluation rigor, human responsibility, and documented
  safeguards; feeds candidate SANYI.md entries when it finds undeclared
  invariants. One of Parallax's parallel review subagents — dispatched
  only when the Agent-System Extension is active.
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

---

### Subagent G — SANYI

**Dispatch condition:** only when `SANYI.md` exists in the target repo.

**Rationale:** independent origin, external repo, its own violation
taxonomy — the one subagent whose entire role is a single external skill,
unlike A–F which each bundle a thematic group of Parallax-native
dimensions. `sanyi`'s `SKILL.md` and `references/*.md` are copied directly
into `.claude/skills/sanyi/` (Section 5; parent spec Section 33.12) rather
than linked as a submodule — Claude Code only discovers skills under
`.claude/skills/`, and SANYI is not expected to keep changing, so a plain
copy (with its source commit noted) is simpler than the plugin or symlink
machinery a submodule would otherwise need.

**Owns:** SANYI's full taxonomy (`BY-1`–`BY-4`, `JY-1`–`JY-3`, `BN-1`,
`MG-1`, `UN-1`, `UN-2`) as specified in the parent spec's Section 3 and
`SANYI/references/violations.md`. Nothing is duplicated here — see the
parent spec's Section 17 (SANYI Integration Rules) for the rules this
subagent follows.

```yaml
# .claude/agents/sanyi-review.md
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

---

## 4. Merge and Deduplication

Every subagent returns findings already in the canonical schema (parent
spec Section 11), with its own `PR-<letter>-NNN` ID prefix (parent spec
Section 13.4) — e.g. Subagent B's findings are `PR-B-001`, `PR-B-002`, …,
never colliding with Subagent G's `PR-G-001`.

The orchestrator's Stage 7 (Deduplicate and Prioritize) is where
cross-subagent overlap gets reconciled, in two passes (parent spec Section
13.1–13.2): a deterministic pre-filter clusters findings by file/line-range
overlap and category/symbol match, then the orchestrator makes a bounded
semantic judgment only within each small cluster — e.g. deciding whether a
Reliability finding from B and a SANYI `JY-2` from G on the same lines are
actually the same root cause or two unrelated issues that happen to touch
the same code. This was already anticipated by the parent spec's Section 13
Deduplication Strategy; parallel dispatch makes it load-bearing rather than
an edge case, since overlapping findings are now genuinely produced by
independent concurrent processes instead of sequential passes within one
agent.

---

## 5. Repository Structure Addendum

This is what the parent spec's Section 15 tree points to instead of a
single skill: one skill + one agent per subagent (G's skill, `sanyi`, is
copied in from SANYI's own repo rather than authored here), plus
`parallax-shared` for cross-cutting references — everything under
`.claude/`, the only location Claude Code discovers skills and agents from:

```text
Parallax/
└── .claude/                             # only location Claude Code discovers skills/agents from
    ├── skills/
    │   ├── intent-correctness/
    │   │   └── SKILL.md
    │   ├── reliability-operations/
    │   │   └── SKILL.md
    │   ├── security-privacy-data/
    │   │   └── SKILL.md
    │   ├── architecture-docs/
    │   │   └── SKILL.md
    │   ├── agent-runtime-tooling/
    │   │   └── SKILL.md
    │   ├── accountability-safeguards/
    │   │   └── SKILL.md
    │   ├── parallax-shared/
    │   │   ├── SKILL.md             # operational summary + index, SANYI-style
    │   │   ├── references/
    │   │   │   ├── evidence-model.md
    │   │   │   ├── severity-and-decision.md
    │   │   │   ├── communication-and-handoff.md
    │   │   │   ├── definition-of-done.md
    │   │   │   └── interview-mode.md
    │   │   └── templates/
    │   │       ├── context-brief.md
    │   │       ├── review-report.md
    │   │       ├── github-comment.md
    │   │       └── interview-walkthrough.md
    │   └── sanyi/                    # copied from SANYI's repo, not a submodule (Section 33.12)
    │       ├── SKILL.md
    │       └── references/
    │           └── ...
    └── agents/
        ├── parallax.md                  # orchestrator — skills: [parallax-shared]
        ├── intent-correctness.md        # skills: [intent-correctness, parallax-shared]
        ├── reliability-operations.md    # skills: [reliability-operations, parallax-shared]
        ├── security-privacy-data.md     # skills: [security-privacy-data, parallax-shared]
        ├── architecture-docs.md         # skills: [architecture-docs, parallax-shared]
        ├── agent-runtime-tooling.md     # skills: [agent-runtime-tooling, parallax-shared]
        ├── accountability-safeguards.md # skills: [accountability-safeguards, parallax-shared]
        └── sanyi-review.md              # skills: [sanyi, parallax-shared]
```

`parallax-shared` is a real skill, not a loose folder — structured the same
way SANYI itself is (a top-level `SKILL.md` plus `references/*.md` loaded
on demand). It holds the cross-cutting rules every subagent and the
orchestrator need — evidence model, severity/decision rules, communication
format, DoD, interview mode, report templates — and every one of A–G plus
the orchestrator preloads it via `skills:`, alongside its own
dimension-specific (or SANYI) skill. An earlier version left this content
in an unpackaged `shared/` folder with no preload mechanism, relying on
each subagent's own prose to remember to go read it — exactly the
unreliable "soft suggestion" pattern Section 4.4 rejected for SANYI. Fixed
by giving it the same `skills:` treatment as everything else (parent spec
Section 33.11).
