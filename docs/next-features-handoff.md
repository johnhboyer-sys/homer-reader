# Handoff: five features the advanced-search work made possible

**Written 2026-07-28**, the day advanced search shipped (PR #13, merged to `main`).
Every number here was measured against the built corpus that day. Estimates say so.

These are not speculative. Each one is possible *because* of what PR #13 put in
the build, and for three of them the data already ships — the work is surfacing,
not building.

---

## The list

- [ ] **1. Cross-epic phrase filter** — small. Data ships today.
- [ ] **2. The dual as a first-class query** — small. Data ships today.
- [ ] **3. Enjambment index** — medium. Data ships today; needs a page.
- [ ] **4. Metrical position** — large. The headline. Inputs all exist.
- [ ] **5. Certainty-aware grammar filters** — medium. Philologically the most serious.
- [ ] *(deferred, bigger than it looks)* Dialect as a searchable facet.

Suggested order: 1 and 2 together (one lane, one afternoon), then 3, then 4, then 5.
4 and 3 are natural companions — both are about where a phrase sits in the verse.

---

## Corpus facts you will need (measured 2026-07-28)

| | Iliad | Odyssey | total |
|---|---:|---:|---:|
| Greek tokens | 111,887 | 87,189 | 199,076 |
| grammar signatures | 2,138 | 1,937 | — |
| signatures carrying a dual reading | 263 | 227 | — |
| tokens with a dual reading | 3,785 | 2,757 | **6,542** |
| scansion lines | 15,687 | 12,107 | 27,794 |
| scansion high-confidence | 12,385 | 9,451 | — |
| scansion ambiguous | 3,302 | 2,656 | — |
| scansion unresolved | 499 | 360 | — |

Phrase index: form 68,550 phrases / 6.7 MB · lemma 158,973 / 15 MB · english
118,695 / 12 MB · lemma-map 764 KB. **34 MB total**, no shard over 2 MB.

Grammar ambiguity (Odyssey, from `build/stage6/grammar_report.json`): case
**42.1%**, gender 35.4%, person 24.3%, mood 22.4%, tense 21.0%, number 14.5%,
voice 10.9%, marker 5.2%, degree 0%. Note that report is per-run and the second
work overwrites the first — if you need the Iliad's, capture it during its run
or recompute from `grammar-dict.json` + `grammar-col.bin`.

---

## 1. Cross-epic phrase filter

**What.** A toggle on `/phrases`: show only phrases occurring in *both* epics.

**Why it is nearly free.** The browse row is already `[n, count, score, works]` —
the work map ships in the browse shard precisely so the UI can say "37 times
across 2 works" without loading a single occurrence file
(`pipeline/homer_pipeline/stage8_ngrams.py`, header docstring). The filter is a
predicate over a field that is already in memory.

**Why it matters here.** "Corpus-wide" means two works in this repo, so the
recurrence bar is low and the cross-epic hits are the interesting ones. A phrase
in both poems is a real finding about shared formulaic diction; a phrase in one
is ordinary. Right now both look alike in the list.

**Build.** A checkbox beside the existing within-verse control in
`shared/components/Phrases.svelte` (the verse toggle is at `:157`, `:192`, `:703`,
`:973` — copy its shape), filtering on the row's `works` array. No pipeline change.

**Do not** compute this at build time as a separate stream. It is a view over one
existing field.

---

## 2. The dual as a first-class query

**What.** Let a reader ask for dual forms — on its own for browsing, and as a
grammar slot in a combo query.

**Why now.** `number` is already an indexed category and `dual` is already one of
its values (`stage6_search.py:124`, `"number": "sg pl dual"`). **6,542 tokens
across the corpus carry a dual reading.** It is indexed and unreachable.

**Why it matters.** The dual is a hallmark of Homeric Greek and the site of a
famous crux — the duals used of the embassy in *Iliad* 9, which have been argued
over since antiquity. "Show me the duals in Book 9" is a teaching query the
reader should be able to answer in one click.

**Build.** Surface `number=dual` in the combo panel's grammar slot
(`shared/components/Search.svelte`, `GRAMMAR_CATEGORIES` and the grammar grid),
and consider a link from `/advanced` naming the Iliad 9 case as an example.

**Caution.** Read §5 before shipping a bare dual filter. Of those 6,542 tokens,
some carry dual *among several readings* rather than certainly. Ambiguity in
`number` runs 14.5% — lower than case, but not nothing, and the Iliad 9 crux is
exactly where a reader will not accept a silent guess.

---

## 3. Enjambment index

**What.** A corpus-wide list of recurring phrases that cross a verse end.

**Why now.** The build deliberately retains straddling phrases — filtering them
out at build time would have made the within-verse toggle unimplementable
(`docs/advanced-search-handoff.md` §3). So the enjambment index is the exact
complement of a filter that already runs: instead of keeping occurrences inside
one `line_runs` entry, keep the ones that are not.

**Measured, so you know the shape of the result.** τε καί occurs **526** times:
**511** inside a single verse, **15** across a verse end — including a real
enjambment at Il. 2.676/677, `Κάσον τε / καὶ Κῶν`. Roughly 3% for that phrase;
compute the corpus-wide distribution before designing the page, because the
useful cases are probably the phrases with a *high* straddle ratio, not the
common ones with a low one.

**Why it matters.** Enjambed formula is live scholarly ground — Parry and Lord on
the formula's fit to the verse, Higbie's *Measure and Music* on enjambment types.
No search tool for Homer exposes it. This is the cheapest genuinely novel thing
on the list.

**Build.** A view over existing occurrences plus `line_runs`; reuse `unitRange`
and `lineStarts`, now exported from `shared/lib/search.ts`. Probably its own page
rather than a mode on `/phrases`, because the interesting sort is by straddle
ratio, not by count.

**Do not** conflate it with `repetitions.json`, which is within-line by
construction and is a philological claim, not a search result. Say plainly on the
page how the two differ, as `/phrases` does.

---

## 4. Metrical position — the headline

**What.** Index each token's slot in the verse, so *πόδας ὠκὺς Ἀχιλλεύς,
verse-final only* becomes answerable. Formula is position-bound, and no existing
Homer search tool indexes position.

**Why now.** Every input exists and PR #13 supplied the missing one.
`apparatus_scansion.py` already emits per-line feet strings with honest
confidence flags; `offsets.json` gives every token a global position;
`line_runs` gives its line. Combine them and you get a metrical column, built
exactly like the grammar column of PR #13 (`grammar-col.bin` is a 2-byte-per-token
packed column against a signature dictionary — copy that design).

**Two constraints, from the original handoff §4 and still binding.**
- **Scansion's `confidence: "ambiguous"` must propagate.** 3,302 Iliad lines and
  2,656 Odyssey lines are ambiguous, plus 859 unresolved — that is 21% of the
  corpus. A metrical filter that silently treats ambiguous lines as certain is
  exactly the overstatement the scansion module was written to avoid.
- **The caesura is a derived judgement and is not in the data.** Ship verse
  position first (initial, medial, final); treat caesura-relative queries as a
  later question.

**Sequence.** This wants a finished index under it, which it now has. Do it as its
own PR.

---

## 5. Certainty-aware grammar filters

**What.** Distinguish *certainly* genitive from *possibly* genitive in grammar
queries, rather than treating a three-way ambiguous analysis as a settled parse.

**Why it matters.** **42.1% of case-bearing tokens are ambiguous.** A reader
filtering for genitive today gets a pile in which two of every five tokens are
only maybe genitive, with nothing to say so. The apparatus already applies
certainty tiers to place identifications (`certain | traditional | speculative |
mythical`); this is the same honesty applied to morphology.

**Why the data supports it.** PR #13 kept **whole readings**, never a per-category
union — `{masc nom sg, fem acc pl}` deliberately does not satisfy masc+acc+sg,
and there is a test pinning that. So "this token has exactly one reading and it
is genitive" is already answerable from `grammar-dict.json`; nothing needs
re-deriving.

**Build.** A tri-state on the grammar slot — *any reading* / *only unambiguous* —
plus a marker in the result row when a hit rests on one of several readings.
Cheapest correct version: precompute an is-unambiguous bit per signature at
build time in `stage6_search.py` and let the client read it.

**Do not** default to "only unambiguous". Ambiguity is the normal state of
Homeric morphology, and a default that hides 42% of case-bearing tokens would
mislead worse than the current silence.

---

## Deferred: dialect as a searchable facet

Morpheus tags Homeric forms with dialect labels, and they are currently in the
ignore list by design (`stage6_search.py:151`, `_IGNORED_TAGS`) because they are
not morphology. Measured over the Odyssey: `epic` 10,493, `ionic` 8,413, `doric`
3,943, `attic` 3,437, `aeolic` 2,801, `homeric` 2,010. **The Iliad was never
measured** — its stage-4 output was unavailable when that list was drawn up.

It is genuinely attractive: no other Homer search tool lets a reader ask for
Aeolic forms in Book 9. It is also anti-selective at 10,000+ hits per label, so
it needs the same combo-only treatment grammar got, and it means moving values
out of `_IGNORED_TAGS` into `_FEATURES`, which changes every signature in the
dictionary and forces a full re-emit. Bigger than it looks. John's call.

---

## Standing rules that still bind all of the above

- **Vulgate lineation is sacred.** `line_runs` holds emitted line numbers, never
  an enumeration index. The Odyssey's gaps after 10.455, 16.100 and 23.48 are
  data, not bugs.
- **A CLI rebuild is not `build:public`** — see `CLAUDE.md`. `stage7` recreates
  `build/dist/<work>/` and wipes the per-work apparatus copies, `speeches.json`
  above all. The symptom reads exactly like a scene-paging regression.
- Any `stage7` re-emit must be followed by `apparatus --work <W>` for both works
  and a 48/48 scenes check.
- `pytest` is not a rebuild. The real rebuild is
  `python -m homer_pipeline all --work <Iliad|Odyssey>`, about 6 minutes for both.
- Run vitest from `shared/`, not the repo root. `nvm use 22` first.
- Deploying is John's call. Apparatus `draft → reviewed` flips are John's alone.
