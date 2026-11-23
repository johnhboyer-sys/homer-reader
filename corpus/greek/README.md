# corpus/greek

The Greek text of the Iliad the site is built from: one printed line of the
edition per row. The build reads this file for the Iliad's Greek; the
Odyssey's Greek is the Perseus file in `sources/perseus/`. This folder holds
the line files and this page, and nothing more.

## Format

UTF-8, tab-separated, one row per printed line, in reading order.

```
# work: Iliad
# edition: Allen, T.W., Homeri Ilias (Oxford: Clarendon Press, 1931), …
# columns: book	n	sigla	text
1	t
1	1		Μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος
1	2	>	οὐλομένην, ἣ μυρί' Ἀχαιοῖς ἄλγε' ἔθηκε,
```

- `book` is the book's number; `n` is the line's number as printed, `t` for
  a book's title line, and `605*` once, in Book 18, as the source marks it.
- `sigla` holds the critical signs the edition prints in the line's margin
  (obelos, diplē, diplē periestigmenē, asteriskos, antisigma), with the
  words `corr.` and `ras.` where they stand, or nothing.
- The text is the line as the edition prints it, with runs of white space
  made one space and nothing else changed. A bullet the edition prints at the
  head of four lines stays in the text.
- `pipeline/homer_pipeline/stage1_tlg_iliad.py` reads the file: only the
  obelos brackets a line, the bullet joins the line's signs, and the four
  lines of Book 8 that Allen does not print are supplied there, bracketed.

## Edition

The second line names the edition, taken from the work's manifest
(`manifests/Iliad.yaml`, `work.greek_edition`).

## Licence

These files are released under CC0 1.0 Universal
(https://creativecommons.org/publicdomain/zero/1.0/). The texts are
ancient; the files add no claim of their own.

## Making the files

`python -m homer_pipeline.extract --all` (in `pipeline/`) writes them from the
digital source texts, on a machine that holds those. The source's own files
are never committed to this repository.
`pipeline/tests/test_corpus_greek.py` checks every file here on each test run:
every letter of every line must be Greek, and every margin sign one of the
edition's.
