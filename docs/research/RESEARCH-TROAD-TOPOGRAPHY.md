# Research: Troad topography — the regional identification dossier

**Date:** 2026-07-29
**Extends:** [`docs/TROAD-SOURCES.md`](../TROAD-SOURCES.md) (2026-07-28). That file is the
Trojan-plain source dossier: paleogeography, the plain's named features, the licensing
table, and the record-by-record JSON block. **This file does not repeat it.** Where the
two overlap, this file supersedes only where it says so explicitly, and only because it
carries a verification the earlier file did not have.

**What this is:** the authority file for the gazetteer's `certainty` tiers and for the
wide-sheet (Troad-regional) places — the ones outside the plain, on Ida, in the southern
Troad, and along the Propontis. Consumed by `apparatus/places.json` editors and by the
`troad` plate drawing lanes.

**What this is not:** it is not geometry for the plain, not paleogeography (see
[`RESEARCH-PALEOGEOGRAPHY.md`](RESEARCH-PALEOGEOGRAPHY.md)), and not site copy.

---

## How to read every entry

Per the handoff's dossier discipline, each claim carries four things:

| Element | Meaning |
|---|---|
| **claim** | the assertion, stated so it can be checked |
| **citation** | Chicago for books and articles; a hyperlink for web resources and databases |
| **authority kind** | **geometry** (a coordinate or a line, from survey/DEM/OSM/a georeferenced plan) · **identification** (this ancient name = this place) · **prose** (an argument, a judgement, a description) |
| **verified how** | what I actually did to check it |

**Never mix authorities.** Scholarship settles identifications, tiers and prose. Geometry
comes from Pleiades/AWMC/OSM/DEM. A book is never a source of coordinates, and a
shapefile is never a source of an identification.

### Sampling declaration (read this)

- **Covered, not sampled:** all 28 places tagged `troad` in `apparatus/places.json`, plus
  the four `troad-plain` records this brief names (`uvecik-tepe`, `besik-bay`,
  `callicolone`, `thymbra`).
- **Machine-checked, not eyeballed:** every `pleiades` URL in the whole gazetteer (330
  records) was resolved against the Pleiades bulk CSV dump and its coordinate compared to
  the Pleiades representative point. Findings in §8.
- **Sampled:** Strabo 13.1. I verified **sections 5, 9, 35, 36, 44, 45, 50, 51, 61, 62, 63
  and 65** verbatim. Other section numbers already in the gazetteer are **not** verified
  and are listed in §10.
- **Not seen at all:** Cook 1973 and Luce 1998. Not one page. Every citation of them below
  is at work level with no page number, deliberately. See §9.

---

## 1. The four authorities, and what each is actually good for

### 1.1 Cook, *The Troad* (1973) — the backbone, and we have not read it

**claim:** Cook is the standing modern authority for Troad site identification: a
systematic archaeological and topographical survey, still the reference for the region's
settlement identifications outside Hisarlık itself.
**citation:** Cook, J. M. *The Troad: An Archaeological and Topographical Study*. Oxford:
Clarendon Press, 1973. ISBN 0198131658; LCCN 73178602; 550 scanned images.
[archive.org `troadarchaeologi0000cook`](https://archive.org/details/troadarchaeologi0000cook)
— **lending only.**
**authority kind:** identification (and prose).
**verified how:** fetched `https://archive.org/metadata/troadarchaeologi0000cook`;
`access-restricted-item = true`, collections `inlibrary`/`printdisabled`. I could not open
a single page, and archive.org's search-inside API did not respond. **Consequence: no
Cook page number appears anywhere in this dossier, and none should be added to
`places.json` until someone has the book open.** Nine `places.json` records already cite
Cook 1973 at work level, which is honest; a page number invented later would not be.

### 1.2 Leaf, *Troy: A Study in Homeric Geography* (1912) — PD, verified, and quotable

**claim:** Leaf 1912 is public domain in the US and is a full-text-searchable Troad
topography with a usable index. Its US status is unambiguous: London: Macmillan, 1912.
**citation:** Leaf, Walter. *Troy: A Study in Homeric Geography*. London: Macmillan, 1912.
[Full text, archive.org](https://archive.org/details/troyastudyinhom00leafgoog).
**authority kind:** identification, prose. **Not geometry** — Leaf's maps are traceable as
PD *images*, but his place positions are 1912 judgements, not survey points.
**verified how:** downloaded the `_djvu.txt` (740 kB of body text after stripping the
Google wrapper), read the title page (`MACMILLAN AND CO., LIMITED … 1912`), the contents
(8 chapters, 5 appendices, index at pp. 403–406), and the index entries quoted below. OCR
quality is fair: it renders *Simoeis* as "Simois", *Üvecik* as "Ujek", *Beşik* as
"Besika", and mangles some index page ranges — every page number I cite below was read off
the index or a running head and is flagged where the OCR is doubtful.

Index page references verified by reading the index directly (pp. 403–406):

| Leaf's entry | pages | usable? |
|---|---|---|
| Kallikolone | 44 | yes |
| Ophrynion | 44, 176, 198 | yes |
| Simois River | 27, 31, 34–5, 37, 40, 384–5 | yes |
| Satniois River | 32, 199, 213 | yes |
| Granicus River | 174, 184 | yes |
| Aesepus River | 173, 180–3 | yes |
| Aesepus Valley | 181, 237 | yes |
| Killa | 216–17 | yes |
| Chryse | 223–35 | yes |
| Lyrnessos (Antandros) | 217 | yes |
| Antandros | 203, 218–19, 238, 241 (OCR "288, 241") | partly — 238 is an OCR guess |
| Thebe | 244, plus a range the OCR gives as "218‑6" | **no — do not cite the range** |
| Adramyttium | 214–16, 230 | yes |
| Zeleia | 181 | yes |
| Dardania | 159, 176–80 | yes |
| Besika Bay | 256, 259, 260, 262, 269 | yes |
| Ida | 202–8 | yes |

### 1.3 Leaf, *Strabo on the Troad* (1923) — PD, cited here at second hand

**claim:** Leaf 1923 is the standard PD commentary on Strabo's Troad and is the work
Jones's Loeb notes refer the reader to for Troad topography (e.g. "See Leaf, *Strabo on
the Troad*, p. 48" at Strabo 13.1.5; "On the site of Ophrynium, see Leaf, p153").
**citation:** Leaf, Walter. *Strabo on the Troad: Book XIII, Cap. I*. Cambridge: Cambridge
University Press, 1923.
**authority kind:** prose (identification, where quoted).
**verified how:** I read those cross-references **in Jones's Loeb apparatus**, not in Leaf
1923 itself. I have not opened Leaf 1923. Its page numbers here are Jones's, not mine.

### 1.4 Luce, *Celebrating Homer's Landscapes* (1998) — in copyright, unseen

**claim:** Luce 1998 is the fullest modern defence of the accuracy of Homer's Troad
landscape; it is the prose authority behind several `speculative` records in the
gazetteer.
**citation:** Luce, J. V. *Celebrating Homer's Landscapes: Troy and Ithaca Revisited*. New
Haven: Yale University Press, 1998.
**authority kind:** prose.
**verified how:** **not verified.** Not on archive.org (advanced-search for the title
returns `numFound: 0`). Every gazetteer citation of Luce is at work level; keep it that
way. See §9.

### 1.5 Strabo 13.1 — the Demetrius of Scepsis material, verified verbatim

**claim:** Strabo book 13 chapter 1 is the single ancient source behind most `traditional`
identifications in the Troad, and its topographical core is Demetrius of Scepsis, whom
Strabo names and quotes — "a man who was acquainted with the region and a native of it,
who gave enough thought to this subject to write thirty books of commentary on a little
more than sixty lines of Homer, that is, on the Catalogue of the Trojans" (13.1.45).
**citation:** Strabo, *Geography* 13.1, trans. H. L. Jones, Loeb Classical Library, vols.
V (1928) and VI (1929). Text at LacusCurtius:
[13.1 part 1](https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Strabo/13A1*.html) ·
[part 2](https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Strabo/13A2*.html) ·
[part 3](https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Strabo/13A3*.html).
Also [Perseus](https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0198:book%3D13:chapter%3D1).
**authority kind:** identification (Strabo's own equations) and prose (his and Demetrius's
arguments). **Never geometry** — Strabo's stadia are constraints, not coordinates.
**verified how:** downloaded all three LacusCurtius pages, split them on the
`<A CLASS="sec" NAME="1.N">` anchors into all 70 sections, and read the sections listed in
the sampling declaration. LacusCurtius states the text is public domain; both Loeb volumes
are pre-1931, so PD in the US. Sections 36 and 5 were additionally cross-checked against
Perseus's `xmlchunk` output and agree.

**Stadion caution used throughout:** Strabo's stadion is taken here as 157.5–185 m, so a
figure like "40 stadia" is a band of **6.3–7.4 km**, not a number. Every conversion below
gives the band.

### 1.6 Pleiades and AWMC — the geometry, and what their flags actually mean

**claim (Pleiades):** Pleiades is an identification authority *with coordinates attached*,
CC-BY 3.0, and its `locationPrecision` field is about how precisely a source's point was
digitized — **not** about how well the site is identified. Pleiades 550919 (Thebe) is
`locationPrecision: precise` and its own record describes that point as a "1:500,000 scale
representative point from Barrington Atlas". A `precise` flag on a Barrington
representative point does not license a `certain` tier.
**citation:** [Pleiades](https://pleiades.stoa.org/), CC-BY 3.0. Bulk dump:
[`pleiades-places-latest.csv.gz`](https://atlantides.org/downloads/pleiades/dumps/pleiades-places-latest.csv.gz).
**authority kind:** geometry + identification.
**verified how:** downloaded the dump (42,363 place rows), and fetched the per-place JSON
for 550403, 550870, 554307 and 550919 to read the reference lists and precision prose.

**claim (AWMC):** AWMC's public geodata is **ODbL**, not CC-BY; its documented attribute
for the Pleiades link is `pleiadesid` (GeoJSON) / `pid` (shapefiles), and the AWMC
identifier appears as `AWMC_ID` in the inland-water layer and as `OBJECTID` in the rivers
layer. **The GeoJSON collection contains no river-line layer** — river lines exist only in
the shapefile release, so a lane that expects `rivers.geojson` in that repo will find
nothing.
**citation:** [AWMC/geodata](https://github.com/AWMC/geodata) ·
[attribute_information.md](https://github.com/AWMC/geodata/blob/master/attribute_information.md)
· `LICENSE.txt` = ODC Open Database License (ODbL) ·
`Physical Shapefiles Apr 2024.zip` → `rivers/awmc-osm-rivers.{shp,dbf,shx}` (10,876
records).
**authority kind:** geometry.
**verified how:** read `LICENSE.txt` (first line: "## ODC Open Database License (ODbL)");
downloaded `inland-water-OSM.geojson` (15.9 MB, 6,393 features — lakes and swamps, and
**none** of our ten Troad rivers); downloaded the 20.5 MB physical shapefile zip, listed
it, parsed `awmc-osm-rivers.dbf` field-by-field with `struct`, and read the matching
`.shp` records via the `.shx` index. Extents in §5 are measured off that geometry.

---

## 2. The three coordinate resolutions

These are the three `certainty: certain` records with no coordinate (handoff §3.8 and
§3.12). All three are real places; all three now have a coordinate with a source and a
stated precision.

### 2.1 `uvecik-tepe` — Üvecik Tepe → **39.9003, 26.1992**

**claim:** Üvecik Tepe is at 39.9003 N, 26.1992 E — 7.2 km SSW of Hisarlık (bearing 208°).
**citation (primary):** [Pleiades 897256486, "Uvecik Tepe"](https://pleiades.stoa.org/places/897256486)
— `reprPoint` 39.9003210655 / 26.1991743094, `locationPrecision: precise`, featureType
`tumulus`.
**citation (corroborating):** [Vici.org 11483, "Üvecik Tepe, Tomb of Festus"](https://vici.org/vici/11483/?lang=en)
— 39.900234 / 26.199306 · [Kültür Envanteri, "Üvecik Tepe"](https://kulturenvanteri.com/en/yer/caracalla-tumulusu/)
— 39.9005280 / 26.1991730, "within the boundaries of Üvecik Village in Ezine District,
between Yeniköy and Üvecik Village", height c. 35 m, Roman, 3rd century.
**authority kind:** geometry.
**precision:** the three sources agree to within **35 m**. Treat as ±50 m, mound centre.
This is a hard point and can carry a dot on the geographic plate.
**verified how:** Pleiades value read from the bulk CSV row; the two web sources fetched
independently and the arithmetic done here (Vici↔Kültür Envanteri differ by 0.0003° lat).
The searched-result sexagesimal form 39°54′0.842″N 26°11′57.502″E converts to
39.90023/26.19931, i.e. the Vici figure exactly.

**Two corrections to the record's prose while it is being edited:**

1. **claim:** Festus was Caracalla's **freedman**, not (or not merely) his "favourite".
   **citation:** Pleiades 897256486 description: "a tumulus in the Troad built for one
   Festus, a freedman of the emperor Caracalla"; Leaf, *Troy* (1912), 26: "The great
   tumulus of Ujek Tepe, for instance, is possibly the tomb built by Caracalla for his
   freedman Festus in 214 a.d."
   **authority kind:** prose. **verified how:** both read directly. `places.json` currently
   says "a favourite of Caracalla", following Livius.org. Two independent sources say
   freedman; prefer that, or say both.
2. **claim:** Leaf hedges the attribution — "**possibly** the tomb built by Caracalla".
   The gazetteer states it flatly. **authority kind:** prose. **verified how:** quoted
   above. The tier can stay `certain` (the mound is certainly there and certainly Roman);
   the *identification of the occupant* is the hedged part, and the note should carry
   Leaf's "possibly".

### 2.2 `besik-bay` — Beşik Bay → **39.891, 26.154** (derived; an areal feature)

**claim:** Beşik Bay is the bight on the Aegean coast running south from Beşika Burnu. Its
mouth is a **4.26 km** chord between headlands at 39.8711/26.1511 (south) and
39.9094/26.1501 (north); the coast reaches its innermost point at 39.8945/26.1610, giving
a maximum depth of **0.88 km**; the enclosed water area is **c. 2.16 km²**; the area
centroid is **39.891 N, 26.154 E**, 10.3 km SW of Hisarlık (bearing 224°).
**citation (geometry):** OpenStreetMap `natural=coastline` ways 212382384, 212382385,
4579367 and 4521291, retrieved via
[Overpass API](https://overpass-api.de/api/interpreter) 2026-07-29 (`timestamp_osm_base`
2026-07-29T22:41:09Z), ODbL.
**citation (that this bight is Beşik Bay):**
[Pleiades 550401, "Achilleion"](https://pleiades.stoa.org/places/550401) — 39.9150772041 /
26.1517428172, `precise`, Barrington Directory note (the live JSON's `details`
field; the bulk CSV's geoContext column) **"Beşika Burnu"**, i.e. the cape at the bay's north
end · OSM way 212382335, "Beşiktepe" (`alt_name` "Beşiketepe; Beşik‑Yassıtepe Höyüğü",
`historic=archaeological_site`, `archaeological_site=tumulus`), 39.9169579 / 26.1593986,
which is Korfmann's excavated mound on that same headland.
**authority kind:** geometry (the numbers) + identification (that the named cape and mound
sit on this bight).
**precision:** a bay has no point. Treat the centroid as ±0.5 km and, on the plate, draw
the **chord and the arc**, not a dot. The two headland coordinates are the useful values.
**verified how:** Overpass query for coastline in bbox 39.85–39.96 / 26.05–26.25 returned
17 ways / 1,108 vertices; I ordered the four mainland ways south→north, clipped to the
chord, and computed chord length, depth, shoelace area and centroid in a local planar
approximation. Cross-check: the OSM Beşiktepe node (39.91696/26.15940) matches the
`besik-sivritepe` coordinate already in `places.json` (39.9171/26.1591) to 40 m, so the
coastline extract is in the right place.

**Two findings attached to this resolution:**

1. **Do not use the Wikipedia coordinate.** [Wikipedia, "Beşik Bay, Çanakkale"](https://en.wikipedia.org/wiki/Besika_Bay)
   gives **40°12′N 26°24′E / 40.200 N, 26.400 E** while describing the bay as "on the
   Aegean shore of Troy". 40.200/26.400 is inside the Dardanelles, c. 35 km NE of the
   Aegean coast and nowhere near Beşika Burnu or Beşiktepe. **authority kind:** geometry
   (bad). **verified how:** fetched the article and compared its own coordinate to its own
   locality description and to Pleiades 550401.
2. **There are two Beşiktepes in the Troad, c. 42 km apart.** Pleiades 550565 (Hamaxitos)
   has geoContext **"Beşiktepe, Gülpınar"** at 39.543605 / 26.09471 — the *southwest*
   Troad, by the Smintheion. Ours is Beşik‑Yassıtepe/Beşiktepe near Yeniköy at
   39.9170/26.1594. A lane geocoding "Beşiktepe" by name will land on the wrong one.
   **authority kind:** identification. **verified how:** both Pleiades rows read from the
   dump; distance computed.

**A dissent that belongs in the record, from a PD source:** "Troy has, indeed, two
roadsteads, one to the north on the Hellespont, the other, Besika Bay, to the west; but
both of them are exposed anchorages, offering no safe shelter in gales." — Leaf, *Troy*
(1912), 254. Leaf argues at 256–62 against Bérard's Beşik-Bay-as-transhipment-port thesis:
"Nothing can ever have been gained by land transport from Besika Bay to the mouth of the
Scamander" (258). The `besik-bay` note currently gives only the case *for* the harbour
(Korfmann's LH IIIB pottery). Leaf's objection is about *shelter*, not about the graves,
so the two are compatible — but the record reads one-sidedly.
**authority kind:** prose. **verified how:** quoted from the PD full text; page numbers
from the running heads (p. 254 head "VI THE ALLIES AND THE WAR 255" immediately follows).

### 2.3 `adramyttion` — Adramyttium → **39.4986, 26.9361**

**claim:** Adramyttium is at 39.4986 N, 26.9361 E — the Karataş peninsula at Ören,
Balıkesir province. This is **not** modern Edremit (39.596/27.024), 13 km to the NE.
**citation:** [Pleiades 550403, "Adramyttium"](https://pleiades.stoa.org/places/550403) —
`reprPoint` 39.4986400291 / 26.9360975594, `locationPrecision: precise`, geometry
`LineString`, featureTypes `settlement, archaeological-site`, geoContext "Karataş (Ören)",
`BAtlas 56 D2 Adramyttium`.
**authority kind:** geometry + identification.
**precision:** Barrington 56 D2 point, digitized precisely; the record is a LineString (a
site outline), so ±few hundred m for a representative dot.
**verified how:** fetched the Pleiades JSON directly and read `reprPoint`, precision,
geometry type and Barrington reference; the bulk CSV row agrees exactly.

**Why the record exists at all is now confirmed, with the arithmetic:** Strabo measures
Homeric Thebe *from* Adramyttium. "From Adramyttium the former [Thebê] is distant sixty
stadia and the latter [Lyrnessus] eighty-eight, in opposite directions" (13.1.61, Jones).
Sixty stadia = **9.5–11.1 km**. The Barrington point for Thebe (Pleiades 550919,
39.597431/27.020171, "1 mile NNE Edremit") lies **13.15 km** from Adramyttium on a bearing
of **33°**. So Strabo's figure and Barrington's point agree to within about 2 km — good
corroboration, and worth saying in the note.
**authority kind:** identification (Strabo) + geometry (Pleiades) + arithmetic.
**verified how:** Strabo 13.1.61 read verbatim from LacusCurtius; distance and bearing
computed here from the two Pleiades points.

Also worth carrying, since it anchors the whole southern cluster:
[Pleiades 550402, "Adramyttenos/Idaios Sinus"](https://pleiades.stoa.org/places/550402) —
the Gulf of Edremit, 39.4695211733 / 26.7273648789, `precise`, featureType `water-open`.

---

## 3. Pleiades and AWMC ids for every `troad` place

**authority kind:** geometry + identification throughout. **verified how:** every id and
coordinate below read from the Pleiades bulk CSV (42,363 rows) or, for AWMC, parsed out of
`awmc-osm-rivers.dbf`/`.shp`. Where a place has no record I say so rather than guessing.

`gaz` = what `apparatus/places.json` carries today. `Δ` = distance between the gazetteer
coordinate and the Pleiades representative point, in km, computed here.

| gazetteer id | Pleiades | title / geoContext | Pleiades lat, lon | precision | Δ | AWMC |
|---|---|---|---|---|---|---|
| troy | [550595](https://pleiades.stoa.org/places/550595) | Ilium/Troia · Hisarlık | 39.9574, 26.2385 | precise | 0.06 | — |
| scamander | [550871](https://pleiades.stoa.org/places/550871) | Scamander (river) · Menderes Çay | 39.8287, 26.4784 | precise | 23.29 | rivers `OBJECTID 1667`, pid 550871, `accurate=1` |
| simoeis | [550883](https://pleiades.stoa.org/places/550883) | Simoeis (river) · Dümruk Su | 39.9681, 26.2434 | precise | 3.18 | rivers `OBJECTID 3022`, pid 550883 |
| ida | [550592](https://pleiades.stoa.org/places/550592) | Ida (mountain) · Kaz Dağ | 39.6927, 26.8192 | precise | 6.97 | — |
| gargaron | [550545](https://pleiades.stoa.org/places/550545) | Gargara Akron · Kaz Dağ | 39.75, 26.75 | **rough** | (null) | — |
| lekton | [550691](https://pleiades.stoa.org/places/550691) | Lekton/Lectum · Bababurnu | 39.4783, 26.0633 | precise | 0.00 | — |
| tenedos | [550912](https://pleiades.stoa.org/places/550912) | Tenedos (island) · Bozcaada | 39.8206, 26.0353 | precise | 2.11 | — |
| imbros | [501438](https://pleiades.stoa.org/places/501438) | Imbros (**settlement**) · Kaleköy | 40.2333, 25.9008 | precise | 8.26 | — |
| — (island record) | [501439](https://pleiades.stoa.org/places/501439) | Imbros (**island**) · Gökçeada | 40.1633, 25.8567 | precise | 0.8 from gaz | — |
| samothrace | [501597](https://pleiades.stoa.org/places/501597) | Samothrace (island) | 40.4523, 25.5762 | precise | 6.60 | — |
| lemnos | [550693](https://pleiades.stoa.org/places/550693) | Lemnos (island) | 39.9050, 25.2291 | precise | 1.91 | — |
| lesbos | [550696](https://pleiades.stoa.org/places/550696) | Lesbos (island) | 39.1775, 26.2375 | **related** | 4.65 | — |
| hellespont | [501434](https://pleiades.stoa.org/places/501434) | Hellespont (strait) · Dardanelles | 40.2188, 26.4769 | precise | 10.07 | — |
| abydos | [501325](https://pleiades.stoa.org/places/501325) | Abydos | 40.1942, 26.4113 | precise | 0.48 | — |
| sestos | [501609](https://pleiades.stoa.org/places/501609) | Sestos | 40.2134, 26.3893 | precise | 1.75 | — |
| percote | [501556](https://pleiades.stoa.org/places/501556) | Perkote | 40.2739, 26.5888 | precise | 0.00 | — |
| arisbe | [501359](https://pleiades.stoa.org/places/501359) | Arisbe · Musakoy? | 40.1943, 26.5358 | precise | 0.00 | — |
| dardania | [501393](https://pleiades.stoa.org/places/501393) | **Dardanos** · 2 mi S Kepez | 40.0797, 26.3744 | precise | 7.75 | — |
| zeleia | [511461](https://pleiades.stoa.org/places/511461) | Zeleia · Sarıköy | 40.2036, 27.5961 | precise | **41.29** | — |
| thymbra | [550927](https://pleiades.stoa.org/places/550927) | Thymbra · area of Akça Köy and Hanay Tepe | 39.75, 26.25 | **rough / unlocated** | (null) | — |
| — (the anchor) | [550929](https://pleiades.stoa.org/places/550929) | **Thymbras Pedion** · plain at confluence of Kemer Su and Menderes Çay | 39.8997, 26.2933 | precise | — | — |
| thymbrios (plain layer) | [550930](https://pleiades.stoa.org/places/550930) | Thymbrios (river) · Kemer Su | 39.8604, 26.4230 | related | (null) | rivers `OBJECTID 3093`, pid 550930 |
| chryse | [550501](https://pleiades.stoa.org/places/550501) | Chryse (Aeolis) · Mağara Tepe, near Akçay · `BAtlas 56 D2 Chryse?` | 39.5851, 26.9281 | precise | **65.16** | — |
| — (rival) | [550500](https://pleiades.stoa.org/places/550500) | Chrysa · Göztepe · `BAtlas 56 C2` | 39.5213, 26.0829 | precise | — | — |
| — (rival) | [550892](https://pleiades.stoa.org/places/550892) | Smintheion · Külahlı, Gülpınar | 39.5362, 26.1177 | precise | — | — |
| — (rival) | [554214](https://pleiades.stoa.org/places/554214) | Chryse (on Lesbos) | — | unlocated | — | — |
| cilla | [554254](https://pleiades.stoa.org/places/554254) | Killa · **perhaps near Akçay** · `BAtlas 56 unlocated Killa` | — | **unlocated** | (null) | — |
| — (its anchor) | [550646](https://pleiades.stoa.org/places/550646) | Killaios? (river) · Zeytinli Dere | 39.5831, 26.9434 | precise | — | rivers `OBJECTID 4257`, pid 550646 |
| — (its anchor) | [550645](https://pleiades.stoa.org/places/550645) | Killaios (mountain) · Adatepe | 39.6853, 26.9513 | precise | — | — |
| thebe-hypoplacia | [550919](https://pleiades.stoa.org/places/550919) | Thebe · 1 mi NNE Edremit · `BAtlas 56 E2` | 39.5974, 27.0202 | precise (= BAtlas representative point) | (null) | — |
| — (its plain) | [550920](https://pleiades.stoa.org/places/550920) | Thebes Pedion · plain of Edremit | 39.5974, 27.0202 | related | — | — |
| lyrnessus | [550703](https://pleiades.stoa.org/places/550703) | Lyrnessos · Ala Dağ · `BAtlas 56 E2` | 39.5082, 27.0820 | precise | 0.03 | — |
| — (second record) | [652355](https://pleiades.stoa.org/places/652355) | Lyrnessos · `BAtlas 66 unlocated` | — | unlocated | — | — |
| pedasus-troad | [554307](https://pleiades.stoa.org/places/554307) | Pedasos · deserted site near Satnioeis fl. · `BAtlas 56 unlocated` | 39.5478, 26.1939 | **unlocated** (representative point only) | (null) | — |
| adramyttion | [550403](https://pleiades.stoa.org/places/550403) | Adramyttium · Karataş (Ören) | 39.4986, 26.9361 | precise | (null) | — |
| satnioeis | [550870](https://pleiades.stoa.org/places/550870) | Satnioeis (river) · Tuzla Çayı | 39.5435, 26.2005 | precise (20 m) | (null) | rivers `OBJECTID 3107`, pid 550870 |
| aisepos | [511141](https://pleiades.stoa.org/places/511141) | Aisepos (river) · Gönen Çay | 40.0166, 27.4599 | precise | (null) | rivers `OBJECTID 1668`, pid 511141 |
| granikos | [511260](https://pleiades.stoa.org/places/511260) | Granicus (river) · Biga Çayı | 40.1071, 27.1270 | precise | (null) | rivers `OBJECTID 1699`, pid 511260 |
| rhodios | [501590](https://pleiades.stoa.org/places/501590) | Rhodios (river) · Kocaçay | 40.1400, 26.4645 | precise | (null) | rivers `OBJECTID 3007`, pid 501590 |
| rhesos‑heptaporos‑karesos → Rhesos | [511398](https://pleiades.stoa.org/places/511398) | Rhesos (river) · Karaatli Çay | 40.25, 27.25 | **rough** | (null) | rivers `OBJECTID 3002`, pid 511398 |
| → Karesos | [511287](https://pleiades.stoa.org/places/511287) | **Karesos?** (river) · Kocabaş Çay, tributary of Aisepos | 40.25, 27.25 | **rough** | (null) | rivers `OBJECTID 1703`, pid 511287 |
| → Heptaporos | **none** | no Pleiades record under any spelling | — | — | — | **none** |
| uvecik-tepe (plain layer) | [897256486](https://pleiades.stoa.org/places/897256486) | Uvecik Tepe | 39.9003, 26.1992 | precise | (null) | — |
| besik-bay (plain layer) | **none** | nearest: [550401](https://pleiades.stoa.org/places/550401) Achilleion · Beşika Burnu, 39.9151/26.1517 | — | precise | (null) | — |
| sigeion (plain layer) | [550877](https://pleiades.stoa.org/places/550877) / [550878](https://pleiades.stoa.org/places/550878) | Sigeion · Yenişehir / promontory · Kumkale | 39.9835, 26.1809 / 40.0078, 26.1990 | precise | 0.00 (settlement) | — |
| rhoiteion (plain layer) | [550856](https://pleiades.stoa.org/places/550856) | Rhoiteion · Baba Kale | 40.0097, 26.3033 | precise | 0.04 | — |

**Caution on the AWMC column.** `OBJECTID` is the identifier inside the **Apr-2024
physical shapefile release** of `AWMC/geodata`. It is stable enough to cite as a data
locator ("`rivers/awmc-osm-rivers`, `OBJECTID 3107`, `pid=550870`") but it is not a
published persistent AWMC URI, and it is **not** the same numbering as the `AWMC_ID` field
used in the inland-water layer. Do not present it to readers as an authority id; use it in
build scripts and cite Pleiades to readers.
**verified how:** field list read straight off the DBF header — `OBJECTID, ID, accurate,
perennial, rank, origin, v2eHide, Shape_Leng, Name, en_name, pid, lat, lon, featuretyp,
timeperiod, awmc_mod, awmc_class, creators, notes, Asia_Minor, Strabo, Strabo_nam,
Strabo_n_1, done, importance, ex_data, osm_id, title, external_d`.

---

## 4. What Strabo actually says — the verified quotation base

Each of these is the ancient warrant for a `traditional` tier. Quotations are Jones's Loeb
translation (PD), read verbatim from LacusCurtius.

**4.1 Gargaron — 13.1.5 (verifies the gazetteer's citation).**
> "Now while Homer thus describes Lectum and Zeleia as the outermost foot-hills of Mt. Ida
> in either direction, he also appropriately distinguishes Gargarus from them as a summit,
> calling it 'topmost.' And indeed at present time people point out in the upper parts of
> Ida a place called Gargarum, after which the present Gargara, an Aeolian city, is named."

**authority kind:** identification. **verified how:** read in 13.1.5. The gazetteer's
`gargaron` tradition string — "the summit of Mount Ida / Kaz Dağı, following Strabo
13.1.5" — is **correct**, section and all. Note what Strabo is careful about: Gargarum
(the place on Ida) and Gargara (the city below) are distinct, which is exactly the warning
already in the record.

**4.2 Callicolone — 13.1.35, with real measurements.**
> "A little above this is the Village of the Ilians, where the ancient Ilium is thought to
> have been situated in earlier times, at a distance of thirty stadia from the present
> city. And ten stadia above the Village of the Ilians is Callicolonê, a hill, past which,
> at a distance of five stadia, flows the Simoeis. … But since Callicolonê is forty stadia
> distant from the present Ilium, for what useful purpose would the poet have taken in
> places so far away that the line of battle could not reached them?"

**authority kind:** identification (a triangulation, not a coordinate). **verified how:**
read in 13.1.35. Three constraints, converted with the 157.5–185 m band:

- Callicolone is **40 stadia = 6.3–7.4 km** from Hisarlık;
- it is **10 stadia = 1.6–1.9 km** above the Village of the Ilians;
- the Simoeis flows past it at **5 stadia = 0.8–0.9 km**.

Strabo cites the 40 stadia *polemically* — to argue that Homer cannot have meant the
present Ilium — so the figure is Demetrius's measurement to the Callicolone of his own day,
not an endorsement. Even so it is the only ancient number we have, and it is a genuine
constraint on the drawn sheet. The `callicolone` coordinate currently in `places.json`,
[39.96, 26.28], is **3.55 km** from Hisarlık, i.e. about 19–23 stadia — roughly half
Strabo's distance. See §8.

**4.3 Thymbra — 13.1.35 (verifies the gazetteer's citation and its anchor).**
> "Again, the words, 'And towards Thymbra fell the lot of the Lycians,' are more suitable
> to the ancient settlement, for the plain of Thymbra is near it, as also the Thymbrius
> River, which flows through the plain and empties into the Scamander at the temple of the
> Thymbraean Apollo, but Thymbra is actually fifty stadia distant from the present Ilium."

**authority kind:** identification. **verified how:** read in 13.1.35. This confirms both
halves of the record: the Thymbrios–Scamander confluence as the anchor, and Strabo 13.1.35
as the citation. Fifty stadia = **7.9–9.3 km** from Hisarlık. And Pleiades already has
that confluence as a *precise* point: **550929, Thymbras Pedion, 39.8997/26.2933**,
"plain at confluence of Kemer Su and Menderes Çay" — 7.95 km SE of Troy (bearing 144°),
just inside the low end of Strabo's band. That is the coordinate the record should carry as a **district anchor**, not
Pleiades 550927's rough 39.75/26.25.

**4.4 Pedasos and the Satnioeis — 13.1.50, not 13.1.51.**
> "I must now add that Homer speaks of a Pedasus, a city of the Leleges, as subject to
> lord Altes: 'Of Altes, who is lord over the war-loving Leleges, who hold steep Pedasus
> on the Satnioeis.' And the site of the place, now deserted, is still to be seen. Some
> write, though wrongly, 'at the foot of Satnioeis,' as though the city lay at the foot of
> a mountain called Satnioeis; but there is no mountain here called Satnioeis, but only a
> river of that name, on which the city is situated; but the city is now deserted."

**authority kind:** identification + prose. **verified how:** read in 13.1.50; 13.1.51 was
also read and is about Assos, Gargara, Antandros, the Cebrenians and Dardanians — it does
**not** mention Pedasos or the Satnioeis. The `pedasus-troad` record cites "Strabo
13.1.51"; the passage is **13.1.50**. Note also the substantive point: Strabo says the
deserted site "is still to be seen" in his day — the Barrington entry is nevertheless
`unlocated` (Pleiades 554307), which is the honest modern position.

**4.5 Thebe, Chrysa, Lyrnessus — 13.1.61.**
> "But the greater part of it is now held by the Adramytteni, for here lie both Thebê and
> Lyrnessus, the latter a natural stronghold; but both places are deserted. From
> Adramyttium the former is distant sixty stadia and the latter eighty-eight, in opposite
> directions."

**authority kind:** identification. **verified how:** read in 13.1.61; independently
corroborated by Leaf's own translation of the same sentence (Leaf, *Troy*, 217: "here lie
Thebe and Lyrnessos, a stronghold, but both are deserted. Their distances from Adramyttium
are in the one case 60 stades, and in the other 88 in the opposite direction"). Arithmetic
done here: Barrington's Thebe is 13.15 km from Adramyttium at bearing 33°; Barrington's
Lyrnessos is 12.58 km at bearing 85°. Sixty stadia = 9.5–11.1 km; eighty-eight = 13.9–16.3
km. So Thebe is c. 2 km further than Strabo says, Lyrnessos c. 1.3–3.7 km nearer, and the
two Barrington points are **52° apart, not "in opposite directions"**. Leaf saw the same
problem: "What is meant by … 'the opposite direction,' it is impossible to say. It cannot
mean diametrically opposite; for wherever we choose to place Adramyttium and Thebe, we are
faced by the fact that it is impossible to draw a line of 148 stades in length lying
wholly within the plain" (*Troy*, 217).

**4.6 Cilla — 13.1.62–63, and the anchor Leaf derived from it.**
> "In the territory of Adramyttium lie also Chrysa and Cilla. At any rate there is still
> to-day a place near Thebê called Cilla, where is a temple of the Cillaean Apollo; and
> the Cillaeus river, which runs from Mt. Ida, flows past it. These places lie near the
> territory of Antandrus." (13.1.62)

**authority kind:** identification. **verified how:** read in 13.1.62. Leaf works the
passage into a locality: "This locates Killa just at the north-east corner of the Gulf of
Adramyttium, somewhere in the neighbourhood of Ak Chai, the port of Edremid. No ruins or
tumulus have been discovered in the neighbourhood… It is here that the Zeitünlü Chai enters
the sea. It is the largest stream which flows from Ida on this side, and it is natural to
identify it with the river Killaios… as the local legends appear to be ancient, we may take
it that the Homeric Killa also lay here" (*Troy*, 216–17).

**This is a fully closed chain, and it is worth writing into the record:** Strabo
13.1.62–63 → Leaf 1912, 216–17 (Killa near Akçay; the Killaios = the Zeytinli stream) →
Pleiades 554254, geoContext "**perhaps near Akçay**", `unlocated`, and Pleiades 550646,
"Killaios? (river) · **Zeytinli Dere**", 39.5831/26.9434, `precise`. Pleiades' hedge is
Leaf's reasoning, a century on. The gazetteer's `cilla` tradition currently says only
"Troad, near Thebe under Placus; Barrington Atlas map 56 lists it unlocated" — true, but it
throws away a named tradition it could name.

**4.7 Chryse — 13.1.63, and Strabo argues the opposite of what our record says.**
> "Chrysa was a small town on the sea, with a harbour; and near by, above it, lies Thebê.
> Here too was the temple of the Sminthian Apollo; and here lived Chryseïs. But the place
> is now utterly deserted; and the temple was transferred to the present Chrysa near
> Hamaxitus when the Cilicians were driven out… Those who are less acquainted with ancient
> history say that it was at this Chrysa that Chryses and Chryseïs lived, and that Homer
> mentions this place; but, in the first place, there is no harbour here, and yet Homer
> says, 'And when they had now arrived inside the deep harbour'; and, secondly, the temple
> is not on the sea, though Homer makes it on the sea… neither is it near Thebê…"

**authority kind:** identification + prose. **verified how:** read in 13.1.63, and 13.1.65
read alongside it ("It is twenty stadia distant from the ancient Chrysa, which also had
its temple in a sacred precinct. Here too was the Palisade of Achilles. And in the
interior, fifty stadia away, is Thebê, now deserted, which the poet speaks of as 'beneath
wooded Placus'; but, in the first place, the name 'Placus' or 'Plax' is not found there at
all, and, secondly, no wooded place lies above it, though it is near Mt. [Ida]").

**Strabo's position is that the Hamaxitos Chrysa is *not* Homer's**, and he names the
people who think otherwise as "those who are less acquainted with ancient history." The
`chryse` record's tradition string reads "Near Hamaxitos and the sanctuary of Apollo
Smintheus, Strabo 13.1.47-48, 13.1.63, against a rival Adramyttene Chrysa" — which puts
Strabo behind the candidate he attacks and calls the candidate he defends the "rival". See
§8; this is the single worst factual defect I found.

Note also, for the `thebe-hypoplacia` note: **Strabo himself doubts the Homeric epithet
fits the site he is describing** — "the name 'Placus' or 'Plax' is not found there at all,
and… no wooded place lies above it" (13.1.65). Rich, not hedging: state that as the ancient
geographer's own objection, which is what it is.

**4.8 The eight Idaean rivers — 13.1.44, Demetrius's own uncertainty.**
> "It is said that the country was named after the Caresus River, which is named by the
> poet, 'Rhesus, Heptaporus, Caresus, and Rhodius'… Again, Demetrius says as follows: 'The
> Rhesus River is now called Rhoeites, unless it be that the river which empties into the
> Granicus is the Rhesus. The Heptaporus, also called Polyporus, is crossed seven times by
> one travelling from the region of the Beautiful Pine to the village called Melaenae and
> the Asclepieium that was founded by Lysimachus.' … The Caresus flows from Malus, a place
> situated between Palaescepsis and the Achaeïum… and it empties into the Aesepus. The
> Rhodius flows from Cleandria and Gordus, which are sixty stadia distant from the
> Beautiful Pine; and it empties into the Aenius."

**authority kind:** identification (contested, in antiquity). **verified how:** read in
13.1.44; 13.1.45 read for the Caresus dale on the left bank of the Aesepus and for
Strabo's assessment of Demetrius. This is the passage that justifies keeping
`rhesos-heptaporos-karesos` at `speculative`: the local expert, writing thirty books on
sixty lines, could not decide which stream the Rhesus was, and identified the Heptaporus by
a *route* ("crossed seven times") rather than a place. **The gazetteer's note that these
were "already puzzling to ancient geographers" is now verified against the primary text,
with the quotation to prove it.**

---

## 5. Rivers with known courses — what to draw, and at what tier

The handoff (§3.12) is right that these are rivers with known courses and no gazetteer
coordinate, and wrong to imply that gives them a coordinate. **A river takes a line, not a
point.** Here is the line, measured.

All extents from `AWMC/geodata`, `Physical Shapefiles Apr 2024.zip`,
`rivers/awmc-osm-rivers` (ODbL). `accurate` is AWMC's own flag.
**verified how:** DBF parsed by field offsets; the matching SHP polyline read via the SHX
index; bounding boxes and vertex counts read off the record headers. Cross-check: the
Pleiades representative point for each river falls **inside** its AWMC bounding box in all
ten cases.

| gazetteer id | modern stream | AWMC vertices | lat extent | lon extent | `accurate` | BAtlas source | tier the evidence supports |
|---|---|---|---|---|---|---|---|
| scamander | Karamenderes / Menderes Çay | 501 | 39.7753–40.0028 | 26.1970–26.9805 | **1** | BAMap56 | `certain` ✔ |
| simoeis | Dümrek Su | 92 | 39.9663–39.9966 | 26.2299–26.3968 | 0 | BA56 | `traditional` ✔ (as the gazetteer now has it) |
| satnioeis | Tuzla Çayı | 288 | 39.5024–39.5899 | 26.1038–26.3222 | 0 | BA56 | `traditional` ✔ |
| aisepos | Gönen Çay | 460 | 39.8159–40.3234 | 27.2547–27.6854 | 0 | BAMap1 | `certain` ✔ |
| granikos | Biga Çayı | 225 | 39.9790–40.2703 | 26.8786–27.2482 | 0 | BA52 | `traditional` ✔ |
| rhodios | Kocaçay | 209 | 39.9635–40.1508 | 26.4000–26.6100 | 0 | BA51 | `speculative` — but see below |
| rhesos‑…‑karesos → Rhesos | Karaatli Çay | 257 | 40.1424–40.3731 | 26.8188–27.3007 | 0 | BA51 | `speculative` ✔ |
| → Karesos? | Kocabaş Çay | 295 | 39.9119–40.3083 | 27.1311–27.3894 | 0 | BA52 | `speculative` ✔ |
| → Heptaporos | **no modern identification anywhere** | — | — | — | — | — | `speculative`; say it is unmapped, not merely uncertain |
| thymbrios (plain layer) | Kemer Su | 236 | 39.8952–39.9627 | 26.2860–26.4719 | 0 | BA56 | `traditional` ✔ |
| (cilla's anchor) Killaios? | Zeytinli Dere | 149 | 39.5712–39.7634 | 26.9376–26.9697 | 0 | BA56 | anchor only, not a Homeric place |

**Two things this table settles.**

1. **Only the Scamander line is flagged accurate by AWMC.** Nine of the ten carry
   `accurate=0`. A plate that draws all ten with the same weight and the same implied
   authority is overclaiming, and the fix costs nothing: draw the nine at a lighter weight
   or with a note, and say in the legend that AWMC flags only the Scamander as accurate.
   **authority kind:** geometry. **verified how:** the field is literally named `accurate`
   and is documented in AWMC's `attribute_information.md`.
2. **`rhodios` has a mapped course but not a secure identification, and those are
   different claims.** Barrington 51, Pleiades 501590 and AWMC all place a Rhodios on the
   Kocaçay, flowing to the Hellespont near Dardanos. Demetrius could not fix the Rhesus and
   put the Rhodius's outfall in the Aenius (13.1.44). So the honest treatment is: keep the
   tier `speculative` **for the Homeric identification**, record the Pleiades and AWMC ids,
   and if the line is drawn, label it "Barrington's Rhodios" — an identification by a modern
   atlas, not by Homer. The gazetteer's note ("No secure modern identification; variously
   placed east of the Scamander since antiquity") is true about scholarship and misleading
   about data availability; it is why the Tiles view says "Not locatable" about a river the
   drawn plate can trace.

### 5.1 `gargaron` — the peak, with two candidate summits

**claim:** Homeric Gargaron is traditionally the summit region of Kaz Dağı. Two OSM summit
nodes compete for the honour and disagree by 2.45 km:

- OSM node 26863370, `name=Karataş Tepesi`, `alt_name=Karataş Zirvesi`, **`alt_name:en=Gargarus`**, `ele=1759`, at **39.6997, 26.8571**
- OSM node 1326637741, `name=Kazdağı`, `alt_name=Kaz Dağı`, `name:en=Ida`, `name:el=Ἴδη`, `ele=1774`, at **39.7044, 26.8292**

**citation:** OpenStreetMap via [Overpass](https://overpass-api.de/api/interpreter),
retrieved 2026-07-29, ODbL · [Pleiades 550545, "Gargara Akron"](https://pleiades.stoa.org/places/550545)
— 39.75 / 26.75, `locationPrecision: **rough**`, "One of the heights of Mount Ida in the
Troad" · [Pleiades 550592, "Ida (mountain)"](https://pleiades.stoa.org/places/550592) —
39.6927 / 26.8192, precise · Strabo 13.1.5 (§4.1).
**authority kind:** geometry (OSM/Pleiades) + identification (Strabo).
**verified how:** Overpass query for `natural=peak` with `ele>1400` in bbox 39.60–39.80 /
26.70–26.95 returned 15 nodes; the two above are the highest and the only named ones. The
OSM tagging is internally inconsistent — the node tagged `Kazdağı` carries the massif's
highest elevation (1774 m) while the node explicitly glossed `Gargarus` in English carries
1759 m.
**recommendation:** keep `traditional` (Strabo 13.1.5 names the tradition and the record
already does). If a coordinate is wanted, use **39.6997, 26.8571** — the node that carries
the English gloss *Gargarus* — with precision **±3 km** and a note that the summit region,
not a surveyed point, is what the tradition identifies. **Do not use Pleiades 550545's
39.75/26.75**: it is `rough`, and it sits **10.75 km NW** of the massif's summits, which
would put Zeus's seat off the mountain.

### 5.2 `thebe-hypoplacia`, `pedasus-troad`, `cilla`, `lyrnessus` — the southern cluster

| id | what the authorities give | coordinate available? | tier the evidence supports |
|---|---|---|---|
| `thebe-hypoplacia` | Strabo 13.1.61 (60 stadia from Adramyttium) + 13.1.65 (50 stadia inland from Astyra, and Strabo's own doubt about "Placus"); Barrington 56 E2 → Pleiades 550919, 39.5974/27.0202 | **yes**, as a Barrington representative point, ±2 km against Strabo's own figure | `traditional` ✔ — with the tradition named as *Barrington 56 E2, after Strabo 13.1.61*, and Strabo's Placus objection in the note |
| `pedasus-troad` | Strabo **13.1.50** (steep Pedasus on the Satnioeis; the deserted site "still to be seen"); Barrington 56 **unlocated** → Pleiades 554307, whose 39.5478/26.1939 is a representative point on an `unlocated` record, derived from its link to the Satnioeis | **no** — the Pleiades point is a relation, not a site | `speculative` ✔; anchor to the Satnioeis line, and fix the section number to 13.1.50 |
| `cilla` | Strabo 13.1.62–63; Leaf 1912, 216–17 (near Akçay, at the mouth of the Zeytinli stream); Barrington 56 **unlocated** → Pleiades 554254 "perhaps near Akçay" | **no** — a documented, not a guessed, null | `speculative` ✔; but name the tradition (Strabo via Leaf) and record Pleiades 554254 + the Killaios anchor 550646 |
| `lyrnessus` | Strabo 13.1.61 (88 stadia from Adramyttium, "in the opposite direction" — which Leaf shows cannot be satisfied); Barrington 56 E2 → Pleiades 550703, 39.5082/27.0820, Ala Dağ; plus a second, `unlocated` Lyrnessos, Pleiades 652355 | **a point exists**, and the gazetteer now matches it to 0.03 km | `speculative` ✔ — the coordinate is now correctly sourced, and the note should say the Barrington point does **not** satisfy Strabo's own bearing |

**verified how:** Strabo sections read verbatim as above; Leaf's pages read in the PD full
text; Pleiades rows read from the dump; all distances and bearings computed here.

---

## 6. The 2020 hydrochemistry — the citation in the repo is wrong

**claim:** the study that found no hot-and-cold spring pair near Troy was published in
**CATENA**, not in *Geochemistry*, and it carries a published **erratum**.

**citation (corrected):** Wolkersdorfer, Christian, Susanne Stadler, Anja Bretzler, Claudia
Müller, and Claudia Zedler. "Hydrochemical investigations to locate Homer's hot and cold
springs of Troia (Troy)/Turkey." *CATENA* 200 (2021): 105070.
https://doi.org/10.1016/j.catena.2020.105070.
**Erratum:** Wolkersdorfer, Christian, Susanne Stadler, Anja Bretzler, Claudia Müller, and
Claudia Zedler. "Erratum to 'Hydrochemical investigations to locate Homer's hot and cold
springs of Troia (Troy)/Turkey' [Catena 200 (2021) 105070]." *CATENA* 202 (2021): 105295.
https://doi.org/10.1016/j.catena.2021.105295.

**authority kind:** prose (a measured negative result).
**verified how:** queried the Crossref REST API by title. Both records returned with
`container-title: ["CATENA"]`, `ISSN: ["0341-8162"]` (CATENA's ISSN — and the prefix of the
ScienceDirect PII `S0341816220306202` that the current citation links to), volume 200 /
page 105070, published 2021-05, and the full five-author list with Wolkersdorfer's ORCID
`0000-0003-2035-1863`. The article was published online in 2020 and in the 2021 print
volume, which is where "Geochemistry 80 (2020)" seems to have come from — but neither the
journal name nor the volume matches anything Crossref knows.

**Where the wrong citation currently lives:** `apparatus/places.json` →
`two-springs-of-scamander` and `washing-troughs` (both say *Geochemistry* 80 (2020)), and
`docs/TROAD-SOURCES.md` §B and the JSON block. **Flagged, not edited** — this dossier
touches no other file.

**The finding itself, as the abstract states it:** four springs showed elevated
geothermometric reservoir temperatures, three above 95 °C, **none of them close to today's
Troia**; no spring showed an elevated *discharge* temperature; springs that locals call
"hot and cold" held nearly constant temperature through the measuring period (±0.1–0.3 K),
so they read warm in winter and cold in summer. The authors conclude that "a spring *sensu
Homer* never existed in Troia" and that Homer may mean one spring perceived two ways
across the year.
**verified how:** abstract read via search-engine summary and Semantic Scholar's record for
the paper. **I could not open the article itself** — ScienceDirect returned HTTP 403. So the
*wording* above is a paraphrase of the abstract, not a quotation from the paper. Do not put
it in quotation marks on the site until someone has the PDF. See §9.

---

## 7. Two identifications the gazetteer does not currently name

### 7.1 Callicolone: Leaf proposed Ophrynion, and it is not in the record

**claim:** Leaf 1912 identifies the Homeric Kallikolone with the "browy" hills at
Ophrynion, on the eastern side of the plain — an identification the gazetteer does not
mention, which credits only Cook.
> "For Kallikolone we should, therefore, naturally look in a corresponding position on the
> other or eastern side of the plain. The name tells us little; but it must be a hill with
> 'brows,' and these are rare in this region of gentle declivities. It happens, however,
> that just where we want it, there is a group of hills so markedly 'browy' that they gave
> the name of Ophrynion to the Greek town set upon them."

**citation:** Leaf, Walter. *Troy: A Study in Homeric Geography*. London: Macmillan, 1912,
44 (index: "Kallikolone, 44"; "Ophrynion, 44, 176, 198").
**authority kind:** identification (prose reasoning, no coordinate).
**verified how:** passage read in the PD full text; page from the index entry, which the
running heads corroborate. Leaf's reasoning is structural — he pairs Kallikolone against
the Wall of Heracles as the two divine grandstands (Il. 20.144–51) and rejects Dörpfeld's
placing of the Wall at Sigeum because "this would be to all intents and purposes in the
Greek camp, from which the gods retire."

**A second Leaf statement, and I am not certain of its referent.** In a footnote at p. 144
Leaf reports Strabo's measurements — "He says it lay 30 stades along the ridge (of
Hissarlik) towards Ida; 10 stades farther on lay Kallikolone, at 5 stades from the stream
of the Simois" — and continues "This must be the hill called Kara Yur, 680 feet high, the
most conspicuous and characteristic point in the whole ridge." By context "This" is
Kallikolone, but the footnote is compressed and the sentence immediately following is about
the Village of the Ilians. **Do not cite "Leaf identified Kallikolone with Kara Yur" until
someone reads p. 144 in a clean copy.** Listed in §10.

### 7.2 Lyrnessus: Leaf identified it with Antandros

**claim:** Leaf 1912's index entry is "Lyrnessos (Antandros), 217" — he identifies Homeric
Lyrnessos with the historical Antandros. His stated grounds, at 217–19: the pairing of
Thebe with Lyrnessos (Il. 2.691) and of Lyrnessos with Pedasos (Il. 20.92) "raises a
presumption that Lyrnessos lay between Thebe and Pedasos"; and Lyrnessos is where Aeneas
took refuge when Achilles chased him off Ida (Il. 20.187–94), which Leaf explains by the
summer movement of herdsmen to Ida's summits from all the surrounding country.
**citation:** Leaf, *Troy* (1912), 217–19; index p. 405 s.v. Lyrnessos, Antandros.
**authority kind:** identification.
**verified how:** index entry and both passages read in the PD full text. Antandros is a
real, located site, so this is a *checkable* alternative to Barrington's Ala Dağ point —
and it is a different tradition, which the record should name if it names any.

---

## 8. Tiers and coordinates this evidence says are wrong

**Flagged, not edited.** This dossier changes no data file. Ordered by severity.

**8.1 `chryse` — the tradition string inverts Strabo, and the coordinate matches neither
of its own citations. (Severity: high.)**
The record cites Pleiades 550501 and carries `coords: [39.55, 26.17]`. Pleiades 550501 is
at **39.5851/26.9281** — **65.2 km** away. The coordinate is not 550501, not Chrysa 550500
(39.5213/26.0829, 8.1 km off), and not the Smintheion 550892 (39.5362/26.1177, 4.7 km off);
it is an uncited third number, 8.14 km from Chrysa 550500 and 4.74 km from the Smintheion
550892, in the general area of the SW-Troad candidate but at neither of its two sites. And
the tradition string puts Strabo behind the Hamaxitos option while 13.1.63 is Strabo's argument
*against* it (§4.7). **Both the coordinate and the tradition string need John's judgement;
this is a contested identification, so it is a human gate.**

**8.2 `zeleia` — the coordinate is 41 km from the Pleiades record it cites. (High.)**
`coords: [40.35, 27.15]`, cited to Pleiades 511461, which is at **40.2036/27.5961**
(Sarıköy). The record's own tradition string says "near modern Sarıköy" — so the coordinate
contradicts the tradition it states. Either adopt 511461's point or set null.

**8.3 `dardania` — 7.75 km from its cited Pleiades point, and the wrong kind of place.
(Medium.)**
`coords: [40.14, 26.42]`, cited to Pleiades 501393, which is **Dardanos**, "2 miles S
Kepez", at 40.0797/26.3744. Two problems: the number does not match the citation, and
Homeric Dardanie (founded on Ida's slopes *before* Ilios existed, Il. 20.216–18) is not the
historical town of Dardanos. Naming the Pleiades record for a different place as the
authority for this one needs at least a note.

**8.4 `callicolone` — the coordinate is half Strabo's distance. (Medium.)**
`coords: [39.96, 26.28]` is 3.55 km from Hisarlık; Strabo 13.1.35 puts Callicolone at 40
stadia = 6.3–7.4 km (§4.2). The record's `tradition` credits Cook's tentative proposal, but
we cannot read Cook, so we cannot check whether the number is his (one of the nine
Cook-citing records). Given `TROAD-SOURCES.md`
§E already recommends null here, and given the one ancient measurement disagrees with it,
the coordinate should not be drawn as a dot on the geographic plate. Leaf's Ophrynion
proposal (§7.1) should be named alongside Cook's.

**8.5 `imbros` — right coordinate, wrong Pleiades id. (Low, and trivially fixable.)**
`coords: [40.17, 25.85]` cites Pleiades 501438, which is **Imbros (settlement)**, Kaleköy,
40.2333/25.9008 — 8.3 km away. The island record, Pleiades **501439**, is at
40.1633/25.8567 — **0.94 km** from the gazetteer point. The record means the island; cite
501439.

**8.6 `scamander` and `hellespont` — reprPoint-vs-record mismatches, explainable but worth
a note. (Low.)**
`scamander` carries [39.93, 26.24] (a point near Troy) while citing Pleiades 550871, whose
reprPoint is 39.8287/26.4784 — 23.3 km upstream, because the representative point of a
LineString is not a site. Same pattern for `hellespont` (10.1 km) and, less sharply, `ida`
(7.0 km), `samothrace` (6.6 km), `lesbos` (4.7 km, and 550696's precision is `related`, not
`precise`). None of these is a defect in itself; the defect would be a validator or a
reader believing the coordinate came from the cited record. **Recommendation: for
line/area features, record the Pleiades id as an *identification* citation and mark the
coordinate's own basis separately.**

**8.7 `pedasus-troad` — the Strabo section number is wrong. (Low.)**
Cites 13.1.51; the passage is **13.1.50** (§4.4).

**8.8 `thymbra` — has a better anchor available than the one it declines to use. (Low.)**
The record correctly refuses Pleiades 550927's rough 39.75/26.25. But Pleiades **550929**
(Thymbras Pedion) gives the Thymbrios–Scamander confluence as a `precise` point,
39.8997/26.2933 — exactly the anchor the tradition string describes, and inside Strabo's
50-stadia band. Adopt it as a district anchor.

**8.9 Tiers I checked and found correct.** `simoeis` at `traditional` (§5); `satnioeis`,
`granikos`, `thymbrios`, `thebe-hypoplacia`, `gargaron`, `dardania`, `zeleia`, `percote`,
`arisbe` at `traditional`; `rhodios` and `rhesos-heptaporos-karesos` at `speculative`
(§4.8); `cilla`, `pedasus-troad`, `lyrnessus`, `chryse` at `speculative`; `aisepos`,
`scamander`, `lekton`, `abydos`, `sestos`, `adramyttion`, `uvecik-tepe`, `besik-bay` at
`certain`. `washing-troughs` is now `speculative`, which is what `TROAD-SOURCES.md` §E
recommended — that one has landed.

**8.10 One nuance the tier vocabulary cannot express, and that briefs keep tripping over.**
Pleiades `locationPrecision: precise` means *the source's point was digitized precisely*.
For Thebe (550919) that source is a Barrington 1:500,000 representative point; for Üvecik
Tepe (897256486) it is a surveyed mound. Same flag, different epistemic weight by two
orders of magnitude. **Rule for the gazetteer: a Barrington representative point supports
`traditional` at best, never `certain`, however "precise" Pleiades calls it.**

---

## Needs paywalled access

Every item here is a claim we would like to make and currently cannot verify. None of them
should be asserted, page-cited, or quoted until someone has the physical or licensed copy.

1. **Cook, *The Troad* (1973)** — not one page seen. archive.org
   `troadarchaeologi0000cook` is lending-only (`access-restricted-item: true`), and the
   search-inside API did not respond. **Wanted:** Cook's own treatment of, and page numbers
   for, Callicolone (the tentative ridge east of Troy that `places.json` credits to him),
   the Satnioeis = Tuzla Çayı equation, Gargaron, the Scaean/Dardanian gate question, and
   Thebe/Lyrnessos/Pedasos in the southern Troad. **Nine `places.json` records cite Cook at
   work level right now (`simoeis`, `thebe-hypoplacia`, `callicolone`, `scaean-gate`,
   `dardanian-gates`, `sigeion`, `rhoiteion`, `gargaron`, `satnioeis`); a page number must
   not be added to any of them from a secondary summary.**
2. **Luce, *Celebrating Homer's Landscapes* (1998)** — not on archive.org at all
   (`numFound: 0`). **Wanted:** whether Luce charts the fighting scene by scene (already an
   open item in `TROAD-CARTOGRAPHY.md`), and his own positions for the ford, the wagon-road
   and the camp. Eleven `places.json` records cite him (`samothrace`, `oak-of-zeus`,
   `fig-tree`, `lookout-skopie`, `wagon-road`, `scamander-simoeis-confluence`,
   `ford-of-the-scamander`, `bay-of-troy`, `achaean-camp`, `achaean-assembly-place`,
   `besik-bay`), all at work level.
3. **Wolkersdorfer et al., *CATENA* 200 (2021) 105070, and the erratum at *CATENA* 202
   (2021) 105295** — ScienceDirect returns HTTP 403. **Wanted:** the four springs' names
   and coordinates, the measured discharge temperatures, and **what the erratum corrects**.
   The erratum is the more urgent of the two: we are citing a paper whose published record
   includes a correction we have not read.
4. **Leaf, *Strabo on the Troad* (1923)** — PD, but I did not open it; every page number
   attributed to it here is Jones's Loeb cross-reference, not my reading. **Wanted:** Leaf's
   commentary on 13.1.35 (Callicolone's 40 stadia) and 13.1.44 (the Idaean rivers), which
   would be a PD, quotable second opinion on the two hardest identification problems in
   this file.
5. **Rose & Körpe, "The Tumuli of Troy and the Troad" (2016)** — cited by four gazetteer
   records; De Gruyter, unseen. A PDF appears on ResearchGate but I did not fetch it and
   cannot vouch for it being the published version. **Wanted:** which of the Troad mounds
   the survey reclassifies as settlement mounds, and Üvecik Tepe's survey coordinate and
   dimensions.
6. **Barrington Atlas map 56 and its Directory** — the ultimate source of most points in §3,
   reached only through Pleiades. **Wanted:** the Directory entries for Thebe (56 E2),
   Lyrnessos (56 E2), Chryse (56 D2, queried) and Chrysa (56 C2), which would tell us what
   the queries mean.

---

## Unverified — do not claim publicly

1. **Whether Cook 1973 actually proposes the Callicolone ridge at [39.96, 26.28].** The
   gazetteer credits him; the number is uncited; and 3.55 km from Hisarlık contradicts
   Strabo's 40 stadia. We do not know whether the coordinate is Cook's, someone's reading of
   Cook, or invented. **Do not attribute the coordinate to Cook on the site.**
2. **That Leaf identified Callicolone with Kara Yur.** The p. 144 footnote's "This must be
   the hill called Kara Yur, 680 feet high" reads as Kallikolone by context, but the OCR is
   compressed and the next clause is about the Village of the Ilians. Leaf's *main* text
   (p. 44) proposes Ophrynion instead, which makes the footnote harder, not easier, to
   assign. Verify in a clean copy before using either as *the* Leaf position.
3. **The exact wording of the 2020 hydrochemistry's conclusions.** §6 paraphrases the
   abstract from a search summary and a Semantic Scholar record; the article itself was
   403. The *journal, volume, page, DOI, author list and the existence of the erratum* are
   verified through Crossref and are safe. **The sentences are not quotations. Do not put
   them in quotation marks.**
4. **The Üvecik Tepe date of 214 AD.** Leaf says "possibly the tomb built by Caracalla for
   his freedman Festus in 214 a.d."; Kültür Envanteri says "3rd century"; Pleiades says
   "built for one Festus, a freedman of the emperor Caracalla" with no year. The gazetteer
   asserts "built c. 214 AD" flatly. The year traces to Livius.org, not to a source we have
   checked. Keep the "c." and Leaf's "possibly", or verify in Rose 2014.
5. **Whether Beşik Bay is the right *name* for the bight measured in §2.2.** The geometry is
   solid and the two named features on its northern headland (Pleiades 550401 "Beşika Burnu";
   OSM "Beşiktepe") are solid. What I have **not** found is a source that draws the bay's
   own boundary — a chart or a Turkish toponymic authority saying where Beşik Koyu begins and
   ends. My southern headland (39.8711/26.1511) is the coastline's local westernmost point,
   which is a reasonable but *chosen* boundary. State the centroid as derived, and give the
   headlands.
6. **Barrington's basis for the Lyrnessos point at Ala Dağ.** The point fails Strabo's own
   "opposite directions" (§4.5), and Leaf argued the Strabo figures cannot be satisfied at
   all. Whether Barrington had independent grounds — a surveyed site at Ala Dağ — is not
   knowable from Pleiades, whose description is the bare "An ancient place, cited: BAtlas 56
   E2 Lyrnessos". **Do not tell a reader that Lyrnessos "is at" Ala Dağ.**
7. **Whether the AWMC `OBJECTID`s in §3 and §5 are stable across releases.** They come from
   the April 2024 physical shapefile release. Treat them as build-time locators, re-derive
   them if the release changes, and never surface them to readers as identifiers.
8. **Hainsworth on the Troad as a poetical construction.** Carried over from
   `TROAD-SOURCES.md` §C, still unverified at the page, still second-hand. Repeated here so
   it does not get lost when someone reads only this file.
