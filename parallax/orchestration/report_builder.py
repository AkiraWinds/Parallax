"""Render canonical review data into the Markdown structures defined by
Evidence_Driven_PR_Review_System_Spec.md Section 22 (Output Report) and
Section 23 (Interview Mode Output).

This module owns *structure*, not *content*: the prose inside each section
(overall understanding, findings' claims, etc.) is authored by the
orchestrator/subagents' own reasoning and simply passed through. What this
module guarantees deterministically is section order, exact headers, and
that all seven subagents' dispatch status is enumerated (Section 29
acceptance criterion 14) — the same guarantee already enforced by
`ReviewReport`'s own validators (parallax/schemas/models.py).
"""

from __future__ import annotations

from parallax.schemas.models import (
    InterviewWalkthrough,
    ReviewFinding,
    ReviewReport,
    SubagentLetter,
    SubagentStatus,
)


def _render_finding(finding: ReviewFinding) -> str:
    lines = [
        f"### {finding.review_finding_id} — {finding.claim.title}",
        f"- Evidence state: {finding.status.evidence_state.value} "
        f"(confidence: {finding.status.confidence.value})",
        f"- Merge impact: {finding.review_assessment.merge_impact.value}",
    ]
    if finding.location.files:
        locs = ", ".join(
            f"{f.path}:{f.start_line}-{f.end_line}"
            if f.start_line is not None
            else f.path
            for f in finding.location.files
        )
        lines.append(f"- Location: {locs}")
    lines.append(f"- Observation: {finding.claim.observation}")
    if finding.claim.failure_scenario:
        lines.append(f"- Failure scenario: {finding.claim.failure_scenario}")
    if finding.claim.impact:
        lines.append(f"- Impact: {finding.claim.impact}")
    if finding.review_assessment.blocking_rationale:
        lines.append(f"- Blocking rationale: {finding.review_assessment.blocking_rationale}")
    if finding.recommendation.options:
        for option in finding.recommendation.options:
            trade = f" ({option.tradeoffs})" if option.tradeoffs else ""
            lines.append(f"- Option: {option.description}{trade}")
    if finding.source.source_id:
        lines.append(
            f"- Source: {finding.source.system.value} ({finding.source.source_id})"
        )
    return "\n".join(lines)


def _render_findings_section(findings: list[ReviewFinding]) -> str:
    if not findings:
        return "_None._"
    return "\n\n".join(_render_finding(f) for f in findings)


def _render_dispatch_line(letter: SubagentLetter, entry_map: dict) -> str:
    entry = entry_map[letter]
    if not entry.dispatched:
        return f"- {letter.value} ({entry.name}): skipped ({entry.skip_reason})"
    status_text = (
        "completed" if entry.status == SubagentStatus.COMPLETED else "failed after retries"
    )
    return f"- {letter.value} ({entry.name}): dispatched / {status_text}"


def build_review_report(report: ReviewReport) -> str:
    """Render a `ReviewReport` into the exact Markdown structure of Section
    22. Assumes `report` already passed Pydantic validation (all seven
    subagent letters present, etc.)."""
    entry_map = {entry.letter: entry for entry in report.subagent_dispatch}
    dispatch_lines = "\n".join(
        _render_dispatch_line(letter, entry_map) for letter in SubagentLetter
    )

    sanyi_section = ""
    if report.sanyi_summary is not None:
        s = report.sanyi_summary
        sanyi_section = "\n".join(
            [
                "\n### SANYI\n",
                f"- contract found: {s.contract_found}",
                f"- review invoked: {s.review_invoked}",
                f"- source verdict: {s.source_verdict or 'n/a'}",
                f"- findings imported: {s.findings_imported}",
            ]
        )

    return "\n".join(
        [
            "# PR Review",
            "",
            "## 1. Overall Understanding",
            "",
            report.overall_understanding,
            "",
            "## 2. Review Contract",
            "",
            report.review_contract,
            "",
            "## 3. Change and Execution Map",
            "",
            report.change_and_execution_map,
            "",
            "## 4. What Looks Strong",
            "",
            report.strengths,
            "",
            "## 5. Blocking Findings",
            "",
            _render_findings_section(report.blocking_findings),
            "",
            "## 6. Important Findings",
            "",
            _render_findings_section(report.important_findings),
            "",
            "## 7. Questions and Unverified Hypotheses",
            "",
            _render_findings_section(report.questions_and_hypotheses),
            "",
            "## 8. Suggestions",
            "",
            _render_findings_section(report.suggestions),
            "",
            "## 9. Testing and Evaluation Assessment",
            "",
            report.testing_evaluation_assessment,
            "",
            "## 10. Definition of Done Assessment",
            "",
            report.definition_of_done_assessment,
            "",
            "## 11. Source-System Summary",
            "",
            "### Subagent Dispatch",
            "",
            dispatch_lines,
            sanyi_section,
            "",
            "## 12. Suggested Merge Decision",
            "",
            report.merge_decision.value,
            "",
        ]
    )


def _render_main_concern(index: int, concern) -> str:
    return "\n".join(
        [
            f"## Main Concern {index}",
            "",
            f"- observation: {concern.observation}",
            f"- scenario: {concern.scenario}",
            f"- impact: {concern.impact}",
            f"- recommendation: {concern.recommendation}",
            f"- validation: {concern.validation}",
            f"- blocking status: {concern.blocking_status}",
        ]
    )


def build_interview_walkthrough(walkthrough: InterviewWalkthrough) -> str:
    """Render an `InterviewWalkthrough` into the exact Markdown structure
    of Section 23."""
    concern_blocks = "\n\n".join(
        _render_main_concern(i + 1, c) for i, c in enumerate(walkthrough.main_concerns)
    )
    questions_block = (
        "\n".join(f"- {q}" for q in walkthrough.clarifying_questions)
        if walkthrough.clarifying_questions
        else "_None._"
    )

    return "\n".join(
        [
            "# PR Review Interview Walkthrough",
            "",
            "## 60-Second Summary",
            "",
            walkthrough.summary_60s,
            "",
            "## How I Approached the Review",
            "",
            walkthrough.approach,
            "",
            "## What the PR Does Well",
            "",
            walkthrough.strengths,
            "",
            concern_blocks,
            "",
            "## Clarifying Questions",
            "",
            questions_block,
            "",
            "## Alternative Designs and Trade-Offs",
            "",
            walkthrough.alternatives_and_tradeoffs,
            "",
            "## Testing and Evaluation Strategy",
            "",
            walkthrough.testing_evaluation_strategy,
            "",
            "## How New Constraints Would Change My Decision",
            "",
            walkthrough.new_constraints_effect,
            "",
            "## Final Merge Recommendation",
            "",
            walkthrough.final_recommendation.value,
            "",
        ]
    )
