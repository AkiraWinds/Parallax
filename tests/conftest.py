"""Shared test fixtures/factories for Parallax's canonical schema."""

from __future__ import annotations

import pytest

from parallax.schemas.models import (
    Claim,
    Communication,
    CommentType,
    Confidence,
    Evidence,
    EvidenceState,
    FileLocation,
    Lens,
    LensCategory,
    Location,
    MergeImpact,
    NativeSeverity,
    Profile,
    ReviewAssessment,
    ReviewFinding,
    Source,
    SourceSemantics,
    SourceSystem,
    SourceType,
    Status,
)


def make_finding(
    review_finding_id: str = "PR-A-001",
    *,
    path: str = "src/example.py",
    start_line: int | None = 10,
    end_line: int | None = 20,
    symbols: list[str] | None = None,
    category: LensCategory = LensCategory.CORRECTNESS,
    evidence_state: EvidenceState = EvidenceState.VERIFIED,
    confidence: Confidence = Confidence.HIGH,
    merge_impact: MergeImpact = MergeImpact.IMPORTANT,
    source_system: SourceSystem = SourceSystem.PARALLAX,
    source_id: str | None = None,
    source_type: SourceType = SourceType.NATIVE,
    native_severity: NativeSeverity | None = None,
    native_code: str | None = None,
    title: str = "Example finding",
) -> ReviewFinding:
    """Build a minimally-valid ReviewFinding for tests, with every field
    overridable so tests only spell out what they actually vary."""
    return ReviewFinding(
        review_finding_id=review_finding_id,
        source=Source(system=source_system, source_id=source_id, source_type=source_type),
        profile=Profile(),
        lens=Lens(category=category),
        status=Status(evidence_state=evidence_state, confidence=confidence),
        location=Location(
            files=[FileLocation(path=path, start_line=start_line, end_line=end_line)],
            symbols=symbols or [],
        ),
        claim=Claim(title=title, observation="Something was observed."),
        evidence=Evidence(),
        source_semantics=SourceSemantics(native_severity=native_severity, native_code=native_code),
        review_assessment=ReviewAssessment(merge_impact=merge_impact),
        communication=Communication(
            comment_type=CommentType.SUGGESTION, proposed_comment="See observation."
        ),
    )


@pytest.fixture
def finding_factory():
    return make_finding
