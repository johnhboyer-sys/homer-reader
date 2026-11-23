# Architecture

How the site is made, what it needs, and what it calls. Written so that someone
with this repository and no access to its author's machines or accounts can
build the site and serve it. State and plans for the work that made this
possible are in `HANDOFF-PORTABILITY.md`; how to bring the site back from a
bundle or from source is `RESTORE.md`.

## The site is static

Every page is a file. There is no server code, no database, and no account
system. A host needs to do one thing: serve a folder of files over HTTPS, with
`index.html` for a folder and `404.html` for a missing page.

A build has two parts:

| Part | Folder in a build | Size | What it is |
|---|---|---|---|
| App | `app/dist/` less `data/` | about 4,790 files, 180 MB | Pages, scripts, styles, fonts, map art, share cards, the service worker |
| Corpus data | `app/dist/data/` | about 5,260 files, 166 MB | Per-work JSON: Greek and English by book, scenes and speeches, lemmas, search indexes, LSJ and Cunliffe entries, map plates |

The app fetches data as the reader moves. Where it fetches from is a build
parameter (below), so the two parts can sit on one host or on two.

## From sources to a site

```
corpus/greek/Iliad.tsv    the Iliad's Greek, one printed line per row (committed)
sources/                  the Odyssey's Greek (Perseus), the English translations,
                          Cunliffe, map sources (committed)
apparatus/                scenes, speeches, places, plates, audio manifest (committed)
manifests/*.yaml          one per work: editions, books, translations, gaps
greek-analyses.txt        Morpheus parse table   } not committed; pinned by
grc.lsj.xml               LSJ lexicon            } sha256, from Diogenes 4.7.2
        │
        ▼  pipeline/ (Python): stages 1–7 per work, stage 8, the turn
        │  aligner, the search's scene paging, and their gates
        │  (scripts/build-public.mjs)
build/dist/               corpus data
        │
        ▼  app/ (Astro and Svelte, Node 22), with shared/ compiled in
app/dist/                 the site
```

- **Greek text.** `corpus/greek/Iliad.tsv` holds the Iliad's Greek as a plain
  line file; its README gives the format. The Odyssey's Greek is the Perseus
  TEI in `sources/perseus/`. The build reads them and runs no outside
  program. Making the Iliad's file afresh (`python -m homer_pipeline.extract
  --all`) is a separate step for a machine that holds the digital source
  texts.
- **Two outside inputs.** The Morpheus table and the LSJ XML are not in the
  repository. `python -m homer_pipeline.inputs check` (in `pipeline/`) checks
  the copies it finds against pinned sizes and sha256 sums; the folder is named
  by `DIOGENES_DATA`. On a machine without Diogenes,
  `python -m homer_pipeline.inputs fetch --dir <folder>` downloads the
  Diogenes 4.7.2 release (186 MB, pinned by sha256), takes the two files out
  of it, and holds each to its pin.
- **Full build.** `npm run build:public` at the root checks the two inputs,
  runs the pipeline for both works, the corpus-wide stages, the gates
  (preflight, the shared LSJ and Cunliffe checks), the app build, and the
  link check. About nine minutes on a laptop, six on GitHub's Linux runner.
- **App-only build.** `PUBLIC_SHOW_PRIVATE=0 npm run build` in `app/`, when
  `build/dist/` is already there. About two and a half minutes.
- **`shared/`** is the reader core this site has in common with its sibling
  readers. It is copied between the repositories, not linked.

## Build parameters

All are read at build time. Unset, each gives the primary site's build.

| Variable | Default | What it sets |
|---|---|---|
| `SITE_ORIGIN` | `https://homer.johnhboyer.com` | The origin in canonical links, share cards, `robots.txt`, and the sitemap |
| `SITE_BASE` | `/` | The path the site is served under, such as `/homer/` |
| `PUBLIC_DATA_ROOT` | unset | Where the app fetches corpus data. Unset: `<base>/data` on the site's own origin. Set: an absolute URL on another host |
| `PUBLIC_GRAMMATA_LOOKUP` | Grammata's `lookup.js` | The address of the dictionary script (see outside calls) |
| `PUBLIC_SHOW_PRIVATE` | unset | Must be unset or `0` for anything that leaves the machine; `build:public` forces `0` |
| `DIOGENES_DATA` | each manifest's path | The folder that holds the two outside inputs |

`scripts/site-params.mjs` reads the first two for the Astro config and for the
link check alike, and refuses a value that is not an origin or a base path.

## What runs where today

| Piece | Where | Notes |
|---|---|---|
| App | A Cloudflare Worker serving static assets, at `homer.johnhboyer.com` | `npm run deploy:cloudflare`; `docs/cloudflare.md` |
| Corpus data | A Cloudflare R2 bucket, at `homer-data.johnhboyer.com` | The build sets `PUBLIC_DATA_ROOT` to it |
| Source | GitHub, `johnhboyer-sys/homer-reader` | A private copy on GitLab, `johnhboyer/homer-reader` |

Homer's whole site is about 10,050 files and would fit in one Worker version
(20,000 files); the split matches Aristotle's and Plato's so the three readers
share one recipe. It is a choice of this host, not of the site. The site was
on GitHub Pages until 2026-11-19; the `gh-pages` branch now holds only a
redirect.

## A copy any host can serve

Build with `PUBLIC_DATA_ROOT` unset and the data sits beside the app, so one
folder is the whole site. `scripts/make-bundle.mjs` packs that folder as one
`.tar.gz`:

- without `CNAME`, which belongs to the primary's name;
- with a `SHA256SUMS` that names every file, so a copy can be checked with
  `shasum -a 256 -c SHA256SUMS`;
- only after the data has passed the deploy's data gates (preflight over the
  data, with the public-domain and Creative Commons lists, and the shared LSJ
  and Cunliffe checks), every lemma page in the index has its file, and every
  JSON file parses.

Unpacked at a web root, the bundle is the site. Its canonical links name the
primary, so a mirror does not compete with it in search results.

The `Dockerfile` at the root is the same thing in one command: its first stage
is the full build with its tools pinned, and its second serves the unpacked
bundle with Caddy on port 80.

## Outside calls a visitor's browser makes

| Host | For | State |
|---|---|---|
| The data host | Corpus data, when `PUBLIC_DATA_ROOT` is set | None in a same-origin build |
| None, for fonts | Web fonts | The build bundles its own under `_astro/` |
| Grammata (`PUBLIC_GRAMMATA_LOOKUP`, and its packs on `pub-d505f3fd993b4e01b2ab095428d0493e.r2.dev`) | The word popup's LSJ tab; the script that draws its Cunliffe tab (the record itself is this site's data); the LSJ entry on lemma pages | Stays, by a ruling of 2026-08-29. With it refused, the popup still shows its own headword, gloss, and parses, and the Cunliffe tab says "The dictionary could not be loaded." |
| `cawm.lib.uiowa.edu` | The base tiles of the map explorer (`/maps/`, Leaflet, `LandmarkMap.svelte`) | Loaded when the map shows. Not on decision 4's list: John's call (`HANDOFF-PORTABILITY.md`) |
| `archive.org` | The recitation MP3s ("Hear this passage"; `data/audio.json` names them) | Only when a reader turns the audio on and presses play. Not on decision 4's list: John's call |

Links to Logeion, Perseus, Kosmos, the sibling readers, and the support page
are plain links a reader follows. The site carries no analytics or trackers.
Cloudflare adds its Web Analytics beacon to the pages it serves; that is a
setting of the host, not part of the build (`docs/cloudflare.md`).

## Checks

| Check | Command | What it proves |
|---|---|---|
| Pipeline tests | `cd pipeline && uv run --with pytest pytest -q` | The stages, and that every character of every committed Greek line is Greek or a listed mark |
| Script tests | `npm run test:scripts` | The build, deploy, snapshot, bundle, and outside-call scripts |
| App and shared tests | `cd app && npm test`; `cd shared && npm test` | The reader's code |
| Link check | `node scripts/check-links.mjs app/dist` | No broken link or anchor in a built site, at any base path (`SITE_BASE`) |
| Data gates | `python -m homer_pipeline.preflight <data> manifests`, and `verify_shared_lsj`, `verify_shared_cunliffe` (in `pipeline/`) | Every book and its apparatus, the translation lists, the search indexes, and that every word's dictionary key resolves |
| No outside calls | `node scripts/check-no-outside-calls.mjs` | In a browser whose every request passes a recorder that forwards nothing, the built site shows an Iliad book, a word popup with its Cunliffe record, a search, a lemma page, a map plate, the map explorer, the recitation player, and the book under its service worker, and asks for no host off its allowed list. Needs Playwright and its Chromium |
| A host serves the bundle | `node scripts/check-served.mjs --origin=<host> --sums=<SHA256SUMS>` | A running host answers every file the bundle's list names with the listed bytes, a folder's address with its index, and a missing page with 404 and the 404 page |
| Same output | `node scripts/compare-snapshot.mjs --sums=<snapshot>/SHA256SUMS --prefix=data/ --build=app/dist/data --live-only=docs/portability/homer-live-only-2026-11-20.list` (the page form is in `HANDOFF-PORTABILITY.md`, phase 1) | A build matches a dated snapshot of the live site: data byte for byte, pages byte for byte once the names a checkout's folder changes are swapped |

Two builds of one commit in two folders differ in a few class names and bundle
file names: Svelte hashes a component's absolute path into its style class when
the component lives outside `app/`. `compare-snapshot.mjs` computes the
expected names and accepts those swaps and no others.
