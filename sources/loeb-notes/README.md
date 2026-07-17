# Murray Loeb footnotes (acquired from first-printing scans)

## Purpose

Perseus Murray TEI marks **336** Loeb footnotes but keeps only bare citation numbers.
This directory holds **real note wording** from public-domain first-printing Loeb scans.

## US public-domain status (as of 2026)

| Work | First publication | PD basis |
|------|-------------------|----------|
| Odyssey (2 vols) | **1919** Heinemann/Putnam | US pre-1931 |
| Iliad (2 vols) | **1924** / **1925** Heinemann/Putnam | US pre-1931 |

### First-printing scans used

| Volume | archive.org id | Title-page date | URL |
|--------|----------------|-----------------|-----|
| Odyssey I | `odyssey01home` | MCMXIX (1919) | https://archive.org/details/odyssey01home |
| Odyssey II | `odysseywithengli02home` | MCMXIX (1919) | https://archive.org/details/odysseywithengli02home |
| Iliad I | `in.ernet.dli.2015.12689` | MCMXXIV (1924) | https://archive.org/details/in.ernet.dli.2015.12689 |
| Iliad II | `in.ernet.dli.2015.12691` | MCMXXV (1925) | https://archive.org/details/in.ernet.dli.2015.12691 |

Title-page OCR evidence is in each JSON `provenance.volumes[].titlePageDateEvidence`.

**Rejected (not first printings):** `odysseymurray01homeuoft` (1945 reprint), `iliadmurray01homeuoft` (1928 reprint), Dimock 1995 revision, 1940s Harvard DLI reprints.

## Marker inventory

| Source | Count |
|--------|-------|
| TEI Iliad Loeb notes | **144** |
| TEI Odyssey Loeb notes | **192** |
| **Total** | **336** |
| `build/dist/iliad/footnotes.json` keys | 99 (collisions) |
| `build/dist/odyssey/footnotes.json` keys | 46 (collisions) |

Pipeline: `pipeline/homer_pipeline/stage1_perseus_milestone_english.py` — labels `{book}.{raw}`, overwrites duplicates.

Reference shapes: simple per-page `N`; Iliad page-style `PAGE.N` (85 notes); stable `markerId=work.book.seqInBook`; `approxLine` from TEI line milestone.

## Method (v2, deterministic re-match — 2026-07-17)

The first-pass matching (sequential/best-effort, see git history) had correct note
*text* extraction but a defective *attachment* step: a Codex audit sampled its
confidence bands and found 14.3% wrong-locus in "high", 50% in "medium", 89% in
"low". Root cause: it didn't systematically use the OCR page running heads as an
alignment signal. This directory now uses a deterministic re-match:

1. **Page-head index, not sequential guessing.** Every OCR page in the four
   `_djvu.txt` scans carries a running head (`THE ILIAD, IX. 214-241`, tolerant of
   OCR noise in the digits/roman numeral). These are parsed into an ordered
   per-volume index of `(book, lineLo, lineHi)` zones, validated against
   TEI-derived canonical per-book max line numbers (rejects OCR-mangled ranges,
   e.g. `THE ODYSSEY, IV. 5090-533` for true `509-533`, rather than letting them
   corrupt book-boundary tracking).
2. **Loeb page-pairing.** Dual-text Loeb pages alternate a bare-header Greek
   (verso) page and a ranged-header English (recto) page that share one line
   range. A footnote's true zone is resolved from which header immediately
   *follows* it (if ranged, the footnote sits on the Greek page sharing that
   range) or immediately *precedes* it (if bare, the footnote is the tail of
   that English page) — not by treating "nearest preceding ranged header" as
   authoritative, which silently drops footnotes printed on Greek pages.
3. **Marker → note matching**, in priority passes so a weak marker can never
   pre-empt a candidate a later marker needs for an exact match: (a) TEI marker's
   `approxLine` falls inside the note's page zone AND the note's printed in-page
   footnote number equals the marker's own number (ties broken by the note's
   internal "Line N" self-references) → `high`; (b) same but with the zone
   widened ±30 lines (one page of slack) → `medium`; (c) same-book number match
   with no reliable zone → `low`; (d) never invent text — unmatched stays
   `noteText: null`.
4. **Garble detection.** Each candidate note is scored on the proportion of
   dictionary-plausible tokens (English/Greek word shapes, numerals) vs. OCR
   junk (isolated symbols/single letters). Notes failing the bar are flagged
   `garbled: true` and only ever used as an absolute last resort, never silently.
5. **Three manual-verified patches.** Three notes were dropped by the automatic
   footnote-line regex because the printed footnote glyph OCR'd as a letter, not
   a digit (`i` for `1`, `a` for a symbol), or because the page's own running
   head was OCR-mangled beyond automatic recovery. These were located and
   transcribed by hand against the raw `djvu.txt` and the Perseus TEI anchor
   context, and are tagged `matchMethod` containing `manual-verified-patch`:
   `iliad.18.5`, `odyssey.4.14`, `odyssey.15.2`.

Extraction date: **2026-07-17**. Re-match date: **2026-07-17**.

## Coverage

| Work | TEI | Matched | high | medium | low | garbled | Unmatched | % |
|------|-----|---------|------|--------|-----|---------|-----------|---|
| Iliad | 144 | 143 | 84 | 36 | 23 | 0 | 1 | 99.3% |
| Odyssey | 192 | 179 | 103 | 49 | 27 | 0 | 13 | 93.2% |
| **Total** | **336** | **322** | **187** | **85** | **50** | **0** | **14** | **95.8%** |

No `noteText` in the delivered files is flagged `garbled: true` — candidates that
failed the garble bar were only ever used when no clean alternative existed
anywhere in the same book, and none were needed in the final assignment.

## Self-audit (Codex's named failures + showcase notes, re-checked against v2)

All 6 of Codex's named wrong-locus failures are now `high` confidence with
verified-correct content: `iliad.9.1` (embassy/Phoenix note, not the book9
214–241 page), `iliad.18.5` (necklaces/ὅρμοι note, via manual patch — not the
stray "Line 441" note), `iliad.23.1` (Antilochus oath-in-chariot-race note, not
"Line 479"), `odyssey.4.14` (Thyestes/Aegisthus geography, via manual patch —
not the 756–779 range), `odyssey.15.2` ("Possibly 'fragrant'", via manual patch
— not the Pero/Melampus text with a garbled tail), `odyssey.19.9` (nightingale/
scholiast note, not the book-21 axes note or the Horn/Ivory wordplay passage).

All 8 showcase notes re-verified against the Perseus TEI anchor context: Il.
1.5 ἐξ οὗ, 1.10 Archer-god, 1.35 Smintheus/Mouse-god, 1.125 Aristarchus (medium —
two exact-zone candidates, no clean tiebreak); Od. 1.35 Argeiphontes, 1.40
grey-eyed (medium — widened match), 1.60 Odysseus/wrath wordplay (ὠδύσαο /
Ὀδυσεύς pun), 9.20(→9.2, true anchor line 25) Strabo/Ithaca χθαμαλή note. All
attach correct content; two remain `medium` rather than `high` because the
pipeline found a genuine positional ambiguity, not because the content is
wrong — spot-checked by hand against the TEI.

## Known noise / residual weaknesses

1. OCR errors (Greek lemmas, hyphenation); light polish only — not human-corrected.
2. Greek apparatus and English notes share the OCR stream on facing pages. The
   page-pairing logic (method step 2) resolves most of this, but a few
   candidate notes are still Greek apparatus criticus prose (e.g. "Lines N were
   rejected by Aristarchus") that happens to satisfy the same book+number match
   as the true Murray note when the true note was never extracted at all (see
   below). These are legible, not garbled, so they pass the garble bar and can
   still occupy a `medium`/`low` slot instead of the correct note.
3. **Known extraction gaps beyond the 3 patched:** the footnote-line extractor
   requires the printed number to OCR as a digit. Loeb print occasionally uses
   symbols (†, *, lowercase superscript letters) for a second note stream on
   the same page, which OCR renders as stray letters (`i`, `a`) that the
   extractor's `\d` regex misses entirely — those notes are silently absent
   from the candidate pool, not merely mis-zoned. Only the 3 self-audit-named
   instances were hand-recovered; others of this class likely remain among the
   `medium`/`low`/unmatched records. A full fix would re-run footnote-line
   detection with a broader marker-glyph regex and is future work.
4. `sourcePage` is recomputed independently (nearest standalone page-number
   line in the OCR after the note) and is informational only — it is not used
   for matching and is occasionally `null` when no digit-only line was found
   nearby.
5. Odyssey bare `1`/`2` markers (no page-style prefix) make same-page
   disambiguation harder when a page has 2+ footnotes; internal "Line N"
   self-references are used to break ties where present.
6. Prefer `confidence: high` for UI; review `medium`/`low` before sign-off.
7. Do not fill unmatched from Wyatt/Dimock revised Loebs (not PD).
8. `footnotes.json` unique-key counts are **not** the full 336-marker inventory.

Rebuild scripts (not in repo, scratchpad only): `rebuild/headers2.py` (page-head
index + book assignment, validated against TEI canonical max-lines),
`rebuild/match.py` (candidate pool, garble scoring, multi-pass matching),
`rebuild/finalize.py` (writes `notes-{iliad,odyssey}.json` in this directory).

Scratchpad (not in repo):  
`/private/tmp/claude-501/-Users-johnboyer-Developer-homer-reader/7a5765b7-2fee-4816-80c9-4ce966ef465e/scratchpad/loeb-notes/`
