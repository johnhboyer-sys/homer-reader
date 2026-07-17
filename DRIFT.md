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
- `app/astro.config.mjs` — `site` set to placeholder `https://example.invalid`
  (`// TODO real domain (John)`); `base` changed from `/plato-reader` to `/`
  (GitHub Pages one-off, domain root, no Cloudflare/R2 — John, 2026-07-17).
- `scripts/build-public.mjs` — env var override renamed `PLATO_PY` →
  `HOMER_PY`; internal `plato_pipeline` module-invocation strings renamed
  `homer_pipeline` (tracks the `pipeline/` package rename below).

Not shared-core but worth noting here since it touches every pipeline
reference across the repo: `pipeline/plato_pipeline/` was renamed to
`pipeline/homer_pipeline/` (directory + all imports/docstrings/tool scripts),
and `pipeline/pyproject.toml`'s project name changed `plato-pipeline` →
`homer-pipeline`. Not file-by-file listed here since it's a mechanical,
repo-wide package rename rather than incremental content drift.
