"""Schema validation tests (Section 27.1: 'schema validation').

Covers finding-ID namespacing (Section 13.4), the evidence/merge-impact
consistency rule (Section 20), the seven-subagent dispatch invariant
(Section 22, Section 29 criterion 14), and that the committed JSON Schema
exports have not drifted from the live Pydantic models (Section 25.1's
"canonical schema" requirement — a schema nobody keeps in sync is not a
real guardrail).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from parallax.schemas.export_schemas import EXPORTS
from parallax.schemas.models import (
    EvidenceState,
    MergeImpact,
    ReviewReport,
    SanyiSummary,
    SubagentDispatchEntry,
    SubagentLetter,
    SubagentStatus,
)
from tests.conftest import make_finding


class TestFindingIdNamespacing:
    @pytest.mark.parametrize("letter", ["A", "B", "C", "D", "E", "F", "G"])
    def test_accepts_every_subagent_letter(self, letter):
        make_finding(f"PR-{letter}-001")

    @pytest.mark.parametrize(
        "bad_id",
        ["PR-001", "PR-H-001", "PR-A-1", "pr-a-001", "PR-A-001-extra", "A-001"],
    )
    def test_rejects_non_namespaced_ids(self, bad_id):
        with pytest.raises(ValidationError):
            make_finding(bad_id)

    def test_source_subagent_letter_property(self):
        finding = make_finding("PR-G-042")
        assert finding.source_subagent_letter == "G"


class TestEvidenceMergeImpactConsistency:
    def test_question_evidence_with_blocker_impact_rejected(self):
        with pytest.raises(ValidationError):
            make_finding(
                evidence_state=EvidenceState.QUESTION,
                merge_impact=MergeImpact.BLOCKER,
            )

    def test_question_evidence_with_question_impact_allowed(self):
        make_finding(
            evidence_state=EvidenceState.QUESTION,
            merge_impact=MergeImpact.QUESTION,
        )

    def test_hypothesis_evidence_with_blocker_impact_allowed(self):
        # A hypothesis can still be a serious, plausible risk worth
        # blocking on pending verification — only the QUESTION state
        # (missing context, not risk severity) is constrained.
        make_finding(
            evidence_state=EvidenceState.HYPOTHESIS,
            merge_impact=MergeImpact.BLOCKER,
        )


def _dispatch_entries(**overrides: SubagentStatus | None) -> list[SubagentDispatchEntry]:
    entries = []
    for letter in SubagentLetter:
        if letter in overrides:
            status = overrides[letter]
            entries.append(
                SubagentDispatchEntry(letter=letter, dispatched=True, status=status)
            )
        else:
            entries.append(
                SubagentDispatchEntry(
                    letter=letter, dispatched=False, skip_reason="not applicable"
                )
            )
    return entries


class TestReviewReportDispatchInvariant:
    def _make_report(self, dispatch, sanyi_summary=None) -> ReviewReport:
        return ReviewReport(
            overall_understanding="...",
            review_contract="...",
            change_and_execution_map="...",
            strengths="...",
            testing_evaluation_assessment="...",
            definition_of_done_assessment="...",
            subagent_dispatch=dispatch,
            sanyi_summary=sanyi_summary,
            merge_decision="comment",
        )

    def test_requires_all_seven_letters(self):
        dispatch = _dispatch_entries(A=SubagentStatus.COMPLETED)[:-1]  # drop G
        with pytest.raises(ValidationError):
            self._make_report(dispatch)

    def test_accepts_full_dispatch_set(self):
        dispatch = _dispatch_entries(
            A=SubagentStatus.COMPLETED,
            B=SubagentStatus.COMPLETED,
            C=SubagentStatus.COMPLETED,
            D=SubagentStatus.COMPLETED,
        )
        report = self._make_report(dispatch)
        assert len(report.subagent_dispatch) == 7

    def test_dispatched_g_requires_sanyi_summary(self):
        dispatch = _dispatch_entries(
            A=SubagentStatus.COMPLETED, G=SubagentStatus.COMPLETED
        )
        with pytest.raises(ValidationError):
            self._make_report(dispatch)

        self._make_report(
            dispatch,
            sanyi_summary=SanyiSummary(contract_found=True, review_invoked=True),
        )

    def test_skipped_subagent_requires_reason(self):
        with pytest.raises(ValidationError):
            SubagentDispatchEntry(letter=SubagentLetter.E, dispatched=False)


class TestJsonSchemaExportsAreInSync:
    @pytest.mark.parametrize("filename,model", EXPORTS.items())
    def test_committed_schema_matches_live_model(self, filename, model):
        committed = json.loads((Path("parallax/schemas") / filename).read_text())
        live = model.model_json_schema()
        assert committed == live, (
            f"{filename} is stale — run "
            "`uv run python -m parallax.schemas.export_schemas`"
        )
