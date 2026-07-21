"""End-to-end CLI tests, run as real subprocesses.

This is the actual integration point: an agent's `Bash` tool runs `uv run
python -m parallax.cli <subcommand>` exactly the way these tests do — a
unit test that calls `cmd_dedup(...)` directly would miss a broken
`__main__`, a broken subparser wiring, or a JSON encoding bug that only
shows up when going through a real process boundary. That's what caused
the original integration gap this module fixes: the orchestration code
was fully correct and fully unreachable from any agent.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from tests.conftest import make_finding


def run_cli(*args: str, input_obj=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "parallax.cli", *args],
        input=json.dumps(input_obj) if input_obj is not None else None,
        capture_output=True,
        text=True,
    )


class TestValidateFinding:
    def test_valid_finding_passes(self):
        finding = make_finding().model_dump(mode="json")
        result = run_cli("validate-finding", input_obj=finding)
        assert result.returncode == 0
        assert json.loads(result.stdout) == {"valid": True}

    def test_bad_id_fails_with_errors(self):
        finding = make_finding().model_dump(mode="json")
        finding["review_finding_id"] = "not-a-valid-id"
        result = run_cli("validate-finding", input_obj=finding)
        assert result.returncode == 1
        payload = json.loads(result.stdout)
        assert payload["valid"] is False
        assert payload["errors"]


class TestValidateReport:
    def test_missing_subagent_letter_fails(self):
        result = run_cli(
            "validate-report",
            input_obj={
                "overall_understanding": "...",
                "review_contract": "...",
                "change_and_execution_map": "...",
                "strengths": "...",
                "testing_evaluation_assessment": "...",
                "definition_of_done_assessment": "...",
                "subagent_dispatch": [],
                "merge_decision": "comment",
            },
        )
        assert result.returncode == 1
        assert json.loads(result.stdout)["valid"] is False


class TestDedup:
    def test_clusters_overlapping_findings(self):
        a = make_finding("PR-A-001", path="x.py", start_line=1, end_line=10)
        b = make_finding("PR-B-001", path="x.py", start_line=5, end_line=15)
        c = make_finding("PR-C-001", path="y.py", start_line=1, end_line=5)
        payload = [f.model_dump(mode="json") for f in (a, b, c)]
        result = run_cli("dedup", input_obj=payload)
        assert result.returncode == 0
        clusters = json.loads(result.stdout)
        assert sorted(clusters, key=str) == sorted(
            [["PR-A-001", "PR-B-001"], ["PR-C-001"]], key=str
        )


class TestBucket:
    def test_buckets_by_merge_impact_and_evidence_state(self):
        from parallax.schemas.models import EvidenceState, MergeImpact

        blocker = make_finding("PR-A-001", merge_impact=MergeImpact.BLOCKER)
        question = make_finding(
            "PR-A-002", evidence_state=EvidenceState.QUESTION, merge_impact=MergeImpact.QUESTION
        )
        payload = [f.model_dump(mode="json") for f in (blocker, question)]
        result = run_cli("bucket", input_obj=payload)
        assert result.returncode == 0
        buckets = json.loads(result.stdout)
        assert buckets["blocking_findings"] == ["PR-A-001"]
        assert buckets["questions_and_hypotheses"] == ["PR-A-002"]


class TestSanyiDefaultImpact:
    @pytest.mark.parametrize(
        "severity,expected",
        [("blocker", "blocker"), ("warning", "important"), ("info", "suggestion")],
    )
    def test_matches_section_12_1_examples(self, severity, expected):
        result = run_cli("sanyi-default-impact", input_obj={"severity": severity})
        assert result.returncode == 0
        assert json.loads(result.stdout) == {"merge_impact": expected}


class TestDetectSignals:
    def test_triggers_on_llm_sdk_import(self):
        payload = {"files": {"backend/agents/router.py": "import anthropic\n"}}
        result = run_cli("detect-signals", input_obj=payload)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["triggered"] is True
        assert "llm_sdk_import" in data["matched_signals"]

    def test_no_signals_on_plain_code(self):
        payload = {"files": {"src/orders.py": "def get_order(id): return db.get(id)\n"}}
        result = run_cli("detect-signals", input_obj=payload)
        assert json.loads(result.stdout)["triggered"] is False


class TestDiffScope:
    def test_reports_no_base_branch_error_as_json(self, tmp_path):
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)
        (tmp_path / "f.txt").write_text("x\n")
        subprocess.run(["git", "add", "f.txt"], cwd=tmp_path, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

        result = run_cli("diff-scope", "--repo-path", str(tmp_path))
        assert result.returncode == 1
        assert json.loads(result.stdout)["error"] == "no_base_branch"

    def test_reports_staged_changes(self, tmp_path):
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)
        (tmp_path / "f.txt").write_text("x\n")
        subprocess.run(["git", "add", "f.txt"], cwd=tmp_path, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
        (tmp_path / "g.txt").write_text("y\n")
        subprocess.run(["git", "add", "g.txt"], cwd=tmp_path, check=True)

        result = run_cli("diff-scope", "--repo-path", str(tmp_path))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["mode"] == "staged"
        assert data["changed_files"] == ["g.txt"]

    def test_git_failure_is_clean_json_not_a_traceback(self, tmp_path):
        """Reproduces the class of failure a user hit in production:
        `git diff --cached --name-only` failing for a repo-specific
        reason (there, a conflicting local `diff` alias; here, a
        corrupted `HEAD` — git rejects `--cached` once there's no valid
        HEAD to compare against). Before this fix, this surfaced as a
        bare Python traceback on stdout instead of the CLI's usual JSON
        contract."""
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        (tmp_path / ".git" / "HEAD").write_text("garbage, not a ref\n")

        result = run_cli("diff-scope", "--repo-path", str(tmp_path))
        assert result.returncode == 1
        data = json.loads(result.stdout)  # must parse as JSON, not a traceback
        assert data["error"] == "git_command_failed"
        assert "--cached" in data["message"]


class TestRenderReport:
    def test_renders_markdown_matching_golden_via_cli(self):
        from tests.fixtures.sample_report import build_sample_report
        from parallax.orchestration.report_builder import build_review_report

        report = build_sample_report()
        result = run_cli("render-report", input_obj=report.model_dump(mode="json"))
        assert result.returncode == 0
        assert result.stdout == build_review_report(report)

    def test_invalid_report_fails_with_nonzero_exit(self):
        result = run_cli("render-report", input_obj={"not": "a report"})
        assert result.returncode == 1
        assert result.stdout == ""


class TestRenderInterview:
    def test_renders_expected_headers(self):
        payload = {
            "summary_60s": "...",
            "approach": "...",
            "strengths": "...",
            "main_concerns": [],
            "alternatives_and_tradeoffs": "...",
            "testing_evaluation_strategy": "...",
            "new_constraints_effect": "...",
            "final_recommendation": "approve",
        }
        result = run_cli("render-interview", input_obj=payload)
        assert result.returncode == 0
        assert "# PR Review Interview Walkthrough" in result.stdout
        assert "approve" in result.stdout
