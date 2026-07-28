# Advanced search — Step 6 (client) implementation plan

Recon by Opus 5, 2026-07-28, read-only against the repo as it stood. Companion to
`docs/advanced-search-handoff.md` (which this plan does not repeat). Homer paths
are relative to the repo root; Aristotle paths are marked `A:` and are
**read-only reference** (`~/Developer/aristotle-reader`).

---

## 1. Homer-only surface that a wholesale port destroys

| # | Capability | Anchor | Why the port kills it |
|---|---|---|---|
| H1 | `englishOccurrences(text, terms, mode)` — **exported**, returns one char offset per English occurrence | `shared/lib/search.ts:161-179` | A: has only `engPhraseMatches` (boolean, `A:272`). No offsets ⇒ no English KWIC, no English instance count. |
| H2 | `SearchResult.engPositions: number[]` | `search.ts:191`, produced `search.ts:331-333` | A's `SearchResult` (`A:297-307`) has no such field. Consumed at `Search.svelte:594, 677-682`. |
| H3 | `SegMeta.greek_tokens` (space-joined fold sequence) | `search.ts:29`; emitted `pipeline/homer_pipeline/stage6_search.py:165` | A's `SegMeta` (`A:23-29`) lacks it. Handoff §1: "do not fix". Test fixtures rely on it (`shared/__tests__/search.test.ts:5-7`). |
| H4 | `search()` returns `SearchResult[]` | `search.ts:339-376`; caller `Search.svelte:789` | A returns `SearchOutcome` (`A:1160-1201`). Straight swap breaks the only caller. |
| H5 | Speaker / "speeches only" result filters | `shared/lib/search-filters.ts` (all 69 lines); wiring `Search.svelte:92-106, 108-168, 193-225, 249-257` | Not in search.ts, but `applyResultsPipeline` is entangled with `rawResults`/`instCount`/`paginate`. |
| H6 | Accent-sensitive post-filter | `Search.svelte:276-290`, applied `Search.svelte:659-667` | Depends on `grkPositions` being indices into the **flattened surface token list** of `seg.greek`. |
| H7 | URL state round-trip (`g,e,w,b,spk,so`) | `Search.svelte:262-274, 750-768` | A has no filter params. |
| H8 | CSV export of the whole filtered set | `Search.svelte:868-931` | A's is narrower; Homer's carries the column-order fix. |
| H9 | Work/book filters + `zeroResultHint` | `Search.svelte:78-91, 170-175, 229-236` | — |
| H10 | Verse-line citation composition (`formatCite`/`formatLocValue` → `9.366`) | `shared/lib/citation.ts:183-200`; used `Search.svelte:651-652` | A hardcodes `${column}:${line}` in Phrases.svelte (`A:581`). |

**Scansion / epithets / repetitions / scenes**: verified — `Search.svelte` has **no**
hooks to any of them. Those live in `RepetitionsIndex.svelte`, `FormulaLedger.astro`,
`/formulas`, `/repetitions`. Step 6 does not touch them. (Handoff §1's table lists
them as *shipped*, not as search-path features.)

**`search-filters.ts` posture — preserve verbatim** (`search-filters.ts:11-23`), the
load-bearing sentences: "a crossBook speech only ever matches lines in its own
recorded `book`, from `lines[0]` onward with NO upper bound", and "This under-matches
the true span rather than over-claiming one". Do not touch the file;
`shared/__tests__/search-filters.test.ts:66-90` is the contract.

---

## 2. API delta

**Add (Aristotle-only):** `Offsets`, `OffsetRef`, `offsetRef`, `GrammarDict`,
`GrammarQuery`, `SearchOutcome`, `searchGrammar`, `VARIANT_READING_CAP`,
`VariantOutcome`, `lemmaOptions`, `lemmaReadings`, `searchPhraseVariants`, `SlotKind`,
`SlotRelation`, `ComboSlot`, `WindowUnit`, `ComboOptions`, `COMBO_WINDOW_DEFAULT`,
`COMBO_WINDOW_MAX`, `ComboHit`, `comboWindows`, `searchCombo`. Plus private
`loadShared`, `loadBinary`, `compilePattern`, `englishFold`, `phraseStarts`, `locate`,
`unitRange`, `lowerBound`, `lineStarts`, `resolveHeadwords`.

**Must survive (Homer-only):** `englishOccurrences` (H1), `SearchResult.engPositions`
(H2), `SegMeta.greek_tokens` (H3).

**In both, differing — the real risk:**

| Symbol | Homer | Aristotle | Resolution |
|---|---|---|---|
| `search()` | → `SearchResult[]` (`:339`) | → `SearchOutcome` (`A:1160`) | Adopt A. Update `Search.svelte:789` to destructure and render `failedWorks` (copy A's notice, `A:1527-1532`). |
| `SearchResult` | `+engPositions` | `+grammar?` | Union of both fields. |
| `searchWork`/`greekPositions` | `grkTerms: string[]`, `greekPositions(idx, meta, …)` | `string[][]`, no `meta` | Adopt A wholesale; keep the English branch from Homer (`:294-308, 331-333`). |
| Greek phrase check | `phraseMatches` over `meta.greek_tokens` (`:145, 224-237`) | `phraseStarts` over postings (`A:255-269`) | **Adopt A** — see Trap T1. `greek_tokens` stays in `SegMeta` and in meta.json, unused by search.ts. |
| Wildcards | prefix `*` only (`:105-120, 205-212`) | `compilePattern`: `*` anywhere + `?` (`A:166-200`) | Adopt A; strictly wider. |
| English phrase | `englishOccurrences(…,'phrase')` filters hits AND yields offsets (`:303`) | `engPhraseMatches` boolean | **Keep Homer's.** Port A's `?`-wildcard handling into `engMatchTerm` only if free. |

**Places assuming Bekker columns or a non-empty `chapter_bounds`:**

- `A:888` `chapStarts = offsets.chapter_bounds.map(...)`, `A:907, 909` — with Homer's
  empty array, the `chapStarts.length` guards already no-op. Consequence: the **"Same
  chapter" unit and "Keep hits that cross a chapter" checkbox become silently inert**
  (`A:1339-1348`). Delete both controls from Homer's UI; keep the `ComboOptions`
  fields to hold divergence down.
- `A:1112-1124` `approximateChapters` — unreachable with empty bounds; leave the code,
  never populate, drop the notice at `A:1534-1537`.
- `A:459` `OffsetRef.column` — for Homer `seg.column === String(book)` (verified:
  stage3 segment `id "1:1"`, `book 1`, `column "1"`). **Keep the field**: it lets
  href-building go through `formatLocValue(work, ref.column, ref.line)` with no fork.
- `A:776-780` `COMBO_WINDOW_DEFAULT = 5` — comment justifies it as "half a Bekker line
  (9.5 tokens/line)". Measured for Homer: **7.2 tokens per verse** (87,189 tokens /
  12,107 lines, Odyssey). Keep 5; rewrite the comment with the Homeric figure. Do not
  ship the Bekker rationale.
- `A:762` `WindowUnit = 'words' | 'line' | 'chapter'` — for Homer `'line'` means "same
  verse" and is the *interesting* default (handoff §3, §4). Relabel in the UI; keep the
  type value.
- `A:1062-1066` combo's "a window can straddle a column boundary" comment — impossible
  in Homer (segment == book, and a window never crosses a book). Simplification, not a
  bug; correct the comment.

---

## 3. `offsetRef` rewritten for `book.line`

```ts
export interface OffsetRef { seg_idx: number; pos: number; book: number; column: string; line: number }

export function offsetRef(offsets: Offsets, global: number): OffsetRef | null {
  const base = offsets.seg_base_offset;
  if (!base.length || global < 0 || global >= offsets.token_count) return null;
  const [seg_idx, pos] = locate(base, global);          // A:518, unchanged
  const seg = offsets.segments[seg_idx];
  if (!seg) return null;
  let left = pos;
  for (const [line, count] of seg.line_runs) {          // line is the EMITTED number
    if (left < count) return { seg_idx, pos, book: seg.book, column: seg.column, line };
    left -= count;
  }
  return null;                                          // build defect — never guess
}
```

The shape is A's; what changes is everything downstream: the caller composes
`formatLocValue(work, ref.column, ref.line)` → `"9.366"`, never `${column}:${line}`.

**Edge cases the tests must cover:**

1. **Numbering gaps.** Measured in the current Odyssey build: 3 gaps — after 10.455,
   16.100, 23.48. `line_runs` stores the emitted `n`, so runs are simply
   non-consecutive; the walk uses **no index arithmetic**. Test: an offset in Od. 10
   past the gap resolves to 457, not 456.
2. **Athetized / bracketed lines.** Same mechanism — they carry their own `n` and their
   own token count; they are ordinary runs. A test asserting one resolves to its
   bracketed number.
3. **Zero-token line** (`count === 0`): `left < 0` is false, so the run is skipped and
   can never own an offset. Correct. (Currently 0 such lines in the Odyssey — assert
   the behaviour anyway, it is cheap.)
4. **Segment boundary.** `locate` returns the greatest `i` with `base[i] <= global`, so
   `global === base[i]` lands in segment `i`, not `i-1`. A zero-token segment sharing a
   base is skipped in favour of the following one. Test both edges of a book.
5. **Keyless token.** The offset space counts every stage-3 token
   (`stage6_search.py:111` increments `pos` unconditionally; `line_runs` must use
   `len(l["tokens"])`, matching `A:275`). Measured: **0 keyless tokens in the Odyssey
   build** — so this is latent, not live. The resolver must not depend on that; a
   synthetic fixture with a keyless token proves it.
6. **Fingerprint.** `token_count` must equal `Σ line_runs[..][1]`. The client already
   throws on `token_count` disagreement (`A:538, 546`) — keep, and add the same check
   to `offsetRef`'s callers.
7. **Never mix works.** `offsets.json` is per work; a phrase's occurrence list is keyed
   by work (`A:530-546`).

---

## 4. Component plan

**`shared/components/Search.svelte`**

- `doSearch` (`:789`): `const { results, failedWorks } = await search(...)`;
  `rawResults = results`. Add the incomplete-results notice (`A:1527-1532`). Everything
  from `:193` (`applyResultsPipeline`) down stays as-is.
- Add exactly two `<details>` panels, both with **`bind:open`** (`A:1189, 1212` —
  two-way; a one-way binding collapses them as the user types):
  - **"Single dictionary word"** (A's `lemma-panel`). Label: "Every form of one word" —
    no "lemma", no "headword" in the visible copy (handoff §5).
  - **"Two things near each other"** (A's `combo-panel`). Slot kinds labelled *Phrase /
    Exact spelling / Any form of this word / Grammar*. **Grammar exists only as a slot
    kind — never a standalone panel** (§5: A's standalone returned 33,504 hits). Do not
    surface `searchGrammar` in the UI even though it is exported.
  - Unit selector: **Words / Same verse** only. Delete "Same chapter" and the
    cross-chapter checkbox (§2).
- Add the "find it under any dictionary form" widening button (`A:85-132`,
  `searchPhraseVariants`), gated on a multi-word Greek query.
- **Lemma search must accept an inflected form**: this is in `resolveHeadwords`
  (`A:1142-1156`), reached from `search()` when `matchMode === 'lemma'`. It is free with
  the port — but it silently no-ops unless step 4 emitted `lemma-map/<letter>.json`.
  Verify with a real inflected query, not a unit test alone.
- **Snippets go through the shared sanitizer**: `highlightPrefixMatches` at
  `shared/lib/text.ts:13` (which escapes via `text.ts:2` and regex-escapes via
  `escapeRe`, `text.ts:5`). Homer already routes English through it
  (`Search.svelte:848-850`); Greek KWIC uses the local `esc` (`Search.svelte:852-854`).
  **Every new panel's snippet path must use one of those two — no new `{@html}` sink.**
  Add a case to `shared/__tests__/security.test.ts`.
- Keyboard: the Greek-token popup path is in `Reader.svelte`, untouched. New selects
  and checkboxes need visible focus rings in both themes; run the existing
  `shared/__tests__/a11y.test.ts` pattern over the new controls.

**`shared/components/Phrases.svelte` (new)**

- Port A's file, with these Homer changes:
  - **Data-root override**: A's `fetchWorkOffsets` (`A:496-508`) calls
    ``fetch(`${BASE_URL}/data/${work}/search/offsets.json`)`` directly — it **bypasses
    the override**. Homer's rule (CLAUDE.md) forbids that. Route it through `data.ts`'s
    `ROOT()` (`shared/lib/data.ts:504-505`) — add `fetchOffsets(work)` there beside the
    new `fetchNgramShard`/`fetchNgramOccurrences`/`decodeOffsets` (A's are at
    `A:data.ts:350-412`).
  - Citations: `formatCite`/`formatLocValue` from `shared/lib/citation.ts`, not string
    concat.
  - **Within-one-verse toggle** (handoff §3): after `decodeOffsets`, filter occurrences
    whose whole span sits inside one `line_runs` entry. Reuse `lineStarts(offsets)`
    (`A:851-858`) + `unitRange` (`A:826-835`): keep an occurrence iff
    `unitRange(lines, g, total)` contains `g + n - 1`. Default **on** for the
    `form`/`lemma` streams (Homeric formula is a within-verse phenomenon); off for
    `english`. Never filtered at build time.
  - English stream: A resolves English offsets via `fetchEnglishSegments`
    (`A:544, 552-570`) to a column with `line: null`. Homer's column is the book, so an
    English phrase cites the book, not the verse. Say so in the UI copy.

**`app/src/pages/phrases.astro`** — mirror `app/src/pages/search.astro:1-20` (Homer
uses `SiteHeader.astro`, not A's hand-rolled `simple-header`). Add
``{ label: 'Phrases', href: `${base}/phrases/`, prefix: '/phrases' }`` to
`app/src/components/SiteHeader.astro:23-35`. Must contain **one sentence**
distinguishing it from `/formulas`: roughly *"/formulas lists the fixed
epithet-formulas the apparatus identifies by lemma; this page lists every
word-sequence that simply recurs, however spelled and wherever it falls in the
verse."* (§3 — own this prose; do not leave it to the implementer's improvisation.)

**`app/src/pages/advanced.astro`** — guide page, same shell. **Every number generated
or verified against the built corpus** (§5): put them in one `const corpus = {…}` block
as A does (`A:advanced.astro:26-31`), sourced from `Σ token_count` over
`search/offsets.json` and `streams.*.kept` in `build/dist/ngrams/summary.json`. Add both
`/advanced` and `/phrases` to the header nav.

---

## 5. Build sequence

Prereq: handoff steps 1–5 landed (`offsets.json`, `grammar-*`, `lemma-map/`, `ngrams/`
present in `build/dist`). Every gate: `nvm use 22` first; vitest run **from `shared/`**.
Corpus-reading tests use `path.resolve(process.cwd(), '../app/public/data')` and
`ctx.skip()` loudly.

| # | Task | Files | Gate | Parallel? |
|---|---|---|---|---|
| 6a | Port A's `search.ts` into Homer's, preserving H1–H4: A's loaders, `compilePattern`, `phraseStarts`, `SearchOutcome`, `resolveHeadwords`, combo/variant/grammar engines + Homer's `englishOccurrences`, `engPositions`, `SegMeta.greek_tokens` | `shared/lib/search.ts` | `npx vitest run search` green **unchanged** (`shared/__tests__/search.test.ts`), incl. the two English-occurrence integration cases (`:117-146`) | serial (everything depends on it) |
| 6b | `offsetRef` for `book.line` + tests | `shared/lib/search.ts`, new `shared/__tests__/offset-ref.test.ts` | New tests cover §3 cases 1–6; one asserts Od. 10 past-gap → 457 | after 6a |
| 6c | Port A's `combo.test.ts` | `shared/__tests__/combo.test.ts` | green | ∥ with 6d, after 6a |
| 6d | `data.ts` additions: `fetchNgramShard`, `fetchNgramOccurrences`, `decodeOffsets`, `fetchOffsets`, `NgramRow`, `NgramStream` — **all through `ROOT()`** | `shared/lib/data.ts` | `vitest run data` green; grep proves no `fetch('…/data/` literal outside `data.ts` | ∥ with 6c |
| 6e | `Search.svelte`: `SearchOutcome` call-site, `failedWorks` notice, two `bind:open` panels, no standalone grammar, no chapter unit | `shared/components/Search.svelte` | `vitest run components a11y security` green; `search-filters.test.ts` **untouched and green**; manual: speaker-filtered query still returns hits | after 6b |
| 6f | `Phrases.svelte` + within-verse toggle | new `shared/components/Phrases.svelte` | `npm run build` in `app/`; toggle changes the count on a known enjambed phrase | after 6d + 6b |
| 6g | `/phrases` + `/advanced` pages, header nav | `app/src/pages/{phrases,advanced}.astro`, `app/src/components/SiteHeader.astro` | `npm run build:public` — **0 broken links** | after 6e + 6f |
| 6h | Handoff §6.6 deliverable: one paragraph in `docs/APPARATUS-SCHEMAS.md` on phrase-index vs repetitions vs epithets | `docs/APPARATUS-SCHEMAS.md` | John reads it | ∥ any time |

Serial spine: **6a → 6b → 6e → 6g**. Parallel: 6c ∥ 6d after 6a; 6f after 6d+6b; 6h any
time. Do not run 6g's `npm run build:public` while a pipeline lane is regenerating
`build/dist` (CLAUDE.md concurrency gotcha).

---

## 6. Traps the handoff does not mention

- **T1 — `greek_tokens` is not in `token_pos` space.** `stage6_search.py:72-87` builds
  the fold sequence with `if stored: … elif key: …` and **no else**, so a keyless token
  contributes nothing; the posting loop at `:95-111` increments `pos` for **every**
  token. Any segment with a keyless token makes Homer's existing Greek-phrase highlight
  positions off by N. Measured: 0 keyless tokens in the current Odyssey build, so the
  bug is latent. Porting A's `phraseStarts` (posting-based) fixes it by construction —
  **that is a reason to port, not to patch**. Second defect in the same block:
  `fold_seq_by_id` keeps only `lemmata[0]` (`:82`) while `lemma_posts` indexes every
  analysis (`:107-110`), so `greek_tokens` phrase matching is narrower than the postings
  it filters. Do not preserve either behaviour.
- **T2 — the data-root bypass is in the file being copied.** `A:Phrases.svelte:499`
  fetches `offsets.json` with a raw `fetch(BASE_URL + '/data/…')`. Copying it wholesale
  violates Homer's hard rule. Fix at copy time, not in review.
- **T3 — `__ARISTOTLE_DATA_ROOT__` is the override key in Homer too**
  (`shared/lib/data.ts:505`, `search.ts:18`). A fork leftover, but it is the *live
  contract* between `data.ts` and `search.ts`. Do not "correct" it to
  `__HOMER_DATA_ROOT__` in this PR — that is a separate, whole-repo rename.
- **T4 — the accent post-filter constrains `grkPositions` semantics.**
  `Search.svelte:659-667` indexes the flattened `seg.greek` surface tokens by
  `grkPositions[i]`. A's `phraseStarts`/`termPositions` yield the same space (every
  token counted), so this survives — but any future "compress out keyless tokens"
  optimisation silently corrupts it. Add a comment, and one test that a phrase hit's
  `grkPositions` index the full token list.
- **T5 — Homer's segment *is* the book.** 24 segments/work,
  `column === String(book)`. A's combo code comments about windows straddling columns
  (`A:1062-1066`) and its `book_bounds` dedupe loop (`A:283-286`) are no-ops here.
  Harmless, but the comments will mislead the next reader — correct them.
- **T6 — `paginate` sorts by `meta.book` only** (`Search.svelte:696-698`), which for
  Homer means one block per segment. Fine today; if step 1 ever splits books into
  sub-segments, pagination and `instCount` both drift. Not in scope; worth a line in the
  PR body.
- **T7 — page-count/scene transients.** Any verification of 6g run while a pipeline lane
  regenerates `build/dist` shows transient states. Re-verify after the pipeline lane
  lands; never "fix" what such a build shows.

**Genuinely uncertain:** whether the Iliad build also has zero keyless tokens (only the
Odyssey could be measured — `build/stage3` is a per-run working dir which at the time
held the Odyssey). T1's severity depends on that; measure it during 6a rather than
assume.
