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
_this specific PR_ should merge because of it.

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

| File                                      | Read when                                                      |
| ----------------------------------------- | -------------------------------------------------------------- |
| `references/evidence-model.md`            | classifying a candidate finding                                |
| `references/severity-and-decision.md`     | assigning merge impact, or reconciling source severity with it |
| `references/definition-of-done.md`        | assessing whether the PR is ready to merge                     |
| `references/communication-and-handoff.md` | writing up a finding or the final report                       |
| `references/interview-mode.md`            | interview mode is requested                                    |

## Templates

| File                                 | Used by                                                                                |
| ------------------------------------ | -------------------------------------------------------------------------------------- |
| `templates/context-brief.md`         | orchestrator, Stage 0–2 output passed to every subagent                                |
| `templates/review-report.md`         | orchestrator, final unified report                                                     |
| `templates/github-comment.md`        | orchestrator, when posting a finding as a PR comment (requires explicit authorization) |
| `templates/interview-walkthrough.md` | orchestrator, interview mode output                                                    |
