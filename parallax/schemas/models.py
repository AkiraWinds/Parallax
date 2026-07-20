"""Canonical schema for Parallax review findings and reports.

Mirrors Evidence_Driven_PR_Review_System_Spec.md Section 11 (Canonical
Integration Schema) and Section 22 (Output Report). These models are what
a dispatched subagent's returned output is validated against (Section
16.2 partial-failure handling) and what report_builder.py renders into
Markdown.
"""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SourceSystem(str, Enum):
    PARALLAX = "parallax"
    SANYI = "sanyi"


class SourceType(str, Enum):
    NATIVE = "native"
    ADAPTED = "adapted"


class LensCategory(str, Enum):
    CORRECTNESS = "correctness"
    RELIABILITY = "reliability"
    SECURITY = "security"
    DATA = "data"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    OPERATIONS = "operations"
    AGENT_BEHAVIOR = "agent_behavior"
    EVALUATION = "evaluation"
    COMMUNICATION = "communication"


class EvidenceState(str, Enum):
    VERIFIED = "verified"
    SUPPORTED = "supported"
    HYPOTHESIS = "hypothesis"
    QUESTION = "question"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NativeSeverity(str, Enum):
    BLOCKER = "blocker"
    WARNING = "warning"
    INFO = "info"
    NOTICE = "notice"


class MergeImpact(str, Enum):
    BLOCKER = "blocker"
    IMPORTANT = "important"
    QUESTION = "question"
    SUGGESTION = "suggestion"
    NIT = "nit"


class UnknownableLevel(str, Enum):
    """Shared by user_impact / blast_radius (Section 11.1)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class Recoverability(str, Enum):
    EASY = "easy"
    MODERATE = "moderate"
    DIFFICULT = "difficult"
    UNKNOWN = "unknown"


class CommentType(str, Enum):
    REQUEST_CHANGE = "request_change"
    QUESTION = "question"
    SUGGESTION = "suggestion"
    NIT = "nit"


class MergeDecision(str, Enum):
    APPROVE = "approve"
    COMMENT = "comment"
    REQUEST_CHANGES = "request_changes"
    INSUFFICIENT_CONTEXT = "insufficient_context"


class SubagentLetter(str, Enum):
    """The seven dispatchable subagents (parent spec Section 16.2)."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class SubagentStatus(str, Enum):
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED_AFTER_RETRIES = "failed_after_retries"


# ---------------------------------------------------------------------------
# Finding sub-models (Section 11.1)
# ---------------------------------------------------------------------------


class Source(BaseModel):
    system: SourceSystem
    source_id: str | None = None
    source_type: SourceType
    source_contract_entry: str | None = None

    @model_validator(mode="after")
    def _system_and_type_agree(self) -> "Source":
        """Section 12.1/12.2: a Parallax-native finding is native; a
        SANYI finding has been mapped into the canonical schema, so it is
        adapted. This is what 'never invent or rewrite violation codes'
        cashes out to at the schema level — a SANYI finding claiming to
        be 'native' would mean its code/severity were authored fresh
        instead of preserved from SANYI's own taxonomy.
        """
        expected = {
            SourceSystem.PARALLAX: SourceType.NATIVE,
            SourceSystem.SANYI: SourceType.ADAPTED,
        }[self.system]
        if self.source_type != expected:
            raise ValueError(
                f"source.system={self.system.value} must have "
                f"source_type={expected.value} (parent spec Section 12.1/12.2)"
            )
        return self


class Profile(BaseModel):
    general: bool = True
    agent_system: bool = False


class Lens(BaseModel):
    category: LensCategory
    subcategory: str | None = None


class Status(BaseModel):
    evidence_state: EvidenceState
    confidence: Confidence


class FileLocation(BaseModel):
    path: str
    start_line: int | None = None
    end_line: int | None = None

    @model_validator(mode="after")
    def _line_range_is_ordered(self) -> "FileLocation":
        if (
            self.start_line is not None
            and self.end_line is not None
            and self.end_line < self.start_line
        ):
            raise ValueError("end_line must be >= start_line")
        return self


class Location(BaseModel):
    files: list[FileLocation] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)


class Claim(BaseModel):
    title: str
    observation: str
    failure_scenario: str | None = None
    impact: str | None = None


class EvidenceItem(BaseModel):
    type: str
    reference: str
    detail: str | None = None


class Evidence(BaseModel):
    direct: list[EvidenceItem] = Field(default_factory=list)
    supporting: list[EvidenceItem] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    verification_attempted: list[str] = Field(default_factory=list)
    remaining_uncertainty: list[str] = Field(default_factory=list)


class SourceSemantics(BaseModel):
    native_severity: NativeSeverity | None = None
    native_code: str | None = None


class ReviewAssessment(BaseModel):
    merge_impact: MergeImpact
    blocking_rationale: str | None = None
    user_impact: UnknownableLevel = UnknownableLevel.UNKNOWN
    blast_radius: UnknownableLevel = UnknownableLevel.UNKNOWN
    recoverability: Recoverability = Recoverability.UNKNOWN


class RecommendationOption(BaseModel):
    description: str
    tradeoffs: str | None = None


class Recommendation(BaseModel):
    options: list[RecommendationOption] = Field(default_factory=list)
    validation: list[str] = Field(default_factory=list)


class Communication(BaseModel):
    comment_type: CommentType
    proposed_comment: str


# ---------------------------------------------------------------------------
# ReviewFinding (Section 11.1 top-level schema)
# ---------------------------------------------------------------------------

_FINDING_ID_PATTERN = re.compile(r"^PR-([A-G])-(\d{3,})$")


class ReviewFinding(BaseModel):
    review_finding_id: str
    source: Source
    profile: Profile
    lens: Lens
    status: Status
    location: Location
    claim: Claim
    evidence: Evidence
    source_semantics: SourceSemantics = Field(default_factory=SourceSemantics)
    review_assessment: ReviewAssessment
    recommendation: Recommendation = Field(default_factory=Recommendation)
    communication: Communication

    @field_validator("review_finding_id")
    @classmethod
    def _id_is_namespaced_per_subagent(cls, value: str) -> str:
        """Section 13.4: IDs are PR-<letter>-NNN, prefixed per subagent.

        Enforced here (not just by convention) because up to seven
        subagents assign IDs concurrently — a malformed or
        non-namespaced ID is exactly the collision risk Section 13.4
        exists to prevent.
        """
        if not _FINDING_ID_PATTERN.match(value):
            raise ValueError(
                f"review_finding_id {value!r} must match PR-<A-G>-<NNN>, "
                "e.g. PR-B-001 (parent spec Section 13.4)"
            )
        return value

    @property
    def source_subagent_letter(self) -> str:
        match = _FINDING_ID_PATTERN.match(self.review_finding_id)
        assert match is not None  # guaranteed by the validator above
        return match.group(1)

    @model_validator(mode="after")
    def _hypothesis_or_question_not_asserted_as_verified(self) -> "ReviewFinding":
        """Section 20: a hypothesis/question must not be phrased as a
        confirmed defect. We can't police prose, but we can refuse the
        one purely mechanical contradiction: claiming 'verified' evidence
        while the merge impact records missing-context uncertainty.
        """
        if (
            self.status.evidence_state == EvidenceState.QUESTION
            and self.review_assessment.merge_impact
            not in (MergeImpact.QUESTION, MergeImpact.SUGGESTION, MergeImpact.NIT)
        ):
            raise ValueError(
                "a finding with evidence_state=question (missing context) "
                "cannot carry merge_impact="
                f"{self.review_assessment.merge_impact.value} "
                "(main spec Section 20/14.2) — use merge_impact=question"
            )
        return self


# ---------------------------------------------------------------------------
# Report models (Section 22)
# ---------------------------------------------------------------------------

SUBAGENT_NAMES: dict[SubagentLetter, str] = {
    SubagentLetter.A: "Intent, Correctness & Testing",
    SubagentLetter.B: "Reliability & Operations",
    SubagentLetter.C: "Security, Privacy & Data",
    SubagentLetter.D: "Architecture & Documentation",
    SubagentLetter.E: "Agent Runtime & Tooling",
    SubagentLetter.F: "Accountability & Safeguards",
    SubagentLetter.G: "SANYI",
}


class SubagentDispatchEntry(BaseModel):
    letter: SubagentLetter
    dispatched: bool
    status: SubagentStatus | None = None
    skip_reason: str | None = None

    @model_validator(mode="after")
    def _status_and_skip_reason_are_consistent(self) -> "SubagentDispatchEntry":
        if self.dispatched and self.status is None:
            raise ValueError("a dispatched subagent must record a status")
        if not self.dispatched and self.status is not None:
            raise ValueError("a non-dispatched subagent must not record a status")
        if not self.dispatched and not self.skip_reason:
            raise ValueError(
                "a skipped subagent must record why (Section 22's Subagent "
                "Dispatch section exists so coverage gaps are explicit)"
            )
        return self

    @property
    def name(self) -> str:
        return SUBAGENT_NAMES[self.letter]


class SanyiSummary(BaseModel):
    contract_found: bool
    review_invoked: bool
    source_verdict: str | None = None
    findings_imported: int = 0


class ReviewReport(BaseModel):
    overall_understanding: str
    review_contract: str
    change_and_execution_map: str
    strengths: str
    blocking_findings: list[ReviewFinding] = Field(default_factory=list)
    important_findings: list[ReviewFinding] = Field(default_factory=list)
    questions_and_hypotheses: list[ReviewFinding] = Field(default_factory=list)
    suggestions: list[ReviewFinding] = Field(default_factory=list)
    testing_evaluation_assessment: str
    definition_of_done_assessment: str
    subagent_dispatch: list[SubagentDispatchEntry]
    sanyi_summary: SanyiSummary | None = None
    merge_decision: MergeDecision

    @field_validator("subagent_dispatch")
    @classmethod
    def _exactly_one_entry_per_letter(
        cls, value: list[SubagentDispatchEntry]
    ) -> list[SubagentDispatchEntry]:
        """Acceptance criterion 14 (Section 29): each of the seven
        subagents' dispatch condition must be represented in the report,
        not silently dropped."""
        letters = [entry.letter for entry in value]
        if sorted(letters, key=lambda l: l.value) != list(SubagentLetter):
            raise ValueError(
                "subagent_dispatch must contain exactly one entry for each "
                "of A-G (parent spec Section 22, Section 29 criterion 14)"
            )
        return value

    @model_validator(mode="after")
    def _sanyi_summary_matches_dispatch(self) -> "ReviewReport":
        g_entry = next(
            e for e in self.subagent_dispatch if e.letter == SubagentLetter.G
        )
        if g_entry.dispatched and self.sanyi_summary is None:
            raise ValueError(
                "Subagent G was dispatched but no sanyi_summary was provided"
            )
        return self


# ---------------------------------------------------------------------------
# Interview mode (Section 23)
# ---------------------------------------------------------------------------


class MainConcern(BaseModel):
    observation: str
    scenario: str
    impact: str
    recommendation: str
    validation: str
    blocking_status: str


class InterviewWalkthrough(BaseModel):
    summary_60s: str
    approach: str
    strengths: str
    main_concerns: list[MainConcern]
    clarifying_questions: list[str] = Field(default_factory=list)
    alternatives_and_tradeoffs: str
    testing_evaluation_strategy: str
    new_constraints_effect: str
    final_recommendation: MergeDecision

    @field_validator("main_concerns")
    @classmethod
    def _at_most_three_main_concerns(cls, value: list[MainConcern]) -> list[MainConcern]:
        """Section 10 Stage 10 / Section 23: 'top three concerns' —
        the walkthrough is meant to force prioritization, not list
        everything."""
        if len(value) > 3:
            raise ValueError(
                "interview mode surfaces at most the top three concerns "
                "(parent spec Section 23) — pick the three with the "
                "highest merge impact"
            )
        return value
