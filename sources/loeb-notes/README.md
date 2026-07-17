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

## Method

1. Download `_djvu.txt` for the four first-printing identifiers.
2. Stream-parse running headers + English footnote blocks (incl. OCR `+` as numeral).
3. Per-book **sequential assignment** by footnote number; page-style by printed page;
   skip pure apparatus notes when a nearby explanatory note exists and the apparatus
   line-ref is not within ±2 of the TEI line.
4. Confidence from line-range / line-ref / page agreement.
5. Never invent text; unmatched → `noteText: null`.

Extraction date: **2026-07-17**.

## Coverage

| Work | TEI | Matched | high | medium | low | Unmatched | % |
|------|-----|---------|------|--------|-----|-----------|---|
| Iliad | 144 | 124 | 46 | 10 | 68 | 20 | 86.1% |
| Odyssey | 192 | 185 | 56 | 20 | 109 | 7 | 96.4% |
| **Total** | **336** | **309** | **102** | **30** | **177** | **27** | **92.0%** |

## Known noise

1. OCR errors (Greek lemmas, hyphenation); light polish only — not human-corrected.
2. Greek apparatus and English notes share the OCR stream; residual mis-attachments remain.
3. Odyssey bare `1`/`2` markers make matching approximate; sequential assignment is best-effort.
4. Prefer `confidence: high` for UI; review `medium`/`low` before sign-off.
5. Do not fill unmatched from Wyatt/Dimock revised Loebs (not PD).
6. `footnotes.json` unique-key counts are **not** the full 336-marker inventory.

Scratchpad (not in repo):  
`/private/tmp/claude-501/-Users-johnboyer-Developer-homer-reader/7a5765b7-2fee-4816-80c9-4ce966ef465e/scratchpad/loeb-notes/`
