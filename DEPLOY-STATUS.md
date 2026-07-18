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

- **Iliad re-based onto TLG Allen 1931** (2026-07-17, John's call +
  Allen-supplement ruling): line-set identity all 24 books, totals
  unchanged (15,687), Murray ticks byte-identical, preflight 0 errors.
  bracketed flag now live: 528 lines (524 Allen obeloi + Il. 8.548/
  550-552 supplied from the vulgate). Stage4 unparsed 0.075% (was
  0.04%). 8,648 Greek lines differ from the Perseus text (Allen
  orthography + genuine variants). PENDING before deploy: attribution
  page + works.ts still credit Monro-Allen/Perseus for the Iliad
  (queued behind the hydration-diagnosis lane).

- **Gate 4 PASSED** (2026-07-17, checked in main loop): 48/48 books
  carry scenes; maps render certainty tiers + legend; epithet and
  repetition stages green (29 tests); 2 crossBook speech spans, both
  flagged, rendered degraded. The gate CAUGHT a real regression: a
  stage-1..7 re-run (lemma fix lane) re-emitted all books WITHOUT
  re-running the apparatus merge, silently wiping scenes corpus-wide;
  restored by re-running the apparatus stage for both works and
  rebuilding. Preflight did not catch scene-less emits — hardening
  queued for Phase 6.

- **Gate 5 PASSED** (2026-07-17, checked in main loop): SSR text
  visible with JS disabled (611 Greek lines in static book-1 HTML;
  funnel/SEO pages full-content, per-lane JS-off Playwright);
  /start + About + 5 SEO landers live in dist; sitemap valid XML,
  4,703 urls incl. the new routes; robots gated on real domain (no
  placeholder origins). Search filters shipped (work/book/speaker/
  speeches-only) — including a pre-existing silent search-grouping
  bug fixed (empty chapters.json for verse-line works). Remaining
  Phase-5-adjacent: formula glosses (Opus drafting; Grok translation
  gate + UI wiring to follow).

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
- **Loeb real-notes extraction (two-cycle cross-model loop): high band
  SHIPPABLE** (2026-07-17). Grok extracted from first-printing scans
  (texts verified genuine, PD evidence recorded); Codex audit FAILED
  attachment v1 (14%/50%/89% wrong-locus by band); Sonnet re-attached
  deterministically (page running-heads + dual-page pairing); Grok
  audit v2: high 0/22 wrong-locus, medium 33%, low 90%. DECISION:
  ship confidence:high only (~187 notes) + internal-line-ref distance
  post-filter + drop pure app-crit strings; medium/low/null retained
  in sources for human review. Integration lane dispatched.
- **Formula glosses (Grok translation gate, two cycles): PASS**
  (2026-07-17). Opus drafted 1,152 glosses (compositional engine,
  consistency by construction); gate v1 PASS-WITH-FIXES (postpositive
  particle order ~50, mechanical doubles, long-tail case/apposition
  errors, 2 consistency divergences); Sonnet fixed 104 values (engine-
  level where systematic); gate v2: 30/30 fixed confirmed, 0 new
  errors, cores byte-identical, Ἆρες Ἆρες epanalepsis preserved; 5
  optional residuals polished by orchestrator. English glosses live
  under the Greek on /formulas/{iliad,odyssey}/ (draft-badged).
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

## John's decisions (2026-07-17, review-queue round 1)

1. **Iliad Greek re-bases to TLG Allen 1931** ("Allen ships") — John
   accepts the ~6-months-to-PD copyright posture; not launch-gating.
   Odyssey STAYS Perseus (TLG's Odyssey is von der Muehll 1962, in
   copyright for decades; the OCT Odyssey is not in TLG). Re-base lane
   dispatched with a hard line-set-identity gate before anything else.
2. Odyssey credit wording: draft shown to John (pending his edit).
1a. **Il. 8.548/550-552 ruling (John, 2026-07-17): Allen + supplement.**
   Allen 1931 omits the four "gods hated sacred Ilios" lines that the
   Perseus/OCT vulgate prints. Decision: ship Allen's text with the four
   lines supplied from the vulgate, rendered bracketed/athetized with
   recorded provenance — every vulgate line number stays citable; corpus
   total stays 15,687. Gate A also inventoried Allen's Alexandrian
   sigla (1,789 diplai / 411 obeloi / 290 dotted diplai / 69 asterisks);
   obelos maps to the bracketed flag, other sigla preserved as data only.

3. Pope: keep "alignment approximate" (drift is Pope's uneven couplet
   expansion, not an edition mismatch — not cheaply fixable).
4. Murray footnotes: REAL Loeb notes wanted — acquisition/extraction
   lane queued (PD Loeb scans -> note text -> join to markers).
5. Autenrieth: one-liner re-sent to John for an unconstrained network.
6. Catalogue coords + omitted Pleiades URIs: accepted for now,
   revisit during QA (Phase 6 item).
7. Contested-identification recordings (Oechalia single entry, Zeleia
   included): accepted as recorded.
8. Troop-total extrapolation: omitted from site data AND About;
   instead add a courtesy "see also" link to Mollick's
   catalogue-of-ships.netlify.app visualization (maps page).
9. Nav: wire in the Cmd/Ctrl-K "Go to..." palette (Treatment 3) in
   addition to the scene rail; book-grid stepper stays shelved.

## John's review queue (accumulating; final list at handoff)

0a. NEW: Apologoi nested-speech rendering — level-1 speeches recorded
   under a different book than their crossBook frame (most of Od. 10,
   all of Od. 12, pre-336 Nekyia) currently render as flagged markers,
   not rails (~40% of Odyssey level-1s). Extending containment across
   the two known frames would rail them; needs your call on whether
   that inference is philologically acceptable.
0. NEW: Il. 8.538-541 — TLG carries a bare Beta Code %11 bullet inside
   the line text (not the usual sigla markup) at a known Aristarchan
   athetesis locus. Currently preserved as data, NOT bracketed (obelos-
   only rule). Call: should 8.538-541 render athetized?

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

## Overnight build ledger (2026-07-17 night — John authorized autonomous build)

Standing order + held-decision queue: docs/OVERNIGHT.md. Landed tonight,
each commit pushed on landing (newest last):

- 201b19f Wanderings **Story mode** — 17 stations in Odysseus's telling
  order, route-as-hero, "Beyond the map's edge" strip (Cimmerians,
  Ogygia), Planctae excluded (never visited). Toggle persists (?story=1).
- 4ebd8fe **Genealogies drawn as real trees** (punch #3) — labels at
  node coordinates, 50 labels/43 connectors; list is now the AT/mobile
  fallback. (Grok implementation, independently verified.)
- 6060c87 **Hexameter scansion stage** — whole-corpus computed scansion
  with honest residue (79% high-confidence; ambiguous/unresolved marked,
  never faked). Found a real corpus quirk: Perseus Odyssey elision is
  U+02BC (phantom-consonant bug fixed; unresolved 23%→3%).
- 51c333b **/places/ gazetteer** — 274 places, certainty tiers, tradition
  lines, Pleiades links, 336 anchor citations deep-linking the reader
  (spot-verified: Abydos lands on the line naming Abydos). (Codex
  implementation + Sonnet taste pass.)
- af03e2f **ἐπ' αἶαν fixed** — epithet entity matching is lemma-aware;
  the 'earth' formulas are out of both Ajaxes (Iliad 877→873, Odyssey
  405→404, same-class corrections only).
- 2917a86 **Per-book vocabulary stage** — top-25 words per book,
  mechanical stoplist (corpus top-100) + proper-name exclusion, Morpheus
  one-line glosses (96.5%/97.7% coverage). Il. 1 surfaces γέρας.
- b4fc237 **/characters/ network** — kinship + speech edges from our
  data, seeded deterministic layout, SSR SVG; 96/100 linked figures
  shown, isolates + all exclusion counts stated on the page.
- 12d6d17 **Design Wave A** — Reading-Mode scene chips fixed (two-layer
  root cause), Wine-dark Homer OG cards replace the Plato ones,
  accent-color token on native controls, compact maps draft badge,
  Homeric search placeholders.

Also: Chamberlain audio recon complete — CC BY confirmed (3.0/4.0 split
per item), NO per-line timing exists anywhere in his corpus → shipping
"hear this passage" at his real chunk granularity, hotlinked from
archive.org (his own pattern); decision detail in docs/OVERNIGHT.md §8.

Superseded queue items above: #1 (Allen re-base LANDED, John's call
2026-07-17) and #5 (real Loeb notes SHIPPED, high-confidence band).

In flight at ledger-write time: vocabulary UI pages, audio manifest,
meter overlay in the reader; then Wave B design cohesion, audio player,
Phase 6 QA + Sol adversarial review + FINAL GATE.

## FINAL GATE — Od. 9.366 (Οὖτις) — PASS (2026-07-18 ~00:20, orchestrator-run, main loop)

Run against the production dist build (fresh, post-QA-fixes HEAD).
1. Jump box: palette resolves 9.366 → lands on ?loc=9.366. PASS
2. Deep link: line 366 scrolled + highlighted (Οὖτις ἐμοί γ' ὄνομα). PASS
3. Parse: Οὖτις → 'no one', masc nom sg; LSJ·Cunliffe·Logeion tabs. PASS
4. Translations: Murray (default) · Butler · Pope ('alignment
   approximate' wording as approved). PASS
5. Wanderings pin: Land of the Cyclopes, certainty traditional, deep
   link → Od. 9.106; Story mode station 6. PASS
6. Nested speech: Odysseus → Polyphemus rail wraps 364–366 inside the
   Apologoi; Polyphemus's replies railed around it. PASS
7. Scene summary: SCENES drawer draft-badged; active scene 345–374
   ('…gives his name as Noman'), scroll-tracked. PASS
Screenshots: session design board, final-gate/.

Gate-walk defects found (fix lane dispatched same hour): palette
rejects the work-prefixed form ('Od. 9.366') its placeholder
advertises; /maps/?map= param not applied on cold load; docked
lexicon intercepts clicks into the settings sidebar when both open.

## Adversarial review + QA sweep (Sol + metrics, 2026-07-18) — all
findings fixed or held

Fixed same night: check-links loc grammar (5,271 false failures —
links were fine, gate now 0 broken); Iliad credit misstatement
('Perseus, CC BY-SA' → 'Allen 1931 (licensed TLG export)'); 6
formula displays missing glosses (Opus, cited); vocab lemma links
(476/471→592/594 of 600, 0 dead); mobile reader toggle names (axe
critical → 0); cluster-badge keyboard access; FormulaLedger empty
gloss node; BASE fork drift.
Sol found NOTHING in: places citations (336/336 resolve), vulgate
exception handling, audio license labels, JSON-LD safety, XSS/regex
injection surface, forbidden-translation scan.
Metrics: Lighthouse home 97/100 mobile/desktop; new pages 97–100;
CLS = 0 everywhere (payload-strip promise holds); axe 0 violations
desktop+mobile after fixes; console clean.
HELD for John (docs/OVERNIGHT.md queue): reader book pages are
0.7–1.8MB SSR HTML (Lighthouse mobile 53–56 measured UNGZIPPED
locally; GH Pages gzip → ~150–250KB wire; cutting the duplicate
Reading-Mode English flow would save ~25% but trades against
SSR-complete deep links) — decision, not defect. Maps mobile 79.
WCAG 2.2 target-size on places/characters (2.2 is beyond the AA
commitment; noted).

## Day-2 ledger (2026-07-18, John-directed session — through compact point)

Morning text/nav round (all landed): Murray space-loss fixed at source
+ corpus re-emit; footnotes now 158 real markers, 0 empty; TOC books
are links; scene-paged Reading Mode (?scene=N, ?loc lands in-scene);
stacked Both view on phones; meter wraps (works all widths); one-row
mobile header; cartouche border fix; mobile genealogies = indented
descent charts (Astro scoping bug fixed); formula noise purged (71
demoted, 'If Achilles' class); Apologoi 'Day 34 · telling' cue + Od.
10/12 frame markers.

Sourced-scholarship apparatus (new standing policy in CLAUDE.md;
Chicago/hyperlink citations): chronology research both epics
(docs/research/); Iliad calendar recalibrated to traditional ~51 days
(Book 24 was miscounting via the nested nine-day quarrel);
/timeline/ page — day strips w/ hatched compressed spans, Day-34
telling inset, voyage strip Troy→Ithaca (all durations verified on
their Greek lines; stated spans sum ~8.3yr vs the asserted twentieth
year; two ref corrections incl. journeys' six-days ἑξῆμαρ fix);
apparatus/bibliography.json (21 entries).

Journeys: apparatus/journeys.json (4 nostoi, 37 legs, Grok-gated
PASS-WITH-FIXES — the Pharos→Sparta citation defect confirmed and
fixed by splitting per 4.581-586); 5 new places; Journeys map tab
(curved arcs, CVD-safe color+dash, honest gap stubs, Ithaca arrival;
Odysseus tail added to Wanderings). Wanderings audit: 32 stations
verified; Ogygia rival tradition → John's queue.

Context panel (John's picks: B plates / A rail-toggle / C sheet):
scenemap SVG foundation (Natural Earth PD, 34.7KB, 27 tests);
Variant B figure plates LIVE in Reading Mode (honest place resolver —
no invented plate titles; Scholar loads zero bytes of it). A-rail +
C-sheet queued. Art survey done (Flaxman = our Doré; licensing
verdicts in docs/research/art-illustrations.md) — mockup-gated.

Also: Οὖτις 404. IN FLIGHT at compact: map timelines + animated
step-by-step playthrough lane. QUEUED: A-rail, C-sheet, full rebuild +
fresh preview + screenshot sweep. John's open queue: Ogygia tier,
domain, PR/main, deploy, Wilson jokes stay off-site.

## Day-2 ledger, afternoon (2026-07-18, post-compact through preview restart)

Usage rebalance in force (John): implementation to Codex/Grok, Claude for
verification + philology. Commits this block, all pushed:

- a467021 places: Pylos (Strabo 8.3.7 three-Pylos dispute) + Scheria
  (Thuc. 1.25.4 reworded to the Corcyraeans' own boast) — first per-place
  `sources` citation arrays. Grok-implemented, orchestrator-verified.
- 41f3966 maps: duration chips (Greek-cited, chip table verified against
  raw lines) + Story-mode animated playthrough (play/pause/step, reduced-
  motion honest, unlocatable legs stay stubs). Sonnet lane; Grok gate
  caught a rough-for-smooth breathing on ὀγδοάτῳ pre-commit.
- f3a579c reader: Chart Room rail (Scholar desktop, toggled, persisted) +
  mobile scene-context bottom sheet (both views; B-plate map yields on
  mobile). Codex-implemented; Sonnet verify: 484/484, a11y, lazy-load
  honesty (gazetteer fetched only on first panel open).
- e749ab5 reader: scene-tracking arms from Chart Room; conditional
  aria-controls (verification nits).
- 99e685a scene-place: THE BIG ONE. Grok audit proved the mention-based
  resolver wrong for 385/592 resolutions (speech hijack: Phthia for the
  Il. 1 assembly, Thymbra for all of Il. 10, Lotus-eaters for all of
  Od. 23). Rewritten around the scenes' authored location prose (94-entry
  curated dictionary, book-scoped + line-spanned rules with explicit-null
  verdicts), journey-leg fallback, Olympus guard, no establishing
  fallback. Independent Grok re-audit: 733/790 resolved, 0 confidently
  wrong, 57 honest nulls; its one finding (post-Thrinacia wreck pinned to
  Sirens) fixed + regression-tested. 492/492.

build:public gate: PASS (4713 pages, 221,467 links, 0 broken;
48/48 books carry apparatus.scenes). Preview restarted: 192.168.1.90:8090.

Queued, non-blocking: Olympus gazetteer entry (37 divine scenes now
honest-null, would gain a pin); panel full-mock fidelity build-out
(place-name headline, citation line, cast chips) — John's call; art
vendoring pending John's B-plates render verdict.
