# Apparatus data schemas (Phase 4) — defined BEFORE fan-out

All authored apparatus is AI-drafted with `"status": "draft"` until John flips
it. Drafting agents return DATA in these exact shapes; non-conforming output is
rejected and re-run, never hand-patched. The drafting agent for a book never
signs off on that book.

## scenes.json (per work: `apparatus/scenes/<work>.json`)

```json
{
  "work": "iliad",
  "status": "draft",
  "books": [
    {
      "book": 1,
      "argument": "<= 15 words, the book in one line>",
      "where": ["Troy", "the Achaean camp"],
      "who": ["Achilles", "Agamemnon", "Chryses", "Apollo"],
      "days": "1-21",
      "scenes": [
        {
          "lines": [1, 7],
          "summary": "<= 20 words, present tense, factual (Landmark register)",
          "location": "Achaean camp",
          "dayNumber": 1
        }
      ]
    }
  ]
}
```

Rules: `lines` are vulgate line numbers within the book, non-overlapping,
ascending, covering the whole book (gaps allowed only at the six known
vulgate gaps). `dayNumber` per the epic's internal calendar (Iliad: 1–51
tradition; Odyssey: story-day of the telling frame); use `null` where a day
is indeterminate (e.g. Olympian scenes outside time). Summaries: no
interpretation beyond the text, no spoiler-avoidance games, Landmark register
("Persia conquers Ionia and the islands.").

## places.json (single file `apparatus/places.json`)

```json
{
  "status": "draft",
  "places": [
    {
      "id": "ismarus",
      "name": "Ismarus",
      "greek": "Ἴσμαρος",
      "pleiades": "https://pleiades.stoa.org/places/501348",
      "certainty": "traditional",
      "tradition": "identified with Maroneia region, Thrace (ancient tradition; Strabo 7 fr.)",
      "coords": [40.65, 25.52],
      "maps": ["wanderings"],
      "mentions": [{"work": "odyssey", "book": 9, "lines": [39, 40]}],
      "note": "<= 40 words"
    }
  ]
}
```

`certainty`: `certain | traditional | speculative | mythical`. A `traditional`
or `speculative` identification MUST name its tradition/proponent in
`tradition`. `mythical` places get no `pleiades`/`coords` unless a traditional
localization exists (then keep certainty `mythical` and put the localization
in `tradition`). NEVER invent an identification. `maps`: which of
`ships | troad | wanderings | greece` panels show it.

## characters.json (single file `apparatus/characters.json`)

```json
{
  "status": "draft",
  "characters": [
    {
      "id": "achilles",
      "name": "Achilles",
      "greek": "Ἀχιλλεύς",
      "epithets": ["swift-footed", "son of Peleus"],
      "role": "<= 12 words",
      "genealogy": {"tree": "aeacus", "father": "peleus", "mother": "thetis"},
      "note": "<= 60 words, draft",
      "dicesId": null
    }
  ]
}
```

Genealogy trees: `atreus | aeacus | troy | olympians`. `dicesId` filled by the
speech-span stage join, not by drafters.

Genealogy honesty (added after the 2026-07-17 Grok gate): a parent link not
attested in Homer may remain in the structured fields ONLY when the tree needs
it to connect, and must then be flagged: `"genealogy": {..., "nonHomeric":
["father"]}` with the source tradition named in `note`. The UI renders
flagged links visually distinct (dashed). Unflagged links assert Homeric
attestation. Figures never named in Homer get no entry unless a tree
structurally requires them (then the whole entry's note states the source).

## catalogue.json (single file `apparatus/catalogue.json` — Catalogue of Ships)

```json
{
  "status": "draft",
  "achaean": [
    {
      "id": "boeotians",
      "name": "Boeotians",
      "lines": [494, 510],
      "leaders": ["peneleos", "leitus"],
      "ships": 50,
      "places": ["hyria", "aulis"],
      "note": "<= 30 words"
    }
  ],
  "trojan": [
    { "id": "trojans", "name": "Trojans", "lines": [816, 818],
      "leaders": ["hector"], "ships": null, "places": ["troy"] }
  ]
}
```

`lines` are vulgate lines within Il. 2 (Achaean 494–759, Trojan 816–877),
non-overlapping, ascending. `ships` = the number Homer states (null for the
Trojan catalogue, which counts no ships). `leaders`/`places` are kebab-case
ids; leaders SHOULD resolve to characters.json when the figure is there,
else remain plain strings (catalogue-only leaders are NOT added to
characters.json). `places` entries MUST exist in places.json (the ships-map
entries added by the same lane). Ship counts are data: verify each against
the Greek line that states it.

## speeches.json (per work, from DICES: `apparatus/speeches/<work>.json`)

Computed from sources/dices/speechdb.json (CC-BY 4.0), not authored:
`{work, status: "imported", speeches: [{id, book, lines: [fi, la], speaker:
[charId], addressee: [charId], level, cluster, part, type}]}`. Spans crossing
book boundaries are flagged `crossBook: true`, never split silently. Nesting
`level >= 1` renders flagged (Apologoi rule); coloring only for
high-confidence spans (level 0 and clean level 1).

## Computed stages (4d — no authoring)

- epithets: `build/dist/<work>/epithets.json` — per named entity:
  `{entity, formulas: [{text, lemmaKeys, count, refs: [{book, line}]}]}`.
- repetitions: `build/dist/repetitions.json` — exact repeated lines + 4-word+
  n-grams occurring >= 2x, cross-epic: `{key, text, count, refs}`.
Maximal-n-gram rule (both stages, explosion control): a shorter candidate is
dropped only when a strictly longer *accepted* candidate contains it as a
contiguous sub-sequence AND has the identical ref set; a shorter candidate
with a broader/different ref set is kept independently.
Both deterministic, pipeline-tested (fixture + determinism test re-run twice,
byte-identical output).
