# The Homer Reader — Planning Doc + One-Shot Build Prompt

**Date:** 2026-07-17 · **Occasion:** Nolan's *The Odyssey* opens **today**; the interest window runs through the IMAX run, home release, and awards season (~6–9 months), but the SEO race starts this week. · **Product:** *The Homer Reader* — a standalone digital Landmark-style edition of the Iliad and Odyssey, Greek/English parallel, hosted at the Lyceum.

**The positioning insight:** Strassler's Landmark series (Herodotus, Thucydides, Xenophon, Arrian, Caesar, Polybius) **never did Homer**. Nobody has: Perseus/Scaife is a research tool, the Chicago Homer is aging infrastructure with licensed translations, and no site pairs the Greek with Landmark-grade apparatus — maps keyed to the text, marginal summaries, timelines, genealogies. This is a gap, not an imitation.

---

## 1. Decisions locked (this session, 2026-07-17)

| Decision | Call |
|---|---|
| Codebase | **Fork plato-reader** (newest shared core: citation contract, turn-flow, a11y/search fixes) **borrowing verse machinery from classical-philosophy-reader** as needed |
| Repo | New: `homer-reader` |
| Brand | **The Homer Reader**, standalone, Lyceum-hosted (e.g. `homer.lyceum.institute` CNAME later); Cloudflare Pages + R2 per the 2026-07-15 hosting decision; build/iterate on `*.pages.dev` staging |
| Works | Iliad + Odyssey (Homeric Hymns / Batrachomyomachia / Hesiod are fast-follows — Evelyn-White's 1914 Loeb is PD and covers all of them) |
| Translations | **Murray + Butler + Pope** per epic (3 slots, like NE) |
| Supplements in the one-shot | **All four**: maps · marginal argument + timeline · people/gods/epithets · speech attribution |
| Apparatus authorship | **AI-drafted, John reviews** — every apparatus datum carries `status: draft \| reviewed`; unreviewed items ship with a discreet "draft" badge |
| Movie tie-in | **Tasteful funnel** — no movie branding; a "New to Homer? Start here" path, SEO pages for high-intent queries, an About line noting the moment |
| Design | **Distinctive and reading-first** — snazzier than the restrained Aristotle/Plato look, without sacrificing parse popups, parallel columns, or search (design brief in §6) |

---

## 2. Architecture reuse map (what's free, what's new)

### Free (inherited from plato-reader / siblings)

Bilingual parallel reader + view toggles · clickable-word morphology + LSJ popup with concordance · citation-scheme registry contract (`scheme.py` + `citation.ts`) · translation slots with picker + footnote popups · unified search (lemma/form/English, Beta Code input, filters, CSV export) · settings sidebar, night mode, mobile reader, print CSS · SSR/SEO machinery, sitemap, feedback modal · copyright gating pattern · manifest-driven pipeline, gloss-based aligner, verifier passes · turn-flow/speakers machinery (Plato) → Homeric speeches · Diogenes `-y` verse-export patch (documented in plato-reader docs; classical-philosophy-reader has newer verse work — borrow it).

### New (the real work)

1. **`verse-line` citation scheme** — "Il. 1.1" / "Od. 9.366". *Simpler than Bekker*: the physical line is the citation unit; no character-offset floating. Gutter numbers every 5 lines; jump box; URL hash per line.
2. **Verse rendering** — line-per-line Greek with hanging indent for runover; athetized/bracketed lines visually marked; vulgate numbering preserved verbatim (including gaps where lines are omitted by the edition — never renumber).
3. **The four supplements** (§5) — maps, margins/timeline, people/epithets, speeches. Two of the four are *computed* (epithets, repeated lines), not authored.
4. **The design skin** (§6).
5. **Pope alignment** — loose Augustan verse; coarse anchors (speech/paragraph granularity), disclosed honestly in the picker ("literary translation; alignment approximate").

### Scale check

Iliad ≈ 15,693 lines; Odyssey ≈ 12,110. Two works vs. Aristotle's 29 — the corpus is *small*. The shared-LSJ dedup pattern carries over; site should land well under Aristotle's 368 MB. No hosting pressure.

---

## 3. Corpus and copyright table

| Asset | Source | Status |
|---|---|---|
| Greek text | TLG 0012 via local Diogenes export | Same posture as siblings (served, never committed). **Pre-flight: verify which edition TLG uses** (Allen OCT = PD; if any West-derived text, check posture — West's editorial text is in copyright) |
| Murray, *Odyssey* (Loeb 1919) + *Iliad* (Loeb 1924–25) | Perseus TEI (has book/line milestones — likely pre-aligned) or archive.org | **PD** ✓ — the scholarly, line-keyed slot. Note: Perseus's TEI *encoding* is CC-BY-SA; underlying text PD — attribute Perseus, or re-key from scans if that rankles |
| Butler, *Iliad* (1898) / *Odyssey* (1900) | Project Gutenberg | **PD** ✓ — readable prose; gloss-based aligner (exists) |
| Pope, *Iliad* (1715–20) / *Odyssey* (1725–26) | Gutenberg | **PD** ✓ — disclose that Broome & Fenton translated ~half the Odyssey's books |
| Autenrieth, *A Homeric Dictionary* | Perseus TEI | **PD** ✓ — bake native beside LSJ; the student's Homer lexicon |
| Cunliffe, *Lexicon of the Homeric Dialect* (1924) | PD since 2020; open digitization to verify (Logeion has it; open data uncertain) | The **Bonitz-equivalent marquee** for Homer. If no open data: OCR pipeline fast-follow, exactly like Bonitz |
| Morphology | Diogenes `greek-analyses.txt` (Morpheus) | Built for Perseus, which serves Homer — coverage should be good; **measure unparsed-token rate** and report |
| Places | Pleiades gazetteer (**CC-BY**), ToposText (CC-BY) | Open ✓ |
| Basemap tiles | AWMC / CAWM ancient-world tiles (CC-BY) — terrain, no modern labels | Open ✓; fallback: plain Esri/Stamen terrain |
| Speeches | DICES (Digital Corpus of Epic Speeches) — open scholarly dataset covering Homer | **Verify license + coverage**; fallback: compute from speech-formula detection + AI pass with review flags |
| Off-limits | Lattimore, Fitzgerald, Fagles, Lombardo, **Wilson**, West's editorial matter, Landmark content itself | All in copyright. T. E. Lawrence's Odyssey (1932) unlocks **Jan 1, 2028** — standing note |

Fast-follow PD bench: Butcher & Lang (Od. 1879), Lang-Leaf-Myers (Il. 1883), Chapman, Cowper, Derby, Bryant, Morris, Palmer.

---

## 4. Why this wins (competitive frame)

Perseus/Scaife: superb data, research-tool UX, no apparatus, no narrative on-ramp. Chicago Homer: great lemma data, 2000s-era frames UI. Print Landmark: doesn't exist for Homer; print Loebs: $30/volume × 5. **Nobody serves the person who walks out of the Nolan film wanting to actually read the thing** — let alone read it with the Greek, a map of the wanderings, and "who is this person again?" answered in one click. The Homer Reader is simultaneously the movie-goer's on-ramp and the grad student's daily driver. That dual audience is the same one the Landmark series captured in print.

---

## 5. The four supplements (design sketches)

### 5.1 Maps layer — the Landmark-defining feature

Leaflet + AWMC/CAWM ancient-terrain tiles + a `places.json` gazetteer keyed to Pleiades IDs. Every place carries a **certainty tier**: `certain` (Troy, Pylos, Mycenae) / `traditional` (Djerba = Lotus-eaters, Strait of Messina = Scylla) / `speculative` / `mythical` (Ogygia, Scheria, the Underworld). The honesty tiers ARE the scholarship — a classicist's map never pretends Circe has coordinates.

Four curated maps: **① Catalogue of Ships explorer** (Il. 2.494–759: all 29 Achaean contingents + the Trojan catalogue — pin → contingent card: leaders, ships, places, jump-to-lines; this is the single most Landmark-ish artifact possible), **② the Troad** (battlefield close-map: city, ships, rivers Scamander/Simoeis, Ida), **③ the Wanderings** (Troy → Ithaca route with tier-labeled pins and the great disclaimer done charmingly — Eratosthenes' quip that you'll map Odysseus' route when you find the cobbler who sewed the bag of winds), **④ the Real Greece of the poems** (Ithaca, Pylos, Sparta, Mycenae, plus Odyssey's Mediterranean rim). Place-name tokens in the reading text get a subtle marker; click → map panel zoomed to that pin.

### 5.2 Marginal argument + timeline

A `scenes.json` per book: `{lineRange, summary ≤ 20 words, location, dayNumber, speakerContext}`. Rendered as (a) Strassler-style **running marginal summaries** in the reader gutter (the Bekker-margin machinery repurposed), (b) **book headers** with where/who/day, (c) a **timeline page**: the Iliad's day-calendar (~51 days, four great battle days) and the Odyssey's **told-order vs. story-order diagram** — the in-medias-res structure and the Apologoi flashback (Books 9–12) visualized as two parallel tracks with crossing links. Nolan is reportedly playing with structure; the audience primed for that will *love* seeing Homer did it first.

### 5.3 People, gods & epithets

`characters.json`: names (Greek + English), patronymics, epithets, faction (Achaean/Trojan/Olympian/Ithacan…), relationships. Four genealogy trees: House of Atreus, line of Aeacus (→ Achilles), Trojan royal house, the Olympians. Character pages with every mention linked.

Two **computed** features (pipeline stages, zero authoring):
- **Epithet explorer**: from the lemmatized text, extract noun-epithet formulas per named entity with counts and line refs — πολύτροπος, πόδας ὠκύς, γλαυκῶπις, ῥοδοδάκτυλος — the oral-formulaic system made browsable.
- **Repeated-line finder**: exact repeated lines and 4+-word formulas across both epics with counts ("and rosy-fingered Dawn appeared" × N). No print edition can do this; it teaches Parry's insight by direct experience.

### 5.4 Speech attribution

≈45% of Homer is direct speech. Reuse Plato's turn-flow/speakers machinery: speech spans (`book.line` ranges, speaker, addressee) drive subtle speaker coloring/labels in the reader, a speaker filter in search ("all of Achilles' speeches", "every Athena–Odysseus exchange"). Data: DICES if license permits; else compute from Homeric speech-introduction formulas (τὸν δ' ἀπαμειβόμενος προσέφη…) + AI pass, review-flagged.

---

## 6. Design brief — "distinctive and reading-first"

The Aristotle/Plato readers are deliberately restrained critical editions. The Homer Reader should feel like a **beautiful book**, not a database — the difference between an OCT and a Folio Society edition, while keeping every scholarly control.

- **Two reading postures, one reader.** (a) **Scholar view** — the inherited parallel columns, parse popups, full apparatus. (b) **Reading mode** — a single-column, generous-measure immersive view (one translation, marginal summaries, place/person markers, nothing else), one keystroke away. Reading mode is the movie-audience on-ramp *and* what makes the design feel different; scholar view is why classicists stay.
- **Visual identity**: an "Aegean" palette — wine-dark sea, bronze, terracotta, bone — drawn from black-/red-figure vase conventions but abstracted (thin meander/wave-band rules, silhouette figure motifs on book-opening pages and empty states), never theme-park. Night mode as "night sailing": deep indigo, bone text, bronze accents.
- **Typography does the heavy lifting**: a real display serif for titles and drop-caps at book openings; a Greek face chosen for extended verse reading; comfortable default measure and leading tuned for poetry (hanging indents, line numbers whispering in the gutter, not shouting).
- **Book openings as moments**: each of the 48 books opens with a header "plate" — book number, one-line argument, where/who/day strip, and the relevant map thumbnail — the digital equivalent of Landmark's running headers.
- **Motion, sparingly**: soft transitions on book/map navigation; nothing that slows a reader down. Performance budget: reading view interactive < 1s on mid mobile.
- **Hard constraint**: WCAG AA contrast throughout (the a11y round from plato-reader is inherited — don't regress it for aesthetics).

---

## 7. Unknowns ledger

**Resolved this session:** codebase (fork plato + borrow verse) · supplements scope (all four) · translations (Murray/Butler/Pope) · brand (The Homer Reader) · apparatus authorship (AI-draft + review flags) · movie posture (tasteful funnel) · design direction (§6).

**Known unknowns — the prompt's Phase 0 verifies each (with fallbacks):**

1. **Which edition TLG 0012 uses** (Allen OCT vs. West-derived) and its lineation quirks — athetized lines, plus-lines, numbering gaps. *Fallback if posture-problematic: Perseus's PD Allen/Monro-Allen TEI as the Greek source (different stage-1 reader, same downstream).*
2. **Perseus Murray TEI granularity** — per-line milestones or per-"card" (~5 lines)? Either works; determines whether Murray alignment is free or near-free.
3. **Cunliffe open data** — exists? If not: OCR fast-follow (Bonitz pattern); Autenrieth carries the Homeric-lexicon load at launch.
4. **Morpheus coverage of Homeric forms** — measure unparsed rate; epic forms, tmesis, ephelcystic-nu variants may need lookup-variant logic (the Homeric analogue of Latin enclitic splitting).
5. **DICES license + coverage** for speech spans; fallback is formula-detection + AI pass.
6. **AWMC/CAWM tile service status + terms**; fallback plain terrain tiles.
7. **Where classical-philosophy-reader's verse machinery lives** and its state (John: "that project has built stuff to deal with verse") — Phase 0 reads that repo before writing any verse code.
8. **Pope's own line numbers** (≠ Greek lines) — display his numbering, anchor coarsely to Greek ranges.

**Unknown unknowns this pass surfaced:**

- The **fourth fork**. This decision consciously re-accepts the drift risk the 07-15 plan documented, on the theory that Homer is a distinct *product*. Mitigation: the prompt orders a **DRIFT.md** ledger — every shared-core file touched gets one line noting divergence from plato-reader, so a future platform unification knows exactly what to reconcile.
- **Vulgate numbering is sacred.** Editions omit/bracket lines but preserve numbering; a naive pipeline that renumbers sequentially corrupts every citation. The prompt makes this a verifier check.
- **Speech spans nest** (Odysseus quoting Circe inside the Apologoi, messengers repeating speeches verbatim). Turn-flow must tolerate nesting or flatten with a `nested` flag — decide cheap, decide early.
- **The Odyssey's narrator problem**: Books 9–12 are Odysseus speaking for four books. Speaker-coloring logic that paints whole books as one speech must degrade gracefully (treat the Apologoi as narrative-within-speech).
- **"Draft apparatus" credibility**: AI-drafted place identifications are the riskiest apparatus class (real scholarly controversy). The certainty tiers + draft badges + John's review queue are the mitigation; the prompt forbids inventing identifications beyond the traditional ones.
- **SEO cold start**: a brand-new domain during the hottest search window. Mitigations: launch on staging immediately, get the CNAME + Search Console fast, and lean on outreach (r/classics, Sententiae Antiquae, classics blogosphere — a "free Landmark-style Homer" is genuinely news there).

---

## 8. Skeptical pass (where this plan is most likely wrong)

1. **"One shot" is doing a lot of lifting.** Core reader + search + computed features (epithets, repeats) are honestly one-shot-able on this architecture. The maps and 48 books of scene data are *content* — the prompt therefore orders them as data-schema-first with full AI-draft coverage, but expect the polish pass to be yours. The prompt's phase gates mean a partial success still ships a complete reader.
2. **Pope may fight the aligner.** He inflates 15,693 lines to ~heroic-couplet scale with wholesale invention. Coarse anchoring is the plan; if even that's ugly, the degrade rule is: ship Pope unaligned as a "reading translation" (picker note), never block launch on him.
3. **Speaker data quality** could embarrass (mis-attributed speeches are visible errors). Degrade rule: ship speech coloring only for spans above a confidence bar; the rest plain.
4. **Design ambition vs. one-shot**: a distinctive skin done badly is worse than the restrained inherited one. The prompt orders the skin as a token layer (CSS custom properties) over the inherited components — if the Aegean skin isn't landing, flipping back to restrained is a variable swap, not a rebuild.
5. **Movie-window pressure** shouldn't push a broken deploy. Staging URL immediately; the Lyceum CNAME only after the QA gate. The window is months, not days — today matters for *starting*, not shipping.

---

## 9. THE ONE-SHOT PROMPT

Paste the following into a fresh fable session in `~/Developer` (with Diogenes/TLG available locally and the sibling repos present). It assumes long-running autonomous work with phase gates.

```markdown
# BUILD: The Homer Reader — one-shot

You are building **The Homer Reader** (`~/Developer/homer-reader`, new git repo): a
Greek/English parallel digital edition of the Iliad and Odyssey with Landmark-style
apparatus — the digital equivalent of Strassler's Landmark editions, which never
covered Homer. Nolan's *Odyssey* film opened 2026-07-17; this site is the scholarly
on-ramp for that audience AND a daily-driver for classicists. Work autonomously
through the phases below. Each phase has an exit gate; do not proceed past a failed
gate — apply the phase's degrade rule instead. This is a long session: use
subagents/workflows for fan-out work (per-book data drafting, alignment QA).

## Persona & standards
Act as a classicist PhD (Homerist) + senior web engineer. Ancient Greek accuracy is
non-negotiable: Homeric dialect, vulgate lineation, and citation conventions
(Il. 1.1 / Od. 9.366) must be handled to professional standard.

## HARD RULES (violating any of these is failure)
1. NEVER commit TLG-derived Greek text to git history in raw source form; follow the
   exact TLG posture used by aristotle-reader/plato-reader (read their CLAUDE.md and
   pipeline docs FIRST and replicate the discipline).
2. NEVER include copyrighted translations or editorial matter: no Lattimore,
   Fitzgerald, Fagles, Lombardo, Wilson; no M.L. West editorial text; nothing from
   the print Landmark series. PD only: Murray (Loebs 1919/1924–25), Butler
   (1898/1900), Pope (1715–26).
3. NEVER renumber lines. Vulgate line numbering is preserved verbatim, including
   gaps and bracketed/athetized lines. A verifier must assert monotonic numbering
   with recorded, expected gaps per book.
4. Apparatus content (scene summaries, character bios, place notes, book intros) is
   AI-drafted BY YOU but every datum carries `status: "draft"`; the UI shows a
   discreet "· draft" badge on unreviewed apparatus. Never fabricate place
   identifications: every place gets a certainty tier
   (certain | traditional | speculative | mythical) and traditional identifications
   name their tradition (e.g., "Strait of Messina, traditional since antiquity").
5. No movie branding anywhere. No stills, no title treatment, no "Nolan". The
   tie-in is structural (a Start Here funnel + SEO pages), not visual.
6. Do not modify the sibling repos. Read-only.
7. Maintain `DRIFT.md`: one line per shared-core file you change vs. plato-reader,
   so future platform unification knows what diverged.
8. Deploy target is Cloudflare Pages staging (`*.pages.dev`) + R2 for /data (reuse
   the rclone/checksum-incremental recipe from classical-philosophy-reader's plan
   if present, else document the recipe). NEVER touch production DNS/domains.
9. Accessibility: inherit plato-reader's a11y fixes; WCAG AA contrast in BOTH themes
   of the new skin. Do not regress keyboard access on Greek tokens.

## PHASE 0 — Recon & unknown verification (no code)
Read, in order: plato-reader (CLAUDE.md, shared/lib/citation.ts, speakers.ts,
pipeline, docs/diogenes-xml-export-y.patch), classical-philosophy-reader (its verse
machinery, scheme registry state, hosting/deploy recipes), aristotle-reader
(ADDING-A-WORK.md, security-relevant shared code from PR #17 era, deploy discipline).
Then verify each unknown and WRITE `docs/PHASE0-FINDINGS.md`:
  a. TLG 0012 edition + lineation quirks (sample-export Il. 1, Od. 1 via Diogenes
     with the -y verse patch; check bracketed lines, numbering gaps). If the TLG
     text's editorial provenance is problematic, FALLBACK: Perseus PD Allen/
     Monro-Allen TEI as Greek source (write a stage-1 TEI reader instead).
  b. Perseus Murray TEI: fetch Il. + Od. English TEI; record milestone granularity
     (per-line or per-card). This decides Murray alignment cost.
  c. Autenrieth TEI from Perseus: confirm availability; plan native bake-in.
  d. Cunliffe: search for open digitized data. If none in 30 min of looking, mark
     fast-follow and move on (Autenrieth carries launch).
  e. Morpheus coverage: run the stage-4 targeted scan on the Il. 1 sample; report
     unparsed-token rate. If >8%, add Homeric lookup-variants (movable-nu,
     apocope/tmesis parts, uncontracted forms) analogous to beta.lookup_variants.
  f. DICES speech data: check license + Homer coverage. If unusable, plan the
     formula-detection route.
  g. AWMC/CAWM ancient-world map tiles: confirm a working tile URL + CC-BY terms;
     else select a modern-label-free terrain tile fallback.
GATE 0: findings doc exists; Greek sample renders 24 lines of Il. 1 with correct
vulgate numbers; a chosen Greek-source path is committed to in writing.

## PHASE 1 — Repo bootstrap
Fork plato-reader's code into homer-reader (fresh git history). Rename pipeline
package (`homer_pipeline`). Strip Plato works/data. Register scheme `verse-line`
(container=book, unit=line; renders "Il. 1.1" / "Od. 9.366"; jump box accepts
"9.366", "Od. 9.366", "od 9 366"). Works registry: iliad, odyssey (24 books each,
book = chapter machinery; author field "Homer"). Citation conventions for Copy
Citation: "Hom. Il. 1.1, trans. Murray" pattern. Port/borrow the newest verse
rendering from classical-philosophy-reader per Phase 0 findings; verse layout:
line-per-line, hanging indent on runover, gutter numbers every 5, athetized lines
marked with brackets + a legend. CLAUDE.md written now: hard rules above, TLG
posture, deploy discipline, DRIFT.md duty.
GATE 1: `npm run dev` serves Il. 1 Greek-only end-to-end from the pipeline.

## PHASE 2 — Corpus pipeline
Full Greek export (both epics, 48 books) → tokenize → morphology (with any Homeric
lookup-variants from Phase 0e) → shared LSJ shards (dedup pattern from aristotle)
+ Autenrieth as a second native lexicon pane in the word popup (LSJ | Autenrieth
tabs; Logeion external link row per the dictionaries plan).
Translations:
  - Murray: ingest from Perseus TEI, align via its milestones (attribute Perseus).
  - Butler: Gutenberg prose → gloss-based aligner (aristotle's) at ~5-line tick
    granularity. Verifier: every book covered, ticks monotonic.
  - Pope: Gutenberg → coarse anchors at speech/paragraph level; display Pope's own
    couplet line numbers; picker labels it "literary translation — alignment
    approximate". Disclose Broome/Fenton co-authorship of the Odyssey in the
    translation note. DEGRADE RULE: if coarse alignment quality is poor, ship Pope
    unaligned as a standalone reading text rather than blocking.
Footnotes: Murray's and Butler's notes → footnote popup machinery.
GATE 2: data-preflight passes 0 errors; spot-check page Od. 9.105–115 (Cyclopes)
shows Greek + all three translations correctly aligned; unparsed-token rate
reported in DEPLOY-STATUS.

## PHASE 3 — Reader + the Aegean skin
Design tokens FIRST (CSS custom properties over inherited components — the skin
must be revertible by variable swap): "Aegean" palette (wine-dark sea, bronze,
terracotta, bone), night mode = "night sailing" (deep indigo/bone/bronze), a
display serif for titles + drop caps, a Greek face suited to extended verse, meander
/wave-band rules used sparingly, abstracted vase-silhouette motifs ONLY on book-
opening plates and empty states. Two postures:
  - Scholar view: inherited parallel columns + full apparatus.
  - READING MODE (new, one keystroke: `r`): single column, generous measure, one
    translation, marginal scene summaries, subtle place/person markers, nothing
    else. This is the flagship UX.
Book-opening plates: book number, one-line argument, where/who/day strip, map
thumbnail. Performance budget: reading view interactive <1s mid-mobile; skin adds
zero blocking requests (system-font fallbacks, font-display: swap).
GATE 3: axe-core clean; AA contrast verified both themes; Lighthouse perf ≥ 90
on a book page; screenshots of both postures × both themes saved to docs/.

## PHASE 4 — Landmark apparatus (data-schema-first; all content AI-drafted with
status flags; fan out per-book work to subagents)
  4a. scenes.json per book: {lineRange, summary ≤20 words, location, dayNumber} →
      marginal running summaries (gutter machinery), book headers, and a Timeline
      page: Iliad day-calendar; Odyssey told-order vs story-order double-track
      diagram (Apologoi Books 9–12 as flashback links).
  4b. places.json keyed to Pleiades IDs, certainty tiers per Hard Rule 4. Four
      Leaflet maps: Catalogue of Ships explorer (Il. 2.494–759: every contingent a
      pin → card with leaders/ships/places/jump-to-lines); the Troad; the
      Wanderings (tier-labeled, with Eratosthenes' bag-of-winds quip in the intro
      note); Real Greece of the poems. Place tokens in text → map panel.
  4c. characters.json + 4 genealogy trees (Atreus, Aeacus, Troy, Olympians) +
      character pages with mention concordance.
  4d. COMPUTED: epithet explorer (noun-epithet formulas per named entity, from
      lemmatized text, with counts + line refs) and repeated-line/formula finder
      (exact lines + 4-word+ n-grams occurring ≥2×, cross-epic). These are pipeline
      stages with tests, not authored content.
  4e. Speech spans (DICES if Phase 0f cleared it, else formula detection + AI pass):
      speaker/addressee per span, nested speeches flagged (Apologoi = narrative-
      within-speech, do NOT paint Books 9–12 as one Odysseus speech); turn-flow
      coloring in reader + speaker filter in search. DEGRADE RULE: ship coloring
      only for high-confidence spans.
GATE 4: every book has scenes data (drafts OK); maps render with correct tier
labels; epithet + repetition pages pass their tests; no speech span crosses a book
boundary unflagged.

## PHASE 5 — Search, funnel, SEO
Search inherited; add filters: work, book, speaker, and a "speeches only" toggle.
Start Here funnel (/start): three doors — "New to Homer" (→ Od. 9 in Reading Mode),
"Reading along in Greek" (→ scholar view + a 5-minute how-to-use-the-parse tour),
"Just the maps" (→ map index). SEO: SSR all reader pages (inherited), landing pages
for high-intent queries ("read the Odyssey online free", "the Odyssey in Greek
English", "Catalogue of Ships map"), sitemap, robots, canonical on staging domain
initially. About page: the edition's sources (every PD translation + edition
credited), the draft-apparatus disclosure, the Lyceum, one tasteful line about this
being a good year to read Homer. No movie branding (Hard Rule 5).
GATE 5: SSR text visible with JS disabled; sitemap valid; funnel pages live.

## PHASE 6 — QA + staging deploy
Test suite green (port plato's suite; add: numbering verifier, alignment coverage,
scheme round-trip, epithet/repetition determinism). data-preflight 0 errors. Deploy:
R2 data sync + Pages deploy to staging. Write DEPLOY-STATUS.md ledger (sibling
discipline): what shipped, what's draft, unparsed rate, known issues, John's review
queue (apparatus books in draft, Pope alignment verdict, speech-confidence
threshold). Produce docs/LAUNCH-CHECKLIST.md for the human steps: Cloudflare
account/R2 bucket if absent, Lyceum CNAME ask, Search Console, outreach list
(r/classics, Sententiae Antiquae, classics blogs, Daily Nous-equivalents).
FINAL GATE: staging URL loads; Od. 9.366 (Οὖτις — "Nobody") reachable by jump box,
correctly parsed on click, Murray/Butler/Pope switchable, on the Wanderings map,
inside a colored Odysseus speech span, with a draft-badged marginal summary. That
single line exercises the whole machine.

## REPORT BACK
End with: staging URL, DEPLOY-STATUS summary, the Phase 0 findings that changed the
plan, DRIFT.md contents, and the top 5 items needing John's judgment.
```

---

## 10. Launch-week checklist (outside the prompt — John's side)

1. Run the one-shot; review DEPLOY-STATUS + the review queue it produces.
2. Cloudflare: account/bucket/tokens if not already set up from the classical-philosophy plan; then the Lyceum CNAME ask (`homer.lyceum.institute` or similar).
3. Apparatus review cadence: 2–3 books/day of scene summaries flips the draft badges in ~3 weeks; prioritize Od. 5, 9–12, 21–23 and Il. 1, 6, 9, 16, 18, 22, 24 (the books people actually land on).
4. Outreach once the CNAME is live: r/classics + r/AncientGreek, Sententiae Antiquae (they literally run "free tools for reading Homer" roundups), classics blogs, the Lyceum's own channels. The pitch writes itself: *"A free digital Landmark Homer — Greek and English, maps, genealogies, every formula indexed — there has never been a Landmark Homer."*
5. Standing notes: T. E. Lawrence's Odyssey unlocks Jan 1, 2028; Evelyn-White's Hesiod/Hymns Loeb (1914, PD) is the natural second wing; Cunliffe OCR is the Bonitz-pattern fast-follow.
