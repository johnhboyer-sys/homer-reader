# Sources inventory — provenance and licenses

All fetched 2026-07-17. US copyright rules apply (PD = pre-1931 as of 2026).
The TLG corpus is licensed/local and is **never** vendored here (see CLAUDE.md).

## perseus/ — PerseusDL/canonical-greekLit @ master (CC-BY-SA 4.0 encoding)

| File | Content | Underlying edition | US status |
|---|---|---|---|
| tlg0012.tlg001.perseus-grc2.xml | Iliad, Greek | Monro–Allen OCT, Editio Tertia, 1908–1920 | PD |
| tlg0012.tlg002.perseus-grc2.xml | Odyssey, Greek | Murray Loeb Greek text, 1919 (per sourceDesc) | PD |
| tlg0012.tlg001.perseus-eng3.xml | Iliad, English | A. T. Murray (Loeb), 1924–25 | PD |
| tlg0012.tlg002.perseus-eng3.xml | Odyssey, English | A. T. Murray (Loeb), 1919 | PD |
| tlg0012.tlg001.perseus-eng4.xml | Iliad, English | Samuel Butler, 1898 ("Revised edition") | PD |
| tlg0012.tlg002.perseus-eng4.xml | Odyssey, English | Samuel Butler, 1900 | PD |

Note: catalog UI labels the English editions eng1/eng2; the canonical filenames
are eng3/eng4 (verified via __cts__.xml). Attribute Perseus on the About page.

## dices/ — cwf2/dices @ main (code MIT; data CC-BY 4.0 via Borealis doi:10.5683/SP3/N8LS2Y)

- speechdb.json — Django fixture dump, 4689 speeches, both epics, speaker/
  addressee/line-range/cluster/`level` (nesting depth). v1.1 per metadata row.

## cunliffe/ — scaife-viewer/atlas-data-prep @ main (repo license MIT, Perseus Digital Library 2024)

- cunliffe-1-lex.jsonl — R. J. Cunliffe, A Lexicon of the Homeric Dialect
  (1924, PD-US). 9,825 entries; citations carry CTS URNs onto perseus-grc2.
- cunliffe-2-hompers.jsonl — Cunliffe, Homeric Proper and Place Names (1931;
  US PD from 2027). **Included at launch by John's explicit decision,
  2026-07-17** ("I'm not worried about cunliffe being half a year out").
  1,591 entries.

## Still to vendor (later phases)

- Pope (Iliad 1715–20, Odyssey 1725–26) — Project Gutenberg plaintext/HTML (PD).
- Autenrieth, A Homeric Dictionary (Eng. tr. 1880s, PD) — no clean structured
  source exists; legacy Perseus Hopper scrape is a time-boxed Phase 2 attempt,
  else fast-follow (see docs/PHASE0-FINDINGS.md (c)/(d)).
- CAWM map tiles are hotlinked (CC BY 4.0), not vendored.
