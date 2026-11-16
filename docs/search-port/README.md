# Search port: groundwork

Groundwork for porting aristotle-reader's new search (PR #195, `de57f687c6`) into this reader. No code here
changes the site. The port waits for Aristotle's counting PR (`HANDOFF-SEARCH-FOLLOWUPS.md` there) and for
John's two rulings below.

| File | What it is |
|---|---|
| `diff-map.md` | File by file: what is new in Aristotle, what is Homer's own, what both changed; port or rebuild. |
| `search-counts.mjs` | Runs 18 searches on a served build and records each bar's text, total and pages. |
| `counts-base-2026-11-16.json` | Its output on main `05d0cd885`: the baseline to compare after the port. |
| `unit-counts.py` | Counts three searches under each candidate counting unit, from `build/dist`. |
| `unit-counts-2026-11-16.json` | Its output on the same build. |
| `shots.mjs` | Search-page screenshots at 390, 844 and 1440 wide, both themes. |

Rulings page for John (both rulings, with pictures): https://claude.ai/artifact/5xhtqGkwYRvFgsbSk6DTW5

## How to re-run

```bash
nvm use 22
cd app && npx astro preview --port 4610   # read the bound port from its log
node docs/search-port/search-counts.mjs --base http://localhost:4610 --out /tmp/counts.json
python3 docs/search-port/unit-counts.py build/dist > /tmp/units.json
node docs/search-port/shots.mjs --base http://localhost:4610 --path '/search/?g=θάλασσα&e=sea' \
  --prefix homer-open --open '.group-head[aria-expanded="false"]' --out /tmp/shots
```

Playwright comes from the npm cache; when its own browser build is missing, the scripts use the installed
Google Chrome.

## What the baseline found

- **Homer's search has one search unit per book.** `search/meta.json` holds 24 entries per work, so "and" today
  means both words somewhere in the same book: `θάλασσα` + sea reports "498 instances" over 38 books.
- **A hyphenated English query finds nothing.** "rosy-fingered dawn" (exact phrase) finds 0; "rosy fingered
  dawn" finds 6. `englishFold` (`shared/lib/search.ts:210`) strips the hyphen from the query, giving
  "rosyfingered", a token the index never holds.
- **English rows cite only the book**, not the line, and raw footnote marks (`[^1.8.1]`) show in English
  snippets (visible in the screenshots).
- **The speaker filter re-filters after speech data loads**: the bar first reads "No passages found", then the
  real count. A script that reads the bar early gets the wrong answer; `search-counts.mjs` waits for the
  network to go quiet.
- The rebuilt site: 4,687 pages, 0 broken links (`npm run build:public`, 16 Nov).
