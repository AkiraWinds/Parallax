"""Deterministic pre-filter for finding deduplication.

Implements Evidence_Driven_PR_Review_System_Spec.md Section 13.1: a purely
mechanical grouping of findings that *might* be duplicates, with no LLM
judgment involved. This exists specifically so that Section 13.2's semantic
merge decision is applied only within small pre-filtered clusters rather
than across the full cross-product of findings from all dispatched
subagents (Section 25.2 explicitly defers "LLM-based duplicate detection
without deterministic fallback" — this module is that fallback).

Two findings are pre-filter candidates when their file/line ranges overlap
AND (their lens.category matches OR their symbols overlap) — Section 13.1.
Clustering is transitive (union-find): if A overlaps B and B overlaps C,
all three land in one candidate cluster even if A and C don't directly
overlap, since the orchestrator's semantic pass (13.2) still needs to see
them together to decide.

The semantic "is this actually the same root cause" decision (Section
13.2) is NOT implemented here — that's real judgment the orchestrator
applies, bounded to the clusters this module produces.
"""

from __future__ import annotations

from config import DEDUPLICATION_LINE_TOLERANCE
from parallax.schemas.models import FileLocation, ReviewFinding


def _file_ranges_overlap(a: FileLocation, b: FileLocation) -> bool:
    if a.path != b.path:
        return False
    # A finding with no line range (e.g. a whole-file concern) is treated
    # as overlapping anything else in the same file — there is no narrower
    # range to compare against.
    if a.start_line is None or a.end_line is None:
        return True
    if b.start_line is None or b.end_line is None:
        return True
    a_start, a_end = a.start_line - DEDUPLICATION_LINE_TOLERANCE, a.end_line + DEDUPLICATION_LINE_TOLERANCE
    return a_start <= b.end_line and b.start_line <= a_end


def _locations_overlap(f1: ReviewFinding, f2: ReviewFinding) -> bool:
    return any(
        _file_ranges_overlap(loc1, loc2)
        for loc1 in f1.location.files
        for loc2 in f2.location.files
    )


def _category_or_symbol_matches(f1: ReviewFinding, f2: ReviewFinding) -> bool:
    if f1.lens.category == f2.lens.category:
        return True
    symbols1 = set(f1.location.symbols)
    symbols2 = set(f2.location.symbols)
    return bool(symbols1 & symbols2)


def _is_candidate_pair(f1: ReviewFinding, f2: ReviewFinding) -> bool:
    return _locations_overlap(f1, f2) and _category_or_symbol_matches(f1, f2)


class _UnionFind:
    def __init__(self, items: list[str]) -> None:
        self._parent = {item: item for item in items}

    def find(self, item: str) -> str:
        root = item
        while self._parent[root] != root:
            root = self._parent[root]
        self._parent[item] = root
        return root

    def union(self, a: str, b: str) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self._parent[root_a] = root_b


def find_duplicate_clusters(
    findings: list[ReviewFinding],
) -> list[list[ReviewFinding]]:
    """Group findings into candidate-duplicate clusters (Section 13.1).

    Returns a list of clusters; a finding with no overlap candidates comes
    back as its own singleton cluster. Every input finding appears in
    exactly one output cluster.
    """
    by_id = {f.review_finding_id: f for f in findings}
    uf = _UnionFind(list(by_id))

    for i, f1 in enumerate(findings):
        for f2 in findings[i + 1 :]:
            if _is_candidate_pair(f1, f2):
                uf.union(f1.review_finding_id, f2.review_finding_id)

    clusters: dict[str, list[ReviewFinding]] = {}
    for finding_id in by_id:
        root = uf.find(finding_id)
        clusters.setdefault(root, []).append(by_id[finding_id])

    return list(clusters.values())
