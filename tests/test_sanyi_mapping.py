"""SANYI mapping tests (Section 27.1: 'SANYI field mapping', 'source
preservation', 'severity separation').

Per Section 33.2, there is no code that parses a persisted SANYI report —
the `sanyi-review` subagent emits canonical findings directly from its own
reasoning pass. What *is* real code, and what these tests cover, is the
schema-level guarantee that a SANYI-sourced finding preserves its native
code/severity distinctly from Parallax's own merge-impact judgment
(Section 12.1's responsibilities list), plus the default severity mapping
table (Section 12.1's worked examples).

`tests/fixtures/sanyi_report_sample.md` is used only as the worked
example this test mirrors — see that file's own header for why it isn't
parsed by any production code.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from parallax.orchestration.prioritization import default_merge_impact_for_sanyi_severity
from parallax.schemas.models import (
    MergeImpact,
    NativeSeverity,
    SourceSystem,
    SourceType,
)
from tests.conftest import make_finding

_FIXTURE = Path("tests/fixtures/sanyi_report_sample.md")


def test_fixture_contains_the_worked_by2_example():
    text = _FIXTURE.read_text()
    assert "BY-2" in text
    assert "不易 Buyi" in text


def test_sanyi_finding_preserves_native_code_and_severity():
    """Mirrors the fixture's BY-2 finding: source_id/native_code/
    native_severity must all read back exactly as SANYI produced them —
    never invented or rewritten (Section 12.1)."""
    finding = make_finding(
        "PR-G-001",
        source_system=SourceSystem.SANYI,
        source_id="BY-2",
        source_type=SourceType.ADAPTED,
        native_severity=NativeSeverity.BLOCKER,
        native_code="BY-2",
    )
    assert finding.source.source_id == "BY-2"
    assert finding.source_semantics.native_code == "BY-2"
    assert finding.source_semantics.native_severity == NativeSeverity.BLOCKER


def test_sanyi_finding_must_be_adapted_not_native():
    """A SANYI-sourced finding claiming source_type=native would mean its
    code/severity were authored fresh rather than mapped from SANYI's own
    taxonomy — exactly what Section 12.1 forbids."""
    with pytest.raises(ValidationError):
        make_finding(
            source_system=SourceSystem.SANYI,
            source_id="BY-2",
            source_type=SourceType.NATIVE,
        )


def test_parallax_native_finding_must_not_claim_adapted():
    with pytest.raises(ValidationError):
        make_finding(source_system=SourceSystem.PARALLAX, source_type=SourceType.ADAPTED)


def test_merge_impact_is_independent_of_native_severity_value():
    """Section 14 design principle: source severity and merge impact are
    separate fields — setting one must never silently determine the
    other inside the schema itself (only the *default suggestion*
    function does that, and only when explicitly called)."""
    finding = make_finding(
        source_system=SourceSystem.SANYI,
        source_id="BY-2",
        source_type=SourceType.ADAPTED,
        native_severity=NativeSeverity.BLOCKER,
        merge_impact=MergeImpact.SUGGESTION,  # a human downgraded it (Section 14.2)
    )
    assert finding.source_semantics.native_severity == NativeSeverity.BLOCKER
    assert finding.review_assessment.merge_impact == MergeImpact.SUGGESTION


@pytest.mark.parametrize(
    "severity,expected",
    [
        (NativeSeverity.BLOCKER, MergeImpact.BLOCKER),  # BY-1..4
        (NativeSeverity.WARNING, MergeImpact.IMPORTANT),  # JY-1..3
        (NativeSeverity.INFO, MergeImpact.SUGGESTION),  # BN-1
        (NativeSeverity.NOTICE, MergeImpact.SUGGESTION),  # MG-1, UN-1, UN-2
    ],
)
def test_default_mapping_covers_every_sanyi_severity(severity, expected):
    assert default_merge_impact_for_sanyi_severity(severity) == expected
