# Autenrieth, A Homeric Dictionary — provenance (partial acquisition)

Fetched 2026-07-17. Route taken: **Route 2 (scrape)** — Route 1 (clean download)
was attempted first and failed; see "Route 1 attempts" below.

## Work

Georg Autenrieth, *A Homeric Dictionary for Schools and Colleges* (tr. from the
German, New York: Harper and Brothers, 1891). **US PD** (pre-1931).

## Source

Legacy Perseus 4.0 "Hopper" at `www.perseus.tufts.edu`, text id
`Perseus:text:1999.04.0073`. This is the only structured source found — the text
does **not** exist in any modern CTS/GitHub Perseus repo (canonical-pdlrefwk,
PerseusDL/lexica, scaife-viewer/atlas-data-prep all checked, zero hits — this
matches the prior Phase 0 finding in `docs/PHASE0-FINDINGS.md` section (c)).

Encoding: NEH-funded Perseus TEI (`TEI.2`), CC-BY-SA family per Perseus's usual
terms for its encoding; the underlying 1891 work is PD. Perseus's text-page
footer states: "The National Endowment for the Humanities provided support for
entering this text... converted to electronic form by professional data entry
and has been proofread to a **medium** level of accuracy" — flag this
proofreading-quality caveat downstream (do not treat as OCR-clean).

## Route 1 attempts (download) — all failed or dead-ended

- `PerseusDL/lexica` GitHub repo (`CTS_XML_TEI/perseus/pdllex/`): contains only
  `grc/lsj` (Liddell-Scott-Jones) and `lat/ls` (Lewis-Short). No Autenrieth.
- `PerseusDL/dynamic-lexicon`: unrelated project (auto-generated bilingual
  lexicon from aligned parallel texts + treebanks), not Autenrieth's dictionary.
- `PerseusDL/canonical-pdlrefwk`: not checked via GitHub code search in this run
  (search requires auth); prior Phase 0 pass already recorded zero hits here.
- UChicago "Perseus under PhiloLogic" mirror (`perseus.uchicago.edu`,
  `artfl-project.uchicago.edu`) hosts a live PhiloLogic search database built
  from the same Autenrieth source (mentions an "Autenrieth XML Header" in its
  legacy page copy) but exposes no bulk download — search/browse only, same
  scrape-only posture as Tufts.
- Perseus Open Source download page
  (`https://www.perseus.tufts.edu/hopper/opensource/download`) **does** offer a
  "Greek and Roman texts" bundle (`hopper-texts-GreekRoman.tar.gz`, ~125 MB,
  CC-BY-SA 3.0) that should contain the Autenrieth SGML/XML source file
  alongside all other Perseus Greek/Roman texts. **This is the single most
  promising still-untried lead** — see RESUME.md. In this run the download
  consistently truncated after ~0.9–1.1 MB (curl error 18 "partial file", then
  error 33 "range not supported" on resume attempts) across three tries from
  this sandbox's network — looks like an environment-side transfer cap/timeout
  on this large binary, not a server refusal (HTTP 200, no Content-Length,
  chunked transfer). A run from an unconstrained network should be retried.

## Route 2 (scrape) — what worked

The Hopper's `xmlchunk` endpoint (e.g.
`http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.04.0073%3Aentry%3D<KEY>`)
returns a clean, small `TEI.2` XML fragment for exactly one entry (one
`entryFree`), given a Beta-Code-encoded entry `key`. Requires a browser
`User-Agent` and a `Referer` header pointing at the text's hopper page — bare
`curl` with no headers gets a Varnish 405.

Entry keys are **not** enumerable via `xmltoc` (returns an empty stub for this
text) or via any bulk index. They were recovered by scraping the HTML "browse"
page for each of the 36 `entry+group` pagination pages under
`alphabetic+letter=a` (`.../text?doc=...:alphabetic+letter=a:entry+group=N` for
N=1..36) and regex-extracting the `entry=<KEY>` links embedded in each page's
navbar. This enumerated **1,793 entry keys for letter alpha alone** — see
`alpha-entry-ids.txt`.

**Rate limiting:** after roughly 150 combined requests (36 enumeration fetches +
~120 entry fetches) at a 0.4s inter-request delay, `www.perseus.tufts.edu`
started returning `HTTP 429 Too Many Requests` on effectively every subsequent
request, non-recoverable within a few retries. The scrape was stopped at that
point rather than burn the time-box retrying into a wall.

## US copyright / license summary

- Underlying work (Autenrieth 1891 English tr.): **PD** in the US.
- Perseus's TEI encoding/markup: CC-BY-SA (Perseus's standard terms for Hopper
  texts) — attribute Perseus Digital Library, Tufts University, on the About
  page per site convention (matches the pattern already used for
  `sources/perseus/*` in this repo).
