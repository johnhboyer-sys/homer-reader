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

## pope/ — Project Gutenberg (PD)

- pope-iliad.txt — PG #6130, "The Iliad", Translator: Alexander Pope (1715–20).
- pope-odyssey.txt — PG #3160, "The Odyssey", Translator: Alexander Pope
  (1725–26; Odyssey co-authored with Broome/Fenton — translation note must
  disclose, per PROMPT.md).

## naturalearth/ — Natural Earth 1:50m land polygons (public domain)

- mediterranean-coastline.json — Mediterranean-basin coastline, clipped +
  simplified from `ne_50m_land` for the context-panel scene-maps
  (`shared/lib/scenemap.ts`). Fetched 2026-07-18 from
  `nvkelso/natural-earth-vector` (Natural Earth's own GitHub mirror). Public
  domain per Natural Earth's terms of use — not a US-copyright judgment call.
  See `sources/naturalearth/README.md` for full provenance + the derivation
  pipeline (`scripts/prep-naturalearth-coastline.py`).

## copernicus-dem/ — coastlines and islands of the two Troad plates (attribution licence)

- trojan-plain-coastline.json, trojan-plain-sea.json, troad-coastline.json —
  contoured from the **Water Body Mask** of the Copernicus DEM GLO-30 (30 m),
  fetched 2026-07-28 from the AWS Open Data registry. Licence: free worldwide
  use, reproduction, modification and distribution **conditional on the
  attribution** "© DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH
  2014–2018 provided under COPERNICUS by the European Union and ESA" —
  **not** share-alike. See `sources/copernicus-dem/README.md` for full
  provenance and the derivation (`scripts/prep-troad-basemap.py`).

## terrain-tiles/ — relief contours of the two Troad plates (public domain)

- troad-contours.json, trojan-plain-contours.json — contour lines at 200 m
  (Troad) and 20/50 m (plain), traced from the **Terrain Tiles** terrarium
  DEM on AWS Open Data (Tilezen `elevation-tiles-prod`), fetched 2026-07-28.
  Over Turkey the underlying data is **SRTM**, a US-government work with no
  domestic copyright asserted; the only obligation is the credit line
  **"SRTM data courtesy of the U.S. Geological Survey"**, which is carried in
  the JSON and on every plate layer derived from it. Not share-alike. See
  `sources/terrain-tiles/README.md` for provenance, the zoom/interval
  reasoning, the elevation sanity check against Kaz Dağı, Hisarlık and sea
  level, and the derivation (`scripts/prep-terrain-contours.py`).

## openstreetmap/ — river courses of the two Troad plates (⚠ ODbL 1.0)

- trojan-plain-rivers.json, troad-rivers.json — Scamander, Simoeis, Granicus,
  Aesepus, Satnioeis, from OSM `waterway` ways via Overpass, 2026-07-28.
  **ODbL 1.0: attribution required, and share-alike applies to derivative
  databases — which these files and the plates' river layers are.** No
  public-domain substitute exists (measured: Natural Earth 1:10m has no
  watercourse inside the Troad sheet). Accepting the obligation is John's
  call; `sources/openstreetmap/README.md` states it in full and gives the
  alternative.

## Still to vendor (later phases)

- Autenrieth, A Homeric Dictionary (Eng. tr. 1880s, PD) — no clean structured
  source exists; legacy Perseus Hopper scrape is a time-boxed Phase 2 attempt,
  else fast-follow (see docs/PHASE0-FINDINGS.md (c)/(d)).
- CAWM map tiles are hotlinked (CC BY 4.0), not vendored.
