import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline import apparatus_repetitions as ar


# ── _is_contiguous_subsequence ──────────────────────────────────────────


def test_is_contiguous_subsequence_true_for_embedded_run():
    assert ar._is_contiguous_subsequence(("b", "c"), ("a", "b", "c", "d"))


def test_is_contiguous_subsequence_false_for_noncontiguous_words():
    assert not ar._is_contiguous_subsequence(("a", "c"), ("a", "b", "c"))


# ── find_repetitions: core n-gram mining over pre-extracted rows ───────────


def test_find_repetitions_reports_whole_line_repeat_under_four_words():
    lines = [
        ("iliad", 1, 1, "χαῖρε φίλος"),
        ("odyssey", 1, 1, "χαῖρε φίλος"),
    ]
    out = ar.find_repetitions(lines)
    assert len(out) == 1
    assert out[0]["text"] == "χαῖρε φίλος"
    assert out[0]["count"] == 2
    assert {tuple(r.values()) for r in out[0]["refs"]} == {
        ("iliad", 1, 1),
        ("odyssey", 1, 1),
    }


def test_find_repetitions_ignores_single_occurrence():
    lines = [("iliad", 1, 1, "χαῖρε φίλος καὶ ὑγίαινε πάντοτε")]
    assert ar.find_repetitions(lines) == []


def test_find_repetitions_finds_four_word_partial_ngram_across_different_lines():
    # The two lines share a run of exactly 4 words, flanked on both sides by
    # words that differ -- so that run is the maximal common n-gram and is
    # neither line's whole-line text.
    lines = [
        ("iliad", 1, 1, "α βήτα γάμμα δέλτα έψιλον ζήτα"),
        ("iliad", 1, 84, "θήτα βήτα γάμμα δέλτα έψιλον ήτα"),
    ]
    out = ar.find_repetitions(lines)
    texts = {e["text"] for e in out}
    assert "βήτα γάμμα δέλτα έψιλον" in texts
    # a 3-word sub-run below MIN_NGRAM_LEN is never a standalone candidate
    assert "γάμμα δέλτα έψιλον" not in texts


def test_find_repetitions_reports_the_maximal_ngram_when_a_longer_run_shares_the_same_lines():
    # Here the whole tail of both lines is identical (only the first word
    # differs), so the maximal common n-gram is the full 6-word tail; the
    # 4- and 5-word sub-runs of that same tail are pure redundancy (same ref
    # set) and must not also be reported.
    lines = [
        ("iliad", 1, 1, "τὸν δʼ ἀπαμειβόμενος προσέφη πόδας ὠκὺς Ἀχιλλεύς"),
        ("iliad", 1, 84, "τὴν δʼ ἀπαμειβόμενος προσέφη πόδας ὠκὺς Ἀχιλλεύς"),
    ]
    out = ar.find_repetitions(lines)
    assert len(out) == 1
    assert out[0]["text"] == "δʼ ἀπαμειβόμενος προσέφη πόδας ὠκὺς Ἀχιλλεύς"
    assert out[0]["count"] == 2


def test_find_repetitions_drops_subgram_with_identical_ref_set():
    # Both lines are byte-identical, so every n-gram within them (the whole
    # line and every 4+-word slice) shares the exact same 2-line ref set;
    # only the maximal (whole-line) entry should survive.
    lines = [
        ("iliad", 1, 1, "τὸν δʼ ἀπαμειβόμενος προσέφη πόδας ὠκὺς Ἀχιλλεύς·"),
        ("iliad", 1, 84, "τὸν δʼ ἀπαμειβόμενος προσέφη πόδας ὠκὺς Ἀχιλλεύς·"),
    ]
    out = ar.find_repetitions(lines)
    assert len(out) == 1
    assert out[0]["text"] == "τὸν δʼ ἀπαμειβόμενος προσέφη πόδας ὠκὺς Ἀχιλλεύς·"
    assert out[0]["count"] == 2


def test_find_repetitions_keeps_subgram_with_a_broader_ref_set():
    lines = [
        ("iliad", 1, 1, "τὸν δʼ ἀπαμειβόμενος προσέφη πόδας ὠκὺς Ἀχιλλεύς·"),
        ("iliad", 1, 84, "τὴν δʼ ἀπαμειβόμενος προσέφη πόδας ὠκὺς Ἀχιλλεύς·"),
        ("iliad", 2, 5, "καί μιν δʼ ἀπαμειβόμενος προσέφη πόδας κρατερός τις"),
    ]
    out = ar.find_repetitions(lines)
    texts = {e["text"]: e for e in out}
    # "δʼ ἀπαμειβόμενος προσέφη πόδας" recurs on all three lines (broader
    # ref set than any single whole-line match) and must be kept.
    assert "δʼ ἀπαμειβόμενος προσέφη πόδας" in texts
    assert texts["δʼ ἀπαμειβόμενος προσέφη πόδας"]["count"] == 3


def test_find_repetitions_normalizes_whitespace_but_keeps_accents():
    lines = [
        ("iliad", 1, 1, "χαῖρε   φίλος"),
        ("iliad", 2, 1, "χαῖρε φίλος"),
    ]
    out = ar.find_repetitions(lines)
    assert len(out) == 1
    assert out[0]["text"] == "χαῖρε φίλος"


def test_find_repetitions_output_sorted_by_count_desc_then_text():
    lines = [
        ("iliad", 1, 1, "α β γ δ"),
        ("iliad", 1, 2, "α β γ δ"),
        ("iliad", 1, 3, "ε ζ η θ"),
        ("iliad", 1, 4, "ε ζ η θ"),
        ("iliad", 1, 5, "ε ζ η θ"),
    ]
    out = ar.find_repetitions(lines)
    assert [e["text"] for e in out] == ["ε ζ η θ", "α β γ δ"]


# ── run(): end-to-end fixture (fake manifests + fake corpus) ──────────────


def _write_book(dist_dir: Path, book_n: int, lines: list[tuple[int, str]]) -> None:
    dist_dir.mkdir(parents=True, exist_ok=True)
    greek = [{"n": n, "text": text, "tokens": []} for n, text in lines]
    doc = {"book": book_n, "segments": [{"id": f"{book_n}:1", "column": str(book_n), "greek": greek}]}
    (dist_dir / f"book-{book_n:02d}.json").write_text(
        json.dumps(doc, ensure_ascii=False), encoding="utf-8"
    )


def _setup_fixture(tmp_path: Path, monkeypatch):
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    (manifests_dir / "iliad.yaml").write_text("work:\n  id: iliad\n", encoding="utf-8")
    (manifests_dir / "odyssey.yaml").write_text("work:\n  id: odyssey\n", encoding="utf-8")

    build_dir = tmp_path / "build"
    _write_book(
        build_dir / "dist" / "iliad", 1,
        [(1, "τὸν δʼ ἀπαμειβόμενος προσέφη πόδας ὠκὺς Ἀχιλλεύς·"), (2, "μῆνιν ἄειδε θεὰ")],
    )
    _write_book(
        build_dir / "dist" / "odyssey", 1,
        [(1, "τὸν δʼ ἀπαμειβόμενος προσέφη πόδας ὠκὺς Ἀχιλλεύς·"), (2, "ἄνδρα μοι ἔννεπε")],
    )

    monkeypatch.setattr(ar, "MANIFESTS_DIR", manifests_dir)
    monkeypatch.setattr(ar, "BUILD_DIR", build_dir)
    return build_dir


def test_run_emits_cross_epic_repetitions_json(tmp_path, monkeypatch):
    build_dir = _setup_fixture(tmp_path, monkeypatch)
    result = ar.run()

    assert sorted(result["works"]) == ["iliad", "odyssey"]
    assert result["lines_scanned"] == 4

    out_path = build_dir / "dist" / "repetitions.json"
    doc = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(doc) == 1
    entry = doc[0]
    assert entry["text"] == "τὸν δʼ ἀπαμειβόμενος προσέφη πόδας ὠκὺς Ἀχιλλεύς·"
    assert entry["count"] == 2
    assert {r["work"] for r in entry["refs"]} == {"iliad", "odyssey"}


def test_run_does_not_crash_when_a_works_dist_dir_is_missing(tmp_path, monkeypatch):
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    (manifests_dir / "iliad.yaml").write_text("work:\n  id: iliad\n", encoding="utf-8")
    (manifests_dir / "odyssey.yaml").write_text("work:\n  id: odyssey\n", encoding="utf-8")
    build_dir = tmp_path / "build"
    _write_book(build_dir / "dist" / "iliad", 1, [(1, "χαῖρε φίλος"), (2, "χαῖρε φίλος")])
    # odyssey dist dir intentionally absent (not built yet)

    monkeypatch.setattr(ar, "MANIFESTS_DIR", manifests_dir)
    monkeypatch.setattr(ar, "BUILD_DIR", build_dir)

    result = ar.run()
    assert result["lines_scanned"] == 2
    assert result["repetitions"] == 1


def test_run_is_deterministic_across_repeated_runs(tmp_path, monkeypatch):
    build_dir = _setup_fixture(tmp_path, monkeypatch)
    ar.run()
    first = (build_dir / "dist" / "repetitions.json").read_bytes()
    ar.run()
    second = (build_dir / "dist" / "repetitions.json").read_bytes()
    assert first == second
