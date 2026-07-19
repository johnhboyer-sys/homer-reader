import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline import apparatus_speeches as asp


class TinyManifest:
    def __init__(self, work_id: str):
        self._work_id = work_id

    @property
    def work_id(self) -> str:
        return self._work_id


# ── pure helpers ─────────────────────────────────────────────────────────


def test_parse_ref_splits_book_and_line():
    assert asp._parse_ref("9.2") == (9, 2)
    assert asp._parse_ref("12.453") == (12, 453)


def test_join_character_id_exact_match():
    apparatus_by_name = {"achilles": "achilles"}
    assert asp.join_character_id("Achilles", apparatus_by_name) == ("achilles", True)


def test_join_character_id_case_insensitive():
    apparatus_by_name = {"achilles": "achilles"}
    assert asp.join_character_id("ACHILLES", apparatus_by_name) == ("achilles", True)


def test_join_character_id_uses_verified_alias_table():
    # DICES spells the two Ajaxes with "Aias"; our apparatus roster uses the
    # Latinized "Ajax (son of X)". A naive parenthetical-stripping match
    # would collapse both onto one id -- the alias table keeps them distinct.
    apparatus_by_name = {
        "ajax (son of telamon)": "ajax-telamonian",
        "ajax (son of oileus)": "ajax-oileus",
    }
    assert asp.join_character_id("Aias (son of Telamon)", apparatus_by_name) == (
        "ajax-telamonian", True,
    )
    assert asp.join_character_id("Aias (son of Oileus)", apparatus_by_name) == (
        "ajax-oileus", True,
    )


def test_join_character_id_unmatched_keeps_lowercased_dices_name():
    cid, matched = asp.join_character_id("Some Random Herald", {})
    assert matched is False
    assert cid == "some random herald"


def test_build_instance_name_map_collapses_disguise_to_base_character():
    char_records = [{"pk": 722, "fields": {"name": "Odysseus"}}]
    inst_records = [
        {"pk": 5, "fields": {"name": "Odysseus-beggar", "char": 722}},
    ]
    names = asp.build_instance_name_map(char_records, inst_records)
    assert names[5] == "Odysseus"  # not "Odysseus-beggar"


def test_build_instance_name_map_keeps_own_name_for_anonymous_instance():
    inst_records = [{"pk": 6, "fields": {"name": "Greeks", "char": None}}]
    names = asp.build_instance_name_map([], inst_records)
    assert names[6] == "Greeks"


# ── run(): end-to-end fixture (fake DICES export + fake corpus) ────────────


def _write_book(dist_dir: Path, book_n: int, lines_n: list[int]) -> None:
    dist_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "book": book_n,
        "segments": [{
            "id": f"{book_n}:1",
            "column": str(book_n),
            "greek": [{"n": n, "text": "x", "tokens": []} for n in lines_n],
        }],
    }
    (dist_dir / f"book-{book_n:02d}.json").write_text(
        json.dumps(doc, ensure_ascii=False), encoding="utf-8"
    )


def _fixture_speechdb_records() -> list[dict]:
    return [
        {"model": "speechdb.character", "pk": 10,
         "fields": {"name": "Achilles", "public_id": "AAAA"}},
        {"model": "speechdb.character", "pk": 20,
         "fields": {"name": "Agamemnon", "public_id": "BBBB"}},
        {"model": "speechdb.characterinstance", "pk": 100,
         "fields": {"name": "Achilles", "char": 10, "context": "Homer Iliad"}},
        {"model": "speechdb.characterinstance", "pk": 101,
         "fields": {"name": "Agamemnon", "char": 20, "context": "Homer Iliad"}},
        {"model": "speechdb.characterinstance", "pk": 102,
         "fields": {"name": "Nobody Special", "char": None, "context": "Homer Iliad"}},
        # Ordinary, single-book, level-0 speech.
        {"model": "speechdb.speech", "pk": 1,
         "fields": {"work": 1, "cluster": 500, "part": 1, "level": 0, "type": "G",
                    "l_fi": "1.1", "l_la": "1.5", "spkr": [100], "addr": [101]}},
        # Crosses book 1 -> book 2, level 0 (Apologoi-shaped: a frame speech
        # that spans books but is not itself "nested").
        {"model": "speechdb.speech", "pk": 2,
         "fields": {"work": 1, "cluster": 500, "part": 2, "level": 0, "type": "G",
                    "l_fi": "1.10", "l_la": "2.3", "spkr": [101], "addr": [100]}},
        # Nested (level 1), single-book, with an unmatched (unresolvable)
        # speaker that must be kept as a lowercase string, not dropped.
        {"model": "speechdb.speech", "pk": 3,
         "fields": {"work": 1, "cluster": 501, "part": 1, "level": 1, "type": "M",
                    "l_fi": "2.1", "l_la": "2.2", "spkr": [102], "addr": [100]}},
        # References a line that does not exist in the fixture corpus (a
        # numbering-gap-shaped data error) -- must be reported, not clamped.
        {"model": "speechdb.speech", "pk": 4,
         "fields": {"work": 1, "cluster": 502, "part": 1, "level": 0, "type": "D",
                    "l_fi": "1.99", "l_la": "1.99", "spkr": [100], "addr": [101]}},
    ]


def _setup_fixture(tmp_path: Path, monkeypatch):
    speechdb_path = tmp_path / "speechdb.json"
    speechdb_path.write_text(
        json.dumps(_fixture_speechdb_records(), ensure_ascii=False), encoding="utf-8"
    )

    apparatus_dir = tmp_path / "apparatus"
    apparatus_dir.mkdir()
    characters_path = apparatus_dir / "characters.json"
    characters_doc = {
        "status": "draft",
        "characters": [
            {"id": "achilles", "name": "Achilles", "dicesId": None},
            {"id": "agamemnon", "name": "Agamemnon", "dicesId": None},
            {"id": "hector", "name": "Hector", "dicesId": None},  # never referenced
        ],
    }
    characters_path.write_text(json.dumps(characters_doc, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")

    speeches_dir = apparatus_dir / "speeches"
    build_dir = tmp_path / "build"
    dist_dir = build_dir / "dist" / "iliad"
    _write_book(dist_dir, 1, list(range(1, 11)))  # lines 1..10, so 1.99 is invalid
    _write_book(dist_dir, 2, list(range(1, 6)))   # lines 1..5

    monkeypatch.setattr(asp, "SPEECHDB_PATH", speechdb_path)
    monkeypatch.setattr(asp, "CHARACTERS_PATH", characters_path)
    monkeypatch.setattr(asp, "SPEECHES_DIR", speeches_dir)
    monkeypatch.setattr(asp, "BUILD_DIR", build_dir)
    return TinyManifest("iliad"), speeches_dir, characters_path


def test_run_emits_speeches_with_expected_shape(tmp_path, monkeypatch):
    manifest, speeches_dir, characters_path = _setup_fixture(tmp_path, monkeypatch)
    result = asp.run(manifest)

    assert result["speech_count"] == 4
    assert result["cross_book_count"] == 1
    assert result["level_counts"] == {0: 3, 1: 1}
    assert "Nobody Special" in result["unmatched_names"]  # report keeps original case
    assert any("1.99" in msg for msg in result["line_ref_errors"])

    doc = json.loads((speeches_dir / "iliad.json").read_text(encoding="utf-8"))
    assert doc["work"] == "iliad"
    assert doc["status"] == "imported"
    by_id = {s["id"]: s for s in doc["speeches"]}

    ordinary = by_id["iliad-1"]
    assert ordinary["book"] == 1
    assert ordinary["lines"] == [1, 5]
    assert ordinary["speaker"] == ["achilles"]
    assert ordinary["addressee"] == ["agamemnon"]
    assert "crossBook" not in ordinary

    crossing = by_id["iliad-2"]
    assert crossing["book"] == 1  # book of l_fi
    assert crossing["lines"] == [10, 3]
    assert crossing["crossBook"] is True

    nested = by_id["iliad-3"]
    assert nested["level"] == 1
    assert nested["speaker"] == ["nobody special"]  # unmatched, kept lowercase
    assert "crossBook" not in nested


def test_run_fills_dicesid_for_matched_characters_only(tmp_path, monkeypatch):
    manifest, _, characters_path = _setup_fixture(tmp_path, monkeypatch)
    asp.run(manifest)

    doc = json.loads(characters_path.read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in doc["characters"]}
    assert by_id["achilles"]["dicesId"] == "AAAA"
    assert by_id["agamemnon"]["dicesId"] == "BBBB"
    assert by_id["hector"]["dicesId"] is None  # never referenced, untouched

    # Every other field byte-preserved for the untouched character.
    assert by_id["hector"] == {"id": "hector", "name": "Hector", "dicesId": None}


def test_run_is_deterministic_across_repeated_runs(tmp_path, monkeypatch):
    manifest, speeches_dir, characters_path = _setup_fixture(tmp_path, monkeypatch)
    asp.run(manifest)
    speeches_first = (speeches_dir / "iliad.json").read_bytes()
    characters_first = characters_path.read_bytes()

    asp.run(manifest)
    speeches_second = (speeches_dir / "iliad.json").read_bytes()
    characters_second = characters_path.read_bytes()

    assert speeches_first == speeches_second
    assert characters_first == characters_second
