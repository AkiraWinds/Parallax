"""Deterministic merge-impact bucketing and sorting.

Implements the non-judgment parts of Evidence_Driven_PR_Review_System_Spec.md
Section 13.3/14/22: once findings already carry a `merge_impact` and
`evidence_state` (assigned by the subagent that produced them, or by the
orchestrator during Stage 7 semantic merge — Section 13.2 remains real LLM
judgment and is not implemented here), this module deterministically sorts
and buckets them into the sections Section 22's report template expects.

Also implements Section 12.1's default SANYI-severity -> merge_impact
mapping table, as a *default* an orchestrator or human may override
(Section 14.2) — never a rewrite of SANYI's own source_semantics.
"""

from __future__ import annotations

from config import CONFIDENCE_ORDER, MERGE_IMPACT_ORDER, SANYI_SEVERITY_TO_MERGE_IMPACT_DEFAULT
from parallax.schemas.models import (
    Confidence,
    EvidenceState,
    MergeImpact,
    NativeSeverity,
    ReviewFinding,
)


def default_merge_impact_for_sanyi_severity(severity: NativeSeverity) -> MergeImpact:
    """Section 12.1 example mappings, e.g. SANYI BY-2 (blocker) -> blocker;
    SANYI JY-2 (warning) -> important. A default starting point only —
    Section 14.2 leaves the final merge_impact to Parallax's own judgment.
    """
    return MergeImpact(SANYI_SEVERITY_TO_MERGE_IMPACT_DEFAULT[severity.value])


def _sort_key(finding: ReviewFinding) -> tuple[int, int]:
    impact_rank = MERGE_IMPACT_ORDER.index(finding.review_assessment.merge_impact.value)
    confidence_rank = CONFIDENCE_ORDER.index(finding.status.confidence.value)
    return (impact_rank, confidence_rank)


def sort_by_merge_impact(findings: list[ReviewFinding]) -> list[ReviewFinding]:
    """Stable sort: blocker before important before question before
    suggestion before nit (Section 14.2); ties broken by confidence,
    high first (Section 11.1 `status.confidence`)."""
    return sorted(findings, key=_sort_key)


def bucket_findings(
    findings: list[ReviewFinding],
) -> dict[str, list[ReviewFinding]]:
    """Split findings into the four Section 22 report buckets.

    A finding whose evidence_state is hypothesis or question always lands
    in "questions_and_hypotheses" regardless of merge_impact — the report
    section is literally titled "Questions and Unverified Hypotheses"
    (Section 22 #7), and Section 20 requires hypotheses to be communicated
    as such, not folded into a Blocking/Important bucket that reads as a
    confirmed defect.
    """
    blocking: list[ReviewFinding] = []
    important: list[ReviewFinding] = []
    questions_and_hypotheses: list[ReviewFinding] = []
    suggestions: list[ReviewFinding] = []

    for finding in findings:
        if (
            finding.status.evidence_state in (EvidenceState.HYPOTHESIS, EvidenceState.QUESTION)
            or finding.review_assessment.merge_impact == MergeImpact.QUESTION
        ):
            questions_and_hypotheses.append(finding)
        elif finding.review_assessment.merge_impact == MergeImpact.BLOCKER:
            blocking.append(finding)
        elif finding.review_assessment.merge_impact == MergeImpact.IMPORTANT:
            important.append(finding)
        else:
            suggestions.append(finding)

    return {
        "blocking_findings": sort_by_merge_impact(blocking),
        "important_findings": sort_by_merge_impact(important),
        "questions_and_hypotheses": sort_by_merge_impact(questions_and_hypotheses),
        "suggestions": sort_by_merge_impact(suggestions),
    }
