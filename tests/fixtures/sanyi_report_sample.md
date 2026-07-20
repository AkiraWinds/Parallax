Reference fixture only — no production code parses this file.

Evidence_Driven_PR_Review_System_Spec.md Section 33.2 established that
SANYI composition works by preloading SANYI's taxonomy directly into the
`sanyi-review` subagent (via Claude Code's `skills:` field), which then
emits canonical-schema `ReviewFinding`s in the same reasoning pass that
runs its review. There is no persisted report for anything to read back
(SANYI's own `references/violations.md` §5 treats reports as ephemeral:
"Reports are Bianyi — freely generated, regenerate at will").

This file exists so Section 15's repository structure has a concrete,
readable example of what the `sanyi-review` subagent's _prose_ report
looks like (per `.claude/skills/sanyi/references/violations.md` §3's
template) — the same shape `tests/test_sanyi_mapping.py` uses as the
worked example when testing that a SANYI-sourced `ReviewFinding` preserves
this report's native code and severity rather than inventing new ones.

---

# SANYI Review — feature/webhook-retry — 2026-07-19

Contract: SANYI.md v3 (last audit 2026-07-01)

## Verdict

Yes — this diff makes a declared Buyi invariant bypassable via a new
config flag.

## Findings

### [BLOCKER] BY-2 — PII masking made conditional

- Entry: 不易 Buyi / PII Masking
- Where: backend/middleware/outbound.py:41-52
- What: A new `SKIP_MASKING_IN_STAGING` environment variable now bypasses
  `mask_pii()` for outbound messages. The masking invariant survives the
  diff but becomes conditional — every individual line looks innocent,
  but comparing against the contract shows Buyi silently demoted to
  Bianyi.
- Decision options: revert | redesign | amend contract via architecture
  review

## Bookkeeping

- Updated current: (none — Buyi entries have no `current` stamp)

## Debt candidates

_None._
