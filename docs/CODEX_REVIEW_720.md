# Adversarial Repository Review — 2026-07-20

**Repository:** The Homer Reader  
**Reviewed commit:** `530ff712` on `claude/build`  
**Review posture:** read-only inspection of source, generated data, documentation, tests, and the existing `app/dist`; the only file created is this requested report.  
**Bottom line:** No P0 blocker remains under the project's current decisions. The reader itself is unusually strong, but the repository has multiple high-severity provenance, philological, security, accessibility, and release-gate defects that should be triaged before the next release.

**Owner decision recorded after review:** Cunliffe's 1931 *Homeric Proper and Place Names* is an explicitly accepted project exception. Its publication status and use are outside this review's issue scope and are not counted as a finding or release blocker.

## Severity scale

- **P0 — Release blocker:** do not publish/redeploy until resolved or explicitly cleared by the relevant human gate.
- **P1 — High:** correctness, security, source integrity, or core accessibility failure; fix before the next release.
- **P2 — Medium:** material functional, UX, performance, maintainability, or operational defect.
- **P3 — Low:** polish, documentation drift, hygiene, or a bounded edge case.

## Executive findings

1. Corpus provenance is internally contradictory: the Odyssey uses tracked Perseus Greek despite the binding TLG-only rule; the homepage labels all Greek as Perseus CC BY-SA even though the Iliad is a licensed TLG export; and the Iliad manifest makes a plainly false “pre-1931” claim about a 1931 edition.
2. Morphology is corrupted by a capitalization bug affecting at least 711 lowercase token occurrences; ordinary words can be globally resolved as proper names.
3. The “Epithets & formulas” feature is not a formula detector. It emits recurring name-adjacent n-grams, includes syntactic fragments, and assigns mutually exclusive Ajax epithets to both Ajaxes.
4. Sacred-lineation checks can miss clean truncation at the start or end of a book, and Greek ingest silently keeps the first of duplicate book/line identifiers.
5. The apparatus data model cannot enforce the stated claim-level citation rule. Most character, place, journey, catalogue, and chronology claims carry no structured secondary citation.
6. The public release command omits the required unit tests and type/import checks. The shared suite is currently red: 534/535 tests pass, with Reading Mode scene paging failing.
7. Share/resume verse hashes do not round-trip, search can race itself, imported translations cross raw-HTML injection boundaries, and most map pins are inaccessible to keyboard users.
8. Several public indexes are far too large for usable navigation: the lemma index renders 4,638 cards in a 1.15 MiB HTML document; the places/formulas/repetitions pages are tens of thousands of pixels long without adequate search or taxonomy.
9. The visual foundation is nevertheless excellent: homepage art direction, parallel-text typography, focus treatment, theme contrast, core token interaction, and responsive reader behavior all performed well in live review.

## P0 — No current blockers

The original review classified Cunliffe 1931 as P0. John's subsequent decision explicitly accepts that use for this project, so it has been removed from the findings. No other issue in this report is classified P0.

## P1 — High-severity findings

### P1-01 — The Odyssey violates the binding Greek-source rule

`AGENTS.md`/`CLAUDE.md:19-20` require local licensed TLG Greek and prohibit committing corpus source text. `manifests/Odyssey.yaml:1-17` instead selects a vendored Perseus Greek TEI; `pipeline/homer_pipeline/__main__.py:17-33` defaults verse works without `greek_source_kind: tlg` to that reader. The Perseus Odyssey Greek XML is tracked under `sources/perseus/`.

The Iliad also retains a tracked Perseus Greek file as a four-line supplement (`manifests/Iliad.yaml:13-17,34-37`). Either migrate the Odyssey to the approved TLG export and revisit the supplement posture, or obtain John's explicit source-policy decision to change the rule.

### P1-02 — Public Greek-source and copyright claims contradict each other

- `app/src/pages/index.astro:266-271` tells users globally that the Greek is “Perseus (CC BY-SA).” `shared/lib/works.ts:137-156` and the reader attribution identify the Iliad as a licensed TLG export of Allen.
- `manifests/Iliad.yaml:3-6` calls Allen's 1931 edition “PD-US” because a “pre-1931 cutoff [was] met by one year.” A 1931 publication is not pre-1931.
- `app/src/pages/attribution.astro:281-286` relies instead on TLG licensing, which is a different authorization basis.

These are not harmless copy errors: they can drive incorrect release decisions and misstate public reuse rights. Source credits and rights bases must be generated per work and reconciled in manifests, attribution, and homepage copy.

### P1-03 — Mixed capitalization globally corrupts morphology

`pipeline/homer_pipeline/stage4_morphology.py:48-67` collapses every surface spelling to one key and turns on a global `capitalized` flag if any occurrence is capitalized. At `:123`, all occurrences are then resolved under that flag. `pipeline/homer_pipeline/beta.py:78` prefers starred proper-name analyses when the flag is true.

Corpus-wide evidence found:

- Iliad: 95 mixed-case keys resolve to proper-name lemmas, affecting 586 lowercase tokens.
- Odyssey: 25 keys, affecting 125 lowercase tokens.

Concrete examples include line-initial `Ἵπποι` at Il. 2.763 causing lowercase `ἵπποι` at 2.770 to resolve as the proper name `*(/ippos` rather than “horses,” and lowercase `γαίης` at Od. 1.59 resolving as `*gai=a`. This poisons word popups, glosses, lemma identity, and proper-name filtering (`pipeline/homer_pipeline/apparatus_vocab.py:219`). Existing morphology tests do not cover the same normalized key appearing in both cases.

Resolve analysis per token or by `(key, capitalized)`, then add mixed-case regressions and regenerate every dependent artifact.

### P1-04 — “Epithets & formulas” is philologically misclassified and misattributes the Ajaxes

`pipeline/homer_pipeline/apparatus_epithets.py:223-303` generates every recurring 2–6-token window that contains a character name. It has no POS, epithet, semantic, metrical, or traditional-formula criterion. Public results therefore include fragments such as `γὰρ Ἀχιλλεὺς`, `δ' Ἀχιλλῆϊ`, and `εἰ μὴ Ἀχιλλεὺς`.

The detector explicitly discards patronymic disambiguation at `:75-80`. Current output gives Telamonian Ajax and Oilean Ajax the same 35 formulas, including each other's mutually exclusive epithets. Six records also contain 17 duplicate references. Literal glosses include fragments such as “and to Achilles to bring which heart” (`apparatus/formula-glosses.json:24`).

This must either be renamed honestly as recurring name-adjacent n-grams, or replaced by a curated/POS-aware, metrical, philologically defensible formula apparatus. Homonymous figures must not share undifferentiated records.

### P1-05 — Public vocabulary and lemma glosses contain materially wrong lexical claims

Live inspection found `ἕπομαι` presented and indexed as “to be,” even though its displayed LSJ entry gives the core sense “to be or come after, follow.” Other examples include `οἶδα` reduced to “see,” `ἁγέομαι` shown as “custom, prescription,” and `ἀμφίπολος` treated as “busied about, busy” where the contextual noun is a handmaid/attendant.

The Draft badge is honest but insufficient because these strings are also prominent page titles/descriptions and therefore public lexical claims. The capitalization defect above explains some errors, but not all gloss selection problems. Add a reviewable gloss provenance field, prevent draft glosses from driving confident SEO metadata, and benchmark a substantial expert-reviewed sample before calling the vocabulary a learning tool.

### P1-06 — Sacred-lineation gates accept clean prefix or suffix truncation

`pipeline/homer_pipeline/stage2_validate.py:67,228-269` checks book presence and adjacent transitions. `pipeline/homer_pipeline/preflight.py:382-422` checks continuity and duplicates, but neither compares the first and last emitted verses with each manifest book's declared `start`/`end`. The columns check at `:649-696` compares derived output with itself.

An in-memory manifest declaring 1.1–1.10 produced zero problems for emitted 1.2–1.10 and for 1.1–1.9. Current output is complete, but the hard gate would accept future loss of a book's opening or closing line. Assert exact manifest boundaries and exact equality of the observed gap set to the expected gap set.

### P1-07 — Greek ingest silently discards duplicate lines and book divisions

`pipeline/homer_pipeline/stage1_perseus_greek.py:83,128-131` and `stage1_tlg_iliad.py:168,217-220` silently keep the first duplicate book or line identifier, including collisions created by normalizing decorated numbers such as `605*`. A duplicate can encode an alternate, athetized, or differently marked line. “First wins” is incompatible with sacred lineation. Duplicate normalized identifiers must be a hard error with raw-source evidence.

### P1-08 — Public alignment ticks are counted but not structurally validated

`pipeline/homer_pipeline/preflight.py:488` skips the non-verse English-marker validator for Homer. Coverage at `:1094-1145` only counts marker list elements against a floor. Malformed objects, invalid offsets, `real:false`, duplicate/reordered ticks, or nonexistent line numbers can meet the floor.

Current ticks passed an independent audit—3,140/1,433 Iliad Murray/Butler ticks and 2,432/1,029 Odyssey ticks were well-shaped, real, anchored, and monotone—but the release gate does not protect that state. Validate shape, membership, bounds, and monotonicity and pin exact/bounded expectations.

### P1-09 — The apparatus schema cannot satisfy the claim-level citation rule

`docs/APPARATUS-SCHEMAS.md:8+` defines scenes, places, characters, catalogue, and speeches without a general claim-level citation field. A current census found:

- 100/100 character records with claim-bearing prose but no citation/source keys;
- 280 place records, only two with structured `sources`;
- 37 journey legs with no secondary citation keys;
- 45 catalogue groups with no citation keys;
- voyage chronology with primary verse citations on only part of the claim structure.

Some prose names Strabo or other sources, but records do not consistently reference `apparatus/bibliography.json`, and `preflight.py:798+` does not validate citation completeness or bibliography IDs. Add structured `citations` to each claim-bearing unit, validate Chicago/web forms and resolvable bibliography IDs, and make completeness a hard gate.

### P1-10 — Deploy commits are going to the wrong remote

The required two-remote split is explicit in `CLAUDE.md:48-52`: source to private `origin`, deployments only to public `deploy/gh-pages`. Instead, `origin/gh-pages` ends at `a00dd596`/`cedd4249`, while `deploy/gh-pages` remains at older launch commit `c3787996`; the branches do not share an ancestor.

Codify one deploy command that refuses `origin`, hard-targets `deploy`, and verifies the remote URL/branch before pushing. Audit whether Pages is enabled on the private source repository and whether that conflicts with the free-tier constraint.

### P1-11 — `build:public` omits the required verification matrix

`scripts/build-public.mjs:54-174` generates data, runs preflight and dictionary coverage, builds Astro, and checks links. It does **not** run pipeline pytest, app/shared Vitest, `svelte-check`, or `scripts/verify-shared-imports.mjs`, despite `AGENTS.md`/`CLAUDE.md:67-73` naming them as the release matrix.

This is currently consequential: the shared suite fails one of 535 tests. A public build can ship red tests or broken type/import boundaries while claiming to be the hard gate. Make a single non-optional, fail-fast release command cover the entire matrix before deploy output is mutated.

### P1-12 — Homeric share/resume hashes do not round-trip

`shared/components/Reader.svelte:1222-1243` writes hashes such as `#1.350`, but mount restoration at `:2054-2077` parses every hash with `parseBekker`, which rejects Homeric dotted verse grammar. `app/src/components/WorkSwitcher.svelte:22-32` and `Landing.astro:517-531` reuse the same broken hash.

Reloaded shared links, work switching, and “Resume” can open at the top instead of the saved verse. Use the work-aware `parseLocation(work, hash)` path and test reload/share/resume for both epics, gaps, and invalid lines.

### P1-13 — SSR book transfer is a module-global race

`shared/lib/ssr-book.ts:19-31` holds a single global book. `app/src/components/ReaderShell.astro:96-107` sets it; `shared/components/Reader.svelte:172-178` consumes and clears it. Concurrent static-page rendering can interleave pages so one book consumes another's data or `null`.

Replace this with page-scoped props/context. If retained temporarily, tag the payload with work/book identity and fail loudly on mismatch. Add a concurrent-render regression.

### P1-14 — Most mapped places are inaccessible to keyboard users

`app/src/components/maps/LandmarkMap.svelte:1144-1214` creates ordinary place/station/city markers with `keyboard:false`; the map itself disables keyboard interaction at `:1315-1323`. Troad, default Wanderings, and Greece render text lists only for unlocated places (`MapsPage.svelte:558-580,682-721`), so located-pin notes and citations have no complete semantic equivalent.

Enable accessible markers or render a full place ledger synchronized with the map. This is a core WCAG issue, not optional map polish.

### P1-15 — Search can issue duplicate requests and display stale results

Enter handlers call `doSearch()` (`shared/components/Search.svelte:933-952,981-989`) while the surrounding form also submits at `:941`. `doSearch`/`applyResultsPipeline` mutate shared state without an abort signal or request token (`:193-225,770-798`), so one Enter can produce duplicate work and an older request can overwrite newer results.

Use submit as the single trigger and abort or sequence in-flight work. Bind result rendering to an immutable submitted-query snapshot.

### P1-16 — English search links and speech filters rely on a gross approximation

`shared/components/Search.svelte:578-587` maps an English character offset proportionally across an entire segment's Greek lines. A segment can span much of a book. The result link and line-based speech filters at `:674-682` can therefore be far from the actual match.

Use emitted alignment ticks/anchors. Any unavoidable fallback must be visibly labelled approximate and excluded from strict line/speaker filters.

### P1-17 — Character apparatus crosses a stored-XSS boundary

`app/src/components/CharacterNetwork.astro:194-202` reads character name, Greek, and role from `data-*` and interpolates them into `innerHTML`. A markup-bearing apparatus record would execute in the flyout. Construct this UI with DOM nodes and `textContent`, following the safer map-popup implementation.

### P1-18 — Imported translations have two raw-HTML injection paths

`shared/components/Reader.svelte:1394-1408,2511-2513` interpolates imported `transId` into an HTML attribute without attribute escaping. `shared/components/FootnotePopup.svelte:48-84,149-156` renders imported footnote strings through `{@html}`. A malicious imported translation can inject markup/script. Validate IDs and sanitize imported rich text with a strict allowlist; add hostile-import tests.

### P1-19 — Reader help is inherited Plato copy and actively misleading

`app/src/components/HelpButton.svelte:126-159` teaches Stephanus citations, dialogues, dialogue lookup, a launcher Greek-word lookup, and Plato-style speaker coloring. The Homer launcher actually supports books, scenes, and verse citations (`shared/components/CommandPalette.svelte:65-134`). Rewrite onboarding around vulgate `book.line`, epic speeches, maps/scenes, token parsing, and the actual command palette.

## P2 — Medium-severity findings

### P2-01 — Most generated apparatus is accepted when merely parseable JSON

`preflight.py:911-1077` largely checks speeches, epithets, scansion, vocabulary, characters, repetitions, and audio for existence/JSON parsing. Tests such as `pipeline/tests/test_preflight.py:84,327-362` explicitly accept empty containers. Stale copies, empty artifacts, invalid references, broken counts, and malformed records can ship. Add schemas, cross-file reference validation, source-copy hashes, and expected coverage/count invariants.

### P2-02 — DICES output knowingly ships an invalid endpoint and loses end-book data

`apparatus_speeches.py:208-242` records invalid endpoints but still emits them; the CLI only warns (`__main__.py:347`). `odyssey-931` begins at omitted Od. 10.456 yet ships normally.

The two Apologoi frames retain `crossBook:true` but discard `endBook`; Od. 9.2–11.332 becomes book 9 with lines `[2,332]`. `shared/lib/speeches.ts:23+` must degrade that frame and cannot associate it with intervening books. Emit full start/end references plus explicit invalid-reference metadata, and fail on unexplained invalid endpoints.

### P2-03 — Scansion confidence overstates what the algorithm establishes

`apparatus_scansion.py:403-459` lets dichrona satisfy either quantity and labels a result `high` whenever only one `(feet, notes)` combination survives, even when it requires synizesis, correption, digamma, unknown quantities, or hiatus. Il. 1.1 is `high` while carrying `synizesis`, `hiatus`, and `brevis-in-longo`.

Counts are 12,385 `high`, 3,302 ambiguous, 499 unresolved for the Iliad and 9,451/2,656/360 for the Odyssey. Prefer `unique-fit`, `ambiguous-fit`, and `unresolved`; lower confidence when relaxations/unknowns are needed and validate on an expert gold sample.

### P2-04 — Build and emit operations are non-atomic and mutate authored state

`stage7_emit.py:429+` deletes an entire work output directory before emission; later failure leaves partial or absent output. `apparatus_scenes.py:358+` rewrites canonical scene source during builds, and `apparatus_speeches.py:295+` can rewrite tracked `apparatus/characters.json`. A release build is therefore neither pure nor failure-atomic.

Emit into a sibling temporary directory and replace atomically only after full validation. Separate authored-source mutation from public builds.

### P2-05 — Per-work reports overwrite one another

`stage7_emit.py:545+` copies both works' validation, morphology, sigla, and missing-lemma reports to generic filenames. The second work wins; current `build/dist/reports/` contains only one generic report set. Store reports under `reports/<work>/` or prefix every filename.

### P2-06 — Future public manifest variants can double-count corpora

`apparatus_repetitions.py:54+` and `apparatus_vocab.py:318+` enumerate work IDs from every YAML without deduplication. Adding `Iliad-public.yaml` beside `Iliad.yaml` loads the same dist work twice, doubling counts and turning unique lines into repetitions. Reuse the public-variant selection logic already in `scripts/build-public.mjs:43`.

### P2-07 — Toolchain/runtime state is not reproducible

- Current system Node is v24.18.0, outside `>=22.12 <24` in app/shared package files.
- Only `app/.nvmrc` exists; the root release command has no engine assertion, root `.nvmrc`, or `packageManager` pin.
- `build-public.mjs:155-158` runs `npm ci` only when `node_modules` is absent, reusing arbitrary installed state otherwise.
- The script uses an arbitrary existing `pipeline/.venv` and never verifies it against `uv.lock`.
- `pipeline/config.py:31` and the CLI default to nonexistent `manifests/EN.yaml`.
- `pipeline/pyproject.toml` claims Python `>=3.9` while the code uses 3.10+ union syntax and `.python-version` says 3.12.

Assert Node 22 at entry, pin package managers, require a work/manifest, and bootstrap or verify the locked Python environment.

### P2-08 — The claimed MIT/source posture is not operationally backed

`app/src/pages/attribution.astro:338-347` says the application is MIT licensed, but no `LICENSE`/`COPYING` exists. The attribution page links users to the source inventory in `homer-reader` (`:227-231`), while the repository is designated private. Include the actual license grant and provide an accessible public inventory/source location, or revise the claims.

### P2-09 — The provenance ledger does not contain what the site promises

`app/src/pages/attribution.astro:227-230` promises pinned external commits, per-file checksums, and source paths. `sources/INVENTORY.md` provides branches/fetch dates but no commit SHA or per-file checksum. Record immutable revisions, acquisition URLs/dates, checksums, rights basis, and transformations for every source.

### P2-10 — Search bypasses the required central data layer

`shared/lib/search.ts:12-19,48-62` duplicates the data-root override and performs direct fetches instead of using `shared/lib/data.ts`. It currently honors the same global override, so this is architectural drift rather than a present path failure. Export and consume a single path/fetch helper.

### P2-11 — Search phrase behavior is internally inconsistent

- Greek phrase presence uses substring matching across joined tokens (`shared/lib/search.ts:144-149`), so a query can match inside unrelated token text.
- Occurrences are recorded once per token rather than once per phrase (`:224-236`), duplicating results and highlighting one word at a time.
- Prefix wildcards work in postings but are stripped/exact-compared during phrase verification (`:105-119,224-235,285-289`), despite the UI presenting wildcard support generally.

Represent phrase hits as exact sliding token spans and test punctuation, accent modes, and wildcarded phrase terms.

### P2-12 — Search state, failure reporting, and citations are incomplete

- URL serialization omits Greek/English match modes, language operator, lemma/form mode, accent sensitivity, and selected works (`Search.svelte:259-291,745-768`). Shared URLs do not reproduce the search.
- A failed work index is only logged to console and partial results look complete (`shared/lib/search.ts:356-375`).
- English hits compute a line but display only the book number (`Search.svelte:674-682`).
- Users can select zero works and receive “No passages found” instead of validation (`:300-310,1015-1020,1074`).

Serialize the full submitted state, surface per-work failures, show `book.line` with an approximation marker where necessary, and require at least one work.

### P2-13 — Search has no page-level heading

`app/src/pages/search.astro:55-58` mounts `Search`, whose `<main>` begins with the form (`shared/components/Search.svelte:940-941`). Live inspection confirmed no `<h1>`. This weakens document structure, screen-reader navigation, and visual wayfinding. Add a visible “Search Homer” heading and use the canonical site shell.

### P2-14 — Multi-term English highlighting can corrupt its own markup

`shared/lib/text.ts:13-22` escapes once and then repeatedly regex-replaces HTML emitted by earlier terms. A later term such as `mark` can match the inserted `<mark>` tag. Compute/merge ranges against original text, then escape and render once. Current security tests cover only one term.

### P2-15 — The command palette accepts nonexistent line numbers

`shared/components/CommandPalette.svelte:77-105` validates the book but not the line. A query such as `Il. 1.99999` is offered and Reader silently snaps to the nearest real line (`Reader.svelte:2032-2046`). Validate against per-book line ranges and known gaps; do not silently reinterpret an invalid citation.

### P2-16 — Scene paging is currently red, and live scene highlighting is stale

The shared test “opens Reading Mode on the scene containing the top-visible line, and pages by scene” fails at `shared/__tests__/components.test.ts:465`: the rendered page contains `ChunkA` but not expected `ChunkB`.

Live Scholar-view checks found related state drift: navigating to `?loc=1.10` correctly focused line 10 but left the scene rail on lines 1–7 rather than 8–32. Clicking scene 43–52 scrolled with the preceding 33–42 scene still marked current. Reconcile the visible-line observer, focus jump, and current-scene state, then add end-to-end URL/click regressions.

### P2-17 — Homer landing and reader metadata use inherited prose-work concepts

- Work landing pages report “24 books, 0 chapters” because `Landing.astro:110-120,180,328-335` reads empty `chapters.json` files.
- Structured data publishes `numberOfPages: 0`, which is semantically wrong.
- `Landing.astro:38,121,159-163` defaults verse works to “Bekker.”
- `ReaderShell.astro:198-203` advertises “Stephanus citation” on all 48 book pages.

Use books/lines and a work-aware vulgate citation description throughout metadata.

### P2-18 — Lemma publication and index scale are excessive

`app/scripts/build-lemmata.mjs:27-31` publishes every non-stopword lemma appearing only three times. Current output has 4,638 lemma pages and about 143 MiB of lemma HTML. Of those, 2,585 titles exceed 60 characters and 4,697 descriptions exceed 160; maxima are 111 and 283.

The lemma index renders all 4,638 cards (`app/src/pages/lemma/index.astro:15-24,107-116`), producing 1,155,852 bytes of HTML, then loops every node on each keystroke (`:139-158`). Live mobile height was roughly 247,586 px. Paginate/alphabetize, debounce or virtualize, shorten metadata, raise the value threshold, and `noindex` thin/unreviewed pages.

### P2-19 — LSJ rendering is a dense wall rather than a usable lexical article

Individual lemma pages flatten long LSJ material into visually dense prose with little sense hierarchy, labels, indentation, or scan support. Mobile use is particularly difficult. Preserve dictionary structure where licensed data permits it: principal senses, sub-senses, grammatical labels, citations, and expandable detail. Do not let a short machine gloss contradict the fuller entry.

### P2-20 — Places, formulas, and repetitions lack adequate large-corpus navigation

- `/places/` contains 438 links, is roughly 40,643 px desktop/60,138 px mobile, and has no search/filter beyond alphabet anchors.
- The Iliad formula ledger contains 3,184 links and is roughly 51,952 px tall, with no effective query/jump tool.
- Repetitions are fragmented by apostrophe/case/orthographic variants (for example `ὣς ἔφαθʼ, οἱ δʼ` versus `Ὣς ἔφαθ', οἳ δ'`) and by prefix/superset duplicates; the page is roughly 14,290 px desktop/21,563 px mobile.

Add client-searchable indexes and meaningful facets. Normalize orthography for grouping while retaining display forms; collapse nested formula families and keep exact variants underneath.

### P2-21 — The character network is a hairball, not a useful first view

The current 96-node/241-edge network has dense crossings and overlapping central labels. It is visually striking but low-comprehension, especially on mobile. Default to a filtered ego network or relation type, add search/focus and an accessible relation table, and reserve “all characters” as an expert view.

### P2-22 — Maps have weak fallback and can hijack scrolling

`app/src/pages/maps/index.astro:5-6,125-126` uses `client:only="svelte"` for the entire explorer, including semantic content. A hydration failure leaves no useful map/place shell. `LandmarkMap.svelte:1315-1323` also enables wheel zoom immediately, capturing ordinary page scroll. SSR a text/list fallback and require focus/deliberate activation before wheel zoom.

### P2-23 — Map presentation depends automatically on a third party without disclosure

`LandmarkMap.svelte:1324-1327` automatically loads CAWM tiles, disclosing visitor network metadata to that provider. Initial markers also remain visibly clumped even with cluster counts. Add a privacy/source disclosure, a graceful local fallback, and tune default bounds/clustering for each map mode.

### P2-24 — Service-worker caching is unreliable and unbounded

`app/public/sw.js:48-68` calls `cache.put` without awaiting it, so the worker may terminate before persistence. `:48-95` places all visited HTML/data/assets into one unbounded cache, and network-first requests have no timeout. The deploy tree is about 294 MiB with individual data files up to 5 MiB.

Separate cache classes, await writes, handle quota errors, impose entry/byte/LRU limits, and add network timeouts plus upgrade/eviction tests.

### P2-25 — Print can lose scholarship and include open UI chrome

`shared/styles/global.css:3444-3448` hides all footnote markers without printing corresponding notes. The print-exclusion list at `:3426-3434` omits newer `.word-sidebar`, `.scene-rail`, `.audio-dock`, and transient tips, so open overlays/player UI can print. Render notes/endnotes and mark all transient chrome with a shared screen-only class.

### P2-26 — Several dialog/form edge cases remain

- `FootnotePopup.svelte:37-43` clamps only the upper bound of `top`; short landscape viewports can produce negative positioning.
- Homepage feedback gives its textarea only a placeholder and radio choices no `fieldset`/`legend` (`index.astro:284-297`).
- The reader Settings “Reset to defaults” clears only typography/copy/speaker-color preferences, not the full visible settings set (`Reader.svelte:372-381,3404-3406`).

Measure/clamp popups to both viewport bounds, add persistent form labels/grouping, and either reset all settings or rename the control “Reset text settings.”

### P2-27 — Mobile/global navigation is inconsistent and unnecessarily tall

The homepage renders twelve navigation links as three wrapping rows on a 390 px viewport, consuming about a quarter of the initial screen (`index.astro:142-162,344-363`). Search uses a sparse custom wordmark/header; SEO landing pages hand-roll another stale header (`SeoLanding.astro:170-181`) despite `SiteHeader.astro` declaring itself the canonical non-reader header.

Use one shell with a compact “Sections” disclosure on small screens. Retain the reader's purpose-built compact header, but align wordmark, theme, and core navigation semantics.

### P2-28 — Character roster alphabet styling is dead

`app/src/pages/characters/index.astro:284-286` renders roster letters as `<h3>`, while CSS targets `.roster-letter h2` at `:228-230`. The intended separators never receive their styles. Align markup and selector and verify the heading outline.

### P2-29 — Browser/print QA scripts are stale and can falsely pass

Multiple scripts still target Aristotle/Plato routes, selectors, Bekker jumps, `/plato-reader`, `/EN/book/1`, or nonexistent Homer paths: `app/scripts/shoot.mjs`, `shoot-mobile.mjs`, `build-design-snapshot.mjs`, `shoot-help.mjs`, `shoot-lsj.mjs`, and `print-check.mjs`. `shoot.mjs:137-147` logs failed scenes without a nonzero exit. They rely on an incidental Playwright copy rather than a declared dependency.

Retarget them to Homer, make assertions fatal, and pin the browser tool if these scripts are release evidence.

### P2-30 — `DRIFT.md` does not meet its own hard rule

`DRIFT.md:3-7` requires one line per divergent shared-core file. A byte comparison found 152 divergent/Homer-only tracked paths and 103 without an exact ledger entry. Excluding image binaries and the data symlink still leaves 52 missing code/config/content paths, including `sw.js`, `manifest.webmanifest`, PWA/maps/header/robots files, seven shared tests, `BekkerJump.svelte`, and scene/audio libraries. `DRIFT.md:45-47` also retains `example.invalid` and base `/`.

Generate the ledger from a comparator and enforce exact-path coverage automatically.

### P2-31 — Deployment and launch documentation contradict current reality

`DEPLOY-STATUS.md:3-4` says no deployment has occurred while `:479-517` records launch/post-launch deploys. Old issues remain listed as open. Root and `docs/` launch checklists describe obsolete domain-root/user-site flows, wrong sitemap filenames, and placeholder state. `app/README.md` remains the Astro starter; `shared/README.md` describes nonexistent consumers/CI.

Replace these with one current runbook and archive historical launch records separately.

### P2-32 — Link checking is useful but narrower than its gate implies

The current checker passed 4,713 pages, 314,575 links, and 148,625 anchors with zero internal breaks. However, `scripts/check-links.mjs` hardcodes `/homer-reader`, skips external URLs, and only scans `a`, `img`, `link`, and `script`. It does not cover audio/source/srcset, CSS URLs, manifest/service-worker resources, sitemap, canonical tags, or JSON-LD. Source the base from one config and add focused metadata/PWA checks.

## P3 — Lower-severity findings

### P3-01 — Theme initialization contradicts its documentation

`ThemeToggle.astro:2-5` says the site follows the OS until explicit choice; `ThemeInit.astro:2-13` always defaults to light. Implement the documented preference or update the copy/tests.

### P3-02 — Offline/PWA colors are stale

`app/public/manifest.webmanifest:8-9` and `offline.html:8-21` retain the older Aegean palette rather than the current wine-dark tokens. The service worker also retains dead Google-font caching (`sw.js:92-95`) although webfonts were removed.

### P3-03 — A help-tour pointer references navigation that is not present

`ParsePopupTour.svelte:42-44` says Maps, Genealogies, and Search are “in the header above,” which is not true in the current compact reader header.

### P3-04 — A nonfunctional dagger is exposed as a button

`Reader.svelte:2456-2461` renders a speech-degradation dagger as `<button>` without activation behavior. Make it annotated noninteractive text or a genuine disclosure.

### P3-05 — Deferred listener installation can outlive the Reader

The timer created at `Reader.svelte:2029-2085` is not stored/cleared on teardown, so rapid unmount can attach listeners after the component is gone.

### P3-06 — Audio/license wording and overlap validation drift

`shared/lib/audio.ts:1` calls CC BY 3.0/4.0 recordings “public-domain,” while `apparatus/audio/manifest.json` correctly identifies CC BY. Iliad Book 3 audio ranges overlap at line 382; code deterministically chooses the narrower chunk, but no validator distinguishes intentional from accidental overlaps.

### P3-07 — Apparatus/source documentation contains stale claims

`sources/loeb-notes/README.md:35` describes an obsolete footnote-key collision scheme; `apparatus_epithets.py:157` documents capitalization behavior opposite to the current implementation; `voyage-chronology.json:4` claims a journey-duration discrepancy already corrected in `journeys.json:112`.

### P3-08 — Repository governance and artifact hygiene are thin

There are no tracked GitHub Actions workflows, Dependabot config, `CODEOWNERS`, `SECURITY.md`, or license file. The deployed branch contains root and `data/.DS_Store`. `pipeline/pyproject.toml` still says “Add your description here,” and several config comments describe obsolete placeholder/root deployment.

### P3-09 — App test coverage is extremely small

The app project has only two substantive tests in `app/src/__tests__/security.test.ts`; there is no route-metadata, sitemap, PWA, canonical, generated-page-budget, or interaction coverage. The app test run also warns that no Svelte config was found.

### P3-10 — Dense reader chrome and map clustering still need refinement

The desktop reader header remains information-dense, while mobile navigation is tall. Default Ships-map markers are still clumped even with cluster counts. These are not functional blockers, but both increase first-use cognitive load.

## Verification performed

### Automated checks

| Check | Result |
|---|---|
| Pipeline pytest | **341 passed** with bytecode/cache disabled |
| Pipeline preflight against current `build/dist` | **Pass / 0 errors** |
| Shared Vitest | **Fail: 534 passed, 1 failed** (`components.test.ts:465`, Reading Mode scene paging) |
| App Vitest | **2 passed**; warning: no Svelte config found |
| Existing built-site internal link checker | **Pass:** 4,713 pages, 314,575 links, 148,625 anchors, 0 broken |
| Current Greek corpus census | Iliad 24 books/15,687 lines; Odyssey 24 books/12,107 lines; all current manifest boundaries match; six declared gaps observed |
| Current scene census | 48/48 books; 412 Iliad scenes and 378 Odyssey scenes |

The shared test was rerun outside the filesystem/network sandbox. The same assertion failed; localhost connection noise changed from sandbox `EPERM` to expected `ECONNREFUSED`, confirming that the red assertion is not merely a sandbox artifact.

No fresh Astro build was run because this review was constrained not to change files, and builds mutate shared `dist`/cache state. Browser checks used the existing `app/dist`. No dependency vulnerability audit was attempted because that requires live registry access; this report makes no claim that installed dependency versions are vulnerable.

### Live UI/UX review

The existing built site was served at its actual bound preview port and reviewed in the in-app browser at desktop (1440×1000) and mobile (390×844), in both light and dark themes. Coverage included:

- homepage, Start Here, both work landings, Search, Maps and Wanderings, Timeline, Characters, Places, Genealogies, Vocabulary, Formulas, Repetitions, Lemma index/detail, About, Attribution, Support, Catalogue, four SEO landing pages, and 404;
- all 48 Iliad/Odyssey book pages;
- Scholar/Reading/Greek views, Greek token popups, Settings, command-palette citation jumps, scene rail, theme switching, and mobile overlays.

All 48 book pages loaded with one `<h1>`, no horizontal overflow, and no browser console warning/error during the crawl. All 24 major public route types loaded without horizontal overflow. Escape closed the Greek token popup and returned focus; token buttons were keyboard focusable; theme and responsive behavior were stable. Findings from interaction and visual review are included above rather than relegated to a separate cosmetic appendix.

## What is working well

- The homepage has a distinctive, Homer-specific visual identity without movie branding. Typography, wine-dark palette, cartographic texture, and hierarchy feel intentional rather than templated.
- Parallel Greek/English reading is clear and mature. The book plate, line ticks, Greek token focus ring, view switching, settings panels, and mobile stacking are strong.
- Both themes use semantic tokens and maintained readable contrast in the surfaces reviewed.
- Core keyboard behavior is thoughtful: Greek tokens are operable; multiple dialogs use focus traps, `inert`, focus restoration, and Escape correctly.
- Astro's default escaping and `jsonLdSafe` protect ordinary page/apparatus data. Most map popups use DOM APIs and `textContent` rather than HTML strings.
- Base-path and work-path composition are generally centralized. No broken internal links were found in the current 4,713-page artifact.
- The current emitted Greek is structurally complete, current translation sources are Murray/Butler/Pope, and no prohibited modern translation or movie branding appeared in shipped surfaces.
- Place identifiers/certainty enums and primary mention endpoints passed the independent audit; scansion keys cover every emitted verse; repetition count/reference consistency was clean.
- The service worker namespaces cache deletion rather than endangering sibling-site caches.

## Recommended order of remediation

1. **Reconcile corpus provenance:** correct Allen/Perseus/TLG claims and complete the Odyssey source-policy human gate.
2. **Protect textual integrity:** fix mixed-case morphology, start/end lineation checks, duplicate ingest behavior, and alignment validation; fully rebuild dependent artifacts.
3. **Make apparatus honest:** replace/rename formula detection, correct Ajax disambiguation, add claim-level citation schema/gates, and review public vocabulary glosses.
4. **Close security and accessibility defects:** eliminate raw-HTML import/network sinks; make all mapped content keyboard/semantic; fix search races.
5. **Repair core navigation:** verse hash round-trip, scene paging/highlighting, English search anchors, and Homer-specific help/metadata.
6. **Make releases trustworthy:** one full release matrix, atomic/pure generation, pinned runtimes, correct remote enforcement, and current deployment documentation.
7. **Tame scale:** paginate/filter lemma, place, formula, and repetition indexes; rationalize SEO thresholds and metadata; bound offline caching.
8. **Finish UX consistency:** one global non-reader header, compact mobile navigation, structured LSJ display, usable character graph, and reliable print output.

## Review limitations

- This was a static/code/data review plus interaction testing of the existing built artifact, not a penetration test, legal opinion, or expert line-by-line verification of every translation and apparatus statement.
- External URLs, third-party availability, dependency advisories, real assistive-technology sessions, and performance on low-end hardware were not exhaustively tested.
- Sampling was used for semantic/philological content beyond the corpus-wide scripted audits explicitly quantified above. The report does not imply that unreported lexical/apparatus records are correct.
