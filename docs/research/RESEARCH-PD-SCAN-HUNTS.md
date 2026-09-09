# Research: four public-domain scan/publication hunts

Scope: four independent bibliographic hunts flagged as open items in
`RESEARCH-POEM-TOPOGRAPHY.md` and `RESEARCH-CITADEL.md`. Tools used: WebSearch,
WebFetch, and `curl`/`pdftotext` via Bash for sites that reject WebFetch's
default user agent or that expose useful machine APIs (archive.org's
search-inside and metadata APIs, the Wayback Machine's CDX API). No browser
MCP was used. Every image claim below was visually confirmed by fetching and
reading the actual page/leaf image, not inferred from OCR alone — flagged
where that was and wasn't possible.

**Headline result: Hunt 3 overturns a standing claim.** `RESEARCH-CITADEL.md`
§1.1 and §7 state Dörpfeld's Tafel I ("Karte der Ebene von Troja") is missing
from all three known archive.org copies. It is not missing. It is at
`trojaundilionerg02dorp`, leaf `n268`, one leaf before the already-documented
Tafel II (`n270`) — visually confirmed, full color, high resolution. See §3.

---

## 1. HUNT 1 — Mey 1926 and the "1928 Andrae plate"

**Question:** is Oscar Mey, *Das Schlachtfeld vor Troja: eine Untersuchung*
(Berlin/Leipzig: de Gruyter, 1926) scanned anywhere, and did Mey or Andrae
publish anything in 1928 that could carry the pen-and-ink Teichomachia
reconstruction described in `RESEARCH-POEM-TOPOGRAPHY.md` §9.3
(`BattlefieldH.jpg`, monogrammed/dated 1928, German caption crediting
"Prof. Walter Andrae")?

**Citation confirmed.** "Das Schlachtfeld vor Troja, eine Untersuchung. Von
Oscar Mey. Berlin and Leipzig: de Gruyter. 1926." — reviewed by A. Shewan,
*The Classical Review* 42, no. 1 (February 1928): 41.
[Cambridge Core abstract page](https://www.cambridge.org/core/journals/classical-review/article/abs/das-schlachtfeld-vor-troja-eine-untersuchung-von-oscar-mey-berlin-and-leipzig-de-gruyter-1926/3F99C97F6E48A6EF044C0BBA602EA177).
*authority:* reference. *verified how:* WebFetch of the Cambridge Core page,
which quotes the citation verbatim.

**No scan found — searched and came up empty:**
- Google Books, archive.org, HathiTrust: no item titled *Das Schlachtfeld vor
  Troja* or attributed to Oscar/Oskar Mey in any of the three catalogues
  (WebSearch across all three, plus a Google Books API query that hit a quota
  wall before returning results — noted as inconclusive, not a negative).
- K10plus/GVK (German union catalogue): WebSearch could not surface a direct
  catalogue record; the K10plus OPAC's search interface is JS-driven and not
  fetchable with WebSearch alone. **Not resolved — a human with an interactive
  K10plus session should retry.**
- No mention of the book at German digitised-collection sites reachable in
  this session (SBB Berlin, MDZ München were searched by WebSearch only, no
  hits).

**No 1928 Mey publication found.** German Wikipedia's Oskar Mey article
([de.wikipedia.org/wiki/Oskar_Mey](https://de.wikipedia.org/wiki/Oskar_Mey))
lists exactly two publications — a textile-engineering monograph and *Das
Schlachtfeld vor Troja* (1926) — and gives no second edition, *Ergänzung*, or
1928 title. Targeted WebSearches for "Mey 1928 Ergänzung/Nachtrag/zweite
Auflage" and for a Mey WorldCat record returned nothing. *authority:*
reference. *verified how:* WebFetch of the Wikipedia article; four
WebSearch passes with different phrasings, all negative.

**Andrae's own catalogued estate has no record of it — a genuine negative
result new to this lane.** The Staatliche Museen zu Berlin hold Andrae's
Nachlass finding aid (*Findbuch*) online:
[ZA_Findbuch_Nachlass_Walter_Andrae.pdf](https://www.smb.museum/fileadmin/website/Institute/Zentralarchiv/Bestaende/Dokumente/ZA_Findbuch_Nachlass_Walter_Andrae.pdf).
It is organized in six sections including "5. Zeichnungen" (drawings) and
covers 1903–1938 with individual dated entries (lectures, articles, drawings).
`pdftotext -layout` extraction (confirmed working — legible entries like
"SMB-ZA, IV/NL Andrae 001 Vorträge und wissenschaftlichen Arbeiten von 1908 -
1938") turned up **zero** hits for "Troja," "Troia," "Schlachtfeld," "Mey," or
"Teichomachie" anywhere in the ~1,200-line document. *authority:* reference
(a catalogued absence, not proof of non-existence — Nachlass finding aids are
not always complete, and a drawing made for someone else's publication might
never enter the artist's own estate catalogue). *verified how:* WebFetch of
the PDF (failed to extract text — binary), re-fetched as a raw download, and
run through `pdftotext -layout` locally; grep confirmed both that the
extraction worked (legible unrelated entries throughout) and that the four
search terms return no matches.

**The hosting site tried to trace `BattlefieldH.jpg` no longer shows it.**
Identified the likely source as Jenny Strauss Clay's "Homer's Trojan Theater"
project, University of Virginia IATH:
[homerstrojantheater.iath.virginia.edu](https://homerstrojantheater.iath.virginia.edu/).
WebFetch of the live site found no reference to a battlefield reconstruction
image, Andrae, or Mey — the current site is a different, narrower spatial
project (staging movement in the *Iliad*'s battle books), and may not be the
same "Clay's UVa site" as the one that hosted the 2006-vintage JPEG described
in `RESEARCH-POEM-TOPOGRAPHY.md` §9.3. A Wayback Machine CDX query for
`*BattlefieldH.jpg*` returned **zero snapshots at any host** — inconclusive
(the file may live at a URL/domain the wildcard didn't match, or may simply
never have been crawled), not proof it never existed. *authority:* reference.
*verified how:* WebFetch of the live IATH site; CDX API query
(`web.archive.org/cdx/search/cdx?url=*BattlefieldH.jpg*`) returned an empty
array.

**Verdict for Hunt 1:** No progress toward confirming a pre-1931 publication
for the Andrae drawing. If anything, the new negative (nothing in Andrae's own
finding aid) makes a 1928 *Mey* second publication less likely as the vehicle,
though it does not rule out an *Andrae*-side 1928 venue never searched under
Andrae's own name in combination with "Troja" phrased differently (e.g. as
part of a DAI *Jahresbericht* illustration, or a museum bulletin). **Do not
claim the plate is public domain. The publication remains unestablished.**

---

## 2. HUNT 2 — Brückner, *Archäologischer Anzeiger* 1912 and 1925

**Question:** do A. Brückner, "Das Schlachtfeld vor Troia," *Archäologischer
Anzeiger* 26 (1912): 616–33, and a second Brückner AA piece, 39 (1925):
230–48, exist as cited, and where can they be read?

### 2.1 The 1912 piece — CONFIRMED, found, read, verified line-by-line

The *Archäologischer Anzeiger* of this era is bound as the Beiblatt to the
*Jahrbuch des Kaiserlich Deutschen Archäologischen Instituts* (JdI). Working
out the year-to-volume correspondence (JdI Band *N* = year 1885+*N*, confirmed
against Heidelberg's own listing of "JdI (26.1911)" and "JdI (40.1925(1926))"),
JdI Band 27 = 1912.

**Found:** archive.org holds this exact volume, scanned complete —
[`jahrbuchdeskaise27kaisrich`](https://archive.org/details/jahrbuchdeskaise27kaisrich)
(842 leaves). Its full OCR text (`_djvu.txt`) contains, in context: "Zum
Schluß hielt Herr A. Brueckner folgenden Vortrag über das Schlachtfeld vor
Troja," immediately followed by the article text, running header
"Archäologische Gesellschaft zu Berlin. November-Sitzung 1912.," printed
page numbers **617–618** visible on the page image. The article includes its
own figure, captioned in the OCR as "Abb. I. Skizze des Schlachtfeldes vor
Troja" (a sketch map — an additional period image, not independently pinned
to a leaf number in this pass).

**Visually confirmed** — the page image at
`https://archive.org/download/jahrbuchdeskaise27kaisrich/page/n766_w1200.jpg`
shows printed pages 617/618 (mid-article, running head *Archäologische
Gesellschaft zu Berlin. November-Sitzung 1912*). The article's OPENING — "Zum
Schluß hielt Herr A. Brueckner folgenden Vortrag über das Schlachtfeld vor
Troja," printed p. 616 — is one leaf earlier, on **n765** (Grok verification,
2026-07-29: cite n765 for the opening, n766 for the 617–618 sample). Direct
reader link:
[archive.org/details/jahrbuchdeskaise27kaisrich](https://archive.org/details/jahrbuchdeskaise27kaisrich)
(use the `page/n765_w1600.jpg` / `n766_w1600.jpg` / `_w4000.jpg` image URLs
for higher resolution).

**Note on the volume-number discrepancy.** Archive.org's own metadata labels
this item "volume: 27," while the citation under test names "*Archäologischer
Anzeiger* 26." The content and year (1912) match exactly; the numbering
mismatch is most likely AA's Beiblatt volume count running one behind the
JdI Band count (a pattern also visible in the 1925 case below: AA 39 pairs
with JdI Band 40). Flagging this as an unresolved numbering-convention detail,
not a doubt about content identity.

**Licence.** Published 1912, pre-1931 → US public domain (95-year term from
publication under the standard pre-1978 bright line, same reasoning already
applied to Dörpfeld 1902 in `RESEARCH-CITADEL.md`). *authority:* licence.
*verified how:* publication date read directly off the page image (running
head "November-Sitzung 1912").

### 2.2 The 1925 piece — volume located, article NOT independently confirmed

By the same Band=year-1885 arithmetic, AA 39 (1925) pairs with **JdI Band 40**
(year 1925). This volume is **not** among the archive.org DAI/JdI holdings
searched in this session — archive.org's run of that series (searched via
`advancedsearch.php` for the exact German title) tops out at a combined
Band 38/39 item
([`jahrbuchdeskai3839kaisrich`](https://archive.org/details/jahrbuchdeskai3839kaisrich),
confirmed by its own OCR text to cover 1923–1924 only — no "Schlachtfeld vor
Troja" or "Brückner...Troja" match anywhere in its full text). Band 40 is
absent from that run entirely.

**Found instead at Heidelberg**, but access-blocked in this session. The
Universitätsbibliothek Heidelberg hosts JdI Band 40:
`digi.ub.uni-heidelberg.de/diglit/jdi1925`, DOI
[10.11588/diglit.44818](https://doi.org/10.11588/diglit.44818). Live access
(WebFetch and `curl`, including with a full browser User-Agent) returns
Heidelberg's **Anubis** bot-mitigation challenge page (a JavaScript
proof-of-work gate, HTTP 200 with challenge HTML, not a literal 403 as
earlier lanes described it — confirmed by inspecting the response body,
which embeds `anubis_challenge` JSON and the text "Making sure you're not a
bot!"). This blocks both direct viewing and the PDF-download endpoint.

**Worked around via the Wayback Machine**, which holds pre-Anubis snapshots.
A 2020 snapshot of the volume's table of contents
([cached copy](http://web.archive.org/web/20200213131536/https://digi.ub.uni-heidelberg.de/diglit/jdi1925))
confirms the volume's structure: JdI's own articles run to printed p. 223,
followed by a "Jahresbericht des Archäologischen Instituts für das Jahr 1924"
(roman I–IV) and then a chapter labelled "Archäologisches Institut des
deutschen Reiches" (roman I–XV, leaves 249–263 per its PDF-download range) —
this is where the AA Beiblatt's own table of contents and articles live,
under its own internal pagination. A later chapter, "Register," covers pp.
407–432 (leaves 265–277), confirming the AA content runs at least that far
and therefore comfortably contains pp. 230–248. **The outer Heidelberg TOC
does not itemise individual AA articles by author**, so Brückner's specific
piece was not independently pinned to a leaf number — a human who solves the
Anubis challenge (or has institutional access) can go directly to
`digi.ub.uni-heidelberg.de/diglit/jdi1925/0249` onward and locate it, or a
future automated pass could try the IIIF manifest at
`digi.ub.uni-heidelberg.de/diglit/iiif/jdi1925/manifest.json`, which was not
attempted in this session.

**Licence.** Published 1925, pre-1931 → US public domain, same reasoning as
2.1. *authority:* licence. **Not fully verified** — the volume's existence
and Heidelberg's hosting are confirmed; the specific article's presence at pp.
230–248 is inferred from the volume's overall page range, not read directly.

---

## 3. HUNT 3 — Dörpfeld, *Troja und Ilion* (1902), Tafel I

**This corrects a standing claim.** `RESEARCH-CITADEL.md` §1.1's plate table
lists Tafel I ("Karte der Ebene von Troja") as "not in these scans (§7)," and
§7 records "Tafel I ... not in these scans" as a known gap across all three
archive.org copies then known
(`trojaundilionerg01dorp`, `trojaundilionerg02dorp`, `trojaundilionerg00drpf`).

**Tafel I is present.** It is in `trojaundilionerg02dorp` (the same item
already used for Tafeln II–VIII), at leaf **`n268`** — one leaf before the
already-documented Tafel II at `n270` (leaf `n269` is a blank protective
interleaf, standard practice between foldout plates in bound volumes; this
also explains why a search for "Tafel I" text inside the volume, or a glance
one leaf past the Erläuterung text, would miss it).

**Visually confirmed** by downloading and reading the actual image:
`https://archive.org/download/trojaundilionerg02dorp/page/n268_w1600.jpg`
(full-res: `..._w4000.jpg`, 3489×3501 px — comparable resolution to the
already-used Tafel V). It is a full-colour topographic map, titled in its own
cartouche "KARTE DER EBENE VON TROJA / NACH DER AUFNAHME VON T. SPRATT /
VERVOLLSTAENDIGT 1894," headed "W. DÖRPFELD, TROJA und ILION." / "TAFEL I."
top corners — matching Dörpfeld's own Erläuterung description word for word
(source: J. Forchhammer's published redrawing of Graves & Spratt's 1840
survey of the Skamander plain; colour-coded river channels — dark blue for
the ancient bed contemporary with the Trojan War as Homer describes it,
light blue for the modern bed, green for the Strabo/Pliny-era channel;
contour heights from Graves, Spratt, and Burnouf). It shows the Hellespont
coastline, Aegean coastline, Kum Kale, Achilleion/Cap Sigeion, Kallikolone,
Troy/Ilion, and the full Scamander–Simoeis drainage.

Direct link: [archive.org/details/trojaundilionerg02dorp](https://archive.org/details/trojaundilionerg02dorp),
leaf 268, or the image URL above.

**Licence.** Same as the rest of Dörpfeld 1902 — published 1902, US public
domain, 95-year term expired 1997 (per `RESEARCH-CITADEL.md` §1's own
reasoning, which applies unchanged). *authority:* licence + geometry.
*verified how:* image fetched and read directly (not OCR-inferred); Erläuterung
prose (the plate's own explanatory text, printed pp. 648–649 in the same
volume) also re-extracted from the item's OCR text and matches the plate's
content exactly.

**Consequence, stated but not acted on** (out of this lane's scope — no
tracked file besides this one was touched): `RESEARCH-CITADEL.md` §1.1's
plate table and §7's "not in these scans" line for Tafel I are now
superseded. The full 8-Tafel apparatus (I–VIII) is confirmed present and
readable on archive.org in `trojaundilionerg02dorp`. Whoever next revises
`RESEARCH-CITADEL.md` should update the table (add `page/n268_w4000.jpg` for
Tafel I) and strike the corresponding "unverified" item.

**Other Dörpfeld avenues checked, for completeness:**
- Heidelberg (`digi.ub.uni-heidelberg.de/diglit/doerpfeld1902ga`,
  `doerpfeld1902bd1`, `doerpfeld1902bd2`): confirmed blocked by the same
  Anubis challenge described in Hunt 2 (verified directly — raw response
  body inspected, contains the `anubis_challenge` JSON, not a generic 403).
  Wayback snapshots exist for the landing pages and confirm Heidelberg hosts
  Band 1 and Band 2 as **separate** records from the combined overview page,
  each with a whole-book PDF download link (`zoom=1` / `zoom=4`) — but PDF
  generation is dynamic and not present in Wayback's cache, so it could not
  be checked for Tafel I without solving Anubis. Moot now that archive.org
  has confirmed the plate.
- A fourth archive.org copy not in `RESEARCH-CITADEL.md`'s table:
  [`trojaundilioner00drgoog`](https://archive.org/details/trojaundilioner00drgoog)
  (Google-digitised from the New York Public Library, Vol. 1, 554 leaves).
  Checked its OCR text for the plate title — no match, consistent with
  Tafel I not being in Volume 1 (it belongs with the other plates in Volume
  2, confirmed above).
- Gallica (BnF), MDZ München, arachne.dainst.org: WebSearch only, no
  direct hits for this title at any of the three. Not independently
  confirmed present or absent.

---

## 4. HUNT 4 — Leaf, *Strabo on the Troad* (1923) and *Troy* (1912)

### 4.1 Leaf, *Strabo on the Troad: Book XIII, Cap. I* (Cambridge, 1923)

**Citation, independently corroborated.** W. M. Calder's review: "Strabo on
the Troad. Book XIII., Chap. I. By Walter Leaf. Pp. xlviii + 352. 20 plates
and 8 maps. Cambridge: University Press, 1923." —
[PhilPapers record](https://philpapers.org/rec/CALSOT). This confirms the
citation already used in `RESEARCH-TROAD-TOPOGRAPHY.md`/gazetteer entries and
gives a full collation (20 plates, 8 maps) not previously recorded.

**Full-view scan located, not independently opened.** HathiTrust holds a
full-view copy: catalog record
[catalog.hathitrust.org/Record/001223462](https://catalog.hathitrust.org/Record/001223462),
reader link
[babel.hathitrust.org/cgi/pt?id=mdp.39015013332179](https://babel.hathitrust.org/cgi/pt?id=mdp.39015013332179).
**This session could not verify the reader directly** — every access attempt
(WebFetch on both URLs, `curl` with a full browser User-Agent on both the
reader URL and the HathiTrust Bib API) returned HTTP 403 from HathiTrust
itself, which looks like an IP/datacenter-level block rather than a
per-request bot check (no challenge page returned, just a bare Apache 403).
*authority:* reference (existence) — access blocked, not content-verified.
No archive.org or Google Books full-view alternative was found (WebSearch for
both came up empty or preview-only — Google Books shows a "Preview this
book »" button on its about page for id `qs87AAAAIAAJ`, which reads as
limited preview, not full view).

**Verdict:** the scan almost certainly exists and is almost certainly public
domain (published 1923, pre-1931), but this session cannot personally attest
to having opened it. A human with a normal residential/institutional IP
should retry the HathiTrust link directly — the block looks environmental to
this research session, not a genuine access restriction on the item.

### 4.2 Leaf, *Troy: A Study in Homeric Geography* (1912) — resolving the ±1 page-number flag

`RESEARCH-POEM-TOPOGRAPHY.md` §9 item 6 flags every Leaf 1912 page number
quoted in that document as "±1 until someone opens the scan to the page,"
because they were read from OCR'd index text.

**Resolved for the sample checked.** The archive.org item
([`troyastudyinhom00leafgoog`](https://archive.org/details/troyastudyinhom00leafgoog),
490 leaves) provides normal archive.org BookReader page-image access (not
OCR-only) — this was already true and just needed confirming. I fetched and
read the actual index page image at leaf `n486`: it is printed page **406**,
and it reads, exactly as quoted in the existing doc: `"Spring of the Plain"
(Throsmos), 41`. This confirms that specific citation is accurate as
transcribed, not OCR-corrupted.

**Leaf-to-page offset, for resolving the rest of the flagged citations
quickly:** printed page = leaf number − 80 (486 − 406 = 80), at least in the
back matter. A future pass can use this to jump straight to any other flagged
page (e.g. the doc's other flagged corrections, "85-40" for 35-40 and "48"
for 43) via
`https://archive.org/download/troyastudyinhom00leafgoog/page/n{page+80}_w1600.jpg`,
then confirm visually rather than trusting OCR. This offset is a local
estimate from one data point near the end of the book; front-matter and
plate pages may shift it — verify against a second index entry before relying
on it for early-book citations.

**Bonus find, not previously noted:** leaf `n487` (immediately after the
index) is a separate fold-out map, "THE PLAIN OF TROY" ("From Admiralty
Chart, 1608. By permission." — that is chart **number 1608**, not a year; a
first draft misread the digit, caught at Grok verification against the ink and
the volume's plate list), with a nautical-mile/cable scale bar — an
additional period map bound into this same PD volume, not currently used
anywhere in the apparatus. Caveat: the BookReader JPEGs for `n487` render the
foldout almost blank (a rotated caption strip only) — a usable extract needs
the item's JP2/PDF, not the `page/n487_w*.jpg` URLs.

*authority:* geometry (page-number accuracy) + reference (the bonus map).
*verified how:* both leaf images fetched and read directly.

---

## 5. Unverified — do not claim publicly

1. **Hunt 1, in full.** Neither Mey 1926 nor any 1928 Andrae/Mey publication
   was found scanned or otherwise located. The Andrae Nachlass finding aid's
   silence is a real negative result but not proof of non-publication.
   **Do not attribute the `BattlefieldH.jpg` drawing to any dated, PD source.**
2. **Hunt 2.2, the 1925 Brückner piece's exact leaf/page location.** The
   volume (JdI Band 40 / Heidelberg `jdi1925`) and its approximate page range
   are confirmed; the article itself was not opened. Do not cite a specific
   page image URL for it yet.
3. **Hunt 3's "K10plus," Gallica, MDZ, and arachne.dainst.org checks for
   Dörpfeld** were WebSearch-only and inconclusive (neither confirmed present
   nor confirmed absent). Moot for current purposes since archive.org already
   supplies a full, high-resolution, visually confirmed Tafel I — but don't
   cite these as "checked, absent."
4. **Hunt 4.1, direct confirmation of the HathiTrust Leaf 1923 scan's
   contents.** Existence and full-view status are well corroborated by
   independent secondary sources; this session's own access attempts were
   blocked outright by HathiTrust, so no direct look at a single page was
   possible. Treat as "very likely available," not "confirmed open."
5. **The AA volume-numbering offset noted in Hunt 2.1** (AA "26"/"39" vs. JdI
   Band "27"/"40") is inferred from two matching year/content pairs, not from
   a documented editorial convention. Treat as a working hypothesis.
