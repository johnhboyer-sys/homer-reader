import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline import apparatus_epithets as ae
from homer_pipeline.config import Manifest


# ── pure helpers ─────────────────────────────────────────────────────────


def test_entity_head_word_single_word():
    assert ae.entity_head_word("Ἀχιλλεύς") == "Ἀχιλλεύς"


def test_entity_head_word_takes_first_word_of_disambiguated_name():
    # The two Ajaxes disambiguate a homonym with a trailing patronymic; only
    # the name itself is what formulas match against (documented limitation:
    # both entries then share a head lemma).
    assert ae.entity_head_word("Αἴας Τελαμώνιος") == "Αἴας"


def test_is_contiguous_subsequence_true_for_embedded_run():
    assert ae._is_contiguous_subsequence(("b", "c"), ("a", "b", "c", "d"))


def test_is_contiguous_subsequence_false_for_noncontiguous_words():
    assert not ae._is_contiguous_subsequence(("a", "c"), ("a", "b", "c"))


def test_is_contiguous_subsequence_false_when_not_shorter():
    assert not ae._is_contiguous_subsequence(("a", "b", "c"), ("a", "b"))


def test_resolve_lemma_map_takes_first_present_variant():
    variant_map = {"tok1": ["*var_a", "*var_b"]}
    found = {"*var_b": [{"lemma": "*lemma_b"}]}
    assert ae.resolve_lemma_map(variant_map, found) == {"tok1": "*lemma_b"}


def test_resolve_lemma_map_omits_entries_with_no_match():
    variant_map = {"tok1": ["*var_a"]}
    assert ae.resolve_lemma_map(variant_map, {}) == {}


def test_entity_occurrence_indices_rejects_known_non_name_lemma_despite_surface_prefix():
    tokens = [
        {"t": "αἶαν", "k": "ai)=an", "lemma": "ai)=a"},
        {"t": "Αἶαν", "k": "ai)=an", "lemma": "*ai)/as"},
    ]

    assert ae.entity_occurrence_indices(
        tokens, {"*ai)/as"}, {"ai)=an"}
    ) == [1]


# ── _formula_windows: window generation around a target lemma ──────────────


def test_formula_windows_generates_all_lengths_containing_target():
    lemmas = ["pou/s", "w)ku/s", "*)axilleu/s"]
    surfaces = ["πόδας", "ὠκὺς", "Ἀχιλλεύς"]
    windows = ae._formula_windows(lemmas, surfaces, 1, 58, "*)axilleu/s")
    lemma_tuples = {w[0] for w in windows}
    assert ("w)ku/s", "*)axilleu/s") in lemma_tuples
    assert ("pou/s", "w)ku/s", "*)axilleu/s") in lemma_tuples
    assert ("*)axilleu/s",) not in lemma_tuples  # below MIN_FORMULA_LEN


def test_formula_windows_respects_max_formula_len_cap():
    lemmas = ["a", "b", "c", "d", "e", "f", "g", "*)axilleu/s"]
    surfaces = lemmas
    windows = ae._formula_windows(lemmas, surfaces, 1, 1, "*)axilleu/s")
    assert all(len(w[0]) <= ae.MAX_FORMULA_LEN for w in windows)


def test_formula_windows_never_returns_empty_for_single_token_line():
    windows = ae._formula_windows(["*)axilleu/s"], ["Ἀχιλλεύς"], 1, 1, "*)axilleu/s")
    assert windows == []  # can't form a 2+ token window from one token


# ── formulas_from_occurrences: grouping, threshold, maximal pruning ────────


def _occ(lemma_tuple, surface_tuple, book, line):
    return (lemma_tuple, surface_tuple, book, line)


def test_formulas_from_occurrences_requires_min_count():
    occs = [
        _occ(("w)ku/s", "*)axilleu/s"), ("ὠκὺς", "Ἀχιλλεύς"), 1, 1),
        _occ(("w)ku/s", "*)axilleu/s"), ("ὠκὺς", "Ἀχιλλεύς"), 1, 2),
    ]
    assert ae.formulas_from_occurrences(occs) == []  # only 2 < MIN_FORMULA_COUNT


def test_formulas_from_occurrences_reports_count_and_most_frequent_surface():
    occs = [
        _occ(("w)ku/s", "*)axilleu/s"), ("ὠκὺς", "Ἀχιλλεύς"), 1, 1),
        _occ(("w)ku/s", "*)axilleu/s"), ("ὠκὺς", "Ἀχιλλεύς"), 1, 2),
        _occ(("w)ku/s", "*)axilleu/s"), ("ὠκὺς", "Ἀχιλλεύς·"), 1, 3),
    ]
    formulas = ae.formulas_from_occurrences(occs)
    assert len(formulas) == 1
    f = formulas[0]
    assert f["count"] == 3
    assert f["text"] == "ὠκὺς Ἀχιλλεύς"  # 2 vs 1 occurrence wins the tie
    assert f["lemmaKeys"] == ["w)ku/s", "*)axilleu/s"]
    assert f["refs"] == [
        {"book": 1, "line": 1},
        {"book": 1, "line": 2},
        {"book": 1, "line": 3},
    ]


def test_formulas_from_occurrences_prunes_subgram_with_identical_ref_set():
    # "πόδας ὠκὺς Ἀχιλλεύς" (3-gram) occurs on the same 3 lines as its own
    # sub-gram "ὠκὺς Ἀχιλλεύς" (2-gram) -- the 2-gram is pure redundancy and
    # must be dropped.
    long_lemma = ("pou/s", "w)ku/s", "*)axilleu/s")
    short_lemma = ("w)ku/s", "*)axilleu/s")
    occs = []
    for line in (1, 2, 3):
        occs.append(_occ(long_lemma, ("πόδας", "ὠκὺς", "Ἀχιλλεύς"), 1, line))
        occs.append(_occ(short_lemma, ("ὠκὺς", "Ἀχιλλεύς"), 1, line))
    formulas = ae.formulas_from_occurrences(occs)
    assert [f["lemmaKeys"] for f in formulas] == [list(long_lemma)]


def test_formulas_from_occurrences_keeps_subgram_with_a_broader_ref_set():
    # The 2-gram recurs on a 4th line where the 3-gram does NOT -- it is a
    # genuinely broader formula and must be kept alongside the 3-gram.
    long_lemma = ("pou/s", "w)ku/s", "*)axilleu/s")
    short_lemma = ("w)ku/s", "*)axilleu/s")
    occs = []
    for line in (1, 2, 3):
        occs.append(_occ(long_lemma, ("πόδας", "ὠκὺς", "Ἀχιλλεύς"), 1, line))
        occs.append(_occ(short_lemma, ("ὠκὺς", "Ἀχιλλεύς"), 1, line))
    occs.append(_occ(short_lemma, ("ὠκὺς", "Ἀχιλλεύς"), 1, 9))
    formulas = ae.formulas_from_occurrences(occs)
    lemma_key_sets = {tuple(f["lemmaKeys"]) for f in formulas}
    assert long_lemma in lemma_key_sets
    assert short_lemma in lemma_key_sets


# ── run(): end-to-end fixture (fake corpus + fake Diogenes source) ────────


def _fixture_manifest(tmp_path: Path) -> Manifest:
    diogenes_dir = tmp_path / "diogenes"
    diogenes_dir.mkdir()
    (diogenes_dir / "greek-analyses.txt").write_text(
        "*)axilleu/s\t{1 9 *)axilleu/s\tAchilles\tmasc nom sg}\n",
        encoding="utf-8",
    )
    data = {
        "work": {"id": "fixture", "greek_source": "unused.xml"},
        "sources": {
            "tlg_dir_env": "TLG_DIR_UNUSED",
            "tlg_dir_default": ".",
            "diogenes_server": ".",
            "diogenes_data": str(diogenes_dir),
        },
    }
    return Manifest(data, tmp_path / "fixture.yaml")


def _write_book(dist_dir: Path, book_n: int, lines: list[dict]) -> None:
    dist_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "book": book_n,
        "segments": [{"id": f"{book_n}:1", "column": str(book_n), "greek": lines}],
    }
    (dist_dir / f"book-{book_n:02d}.json").write_text(
        json.dumps(doc, ensure_ascii=False), encoding="utf-8"
    )


def _tok(t, o, k):
    return {"t": t, "o": o, "k": k}


def _setup_fixture_corpus(tmp_path: Path, monkeypatch) -> tuple[Manifest, Path]:
    manifest = _fixture_manifest(tmp_path)
    dist_dir = tmp_path / "build" / "dist" / "fixture"

    # "πόδας ὠκὺς Ἀχιλλεύς" (Achilles swift-footed), repeated 3x plus one
    # distractor line that only has "δῖος Ἀχιλλεύς" -- a shorter, separate
    # 2-gram that should also qualify.
    lines = []
    for i, n in enumerate((1, 2, 3), start=1):
        lines.append({
            "n": n,
            "text": "πόδας ὠκὺς Ἀχιλλεύς",
            "tokens": [
                _tok("πόδας", 0, "po/das"),
                _tok("ὠκὺς", 6, "w)ku/s"),
                _tok("Ἀχιλλεύς", 11, "a)xilleu/s"),
            ],
        })
    lines.append({
        "n": 4,
        "text": "δῖος Ἀχιλλεύς",
        "tokens": [
            _tok("δῖος", 0, "di=os"),
            _tok("Ἀχιλλεύς", 5, "a)xilleu/s"),
        ],
    })
    _write_book(dist_dir, 1, lines)

    analyses = {
        "po/das": [{"lemma": "pou/s", "gloss": "foot", "parse": "", "lsj": [], "cunliffe": []}],
        "w)ku/s": [{"lemma": "w)ku/s", "gloss": "swift", "parse": "", "lsj": [], "cunliffe": []}],
        "di=os": [{"lemma": "di=os", "gloss": "divine", "parse": "", "lsj": [], "cunliffe": []}],
    }
    (dist_dir / "analyses.json").write_text(json.dumps(analyses, ensure_ascii=False), encoding="utf-8")

    characters_dir = tmp_path / "apparatus"
    characters_dir.mkdir()
    characters = {
        "status": "draft",
        "characters": [
            {"id": "achilles", "greek": "Ἀχιλλεύς"},
            {"id": "unresolvable", "greek": "Ζζζζζζ"},  # never in the fixture analyses file
        ],
    }
    (characters_dir / "characters.json").write_text(
        json.dumps(characters, ensure_ascii=False), encoding="utf-8"
    )

    monkeypatch.setattr(ae, "BUILD_DIR", tmp_path / "build")
    monkeypatch.setattr(ae, "CHARACTERS_PATH", characters_dir / "characters.json")
    return manifest, dist_dir


def test_run_emits_epithets_json_with_expected_formula(tmp_path, monkeypatch):
    manifest, dist_dir = _setup_fixture_corpus(tmp_path, monkeypatch)
    result = ae.run(manifest)

    assert result["entities_total"] == 2
    assert result["entities_unresolved"] == ["unresolvable"]

    doc = json.loads((dist_dir / "epithets.json").read_text(encoding="utf-8"))
    assert [e["entity"] for e in doc] == ["achilles"]
    formulas = {tuple(f["lemmaKeys"]): f for f in doc[0]["formulas"]}
    # The maximal 3-gram "πόδας ὠκὺς Ἀχιλλεύς" is reported...
    assert ("pou/s", "w)ku/s", "*)axilleu/s") in formulas
    assert formulas[("pou/s", "w)ku/s", "*)axilleu/s")]["count"] == 3
    assert formulas[("pou/s", "w)ku/s", "*)axilleu/s")]["text"] == "πόδας ὠκὺς Ἀχιλλεύς"
    # ...and its 2-gram sub-formula "ὠκὺς Ἀχιλλεύς" shares the identical
    # 3-line ref set, so maximal-formula pruning drops it as redundant.
    assert ("w)ku/s", "*)axilleu/s") not in formulas
    # "δῖος Ἀχιλλεύς" only occurs once (book 1 line 4), below
    # MIN_FORMULA_COUNT, so it must not appear either.
    assert ("di=os", "*)axilleu/s") not in formulas


def test_run_is_deterministic_across_repeated_runs(tmp_path, monkeypatch):
    manifest, dist_dir = _setup_fixture_corpus(tmp_path, monkeypatch)
    ae.run(manifest)
    first = (dist_dir / "epithets.json").read_bytes()
    ae.run(manifest)
    second = (dist_dir / "epithets.json").read_bytes()
    assert first == second
