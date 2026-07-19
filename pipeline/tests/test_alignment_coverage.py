"""Alignment-coverage regression guard: Murray/Butler milestone-tick density
per book must never drop below its recorded floor.

The floor values in fixtures/alignment_coverage_floor.json are the exact
Murray/Butler tick counts read off the live build/dist/{iliad,odyssey}/book-
NN.json on 2026-07-17 (Phase 6 QA pass), via
`homer_pipeline.preflight.murray_butler_tick_counts` — see that function's
docstring for why tick count is a meaningful density proxy. Pinning today's
healthy numbers as a floor means a future ingest regression (a milestone-
parsing bug, a re-export that drops anchors, ...) that thins out alignment
density fails this test loudly instead of shipping silently.

This test exercises the REAL current build, so it needs build/dist to exist
(`node scripts/build-public.mjs`, or a prior pipeline `all` run) — a fresh
checkout with no local TLG/Diogenes access has no build/dist yet, so the
whole module is skipped rather than failed in that case. The hermetic unit
tests for the underlying mechanism (murray_butler_tick_counts,
tick_coverage_violations) live in test_preflight.py and always run.
"""

import json
from pathlib import Path

import pytest

from homer_pipeline.preflight import murray_butler_tick_counts, tick_coverage_violations

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "build" / "dist"
FLOOR_PATH = Path(__file__).resolve().parent / "fixtures" / "alignment_coverage_floor.json"

FLOOR: dict[str, dict[int, dict[str, int]]] = {
    work: {int(book): counts for book, counts in books.items()}
    for work, books in json.loads(FLOOR_PATH.read_text(encoding="utf-8")).items()
}

pytestmark = pytest.mark.skipif(
    not DATA_DIR.exists(),
    reason="requires a local build/dist (node scripts/build-public.mjs or `homer_pipeline all`)",
)


@pytest.mark.parametrize("work_id", sorted(FLOOR))
def test_tick_coverage_meets_pinned_floor(work_id):
    if not (DATA_DIR / work_id).is_dir():
        pytest.skip(f"build/dist/{work_id} not present")
    counts = murray_butler_tick_counts(DATA_DIR, work_id)
    violations = tick_coverage_violations(counts, FLOOR[work_id])
    assert violations == [], f"{work_id}: " + "; ".join(violations)


@pytest.mark.parametrize("work_id", sorted(FLOOR))
def test_pinned_floor_covers_every_recorded_book(work_id):
    # The floor fixture should name every book the manifest declares (24 for
    # both epics) — a shrinking floor file would silently stop guarding books.
    if not (DATA_DIR / work_id).is_dir():
        pytest.skip(f"build/dist/{work_id} not present")
    assert sorted(FLOOR[work_id]) == list(range(1, 25))
