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
