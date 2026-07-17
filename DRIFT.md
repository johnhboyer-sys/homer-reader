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

Not shared-core but worth noting here since it touches every pipeline
reference across the repo: `pipeline/plato_pipeline/` was renamed to
`pipeline/homer_pipeline/` (directory + all imports/docstrings/tool scripts),
and `pipeline/pyproject.toml`'s project name changed `plato-pipeline` →
`homer-pipeline`. Not file-by-file listed here since it's a mechanical,
repo-wide package rename rather than incremental content drift.
