# DEPLOY-STATUS — The Homer Reader

Ledger for John. One-off GitHub Pages build (no Cloudflare/R2). No deploys have
occurred; deploying, the GitHub remote, and the first push are John-gated.

## Build progress (2026-07-17)

- **Gate 0 PASSED**: docs/PHASE0-FINDINGS.md. Greek source = Perseus
  perseus-grc2 both poems (TLG texts are Allen **1931** and von der Mühll
  **1962** — in-copyright editions; Perseus fallback applied per the written
  degrade rule). Cunliffe included at launch incl. the 1931 proper-names
  volume (John's call, 2026-07-17).
- **Gate 1 PASSED**: fork bootstrapped; verse-line scheme live (dual TS/Python);
  full pipeline (stages 1–7) runs for both epics; dev server serves Il. 1
  (611 lines, n=1..611) and Od. 9 with tokenized Greek + verse layout.
  Tests: shared 218/218, app 2/2, pipeline pytest 125 pass.
- **Gate 2 PASSED** (2026-07-17, checked in main loop): preflight 0 errors;
  Od. 9.105–115 verified — Greek + Murray/Butler blocks aligned at tick 105,
  Pope standalone per degrade rule. All three translations emitted for all
  48 books. Cunliffe pane live (LSJ/Cunliffe/Logeion tabs). Corpus-wide
  gates PASS (LSJ 13,472 keys; Cunliffe 11,003 keys). Autenrieth =
  fast-follow (YELLOW).
- **Phase 3 begun**: design locked (Chart-Room base × Aegean palette,
  docs/DESIGN.md); lookup UX = docked sidebar desktop / popup mobile,
  EXPAND control, no new tabs except Logeion.

## Corpus facts

- Line totals (verbatim from Perseus grc2, independently re-derived): Iliad
  15,687; Odyssey 12,107.
- Vulgate numbering gaps (recorded as expected_line_gaps in manifests, all
  verified against raw TEI): Il. 9.458–461, Il. 11.543, Il. 14.269,
  Od. 10.456, Od. 16.101, Od. 23.49. Doc-order glitches sorted by n:
  Od. 3.304/305, Od. 14.63/64.
- **Morpheus unparsed-token rate** (stage 4, greek-analyses.txt scan):
  Iliad 0.04% (99.96% matched), Odyssey 0.13% (99.87% matched). Phase 0
  sample estimate was 0.33% on Il. 1. Homeric lookup-variants not needed
  (threshold was 8%).
- LSJ entries kept: Iliad 7,155; Odyssey 6,332.

## Model roster notes

- Grok-4.5 restored 2026-07-17 (free trial, ~85% balance; off probation —
  full implementer). Implemented the stage-1 Perseus reader + pipeline run;
  gap list independently confirmed by the orchestrator before commit.

## Known issues / open items

- `bracketed` line flag renders but no data populates it yet (neither Perseus
  nor TLG export carries modern athetesis brackets; TLG's Alexandrian sigla are
  Iliad-only and were left behind with the TLG source). Fast-follow candidate.
- Homepage copy still carries Plato branding (rebrand pass due in Phase 3).
- app vitest.config.ts has a pre-existing vite/vitest Plugin type mismatch
  (does not affect runs).

## Verification gates run

- **Murray/Butler alignment (Grok-4.5 content gate): PASS-WITH-ISSUES.**
  144 tick samples across all 48 books: 0 WRONG, 1 off-by-one-block; all 4
  documented anomaly resolutions and all 6 vulgate-gap boundaries verified
  honest against raw TEI; footnote markers 336/336 consistent. Defects found:
  B1 MAJOR (Butler terminal empty tick window in 34 books), M1 (~38 glued
  word pairs at milestone strips), M2/M5 minor — fix agent dispatched
  (in progress).

## John's review queue (accumulating; final list at handoff)

1. Greek-source copyright call: confirm Perseus fallback (Allen 1931 enters US
   PD in 2027 — optional future re-basing to the TLG text).
2. Odyssey Greek is the 1919 Loeb text, not the OCT — edition credits must say
   so (About page wording).
3. Autenrieth vs Cunliffe as the launch second-lexicon pane (data reality
   favors Cunliffe; PROMPT.md named Autenrieth). Cunliffe pane in build;
   Autenrieth fast-follow (partial scrape + RESUME.md in sources/autenrieth/;
   bulk download needs an unconstrained network — one-liner curl in the
   conversation log).
4. **Pope alignment verdict** (PROMPT queue item): shipped STANDALONE
   (book-level anchors only) per the written degrade rule — proportional
   anchoring drifted ~15% (~77 lines) on Il. 6 Hector/Andromache. Picker
   label says "alignment approximate"; confirm wording or change to
   "unaligned".
5. Murray's Loeb footnotes are bare citation numbers (no annotation prose
   survives in Perseus's TEI) — popup shows the number verbatim. Decide:
   drop the markers at launch, or fast-follow real Loeb notes from another
   PD source.
