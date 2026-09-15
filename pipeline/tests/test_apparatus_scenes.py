import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline import apparatus_scenes


class TinyManifest:
    def __init__(self, work_id: str, books: list[dict], gaps: list[dict] | None = None):
        self.data = {
            "work": {"id": work_id},
            "books": books,
            "expected_line_gaps": gaps or [],
        }

    @property
    def work_id(self) -> str:
        return self.data["work"]["id"]

    @property
    def books(self) -> list[dict]:
        return self.data["books"]


def _scene(lo, hi, summary="A short factual summary of the scene.", location="camp", day=1):
    return {"lines": [lo, hi], "summary": summary, "location": location, "dayNumber": day}


# ── validate_scenes_list: coverage / overlap / hole / gap-boundary / word count ──


def test_validate_scenes_list_good_fixture_passes():
    scenes = [_scene(1, 4), _scene(5, 10)]
    assert apparatus_scenes.validate_scenes_list(scenes, 1, 10, []) == []


def test_validate_scenes_list_detects_overlap():
    scenes = [_scene(1, 5), _scene(4, 10)]
    problems = apparatus_scenes.validate_scenes_list(scenes, 1, 10, [])
    assert any("overlaps" in p for p in problems)


def test_validate_scenes_list_detects_hole():
    scenes = [_scene(1, 4), _scene(6, 10)]
    problems = apparatus_scenes.validate_scenes_list(scenes, 1, 10, [])
    assert any("coverage hole" in p for p in problems)


def test_validate_scenes_list_detects_gap_boundary_violation():
    # book_end=12, gap after=5 next=8 (lines 6,7 don't exist); a scene starting
    # at line 6 lands inside the excluded range.
    gaps = [(5, 8)]
    scenes = [_scene(1, 5), _scene(6, 12)]
    problems = apparatus_scenes.validate_scenes_list(scenes, 1, 12, gaps)
    assert any("nonexistent" in p for p in problems)


def test_validate_scenes_list_respects_declared_gap_as_legal_jump():
    gaps = [(5, 8)]
    scenes = [_scene(1, 5), _scene(8, 12)]
    assert apparatus_scenes.validate_scenes_list(scenes, 1, 12, gaps) == []


def test_validate_scenes_list_detects_long_summary():
    long_summary = " ".join(["word"] * 21)
    scenes = [_scene(1, 10, summary=long_summary)]
    problems = apparatus_scenes.validate_scenes_list(scenes, 1, 10, [])
    assert any("exceeds 20 words" in p for p in problems)


def test_validate_scenes_list_detects_incomplete_final_coverage():
    scenes = [_scene(1, 4), _scene(5, 8)]  # book_end=10, stops short
    problems = apparatus_scenes.validate_scenes_list(scenes, 1, 10, [])
    assert any("coverage incomplete" in p for p in problems)


def test_validate_scenes_list_detects_out_of_bounds_line():
    scenes = [_scene(1, 15)]  # book_end=10
    problems = apparatus_scenes.validate_scenes_list(scenes, 1, 10, [])
    assert any("nonexistent/out-of-range" in p for p in problems)


# ── validate_scenes_list: optional `places` (Phase P7a) ─────────────────────


def test_validate_scenes_list_accepts_scene_with_no_places_key():
    scenes = [_scene(1, 10)]
    assert apparatus_scenes.validate_scenes_list(scenes, 1, 10, []) == []


def test_validate_scenes_list_accepts_scene_with_valid_places_list():
    scene = _scene(1, 10)
    scene["places"] = ["troy", "olympus"]
    assert apparatus_scenes.validate_scenes_list([scene], 1, 10, []) == []


def test_validate_scenes_list_rejects_non_list_places():
    scene = _scene(1, 10)
    scene["places"] = "troy"
    problems = apparatus_scenes.validate_scenes_list([scene], 1, 10, [])
    assert any("places" in p for p in problems)


def test_validate_scenes_list_rejects_empty_places_list():
    scene = _scene(1, 10)
    scene["places"] = []
    problems = apparatus_scenes.validate_scenes_list([scene], 1, 10, [])
    assert any("places" in p for p in problems)


def test_validate_scenes_list_rejects_blank_string_in_places():
    scene = _scene(1, 10)
    scene["places"] = ["troy", "  "]
    problems = apparatus_scenes.validate_scenes_list([scene], 1, 10, [])
    assert any("places" in p for p in problems)


# ── merge_staging: fixtures on disk, temp STAGING_DIR ───────────────────────


def _write_staging(tmp_path, monkeypatch, filename, doc):
    staging = tmp_path / "staging"
    staging.mkdir(exist_ok=True)
    (staging / filename).write_text(json.dumps(doc), encoding="utf-8")
    monkeypatch.setattr(apparatus_scenes, "STAGING_DIR", staging)
    monkeypatch.setattr(apparatus_scenes, "SCENES_DIR", tmp_path / "scenes")


def test_merge_staging_good_fixture_merges_and_sorts(tmp_path, monkeypatch):
    manifest = TinyManifest("testwork", [{"n": 1, "start": "1.1", "end": "1.10"},
                                          {"n": 2, "start": "2.1", "end": "2.6"}])
    doc = {
        "work": "testwork",
        "status": "draft",
        "books": [
            {"book": 2, "argument": "Short.", "where": ["Ithaca"], "who": ["A"],
             "days": "1", "scenes": [_scene(1, 6)]},
            {"book": 1, "argument": "Short too.", "where": ["Troy"], "who": ["B"],
             "days": "1", "scenes": [_scene(1, 4), _scene(5, 10)]},
        ],
    }
    _write_staging(tmp_path, monkeypatch, "scenes-testwork-01-02.json", doc)

    merged = apparatus_scenes.merge_staging(manifest)
    assert [b["book"] for b in merged["books"]] == [1, 2]
    assert all(b["status"] == "draft" for b in merged["books"])
    assert merged["status"] == "draft"


def test_merge_staging_rejects_overlap_violation(tmp_path, monkeypatch):
    manifest = TinyManifest("testwork", [{"n": 1, "start": "1.1", "end": "1.10"}])
    doc = {
        "work": "testwork", "status": "draft",
        "books": [{"book": 1, "argument": "Short.", "where": ["Troy"], "who": ["B"],
                   "days": "1", "scenes": [_scene(1, 5), _scene(4, 10)]}],
    }
    _write_staging(tmp_path, monkeypatch, "scenes-testwork-01.json", doc)
    with pytest.raises(apparatus_scenes.ApparatusValidationError) as exc:
        apparatus_scenes.merge_staging(manifest)
    assert any("overlaps" in p for p in exc.value.problems)


def test_merge_staging_rejects_duplicate_book_across_batches(tmp_path, monkeypatch):
    manifest = TinyManifest("testwork", [{"n": 1, "start": "1.1", "end": "1.10"}])
    staging = tmp_path / "staging"
    staging.mkdir()
    book1 = {"work": "testwork", "status": "draft",
             "books": [{"book": 1, "argument": "Short.", "where": ["Troy"], "who": ["B"],
                        "days": "1", "scenes": [_scene(1, 10)]}]}
    (staging / "scenes-testwork-a.json").write_text(json.dumps(book1), encoding="utf-8")
    (staging / "scenes-testwork-b.json").write_text(json.dumps(book1), encoding="utf-8")
    monkeypatch.setattr(apparatus_scenes, "STAGING_DIR", staging)
    monkeypatch.setattr(apparatus_scenes, "SCENES_DIR", tmp_path / "scenes")
    with pytest.raises(apparatus_scenes.ApparatusValidationError) as exc:
        apparatus_scenes.merge_staging(manifest)
    assert any("duplicate book" in p for p in exc.value.problems)


def test_merge_staging_no_files_returns_empty_doc(tmp_path, monkeypatch):
    manifest = TinyManifest("testwork", [{"n": 1, "start": "1.1", "end": "1.10"}])
    monkeypatch.setattr(apparatus_scenes, "STAGING_DIR", tmp_path / "staging")
    monkeypatch.setattr(apparatus_scenes, "SCENES_DIR", tmp_path / "scenes")
    merged = apparatus_scenes.merge_staging(manifest)
    assert merged == {"work": "testwork", "status": "draft", "books": []}


# ── emit shape: bookData.apparatus per ReaderShell.astro's BookApparatus ────


def test_emit_book_apparatus_matches_reader_shell_shape():
    book = {
        "book": 1, "status": "draft",
        "argument": "The wrath of Achilles.",
        "where": ["Achaean camp", "Olympus"],
        "who": ["Achilles", "Agamemnon"],
        "days": "1-21",
        "scenes": [_scene(1, 7, summary="Proem.", location="proem", day=None)],
    }
    out = apparatus_scenes.emit_book_apparatus(book)
    assert out["argument"] == "The wrath of Achilles."
    assert out["where"] == "Achaean camp, Olympus"
    assert out["who"] == ["Achilles", "Agamemnon"]
    assert out["day"] == "1-21"
    assert out["draft"] is True
    assert out["scenes"] == [
        {"lines": [1, 7], "summary": "Proem.", "location": "proem", "dayNumber": None}
    ]
    # Only ReaderShell's BookApparatus keys + scenes — no leftover staging keys.
    assert set(out.keys()) == {"argument", "where", "who", "day", "draft", "scenes"}


def test_emit_book_apparatus_omits_empty_optional_fields():
    book = {"book": 1, "status": "draft", "argument": "X.", "where": [], "who": [],
            "days": "", "scenes": []}
    out = apparatus_scenes.emit_book_apparatus(book)
    assert "where" not in out
    assert "who" not in out
    assert "day" not in out
    assert out["draft"] is True
    assert out["scenes"] == []


def test_emit_book_apparatus_carries_places_when_present():
    scene = _scene(1, 7, summary="Proem.", location="proem", day=None)
    scene["places"] = ["troy", "olympus"]
    book = {"book": 1, "status": "draft", "argument": "The wrath of Achilles.",
            "where": ["Troy"], "who": ["Achilles"], "days": "1", "scenes": [scene]}
    out = apparatus_scenes.emit_book_apparatus(book)
    assert out["scenes"] == [
        {"lines": [1, 7], "summary": "Proem.", "location": "proem", "dayNumber": None,
         "places": ["troy", "olympus"]}
    ]


def test_emit_book_apparatus_omits_places_key_when_absent():
    scene = _scene(1, 7, summary="Proem.", location="proem", day=None)
    book = {"book": 1, "status": "draft", "argument": "The wrath of Achilles.",
            "where": ["Troy"], "who": ["Achilles"], "days": "1", "scenes": [scene]}
    out = apparatus_scenes.emit_book_apparatus(book)
    assert out["scenes"] == [
        {"lines": [1, 7], "summary": "Proem.", "location": "proem", "dayNumber": None}
    ]
    assert "places" not in out["scenes"][0]


# ── run(): partial coverage tolerance (missing staging, missing emit target) ─


def test_run_with_no_staging_files_does_not_crash(tmp_path, monkeypatch):
    manifest = TinyManifest("testwork", [{"n": 1, "start": "1.1", "end": "1.10"},
                                          {"n": 2, "start": "2.1", "end": "2.6"}])
    monkeypatch.setattr(apparatus_scenes, "STAGING_DIR", tmp_path / "staging")
    monkeypatch.setattr(apparatus_scenes, "SCENES_DIR", tmp_path / "scenes")
    monkeypatch.setattr(apparatus_scenes, "BUILD_DIR", tmp_path / "build")
    result = apparatus_scenes.run(manifest)
    assert result["staging_files"] == []
    assert result["books_emitted"] == []
    assert result["books_without_staging"] == [1, 2]


def test_run_rejects_partial_coverage_before_overwriting_canonical(tmp_path, monkeypatch):
    manifest = TinyManifest("testwork", [{"n": 1, "start": "1.1", "end": "1.10"},
                                          {"n": 2, "start": "2.1", "end": "2.6"}])
    staged = {
        "work": "testwork", "status": "draft",
        "books": [{"book": 1, "argument": "Short.", "where": ["Troy"], "who": ["B"],
                   "days": "1", "scenes": [_scene(1, 10)]}],
    }
    _write_staging(tmp_path, monkeypatch, "scenes-testwork-01.json", staged)
    canonical_path = apparatus_scenes.SCENES_DIR / "testwork.json"
    canonical_path.parent.mkdir()
    original = {"work": "testwork", "status": "draft", "books": [{"book": 1}, {"book": 2}]}
    canonical_path.write_text(json.dumps(original), encoding="utf-8")
    monkeypatch.setattr(apparatus_scenes, "BUILD_DIR", tmp_path / "build")

    with pytest.raises(apparatus_scenes.ApparatusValidationError) as exc:
        apparatus_scenes.run(manifest)

    assert exc.value.problems == [
        "testwork: staged scenes cover 1/2 manifest books; missing books: [2]"
    ]
    assert json.loads(canonical_path.read_text(encoding="utf-8")) == original


def test_run_partial_coverage_merges_available_books_and_reports_the_rest(tmp_path, monkeypatch):
    manifest = TinyManifest("testwork", [{"n": 1, "start": "1.1", "end": "1.10"},
                                          {"n": 2, "start": "2.1", "end": "2.6"}])
    doc = {
        "work": "testwork", "status": "draft",
        "books": [{"book": 1, "argument": "Short.", "where": ["Troy"], "who": ["B"],
                   "days": "1", "scenes": [_scene(1, 10)]}],
    }
    _write_staging(tmp_path, monkeypatch, "scenes-testwork-01.json", doc)
    build_dir = tmp_path / "build"
    monkeypatch.setattr(apparatus_scenes, "BUILD_DIR", build_dir)
    out_dir = build_dir / "dist" / "testwork"
    out_dir.mkdir(parents=True)
    (out_dir / "book-01.json").write_text(json.dumps({"book": 1, "segments": []}), encoding="utf-8")
    # book-02.json deliberately absent (stage7 hasn't emitted it in this test).

    result = apparatus_scenes.run(manifest, allow_partial=True)
    assert result["books_merged"] == 1
    assert result["books_emitted"] == [1]
    assert result["books_without_staging"] == [2]

    updated = json.loads((out_dir / "book-01.json").read_text(encoding="utf-8"))
    assert updated["apparatus"]["draft"] is True
    assert updated["apparatus"]["scenes"][0]["lines"] == [1, 10]

    canonical = json.loads((apparatus_scenes.SCENES_DIR / "testwork.json").read_text(encoding="utf-8"))
    assert [b["book"] for b in canonical["books"]] == [1]
