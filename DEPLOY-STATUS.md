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

## Day-2 ledger, phone-review fix round (2026-07-18, ~13:00-14:00)

John's live phone review found six defects; all fixed, committed,
pushed, rebuilt, and re-verified the same hour:

- f834559 hero: horizon SVG hidden on the stacked mobile layout
  (preserveAspectRatio stretch artifact).
- fc315c1 reader: scene prose merged across alignment-chunk seams
  ("native land" mid-sentence fracture; Codex, failing-first repro).
- 9236e17 maps: numbered gap badges for unlocatable stations (silent
  9→11 jump; Nekyia #10 + Ogygia #15 now dashed-diamond badges with
  honesty popups; partition test 1-17).
- 41ba38c reader: speech-snap alignment (Il. 1.25/26 seed; 570 seams
  auto-fixed corpus-wide, audit in scratchpad), iOS sheet teleport to
  body (display:contents WebKit hazard; device confirmation pending),
  sheet scene-tracking arming.

build:public gate: PASS again (4713 pages, 0 broken, 48/48 scenes).
Preview refreshed. Open judgment calls for John: snap window 2 vs 1
(4/10 sampled 2-line snaps are partial fixes, none wrong-direction);
speeches-toggle dependency of the snap (pipeline precompute queued).

## Day-2 ledger, afternoon feature batch (2026-07-18, ~14:00-15:00)

Four John-directed features, Codex-implemented, orchestrator-reviewed:
- 2dab236 Catalogue of Ships section explorer (wide Troy-free framing,
  direct per-section city-pin swapping, unlocatable towns disclosed)
- 6e8bf65 contents rail book arguments (single Draft badge)
- 3191d11 scenemap land/sea tokens + 0.006-tolerance coastline (38.4KB;
  global.css drift logged); verified both themes post-build
- 2ff47a7 landing cards: line counts + arguments replace "0 chapters"
Plus 95a37f4 CLAUDE.md: Codex model-flag rejection gotcha (account
default model at --effort high is what actually runs).

build:public: PASS (4713 pages, 0 broken, 48/48 scenes). Preview
refreshed. Pending from John: iOS sheet pin confirmation on device;
snap-window and speeches-toggle judgment calls; render verdicts.

## Day-2 ledger, evening block (2026-07-18, John's live desktop review round)

John reviewed live and directed; every item landed same-session:
- bfa4d1a hero 50/50 + equal titles; 817af30 nav (12 sections,
  aria-current, Timeline discoverable) + hero moonlight seam mask
- 2788544 one-line desktop reader header, Contents/Scenes in nav rail
- 0f46062 Olympus gazetteer (verified refs; 37 divine scenes pin)
- 10ffe4f story-mode overhaul (zoom-banded labels, bottom-right dock
  card, badge-anchored uncertain legs through Nekyia/Ogygia) + Troad/
  Greece tab explainers
- aba6898 sentence-snapped scene pages (discovered + fixed boundary-
  chunk DUPLICATION; lossless partition invariant tested), honest
  Pope book-level notice (data: exactly 1 anchor/book, all 48),
  cartouche gap 52->24px
- 5ba7978 Sol adversarial fixes: speech-snap decoupled from the
  Speeches toggle (major), compare loading/error states, sheet
  aria-hidden+inert, CAWM/Natural Earth attribution

Sol whole-site review: 1 major + 3 minor, all fixed same-day;
verified-clean: footnote seams, XSS/regex, AA contrast, vulgate
integrity, honesty rules, payloads. Art: Flaxman greenlit; recolor
PoC + margin-panel/identity mocks delivered (scratchpad, mockup-gated);
Ogilby researched (verdict: highlights register, IA microfilm baseline).

FINAL GATE: build:public PASS - 4713 pages, 314,575 links, 0 broken,
48/48 scenes, Olympus in data root. Preview: 192.168.1.90:8090.
HEAD this block: 5ba7978 + this ledger commit; all pushed.

Awaiting John: Flaxman mock verdicts (A/B/C), Ogilby register decision,
"FOR GREECE MAP" note (cut off), iPhone sheet-pin confirmation,
domain/PR/deploy (standing).

## LAUNCH — 2026-07-18, evening (Day 2)

**LIVE: https://johnhboyer-sys.github.io/**

John: "Let's launch tonight." Sequence executed per docs/
LAUNCH-CHECKLIST.md: final build:public gate on the launch tree
(4,713 pages, 314,575 links, 0 broken, 48/48 scenes, canonicals/
sitemap on the live origin) -> PR #1 merged (John's order; 159
commits, claude/build -> main @ 7787ab0) -> repo renamed
johnhboyer-sys.github.io -> flipped public (John, via phone, after a
sign-in odyssey worthy of the subject matter) -> gh-pages orphan
published from the gated dist (+.nojekyll) -> Pages enabled
(gh-pages/root, HTTPS enforced) -> live at attempt 3 of polling.
Post-deploy live sweep: home, readers, maps, timeline, sitemap, data
root, and the Outis 404 all verified on the live URL.

URL decision: github.io user site tonight; custom domain may layer
later (config/site + CNAME + DNS, no rebuild of substance).
In flight at launch: Flaxman asset factory (art ships as the first
post-launch update on John's render verdict - his standing order:
"Then give me art").

## Post-launch repo split (2026-07-18, late)

John's call: source back under its own name. `homer-reader` (private)
recreated with full history — canonical source, remote `origin`. The
public `johnhboyer-sys.github.io` repo stripped to a stub README +
`gh-pages` (the served site) only — remote `deploy`. Site verified
live throughout.

## ART LIVE — 2026-07-18, night (second deploy)

John: "Then give me art." Shipped: 48/48 Flaxman book plates in the
reader cartouches (ink-masked, --flaxman-ink, ink A dark), distinct
hero motifs (Thetis / Sirens) behind the English-first titles, and the
og-default.png social card (Sirens on hero navy, polytonic epigraph).
Deployed to homer-reader gh-pages @ source 3d26b81e; verified live
(plate assets 200, plate markup in served HTML, og 200). Known
pre-existing headless-only cosmetic (cartouche meta clip) filed.

## POPE SCENE ALIGNMENT LIVE — 2026-07-21 (fourth deploy)

Ledger note: the third deploy (John, 2026-07-21 midday, gh-pages
aa1d70b0) shipped the merged post-launch PRs #2–#6 — palette temper,
scene-paging fixes (Murray+Butler corpus-verified), omega favicon,
John's boundary overrides — and predates this entry; recorded here
retroactively.

This deploy: Pope pages by scene. 742 curated scene-boundary anchors
(388 Il. + 354 Od.), AI-drafted per book, Grok-verified anchor-by-anchor
(19 boundary corrections), 2 boundaries Opus-adjudicated from the Greek;
stage1_pope resolver with hard-fail validation; preflight validates
third ticks + pope floors; corpus audit 144 books (documented
pope-specific ownership floor 0.565, binary gates all zero); Reader
curated-tick snap-skip + discreet approximate-alignment note; Codex
adversarial review (4 P1s fixed). PR #7 merged by John (ee3a6b5a).

Gate: pytest 364 · shared vitest 678 · app vitest · build:public
preflight 0 errors · 4,713 pages, 0/314,575 broken links · browser
smoke both themes. Deployed gh-pages 94db410c → origin (public
homer-reader repo serves /homer-reader/; the `deploy` remote
johnhboyer-sys.github.io serves only the root redirect). Live verified:
new Reader bundle 200 + served, notice string present, Il. 1 / Od. 9
200. John spot-checking post-deploy.

## LSJ GLOSS REPAIR LIVE — 2026-07-27 (fifth deploy)

PR #10 merged by John (a76e8e39) — the post-launch umbrella, 51 commits.
Lexicon work is what reaches the reader here.

The repair: Diogenes' greek-analyses.txt field 3 keeps only the FIRST
italic run of LSJ sense A, so word popups shipped truncated glosses.
Stage 5 now derives the whole leading italic run into
build/stage5/short_defs.json; stage 7's resolve_parses extends a gloss
only when the derived def starts with it on a word boundary. ~792 of
9,948 distinct lemma/gloss pairs repaired (8.0%) — ei)=mi "come" ->
"come or go", mh=lon "sheep" -> "sheep or goat".

Ordering correction, and it matters: the merge must run AFTER
filter_parses, which identifies junk readings by gloss-duplication on
RAW Morpheus glosses. The FOURTH deploy (source 6da11c3e) shipped the
repair WITHOUT this fix, so junk readings survived into primary
analyses and four spurious lemma pages were live. Corrected here: 7
lemma slugs move (charizomai->charizo, endyno->endyo, dyo-3 added;
epasso and sidereios were spurious and now 404). Anyone holding those
four URLs gets a 404 — the correct outcome, they were wrong pages.

Homonym guards (739b6cefc): merge_short_def refuses to extend when two
candidate LSJ entries disagree (was picking by list position), and
treats a candidate whose def EQUALS the gloss as proof Morpheus was
never truncated. The second fixes a wrong gloss that was live —
malo/s "white" was showing ma/los's "white-tailed". Extensions 792 ->
791; that single loss is the error itself. Zero correct extensions lost.
The ordering defect itself was confirmed UNREACHABLE on current data by
two independent counts, each reusing the real merge_short_def.

Gate: pytest 385 · build:public preflight ok · LSJ + Cunliffe keys all
resolve · 4,713 pages · 0/313,600 broken links, 148,627 anchors ·
48/48 books with scenes (790) · glosses spot-verified in emitted data.
Deployed gh-pages 41eb8385b -> origin. Live verified: Pages build
"built", / and Il. 1 and Od. 9 all 200, /lemma/charizo/ 200,
/lemma/charizomai/ and /lemma/epasso/ 404, "white-tailed" absent.

Known gap, not shipped: the popup renders one card per READING, but a
single reading carrying several LSJ homonym keys shows only the first
(LexiconPanel.svelte:134 reads a.lsj[0]). o(/s1/o(/s2 collapse into one
box. Splitting those into separate cards needs both a data and a
rendering change, and may retire the ambiguity guard above. Scoped,
not started.

## ADVERSARIAL REVIEW FIXES LIVE — 2026-07-27 (sixth deploy)

PR #12 merged by John (8928821d), 12 commits. A three-lane adversarial
review (reader/a11y, philology, engineering) plus follow-up verification
found four real defects; all four shipped fixed.

WRONG GREEK THAT WAS LIVE. Thirteen apparatus claims contradicted the
text while carrying status "reviewed": Polyphemus described as blinding
Odysseus's crew (reversed); Book 6's argument giving Hector the Glaucus
exchange that belongs to Diomedes; Penelope holding off the suitors
"twenty years" when Antinous dates them to the third going on fourth
(Od. 2.89-90); Leto gathering "her children's weapons" at Il. 21.505-511
when she gathers Artemis's bow at 21.502-504; Antilochus's self-sacrifice
cited to Od. 24.78-79, which mentions only his bones. Each corrected with
decisive Greek and audited by a second lane.

JUNK PRIMARY ANALYSES. Nothing in the pipeline ranked parses — Morpheus
emission order reached the reader. 9,175 token occurrences showed junk
first: ou) as "u", a)/n and ke as "he came", mh/ as "will", a)ndrw=n as
a)ndro/w "change into a man". Three ranking rules plus 28 curated
overrides. Zero previously-correct primaries changed; the 1,993 debatable
homonym keys deliberately untouched. Scope came from three independent
measurements (6,918 / 13,944 / 9,175) — the third reproduced the other
two and showed one missed morphological impossibilities while the other
counted debatable homonyms as defects.

Ten lemma pages now 404 — achaia, andris, androo, apeiroo, gynaikoo,
hoste-2, hyphe, katha, podoo, theao. They existed only because junk held
the primary slot. With the four from the fifth deploy, fourteen lemma
URLs have gone in one day, all correctly.

LEXICON. 159 glosses shipped literal <foreign> markup — from Diogenes'
source data, not from the LSJ repair as first assumed. Sanitized at
ingestion; extensions rose 791 -> 797 because the tags had been blocking
prefix matches. 736 empty glosses filled by following LSJ cross-
reference stubs one hop (du/w2 -> "two", pera/w2 -> "export for sale").
4,652 stay empty where no definition or clean pointer exists.

TWO GATES THAT COULD NOT FAIL. A build could silently delete six books of
curated scene apparatus and exit 0 — merge_staging accepted partial
coverage, run() overwrote the canonical file, preflight only checked what
remained. Now raises before the write; --allow-partial-apparatus is the
explicit opt-in. And every public build loaded the private manifest while
the private-content check short-circuited, because no <work>-public.yaml
exists; the check now asserts a positive public-domain allowlist and a
missing or empty allowlist is itself a failure.

Also live: a box per dictionary-level homonym in the word popup (PR #11),
1,462 analyses rendering as 3,061 cards over 890 token-keys.

Gate: pytest 403/404 (known xa/w gloss gap — its LSJ body is not a clean
cross-reference, so the code refuses to invent one; documented in PR #12)
· build:public preflight ok · LSJ + Cunliffe keys all resolve · 4,703
pages · 0/312,770 broken links, 148,137 anchors · 48/48 books with scenes
(790). Deployed gh-pages 9145cd016 -> origin. Live verified: Pages build
"built", / and Il. 1 and Od. 9 200, /lemma/aner/ 200, /lemma/androo/ and
/lemma/achaia/ 404, live data ou) -> "not" and a)ndrw=n -> a)nh/r "man".

LESSON. apparatus/scenes/<work>.json is DERIVED from apparatus/staging/.
Corrections written to it survive exactly until the next re-emit
regenerates the file. They belong in staging, which also subjects them to
schema validation — that caught a 16-word Book 6 argument against a
15-word cap that direct editing had waved through. The loose JSONs at
apparatus/ root (places.json, characters.json) are source, copied verbatim.

## SUPPORT FUNNEL LIVE — 2026-08-05 (seventh deploy)

PR #19 merged by John's order (be3d047c9): the donation funnel, end to
end, in one visual language. app/src/lib/support.ts now carries the live
Stripe Payment Link. og-support.png and og-default.png redrawn as the
black-figure galley — terracotta sail, bone linework, wave band, wine-dark
ground — matching the 1600px graphic John uploaded to the Stripe checkout
itself. Oars fully formed per John's review: shafts from under the hull,
blades in the water. SVG sources live in docs/ (og-support-card.html,
og-default-card.html, stripe-checkout-graphic.html); render via headless
Chrome (macOS system fonts: Big Caslon, Palatino, Iowan Old Style).

Deliberately narrow: cherry-picked support-funnel branch off main, so the
Chart Room and the unsigned citadel plate stayed on claude/build behind
John's sign-off gate. The deploy therefore also ships what main had
accumulated since the sixth deploy: advanced search (PR #13), cross-epic
phrases and dual-number search (PR #14), and the word-popup fixes (PRs
#17, #18). CORRECTION (same night): this entry first claimed the Troad
plates (PR #16) shipped here — false. PR #16 is still OPEN; the five
plates live only on claude/build. A stale session note ("PR #16 merged",
2026-07-29) propagated into the first draft of this entry.

Built in an isolated worktree (main + PR #19 only): own build/ (export
cache copied, 1.6M), venv symlinked read-only — the main checkout's
build/dist untouched with a second session active in it. Gate: pipeline
public build both works · preflight ok · LSJ + Cunliffe keys all resolve
· 4,705 pages · 0/331,431 broken links, 148,145 anchors. Deployed
gh-pages 350799e11 -> origin (source be3d047c9). Live verified: Pages
"built"; /, /support/, Il. 1, Od. 9 all 200; /support/ serves the live
payment link; both OG PNGs byte-identical to the reviewed renders.

Stripe-side, only John can fix: checkout header reads "Aristotle Reader"
(Settings -> Business -> Public business name) and the link description
is missing "is" ("The Homer Reader s free and open").
