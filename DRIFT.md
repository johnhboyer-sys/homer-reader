# DRIFT.md

Tracks every file in this repo's shared-core areas (`shared/`, `app/`, plus
the root build script) that has diverged from its `plato-reader` counterpart,
so a future sync/patch-forward pass knows what NOT to blindly overwrite. One
line per file. Update this whenever a shared-core file is edited for a
Homer-specific reason.

- `shared/lib/works.ts` — `WORKS` populated with the two Homer epics (`iliad`,
  `odyssey`; `citation.scheme: verse-line`, 24 books each); `SHELVES` = one "The
  Epics" shelf; `START_HERE` = `['iliad','odyssey']`; `HOUSE_AUTHOR` `'Plato'` →
  `'Homer'`; `Work` gained optional `authorAbbr` and `verse-line` added to the
  `citation.scheme` union. Derived exports/helpers unchanged.
- `shared/lib/data.ts` — comment reference `pipeline/plato_pipeline/...` →
  `pipeline/homer_pipeline/...` (no logic change).
- `shared/lib/citation.ts` — added the `verse-line` scheme (book.line grammar,
  dot separator, user-facing lines) plus work-aware helpers
  (`parseVerseCitation`, `formatVerseCitation`, `formatCopyCitation`); comment
  reference `plato_pipeline` → `homer_pipeline`.
- `shared/__tests__/works.test.ts` — Plato assertions retargeted to the Homer
  registry (iliad/odyssey, 1 shelf, START_HERE, no Platonic period).
- `shared/__tests__/palette.test.ts` — `rankWorks` assertions retargeted to
  Homer abbreviations/ids (Il./Od., iliad/odyssey).
- `shared/__tests__/verse-line.test.ts` — new: verse-line scheme + jump/citation
  round-trip coverage (Homer-only, no plato-reader counterpart).
- `shared/__tests__/data.test.ts` — comment reference `plato_pipeline` →
  `homer_pipeline` (no logic change).
- `shared/components/Reader.svelte` — new `epicVerse` const (`cscheme.id ===
  'verse-line'`) scoping a `verse-line` class on `.reader-body` (parallel to
  `busse`/`stephanus`, no plato-reader counterpart); `hasBracketedLines`
  reactive + a one-line legend gated on it; the segment-path `.greek-line` div
  gained `class:bracketed` + a `title` tooltip and `.line-text` gained
  `[`/`]` glyph spans for `GreekLine.bracketed`. Not ported from
  classical-philosophy-reader's `dkVerse` (that's per-fragment DK verse, a
  different scheme) — an independent verse-line implementation.
- `shared/lib/data.ts` — `GreekLine` gained optional `bracketed?: boolean`
  (type-only; inert until a future apparatus pass sets it).
- `shared/styles/global.css` — new "Verse-line (Homer)" section:
  `.reader-body.verse-line .line-text` hanging indent (ported from
  classical-philosophy-reader's dk-verse CSS), `.greek-line.bracketed` +
  `.line-bracket` muted styling, `.verse-bracket-legend`.
- `shared/__tests__/components.test.ts` — new `describe` block: verse-line
  (epic) rendering coverage against the real `iliad` registry work (Homer-only,
  no plato-reader counterpart).
- `app/astro.config.mjs` — `site` set to placeholder `https://example.invalid`
  (`// TODO real domain (John)`); `base` changed from `/plato-reader` to `/`
  (GitHub Pages one-off, domain root, no Cloudflare/R2 — John, 2026-07-17).
- `scripts/build-public.mjs` — env var override renamed `PLATO_PY` →
  `HOMER_PY`; internal `plato_pipeline` module-invocation strings renamed
  `homer_pipeline` (tracks the `pipeline/` package rename below).
- `shared/lib/works.ts` — both epics' `murray` translation entries gained
  `footnotes: true` (Phase 2: Loeb `<note>` apparatus, milestone-anchored,
  spliced into the prose as `[^label]` markers; see
  `pipeline/homer_pipeline/stage1_perseus_milestone_english.py`).
- `shared/lib/works.ts` — both epics' `pope` translation `name` gained
  "— alignment approximate" (Phase 3: Pope ingested book-anchored only, no
  intra-book proportional gutter — see
  `pipeline/homer_pipeline/stage1_pope.py`'s module docstring for the
  spot-check evidence behind that decision; label text pre-authorized by
  John, 2026-07-17). No new `TranslationRef` field — the existing `name`
  string already flows straight into the picker's `<option>` label
  (`shared/components/Reader.svelte`), so no component change was needed.

- `shared/lib/data.ts` — Cunliffe added as a second native lexicon dictionary
  beside LSJ: `Analysis` gained `cunliffe: string[]`; new `CunliffeEntry`
  interface, `_cunliffeCache`, `cunliffeShard` (identical letter rule to
  `lsjShard`, kept as a separate function — see its own comment), and
  `fetchCunliffeShard`; `lookupWord`'s return gained `cunliffe: CunliffeEntry[]`
  resolved the same de-duped way as `lsj`. No plato-reader counterpart.
- `shared/components/WordPopup.svelte` — the unconditional LSJ-only section
  replaced with an ARIA-tabs dictionary row ("LSJ · Cunliffe · Logeion ↗"),
  LSJ default; both dictionary panels gained a quiet empty state ("Not in
  LSJ."/"Not in Cunliffe."); new `onCunliffeClick` resolves a Cunliffe entry's
  internal `<a class="cunliffe-cite" data-work data-book data-line>` citation
  markers to a real reader URL via `workPath`/`formatLocValue` (same pattern as
  `BekkerJump.svelte`); new `onTabRowKey` for arrow-key tab navigation; new
  `logeionHref` reactive. No plato-reader counterpart (Cunliffe is Homer-only).
- `shared/styles/global.css` — new `.dict-tabs`/`.dict-tablist`/`.dict-tab`/
  `.dict-tab-link` (the tab row) and `.cunliffe-entry` + its `.cunliffe-sense`/
  `.cunliffe-cite` child rules (Cunliffe HTML classes from stage5_cunliffe),
  placed beside the existing `.lsj-section`/`.lsj-entry` rules. Reuses only
  existing CSS custom properties — no new palette values. No plato-reader
  counterpart.
- `shared/__tests__/a11y.test.ts`, `shared/__tests__/data.test.ts` — `lsj`-only
  `lookupWord`/`Analysis` fixtures extended with `cunliffe` fields (required by
  the new field); `data.test.ts` gained a Cunliffe shard-selection assertion
  and the TS half of the Python/TS shard-letter parity check (see
  `pipeline/tests/test_stage5_cunliffe.py`'s `SHARD_FIXTURE`).
- `shared/__tests__/word-popup.test.ts` — new: WordPopup dictionary-tab
  coverage (tab presence/default, Cunliffe empty state, arrow-key nav, Logeion
  link attributes). No plato-reader counterpart.
- `scripts/build-public.mjs` — added a `verify_shared_cunliffe` gate call
  right after the existing `verify_shared_lsj` one (same pattern, second
  dictionary). No plato-reader counterpart (Cunliffe is Homer-only).

Not shared-core but worth noting here since it touches every pipeline
reference across the repo: `pipeline/plato_pipeline/` was renamed to
`pipeline/homer_pipeline/` (directory + all imports/docstrings/tool scripts),
and `pipeline/pyproject.toml`'s project name changed `plato-pipeline` →
`homer-pipeline`. Not file-by-file listed here since it's a mechanical,
repo-wide package rename rather than incremental content drift.

## Aegean skin + rebrand (2026-07-17)

Token layer per `docs/DESIGN.md` (John's hybrid-v2 verdict). **Revert
mechanism:** every colour/font custom property kept its EXISTING name — only
the VALUE changed — so the skin reverts by swapping `:root` /
`:root[data-theme="dark"]` values back to the "Ionian teal" block recorded in
a comment at the top of `shared/styles/global.css` (just above `:root`).

- `shared/styles/global.css` — `:root`/`:root[data-theme="dark"]` re-valued to
  the Aegean palette (marble ground, wine-dark indigo night mode, metallic
  bronze; old teal values preserved in a comment for revert). Two NEW tokens:
  `--rule-strong` (strong hairline/gutter-number colour) and `--terracotta`
  (draft-badge only, per CLAUDE.md's apparatus-honesty rule — not yet wired to
  a component, no draft-badge UI exists yet). `--text-light` collapsed onto
  the same value as `--text-mid` (Aegean defines only two ink shades; both
  pass AA — see contrast table in the PR/report). `--greek-hover`/
  `-hover-border`/`-active` now `color-mix()` off `--accent`/`--page-bg` so
  they auto-track the active theme instead of duplicating hex per theme.
  Fonts: `--font-greek`→Palatino stack, `--font-english`→Iowan Old
  Style/Charter stack, `--font-ui`→Optima stack, new `--font-display` (Big
  Caslon/Hoefler) for cartouche/masthead titles — all system stacks, zero
  webfont network requests. New "Aegean chrome" CSS block (masthead wordmark,
  `.contour-band`, `.book-plate` cartouche, `.site-footer`) added before the
  print media query. New "Verse-line (Homer)" rule: gutter numerals
  (`.line-num`/`.bk-num`) coloured `--accent` (bronze) in `.reader-body.verse-line`
  — `showLineNum()` (Reader.svelte) already only ever renders the 1/5/10…
  tick cadence, so there's no separate "unmarked gutter" state to colour
  differently. Hardcoded dark/light chevron SVG hex + `var(--accent, #1f6f7a)`
  fallbacks recoloured to match. Several hardcoded `color: #fff` button-text
  rules (paired with `background: var(--accent)`) swapped to `color:
  var(--on-accent)` — the old teal dark-mode accent already failed AA there
  (2.34:1); bronze doesn't fix that on its own, `--on-accent` does (5.89:1 /
  7.36:1, both themes, computed).
- `app/src/components/ReaderShell.astro` — home-link replaced with a
  `.home-wordmark` (name + "Digital Landmark Edition" eyebrow); contour-band
  SVG inserted under the header; new `.book-plate` cartouche section (Greek
  genitive title + Α–Ω/α–ω book letter — Iliad capital, Odyssey lowercase,
  the inherited Alexandrian convention — computed locally, no registry
  change) rendered before `<Reader>` for verse-line, non-bookless works only;
  argument/where-who-day slots read an optional `bookData.apparatus` field
  that no pipeline stage emits yet (renders nothing until Phase 4 populates
  it — no placeholder text); new `.site-footer` with the three source
  credits. Google Fonts `<link>`s (Cardo/EB Garamond + print-only Bodoni
  Moda/DM Mono) removed.
- `app/src/components/Landing.astro` — same wordmark + contour-band +
  `.site-footer` treatment; `og:site_name`/breadcrumb/support-heading
  Plato→Homer; `work.period` string no longer hardcodes "Plato's" (now
  `{work.author}'s`, a latent bug independent of this rollout); Google Fonts
  link removed.
- `app/src/pages/index.astro` — homepage masthead eyebrow "Plato" →
  "Digital Landmark Edition", h1/lede/meta/JSON-LD Homer-ized, contour-band
  added, aristotle-reader footer cross-link removed (per brief), Google Fonts
  link removed.
- `app/src/pages/attribution.astro` — content sections rewritten from
  Plato-reader inheritance (Stephanus/Loeb/Burnet, still describing a
  different site) to the facts this build actually carries: vulgate line
  numbering (not Stephanus), Murray/Butler/Pope (not Loeb), Monro–Allen OCT
  (not Burnet), Cunliffe added as a credited lexicon alongside LSJ, github
  links repointed `plato-reader`→`homer-reader`. Google Fonts link removed.
- `app/src/pages/{404,support,search,lemma/index}.astro`,
  `app/src/components/LemmaPage.astro` — title/meta/JSON-LD/home-link
  Plato→Homer strings; 404's Meno-geometry joke replaced with an
  Odyssey/nostos-themed one (same structure, different classical reference,
  no fabricated quotations); Google Fonts links removed from all.
  (WorkSwitcher.astro is absent on both repos — not a drift file.)
- `shared/components/WordPopup.svelte` — "Appears N× across Plato" →
  "…across Homer" (matches `HOUSE_AUTHOR`).
- `shared/components/Search.svelte` — CSV export filename `plato-search-*` →
  `homer-search-*` (cosmetic string only, no logic touched).
- `pipeline/homer_pipeline/preflight.py` — module docstring Plato→Homer.

## Phase 3 — Reading Mode posture + docked lexicon rail (Homer, 2026-07-17)

- `shared/components/LexiconPanel.svelte` — NEW, no plato-reader counterpart:
  the shared BODY of the word lookup (entry-fetch via `lookupWord`, headword +
  short gloss + analysis cards, the EXPAND disclosure to the full LSJ/Cunliffe
  entry, and the LSJ · Cunliffe · Logeion↗ tab row). Extracted out of WordPopup
  so the docked desktop rail and the mobile popup share one source of truth
  (DESIGN.md 2026-07-17). A future plato sync should fold WordPopup's dictionary
  body into this component rather than diverging.
- `shared/components/WordPopup.svelte` — refactored from a monolithic modal
  into a thin PRESENTATION shell around `<LexiconPanel>`, gaining `docked` +
  `autofocus` props: `docked=true` renders a NON-modal in-layout lexicon rail
  (no backdrop, no aria-modal, no focus-trap — desktop ≥1100px) while the
  default stays the modal anchored popup/sheet (<1100px). The dictionary tabs
  and the "Appears N× across Homer" lemma link moved into LexiconPanel.
- `shared/components/Reader.svelte` — Reading Mode posture (`r` keystroke +
  header `.posture-btn`, input-focus-guarded, aria-live announced,
  `?mode=reading` shareable, persisted global `reader-posture`): a single-column
  `readingView` snippet reusing `transFlow`/`primaryEng`/`altEng`, with
  `sceneChip` marginal chips driven by the new optional `BookData.scenes`.
  Lookup presentation now chooses docked-rail vs popup by
  `matchMedia('(min-width: 1100px)')` (`computeDocked`, recomputed on resize);
  `handleTokenClick` takes a `viaKeyboard` flag so a keyboard-opened docked rail
  takes focus and returns it to the token on close.
- `shared/lib/data.ts` — new optional `Scene` interface + `BookData.scenes?`
  (Landmark scene apparatus; absent on every payload today, inert like
  `GreekLine.bracketed`).
- `shared/styles/global.css` — new additive "Phase 3 — Reading Mode posture +
  docked lexicon rail" section (`.posture-btn`, `.reading-col`, `.scene-chip`
  family, `.word-sidebar.docked`, reading-mode chrome trims) — Aegean tokens
  only, no new palette values.
- `shared/__tests__/word-popup.test.ts` — extended: EXPAND disclosure (gloss
  first, tabs revealed on expand), "Logeion is the only target=_blank", and
  docked-vs-modal presentation.
- `shared/__tests__/components.test.ts` — new describe blocks: Reading Mode
  posture (`r` key, input guard, button, `?mode=reading`) and the
  docked/modal lexicon breakpoint (mocked matchMedia).
- `app/public/{manifest.webmanifest,offline.html,sw.js}` — PWA
  name/short_name/description, offline-page title + hardcoded colours (now
  the Aegean ground/ink hex), sitemap URL, and the service worker's cache-key
  prefix (`plato-reader-`→`homer-reader-`, a fresh cache namespace post-deploy,
  harmless) — all Plato→Homer. Not `shared/`/`app/src`, but clearly
  in-scope for a rebrand pass (PWA install name, offline page) and low-risk.
  (`app/public/robots.txt` is plato-only source; Homer has no counterpart under
  `app/public/` — do not treat as a diverged twin.)
- Grep sweep (case-insensitive "plato") on rendered `dist/` output found only
  two justified remainders: LSJ dictionary entries and lemma pages that
  legitimately cite the classical author "Plato" (LSJ usage citations, e.g.
  "Neo-Platonists") — real lexicographic content, not branding; and
  `dist/sw.js`'s dormant `fonts.googleapis.com`/`fonts.gstatic.com`
  cache-first hostname rule, now unreachable dead code since no page loads a
  webfont — left in place as zero-impact, out of this pass's blast radius.
  Source-level remainders (doc comments in `shared/lib/{speakers,palette}.ts`,
  `pipeline/homer_pipeline/*.py` Stephanus-scheme infrastructure comments,
  `shared/glossary/EN.md`'s Nicomachean-Ethics glossary prose) are inert,
  non-user-facing, and outside this agent's blast radius (not
  `app/src`/`shared/styles`/`shared/components`).

## Gate-3 performance + apparatus pass (2026-07-17)

- `shared/components/Reader.svelte` — Homer-specific perf + apparatus divergence
  beyond the verse-line entries above: (1) Greek token markup in the `greekToks`
  snippet is now INERT (no per-token `class:active`/`class:hit` or
  `on:click`/`on:keydown`; carries `data-k`/`data-o`) with ONE delegated
  click+keydown handler on `.reader-body` (`onReaderClick`/`onReaderKeydown`/
  `activateToken`) — removed the ~1.2s hydration task on a ~7000-token book.
  Active-word ring + search-hit paint are imperative (`refreshTokenDecorations`
  in `afterUpdate`). (2) onMount clears the `data-rview` pre-paint view bridge
  once Svelte owns the view class. (3) `scenesDraft` + a `.draft-badge` on each
  Reading-Mode scene chip (apparatus-honesty). Uses new `RawBookData` import.
- `shared/lib/data.ts` — extracted `normalizeBookData(RawBookData): BookData`
  (+ exported `RawBookData` interface) as the ONE authoritative
  `apparatus.scenes → scenes` normalizer, now called by BOTH `fetchBook` and the
  build-time SSR path (`ReaderShell.astro`); previously the normalization lived
  inline in `fetchBook` only, so static pages had `scenes` undefined.
- `shared/styles/global.css` — (1) `:root[data-rview="english"|"greek"]
  .reader-body.view-both …` pre-hydration view bridge (mirrors the monolingual
  column display/width AND the mobile font-size, so the SSR `view-both` paint
  matches the hydrated single-language layout — kills a ~0.16 CLS on
  `.ross-prose`). (2) `.draft-badge` (terracotta outline chip, both grounds AA)
  for the scene chips + cartouche. Paired with `ReaderShell.astro`'s inline
  `data-rview` head script.
- `shared/__tests__/data.test.ts` — added two `normalizeBookData` cases (SSR-path
  shape + already-normalized passthrough).

## Gate-3 payload follow-up: token-stripped island props (2026-07-17)

Eliminates the redundant serialized `bookData` the Reader island inlined (mobile
Lighthouse on `/iliad/book/1/` 88 → 90; HTML gzip 216 KB → 138 KB; Reader island
props 668 KB → 139 KB). The Greek token arrays duplicated the SSR token spans and
the non-default translations weren't in the default view at all.

- `shared/lib/ssr-book.ts` — NEW. Build-time SSR channel (`setSsrBook`/
  `takeSsrBook`): ReaderShell stashes the FULL book here so the island's SERVER
  render still emits every token span, while its serialized props carry a
  token-stripped copy. Server-only (null in the browser). Not in plato-reader.
- `shared/lib/data.ts` — added `stripBookForClient(BookData)` (drops each Greek
  line's `tokens` → `[]` and the non-default `ross`/`third`/`overlays`, keeps
  active English + line text + scenes, sets `tokensStripped`) and the
  `BookData.tokensStripped?` flag. Homer-specific payload divergence beyond the
  verse-line entries above.
- `shared/components/Reader.svelte` — Homer-specific perf divergence beyond the
  Gate-3 entry: (1) on the SERVER the render sources the full book from the SSR
  channel (`takeSsrBook`); on the CLIENT `rebuildTokensFromDom` refills each
  stripped line's `tokens` from the SSR `.tok` spans (data-k/data-o/text) in
  component init — BEFORE first hydration render, so parts match and Svelte
  claims the existing spans (no wipe). (2) `ensureFullBook` lazily `fetchBook`s
  the full book (with the other translations) the first time a NON-english-slot
  translation becomes visible (single / either compare column / Reading Mode) —
  reactive-gated on `wantsNonDefaultTrans` + `mounted`.
- `shared/__tests__/data.test.ts` — added a `stripBookForClient` case (strips
  tokens + ross/third, keeps text/english/scenes, input left intact).
- `app/src/components/ReaderShell.astro` — passes `stripBookForClient(bookData)`
  to the island and `setSsrBook(bookData)` for the server render; the local
  `bookData` (cartouche/apparatus reads) is unchanged.

## Wine-dark token swap + homepage v1.5 rebuild (2026-07-17)

Token layer per `docs/DESIGN.md`'s LOCKED Wine-dark palette (John, 2026-07-17),
superseding the Aegean bronze/marble skin from the rollout above (same posture:
revert by swapping `:root`/`:root[data-theme="dark"]` values back — the Aegean
values are now recorded in the same revert comment, alongside the original
"Ionian teal" block). Homepage rebuilt per `docs/mocks-homepage-v1.5.html`
(John: "better for now") — no more catalog cards (the corpus is only ever two
works: `iliad`, `odyssey`).

- `shared/styles/global.css` — `:root`/`:root[data-theme="dark"]` re-valued to
  Wine-dark (cool grey-biased bone grounds, deep indigo-black night, οἴνοπα
  garnet accent). `--terracotta` renamed to `--draft` (slate-blue #375065
  light / #8FB0C9 dark — the new colour is not a terracotta, so the old name
  would mislead); `.draft-badge` repainted off `var(--draft)`. No other
  selectors touched — pure token-value swap, contrast re-verified (all pairs
  ≥4.5:1, see the implementation report).
- `app/src/pages/index.astro` — full rewrite: monumental asymmetric
  ΙΛΙΑΣ/ΟΔΥΣΣΕΙΑ hero (fixed wine-dark ground, both themes, dusk/night
  variants) with per-epic watchfire/star ambient animation, diagonal
  horizon-seam SVG, three "Start Here" doors, and a factual apparatus band
  (scene chip + day marker read LIVE off `public/data/iliad/book-01.json`'s
  `apparatus` block, not hardcoded — see the implementation report for why).
  Catalog/shelf browsing (`SHELVES`, `START_HERE` cards, mobile
  collapse-toggle) and the "Continue reading" resume-card removed — no longer
  reachable from the homepage (both still work from a work's landing page /
  the reader itself). The feedback modal (Request a Feature / Report an
  Error) kept — the mock doesn't show it, but it's the site's only bug/feature
  report channel and dropping it would have been a silent regression outside
  this task's scope. The hero's fixed (non-swapping) `--hero-*` tokens are
  re-based on Wine-dark's dark-theme hex (previously Aegean's) so the hero and
  the re-skinned rest of the page read as one accent family.

## Genealogies page (2026-07-17)

New Homer-only apparatus feature — the four Landmark-style family trees
(House of Atreus, House of Aeacus, House of Troy/Dardanids, the Olympians)
drawn from `apparatus/characters.json`'s `genealogy` field. No plato-reader
counterpart (Plato's corpus has no character genealogy apparatus); listed
here because the new files live in `shared/`.

- `shared/lib/genealogy.ts` — new: `buildGenealogyTree`/`flattenGenealogy`,
  pure flat-list-to-forest transform (patrilineal nesting; external/cross-tree
  parent resolution; `nonHomeric` flag carried per parent). No runtime fetch —
  called once at build time by `app/src/pages/genealogies/index.astro`.
- `shared/__tests__/genealogy.test.ts` — new: fixture-based coverage of the
  above (single-root chain, multi-root sibling tree, nonHomeric flag, external
  vs. known-cross-tree parent resolution, empty-tree case).
- `app/src/pages/genealogies/index.astro` (new page, `/genealogies/`) and
  `app/src/components/GenNode.astro` (new recursive node renderer) — not
  shared-core, but the page reads `apparatus/characters.json` via
  `readFileSync('../apparatus/characters.json', ...)` since that file isn't
  copied into `public/data` by any pipeline stage (it's raw apparatus source,
  not per-work build output) — a deliberate, narrow exception to the
  `public/data/*` readFileSync convention used elsewhere on this page family.
- `app/src/pages/index.astro` — primary nav gained a "Genealogies" link
  (between Odyssey and Search).
- 2026-07-18, mobile tree (John: desktop chart hidden <480px read as "just a
  list"): `shared/lib/genealogy.ts`'s `GenealogyNode` gained `spouses:
  ParentRef[]` (deduped mothers of a node's children — patrilineal invariant
  means "spouse" is always read off a child's mother link, never invented).
  `GenNode.astro` gained a `variant?: 'list' | 'chart'` prop rendering a
  mobile "indented descent chart" (nested `<ul>`s + drawn connector rules,
  spouse cards paired inline) with its own `<style>` block — Astro scopes
  `<style>` to the file that renders the markup, not the caller, so the
  chart's CSS had to live in GenNode.astro itself (discovered the same gap
  already made the pre-existing `.gen-list`/`.gen-card` rules in
  index.astro no-op against GenNode's list markup — latent, harmless only
  because that list has always been sr-only; not fixed, out of this task's
  blast radius). `index.astro`'s breakpoint for hiding the desktop SVG chart
  moved 480px → 700px (measured: Troy's chart is 1664px wide, Olympians'
  1868px, against a 375px phone — no viewport choice fits Priam's row of 8
  or Zeus's row of 9 children, so only a real vertical layout works).

- `shared/lib/data.ts` — `Scene` gained optional `day?: number | null`;
  `normalizeBookData` now carries `apparatus.scenes[].dayNumber → day` (the scene
  rail shows a "Day N" marker); new pure export `activeSceneIndex(scenes, line)`
  (order-independent line→scene mapping for the rail's live current-scene
  highlight). Homer-specific; no plato-reader counterpart.
- `shared/components/Reader.svelte` — new Scene rail (in-book scene-navigation
  flyout): left drawer of the book's scenes, mirroring the Settings-drawer
  island/CustomEvent pattern (`toggle-scenes`/`close-scenes`/`scenes-state`).
  Adds open/close + focus-trap + Esc + arrow-key roving, a rAF-throttled
  scroll scan (`computeCurrentScene`, wired only while open) that drives the
  `aria-current` highlight, and `jumpToScene` (scrollIntoView to the Greek line,
  or the Reading-Mode scene chip). The `sceneChip` snippet gained
  `id="scene-{startLine}"` + `data-line` anchors. No plato-reader counterpart.
- `shared/__tests__/data.test.ts` — new coverage for the `dayNumber → day`
  passthrough and for `activeSceneIndex` (Homer-specific).
- `shared/styles/global.css` — new "Scenes rail drawer" section
  (`.scenes-toggle`, `.scene-rail*`, `.scene-item*`, `.scenes-backdrop`;
  reduced-motion + mobile rules); `.greek-line` and `.scene-chip` gained
  `scroll-margin-top` so rail jumps clear the sticky chrome. No plato-reader
  counterpart.
- `app/src/components/ReaderShell.astro` — header gained a `.scenes-toggle`
  button (gated on `bookData.scenes?.length`), its click→`toggle-scenes` bridge
  and `scenes-state`→aria-expanded sync (mirroring the Settings toggle), and the
  Escape handler now also dispatches `close-scenes`. Homer-specific.

## Maps pages (2026-07-17)

New Homer-only apparatus feature — the four Landmark-style maps (Ships/
Catalogue of Ships explorer, Troad, Wanderings, Greece) at `/maps/`, drawn
from `apparatus/places.json` (274 places) and `apparatus/catalogue.json` (29
Achaean + 16 Trojan contingents). No plato-reader counterpart (Plato's corpus
has no geographic apparatus); listed here because the new pure-logic files
live in `shared/`. First use of `leaflet` in this repo — see the package.json
note below for the justification.

- `shared/lib/maps.ts` — new: pure, DOM-free helpers only (no Leaflet import).
  `placesForMap`/`splitByCoords` (map-tag filtering + located/unlocated split,
  the "not locatable" honesty list); `sortContingents` (catalogue/ships-desc/
  alpha, the panel's sort toggles); `shipCircleRadius` (area-proportional
  circle sizing: radius = maxRadius·sqrt(ships/maxShips), so circle AREA, not
  radius, scales with ship count); `principalPlace`/`placesById` (a
  contingent's first coord-bearing toponym — never invents a position);
  `contingentLocValue` (the reader `?loc=` colon-grammar value for a
  contingent's first line, per `shared/lib/citation.ts`'s
  `formatLocValue` — NOT the dot copy-citation form); `humanizeId`/
  `leaderDisplayName` (Catalogue leader display name: real
  characters.json name when the leader has an entry — only 16 of 73 leader
  refs do — else a humanized id, same posture as `genealogy.ts`'s
  `humanize`); `wanderingsRoute` (the Apologoi Od. 9–12 sea-voyage stations
  in narrative/voyage order for the dashed route line — a documented,
  narrow scope decision: restricted to book 9–12 mentions with coords and
  non-mythical certainty, one explicit exclusion (`zacynthus`, Od. 9.24,
  named in Odysseus's description of Ithaca's neighbors, not a waypoint) —
  other wanderings-tagged places (Ithaca, Sparta, Menelaus's Egypt/Cyprus/
  Libya travels, Ogygia, Scheria) are real pins but not connected, since
  they aren't stations on Odysseus's own voyage).
- `shared/__tests__/maps.test.ts` — new: fixture-based coverage of the above
  plus two regression tests against the REAL `apparatus/places.json` and
  `apparatus/catalogue.json` (the exact wanderings route id order; the exact
  achaean ships-desc order, Mycenae 100 → Symaeans 3, used by the Playwright
  QA pass as its ground truth).
- `app/src/pages/maps/index.astro` (new page, `/maps/`), `app/src/components/
  MapsPage.svelte` (tablist orchestrator: Ships/Troad/Wanderings/Greece, plus
  the Achaean/Trojan sub-tablist), `app/src/components/maps/LandmarkMap.svelte`
  (generic Leaflet canvas: CAWM tiles, certainty-tier marker styling via CSS
  classes — never inline color options, so theme tokens win over Leaflet's
  SVG presentation-attribute defaults — popups built with createElement/
  textContent only, no innerHTML), `app/src/components/maps/
  ContingentPanel.svelte` (fully keyboard-operable sort+listbox+detail panel,
  independent of map mouse interaction) — none shared-core (app-only, like
  `genealogies/index.astro`/`GenNode.astro`); `index.astro` reads
  `apparatus/places.json`/`catalogue.json`/`characters.json` directly via
  `readFileSync('../apparatus/...', ...)`, same narrow exception as the
  Genealogies page.
- `app/src/types/leaflet.d.ts` (new) — `declare module 'leaflet';` ambient
  stub. Leaflet ships no bundled TS types and `@types/leaflet` is out of
  scope (only the `leaflet` runtime package itself was pre-authorized); this
  repo's `npm run build` doesn't run `astro check`/`tsc`, so it's a dev-
  ergonomics aid, not a build gate.
- `app/src/pages/index.astro` — header nav gained a "Maps" link (between
  Genealogies and Search); "The Maps" door now points at `/maps/` instead of
  the Iliad landing-page placeholder it shipped with.
- `app/package.json`/`package-lock.json` — added `leaflet` (exact-pinned
  `1.9.4`, plain Leaflet only — no react-leaflet, no plugins) as a
  **dependency**, not dev: it ships to the built `/maps/` bundle. Justification
  for this repo's one pre-authorized new package: there is no existing
  mapping primitive in the shared reader core, the corpus apparatus has real
  lat/lon coordinates to plot, and Leaflet is the smallest well-maintained
  library that does area-scaled markers + custom tiles + popups without a
  hosted-map-provider API key (CAWM's ancient-world tiles are free/CC BY
  4.0). `leaflet/dist/leaflet.css` and the Leaflet JS are imported ONLY from
  `LandmarkMap.svelte`, which is reachable ONLY from the `client:only="svelte"`
  `MapsPage` island on `/maps/` — confirmed by build-output inspection that
  neither `/index.html` nor `/iliad/book/1/index.html` reference the
  `MapsPage.*.js` chunk (Leaflet is bundled inside it) or make any
  `cawm.lib.uiowa.edu` request; Reader.svelte and global.css were not
  touched by this feature.

## Go-to command palette (Codex lane, Sonnet-verified, 2026-07-17)

- `shared/components/CommandPalette.svelte` — ancestor search-palette extended
  into the Treatment-3 "Go to…": books/scenes/citation sources, Wine-dark
  tokens, dialog a11y kept from ancestor.
- `shared/lib/palette.ts` — ranked 48-book index (new vs plato-reader).
- `shared/lib/citation.ts` — formatLocValue verse-line branch (additive).
- `shared/lib/works.ts` — GREEK_BOOK_LETTERS hoisted here from ReaderShell.
- `shared/__tests__/command-palette.test.ts` — new: Go-to palette coverage
  (Homer-only, no plato-reader counterpart).
- `shared/__tests__/citation.test.ts` — one additive assertion:
  `formatLocValue('iliad', '5', 239)` → `'5.239'` (verse-line loc grammar).

## `?loc=` initial-scroll fix (2026-07-17)

- `shared/components/Reader.svelte` — the `onMount` `?loc=` jump-to-line scroll
  changed `behavior: 'smooth'` → `'auto'` (instant), matching the sibling
  hash-citation path a few lines below (`col-<col>` branch) whose comment
  already documents why: a smooth animation started during `client:idle`
  hydration can be delayed/interrupted by layout churn. The `?loc` path had the
  same risk but was never updated to match; brought in line. No plato-reader
  counterpart (this repo's `?loc` scheme is Homer-only verse-line).

## DICES speech spans (Phase 4 flagship, 2026-07-17)

- `shared/lib/data.ts` — new `Speech`/`SpeechesFile`/`CharacterEntry` types,
  `fetchSpeeches(work)` (per-work, `/data/<work>/speeches.json`, cached) and
  `fetchCharacters()` (whole-corpus, `/data/characters.json`, cached). Both
  lazy — nothing fetches until the reader's Speeches toggle is switched on.
  No plato-reader counterpart (Plato's corpus has no DICES apparatus).
- `shared/lib/speeches.ts` — new, Homer-only: `classifySpeech` (the
  CONFIDENCE DEGRADE RULE predicate — level 0 or a level-1 fully inside a
  same-book level-0 span renders a rail; crossBook / level>=2 / a vulgate-gap
  line / an unresolved speaker always degrades to a flagged marker),
  `realLinesFromSegments`, `humanizeSpeaker`/`speakerDisplayName` (never
  invents an identification — same posture as `shared/lib/maps.ts`'s
  `humanizeId`/`leaderDisplayName`), `speechLabel`. See its module doc
  comment for the "same book" limitation this predicate accepts (level-1
  speeches recorded in a book OTHER than their narrative frame's book — e.g.
  most of Od. 10 and all of Od. 12's speeches — correctly degrade, since the
  data gives no cross-book containment signal).
- `shared/components/Reader.svelte` — new Speeches state block (`speechesOn`
  toggle, persisted like the other reader prefs; `ensureSpeeches` lazy fetch;
  `bookSpeeches`/`bookRealLines`/`speechRenders`/`speechRailLines`/
  `speechRailStarts`/`speechDegradedStarts` reactive maps, all empty — zero
  cost — while the toggle is off). New `speeches-on` class on `.reader-body`.
  New Settings ▸ Speeches row (gated on `epicVerse`, mirrors the existing
  Speakers/Copying `.settings-check-row` pattern) with a `.dices-badge`
  source chip (NOT the draft badge — this data is `status:"imported"`, a
  computed corpus import, not AI-drafted apparatus). Template: a
  `.spk-rail-label` `<p>` before a rail's opening `.greek-line`, a
  `class:spk-rail` binding per line (CSS-only rail, no per-line listener),
  and a `.spk-flag` button (keyboard-reachable, `title`+`aria-label` carry
  the degrade reason) inside a degraded span's opening line. No
  plato-reader counterpart.
- `shared/styles/global.css` — new section: `.reader-body.speeches-on
  .greek-line` reserves a fixed transparent-border gutter (so toggling never
  shifts the line-num column); `.spk-rail` paints it `var(--accent)`
  (wine-dark, no new token); `.spk-rail-label` (small-caps, real text, not
  aria-hidden); `.spk-flag` (absolutely positioned, decorative-icon
  contrast); `.dices-badge` (neutral `--text-light` tone, not `--draft`).
- `scripts/build-public.mjs` — new copy step after the corpus build: plain
  `apparatus/speeches/<work>.json` → `build/dist/<work>/speeches.json` and
  `apparatus/characters.json` → `build/dist/characters.json` (no transform —
  all classification/label logic is client-side in `shared/lib/speeches.ts`).
  `apparatus_speeches.py` writes only the source-of-truth `apparatus/`
  files, so nothing copied them into the public data root before this.
- `shared/__tests__/speeches.test.ts` — new: classification predicate
  coverage (both Apologoi crossBook frames, a clean level-1 inside a
  crossBook parent, the "different book than its frame" honest limitation,
  level>=2, the odyssey-931/Od.10.456 vulgate-gap fixture, an unresolved
  speaker), humanize/label formatting, and real-apparatus regression checks
  against the committed `apparatus/speeches/*.json` / `characters.json`.

## Formula/repetition indexes (Codex lane, Sonnet-verified, 2026-07-17)

- `shared/lib/repetitions.ts` — new: top-N selection/filter helpers
  (Homer-only, no plato-reader counterpart).
- `shared/__tests__/repetitions.test.ts` — new: coverage for the above
  (Homer-only, no plato-reader counterpart).
- `shared/lib/data.ts` — `fetchRepetitions` lazy helper (`fetchCharacters` shape).

## Search result filters: work/book/speaker/speeches-only (Sonnet, 2026-07-17)

- `shared/lib/search-filters.ts` — new (Homer-only, no plato-reader
  counterpart): pure line→speech-span membership helpers (`buildSpanIndex`,
  `speechesAtLine`, `lineInAnySpeech`, `lineMatchesSpeaker`) consumed by
  Search.svelte's speaker/"speeches only" result filters. crossBook spans
  (the two Apologoi frames) match only within their own recorded `book`,
  unbounded past `lines[0]` — never claiming a match in a book they merely
  pass through, since the schema carries no `endBook` (see the file's
  docstring; same "never invent" posture as `shared/lib/speeches.ts`'s
  classifySpeech crossBook degrade).
- `shared/__tests__/search-filters.test.ts` — new: span-membership coverage
  incl. both crossBook frames' honest under-match.
- `shared/components/Search.svelte` — added the "Filter results" row (work /
  book / speaker / speeches-only) above the result list: work+book filter
  the already-fetched result set for free; a speaker or speeches-only filter
  switches to an eager whole-result-set `buildGroups` pass (bypassing the
  per-page pager) so every hit's line number can be checked against a
  `SpanIndex`, built from `fetchSpeeches`/`fetchCharacters` lazily fetched
  only when one of those two filters first activates. URL round-trips `w`/
  `b`/`spk`/`so` via `history.replaceState`. Also fixes a pre-existing,
  previously-undiscovered bug this work exposed: verse-line works (Homer)
  ship an empty `chapters.json` (no plato-reader-style sub-book chapters —
  a Homer book is a single segment; see `fetchBook`), so `buildGroups` could
  never resolve ANY search hit into a chapter group and the results list
  silently rendered nothing (same defect class as the documented Stephanus
  `sectionsToChapters` fix above, just never hit until this task's
  end-to-end verification). New `columnsToChapters` adapts `columns.json`
  (already-existing generic Bekker-column infrastructure, reused since a
  verse-line book's "column" is the whole book) into one synthetic
  whole-book chapter per book; `fetchOutline`/`groupUnitLabel` gained a
  `verse-line` branch alongside the existing `stephanus` one.

## Character network (Feature #20, 2026-07-17)

New Homer-only apparatus feature — kinship + speech co-occurrence graph for
`/characters/`, built pure (no d3) at build time. No plato-reader counterpart.

- `shared/lib/network.ts` — new: pure edge aggregation + deterministic
  force-directed layout (`buildKinshipEdges`, `aggregateSpeechEdges`,
  `layoutNetwork`, participation/degree helpers). Build-time only (consumed by
  `app/src/pages/characters/index.astro`); never fetched at runtime. Both
  ends of every edge must be joined character ids (apparatus honesty).
- `shared/__tests__/network.test.ts` — new: fixture coverage for kinship
  edges (joined / nonHomeric / external-parent exclusion), speech aggregation
  (single speaker+addressee only; self-address excluded), and layout.
- `app/src/pages/characters/index.astro` — new page (`/characters/`); not
  shared-core, but the consumer of `shared/lib/network.ts` (same posture as
  genealogies/maps apparatus pages).

## Hexameter scansion overlay (Feature #19, 2026-07-17)

Homer-only meter apparatus (Plato's corpus is prose). Pure shared helpers +
lazy per-book JSON; no plato-reader counterpart. Concurrent pipeline work
(`pipeline/homer_pipeline/apparatus_scansion.py`) is not listed file-by-file
here (pipeline rename note at top still covers the package).

- `shared/lib/scansion.ts` — new: pure glyph + confidence-honesty helpers
  (`scansionTier` normal/ambiguous/unresolved, `renderFeet`, `formatNotes`,
  `scansionDisplay`, `scansionKey`) consumed by the reader meter overlay.
- `shared/__tests__/scansion.test.ts` — new: tier/glyph/notes coverage
  (Homer-only).
- `shared/lib/data.ts` — `ScansionEntry`/`ScansionFile` types +
  `fetchScansion(work, book)` (lazy per-book cache of
  `scansion-<NN>.json`); further Homer-specific payload surface on top of
  the earlier data.ts entries.

## Mobile reader-chrome fixes (John's phone session, 2026-07-18)

- `shared/styles/global.css` — `@media (max-width: 680px)`: the
  `.reader-controls { display: none; }` rule that hid the ENTIRE sticky
  controls strip (including `.posture-btn`, the only Scholar⇄Reading Mode
  toggle) is replaced with slimmed padding + an enlarged `.posture-btn`
  (min-height 40px); the strip itself stays visible so Reading Mode has a
  touch affordance on phones (previously only the `r` keystroke worked).
  **Superseded same day:** the mobile-only `.toc-book-nav` row added here
  (below) was removed once the Contents drawer's own outline got a proper
  chapterless (verse-line) rendering that works at every width — see the
  ReaderShell.astro entry below and the new `.toc-book-link` rule (next to
  `.toc-book`) for the replacement. No plato-reader counterpart either way
  (Homer-specific; plato-reader's dialogues are chaptered, so its disclosure
  TOC is unaffected — though the underlying "chapterless works get a
  nonsense '0 ch.' disclosure row" defect could recur there for a future
  chapterless work).
- `app/src/components/ReaderShell.astro` — the TOC sidebar's per-book
  outline (`outline.map`, previously always `<details class="toc-book">`
  with an "N ch." disclosure) gained a `verseLine`-gated branch: for
  chapterless verse-line works (Iliad, Odyssey — `chapters.json` is `{}` for
  both epics, so the disclosure always showed a nonsense "0 ch." row whose
  triangle expanded onto nothing and didn't itself navigate) the outline
  instead renders one plain `.toc-book-link` per book, no disclosure, in the
  SAME `.toc-outline` list used at every width (desktop and mobile share one
  Contents drawer). This replaces the earlier same-day `.toc-book-nav`
  hotfix (mobile-only row, now deleted from both this file and
  global.css) — one book list in the drawer, not two, and it now works on
  desktop too where the hotfix never reached. Chaptered works (Plato
  dialogues, via the shared core) keep the original disclosure path
  untouched, gated on the same `verseLine` const already used for the
  book-plate below. Also: cartouche's day meta gained a
  `dayIsTelling` cue (`apparatus.where` containing the pipeline's
  `"(telling)"` frame-scene marker) — renders "Day N · telling" with a
  tooltip instead of a bare, chronologically-misleading number for a book
  narrated in flashback (Od. 9/11's Apologoi frame at Alcinous's palace).
  Known gap: Od. 10/12 share the same flashback day but carry no
  `"(telling)"`-marked scene of their own, so this display-only cue can't
  reach them — needs a data-side fix (apparatus/staging + re-merge), not
  done here.
- `shared/components/Reader.svelte` — same `"(telling)"`-marker day cue
  applied to the scene rail's `.scene-item-day` (book-wide `bookTellingDay`,
  read once from `apparatus.where` — the marker sits on the book-level
  aggregate, never on an individual scene's `location`/`place` — not
  hardcoded to any book number). Same Od. 10/12 known gap as above.
- `shared/lib/data.ts` — `RawBookData.apparatus` gained `draft?: boolean;
  where?: string;` (it only declared `scenes` before; `draft` was already
  being read off it via an untyped cast — this makes that and the new
  `where` read type-correct).
- `shared/lib/scene-paging.ts` — new, no plato-reader counterpart: the pure
  `chunksForScene` function (+ `TickChunkRange`/`SceneRange` types)
  reconciling a scene's apparatus line range against the ~5-line Murray
  tick chunks Reader.svelte's `alignGroups` derives — the core of Reading
  Mode's scene pagination (John, 2026-07-18).
- `shared/components/Reader.svelte` — Reading Mode now PAGES BY SCENE
  instead of rendering a whole book as one scroll (John's directive,
  2026-07-18; no plato-reader counterpart — that fork's Reading Mode still
  shows the whole book). `alignGroups` gained a second `flow` parameter
  (default `block.flow`, byte-identical for its one pre-existing call site)
  so the new scene chunker can page a non-primary translation (Butler/Pope)
  by its own ticks. New state (`readingSceneIndex`, `?scene=` URL sync),
  new `gotoScene`/`prevScene`/`nextScene`/`scrollReadingToTop`, ←/→
  keyboard paging in `onGlobalKey`, and `setReading` now seeds/exits the
  scene position via `computeCurrentScene`/`jumpToScene`. REMOVED (dead
  after the pagination change, no other consumer): the marginal `sceneChip`
  snippet, `scenesForSegment`, and `positionSceneChips` (+ its `afterUpdate`
  and `onResize` calls) — replaced by a `.reading-scene-head` page header.
  `jumpToScene` is now the shared jump-list handler for both postures
  (pages in Reading Mode, scrolls in Scholar).
- `shared/styles/global.css` — removed the `.scene-chip`/`.scene-lines`/
  `.scene-place`/`.scene-summary`/`.scene-people` rules and their
  1400px-margin layout (dead with the chips gone); added
  `.reading-scene-head`/`.reading-scene-pos`/`.reading-scene-meta`/
  `.reading-scene-day`/`.reading-scene-place`/`.reading-scene-summary`/
  `.reading-scene-nav` + prev/next button styles for the new scene-paged
  Reading Mode. `.draft-badge` base rule kept (still used by the scene rail
  and cartouche).
- `app/src/components/ReaderShell.astro` — comment-only: the `scenes`
  normalization note updated for scene-paging (no longer "marginal chips").
- `shared/styles/global.css` — scene-map land/sea tokens (2026-07-18):
  `--scene-map-sea/-land/-coast/-label-halo` declared in all four theme
  blocks; Homer-only (Chart Room panels), no plato counterpart.
- `shared/styles/global.css` — Flaxman art layer (2026-07-18 launch night):
  `--flaxman-ink` in all four theme blocks + `.plate-art` cartouche plate
  rules. Homer-only.
- `shared/components/Reader.svelte` + `shared/lib/tick-chunks.ts` (2026-07-21,
  Codex review F1) — extracted the tick-chunking core (`flowParts`,
  `groupFlowByTicks`, `isTickPart`, `alignGroups`, `AlignGroup`, `TickFlowPart`)
  VERBATIM out of Reader.svelte into the new pure `shared/lib/tick-chunks.ts`,
  so the Reading-Mode scene-paging audit/tests measure the SAME geometry the
  component renders. Reader.svelte now imports them (`alignGroups` takes
  `block.lines` explicitly, no `block.flow` default); no plato-reader
  counterpart to `tick-chunks.ts`.

## Merged nav bar — three chrome bands to two (2026-07-25)

A reader's screenshot showed the Books 1–24 strip wrapping to a second row, so
three bands of chrome ate ~225 CSS px before line one (a third of a landscape
iPad's height). The Books strip is deleted, the third controls row is merged up
into the nav bar, and Print moves into the Settings sidebar. Homer-specific
throughout — plato-reader has no Books strip and its controls row is untouched.

Tiers: **≤690px** phone arrangement (no control row; Contents/Scenes in the
header; controls in Settings). **691–1039** control row, icon-only, `Reader ⇄`
action posture, `Jump to…` from 775. **≥1040** full labels with icons, segmented
`Scholar | Reader`. Short-landscape (`orientation: landscape`, `max-height:
500px`) strips the control row and puts Contents+Scenes beside the work switcher.

- `app/src/components/ReaderShell.astro` — Books 1–24 strip deleted (the
  Contents drawer already lists all books). `.nav-panel` gained
  `.nav-panel-inner` → `.nav-group-left` (Contents, Scenes, `Jump to…`,
  `‹ Book N ›` stepper) + `.nav-group-right` (translation `<select>`,
  Greek/Both/English, posture, Chart Room), all SERVER-RENDERED and wired to the
  `Reader.svelte` island by new `window` CustomEvents (`set-trans`/`set-view`/
  `toggle-reading`/`toggle-chart-room` in; `*-state` back), mirroring the
  pre-existing `toggle-settings`/`toggle-scenes` bridge. The head `is:inline`
  bridge that stamped `data-rview` now also stamps `data-rposture`, so FIRST
  PAINT is honest about posture (previously it always painted Scholar and
  exposed Chart Room, then flipped at hydration). New `window.__navPrehydrated`
  records the VALUE of any click made before hydration. `.header-title`'s
  flex-grow is zeroed inside the short-landscape query so Contents/Scenes land
  next to the work switcher rather than the title box's invisible far edge.
- `shared/components/Reader.svelte` — `.rc-desktop-controls` removed from the
  desktop path (its markup now lives in ReaderShell); listeners for the four new
  events plus matching `*-state` broadcasts. `onMount` gained ONE choke point
  that applies `window.__navPrehydrated` AFTER all URL/storage handling, so a
  pre-hydration click beats `?view=`/`?trans=`/`?mode=`/`loc`/`hlg` — deliberately
  a single site rather than a guard at each URL reader (four scattered guards
  were tried first; two were forgotten, caught in review). `setReading` now
  closes Chart Room (the rail requires `!reading`, so it otherwise left a
  dangling `aria-controls`). `colScale` was briefly mirrored onto
  `document.documentElement` as `--colw-scale` to feed `.nav-panel-inner`'s
  now-removed width cap (see below); that mirror is gone as of 2026-07-26 —
  it had no remaining consumer once the cap was removed.
- `shared/components/BekkerJump.svelte` — new optional `toggleLabel` prop,
  default `null`. Homer's nav-bar instance passes `Jump to…`; every other call
  site, including the sibling forks, is byte-identical. **Do not remove the
  nullish fallback** — it is what keeps this shared component inert elsewhere.
- `shared/styles/global.css` — new `.nav-panel-inner`, a flex container
  (`justify-content: space-between`) for the two groups (the tinted band
  still spans full width). It was initially capped at `calc(1080px *
  var(--colw-scale, 1))` and centred, so at wide viewports the two groups
  aligned with the READING COLUMN's edges rather than the row's own —
  requiring `--colw-scale` (normally set only on `.reader-body`, inside the
  island) to also be published on the root element for the header to read
  it. **John's call, 2026-07-26: corrected to flush-left/flush-right on the
  ROW's own outer edges instead** — they now line up with the header bar's
  wordmark and Support button, sharing one set of edges with the band
  above. The max-width cap, the `margin: 0 auto` centring, and the
  root-level `--colw-scale` publication (Reader.svelte) are all removed;
  the control row is now completely unaffected by the column-width slider.
  New `--nav-panel-bg` (light: a faint `color-mix`
  tint so the band reads against the header; dark: `var(--col-bg)`, i.e.
  unchanged from before this work). Tier boundaries moved 680/681 → 690/691 and
  the label tier to 1039/1040; ELEVEN rules deliberately LEFT at 680 (reading
  typography, touch targets, glossary bottom-sheet, sidenote rail, TOC-drawer
  dedup) — they merely reuse the number and are not part of this arrangement.
  Previously-known behaviour, no longer applicable after the 2026-07-26
  correction above: at the minimum column-width setting (0.8) the full-label
  row used to wrap to two lines, since the capped measure was narrower than
  the row needed. With the cap gone the row is unaffected by the slider at
  any setting.
- `app/src/components/HelpButton.svelte` — compact-header breakpoint moved with
  the rest (it was missed in the first pass, leaving a hybrid header at
  681–1099 where every other control had gone compact but `?` had not).
- `shared/__tests__/components.test.ts` — new describe block covering the four
  nav-bar bridge events, mirroring the existing `toggle-settings` test.
- Found but NOT fixed here (out of blast radius, logged separately): the header's
  `.header-search` button wraps its own label onto two lines between ~900 and
  1022px, a pre-existing flex-shrink squeeze. Unreachable at the 1040 boundary,
  but it will resurface if that boundary ever moves down.

## Lexicon — one box per dictionary-level homonym (Homer, 2026-07-27)

- `shared/components/LexiconPanel.svelte` — the analysis cards are now derived
  (`toCards`) instead of iterating `analyses` directly. A single analysis can
  carry several LSJ keys (2,335 across the corpus) and only `lsj[0]` ever
  reached the screen, so ἔχω¹ "have, hold" hid ἔχω² "bear, carry, bring" behind
  one card. A homonym earns its own box only when it brings its OWN distinct
  short definition: 1,462 analyses split into 3,061 boxes over 890 token-keys,
  while ὅς¹/ὅς² (no derived definition either side) stay a single box rather
  than print the shared Morpheus gloss twice. Homonyms share a headword, so
  boxes carry the LSJ index as a `<sup class="homonym">`.
- `shared/lib/data.ts` — `LsjEntry` gained optional `short?: string`, LSJ's
  one-line sense for that key. Previously derived at stage 5 into
  `short_defs.json` and used only to extend Morpheus glosses; it is now shipped
  on the entry, because a per-homonym box needs a per-homonym definition.
- `shared/styles/global.css` — new `.analysis-card .lemma .homonym` rule. It
  inherits the `.lemma` accent colour, so contrast is unchanged in both themes.
- `pipeline/homer_pipeline/stage5_lsj.py` — the LSJ shard entry carries `short`
  alongside `key`/`head`/`html`. `short_defs.json` is unchanged, so
  `merge_short_def` behaves exactly as before.
- The ambiguity guard (739b6cefc) was reviewed and KEPT. Against real stage4
  input it refuses zero times in 1,085 multi-key parses — it is defensive only,
  so the split cannot have made it obsolete. It still covers the surfaces that
  have no boxes and take one gloss per lemma (`apparatus_vocab.lemma_gloss_map`,
  `app/scripts/build-lemmata.mjs`).
