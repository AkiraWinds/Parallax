# Evidence-Driven PR Review System Specification

## 0. Document Purpose

This document specifies the design and implementation of a new evidence-driven PR review system that composes two distinct capabilities:

1. **PR Review methodology** — the governing review stages, dimensions, evidence model, and merge-decision framework, implemented across per-dimension skills and subagents (Section 16).
2. **SANYI** — an existing change-contract system for agent architectures.

The system must support two review profiles:

- **General PR Review** for any software repository.
- **Agent-System PR Review** for repositories or pull requests involving LLMs, agents, prompts, tools, retrieval, memory, workflows, graders, evaluations, or human-agent handoffs.

The central design requirement is that SANYI remains an independent system with its own native schema and lifecycle. The new PR Review system must integrate it through a mapping layer rather than rewriting or duplicating its internals. Where composition needs to be _guaranteed_ rather than left to a runtime judgment call, the system dispatches parallel subagents (Section 16; full breakdown in `Parallax_Subagent_Architecture.md`), each preloading exactly the skill relevant to its own role via Claude Code's `skills:` mechanism, instead of relying on one skill's prose to instruct the model to invoke another. SANYI is preloaded by one such subagent (Subagent G), not by a single agent that preloads everything.

This document is intended for a coding agent implementing the system from scratch.

---

## 1. Executive Summary

We are building an **evidence-driven PR review system** that helps a human reviewer answer:

> Is this specific change understood, sufficiently validated, safe, maintainable, and ready to merge?

The system must not optimize for the largest number of comments. It must instead:

- reconstruct the intent and scope of the PR;
- understand the execution and change path;
- identify material software-engineering risks;
- conditionally apply agent-system-specific review, including documentation-accuracy, cross-usage schema consistency, and documented-safeguard checks;
- consume SANYI findings when a change contract exists;
- verify findings with evidence;
- distinguish verified facts from hypotheses and questions;
- prioritize findings by merge impact;
- assess Definition of Done;
- produce a unified review report;
- support interview walkthrough mode;
- preserve human responsibility for the final decision.

The design is based on three layers:

```text
SANYI
  → enforces explicit architecture change contracts

PR Review methodology
  → governs the end-to-end review process, general and agent-system dimensions, and merge decision (Sections 18–19, 21–24)

Parallax
  → orchestrator + parallel subagents (Section 16) that apply the methodology and SANYI together, guaranteed by skill-preloading, not inferred
```

The intended philosophy is:

> SANYI checks what was allowed to change.
> PR Review decides whether the change is ready.

---

## 2. Problem Statement

Existing PR review automation often fails in one of two ways.

The first failure mode is **surface-level review**. The system produces comments about naming, formatting, local code smells, or generic best practices but fails to understand:

- why the change exists;
- the actual behavioral change;
- the blast radius;
- side effects;
- retries and partial failures;
- product implications;
- operational readiness;
- agent-specific failure modes;
- long-term architecture contracts.

The second failure mode is **schema and responsibility collapse**. Multiple tools are combined into one large reviewer, and each tool's domain-specific semantics are flattened into a generic issue list. This creates duplication, loss of provenance, inconsistent severity, and unclear ownership.

The new system must avoid both.

It must preserve specialized systems while providing a coherent review experience.

---

## 3. Existing System: SANYI

SANYI is an existing change-contract system for agent architectures.

It classifies architecture into three change layers:

- **Bianyi** — expected to change cheaply;
- **Jianyi** — expected to remain simple and bounded;
- **Buyi** — invariant, safety-critical, or trust-critical.

The contract is stored in `SANYI.md`.

SANYI supports:

- `/sanyi init`;
- `/sanyi review`;
- `/sanyi review --fix`;
- `/sanyi audit`.

SANYI emits domain-specific codes such as:

- `BY-1` to `BY-4`;
- `JY-1` to `JY-3`;
- `BN-1`;
- `MG-1`;
- `UN-1`;
- `UN-2`.

SANYI also contains:

- debt baselines;
- pending entries;
- migrations;
- contract matching;
- current-value refresh;
- audit behavior;
- strict rules for Buyi invariants.

SANYI's primary question is:

> Does this diff violate an explicit architectural change contract or silently move a boundary?

SANYI is not a general PR reviewer and must not be used as one.

---

## 4. Key Design Decisions

### 4.1 Do not modify SANYI's schema

The first implementation must preserve SANYI's native output — its violation taxonomy, severities, and report structure.

Reasons:

1. **It encodes domain-specific semantics.**
   `BY-2` is not simply "high severity." It means a specific Buyi invariant became bypassable.

2. **Independent lifecycle matters.**
   SANYI should remain useful outside PR Review.

3. **Mapping is cheaper and safer than rewriting.**
   Integration concerns belong in the integration layer, not inside SANYI itself.

The system therefore uses:

```text
Native SANYI taxonomy
        ↓
SANYI-aware mapping
        ↓
Canonical PR Review integration schema
```

### 4.2 Build one PR Review methodology with two profiles

Do not build separate unrelated skills for general PR review and agent-system PR review.

Use:

```text
General Review Core
        +
Conditional Agent-System Extension
```

Every PR receives the general review.

The agent-system extension is loaded when:

- explicitly requested; or
- the repository or PR contains relevant signals.

### 4.3 The PR Review methodology governs the process

The PR Review methodology owns:

- stages;
- review contract;
- general review;
- agent-change decision lens;
- evidence requirements;
- canonical finding schema;
- severity and merge impact;
- Definition of Done;
- communication;
- final report;
- interview walkthrough.

SANYI does not own the final output.

### 4.4 Guaranteed composition via Agent skill-preloading, not runtime invocation

A Skill's own instructions cannot reliably guarantee that another Skill gets applied — whether a nested invocation actually happens depends on the model choosing, at runtime, to comply with prose telling it to call a second skill. That is a soft suggestion, not a harness-level guarantee.

Claude Code's subagent `skills:` frontmatter field is a different mechanism: it injects the full content of every listed skill into the subagent's context at startup. The ruleset is already part of the subagent's own operating instructions before it starts working — there is no separate "decide whether to invoke" step.

Parallax uses this for every review dimension, not only SANYI: rather than one large agent preloading every skill and applying all dimensions sequentially in one growing context, the `parallax` orchestrator dispatches multiple parallel subagents, each preloading exactly the one skill relevant to its narrow role (Section 16; full breakdown in `Parallax_Subagent_Architecture.md`). The `sanyi` subagent is one instance of this same pattern, dispatched only when `SANYI.md` exists.

This makes "the right ruleset is applied when needed" a property of each subagent's static configuration, not of the model's in-the-moment judgment — and dispatching subagents in parallel also gives genuine concurrency and keeps each one's context small. See Section 33.2 for how this decision was reached.

---

## 5. Goals

### 5.1 Functional goals

The system must:

1. Review any PR or diff using a general software-engineering methodology.
2. Detect whether agent-system-specific review is relevant.
3. Apply documentation-accuracy, cross-usage schema consistency, and documented-safeguard checks when agent-system review is relevant.
4. Integrate SANYI findings when `SANYI.md` exists or the user explicitly requests SANYI.
5. Preserve source finding IDs and provenance.
6. Normalize findings into a canonical schema.
7. Deduplicate overlapping findings.
8. Verify candidate findings.
9. Separate:
   - verified findings;
   - supported findings;
   - hypotheses;
   - questions.
10. Prioritize findings by merge impact.
11. Assess Definition of Done.
12. Produce:

- review context;
- execution/change map;
- findings;
- questions;
- test/evaluation assessment;
- merge recommendation.

13. Support interview mode.
14. Default to read-only behavior.
15. Require explicit authorization before:

- editing code;
- posting comments;
- approving;
- requesting changes;
- applying SANYI fixes.

### 5.2 Quality goals

The system should reduce:

- unsupported claims;
- generic checklist spam;
- duplicate comments;
- style-heavy reviews;
- missing provenance;
- false merge blockers;
- review reports disconnected from the current diff.

It should improve:

- context reconstruction;
- evidence quality;
- prioritization;
- agent-system review depth;
- architecture governance;
- communication;
- merge-decision explainability.

---

## 6. Non-Goals

The first version will not:

- replace the human reviewer;
- automatically approve or reject PRs;
- automatically post comments;
- automatically fix code;
- create a full autonomous multi-agent system;
- rewrite SANYI;
- require SANYI in repositories that do not use it;
- invent SANYI violation codes without a contract;
- treat every agent-system concern as a blocker;
- perform exhaustive whole-repository audits for every PR;
- run arbitrary untrusted commands without confirmation;
- guarantee bug-free output;
- enforce a specific cost or concurrency cap — left to the operator's own `config.py` and deployment (Section 16.5).

---

## 7. High-Level Architecture

```text
                         ┌──────────────────────────┐
                         │   Human Reviewer / User  │
                         └─────────────┬────────────┘
                                       │
                                       ▼
                         ┌──────────────────────────┐
                         │  parallax (orchestrator) │
                         │  Stage 0–2: context brief│
                         └─────────────┬────────────┘
                                       │  parallel dispatch
        ┌───────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼           ▼           ▼
      ┌───┐       ┌───┐       ┌───┐       ┌───┐       ┌───┐       ┌───┐       ┌───┐
      │ A │       │ B │       │ C │       │ D │       │ E │       │ F │       │ G │
      └───┘       └───┘       └───┘       └───┘       └───┘       └───┘       └───┘
    Intent/    Reliability/  Security/  Architecture/   Agent    Account-    SANYI
    Correct-   Operations    Privacy/   Docs           Runtime/  ability/    (if
    ness/                    Data                      Tooling   Safeguards  SANYI.md
    Testing                                            (if       (if         exists)
    (always)   (always)      (always)   (always)       agent-    agent-
                                                        system)   system)
        │           │           │           │           │           │           │
        └───────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
                                       │  canonical findings
                                       ▼
                         ┌──────────────────────────┐
                         │ Canonical Finding Model  │
                         └─────────────┬────────────┘
                                       │
                                       ▼
                         ┌──────────────────────────┐
                         │ Deduplicate / Prioritize │
                         │ / Decide (Stage 7–10,    │
                         │ once, in the orchestrator│
                         │ — includes cross-subagent│
                         │ evidence reconciliation) │
                         └─────────────┬────────────┘
                                       │
                                       ▼
                         ┌──────────────────────────┐
                         │ Unified Review Report    │
                         └──────────────────────────┘
```

Subagents A–G are defined in full, including exactly which dimensions each
owns and which skill each preloads, in the companion document
`Parallax_Subagent_Architecture.md`.

---

## 8. Responsibility Boundaries

### 8.1 PR Review Methodology

Owns:

- review stages;
- review contract;
- profile selection;
- general software review;
- agent-change decision review (including documentation accuracy, cross-usage schema consistency, and documented safeguards);
- evidence policy;
- canonical schema;
- merge-impact classification;
- Definition of Done;
- communication;
- unified report;
- interview mode;
- human approval boundaries.

This is distributed across the six dimension skills (`intent-correctness`, `reliability-operations`, `security-privacy-data`, `architecture-docs`, `agent-runtime-tooling`, `accountability-safeguards`) plus the `shared/` references every subagent and the orchestrator draw on — not owned by a single skill file (Section 33.4).

Does not own:

- SANYI contract semantics;
- SANYI violation codes;
- SANYI audit behavior.

### 8.2 SANYI

Owns:

- `SANYI.md`;
- contract parsing;
- layer classification semantics;
- violation taxonomy;
- debt;
- migrations;
- pending;
- audit;
- contract-scoped review;
- source severity.

Does not own:

- general correctness;
- general testing;
- product intent;
- review communication;
- final merge decision.

### 8.3 Parallax Agent

Owns only orchestration:

- dispatching subagents A–G, each preloading exactly the skill relevant to its own role;
- passing the correct diff scope, via the context brief, to every dispatched subagent;
- ensuring output collection from all dispatched subagents;
- preventing unsafe automatic actions;
- producing one final report.

It must not implement review logic itself — that belongs to each subagent's preloaded skill content.

---

## 9. Review Profiles

### 9.1 General Profile

Always active.

Covers:

- intent and product behavior;
- correctness and contracts;
- reliability and failure recovery;
- security and privacy;
- data and state;
- architecture and maintainability;
- testing;
- operations and delivery;
- documentation;
- Definition of Done;
- communication;
- merge decision.

### 9.2 Agent-System Extension

Conditionally active.

Triggered by, in order of reliability:

1. **Explicit declaration at Stage 0** (Section 10) — the human states directly whether this is a general software PR or an agent-system PR. Accepted as-is; skips automatic signal detection for this determination entirely. This is the simplest and most reliable path — ask up front rather than relying on inference whenever the human is available to answer.
2. **High-confidence repository/PR signals**, when no explicit declaration was given.
3. **A corrective follow-up dispatch** (Section 16.6), for the remaining case where neither of the above caught it and Subagents A–D notice signals during their own review that detection missed.

Signals for (2) may include:

- LLM SDK imports;
- agent framework imports;
- prompt files;
- tool schemas;
- MCP;
- retrieval;
- vector database;
- memory;
- workflow orchestration;
- graders;
- eval scenarios;
- model configuration;
- human-agent handoffs;
- agent traces.

The extension focuses on **change-level decision risk** and on **undeclared drift** that neither general review nor SANYI catches on its own — SANYI only enforces contract entries that already exist in `SANYI.md`; it says nothing about drift nobody has declared yet.

Automatic detection at Stage 0–2 is a fallback, not the primary path (see the ordering above) — and even then, it's not the last chance: Subagents A–D (always dispatched) can also surface agent-system signals they happen to notice during their own review, correcting a false negative after the fact (Section 16.6).

It covers:

- tool side effects;
- retry and idempotency;
- workflow partial failure;
- agent termination;
- human approval;
- permissions;
- retrieval boundaries;
- memory write-back;
- production observability;
- repeated-run validation;
- grader impact;
- rollout and rollback;
- product/accountability implications;
- documentation accuracy (Section 18.7);
- cross-usage schema consistency (Section 18.2);
- documented safeguards without deterministic backing (Section 19.7).

---

## 10. Review Stages

### Stage 0 — Establish Review Contract

Inputs:

- PR title;
- PR description;
- linked issue;
- design doc;
- user instructions;
- repository instructions;
- current branch;
- base branch;
- time budget;
- review profile (general | agent-system), if the human states it directly — this is the preferred way to activate the Agent-System Extension (Section 9.2), simpler and more reliable than waiting on automatic signal detection.

Output:

- intended change;
- expected behavior;
- scope;
- out-of-scope;
- constraints;
- confirmed facts;
- inferred assumptions;
- unknowns;
- initial risk areas.

The system must not treat missing context as a code defect.

### Stage 1 — Collect Context

Read:

- repository structure;
- `CLAUDE.md`;
- `AGENTS.md`;
- `CONTRIBUTING.md`;
- `README.md`;
- PR templates;
- CI workflows;
- tests;
- architecture docs;
- ADRs;
- changed files;
- nearby files;
- callers and callees;
- relevant historical changes.

### Stage 2 — Build Change Map

Trace:

- input;
- validation;
- transformation;
- state transition;
- external systems;
- tools;
- side effects;
- persistence;
- output;
- error path;
- human handoff;
- evaluation path;
- memory write-back.

Output a concise execution map.

### Stage 3 — General Review

Apply the general lenses (Section 18).

### Stage 4 — Conditional Agent-System Review

If relevant:

- run the agent-change decision lens (Section 19), including documentation-accuracy, cross-usage schema consistency, and documented-safeguard checks;
- for any shared schema/type touched by the diff, search the full repo for other usages, not just the diff's own callers;
- for any safety/guardrail claim touched or referenced by the diff, verify it against actual code, not just documentation or prompt text.

### Stage 5 — Conditional SANYI Review

If `SANYI.md` exists:

- apply the preloaded SANYI taxonomy against the exact same diff scope;
- classify findings using SANYI's native codes and severities;
- preserve source codes and severity in the canonical schema.

If no `SANYI.md` exists:

- do not emit formal SANYI violations;
- surface general architecture concerns;
- optionally recommend `/sanyi init` — especially if Stage 4's documented-safeguard check found an undeclared invariant.

### Stage 6 — Evidence Verification

This stage is distributed, not centralized — see Section 33.5 for why.

**Inside each subagent (A–G), before it returns its findings:** for every
candidate finding that subagent generated, apply the same checklist to its
own claims, since it already holds the context needed to do so:

- inspect code;
- inspect contracts;
- inspect callers;
- inspect tests;
- run safe checks;
- create minimal reproduction when appropriate;
- inspect traces;
- run repeated scenarios for nondeterministic behavior;
- downgrade unsupported claims.

Each subagent assigns its own findings an `evidence_state` (Section 20)
before returning them in the canonical schema.

**In the orchestrator, once, folded into Stage 7:** cross-subagent evidence
reconciliation — cases that no single subagent could verify alone, such as
two subagents reaching conflicting conclusions about the same code, or a
finding whose verification depends on combining two subagents' outputs
(e.g., confirming that a Reliability finding also breaches a SANYI contract
entry requires both the Reliability subagent's and the SANYI subagent's
results together).

### Stage 7 — Deduplicate and Prioritize

Group findings that refer to the same root cause.

Preserve all source references.

Choose a canonical finding.

Assess:

- merge impact;
- confidence;
- user impact;
- severity;
- detectability;
- recoverability;
- blast radius.

### Stage 8 — Definition of Done

Assess:

- behavior;
- tests;
- evaluation;
- documentation;
- observability;
- migration;
- rollout;
- rollback;
- security;
- handoff;
- known limitations.

### Stage 9 — Communication and Decision

Produce:

- strengths;
- blocking findings;
- important findings;
- questions;
- suggestions;
- test/evaluation gaps;
- Definition of Done summary;
- merge recommendation.

### Stage 10 — Interview Mode

When interview mode is active, add:

- 60-second summary;
- review approach;
- top three concerns;
- why each concern is or is not blocking;
- alternatives;
- trade-offs;
- expected interviewer challenges;
- testing strategy;
- final decision.

---

## 11. Canonical Integration Schema

The canonical schema must preserve SANYI's semantics while enabling unified review.

### 11.1 Finding Schema

```yaml
review_finding_id: PR-B-001 # <subagent letter>-prefixed, Section 13.4

source:
  system: parallax | sanyi
  source_id: null | BY-2
  source_type: native | adapted
  source_contract_entry: null | "PII Masking"

profile:
  general: true
  agent_system: false

lens:
  category: correctness | reliability | security | data | architecture | testing | operations | agent_behavior | evaluation | communication
  subcategory: null

status:
  evidence_state: verified | supported | hypothesis | question
  confidence: high | medium | low

location:
  files:
    - path: src/example.py
      start_line: 10
      end_line: 20
  symbols:
    - example_function

claim:
  title: "Retry may duplicate an external side effect"
  observation: >
    The handler retries every exception after the external write call.
  failure_scenario: >
    The external service succeeds, but the client times out before the local
    state commit.
  impact: >
    The same action may be executed more than once.

evidence:
  direct:
    - type: code
      reference: src/example.py:10-20
      detail: "All exceptions enter the retry loop."
  supporting:
    - type: test
      reference: tests/test_example.py
      detail: "No partial-success test exists."
  assumptions:
    - "The external API does not provide idempotency guarantees."
  verification_attempted:
    - "Inspected API wrapper."
    - "Searched for idempotency key."
  remaining_uncertainty:
    - "External provider behavior is undocumented."

source_semantics:
  native_severity: null | blocker | warning | info | notice
  native_code: null | BY-2

review_assessment:
  merge_impact: blocker | important | question | suggestion | nit
  blocking_rationale: >
    This can produce irreversible duplicate actions.
  user_impact: high | medium | low | unknown
  blast_radius: high | medium | low | unknown
  recoverability: easy | moderate | difficult | unknown

recommendation:
  options:
    - description: "Use an idempotency key."
      tradeoffs: "Requires API and storage support."
    - description: "Retry only before the external write."
      tradeoffs: "May require manual recovery."
  validation:
    - "Add a partial-success integration test."
    - "Verify provider idempotency guarantees."

communication:
  comment_type: request_change | question | suggestion | nit
  proposed_comment: >
    This retry catches failures after the external side effect...
```

### 11.2 Design principles

The schema must:

- preserve SANYI's native codes;
- preserve native severity;
- preserve source-specific fields;
- avoid rewriting SANYI semantics;
- allow PR-native findings;
- support deduplication;
- support final communication;
- distinguish source severity from merge impact;
- ensure finding IDs are unique across concurrently-dispatched subagents (Section 13.4).

---

## 12. Adapter Design

### 12.1 SANYI Mapping

Responsibilities:

- preserve:
  - source violation code;
  - source severity;
  - contract entry;
  - layer;
  - path;
  - verdict;
  - decision options;
- map to canonical schema;
- never invent or rewrite violation codes;
- never emit formal SANYI findings if no `SANYI.md` exists;
- preserve diff-scoped behavior;
- preserve debt distinction;
- preserve migration semantics;
- map source severity separately from merge impact.

Because `sanyi`'s taxonomy is preloaded directly into a dedicated subagent (Section 4.4), this mapping happens in the same reasoning pass that runs that subagent's review — there is no separate file to read or external report to parse. The responsibilities above still apply; only the mechanism for obtaining SANYI's raw classification changes (see Section 33.2).

### Example mapping

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

### 12.2 Parallax Native Adapter

Parallax-native findings — including documentation-accuracy, cross-usage schema consistency, and documented-safeguard findings from Section 19 — are already canonical.

They should use:

```text
source.system = parallax
source.source_type = native
```

---

## 13. Deduplication Strategy

Two findings should be considered possible duplicates when they share:

- same file or symbol;
- same behavioral root cause;
- same failure scenario;
- same affected contract;
- same side effect;
- same schema drift.

Do not deduplicate based on title similarity alone.

"Same root cause" and "same failure scenario" require semantic judgment, not mechanical comparison — two findings touching the same lines are not automatically duplicates (a Reliability finding about a missing idempotency key and a SANYI `JY-2` about the same lines growing the schema too fast are two different problems, not one). With findings now arriving concurrently from up to seven independent subagents (Section 16), deduplication runs in two passes rather than asking one pass to do both jobs at once.

### 13.1 Deterministic pre-filter (`deduplication.py`)

Purely mechanical, no LLM judgment involved: group findings whose `location.files` overlap in path and line range, and whose `lens.category` matches (or whose `location.symbols` overlap). This produces small candidate clusters of findings that _might_ be duplicates, without needing to understand what any of them mean — just comparing paths, line ranges, and category labels. This is the deterministic component the MVP scope (Section 25.2) requires, and it exists specifically so semantic judgment is never asked to compare every finding against every other finding.

### 13.2 Semantic merge decision (orchestrator, Stage 7)

Only within each candidate cluster produced by 13.1, the orchestrator judges whether the findings are actually the same underlying issue or merely touch the same code for unrelated reasons. This is real LLM judgment, but bounded to a small, pre-filtered set rather than applied to the full cross-product of all findings from all subagents — which is what keeps this from being the "LLM-based duplicate detection without deterministic fallback" that Section 25.2 defers.

### 13.3 Canonical finding selection

When 13.2 confirms multiple lenses identified the same issue:

1. preserve all source references;
2. select the most precise root-cause description;
3. retain SANYI contract semantics if present;
4. use Parallax for merge impact and communication.

Example:

```text
Parallax (cross-usage schema check, from Subagent D — architecture-docs):
PR-D-004 — downstream serializer silently drops a renamed field on a shared response type

SANYI (from Subagent G):
JY-2 — anomalous schema growth on the same type

Parallax:
merge impact: important — data-loss risk for existing callers
```

Unified result:

```text
One PR finding
Sources:
- PR-D-004 (Parallax-native cross-usage schema check)
- JY-2 (SANYI)
```

### 13.4 Finding ID namespacing

Each subagent prefixes its own findings' `review_finding_id` with its own subagent letter (`PR-A-001`, `PR-B-001`, `PR-G-001`, …) rather than drawing from one shared, subagent-agnostic counter (`PR-001`). Because up to seven subagents run concurrently and independently, two unrelated findings from different subagents could otherwise be assigned the identical ID before the merge step (13.1–13.2) ever runs.

---

## 14. Severity Model

Do not collapse source severity and merge impact.

### 14.1 Source severity

Owned by source systems.

Examples:

- SANYI blocker/warning/info/notice;
- Parallax-native internal risk level.

### 14.2 Merge impact

Owned by Parallax.

Values:

- **blocker** — should not merge;
- **important** — must be addressed or consciously accepted;
- **question** — missing context prevents judgment;
- **suggestion** — meaningful improvement but not required;
- **nit** — minor polish.

### 14.3 Decision outcomes

- `approve`
- `comment`
- `request_changes`
- `insufficient_context`

---

## 15. Repository Structure

```text
Parallax/
├── README.md
├── config.py                       # dedup thresholds, confidence bands, time budgets
├── docs/
│   ├── Parallax_Project_Name.md
│   ├── images/Parallax.png
│   └── documents/
│       ├── Evidence_Driven_PR_Review_System_Spec.md
│       └── Parallax_Subagent_Architecture.md
├── .claude/                         # Claude Code only discovers skills/agents here (Section 33.12)
│   ├── skills/                      # one skill per subagent, plus parallax-shared and sanyi
│   │   └── ... (see Parallax_Subagent_Architecture.md Section 5 for the
│   │             full per-subagent skill tree, parallax-shared, and
│   │             sanyi — copied from SANYI's repo, not a submodule)
│   └── agents/
│       └── ... (parallax.md orchestrator + one agent per subagent A–G; see
│                 Parallax_Subagent_Architecture.md Section 5)
├── parallax/
│   ├── __init__.py
│   ├── orchestration/
│   │   ├── profile_detection.py
│   │   ├── diff_scope.py
│   │   ├── deduplication.py
│   │   ├── prioritization.py
│   │   └── report_builder.py
│   └── schemas/
│       ├── review_finding.schema.json
│       ├── review_report.schema.json
│       └── models.py
└── tests/
    ├── fixtures/
    │   └── sanyi_report_sample.md
    ├── test_sanyi_mapping.py
    └── test_report_builder.py
```

---

## 16. Parallax Agent

### 16.1 Purpose

Guarantee that every review dimension's ruleset is available to the subagent responsible for it, without depending on a Skill's prose to trigger another Skill at runtime (Section 4.4), and give the review genuine parallelism instead of one agent working through every dimension sequentially in a single growing context.

### 16.2 Orchestrator and subagents (overview)

`parallax` is a thin orchestrating Agent. It does not preload every skill itself; it dispatches seven possible subagents in parallel, each preloading exactly the skill relevant to its own narrow role:

| Subagent                         | Owns                  | Dispatch condition            |
| -------------------------------- | --------------------- | ----------------------------- |
| A. Intent, Correctness & Testing | 18.1, 18.2, 18.8      | always                        |
| B. Reliability & Operations      | 18.3, 18.9            | always                        |
| C. Security, Privacy & Data      | 18.4, 18.5            | always                        |
| D. Architecture & Documentation  | 18.6, 18.7            | always                        |
| E. Agent Runtime & Tooling       | 19.1–19.4             | Agent-System Extension active |
| F. Accountability & Safeguards   | 19.5–19.7             | Agent-System Extension active |
| G. SANYI                         | SANYI's full taxonomy | `SANYI.md` exists             |

The orchestrator runs Stage 0–2 once, builds a context brief, dispatches the applicable subagents with that brief, then runs Stage 6–10 once over their combined canonical findings (Section 10; Section 7's diagram shows the full fan-out/fan-in).

Every one of A–G, plus the orchestrator itself, also preloads `parallax-shared` — the packaged skill holding the evidence model, severity/decision rules, communication format, Definition of Done, interview mode, and report templates every subagent and the orchestrator draw on (`Parallax_Subagent_Architecture.md` Section 5). This gets the same `skills:` guarantee as SANYI and each dimension skill, rather than being left as loose files subagents are merely told to go read (Section 33.11).

Full subagent definitions — exact dimension ownership, rationale for each grouping, and each one's skill/agent frontmatter — live in the companion document `Parallax_Subagent_Architecture.md`, kept separate so an implementation session working on one subagent doesn't need to load this entire spec.

**Partial-failure handling:** there is no per-subagent wall-clock timer this spec can enforce — no such field exists in a Claude Code agent's own configuration (unlike `skills:`, established as real in Section 4.4). Failure is instead detected by output validity: if a dispatched subagent does not return output that validates against the canonical schema (Section 11) — whether it errored or returned something malformed — the orchestrator retries that subagent up to two times before giving up on it. Giving up on one subagent does not fail the whole review: the orchestrator proceeds to Stage 7–10 with whatever subagents did return, and the report's Subagent Dispatch section (Section 22) states plainly which subagent(s) failed and were skipped, so the human reviewer knows the review's coverage may be incomplete rather than assuming it's exhaustive.

### 16.3 Without the orchestrator

There is no standalone fallback skill that bundles every dimension into one file (Section 33.4 explains why one was tried and dropped). Without the `parallax` orchestrator dispatching subagents A–G, a user or host session can still invoke the individual dimension skills (`intent-correctness`, `reliability-operations`, `security-privacy-data`, `architecture-docs`, `agent-runtime-tooling`, `accountability-safeguards`) and `sanyi` directly, and Claude's own skill-matching will apply whichever ones its judgment decides are relevant to the request.

This is a reduced mode, not an equivalent one:

- no guarantee that every applicable dimension actually gets checked;
- no deduplication or prioritization across findings from different skills;
- no unified report or merge-impact synthesis — Stage 6–10 only run inside the orchestrator.

Use it only for a quick, exploratory look-in — not as a substitute for a full review.

### 16.4 Running a single subagent directly

Beyond the full `parallax` orchestrator (16.2) and skill-only invocation with no agent at all (16.3), any of A–G can also be invoked directly and individually, by name, when only one dimension's review is wanted — e.g. `security-privacy-data-review` alone for a quick security-focused look, with no interest in the rest.

This gives that subagent's full capability: its preloaded skill, and its own Bash-based self-verification (Stage 6, Section 10) — scoped to just that one dimension. It is stronger than 16.3's skill-only fallback (a real subagent ran, not just skill-matching guesswork) but narrower than a full orchestrated review.

What's still missing compared to a full orchestrator run: deduplication and merge across dimensions (Section 13), Definition of Done assessment (Section 21), and the unified report (Section 22) — those stages only run inside the `parallax` orchestrator, since they require seeing every dispatched subagent's output together.

### 16.5 Cost and Latency Tradeoff

Running up to seven concurrent subagents costs more than a single sequential pass — several will independently read overlapping files (e.g., both the intent-correctness and security-privacy-data subagents reading the same touched file, each through its own lens). This overlap is not eliminated by design; avoiding it would mean merging back into one sequential agent, undoing the parallelism this architecture exists for (Section 33.3). Parallax does not attempt to enforce a hard cost cap on a review from inside a subagent's own instructions — that is a deployment-level concern (how many concurrent sessions an operator's own budget allows), not something this spec can observe or control.

What the design already does to keep cost proportionate to what's actually needed:

- **Conditional dispatch is the primary lever.** E, F, and G are not dispatched at all unless their trigger condition holds (Section 2 of `Parallax_Subagent_Architecture.md`) — a plain, non-agentic PR with no `SANYI.md` runs only 4 subagents, not 7.
- **The context brief is built once.** Stage 0–2 run a single time in the orchestrator; no subagent re-derives "what is this diff" independently (Section 16.1).
- **Cheaper modes already exist for when the full run isn't wanted.** Section 16.3 (skill-only, no agent) and Section 16.4 (a single named subagent) are intentionally lighter-weight options, not just fallbacks for unsupported hosts.

`config.py` (Section 15) is where an operator can add their own cap — e.g. a maximum subagent concurrency, or a rule that downgrades to a Section 16.4-style single-subagent review below some diff-size threshold. Parallax does not prescribe a specific number here, since the right cap depends on the operator's own budget and traffic, not on anything this spec can observe.

### 16.6 Correcting a Missed Agent-System Detection

Section 9.2's signal detection runs once, upfront, in Stage 0–2, and directly decides whether E and F are dispatched at all. A false negative there — missing that a PR is agent-related — has no chance to self-correct in the way it once did: in an earlier, sequential single-agent design, the same agent doing context-gathering also did the general review afterward, in one continuous reasoning stream, so it could notice a missed signal partway through and adjust. With A–D now running in their own isolated, parallel contexts, none of them can dispatch E or F themselves, and the orchestrator has already made its one dispatch decision before they even start.

Resolved with the same follow-up-dispatch pattern used for the SANYI-candidate hand-off (Section 19.7, 33.7): if any of A–D notices agent-system signals during its own review — LLM SDK imports, prompt files, agent framework code — that weren't accounted for by the initial detection, it flags this explicitly in its returned output rather than silently staying inside its own assigned dimension. During Stage 7 merge, if the orchestrator sees this flag and E/F were not dispatched, it makes a corrective follow-up dispatch of E and F before finalizing the report. This only adds latency in the rare case of a corrected false negative, not on every review.

---

## 17. SANYI Integration Rules

### 17.1 If `SANYI.md` exists

Apply the preloaded SANYI taxonomy to the same diff.

Preserve native semantics.

### 17.2 If `SANYI.md` does not exist

Do not:

- emit BY/JY/BN/MG/UN codes;
- infer formal layer assignments;
- claim contract violations.

May:

- surface general architecture-boundary concerns;
- recommend `/sanyi init` — in particular when Section 19.7's documented-safeguard check finds an undeclared invariant. Since Subagent G is not dispatched when `SANYI.md` doesn't exist, no subagent has SANYI's contract format preloaded, so Subagent F can only recommend running `/sanyi init` — it cannot draft a candidate entry itself;
- explain that formal enforcement requires a contract.

### 17.3 SANYI findings and merge decision

The PR Review system may map SANYI findings to merge impact, but must not alter the SANYI source finding.

---

## 18. General Review Dimensions

### 18.1 Intent and Product Behavior

- Does the PR solve the intended problem?
- Is user-visible behavior clear?
- Is the scope appropriate?
- Does it solve the cause or only the symptom?
- Is the implementation unnecessarily complex?

### 18.2 Correctness and Contracts

- Inputs;
- outputs;
- schemas;
- state transitions;
- invariants;
- edge cases;
- ordering;
- concurrency;
- compatibility;
- **cross-usage consistency**: when the diff modifies a shared schema/type, check all of its usages across the repo, not only the diff's own callers.

### 18.3 Reliability

- retries;
- timeouts;
- idempotency;
- partial failures;
- fallback;
- cancellation;
- recovery;
- cleanup;
- consistency.

### 18.4 Security and Privacy

- authn;
- authz;
- tenant isolation;
- PII;
- secrets;
- injection;
- unsafe writes;
- auditability.

### 18.5 Data and State

- validation;
- provenance;
- migration;
- serialization;
- stale data;
- duplicated state;
- source of truth.

### 18.6 Architecture and Maintainability

- boundaries;
- dependency direction;
- coupling;
- abstraction;
- duplication;
- evolution;
- rollback;
- long-term contract.

### 18.7 Documentation Accuracy

- Do existing docs (`CLAUDE.md`, `README.md`, architecture docs, any capability/status tables the project maintains) still describe the code accurately after this diff?
- Do file paths, module references, or capability claims in project docs still resolve to something real?
- This is distinct from Section 21's Definition-of-Done check ("did this diff update its own docs") — it catches pre-existing or diff-introduced drift between docs and code, not just missing updates for the current change.

### 18.8 Testing

- unit;
- integration;
- contract;
- regression;
- end-to-end;
- negative paths;
- useful assertions;
- failure-before-fix evidence.

### 18.9 Operations and Delivery

- logging;
- metrics;
- tracing;
- deployment;
- rollout;
- rollback;
- migration;
- documentation;
- handoff.

---

## 19. Agent-System Decision Dimensions

### 19.1 Tool Side Effects

- Is the tool read-only or write-capable?
- Is confirmation required?
- Is retry safe?
- Is idempotency guaranteed?
- Is output validated?
- Are permissions enforced at the tool boundary?

### 19.2 Workflow State and Partial Failure

- Is the graph bounded?
- Can it terminate?
- Can it resume?
- What happens after partial success?
- Are handoffs explicit?
- Is deterministic code used where appropriate?

### 19.3 Retrieval and Context

- Is retrieval scoped correctly?
- Is provenance preserved?
- Are permissions respected?
- Is stale or conflicting context handled?
- Can external content influence a sensitive sink?

### 19.4 Memory Write-Back

- What is persisted?
- Is it fact, inference, or model output?
- Can it be corrected?
- Is confidence stored?
- Is approval required?
- Can bad runs contaminate future cases?

### 19.5 Evaluation

- Is one successful run being overvalued?
- Are repeated runs needed?
- Is there a baseline?
- Are deterministic graders possible?
- Is an LLM judge calibrated?
- Are trace and final output both evaluated?
- Are cost and latency considered?

### 19.6 Human Responsibility

- Who approves?
- Who is accountable?
- Can a human take over?
- Is uncertainty visible?
- Is escalation available?

### 19.7 Documented Safeguards

- Does documentation, a system prompt, or configuration claim a safety/guardrail behavior exists (an escalation path, an input/output validation layer, a confidence gate)?
- Is that claim backed by an actual deterministic code path, or does it exist only as a sentence in a prompt?
- If a gap is found and no SANYI contract already governs it, recommend recording it as a candidate `SANYI.md` Buyi or Pending entry (Section 17.2) rather than treating it as a standalone PR Review finding — this is the same failure mode SANYI's BY-4 targets, applied proactively to invariants nobody has declared yet.
- If `SANYI.md` exists (Subagent G was dispatched), G — not F — drafts the properly-formatted candidate entry, since it is the one subagent with SANYI's own contract format preloaded. Because A–G run concurrently and cannot coordinate with each other mid-flight, this is not F handing off live to G: the orchestrator, during Stage 7 merge, recognizes F's flagged gap and makes one additional, sequential follow-up dispatch to G with F's finding as input, specifically to draft the entry. The draft is surfaced as a recommendation in the unified report (Section 22); nothing is written to `SANYI.md` without explicit human approval (Section 24). If `SANYI.md` does not exist, no properly-formatted draft is possible — see Section 17.2.

---

## 20. Evidence Model

Every candidate finding must be classified.

### Verified

Directly confirmed by:

- code;
- test;
- reproduction;
- explicit contract;
- trace;
- deterministic evidence.

### Supported

Strong evidence exists, but one external assumption remains.

### Hypothesis

Plausible risk without enough evidence.

Must not be phrased as a confirmed defect.

### Question

Missing context prevents judgment.

Must be phrased as a clarification request.

---

## 21. Definition of Done

Default fallback:

- intended behavior complete;
- important edge cases handled;
- tests sufficient;
- evaluation sufficient;
- documentation updated;
- observability present;
- migration handled;
- rollout understood;
- rollback understood;
- security reviewed;
- handoff complete;
- limitations recorded.

Priority:

```text
Repository-specific DoD
→ Team/project DoD
→ Skill default
```

---

## 22. Output Report

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

---

## 23. Interview Mode Output

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

---

## 24. Read-Only and Safety Policy

Default behavior is read-only.

The system must require explicit user authorization before:

- editing files;
- applying patches;
- running SANYI `--fix`;
- committing;
- pushing;
- posting GitHub comments;
- approving;
- requesting changes;
- deleting files;
- modifying configuration;
- writing an approved SANYI.md candidate entry (Section 19.7) — drafting one and surfacing it in the report requires no authorization; writing it into `SANYI.md` does.

Safe commands may include:

- reading files;
- grep/search;
- git diff;
- git status;
- test discovery;
- known project checks.

Unknown scripts must be inspected before execution.

Every subagent (A–G) has `Bash` access for exactly the safe-commands list above, needed for Stage 6 self-verification (Section 10) — running tests, safe checks, and reproductions. None of A–G may edit, commit, push, or take any action requiring the authorization this section already gates.

---

## 25. MVP Scope

### 25.1 Required

Implement:

- `SKILL.md` for each of the six dimension skills;
- review workflow reference;
- general review reference, including documentation-accuracy and cross-usage schema-consistency checks;
- agent-change decision reference, including the documented-safeguards check;
- evidence model;
- canonical schema;
- SANYI mapping documentation (Section 12.1);
- `parallax` orchestrator plus the seven subagent definitions A–G (`Parallax_Subagent_Architecture.md`);
- diff relevance classifier;
- deduplication: deterministic pre-filter plus orchestrator-side semantic merge (Section 13);
- partial-failure handling for subagent dispatch: retry up to two times on invalid output, then proceed and report the gap (Section 16.2);
- report builder;
- interview mode;
- read-only policy;
- `config.py` for tunables;
- tests for schema and report builder.

### 25.2 Deferred

Do not implement initially:

- autonomous multi-agent orchestration beyond the `parallax` orchestrator and its seven subagents;
- automatic GitHub posting;
- automatic code fixes;
- SANYI `--fix`;
- semantic history search;
- LLM-based duplicate detection without deterministic fallback;
- organization-wide dashboard;
- complex numerical risk score;
- CI deployment gate.

---

## 26. Implementation Order

### Phase 1 — Schema

1. Define canonical Pydantic models.
2. Add JSON schema export.
3. Document SANYI's taxonomy mapping (Section 12.1).
4. Add fixtures, including a sample SANYI report.
5. Add round-trip tests.

### Phase 2 — Skills and Workflow

1. Create the six dimension skills' `SKILL.md` files (`intent-correctness`, `reliability-operations`, `security-privacy-data`, `architecture-docs`, `agent-runtime-tooling`, `accountability-safeguards`).
2. Add `shared/` references, including the new dimensions (Section 18.7, 18.2, 19.7).
3. Add templates.
4. Implement profile detection.
5. Implement diff-scope normalization.
6. Implement report builder.

### Phase 3 — Finding Processing

1. Implement diff relevance.
2. Implement deduplication: the deterministic pre-filter in `deduplication.py` (file/line-range overlap plus `lens.category`/symbol match, Section 13.1) is a real, testable code module; the semantic merge decision within each pre-filtered cluster (Section 13.2) is orchestrator judgment during Stage 7, not a separate module.
3. Implement evidence-state validation.
4. Implement merge-impact prioritization.
5. Implement Definition of Done assessment.

### Phase 4 — Agent-System Dimensions

1. Implement documentation-accuracy checks.
2. Implement cross-usage schema-consistency checks.
3. Implement documented-safeguard checks and the SANYI-candidate recommendation path.
4. Detect `SANYI.md` and apply its taxonomy.

### Phase 5 — Parallax Orchestrator and Subagents

1. Create the seven subagent definitions A–G per `Parallax_Subagent_Architecture.md` Section 3, each preloading exactly its own skill (G preloads `sanyi`).
2. Copy SANYI's `SKILL.md` and `references/*.md` directly into `.claude/skills/sanyi/` (Section 33.12) — not a git submodule; Claude Code only discovers skills under `.claude/skills/` or `~/.claude/skills/`, and a submodule elsewhere would need extra plugin or symlink machinery this design doesn't need if SANYI is expected to stay stable. Note the source commit/version copied from, for future reference.
3. Create `.claude/agents/parallax.md`, the thin orchestrator that dispatches A–D always, E–F when the Agent-System Extension is active, and G when `SANYI.md` exists.
4. Enforce read-only default across the orchestrator and all subagents.
5. Add integration tests confirming: each subagent's preloaded skill is present in its context at startup; A–D are always dispatched; E–F and G are dispatched only under their respective conditions; the orchestrator correctly merges findings from all dispatched subagents.

### Phase 6 — Evaluation

Build benchmark PR fixtures:

- general correctness bug;
- partial side-effect bug;
- agent prompt-only safeguard with no SANYI entry (Section 19.7);
- schema drift across usages (Section 18.2);
- doc drift (Section 18.7);
- eval regression;
- SANYI BY-2;
- SANYI JY-2;
- duplicate SANYI/PR finding;
- no-SANYI repository;
- interview-mode PR.

---

## 27. Testing Strategy

### 27.1 Unit tests

Test:

- schema validation;
- SANYI field mapping;
- source preservation;
- severity separation;
- diff relevance;
- deduplication;
- report rendering.

### 27.2 Integration tests

Test:

- general repository;
- agent repository;
- repository with SANYI;
- repository without SANYI;
- overlapping findings (PR-native + SANYI);
- no findings;
- insufficient context;
- read-only enforcement;
- each subagent's startup context includes exactly its own preloaded skill (no cross-contamination between A–G);
- conditional dispatch: E/F only fire when the Agent-System Extension is active, G only when `SANYI.md` exists;
- one subagent returns invalid output or errors on every attempt (through two retries) — the review still completes using the remaining subagents, and the report's Subagent Dispatch section (Section 22) states which one failed;
- a single subagent (e.g. `security-privacy-data-review`) can be invoked directly without the orchestrator (Section 16.4) and returns valid canonical-schema findings on its own.

### 27.3 Golden tests

Use golden Markdown reports to ensure stable output.

### 27.4 Safety tests

Verify the system does not:

- auto-edit;
- auto-comment;
- auto-approve;
- run SANYI fix;

without explicit authorization.

---

## 28. Evaluation Metrics

Measure:

- critical issue recall;
- unsupported claim rate;
- actionable comment rate;
- duplicate finding rate;
- diff relevance precision;
- priority agreement with human reviewer;
- false blocker rate;
- source provenance preservation;
- review preparation time;
- human override rate;
- noise per PR;
- interview walkthrough usefulness.

Do not optimize only for total findings.

---

## 29. Acceptance Criteria

The MVP is complete when:

1. A user can provide a PR or diff.
2. The system produces a general review.
3. Agent-system relevance is detected.
4. Documentation-accuracy, cross-usage schema, and documented-safeguard checks run when agent-system review is relevant.
5. SANYI findings can be produced when `SANYI.md` exists.
6. Source IDs and severity are preserved.
7. Duplicate findings are consolidated.
8. Unsupported findings remain hypotheses/questions.
9. Final report includes merge impact.
10. Definition of Done is assessed.
11. Interview mode works.
12. The system remains read-only by default.
13. No SANYI native schema changes are required.
14. Each of the seven subagents' startup context includes exactly its own preloaded skill (Subagent G includes SANYI's ruleset), and dispatch conditions (Section 2 of `Parallax_Subagent_Architecture.md`) are respected.
15. The final output is one coherent review, not concatenated reports.

---

## 30. Future Extensions

Possible later additions:

- GitHub API integration;
- CI status integration;
- historical PR retrieval;
- reviewer calibration;
- team-specific DoD packs;
- repository-specific policy packs;
- frontend review extension;
- data-pipeline extension;
- infrastructure extension;
- security extension;
- independent evidence-verifier subagent;
- review analytics;
- continuous benchmark suite;
- human feedback loop;
- report-to-comment approval UI.

---

## 31. Final Design Principles

1. Preserve specialized systems.
2. Integrate through mapping, not rewriting.
3. Keep source provenance.
4. Separate source severity from merge impact.
5. General review always runs.
6. Agent-system review is conditional.
7. SANYI requires an explicit contract; undeclared drift is caught by Sections 18.7, 18.2, and 19.7 instead, and feeds candidate SANYI entries.
8. Guaranteed composition (SANYI with the PR Review methodology) is a property of each subagent's static configuration, not a runtime prompt suggestion.
9. Hypotheses are not defects.
10. The system is read-only by default.
11. Communication is part of correctness.
12. The final decision belongs to the human.
13. Automate coverage, not accountability.
14. Produce one review, not multiple reports.
15. Optimize for evidence and prioritization, not comment volume.

---

## 32. One-Sentence Product Definition

> An evidence-driven PR review system that combines general software review, agent-system-specific review dimensions, and architecture change-contract enforcement to help human reviewers make responsible, explainable merge decisions.

---

## 33. Design Decisions Log

Earlier drafts of this spec integrated a third system, Akira, and treated SANYI composition as an adapter reading a persisted report. Both were revised after checking the actual Akira implementation (`galactus/src/akira`) and the actual SANYI skill (`SANYI/SKILL.md`, `SANYI/references/violations.md`), and after verifying Claude Code's subagent skill-preloading mechanism against current documentation.

### 33.1 Akira dropped; two of its checks folded into General/Agent-System Dimensions

Akira's five subagents split into two groups:

- **CodeQualityAgent** and **EvalAgent** duplicated dimensions already covered by Section 18.8 (Testing) and Section 19.5 (Evaluation) — dropped without replacement.
- **EvalAgent** and **SchemaAgent**'s original implementations derived their value from tribal knowledge hardcoded into their prompts (specific field names, specific known bug signatures, specific file paths under `galactus/src/support_agents/`) — genericizing that prompt text would strip exactly what made them useful, leaving something redundant with general review. That implementation was not ported.
- **SchemaAgent**'s underlying _concept_ (cross-usage schema consistency) and **DocsAgent**'s underlying concept (docs-vs-code drift) are genuinely repo-agnostic and fall in a real gap: SANYI only enforces contract entries that already exist, and diff-scoped general review doesn't naturally check usages or docs outside the diff. These became Section 18.2 (cross-usage consistency) and Section 18.7 (Documentation Accuracy).
- **SafeguardAgent**'s concept — verifying a documented safety claim has real code backing — is the same failure mode as SANYI's BY-4, just applied to invariants nobody has declared yet. This became Section 19.7 (Documented Safeguards), which explicitly recommends feeding discoveries back into `SANYI.md` rather than duplicating SANYI's role.

### 33.2 SANYI composition resolved via Agent skill-preloading, not report-parsing

The original design assumed the PR Review Skill or Agent would "invoke" `sanyi` at runtime and read a persisted report. Two problems with that: (1) SANYI's own design treats its reports as ephemeral — `SANYI/references/violations.md` §5 states "Reports are Bianyi — freely generated, regenerate at will" — nothing writes them to disk; (2) a Skill's prose telling the model to invoke another Skill is not a guaranteed mechanism — the model may or may not comply, consistently or not.

Verified against current Claude Code documentation: a subagent's `skills:` frontmatter field injects a listed skill's full content into the subagent's context at startup, distinct from the generic `tools:` allowlist. This resolves both problems at once — a dedicated subagent (Section 16) preloads `sanyi`'s taxonomy directly, so there is no separate invocation step and no report to parse. That subagent produces canonical findings using SANYI's codes in the same reasoning pass that runs its review.

### 33.3 Single preloading agent replaced with parallel subagents

An intermediate design had one `parallax` Agent preloading both `pr-review` and `sanyi` and applying every dimension itself, sequentially, in one context. Two problems with that once the dimension count grew: (1) preloaded-skill content is not executed in parallel — it is concatenated into one shared context and worked through by a single sequential LLM pass, so bundling many dimensions into one agent gives no speed benefit; (2) Claude Code's own documented philosophy (subagent context isolation, "agent teams" design) treats bundling many unrelated responsibilities into one context as the thing to avoid, even though no hard token-count threshold is documented.

The design was revised to a thin `parallax` orchestrator dispatching seven parallel subagents (A–G), each preloading exactly one skill scoped to a thematically-tight group of dimensions — full detail in `Parallax_Subagent_Architecture.md`. This restores genuine concurrency (each subagent is an independent LLM invocation, not sequential work in a shared context) and keeps each subagent's context small, while keeping the reliability property from Section 33.2 (each subagent's ruleset is preloaded, not invoked at runtime).

### 33.4 Standalone `pr-review` skill dropped

Once dimension content moved into six separate per-dimension skills (Section 33.3), a leftover monolithic `pr-review` Skill still existed as a "no orchestrator" fallback, duplicating content already owned by those six skills — updating a dimension would have meant editing it in two places, with no mechanism to keep them in sync.

Dropped `pr-review` entirely; nothing replaces it as a single artifact. Without the `parallax` orchestrator, a user or host session can still invoke the individual dimension skills (and `sanyi`) directly, and Claude's own skill-matching decides which ones are relevant — but there is no guarantee every applicable dimension gets checked, and no deduplication or unified-report synthesis outside the orchestrator (Section 16.3). This is a real capability reduction for the no-orchestrator path, not a free equivalent.

### 33.5 Evidence Verification (Stage 6) split between subagents and orchestrator

Stage 6 originally read as a single pass owned entirely by the orchestrator, "once," alongside Stage 7–10. That doesn't hold once review is parallelized across seven subagents: the orchestrator never reads the code itself — it only receives each subagent's already-formed findings — so it cannot "inspect code / inspect callers" to verify a claim without redoing the investigating subagent's work from scratch, which defeats the point of dispatching in parallel. It also requires running checks and reproductions, which needs `Bash`, not previously granted to A–F.

Resolved by splitting Stage 6: each subagent (A–G) verifies its own candidate findings before returning them — it already holds the context to do so — and assigns them an `evidence_state`. The orchestrator's residual role, folded into Stage 7, is cross-subagent evidence reconciliation: conflicts between subagents' claims, or verifications that require combining two subagents' outputs. All seven subagents were given `Bash` access, scoped to the same safe-commands list Section 24 already defines for read-only operation.

### 33.6 Deduplication split into a deterministic pre-filter and a bounded semantic pass; finding IDs namespaced per subagent

Section 13's dedup criteria ("same root cause," "same failure scenario") require semantic judgment — no mechanical rule decides whether two findings touching the same lines are the same bug or two unrelated issues. But Section 25.2 explicitly defers "LLM-based duplicate detection without deterministic fallback" for the MVP. As written, Stage 7 dedup was exactly that deferred thing — a direct contradiction.

Resolved by splitting dedup into two passes: a purely mechanical pre-filter (`deduplication.py`, Section 13.1) that clusters findings by file/line-range overlap and category/symbol match — no understanding required, just comparing paths and ranges — followed by a bounded semantic merge decision (Section 13.2) that the orchestrator makes only within each small pre-filtered cluster, never across the full set of findings from all subagents. The deterministic pass satisfies Section 25.2's requirement; the semantic pass is real but scoped down to a small candidate set rather than an unbounded comparison.

Separately: with up to seven subagents assigning finding IDs concurrently and independently, a shared `PR-001`-style counter risked collisions before the merge step ever ran. IDs are now namespaced per subagent (`PR-A-001`, `PR-B-001`, …, Section 13.4).

### 33.7 SANYI-candidate recommendation loop: draft requires SANYI's own format, write requires human approval

Section 19.7's "recommend a candidate SANYI.md entry" was underspecified: who drafts it, in what format, under what authorization — and drafting a syntactically valid entry arguably requires understanding SANYI's own contract format, in tension with Section 4.1's "mapping, not rewriting" principle.

Resolved by splitting the work along the same lines used everywhere else in this spec: (1) only Subagent G — the one subagent with SANYI's contract format preloaded — drafts a properly-formatted candidate entry, when `SANYI.md` exists; Subagent F identifies the gap but does not draft. Since A–G run concurrently with no mid-flight coordination between them, this draft happens via one additional sequential follow-up dispatch to G after the parallel round, not live hand-off. When `SANYI.md` doesn't exist, no subagent has the format loaded, so F can only recommend `/sanyi init`, matching Section 17.2's existing rule. (2) The draft is only ever a recommendation inside Parallax's own report (Section 22) — writing it into `SANYI.md` is gated behind explicit human approval, the same authorization mechanism Section 24 already applies to every other write action (editing files, SANYI `--fix`, etc.), not a new bespoke rule.

### 33.8 Partial-failure handling, and two more supported invocation modes

An initial proposal for handling a hung or erroring subagent introduced a per-subagent "timeout budget." That doesn't correspond to anything Claude Code actually lets this spec configure — there is no documented per-agent wall-clock kill-switch, unlike `skills:` preloading (verified real in Section 4.4). Reframed around what can actually be checked: whether a dispatched subagent returns output that validates against the canonical schema (Section 11) at all. A subagent that doesn't — errored, hung, or returned malformed output — is retried up to two times, then given up on without failing the whole review; the gap is reported explicitly (Section 22's Subagent Dispatch summary) rather than silently absorbed.

Two more invocation modes were made explicit alongside the full orchestrator (16.2) and the skill-only fallback (16.3): running a single named subagent directly for one dimension's review (16.4), and — unchanged from before — the orchestrator's own retry/degrade behavior above. Both close gaps an earlier draft left silent about how the system could be used at less than full scale.

### 33.9 Cost/latency named as a tradeoff, not solved with an invented cap

Parallel dispatch across up to seven subagents costs more than one sequential pass, and nothing in the spec acknowledged this. Rather than inventing an enforceable cost or concurrency limit this spec has no way to actually control (there's no hook here into an operator's API budget), the tradeoff is now stated plainly (Section 16.5), alongside the mitigations already present by construction — conditional dispatch (most PRs skip E/F/G entirely), a context brief built once rather than per-subagent, and the 16.3/16.4 lighter-weight modes for when the full run isn't wanted. Enforcing a specific cap is left to the operator's own `config.py` and deployment, and named explicitly as a non-goal (Section 6).

### 33.10 Missed agent-system detection can now self-correct

Section 9.2's detection runs once, upfront, and directly gates whether E/F are dispatched — a false negative there had no recovery path, which is more brittle than an earlier sequential design where the same agent doing context-gathering could notice a missed signal later in its own continuous reasoning. Parallel subagents can't do that: A–D run in isolated contexts and can't dispatch E/F themselves, and the orchestrator's one dispatch decision is already made before they start.

Resolved with the same pattern already used for the SANYI-candidate hand-off (33.7): A–D flag agent-system signals they notice during their own review, even outside their assigned dimension, and the orchestrator makes a corrective follow-up dispatch of E/F during Stage 7 merge if it sees such a flag and they weren't already dispatched (Section 16.6).

On reflection, the simplest fix for most of this problem doesn't need any of the above: just ask the human directly at Stage 0 whether the PR is general or agent-system (Section 10), and treat that as authoritative. Automatic signal detection and the Section 16.6 corrective dispatch remain as the fallback and the safety net, respectively, for when the human doesn't state a profile — not as the primary mechanism.

### 33.11 Cross-cutting references packaged as a preloaded skill, not left as loose files

`shared/` (evidence model, severity/decision rules, communication format, DoD, interview mode, report templates — content every subagent and the orchestrator need) had no preload mechanism; subagents were only ever told, in prose, to go read it. That is exactly the unreliable "soft suggestion" pattern Section 4.4 rejected for SANYI, applied inconsistently here.

Resolved by packaging it as `parallax-shared`, a real skill structured like SANYI's own (`SKILL.md` plus `references/*.md` loaded on demand, per Claude Code's progressive-disclosure guidance), and adding it to every subagent's and the orchestrator's `skills:` list alongside their own dimension (or SANYI) skill. This gets the same reliability guarantee as everything else in the design, closing the one remaining place still relying on a runtime "remember to go read this" instruction.

### 33.12 Skill/agent discovery only works under `.claude/`; SANYI vendored by copy, not submodule

Two related gaps surfaced together. First: Claude Code only discovers skills and agents at `.claude/skills/<name>/SKILL.md` and `.claude/agents/<name>.md` (plus the user-level `~/.claude/` equivalents) — there is no setting to add custom search paths. Every repo-structure tree in this spec and its companion document had `skills/` and `agents/` at the repo root, one level too shallow to actually be found; this affected all seven subagents, not just SANYI. Fixed throughout: both trees, and every per-file comment header, now nest under `.claude/`.

Second, and the reason this surfaced: `vendor/sanyi` as a git submodule would never have been discovered either way — an arbitrary path outside `.claude/` isn't scanned regardless of what `skills:` references it. The documented, supported fix for vendoring a skill at a non-standard path is packaging it as a Claude Code plugin (a `.claude-plugin/plugin.json` manifest); a simpler but undocumented alternative is symlinking `.claude/skills/sanyi` to the submodule. Weighing that complexity against the actual need: SANYI is not expected to keep changing, so the drift risk a submodule exists to prevent doesn't apply here as strongly. Resolved by dropping the submodule and copying SANYI's `SKILL.md` and `references/*.md` directly into `.claude/skills/sanyi/`, noting the source commit/version at copy time as a lightweight paper trail — simpler than a plugin manifest or an unverified symlink, at the cost of needing a manual re-copy if SANYI is ever updated upstream.
