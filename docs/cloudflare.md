# Cloudflare hosting

The plan (John, 2026-11-19): move Aristotle, Plato and Homer off GitHub Pages
and onto Cloudflare. Homer follows the Aristotle Reader's move (its PR #222,
recipe in its `docs/cloudflare.md`): the app goes on a Worker serving static
files, the corpus data goes on R2, and a build-time data root joins them.
The gh-pages branch it replaces held 10,053 files, 331 MB.

## What runs where

| Part | Where | Size |
|---|---|---|
| App (pages, `_astro`, art, og cards, icons, `sw.js`) | Worker `homer-reader`, static assets only, no script (`app/wrangler.jsonc`) | about 4,790 files |
| Corpus data (`data/`) | R2 bucket `homer-reader-data`, keys without the `data/` prefix | 5,261 objects, 166 MB |
| Data address | `https://homer-data.johnhboyer.com` (R2 custom domain; John attaches it at cutover) | |
| Preview | `https://homer-reader.johnhboyer.workers.dev` | |
| Test data address | `https://pub-05b0ee6c05434a4099169d3fdfba5bfe.r2.dev` (r2.dev: rate-limited; turn off after cutover) | |

Homer's 10,053 files would fit under the Workers limit of 20,000 files per
version, so the data could ship inside the Worker as greekdrama's does. It
goes to R2 to match Aristotle and Plato: one recipe for the three readers.

The data root is baked in at build time through `PUBLIC_DATA_ROOT`
(`shared/lib/data.ts`, `shared/lib/search.ts`; every client data fetch goes
through them). The desktop app's `globalThis.__ARISTOTLE_DATA_ROOT__` still
wins. With the variable unset the build is the GitHub Pages build, unchanged.
With it set, `app/scripts/postbuild-data-root.mjs` writes the root into
`dist/sw.js`, so offline reading caches R2 data, and writes
`dist/.assetsignore` so `wrangler deploy` leaves out `dist/data` and every
`.DS_Store`. (gh-pages tracked five `.DS_Store` files, and live served them.)

## Free-tier check (2026-11-19)

R2 before this move: `aristotle-reader-data` 459 MB,
`classical-philosophy-reader-data` 548 MB and `grammata-packs` 85 MB. With
Homer's 166 MB the account holds about 1.26 GB of the 10 GB-month free
storage, before Plato. The first upload costs about 5,300 writes against
1 million free a month. Reads are free up to 10 million a month, and egress
is always free. A payment method is on file for R2, so going past these
limits would be billed, not refused. Workers static-asset requests are free
and unlimited; the Worker runs no script, so the 100,000-requests-a-day
limit on Workers does not apply.

## Build and deploy

From the repo root, on Node 22 (`nvm use 22`), with `build/dist` holding the
corpus:

1. Build. Either the full `PUBLIC_DATA_ROOT=https://homer-data.johnhboyer.com
   npm run build:public` (it passes the variable through to the app build),
   or, for an app-only change, with `build/dist` a copy of live's `data/`:
   `cd app && PUBLIC_SHOW_PRIVATE=0 PUBLIC_DATA_ROOT=https://homer-data.johnhboyer.com npm run build`.
   The last line should read `postbuild-data-root: sw.js and .assetsignore written for …`.
2. Rehearse: `npm run deploy:cloudflare:dry`. It refuses a build without the
   data address or whose `.assetsignore` lets `data/` or `.DS_Store` through,
   checks the page count against the live sitemap (90% floor), runs the link
   check, then Homer's data gates (below), then reads every data file's ETag
   from R2 and lists what would upload.
3. Deploy: `npm run deploy:cloudflare`. It uploads only the data files whose
   MD5 differs from R2's ETag (wrangler `r2 bulk put`, `max-age=600` as
   GitHub Pages sent), reads them back, then runs `wrangler deploy` from `app/`.
   It never deletes from R2: a file the build lacks stays, and it is fetched
   and run through the same data gates. Wrangler cannot list a bucket, so the
   bucket keeps a record of every key the script has uploaded,
   `_deploy/keys.json` (seeded empty on 2026-11-19; the first run filled it);
   upload data only through the script, or the record goes stale.
   Cloudflare's API limit holds uploads to about 1,100 files per 5 minutes,
   so a full corpus upload takes about 25 minutes.
4. Check (optional, while gh-pages is still the record of live):
   `node scripts/compare-live.mjs --app=<worker url> --data=<data address>`
   fetches every file in the gh-pages tree from Cloudflare (4 at a time) and
   compares its hash with the tree's, plus a sample of 40 from live itself.
   The `.DS_Store` files must answer 404.

The data gates are Homer's own, the ones `npm run build:public` ends with:
`homer_pipeline.preflight` over the data R2 will serve (manifests, the
public-domain and CC allowlists, every book and its apparatus, the search
port), and the shared LSJ and Cunliffe coverage checks. Those two read
`build/dist`, the folder the build copied into `dist/data`. The script runs
them with `pipeline/.venv/bin/python`, or `HOMER_PY` if set.

### What changed from Aristotle's script, and why

- **Gates.** Aristotle's script imports five data gates (leak check, gated
  slots, held works, search indexes, search shards) from its
  `deploy-gh-pages.mjs`. Homer has no such script: it deployed by rsync, and
  its gates live in `build:public`. So the script runs those instead.
- **Dropped refusals.** The `/bonitz/` refusals and the `lemma-slugs.json`
  check guard Aristotle-only files. Homer has neither.
- **Added refusal.** `.assetsignore` must exclude `.DS_Store`, and the data
  walk never uploads one.
- **Added check.** No pipeline interpreter, no deploy: the gates need it.
- `walk` and `auditDistScale` live in the script itself, not an import.

Bucket CORS is in `deploy/r2-cors.json`: GET and HEAD from
`https://homer.johnhboyer.com` and the preview origin. Apply it with
`npx wrangler@4 r2 bucket cors set homer-reader-data --file deploy/r2-cors.json`.

Open question for John (the same as Aristotle's): the data is overwritten in
place, not swapped in one step. Between the upload and the Worker deploy, or
for good if the Worker deploy fails, the old app reads the new data. GitHub
Pages had a milder form of this (browsers keep JSON for 10 minutes). A folder
per release would close it, at the cost of a full upload on every deploy that
changes data. For app-only deploys and small data fixes the in-place upload
is safe.

## Cutover checklist (John's to do or approve)

1. **Merge** the PR that brings this file. Merging deploys nothing.
2. **Data hostname.** Attach `homer-data.johnhboyer.com` to the bucket
   (R2 → `homer-reader-data` → Settings → Custom Domains). Cloudflare creates
   the DNS record. The bucket CORS already allows `https://homer.johnhboyer.com`.
3. **Rebuild against it** (the agent, once 2 is done): build current main with
   `PUBLIC_DATA_ROOT=https://homer-data.johnhboyer.com`, `npm run
   deploy:cloudflare`, and rerun `compare-live.mjs` with `--data=` that
   hostname. Approved by John on 2026-11-19: it ships the merged
   `claude/lemma-accents` work, so `data/lemma-accents.json` is new.
4. **Switch the site's DNS.** At a quiet hour: delete the DNS-only CNAME
   `homer → johnhboyer-sys.github.io`, then attach `homer.johnhboyer.com` to
   the Worker (Workers → `homer-reader` → Settings → Domains). Cloudflare
   refuses the custom domain while the old record exists, so expect a few
   minutes of errors between the two steps. HSTS and Always Use HTTPS are on,
   so check `https://homer.johnhboyer.com/` answers before leaving it. Two
   small differences from GitHub Pages: a missing trailing slash redirects
   with 307, not 301, and `/data/...` on the site's own address answers 404.
5. **Check live.** `/`, an Iliad book, `/search/`, a lemma page, and a word
   popup, with the network panel showing data from the data hostname.
6. **GitHub Pages.** Once Cloudflare serves the domain, remove the custom
   domain in the repo's Settings → Pages, then unpublish. The old
   `johnhboyer-sys.github.io/homer-reader/` addresses redirect only while
   GitHub Pages holds the custom domain, so decide first whether they matter.
   Leave the gh-pages branch in place as the record until you choose to
   delete it. `app/public/CNAME` can go then too.
7. **After.** Add `"routes": [{ "pattern": "homer.johnhboyer.com",
   "custom_domain": true }]` to `app/wrangler.jsonc` so a deploy keeps the
   domain; turn off the r2.dev address
   (`npx wrangler@4 r2 bucket dev-url disable homer-reader-data`); update
   CLAUDE.md's deploy recipe and DEPLOY-STATUS.md.

Visitors' service workers update themselves: the origin stays the same, and
the new `sw.js` caches R2 data. Their old cached `/data/` copies stay in the
cache unused until the cache version is next bumped. The cache version is not
bumped here: the data did not change (CLAUDE.md: bump on data change, never
on worker-behaviour change).
