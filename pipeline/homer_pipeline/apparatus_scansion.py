"""Computed hexameter scansion stage: per-line dactyl/spondee analysis of the
corpus's own Greek text, with honest confidence flags. Clean-room
implementation -- no vendored scansion library; general Greek-prosody rules
only (see module functions below for the specific rules applied).

Emits build/dist/<work>/scansion-<NN>.json, one per book (a whole-work single
file ran ~1.5MB for the Iliad -- too heavy for a reader toggle's lazy fetch,
so the emit is split the same way book-<NN>.json already is):
    {"work": <id>, "book": <int>, "lines": {"<book>.<line>": {
        "feet": <6-char string, chars 1-5 in {D,S}, char 6 in {S,X}>,
        "confidence": "high" | "ambiguous",
        "notes": [<flag>, ...]
    }}}

Method (summary; see the constraint solver docstrings for the mechanics)
--------------------------------------------------------------------------
1. Syllabify each line's Greek text into an ordered stream of vowel nuclei
   (diphthongs merged; diaeresis explicitly blocks a diphthong reading, per
   the source text's own diacritics) separated by intervening consonants
   counted across word boundaries (Greek verse is phonologically continuous
   within a line -- synapheia -- so "long by position" counts consonants
   regardless of which word they belong to).
2. Each nucleus gets a weight: long by nature (eta, omega, diphthongs, an
   iota-subscript nucleus), short by nature (epsilon, omicron), long by
   position (2+ intervening consonants before the next nucleus, doubled
   consonants zeta/xi/psi counting as 2), or -- for a bare alpha/iota/upsilon
   not closed by position -- genuinely ambiguous ("dichronon"): the algorithm
   does not know or guess the lexical vowel quantity, and tries both.
3. A hexameter line is 6 feet: feet 1-5 each a dactyl (long-short-short) or
   spondee (long-long); foot 6 is long + anceps (a always-long-counted final
   syllable, occasionally a naturally short syllable admitted at the verse
   end -- "brevis in longo"). Given N total nuclei, the number of dactyls
   among feet 1-5 is fixed by arithmetic (k = N - 12), so the solver only
   needs to enumerate WHICH of the 5 feet are dactyls (C(5,k) arrangements)
   and check each fixed-weight nucleus against the arrangement's required
   pattern; ambiguous (dichronon) nuclei are compatible with any requirement,
   since their true weight is unknown, not fixed.
4. If no arrangement is compatible outright, the solver tries increasingly
   many simultaneous "relaxations" -- philological escape hatches a line may
   genuinely need: synizesis (two adjacent vowel nuclei, in one word or
   across a word boundary, pronounced as one long syllable), correption (a
   long vowel/diphthong shortened before a following word-initial vowel),
   an assumed initial digamma (historical /w/, lost from the spelling, that
   closes the preceding syllable -- offered only for a small, named list of
   well-attested digamma words), and muta-cum-liquida lightening (a
   stop+liquid/nasal cluster optionally not closing the preceding syllable,
   poet's licence). The solver prefers the fewest simultaneous relaxations;
   ties or exhaustion are reported honestly (confidence "ambiguous", a
   best-effort scan, note "unresolved") rather than invented.

Determinism: no hash-seed-dependent iteration order is used to produce
output (see the stage's determinism test); all iteration is over lists/
tuples in stable, explicit order.
"""

from __future__ import annotations

import json
import unicodedata
from itertools import combinations
from pathlib import Path

from .config import BUILD_DIR, Manifest

VOWEL_BASES = set("αεηιουω")
LONG_BY_NATURE_BASES = set("ηω")
SHORT_BY_NATURE_BASES = set("εο")
DICHRONA_BASES = set("αιυ")
DIPHTHONGS = {"αι", "ει", "οι", "υι", "αυ", "ευ", "ηυ", "ου", "ωυ"}
DOUBLE_CONSONANT_BASES = set("ζξψ")
STOP_BASES = set("βγδκπτθφχ")
LIQUID_NASAL_BASES = set("λρμν")
CONSONANT_BASES = set("βγδζθκλμνξπρσςτφχψ")
GREEK_LETTER_BASES = VOWEL_BASES | CONSONANT_BASES

DIAERESIS_MARK = "̈"          # COMBINING DIAERESIS
YPOGEGRAMMENI_MARK = "ͅ"      # COMBINING GREEK YPOGEGRAMMENI (iota subscript)

MAX_RELAXATION_LEVEL = 4

# Well-attested Homeric digamma-initial words (historical initial /w/, lost
# from the Ionic spelling used by our TLG/Perseus source text). Non-
# exhaustive by design: this is not a lexicon of every digamma word in
# Homer, only common items whose digamma is uncontroversial in the standard
# handbooks (Monro, Chantraine), used solely as a last-resort relaxation
# offered to the solver -- never silently assumed, always flagged
# "digamma-assumed" in the line's notes when actually invoked. Matched
# against the accent/breathing-stripped lowercase surface form.
DIGAMMA_WORDS = {
    "αναξ", "ανακτος", "ανακτι", "ανακτα", "ανακτες", "ανακτων", "ανακτεσσι",
    "εργον", "εργα", "εργων", "εργοισι", "εργοιο",
    "οικος", "οικον", "οικοι", "οικαδε", "οικῳ",
    "οινος", "οινον", "οινοιο", "οινῳ",
    "ειπον", "ειποι", "ειπε", "ειπες", "ειπειν", "επος", "επεα", "επεσσι", "επεσσιν",
    "ειδον", "ιδειν", "ιδε", "ιδοι", "οιδα", "ιδμεν", "ιδμεναι",
    "εκαστος", "εκαστη", "εκαστον",
    "ε", "οι", "εο", "εθεν", "οφρα",
    "εικοσι", "εικων", "εικελος",
    "ηδυς", "ηδεια",
    "αστυ", "αστεος",
}


def _strip_accents_lower(word: str) -> str:
    nfd = unicodedata.normalize("NFD", word)
    stripped = "".join(ch for ch in nfd if not unicodedata.combining(ch))
    return stripped.lower()


def _letter_units(word: str) -> list[dict]:
    """[{'base': lowercase letter, 'vowel': bool, 'diaeresis': bool,
    'subscript': bool}, ...] for a word's real Greek letters, skipping the
    elision apostrophe and any other non-Greek punctuation embedded in the
    token.

    Deliberately checks membership in GREEK_LETTER_BASES rather than
    Python's str.isalpha(): the elision mark in this corpus is sometimes the
    ASCII apostrophe (U+0027, not alphabetic) and sometimes U+02BC MODIFIER
    LETTER APOSTROPHE, which IS Unicode category Lm ("letter, modifier") and
    so DOES pass isalpha() -- treating it as a real letter would inject a
    phantom consonant after every elided word, silently corrupting every
    downstream position-length count for that line."""
    nfd = unicodedata.normalize("NFD", word)
    units: list[dict] = []
    i, n = 0, len(nfd)
    while i < n:
        ch = nfd[i]
        base = ch.lower()
        if base not in GREEK_LETTER_BASES:
            i += 1
            continue
        j = i + 1
        marks = ""
        while j < n and unicodedata.combining(nfd[j]):
            marks += nfd[j]
            j += 1
        units.append({
            "base": base,
            "vowel": base in VOWEL_BASES,
            "diaeresis": DIAERESIS_MARK in marks,
            "subscript": YPOGEGRAMMENI_MARK in marks,
        })
        i = j
    return units


def word_symbols(word: str) -> list[dict]:
    """A word's letters reduced to a symbol stream: vowel NUCLEI (diphthongs
    already merged, subject to a diaeresis blocking the merge) each carrying
    a natural-quantity weight ('L'/'S'/'D' for dichronon), and consonants.
    Pure function of one word's surface text; used by build_line_slots to
    assemble the whole-line nucleus/consonant stream (position-length needs
    the whole line, since Greek verse counts consonants across word
    boundaries)."""
    units = _letter_units(word)
    out: list[dict] = []
    i, n = 0, len(units)
    while i < n:
        u = units[i]
        if not u["vowel"]:
            out.append({"kind": "consonant", "base": u["base"]})
            i += 1
            continue
        if u["subscript"]:
            # Iota-subscript nucleus (a/e/o + adscript iota already fused):
            # always long by nature, a single nucleus.
            out.append({"kind": "vowel", "weight": "L", "bases": [u["base"]]})
            i += 1
            continue
        nxt = units[i + 1] if i + 1 < n else None
        if (nxt is not None and nxt["vowel"] and not nxt["diaeresis"]
                and (u["base"] + nxt["base"]) in DIPHTHONGS):
            out.append({"kind": "vowel", "weight": "L", "bases": [u["base"], nxt["base"]]})
            i += 2
            continue
        b = u["base"]
        if b in LONG_BY_NATURE_BASES:
            w = "L"
        elif b in SHORT_BY_NATURE_BASES:
            w = "S"
        else:
            w = "D"  # dichronon alpha/iota/upsilon: genuinely ambiguous
        out.append({"kind": "vowel", "weight": w, "bases": [b]})
        i += 1
    return out


def build_line_slots(words: list[str]) -> list[dict]:
    """The whole line's ordered nucleus slots, each:
        {weight, closed_by_position, mcl_candidate, gap, boundary,
         next_word: <index or None>, word: <index>}
    `gap` is the count of intervening consonants before the NEXT nucleus
    (0 = directly adjacent -- a synizesis candidate; 1 = open; 2+ = closed
    by position). `boundary` is True when that gap crosses a word boundary
    (needed for hiatus/digamma/correption, which are word-boundary
    phenomena only). `mcl_candidate` is True only when the closing pair is
    exactly one stop + one liquid/nasal, both within the word of the
    following vowel (the traditional muta-cum-liquida licence)."""
    flat: list[dict] = []
    for widx, word in enumerate(words):
        for sym in word_symbols(word):
            sym = dict(sym)
            sym["word"] = widx
            flat.append(sym)

    vowel_positions = [i for i, s in enumerate(flat) if s["kind"] == "vowel"]
    slots: list[dict] = []
    for idx, pos in enumerate(vowel_positions):
        sym = flat[pos]
        next_pos = vowel_positions[idx + 1] if idx + 1 < len(vowel_positions) else None
        between = flat[pos + 1: next_pos] if next_pos is not None else flat[pos + 1:]
        cons = [s for s in between if s["kind"] == "consonant"]
        gap = sum(2 if c["base"] in DOUBLE_CONSONANT_BASES else 1 for c in cons)
        boundary = next_pos is not None and flat[next_pos]["word"] != sym["word"]
        closed = gap >= 2
        mcl_candidate = (
            closed and len(cons) == 2
            and cons[0]["base"] in STOP_BASES and cons[1]["base"] in LIQUID_NASAL_BASES
            and cons[0]["word"] == cons[1]["word"] == (flat[next_pos]["word"] if next_pos is not None else sym["word"])
        )
        weight = "L" if closed else sym["weight"]
        slots.append({
            "weight": weight,
            "natural_weight": sym["weight"],
            "closed_by_position": closed,
            "mcl_candidate": mcl_candidate,
            "gap": gap,
            "boundary": boundary,
            "word": sym["word"],
            "next_word": flat[next_pos]["word"] if next_pos is not None else None,
            "bases": sym["bases"],
        })
    return slots


def _digamma_candidates(slots: list[dict], words: list[str]) -> set[int]:
    out = set()
    for i, slot in enumerate(slots):
        if slot["gap"] == 0 and slot["boundary"] and slot["next_word"] is not None:
            nxt = _strip_accents_lower(words[slot["next_word"]]).rstrip("'’ʼ")
            if nxt in DIGAMMA_WORDS:
                out.add(i)
    return out


def _correption_candidates(slots: list[dict]) -> set[int]:
    return {
        i for i, s in enumerate(slots)
        if s["weight"] == "L" and not s["closed_by_position"] and s["gap"] == 0 and s["boundary"]
    }


def _mcl_candidates(slots: list[dict]) -> set[int]:
    return {i for i, s in enumerate(slots) if s["mcl_candidate"]}


def _synizesis_candidates(slots: list[dict]) -> set[int]:
    """Indices i such that slots[i] and slots[i+1] are directly adjacent
    (gap 0) and can be merged into one long nucleus."""
    return {i for i, s in enumerate(slots) if s["gap"] == 0 and i + 1 < len(slots)}


def apply_relaxations(
    slots: list[dict], ops: tuple[tuple[str, int], ...]
) -> list[dict]:
    """Rebuild the slot list under a specific set of relaxation ops (each
    ("mcl"|"correption"|"digamma"|"synize", original_index)). Non-merge ops
    override one slot's weight; "synize" ops merge original-index i with
    i+1 into a single long nucleus. Applied against ORIGINAL slot indices so
    combinations compose without re-indexing bugs."""
    working = [dict(s) for s in slots]
    merges = set()
    for kind, i in ops:
        if kind == "mcl":
            working[i]["weight"] = working[i]["natural_weight"]
            working[i]["closed_by_position"] = False
        elif kind == "correption":
            working[i]["weight"] = "S"
        elif kind == "digamma":
            working[i]["weight"] = "L"
            working[i]["closed_by_position"] = True
        elif kind == "synize":
            merges.add(i)

    if not merges:
        return working

    out: list[dict] = []
    i = 0
    n = len(working)
    while i < n:
        if i in merges and i + 1 < n:
            merged = dict(working[i + 1])
            merged["weight"] = "L"
            merged["natural_weight"] = "L"
            merged["closed_by_position"] = False
            merged["mcl_candidate"] = False
            merged["synized_from"] = (i, i + 1)
            out.append(merged)
            i += 2
        else:
            out.append(working[i])
            i += 1
    return out


def foot_arrangements(k: int, total_feet: int = 5) -> list[tuple[bool, ...]]:
    """Every way to choose which `k` of `total_feet` feet are dactyls (True)
    vs. spondees (False), in deterministic (combinations()) order."""
    out = []
    for combo in combinations(range(total_feet), k):
        pattern = [False] * total_feet
        for idx in combo:
            pattern[idx] = True
        out.append(tuple(pattern))
    return out


ANCEPS = "X"  # required-weight placeholder: matches either L or S


def _required_sequence(arrangement: tuple[bool, ...]) -> list[str]:
    seq: list[str] = []
    for is_dactyl in arrangement:
        seq.extend(["L", "S", "S"] if is_dactyl else ["L", "L"])
    seq.extend(["L", ANCEPS])  # foot 6
    return seq


def _compatible(slots: list[dict], required: list[str]) -> bool:
    if len(slots) != len(required):
        return False
    for slot, req in zip(slots, required):
        if req == ANCEPS:
            continue
        if slot["weight"] == "D":
            continue
        if slot["weight"] != req:
            return False
    return True


def solve_arrangements(slots: list[dict]) -> list[tuple[bool, ...]]:
    """Every foot arrangement compatible with this exact slot list (no
    relaxations applied beyond whatever is already baked into `slots`),
    in deterministic order. Empty if the slot count is out of hexameter
    range (12-17) or no arrangement fits."""
    n = len(slots)
    k = n - 12
    if not (0 <= k <= 5):
        return []
    return [a for a in foot_arrangements(k) if _compatible(slots, _required_sequence(a))]


def _feet_string(arrangement: tuple[bool, ...], slots: list[dict]) -> str:
    """6-char feet string: chars 1-5 from the arrangement (D/S); char 6 is
    the verse-final anceps syllable, recorded 'S' (long, or long-by-verse-
    end-convention) unless it is naturally short and NOT closed by
    position, in which case it is 'X' -- a brevis in longo (flagged in
    notes by the caller)."""
    chars = ["D" if d else "S" for d in arrangement]
    last = slots[-1]
    if last["natural_weight"] == "S" and not last["closed_by_position"]:
        chars.append("X")
    else:
        chars.append("S")
    return "".join(chars)


FLAG_LABELS = {
    "mcl": "muta-cum-liquida",
    "correption": "correption",
    "digamma": "digamma-assumed",
    "synize": "synizesis",
}


def _render(
    ops: tuple[tuple[str, int], ...],
    resulting_slots: list[dict],
    arrangement: tuple[bool, ...],
    hiatus_positions: set[int],
) -> tuple[str, tuple[str, ...]]:
    """One (ops, slots, arrangement) triple -> its actual output (feet,
    notes). Two different relaxation derivations that happen to produce the
    identical output (e.g. two different, arithmetically-equivalent
    synizesis choices when the intervening syllables are all dichrona
    anyway) are the SAME answer, not a source of ambiguity -- see scan_line."""
    notes: list[str] = []
    for kind, _i in ops:
        label = FLAG_LABELS[kind]
        if label not in notes:
            notes.append(label)
    synized_here = {i for kind, i in ops if kind == "synize"}
    if hiatus_positions - synized_here:
        notes.append("hiatus")
    feet = _feet_string(arrangement, resulting_slots)
    if feet[-1] == "X" and "brevis-in-longo" not in notes:
        notes.append("brevis-in-longo")
    return feet, tuple(sorted(set(notes)))


def scan_line(words: list[str]) -> dict:
    """Scan one line's word list. Returns {"feet", "confidence", "notes"}."""
    base_slots = build_line_slots(words)

    # Hiatus is descriptive, not a relaxation: every raw word-boundary
    # vowel-vowel adjacency (gap 0, boundary True) is a candidate to report,
    # unless a synizesis op actually merges that exact pair -- see _render.
    hiatus_positions = {i for i, s in enumerate(base_slots) if s["gap"] == 0 and s["boundary"]}

    mcl = sorted(_mcl_candidates(base_slots))
    correption = sorted(_correption_candidates(base_slots))
    digamma = sorted(_digamma_candidates(base_slots, words))
    synize = sorted(_synizesis_candidates(base_slots))
    all_candidates = (
        [("mcl", i) for i in mcl]
        + [("correption", i) for i in correption]
        + [("digamma", i) for i in digamma]
        + [("synize", i) for i in synize]
    )

    def try_level(level: int) -> list[tuple[tuple[tuple[str, int], ...], list[dict], tuple[bool, ...]]]:
        """All (ops, resulting_slots, arrangement) triples valid at exactly
        `level` simultaneous relaxations, in deterministic candidate order."""
        found = []
        for ops in combinations(all_candidates, level):
            resulting = apply_relaxations(base_slots, ops)
            for arrangement in solve_arrangements(resulting):
                found.append((ops, resulting, arrangement))
        return found

    chosen = None
    for level in range(0, min(MAX_RELAXATION_LEVEL, len(all_candidates)) + 1):
        results = try_level(level)
        if results:
            chosen = results
            break

    if chosen is None:
        # No parse at any relaxation level: honest best-effort residue.
        # Best-effort feet: clamp the raw (unrelaxed) syllable count into
        # hexameter range and take the first arrangement at that count, so
        # the output is *some* well-formed 6-char string, never a claim of
        # a clean scan.
        n = len(base_slots)
        k = max(0, min(5, n - 12))
        arrangement = foot_arrangements(k)[0]
        feet = "".join("D" if d else "S" for d in arrangement) + "S"
        return {"feet": feet, "confidence": "ambiguous", "notes": ["unresolved"]}

    # Distinct actual OUTPUTS (feet, notes) among the winning (minimal-
    # relaxation-level) derivations -- see _render's docstring for why two
    # different derivations can legitimately collapse to one answer.
    outputs = [_render(ops, slots, arrangement, hiatus_positions) for ops, slots, arrangement in chosen]
    distinct = list(dict.fromkeys(outputs))  # de-dup, preserve first-seen order

    feet, notes = distinct[0]
    confidence = "high" if len(distinct) == 1 else "ambiguous"
    return {"feet": feet, "confidence": confidence, "notes": list(notes)}


def _load_book_lines(dist_dir: Path) -> list[tuple[int, int, list[str]]]:
    """[(book, line_n, [word_surface, ...]), ...] for every line, in the
    corpus's own emitted order."""
    out = []
    for path in sorted(dist_dir.glob("book-*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        book_n = doc["book"]
        for seg in doc["segments"]:
            for line in seg["greek"]:
                words = [tok["t"] for tok in line["tokens"]]
                out.append((book_n, line["n"], words))
    return out


def run(manifest: Manifest) -> dict:
    work_id = manifest.work_id
    dist_dir = BUILD_DIR / "dist" / work_id
    lines_raw = _load_book_lines(dist_dir)

    # Clear any stale scansion-*.json from a previous run whose book set has
    # since shrunk (e.g. a manifest edit), so a re-run never leaves an orphan
    # file behind for a book that no longer exists.
    for stale in dist_dir.glob("scansion-*.json"):
        stale.unlink()

    lines_by_book: dict[int, dict[str, dict]] = {}
    high = ambiguous = unresolved = 0
    feet_counter: dict[str, int] = {}
    flag_counter: dict[str, int] = {}
    for book_n, line_n, words in lines_raw:
        result = scan_line(words)
        key = f"{book_n}.{line_n}"
        lines_by_book.setdefault(book_n, {})[key] = result
        if result["confidence"] == "high":
            high += 1
        else:
            ambiguous += 1
        if "unresolved" in result["notes"]:
            unresolved += 1
        feet_counter[result["feet"]] = feet_counter.get(result["feet"], 0) + 1
        for flag in result["notes"]:
            flag_counter[flag] = flag_counter.get(flag, 0) + 1

    out_paths: list[Path] = []
    for book_n in sorted(lines_by_book):
        out_path = dist_dir / f"scansion-{book_n:02d}.json"
        out_path.write_text(
            json.dumps(
                {"work": work_id, "book": book_n, "lines": lines_by_book[book_n]},
                ensure_ascii=False, indent=1,
            ) + "\n",
            encoding="utf-8",
        )
        out_paths.append(out_path)

    total = len(lines_raw)
    return {
        "work": work_id,
        "paths": out_paths,
        "books": sorted(lines_by_book),
        "total_lines": total,
        "high": high,
        "ambiguous": ambiguous,
        "unresolved": unresolved,
        "feet_counter": feet_counter,
        "flag_counter": flag_counter,
    }
