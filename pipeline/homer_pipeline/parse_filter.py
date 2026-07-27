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
    """Apply a curated lemma/gloss repair after automatic resolution."""
    override = overrides.get(surface) if surface is not None else None
    if override is None or not parses:
        return parses

    corrected = list(parses)
    corrected[0] = dict(corrected[0])
    if lemma := override.get("lemma"):
        corrected[0]["lemma"] = lemma
    if gloss := override.get("gloss"):
        corrected[0]["gloss"] = gloss
    return corrected


def filter_parses(parses: list[dict]) -> list[dict]:
    """Return `parses` with redundant unresolved readings removed.

    Each parse is a dict with at least `gloss` (str) and `lsj` (list) keys.
    """
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
