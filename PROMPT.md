# BUILD: The Homer Reader — one-shot brief

John triggers this by saying **GO**. This file is the complete brief. `CLAUDE.md`
(this folder) is binding — hard rules, fleet rules (5-agent cap; subagents are
Opus/Sonnet/Codex only; no Fable subagents without John's say-so; Grok offline
until ~2026-07-24), orchestration discipline, and Karpathy rules all apply to you
and to every brief you write. `homer-reader-plan-2026-07-17.md` is background
reading; where it conflicts with this file or CLAUDE.md, this file and CLAUDE.md
win (notably: **no Cloudflare/R2 — this is a one-off GitHub Pages build**).

## Mission

Build **The Homer Reader** in this folder (`~/Developer/homer-reader`): a
Greek/English parallel digital edition of the Iliad and Odyssey with
Landmark-style apparatus — the digital Landmark Homer, which never existed in
print (Strassler's series skipped Homer). Nolan's *Odyssey* film opened
2026-07-17; this site is the movie audience's scholarly on-ramp AND a classicist's
daily driver. Work autonomously through the phases; each has an exit gate — never
improvise past a failed gate, apply the written degrade rule instead.

## Setup facts

- This folder already contains CLAUDE.md, this PROMPT.md, and the plan doc. Keep
  them; they're part of the repo. `git init` here (fresh history). Creating the
  GitHub remote and first push: ask John. Deploying: John's explicit go-ahead
  only.
- Sibling repos (`~/Developer/plato-reader`, `~/Developer/classical-philosophy-
  reader`, `~/Developer/aristotle-reader`) are **read-only**. A build session may
  be running in classical-philosophy-reader — do not touch that repo, only read.
- Greek source: local TLG via Diogenes with the patched `-y` verse export. Corpora
  location and export recipes: see the siblings' docs (aristotle's
  `docs/tlg-phi-export.md` equivalent). TLG source text is never committed.
- `nvm use 22` before any npm/vitest/astro command (system node is likely v24,
  outside the engines range — sibling gotcha).

## PHASE 0 — Recon & unknown verification (no code)

Read, in order (delegate the bulk reading per CLAUDE.md context discipline):
plato-reader (CLAUDE.md, `shared/lib/citation.ts`, `speakers.ts`, pipeline,
`docs/diogenes-xml-export-y.patch`), classical-philosophy-reader (verse machinery
state, scheme registry), aristotle-reader (ADDING-A-WORK.md, gh-pages incremental
deploy recipe, PR #17-era security fixes in shared code). Then verify each
unknown and write `docs/PHASE0-FINDINGS.md`:

a. TLG 0012 edition + lineation quirks (sample-export Il. 1 and Od. 1; check
   bracketed/athetized lines, numbering gaps). If the TLG text's editorial
   provenance is problematic (West-derived), FALLBACK: Perseus PD Allen/
   Monro-Allen TEI as Greek source (write a stage-1 TEI reader instead).
b. Perseus Murray TEI (Il. + Od. English): record milestone granularity
   (per-line or per-card ~5 lines). This decides Murray alignment cost.
c. Autenrieth TEI from Perseus: confirm availability; plan native bake-in.
d. Cunliffe: search ≤30 min for open digitized data; if none, mark fast-follow
   (Autenrieth carries launch).
e. Morpheus coverage: stage-4 targeted scan on the Il. 1 sample; report
   unparsed-token rate. If >8%, add Homeric lookup-variants (movable nu, apocope,
   tmesis parts, uncontracted forms) analogous to `beta.lookup_variants`.
f. DICES speech-span data: license + Homer coverage. If unusable, plan the
   speech-formula-detection route.
g. AWMC/CAWM ancient-world map tiles: working tile URL + CC-BY terms confirmed;
   else pick a modern-label-free terrain fallback.

GATE 0: findings doc exists; a Greek sample renders 24 lines of Il. 1 with
correct vulgate numbers; the chosen Greek-source path is committed to in writing.

## PHASE 1 — Repo bootstrap

Fork plato-reader's code in (fresh git history, `homer_pipeline` package rename;
start `DRIFT.md` immediately). Strip Plato works/data. Register scheme
`verse-line` (container=book, unit=line; renders "Il. 1.1" / "Od. 9.366"; jump
box accepts "9.366", "Od. 9.366", "od 9 366"). Works registry: iliad, odyssey
(24 books each; book = the chapter machinery; author "Homer"). Copy Citation
emits "Hom. Il. 1.1, trans. Murray". Port the newest verse rendering from
classical-philosophy-reader per Phase 0: line-per-line, hanging indent on
runover, gutter numbers every 5, athetized lines marked with brackets + legend.

GATE 1: `npm run dev` serves Il. 1 Greek-only end-to-end from the pipeline.

## PHASE 2 — Corpus pipeline

Full Greek export (48 books) → tokenize → morphology (with any Phase-0e Homeric
lookup-variants) → shared deduplicated LSJ shards (aristotle pattern) +
Autenrieth as a second native lexicon pane (LSJ | Autenrieth tabs; Logeion
external-link row per the dictionaries plan). Translations:

- **Murray** (Loeb: Od. 1919, Il. 1924–25; PD): ingest from Perseus TEI, align
  via its milestones; attribute Perseus.
- **Butler** (1898/1900): Gutenberg prose → gloss-based aligner (aristotle's) at
  ~5-line tick granularity. Verifier: every book covered, ticks monotonic.
- **Pope** (1715–26): Gutenberg → coarse anchors at speech/paragraph level;
  display Pope's own couplet numbering; picker labels it "literary translation —
  alignment approximate"; translation note discloses Broome/Fenton co-authorship
  of the Odyssey. DEGRADE: if coarse alignment is poor, ship Pope unaligned as a
  standalone reading text — never block launch on him.

Murray's and Butler's notes → footnote popup machinery.

GATE 2: data-preflight 0 errors; Od. 9.105–115 (Cyclopes) shows Greek + all
three translations correctly aligned; unparsed-token rate recorded in
DEPLOY-STATUS.md.

## PHASE 3 — Reader + the Aegean skin

Design tokens FIRST (CSS custom properties over inherited components — the skin
must revert by variable swap): "Aegean" palette (wine-dark sea, bronze,
terracotta, bone); night mode = "night sailing" (deep indigo/bone/bronze);
display serif for titles + drop caps; a Greek face suited to extended verse;
meander/wave-band rules sparingly; abstracted vase-silhouette motifs ONLY on
book-opening plates and empty states. Two postures:

- **Scholar view**: inherited parallel columns + full apparatus.
- **READING MODE** (new; keystroke `r`): single column, generous measure, one
  translation, marginal scene summaries, subtle place/person markers, nothing
  else. This is the flagship UX.

Book-opening plates: book number, one-line argument, where/who/day strip, map
thumbnail. Perf: reading view interactive <1s mid-mobile; zero blocking font
requests (font-display: swap).

GATE 3: axe-core clean; AA contrast both themes; Lighthouse perf ≥90 on a book
page; both postures × both themes screenshotted to docs/ (screenshots are
documentation here, not verification — functional checks still required).

## PHASE 4 — Landmark apparatus

Data-schema-first; ALL authored content is AI-drafted with `status: "draft"` +
UI draft badge; fan out per CLAUDE.md (batches of ~5 books; drafting agent never
verifies its own book; schema validation before merge).

4a. `scenes.json` per book `{lineRange, summary ≤20 words, location, dayNumber}`
    → marginal running summaries (gutter machinery), book headers, and a Timeline
    page: Iliad day-calendar; Odyssey told-order vs story-order double-track
    diagram (Apologoi Books 9–12 as flashback links).
4b. `places.json` keyed to Pleiades IDs with certainty tiers
    (certain | traditional | speculative | mythical; traditional identifications
    name their tradition; never invent one). Four Leaflet maps: **Catalogue of
    Ships explorer** (Il. 2.494–759 — every contingent a pin → card with
    leaders/ships/places/jump-to-lines), **the Troad**, **the Wanderings**
    (tier-labeled; Eratosthenes' bag-of-winds quip in the intro note), **Real
    Greece of the poems**. Place tokens in text → map panel zoomed to pin.
4c. `characters.json` + four genealogy trees (Atreus, Aeacus, Troy, Olympians) +
    character pages with mention concordance.
4d. COMPUTED (pipeline stages with tests, no authoring): epithet explorer
    (noun-epithet formulas per named entity from the lemmatized text, counts +
    line refs) and repeated-line/formula finder (exact lines + 4-word+ n-grams
    occurring ≥2×, cross-epic).
4e. Speech spans (DICES if Phase 0f cleared it, else formula detection + AI pass,
    review-flagged): speaker/addressee per span; nesting flagged (the Apologoi
    are narrative-within-speech — do NOT paint Od. 9–12 as one Odysseus speech);
    turn-flow coloring in the reader + speaker filter in search. DEGRADE: ship
    coloring only for high-confidence spans.

GATE 4: every book has scenes data (drafts OK); maps render with correct tier
labels; epithet + repetition stages pass their tests; no speech span crosses a
book boundary unflagged.

## PHASE 5 — Search, funnel, SEO

Search inherited; add filters: work, book, speaker, "speeches only" toggle.
Start Here funnel (`/start`): three doors — "New to Homer" (→ Od. 9 in Reading
Mode), "Reading along in Greek" (→ scholar view + a 5-minute parse-popup tour),
"Just the maps" (→ map index). SSR all reader pages (inherited); landing pages
for high-intent queries ("read the Odyssey online free", "the Odyssey in Greek
and English", "Catalogue of Ships map"); sitemap + robots + canonicals gated on
the real domain per sibling discipline (don't bake a placeholder origin). About
page: every PD source credited, the draft-apparatus disclosure, the Lyceum, one
tasteful line about this being a good year to read Homer. **No movie branding.**

GATE 5: SSR text visible with JS disabled; funnel pages live; sitemap valid.

## PHASE 6 — QA + handoff (no deploy)

Test suite green (port plato's; add: vulgate-numbering verifier, alignment
coverage, scheme round-trip, epithet/repetition determinism). data-preflight 0
errors. Production build (`npm run build`) green and served locally for
functional verification. Adversarial review pass per CLAUDE.md routing (Codex
Sol reviewing Claude-written work) before John's gate. Write:

- `DEPLOY-STATUS.md`: what shipped, what's draft, unparsed rate, known issues,
  John's review queue (apparatus books in draft, Pope alignment verdict,
  speech-confidence threshold).
- `docs/LAUNCH-CHECKLIST.md` (human steps): create GitHub repo + first push
  (John-gated), enable GH Pages, Search Console, domain/CNAME decision, outreach
  list (r/classics, r/AncientGreek, Sententiae Antiquae, classics blogs).

FINAL GATE (functional, on the local production build): **Od. 9.366 — Οὖτις,
"Nobody"** — reachable by jump box; correctly parsed on click;
Murray/Butler/Pope switchable; pinned on the Wanderings map; inside a colored
Odysseus speech span (nesting-flagged); with a draft-badged marginal summary.
That single line exercises the whole machine.

## REPORT BACK

End with: DEPLOY-STATUS summary, Phase 0 findings that changed the plan,
DRIFT.md contents, the review queue, and the top 5 items needing John's
judgment. Then stop — the GitHub push and deploy are John's calls.
