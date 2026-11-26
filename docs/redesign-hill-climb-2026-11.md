# Redesign hill climb, 25–26 November 2026

Branch `claude/redesign-hillclimb` (off main `a020643ca`). Nothing merged, nothing deployed.
Harness, briefs, judge votes and every round's measurements: `~/Developer/homer-redesign-hillclimb/`
(outside git; `PLAN.md` there is the running log).

## What you asked for

"Rounds of redesign scored by Opus, Codex, and Grok. Optimize and modernize." Free hand on
looks with the hard rules kept (AA in both themes, keyboard access to Greek words, blue sea,
no movie branding, skin as a token layer). Optimize page weight, reading, and navigation.
Five rounds, then this report. Search page body left alone.

## How each round was judged

Each candidate was built and served locally. The harness shot 17 pages in four views (desktop
and phone, light and dark), measured bytes, LCP and CLS, and ran axe in both themes. It also ran
a keyboard check (Tab to a Greek word, Enter and Space open the popup) and both vitest suites.
Judges saw the two versions side by side, with the sides in random order per image, and did
not know which was new. `tally.py` unblinded the votes afterwards. A round was kept when the
judges who could vote preferred it, no hard rule broke, and bytes rose no more than 10%.

## Rounds

| Round | What changed | Blind votes (new – old – tie) | Kept |
|---|---|---|---|
| 0 | Critique of the live site | Judges scored it 4.6–6 out of 10 | — |
| 1 | "Edition" skin: Gentium Book Plus for Greek and English, Newsreader display, Inter for controls; warm paper / dark ink tokens; Flaxman line art; new header | Opus 28–0, Grok 27–1 (against Grok's own design) | yes |
| 2 | Header menus as real disclosures (Atlas / People / Language); 17 reference pages restyled; breakpoints unified at 680px; seven defects from Grok's review fixed | Opus 40–0, Grok 27–13 | yes |
| 3 | Navigation: header Go to field and ⌘K palette take citations (`6.237`, `od 9.105`), places, people and lemmas (`menis`, `μῆνις`); breadcrumbs; end-of-book links; cross-links from places and people; Codex's five findings fixed | Opus 30–0–10, Grok 25–2–13 | yes |
| 4 | Speed: fonts split by character range, art at display size, palette and plates loaded on demand, reader JS 135 → 79 KB | Opus 0–0–40 (no visible change, as intended) | yes |
| 5 | Phone polish: strips wrap instead of clipping, phone layout for the character graph, hanging indent for wrapped hexameters, 3:1 borders and tracks, lemma page in two columns, no scene-card shift in Reader mode | Opus 13–1–26 | yes |
| Final | Round 5 against the live site | Opus 64–0, mean score 5.2 → 8.0 | — |

Who could vote: Codex's five-hour window ran out twice, so it judged no round. Grok judged
rounds 1–3 and was benched by the budget board after that (83% of its week). Rounds 4, 5 and
the final were judged by Opus alone. Opus is the same model family as the lanes that built
rounds 4 and 5, so those three verdicts lack a cross-family check. The code was reviewed
across families: Grok reviewed rounds 1 and 2, Codex reviewed rounds 1–2 (five findings, all
fixed in round 3), and the Codex review of rounds 3–5 is below.

## Before and after

Pictures in `docs/redesign-2026-11/` (left: main; right: this branch):
`home-desktop-light`, `iliad-1-desktop-light`, `iliad-1-desktop-dark`, `iliad-1-mobile-light`,
`odyssey-9-mobile-dark`, `iliad-index-desktop-light`, `places-mobile-light`,
`characters-desktop-dark`.

Page weight (KB transferred, desktop, cold, Brotli; median of three loads on a local server):

| page | before | after | change | JS before | JS after | LCP ms before → after |
|---|---|---|---|---|---|---|
| home | 379 | 134 | −65% | 56 | 3 | 112 → 44 |
| /iliad/ | 79 | 139 | +75% | 57 | 4 | 56 → 44 |
| Iliad 1 | 454 | 292 | −36% | 135 | 81 | 208 → 92 |
| Odyssey 9 | 467 | 284 | −39% | 135 | 81 | 172 → 88 |
| maps | 234 | 296 | +27% | 143 | 136 | 96 → 36 |
| places | 66 | 186 | +181% | 0 | 4 | 84 → 72 |
| characters | 36 | 131 | +260% | 0 | 4 | 64 → 52 |
| timeline | 30 | 151 | +397% | 0 | 3 | 64 → 48 |
| lemma μῆνις | 20 | 95 | +363% | 1 | 3 | 56 → 40 |
| about | 19 | 90 | +384% | 0 | 3 | 52 → 36 |
| genealogies | 25 | 100 | +300% | 0 | 3 | 52 → 36 |
| vocabulary | 25 | 100 | +299% | 0 | 3 | 56 → 64 |
| formulas | 17 | 95 | +452% | 0 | 3 | 36 → 32 |
| repetitions | 90 | 142 | +58% | 55 | 35 | 56 → 48 |
| read-the-iliad-online | 18 | 117 | +558% | 0 | 3 | 48 → 40 |

The reader and the home page are lighter than before. Plain pages are heavier because the live
site loads no web fonts at all; the redesign's type (Gentium, Newsreader, Inter) costs 47–104 KB
on each page, already cut by about a third in round 4. Every page stays under 300 KB except
search, and LCP is equal or faster on every page but vocabulary.

Gates on the final build: build ok (4,687 pages); axe 0 violations on all 17 pages in both
themes; keyboard check passes (21 Tabs to the first Greek word in Iliad 1, 22 in Odyssey 9;
main takes 22 and 23); vitest shared 2,612 passed / 0 failed / 5 skipped, app 96/96; link
check (round 3) 431,324 links, 0 broken; CLS 0 on every page but search (0.0104, unchanged)
and read-the-iliad-online (0.0012).

## Decisions for you

1. **Merge.** Open a PR from `claude/redesign-hillclimb` to main when you want it; deploying
   stays your call.
2. **System font for controls** (commit `b1846f81b`, on `claude/redesign-r4`, NOT on the climb
   branch). Replaces Inter with the system UI face for buttons and menus; saves about 20 KB on
   every page and brings six more plain pages under 90 KB. Opus could not tell them apart
   (37 ties of 40). The judges only saw macOS, where the system face is San Francisco; on
   Windows it is Segoe UI and on Android Roboto, and nobody has looked at those.
3. **Page weight on plain pages** (table above): web fonts are the price of the new type. If
   that is too much, the system-font commit is the cheapest cut; the next is splitting
   `global.css` by page type (not done; it was not clean).
4. **A live bug fix that could ship alone.** `shared/lib/tick-chunks.ts`: the phone's stacked
   view dropped the first line of a block (Od. 9.1 was missing). Fixed with a test in round 1.
   It can go to main as its own small PR before the rest.
5. **Interface copy the lanes added.** Short labels only: section eyebrows, breadcrumbs, "Find
   a place", "Every mention in the Greek", "On the map", "First speech", "Read them in context".
   No translation, Greek or apparatus text changed. Lemma pages now cite occurrences as
   `1.75` where they printed `175` (a display fix).
6. **Copy left alone for you to rule on:** the Iliad index says "exact Bekker citation", which is
   Aristotle's scheme, not Homer's.

## Rough edges left

- Reader mode on desktop still shifts slightly on scenes with a map (Od. 9: CLS 0.044, as
  before the climb).
- At 375px, 43 of the 611 lines of Iliad 1 still wrap; they turn with a hanging indent. Zero
  would need smaller Greek type.
- The phone character graph names 84 figures (desktop 95); the rest are in the roster below.
- ⌘K re-sorts once when the lexicon finishes loading; "tro" lists Tros before Troy.
- No "all speeches by this character" link: search does not take a speaker alone.
- Controls on the search page body were left as they were (out of scope), so a few borders
  there are below 3:1.
- Plain pages over 90 KB: places, characters, timeline, repetitions (HTML size or JS).
- Work-index drawings load as they scroll into view; readers without JavaScript see none.

## Codex review of rounds 3–5

Pending (Codex's window reopened at 00:46). Findings will be added here and fixed before any PR.

## Branches

`claude/redesign-hillclimb` (final), and the round branches `claude/redesign-r1-fable`,
`-r1-grok` (rejected), `-r2-core`, `-r2-pages`, `-r3`, `-r4` (holds the font experiment),
`-r5`. All pushed. Worktrees left: `~/Developer/homer-reader-redesign`, `-r4`, `-r5`.
