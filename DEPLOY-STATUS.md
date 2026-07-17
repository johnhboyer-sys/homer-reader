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
- **Gate 3 PASSED** (2026-07-17, checked in main loop): axe 0
  serious/critical both themes (/ and book page); AA both themes;
  Lighthouse /iliad/book/1/ mobile 90 (median of 3, stable), desktop
  100, CLS 0.000. Two Opus perf lanes: delegated token events (~7000
  per-token listeners -> 1 handler; longest task 1250ms -> 75ms) then
  island-prop stripping with DOM token reconstruction (book-1 HTML
  gzip 216KB -> 138KB). Reading Mode, scene chips + draft badges,
  lexicon, deep links, translation switch, compare all verified on the
  built site. Remaining Phase-3-adjacent work tracked separately:
  homepage implementation (Wine-dark token swap), in-book nav (mocks
  with John).

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
- **Odyssey scenes apparatus (Grok-4.5 content gate): PASS-WITH-FIXES**,
  fixes applied (Od.1 ὀτρύνομεν cohortative, Od.7 span, 5 minors) and
  merged to apparatus/scenes/odyssey.json.
- **Iliad scenes apparatus (Grok-4.5 content gate): FAIL** (2026-07-17).
  Concentrated defects: Bk 16 (Patroclus death sequence scenes shifted/
  misattributed), Bk 17 (scene [11] credits Automedon with Aretus — the
  kill is Menelaus→Podes), Bk 6 (Hector–Andromache farewell climax
  swapped across scenes 13–15); plus Bk 1 [3] nine-days boundary, Bk 12
  [6] boundary, Bk 23 [4] location, and a day-calendar ruling (divine
  scenes synchronized with battle action take the battle day; null only
  for proems/elisions/unpinned spans). Evidence: scratchpad
  scenes-verify/findings.md. Sonnet fix lane dispatched; Grok re-verifies
  Bks 6/16/17 before the gate flips.
- **characters.json + places.json (Grok-4.5 content gate): PASS** after
  one fix cycle (2026-07-17). First pass: places PASS-WITH-FIXES (3 tier
  corrections incl. Ithaca certain->traditional, Same unfused from the
  Cephallenian ethnonym), characters FAIL (Hesione presented as Homeric;
  7 majors incl. a note contradicting Od. 4.518; 5 epithet minors). All
  fixed with corpus evidence; nonHomeric genealogy-flag convention added
  to the schema; targeted Grok re-check confirms every item. Note: the
  fixer overturned one gate claim with evidence (Aeacus's Zeus paternity
  is Homeric, Il. 21.189) and Grok independently confirmed.
- **Catalogue of Ships (Grok-4.5 content gate): PASS-WITH-FIXES ->
  fixed** (2026-07-17). All 29 Achaean ship counts verified against
  Greek numerals (fleet total 1,186 = traditional count); spans tile
  exactly; leader traps (Phocians, two Ajaxes, Protesilaus/Philoctetes
  replacements) all correct; 60-toponym stratified sample + full
  237-entry scan: 0 false citations; 8 homonym pairs genuine. Fixes
  applied in main loop: pelion +Il.2.757, peneius-river +2.753/757
  mentions (Greek-verified). Trojans contingent keeps places:["troy"]
  as muster-point per schema (2.816 has ethnic Τρωσί, and places.json
  troy claims no Il.2 mention — nothing false to fix).
- **Iliad scenes apparatus re-gate: PASS** (2026-07-17). Sonnet fix pass
  corrected all blockers plus wider unsampled cascade members in Bks
  16/17 (Greek-cited); Grok exhaustive re-verify of Bks 6/16/17 (51
  scenes, every scene) found 2 residual defects (16[4] stale Bk-17
  duplicate; 17[8] "fights on"), orchestrator-fixed with line evidence,
  Grok re-checked both: OK. Tiling/lineation confirmed untouched
  throughout. Both epics' scenes now verified (790 scenes total).

## Trademark decision (2026-07-17)

Research (Sonnet, sourced; not legal advice): "Landmark" is a live series
brand of Penguin Random House/Pantheon (continuous use since 1996; Random
House "Landmark Books" lineage since 1950). Masthead use = medium-high risk;
descriptive attributed prose = low (nominative fair use); structural
inspiration = none. **Applied: "Digital Landmark Edition" removed from all
user-facing chrome** (replaced with "The Iliad & Odyssey · Greek and
English"); the word appears publicly only in attributed About-page prose
("in the tradition of Robert Strassler's Landmark editions"). USPTO
registration status could not be confirmed by automated search (tools
blocked) — if certainty is wanted pre-launch, a human clearance search is
the step. "Digital Landmark Homer" remains internal-docs-only vocabulary.

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
