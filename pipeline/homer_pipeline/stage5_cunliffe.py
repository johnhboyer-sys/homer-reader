"""Stage 5b: Cunliffe (A Lexicon of the Homeric Dialect) entries for
corpus-occurring lemmata, mirroring stage5_lsj's shape as a second native
lexicon pane beside LSJ.

Source: sources/cunliffe/cunliffe-1-lex.jsonl (the general lexicon, ~9,825
entries) and cunliffe-2-hompers.jsonl (the "Homeric personages" proper-name
volume, ~1,591 entries — included at launch by John's decision, 2026-07-17).
Both are flat JSONL (not a streamed TEI export like grc.lsj.xml), so they are
loaded fully into memory; at ~11.4k entries total this is trivial next to
LSJ's 116k-entry XML. Each row: {headword, urn, definition, citations, key,
type}. `key` is a Betacode headword, matched against Stage 4 lemmata the same
way stage5_lsj matches LSJ div2 keys, plus two Cunliffe-specific fallbacks
(see `destar_key` and `_ionic_variants` below) documented per-lemma in the
match-rate report stage7 prints.

Both volumes merge into ONE shard set (a proper name is just a row whose
source is hompers; a `src` field on the emitted entry records where it came
from — "lex", "hompers", or "both" when a key collides across volumes).
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from html import escape
from pathlib import Path

from .config import BUILD_DIR, SOURCES_DIR, Manifest
from .stage5_lsj import base_key, fold_key, needed_lemmata, shard_letter

_SOURCES = (
    ("lex", "cunliffe-1-lex.jsonl"),
    ("hompers", "cunliffe-2-hompers.jsonl"),
)

# TLG-style Betacode groups a capitalized word's breathing/accent BEFORE the
# base letter ("*(/ektwr" = capital + rough-breathing + acute + e-k-t-w-r, for
# Ἕκτωρ) — the convention Morpheus lemmata use. Cunliffe's `key` field is
# always lowercase and keeps the ordinary letter-then-diacritic order
# ("e(/ktwr"). destar_key undoes the capital grouping so a proper-noun lemma
# can hit Cunliffe's (uncapitalized) key directly.
_DESTAR_RE = re.compile(r"^([()/\\=|+_^]*)([a-z])(.*)$")


def destar_key(lemma: str) -> str | None:
    if not lemma.startswith("*"):
        return None
    m = _DESTAR_RE.match(lemma[1:])
    if not m:
        return None
    marks, letter, tail = m.groups()
    return letter + marks + tail


def _ionic_variants(fold: str) -> list[str]:
    """Homeric-dialect alpha/eta alternation, tried last: Ionic epic diction
    has eta where the Attic-normalized Morpheus lemma keeps the original long
    alpha after epsilon/iota/rho (Hera *(/hra vs. Cunliffe's e(/pi form h(/rh;
    a(rmoni/a vs. a(rmoni/h). A narrow, best-effort heuristic in the spirit of
    stage5_lsj's -ws/-teos fallbacks: only the final syllable is swapped
    (guarded so it never fires after another vowel, i.e. never inside a
    diphthong), so it cannot misfire on an unrelated word merely sharing a
    prefix. Measured to lift the match rate ~0.7pp on both works — real but
    modest, because most of the corpus's remaining gap is genuine dialect
    divergence beyond a single-syllable swap (see stage5's summary report)."""
    out = []
    for suf, rep in (("as", "hs"), ("an", "hn"), ("a", "h")):
        if fold.endswith(suf):
            stem = fold[: -len(suf)]
            if stem and stem[-1] not in "aeiouhw":
                out.append(stem + rep)
            break
    for suf, rep in (("hs", "as"), ("hn", "an"), ("h", "a")):
        if fold.endswith(suf):
            stem = fold[: -len(suf)]
            if stem and stem[-1] not in "aeiouhw":
                out.append(stem + rep)
            break
    return out


def cunliffe_candidates(lemma: str) -> list[tuple[str, str]]:
    """Ranked (index, value) lookups for a lemma against Cunliffe keys.

    Adapts stage5_lsj.lemma_candidates: same exact/digit-stripped-base/accent
    -fold core, plus two Cunliffe-specific fallbacks — destarring a
    capitalized (proper-noun) lemma, and the Ionic alpha/eta alternation —
    since Cunliffe's headword conventions diverge from LSJ's in exactly those
    two ways (see module docstring and `_ionic_variants`)."""
    cands: list[tuple[str, str]] = [("exact", lemma), ("base", base_key(lemma))]
    fold = fold_key(lemma)
    cands.append(("fold", fold))
    if fold.endswith("ws"):
        cands.append(("fold", fold[:-2] + "hs"))
    if fold.endswith("teos"):
        cands.append(("fold", fold[:-4] + "teon"))
    for v in _ionic_variants(fold):
        cands.append(("fold", v))
    destarred = destar_key(lemma)
    if destarred is not None:
        cands.append(("exact", destarred))
        cands.append(("base", base_key(destarred)))
        dfold = fold_key(destarred)
        cands.append(("fold", dfold))
        for v in _ionic_variants(dfold):
            cands.append(("fold", v))
    return cands


# citations[].data.urn is a CTS urn like
# "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:18.271" — tlg001 is the Iliad,
# tlg002 the Odyssey (both under Homer's tlg0012), and the trailing "18.271"
# is exactly book.line in the reader's verse-line citation grammar. Using the
# urn (rather than parsing the visible "Il."/"Od." abbreviation out of the ref
# text) is robust to continuation refs like "541," that carry no work prefix.
_CTS_RE = re.compile(r"(tlg\d+\.tlg\d+)\.[^:]*:(\d+)\.(\d+)$")
_TLG_WORK = {"tlg0012.tlg001": "iliad", "tlg0012.tlg002": "odyssey"}
_TRAIL_PUNCT = " ,.;:"


def linkify_definition(text: str, citations: list[dict]) -> str:
    """Escape a Cunliffe definition to safe HTML, turning each embedded
    citation ref ("Il. 18.271", or a bare continuation like "541,") into an
    internal-link marker. Every citations[].data.ref in the corpus was
    verified to appear as a literal, in-order substring of `definition`
    (measured: 99,046/99,046), so a simple sequential `str.find` suffices —
    no regex needed to locate the span.

    The emitted `<a>` carries data-work/data-book/data-line rather than a
    baked href: the reader's BASE_URL (GitHub Pages project-page prefix) is
    only known client-side, and the site's own hard rule is that a base path
    is never hardcoded in emitted content (see CLAUDE.md "Base-path pain").
    WordPopup.svelte's click handler resolves the real href via the existing
    citation machinery (workPath + formatLocValue), the same way BekkerJump
    and CommandPalette do."""
    parts: list[str] = []
    pos = 0
    for c in citations:
        data = c.get("data") or {}
        ref = data.get("ref") or ""
        if not ref:
            continue
        idx = text.find(ref, pos)
        if idx == -1:
            # Not observed in the corpus (see docstring), but degrade to
            # leaving this citation un-linked rather than dropping/misplacing
            # text.
            continue
        parts.append(escape(text[pos:idx]))
        core = ref.rstrip(_TRAIL_PUNCT)
        trail = ref[len(core):]
        target = None
        m = _CTS_RE.search(data.get("urn") or "")
        if m:
            work = _TLG_WORK.get(m.group(1))
            if work:
                target = (work, m.group(2), m.group(3))
        if target and core:
            work, book, line = target
            parts.append(
                f'<a class="cunliffe-cite" href="#" data-work="{escape(work)}" '
                f'data-book="{escape(book)}" data-line="{escape(line)}">'
                f'{escape(core)}</a>{escape(trail)}'
            )
        else:
            parts.append(escape(ref))
        pos = idx + len(ref)
    parts.append(escape(text[pos:]))
    return "".join(parts)


def entry_html(rows: list[dict]) -> str:
    """Render every row sharing a key (usually one; Cunliffe numbers homonyms
    only in the headword text — "ἄγη2" — not in a distinct key, unlike LSJ's
    a)1/a)2 convention) as its own sense block."""
    return "".join(
        f'<div class="cunliffe-sense">{linkify_definition(r["definition"], r.get("citations", []))}</div>'
        for r in rows
    )


def _merged_src(rows: list[dict]) -> str:
    srcs = {r["src"] for r in rows}
    return "both" if len(srcs) > 1 else srcs.pop()


def run(manifest: Manifest) -> Path:
    analyses = json.loads(
        (BUILD_DIR / "stage4" / "analyses.json").read_text(encoding="utf-8")
    )
    lemmata = needed_lemmata(analyses)

    all_keys: set[str] = set()
    base_index: dict[str, list[str]] = defaultdict(list)
    fold_index: dict[str, list[str]] = defaultdict(list)
    rows_by_key: dict[str, list[dict]] = defaultdict(list)
    entries_by_src = {"lex": 0, "hompers": 0}
    for src, filename in _SOURCES:
        path = SOURCES_DIR / "cunliffe" / filename
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                key = row["key"]
                all_keys.add(key)
                base_index[base_key(key)].append(key)
                fold_index[fold_key(key)].append(key)
                rows_by_key[key].append(
                    {
                        "headword": row["headword"],
                        "definition": row["definition"],
                        "citations": row.get("citations", []),
                        "src": src,
                    }
                )
                entries_by_src[src] += 1

    lemma_map: dict[str, list[str]] = {}
    missing: list[str] = []
    for lemma in sorted(lemmata):
        matched: list[str] | None = None
        for kind, value in cunliffe_candidates(lemma):
            if kind == "exact" and value in all_keys:
                matched = [value]
            elif kind == "base" and base_index.get(value):
                matched = sorted(base_index[value])
            elif kind == "fold" and fold_index.get(value):
                matched = sorted(fold_index[value])
            if matched:
                break
        if matched:
            lemma_map[lemma] = matched
        else:
            missing.append(lemma)
    wanted = {k for keys in lemma_map.values() for k in keys}

    shards: dict[str, dict] = defaultdict(dict)
    kept_lex = 0
    kept_hompers = 0
    for key in wanted:
        rows = rows_by_key[key]
        shards[shard_letter(key)][key] = {
            "key": key,
            "head": rows[0]["headword"],
            "html": entry_html(rows),
            "src": _merged_src(rows),
        }
        for r in rows:
            if r["src"] == "lex":
                kept_lex += 1
            else:
                kept_hompers += 1

    out_dir = BUILD_DIR / "stage5"
    shard_dir = out_dir / "cunliffe"
    shard_dir.mkdir(parents=True, exist_ok=True)
    for letter, entries in sorted(shards.items()):
        (shard_dir / f"{letter}.json").write_text(
            json.dumps(entries, ensure_ascii=False), encoding="utf-8"
        )
    (out_dir / "cunliffe_lemma_map.json").write_text(
        json.dumps(lemma_map, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "cunliffe_missing_lemmata.json").write_text(
        json.dumps(missing, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    summary = {
        "lemmata_needed": len(lemmata),
        "cunliffe_entries_kept": len(wanted),
        "cunliffe_rows_kept_lex": kept_lex,
        "cunliffe_rows_kept_hompers": kept_hompers,
        "shards": len(shards),
        "lemmata_without_entry": len(missing),
    }
    (out_dir / "cunliffe_summary.json").write_text(json.dumps(summary, indent=1))
    return shard_dir
