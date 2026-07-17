# Phase 0 Findings — The Homer Reader

Date: 2026-07-17. Recon by 5-agent fleet (Sonnet) + orchestrator synthesis.
Status: **complete except unknown (a)/(e)** — TLG 0012 sample export + Morpheus
scan in flight; this doc is updated and Gate 0 is evaluated when it lands.

## (a) TLG 0012 edition + lineation — RESOLVED: **Perseus fallback chosen**

Export executed successfully (recipe below verified working). Verdict:
- TLG Iliad = **Allen, Oxford 1931** (editio maior vols 2–3). TLG Odyssey =
  **von der Mühll, Basel 1962**. Neither is West — but 1931 misses the US PD
  line (pre-1931) by one year, and 1962 is firmly in copyright. Serving these
  editorial texts publicly conflicts with the project's copyright posture.
- **DECISION (Gate 0, in writing): Greek source is Perseus
  `tlg0012.tlg001/002.perseus-grc2` for both poems** — Iliad: Monro–Allen OCT
  Editio Tertia 1908–1920 (PD-US); Odyssey: the 1919 Murray Loeb Greek text
  (PD-US). Verified by direct fetch 2026-07-17: Il. 1 = 611/611 lines, Od. 1 =
  444/444, explicit continuous `n=` attributes, zero anomalies. This is the
  PROMPT.md fallback path (stage-1 TEI reader), applied per its written degrade
  rule. Decisive extras: DICES speech spans and Cunliffe's citation URNs both
  key to perseus-grc2 lineation — source-native integration.
- For John's review queue: (1) confirm the copyright call (Allen 1931 enters US
  PD 2027 — a future re-basing option); (2) the Odyssey Greek is the Loeb 1919
  text, not the OCT — About-page edition credits must say so; (3) TLG's
  Alexandrian sigla (obelos ×440, diplē ×1875, asteriskos — Iliad-only
  `<seg rend="Marginalia">`) are NOT available in Perseus — athetesis display
  becomes a fast-follow needing a PD secondary source. Notably the TLG export
  has NO modern bracket notation either — "bracketed lines" data exists in
  neither source.
- TLG lineation cross-check (for the record): TLG Il. 1 = 611, Od. 1 = 444,
  zero anomalies, one stray `n="605*"` corpus-wide; `<l n="t">` book-title
  lines excluded. TLG export recipe verified and archived in the recon report
  (scratch-patched `xml-export.pl -c tlg -n 0012 -y`).

Established during recon:
- Corpus present: `TLG0012.TXT`/`.IDT` at
  `/Users/johnboyer/Documents/CLAUDE CODE ARISTOTLE PROJECT/TLG Files/TLG`.
- Export recipe (from plato/classical docs): patch a scratch copy of
  Diogenes v4.5 `xml-export.pl` with `docs/diogenes-xml-export-y.patch`
  (plato-reader; ~6 lines, adds `-y` verse mode), scratch `diogenes.prefs`
  with `tlg_dir`, then
  `Diogenes_Config_Dir=<scratch> PATH=/usr/bin:/bin perl -I <Diogenes>/server
  -I <Diogenes>/dependencies/CPAN xml-export.pl -c tlg -n 0012 -y -o <outdir>`.
  Whole-author export; output `tlg0012001.xml` (Il.), `tlg0012002.xml` (Od.).
- Edition string lives in each work's `<sourceDesc><p>` — only readable
  post-export. **Decision rule stands:** if West-derived → fall back to Perseus
  `tlg0012.tlg001/002.perseus-grc2` (Monro/Allen OCT 1908–1920, PD) with a
  stage-1 TEI reader.
- Pipeline gotcha (aristotle): the pipeline's stripped-PATH subprocess export
  dies (exit 25) — run the export manually to pre-populate `build/export/`;
  pipeline consumes the cached XML.

## (b) Perseus Murray TEI — GREEN

- Iliad `tlg0012.tlg001.perseus-eng3.xml` = Murray 1924–25; Odyssey
  `tlg0012.tlg002.perseus-eng3.xml` = Murray 1919. (`perseus-eng4` = Butler on
  both — a bonus TEI source for Butler, potentially better than Gutenberg.)
  Catalog UI mislabels these eng1/eng2 — trust the `__cts__.xml`/filenames.
- Repo: PerseusDL/canonical-greekLit, CC-BY-SA 4.0. Raw URLs recorded in the
  recon report (standard raw.githubusercontent paths).
- **Milestone granularity: every 5 lines** (`<milestone n="5" unit="line"/>`
  anchors inside continuous prose within ~25–50-line "card" divs). Murray
  alignment is therefore cheap (parse milestones) but snaps to 5-line blocks —
  the parallel view design must accept 5-line granularity for Murray, same
  cadence as the Butler gloss-aligner ticks. Loeb footnotes present as
  `<note resp="Loeb">` inline — feeds the footnote-popup machinery.

## (c) Autenrieth — YELLOW (plan inversion, see d)

- NOT in any modern CTS/GitHub repo (checked canonical-pdlrefwk, lexica,
  scaife atlas-data-prep; catalog.perseus.org has zero hits). Only the legacy
  Perseus 4.0 Hopper serves it (`Perseus:text:1999.04.0073`), per-entry HTML,
  scrape-only.
- Consequence: "Autenrieth carries launch" (PROMPT 0d assumption) is inverted —
  see (d). Recommendation: **Cunliffe becomes the native second lexicon pane at
  launch**; Autenrieth attempted via a time-boxed Hopper scraper in Phase 2,
  else fast-follow. → John's review queue (PROMPT names Autenrieth; data
  reality favors Cunliffe).

## (d) Cunliffe — GREEN (better than expected)

- Structured JSONL exists: `scaife-viewer/atlas-data-prep` →
  `test-data/dictionaries/cunliffe-1-lex/entries_01.jsonl` (+ `cunliffe-2-hompers`,
  the proper-names companion). One entry per line: headword, full definition,
  citations with quotes and **CTS URNs pointing at the same perseus-grc2 line
  numbering** — auto-linkable to our text.
- Cunliffe 1924 → PD in US (pre-1931). The JSONL encoding's repo license must
  be confirmed at ingest time (atlas-data-prep LICENSE file) — Phase 2 checklist
  item.

## (e) Morpheus coverage — RESOLVED: 0.33% unparsed (Il. 1) — GREEN

- Measured on the TLG Il. 1 sample: 2,108 unique tokens, 7 unmatched =
  **0.33% unparsed**, far below the 8% threshold. **Homeric lookup-variants are
  NOT required at Phase 2 entry.** (Rate to be re-measured corpus-wide on the
  Perseus text in Phase 2 and recorded in DEPLOY-STATUS.)
- The 7 misses, diagnosed: real Morpheus data gaps (bare θέσαν/ἔθεσαν,
  τετάγων, οἷδε, epic crasis ταρ) plus one fixable lookup-logic gap:
  accent-placement variants (τῆνδε circumflex vs Morpheus's acute key) —
  a small accent-normalized fallback in `beta.py` `lookup_variants` is a cheap
  Phase 2 improvement if the corpus-wide rate shows the pattern recurring.
- Morpheus is not a service: single targeted scan of
  `/Applications/Diogenes.app/Contents/dependencies/data/greek-analyses.txt`
  (115 MB) via `stage4_morphology.py` key expansion. Attic baseline ~0.11%
  unmatched; preflight treats unmatched as expected (no hard gate) — record,
  don't fail.

## (f) DICES speech spans — GREEN

- Code MIT (cwf2/dices); **data CC-BY 4.0** (Borealis release
  doi:10.5683/SP3/N8LS2Y). Single fetchable fixture:
  `data/speechdb.json` (3.6 MB, 4689 speeches).
- Homer coverage: both epics (Iliad 698 speeches). Per speech: first/last line,
  speaker + addressee ID lists (co-speakers supported), cluster/part (exchanges),
  type, and **`level` (embedded-speech depth: 0=4209, 1=445, 2=31, 3=4)** —
  nesting is first-class, so the Apologoi flagging requirement is satisfied by
  the source data. Character metadata rows included.
- Verdict: use DICES for Phase 4e; the formula-detection fallback route is NOT
  needed. Attribution on About page.

## (g) Map tiles — GREEN

- CAWM tile server (Iowa-hosted successor to AWMC tiles):
  `https://cawm.lib.uiowa.edu/tiles/{z}/{x}/{y}.png` — live-tested HTTP 200,
  real 256×256 PNG. CC BY 4.0, no key, no stated rate limits; public-site use
  with attribution is fine.
- Required attribution (verbatim, for map credits + About):
  Horne, R., Talbert, R., Becker, J., Twele, R., Jo, A., Belanger, R.,
  Hagemann, L., Lee, A., Bowen, J., Butler, M., et al. *Consortium of Ancient
  World Mappers Map Tiles.* The Consortium of Ancient World Mappers and the
  Digital Scholarship & Publishing Studio at the University of Iowa, 2022,
  https://cawm.lib.uiowa.edu.
- No fallback needed. Ancient basemap, no modern labels.

## Sibling-machinery findings that change the build plan

1. **No epic verse renderer exists to port.** classical-philosophy-reader's
   `verse-line` scheme is a deliberate stub; its real verse behavior is a
   per-fragment DK composition (numbering restarts per fragment). Homer's
   continuous book-scoped lineation needs a real new scheme in BOTH
   `shared/lib/citation.ts` and pipeline `scheme.py` (dual TS/Python contract),
   modeled on bekker's validation machinery. Reusable near-verbatim: hanging
   indent CSS (one rule), gutter every-5 `showLineNum` pattern, the
   `expected_line_gaps` monotonic verifier (implemented but never yet used by a
   live manifest — treat as untested), the `build-public.mjs` preflight hard
   gate, FootnotePopup/WordPopup (scheme-agnostic).
2. **`GreekLine` has no bracketed/athetized field anywhere in the family** —
   new field + rendering + legend are new work (CLAUDE.md hard rule).
3. **Security port needs a fresh diff:** aristotle keeps sanitizeHtml/escapeRe
   in `shared/`; plato-reader's sanitizer appears app-local and escapeRe wasn't
   found there. Port the stronger aristotle versions + `security.test.ts` +
   app-local `jsonld.ts` during Phase 1.
4. **Butler ships from Perseus TEI, not Gutenberg** (verified 2026-07-17 by
   direct fetch): `perseus-eng4` Iliad has 1450 line milestones (5-line cadence
   at open), Odyssey 1048 (~10–15-line, paragraph-anchored). Ingest via the same
   milestone parser as Murray; interpolate between anchors; the gloss aligner
   becomes an optional refinement pass, not the critical path. (Pope remains
   Gutenberg + coarse anchors.)
5. Murray at 5-line snap + Butler at 5-line ticks means the parallel view has a
   uniform 5-line alignment cadence; only Pope is coarser.

## Gate 0 checklist — **PASSED 2026-07-17**

- [x] Findings doc exists (this file, all seven unknowns resolved)
- [x] Greek sample renders 24 lines of Il. 1 with correct vulgate numbers —
      `scratchpad/gate0-il1-sample.html`, functionally verified (24 `<l>`,
      n=1..24 continuous, gutter ticks 1/5/10/15/20, Greek text present)
- [x] Chosen Greek-source path committed in writing: **Perseus perseus-grc2,
      both poems** (see (a) above)

Consequences for Phase 1+: stage 1 is a Perseus TEI reader (not the Diogenes
export reader); translations Murray + Butler both ingest from Perseus TEI
milestones; DICES + Cunliffe URNs align natively; Morpheus stage ports as-is.
