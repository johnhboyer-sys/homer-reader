import json
import subprocess
import sys
from pathlib import Path

import yaml

from homer_pipeline.preflight import WorkManifest, _validate_manifest_schema


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "pipeline" / "tests" / "fixtures" / "preflight"
MANIFESTS = ROOT / "manifests"


def _load_manifest(name: str) -> dict:
    return yaml.safe_load((MANIFESTS / name).read_text(encoding="utf-8"))


def _schema_problems(data: dict, name: str = "Euthyphro.yaml") -> list[str]:
    manifest = WorkManifest(work_id=data["work"]["id"], path=MANIFESTS / name, data=data)
    problems: list = []
    _validate_manifest_schema(manifest, problems)
    return [message for _work, _file, message in problems]


def _run_preflight(name: str) -> subprocess.CompletedProcess[str]:
    fixture = FIXTURES / name
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "homer_pipeline.preflight",
            str(fixture / "data"),
            str(fixture / "manifests"),
        ],
        cwd=ROOT / "pipeline",
        text=True,
        capture_output=True,
        check=False,
    )


def test_preflight_valid_fixture_passes():
    result = _run_preflight("valid")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "preflight ok:" in result.stdout


def test_preflight_broken_fixture_reports_bekker_order_and_dangling_reference():
    result = _run_preflight("broken")

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "Greek Bekker lines are out of order" in output
    assert "chapter '1' has dangling Bekker anchor 1094a5" in output


def test_preflight_schema_accepts_real_homer_manifests():
    # Verse-line manifests: no bekker_range/chapters/section_spine; books bounded
    # by book.line refs; expected_line_gaps use {book, after, next}.
    assert _schema_problems(_load_manifest("Iliad.yaml"), "Iliad.yaml") == []
    assert _schema_problems(_load_manifest("Odyssey.yaml"), "Odyssey.yaml") == []


def test_preflight_schema_rejects_bad_verse_ref():
    data = _load_manifest("Iliad.yaml")
    data["books"][0]["start"] = "1a1"  # Bekker-shaped, not book.line
    problems = _schema_problems(data, "Iliad.yaml")
    assert any("books[0].start must be a verse book.line ref" in p for p in problems)


def _apparatus_manifest() -> "WorkManifest":
    from homer_pipeline.preflight import WorkManifest

    return WorkManifest(
        work_id="testwork",
        path=MANIFESTS / "Iliad.yaml",
        data={"books": [{"n": 1, "start": "1.1", "end": "1.10"}], "expected_line_gaps": []},
    )


def _stub_epithets(data_dir, work_id: str = "testwork") -> None:
    # _validate_apparatus_epithets_emitted, _validate_apparatus_scansion_emitted,
    # and _validate_apparatus_vocab_emitted each require
    # build/dist/<work>/{epithets,scansion,vocab}.json to exist for every verse
    # work; tests that aren't exercising THOSE checks stub all three out so
    # they stay focused on what they actually test.
    work_dir = data_dir / work_id
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "epithets.json").write_text("{}", encoding="utf-8")
    (work_dir / "scansion.json").write_text("{}", encoding="utf-8")
    (work_dir / "vocab.json").write_text("{}", encoding="utf-8")


def test_validate_apparatus_skips_books_with_no_apparatus_yet(tmp_path):
    from homer_pipeline.preflight import _validate_apparatus

    _stub_epithets(tmp_path)
    problems: list = []
    _validate_apparatus(_apparatus_manifest(), tmp_path, {"book-01.json": {"book": 1}}, problems)
    assert problems == []


def test_validate_apparatus_accepts_clean_apparatus(tmp_path):
    from homer_pipeline.preflight import _validate_apparatus

    _stub_epithets(tmp_path)
    loaded = {
        "book-01.json": {
            "book": 1,
            "apparatus": {
                "argument": "A clean argument.",
                "who": ["A"],
                "draft": True,
                "scenes": [
                    {"lines": [1, 10], "summary": "ok", "location": "x", "dayNumber": 1}
                ],
            },
        }
    }
    problems: list = []
    _validate_apparatus(_apparatus_manifest(), tmp_path, loaded, problems)
    assert problems == []


def test_validate_apparatus_fails_loudly_on_missing_draft_flag_and_coverage_hole(tmp_path):
    from homer_pipeline.preflight import _validate_apparatus

    _stub_epithets(tmp_path)
    loaded = {
        "book-01.json": {
            "book": 1,
            "apparatus": {
                "argument": "A clean argument.",
                "scenes": [
                    {"lines": [1, 4], "summary": "ok", "location": "x", "dayNumber": 1},
                    {"lines": [6, 10], "summary": "ok", "location": "x", "dayNumber": 1},
                ],
            },
        }
    }
    problems: list = []
    _validate_apparatus(_apparatus_manifest(), tmp_path, loaded, problems)
    messages = [p[2] for p in problems]
    assert any("draft flag" in m for m in messages)
    assert any("coverage hole" in m for m in messages)


# ── Gate-4 hardening: apparatus/scenes/<work>.json coverage vs. the emit ────


def _scene(lo, hi, summary="A short factual summary of the scene.", location="camp", day=1):
    return {"lines": [lo, hi], "summary": summary, "location": location, "dayNumber": day}


def _canonical_scenes_doc(book_n: int = 1) -> dict:
    return {
        "work": "testwork",
        "status": "draft",
        "books": [
            {
                "book": book_n,
                "status": "draft",
                "argument": "A clean argument.",
                "where": ["Troy"],
                "who": ["A"],
                "days": "1",
                "scenes": [_scene(1, 10)],
            }
        ],
    }


def test_apparatus_scenes_coverage_passes_when_emit_matches_canonical(tmp_path, monkeypatch):
    from homer_pipeline import apparatus_scenes
    from homer_pipeline.preflight import _validate_apparatus_scenes_coverage

    scenes_dir = tmp_path / "scenes"
    scenes_dir.mkdir()
    canonical = _canonical_scenes_doc()
    (scenes_dir / "testwork.json").write_text(json.dumps(canonical), encoding="utf-8")
    monkeypatch.setattr(apparatus_scenes, "SCENES_DIR", scenes_dir)

    expected_scenes = apparatus_scenes.emit_book_apparatus(canonical["books"][0])["scenes"]
    loaded = {
        "book-01.json": {
            "book": 1,
            "apparatus": {"argument": "A clean argument.", "draft": True, "scenes": expected_scenes},
        }
    }
    problems: list = []
    _validate_apparatus_scenes_coverage(_apparatus_manifest(), loaded, problems)
    assert problems == []


def test_apparatus_scenes_coverage_fails_when_emitted_book_missing_apparatus(tmp_path, monkeypatch):
    # Reproduces the Gate-4 incident: canonical scenes.json covers book 1, but
    # the emitted book file carries no apparatus at all (a rebuild that
    # silently skipped the apparatus merge/emit stage).
    from homer_pipeline import apparatus_scenes
    from homer_pipeline.preflight import _validate_apparatus_scenes_coverage

    scenes_dir = tmp_path / "scenes"
    scenes_dir.mkdir()
    (scenes_dir / "testwork.json").write_text(json.dumps(_canonical_scenes_doc()), encoding="utf-8")
    monkeypatch.setattr(apparatus_scenes, "SCENES_DIR", scenes_dir)

    loaded = {"book-01.json": {"book": 1, "segments": []}}  # no "apparatus" key
    problems: list = []
    _validate_apparatus_scenes_coverage(_apparatus_manifest(), loaded, problems)
    messages = [p[2] for p in problems]
    assert any("missing or empty" in m for m in messages)


def test_apparatus_scenes_coverage_fails_when_emitted_scenes_diverge_from_canonical(tmp_path, monkeypatch):
    from homer_pipeline import apparatus_scenes
    from homer_pipeline.preflight import _validate_apparatus_scenes_coverage

    scenes_dir = tmp_path / "scenes"
    scenes_dir.mkdir()
    (scenes_dir / "testwork.json").write_text(json.dumps(_canonical_scenes_doc()), encoding="utf-8")
    monkeypatch.setattr(apparatus_scenes, "SCENES_DIR", scenes_dir)

    loaded = {
        "book-01.json": {
            "book": 1,
            "apparatus": {
                "argument": "Stale.",
                "draft": True,
                "scenes": [_scene(1, 10, summary="A stale, wrong summary.")],
            },
        }
    }
    problems: list = []
    _validate_apparatus_scenes_coverage(_apparatus_manifest(), loaded, problems)
    messages = [p[2] for p in problems]
    assert any("does not match" in m for m in messages)


def test_apparatus_scenes_coverage_noop_when_no_canonical_file(tmp_path, monkeypatch):
    from homer_pipeline import apparatus_scenes
    from homer_pipeline.preflight import _validate_apparatus_scenes_coverage

    monkeypatch.setattr(apparatus_scenes, "SCENES_DIR", tmp_path / "no-such-dir")
    problems: list = []
    _validate_apparatus_scenes_coverage(_apparatus_manifest(), {}, problems)
    assert problems == []


# ── speeches.json / epithets.json / characters.json / repetitions.json ─────


def test_apparatus_speeches_emitted_fails_when_source_exists_but_copy_missing(tmp_path, monkeypatch):
    from homer_pipeline import apparatus_scenes
    from homer_pipeline.preflight import _validate_apparatus_speeches_emitted

    apparatus_dir = tmp_path / "apparatus"
    (apparatus_dir / "speeches").mkdir(parents=True)
    (apparatus_dir / "speeches" / "testwork.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(apparatus_scenes, "APPARATUS_DIR", apparatus_dir)

    data_dir = tmp_path / "data"
    (data_dir / "testwork").mkdir(parents=True)
    problems: list = []
    _validate_apparatus_speeches_emitted(_apparatus_manifest(), data_dir, problems)
    messages = [p[2] for p in problems]
    assert any("was not copied" in m for m in messages)


def test_apparatus_speeches_emitted_passes_when_copied(tmp_path, monkeypatch):
    from homer_pipeline import apparatus_scenes
    from homer_pipeline.preflight import _validate_apparatus_speeches_emitted

    apparatus_dir = tmp_path / "apparatus"
    (apparatus_dir / "speeches").mkdir(parents=True)
    (apparatus_dir / "speeches" / "testwork.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(apparatus_scenes, "APPARATUS_DIR", apparatus_dir)

    data_dir = tmp_path / "data"
    (data_dir / "testwork").mkdir(parents=True)
    (data_dir / "testwork" / "speeches.json").write_text("[]", encoding="utf-8")
    problems: list = []
    _validate_apparatus_speeches_emitted(_apparatus_manifest(), data_dir, problems)
    assert problems == []


def test_apparatus_epithets_emitted_fails_when_missing(tmp_path):
    from homer_pipeline.preflight import _validate_apparatus_epithets_emitted

    data_dir = tmp_path / "data"
    (data_dir / "testwork").mkdir(parents=True)
    problems: list = []
    _validate_apparatus_epithets_emitted(_apparatus_manifest(), data_dir, problems)
    messages = [p[2] for p in problems]
    assert any("epithets.json was not emitted" in m for m in messages)


def test_apparatus_scansion_emitted_fails_when_missing(tmp_path):
    from homer_pipeline.preflight import _validate_apparatus_scansion_emitted

    data_dir = tmp_path / "data"
    (data_dir / "testwork").mkdir(parents=True)
    problems: list = []
    _validate_apparatus_scansion_emitted(_apparatus_manifest(), data_dir, problems)
    messages = [p[2] for p in problems]
    assert any("scansion.json was not emitted" in m for m in messages)


def test_apparatus_scansion_emitted_passes_when_present(tmp_path):
    from homer_pipeline.preflight import _validate_apparatus_scansion_emitted

    data_dir = tmp_path / "data"
    work_dir = data_dir / "testwork"
    work_dir.mkdir(parents=True)
    (work_dir / "scansion.json").write_text('{"work": "testwork", "lines": {}}', encoding="utf-8")
    problems: list = []
    _validate_apparatus_scansion_emitted(_apparatus_manifest(), data_dir, problems)
    assert problems == []


def test_apparatus_vocab_emitted_fails_when_missing(tmp_path):
    from homer_pipeline.preflight import _validate_apparatus_vocab_emitted

    data_dir = tmp_path / "data"
    (data_dir / "testwork").mkdir(parents=True)
    problems: list = []
    _validate_apparatus_vocab_emitted(_apparatus_manifest(), data_dir, problems)
    messages = [p[2] for p in problems]
    assert any("vocab.json was not emitted" in m for m in messages)


def test_apparatus_vocab_emitted_passes_when_present(tmp_path):
    from homer_pipeline.preflight import _validate_apparatus_vocab_emitted

    data_dir = tmp_path / "data"
    work_dir = data_dir / "testwork"
    work_dir.mkdir(parents=True)
    (work_dir / "vocab.json").write_text('{"status": "draft", "books": {}}', encoding="utf-8")
    problems: list = []
    _validate_apparatus_vocab_emitted(_apparatus_manifest(), data_dir, problems)
    assert problems == []


def test_validate_global_apparatus_emits_flags_missing_characters_and_repetitions(tmp_path, monkeypatch):
    from homer_pipeline import apparatus_scenes
    from homer_pipeline.preflight import WorkManifest, _validate_global_apparatus_emits

    apparatus_dir = tmp_path / "apparatus"
    apparatus_dir.mkdir()
    (apparatus_dir / "characters.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(apparatus_scenes, "APPARATUS_DIR", apparatus_dir)

    manifest = WorkManifest(
        work_id="iliad",
        path=MANIFESTS / "Iliad.yaml",
        data={"citation": {"scheme": "verse-line"}, "books": []},
    )
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    problems: list = []
    _validate_global_apparatus_emits(data_dir, [manifest], problems)
    messages = [p[2] for p in problems]
    assert any("characters.json exists but was not copied" in m for m in messages)
    assert any("repetitions.json was not emitted" in m for m in messages)


def test_validate_global_apparatus_emits_skips_non_verse_corpora(tmp_path, monkeypatch):
    from homer_pipeline import apparatus_scenes
    from homer_pipeline.preflight import WorkManifest, _validate_global_apparatus_emits

    apparatus_dir = tmp_path / "apparatus"
    apparatus_dir.mkdir()
    (apparatus_dir / "characters.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(apparatus_scenes, "APPARATUS_DIR", apparatus_dir)

    manifest = WorkManifest(work_id="EN", path=MANIFESTS / "Iliad.yaml", data={"books": []})
    problems: list = []
    _validate_global_apparatus_emits(tmp_path / "data", [manifest], problems)
    assert problems == []


# ── vulgate-numbering verifier: runs as part of preflight's book walk ──────


def _numbering_manifest(expected_gaps: list | None = None) -> "WorkManifest":
    from homer_pipeline.preflight import WorkManifest

    return WorkManifest(
        work_id="testwork",
        path=MANIFESTS / "Iliad.yaml",
        data={
            "books": [{"n": 1, "start": "1.1", "end": "1.10"}],
            "expected_line_gaps": expected_gaps or [],
        },
    )


def _numbering_doc(lines: list[int]) -> dict:
    return {
        "book": 1,
        "segments": [
            {
                "id": "1.1",
                "column": "1",
                "greek": [{"n": n, "tokens": []} for n in lines],
            }
        ],
    }


def test_preflight_flags_undeclared_verse_numbering_gap():
    from homer_pipeline.preflight import _validate_books

    loaded = {"book-01.json": _numbering_doc([1, 2, 5, 6])}
    problems: list = []
    _validate_books(_numbering_manifest(), loaded, problems, verse=True)
    messages = [p[2] for p in problems]
    assert any("unexpected verse gap 2 -> 5" in m for m in messages)


def test_preflight_honours_declared_verse_numbering_gap():
    from homer_pipeline.preflight import _validate_books

    loaded = {"book-01.json": _numbering_doc([1, 2, 5, 6])}
    manifest = _numbering_manifest([{"book": 1, "after": 2, "next": 5}])
    expected_gaps = {("1", 2, 5)}
    problems: list = []
    _validate_books(manifest, loaded, problems, expected_gaps=expected_gaps, verse=True)
    messages = [p[2] for p in problems]
    assert not any("verse gap" in m for m in messages)


# ── alignment coverage: Murray/Butler tick counts and the floor check ──────


def _book_with_ticks(book_n: int, murray_ticks: int, butler_ticks: int) -> dict:
    return {
        "book": book_n,
        "segments": [
            {
                "id": f"{book_n}.1",
                "column": str(book_n),
                "english": {"bekker": [{"n": i + 1, "offset": i, "real": True} for i in range(murray_ticks)]},
                "ross": [
                    {"bekker": [{"n": i + 1, "offset": i, "real": True} for i in range(butler_ticks)]}
                ],
            }
        ],
    }


def test_murray_butler_tick_counts_reads_bekker_marker_lists(tmp_path):
    from homer_pipeline.preflight import murray_butler_tick_counts

    work_dir = tmp_path / "testwork"
    work_dir.mkdir()
    (work_dir / "book-01.json").write_text(json.dumps(_book_with_ticks(1, 5, 3)), encoding="utf-8")
    counts = murray_butler_tick_counts(tmp_path, "testwork")
    assert counts == {1: {"murray": 5, "butler": 3}}


def test_murray_butler_tick_counts_empty_for_missing_work_dir(tmp_path):
    from homer_pipeline.preflight import murray_butler_tick_counts

    assert murray_butler_tick_counts(tmp_path, "nonesuch") == {}


def test_tick_coverage_violations_reports_regression():
    from homer_pipeline.preflight import tick_coverage_violations

    counts = {1: {"murray": 10, "butler": 8}}
    floor = {1: {"murray": 12, "butler": 8}}
    assert tick_coverage_violations(counts, floor) == [
        "book 1 murray ticks 10 below recorded floor 12"
    ]


def test_tick_coverage_violations_clean_when_at_or_above_floor():
    from homer_pipeline.preflight import tick_coverage_violations

    counts = {1: {"murray": 12, "butler": 9}}
    floor = {1: {"murray": 12, "butler": 8}}
    assert tick_coverage_violations(counts, floor) == []


def test_tick_coverage_violations_missing_book_counts_as_zero():
    from homer_pipeline.preflight import tick_coverage_violations

    assert tick_coverage_violations({}, {1: {"murray": 1}}) == [
        "book 1 murray ticks 0 below recorded floor 1"
    ]
