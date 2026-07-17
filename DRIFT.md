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
  `app/src/components/{LemmaPage,WorkSwitcher}.astro` — title/meta/JSON-LD/
  home-link Plato→Homer strings; 404's Meno-geometry joke replaced with an
  Odyssey/nostos-themed one (same structure, different classical reference,
  no fabricated quotations); Google Fonts links removed from all.
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
- `app/public/{manifest.webmanifest,offline.html,robots.txt,sw.js}` — PWA
  name/short_name/description, offline-page title + hardcoded colours (now
  the Aegean ground/ink hex), sitemap URL, and the service worker's cache-key
  prefix (`plato-reader-`→`homer-reader-`, a fresh cache namespace post-deploy,
  harmless) — all Plato→Homer. Not `shared/`/`app/src`, but clearly
  in-scope for a rebrand pass (PWA install name, offline page) and low-risk.
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
