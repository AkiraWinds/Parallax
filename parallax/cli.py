"""Command-line entry point exposing `parallax/orchestration/` and
`parallax/schemas/` to agents via `Bash` (`uv run python -m parallax.cli
<subcommand>`).

This exists because a Claude Code (sub)agent can only reach code through
tool calls — a plain importable Python function is invisible to it. Every
subcommand reads one JSON document (via `--input <path>` or stdin) and
writes one JSON document (or, for the two `render-*` commands, plain
Markdown) to stdout, so an agent's `Bash` call is a single round trip:
write the payload to a scratch file, run the command, read the result.

Each subcommand is a thin wrapper around an already-tested pure function
in `parallax/orchestration/` or `parallax/schemas/` — this module adds no
logic of its own beyond argument parsing and JSON (de)serialization.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError

from parallax.orchestration.deduplication import find_duplicate_clusters
from parallax.orchestration.diff_scope import GitCommandError, NoBaseBranchError, resolve_diff_scope
from parallax.orchestration.prioritization import (
    bucket_findings,
    default_merge_impact_for_sanyi_severity,
    sort_by_merge_impact,
)
from parallax.orchestration.profile_detection import detect_agent_system_signals
from parallax.orchestration.report_builder import (
    build_interview_walkthrough,
    build_review_report,
)
from parallax.schemas.models import (
    InterviewWalkthrough,
    NativeSeverity,
    ReviewFinding,
    ReviewReport,
)

_FindingList = TypeAdapter(list[ReviewFinding])


def _read_input(args: argparse.Namespace) -> Any:
    raw = Path(args.input).read_text() if args.input else sys.stdin.read()
    return json.loads(raw)


def _emit(payload: Any) -> None:
    print(json.dumps(payload, indent=2, default=str))


def _emit_validation_error(exc: ValidationError) -> None:
    _emit({"valid": False, "errors": json.loads(exc.json())})


# --- subcommands -------------------------------------------------------------


def cmd_validate_finding(args: argparse.Namespace) -> int:
    """Section 16.2 partial-failure handling: does a subagent's returned
    finding validate against the canonical schema? Also usable by a
    subagent on itself before returning (Stage 6 self-verification,
    parallax-shared/references/evidence-model.md)."""
    try:
        ReviewFinding.model_validate(_read_input(args))
    except ValidationError as exc:
        _emit_validation_error(exc)
        return 1
    _emit({"valid": True})
    return 0


def cmd_validate_report(args: argparse.Namespace) -> int:
    """Same as validate-finding, for a full ReviewReport payload — used
    before finalizing the report (Section 22) or interview walkthrough."""
    try:
        ReviewReport.model_validate(_read_input(args))
    except ValidationError as exc:
        _emit_validation_error(exc)
        return 1
    _emit({"valid": True})
    return 0


def cmd_dedup(args: argparse.Namespace) -> int:
    """Section 13.1's deterministic pre-filter. Input: a JSON list of
    findings. Output: a list of clusters, each a list of
    `review_finding_id`s — the orchestrator still does the semantic
    judgment (13.2) within each cluster; this only groups candidates."""
    try:
        findings = _FindingList.validate_python(_read_input(args))
    except ValidationError as exc:
        _emit_validation_error(exc)
        return 1
    clusters = find_duplicate_clusters(findings)
    _emit([sorted(f.review_finding_id for f in cluster) for cluster in clusters])
    return 0


def cmd_bucket(args: argparse.Namespace) -> int:
    """Section 22 report buckets, sorted by merge impact (Section 14.2).
    Input: a JSON list of findings, already carrying their final
    merge_impact/evidence_state. Output: the four bucket names mapped to
    ordered lists of `review_finding_id`s."""
    try:
        findings = _FindingList.validate_python(_read_input(args))
    except ValidationError as exc:
        _emit_validation_error(exc)
        return 1
    buckets = bucket_findings(findings)
    _emit({name: [f.review_finding_id for f in fs] for name, fs in buckets.items()})
    return 0


def cmd_sanyi_default_impact(args: argparse.Namespace) -> int:
    """Section 12.1's default SANYI-severity -> merge_impact mapping.
    Input: `{"severity": "blocker" | "warning" | "info" | "notice"}`."""
    data = _read_input(args)
    severity = NativeSeverity(data["severity"])
    impact = default_merge_impact_for_sanyi_severity(severity)
    _emit({"merge_impact": impact.value})
    return 0


def cmd_detect_signals(args: argparse.Namespace) -> int:
    """Section 9.2 path 2 fallback: `{"files": {"<path>": "<content>"}}`."""
    data = _read_input(args)
    result = detect_agent_system_signals(data["files"])
    _emit(
        {
            "triggered": result.triggered,
            "matched_signals": result.matched_signals,
            "matched_files": result.matched_files,
        }
    )
    return 0


def cmd_diff_scope(args: argparse.Namespace) -> int:
    """Shared staged/working-tree/branch-diff fallback order (Section 10
    Stage 1; `.claude/skills/sanyi` "Mode: review"). Takes plain flags,
    not JSON, since both are optional and there is nothing to validate."""
    try:
        scope = resolve_diff_scope(repo_path=args.repo_path, base_branch=args.base_branch)
    except NoBaseBranchError as exc:
        _emit({"error": "no_base_branch", "message": str(exc)})
        return 1
    except GitCommandError as exc:
        _emit({"error": "git_command_failed", "message": str(exc)})
        return 1
    _emit(
        {
            "mode": scope.mode.value,
            "changed_files": scope.changed_files,
            "base_ref": scope.base_ref,
        }
    )
    return 0


def cmd_render_report(args: argparse.Namespace) -> int:
    """Section 22's exact Markdown structure. Input: a full ReviewReport
    JSON object. Output: Markdown (not JSON) on stdout."""
    try:
        report = ReviewReport.model_validate(_read_input(args))
    except ValidationError as exc:
        print(exc.json(), file=sys.stderr)
        return 1
    print(build_review_report(report), end="")
    return 0


def cmd_render_interview(args: argparse.Namespace) -> int:
    """Section 23's exact Markdown structure. Input: an InterviewWalkthrough
    JSON object. Output: Markdown (not JSON) on stdout."""
    try:
        walkthrough = InterviewWalkthrough.model_validate(_read_input(args))
    except ValidationError as exc:
        print(exc.json(), file=sys.stderr)
        return 1
    print(build_interview_walkthrough(walkthrough), end="")
    return 0


# --- wiring -------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="parallax.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    json_input_commands = {
        "validate-finding": cmd_validate_finding,
        "validate-report": cmd_validate_report,
        "dedup": cmd_dedup,
        "bucket": cmd_bucket,
        "sanyi-default-impact": cmd_sanyi_default_impact,
        "detect-signals": cmd_detect_signals,
        "render-report": cmd_render_report,
        "render-interview": cmd_render_interview,
    }
    for name, handler in json_input_commands.items():
        doc_lines = (handler.__doc__ or "").strip().splitlines()
        p = sub.add_parser(name, help=doc_lines[0] if doc_lines else "")
        p.add_argument(
            "--input",
            help="path to a JSON input file (default: read JSON from stdin)",
        )
        p.set_defaults(handler=handler)

    diff_scope_parser = sub.add_parser(
        "diff-scope", help=(cmd_diff_scope.__doc__ or "").strip().splitlines()[0]
    )
    diff_scope_parser.add_argument("--repo-path", default=".")
    diff_scope_parser.add_argument("--base-branch", default=None)
    diff_scope_parser.set_defaults(handler=cmd_diff_scope)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except Exception as exc:  # last-resort: a Bash caller gets clean JSON
        # and a nonzero exit, never a bare Python traceback, even for a
        # failure mode no subcommand's own try/except anticipated.
        _emit({"error": type(exc).__name__, "message": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
