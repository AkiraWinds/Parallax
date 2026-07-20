"""Prioritization/bucketing tests (Section 27.1: 'severity separation').

Confirms source severity and merge impact never collapse (Section 14),
that SANYI's default severity mapping matches Section 12.1's worked
examples exactly, and that hypotheses/questions always land in the
"Questions and Unverified Hypotheses" bucket regardless of merge_impact
(Section 20).
"""

from __future__ import annotations

from parallax.orchestration.prioritization import (
    bucket_findings,
    default_merge_impact_for_sanyi_severity,
    sort_by_merge_impact,
)
from parallax.schemas.models import (
    Confidence,
    EvidenceState,
    MergeImpact,
    NativeSeverity,
)
from tests.conftest import make_finding


class TestSanyiSeverityDefaultMapping:
    def test_by2_blocker_maps_to_blocker(self):
        # Section 12.1: "SANYI BY-2 blocker -> canonical merge impact: blocker"
        assert (
            default_merge_impact_for_sanyi_severity(NativeSeverity.BLOCKER)
            == MergeImpact.BLOCKER
        )

    def test_jy2_warning_maps_to_important(self):
        # Section 12.1: "SANYI JY-2 warning -> canonical merge impact:
        # important or suggestion" — important is the default; a human
        # or the orchestrator may still downgrade it per Section 14.2.
        assert (
            default_merge_impact_for_sanyi_severity(NativeSeverity.WARNING)
            == MergeImpact.IMPORTANT
        )

    def test_mapping_never_returns_a_native_severity_value_directly(self):
        """Source severity and merge impact use overlapping vocab
        (both have no shared literal values here, but the guarantee this
        test protects is: the function must go through the lookup table,
        not just echo the input — i.e. never accidentally identity-map."""
        for severity in NativeSeverity:
            result = default_merge_impact_for_sanyi_severity(severity)
            assert isinstance(result, MergeImpact)


class TestSortByMergeImpact:
    def test_orders_blocker_before_important_before_suggestion(self):
        blocker = make_finding("PR-A-001", merge_impact=MergeImpact.BLOCKER)
        important = make_finding("PR-A-002", merge_impact=MergeImpact.IMPORTANT)
        suggestion = make_finding("PR-A-003", merge_impact=MergeImpact.SUGGESTION)
        ordered = sort_by_merge_impact([suggestion, blocker, important])
        assert [f.review_finding_id for f in ordered] == [
            "PR-A-001",
            "PR-A-002",
            "PR-A-003",
        ]

    def test_breaks_ties_by_confidence_high_first(self):
        low = make_finding(
            "PR-A-001", merge_impact=MergeImpact.IMPORTANT, confidence=Confidence.LOW
        )
        high = make_finding(
            "PR-A-002", merge_impact=MergeImpact.IMPORTANT, confidence=Confidence.HIGH
        )
        ordered = sort_by_merge_impact([low, high])
        assert [f.review_finding_id for f in ordered] == ["PR-A-002", "PR-A-001"]


class TestBucketFindings:
    def test_hypothesis_goes_to_questions_bucket_even_with_blocker_impact(self):
        finding = make_finding(
            evidence_state=EvidenceState.HYPOTHESIS, merge_impact=MergeImpact.BLOCKER
        )
        buckets = bucket_findings([finding])
        assert buckets["questions_and_hypotheses"] == [finding]
        assert buckets["blocking_findings"] == []

    def test_question_merge_impact_goes_to_questions_bucket(self):
        finding = make_finding(
            evidence_state=EvidenceState.QUESTION, merge_impact=MergeImpact.QUESTION
        )
        buckets = bucket_findings([finding])
        assert buckets["questions_and_hypotheses"] == [finding]

    def test_verified_blocker_goes_to_blocking_bucket(self):
        finding = make_finding(
            evidence_state=EvidenceState.VERIFIED, merge_impact=MergeImpact.BLOCKER
        )
        buckets = bucket_findings([finding])
        assert buckets["blocking_findings"] == [finding]

    def test_supported_important_goes_to_important_bucket(self):
        finding = make_finding(
            evidence_state=EvidenceState.SUPPORTED, merge_impact=MergeImpact.IMPORTANT
        )
        buckets = bucket_findings([finding])
        assert buckets["important_findings"] == [finding]

    def test_nit_goes_to_suggestions_bucket(self):
        finding = make_finding(
            evidence_state=EvidenceState.VERIFIED, merge_impact=MergeImpact.NIT
        )
        buckets = bucket_findings([finding])
        assert buckets["suggestions"] == [finding]

    def test_every_finding_lands_in_exactly_one_bucket(self):
        findings = [
            make_finding("PR-A-001", evidence_state=EvidenceState.VERIFIED, merge_impact=MergeImpact.BLOCKER),
            make_finding("PR-A-002", evidence_state=EvidenceState.HYPOTHESIS, merge_impact=MergeImpact.IMPORTANT),
            make_finding("PR-A-003", evidence_state=EvidenceState.VERIFIED, merge_impact=MergeImpact.NIT),
        ]
        buckets = bucket_findings(findings)
        all_ids = [f.review_finding_id for bucket in buckets.values() for f in bucket]
        assert sorted(all_ids) == ["PR-A-001", "PR-A-002", "PR-A-003"]
