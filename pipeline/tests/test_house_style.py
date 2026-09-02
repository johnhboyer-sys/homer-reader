"""House style: American English in reader-facing apparatus prose.

Walks apparatus/**/*.json and flags British spellings in prose fields
(name, note, title, label, summary, tradition, caption, subtitle, english,
text, key, plus epithets / argument / glosses). Citations (sources, cite)
are skipped. Quoted spans and an explicit allowlist keep source titles.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPARATUS = ROOT / "apparatus"

# Keys whose string values are reader-facing prose. `sources` / `cite` are
# citations and are never scanned.
PROSE_KEYS = {
    "name",
    "note",
    "title",
    "label",
    "summary",
    "tradition",
    "caption",
    "subtitle",
    "english",
    "text",
    "key",
    # Scene book-arguments and character epithets are also reader-facing.
    "argument",
    "epithets",
    # formula-glosses.json: { "glosses": { <greek>: <english> } }
    "glosses",
}

SKIP_KEYS = {"sources", "cite"}

# British → American. Longer forms first so the alternation is unambiguous.
BRITISH_TO_AMERICAN = {
    "colouring": "coloring",
    "coloured": "colored",
    "colours": "colors",
    "colour": "color",
    "centred": "centered",
    "centres": "centers",
    "centre": "center",
    "harbours": "harbors",
    "harbour": "harbor",
    "kilometres": "kilometers",
    "kilometre": "kilometer",
    "metres": "meters",
    "metre": "meter",
    "defences": "defenses",
    "defence": "defense",
    "grey": "gray",
    "honoured": "honored",
    "honours": "honors",
    "honour": "honor",
    "labours": "labors",
    "labour": "labor",
    "neighbours": "neighbors",
    "neighbour": "neighbor",
    "travelled": "traveled",
    "travelling": "traveling",
    "modelled": "modeled",
    "modelling": "modeling",
    "levelled": "leveled",
    "cancelled": "canceled",
    "favourite": "favorite",
    "favour": "favor",
    "behaviour": "behavior",
    "armour": "armor",
    "organised": "organized",
    "organise": "organize",
    "recognised": "recognized",
    "recognise": "recognize",
    "realised": "realized",
    "realise": "realize",
    "emphasise": "emphasize",
    "summarise": "summarize",
    "analysed": "analyzed",
    "analyse": "analyze",
    "programme": "program",
    "storeys": "stories",
    "storey": "story",
    "artefacts": "artifacts",
    "artefact": "artifact",
    "sceptical": "skeptical",
    "judgement": "judgment",
    "ageing": "aging",
    "plough": "plow",
    "moulded": "molded",
    "mould": "mold",
    "sulphur": "sulfur",
    "theatre": "theater",
    "litre": "liter",
    "fibres": "fibers",
    "fibre": "fiber",
    "aluminium": "aluminum",
    "draught": "draft",
    "enrol": "enroll",
    "fulfil": "fulfill",
    "instalment": "installment",
    "skilful": "skillful",
    "wilful": "willful",
    "jewellery": "jewelry",
}

_BRITISH_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in BRITISH_TO_AMERICAN) + r")\b",
    re.IGNORECASE,
)

# Phrases that keep their author's / tradition's spelling. Each entry is a
# case-insensitive substring; a British word sitting inside one is exempt.
ALLOWLIST_PHRASES = [
    # Established Homeric section title (John, 2026-09-02): keep -ue.
    "Catalogue of Ships",
    # Simpson & Lazenby 1970 book title; keep the author's spelling.
    "The Catalogue of the Ships in Homer's Iliad",
    # Copernicus DEM attribution; German company name, not house prose.
    "Airbus Defence and Space",
    # Kayan 1995 article title; keep the author's spelling.
    "The Troia Bay and Supposed Harbour Sites in the Bronze Age",
]

# Straight and curly double quotes, plus curly singles used as quotes.
# Straight apostrophes are possessives (Catalogue's) and are not quotes.
_QUOTE_RE = re.compile(
    r'"[^"\n]{1,500}"'
    r"|“[^”\n]{1,500}”"
    r"|‘[^’\n]{1,500}’"
)


def _quoted_spans(text: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in _QUOTE_RE.finditer(text)]


def _inside(spans: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(a <= start and end <= b for a, b in spans)


def _allowlist_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    lower = text.lower()
    for phrase in ALLOWLIST_PHRASES:
        needle = phrase.lower()
        start = 0
        while True:
            found = lower.find(needle, start)
            if found == -1:
                break
            spans.append((found, found + len(needle)))
            start = found + 1
    return spans


def british_hits(text: str) -> list[str]:
    """British whole-words in `text` that are not quoted and not allowlisted."""
    quoted = _quoted_spans(text)
    allowed = _allowlist_spans(text)
    found: list[str] = []
    for m in _BRITISH_RE.finditer(text):
        if _inside(quoted, m.start(), m.end()):
            continue
        if _inside(allowed, m.start(), m.end()):
            continue
        found.append(m.group(0))
    return found


def _walk(obj, *, in_prose: bool, file: Path, path: str, hits: list[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            kl = key.lower() if isinstance(key, str) else str(key)
            child_path = f"{path}/{key}" if path else str(key)
            if kl in SKIP_KEYS:
                continue
            child_prose = in_prose or kl in PROSE_KEYS
            _walk(value, in_prose=child_prose, file=file, path=child_path, hits=hits)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            _walk(
                value,
                in_prose=in_prose,
                file=file,
                path=f"{path}[{i}]",
                hits=hits,
            )
    elif isinstance(obj, str) and in_prose:
        words = british_hits(obj)
        if words:
            rel = file.relative_to(ROOT)
            unique = ", ".join(dict.fromkeys(words))
            snippet = obj.replace("\n", " ")
            if len(snippet) > 160:
                snippet = snippet[:157] + "..."
            hits.append(f"{rel} {path}: {unique} — {snippet}")


def test_apparatus_prose_is_american_english():
    hits: list[str] = []
    files = sorted(APPARATUS.rglob("*.json"))
    assert files, f"no apparatus JSON under {APPARATUS}"
    for path in files:
        doc = json.loads(path.read_text(encoding="utf-8"))
        _walk(doc, in_prose=False, file=path, path="", hits=hits)
    assert hits == [], (
        f"{len(hits)} British spelling(s) in reader-facing apparatus prose:\n"
        + "\n".join(hits)
    )
