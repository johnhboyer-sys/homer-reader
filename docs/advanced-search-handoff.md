# Handoff: advanced search for the Homer Reader

**Written from aristotle-reader, 2026-07-27**, the day advanced search shipped
there (PR #56, gh-pages `de0cfb2f`). A companion handoff went to plato-reader
the same day (`plato-reader/docs/advanced-search-handoff.md`) — read it if you
want the plainest statement of the port; this one covers what Homer does
differently, and Homer differs more than Plato does.

Do the work **in the homer-reader repo/session**. The sister repos are
read-only from here.

Every number below was measured against the repos as they stand today.
Estimates say so.

---

## 1. Where Homer stands

Homer is **furthest behind on search internals and furthest ahead on
apparatus.** That combination decides the whole plan: most of the port is
lifting machinery Homer lacks, but the risk is clobbering apparatus features
the siblings never had.

| | Aristotle | Homer |
|---|---|---|
| `stage6_search.py` | 481 lines | 191 lines |
| per-work artifacts | + `offsets.json`, `grammar-dict.json`, `grammar-col.bin` | none of these |
| cross-work n-gram stage | `stage8_ngrams.py` | none (but see §3 — `apparatus_repetitions.py` overlaps) |
| `shared/lib/search.ts` | 1,188 lines | **376 lines** |
| `Search.svelte` | 2,599 lines | 1,957 lines |
| speech/speaker result filters | none | `shared/lib/search-filters.ts` + tests |
| scansion, epithets, repetitions, scenes | none | all shipped |

Corpus scale: Aristotle indexes 848,592 Greek tokens. Homer indexes
**199,076** (Iliad 111,887, Odyssey 87,189 — counted as Greek form postings).
That is 23% of Aristotle, whose n-gram payload is 61 MB. Homer's should land
near **14 MB**. Measure before shipping; do not assume.

Two things Homer already has right that Plato does not: `english_head` is
already the full chunk (not truncated), and `meta.json` already carries
`greek_tokens`. Do not "fix" either.

**Segments are books.** Homer's `meta.json` has 24 entries per work, one per
book, where Aristotle's has one per Bekker column. Everything in the port still
works — `seg_base_offset[seg_idx] + token_pos` is granularity-blind — but
`token_pos` runs to several thousand inside a book instead of a few dozen, and
the per-segment `line_runs` array is what carries book.line resolution. It is
the load-bearing field for Homer, not an optimization.

---

## 2. The port, in order

Each step has its own gate. Do not start the next until the current one passes.

### Step 1 — the offset primitive

Port the `-- Offset primitive --` block from aristotle `stage6_search.py:261`.
It emits `offsets.json`:

```
{ token_count, seg_base_offset[], segments[{book, column, line_runs}],
  book_bounds[], chapter_bounds[] }
```

No existing posting changes and no reverse map is needed. It counts every
stage-3 token, keyless ones included, so it stays in step with `token_pos`.
`token_count` doubles as a build fingerprint — every offset-indexed artifact
must agree on it, and the client throws when they disagree. Keep that.

For Homer, `book_bounds` is nearly the whole segment list, and `chapter_bounds`
has no analogue: emit it empty. Do not fake it. §3 says what takes its place.

**Vulgate lineation is sacred** (repo hard rule) and this stage is where a
careless port would break it. `line_runs` is `[[line_number, token_count], …]`
taken from the emitted line numbers, never from an enumeration index. Numbering
gaps and athetized lines must survive into `line_runs` exactly as the spine has
them — an offset that resolves to a renumbered line is worse than no offset.

*Gate:* port `check_offsets` from aristotle's `stage2_validate.py`, and extend
it with a Homer-only assertion that the line numbers in `line_runs` match the
book's recorded expected-gap list.

### Step 2 — the grammatical index

Port `_FEATURES`, `parse_reading`, `signature`, and the emission of
`grammar-dict.json` + `grammar-col.bin` (aristotle `stage6_search.py:342`). It
is a signature dictionary plus a packed column, **not an inverted index**:
grammatical predicates are anti-selective (`case=gen` matches ~10% of every
token), so postings go near-dense and dwarf the lexical index.

Four rules in that code are load-bearing:

- **No part of speech.** Morpheus emits no such field. Participles carry both
  nominal and verbal morphology; nouns and adjectives are indistinguishable
  here. Only Morpheus's explicit markers are indexed, under `marker`.
- **`part` is the participle mood, not `particle`.** Never conflate them.
- **Syncretic values expand inside a reading.** `nom/voc/acc` becomes three
  values in that one reading; a three-way ambiguous analysis must not be
  reported as one certain parse.
- **Whole readings are kept, never a per-category union.** Analyses
  `{masc nom sg, fem acc pl}` must not satisfy masc + acc + sg.

`SIG_UNKEYED = 0` and `SIG_UNANALYSED = 1` keep the column aligned with the
offset space where there is nothing to say about a token.

**Homer-specific caution.** Epic dialect forms and the corpus's morphology
overrides mean Homer's analysis distribution is not Attic's. Two things to
check rather than assume: that `_FEATURES` covers every value Morpheus emits
over this corpus (log the unclassified words on a full run — if a Homeric tag
falls through, it silently vanishes from every grammar query), and that
`morphology_overrides.json` and the analysis ranking added in `6166beb23` are
read by the signature builder, not bypassed.

*Gate:* `check_grammar`; column length must equal `token_count` per work; and
the unclassified-word log must be empty or explained.

### Step 3 — fold streams, stage 7 copy

Stage 6 also writes per-work fold streams to `build/ngrams/<work>.json`, one
for `form` and one for `lemma`. Extend `stage7_emit` to copy the new artifacts
into `build/dist/<work>/search/`.

### Step 4 — `stage8_ngrams.py` (new file) — **read §3 first**

Copy aristotle's module; its header docstring is the spec.

```
build/dist/ngrams/<stream>/<letter>.json         browse list
    { "<fold phrase>": [n, count, score, works] }
build/dist/ngrams/<stream>/occ/<letter>-<n>.json fetched on expand
    { "<fold phrase>": { "EN": [1204, 88, 310], "iliad": [90211] } }
```

Occurrences are per-work global offsets, delta-encoded after the first. The
browse list carries the work map, so the UI can say "37 times across 2 works"
without loading an offset. The browse/occurrence split is not cosmetic —
keeping them together made one Aristotle shard 10.4 MB.

Build-time rules: never span a book edge; never span a token no index can key;
keep only phrases occurring twice or more corpus-wide; do **not** filter
straddling at build time (it is a query-time toggle, and dropping the
occurrences makes the toggle unimplementable).

Stage 8 also emits `build/dist/lemma-map/<letter>.json` — `fold(surface)` → the
headwords that surface can belong to. It needs the same corpus-wide pass, and
it is what lets a typed word be widened to its inflected forms without the
reader knowing any headwords. **Do not skip it** (§5, the lemma bug).

"Corpus-wide" means two works here, so the recurrence bar is low and the
cross-epic hits are the interesting ones — a phrase in both epics is a real
finding, and the work map already surfaces it.

### Step 5 — wire stage 8 into the build

Stage 8 takes no `--work`, so it is **not part of `all`** and must be called
explicitly after `build-public.mjs` cleans `build/dist`. Aristotle's
`build-public.mjs:62` carries the call and the comment: without it, a full
rebuild emits a site whose `/phrases` pages have no data behind them.

### Step 6 — the client, carefully

Homer's `shared/lib/search.ts` is 376 lines against Aristotle's 1,188. Port the
Aristotle file wholesale rather than patching Homer's incrementally — but
**Homer's search page has features neither sibling has**, and a wholesale port
will destroy them if you are not deliberate:

- `shared/lib/search-filters.ts` — the speaker / "speeches only" result
  filters, with a documented under-matching posture for `crossBook` spans (the
  two Apologoi frames). That file's doc comment explains why it never guesses a
  span's true close. **Preserve the posture verbatim.** Its tests
  (`search-filters.test.ts`) are the contract; they must still pass.
- Whatever `Search.svelte` wires on top of it.

The offset→citation resolver (aristotle `search.ts:456`) needs rewriting for
`book.line`: it turns a global offset into a citable position from
`offsets.json` alone, walking `line_runs` within the segment.

Then the UI: the new `Search.svelte` panels, a `Phrases.svelte`, an `/advanced`
guide page, a `/phrases` page. §5 lists the UI decisions Aristotle got wrong
first — read it before copying components, not after.

---

## 3. The collision Homer has and the siblings do not

**`apparatus_repetitions.py` already is an n-gram index.** It emits
`build/dist/repetitions.json`: 4,390 entries, 1.6 MB, exact repeated whole
lines and long word-sequences, cross-epic. `apparatus_epithets.py` does the
same over lemma sequences, per work, keyed to characters. Both already ship,
both have readers (`RepetitionsIndex.svelte`, `FormulaLedger.astro`,
`/formulas`), both are documented in `docs/APPARATUS-SCHEMAS.md`.

Stage 8 would be a **third** n-gram index. Resolve this on purpose, in writing,
before you build it. The three differ in ways that matter:

| | repetitions | epithets | stage 8 |
|---|---|---|---|
| matched on | exact surface text | lemma sequence | fold-normalized, form *and* lemma streams |
| crosses lines | no | no | yes, unless you stop it |
| scope | cross-epic | per work, per entity | corpus-wide |
| explosion control | maximal-n-gram rule | maximal-n-gram rule | ≥2 occurrences |
| what it is | a philological claim | a philological claim | a search tool |

**My recommendation: keep all three, and label them so a reader is never
confused about which question each answers.** Repetitions and epithets encode
deliberate philological decisions — exact accents and breathings as printed,
within-line only, the maximal-n-gram rule — and folding them into a normalized
search index would quietly weaken published claims. Stage 8 answers a
different question: *what recurs, however spelled, wherever it falls.*

Two consequences for the build:

- Add a **within-one-verse** toggle to the phrase query, powered by
  `line_runs`. Homeric formula is largely a within-line phenomenon, and without
  the toggle stage 8's cross-line results will look like noise beside
  repetitions.json. Do not enforce it at build time — enjambed repetition is
  real, and filtering it out of the data makes the toggle unimplementable.
- The `/phrases` page must say, in one sentence, how it differs from
  `/formulas`. Aristotle's guide page shipped with wrong numbers because nobody
  owned the prose; do not repeat that here where the prose does more work.

---

## 4. The feature nobody else can build

**Metrical position.** `apparatus_scansion.py` already emits per-line feet
strings with honest confidence flags. `offsets.json` will give every token a
global position; `line_runs` gives its line; scansion gives that line's feet.
Combine them and you can index **each token's slot in the verse** — a metrical
column built exactly like the grammar column of step 2.

That makes real queries answerable: *πόδας ὠκὺς Ἀχιλλεύς, verse-final only.*
*This epithet before the caesura, that one after.* Formula is position-bound;
no existing search tool for Homer indexes position, and this corpus already
holds every input.

Two constraints. Scansion's `confidence: "ambiguous"` must propagate — a
metrical filter that silently treats ambiguous lines as certain is exactly the
overstatement the scansion module was written to avoid. And the caesura is a
derived judgment, not in the data yet; ship verse-position first (initial,
medial, final) and treat caesura-relative queries as a later question.

**Sequencing: build the port first, ship it, then do this as its own PR.** It
is the headline, and it is worthless on top of a half-ported index. The same
advice went to Plato about its speaker column.

---

## 5. Mistakes Aristotle made first

Each cost a round trip. None need repeating.

- **A lemma search must accept the inflected form.** Typing `λόγου` in lemma
  mode returned nothing for a word occurring 2,269 times, because the index is
  keyed by headword. Resolve the surface through `lemma-map` at query time —
  which is why step 4 cannot skip the lemma-map emission.
- **Grammar is combo-only.** A standalone grammar query returned 33,504 hits
  for genitive-plural-feminine, which is not a result, it is the corpus. Ship
  grammar as a filter on a lexical query. Aristotle disabled its standalone
  panel after building it.
- **No jargon in the labels.** "Any form of this word" / "Only as I typed it".
- **Every number on the guide page must be generated or verified against the
  built corpus.** Aristotle's `/advanced` shipped with a corpus-wide claim that
  was one-work-only and a phrase count 4× off. Numbers typed from a session go
  stale silently.
- **`<details>` needs `bind:open`**, not a one-way binding, or panels collapse
  as the user types.
- **Snippets go through the shared sanitizer.** The search markup path has had
  an XSS defect before.

---

## 6. Success criteria

1. `stage2_validate` green for both works: `check_offsets` (including the
   lineation-gap assertion), `check_grammar`, `check_ngram_streams`.
2. `npm test` in `shared/` green — the full existing suite, with
   `search-filters.test.ts`, `repetitions.test.ts`, and `scansion.test.ts`
   passing unchanged. Add aristotle's `combo.test.ts` and book.line cases for
   the offset→citation resolver. Run vitest from `shared/`, not the worktree
   root.
3. Full corpus rebuild, then `npm run build:public` with **0 broken links**.
4. Spot queries verified by hand — one per mode: form, lemma widened from an
   inflected form, grammar in combo, phrase, English, and one speech-filtered
   query proving the existing filters survived the port.
5. `/data/ngrams` size measured and recorded against the ~14 MB estimate.
6. One paragraph in `docs/APPARATUS-SCHEMAS.md` stating how the phrase index
   relates to repetitions and epithets (§3). This is a deliverable, not a note.

## 7. Blast radius

Touch: `pipeline/homer_pipeline/{stage6_search,stage7_emit,stage2_validate}.py`,
a new `stage8_ngrams.py`, `scripts/build-public.mjs`, `shared/lib/search.ts`,
`shared/components/Search.svelte`, new `shared/components/Phrases.svelte`,
`app/src/pages/{advanced,phrases}.astro`, and their tests.

Do not touch: `apparatus_*.py`, `shared/lib/search-filters.ts` (read it, keep
it working, leave it alone), the reader, stages 1–5, the lexicon, or anything
under `/formulas`, `/maps`, `/characters`, `/genealogies`.

Repo rules that still apply: vulgate lineation is never renumbered, corpus
source text is never committed, public-domain translations only by US rules,
and deploying is John's call.

---

## 8. Addendum, 2026-07-28: the Phrases page in Svelte — read before Step 6

**Written from aristotle-reader the day the n-gram page was fixed to accept the
phrase as it stands on the page** (PR #57, deployed to gh-pages `99f0b57f`).

**This supersedes what §2 Step 6 implies about the phrase index.** That step
describes a page whose typed prefix names one shard. That design is wrong — it
made the commonest formula in the Metaphysics unfindable — and retrofitting it
in aristotle-reader cost a 325-line diff. Build it the way described here the
first time.

Everything below was measured in aristotle-reader and applies to Homer
unchanged: it is all client-side, so §3's `apparatus_repetitions.py` collision
decides what the shards *contain* but changes none of what follows. Whatever
Homer ends up emitting, the client must still resolve a typed phrase to a plan
of shards rather than to one letter.

### A1. The defect the design must not repeat

The dictionary-form index is keyed on **headwords**. So the phrase a reader has
in front of them matches nothing when typed literally: `to ti hn einai` is
stored as `o tis eimi eimi`, because τό is not a headword — ὁ is. Prefix-match
the typed string and the commonest formula in the Metaphysics returns zero rows
while occurring 127 times.

The fix is to resolve each typed word through `/data/lemma-map/<letter>.json`
(fold(surface) → headwords) and match **every reading** of the phrase. Three
rules, each of which cost something to learn:

- **A single character never widens.** The letter-browse buttons type into the
  same box, and `h` is the surface of ἡ → ὁ, so widening one letter silently
  moves the browse to the O shard.
- **A word the map records uses its headwords alone** — do not union the typed
  word back in. A dictionary form is always among its own headwords (`o` → `o`,
  `os`), so the union changes no result, and τό is a headword of nothing:
  reading it literally fetched a 3.3 MB shard with zero matching rows.
  (`resolveHeadwords` in `search.ts` *does* union, correctly — there the extra
  option costs one index lookup, not a shard.)
- **A word the map does not record falls back to itself.** That is the fragment
  still being typed, and it is what keeps the list narrowing keystroke by
  keystroke.

Cap the fan-out at `VARIANT_READING_CAP` (64) and say so in the UI when it bites.

### A2. Shape it as a plan, not a letter

The readings of one typed phrase **do not live in one shard**. `hn einai` reads
E, H and O and merges 686 rows. So the query resolves to:

```ts
interface Plan {
  key: string;        // `${stream}|${normalizedPrefix}` — the query it answers
  stream: NgramStream;
  byLetter: Array<{ letter: string; prefixes: string[] }>;   // [] prefixes = whole shard
  readings: string[][];
  cappedFrom: number;
}
```

Bounded: the worst case across all 45,942 mapped surface forms is 4 letters, and
96% need 1. Do not cap it — a cap here drops rows silently.

Two consequences that are easy to get wrong and hard to notice:

- **A row's occurrence file comes from the row's own key**, never from the typed
  letter: `shardLetter(item.key)`, not `letter`. Same for the DOM id that keys
  expanded rows. Get this wrong and expanding a widened row 404s or, worse,
  silently resolves against the wrong shard.
- **The work filter should fetch occurrence files only for letters that actually
  produced rows**, not every planned letter. Widening ἦν plans three shards and
  two are routinely dead ends; at up to 2.9 MB per (letter × length) that is the
  difference between 4 fetches and 12.

### A3. Svelte specifics

- **Async derivation needs a signature guard.** An async step in a reactive
  chain must stamp `requestedKey = key` *synchronously, before its first await*,
  and consumers must check `plan.key === wantedKey` before rendering. Otherwise
  a fast typist renders rows for a query they have already replaced. Same
  pattern as the existing shard and work-filter loaders — reuse it, do not
  invent a second one.
- **One scan pass, prefixes grouped by shard letter.** A shard holds up to
  93,000 keys and the prefix test is per reading; testing every key against
  every reading is 6M `startsWith` calls per keystroke. Iterate each shard
  against only the readings that begin with its own letter.
- **Do not put the row filter in a `.filter()` chain if you also need to know
  which readings matched.** One pass returns both; a second pass over 93k keys
  to compute the note is the lazy version of the same work.

### A4. Testing it (the trap that cost the most time)

`shared/lib/data.ts` caches every fetched shard per letter for the life of the
module. Under vitest that means **the second test in a file sees zero fetches**
and passes or fails for the wrong reason.

The obvious fix does not work: `vi.resetModules()` plus a dynamic
`import('../components/Phrases.svelte')` gives you a **second Svelte 5 runtime
instance**, and the component dies with `effect_orphan` — "`$effect` can only be
used inside an effect".

What works: mock the data module and record the calls.

```ts
const { shardCalls } = vi.hoisted(() => ({ shardCalls: [] as string[] }));
vi.mock('../lib/data', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../lib/data')>()),
  fetchNgramShard: vi.fn(async (stream, letter) => {
    shardCalls.push(`${stream}/${letter}`);
    return shards[`${stream}/${letter}`] ?? {};
  }),
}));
beforeEach(() => { shardCalls.length = 0; /* spy fetch for lemma-map only */ });
```

Two more that will bite:

- **The page prints accent-free Greek.** Keys are accent-folded Beta Code, so
  `betaToGreek` yields `ο τις ειμι ειμι`, not `ὁ τίς εἰμί εἰμί`. Assert on what
  the page shows.
- **A phrase appears twice** — once as a row, once named in the note under the
  box — so scope row queries: `findByText(greek, { selector: '.phrase-greek' })`.

Write the failing test first and confirm it fails with the widening off. Five of
the nine tests in `shared/__tests__/phrases.test.ts` do.

### A5. Two control decisions, already made here

Copy them; both were John's calls after using the page.

- **Sort belongs in the results head, above the list** — not in the filter
  panel. It orders results; it does not filter them, and buried among filters
  nobody sees which order they are looking at.
- **The work filter is a checkbox list, not `<select multiple>`.** Picking two
  works out of 41 in a list box needs a modifier key nobody is told about, and
  one stray click throws the whole selection away. Two scrolled columns of
  checkboxes, `bind:group`, and a clear button carrying the count.
- The stream radio reads **"Word in any of its forms"**, not "Dictionary word":
  the word *dictionary* names the knowledge the fix exists to stop demanding.

### A6. Blast radius

Adds to what the main handoff lists: `shared/lib/search.ts` gains two exports
(`lemmaOptions`, and `lemmaReadings` becomes exported), and
`shared/components/Phrases.svelte` owns the plan. Nothing in the pipeline
changes — `stage8_ngrams.py` already emits `/data/lemma-map/`, which is what
makes all of this possible. If your port skipped that emit, go back for it.
