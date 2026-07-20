"""Builds the sample ReviewReport used by the report_builder golden test.

Kept as its own module (rather than inlined in the test) so the golden
markdown fixture (`review_report_golden.md`) has a single, obvious source
of truth to regenerate from if the report structure ever changes.
"""

from __future__ import annotations

from parallax.schemas.models import (
    Confidence,
    EvidenceState,
    LensCategory,
    MergeDecision,
    MergeImpact,
    NativeSeverity,
    ReviewReport,
    SanyiSummary,
    SourceSystem,
    SourceType,
    SubagentDispatchEntry,
    SubagentLetter,
    SubagentStatus,
)
from tests.conftest import make_finding


def build_sample_report() -> ReviewReport:
    blocker = make_finding(
        "PR-C-001",
        title="Retry may duplicate an external side effect",
        path="src/handler.py",
        start_line=10,
        end_line=20,
        category=LensCategory.RELIABILITY,
        evidence_state=EvidenceState.VERIFIED,
        merge_impact=MergeImpact.BLOCKER,
    )
    sanyi_finding = make_finding(
        "PR-G-001",
        title="Buyi invariant made bypassable",
        path="backend/security/masking.py",
        start_line=5,
        end_line=8,
        category=LensCategory.SECURITY,
        evidence_state=EvidenceState.VERIFIED,
        merge_impact=MergeImpact.BLOCKER,
        source_system=SourceSystem.SANYI,
        source_id="BY-2",
        source_type=SourceType.ADAPTED,
        native_severity=NativeSeverity.BLOCKER,
        native_code="BY-2",
    )
    question = make_finding(
        "PR-A-001",
        title="Unclear how partial success is surfaced to the caller",
        path="src/handler.py",
        start_line=30,
        end_line=35,
        category=LensCategory.CORRECTNESS,
        evidence_state=EvidenceState.QUESTION,
        merge_impact=MergeImpact.QUESTION,
    )

    dispatch = [
        SubagentDispatchEntry(letter=SubagentLetter.A, dispatched=True, status=SubagentStatus.COMPLETED),
        SubagentDispatchEntry(letter=SubagentLetter.B, dispatched=True, status=SubagentStatus.COMPLETED),
        SubagentDispatchEntry(letter=SubagentLetter.C, dispatched=True, status=SubagentStatus.COMPLETED),
        SubagentDispatchEntry(
            letter=SubagentLetter.D, dispatched=True, status=SubagentStatus.FAILED_AFTER_RETRIES
        ),
        SubagentDispatchEntry(
            letter=SubagentLetter.E, dispatched=False, skip_reason="Agent-System Extension not active"
        ),
        SubagentDispatchEntry(
            letter=SubagentLetter.F, dispatched=False, skip_reason="Agent-System Extension not active"
        ),
        SubagentDispatchEntry(letter=SubagentLetter.G, dispatched=True, status=SubagentStatus.COMPLETED),
    ]

    return ReviewReport(
        overall_understanding="This PR adds a retry wrapper around the payment webhook handler.",
        review_contract="General profile. No explicit agent-system declaration; no signals detected.",
        change_and_execution_map="input -> validate -> call payment provider -> persist -> ack",
        strengths="Test coverage for the happy path is thorough.",
        blocking_findings=[blocker, sanyi_finding],
        questions_and_hypotheses=[question],
        testing_evaluation_assessment="No test covers the partial-success path.",
        definition_of_done_assessment="Rollback plan is undocumented.",
        subagent_dispatch=dispatch,
        sanyi_summary=SanyiSummary(
            contract_found=True,
            review_invoked=True,
            source_verdict="This diff changes the change-contract structure.",
            findings_imported=1,
        ),
        merge_decision=MergeDecision.REQUEST_CHANGES,
    )
