"""Deduplication pre-filter tests (Section 27.1: 'deduplication').

Covers Section 13.1's rule directly: overlap alone is not enough
(category/symbol must also match), category match alone is not enough
(files must overlap), and transitive clustering across three findings.
"""

from __future__ import annotations

from parallax.orchestration.deduplication import find_duplicate_clusters
from parallax.schemas.models import LensCategory
from tests.conftest import make_finding


def _cluster_ids(clusters: list[list]) -> list[set[str]]:
    return [{f.review_finding_id for f in cluster} for cluster in clusters]


def test_non_overlapping_findings_stay_separate():
    a = make_finding("PR-A-001", path="src/one.py", start_line=1, end_line=5)
    b = make_finding("PR-B-001", path="src/two.py", start_line=1, end_line=5)
    clusters = find_duplicate_clusters([a, b])
    assert len(clusters) == 2


def test_overlapping_lines_and_matching_category_cluster_together():
    a = make_finding(
        "PR-B-001", path="src/x.py", start_line=10, end_line=20, category=LensCategory.RELIABILITY
    )
    g = make_finding(
        "PR-G-001", path="src/x.py", start_line=15, end_line=18, category=LensCategory.RELIABILITY
    )
    clusters = _cluster_ids(find_duplicate_clusters([a, g]))
    assert {"PR-B-001", "PR-G-001"} in clusters


def test_overlapping_lines_but_different_category_and_symbols_stay_separate():
    """The spec's own example (Section 13): a Reliability finding about a
    missing idempotency key and a SANYI JY-2 about schema growth on the
    same lines are two different problems, not one."""
    reliability = make_finding(
        "PR-B-001",
        path="src/x.py",
        start_line=10,
        end_line=20,
        category=LensCategory.RELIABILITY,
        symbols=["handle_request"],
    )
    sanyi = make_finding(
        "PR-G-001",
        path="src/x.py",
        start_line=10,
        end_line=20,
        category=LensCategory.ARCHITECTURE,
        symbols=["GlobalState"],
    )
    clusters = find_duplicate_clusters([reliability, sanyi])
    assert len(clusters) == 2


def test_matching_category_but_no_file_overlap_stay_separate():
    a = make_finding(
        "PR-A-001", path="src/one.py", start_line=1, end_line=5, category=LensCategory.SECURITY
    )
    b = make_finding(
        "PR-C-001", path="src/two.py", start_line=1, end_line=5, category=LensCategory.SECURITY
    )
    clusters = find_duplicate_clusters([a, b])
    assert len(clusters) == 2


def test_symbol_overlap_clusters_even_with_different_category():
    a = make_finding(
        "PR-A-001",
        path="src/x.py",
        start_line=1,
        end_line=5,
        category=LensCategory.CORRECTNESS,
        symbols=["retry_handler"],
    )
    b = make_finding(
        "PR-B-001",
        path="src/x.py",
        start_line=1,
        end_line=5,
        category=LensCategory.RELIABILITY,
        symbols=["retry_handler"],
    )
    clusters = _cluster_ids(find_duplicate_clusters([a, b]))
    assert {"PR-A-001", "PR-B-001"} in clusters


def test_transitive_clustering_across_three_findings():
    """A overlaps B, B overlaps C, A does not directly overlap C — all
    three should still land in one candidate cluster for the semantic
    pass to look at together (Section 13.1)."""
    a = make_finding(
        "PR-A-001", path="src/x.py", start_line=1, end_line=10, category=LensCategory.CORRECTNESS
    )
    b = make_finding(
        "PR-B-001", path="src/x.py", start_line=8, end_line=20, category=LensCategory.CORRECTNESS
    )
    c = make_finding(
        "PR-C-001", path="src/x.py", start_line=18, end_line=30, category=LensCategory.CORRECTNESS
    )
    clusters = _cluster_ids(find_duplicate_clusters([a, b, c]))
    assert clusters == [{"PR-A-001", "PR-B-001", "PR-C-001"}]


def test_finding_with_no_line_range_overlaps_whole_file():
    whole_file = make_finding(
        "PR-D-001", path="src/x.py", start_line=None, end_line=None, category=LensCategory.ARCHITECTURE
    )
    specific = make_finding(
        "PR-A-001", path="src/x.py", start_line=100, end_line=105, category=LensCategory.ARCHITECTURE
    )
    clusters = _cluster_ids(find_duplicate_clusters([whole_file, specific]))
    assert {"PR-D-001", "PR-A-001"} in clusters


def test_every_input_finding_appears_in_exactly_one_cluster():
    findings = [
        make_finding("PR-A-001", path="a.py"),
        make_finding("PR-B-001", path="b.py"),
        make_finding("PR-C-001", path="c.py"),
    ]
    clusters = find_duplicate_clusters(findings)
    all_ids = [f.review_finding_id for cluster in clusters for f in cluster]
    assert sorted(all_ids) == ["PR-A-001", "PR-B-001", "PR-C-001"]
