"""Drop spurious Morpheus secondary readings from a token's analyses.

Morpheus emits every homonym candidate it can generate, unranked. For Attic
prose like Aristotle this includes obvious noise — a Doric masculine reading of
a feminine proper noun (Εὐρώπης), a back-formed alternate lemma sharing the same
gloss as the real one (ἡδονά beside ἡδονή), etc. These surface in the word popup
as extra parse cards, often with no dictionary headword at all.

The filter is deliberately conservative. An analysis with no LSJ match is
removed only when BOTH:
  * the same token has at least one LSJ-backed reading (so something real
    remains), AND
  * the unresolved reading is redundant — it has no gloss, or its gloss exactly
    duplicates a resolved sibling's gloss.

Genuine alternative lemmas (an unresolved reading with a *distinct* gloss, e.g.
ἐφαιρέομαι beside πέλω) and wholly unresolved words (rare terms, proper names not
in LSJ) are always kept. No token is ever left with zero analyses.
"""

from __future__ import annotations

import json
from pathlib import Path


_OVERRIDE_PATH = Path(__file__).with_name("morphology_overrides.json")

# Closed-class forms whose spelling/elision makes the later indeclinable parse
# unambiguous in Homer.  Each family is guarded by both surface and misleading
# first lemma so that other short-form homonyms keep Morpheus's stable order.
_FUNCTION_WORD_FAMILIES = (
    ({"w(/s"}, {"o(/s"}, "w(s"),
    ({"t'", "q'", "te/"}, {"su/"}, "te"),
    ({"o(/te", "o(/t'"}, {"o(/ste"}, "o(/te"),
    ({"w)="}, {"ei)mi/"}, "w)="),
    ({"e)/peit'", "e)/peiq'"}, {"e)/peimi2"}, "e)/peita"),
    ({"e)/t'"}, {"e)/ths"}, "e)/ti"),
    ({"kaq'", "ka/ta"}, {"kaqa/", "ka/tos"}, "kata/"),
    ({"u(f'"}, {"u(fh/"}, "u(po/"),
)

# Inflectional families for which the primary is a demonstrably impossible or
# non-Homeric homonym and the later analysis supplies the Homeric noun/verb.
_HOMERIC_LEMMA_FAMILIES = (
    ({"a)xaiw=n"}, {"*)axai/a"}, "*)axaio/s"),
    (
        {"qew=n", "qeoi=si", "qeoi=sin", "qeoi=s", "qeou=", "qew=|", "qeoi=o"},
        {"qe/a", "qea/", "qea/w", "qea/omai"},
        "qeo/s",
    ),
    ({"nhw=n", "new=n"}, {"nao/s"}, "nau=s"),
    ({"e)/xei"}, {"e)/xis"}, "e)/xw"),
    ({"a)ndri/"}, {"a)ndri/s"}, "a)nh/r"),
    ({"bow=n"}, {"bo/a"}, "bou=s"),
    ({"i(drw=", "i(drw=|"}, {"i(dro/w"}, "i(drw/s"),
)


def load_morphology_overrides(path: Path = _OVERRIDE_PATH) -> dict[str, dict]:
    """Load and validate the owner-reviewable surface-form overrides."""
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError(f"{path}: expected a JSON list")

    overrides = {}
    required = {"surface", "justification"}
    allowed = required | {"lemma", "gloss"}
    for entry in entries:
        if not isinstance(entry, dict) or not required <= entry.keys():
            raise ValueError(f"{path}: every override needs surface and justification")
        if set(entry) - allowed or not ({"lemma", "gloss"} & entry.keys()):
            raise ValueError(f"{path}: invalid override fields for {entry.get('surface')}")
        if not all(isinstance(value, str) and value for value in entry.values()):
            raise ValueError(f"{path}: override values must be non-empty strings")
        surface = entry["surface"]
        if surface in overrides:
            raise ValueError(f"{path}: duplicate surface {surface}")
        overrides[surface] = entry
    return overrides


MORPHOLOGY_OVERRIDES = load_morphology_overrides()


def _promote(parses: list[dict], index: int) -> list[dict]:
    """Move one analysis to the front without disturbing any other order."""
    return [parses[index], *parses[:index], *parses[index + 1 :]]


def _preferred_index(parses: list[dict], lemma: str) -> int | None:
    return next(
        (index for index, parse in enumerate(parses[1:], 1)
         if parse["lemma"] == lemma),
        None,
    )


def _is_nominal(parse: dict) -> bool:
    words = set(parse["parse"].replace("/", " ").split())
    has_gender = bool(words & {"masc", "fem", "neut"})
    is_verbal = bool(
        words & {"part", "ind", "subj", "opt", "imperat", "inf", "imperf"}
    )
    return has_gender and not is_verbal


def _promote_family_match(
    parses: list[dict],
    surface: str | None,
    families: tuple[tuple[set[str], set[str], str], ...],
) -> list[dict] | None:
    primary = parses[0]
    for surfaces, misleading_lemmata, preferred_lemma in families:
        if (surface is None or surface in surfaces) and (
            primary["lemma"] in misleading_lemmata
        ):
            index = _preferred_index(parses, preferred_lemma)
            if index is not None:
                return _promote(parses, index)
    return None


def rank_parses(parses: list[dict], surface: str | None = None) -> list[dict]:
    """Stably promote a demonstrably preferable Homeric analysis, if present."""
    if len(parses) < 2:
        return parses

    if preferred := _promote_family_match(
        parses, surface, _FUNCTION_WORD_FAMILIES
    ):
        return preferred

    # Morpheus often reads a genitive noun as a back-formed denominal -όω
    # verb.  Prefer the nominal candidate only when the verb has no Cunliffe
    # entry and the noun does; this excludes real Homeric verbs such as βιόω.
    primary = parses[0]
    if primary["lemma"].endswith("o/w") and not primary.get("cunliffe"):
        index = next(
            (
                index
                for index, parse in enumerate(parses[1:], 1)
                if parse.get("cunliffe") and _is_nominal(parse)
            ),
            None,
        )
        if index is not None:
            return _promote(parses, index)

    if preferred := _promote_family_match(
        parses, surface, _HOMERIC_LEMMA_FAMILIES
    ):
        return preferred

    return parses


def apply_morphology_override(
    parses: list[dict],
    surface: str | None,
    overrides: dict[str, dict] = MORPHOLOGY_OVERRIDES,
) -> list[dict]:
    """Apply a curated lemma/gloss repair after automatic resolution.

    Two shapes, and the difference matters:

    * The target lemma is ALREADY among the parses — Morpheus simply ranked it
      below something else. Promote the real analysis, which keeps its own
      parse and its lexicon links. Rewriting the front entry instead would
      relabel a different reading: χωόμενος took χάζομαι's FUTURE participle,
      stamped "χώομαι" on it, and so claimed χωόμενος was a future participle
      of χώομαι, with no LSJ link. A false morphological claim, and worse than
      the wrong lemma it replaced.
    * The target is absent — Morpheus offers no correct reading at all, as with
      the negative particle whose gloss comes through as "u". There the front
      entry is repaired in place, which is the only option and changes no
      ordering.
    """
    override = overrides.get(surface) if surface is not None else None
    if override is None or not parses:
        return parses

    lemma = override.get("lemma")
    if lemma:
        index = _preferred_index(parses, lemma)
        if index is not None:
            return _promote(parses, index)

    corrected = list(parses)
    corrected[0] = dict(corrected[0])
    if lemma:
        corrected[0]["lemma"] = lemma
    if gloss := override.get("gloss"):
        corrected[0]["gloss"] = gloss
    return corrected


# ── Ghost lemmata ───────────────────────────────────────────────────────────
# Lemmata Morpheus offers that are not Homeric words at all. Dropped here, at
# the emit, so every consumer is clean at once — the word popup's cards, the
# vocabulary lists, and the lemma pages — rather than each filtering its own.
#
# χάω is the whole of LSJ s.v.:
#
#     χάω, contr. χῶ, = χωρῶ, coined as etym. of χάος by Simp. in Ph. 620.14.
#
# Simplicius coined it in the sixth century AD as an etymological guess for
# χάος; it is attested once, in a commentary on the Physics. It was Morpheus's
# FIRST analysis on 39 forms across the two poems, displacing χέω "pour out"
# (28 — libations and tears), χώομαι "to be angry" (9, in the poem about
# Achilles' wrath), χαίτη and χήν.
#
# ἐφαμάω's whole entry is "ἐφαμάω, v. ἐπαμάομαι." — a cross-reference stub with
# no definition of its own. It was taking ἐφάμην, the imperfect of φημί, which
# is "I said" and is most of Odysseus' narration.
#
# ἐλεάω's whole entry is "ἐλεάω, later form of ἐλεέω, EM 327.29, LXX Pr.
# 21.26." — a form recorded only from the Etymologicum Magnum and the
# Septuagint, with no independent Homeric standing. It was Morpheus's FIRST
# analysis on every occurrence: 38 tokens across the two poems (28 Iliad, 10
# Odyssey; 15 distinct surface forms), every one displacing ἐλεέω "have pity
# on, show mercy to" — and always with the identical parse in the same slot
# (e.g. ἐλεήσῃ's "aor subj mid 2nd sg" is tagged on both lemmata verbatim), so
# dropping the ghost changes no morphology, only which lemma is attached to
# it.
#
# ἀπέχθομαι's whole entry is likewise "ἀπέχθομαι, later form of ἀπεχθάνομαι"
# (Theocritus onward). It was Morpheus's FIRST analysis on all 12 occurrences
# (8 Iliad, 4 Odyssey; 6 distinct surface forms), reading the Homeric aorist
# middle forms ἀπήχθετο, ἀπέχθηται, ἀπεχθόμενος etc. as its OWN present-stem
# imperfect or present. But LSJ's ἀπεχθάνομαι entry itself cites the very
# form ἀπήχθετο as that verb's aorist ("ἀπήχθετο πᾶσι θεοῖσι", Il. 6.140) and
# notes Homer uses the verb "always in aor." Dropping the ghost does not
# relabel anything: it removes the mismatched present/imperfect parse
# outright, and ἀπεχθάνομαι's own aorist parse — already correctly tagged by
# Morpheus — takes its place.
#
# πέδιον's whole entry is "πέδιον, τό, Dim. of πέδη, EM 658.23." — a diminutive
# of πέδη "fetter," recorded only in the Etymologicum Magnum, spelled exactly
# like the real word but for where the accent falls. It was Morpheus's FIRST
# analysis on all 68 occurrences across the two poems (3 distinct surface
# forms — πεδίοιο, πεδίῳ, πεδίου), always beside πεδίον "plain" tagged with the
# identical case and number, so dropping it changes no morphology, only which
# lemma is attached to it.
#
# νεί's whole entry is "νεί, Boeot. for νή, Ar. Ach. 867, 905; also Arc." — a
# Boeotian and Arcadian dialect spelling of the oath-particle νή, attested
# only in Aristophanes and an Orchomenos inscription. It was Morpheus's FIRST
# analysis on 43 occurrences across the two poems (7 distinct surface forms of
# νεῖκος "quarrel, strife, feud" and νεικέω "quarrel, wrangle with"), always
# beside a correctly-tagged νεῖκος or νεικέω sibling in the identical
# case/number/person — nei/kei even carries three ghost entries in the same
# slot list, each matched by its own nei=kos or neike/w counterpart.
#
# θέραψ's whole entry is "θέραψ, ᾰπος, ὁ, poet., = θεράπων, rare in sg." and
# every citation in it is Euripides, Anacreon, or an inscription — never
# Homer. It was Morpheus's FIRST analysis on all 26 occurrences of θεράπων
# "henchman, attendant" (Patroclus is θεράπων Ἀχιλῆος throughout the Iliad),
# tagging the nominative singular surface θεράπων as θέραψ's genitive plural,
# always beside θεράπων's own correctly-tagged nominative singular.
#
# ῥόον's whole entry is "ῥόον, τό, only in pl. ῥόα, = τὰ ἐκ τῆς συκαμίνου μόρα
# τὰ ἄωρα ξηρανθέντα" — unripe, dried mulberries, a Hippocratic medical term.
# It was Morpheus's FIRST analysis on all 23 occurrences of ῥόος "stream, flow
# of water, current" (the rivers of the Troad — Scamander, Ocean), always
# beside ῥόος's own correctly-tagged sibling in the identical case/number.
#
# ἄμυμος's whole entry is "ἄμυμος, ον, = sq., Cyr., prob. in Hsch." — a
# conjectural form standing in for the real adjective, sourced from Cyril and
# a probable Hesychius gloss. It was Morpheus's FIRST analysis on all 19
# occurrences of ἀμύμων "blameless, noble, excellent," one of Homer's most
# frequent epithets, always beside ἀμύμων's own correctly-tagged sibling.
#
# οἴη (as a common noun, not the fem. of οἶος) has two LSJ entries and neither
# is Homeric: οἴη (A), "= κώμη [village]," attested at Chios, in Apollonius
# Rhodius, and in Hesychius; and οἴη (B), a bare cross-reference to ὄα (A).
# Both ride the single Morpheus lemma οἴη, whose lsj field reads ["οἴη1",
# "οἴη2"]. It was Morpheus's FIRST analysis on 43 occurrences across the two
# poems (7 distinct surface forms), always beside οἶος "alone, lonely" tagged
# with the identical feminine case/number — LSJ's own entry for οἶος cites
# this exact spelling as its Epic feminine ("μία οἴη, one alone," Il. 4.397).
#
# κάλη's whole entry is a cross-reference stub, "κάλη, καλήτης, v. κήλη,
# κηλήτης" — the Attic spelling of κήλη "tumour, hernia," a medical term
# absent from Homer under either spelling. It was Morpheus's FIRST analysis on
# 14 occurrences (κάλ', καλέων), always beside κάλως "reefing rope, reef"
# (Od. 5.260, of Odysseus's raft) or κήλη's own tumour sense, each an
# independently, correctly tagged sibling.
#
# κραταιά's whole entry is "κραταιά, ἡ, = χελιδόνιον μέγα, Ps.-Dsc. 2.180" —
# greater celandine, a plant name from Pseudo-Dioscorides. It was Morpheus's
# FIRST analysis on all 9 occurrences (Iliad only) of κραταιός "strong,
# mighty" (Il. 16.334's μοῖρα κραταιή and its kin), always beside κραταιός's
# own correctly-tagged sibling in the identical case/number.
#
# τήλη's whole entry is "τήλη, ἡ, = τῆλις" (fenugreek), attested only in a
# gloss and in Ptolemaic-era papyri. It was Morpheus's FIRST analysis on all 8
# occurrences of τῆλε "at a distance, far off," a common Homeric adverb,
# always beside τῆλε's own correctly-tagged sibling.
#
# φάρος bundles two non-Homeric LSJ senses under one Morpheus lemma: the
# pipeline's lemma field drops LSJ's disambiguating digit, so φάρος (A), "=
# φάρυγξ [throat], Lyc. 154" (attested only in Lycophron), is inseparable
# here from φάρος (B), "plough, Alcm. 23.61 ... Antim." (also non-Homeric,
# attested only in Alcman and Antimachus) — both ride the one parse whose lsj
# field reads ["φάρος1", "φάρος2"]. That parse's gloss, "a large piece of
# cloth, web," is a separate data bug: the text belongs to a third, unrelated
# entry, φᾶρος (A) — see this session's report; not fixed here. All 7
# occurrences (φάρεϊ, φάρεα, φάρε') sit beside a correctly-tagged φᾶρος "a
# large piece of cloth, web" sibling (Od. 5.258's φάρε' ἔνεικε Καλυψώ, Il.
# 2.43) in the identical case/number, so dropping φάρος leaves the real word
# standing under its own, correctly glossed entry.
#
# κλεῖτος bundles two non-Homeric LSJ senses the same way: κλεῖτος (A), "poet.
# for κλέος, Alcm. 96, cf. Hsch."; and κλεῖτος (B), "= [κλίτος], pl. κλείτεα
# A.R. 1.599" (Apollonius Rhodius) — neither Homeric, both blank-glossed, both
# riding the one parse whose lsj field reads ["κλεῖτος1", "κλεῖτος2"]. It was
# Morpheus's FIRST analysis on all 3 occurrences of κλειτῶν (genitive
# plural), always beside κλειτός "renowned, famous" (Il. 3.451's κλειτοὶ
# ἐπίκουροι) correctly tagged in the identical case/number.
#
# A ghost is only ever dropped when the token has some other reading: see
# tests/test_parse_filter.py, which asserts over the shipped corpus that no
# token is left empty.
GHOST_LEMMA: frozenset[str] = frozenset(
    {
        "xa/w", "e)fama/w", "e)lea/w", "a)pe/xqomai",
        "pe/dion", "nei", "qe/ray", "r(o/on", "a)/mumos", "oi)/h", "ka/lh",
        "krataia/", "th/lh", "fa/ros", "klei=tos",
    }
)


def filter_parses(parses: list[dict]) -> list[dict]:
    """Return `parses` with redundant unresolved readings and ghost lemmata
    removed.

    Each parse is a dict with at least `gloss` (str) and `lsj` (list) keys.
    """
    # Never strand a token: a ghost is dropped only where something else
    # remains to read the form by.
    if any(p.get("lemma") not in GHOST_LEMMA for p in parses):
        parses = [p for p in parses if p.get("lemma") not in GHOST_LEMMA]

    has_resolved = any(p["lsj"] for p in parses)
    if not has_resolved:
        return parses

    resolved_glosses = {
        p["gloss"].strip() for p in parses if p["lsj"] and p["gloss"].strip()
    }

    kept = []
    for p in parses:
        gloss = p["gloss"].strip()
        redundant = (not p["lsj"]) and (not gloss or gloss in resolved_glosses)
        if not redundant:
            kept.append(p)
    return kept
