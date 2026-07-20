"""Tunables for Parallax's deterministic orchestration modules.

Per Evidence_Driven_PR_Review_System_Spec.md Section 15/16.5: Parallax does
not prescribe a hard cost/concurrency cap — that is an operator decision.
This file is where an operator wires in their own values; nothing here is
hardcoded into the orchestration modules themselves (parallax/orchestration/).
"""

# --- Subagent dispatch (Section 16.2) ---------------------------------------

# How many times to retry a dispatched subagent whose output fails schema
# validation before giving up on it and reporting the gap (Section 16.2,
# 25.1: "retry up to two times on invalid output, then proceed").
SUBAGENT_RETRY_LIMIT = 2

# --- Deduplication (Section 13) ----------------------------------------------

# Section 13.1's deterministic pre-filter clusters findings whose file/line
# ranges overlap. Two ranges on the same file are considered overlapping if
# they intersect at all; this tolerance (in lines) widens the match so that
# near-adjacent findings (e.g. a function header vs. its body) still cluster.
DEDUPLICATION_LINE_TOLERANCE = 0

# --- Merge-impact defaults (Section 12.1, 14) --------------------------------

# Default mapping from SANYI's native severity to a starting merge_impact,
# per Section 12.1's example mappings. The orchestrator (or a human) may
# override this per-finding during Stage 7 synthesis (Section 14.2) — these
# are defaults, not a hard rule.
SANYI_SEVERITY_TO_MERGE_IMPACT_DEFAULT = {
    "blocker": "blocker",
    "warning": "important",
    "info": "suggestion",
    "notice": "suggestion",
}

# --- Time budget (Section 10 Stage 0, 16.5) ----------------------------------

# Default time budget (minutes) recorded in the context brief when the human
# does not state one. Purely informational — Claude Code has no per-agent
# wall-clock kill-switch (Section 33.8), so this cannot be enforced, only
# surfaced to the human reviewer.
DEFAULT_TIME_BUDGET_MINUTES = 30

# --- Confidence bands ---------------------------------------------------------

# Ordering used by prioritization.py when sorting findings that share the
# same merge_impact (Section 14.2) — higher-confidence findings surface
# first within each bucket.
CONFIDENCE_ORDER = ["high", "medium", "low"]

# Ordering used by prioritization.py to sort findings across merge_impact
# buckets before rendering the report (Section 22 sections 5-8).
MERGE_IMPACT_ORDER = ["blocker", "important", "question", "suggestion", "nit"]
