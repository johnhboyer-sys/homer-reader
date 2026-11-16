# Porting Aristotle's new search into Homer: plan of record

Started 16 Nov 2026 on `claude/search-port`. Source: aristotle-reader `origin/main` at `7ddd67b7ef` (PR #195,
the redesign search, plus PR #197, chapter counting). Groundwork: `diff-map.md`, `README.md` (PR #64).

## John's rulings (16 Nov)

1. **Count by scene, Greek and English together.** The reader's scenes (`apparatus/scenes/<work>.json`, 790
   scenes) take the place of Aristotle's chapters. "And" means both terms in the same scene.
2. **Aristotle's search layout, in Homer's own theme.** Port the page and `b-search.css`; take colours, type and
   tokens from Homer's `global.css`, not from Aristotle's `b.css`.
3. **"and/or" is the default join** (John, 16 Nov, for every reader: "make 'and/or' the default setting for when
   search loads (it naturally suggests they can do greek only or english only OR both...)"). Wherever Greek and
   English are joined, the page loads with the inclusive or, labelled "and/or", and "and" stays on offer. How old
   links with no `op` keep their meaning is being settled in aristotle-reader: follow its answer, do not decide it
   here.

## Design

- **Scenes enter as chapters.** Aristotle places every hit with `chapterPlaces` (`shared/lib/chapter-pages.ts`),
  which reads two things per work: `chapter_bounds` in `search/offsets.json` (`{book, chapter, start}`, `start`
  a global Greek token offset) and `search/eng-chapters.json` (`{slot: {seg_idx: [[word, chapter], …]}}`, where
  each translation's word count starts a chapter). Homer's build writes both from the scenes, so the counting
  code ports unchanged. A scene's `chapter` name is its line range, `"<start>-<end>"` (ASCII hyphen).
- **English follows the reader's pages.** The reader already splits each translation at scene edges
  (`shared/lib/scene-paging.ts`, with `scene-boundary-overrides.json`). `eng-chapters.json` is computed by a Node
  build step that imports that module, so an English word is counted in the scene whose page shows it. Where a
  chunk shows on two pages, the word goes to the scene its estimated line falls in (interpolated between the
  translation's line marks).
- **One search index per translation**, with word positions, as Aristotle has: `english.json` (Murray),
  `english-ross.json` (Butler), `english-third.json` (Pope), `english-overlay-kosmos.json` (Kosmos), each
  `{word: [[seg, pos], …]}`. Homer's search segments stay one per book.
- **Homer keeps what only it has:** book filter (`b`), speaker filter (`spk`), speeches only (Homer's `so`
  collides with Aristotle's sort order: rename one, keep old links working), the one-book grammar panel (`gr`),
  "find it under any dictionary form", book.line citations, links into the reader.
- **Things the port fixes on the way:** hyphenated English queries (`englishFold`), English rows citing the
  book only, raw footnote marks in English snippets.

## Lanes

| Lane | Files | Depends on |
|---|---|---|
| A. Data build | `pipeline/homer_pipeline/stage6_search.py`, a new `app/scripts/` build step, `scripts/build-public.mjs`, preflight | — |
| B. Engine | `shared/lib/` (search.ts on Aristotle's file + Homer's 17 hunks, new files copied whole, works/data/citation merges), `shared/__tests__/` | — |
| C. Page | `shared/components/Search.svelte` (Aristotle's file + Homer's features), `SavedSearches.svelte`, `app/src/pages/search*` | A's data shape, B |
| D. Styles | `shared/styles/b-search.css` on Homer's tokens | C |

A and B run at once in separate worktrees. Every lane: tests first for each behaviour it adds; Homer's own
tests stay green or are replaced with a reason. Review: a Codex (GPT-6.1-Sol, medium) pass on A+B and on C+D.

## Proof

- `docs/search-port/search-counts.mjs` re-run after the port; every moved count explained (most move on
  purpose: the unit is now the scene).
- Unit counts from `unit-counts.py` (scene column) agree with the new bar: θάλασσα + sea gives 86 scenes and 111
  Greek words, give or take the English placement rule above.
- Screenshots at 390, 360, 844 and 1440, both themes, old against new, for John.
- `npm run build:public` passes: preflight, link check, 0 broken.
