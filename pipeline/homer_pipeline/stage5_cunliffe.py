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


# In 94 places the scan has LOST THE SPACE in front of a work abbreviation:
# ἄγριος reads "wild creaturesIl. 5.52", αἶθοψ "bright, sparklingIl. 1.462",
# καθίζω "Pple. καθίσσαςIl. 9.488". Every regex here matches the abbreviation
# behind a `\b`, and after a letter — Latin or Greek — there is no word
# boundary before "I" or "O", so the reference is never seen. What the parse
# reads instead is two loose numbers, and _expand restores each of them to
# whatever book the PREVIOUS full reference established: ἄγριος's one
# "Il. 5.52" came out as a live "Il. 19.5" and a live "Il. 19.52", and αἶθοψ's
# "Il. 4.495" as "Od. 24.4" and "Od. 24.495" — in the wrong poem. The English
# in front of it went with them, into `g`, as though Homer had written "wild
# creatures".
#
# Measured over both source volumes (11,416 entries): 94 occurrences in 84
# entries, and every one of them is followed by a complete book.line
# reference. Nothing else of the class occurs — no glued abbreviation without
# a reference behind it (0), no reference with the next word glued to its END
# (0), no "Il 5.52" with the stop missing (0), no lowercase "il."/"od." (0).
# 3 of the 94 are glued to Greek rather than to English (καθίζω, κάνεον,
# Αἴας) and one to a homonym numeral (Ἀθήνη-1Od. 7.80).
#
# The space is restored HERE, where a definition enters the parse, rather than
# by loosening the `\b` in the three regexes that read the abbreviation. Not
# because those three are hard to loosen, but because they are not the only
# rules a glued word breaks: _quote_start, _evidence_start, _has_english,
# _EN_RUN_RE, _split_head_run and split_forms all measure the same string and
# all of them see "creaturesIl" as one word. Fixing the three that are easy to
# find would leave the rest reading a word the dictionary does not contain,
# and would leave the glue standing in front of the reader.
#
# Nothing is lost and nothing is emended: a space is INSERTED, and only where
# the very next thing is a full reference. This is not the mis-scanned "Of."
# below, which is a letter printed wrongly and is reproduced as printed — a
# word separator that the page had and the scan dropped is not text.
_GLUED_ABBR_RE = re.compile(r"(?<=\w)(?=(?:Il|Od)\.\s*\d+\.\d+)")


def unglue_refs(definition: str) -> str:
    """Restore the space the scan lost in front of a work abbreviation."""
    return _GLUED_ABBR_RE.sub(" ", definition)


# Two references the 1924 page does not state correctly, and the only two in
# the corpus that no rule can reach — every other wrong reference was a parsing
# fault, fixable by reading the text properly. These are faults IN the text.
#
# Correcting a printed source is a departure from this edition's default, which
# is to reproduce what Cunliffe set (the "Of." mis-scan in ἐπιτρέχω is kept
# verbatim for exactly that reason). It is done here, on John's ruling, only
# because both targets are established from our own Greek rather than inferred,
# and because the alternative is shipping a live link to the wrong line.
#
# Each correction records the evidence that fixes it. Replacement is literal
# and anchored to the entry, so neither can fire anywhere else.
_SOURCE_MISSCANS: dict[str, tuple[str, str]] = {
    # "Pple. οἰμώξας Il. 5.68, Il. 16.290, Il. 20.417, Od. Il.529, Il. 22.34"
    # — a scan of two abbreviations over one another, in an ordered run that
    # places it between books 20 and 22. Il. 21.529 reads "ὃ δ' οἰμώξας ἀπὸ
    # πύργου βαῖνε χαμᾶζε": the participle this entry is listing, in the book
    # the ordering requires. Od. 5.529 does not exist — Odyssey 5 ends at 493.
    "oi)mw/zw": ("Od. Il.529", "Il. 21.529"),
    # "κύων Ὠρίωνος, Sirius 22.29" — no abbreviation at all, so the digits
    # expand against the last reference (Od. 5.274) and point into Odyssey 5.
    # Il. 22.29 reads "ὅν τε κύν' Ὠρίωνος ἐπίκλησιν καλέουσι", which is the
    # phrase Cunliffe is glossing, in the Sirius simile of Il. 22.26-31.
    "w)ri/wn": ("Sirius 22.29", "Sirius Il. 22.29"),
}


def fix_source_misscan(key: str, definition: str) -> str:
    """Repair the two references the 1924 text itself states wrongly."""
    fix = _SOURCE_MISSCANS.get(key)
    if fix is None:
        return definition
    printed, corrected = fix
    return definition.replace(printed, corrected, 1)


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
    # A reference the scan glued to the word before it is not matchable behind
    # a `\b` — see unglue_refs. citations[] locates its refs by a sequential
    # find, and the space goes in FRONT of the ref, so no ref span moves.
    text = unglue_refs(text)
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
    # Not ";": the source carries a literal "&gt;" in at least one entry
    # (κεφαλή), and trimming the semicolon turned the entity into "&gt".
    return body[:start].strip().rstrip(" :,"), body[start:].strip()


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

# But Cunliffe also cross-references his OWN sense numbers, and those are digits
# standing exactly where a line number could stand: "As in 4.b" (ἄγω), "Sim. in
# 3 pl." (φημί), "in 3.b" (δεύτερος), "For βοὴν ἀ. see βοή 2" (ἀγαθός), "See
# also under ἵημι1 9" (ἐδητύς). Read as continuations they are restored to
# whatever book the previous reference established and become live links to real
# lines that have nothing to do with the entry — Od. 15.4 under ἄγω, Il. 3.349
# under δεύτερος. The digit itself says nothing; what tells the two apart is
# what Cunliffe writes AROUND it, and a line number carries none of these marks:
#
#   · a SUB-SENSE LETTER hanging off it — "4.a", "1.b.β", "ἦμαρ 4 (j)". The
#     letter is Latin and unspaced, so neither the Greek that follows a real
#     citation nor the spaced sub-sense opener "Il. 23.581. b With . . ." is
#     touched.
#   · PERSON AND NUMBER behind it — "3 pl.", "2 sing.", the same shape
#     split_senses already refuses a sense number for, decided by the same
#     _MORPH_RE.
#   · a DIVISION NUMERAL in front of it — "εἴδω III.12", "ὅς2 II.9.a".
#   · a HEADWORD in front of it, named as a cross-reference — "See γυνή 3",
#     "in sense 4". A bare "See 648" is NOT one of these: δέμνια's "Il. 24.644
#     two beds are referred to. See 648" has no headword between the cue and
#     the digit, and there Cunliffe is pointing at a line. So the cue alone
#     never decides it; the Greek word after the cue does.
#
# A marked digit is passed over exactly as a citation inside one of Cunliffe's
# parentheses is (see the depth walk in split_evidence): it stays in the lead
# text and reaches the row as what he wrote, because "As in 4.b" is him telling
# the reader where to look and deleting it would lose the reference altogether.
_SUBSENSE_MARK_RE = re.compile(r"\.[a-z](?![a-z])|\s*\([a-z]\)")
_DIVISION_MARK_RE = re.compile(r"\b[IVX]{1,4}\.$")
_XREF_CUE_RE = re.compile(r"\b(?:see|under|senses?)\b", re.I)


def _is_sense_ref(text: str, start: int, end: int, lead: str) -> bool:
    """Whether the bare digit at [start:end) is a sense number, not a line."""
    if _SUBSENSE_MARK_RE.match(text, end):
        return True
    if _MORPH_RE.match(text[end:].lstrip()) and text[end:end + 1].isspace():
        return True
    if _DIVISION_MARK_RE.search(text[:start]):
        return True
    cue = None
    for m in _XREF_CUE_RE.finditer(lead):
        cue = m
    if cue is None:
        return False
    after = lead[cue.end():]
    # "sense" names a sense outright; "see"/"under" only point at one when a
    # headword stands between the cue and the digit.
    return (cue.group(0).lower().startswith("sense")
            or bool(_GREEK_RE.search(after)))


def _holds_sense_ref(text: str) -> bool:
    """Whether `text` is Cunliffe pointing the reader at another sense.

    A quotation of Homer never does. This is the other half of _is_sense_ref:
    once the sense number stops being read as a citation there is nothing left
    to END the run, and a run with Greek in it and no citation is taken for a
    quotation. ἧος's "Correlative with τόφρα. See τόφρα 3." reaches the tail of
    the evidence exactly so, and ἀμφί's "see βαίνω I.6.a, and cf. ἀμφιβαίνω 4."
    reaches a lead. Both are his own prose and read as Homer's without this.
    27 runs, across 27 entries.

    A cross-reference INSIDE one of his parentheses proves nothing, exactly as
    English inside one does not (see _has_english): δίκη's "οὐ δίκας εἰδότα
    οὐδὲ θέμιστας (having no regard for justice . . .; see εἴδω III.12)" is a
    quotation of Homer carrying a remark, and reading the remark as the run's
    own character puts Homer's words in the definition.
    """
    depth = _paren_depth(text)
    for m in re.finditer(r"\b\d+\b", text):
        if depth[m.start()]:
            continue
        cue = None
        for c in _XREF_CUE_RE.finditer(text[:m.start()]):
            cue = c
        if cue is None:
            continue
        after = text[cue.end():m.start()]
        # A full reference between the cue and the digit means the digit
        # belongs to that reference's list, not to the cross-reference.
        if _FULL_CITE_RE.search(after):
            continue
        if cue.group(0).lower().startswith("sense") or _GREEK_RE.search(after):
            return True
    return False


# Connectors between pieces of evidence. These carry no information a T8 row
# keeps — it joins citations with its own separator — so they are dropped, and
# the audit below asserts that NOTHING ELSE is.
# Only genuinely empty joining words are dropped. "etc." is NOT one: in a
# lexicon it tells the reader the citation list is not exhaustive, and treating
# it as furniture cost 1,336 entries that signal. Dashes and "So" likewise carry
# Cunliffe's own sequencing and stay in the text.
_CONNECTOR_RE = re.compile(r"^[\s,.:;=]*(?:Cf\.|cf\.|and|=)?[\s,.:;=]*")
_PAREN_RE = re.compile(r"\(([^)]*)\)\s*$")
# Two or more English words running together. One is not enough to go on: a
# lone "Absol." or "sc." is apparatus Cunliffe prints inside a quotation, and
# a Greek quotation never carries a phrase.
_EN_RUN_RE = re.compile(r"[A-Za-z]{2,}(?:[.,;:]?\s+[A-Za-z]{2,})+")
# A note at the FRONT of some prose belongs to the citation list before it, not
# to the definition it precedes: "etc. Absol. with the article" opened a sense
# reading "etc. Absol. …" (John, on seeing it). Peeled off and handed back.
_LEADING_NOTE_RE = re.compile(r"^(?:[\s.:,;–-]*(?:etc\.?|So|and so on))+[\s.:,;–-]*")


# Cunliffe's own "and so on" marks. Kept in the text, never given a row.
# Notes come in runs — "etc. So", "– etc.:", a bare "– –". Matching only one
# at a time left the rest to open a row of its own (John, on seeing "etc. So"
# standing above examples that belong to the sense before it).
_TRAILING_NOTE_RE = re.compile(r"(?:[\s.:,;–-]*(?:etc\.?|So|and so on))*[\s.:,;–-]*")

# A bare reference pointer: Cunliffe's own citation IS the grammatical object
# ("Except in Il. 22.218", "– Other combinations in Il. 1.417, …", "Prob.
# also in Od. 14.363") — the phrase names no sense of its own, and reads as
# though Cunliffe defined the word as "Other combinations in" when it is
# given a row (John, on seeing it). Measured over both source volumes
# (11,416 entries, 29,441 T8 rows): exactly these three shapes survive to a
# row with none of Homer's own Greek and no other content — everything else
# that LOOKS like this ("As in 4.a", "Sim. in 3 pl. impf.") is not a
# reference at all but a sense cross-reference number mistaken for a
# citation, a separate and unfixed defect (see stage5_cunliffe test notes);
# folding those in too would have hidden that bug rather than fixed this
# one, so the pattern names exactly what was verified and nothing wider.
_REF_NOTE_RE = re.compile(r"^[\s–-]*(?:Except|Prob\.\s*also|Other\s+\w+)\s+in$", re.I)

# The one mis-scanned connector in the whole dictionary. Cunliffe printed
# "Cf."; the scan reads "Of.", exactly ONCE in 11,416 entries — ἐπιτρέχω sense
# 2, "ἐπέδραμεν ὅς ῥʼ ἔβαλεν Il. 4.524. Of. Il. 5.617, Il. 10.354, …" — and no
# other confusion of the class occurs anywhere (0 for "Gf.", "O f.", a bare
# "Cf" with no stop; "Of" without a stop is his own word and is left entirely
# alone). Given a row of its own it reads as a third sense between two real
# ones, "Of dogs" and "Of a spear", whose whole definition is "Of."
#
# It is NOT dropped, and the text is NOT corrected: this edition reproduces
# what was printed, and the module's corpus audit refuses a parse that loses a
# character (it caught the first attempt at this, which classed "Of." as a
# connector and swallowed the O). It joins the citation list it introduces,
# verbatim, exactly as "etc." and a bare reference pointer do.
_MISSCAN_CF_RE = re.compile(r"^Of\.$")


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


_WORK_ABBR_RE = re.compile(r"^(Il|Od)\.\s*(\d+)\.(\d+)$")


def _expand(cite: str, book: str | None) -> tuple[str, str | None]:
    """A citation, and the book context it leaves behind.

    Cunliffe drops the book when the previous reference established it —
    "Il. 1.83, 496, 533" means Il. 1.83, Il. 1.496, Il. 1.533. That reads
    correctly in running prose and not at all once the references are a
    separated list, where "496 · 533" has nothing to attach to. So a bare
    continuation is restored to the book it belongs to, which also makes it
    linkable; a full reference resets the context, including across the ":"
    that separates one poem from the other.
    """
    m = _WORK_ABBR_RE.match(cite.strip())
    if m:
        return cite, f"{m.group(1)}. {m.group(2)}"
    if book and cite.strip().isdigit():
        return f"{book}.{cite.strip()}", book
    return cite, book


def _split_gloss(body: str) -> tuple[str, str]:
    """A quotation and the English translation Cunliffe parenthesises after it.

    Told apart from a quotation that simply ends inside brackets by having no
    Greek in it.
    """
    pm = _PAREN_RE.search(body)
    if pm and not _GREEK_RE.search(pm.group(1)):
        return body[:pm.start()].strip(), pm.group(1).strip()
    return body, ""


def _has_english(text: str) -> bool:
    """Whether Cunliffe is writing his OWN prose here, outside a parenthesis.

    English inside a parenthesis is the translation he hangs on the quotation
    before it, so it proves nothing about where his prose resumes: δίκη's "οὐ
    δίκας εἰδότα οὐδὲ θέμιστας (having no regard for justice . . .; see εἴδω
    III.12)" moved the quotation itself into the definition on the strength of
    the translation inside its own brackets. Counting only what is outside
    them keeps 30 such quotations where they belong, at the cost of 13 runs
    whose only English is parenthesised staying in `g` — a remark beside
    Homer's words rather than a definition standing in for them.
    """
    depth = 0
    out = []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif not depth:
            out.append(ch)
    return bool(_EN_RUN_RE.search("".join(out)))


def _quote_start(body: str) -> int:
    """Where Homer's own words begin in one lead of an evidence run.

    Cunliffe's English does not stop at the first Greek word. ἄατος reads
    "Except in Il. 22.218 in contr. form ἆτος. Insatiate of, indefatigable in.
    With genit.: πολέμοιο Il. 5.388" — a form, then the gloss, then the
    quotation — and cutting at the FIRST Greek left the whole gloss inside
    `g`, so the entry defined the word as "in contr. form" and rendered
    "Insatiate of, indefatigable in" as though Homer had written it. That is
    the one thing a reader came to ἄατος for.

    So the boundary walks FORWARD over the same sentence stops
    _evidence_start walks back over, and moves across one only when there is
    ENGLISH PROSE behind it. The ellipsis inside a quotation carries none and
    moves nothing (μή: "ἴδοι τις μὴ . . . ὦσιν" stays whole), and a stop with
    no Greek left after it ends the walk, because that would leave the
    citation with no quotation at all. 208 quotations held English this way,
    across 182 entries.
    """
    gm = _GREEK_RE.search(body)
    if not gm:
        return 0
    start = gm.start()
    for m in re.finditer(r"[:.;]\s", body):
        if m.end() <= start:
            continue
        if m.group(0)[0] == "." and _ABBREV_TAIL_RE.search(body[:m.start()]):
            continue
        if not _GREEK_RE.search(body[m.end():]):
            break
        gap = body[start:m.start()]
        if _has_english(gap):
            start = m.end()
        elif start > gm.start() and not gap.strip(" .:;,"):
            # Cunliffe's own ellipsis, still inside the prose the walk is
            # already crossing: "the rest of the . . . : λαόν" (ἄλλος) put
            # ". . : λαόν" in `g` when each stop had to earn its own English.
            # Only once the walk has started, so that an ellipsis INSIDE a
            # quotation cannot open one. 8 quotations, 8 entries.
            start = m.end()
    return start


def _unbalanced(text: str) -> bool:
    """Whether a bracket or parenthesis opens or closes outside `text`.

    A quotation is a phrase Homer wrote: whatever it opens it closes. An
    unmatched delimiter means the run is half of something larger — but it
    cuts BOTH kinds of run, so on its own it says nothing about which half
    this is. Read together with an English phrase it does: the tail of an
    etymology ("τρέμω.] Without motion, still", ἀτρέμας), of the compound list
    he heads a verb with ("ἀνα-) Of armour, to rattle, clash, ring", βράχω),
    of an epithet list (Πάτροκλος). Without one it is Homer, mid-parenthesis —
    τεκμαίρομαι's "Κρονίδης] τεκμαίρεται ἀμφοτέροισιν", ἐπισσείω's "αἰγίδι)
    ἐπισσείων φοβέειν Ἀχαιούς" — and the first draft of this rule moved 19
    such quotations into the definition, which is the very fault it was
    written to cure.

    What breaks a run in half is no longer what it was. This rule was written
    when a citation INSIDE one of Cunliffe's parentheses ended the lead and
    left the parenthesis hanging open; split_evidence now walks past such a
    citation (see `depth` there), so that shape reaches here whole and this
    test no longer sees it. Two shapes still arrive unmatched, and they are
    what the rule now stands on:

      · A SQUARE BRACKET. The depth walk counts parentheses only, so the
        etymology bracket is untouched by it — ἀτρέμας's "τρέμω.] Without
        motion, still", πολεμιστής's "πολεμίζω.] A fighter, warrior".
      · A PARENTHESIS OPENED BEFORE THE EVIDENCE RUN BEGAN. parse_sense cuts
        the sense at its first citation, so an opener standing in the
        definition — ὀκτωκαιδέκατος's "ὀκτωκαιδεκάτῃ (sc. ἡμέρῃ), on the
        eighteenth day" — never enters the string split_evidence measures
        depth over, and the ")" that ends the remark is all that is left of
        it. The depth map cannot see it; the stray close can.

    Measured, not assumed: with _paren_holds_cite carrying the first shape,
    disabling this test alone changes 9 entries and puts 9 more of Cunliffe's
    remarks back into `g` — 2 by bracket (ἀτρέμας, πολεμιστής), 7 by orphaned
    parenthesis (ἀγορή, ἀμφίπολος, αὐλός, λέβης, νεύω, ὀκτωκαιδέκατος,
    ὀρσοθύρη). The two guards are independent; neither subsumes the other.

    Balance, not presence: _evidence_start refuses a run holding a bracket at
    all, but Cunliffe also supplies an implied word inside a genuine quotation
    — ἔνδον's "Διὸς [δώματος] ἐ." — and those close what they open.
    """
    depth = {"(": 0, "[": 0}
    opener = {")": "(", "]": "["}
    for ch in text:
        if ch in depth:
            depth[ch] += 1
        elif ch in opener:
            if not depth[opener[ch]]:
                return True
            depth[opener[ch]] -= 1
    return any(depth.values())

# One of Cunliffe's parentheses, innermost first so a nested pair is still seen.
_INNER_PAREN_RE = re.compile(r"\(([^()]*)\)")


def _paren_holds_cite(text: str) -> bool:
    """Whether a parenthesis in `text` carries a citation of its own.

    _unbalanced was doing this job by accident. A run reading "ἵπποι in sense
    chariot (see ἵππος 3)" (ἀερσίπους) used to reach it with the parenthesis
    cut open at the 3, and the open delimiter plus the English was what told
    it this was Cunliffe's prose and not a quotation. Once the parenthesis is
    kept whole the run balances, and 19 entries put his remark in `g` as
    though Homer had written it. The signal is the same one, said directly.
    Measured by disabling this test alone: 19 entries change, and every one
    of them is a remark of Cunliffe's moving out of Homer's mouth.
    """
    return any(_CITE_TOKEN_RE.search(m.group(1))
               for m in _INNER_PAREN_RE.finditer(text))


def _paren_depth(text: str) -> list[int]:
    """Parenthesis nesting depth BEFORE each character, plus one past the end.

    A closing parenthesis with nothing open is clamped rather than going
    negative: a run handed to split_evidence can begin inside one of
    Cunliffe's parentheses, and the ")" that ends it is then all that is
    left of it.
    """
    out: list[int] = []
    d = 0
    for ch in text:
        out.append(d)
        if ch == "(":
            d += 1
        elif ch == ")":
            d = max(0, d - 1)
    out.append(d)
    return out


def _depth_at(text: str, base: int, idx: int) -> int:
    """Parenthesis depth at `idx` in `text`, given the depth it opens at."""
    d = base
    for ch in text[:idx]:
        if ch == "(":
            d += 1
        elif ch == ")":
            d = max(0, d - 1)
    return d


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
    book: str | None = None
    depth = _paren_depth(evidence)
    for m in _CITE_TOKEN_RE.finditer(evidence):
        # A citation inside one of Cunliffe's parentheses is part of the remark
        # he is making, not a piece of evidence standing on its own — see the
        # note above _paren_depth's callers.
        if depth[m.start()]:
            continue
        # One of Cunliffe's own sense numbers, not a line number — see
        # _is_sense_ref. Passed over so that it stays where he printed it.
        if (m.group(0).strip().isdigit()
                and _is_sense_ref(evidence, m.start(), m.end(),
                                  evidence[pos:m.start()])):
            continue
        lead = evidence[pos:m.start()]
        lead_depth = depth[pos]
        pos = m.end()
        cite, book = _expand(m.group(0), book)
        body = _CONNECTOR_RE.sub("", lead).strip()
        # English ahead of the quotation is Cunliffe's own prose, not part of
        # what it is quoting: "Together, at the same moment: ἁ. ἄμφω σύν ῥʼ
        # ἔπεσον" is a remark and then a quotation. Split at the quotation, or
        # the remark ends up inside `g` and reads as though Homer wrote it.
        q = _quote_start(body)
        # A run that leaves a delimiter open AND carries an English phrase is
        # not a quotation at all, so the whole lead is Cunliffe's own — see
        # _unbalanced. _has_english is what keeps a quotation's own
        # translation from counting here: κατά's "[ξυστὰ] κατὰ στόμα εἱμένα
        # χαλκῷ (at the point)", a quotation whose supplement the preceding
        # citation had split off, reads as prose without it.
        core = body[q:]
        if (_GREEK_RE.search(core) and _has_english(core)
                and (_unbalanced(core) or _paren_holds_cite(core))):
            q = len(body)
        # A cross-reference to another sense is his prose too — see
        # _holds_sense_ref.
        elif _holds_sense_ref(core):
            q = len(body)
        # Greek inside a parenthesis is a word Cunliffe is naming in his own
        # remark, not a phrase of Homer's he is quoting — ἁμός's "Our
        # ( = ἡμέτερος)" put ἡμέτερος in `g` and left "Our ( =" standing as a
        # definition. The whole lead is then his prose.
        elif _depth_at(body, lead_depth, q):
            q = len(body)
        if q > 0:
            prose = _CONNECTOR_RE.sub("", body[:q]).strip().rstrip(" :;,")
            if prose:
                # A note here qualifies the row above and must not open a new
                # one — otherwise the quotation that follows lands on a row
                # whose whole definition reads "etc.". That was 839 rows.
                if _TRAILING_NOTE_RE.fullmatch(prose):
                    _append_note(segments[-1], prose)
                else:
                    lead = _LEADING_NOTE_RE.match(prose)
                    if lead and lead.group(0).strip(" .:,;–-"):
                        _append_note(segments[-1], lead.group(0).strip())
                        prose = prose[lead.end():]
                    segments.append({"z": prose, "ex": [], "au": []})
            body = body[q:].strip()
        if _GREEK_RE.search(body):
            body, gloss = _split_gloss(body)
            item = {"g": body, "c": cite}
            if gloss:
                item["e"] = gloss
            segments[-1]["ex"].append(item)
        elif body:
            if _TRAILING_NOTE_RE.fullmatch(body):
                _append_note(segments[-1], body)
                segments[-1]["au"].append(cite)
            elif _MISSCAN_CF_RE.fullmatch(body):
                # A mis-scanned "Cf." — see _MISSCAN_CF_RE. Kept as printed,
                # joining the list it introduces rather than opening a sense.
                _append_note(segments[-1], body)
                segments[-1]["au"].append(cite)
            elif _REF_NOTE_RE.fullmatch(body):
                # A bare pointer to this citation, not a new statement — see
                # _REF_NOTE_RE. It joins the list above exactly as "etc." does
                # (kept verbatim, dash and all — nothing is ever dropped here).
                _append_note(segments[-1], body)
                segments[-1]["au"].append(cite)
            else:
                # prose with no Greek: a new statement, and the citations that
                # follow belong to it — but any note in FRONT of it closes the
                # list above rather than opening this one.
                lead = _LEADING_NOTE_RE.match(body)
                if lead and lead.group(0).strip(" .:,;–-"):
                    _append_note(segments[-1], lead.group(0).strip())
                    body = body[lead.end():]
                segments.append({"z": body, "ex": [], "au": [cite]})
        else:
            segments[-1]["au"].append(cite)
    tail = _CONNECTOR_RE.sub("", evidence[pos:]).strip()
    if tail:
        gm = _GREEK_RE.search(tail)
        # The run that closes an evidence list has no citation of its own to
        # test it against, so the parenthesis is the only signal there is that
        # it is Cunliffe talking: ἁμός ends on a whole paragraph of his own
        # ("But the sense my (cf. ἡμέτερος 2) is always admissible …") and
        # that Greek made the paragraph a quotation of Homer.
        if (gm and not _depth_at(tail, depth[pos], gm.start())
                and not _holds_sense_ref(tail)):
            segments[-1]["ex"].append({"g": tail})
        elif _TRAILING_NOTE_RE.fullmatch(tail):
            _append_note(segments[-1], tail)
        else:
            segments.append({"z": tail, "ex": [], "au": []})
    return segments


_SUBSENSE_RE = re.compile(r"^([a-z])\s+(?=[A-ZΑ-Ωa-zἀ-῿(])")
# The same letter where it trails a definition rather than leading one.
_SUBSENSE_TAIL_RE = re.compile(r"\s([a-z])$")


def _lift_subsense(rows: list[dict]) -> None:
    """Cunliffe divides a sense with letters — "1 His a ἑός … – b ὅς …".

    Left in the text those read as part of the definition ("His a"), which is
    what John saw. T8 already knows what to do with them: a row whose number is
    a single letter renders as a sub-row.
    """
    out: list[dict] = []
    for r in rows:
        if r.get("b") or not r.get("z"):
            out.append(r)
            continue
        # the letter LEADS: "b ὅς …" — the row is that sub-sense
        m = _SUBSENSE_RE.match(r["z"])
        if m and not r.get("n"):
            r["n"] = m.group(1)
            r["lv"] = 2
            r["z"] = r["z"][m.end():]
            out.append(r)
            continue
        # the letter TRAILS the definition: "1 His a ἑός Il. 1.83 …". The
        # definition belongs to the sense, and the letter opens a sub-sense
        # that owns the evidence after it. Split rather than leave "His a".
        t = _SUBSENSE_TAIL_RE.search(r["z"])
        if t and (r.get("ex") or r.get("au")):
            parent = {k: v for k, v in r.items() if k not in ("ex", "au")}
            parent["z"] = r["z"][:t.start()].strip()
            child = {"lv": 2, "n": t.group(1), "z": ""}
            if r.get("ex"):
                child["ex"] = r["ex"]
            if r.get("au"):
                child["au"] = r["au"]
            out.append(parent)
            out.append(child)
            continue
        out.append(r)
    rows[:] = out


def _move_leading_notes(rows: list[dict]) -> None:
    """A row whose definition OPENS with a note is closing the row before it.

    split_evidence catches these inside an evidence run, but a numbered sense
    can begin with one too — "2 etc. Absol. with the article" — and there the
    previous row is only in view once the whole entry is built.
    """
    for i, r in enumerate(rows):
        if r.get("b") or not r.get("z"):
            continue
        m = _LEADING_NOTE_RE.match(r["z"])
        if not m or not m.group(0).strip(" .:,;–-"):
            continue
        prev = next((p for p in reversed(rows[:i]) if not p.get("b")), None)
        if prev is None:
            continue
        prev.setdefault("au", []).append(m.group(0).strip())
        r["z"] = r["z"][m.end():]


def _fold_leading_ref_note(rows: list[dict]) -> None:
    """A row whose ENTIRE definition is a bare reference pointer ("Except in
    Il. 22.218") is not a sense of its own — see _REF_NOTE_RE. It is
    _move_leading_notes' mirror image: there, a note trails into the row
    AFTER it; here, the whole row IS the note, because parse_sense drew the
    sense/evidence boundary at the citation itself — nothing came before it
    to draw the boundary from (ἄατος: "Except in Il. 22.218 in contr. form
    ἆτος. Insatiate of, indefatigable in. …" reads the exception as the
    definition and the real gloss as evidence). The real definition is in
    the row that follows in the same evidence run, so the note and its
    citation move onto the FRONT of that row, in order, and the row's own
    sense number (if it had one) moves with them rather than being dropped.
    Never merges across a division banner or into the start of a different
    numbered sense — only into a continuation (unnumbered) row of its own
    run, which is the only case where "the next row" is guaranteed to still
    be the same sense.
    """
    out: list[dict] = []
    i, n = 0, len(rows)
    while i < n:
        r = rows[i]
        z = (r.get("z") or "").strip()
        nxt = rows[i + 1] if i + 1 < n else None
        if (not r.get("b") and not r.get("ex") and z
                and _REF_NOTE_RE.fullmatch(z)
                and nxt is not None and not nxt.get("b") and not nxt.get("n")):
            nxt["au"] = [z] + (r.get("au") or []) + (nxt.get("au") or [])
            if r.get("n"):
                nxt["n"] = r["n"]
            i += 1
            continue
        out.append(r)
        i += 1
    rows[:] = out


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


def _markup(text: str, resolve) -> str:
    """A T8 text field, escaped and carrying the links the HTML shard carries.

    grammata runs `z`, `i` and an example's `g` through wrapGreekInHtml rather
    than escapeHtml, so these fields ARE html and anchors survive in them. That
    is the whole reason the T8 records can keep the cross-references: 316 of
    them fall in `z`, 79 in `i`, 61 inside a quotation, and rendering from
    records without this step would have dropped every one — along with the 13
    citations that land in a definition rather than in the evidence.

    Citations in `au` and in an example's `c` are NOT touched: those are bare
    tokens, and grammata's own `citation` hook turns them into links at render
    time using the host's URL scheme.
    """
    out = _link_plain_refs(escape(text))
    return _link_xrefs(out, resolve) if resolve is not None else out


# Cunliffe's own labels for a principal part, learned from the head runs of the
# entries whose boundary the sense-split hands over for free: Infin. 393,
# Pple. 300, Imp. 134, Aor. 107, Fem. 73, Fut. 72, Subj. 64, Opt. 56 … and the
# digit-then-lowercase shape it writes person and number in ("3 sing. pres.").
_FORM_LABEL_RE = re.compile(
    r"(?:\d\s+(?:sing|pl|dual)\.(?:\s+[a-z]{2,8}\.)*"
    r"|(?:Infin|Pple|Imp|Aor|Fem|Fut|Subj|Opt|Pl|Acc|Dat|Genit|Nom|Masc|Neut"
    r"|Sing|Dual|Voc|Perf|Plup|Pres|Impf|Mid|Pass|Act|Contr|Instrumental|Locative)"
    r"\b[a-z. ]*\.)\s+(?=[\u0370-\u03ff\u1f00-\u1fff])"
)


def split_forms(head_run: str) -> tuple[str, list[list[str]], list[str]]:
    """(what stays in `i`, the forms block, entry-level citations).

    Cunliffe puts its principal parts in the head run, chained and only
    half-labelled — "Aor. ἤγειρα Il. 17.222: Od. 2.41. ἄγειρα Od. 14.285.
    3 sing. ἤγειρε Od. 2.28." T8 renders these as `f`, a list of
    [label, form] pairs, which is what the forms bar above the senses is for.

    What precedes the first label — endings, gender, a quantity mark, the
    etymology — is not a form and stays in `i`.
    """
    first = _FORM_LABEL_RE.search(head_run)
    if not first:
        return head_run, [], []
    keep = head_run[:first.start()].strip()
    rest = head_run[first.start():]

    forms: list[list[str]] = []
    au: list[str] = []
    label = ""
    pos = 0
    pending: list[str] = []      # label words with no form of their own yet
    for m in _FORM_LABEL_RE.finditer(rest):
        if m.start() > pos:
            left = _consume_form(rest[pos:m.start()], label, forms, au)
            if left:
                pending.append(left)
        label = " ".join(pending + [m.group(0).strip()])
        pending = []
        pos = m.end()
    left = _consume_form(rest[pos:], label, forms, au)
    if left:
        # nothing followed it: keep it as a labelled row of its own rather than
        # dropping it. 204 entries lost words like "Mid." and "Pass." this way.
        forms.append([left, ""])
    return keep, forms, au


def _consume_form(chunk: str, label: str, forms: list, au: list) -> str:
    """One label's worth of head run: its form(s) and their citations.

    A label can cover SEVERAL forms, and Cunliffe writes the later ones bare:
    "Aor. ἤγειρα Il. 17.222: Od. 2.41. ἄγειρα Od. 14.285." — ἄγειρα sits
    between two citations under the same "Aor." Taking only the text before the
    first citation and after the last one dropped it.
    """
    pos = 0
    first = True
    for c in _CITE_TOKEN_RE.finditer(chunk):
        piece = chunk[pos:c.start()].strip(" .,;:")
        if piece and _GREEK_RE.search(piece):
            forms.append([label if first else "", piece])
            first = False
        elif piece:
            # "etc." between two citations, as everywhere else in this parse:
            # it qualifies the list and joins it rather than being dropped.
            au.append(piece)
        au.append(c.group(0))
        pos = c.end()
    tail = chunk[pos:].strip(" .,;:")
    if tail and _GREEK_RE.search(tail):
        forms.append([label if first else "", tail])
    elif tail:
        # No Greek: this is a label waiting for its form ("Mid." before
        # "Aor. ἀ̄ᾰσάμην"), so hand it back to prefix the next one.
        return tail
    return ""


def to_t8(key: str, headword: str, definition: str, resolve=None) -> dict:
    """A Cunliffe entry as a T8 record: head, the undecomposed head run, and
    rows. Division banners are lv 0 and carry the numeral plus the division's
    own heading; senses are lv 1.

    `s` is never set. grammata renders a continuation dash on rows that carry
    `s` AND an empty numeral, and three quarters of this dictionary is a single
    unnumbered row — every one of which would sprout a dash it should not have.
    """
    # Before anything measures this string: the scan lost the space in front
    # of 94 work abbreviations, and every rule below reads the result as one
    # word — see unglue_refs.
    definition = fix_source_misscan(key, unglue_refs(definition))
    p = split_senses(definition)
    roman = {d["at"]: d["n"] for d in p["divisions"]}
    if not p["senses"]:
        head_run, rest = _split_head_run(definition[len(headword):])
        z, evidence = parse_sense(rest)
        rows = _rows_from({"lv": 1, "n": "", "z": z}, evidence)
        _lift_subsense(rows)
        _move_leading_notes(rows)
        _fold_leading_ref_note(rows)
        for r in rows:
            if r.get("z"):
                r["z"] = _markup(r["z"], resolve)
            for item in r.get("ex") or []:
                if item.get("g"):
                    item["g"] = _markup(item["g"], resolve)
                if item.get("e"):
                    item["e"] = escape(item["e"])
        keep, forms, form_cites = split_forms(head_run)
        out: dict = {"key": key, "head": headword,
                     "i": _markup(keep, resolve), "rows": rows}
        # `f` and entry-level `au` are escaped by grammata itself (unlike i and
        # z, which it treats as html), so they stay raw.
        if forms:
            out["f"] = forms
        if form_cites:
            out["au"] = form_cites
        return out

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

    _lift_subsense(rows)
    _move_leading_notes(rows)
    _fold_leading_ref_note(rows)

    # `gr` names the divisions grammata may turn into a tab strip. It does so
    # only at >= 2 divisions AND >= 10 rows: measured here, 43 entries carry two
    # or more divisions and 24 of those clear the row threshold — ἔχω at 4
    # divisions and 63 rows, then εἴδω, ἵστημι, βάλλω, ἄγω, ἐπί. Exactly the
    # entries where scrolling to the middle voice is the problem tabs solve.
    # (ἄλλος has senses before its first banner and falls back to untabbed —
    # grammata's documented behaviour, harmless, and not a misfiring threshold.)
    for r in rows:
        if r.get("z"):
            r["z"] = _markup(r["z"], resolve)
        for item in r.get("ex") or []:
            if item.get("g"):
                item["g"] = _markup(item["g"], resolve)
            if item.get("e"):
                item["e"] = escape(item["e"])

    gr = [[r["n"], r["z"]] for r in rows if r.get("b") and r["n"]]
    keep, forms, form_cites = split_forms(
        definition[len(headword):head_end].strip())
    out = {"key": key, "head": headword, "i": _markup(keep, resolve),
           "rows": rows}
    if forms:
        out["f"] = forms
    if form_cites:
        out["au"] = form_cites
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
            to_t8(key, r["headword"], r["definition"], resolve) for r in rows
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
