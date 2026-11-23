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

Phase 1 is in a PR (below). Phases 2 and 3 are not started. Nothing is
merged or deployed. Open for John: the licence (below) and decision 10 for
Homer's two fixtures (below).

| Phase 1 step | State |
|---|---|
| `extract` writes `corpus/greek/`; the build reads only those | Done: one file, `Iliad.tsv`, 15,707 rows, 1,454,387 bytes. Stage 1 runs no program |
| Guard on the committed file, failing cases first | Done: every text character Greek or one of five marks; every margin one of the edition's seven signs or two words; no named exception. 24 hand breaks each fail a test |
| The line file gives stage 1 the export's spine | Done: byte for byte the same three ways (old code on the XML, new code on the line file, new code on the XML), 2,075,799 bytes; 24 books, 15,687 lines, 2,815 with sigla, 528 bracketed |
| Morpheus table and LSJ pinned by checksum, folder from the environment | Done: the same two files as Aristotle's pins, byte for byte (sha256 `dfca7ef1…`, `af72685a…`); `inputs check` runs first in `build:public`; `inputs fetch` for a machine without Diogenes |
| Machine paths out of the public build | Nothing to take out: the manifests name only Diogenes.app, as the local default for `extract` and the two inputs, and `../TLG Files/TLG` as `TLG_DIR`'s default |
| CI runs the full build and uploads it | CI_PENDING |
| Same output as live (test 2) | Laptop build done: 5,262 of 5,262 data files byte for byte the snapshot's; the app at `9e327f885` 4,787 of 4,787 files equal (4,725 byte for byte, 62 once 67 folder names are swapped). Linux build: CI_TEST2 |
| Review by another model family | Done: Codex (GPT-6.1-Sol, medium), two reads. First: seven findings, five fixed with tests first, two answered. Second, of the fixes: two gaps left in the export scan, both fixed with tests first |

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

## The licence (open: John's)

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

Question for John: the same as Aristotle and Plato (MIT code, CC0 on
`corpus/greek/`, everything else under its own terms, listed), with the
Kosmos text and the OSM and Perseus derivatives named as exceptions? That is
the recommendation. No licence file is added until he says.

## Decision 10 for Homer (open: John's)

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

Options: **A, keep both, pinned** (as now); B, replace them with made-up
Greek (the old files stay in history either way; rewriting public history is
John's call). Recommendation: A, for the reason John gave for Plato: the
Greek is public already, and what the files add is the export's TEI markup,
not the TLG's own beta code. The tiny file is under the 30-line limit and
would pass unpinned; it is pinned so a change to it is seen.

The two Perseus Greek files are pinned the same way, as not exports: they
hold 15,687 and 12,107 `<l n=…>` lines, and the pin keeps an export from
passing under their names.
