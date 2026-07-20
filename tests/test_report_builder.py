"""Report rendering tests (Section 27.1: 'report rendering'; Section 27.3:
golden Markdown reports for stable output).

`review_report_golden.txt` is a plain-text fixture (not `.md`) on purpose:
a Markdown-aware formatter hook reformats `.md` files on write (e.g.
inserting a blank line after a heading), which would silently desync the
fixture from the builder's actual byte output and defeat the point of a
golden test.
"""

from __future__ import annotations

from pathlib import Path

from parallax.orchestration.report_builder import (
    build_interview_walkthrough,
    build_review_report,
)
from parallax.schemas.models import InterviewWalkthrough, MainConcern, MergeDecision
from tests.fixtures.sample_report import build_sample_report

_GOLDEN_PATH = Path("tests/fixtures/review_report_golden.txt")


def test_review_report_matches_golden_output():
    report = build_sample_report()
    rendered = build_review_report(report)
    golden = _GOLDEN_PATH.read_text()
    assert rendered == golden


def test_sections_appear_in_spec_order():
    report = build_sample_report()
    rendered = build_review_report(report)
    headers = [
        "## 1. Overall Understanding",
        "## 2. Review Contract",
        "## 3. Change and Execution Map",
        "## 4. What Looks Strong",
        "## 5. Blocking Findings",
        "## 6. Important Findings",
        "## 7. Questions and Unverified Hypotheses",
        "## 8. Suggestions",
        "## 9. Testing and Evaluation Assessment",
        "## 10. Definition of Done Assessment",
        "## 11. Source-System Summary",
        "## 12. Suggested Merge Decision",
    ]
    positions = [rendered.index(h) for h in headers]
    assert positions == sorted(positions)


def test_all_seven_subagents_enumerated_in_dispatch_section():
    report = build_sample_report()
    rendered = build_review_report(report)
    for letter in "ABCDEFG":
        assert f"- {letter} (" in rendered


def test_sanyi_source_preserved_distinctly_from_merge_impact():
    """Section 14 design principle: never collapse source severity into
    merge impact when rendering."""
    report = build_sample_report()
    rendered = build_review_report(report)
    assert "Source: sanyi (BY-2)" in rendered
    assert "Merge impact: blocker" in rendered


def test_interview_walkthrough_renders_expected_headers():
    walkthrough = InterviewWalkthrough(
        summary_60s="A retry wrapper was added around the payment webhook handler.",
        approach="Traced the change map, then checked reliability and SANYI dimensions.",
        strengths="Happy-path test coverage is thorough.",
        main_concerns=[
            MainConcern(
                observation="Retry catches every exception after the external write.",
                scenario="External service succeeds, client times out before commit.",
                impact="The external action may run more than once.",
                recommendation="Use an idempotency key.",
                validation="Add a partial-success integration test.",
                blocking_status="Blocking.",
            )
        ],
        clarifying_questions=["Does the payment provider support idempotency keys?"],
        alternatives_and_tradeoffs="Retry only before the external write; requires manual recovery.",
        testing_evaluation_strategy="Add a partial-success test; no evaluation harness applies here.",
        new_constraints_effect="If idempotency keys are unavailable, this becomes a hard blocker.",
        final_recommendation=MergeDecision.REQUEST_CHANGES,
    )
    rendered = build_interview_walkthrough(walkthrough)
    for header in [
        "# PR Review Interview Walkthrough",
        "## 60-Second Summary",
        "## How I Approached the Review",
        "## What the PR Does Well",
        "## Main Concern 1",
        "## Clarifying Questions",
        "## Alternative Designs and Trade-Offs",
        "## Testing and Evaluation Strategy",
        "## How New Constraints Would Change My Decision",
        "## Final Merge Recommendation",
    ]:
        assert header in rendered
    assert "request_changes" in rendered


def test_interview_walkthrough_omits_missing_main_concerns():
    walkthrough = InterviewWalkthrough(
        summary_60s="...",
        approach="...",
        strengths="...",
        main_concerns=[],
        alternatives_and_tradeoffs="...",
        testing_evaluation_strategy="...",
        new_constraints_effect="...",
        final_recommendation=MergeDecision.APPROVE,
    )
    rendered = build_interview_walkthrough(walkthrough)
    assert "## Main Concern 1" not in rendered
    assert "_None._" in rendered  # clarifying questions, none given
