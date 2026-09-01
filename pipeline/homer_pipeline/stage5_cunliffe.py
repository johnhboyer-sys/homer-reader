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

# Scaife's citations[] does not carry every reference Cunliffe prints. Measured
# on the shipped shards before this pass: 64,050 of 78,273 refs were linked and
# 14,223 were dead text, spread over 3,032 of 7,511 entries. A reader whose
# whole purpose is jumping to the poem was being handed "Il. 5.396" as
# unclickable prose two words after an identical live link.
#
# So anything left over is linked from the visible reference. Only a FULL ref
# is matched — work abbreviation, book and line all present. Bare continuations
# ("Il. 19.35, 75", where 75 means Il. 19.75) are deliberately left alone: the
# citations[] pass already resolves those from their urns, and guessing which
# book a loose number belongs to is how a citation silently points at the wrong
# line.
_PLAIN_REF_RE = re.compile(r"\b(Il|Od)\.\s*(\d+)\.(\d+)")
_ABBR_WORK = {"Il": "iliad", "Od": "odyssey"}


def _link_plain_refs(escaped: str) -> str:
    """Link full references in an already-escaped run of definition text."""
    def one(m: re.Match[str]) -> str:
        return (
            f'<a class="cunliffe-cite" href="#" data-work="{_ABBR_WORK[m.group(1)]}" '
            f'data-book="{m.group(2)}" data-line="{m.group(3)}">{m.group(0)}</a>'
        )
    return _PLAIN_REF_RE.sub(one, escaped)


# Cunliffe points from one entry to another constantly — "See πολλός." — and
# those pointers were dead text. The target is resolved against the head of
# every entry in the SOURCE, then kept only if that entry actually ships, so a
# pointer is either live or plain: never a link to nothing.
_SEE_RE = re.compile(r"\bSee(?: also)? ([\u0370-\u03ff\u1f00-\u1fff][^\s.,;:\]]*)")


def _link_xrefs(html: str, resolve) -> str:
    """Link "See <headword>" pointers whose target ships. Runs over rendered
    HTML, so it must not reach inside an existing anchor — the citation links
    are already in place and their text can contain nothing this matches."""
    out: list[str] = []
    pos = 0
    for m in re.finditer(r"<a\b[^>]*>.*?</a>", html, re.S):
        out.append(_link_xrefs_run(html[pos:m.start()], resolve))
        out.append(m.group(0))
        pos = m.end()
    out.append(_link_xrefs_run(html[pos:], resolve))
    return "".join(out)


def _link_xrefs_run(run: str, resolve) -> str:
    def one(m: re.Match[str]) -> str:
        key = resolve(m.group(1))
        if not key:
            return m.group(0)
        head = m.group(0)[: m.start(1) - m.start(0)]
        return (
            f'{head}<a class="cunliffe-xref" href="#" data-key="{escape(key)}">'
            f'{m.group(1)}</a>'
        )
    return _SEE_RE.sub(one, run)


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
        parts.append(_link_plain_refs(escape(text[pos:idx])))
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
            parts.append(_link_plain_refs(escape(ref)))
        pos = idx + len(ref)
    parts.append(_link_plain_refs(escape(text[pos:])))
    return "".join(parts)


# ── Cunliffe as a T8 record ────────────────────────────────────────────────
#
# Cunliffe ships one flat prose string per entry. grammata's T8 presentation —
# sense rows, division tabs, example drawers — renders from a STRUCTURED record
# instead: rows carrying a level, a number and a definition. Confirmed with
# grammar-site 2026-08-31: a T8 pack IS a list of these records, so this shape
# is the same whether the entries are served from grammata or rendered from
# here.
#
# Every rule below was measured over all 9,825 source entries, and every one of
# them replaced a rule that sounded right and was not:
#
#   * The colon is NOT the definition/evidence boundary. After a spaced " : "
#     the next thing is Greek 71.7% of the time and a citation 27.1%; after an
#     unspaced ": " it is 72.1% / 26.5%. The spacing carries no signal at all.
#   * "The definition is the leading English run" fails too — definitions
#     contain Greek ("Of κυδοιμός figured as a symbol").
#   * A sense number cannot be recognised by what follows it. 2,651 entries
#     carry "1 sing." / "2 pl.", which is person and number.
#
# What does work is SEQUENCE: real sense numbers run 1, 2, 3…, so a candidate
# is kept only if it continues the run and a stray line number rejects itself.

# A division banner: " I ", " II " … before a capital. 64 entries carry them.
_ROMAN_RE = re.compile(r"(?:^|[\s.])([IVX]{1,4})\s+(?=[A-ZΑ-Ω(])")
# A candidate sense number.
_SENSE_CAND_RE = re.compile(r"(?:^|[\s.(])(\d{1,2})\s+")
# Person/number labels, which open with a digit and are never senses.
_MORPH_RE = re.compile(r"^(sing|pl|dual|s|p)\b")
_BRACKET_RE = re.compile(r"\[[^\]]*\]")
_GREEK_RE = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]")
_FULL_CITE_RE = re.compile(r"\b(?:Il|Od)\.\s*\d+\.\d+")
# A period after a short Greek token is Cunliffe abbreviating its own headword
# inside a quotation ("σκεψάμενος ἐς νῆʼ ἁ. καὶ μεθʼ ἑταίρους"), not a sentence
# end. Reading those as boundaries cut 3,179 quotations in half.
_ABBREV_TAIL_RE = re.compile(r"(^|\s)[\u0370-\u03ff\u1f00-\u1fff]{1,3}[ʼ’]?$")


def split_senses(definition: str) -> dict:
    """Split a definition into its head run and its numbered senses."""
    divisions = [
        {"at": m.start() + m.group(0).index(m.group(1)), "n": m.group(1)}
        for m in _ROMAN_RE.finditer(definition)
    ]
    # Spans inside [ ... ] are etymology, and Cunliffe's etymologies carry
    # HOMONYM REFERENCES shaped exactly like sense numbers: ἀμβατός reads
    # "[ἀμ-, ἀνα- 1 + βα-, βαίνω.]" where that 1 points at ἀνα-1. A round-trip
    # check cannot see this — a false 1 still forms a valid run and loses no
    # characters — so it has to be excluded by position. 185 false senses.
    brackets = [(m.start(), m.end()) for m in _BRACKET_RE.finditer(definition)]

    cands = []
    for m in _SENSE_CAND_RE.finditer(definition):
        at = m.start() + m.group(0).index(m.group(1))
        if any(a <= at < b for a, b in brackets):
            continue
        if _MORPH_RE.match(definition[at + len(m.group(1)):].lstrip()):
            continue
        after = at + len(m.group(1))
        ws = len(definition[after:]) - len(definition[after:].lstrip())
        cands.append({"at": at, "n": int(m.group(1)), "end": after + ws})

    kept: list[dict] = []
    want = 1
    for c in cands:
        prior = [d["at"] for d in divisions if d["at"] < c["at"]]
        div_at = prior[-1] if prior else -1
        if kept and div_at > kept[-1]["at"]:
            want = 1
        if c["n"] == want:
            kept.append({**c, "div_at": div_at})
            want += 1

    if not kept:
        return {"head": definition, "senses": [], "divisions": divisions}
    senses = []
    for i, k in enumerate(kept):
        end = kept[i + 1]["at"] if i + 1 < len(kept) else len(definition)
        senses.append({
            "n": str(k["n"]), "div_at": k["div_at"],
            "start": k["end"], "end": end,
            "body": definition[k["end"]:end].strip(),
        })
    return {"head": definition[:kept[0]["at"]], "senses": senses, "divisions": divisions}


def _evidence_start(body: str, cite_at: int) -> int:
    """Where a sense's evidence begins, walking back from its first citation."""
    before = body[:cite_at]
    bound = -1
    for m in re.finditer(r"[:.;]\s", before):
        if m.group(0)[0] == "." and _ABBREV_TAIL_RE.search(before[:m.start()]):
            continue
        bound = m.end()
    run = before[bound if bound != -1 else 0:]
    # A quotation is a phrase Homer wrote. It never contains an etymology
    # bracket, and it is not a paragraph: without these guards the head run of
    # an unnumbered entry — "ἄλειφαρ -ατος, τό [ἀλείφω.] Unguent, oil" — is
    # Greek enough to be mistaken for one, and the definition disappears into
    # `g` where it reads as though Homer wrote it.
    if "[" in run or "]" in run:
        return cite_at
    if _GREEK_RE.search(run) and run.strip():
        return bound if bound != -1 else 0
    return cite_at


def parse_sense(body: str) -> tuple[str, str]:
    """A sense body as (definition, evidence).

    Evidence is anchored on the CITATION, which is the one unambiguous mark in
    the text and is already what the reader clicks; a quotation attaches to the
    citation that follows it."""
    m = _FULL_CITE_RE.search(body)
    if not m:
        return body.strip(), ""
    start = _evidence_start(body, m.start())
    # The colon that introduced the quotation belongs to neither side once the
    # two are separate fields.
    return body[:start].strip().rstrip(" :;,"), body[start:].strip()


# Evidence, split into what T8 renders: `ex` is a quotation with its citation
# (and the parenthetical translation Cunliffe sometimes gives it), `au` is a
# bare citation with no quotation attached.
#
# Cunliffe writes evidence as "QUOTATION Cite. Cf. Cite, Cite : Cite." — the
# quotation leads, its own citation follows it, and everything after "Cf." is
# corroboration with nothing quoted.
#
# Bare continuations are real: "Il. 19.35, 75" means Il. 19.75. They are kept as
# printed rather than expanded, because the citations[] pass that resolves them
# from urns owns that, and guessing which book a loose number belongs to is how
# a citation quietly points at the wrong line.
_CITE_TOKEN_RE = re.compile(r"\b(?:Il|Od)\.\s*\d+\.\d+|\b\d+\b")
# Connectors between pieces of evidence. These carry no information a T8 row
# keeps — it joins citations with its own separator — so they are dropped, and
# the audit below asserts that NOTHING ELSE is.
# Only genuinely empty joining words are dropped. "etc." is NOT one: in a
# lexicon it tells the reader the citation list is not exhaustive, and treating
# it as furniture cost 1,336 entries that signal. Dashes and "So" likewise carry
# Cunliffe's own sequencing and stay in the text.
_CONNECTOR_RE = re.compile(r"^[\s,.:;=]*(?:Cf\.|cf\.|and|=)?[\s,.:;=]*")
_PAREN_RE = re.compile(r"\(([^)]*)\)\s*$")
# Cunliffe's own "and so on" marks. Kept in the text, never given a row.
_TRAILING_NOTE_RE = re.compile(r"[\s.:,;–-]*(?:etc\.?|So|and so on)?[\s.:,;–-]*")


def _append_note(segment: dict, note: str) -> None:
    """Attach one of Cunliffe's "and so on" marks to the row it qualifies.

    Never dropped — in a lexicon "etc." says the list is not exhaustive — and
    never given a row of its own. It joins the CITATION LIST it qualifies rather
    than the definition: a row is rendered as "Il. 1.158 · 226 · etc.", which is
    how the list reads on the page, where appending it to the definition gave
    "With, along with, in company with etc. etc." A repeat is kept — the two
    marks are separately printed, and skipping the second was content loss the
    corpus audit caught at once.
    """
    segment["au"].append(note)


def split_evidence(evidence: str) -> list[dict]:
    """One sense's evidence as an ordered list of segments.

    A segment is {z?, ex[], au[]}. A new one opens whenever Cunliffe writes
    PROSE between citations, because that prose is a further statement with its
    own evidence — "Absol. Il. 1.158", or ἀγακλεής's "Very famous, glorious,
    splendid, worthy" following its principal parts.

    Dropping that prose is what an earlier version did, and it cost 2,534
    entries (25.8%) real content — ἀγακλεής lost its entire definition, because
    the definition follows the principal-parts citations and so lands here
    rather than in `z`. Nothing but connectors is ever discarded now.
    """
    segments: list[dict] = [{"ex": [], "au": []}]
    pos = 0
    for m in _CITE_TOKEN_RE.finditer(evidence):
        lead = evidence[pos:m.start()]
        pos = m.end()
        cite = m.group(0)
        body = _CONNECTOR_RE.sub("", lead).strip()
        # English ahead of the quotation is Cunliffe's own prose, not part of
        # what it is quoting: "Together, at the same moment: ἁ. ἄμφω σύν ῥʼ
        # ἔπεσον" is a remark and then a quotation. Split at the first Greek,
        # or the remark ends up inside `g` and reads as though Homer wrote it.
        gm = _GREEK_RE.search(body)
        if gm and gm.start() > 0:
            prose = _CONNECTOR_RE.sub("", body[:gm.start()]).strip().rstrip(" :;,")
            if prose:
                # A note here qualifies the row above and must not open a new
                # one — otherwise the quotation that follows lands on a row
                # whose whole definition reads "etc.". That was 839 rows.
                if _TRAILING_NOTE_RE.fullmatch(prose):
                    _append_note(segments[-1], prose)
                else:
                    segments.append({"z": prose, "ex": [], "au": []})
            body = body[gm.start():].strip()
        if _GREEK_RE.search(body):
            gloss = ""
            pm = _PAREN_RE.search(body)
            if pm and not _GREEK_RE.search(pm.group(1)):
                gloss = pm.group(1).strip()
                body = body[:pm.start()].strip()
            item = {"g": body, "c": cite}
            if gloss:
                item["e"] = gloss
            segments[-1]["ex"].append(item)
        elif body:
            if _TRAILING_NOTE_RE.fullmatch(body):
                _append_note(segments[-1], body)
                segments[-1]["au"].append(cite)
            else:
                # prose with no Greek: a new statement, and the citations that
                # follow belong to it
                segments.append({"z": body, "ex": [], "au": [cite]})
        else:
            segments[-1]["au"].append(cite)
    tail = _CONNECTOR_RE.sub("", evidence[pos:]).strip()
    if tail:
        if _GREEK_RE.search(tail):
            segments[-1]["ex"].append({"g": tail})
        elif _TRAILING_NOTE_RE.fullmatch(tail):
            _append_note(segments[-1], tail)
        else:
            segments.append({"z": tail, "ex": [], "au": []})
    return segments


def _rows_from(base: dict, evidence: str) -> list[dict]:
    """`base` carries lv/n/z; evidence segments extend it, the first onto the
    row itself and any others as unnumbered continuations of it."""
    out = []
    for i, seg in enumerate(split_evidence(evidence)):
        if i == 0:
            row = dict(base)
        else:
            # A continuation: same level, no number of its own. `s` stays unset
            # — grammata draws its dash on a row carrying `s` with an empty
            # numeral, and these are Cunliffe's own prose, not supplied text.
            row = {"lv": base["lv"], "n": "", "z": seg.get("z", "")}
        if i == 0 and seg.get("z"):
            row["z"] = (row.get("z", "") + " " + seg["z"]).strip()
        if seg["ex"]:
            row["ex"] = seg["ex"]
        if seg["au"]:
            row["au"] = seg["au"]
        out.append(row)
    return out


# The morphology an entry opens with, before any definition: declension endings
# ("-ου,", "-ατος,"), gender, a quantity mark, an etymology bracket. Cunliffe
# closes it with a full stop.
_MORPH_HEAD_RE = re.compile(
    r"^(?:\s*(?:-[^\s,.]+|[,;]|\([^)]*\)|\[[^\]]*\]|[ὁἡτότάοἱαἱ]{1,3}|"
    r"\b(?:masc|fem|neut|pl|sing|dual)\b\.?))+"
)


def _split_head_run(body: str) -> tuple[str, str]:
    """(head run, the rest) for an entry with no numbered senses.

    Without this the head run is Greek enough to be read as a QUOTATION, and
    the definition goes with it: αἴγειρος came out with z="-" and the poplar
    itself sitting in `g`, as though Homer had written "ου, ἡ. The poplar".
    151 entries did that.
    """
    m = _MORPH_HEAD_RE.match(body)
    if not m or not m.group(0).strip(" ,;"):
        return "", body
    end = m.end()
    # Cunliffe ends the run with a full stop; take it and any gender that
    # trails the endings ("-ου, ἡ.").
    tail = re.match(r"\s*(?:[ὁἡτότάοἱαἱ]{1,3}|\bpl\b|,)*\s*\.", body[end:])
    if tail:
        end += tail.end()
    return body[:end].strip(), body[end:]


def to_t8(key: str, headword: str, definition: str) -> dict:
    """A Cunliffe entry as a T8 record: head, the undecomposed head run, and
    rows. Division banners are lv 0 and carry the numeral plus the division's
    own heading; senses are lv 1.

    `s` is never set. grammata renders a continuation dash on rows that carry
    `s` AND an empty numeral, and three quarters of this dictionary is a single
    unnumbered row — every one of which would sprout a dash it should not have.
    """
    p = split_senses(definition)
    roman = {d["at"]: d["n"] for d in p["divisions"]}
    if not p["senses"]:
        head_run, rest = _split_head_run(definition[len(headword):])
        z, evidence = parse_sense(rest)
        return {"key": key, "head": headword, "i": head_run,
                "rows": _rows_from({"lv": 1, "n": "", "z": z}, evidence)}

    head_end = len(p["head"])
    # Each sense becomes one or more rows (prose between citations opens a
    # continuation), so rows are built per sense and kept with the span they
    # came from — a division that interrupts a sense has to rebuild it from
    # that span, and only the sense's FIRST row carries the offsets.
    built: list[tuple[dict, list[dict]]] = []   # (sense, its rows)
    last_div = None
    banners: list[tuple[int, dict]] = []        # (index into built, banner row)
    for sense in p["senses"]:
        div_at = sense["div_at"]
        if div_at != -1 and div_at != last_div:
            numeral = roman.get(div_at, "")
            heading = ""
            if built and built[-1][0]["end"] > div_at:
                # The division interrupts the previous sense: its numeral and
                # heading sit between one sense and the next. Cut that sense
                # short and give the span to the banner — emitting the numeral
                # without removing it made 63 entries GAIN characters.
                prev_sense, _ = built[-1]
                heading = definition[div_at + len(numeral):prev_sense["end"]]
                z, evidence = parse_sense(definition[prev_sense["start"]:div_at])
                built[-1] = ({**prev_sense, "end": div_at},
                             _rows_from({"lv": 1, "n": prev_sense["n"], "z": z}, evidence))
            elif div_at < head_end:
                # The first division sits inside the head run, so its numeral is
                # already in `i`; take it out or the entry carries it twice.
                heading = definition[div_at + len(numeral):head_end]
                head_end = div_at
            banners.append((len(built), {"lv": 0, "n": numeral,
                                         "z": heading.strip(), "b": 1}))
            last_div = div_at
        z, evidence = parse_sense(sense["body"])
        built.append((sense, _rows_from({"lv": 1, "n": sense["n"], "z": z}, evidence)))

    rows: list[dict] = []
    banner_at = {i: b for i, b in banners}
    for i, (_, sense_rows) in enumerate(built):
        if i in banner_at:
            rows.append(banner_at[i])
        rows.extend(sense_rows)

    # `gr` names the divisions grammata may turn into a tab strip. It does so
    # only at >= 2 divisions AND >= 10 rows: measured here, 43 entries carry two
    # or more divisions and 24 of those clear the row threshold — ἔχω at 4
    # divisions and 63 rows, then εἴδω, ἵστημι, βάλλω, ἄγω, ἐπί. Exactly the
    # entries where scrolling to the middle voice is the problem tabs solve.
    # (ἄλλος has senses before its first banner and falls back to untabbed —
    # grammata's documented behaviour, harmless, and not a misfiring threshold.)
    gr = [[r["n"], r["z"]] for r in rows if r.get("b") and r["n"]]
    out = {"key": key, "head": headword,
           "i": definition[len(headword):head_end].strip(), "rows": rows}
    if len(gr) >= 2:
        out["gr"] = gr
    return out


def _head_forms(head: str) -> list[str]:
    """The head as written, plus the bare form a cross-reference would use."""
    forms = [head]
    bare = head.lstrip("\u2020").rstrip(".")
    bare = re.sub(r"-\d+$", "", bare)
    if bare and bare != head:
        forms.append(bare)
    return forms


def entry_html(rows: list[dict], resolve=None) -> str:
    """Render every row sharing a key (usually one; Cunliffe numbers homonyms
    only in the headword text — "ἄγη2" — not in a distinct key, unlike LSJ's
    a)1/a)2 convention) as its own sense block.

    `resolve` maps a "See <headword>" target to a shipped Cunliffe key, or to
    None where the pointer cannot be honoured."""
    def block(r: dict) -> str:
        inner = linkify_definition(r["definition"], r.get("citations", []))
        if resolve is not None:
            inner = _link_xrefs(inner, resolve)
        return f'<div class="cunliffe-sense">{inner}</div>'
    return "".join(block(r) for r in rows)


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

    # Headword -> key over EVERY source entry, so a pointer can be resolved
    # before deciding whether its target ships. Cunliffe's heads carry marks
    # that a "See" target does not repeat — a leading dagger, a "-1" homonym
    # suffix, a trailing period — so each head is indexed bare as well. First
    # writer wins, which keeps "-1" ahead of "-2" for a bare target.
    head_to_key: dict[str, str] = {}
    for key, rows in rows_by_key.items():
        for r in rows:
            for form in _head_forms(r["headword"]):
                head_to_key.setdefault(form, key)

    # A pointer is a promise that the entry exists. Honour it: an entry named
    # by a "See" in something we ship is itself worth shipping, even though no
    # lemma in the corpus reaches it. One level only — a pointer's pointer is
    # not something the reader asked for, and the closure has no natural end.
    pulled_in = 0
    for key in list(wanted):
        for r in rows_by_key[key]:
            for m in _SEE_RE.finditer(r["definition"]):
                target = head_to_key.get(m.group(1))
                if target and target not in wanted:
                    wanted.add(target)
                    pulled_in += 1

    def resolve(target: str) -> str | None:
        key = head_to_key.get(target)
        return key if key in wanted else None

    shards: dict[str, dict] = defaultdict(dict)
    # T8 records go in their OWN shards, not beside the html. The two carry the
    # same text, so folding them together would double what a reader downloads
    # on a Cunliffe tap for the benefit of whichever renderer is not in use.
    t8_shards: dict[str, dict] = defaultdict(dict)
    kept_lex = 0
    kept_hompers = 0
    for key in wanted:
        rows = rows_by_key[key]
        shards[shard_letter(key)][key] = {
            "key": key,
            "head": rows[0]["headword"],
            "html": entry_html(rows, resolve),
            "src": _merged_src(rows),
        }
        # One record per row sharing the key, matching entry_html's blocks.
        t8_shards[shard_letter(key)][key] = [
            to_t8(key, r["headword"], r["definition"]) for r in rows
        ]
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
    t8_dir = out_dir / "cunliffe-t8"
    t8_dir.mkdir(parents=True, exist_ok=True)
    for letter, entries in sorted(t8_shards.items()):
        (t8_dir / f"{letter}.json").write_text(
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
        "cunliffe_entries_pulled_in_by_xref": pulled_in,
        "cunliffe_t8_rows": sum(
            len(rec["rows"]) for recs in t8_shards.values()
            for group in recs.values() for rec in group
        ),
    }
    (out_dir / "cunliffe_summary.json").write_text(json.dumps(summary, indent=1))
    return shard_dir
