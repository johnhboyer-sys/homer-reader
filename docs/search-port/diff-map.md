# Search port: diff map, Aristotle's new search against Homer's

Written 16 Nov 2026 in `claude/search-port-prep-7bd710`. Nothing here is ported. Aristotle revisions: old main
`6941109fb7`, merge of PR #195 `de57f687c6`. Paths with no repo name are `shared/...`; `A:` marks a line in
Aristotle's file at `de57f687c6`, `H:` a line in Homer's file in this worktree.

## 1. Headline

- **Search.svelte: rebuild on Aristotle's file, then re-add Homer's features as blocks.** Against Homer's real
  ancestor (Plato `ef6d543a01`, the file Homer forked on 17 Jul), 63 of 79 hunks overlap Aristotle's changes and
  only 15 are clean. Homer's own work is 23 hunks (about 1,370 changed lines), mapped by feature in section 3.
  Four features are Homer's alone (book filter, `spk` and `so` speaker filters, the one-book grammar panel);
  the rest Aristotle's file already has in another form.
- **search.ts: hunk-port Homer's 17 own hunks (about 133 changed lines) onto Aristotle's file.** Homer's file is
  Aristotle's file of 28 Jul (`35c3ed89ab`, 1,201 lines) plus those 17 hunks. Aristotle's file has since
  grown to 2,869 lines (134 clean hunks, 18 overlaps). Start from Aristotle's file, not Homer's.
- **New files: copy whole** (about 20, section 2). Adapt only strings (`aristotle-saved-searches`,
  `aristotle-search-*.csv`, the "Try" and help examples) and the data they read.
- **Shared files Homer already has (`data.ts`, `works.ts`, `citation.ts`, `speakers.ts`): merge by hunk.**
  `betacode.ts`: take Aristotle's whole (Homer's copy has no change of its own that Aristotle lacks).
- **This is more than PR #195.** Homer's engine stops at Aristotle's 28 Jul state. The multi-translation English
  index, the shards, the proximity editor and Plato's search stack landed between 28 Jul and 16 Nov (17 commits
  on `search.ts`). Homer's corpus build must change too (section 5): the English index has another shape, and
  `running.json` and the per-translation indexes do not exist.
- **Wait for the counting PR** (section 7). It rewrites the same Search.svelte, `search.ts`, `chapter-pages.ts`
  and `search-pages.ts` lines. Re-run the commands in section 8 against its merge before porting.

## 2. Per-file table

Counts are hunks from `diff3 homer base aristotle-new`. "Base" is Homer's real ancestor where I could find one
(see section 8); old-main counts are in the notes where they differ. `port` = Homer unchanged, Aristotle
changed. `keep` = Homer changed, Aristotle unchanged. `both` = both changed the same lines.

| File | In Homer? | port / keep / both | Notes |
|---|---|---|---|
| `components/Search.svelte` | yes, H 2,895 lines (A old 2,991, A new 5,442) | 15 / 1 / 63 (Plato base, 1,600 lines). Old-main base: 8 / 24 / 49 | Rebuild on A's file. Feature map in section 3. A's file is Svelte 5 with `{#snippet}`; Homer's has none. Both repos use svelte `^5.56.3` and astro `^7`, so no toolchain change. |
| `components/SavedSearches.svelte` | no | new file, 141 lines: copy whole | Imports only `saved-searches.ts`. Download name `aristotle-saved-searches.json` at A:66. Needs the `/saved` page, `app/src/pages/saved.astro` (new in the PR, 106 lines), which is not in the handoff list. |
| `styles/b-search.css` | no | new file, 2,237 lines | 502 rules under `.search-page` (A:`b-search.css`, header comment). Look is John's call: section 4. |
| `styles/b.css` | no | new file, 1,391 lines | Search needs only its token block and base reset from it (section 4). |
| `lib/search.ts` | yes, H 1,262 (A 28 Jul 1,201; A old 1,625; A new 2,869) | 134 / 2 / 18 (A `35c3ed89ab` base). Old-main base: 67 / 42 / 39, misleading | Hunk-port Homer's 17 hunks. They are listed below this table. |
| `lib/search-url.ts` | no | new, 368 lines (old main 213): copy whole | Param clash with Homer's URLs: section 3. |
| `lib/search-pages.ts` | no | new for Homer, 57 lines (A old 170) | Homer's paging is inline at H:789-830 (`paginate`, `renderPage`, `goPage`). |
| `lib/chapter-pages.ts` | no | new, 160 lines: copy whole | With Homer's empty `chapter_bounds` it falls into the "no chapter edges" branch (A:`chapter-pages.ts`:92-98) and lays out one unit per book, as Homer's pager does now. |
| `lib/result-views.ts` | no | new, 544 lines: copy whole | Imports only `search.ts`. Reads a per-reading `lemma` key that Homer's `grammar-dict.json` lacks; A's comment says older data has none (A:`search.ts`:61-64). |
| `lib/form-panel.ts` | no | new, 79 lines: copy whole | Imports `result-views`, `search`. |
| `lib/english-hit.ts` | no | new for Homer, 244 lines (A old 272) | Needs `esc` from `text.ts`; Homer's `text.ts` has none. |
| `lib/english-place.ts` | no | new, 236 lines | Reads the `bekker` tick field and `seg.chapterStarts`; Homer's segments carry ticks under the same field name, no `chapterStarts` (the code treats absent as null). Untested against Homer's Kosmos verse groups and Pope's curated ticks. |
| `lib/paired-hit.ts` | no | new, 433 lines | Same tick field. Needs `english-hit`, `data` types. |
| `lib/proximity-sentence.ts` | no | new, 110 lines | Imports `search.ts` only. |
| `lib/running-text.ts` | no | new, 414 lines | Needs `lib/memo.ts`, which Homer lacks (`memoAsyncBy`). Needs `search/running.json` per work: not built (section 5). |
| `lib/running-text.worker.ts`, `lib/running-match.ts` | no | new, 22 + 22 lines | The worker is started with `new Worker(new URL('./running-text.worker.ts', import.meta.url))` (A:`running-text.ts`:280). Check Astro's bundling of it. |
| `lib/greek-keys.ts` | no | new, 70 lines | Imports `betacode.ts` only. |
| `lib/betacode.ts` | yes, H 98 (A old 117, A new 223) | 2 / 0 / 0, 1 hunk equal on both sides (Plato base `d74301f814`) | Take A's. It adds marks after the letter, `liveGreek`, `LIVE_RANK`. Homer's one change from Plato (uppercase the base letter first) is in A's file too. |
| `lib/saved-searches.ts` | no | new, 195 lines | `SAVED_KEY = 'aristotle-saved-searches'` at A:25; export `kind` string at A:139. Rename for Homer. |
| `lib/speakers.ts` | yes, H 459 (A new 460) | 9 / 0 / 1, 2 equal (Plato base `98b56d1c53`) | Keep Homer's `bareTokenText` (H:47-59, imported by `Reader.svelte`:10). Take A's leftmost-match fix in `locateToken` and the `es` field on `englishCont`. The one `both` hunk is H:36-85 against A:36-80 (the sigla comment and `locateToken`). |
| `lib/sect-ticks.ts` | no | new, 147 lines | No import of it outside tests in A. The follow-ups file lists it as dead code. Do not copy unless the new Search.svelte needs it (it does not import it). |
| `lib/speaker-colors.ts` | yes, 70 lines | identical to A's | Nothing to do. A's follow-ups file lists it as dead code; Homer's `Reader.svelte`:11 uses it, so a later A removal must not reach Homer. |
| `lib/corpus-tools.ts` | no | new, 214 lines | No non-test importer in A. Dead there. Skip. |
| `lib/inscription.ts` | no | new, 17 lines | No non-test importer in A. Skip. |
| `lib/data.ts` (imported by the new page) | yes, H 1,151 (A new 874) | 42 / 13 / 12 (Plato base `ef6d543a01`) | Missing in Homer: `fetchLemmaPickerShard`, `fetchLemmaGlosses`, `LemmaCandidate`, `LemmaChoice`, `OverlayPiece`, `isChapterSection` (A moved it to `citation.ts`:39, though the page imports it from `data`; A:`data.ts`:300 comment). Also `fetchSearchOffsets`, `hitTokens`, `lineAtPosition`, `tickCite` and others that other new files may call. |
| `lib/works.ts` | yes, H 393 (A 1,597) | not meaningful: Homer's registry is its own | Add `AUTHENTIC_IDS`, `HAS_SPEAKERS`, `SEARCH_GROUPS`, `searchableTranslations` (A:`works.ts`:1167). Slot names differ: Homer `'ross'` against A `'secondary'` (H:`works.ts`:23, A:`works.ts`:20). |
| `lib/citation.ts` | yes, H 281 (A new 199) | 1 / 6 / 2 (Plato base `2239f4826e`) | `formatCite` takes 3 arguments in Homer (H:183), 4 in A (A:`search.ts`:1520 passes `sub`). |
| `lib/memo.ts` | no | exists in A before the PR, 1 file | New search imports `memoAsync`, `memoAsyncBy` from it (`running-text.ts`, `search.ts`). Copy whole. |
| `lib/search-filters.ts`, `lib/speeches.ts` | yes, Homer-only | n/a | Back Homer's `spk` and `so`. No A twin. |
| `app/src/pages/search.astro` | yes | n/a | A passes `chapterTitles` and wraps the page in `.frame.dir-b` with `BNav`, `BFoot`, `BFonts`. Homer uses `SiteHeader`. |

**Homer's 17 own hunks in `search.ts`** (diff of Homer against A `35c3ed89ab`; H line is Homer's line):

1. `SegMeta.greek_tokens` comment (H:25-31). Comment only.
2. `Offsets.chapter_bounds` comment, "Homer has no chapter division" (H:45-48). Overlaps A's change to `Offsets` (`turn_bounds`, A:43-52).
3. `englishOccurrences` and `engMatchTerm` replace `engPhraseMatches` (H:268-310). **Overlaps A's whole English engine** (`EngHit`, `englishWords`, positions): drop Homer's, use A's, and check the Search.svelte consumers (H:1357 `englishKwicAt`).
4. `SearchResult.engPositions` (H:318-332) and `engPositions` in each result (H:450-501, 1180, 1190 area). Same fate as 3: A's `engHits: EngHit[]` (A:849-870) carries it.
5. `offsetRef` doc and zero-token-run rule (H:466-501). Overlaps A's rewritten `offsetRef` (A:1499-1512), which already takes `[line, count, sub]` runs. Re-check the 'numbering gap' cases with `__tests__/offset-ref.test.ts`.
6. `searchPhraseVariants` falls back to the typed word when the map has none (H:710-720). Overlaps A:1659-1680.
7. `unitRange` and `lineStarts` made `export` (H:880, 905). `Phrases.svelte` imports both; A keeps them private (A:1900, 1927). **Port first, or `Phrases.svelte` breaks.**
8. Combo default-window comment, Homeric numbers (H:830-833).
9. `WindowUnit` comment, 'chapter' inert (H:812-816).
10. Comment on windows that straddle a column (H:1100-1109).
11. Comment on `approximateChapters` (H:1236+).
12-17. `engPositions: []` in the grammar and combo result builders (H:1048, 1160, 1175...).

## 3. Search.svelte feature map

Homer's file is Plato's `ef6d543a01` plus 23 hunks. A's file shares almost no lines with it, so this table lists
features, not hunks. H = Homer line, A = Aristotle line at `de57f687c6`.

| Homer feature (H line) | Aristotle equivalent (A line) | Port action |
|---|---|---|
| Greek box, English box (H:1484, 1522); Beta Code, placeholders `μῆνις`, `wine-dark sea` (H:1485, 1522) | `#grk-input` (A:4228), `#eng-input` (A:4358), `onGreekInput` (A:3743), live Beta Code, `betaQueryToGreek` import (A:73) | A's. Swap placeholders and help examples (A:2230-2232, `TERM_EXAMPLES` A:1199, `TRY` A:3086-3090) for Homeric ones. |
| All words / Any word / Exact phrase, per language (H:370-372) | `MODE_OPTS` (A:1812-1816), URL `gm`, `em` | A's. |
| Lemma / Exact form radios (H:1508-1511) | Lemma switch `toggleLemma` (A:3794), `m=form|text`; text mode (regex over `running.json`) is new | A's. `text` mode needs `running.json`. |
| Match accents exactly (H:1515, filter at H:362) | `accentSensitive` (A:1059), `accentMatcher` (A:1086), URL `acc` | A's. A also has `caseExact` (A:1105) but ignores capitals (A:4335 comment). |
| "Every form of one word" panel, `doSoloSearch` (H:990-1016, 1543) | One-lemma pick: `soloLemma` (A:1252), `searchLemmaChoices` (A:1690), `fetchLemmaPickerShard` (A:1491); URL `l` | A's, but its picker needs `lemma-picker/*.json`, which Homer's build does not write (section 5). |
| "Find it under any dictionary form" (H:943-990, button H:1944) | `findVariants` (A:246), button "Find this phrase in any inflection" (A:4889), `canWiden` (A:227) | A's. Homer's fallback in `searchPhraseVariants` goes with `search.ts` hunk 6. |
| "Two things near each other" combo, window, unit (H:1146-1320, 1571-1680) | Proximity editor: `comboEditors`, `editorCombo` (A:1338), `searchEditor` (A:1403), `setComboRelation` (A:1508), join `or`, target, `COMBO_TERMS_MAX` (A:1852 in `search.ts`); URL `c`, `cw`, `cu`, `co`, `cx` | A's. Check `WindowUnit` offers `'line'` (A:`search.ts`:1828: `words|line|turn|chapter`). Homer offers Words and Same verse only; hide `turn` and `chapter` (Homer has neither). |
| "Grammar, scoped to one book" (H:1019-1175, 1686-1740); `searchGrammar` import (H:5); URL `gr` | **None.** Grammar is a slot kind in the proximity editor (`setComboGrammar` A:1667) and a result facet (`view=grammar`, `gf`, A:487-546). A's `searchCombo` refuses grammar-only queries unless fewer than all works are chosen or a speaker is set (A:`search.ts`:2450-2466, returns `unnarrowed`). Its test of "narrowed" is `works.size < WORKS.length`: one book does not count. | **Homer-only block. Keep.** `searchGrammar` is still exported (A:2838). Re-add the panel, its URL param, and `grammarCounts` (H:1056-1100) by hand. Homer's `grammar-ui.test.ts` (349 lines) drives this panel and will break on a rebuild. |
| Ambiguity marker, dotted underline (H:1335, 1382, style H:2873) | `ambiguityNote`, `grammarHitNote` (A:78, `result-views.ts`), `noteOf` (A:677) | A's. Check the Homer styling goes into the chosen look. |
| Work filter `w` = `iliad` / `odyssey` (H:103-123, 281) | Works picker (A:1818 `toggleWork`, `setWorksScope` A:1881), results filter `wf` (A:768 `setWorkFilter`). URL `w` is a work list | A's. Homer has two works, so the picker is short. Old links `?w=iliad` must still read: A's decoder accepts a list of ids (A:`search-url.ts`:355-365), so `w=iliad` reads as one work. |
| Book filter `b` (H:120-130, 281-325, 844-851) | **None found.** `grep` for `bookFilter` finds nothing in A. | **Homer-only. Keep.** It also gates the grammar panel (H:1048-1053). |
| Speaker filter `spk` (H:140-200, 316) | Speaker panel (A:4647), `loadRoster` (A:1930), `speakerRoster` (A:`search.ts`:977), URL `sp` + `sn`. Reads `offsets.turn_bounds`. A hides it with `HAS_SPEAKERS` (A:90). | **Homer-only data source.** Homer's speakers come from `speeches.json` (DICES spans by book and line), not `turn_bounds` (section 6). Keep `search-filters.ts`. |
| "Speeches only" `so` (H:311, 195, 1926) | **None.** | **Homer-only. Keep.** |
| URL params `g`, `e`, `q` (H:844-851) | `g`, `e`, `q` read-only (A:`search-url.ts`:296-300) | Same meaning. |
| URL param `so=1` (H:324-340) | `so` = sort order `work|form|freq` (A:`search-url.ts`:340) | **Clash.** Old `so=1` links read as an unknown sort and fall back to the default. Rename Homer's, and keep a reader for `so=1`. |
| URL params `w`, `b`, `spk`, `gr` | `w` (works list, A:355), no `b`, `sp`/`sn`, `c` grammar slot `g:` | `w` still reads; `b`, `spk`, `gr` need their own keys. Check that `encodeSearchUrl` leaves unknown keys alone (it builds the whole query string, A:230-288), or Homer's keys vanish on write. |
| CSV export (H:1416-1470; file `homer-search-*.csv`, H:1453) | `exportCsv` (A:3566); columns Work, Book, Chapter, Bekker, Language, Translation, Snippet, URL (A:3579); name `aristotle-search-` (A:3612) | A's; rename, and fix the column header "Bekker" (A:3579) and the `formatCite(g.work, inst.column)` call (A:3596) for book.line. |
| Failed-works notice and retry (H:921-930, 1883-1944) | Notice row with "Try again" calling `doSearch` (A:5141-5155); forms and grammar retries (A:448, 536) | A's. |
| Paging by whole books, `PAGE_TARGET = 40` (H:88, 789-830) | `paginate` (A:808) from `chapter-pages.ts`, `pageTarget` (A:322), page sizes 20/40/100 (`ps`, A:487, 570), pager (A:4103) | A's. Pages run over books because Homer's chapters are empty. The 44px pager targets are A's. |
| Grouping by chapter, one chapter per book (H:603-640, `buildGroups` H:678) | `buildGroups` (A:2435), `chapterLookup` (A:2290), `fetchOutline` (A:2337), "Group by" (A:4925), `sx-chap` headings (A:4136) | A's. `fetchOutline` calls `fetchSections` for Stephanus and `fetchChapters` otherwise (A:2337-2341); Homer's scheme id is `verse-line`, so it takes `chapters.json`, which Homer emits empty. Check `chapterOf`'s fallback (A:2500) gives one group per book. |
| Help modal "How to type Greek" (H:506-556, 1835) | `openHelp` (A:2238), modal (A:4745) | A's; replace examples. |
| Result header counts (H:1068-1100) | Bar at A:205-207 (`totalPassages`, `mainCount`); the counting PR rewrites it | A's; wait for the PR. |

**In A and absent in Homer** (all come with the copy): saved searches (A:3027-3094, `/saved` page), result views
(Group by form/grammar, sort, context, per page: A:542-640), the filter sheet and its screens (A:955-1030), the
form panel and set-aside forms (`xf`, A:402-501), running-text mode (A:3251-3356, `m=text`), paired hits (the other
language beside each hit: `paired-hit.ts`), the proximity sentence under the editor (A:1370), the on-screen Greek
keyboard (A:3852-3890), the lemma picker with glosses, English "any form" (`ef`), per-translation filter (`t`),
print handling (A:2173), the B shell.

## 4. The B base

**What the new search needs from `b.css`.** Only tokens and a reset. I found no class that `Search.svelte` uses and
only `b.css` defines, other than 25 shared names (`pager`, `retry-btn`, `help-modal` ...) that both files style.
The token block is `b.css`:12-26, inside `.frame.dir-b`; the page must sit under `.frame.dir-b` (A:`search.astro`
`<div class="frame dir-b pg-search">`, and `Search.svelte`:1420 looks for `.frame.dir-b`). `b-search.css` puts every
rule under `.dir-b .search-page` (header comment). `b.css`:847-870 holds an older search block (`.b-search-page`) that
the current markup and `b-search.css` do not use; I found no `b-search-page` in either.

29 distinct `var(--...)` names appear in `b-search.css` and `Search.svelte`'s own `<style>` (140 lines, A:5303):

| Group | Names (uses) | In `b.css`? | In Homer `global.css`? |
|---|---|---|---|
| B colours | `--ink` 190, `--mid` 90, `--red-ink` 87, `--line` 45, `--paper` 10, `--bg` 22, `--faint` 4, `--line2` 4, `--soft` 4, `--hl` 1 | yes (`b.css`:12-22) | **no** |
| B type | `--sans` 123, `--read` 36, `--tface` 6 | yes (`b.css`:14-15) | **no** |
| Old global names | `--accent` 25, `--text-mid` 21, `--text` 11, `--border` 10, `--font-greek` 3, `--font-english` 3 | `b.css`:847 re-points them to B tokens | **yes** (H:`global.css`:63-130) |
| Page-local | `--sheet-foot`, `--shade`, `--go`, `--veil`, `--sq-side` | defined in `b-search.css` | n/a |
| Not found | `--font-caps` 11, `--prox-bar-height` 2, `--d` 2, `--accent-2` 2 | no | `--font-caps`, `--accent-2` not in Homer either; check for fallbacks. `--prox-bar-height` and `--d` I did not trace; they may be set inline. |
| Other | `--page-bg` 3 | A's `global.css` | yes (H:`global.css`:73) |

Homer's `global.css` has 106 custom-property definitions and no web fonts (system stacks: `--font-ui` Optima,
`--font-english` Iowan Old Style, `--font-greek` Palatino, `--font-display` Big Caslon). B loads Sofia Sans,
Literata and Oswald through `BFonts.astro`. Homer's current Search `<style>` (H:2021-2895, 875 lines) uses
`--font-ui` (37), `--border` (27), `--text-mid` (21), `--accent` (20), `--text` (15), `--accent-light` (15),
`--text-light`, `--col-bg`, `--input-bg`, `--error`, `--on-accent`.

**What porting the B look takes.** Copy `b.css`' token block and reset, plus `b-search.css`, plus the three
shell pieces (`BNav`, `BFoot`, `BFonts`) or a stand-in wrapper that carries `.frame.dir-b`; add the B fonts;
wrap Homer's search page in `.frame.dir-b`. Homer's other pages keep `global.css`. The B tokens are scoped to
`.frame.dir-b`, so they do not leak.

**What restyling to Homer's tokens takes.** Keep `b-search.css`' layout rules; replace the B colour and type
names with Homer's nearest tokens. My reading of the nearest match (John rules these): `--ink` to `--text`,
`--mid` to `--text-mid`, `--faint` to `--text-light`, `--line` to `--border`, `--red-ink` and `--red` to
`--accent`, `--paper` to `--col-bg`, `--bg` to `--page-bg`, `--sans` to `--font-ui`, `--read` to
`--font-english`, `--tface` to `--font-display`. Homer has no `--soft`, `--hl`, `--line2` equivalent that I found.
The 190 `--ink` and 87 `--red-ink` uses make this a search-and-replace over about 620 uses, with a
contrast re-check in both themes (Homer rule: WCAG AA in both). Aristotle's own mapping at `b.css`:847 does the
reverse job for the old names and shows the pairing B chose. Not decided here.

## 5. Corpus files the new search fetches

Homer's emitted data checked in `~/Developer/homer-reader-site/data/` (deploy of 21 Oct 2026, main `b35b0b294`,
read-only), against `pipeline/homer_pipeline/stage6_search.py` and `stage7_emit.py`. Homer's `build/dist` was
being rebuilt and I did not rely on it. Rechecked on the rebuilt `build/dist` (main `05d0cd885`, 16 Nov):
`iliad/search/` holds only `english.json`, `grammar-col.bin`, `grammar-dict.json`, `greek_form.json`,
`greek_lemma.json`, `meta.json` and `offsets.json`; there is no `running.json` and no `lemma-picker/`.

| Fetch (file:line in A) | Homer's build | Status |
|---|---|---|
| `<work>/search/meta.json` (`search.ts`:1473 and others) | writes it (`stage6_search.py`:571) | produced |
| `<work>/search/offsets.json` (`search.ts`:127; `data.ts`:595) | writes it (`stage6_search.py`:531). Keys: `token_count, seg_base_offset, segments, book_bounds, chapter_bounds` (empty). No `turn_bounds`. | produced; A fills `turn_bounds` with `[]` when absent (`search.ts`:116) |
| `<work>/search/greek_lemma.json`, `greek_form.json` (`search.ts`:2301-2302) | writes both | produced |
| `<work>/search/grammar-dict.json`, `grammar-col.bin` (`search.ts`:2303, 2313) | writes both | produced, older shape: readings have no `lemma` key (deployed `grammar-dict.json` reading: `{case, gender, number}`). A tolerates it (`search.ts`:61-64); "own headword" grammar groups then fall back. |
| `<work>/search/english.json` (`search.ts`:739) | writes it, **Murray only**, shape `{word: [seg_idx, ...]}` (7,214 words in the Iliad) | **produced under another shape.** A reads `{word: [[seg_idx, word_pos], ...]}` (`search.ts`:35). Needs a stage 6 change: word positions, A's `english_words` (`stage6_search.py`:99-113 in A) and `_EN_MARKER` rules. |
| `<work>/search/english-<slot>.json` for every other translation (`search.ts`:739; written by A's `emit_translation_indexes`, `stage6_search.py`:267) | not written. Homer carries four translations per work (Murray, Butler, Pope, Kosmos; H:`works.ts`:184-187, 205-208). | **not produced.** Names would be `english-ross.json` (or `-secondary` after a rename), `english-third.json`, `english-overlay-kosmos.json`. A's emitter reads `seg.secondary or seg.ross` (A:`stage6_search.py`:~248), so Homer's `ross` slot works without a rename; the file name would come out `secondary`. Preflight in A checks them (`preflight.py`:247-276). |
| `<work>/search/running.json` (`running-text.ts`:168) | not written | **not produced.** Only the `m=text` mode needs it. A writes it in stage 6 through `running_text.py` (230 lines), which imports `beta`, `stage3_tokenize` pieces; check Homer's `beta.py` and `stage3_tokenize.py` have the same names (`_APOSTROPHES`, `_BASE`, `_MARKS`, `_clean`, `_not_a_word`). Not checked. |
| `search-shards/index.json`, `vocab.json`, `<stream>/<shard>.json`, `accents/<shard>.json` (`search.ts`:1226-1284) | not written; A's `stage9_search_shards.py` writes them | **not produced, and optional.** Every load is `.catch(() => null)` and falls back to the per-work files (`search.ts`:1284-1290, 1255-1259). Without shards each search loads whole per-work indexes: fine for 2 works, but the port gets no shard speed-up. |
| `lemma-map/<letter>.json` (`search.ts`:1631, 2545, 2589) | written (`~/.../data/lemma-map/a.json` exists) | produced |
| `lemma-picker/<letter>.json` (`data.ts`:502) | `build-lemmata.mjs` in Homer has no picker step (it emits `lemmata/` only; A's has `PICKER_OUT`, A:`build-lemmata.mjs`:374) | **not produced.** The new Greek box suggestions and "Every form" picker read it. A's loader throws on a stale shape (`data.ts`:505-510). |
| `lemmata/<slug>.json` `.glosses` (`data.ts`:523) | `lemmata/` has 4,610 files; sample has `glosses` | produced, same key |
| `<work>/book-NN.json` (`data.ts`:143) | written | produced. Segments carry `ross`, `third`, `overlays.kosmos`, `english.bekker`. A's names the second slot `secondary`; Homer's is `ross`. Check `works.ts` slot mapping in the port. |
| `<work>/chapters.json` (`data.ts`:179) | written, empty for Homer (Search.svelte H:603 says so) | produced (empty by design) |
| `<work>/sections.json` (`data.ts`:828) | `stage7_emit.py`:680 writes it only for Stephanus works; none in the deploy | not produced; not needed (scheme is `verse-line`, so `fetchOutline` skips it, A:2337) |
| `<work>/columns.json`, `footnotes.json`, `figures.json`, `analyses.json` (`data.ts`:238, 192, 225, 433) | written (`columns.json`, `footnotes.json`, `analyses.json` in the deploy). `figures.json` and `sidenotes.json`, `quotations.json` are not in the deploy | the new Search.svelte does not call these directly (its data imports are `fetchBook`, `fetchChapters`, `fetchSections`, `fetchLemmaPickerShard`, `fetchLemmaGlosses`, A:53-58). `WordPopup.svelte` (imported A:75) fetches more; Homer keeps its own. |
| `ngrams/english-segments.json`, `ngrams/<key>.json` (`corpus-tools.ts`:104-106; `data.ts`:552-579) | `ngrams/` exists in Homer | only `corpus-tools.ts` calls these; skip that file and this does not matter |
| `bekker.json` (`data.ts`:262) | not written | not called by the search files I read; I did not trace `fetchBekkerIndex` callers |
| `repetitions.json`, `speeches.json`, `characters.json` | written | not fetched by A's search; Homer's own filter uses `speeches.json` |

## 6. Homer features the new search must carry

**Translations.** Homer has four per work: Murray (slot `english`), Butler (`ross`), Pope (`third`, curated ticks),
Kosmos (`overlay`, CC BY-NC-ND, verse groups) (H:`works.ts`:183-208). Homer's search indexes **Murray only**
(`stage6_search.py`: `english_chunks.json` is the primary; `english.json` in the deploy is 7,214 words). The
new engine searches every translation a work lists (`searchableTranslations`, A:`works.ts`:1167;
`englishSources` in `search.ts` reads the registry) and labels each hit with whose words it is. So Homer's search
gains Butler, Pope and Kosmos once the indexes exist. Kosmos has its own rules: ND means no trimming, and its ticks
are only every fifth line (CLAUDE.md), so `english-place.ts`/`paired-hit.ts` must show it in verse groups. Not
checked against those functions.

**Speakers and speeches.** Homer keeps `spk` and `so` with `speeches.json` (`shared/lib/search-filters.ts`,
`speeches.ts`, `data.ts` `fetchSpeeches`). A's filter reads `offsets.turn_bounds` (`{book, speaker, start,
accuracy}`; `search.ts`:52, 903-1000), which Homer's `offsets.json` lacks. Two ways: (a) emit `turn_bounds`
from `speeches.json` in stage 6 (speeches nest and cross books, which `turn_bounds` cannot say; the Apologoi frames
would need a rule), or (b) keep Homer's line-span filter and hide A's speaker panel (`HAS_SPEAKERS` false, as
A does for Aristotle). Option (b) is less work and keeps `so`. I did not decide.

**Line citations.** Homer cites book.line. Places in A that assume Bekker or chapters, with Homer's substitute:

| A function or field | Where | Assumption | Homer substitute |
|---|---|---|---|
| `stephanusPage(column)` | `search-pages.ts`:22 | `parseInt(column)`; sort key `[work, book, page]` (line 28) | Homer's `column` is `String(book)` (`search.ts` H:`offsetRef` comment), so it sorts by book; fine. |
| `chapterMap`, `chapterIdx`, `paginate` | `chapter-pages.ts`:20-160 | chapter starts from `offsets.chapter_bounds`; a "passage" is a Bekker column | Empty `chapter_bounds` gives one unit per book (lines 92-98). No change needed; verify page count equals Homer's current pager on a baseline search. |
| `bekkerCmp`, `chapterOf` | A:3547, 2500 | order hits by page, column half, line | Order by book, then line. Replace `bekkerCmp`; `chapterOf` should return the book's single group. |
| `formatCite(work, column, line, sub)` | `citation.ts` (A), `search.ts`:1520 | Bekker "1094a15"; `sub` for lettered lines | Homer's 3-argument `formatCite` (H:183) returns "9.366"; add `sub` or drop it. `formatLocValue` is used for jump links (A:2366 `jumpLinks`). |
| `offsetRef`, `offsetCite` | `search.ts`:1499, 1518 | line runs `[line, count, sub?]` | Homer's runs store the vulgate number, so gaps resolve with no arithmetic (Homer commit `b519c4d00`). A's loop is the same shape. Re-run `offset-ref.test.ts` (215 lines). |
| `bekkerEnglish`, `englishPlace`, `unitAtEnglish` | `paired-hit.ts`:223-249, `english-place.ts` | English text carries `bekker` ticks (`{n, offset}` lines) | Homer's `english.bekker` holds line ticks under the same field name. Pope's are curated scene anchors and Kosmos's are every fifth line (H:`works.ts`:32-45). Test both. |
| `isChapterSection`, `isNonBekker`, `citeLabel` | `citation.ts`:39-53 | scheme `chapter-section` / `busse` | Homer's scheme id is `verse-line` (H:`citation.ts`:35). Add a branch or leave: they return the old string for other schemes. |
| `crossChapter` (URL `cx`, `WindowUnit 'chapter'`) | `search.ts`:1830, `search-url.ts`:330, `proximity-sentence.ts`:89 | chapters exist | Hide in the editor; keep the field, as Homer did on 28 Jul (commit `54e0eeb63`). |
| `chapterTitles` prop | `Search.svelte`:87, `search.astro` | read from `public/data/<work>/chapter-titles.json` at build | Homer has none; pass `{}`. |
| Search "page" copy: "Bekker order" (A:612), "Bekker" CSV column (A:3579), "cited by Bekker number" (`search.astro`) | strings | | rewrite |

**Grammar-solo panel.** No equivalent (section 3). A's engine, `searchCombo`, accepts a lone grammar slot only when
`works.size < WORKS.length` or a speaker is set (A:`search.ts`:2450-2466). Homer's rule is "one work and one
book". Keep Homer's panel and `searchGrammar`.

**Variant widening.** A has it (`findVariants` A:246, `searchPhraseVariants` A:1659). Homer's extra rule
(an unrecorded word stands for itself) is `search.ts` hunk 6. Homer's `Phrases.svelte` also uses `lemmaReadings`,
`lemmaOptions`, `lineStarts`, `unitRange`, `offsetRef`, `greekFold`: A exports all but the two private ones.

**Other consumers of Homer's `search.ts`.** `Reader.svelte`:17 (`greekFold`), `Phrases.svelte`, `lemma/index.astro`:10.
A's `search()` has two new trailing parameters (`engForms`, `speaker`; A:2725-2735), which Homer's one call site
(H:`Search.svelte`, near line 901) does not pass; both have defaults.

## 7. Overlap with the counting PR

From `HANDOFF-SEARCH-FOLLOWUPS.md` §1-2, §4 (read at `origin/main`). The PR changes what the bar counts, how pages
are cut, and adds phrase Include and Exclude. Files it names or implies:

| File | What the handoff says | Source |
|---|---|---|
| `components/Search.svelte` | `totalPassages = shown.length` (~799); `paginate(shown, offsets, pageTarget(pageSize))` (~808); `buildGroups` (~2440, page 67 empty); `formPanel`, `excludedForms` as the pattern for phrases | §1, §2 |
| `lib/search.ts` | `intersect(grkHits, engHits)` over segments (~1466) becomes "same chapter"; English hits only when one translation per work | §1, §2 |
| `lib/chapter-pages.ts`, `lib/search-pages.ts` | page cut by chapters or rows; `hitCount` stops counting translators | §1, §2 |
| `lib/search-url.ts` | the phrase include/exclude set goes in the URL "like `xforms`" | §2 |
| `lib/form-panel.ts`, `lib/result-views.ts` | named as the pattern to follow; likely extended (my inference) | §2 |
| `lib/english-hit.ts`, `lib/english-place.ts` | phrases built from each English hit with neighbours (my inference; the handoff does not name them) | §2 |
| `styles/b-search.css` | the new controls; also the 44px proximity controls (§4) | §2, §4 |
| `app/scripts/check-redesign.mjs` gate `R-S7`, `search-counts.mjs` | pins 311 passages and 2,952 hits; rewritten | §3 |
| `lib/corpus-tools.ts`, `sect-ticks.ts`, `inscription.ts`, `speaker-colors.ts`, `groupState` | §4 lists them as dead code to remove, in a later PR | §4 |

Not named in the handoff: `betacode.ts`, `greek-keys.ts`, `running-text*`, `saved-searches.ts`,
`proximity-sentence.ts`, `paired-hit.ts`, `speakers.ts`, `SavedSearches.svelte`, `b.css`.
Port the not-touched files first if the counting PR is slow; do not port Search.svelte, `search.ts`, `chapter-pages.ts`,
`search-pages.ts`, `search-url.ts` before it merges. The handoff also asks John to rule Homer's counting unit
(books and lines) first.

## 8. How I made these counts

- Scratch copies: `/private/tmp/claude-501/-Users-johnboyer-Developer-homer-reader--claude-worktrees-search-port-prep-7bd710/2c5081fd-3585-4731-ae83-b42727709fcd/scratchpad/diffmap/`.
- Old main as base misleads: Homer did not fork from it. `b519c4d00` ports Aristotle's `search.ts` "wholesale" on
  28 Jul; the Aristotle commit closest to Homer's file is `35c3ed89ab` (diff of 133 changed lines against Homer's;
  every other commit in the range is over 1,000). `Search.svelte`'s base is Plato `ef6d543a01` (Homer's file
  at fork commit `cb25e5a57` is identical to it). `data.ts` shares `ef6d543a01`, `citation.ts` `2239f4826e`,
  `speakers.ts` `98b56d1c53`, `betacode.ts` `d74301f814`, `speaker-colors.ts` `a1d52d7330`. `works.ts` has no
  usable base (Homer rewrote it).
- Class counts: `diff3 ours base theirs`, counting `====1` (keep), `====3` (port), `====` (both), `====2` (equal on both sides).
  Hunks, not lines. Re-run after the counting PR with the same bases and the new Aristotle merge as `theirs`.
- Data checks used `~/Developer/homer-reader-site/data/` (21 Oct deploy). Homer's `main` is later (butler anchors,
  PR #62); I did not check whether anything in `build/dist` differs.
- Not checked: whether Homer's `stage3_tokenize.py` and `beta.py` carry the names `running_text.py` imports; Astro's
  bundling of `running-text.worker.ts`; how `english-place.ts` treats Kosmos and Pope ticks; `desktop/`; `advanced.astro`
  (Aristotle rewrote it in the PR; Homer's own is separate); the 8 Svelte-local custom properties not found in any
  stylesheet.
