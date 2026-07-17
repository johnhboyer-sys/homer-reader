# Resuming the Autenrieth acquisition

State as of 2026-07-17: **119 of 1,793** letter-alpha entries scraped
(`entries-partial.jsonl`), full alpha id list enumerated
(`alpha-entry-ids.txt`, 1,793 keys), letters β–ω **not yet enumerated**.
Stopped because `www.perseus.tufts.edu` started returning `HTTP 429` on nearly
every request after ~150 total requests in this session.

## Recommended next attempt, in priority order

### 1. Retry the bulk download (Route 1) — try this FIRST, it's a 10-minute win if it works

```
https://www.perseus.tufts.edu/hopper/opensource/downloads/texts/hopper-texts-GreekRoman.tar.gz
```

~125 MB, CC-BY-SA 3.0, contains all Perseus Greek/Roman-collection XML
including (almost certainly) the Autenrieth SGML/XML source. In this sandbox
the transfer truncated at ~1 MB every time (curl error 18, then error 33 on
`-C -` resume — server doesn't support range requests, so resume doesn't work
either). This smells like a sandbox/network egress cap on this session, not a
server-side block. **Retry from a different/unconstrained network first**
before falling back to more scraping. If it downloads fully:
`tar tzf hopper-texts-GreekRoman.tar.gz | grep -i auten` to locate the file,
extract just that one file, and this whole scrape apparatus becomes
unnecessary.

### 2. If download still fails: resume the scrape, but slow down hard

The 429s came from request *volume*, not from any header/UA issue (headers
worked fine for ~150 requests). Next run should:

- Use a **2–3 second** delay between requests, not 0.4s (the brief's 0.4s was
  too aggressive for this legacy server — revise before re-running).
- Possibly split the run across a longer wall-clock window (e.g. run in the
  background over an hour rather than in one dense burst).
- Re-run `scratchpad`'s `scrape_autenrieth.py`-style script (recreate it; it
  was not committed anywhere permanent — see "Script" below) — it already
  supports resume: it skips any `key` already present in
  `entries-partial.jsonl`, so just re-point it at the existing
  `sources/autenrieth/entries-partial.jsonl` (copy back into whatever
  scratchpad the next agent uses) and it will continue from entry 120 of 1,793
  for letter alpha.
- After alpha completes (1,793 entries), the SAME enumeration technique must be
  repeated for the other 23 letters: fetch
  `.../text?doc=Perseus:text:1999.04.0073:alphabetic+letter=<L>` for L in
  b,g,d,e,z,h,q,i,k,l,m,n,c,o,p,r,s,t,u,f,x,y,w (Beta Code single-letter
  codes), extract the `entry+group%3D[0-9]+` link count from each to find its
  group count, then repeat the group-page-scrape enumeration per letter. Total
  dictionary size is likely 8,000–10,000 entries (alpha alone is 1,793 and
  the navbar width suggested alpha is ~17% of the whole text).

### Script (recreate from this description if not preserved)

Two-phase Python script using `urllib` only (stdlib, no deps):

- **Phase A (enumerate)**: for each `entry+group=N` (N = 1..count-for-letter),
  fetch `text?doc=Perseus:text:1999.04.0073:alphabetic+letter=<L>:entry+group=<N>`
  with headers `User-Agent: Mozilla/5.0 ...` and
  `Referer: http://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.04.0073`
  (**both headers are required** — bare curl gets a Varnish 405). Regex out
  `entry%3D([^&"']+)` and URL-decode; drop any containing `'` or `);` (JS
  noise). Append to a per-letter id file.
- **Phase B (fetch)**: for each id, fetch
  `xmlchunk?doc=Perseus%3Atext%3A1999.04.0073%3Aentry%3D<urlencoded-key>` (same
  headers). Each response is one clean `<TEI.2><text><body><div1 ...><entryFree
  key="...">...` fragment — append as one JSON line
  `{"key":..., "key_attr":..., "headword":..., "xml":...}` to the JSONL output.
  Skip ids already present in the output file (resume support).

### Downstream processing (not yet done, for whoever finishes acquisition)

The `xml` field per line is a fragment, not a full document — no shared
`teiHeader`. To build the final `autenrieth.xml`/`autenrieth.jsonl` for the
pipeline: parse each `entryFree`, keep `orth` (headword, Beta-Code/Greek), the
full entry body (retains `foreign lang="greek"`, `gloss`, `bibl n="Hom. ..."`
citation spans — these `bibl` citations are directly usable for
cross-linking to the vulgate line numbering, same pattern as Cunliffe's CTS
URNs already vendored in `sources/cunliffe/`).
