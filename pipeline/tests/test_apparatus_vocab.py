import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from homer_pipeline import apparatus_vocab as v
from homer_pipeline.config import Manifest


# ── resolve_lemma / is_proper_name: the two pure lookups everything else
#    is built on ────────────────────────────────────────────────────────────


def test_resolve_lemma_takes_first_analyses_entry():
    analyses = {"k1": [{"lemma": "primary"}, {"lemma": "homonym"}]}
    assert v.resolve_lemma({"t": "x", "k": "k1"}, analyses) == "primary"


def test_resolve_lemma_returns_none_for_unresolved_key():
    # A token key with no analyses entry at all must never fall back to the
    # raw Beta Code key -- that is not a real "word to know" (see module
    # docstring), so it is simply not counted.
    assert v.resolve_lemma({"t": "x", "k": "missing"}, {}) is None


def test_is_proper_name_true_for_star_prefixed_lemma():
    # Real corpus example: Ἕκτωρ resolves to the Beta Code lemma
    # '*(/ektwr' -- the '*' is exactly the capitalization signal
    # stage4_morphology/beta.py's capital_key produces for a proper name.
    assert v.is_proper_name("*(/ektwr") is True


def test_is_proper_name_false_for_ordinary_lemma():
    assert v.is_proper_name("mh=nis") is False


# ── top_stoplist: mechanical, no hand list ──────────────────────────────────


def test_top_stoplist_picks_n_most_frequent_with_deterministic_tiebreak():
    pooled = Counter({"a": 5, "b": 5, "c": 3, "d": 1})
    # a and b tie at count 5 -> alphabetical tiebreak picks 'a' before 'b'.
    assert v.top_stoplist(pooled, size=1) == {"a"}
    assert v.top_stoplist(pooled, size=2) == {"a", "b"}
    assert v.top_stoplist(pooled, size=3) == {"a", "b", "c"}


def test_pooled_lemma_counts_sums_across_works_and_books():
    per_work = {
        "workA": {1: Counter({"x": 2}), 2: Counter({"x": 1, "y": 4})},
        "workB": {1: Counter({"x": 3, "y": 1})},
    }
    pooled = v.pooled_lemma_counts(per_work)
    assert pooled == Counter({"x": 6, "y": 5})


# ── book_vocab_entries: ranking + the two independent filters ──────────────


def test_book_vocab_entries_excludes_stoplisted_lemmas():
    counts = Counter({"stopword": 50, "content": 5})
    entries, _ = v.book_vocab_entries(counts, stoplist={"stopword"}, gloss_map={"content": "a gloss"})
    assert [e["lemma"] for e in entries] == ["content"]


def test_book_vocab_entries_excludes_proper_names_and_reports_them():
    counts = Counter({"*propername": 40, "commonword": 5})
    entries, proper = v.book_vocab_entries(counts, stoplist=set(), gloss_map={})
    assert [e["lemma"] for e in entries] == ["commonword"]
    assert proper == {"*propername"}


def test_book_vocab_entries_ranks_by_count_desc_then_lemma_asc():
    counts = Counter({"zeta": 3, "alpha": 3, "beta": 5})
    entries, _ = v.book_vocab_entries(counts, stoplist=set(), gloss_map={})
    assert [e["lemma"] for e in entries] == ["beta", "alpha", "zeta"]


def test_book_vocab_entries_caps_at_limit():
    counts = Counter({f"w{i}": 10 - i for i in range(10)})
    entries, _ = v.book_vocab_entries(counts, stoplist=set(), gloss_map={}, limit=3)
    assert len(entries) == 3
    assert [e["lemma"] for e in entries] == ["w0", "w1", "w2"]


def test_book_vocab_entries_honesty_omits_gloss_key_when_none_found():
    # HONESTY RULE: no fabricated placeholder text -- the key is simply absent.
    counts = Counter({"glossed": 5, "glossless": 4})
    entries, _ = v.book_vocab_entries(
        counts, stoplist=set(), gloss_map={"glossed": "a real gloss"}
    )
    by_lemma = {e["lemma"]: e for e in entries}
    assert by_lemma["glossed"]["gloss"] == "a real gloss"
    assert "gloss" not in by_lemma["glossless"]


# ── lemma_gloss_map: honest, deterministic, first-non-empty-wins ───────────


def test_lemma_gloss_map_skips_lemmata_with_no_non_empty_gloss(tmp_path):
    dist_dir = tmp_path / "work"
    dist_dir.mkdir()
    (dist_dir / "analyses.json").write_text(
        json.dumps({
            "k1": [{"lemma": "hasgloss", "gloss": "a gloss"}],
            "k2": [{"lemma": "nogloss", "gloss": ""}],
            "k3": [{"lemma": "properonly"}],
        }),
        encoding="utf-8",
    )
    gloss_map = v.lemma_gloss_map(dist_dir)
    assert gloss_map == {"hasgloss": "a gloss"}


def test_lemma_gloss_map_first_non_empty_wins_deterministically(tmp_path):
    dist_dir = tmp_path / "work"
    dist_dir.mkdir()
    # Two keys resolve to the same lemma with different glosses; sorted-key
    # iteration means 'k1' (alphabetically first) wins over 'k2'.
    (dist_dir / "analyses.json").write_text(
        json.dumps({
            "k2": [{"lemma": "shared", "gloss": "second"}],
            "k1": [{"lemma": "shared", "gloss": "first"}],
        }),
        encoding="utf-8",
    )
    assert v.lemma_gloss_map(dist_dir) == {"shared": "first"}


def test_capped_gloss_truncates_on_word_boundary():
    long_gloss = "word " * 30  # far past MAX_GLOSS_LEN
    capped = v._capped_gloss(long_gloss.strip())
    assert len(capped) <= v.MAX_GLOSS_LEN + 1  # +1 for the ellipsis char
    assert capped.endswith("…")
    assert not capped[:-1].endswith(" ")  # truncated cleanly, no dangling space


def test_capped_gloss_leaves_short_gloss_untouched():
    assert v._capped_gloss("sheep") == "sheep"


# ── run(): fixture-corpus integration, cross-epic pooling, determinism ─────


def _tok(k):
    return {"t": k, "o": 0, "k": k}


def _write_book(dist_dir: Path, book_n: int, token_keys: list[str]) -> None:
    dist_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "book": book_n,
        "segments": [{
            "id": f"{book_n}:1",
            "column": str(book_n),
            "greek": [{"n": 1, "tokens": [_tok(k) for k in token_keys]}],
        }],
    }
    (dist_dir / f"book-{book_n:02d}.json").write_text(
        json.dumps(doc, ensure_ascii=False), encoding="utf-8"
    )


def _write_analyses(dist_dir: Path, entries: dict) -> None:
    dist_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "analyses.json").write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")


ANALYSES_FIXTURE = {
    "k_common": [{"lemma": "commonword", "gloss": "a very frequent word"}],
    "k_target": [{"lemma": "targetword", "gloss": "the word we want to see ranked"}],
    "k_rare": [{"lemma": "rareword", "gloss": "a rare word"}],
    "k_noglossword": [{"lemma": "noglossword"}],
    "k_name": [{"lemma": "*ProperName"}],
    # unresolved key deliberately omitted -- a token using it has no entry.
}


def _fixture_manifest(tmp_path: Path, work_id: str = "fixture") -> Manifest:
    return Manifest({"work": {"id": work_id}}, tmp_path / f"{work_id}.yaml")


def _setup_two_work_fixture(tmp_path: Path, monkeypatch) -> tuple[Manifest, Path]:
    """Two works ('fixture' and 'other'), so the whole-corpus pooled stoplist
    genuinely differs from either work's own book counts -- this is what
    proves cross-epic pooling, not just per-work counting."""
    build_dir = tmp_path / "build"
    monkeypatch.setattr(v, "BUILD_DIR", build_dir)

    fixture_dist = build_dir / "dist" / "fixture"
    _write_analyses(fixture_dist, ANALYSES_FIXTURE)
    # k_common x8, k_target x5, k_rare x2, k_noglossword x1, k_name x6,
    # plus one unresolved token (skipped).
    _write_book(
        fixture_dist, 1,
        ["k_common"] * 8 + ["k_target"] * 5 + ["k_rare"] * 2
        + ["k_noglossword"] + ["k_name"] * 6 + ["k_unresolved"],
    )

    # The other work pushes k_common's POOLED total far higher than anything
    # in 'fixture' alone, so it lands in the stoplist only because of
    # cross-epic pooling.
    other_dist = build_dir / "dist" / "other"
    _write_analyses(other_dist, {"k_common": [{"lemma": "commonword", "gloss": "a very frequent word"}]})
    _write_book(other_dist, 1, ["k_common"] * 50)

    manifest = _fixture_manifest(tmp_path)
    return manifest, fixture_dist


def test_run_emits_vocab_json_with_draft_status_and_books(tmp_path, monkeypatch):
    manifest, fixture_dist = _setup_two_work_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(v, "STOPLIST_SIZE", 1)  # only 'commonword' should stoplist

    result = v.run(manifest, work_ids=["fixture", "other"])

    doc = json.loads((fixture_dist / "vocab.json").read_text(encoding="utf-8"))
    assert doc["status"] == "draft"
    assert set(doc["books"]) == {"1"}
    lemmas = [e["lemma"] for e in doc["books"]["1"]]
    # commonword: stoplisted (pooled top-1). *ProperName: proper-name filtered.
    assert "commonword" not in lemmas
    assert "*ProperName" not in lemmas
    # targetword (count 5) outranks rareword (count 2).
    assert lemmas.index("targetword") < lemmas.index("rareword")
    assert result["books_covered"] == 1
    assert result["proper_names_excluded_distinct"] == 1


def test_run_never_touches_book_json(tmp_path, monkeypatch):
    manifest, fixture_dist = _setup_two_work_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(v, "STOPLIST_SIZE", 1)
    book_path = fixture_dist / "book-01.json"
    before = book_path.read_bytes()

    v.run(manifest, work_ids=["fixture", "other"])

    assert book_path.read_bytes() == before


def test_run_honesty_omits_gloss_for_glossless_lemma(tmp_path, monkeypatch):
    manifest, fixture_dist = _setup_two_work_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(v, "STOPLIST_SIZE", 1)

    result = v.run(manifest, work_ids=["fixture", "other"])

    doc = json.loads((fixture_dist / "vocab.json").read_text(encoding="utf-8"))
    by_lemma = {e["lemma"]: e for e in doc["books"]["1"]}
    assert "gloss" not in by_lemma["noglossword"]
    assert result["total_entries"] == 3  # targetword, rareword, noglossword
    assert result["entries_with_gloss"] == 2


def test_run_is_deterministic_across_repeated_runs(tmp_path, monkeypatch):
    manifest, fixture_dist = _setup_two_work_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(v, "STOPLIST_SIZE", 1)

    v.run(manifest, work_ids=["fixture", "other"])
    first = (fixture_dist / "vocab.json").read_bytes()
    v.run(manifest, work_ids=["fixture", "other"])
    second = (fixture_dist / "vocab.json").read_bytes()
    assert first == second


# ── real-book fixture assertion (skipped without a local build/dist) ───────

REAL_DIST_DIR = ROOT / "build" / "dist"


@pytest.mark.skipif(
    not (REAL_DIST_DIR / "odyssey").is_dir(),
    reason="requires a local build/dist/odyssey (homer_pipeline stage7, then vocab)",
)
def test_real_odyssey_book9_surfaces_the_cyclops_flocks_noun():
    # Od. 9 is the Cyclops episode: Polyphemus's flocks are the book's most
    # concrete recurring noun. Κύκλωψ itself is a proper name and correctly
    # excluded (see is_proper_name); 'μῆλον' (Beta Code 'mh=lon1', "sheep")
    # is the real common noun this stage actually surfaces at the top of
    # Od. 9's ranked list against the live corpus (measured 2026-07-17: count
    # 19, gloss "sheep", rank #2 behind the pronoun-ish 'τότε'). Pinned here
    # so a future regression in lemma resolution or the stoplist/proper-name
    # filters is caught, not just a byte-diff.
    result = v.run(Manifest.for_work("Odyssey"), work_ids=["iliad", "odyssey"])
    doc = json.loads(result["path"].read_text(encoding="utf-8"))
    book9 = {e["lemma"]: e for e in doc["books"]["9"]}
    assert "mh=lon1" in book9
    assert book9["mh=lon1"]["gloss"] == "sheep"
    assert book9["mh=lon1"]["count"] >= 15
    # The Cyclops himself is a proper name and must be excluded, not just
    # absent by chance.
    assert "*ku/klwy" not in book9
