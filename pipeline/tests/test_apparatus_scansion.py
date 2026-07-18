import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline import apparatus_scansion as sc
from homer_pipeline.config import Manifest


# ── word_symbols: syllable-nucleus detection ────────────────────────────────


def test_word_symbols_splits_diphthong_as_one_long_nucleus():
    syms = sc.word_symbols("καὶ")
    vowels = [s for s in syms if s["kind"] == "vowel"]
    assert len(vowels) == 1
    assert vowels[0]["weight"] == "L"
    assert vowels[0]["bases"] == ["α", "ι"]


def test_word_symbols_diaeresis_blocks_diphthong_reading():
    # Ἄϊδι: diaeresis on the iota means "a-i-di", NOT the diphthong "ai".
    syms = sc.word_symbols("Ἄϊδι")
    vowels = [s for s in syms if s["kind"] == "vowel"]
    assert len(vowels) == 3
    assert [v["bases"] for v in vowels] == [["α"], ["ι"], ["ι"]]


def test_word_symbols_iota_subscript_is_a_single_long_nucleus():
    syms = sc.word_symbols("ᾳ")
    vowels = [s for s in syms if s["kind"] == "vowel"]
    assert len(vowels) == 1
    assert vowels[0]["weight"] == "L"


def test_word_symbols_eta_omega_long_epsilon_omicron_short():
    for base, expected in [("η", "L"), ("ω", "L"), ("ε", "S"), ("ο", "S")]:
        syms = sc.word_symbols(base)
        assert syms[0]["weight"] == expected, base


def test_word_symbols_bare_alpha_iota_upsilon_are_dichrona():
    for base in ("α", "ι", "υ"):
        syms = sc.word_symbols(base)
        assert syms[0]["weight"] == "D", base


def test_word_symbols_skips_elision_apostrophe():
    # "ἄλγε'" -- the elided final alpha is already gone from the source text;
    # the apostrophe is punctuation, not a phoneme.
    syms = sc.word_symbols("ἄλγε'")
    vowels = [s for s in syms if s["kind"] == "vowel"]
    assert [v["bases"] for v in vowels] == [["α"], ["ε"]]


# ── build_line_slots: position-length across word boundaries ───────────────


def test_build_line_slots_closes_syllable_across_word_boundary():
    # "...ας κρ..." -- alpha followed by sigma (word-final) + kappa (word-
    # initial) = 2 consonants -> closed by position, regardless of the word
    # boundary in between.
    slots = sc.build_line_slots(["πάντας", "κρατερὰς"])
    # πάντας: α(1st, closed by ντ), α(2nd/final, closed by ς+κ across the
    # boundary).
    penultimate_word_final = [s for s in slots if s["word"] == 0][-1]
    assert penultimate_word_final["closed_by_position"] is True


def test_build_line_slots_open_syllable_not_forced_long():
    slots = sc.build_line_slots(["ἐμὸν", "λέχος"])
    # ἐμὸν's ε: followed by μ only (1 consonant) -> open, short by nature.
    assert slots[0]["weight"] == "S"
    assert slots[0]["closed_by_position"] is False


def test_build_line_slots_flags_muta_cum_liquida_candidate():
    # πατρός: alpha followed by exactly stop+liquid (τ,ρ) -> mcl candidate.
    slots = sc.build_line_slots(["πατρός"])
    first_alpha = slots[0]
    assert first_alpha["closed_by_position"] is True
    assert first_alpha["mcl_candidate"] is True


def test_build_line_slots_three_consonant_cluster_is_not_mcl():
    # σκήπτρῳ: eta followed by pi-tau-rho (3 consonants) -- always closed,
    # but NOT an mcl candidate (that licence applies only to a bare 2-
    # consonant stop+liquid cluster).
    slots = sc.build_line_slots(["σκήπτρῳ"])
    eta_slot = slots[0]
    assert eta_slot["closed_by_position"] is True
    assert eta_slot["mcl_candidate"] is False


def test_build_line_slots_double_consonant_counts_as_two():
    # Ἄϊδι προΐαψεν  -- unrelated words but check ζ/ξ/ψ counting directly:
    slots = sc.build_line_slots(["ἄξ", "ια"])
    assert slots[0]["gap"] == 2
    assert slots[0]["closed_by_position"] is True


# ── foot_arrangements / solve_arrangements ──────────────────────────────────


def test_foot_arrangements_count_matches_binomial():
    assert len(sc.foot_arrangements(0)) == 1
    assert len(sc.foot_arrangements(5)) == 1
    assert len(sc.foot_arrangements(2)) == 10  # C(5,2)


def test_solve_arrangements_empty_outside_hexameter_range():
    # 10 slots -> k = -2, structurally impossible.
    slots = [{"weight": "L"} for _ in range(10)]
    assert sc.solve_arrangements(slots) == []


def test_solve_arrangements_all_dichrona_accepts_every_arrangement():
    slots = [{"weight": "D"} for _ in range(17)]  # k=5: all-dactyl only option
    result = sc.solve_arrangements(slots)
    assert result == [tuple([True] * 5)]


# ── scan_line: the 10 hand-verified canonical lines ─────────────────────────
#
# Verified against the standard rules (nature: eta/omega/diphthongs long,
# epsilon/omicron short, bare alpha/iota/upsilon dichrona; position: 2+
# intervening consonants close a syllable, doubled zeta/xi/psi counting as
# 2, a bare stop+liquid pair optionally light) applied by hand syllable-by-
# syllable, and for Iliad 1.1 additionally cross-checked against two
# independent published scansions (Wikipedia's "Dactylic hexameter" article
# and a second web source), both giving dactyl-dactyl-SPONDEE-dactyl-dactyl
# for feet 1-5, synizesis on Pēlēiadeō's "-eo" (-δεω scanned as one long
# syllable), and a brevis in longo on Achilēos' final short omicron filling
# the verse-final anceps.

CANONICAL_LINES = [
    # (book, line, words, expected_feet, expected_confidence, expected_notes)
    (
        1, 1,
        ["Μῆνιν", "ἄειδε", "θεὰ", "Πηληϊάδεω", "Ἀχιλῆος"],
        "DDSDDX", "high", ["brevis-in-longo", "hiatus", "synizesis"],
    ),
    (
        2, 40,
        ["Τρωσί", "τε", "καὶ", "Δαναοῖσι", "διὰ", "κρατερὰς", "ὑσμίνας"],
        "DDDDSS", "high", [],  # spondaic fifth foot
    ),
    (
        1, 559,
        ["τιμήσῃς", "ὀλέσῃς", "δὲ", "πολέας", "ἐπὶ", "νηυσὶν", "Ἀχαιῶν"],
        "SDDDDS", "high", ["synizesis"],
    ),
    (
        6, 146,
        ["οἵη", "περ", "φύλλων", "γενεὴ", "τοίη", "δὲ", "καὶ", "ἀνδρῶν"],
        "SSDSDS", "high", ["correption", "hiatus"],
    ),
    (
        16, 1,
        ["Ὣς", "οἳ", "μὲν", "περὶ", "νηὸς", "ἐϋσσέλμοιο", "μάχοντο"],
        "SDDSDX", "high", ["brevis-in-longo"],
    ),
    (
        24, 1,
        ["Λῦτο", "δ'", "ἀγών", "λαοὶ", "δὲ", "θοὰς", "ἐπὶ", "νῆας", "ἕκαστοι"],
        "DSDDDS", "high", [],
    ),
    (
        2, 1,
        ["Ἄλλοι", "μέν", "ῥα", "θεοί", "τε", "καὶ", "ἀνέρες", "ἱπποκορυσταὶ"],
        "SDDDDS", "high", ["correption", "hiatus"],
    ),
    (
        9, 1,
        ["τὸν", "δ'", "ἀπαμειβόμενος", "προσέφη", "πολύμητις", "Ὀδυσσεύς"],
        "DDDDDS", "high", [],
    ),
    (
        23, 1,
        ["γρηῢς", "δ'", "εἰς", "ὑπερῷ'", "ἀνεβήσετο", "καγχαλόωσα"],
        "SDDDDS", "high", ["hiatus"],
    ),
    (
        1, 283,
        ["ἐκ", "Διός", "ἥ", "τε", "μάλιστα", "φέρει", "κλέος", "ἀνθρώποισι"],
        "DDDDSS", "high", [],  # spondaic fifth foot (Odyssey)
    ),
]


def test_canonical_lines_scan_as_hand_verified():
    for book, line, words, feet, confidence, notes in CANONICAL_LINES:
        result = sc.scan_line(words)
        assert result["feet"] == feet, f"{book}.{line}: {result}"
        assert result["confidence"] == confidence, f"{book}.{line}: {result}"
        assert sorted(result["notes"]) == sorted(notes), f"{book}.{line}: {result}"


def test_scan_line_never_invents_a_clean_scan_for_an_impossible_line():
    # A single made-up "word" that is far too short to be a hexameter line at
    # all must come back honestly flagged, not silently padded into a fake
    # scan.
    result = sc.scan_line(["μῆ"])
    assert result["confidence"] == "ambiguous"
    assert "unresolved" in result["notes"]
    assert len(result["feet"]) == 6


# ── run(): fixture-corpus integration + determinism ─────────────────────────


def _fixture_manifest(tmp_path: Path) -> Manifest:
    data = {"work": {"id": "fixture"}}
    return Manifest(data, tmp_path / "fixture.yaml")


def _tok(t):
    return {"t": t, "o": 0, "k": "unused"}


def _write_book(dist_dir: Path, book_n: int, lines: list[dict]) -> None:
    dist_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "book": book_n,
        "segments": [{"id": f"{book_n}:1", "column": str(book_n), "greek": lines}],
    }
    (dist_dir / f"book-{book_n:02d}.json").write_text(
        json.dumps(doc, ensure_ascii=False), encoding="utf-8"
    )


def _setup_fixture_corpus(tmp_path: Path, monkeypatch) -> tuple[Manifest, Path]:
    manifest = _fixture_manifest(tmp_path)
    dist_dir = tmp_path / "build" / "dist" / "fixture"
    _write_book(dist_dir, 1, [
        {
            "n": 1,
            "tokens": [_tok(w) for w in
                       ["Μῆνιν", "ἄειδε", "θεὰ", "Πηληϊάδεω", "Ἀχιλῆος"]],
        },
        {
            "n": 2,
            "tokens": [_tok(w) for w in
                       ["Τρωσί", "τε", "καὶ", "Δαναοῖσι", "διὰ", "κρατερὰς", "ὑσμίνας"]],
        },
    ])
    monkeypatch.setattr(sc, "BUILD_DIR", tmp_path / "build")
    return manifest, dist_dir


def test_run_emits_scansion_json_keyed_by_book_dot_line(tmp_path, monkeypatch):
    manifest, dist_dir = _setup_fixture_corpus(tmp_path, monkeypatch)
    result = sc.run(manifest)

    assert result["total_lines"] == 2
    doc = json.loads((dist_dir / "scansion.json").read_text(encoding="utf-8"))
    assert doc["work"] == "fixture"
    assert set(doc["lines"]) == {"1.1", "1.2"}
    assert doc["lines"]["1.1"]["feet"] == "DDSDDX"
    assert doc["lines"]["1.1"]["confidence"] == "high"


def test_run_is_deterministic_across_repeated_runs(tmp_path, monkeypatch):
    manifest, dist_dir = _setup_fixture_corpus(tmp_path, monkeypatch)
    sc.run(manifest)
    first = (dist_dir / "scansion.json").read_bytes()
    sc.run(manifest)
    second = (dist_dir / "scansion.json").read_bytes()
    assert first == second


def test_scan_line_is_deterministic_across_repeated_calls():
    words = ["Μῆνιν", "ἄειδε", "θεὰ", "Πηληϊάδεω", "Ἀχιλῆος"]
    first = sc.scan_line(words)
    second = sc.scan_line(words)
    assert first == second
