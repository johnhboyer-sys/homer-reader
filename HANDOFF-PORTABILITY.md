# Handoff — portability (Homer)

The Homer port of the portability track. The plan, John's rulings
(decisions 1 to 10), and Aristotle's worked example live in
`johnhboyer-sys/aristotle-reader`: its `HANDOFF-PORTABILITY.md` and merged
PRs #228 and #231 to #236. Plato's port (`johnhboyer-sys/plato-reader`, PRs
#130 to #136) is the sibling example. Read Aristotle's "Goal" (the five
tests), "Decisions", and "Plan" first; this file records what the port did
here, what was decided and why, and what failed. Rewrite it as state changes.

The goal, in one line: the site builds from a clone plus checksummed inputs,
with no laptop; any static host can serve it; and copies live off GitHub and
Cloudflare.

## State (2026-11-23)

Phase 1 is on `main`: John said "merge pr 78" on 2026-11-23, and this
session merged homer-reader #78 (`7a13697f2e`) with all five CI jobs green.
Phase 2 is in a PR, and phase 3 in a PR stacked on it (below). Nothing is
deployed.
John ruled on 2026-11-23 that test 3 may call two hosts of Homer's own beside
Grammata's: CAWM's map tiles and archive.org's recitation audio. John ruled the
rest on 2026-11-23: the licence as recommended (MIT in `LICENSE`, CC0 1.0 on
`corpus/greek/` now, CC BY 4.0 on his own apparatus, every source on its own
terms, listed in `sources/INVENTORY.md`); the Kosmos text goes out in public
releases as the live site serves it (A); and decision 10, keep both fixtures
pinned (A). The licence is a PR stacked on phase 3.

| Phase 1 step | State |
|---|---|
| `extract` writes `corpus/greek/`; the build reads only those | Done: one file, `Iliad.tsv`, 15,707 rows, 1,454,387 bytes. Stage 1 runs no program |
| Guard on the committed file, failing cases first | Done: every text character Greek or one of five marks; every margin one of the edition's seven signs or two words; no named exception. 24 hand breaks each fail a test |
| The line file gives stage 1 the export's spine | Done: byte for byte the same three ways (old code on the XML, new code on the line file, new code on the XML), 2,075,799 bytes; 24 books, 15,687 lines, 2,815 with sigla, 528 bracketed |
| Morpheus table and LSJ pinned by checksum, folder from the environment | Done: the same two files as Aristotle's pins, byte for byte (sha256 `dfca7ef1…`, `af72685a…`); `inputs check` runs first in `build:public`; `inputs fetch` for a machine without Diogenes |
| Machine paths out of the public build | Nothing to take out: the manifests name only Diogenes.app, as the local default for `extract` and the two inputs, and `../TLG Files/TLG` as `TLG_DIR`'s default |
| CI runs the full build and uploads it | Done: the `site` job. Run 45223733485 passed in 6 min 20 s: inputs fetched and matched their pins, 0 broken of 335,540 links, 10,049 files packed with a `SHA256SUMS` |
| Same output as live (test 2) | Laptop build done: 5,262 of 5,262 data files byte for byte the snapshot's; the app at `9e327f885` 4,787 of 4,787 files equal (4,725 byte for byte, 62 once 67 folder names are swapped). Linux build (CI's artifact): 10,049 of 10,049 files read against its sums, 5,262 of 5,262 data files byte for byte the snapshot's |
| Review by another model family | Done: Codex (GPT-6.1-Sol, medium), two reads. First: seven findings, five fixed with tests first, two answered. Second, of the fixes: two gaps left in the export scan, both fixed with tests first |

| Phase 2 step | State |
|---|---|
| Build parameters for origin, base path, and the Grammata address | Done: `SITE_ORIGIN`, `SITE_BASE` (`scripts/site-params.mjs`, read by the Astro config and the link check), `PUBLIC_GRAMMATA_LOOKUP`. Unset, the app is 10,050 of 10,050 files byte for byte the phase 1 build |
| A build at a test base path passes the link check | Done: `/mirror/` at another origin, 4,687 pages, 335,540 links, 0 broken. The same build checked as if at `/` reads all 335,540 as broken and exits 1 |
| Fonts self-hosted | Already so (bundled under `_astro/`); test 3 proves it: no font host asked for, and a planted Google stylesheet link fails it |
| No outside calls (test 3) | Green at `/` and at `/mirror/`: 8 of 8 visits, 3 outside hosts asked for, all allowed (Grammata, CAWM's tiles, archive.org's audio) |
| The mirror bundle | Done: `scripts/make-bundle.mjs`, 10,048 files, 347 MB, 59 MB packed, six gates on 5,262 data files |
| `check-served.mjs` | Done (Aristotle's, unchanged); used by the image workflow and the restore drill |
| `Dockerfile`, Caddy, image workflow | Written; the image is built only in CI (never on the Mac), on this PR |
| `ARCHITECTURE.md`, `RESTORE.md` | Written; `RESTORE.md`'s log records each path run |
| Review by another model family | Codex (GPT-6.1-Sol, medium), two reads: four findings, then two gaps in the fixes; all fixed and each break shown failing; one partial-loss case recorded as known |
| The bundle on two candidate hosts | Waits on John (decision 6, accounts), as for Aristotle and Plato |

| Phase 3 step | State |
|---|---|
| Push the repo to a second git host | Done: `scripts/mirror-git.mjs` (Aristotle's, unchanged), run by `mirror.yml` with Homer's deploy key since 2026-11-23; first run 45245208945, 15 of 15 refs (below) |
| Check a git mirror | Done: `scripts/mirror-check.mjs`, run for real against `git@gitlab.com:johnhboyer/homer-reader.git` (below) |
| The deploy tags its commit | Written: `npm run deploy:cloudflare` tags `deploy/<date>` after the Worker deploy succeeds and pushes the tag; `--no-tag` holds it back; the dry run never tags. Not yet run in a real deploy |
| A release for each deploy tag | Written: `.github/workflows/release.yml`, the shared `site-bundle` action, then the bundle's data held to `homer-data.johnhboyer.com`, then `gh release create`. Runs first at the next deploy after this merges; about 59 MB public each time, the Kosmos text among it (below) |
| `mirror.yml`: git on every push, the check weekly | Written. On a push, the git job skips while `MIRROR_GIT_URL` is unset and the check job never runs (this PR's run shows both skipped). The weekly check (Mondays, 11:17 UTC) runs regardless: until the key is set it cannot read the private mirror, fails, and opens one "Mirror check failed" issue, then comments on it each week |
| `check-mirrors.mjs` and `mirrors.json` | Done: `mirrors.json` names the GitLab mirror; the check runs and fails truly (below) |
| Review by another model family | Codex (GPT-6.1-Sol, medium): one finding, a claim in this file that the weekly check skips without the key; corrected (it runs and fails; see the record). No finding in the deploy tag, the release workflow, or the copies |

## Phase 3 record

**What was ported.** `scripts/mirror-git.mjs`, `scripts/mirror-check.mjs`,
`scripts/check-mirrors.mjs`, their tests, `.github/actions/mirror-key`,
`.github/mirror_known_hosts`, and `.github/workflows/mirror.yml` are
Aristotle's merged files unchanged (Plato's are byte for byte the same), but
for one test line that names the reader's base path (`/homer/`). So they
carry every fix the three Codex reviews of Aristotle's forced (its phase 3
record lists them). `release.yml` (Plato's) and `mirrors.json` are renamed for
Homer: the bundle `homer-reader-<tag>.tar.gz`, its data held to
`homer-data.johnhboyer.com`. The deploy tag (`tagPlan`, `tagCommits`,
`uncleanFiles`, `tagDeploy`, `--no-tag`, and the lines in `main()`) is ported
by hunk from Plato's `deploy-cloudflare.mjs`, which has the `uncleanFiles()`
fix (untracked files asked for by name), into Homer's own script, whose gates
differ; its tests come with it.

**Checks.** Script tests 182 of 182. Five hand breaks of the ported tag code
(an unclean tree tagged, a failed push leaving its tag, a second tag at one
commit, an annotated tag's peeled line dropped, untracked files left to the
`status.showUntrackedFiles` setting) each fail a test. A first try at the
annotated-tag break (always overwrite) changed nothing, since `ls-remote`
lists the peeled line second; the break that drops it is the real one.

`mirror-check.mjs` against the GitLab mirror (read with the account key the
lead session made for phase 0):

```
FAIL git@gitlab.com:johnhboyer/homer-reader.git: 10 of 13 refs match; 1 skipped (refs/heads/gh-pages)
  missing on the mirror: refs/heads/claude/portability-phase1
  missing on the mirror: refs/heads/claude/portability-phase2
  differs: refs/heads/main is 7a13697f2e… at the source and 9e327f885c… on the mirror
```

That is the truth: the mirror is the lead session's copy of 2026-11-21;
`main` has moved since (#75 to #78) and the two branches came after it.
Nothing keeps it current until `mirror.yml` has its key. With those three
(and `gh-pages`) skipped: `ok …: 10 of 10 refs match; 4 skipped (…);
history: 809 commits, whole`. `check-mirrors.mjs
--source=https://github.com/johnhboyer-sys/homer-reader.git` reads
`mirrors.json` and fails the same way (`FAIL 0 of 1 mirrors whole and
current`, the three refs named, history not checked because the refs do not
match).

**The Kosmos text in a public release (ruled A by John, 2026-11-23).**
`release.yml` attaches the whole bundle to a public GitHub release at each
deploy. The bundle holds the Kosmos Society revision of Butler (CC BY-NC-ND
3.0), as the live site serves it: verbatim, with its attribution, in each
book's data. A release is a public download, not only a page. John chose to
ship it so; the licence table in `sources/INVENTORY.md` names its terms.

**The weekly check before the key (Codex's review).** `mirror.yml`'s git
job is guarded by `MIRROR_GIT_URL`; its check job is not (it runs on the
schedule and by hand, never on a push). Merged before the key is set, the
check fails each Monday, since it cannot read the private mirror without a
key, and keeps one open issue, "Mirror check failed", with a comment a week.
That is the truth, the mirror being stale, but it is noise. The workflow is
the siblings' file byte for byte, so it is not changed here: set the key
before merging this, or close the issue once it is set.

**Homer's deploy key (2026-11-23).** The lead session made the pair and put
the private half in the repository secret. John confirmed at 13:05 that
GitLab has the key and the protected-branch setting: "gitlabs has key and
protected branches set up properly". Not made here.

The lead session tested the key (it reads `homer-reader`, GitLab refuses it on
`plato-reader`, a dry-run push to `main` is accepted), deleted the local pair
(the private half is in the secret alone), and set `MIRROR_GIT_URL` at
19:05:31Z. Mirror run 45245208945, started by this session's push 11 seconds
before the variable existed, had skipped; the lead reran it at 19:05:40Z: the
git job passed, `15 of 15 refs match the source after the push; 1 left out
(refs/heads/gh-pages)`. `mirror-check.mjs` from the Mac afterwards: 15 of 15
refs match, history 831 commits, whole. Not yet seen: a push to `main`
mirrored (it comes with #80's merge), a tag push, the weekly check, and the
release workflow. When the lead session makes the pair
and gives John the public half, John's two GitLab steps are: add it to the
project `johnhboyer/homer-reader` as a deploy key with write access, and tick
it under `main`'s "Allowed to push and merge" (force push left off). Then the
lead session sets the secret `MIRROR_GIT_SSH_KEY` and the variable
`MIRROR_GIT_URL`.

## Phase 2 record

**Parameters.** As in Plato: `scripts/site-params.mjs` checks `SITE_ORIGIN` (a
bare origin) and `SITE_BASE` (a path with a slash at each end), and both
`app/astro.config.mjs` and `scripts/check-links.mjs` read it. The link check
runs only as a script now, and under a base it fails a root-relative link
that leaves the base out. Homer already wrote `robots.txt` from the config,
and its `offline.html` names no file by path (`sw.js` finds it from its own
scope), so neither changed. `PUBLIC_GRAMMATA_LOOKUP` is read in place in
`LexiconPanel.svelte` (Homer's popup) and `LemmaPage.astro`, with the old
address as its default; `shared/__tests__/grammata-address.test.ts` holds
both to one form (put back to a fixed string, one fails it).

How it was checked: built with only the live data address set, the app is
10,050 of 10,050 files byte for byte the phase 1 build, which matched the
snapshot. Built with `SITE_BASE=/mirror/ SITE_ORIGIN=https://mirror.example.org`,
the link check at that base finds 0 broken of 335,540 links, and the
canonical link, the card image, `robots.txt`, and the sitemap name the new
origin and base.

**The bundle.** `scripts/make-bundle.mjs` is Plato's with Homer's gates, the
ones `deploy:cloudflare` and `build:public` run: `homer_pipeline.preflight`
over the data (which covers the public-domain and Creative Commons lists, so
the Kosmos text's attribution), and the shared LSJ and Cunliffe coverage
checks (run with `BUILD_DIR` at a scratch folder whose `dist` is the data);
then Plato's lemma-page check and JSON check. A Python gate passes only on
exit 0 with its own success line. The real run: `ok …: 10048 files,
347474436 bytes, packed to 58810853; left out CNAME; 5 gates passed on 5262
data files (preflight, shared LSJ coverage, shared Cunliffe coverage, lemma
pages, JSON); unpacked and read back against SHA256SUMS`. One lemma file
taken away: refused (`lemma pages: 1 slug has no file, first: menis`). One
book file cut short: refused by preflight and by the JSON check. The two
real-gate tests skip by name where the pipeline's Python is missing (CI's
`scripts` job); the `site` job runs the real gates.

**No outside calls (test 3).** `scripts/check-no-outside-calls.mjs` is
Plato's method with Homer's eight visits: `iliad/book/1/` (2,000 Greek and
2,000 English letters at least), the word popup (headword, gloss, parse,
then the Cunliffe tab, which must get its record from the site), a search
for μῆνιν (a hit linking to a page of this build), `lemma/menis/`, the
Trojan Plain plate (drawn as SVG from `data/plates/`), the map explorer
(Leaflet), the recitation player (the audio setting on, play pressed), and
the book again under the service worker. The Cunliffe entry is the site's
data, but Grammata's script draws it, so under the check (which refuses even
allowed hosts) the tab ends on "The dictionary could not be loaded."; the
visit requires the site's record to arrive first. One expected 404:
`data/search-shards/index.json`, which search asks for and no Homer build
makes (live answers 404 too). Results: `ok app/dist at /: 8 of 8 visits, 128
requests to the site (0 not found, 4 expected), 3 outside hosts asked for,
all allowed (grammata.pages.dev x2, cawm.lib.uiowa.edu x8, archive.org x1);
control seen`, and at `/mirror/` the same. A planted Google stylesheet link
and the Cunliffe shard taken away each turned it red, by name. Its 16
browser fixtures pass here.

**Two hosts beyond decision 4, ruled by John.** The first run found
`cawm.lib.uiowa.edu` (the map explorer's base tiles, `LandmarkMap.svelte`),
and a scan of the source found `archive.org` (the recitation MP3s, named in
`data/audio.json`, fetched only on play), which the added audio visit then
saw. John, 2026-11-23: "allow both". Both are on the script's default list.

**The restore drill.** From a bundle made on the Mac: unpacked and
`shasum -c` clean in 7 seconds; served by Python's test server,
`check-served.mjs` read all 10,047 files with their bytes and failed only on
that server's missing 404 page. Logged in `RESTORE.md`.

**Review.** Codex (GPT-6.1-Sol, medium; the session log shows both) read
phase 2 statically and found four things. (1) An emptied
`data/cunliffe-t8/<letter>.json` passed every bundle gate and the popup
visit, which took any 200: the bundle now runs a sixth gate, "Cunliffe
records" (every key of the shared Cunliffe, 7,550 today, has a record in the
T8 shard the reader fetches; emptying `m.json` gives `366 Cunliffe keys have
no record, first: ma/`), and the visit requires the served shard to hold
records. (2) The two dictionary checks print their success line and exit 0
when they examined no key (empty analyses): their gates now also require
`checked N referenced keys` with N above 0. (3) The audio visit took any
source, a `data:` URL among them: it now requires a recording
`data/audio.json` names and a request the browser made for it; the hand
break of this fix first failed for the wrong reason (the visit did not take
`dist`), which was fixed. (4) A doc command in `ARCHITECTURE.md` named the
wrong manifest folder; corrected and run. The new unit tests failed before
each fix; both visit breaks were run on the real build and each failed by
name. It found nothing in the parameters, the Grammata address, the
Dockerfile, Caddy, or the workflows. A second read, of the fixes, closed (2) and
(4) and found the two visits still loose: the Cunliffe step took a shard of
other words' records, and the audio step took any named recording. The
Cunliffe step now requires a record whose headword is the popup card's own
(a shard of one unrelated record fails: `holds no record for μῆνις`); the
audio step finds the recording `data/audio.json` names for the line the
pressed button stands on, and requires both the player's source and the
browser's request to be that one. Known and left from that read: the
dictionary gates pass if any key at all was checked, so a partial loss of
analyses would pass them (preflight does not require token coverage); the
original finding was the zero-key case.

**Known and left.** As in Aristotle and Plato: saved searches keep whole
paths, base included, in the browser's storage, so a saved search does not
follow a site to another base. A full `pytest` after a build rewrites both
works' `vocab.json` in `build/dist` (two tests in `test_apparatus_vocab.py`
run the vocabulary stage on the real build); a build after it puts them
back. The heavy `shared` corpus tests were not rerun on the Mac after a
crash (John: the CPU was overloaded); CI runs the suite.

## Phase 1 record

**Only the Iliad has a line file.** Homer has two works. The Iliad's Greek
is Allen's 1931 text from the TLG (`work.greek_source_kind: tlg`); the
Odyssey's is the Perseus TEI vendored at
`sources/perseus/tlg0012.tlg002.perseus-grc2.xml` (Murray's Loeb Greek, 1919,
under CC BY-SA), which the build already read without Diogenes. So
`corpus/greek/` holds one file, `Iliad.tsv`: 15,707 rows (15,683 numbered
lines and 24 title lines), 1,454,387 bytes. `extract` skips the Odyssey.

**The export ran.** No export was on disk. Diogenes 4.7.2
(`xml-export.pl -c tlg -n 0012 -y`) with `HOME` set and `TLG_DIR` at the
iCloud TLG folder (`~/Documents/CLAUDE CODE ARISTOTLE PROJECT/TLG Files/TLG`)
wrote the author's three works in a few seconds, exit 0. The "exit 25" this
repo's CLAUDE.md recorded was the missing `HOME` (Aristotle's phase 1 found
the same); `extract` sets it.

**The format, and where Homer differs from Aristotle and Plato.** One row
per `<l>` in a book: `book`, `n`, `sigla`, `text`. Allen's text carries
Alexandrian critical signs in the margin (`<seg rend="Marginalia">`: the
obelos, diplē, diplē periestigmenē, asteriskos, antisigma, alone or run
together, and the words "corr." and "ras."), 2,811 lines in all. Stage 1
keeps each line's signs on its `sigla` field and brackets a line only for
the obelos (John's ruling). A flattened line would have lost them, so the
file gives them a column of their own. The rest stays as the export has it,
and stage 1 does the reading as before: the bullet (TLG's `%11`, printed at
the head of Il. 8.538-540 and 13.298) stays in the text and stage 1 moves it
to the signs; `605*` stays as printed and stage 1 makes it 605; the text is
not NFC in the file (stage 1 applies NFC, as it always did); the four Book 8
lines Allen does not print are supplied in stage 1's code, not in the file.
The XML reader is shared: `greek_lines.flatten_line` is the walk stage 1
always used, now called by both `rows_from_xml` and stage 1.

`rows_from_xml` raises on shapes the old reader passed over without a word
and the export does not have: a book inside a book, a book number twice (the
old code kept the first), a line with no number (the old code counted it
under "(none)" and dropped it).

**The guard.** `greek_lines.forbidden` reads every line of the file: the
heading lines, each book and line number (`[1-9][0-9]?`; `[1-9][0-9]*\*?` or
`t`), each margin, and each line of text. A character of the text is Greek by
its Unicode name, or one of five marks (space, apostrophe, comma, full stop,
bullet). The margin holds only the seven signs and the two words. Markup
characters (`<`, `>`, `&#`, `&name`) and control characters fail anywhere.
There is no named exception.

**How it was proved.** (1) The spine stage 1 makes is byte for byte the
same three ways: the old code on the export's XML, the new code on the line
file, and the new code on the XML (2,075,799 bytes: 24 books, 15,687 lines,
2,815 with sigla, 528 bracketed, 24 headings, one `605*`). A test pins that
spine's size and sha256, so a change to the file or to stage 1 that moves it
fails. (2) 24 hand-made breaks of the guard, `rows_from_xml`, stage 1,
`extract`, and the export scan each fail a test. (3) Pipeline tests: 1,234
passed, 1 xfailed, with a build present (1,212 passed and 14 skipped before
one was built). Script tests 48 of 48.

**Test 2, the laptop build.** With `build/export` moved out of the tree and
`TLG_DIR` unset, `PUBLIC_DATA_ROOT=https://homer-data.johnhboyer.com npm run
build:public` ran to the end in about 9 minutes (both works, 4,687 pages, 0
broken of 335,540 links and 148,347 anchors, preflight and the shared LSJ and
Cunliffe checks passed). Against `~/Developer/reader-snapshots/2026-11-20/homer/`:

- `node scripts/compare-snapshot.mjs --sums=<snapshot>/SHA256SUMS --prefix=data/
  --build=app/dist/data --live-only=docs/portability/homer-live-only-2026-11-20.list`:
  `5262 of 5262 build files are byte for byte what the snapshot holds; 1
  live-only file allowed`. The live-only file is the bucket's key record.
- **Live moved after the snapshot.** DEPLOY-STATUS.md records a deploy on
  2026-11-23 from main `24cee78df` (PRs #75 and #76): app files only, no data
  uploaded. So the snapshot's `data/` is still live and is compared as above,
  but its `app/` is one deploy old. The pages were compared by building the
  app at `9e327f885`, the commit before those two PRs, over this branch's
  data (`git archive` into a scratch folder, `PUBLIC_SHOW_PRIVATE=0
  PUBLIC_DATA_ROOT=https://homer-data.johnhboyer.com npm run build`):
  `4725 of 4787 build files are byte for byte what the snapshot holds; 55
  pages and 7 renamed bundles equal once 67 names are swapped (Svelte classes
  checked against 9 component paths); 0 differ, 0 only in the build, 0 only
  in the snapshot`. The swaps are the ones Aristotle's record explains: Svelte
  hashes a shared component's folder path into its class, so a build in
  another folder renames 4 classes, the 7 bundles that hold them, and the 56
  island ids those pages carry. (Homer's snapshot has no `_redirects`.)
- A byte added to one data file, and a word changed in one page, each turned
  the comparison red; put back, it was green.

**A portability bug CI found.** The first `site` run (45222308852) stopped at
preflight: `speeches.json` was not copied. `build-public.mjs` named the
apparatus file and the data folder by the manifest's file name (`Iliad`),
while they are `iliad`; the Mac's case-blind disk hid it. It now uses the
lower-case id.

**Review.** Codex (GPT-6.1-Sol, medium; the session log shows both) read the
change statically. Fixed, each with a test that failed first: an empty book
(the old reader gave it a segment; the line file had no row for it); a book
number `01` or in Arabic-Indic digits (book 1 to the old reader's `int()`,
another book to the line file); a tab in a heading line; namespace-prefixed
export lines (`<tei:l n="1">`) and tracked symlinks (git stores the target
string) escaping the export scan; and `build:public` cleaning the last build
before the inputs check. Answered: beta code in the `# edition:` line passes
`forbidden`, since the edition line is free text, and the corpus test pins
it to the manifest's words; and U+00B7 or a decomposed accent fails the guard
though NFC would map it, which is the intent (the file holds the export's
characters, and a new one is for a person to look at). It found no way to
smuggle beta code or markup through the text or margin columns, and no
outside input the CI job lacks. A second read, of those fixes, found the
export scan still missed upper-case and spaced tags and prefixes with a
character outside `\w`, and read the working tree, so a tracked file
deleted from it went unread. The scan now reads every blob from git's
index (`git cat-file --batch`; a symlink as its stored target), and its
pattern takes any case, a space after `<`, and any prefix; tests failed
first. Out of its reach still, and said in the test: compressed or encoded
copies, submodules, and files git does not track. `stage1_greek.run`, the sibling readers'
Bekker and Stephanus path that no Homer work uses, still reads an export
already on disk; it never runs Diogenes.

**The two outside inputs.** `greek-analyses.txt` and `grc.lsj.xml` in this
Mac's Diogenes 4.7.2 are byte for byte the files Aristotle pinned, so
`inputs.py` is Aristotle's with its names changed.

**What is the same as Plato's and was not re-proved here.**
`scripts/compare-snapshot.mjs` and `scripts/verify-snapshot.mjs` are copied
from plato-reader's `main` (one comment changed), with their tests;
`extract.write_all` and its seven tests are Aristotle's, run here against
made-up works W1 to W5 since Homer has one TLG work.

## The licence (ruled by John, 2026-11-23)

The GitHub repo is public with no licence. For Plato John ruled "Same as
Aristotle" (MIT for code in `LICENSE`, CC0 1.0 on `corpus/greek/`, other
sources under their own terms in `sources/INVENTORY.md`). Homer's sources are
not all as open, so a Homer licence section would have to name, apart from
the MIT code and the CC0 Greek:

- **The Kosmos Society revision of Butler, CC BY-NC-ND 3.0** (`sources/kosmos/`,
  shown verbatim in the reader, and in the built data as
  `overlays`). NonCommercial and NoDerivatives: the licence cannot be MIT or
  CC0, and its files must keep their own notice.
- **Perseus TEI, CC BY-SA 4.0** (the encoding; the texts are public domain):
  the Odyssey's Greek, Murray's English, the Perseus Butler files kept for
  Iliad line markers, and the LSJ the site's lexicon is built from. Data built
  from them keeps CC BY-SA 4.0 (decision 3).
- **DICES speech data, CC BY 4.0** (`sources/dices/`).
- **OpenStreetMap river courses, ODbL 1.0** (`sources/openstreetmap/`):
  attribution and share-alike on derived data.
- **Copernicus DEM, an attribution licence** (`sources/copernicus-dem/`).
- Public domain, named for completeness: Butler's own text (Gutenberg and
  Wikisource), Pope (Gutenberg), Natural Earth, the terrain tiles, Cunliffe
  (via a MIT-licensed Perseus repo), Autenrieth.
- **John's own apparatus** (scenes, places, plates, notes): CC BY 4.0 under
  decision 3, if he wants the same here.

Ruled (John, 2026-11-23, "what you recommend"): MIT for the code in
`LICENSE`; CC0 1.0 on `corpus/greek/`, now ("CC0 now", after being told that
Allen's 1931 text enters the US public domain on 1 January 2027 under the
95-year rule, and that a critical edition of an ancient text holds thin
copyright at most; asked again by the lead session, John answered "Now" at
13:04); CC BY 4.0 on his own apparatus; every source on its own
terms. The table is at the head of `sources/INVENTORY.md`. (Much of the
apparatus is AI-drafted, and US law gives no copyright to work without human
authorship; CC BY on those parts does no harm and may not bind.)

The Kosmos text in public releases, ruled A the same day: the release ships
the bundle as built, the text in it as the live site serves it, and the
licence table names its terms. Zenodo and the Internet Archive get no copy
until John says (a Zenodo record cannot be withdrawn).

## Decision 10 for Homer (ruled A by John, 2026-11-23: "keep em")

Two tracked fixtures are in the Diogenes export's markup. Both are pinned by
size and sha256 in `pipeline/tests/test_corpus_greek.py`, so the guard passes
today and fails if either changes; John's ruling decides whether they stay.

- `pipeline/tests/fixtures/stephanus/euthyphro_p2_3.xml` (9,369 bytes,
  77 lines): Plato's fixture, copied here. John ruled A (keep, pinned) for
  the same file in plato-reader on 2026-11-21, and its Greek is now public in
  plato-reader's `corpus/greek/Euthyphro.tsv`.
- `pipeline/tests/fixtures/stage1_tlg/tiny_tlg_iliad.xml` (1,601 bytes,
  9 lines): called synthetic, but its lines are Il. 1.1-5 and Od. 1.1-4 in
  the export's markup, with made-up signs. The Iliad's lines are the text
  `corpus/greek/Iliad.tsv` now publishes under decision 1.

John chose A on 2026-11-23. The options were: **A, keep both, pinned** (as now); B, replace them with made-up
Greek (the old files stay in history either way; rewriting public history is
John's call). Recommendation: A, for the reason John gave for Plato: the
Greek is public already, and what the files add is the export's TEI markup,
not the TLG's own beta code. The tiny file is under the 30-line limit and
would pass unpinned; it is pinned so a change to it is seen.

The two Perseus Greek files are pinned the same way, as not exports: they
hold 15,687 and 12,107 `<l n=…>` lines, and the pin keeps an export from
passing under their names.
