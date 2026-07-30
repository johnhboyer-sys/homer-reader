# RESEARCH-PALEOGEOGRAPHY.md — the Bronze Age shore, bay, barrier and marsh of the Trojan plain

**Date:** 2026-07-29. **Consumed by:** the Bronze Age shoreline, lagoon, barrier and
marsh layers of `apparatus/plates/trojan-plain.json` and `troad.json`.
**Commissioned by:** `docs/TROY-MAPS-HANDOFF-2.md` §5.

**What this is.** A source dossier: what the geoarchaeological literature actually
claims about the Holocene paleogeography of the lower Karamenderes (Scamander)
valley, with the citation and the verification route for every claim. It is not
site copy. It is written for the agent who draws the shore and for the reviewer
who has to be able to redo the arithmetic.

**Copyright posture (unchanged, per CLAUDE.md).** Everything below is cited as a
SOURCE. Facts — a shoreline position, a date, a borehole depth, a contour
elevation — are not copyrightable and may be re-expressed on our own base. The
figures in Kraft's, Kayan's and Brückner's papers are copyrighted expression and
must never be traced. Site *translations* stay PD-only; the Strabo text used here
is Hamilton & Falconer (1903), public domain.

---

## 0. How to read this file, and what it does not cover

Every claim carries three things:

- **Citation** — Chicago for books and articles; a hyperlink for web resources and
  databases.
- **Authority kind** —
  - **geometry**: fixes a position, a distance, a shape or an elevation, and can
    therefore be drawing input;
  - **identification**: says which ancient name belongs to which feature, and how
    firmly;
  - **prose**: interpretive framing — usable in a note, never as geometry.
- **Verified how** — the exact route by which I saw it. "Abstract only" means
  precisely that.

### Coverage — no silent caps

**Read in full:** Brückner et al. 2005 (open access, OpenEdition); Zangger &
Mutlu 2015 (open access, DergiPark; Turkish with English abstract — Turkish
passages translated by me and marked); Strabo 13.1.31 and 13.1.36 in the PD
Hamilton–Falconer translation via Perseus; **Kraft, Kayan & Erol 1980, text and
all six figures** (JSTOR scan cached at `research-cache/kraft-kayan-erol-1980-science.pdf`,
obtained and read 2026-07-29 — this supersedes the "abstract only" line it used
to sit on, and §1.1 now carries page and figure numbers); **Luce 1984, all
thirteen pages and both figures** (scan cached at
`research-cache/luce-1984-oja.pdf`, obtained and read 2026-07-30 — §1.11 now
carries page cites, and the questions §5 item 8 was holding are answered there,
one of them negatively); **Kraft, Rapp, Kayan & Luce 2003, all four pages and all
six figures** (scan cached at
`research-cache/kraft-rapp-kayan-luce-2003-geology.pdf`, obtained and read
2026-07-30 — §1.3 now carries page and figure cites, the figures were measured
pixel-by-pixel, and the dossier's number-one open question is answered; see
§1.3a–d and the method note at §3.7).

**Abstract or publisher metadata only:** Kayan et al. 2003; Kayan 2019; Seeliger
et al. 2021.

**Not seen at all:** Kraft, Kayan & Erol 1982 (the long version — wanted now for
the **core logs**, not for the map series, which turns out to be Fig. 6 of the 1980
paper and is in hand); Kraft, Kayan, Brückner & Rapp 2003; every one of Kayan's *Studia Troica*
papers; Kayan 2014; Cook 1973; Luce 1995, 1998, 2003; Kelletat 1975; Vacchi et
al. 2013. Their content appears below **only** where a source I did read quotes
or reports them, and it is labelled as second-hand every time. §5 lists them for
the library.

**My own measurements** on the cached SRTM terrarium tiles under
`build/terrain-tiles/` (the same DEM the plates are cut from), taken offline with
the decoder in `scripts/prep-terrain-contours.py`, are labelled *DEM measurement
(this dossier)*. They are geometry, and reproducible: the scripts are in this
session's scratchpad and the recipe is stated inline.

---

## 1. The sources, claim by claim

### 1.1 Kraft, Kayan and Erol 1980 — the foundational paper (FULL TEXT READ, 2026-07-29)

**Claim (summary, p. 776, quoted exactly).** "Sea level rise, deltaic
progradation, and floodplain aggradation have changed the landscape in the
vicinity of ancient Troy during the past 10,000 years. With the waning of the last
major world glaciation and resultant sea level rise and fluctuation, **a marine
embayment protruded nearly 10 kilometers south of the site of Troy at Hisarlik** in
the Troad of northwest Turkey. As the sea approached its present level
approximately 6000 years ago, fluvial and marine deposition caused a northerly
migration of the delta and floodplain of the Scamander and Simois Rivers past the
site of Troy toward **the present-day coast about 6 kilometers north of the site**."
And the conclusion that turns the map around: **"If the Trojan War occurred, then
the axis of the battlefield and associated events must be relocated to the south
and west of Troy."**

- Citation: Kraft, John C., İlhan Kayan, and Oğuz Erol. "Geomorphic
  Reconstructions in the Environs of Ancient Troy." *Science* 209, no. 4458
  (1980): 776–82. https://doi.org/10.1126/science.209.4458.776. Stable URL
  [jstor.org/stable/1684627](https://www.jstor.org/stable/1684627).
- Authority: **geometry** for the 10 km and 6 km figures, the Fig. 6 sea levels and
  the Fig. 2 drill-hole elevations; **identification, hedged** for Beşika as the
  Achaean camp (the paper's own strength is "one might suggest" — do not cite it
  harder than that); **prose** for the battlefield conclusion and the reading of
  Strabo.
- Verified how: **full text and all six figures read 2026-07-29** from the JSTOR
  scan cached at `research-cache/kraft-kayan-erol-1980-science.pdf` (8 pp.
  including the cover sheet; article pp. 776–82), figures examined at 400 dpi.
  The scan carries no text layer, so every quotation below was transcribed from
  the image by eye. Page numbers are the printed *Science* pages.

**Two corrections to what this dossier previously said about the paper.**
(a) The 10 km is **"nearly 10 kilometers"**, not "roughly", and it is measured
**south of the site of Troy at Hisarlık** — the origin is the citadel, not the
coast, which is what §3.2 needed to know. (b) The 6 km is **not** a migration
distance: the paper states it of **the present-day coast, about 6 km north of the
site**. Our earlier gloss ("moving the delta about 6 km toward the present coast")
misread the sentence. See §3.5 for the DEM check.

**The evidential base, and it is small (ref. 11 and ref. 17, p. 782).** The paper
rests on **seven rotary drill holes**, sunk in 1977 "along the axis of the
Scamander River (Kara Menderes Çayi) and the Simois River (Dümrek Çayi)", plus
Virchow's 1879 and Mey's 1926 test pits. Surface elevations as printed on Fig. 2:
**T1 0.9 m, T2 2.6 m, T3 0.9 m, T5 2.6 m** (the plain north and west of Troy),
**T4 4.6 m** (Simois valley, north of the citadel), **T6 14.7 m** (mid-valley),
**T7 19.6 m** (immediately beside Pınarbaşı, at the mouth of the gorge). The
sea-level curve inset in Fig. 3 is credited to ref. 17, **"O. Erol, unpublished
data."** Set that against Kayan's later 318 cores (§1.9): the foundational
geometry of this whole field is seven holes and an unpublished curve. That does
not make the paper wrong, but it does mean **the 1980 lines are a first sketch,
and a later core-based line outranks them wherever the two differ.**

**What the figures actually are** (the dossier previously listed them as unseen).

- **Fig. 1**, p. 777, "Geomorphic outlines of the northeastern Aegean": a
  *regional* geomorphological map, Limnos and Lesvos to the Sea of Marmara, with
  two palaeocoastlines drawn from the legend — **15,000 BP at −100 m** and
  **10,000 BP at −30 m**. Not a Trojan-plain sheet and no use to our layers.
- **Fig. 2**, p. 778, "Geomorphology of Troy and environs": the base map, at
  roughly 1:100,000 with a 0–3 km bar. Legend: high plateau, low plateau, Kara
  Menderes plain, swamp, beaches, steep slopes, cliffs, rivers, shoals, spring,
  settlement, tumulus, cemetery, elevations in metres. It carries the **5 m, 10 m
  and 20 m contours across the plain**, marks **swamp over the Kesik/Yeniköy plain
  and along the western and south-western flanks of the Scamander**, plots T1–T7,
  Virchow's B1–B6 and Mey's pits, and the section lines A, B and C. It places
  **Pınarbaşı at the southern end of the plain beside T7** — which is what §3.2a
  needed (see there).
- **Fig. 3**, p. 779: the N–S cross-section along "the hypothetical axis of the
  Kara Menderes (Scamander) valley", 0–18 km horizontally, +30 m to −70 m
  vertically, with Erol's sea-level curve inset at the left. Time-depositional
  surfaces are drawn for **7000, 4500, 3250 and 2000 BP**; C-14 dates plotted are
  2045, 7653 (this digit read at the scan's limit — could be 7663), 7880, 8547,
  9775, 20,796, 31,961, 33,238 and >39,861 BP (caption:
  "corrected to 5730 ½ life"). Troy is marked "2 km east" at about **6 km along the
  section**, so the section's origin is the Dardanelles shore — the same 6 km the
  summary gives. At the southern end the sandy marine embayment interfingers with a
  **brackish–freshwater swamp** near T7, and the 4500 and 3250 BP surfaces lie
  **below the present floodplain surface along the whole section**.
- **Figs. 4 and 5**, p. 780: the two transverse sections — Sigeum cliffs across the
  floodplain to the Troy promontory (W–E, 0–9 km, +40 m to −60 m), and Troy to the
  southern flank of the Yenikumkale cuesta along the lower Simois (N–S, 0–5 km).
- **Fig. 6**, p. 781: **the paleogeographic map series — five panels, and this is
  the whole of it.** With their printed sea levels: **10,000 BP (sea level −40 m);
  7000 BP (−20 m); circa 4500 BP, Troy I/II (+2 m); circa 3250 BP, Troy VI/VII
  (sea level same as present); "Strabo's time, circa 2000 years BP" (sea level same
  as present)**. Legend: sandy estuary, clay-silt estuary, marsh, sea, alluvial
  plains, highly dissected plateaus, present shoreline, present edge of alluvium;
  0–10 km bar. Beşika embayment is labelled on the 4500 and 3250 BP panels;
  Sigeum, Rhoeteum, Aeantium, New Ilium (Troy) and Thymbra on the 2000 BP panel.

**Sea level, in the paper's own numbers — and this settles a dossier question.**
Fig. 6's panel labels *are* the paper's sea-level statement: **+2 m at 4500 BP,
present level at 3250 BP, present level at 2000 BP.** The text adds that at
15,000 BP sea level was "approximately 100 m below its present level" and that the
"peak marine transgression or inundation" came "by approximately 7000 years ago"
(both p. 782). On the curve's status the authors are explicit: "Although some may
argue that the sea level curve (Fig. 3) is not a truly eustatic curve, it
certainly is valid as a **local, relative,** sea level curve for the Biga
Peninsula" (p. 781). Two consequences:

1. **The Late Bronze Age sea level in this reconstruction is at present level, not
   below it.** The ~2 m fall the panels imply runs from a mid-Holocene high *down
   to* today's datum, between 4500 and 3250 BP. Any note that says the sea "fell
   2 to 2.5 m" and lets a reader infer *below present* is contradicted here — see
   the contradiction list below and §2.
2. The **local/relative** qualifier this dossier recommends for Kayan's fall
   (§1.8) is the 1980 authors' own word for their own curve. Use it, and cite
   p. 781 for it.

- One internal inconsistency, recorded because this file is meant to be
  re-checkable: Fig. 1's legend puts the 10,000 BP coastline at **−30 m**, Fig. 6's
  10,000 BP panel at **−40 m**. Neither figure bears on our layers; the
  discrepancy is a caution about how tightly to read the paper's numbers.

**The Bronze Age shoreline relative to the citadel — the paper gives no distance
(p. 782).** Verbatim: "By 3250 years ago (Troy VI/VII), the supposed time of the
'Trojan War,' the delta prograded to the vicinity of Troy and lay to the southwest
of Troy. **Fortification Troy VI and VII lay on a projection or promontory at the
edge of a marine embayment.** It is possible that low-lying swamps occurred around
the base of Troy at this time, although further drilling would be required to
verify this." And for Strabo's day: "By approximately 2000 years ago the sandy
marine embayment lay approximately **3 km south of the present shoreline, or
northwest of Troy**." Those are the paper's only two positional statements for the
periods we draw, and **neither is a measured citadel-to-water distance.** On
Fig. 6's 3250 BP panel the sandy-estuary hatch reaches to immediately west and
north-west of the Troy VI/VII dot; the citadel sits on the estuary's eastern rim.

**It does not read Strabo the way our shore note assumes.** The paper's verdict is
that "Strabo probably erred in that he described the embayment as it was in his
time, approximately 2000 years ago" (pp. 778–79) — i.e. it treats Strabo's
description as evidence for **c. 2000 BP, not for the war** — while praising its
accuracy for that period: "the data determined from our study suggest that
Strabo's statements are extremely accurate despite their secondhand source"
(p. 782). **No stade figure appears anywhere in the paper.** The 6-stade and
20-stade readings therefore belong to the later Kraft/Luce papers, not to 1980
(§1.3, §1.10, §6).

**The camp and the battlefield axis, first-hand (p. 782).** "Should there be a
historic basis to the Trojan War, then **the axis of the battlefield lay to the
south of Troy and to the east of the Beşika embayment.** Thus one might suggest
that **the Beşika embayment was indeed the site of the Achaean camp**, and the
events described in the *Iliad* and *Odyssey* occurred in a dramatically different
geographic and geomorphologic setting from that described heretofore by
archaeologists. There are no apparent contradictions between the stories of the
*Iliad* and the *Odyssey* and the geographical concepts described in this
article." On the bay itself: "The Beşika embayment of 4000 to 5000 years ago
(Figs. 2 and 6) was possibly an indentation **approximately 2 km inland**"
(p. 782). Note that **summary and body do not say the same thing**: the summary
relocates the battlefield "to the south and **west** of Troy", the conclusion "to
the south of Troy and to the **east of the Beşika embayment**". Quote whichever you
use and say which page it is on.

**Contradictions with our own data, recorded rather than reconciled.**

1. **`shore-bronze`'s note attributes a bay head ~1.2 km north of Hisarlık to
   Kraft.** This paper does not contain it, in any form: no distance, and the
   position it does give is *at* the citadel's promontory with the estuary to the
   west and north-west, not 1.2 km to the north. The attribution in the note is to
   the 2003 *Geology* paper — **and that paper, read in full on 2026-07-30, does
   contain the number (§1.3), so the attribution stands.** What stands from this
   entry is the narrower point: **1980 may not be offered as its support**, and
   1980's own Strabo reading points the other way. Our drawn line stays defensible
   on the Strabo arithmetic (§3.1).
2. **Our sheet says it "draws Kraft" for the camp.** Kraft, Kayan and Erol 1980
   put the Achaean camp at the **Beşika embayment**, ~8 km SW of Hisarlık on the
   Aegean side, and the battlefield axis south of Troy and east of that bay
   (p. 782). That is much closer to Luce's west/south-west reading (§1.11) than to
   any Hellespont-beach camp. If a plate note contrasts "Kraft" with "Luce" as
   north-west against west, the contrast is wrong for 1980: on the camp the two
   are on the same side of the city. Kesik enters only with Kraft et al. 2003a
   (§1.4).
3. **`barrier-bronze`'s "relative sea-level fall of 2 to 2.5 m."** 1980's own
   figures give a fall of exactly **2 m, from +2 m at 4500 BP to present level at
   3250 BP** (Fig. 6). So the *magnitude* is corroborated at the low end and the
   *direction of the datum* is not: the sea ends at today's level, not 2–2.5 m
   below it. Kayan's later 2 m / 2–3 m figures are for the same event; none of the
   three sources prints 2–2.5.
4. **1980 contains no "barrier" and no "lagoon."** Its vocabulary for the
   remaining water is *sandy estuary*, *clay-silt estuary*, *marsh* (Fig. 6
   legend), *swamp*, *beaches*, *shoals* (Fig. 2 legend) and
   *brackish–freshwater swamp* (Fig. 3). The barrier-and-lagoon facies language is
   Brückner's and Kayan's, and §2 already flags it as not drawing-ready.

### 1.2 Kraft, Kayan and Erol 1982 — the long version (STILL UNSEEN; priority lowered 2026-07-29)

**Claim (existence and scope only).** A 30-page treatment of the same work, in a
book devoted to the archaeological geology of Troy. On the evidence of its
length and venue it is where the core logs and the full map series live.

- Citation: Kraft, John C., İlhan Kayan, and Oğuz Erol. "Geology and
  Paleogeographic Reconstructions of the Vicinity of Troy." In *Troy: The
  Archaeological Geology*, edited by George Rapp and John A. Gifford, 11–41.
  Princeton: Princeton University Press, 1982.
- Authority: **geometry**, presumed.
- Verified how: bibliography of Zangger & Mutlu 2015, 578 (entry "Kraft v.d.
  1982"), which quotes from p. 40. Nothing else. **Never cite its contents from
  this dossier.**
- **Confirmed as the same work, from the 1980 paper's own reference list**
  (full text, 2026-07-29): ref. 20, p. 782, cites it as forthcoming — "J. C.
  Kraft, I. Kayan, O. Erol, in 'Geology and paleogeographic reconstructions in the
  vicinity of ancient Troy,' G. Rapp, Jr., and J. Gifford, Eds. (Troy Supplementary
  Monograph 4, Princeton Univ. Press, Princeton, N.J., 1980)". Note the drift:
  the title as printed in 1980 differs from the 1982 published title, the series is
  named *Troy Supplementary Monograph 4*, and the imprint year was expected to be
  1980. Anyone hunting the volume in a catalogue should try both titles.
- What the 1980 full text does **not** relieve: the long version is still the only
  place the seven core logs are printed at length, and it is where the p. 40
  Beşika quotation lives. But the map series is no longer unseen — Fig. 6 of the
  1980 paper *is* the five-panel series (§1.1), so the 1982 pull drops in priority
  (§5).

### 1.3 Kraft, Rapp, Kayan and Luce 2003 — the harbour paper, READ IN FULL 2026-07-30

- Citation: Kraft, John C., George (Rip) Rapp, İlhan Kayan, and John V. Luce.
  "Harbor Areas at Ancient Troy: Sedimentology and Geomorphology Complement
  Homer's *Iliad*." *Geology* 31, no. 2 (2003): 163–66.
  https://doi.org/10.1130/0091-7613(2003)031<0163:HAAATS>2.0.CO;2
- Verified how: **full text and all six figures**, scan cached at
  `research-cache/kraft-rapp-kayan-luce-2003-geology.pdf` (4 pp.; the journal's own
  pagination 163–66 is used throughout below). Figures extracted as 300 dpi bitmaps
  and measured pixel-by-pixel against the printed 2 km bar; method at §3.7.
- **Shape of the thing.** Four pages, six figures, three of them maps of the same
  base at the same registration (Fig. 4 = Strabo's day, ca. 2000 BP; Fig. 5 = the
  *Iliad*, ca. 3250 BP; Fig. 6 = Late Neolithic–Early Bronze Age, 5000–5500 BP),
  plus a cross section (Fig. 2), a two-core facies diagram (Fig. 3), and Spratt's
  1839 Admiralty chart (Fig. 1). **The abstract really does contain no number**
  (kept verbatim at §1.3d) — everything quantitative is in the body and the
  figures, and this entry now carries it.

**THE ANSWER TO THE DOSSIER'S NUMBER-ONE QUESTION: the "1.2 km" IS in this paper,
in these words, on p. 166 — and the paper's own Iliad map contradicts it.**

Verbatim, p. 166, col. 1:

> "Note the 12 stades (2400 m) to the 'Achaians Harbour' as thought of by the
> people of New Ilium (Troy) in 2000 yr B.P., and Strabo's note that the 12 stade
> distance would have been only half that, ~6 stades (~1200 m) at the time of the
> *Iliad*. Note Strabo's comment that the Homeric Greek ship station and camp were
> actually 20 stades (4000 m) from Ilium (Troy) and close to Sigeum (Figs. 4 and
> 5). Further, Strabo's 'distances' to the shoreline and the Greek Camp and ship
> station are **well supported by the environmental lithosome distributions and the
> radiocarbon dates**."

So the attribution `shore-bronze` prints — "1.2 km north of Hisarlik, where Kraft,
Rapp, Kayan and Luce put the bay head" — **is not fabricated. The number is
theirs, on their page, and they say their own cores and dates support it.** Three
qualifications, each of which must travel with it:

1. **It is Strabo's arithmetic, endorsed, not an independent measurement.** The
   paper reaches ~1200 m by halving Strabo's 12 stades, not by drawing a shore
   through a core. The endorsement ("well supported by … lithosome distributions
   and the radiocarbon dates") is asserted, not shown: no core, no date, and no
   figure in the paper is tied to that distance.
2. **The conversion is 200 m to the stade** (12 → 2400 m, 20 → 4000 m, 6 →
   1200 m). At the Attic stade of 177.6 m the same three numbers are 2.13, 3.55
   and 1.07 km (§1.10). Brückner's "ca. 1.2 km" (§1.6) is the same 200 m stade.
   **So "1.2 km" and "1.07 km" are one ancient figure under two conversions, not
   two independent constraints** — and this paper's own figures are drawn on a
   third stade again (§1.3a).
3. **Their Iliad plate does not draw it.** Fig. 5's nearest open water to the Troy
   dot is **2.17 km at bearing 334°** — a factor of 1.8 outside the number the
   text asserts on the facing page (§1.3a). Recorded, not harmonised.

**And the deeper problem, which is the one that should change how we cite this
paper.** The figures are not independent geological evidence about Strabo,
because Strabo is one of their inputs. Verbatim, p. 164, col. 2:

> "We interpret lateral and vertical sedimentary environmental lithosome geometries
> through the use of present surficial lineaments, our subsurface drill-core data,
> limitations imposed by archaeological sites, **and passages from historical and
> classical literature**. Figure 4 shows our interpretation of geomorphologies in
> the time of Strabo, and Figure 5 delineates geomorphologies in the time of
> Homer's *Iliad*."

Fig. 5's caption says the same of the Homeric content: "Locations of morphology and
historic features of *Iliad* are from Luce (1998)." **Citing Fig. 5 as
corroboration of Strabo's 6 stades is circular.** Cite it for what it is: a
literary-geological synthesis, register *identification*, not survey.

- Authority: **geometry** for the three maps and the cross section (relative
  geometry only — see the registration failure at §1.3a); **identification** for
  Kesik (§1.9), the camp (§1.11c) and every Homeric name on Fig. 5;
  **prose** for the Strabo argument.
- **What the paper actually claims to have shown**, and it is weaker than the
  abstract: "Although sedimentary environmental lithosome geometries cannot
  validate legend, we find nothing in the stratigraphic record that negates
  descriptions and events in the *Iliad*" (165); "Nothing that our research has
  discovered negates descriptions in the *Iliad*" (163). A double negative twice.
  The abstract's "correlates very well" is the strongest form of the claim and it
  is the form the body does not support. **Quote the body, never the abstract.**
- **The methodological sentence John will enjoy, and it is verbatim** (166):
  "Only a classicist can translate and interpret correctly the nuances of ancient
  Greek literature. Yet it takes a sedimentologist-geomorphologist to correlate the
  scholarship of the classicist with the geologic data and develop reasonably
  precise ancient landscapes."

#### 1.3a The three maps, measured — geometry authority with a hole in it

All three plates (Figs. 4, 5, 6) are the **same base at the same registration**:
the Troy / New Ilium dot falls at the same pixel (±2 px) in all three, both
graticule ticks are at the same pixel, and the scale bars are identical. That is
good news — the three are directly comparable, and a difference between them is a
claim about change over time rather than a difference of draughtsmanship.

**Scale and projection.** No projection is named. Each plate carries a north
arrow, a bar scale (0–1–2 km, printed length 164 px at 300 dpi ⇒ **82 px/km**), and
exactly **two** graticule ticks: the parallel **39°58′N** on the right frame and the
meridian **26°15′E** on the bottom frame. Two ticks and a bar are enough to
georeference a north-up sheet, so I did.

**And the georeferencing fails.** Three independent checks:

| check | figure says | surveyed | discrepancy |
|---|---|---|---|
| Troy dot vs. its own graticule | 39.9684°N, 26.2469°E | Hisarlık 39.9575, 26.2389 | **1.4 km NE** |
| the dot the "CAPE RHOETEUM" label attaches to (Fig. 4) | 26.245°E | Rhoiteion/In Tepe ~26.32°E | **~6 km west** |
| Troy → Cape Sigeum, straight line | 5.6 km | 6.9 km | −19% |
| Achilleion → Cape Sigeum, along the ridge | 8.6 km | 7.9 km | +9% |

Achilleion (39.934, 26.173 read off the figure) and Üvecik Tepe land within ~0.4 km
of truth, so the sheet is not uniformly wrong — it is **internally inconsistent at
the 10–20% level, with at least two site labels grossly displaced**. That is what
a redrawn 1839 Admiralty chart looks like, and Fig. 1 tells us that is exactly what
the base is (Spratt 1839).

**Rule for our plates: use Figs. 4–6 for topology and for distance-and-bearing from
the citadel. Never lift a coordinate off them.**

**The two annotation arcs are distance arcs centred on Troy, not shorelines.** Both
Fig. 4 and Fig. 5 carry a "12 stades" arc and a "20 stades" arc; measured radii are
**~180 px (2.20 km)** and **~306 px (3.73 km)**, ratio 1.70 against the nominal
20⁄12 = 1.67. Dividing through, the arcs are drawn at **~15 px per stade ≈ 181–187 m
per stade** — i.e. the *figures* use an Attic-scale stade while the *text* converts
at 200 m (§1.3, qualification 2). The mismatch is ~8%; do not treat the two as one
number.

**Fig. 5's 12-stades arc is anchored on the shoreline.** Its inner end sits at the
exact point where the drawn 3250 BP shore comes closest to Troy. That is the
paper's committed Iliad-time bay-head geometry, and here it is, as a radial profile
from the Troy dot (flood-fill of the water region, leak-tested against six probe
points in the stippled alluvium; 82 px/km):

| bearing from Troy | Fig. 5, ca. 3250 BP | Fig. 6, 5000–5500 BP |
|---|---|---|
| 000° (N) | 3.78 km | **0.41 km** |
| 015° | 4.55 km | 0.46 km |
| 030° | 5.27 km | 0.57 km |
| 045°–165° | no water on sheet | 0.80 km at 045°, 1.21 km at 060°, 4.70 km at 075°, then none |
| 180° (S) | no water on sheet | 1.57 km |
| 210° | no water on sheet | 1.16 km |
| 240° | 7.73 km | 0.61 km |
| 270° (W) | 2.79 km | 0.44 km |
| 285° | 2.59 km | 0.43 km |
| 300° | 2.20 km | 0.43 km |
| 315° | 2.18 km | 0.39 km |
| **330°** | **2.17 km** ← nearest approach | 0.39 km |
| 345° | 2.72 km | 0.39 km |

Read off that table:

- **Fig. 5 (the Iliad plate) puts no open water within 2.17 km of the citadel, and
  the nearest water is NNW (bearing 330–334°), not N.** Between the citadel and
  that shore Fig. 5 draws stippled alluvium, marsh symbols and a low hill — i.e.
  **the paper's own map shows dry, marshy delta where its text puts the sea.**
- **Fig. 6 (5000–5500 BP) has the bay lapping the citadel** — water at 0.39–0.46 km
  through the whole NW–W–N sector, at 1.16–1.57 km round to the south, and up the
  Simois to the east-north-east. Troy sits at the tip of a promontory with water on
  three sides, which is Kraft, Kayan & Erol 1980's "projection or promontory at the
  edge of a marine embayment" (§1.1) drawn out.
- **Fig. 4 (2000 BP) is not measurable this way.** Its dotted "sandy coastline"
  band and its thin channel lines leak under flood fill, and a probe put the
  apparent nearest water inside the stippled alluvium. Its "(False Achaean Harbor
  of Strabo 13.1.36)" is a long narrow dot-bordered inlet running SE from the Cape
  Sigeum end toward the Simois plain, with the 12-stades arrow pointing NW at its
  inner shore. Do not print a Fig. 4 distance from this dossier.

**Fig. 2 and Fig. 3, the empirical core.** Fig. 2 is an axial W–E cross section of
the Simois floodplain **north of Troy** (line of section drawn on Fig. 6), ~5.5 km
long, +20 m to −50 m, sea level marked "SL", **"After İlhan Kayan, 1996"**, seven
holes (CKM5, 16, 14, 37, KT36, 9, KT35, plus 33 and 80 at the east end). Dated
brackish-to-marine *Cerastoderma edule* shells, at roughly: **3500 BP at ~−2 m**
(hole 16), 4200 at ~−2 m and 7200 at ~−5.5 m (hole 37), 4725 at ~−2 m and 5445 at
~−5 m (KT36), 7000 at ~−2 m (hole 9), 7600 at ~−7 m and 8100 at ~−9.5 m (KT35),
5200 at ~−3 m and 7200 at ~−6 m (CKM5). The unit immediately below SL across the
whole section is "Coastal Sand and Mud: Shallow Marine, Lagoon, Asmak and/or
Estuary". Fig. 3 is the KT-36 / KT-35 facies pair, **1.3 km apart**, reading down
through channel sand → floodplain → backswamp → coastal swamp → lagoon (4725 BP at
~700 cm) → brackish-to-marine (5445 BP at ~1350 cm) → shallow-marine embayment
(7600, 8100 BP) → Neogene bedrock at ~1950–2050 cm; its caption adds that the
KT-36 fossils were recovered from **11–17 m**.

**The 3500 BP shell at ~2 m below present sea level, ~4.5 km along the section west
of its eastern end, is the only datum in this paper that bears directly on the
Trojan-War shore, and it is on the Simois axis north of the citadel, not west of
it.** It is a depth, not a shoreline position. Nothing in Fig. 2 or Fig. 3 puts
water 1.2 km from Hisarlık.

#### 1.3b Numbers on water depth, alluvium and the barrier — and one flat denial

All p. 164, col. 2 unless noted:

- **Water depth in the embayment: "frequently ~1 m and could vary to 3–4 m."** For
  the wider facies class, Yang's (1982) biofacies IV is "very shallow nearshore
  marine embayments or lagoons with variable salinities and water depth to 40 m."
- **"With as much as 20 m of alluvium on the southern Scamander floodplain, we
  cannot hope to locate the river channels of antiquity. However, we can assert
  with confidence that river channels shifted frequently throughout the past six
  millennia."** Note what that costs them: **Fig. 5 nonetheless draws the
  Scamander, the Simois, a Ford and the "Bridges of War".** The paper disclaims
  the ability to locate ancient channels and then locates them. Our own ford and
  river layers may not lean on Fig. 5.
- **THE BARRIER, DENIED:** "As the delta coast approached the Dardanelles, littoral
  currents and increased wave action sorted sands into nearshore shoals and
  possibly thin beaches, **although no barrier lineaments are evident on the lower
  Scamander delta (Kraft et al., 1980)**." That is a flat negative from the same
  research group whose 2005 reporter (Brückner) supplies our barrier language.
  Applied at §2 and §3.3.
- **Sedimentation rates "extremely low, even in the thin alluvial veneer of lower
  delta floodplains, at the foot of the cliff faces such as at Hissarjik (Troy)
  during the Neolithic through Middle Bronze Ages"** (164, col. 1), citing Kayan
  1991/1995/1996/1997.
- **No sea-level curve, no relative-sea-level number, no subsidence figure.** The
  words "sea level" occur once in the body, of river channels incising below it.
  **This paper may not be cited for the "2 m fall" or for any sea-level claim.**
- **Lagoons are everywhere in the facies vocabulary** — biofacies III "brackish to
  moderately saline lagoons, estuaries, or marshes"; "brackish to saline lagoons,
  and bypassed flanking ponds or lakes progressing from saline to brackish to
  freshwater"; the immediate coastal zone "included clastic silt and clay deposits
  in lagoons, marshes, and interdistributary backswamps" — but **no lagoon is
  located, named or dated.** Register: facies, not geography.
- **What the "harbor areas" of the title turn out to be:** not a site. The paper's
  positive statement is that redistribution of river sand "was limited by the very
  low wave activity in this **long-term sheltered marine embayment**" (164, col. 1).
  The shelter is the bay itself — which is Luce 1984's position exactly (§1.11c),
  and the reason the title's plural has no referent in the body.

#### 1.3c Who is cited, and who is not

The reference list is 15 items. Present: Kraft, Kayan & Erol 1980; Kraft et al.
1987 (Thermopylae); Kraft, Kayan, Brückner & Rapp **2001** (Ephesus/Artemision —
*not* the 2003 Troia facies chapter of §1.4); Kayan 1991, 1995, 1996, 1997; **Luce
1998**; Maclaren 1822; Spratt 1839; Fraser 1937; Stanley 2000; Yang 1982 (an
unpublished Delaware M.S. thesis); Strabo 1960.

**Absent, and each absence is informative:** **Luce 1984** — his own dissenting
article, by a co-author, cited nowhere; **Kayan et al. 2003** and **Kraft, Kayan,
Brückner & Rapp 2003** — the two companion 2003 papers by overlapping author sets,
neither cited here, so the three 2003 positions on Kesik (§1.9) were published
without cross-reference; **Cook 1973**; **Korfmann** (thanked in the
acknowledgments as excavation director, cited for nothing); **Blegen**; every
sea-level authority.

Dates: manuscript received 16 May 2002, revised 22 October 2002, accepted 29
October 2002.

#### 1.3d The abstract, kept because it is what everyone else quotes

**Verbatim.** "For at least two thousand years scholars have debated the location
of Troy and the events and geographic features described in Homer's *Iliad*.
Geologic evidence is used to present a series of maps of the Trojan plain that show
the geomorphic changes over the past six millennia. The geologic evidence
correlates very well with the relevant Homeric geography." Keywords: "Troy,
harbors, archaeology, sedimentary environments, facies."

Confirmed on reading the whole paper: **it contains no number, and its "correlates
very well" is stronger than anything the body claims** (§1.3). Kept here so that
nobody re-derives a bay-head position from it, and so the ledger shows what the
pull actually bought.

### 1.4 Kraft, Kayan, Brückner and Rapp 2003 — the facies chapter (UNSEEN)

**Claim, at second hand.** Their reconstruction ("Scenario II" in Brückner et al.
2005, Fig. 3) keeps a **bird's-foot delta in a quiescent, low-wave-energy
embayment until c. 0 BC/AD**, after which the strong east–west Dardanelles
current takes over, eroding distributary arms and building sand spits. They take
**the Kesik plain (= the Lisgar marsh = Ilıca; naming note at §1.9), a former
marine embayment on the eastern slope of the Sigeum ridge, as the best candidate
for a natural harbour** at the time of the war, and
read Strabo as putting the city 6 stades from the sea then (12 in his own day).
Their own summary line: **"Nothing in our research negates the writings of
Homer!"** (p. 375).

- Citation: Kraft, John C., İlhan Kayan, Helmut Brückner, and George Rapp.
  "Sedimentary Facies Patterns and the Interpretation of Paleogeographies of
  Ancient Troia." In *Troia and the Troad: Scientific Approaches*, edited by
  Günther A. Wagner, Ernst Pernicka, and Hans-Peter Uerpmann, 361–77. Berlin:
  Springer, 2003.
- Authority: **identification** (Kesik as the harbour) and **prose**; the
  geometry is in figures I have not seen.
- Verified how: Brückner et al. 2005, §§20–21, which cites pp. 367 and 375 and
  reproduces their Fig. 8 for Ephesus and Fig. 3(II) for Troy. Second-hand
  throughout.
- **Note the pitfall.** Brückner's "Kraft et al. 2003a" is *this* chapter, not the
  *Geology* paper (his 2003b). Anything attributed to "Kraft et al. 2003" needs
  its letter checked before it goes into a citation.
- **The pitfall is now a substantive divergence, not just a bibliographic one
  (2026-07-30).** With 2003b read in full (§1.3), the two 2003 papers turn out to
  disagree about Kesik: **2003a makes the Kesik plain the harbour; 2003b makes the
  Kesik cut Nestor's wall and ditch and proposes no harbour site at all** (§1.9,
  §1.3b). They do not cite each other. Kraft and Kayan are on both. What the two
  *do* share is the Strabo reading — 6 stades then, 12 in Strabo's day — which 2003b
  prints with metric conversions at p. 166 (§1.10). So this chapter's remaining
  unique value (§5 item 3) is Scenario II's per-period shorelines and the
  Kesik-as-harbour argument, not the Strabo arithmetic.

### 1.5 Kayan — the survey series, and the one abstract that carries numbers

**Claim (Kayan et al. 2003, verbatim abstract).** "Sea-level rise during the
Holocene brought about a ria-type bay (Troian Bay) in the lower part of the
Karamenderes (Scamander) valley which intruded approx. **17 km** up to the south
of the present plain about **7000–6000 years ago**. Since then, alluviation and
deltaic progradation has moved the shoreline north of the Çanakkale Strait
(Dardanelles). A relative fall in sea level of **about 2 m** in the Bronze Age
accelerated this process. Thus, Troia was a coastal settlement at first, while
the area to the west in periods **IV, V and VI was a broad deltaic swamp**. The
sea in the coastal zone of the Karamenderes delta plain was **very shallow**, and
the land was **covered by swamps during the entire progradation period**.
Therefore, the geographical environment **has never been suitable for the
establishment of an important harbour** or city development based on harbour
activity."

- Citation: Kayan, İlhan, Ertuğ Öner, Levent Uncu, Beycan Hocaoğlu, and Serdar
  Vardar. "Geoarchaeological Interpretations of the 'Troian Bay.'" In *Troia and
  the Troad: Scientific Approaches*, edited by Günther A. Wagner, Ernst Pernicka,
  and Hans-Peter Uerpmann, 379–401. Berlin: Springer, 2003.
  https://doi.org/10.1007/978-3-662-05308-9_25
- Authority: **geometry** (17 km, 7000–6000 BP, ~2 m); **prose** (swamp,
  shallowness, no harbour).
- Verified how: publisher abstract read in full in-browser; page range confirmed
  independently by Brückner et al. 2005's bibliography.
- **Two corrections to our data fall out of this.** (a) Our plate cites this
  chapter as sole-authored by Kayan and without pages — it has five authors and
  runs 379–401. (b) Springer's own page renders the title with "Trojan"; Brückner
  and the volume use "Troian". Use the volume's form.

**Claim (Kayan 2019, verbatim abstract).** Between plateau ridges **about 50–100 m
high** the lower Karamenderes flows in an alluvial plain. "In this area, the
relative sea level reached its present position **ca. 7000–6000 years ago**, and
the coastline arrived close to the southern end of the embayment. Then, deltaic
progradation processes of the Karamenderes River dominated the embayment filling,
leading the coastline to reach **the west of Troia ca. 4000 years ago**. A **2–3 m
sea level fall during the Late Bronze Age (LBA)** was probably caused by the
acceleration of the deltaic progradation. Later, slightly rising sea reached to
the present level again **around the time of the Emperor Augustus** (27 BC to 14
AD)."

- Citation: Kayan, İlhan. "Landscape Development and Changing Environment of
  Troia (North-western Anatolia)." In *Landscapes and Landforms of Turkey*,
  edited by Catherine Kuzucuoğlu, Attila Çiner, and Nizamettin Kazancı, 277–91.
  Cham: Springer, 2019. https://doi.org/10.1007/978-3-030-03515-0_12
- Authority: **geometry** (the ridge heights, the dates, the 2–3 m).
- Verified how: publisher abstract read in full in-browser, plus its reference
  list (which is where the Kayan bibliography in §5 comes from).
- **Correction to our data.** `barrier-bronze` states "a relative sea-level fall
  of 2 to 2.5 m" and cites Kayan 2019. Kayan 2019 says **2–3 m**; Kayan et al.
  2003 says **about 2 m**. Neither says 2–2.5. Quote a range that a source
  actually prints, and name which source prints it.

**The rest of the series (unseen; cite only after §5).** Kayan, İlhan. "Holocene
Geomorphic Evolution of the Beşik Plain and Changing Environment of Ancient Man."
*Studia Troica* 1 (1991): 79–92. · "The Troia Bay and Supposed Harbour Sites in
the Bronze Age." *Studia Troica* 5 (1995): 211–35. · "Holocene Stratigraphy of the
Lower Karamenderes–Dümrek Plain and Archaeological Material in the Alluvial
Sediments to the North of the Troia Ridge." *Studia Troica* 6 (1996): 239–49. ·
"The Water Supply of Troia." *Studia Troica* 10 (2000): 135–44. · "Die troianische
Landschaft: Geomorphologie und paläogeographische Rekonstruktion der
Alluvialebenen." In *Troia: Traum und Wirklichkeit*, 309–14. Stuttgart, 2001. ·
"Paleogeographical Reconstructions on the Plain along the Western Foot-Slope of
Troy." In *Mauerschau: Festschrift für Manfred Korfmann*, 993–1004. 2002. · "Mit
dem Kernbohrer in die Vergangenheit." In *Troia: Archäologie eines
Siedlungshügels und seiner Landschaft*, edited by Manfred Korfmann, 317–28. Mainz,
2006. · "Kesik Plain and Alacalıgöl Mound: An Assessment of the Paleogeography
around Troia." *Studia Troica* 18 (2009): 105–28. · "Geoarchaeological Research at
Troia and Its Environs." In *Troia 1987–2012: Grabungen und Forschungen I*,
Studia Troica Monographien 5, 694–727. Bonn, 2014.

- Verified how: all page ranges from **two independent bibliographies** — Kayan
  2019's own reference list and Zangger & Mutlu 2015, 576–77. The titles and
  pages are therefore solid; **the contents are not**, except where §1.9 quotes
  them.

### 1.6 Brückner, Vött, Schriever and Handl 2005 — open access, and the best single entry point

**Claim (read in full).** Over **50 m of sedimentary strata** between the Sigeum
ridge to the west and the Hisarlık and Yenikumkale cuestas to the east record "a
marine embayment, coastal swamps, coastal barriers and lagoons as well as
backswamps, floodplains, river channels and marshes." **"The Holocene
transgression reached ca. 17 km inland up to the area immediately northwest of
Pınarbaşı."** The interpretation rests on **roughly 250 drilled cores** in the
floodplain. There are **two scenarios from the same cores**: Kayan et al. 2003
(delta passes the city soon after 2200 BC, distance to the coast increasing
through Troia IV–VIIa) and Kraft et al. 2003a (bird's-foot delta in a quiescent
embayment until c. 0 BC/AD). "**Strabo (13.1.31 and 13.1.36) mentions the distance
between Troia and the so-called Achaian harbour during the 'Troian War' as 20
stades (ca. 4 km). The best candidate for a natural harbour at that time is the
present-day Kesik plain, a former marine embayment on the eastern slope of Sigeum
ridge. Strabo mentions that by then the distance from the city to the sea was 6
stades (ca. 1.2 km), half the distance during his own times.**"

- Citation: Brückner, Helmut, Andreas Vött, Armin Schriever, and Mathias Handl.
  "Holocene Delta Progradation in the Eastern Mediterranean — Case Studies in
  Their Historical Context." *Méditerranée* 104 (2005): 95–106.
  https://doi.org/10.4000/mediterranee.2342
- Authority: **geometry** (50 m of strata, 17 km, 250 cores, the stade
  conversions); **identification** (Kesik as harbour candidate, at second hand
  from Kraft); **prose** (the two-scenario framing).
- Verified how: full text read in-browser at
  [journals.openedition.org/mediterranee/2342](https://journals.openedition.org/mediterranee/2342?lang=en)
  (§§14–21 and the Fig. 3 caption). The site is behind a bot filter — `curl`
  fails, a real browser session works.
- **This is the citation to lean on** for the two-camp structure, because it is
  open, peer-reviewed, and written by someone in neither camp's excavation.

### 1.7 Two different Brückners — do not merge them

**Claim.** *Alfred* Brückner (Dörpfeld's collaborator) published "Das Schlachtfeld
vor Troja," *AA* 26 (1912): 616–33, and "Forschungsaufgaben in der Troas," *AA* 39
(1925): 230–48, and it is he who drew attention to the marshes on the west side
of the plain and to **two artificial cuts through the Yeniköy ridge** connecting
them to the Aegean, and who proposed that the Kesik plain (also called the Lisgar
marsh — **= Ilıca**, per Cook 1973, 166; naming note at §1.9, added 2026-07-30)
was the harbour basin of classical **Sigeion**. *Helmut* Brückner is the modern
geoarchaeologist of §1.6.

- Citation: Brückner, Alfred. "Forschungsaufgaben in der Troas." *Archäologischer
  Anzeiger* 39 (1925): 230–48, esp. 246.
- Authority: **identification** (Sigeion's harbour) and **geometry** (the two
  cuts), both at second hand.
- Verified how: Zangger & Mutlu 2015, 562 and fn. 19, 22 (Turkish; translated by
  me). The 1925 article itself is unseen; it is pre-1931 and therefore PD in the
  US, so it is worth finding.
- Consequence: the handoff's dossier row says "Brückner and collaborators".
  **Both** Brückners are relevant, for different things. `TROAD-SOURCES.md` §D
  already credits "Brückner's topographical/geological treatment of the plain" in
  Dörpfeld 1902 — that is Alfred.

### 1.8 Sea level in the NE Aegean — where Kayan's Bronze Age fall comes from, and what the modern databases say

**Claim (provenance of the fall).** Kayan's Bronze Age sea-level fall is not
derived from the Trojan cores. He takes **Dieter Kelletat's eustatic curve for the
younger Holocene in the eastern Mediterranean**, assumes mid-Holocene sea level
slightly above and then at the present level, and infers that sea level **must
have fallen about 2 m between 3000 BC and 1000 BC**; he then reads that fall as
having accelerated the delta's seaward growth, filling most of the plain in that
period.

- Citation: Kelletat, Dieter. "Eine eustatische Kurve für das jüngere Holozän,
  konstruiert nach Zeugnissen früherer Meeresspiegelstände im östlichen
  Mittelmeergebiet." *Neues Jahrbuch für Geologie und Paläontologie,
  Monatshefte* 6 (1975): 360–74. Applied in Kayan 2001, 310 (with fig. 321) and
  Kayan 2014, 709 (fig. 8); the acceleration claim at Kayan 1995, 217.
- Authority: **geometry**, at second hand, with a **methodological caveat that
  must travel with it**: a curve constructed in 1975 from eastern-Mediterranean
  shoreline indicators, applied to the Troad.
- Verified how: Zangger & Mutlu 2015, 568 and fnn. 49–52 (Turkish; translated by
  me).

**Claim (a second, older, and independent curve — full text, 2026-07-29).** Kayan's
fall is not the only one on the table, and it is not the first. Kraft, Kayan and
Erol 1980 carry their own relative curve, Fig. 3, credited to **"O. Erol,
unpublished data"** (ref. 17, p. 782), and their Fig. 6 panels state its values:
**+2 m at 4500 BP, present level at 3250 BP and 2000 BP.** That is a **2 m relative
fall between 4500 and 3250 BP, ending at today's datum** — the same magnitude
Kayan et al. 2003 print, twenty-three years earlier, from a different source, and
with the endpoint made explicit. The authors' own hedge is the wording our layer
notes should borrow: the curve "certainly is valid as a **local, relative,** sea
level curve for the Biga Peninsula" (Kraft, Kayan & Erol 1980, 781).
- Authority: **geometry** (the panel values), with the caveat that the curve itself
  is unpublished data by a co-author and has never, so far as this dossier can
  tell, been printed in full.
- Verified how: Fig. 3 and Fig. 6 read at 400 dpi in
  `research-cache/kraft-kayan-erol-1980-science.pdf` (§1.1).
- **Why it matters here.** It removes the LBA-sea-level statement from the
  "unverified" list (§6): we now have a published figure that names a Bronze Age
  sea-level position — *at present level* — rather than only a fall in metres with
  no datum. And it means the "2 m" is corroborated across two independent curves,
  while **"2 to 2.5 m" is corroborated by neither.**

**Claim (the modern regional constraint).** The current relative-sea-level
database for the northeastern Aegean **"further demonstrates a continuous Holocene
RSL rise in this portion of the Aegean Sea,"** with crustal subsidence of the
Samothraki Plateau and the North Aegean Trough controlling millennial-scale
change.

- Citation: Seeliger, Martin, Anna Pint, Peter Frenzel, Nick Marriner, Giorgio
  Spada, Matteo Vacchi, Sait Başaran, et al. "Mid- to Late-Holocene Sea-Level
  Evolution of the Northeastern Aegean Sea." *The Holocene* 31, no. 10 (2021):
  1621–34. https://doi.org/10.1177/09596836211025967
- Authority: **geometry** (a regional RSL constraint), abstract only.
- Verified how: verbatim abstract via
  [OpenAlex](https://api.openalex.org/works/doi:10.1177/09596836211025967);
  the SAGE page itself is bot-blocked.
- **Editorial consequence, and it is the honest way to word the barrier note.**
  The regional RSL record shows **rise, not fall**, through the Late Bronze Age.
  Kayan's 2–3 m is therefore best presented as a **local, relative** fall —
  which is exactly how Kayan 2019 frames it ("probably caused by the acceleration
  of the deltaic progradation"), and which is the 1980 authors' own word for their
  own curve (Kraft, Kayan & Erol 1980, 781) — and never as a regional sea-level
  event. A note that says "the sea fell 2–2.5 m" without that qualifier states
  something the NE Aegean database contradicts. **Sharpened (full text,
  2026-07-29):** say *from what to what*, not just how far. Kraft's Fig. 6 gives
  the endpoints — a mid-Holocene high about 2 m above today, back to today's level
  by Troy VI/VII — which is a claim the Seeliger database can live with, whereas
  "2–2.5 m below present in the Bronze Age" is not.

**Companion sources (unseen, for the curve itself):** Vacchi, Matteo, Alessio
Rovere, Alexandros Chatzipetros, Nickolas Zouros, and Marco Firpo. "An Updated
Database of Holocene Relative Sea Level Changes in NE Aegean Sea." *Quaternary
International* 328–29 (2013): 301–10. · Lambeck, Kurt, and Anthony Purcell.
"Sea-Level Change in the Mediterranean Sea since the LGM: Model Predictions for
Tectonically Stable Areas." *Quaternary Science Reviews* 24, nos. 18–19 (2005):
1969–88. · Fleming, Kevin, et al. "Refining the Eustatic Sea-Level Curve since the
Last Glacial Maximum Using Far- and Intermediate-Field Sites." *Earth and
Planetary Science Letters* 163 (1998): 327–42.
- Verified how: titles/pages from Kayan 2019's reference list and OpenAlex
  metadata. Values unseen.

### 1.9 Kesik and Beşik — the harbour hypotheses, and the numbers that constrain them

Everything in this section is from Zangger & Mutlu 2015, which is **open access
and Turkish**; I translated the Turkish and marked the English footnote quotes as
verbatim. The authors are advocates of the artificial-harbour hypothesis, so
their framing is partisan — but the measurements they report cut against their
own case, which is why they are usable.

- Citation: Zangger, Eberhard, and Serdal Mutlu. "Artificial Ports and Water
  Engineering at Troy: A Geoarchaeological Working Hypothesis." *OLBA* 23 (2015):
  553–89. https://dergipark.org.tr/tr/pub/olba/issue/47140/593189
  (open PDF: https://dergipark.org.tr/tr/download/article-file/763930)

**Claim — the Kesik cut, measured.** The "kesik" at Kesik is **400 m long, 50 m
wide and 30 m deep**, an artificial-looking ditch cutting the coastal ridge and
linking the Kesik plain to the Aegean shore. Kayan's drilling in it found a
**2–2.5 m colluvium fill** on its floor, and **the floor stands about 13.7 m above
sea level, some 150 m from the sea**, while the ridge surface there reaches 30 m.
So, deep as it is, the cut's floor is nowhere near sea level: **on either reading
below, it was never navigable.**

**Correction, 2026-07-30 (per `RESEARCH-TROAD-TOPOGRAPHY.md` §9.2, which read Cook
1973, 166–67 off the page images): the two authorities disagree on what the
feature IS, and this entry previously ran them together as if they agreed.**
Do not blend them again.
  - **Kayan: natural.** A **tectonic depression** (Kayan 2009, 124; Kayan 2014,
    723), later **widened by foot traffic** between coast and plain (Kayan 2014,
    724) — never a dug work at all.
  - **Cook: artificial, and "never completed" (his words).** "An artificial cut… a great
    V-shaped trench" (Cook 1973, 166); his verdict, verbatim: "**It seemed to us
    clear that the work was never completed**" (167). **A tectonic depression
    cannot be unfinished** — Cook's sentence presupposes a work in progress, which
    is exactly what Kayan's reading rules out. **The "Cook 1973, 167" citation
    itself is accurate** — Cook does say the work was never completed, on that
    page, in those words (near-verbatim: "never finished" vs. "never completed").
    What was wrong was presenting his artificial-cut, abandoned-work reading and
    Kayan's natural-depression reading as compatible attributes of one feature,
    rather than as rival origin theories.
  - **Cook's own purpose-and-date guess is late Roman, and applies only under his
    own artificial-cut reading — never under Kayan's, and never as Bronze Age
    harbour engineering.** "Drainage seems the more plausible solution", and his
    suggested occasion is "the foundation of Constantine's new city" — i.e.
    **fourth-century AD** (Cook 1973, 167). The harbour reading belongs to
    Brückner's canal theory, which Cook reports and doubts on the cost of the
    spoil; **Cook may not be cited in support of any Bronze Age harbour claim
    at Kesik.**

**Cook's vertical figure independently brackets Kayan's — corroboration by an
early observer, not a second measurement.** Cook, by eye in the field in the
1960s: the floor is "**perhaps 12–15 m. above sea level**" (Cook 1973, 166).
Kayan's later drilling: **13.7 m**. 13.7 sits inside Cook's bracket. **Record
both; keep Cook's "perhaps"** — do not present the two as independent
measurements of the same kind.

- Authority: **geometry** (400 × 50 × 30 m; floor at 13.7 m a.s.l.; 150 m from
  the sea) — **Kayan's and Zangger's figures, never Cook's**: Cook gives no
  length, width, or depth, only the two figures above; **identification**, but a
  **contested** one — Kayan's natural/tectonic reading and Cook's artificial-cut
  reading are mutually exclusive, not complementary.
- Verified how: Zangger & Mutlu 2015, 565 and 569, fnn. 36–37, 57–59 (Turkish;
  translated by me), for Kayan's reading and the 400×50×30 m / 13.7 m / 150 m
  figures. For Cook: Grade A, read off `research-cache/page-captures/cook-p165.png`,
  `cook-p166-kesik-cut.png`, `cook-p167-kesik-cut.png`, per
  `RESEARCH-TROAD-TOPOGRAPHY.md` §9.2. **Crop caveat:** those captures lose the
  last ~6–8 printed lines of every page, so the earthquake theory's proponent
  (foot of 166) and the trough's westward, seaward descent are not verified
  here.

**Naming note, added 2026-07-30 (`RESEARCH-TROAD-TOPOGRAPHY.md` §9.2):** the Kesik
plain, the Lisgar marsh (§1.7), and **Ilıca** are **one basin under three names**.
Cook, independently: "east of it [Kesik Tepe] Spratt's map shows a large marsh
(Lisgar, = Ilıca); it now seems to be drained and cultivated" (Cook 1973, 166;
Grade A). Use whichever name a source uses, but do not treat a change of name as
a change of feature.

**Claim — the Kesik plain.** The basin is **about 800 m wide**, bounded in places
by anomalously steep water-cut cliffs (Kayan 2009, 108 fig. 3); a lake sometimes
forms in it in winter, reaching the cut. Radiocarbon on marine shells puts its
**silting up before 1300 BC** (Kayan 2001, 313; Kayan 2009, 105). Kayan's own
verdict, verbatim in English: **"Yeniköy and Kesik bays could not have been used
as harbours during the Later Bronze Age, especially during Troia VI"** (Kayan et
al. 2003, 400), and there is **"no evidence"** that the natural bays along the
western margin of the Troian bay were developed as harbours (Kayan et al. 2003,
401). Elsewhere he writes the opposite mood: **"One can easily imagine that the
Kesik plain could have been an excellent harbor which was connected to the Aegean
Sea by the Kesik 'canal'"** (Kayan 2014, 723).
- Authority: **geometry** (800 m; pre-1300 BC siltation) and **identification**
  (not an LBA harbour).
- Verified how: Zangger & Mutlu 2015, 566 and 569–70, fnn. 37, 60–65 — the two
  English quotations are printed verbatim in his footnotes; page numbers are his.
- **This is a head-on contradiction with §1.4**, where Kraft et al. take the Kesik
  plain as the best harbour candidate at c. 1200 BC. Both cannot be drawn. Say
  whose it is, or draw neither. **And it is now a four-cornered one — see the next
  block, which is the *Geology* paper's own answer and is a third thing again.**

**Claim — Kesik as the ACHAEAN WALL AND DITCH, first-hand, and it is not a harbour
claim at all** (2026-07-30, from the full text of the 2003 *Geology* paper, §1.3).
Verbatim and entire, p. 166, col. 1:

> "The Kesik cut, a great wall and ditch (Kayan, 1995), was proposed by Nestor:
> Il.7, 336–343, 'And let us build near it a lofty fortification as a protection
> for the ships and ourselves . . . not far away, let us dig a deep ditch to hold
> back horses and fighting men so that the stout Trojan battle line may not
> overwhelm us.'"

They continue with *Il.* 12.50–54 (Hector's horses balking at the ditch's edge) and
16.370–77 (chariot poles snapped in it) as confirmation. **That is the whole of
what this paper says about Kesik.** The word "harbour/harbor" is never applied to
it; the Kesik plain is not proposed as a basin; there is no channel, no entrance, no
slipway.

- Authority: **identification**, and a startling one: the Kesik cut = the Achaean
  fortification of *Iliad* 7. Sourced to **Kayan 1995**, whose title is "The Troia
  Bay and *supposed* harbour sites in the Bronze Age" — i.e. the paper credits the
  wall-and-ditch reading to the very publication in which Kayan is dismantling the
  harbour readings. **Check that against Kayan 1995 itself before repeating it**
  (§5 item 6): the tectonic-depression reading this dossier has from Kayan is cited
  to 2009 and 2014, not 1995, so what 1995 actually says about Kesik is still
  unread here.
- **Geometry as drawn** (measured off Figs. 4 and 5, §1.3a; relative to the Troy
  dot, which is the only registration these plates support): a **ladder-hatched
  band across the neck of the Sigeum ridge, ~5.35 km due west of Troy (bearing
  270°), ~0.6 km long and ~0.33 km wide**, its western end on the Aegean shore and
  its eastern end on the shore of a small **enclosed inner basin** that carries a
  **3400 yr BP** date and whose nearest point to Troy is 3.99 km at bearing 284°.
  It is labelled "Kesik cut" on Fig. 5 and "**Kesic** cut" on Fig. 4 — one feature,
  two spellings, in one paper.
  - **The drawn band is a symbol, not a survey.** Against the measured cut (400 ×
    50 m, §1.9 above) the figure is ~1.5× too long and ~6× too wide. And its
    plotted latitude sits ~2 km north of the modern Kesik/Kesiktepe locality, which
    is inside the sheet's known registration error (§1.3a) but is one more reason
    not to lift a coordinate from it.
  - **It is drawn on the 2000 BP plate as well as the 3250 BP plate.** So on the
    paper's own maps the cut exists in both periods.

**The contradiction, sharpened. Four positions, three of them published in 2003,
and İlhan Kayan is a co-author of three of the four.**

| who | what Kesik is | when |
|---|---|---|
| Kraft, Kayan, Brückner & Rapp **2003a** (Springer chapter, §1.4) | the **best candidate for a natural harbour** at the time of the war — the Kesik plain as a former marine embayment | c. 1200 BC |
| Kraft, Rapp, Kayan & Luce **2003b** (*Geology*, this block) | the **Achaean wall and ditch** of *Il.* 7.336–43 — a fortification, drawn across the ridge neck | c. 1250 BC |
| Kayan et al. **2003** (§1.9) | **not usable at all**: "Yeniköy and Kesik bays could not have been used as harbours during the Later Bronze Age", silted before 1300 BC, "no evidence" of harbour development | — |
| Cook **1973**, 166–67 (§1.9) | "an artificial cut… never completed", purpose-guess **drainage**, occasion-guess Constantine's new city | **fourth century AD** |

Two things follow, and neither may be smoothed over:

1. **2003b puts a Late Bronze Age military earthwork exactly where Cook puts an
   unfinished late-Roman drainage trench.** Same feature, same ground, ~1,600 years
   apart, and neither cites the other. This is the sharpest single conflict in the
   dossier.
2. **Kayan is the common author, and his three 2003-vintage positions do not
   reconcile.** He is credited in 2003b for "a great wall and ditch"; he is
   co-author of 2003a's harbour candidate; and he is lead author of the 2003 paper
   that says the bays "could not have been used as harbours". Do not write "Kayan
   thinks" without a year and a page. Do not write "Kraft et al. 2003" without the
   letter (§1.4).
3. **What we may draw.** Nothing at Kesik on a *geographic* plate. If Kesik appears
   at all it is on a **schematic** plate, labelled with whose reading it is and
   dated, at tier `speculative`, with the four-way disagreement stated. A feature
   whose own excavator-adjacent authorities cannot agree whether it is natural,
   Bronze Age military, Bronze Age maritime or late-Roman civil engineering is not
   map-ready.

**Claim — the Yeniköy plain and canal.** The Yeniköy canal, east of Beşik Bay,
joins the Troy plain to the Yeniköy plain; cores show that marsh **was a bay until
the Early Bronze Age**, and was later flooded as the coast prograded, fed also by
the Pınarbaşı stream that rises at the southern end of the plain (Kayan 1995,
220). Kayan reads the Yeniköy cut as made in bedrock **to bring fresh water to
the Beşik plain** (Kayan 1995, 221); Korfmann dated the canal firmly to the 18th
century AD (Korfmann 1993, 28), a dating already disputed in the 1790s.
- Authority: **identification** and **prose**; the dating is contested.
- Verified how: Zangger & Mutlu 2015, 565 and 568–69, fnn. 36, 54–56.

**Claim — Beşik Bay as the harbour.** The Beşik hypothesis is old and was the
project's working assumption from the start. Verbatim in English: **"One must
seriously consider the possibility that the Greek fleet was beached in the
embayment at Besika"** (Kraft, Kayan & Erol 1982, 40) and **"It is obvious that the
Besik bay could have been used as a harbor"** (Kayan 1991, 91). Kayan drilled
**318 holes between 1977 and 2006**, initially to 75 m depth and after 1988 to
20.5 m with a Unimog rig (Kayan 2006, 322–23; Kayan 2014, 703). Zangger's
criticisms: core descriptions were purely sedimentological and not to
international colour/grain-size standards (Kayan 2006, 324), and the ceramic
fragments in the cores were never published.
- Authority: **identification** (Beşik as candidate harbour); **geometry** for the
  coring campaign's size and depth.
- Verified how: Zangger & Mutlu 2015, 567–68, fnn. 43–47 — English quotations
  verbatim from his footnotes.
- **First-hand, and two years earlier than the 1982 quotation (full text,
  2026-07-29).** The Beşika claim does not need Zangger's footnote any more.
  Kraft, Kayan and Erol 1980, 782 state it themselves: "Thus one might suggest
  that **the Beşika embayment was indeed the site of the Achaean camp**", with
  the battlefield axis "to the south of Troy and to the east of the Beşika
  embayment", and the bay itself "possibly an indentation approximately **2 km
  inland**" at 4000–5000 BP. They rest it on Mey's 1920s excavations on the Beşika
  plain (Mey, *Das Schlachtfeld vor Troja*, 1926 = their ref. 18), which found
  "shoreline sediments overlying Early Helladic artifacts several kilometers
  inland, slightly above present sea level", and they add the tectonic caveat that
  makes those sediments readable at all: "The Biga Peninsula is tectonically
  active and therefore minor coastal uplift is likely. Therefore, these hypotheses
  now merit reevaluation." **Cite 1980, 782 rather than 1982, 40** — same claim,
  a source we have actually read.
- **And note where this leaves Kraft.** In 1980 Kraft's camp is Beşika; in 2003a
  (§1.4) it is the Kesik plain. Whoever writes a plate note saying "the sheet draws
  Kraft" must name the year, because the two Krafts put the fleet on opposite sides
  of the Sigeum/Yeniköy ridge.

**Claim — the artificial-port hypothesis, stated as its authors state it.** From
the English abstract: Troy "may well have possessed an artificial
fresh-water-filled port basin that was connected to the Aegean Sea via a dry
slipway. By being pulled over 150 meters of land and sliding down another 300
meters, eastbound vessels would have avoided a 50 kilometer-long detour all the
way around the island of Gökçeada."
- Authority: **prose**. It is offered as a "working hypothesis" in its own title.
- Verified how: English abstract read verbatim in the open PDF, p. 553 (first
  content page; the OLBA XXIII table of contents places the article at 553).
- **Correction to `TROAD-SOURCES.md` §A.** That file says the hypothesis "proposes
  an artificial rectangular basin c. 330 × 230 m **at Kesik**". The 330 × 230 m
  rectangular basin in this paper is at **PYLOS** — the Port of Nestor, ~500 m in
  from the Ionian shore, beside the Osmanağa lagoon, now under the Costa Navarino
  golf resort (Zangger & Mutlu 2015, 557–58). Pylos is the *analogy* from which
  the Troy hypothesis is generalised. No 330 × 230 m basin is claimed at Kesik.
  The number must come out of the Troad file.

**Claim — the ditches south of the citadel** (adjacent, and useful to
`RESEARCH-CITADEL.md`). Magnetometry found at least two artificial ditches on the
plateau south of the upper city, each **about 4 m wide and 2–3 m deep**; the inner
one lies **about 400 m south of the Troy VI citadel wall, at about 25 m above sea
level**. Too narrow for Bronze Age ships, so unconnected with any hydraulic
system.
- Citation: Becker, Helmut, and Hans Günter Jansen. "Magnetische Prospektion 1993
  der Unterstadt von Troia und Ilion." *Studia Troica* 4 (1994): 105–14; Jablonka,
  Peter, Heike König, and Simone Riehl. "Ein Verteidigungsgraben in der Unterstadt
  von Troia VI." *Studia Troica* 4 (1994): 51–73, at 52.
- Authority: **geometry**, second-hand.
- Verified how: Zangger & Mutlu 2015, 566–67, fnn. 41–42.

### 1.10 Strabo 13.1.31 and 13.1.36 — the ancient measurement, and an ancient lagoon

These are PD and directly quotable on the site.

**Claim (13.1.36).** "If any one shall say that the Naustathmus is the present
harbour of the Achæans, he must mean a place still nearer, **distant about twelve
stadia from the sea, which is the extent of the plain in front of the city to the
sea**; but he will be in error if he include (in the ancient) the present plain,
**which is all alluvial soil brought down by the rivers**, so that **if the interval
is 12 stadia at present, it must have been at that period less in extent by one
half**." Also in the same section: "**the Naustathmus is near Sigeium**. The
Scamander discharges itself near this place **at the distance of 20 stadia from
Ilium**." And on the Achaean wall: "or perhaps no wall was built and the erection
and destruction of it, **as Aristotle says, are due to the invention of the
poet**."

- Citation: Strabo, *Geography* 13.1.36, trans. H. C. Hamilton and W. Falconer
  (London: George Bell & Sons, 1903),
  [Perseus](https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.01.0239%3Abook%3D13%3Achapter%3D1%3Asection%3D36).
- Authority: **geometry** for the stade figures (as ancient testimony, not
  survey); **prose** for the alluvium and the Aristotle remark.
- Verified how: read in full in-browser on Perseus.
- **The arithmetic, done here so nobody re-does it wrong.** At 177.6 m to the
  stade, 12 stades = 2.13 km and 6 stades = 1.07 km; at 185 m, 2.22 km and
  1.11 km. Brückner (§1.6) rounds the 6 to "ca. 1.2 km" and the 20 to "ca. 4 km".
  So **"of the order of 1 km from the citadel to the Bronze Age shore" is the
  ancient constraint**, and it is the only number in this whole dossier that
  independently bears on our bay-head position.
- **Where the stade readings enter the literature — SETTLED 2026-07-30 (§1.3).**
  The dossier's guess was right: **Kraft, Rapp, Kayan & Luce 2003, 165–66** is
  where 13.1.36's numbers get printed with metric conversions and drawn as arcs.
  The paper prints **Luce's own translation** of 13.1.36 (attributed "(J.V. Luce)"),
  with two editorial insertions that are Luce's, not Strabo's — "the distance is now
  **[ca. 0 B.C.]** 12 stades then **[ca. 1250 B.C.]** it would have been half that"
  — and converts at **200 m to the stade**: 12 → 2400 m, 6 → ~1200 m, 20 → 4000 m.
  Two attribution points that matter:
  - **The 20-stades-to-the-camp reading is the PAPER'S, made through Luce's
    translation — but the printed clause itself is ambiguous** (precision at
    Grok verification, 2026-07-30). Luce's rendering: "The ‹Homeric› ship
    station is actually close to Sigeion, and the ‹main› mouth of the Scamander
    is also nearby, being 20 stades distant from Ilion" — where the relative
    clause sits next to the Scamander's mouth, much as in the PD
    Hamilton–Falconer translation (above). What attaches the 20 stades to the
    camp CLEANLY is the paper's own authorial gloss (p. 166: "the Homeric Greek
    ship station and camp were actually 20 stades (4000 m) from Ilium") and the
    Fig. 4 caption. **So the 20-stade camp distance is the 2003 paper's
    reading, built on Luce's version — cite it to the paper, not to the
    translation's grammar.** §6's second entry stands, now with a page.
  - **The paper's own figures are drawn on a ~181–187 m stade, not the 200 m stade
    of its text** (§1.3a). So even inside this one paper the conversion is not
    stable. Never write "Kraft et al. give 1.2 km" as though it were a measurement.
- **One attribution to keep straight.** Brückner reports Kraft et al. as taking
  Strabo's 20 stades for the Troia-to-Achaian-harbour distance and citing
  13.1.31 + 13.1.36. In the PD translation, §31 gives **no distance at all** and
  §36's 20 stadia is stated of **the Scamander's mouth** ("near this place" being
  the Naustathmus). The 20-stade harbour figure is therefore an *interpretation*
  of §36, not a quotation of it. Do not print it as Strabo's own words.

**Claim (13.1.31), and it is a gift to the barrier and lagoon layers.** "After
Rhœteium is Sigeium, a city in ruins, and the naval station, the harbour of the
Achæans, the Achæan camp, **the Stomalimne, as it is called**, and the mouths of
the Scamander. The Scamander and the Simoeis, uniting in the plain, bring down a
great quantity of mud, **bank up the sea-coast, and form a blind mouth,
salt-water lakes, and marshes**."

- Citation: Strabo, *Geography* 13.1.31, trans. Hamilton and Falconer (1903),
  [Perseus](https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.01.0239%3Abook%3D13%3Achapter%3D1%3Asection%3D31).
- Authority: **identification** (Stomalimne as a named lagoon between Sigeium and
  the Scamander mouths) and **prose** (barred mouth, salt lakes, marsh).
- Verified how: read in full in-browser on Perseus.
- **Use.** The barrier–lagoon–marsh complex we draw is not only a modern
  reconstruction from cores: a first-century observer describes a **barred
  ("blind") river mouth with salt lakes and marshes** on this coast, and names the
  lagoon. That belongs in the layer note, and *Stomalimne* is a candidate
  gazetteer record at tier `traditional` (Strabonic, post-Homeric — the name does
  not occur in the *Iliad*).

### 1.11 Luce 1984 — the dissent, read in full, and it is narrower and better founded than the abstract suggests

**The one-sentence version.** Luce accepts Kraft's shoreline entire and moves only
the camp: the fleet is beached on the **eastern flank of the Sigeum ridge, inside
the embayment, 4 to 5 km from Troy** (p. 41), looking south-east across salt water at a
citadel "**5 to 6 km across the expanse of water to the south-east**" (p. 35);
the Scamander runs **between camp and city**, which is "a cardinal point in my
thesis" (p. 39); and the fighting axis therefore runs **east–west**, not
north–south.

- Citation: Luce, J. V. "The Homeric Topography of the Trojan Plain
  Reconsidered." *Oxford Journal of Archaeology* 3, no. 1 (1984): 31–43.
  https://doi.org/10.1111/j.1468-0092.1984.tb00114.x
- Authority: **identification** (camp position; fighting axis; Kallikolone,
  Thymbra, the Aisyetes tumulus, the fort of Heracles); **geometry** for the
  camp-to-Troy distances and the strip marked on his Fig. 1; **prose** for the
  Homeric argument that occupies most of the article.
- Verified how: full text and both figures read page by page in the scan cached at
  `research-cache/luce-1984-oja.pdf` (13 pp., 2026-07-30). Page numbers below are
  the journal's own, 31–43. Supersedes the abstract-only entry this section
  carried on 2026-07-29; the abstract is still quoted in §1.11a below because two
  of its numbers do **not** match the body.

**Where he puts the shore — and it is not his line.** He does not reconstruct a
shoreline. He takes one: "in the time of Troy VI/VII, c 3,250 years BP, the
shore-line still ran somewhat west by south of the city, and the inhabitants
looked across a salt-water bay to the Sigeum ridge (Fig. 1)" (p. 32), and Fig. 1's
caption says exactly where that comes from — "**After Kraft, Kayan and Erol 1980,
fig. 2 with additions from fig. 6**" (p. 33). The evidence is Kraft's: nine
bore-holes, the reconstruction published in Rapp and Gifford's 1982 supplement to
Blegen's *Troy*, and the assumption "that the sea-level of the Aegean stabilised
about 5,000 years ago" (p. 31). His own additions to the map are the camp, Mey's
trenches, and the Homeric names. **So there is no independent "Luce shoreline" to
draw as an alternative to Kraft's** — the two are one line. See §4 item 12: this
kills the shoreline half of our plate note's Kraft-versus-Luce contrast.

**Where he puts the camp, in his own words.** Aristarchus' `προκρόσσας`
(scholion on *Il.* 14.35) has the ships hauled up "one above the other *like the
steps of a ladder* (klimakedon)" so that the Ship Station looked "*like the
auditorium of a theatre (theatroeides)*"; since "the alluvium itself is naturally
flat," a slope steep enough for that "is forced to look to the slopes that flank
the plain" (p. 36). Hence: "**the ships were drawn up on land on a narrow front
somewhere along the line of the Sigeum ridge**. I have marked what seems to me the
most likely stretch by X X on Fig. 1. Its northern end is marked by a break in the
line of the ridge just south of the area christened 'Spratt's plateau' by Cook
(1973, 165). Its southern flank could easily be defended by a wall and ditch as in
the Homeric tradition. The whole strip between the alluvium and the higher ground
of the ridge is marked as marshy on the American-Turkish maps, but drainage must
have been better before the advance of the alluvium" (p. 36). The position is
reached by elimination and he says so: the received north-shore camp "is clearly
untenable in the light of the new findings," Beşika is unsatisfactory, the
embayment's south side "brings it too close to Troy besides putting it athwart the
Scamander delta," so "**by a process of elimination, if nothing else, one is
forced back on the western side of the embayment as the only feasible location**"
(p. 41). He also rejects the far-north option in the same breath — ships "beached
well to the north close to Sigeum point" would "come into conflict with the
Homeric indications about the distance between Troy and the ships" (p. 41), which
is Brückner's Sigeion harbour ruled out by a Homerist on Homeric grounds.

**His distances, all three of them.** 4–5 km camp-to-Troy (p. 41, in the Beşika
comparison); 5–6 km citadel-to-fleet across the water (p. 35); and the abstract's
"about four miles west of Hisarlik" (p. 31), which is ~6.4 km and agrees with
neither. **Record the spread; do not average it.** The body figures are the ones
to use: they are the figures he argues *with*, and they are what Fig. 1's X X
strip is drawn against. Our own sheet then does something useful — see §3.6, which
measures Luce's figures against the `shore-bronze` vertices the plate already
carries. Short version: his 4–5 km lands on the southern half of the ridge branch
we already draw, so **his camp can be shown as an extent along an existing line
without inventing a coordinate**. What is still not locatable is the strip's two
ends: the northern one depends on Cook 1973, 165's "Spratt's plateau" and the
southern on a wall-and-ditch line he proposes without evidence, and we have not
seen Cook. **Anchor it as an extent, never as a pin, and never from the "four
miles".**

**Why he rejects Beşika — three objections, one of which is a measurement.** He
quotes Kraft, Kayan and Erol 1980, 782 exactly as §1.9 does ("the Besika
embayment of 4,000 to 5,000 years ago was possibly an indentation approximately
2 km. inland"; "it was the site of the Achaean camp"), notes the hypothesis is
Alfred Brückner's of 1912, that Oscar Mey's 1924 trenches with Dörpfeld and Schede
"revealed some pottery, including three prehistoric sherds possibly dating from
the 3rd millennium BC, but nothing to confirm his Achaean camp hypothesis," and
that Charles Vellay's rebuttal was in Cook's opinion successful "according to the
rules of the game" (Cook 1973, 170 n.3) — then adds his own three: "**1) It is too
exposed on the side of the Aegean for a permanent camp and ship station. 2) It is
too far from Troy (8½ km as opposed to 4 to 5 km for the Sigeum ridge site). 3)
Access from it to the Scamander plain is not good, lying first across a low ridge
and then across a wide expanse of low-lying and marshy ground**" (pp. 40–41).
Objection (2) is the substantive one and it is a distance, not a taste. Note
against §1.9: Cook, whom Luce is otherwise following, is on the *other* side here
— "Besika Bay must be a very much more satisfactory situation for the Homerists"
(Cook 1973, 171–2) — and Luce says so and disagrees (p. 40).

**How he uses Kraft's geology, and where he refuses it.** The whole article is
written as a response to the 1980 paper's own invitation: Kraft's team asked
Homeric scholars to "reconsider some of their interpretations in the light of the
geological and geographical analysis presented here," and Luce says "this is the
task attempted in the present paper" (p. 32). He takes the shoreline series as
authoritative — "The new findings are totally at odds with the received view"
(p. 32) — and he quotes 1980's floodplain morphology approvingly as the physical
explanation of Homer's `θρωσμὸς πεδίοιο`: "The present Scamander River meanders
across a long narrow floodplain with the highest elevation in the middle of the
plain … and the lowest elevation on the eastern and western flanks" (Kraft et al.
1980, 779, quoted p. 40). He closes by setting 1980, 782's "It is unlikely that we
will discover the many ancient occupation sites that must exist on the modern
floodplain. They are deeply buried …" beside *Il.* 12.24–33, and concludes that
"all traces of the fortified camp were in fact covered up by flooding and
aggradation in the centuries after the fall of Troy" and were invisible already in
Homer's day (p. 42).

But he **separates the shoreline from the rivers**, and this is the one place he
criticises the geology rather than deploying it. Kraft's Troy VI/VII plan "moved
[the Scamander] further to the west and there is no junction with the Simoeis. **It
is not clear to me whether their core data determine the course of the rivers at
different epochs as accurately as they appear to determine the shore-line**"
(pp. 38–39). His disjunction is stated honestly: if the LBA river bed is "somewhat
notional," follow the Eastern theory (the Kalifatli Asmak line, close under Troy);
if Kraft's course is firm, then the river shifted east between the war and Homer,
"as it certainly was seen by Strabo's informants" (p. 39). **Useful for us:** a
Homerist who accepts these cores treats Kraft's *river* lines as the soft part of
the reconstruction. Our `karamenderes-bronze`/confluence posture — not marking
Homer's 5.774 confluence at all — is the same judgement.

He also **flattens Kraft's sea level**. "Assuming that the sea-level of the Aegean
stabilised about 5,000 years ago" (p. 31) is not what the 1980 paper's Fig. 6
prints: +2 m at 4500 BP falling to present level by 3250 BP (§1.8, §2). The 2 m
fall on which our barrier and lagoon depend is absent from Luce's premise.
Contradiction recorded; it does not touch his camp argument, but it means Luce
1984 cannot be cited for anything about sea level or the barrier.

**What his Fig. 1 commits to a position** (p. 33; sketch map, scale bar 0–3 km /
0–2 miles, north arrow, four area fills — low plateau, high plateau, Trojan plain,
marsh to-day). Two reconstructed water lines, both labelled in the legend as
Kraft's: "Reconstructed outline of inner shore of bay **in time of Troy VI/VII**"
(dotted) and "…**in time of Strabo**" (barred). And these named features, each of
which is a drawing claim:

| on Fig. 1 | what it commits | Luce's own hedge |
|---|---|---|
| **X X**, "Projected site of Achaean Camp" | a strip, not a point, on the ridge's eastern flank | "what seems to me the most likely stretch" (36) |
| **Wall** | the camp's south flank, a wall-and-ditch line | "could easily be defended" (36) — proposed, not evidenced |
| **FORD** | mid-plain, on the road, near a ford that still exists | "close to my 'Homeric' ford" (38) |
| **Ilos ?** | east of the ford, city side of the river | question mark on the map |
| **Aisyetes ?** | "the neighbourhood of Old Kalifatli," roughly halfway across the plain, where "remains of a tumulus have been reported" (41, citing Cook 1973, 105). NB the Old-Kalifatli name is PROSE (p. 41); the map label itself is just "Aisyetes ?" | "my tentative placing" + question mark |
| **Throsmos** | between the camp's wall and the ford — i.e. **west of the Scamander**, on the camp side | no hedge; he argues it from 10.160, 11.56, 20.3 |
| **Beşik T = FORT OF HERACLES** | the tumulus on the highest point of the Sigeum ridge, following Leaf 1912, 43–4 | "may be located, as Leaf suggested" (38) |
| **Kara Tepe = KALLIKOLONE** | 9 km east of Troy, following Spratt and Forchhammer (Cook 1973, 111) | "generally taken to be" (37) |
| **THYMBRA** | near the R. Kemer, south-east of Hisarlık | "though no ancient site has been definitely found" (37) |
| **M M**, Mey's trenches | the 1924 Beşika excavation, plotted so it can be seen to have found nothing | — |
| **R. Simoeis** = Dümrek | accepted: "there is no good reason to doubt its identification with the Dümrek" (38) | — |
| Sigeum ridge's "three distinct crests" between Yenişehir and Beşika Burnu, cliffs "certainly sea-beaten" (37, citing Cook 1973, 165–9) | the physical basis for reading *Il.* 20.49–50 of his camp | — |

His **Fig. 2** (p. 34) is the position he is rejecting: "The Plain of Troy with
Leaf's identifications … (After Leaf 1912, map facing p. 44)," with GREEK CAMP and
"Achaean Harbour" strung along the Hellespont. Worth knowing that the features our
gazetteer holds — `wall-of-heracles`, `tomb-of-ilos`, `tomb-of-aesyetes`,
`ford-of-the-scamander`, `callicolone`, `thymbra` — are on **both** of his maps:
the feature list is Leaf's, and what Luce changes is where several of them sit and
which side of the plain the camp is on. `throsmos` and `stomalimne` are on the maps
but not in the gazetteer (the former is flagged as a gap by
`RESEARCH-POEM-TOPOGRAPHY.md` §4; the latter by §1.10 above).

### 1.11a The abstract, kept because two of its numbers are not the body's

"Homeric passages bearing on the location of the Achaean camp at Troy are
re-examined in the light of new scientific data on the time-scale for the
alluviation of the Trojan plain. The new data confirm the accuracy of Strabo's
account of the plain, and in particular of the shore-line having come close to the
Hisarlik site (*Novum Ilium*) in Hellenistic times. **In the era of Troy VI/VII,
c. 3,250 years BP, the shore-line appears to have run west by south of the site,
and a broad marine embayment lay between the city and the Sigeum ridge.** It is
therefore no longer possible to accept the received view (deriving from Schliemann
and Leaf) that the Achaean camp was sited on the present shore-line by the
Hellespont. **A new site is proposed for the camp on the lower slopes of the Sigeum
ridge about four miles west of Hisarlik.** It is argued that the indications in the
*Iliad* are not inconsistent with such a siting, and in fact suit it better than
the received view. This is shown with regard to the course of the Scamander,
evidently pictured by Homer as running between camp and city, and also with
respect to **the general axis of the fighting on the plain, which is indicated to
lie in an east-west rather than a north-south direction**. The Besika Bay site,
first proposed in 1912, is rejected as inconsistent with the Homeric data and
unsatisfactory in itself." (p. 31.)

Two discrepancies against the body, **recorded, not harmonised**:

1. **"About four miles west"** (~6.4 km) against **"4 to 5 km"** (p. 41) and
   **"5 to 6 km across the expanse of water"** (p. 35). Measured against the plate's
   own ridge line (§3.6), no point on the Sigeum ridge's eastern flank is four miles
   west of Hisarlık: the largest westward offset there is 4.91 km and the largest
   straight-line distance 5.95 km. Use the body figures.
2. **"East-west rather than north-south."** The body states the axis three ways:
   "a line running **south-west** from the hill of Hisarlik, and not north-by-west
   as required by the Leaf-Schliemann view" (p. 36), attributed there to Kraft et
   al. 1980, 776; "the generally **east-west** axis of the contest" (p. 38); and
   the abstract's east–west. Kraft, Kayan and Erol 1980, 782 give a fourth —
   "south of Troy and to the east of the Beşika embayment" (§1.9). Four statements
   of one bearing across two papers, spanning ~45°. A plate note may say "west or
   south-west of the city"; it may not print a degree figure.

### 1.11b Luce's Homeric passages, for the poem-topography lane

Every *Iliad* citation Luce argues from, in his order of use, so
`RESEARCH-POEM-TOPOGRAPHY.md` can cross-reference without re-reading the article.
(He uses no *Odyssey*; "these and all subsequent references in the text are to the
*Iliad*," n. 6.)

- **The camp's relation to the sea and the Hellespont** — 15.233 = 18.150 (the
  formulaic "flying they reached the ships and the Hellespont"); "on the shore of
  the sea" at 8.501, 13.682, 14.31, 19.40, 23.59, 24.12; 9.360 and 24.545 as
  "Hellespont" meaning the NE Aegean rather than the strait (p. 35).
- **Whether the poem knows a bay** — 21.124–25 (`halos eurea kolpon`), 2.560,
  18.140 (`thalasses eurea kolpon` of the open sea, which is why he declines to
  press the argument), 14.36 ("long mouth of the shore"). Verdict at p. 35: "this
  particular battle of texts remains drawn."
- **The approach** — 1.71 (the fleet coming "within Ilios"); 6.434, the city
  "most approachable," which he reads as "the apron-like plateau on its south-west
  flank" (p. 36).
- **The Ship Station's shape** — 14.30–36, with the scholion on 14.35
  (`prokrossas`, Aristarchus, `klimakedon`, `theatroeides`) and Herodotus 7.188
  (p. 36); 14.28 and 18.69 via Maclaren (n. 8).
- **The fighting axis** — 10.428–31 (Dolon: the allies "towards the sea" and "the
  station on the side of Thymbra"); 20.49–50 (Athena "now outside the wall by the
  ditch and now on the sea-beaten headlands"); 20.51–53 and 20.144–52 (Ares along
  the Simoeis at Kallikolone; the gods' stations as a matched pair; Poseidon at
  the fort of Heracles) (pp. 37–38).
- **The Scamander between camp and city** — 24.692–93 and 24.349–51 (Priam's
  journey and the watering halt); 21.1 (the rout escaping across the ford);
  5.773–74 (the confluence); 8.560–61 (the watch-fires "between the ships and the
  streams of Xanthos"); 10.415 and 10.416 (Hector's council at the tomb of Ilos,
  "far from the sea-surge"); 11.166–67 (past the tomb of Ilos in the midst of the
  plain); 16.376 and 16.394–98 (Patroclus cutting the Trojans off "between the
  ships and the river and the high wall") (pp. 38–39).
- **The throsmos** — 10.160, 11.56, 20.3 (p. 40).
- **The watch-post** — 2.791–94 (Polites on the tumulus of Aisyetes) (p. 41).
- **The camp's erasure** — 12.24–33, quoted at length as the article's last word
  (p. 42).
- Non-Homeric anchors: Strabo 13.1.31 (the blind mouth, lagoons and marshes),
  13.1.34 (Simoeis joining Scamander near Novum Ilium), 13.1.36 (the distance
  question, and Hestiaea's more deeply recessed bay, n. 4); Pliny *NH* 5.33
  (rejected, p. 41); Leaf 1912, 29–30, 43–44 and map facing p. 44; Cook 1973, 105,
  111, 117–22, 165–71, 294.

**What the article does *not* discuss, which matters for a citation we are already
printing:** the fig tree. No mention of `ἐρινεός`, of 6.433, of 11.167 as a
fig-tree passage, or of the two-fig problem, anywhere in 31–43. Nor the oak, the
Scaean Gate, the springs, or the chase-circuit. See §4 item 13.

### 1.11c The trajectory — Luce changed position twice, and the caption must say which one

Three positions, one man:

1. **1975 — the received view.** He says so himself, in a footnote: "I must admit
   to having followed it unquestioningly in my *Homer and the Heroic Age*, London
   1975, Fig. 95" (p. 42, n. 3).
2. **1984 — the Sigeum ridge's *eastern* flank**, as above.
3. **1998/2003 — the Sigeum ridge's *outer* (Aegean) flank, 20 stades, and Kesik as
   Nestor's ditch.** No longer second-hand: **the 2003 *Geology* figures are in
   hand (2026-07-30, §1.3, §1.3a) and they draw position 3.**

**Position 3, drawn, first-hand.** Figs. 4 and 5 both carry the label "Greek camp
and ship station" (Fig. 4 adds "ca. 3250 yr B.P.", an overlay on its Roman-era
sheet), with an arrow. Measured (§1.3a):

- The arrow tip lands on the **Aegean-facing, west coast of the Sigeum ridge**,
  ~0.5 km south of the Sigeum acropolis dot and ~0.7 km north of the Kesik cut, at
  **5.4 km from the Troy dot, bearing 279°**.
- The stretch it points at is **concave between two projections** — the Sigeum
  headland to the north, the headland at the Kesik cut to the south — and the paper
  says so, quoting *Il.* 14.30–36 ("the beach, though broad, could not contain all
  the ships… they ranged them in rows, and filled all the long mouth of the shore
  **between the enclosing headlands**") and adding: "**Note the embayment between
  the headlands as delineated by Luce (1998) based on Strabo's distance from Troy**"
  (166, col. 1). So the beach *is* Luce's, and it is Luce 1998's.
- **The Kesik cut closes the southern approach to it** — which is what makes the
  wall-and-ditch identification (§1.9) do work: the ditch protects the ships from
  the landward side.
- **The drawn camp does not satisfy the paper's own 20 stades.** 5.4 km is ~29
  stades at 185 m, ~27 at 200 m; the 20-stades arc on the same sheet has a radius of
  3.73 km. Strabo's naustathmon figure has never reached Sigeion and this paper
  inherits the problem rather than solving it. Record the arc *and* the arrow, and
  do not print "20 stades" as the plate's measured distance.

**So 1984 is not anticipated in 2003 — it is reversed, on the point Luce cared
about most.** 1984: fleet on the **inner, eastern** flank, *inside* the embayment,
4–5 km out, looking south-east **across salt water** at the citadel, with the
Scamander between camp and city ("a cardinal point in my thesis", p. 39). 2003: the
fleet is on the **outer, western** flank, on the open Aegean, with the whole ridge
between it and the bay — and the water it looks across is not the bay at all. The
2003 reference list **does not cite Luce 1984** (§1.3c). What survives from 1984 is
only the coarse claim that the camp is **west** of Troy and the battle axis runs
west-south-west, which 2003 states in its own words: the Trojan line "extended from
the sea in front of Troy southeastward, covering the possibility that the Greeks
would attack anywhere on the Scamander plain **from the west-southwest**" (166).

**And the harbour dissent of 1984 is vindicated by 2003b, not overturned.** The
*Geology* paper names **no harbour site**: its only positive statement is that the
whole embayment was "this long-term sheltered marine embayment" (164) — the shelter
*is* the bay, which is precisely Luce 1984's position (below). It is **2003a**, the
Springer chapter (§1.4), that puts the harbour at Kesik. So "Luce 2003 = Kesik
harbour" was wrong in the direction of the *Geology* paper and needs the letter as
badly as Kraft does.

**What 1984 contradicts in it** — four things, and they are the reason a caption
cannot treat "Luce" as one position:

- **No harbour, anywhere.** In 1984 the shelter *is* the bay: "Once established
  there they could look across the water to their objective with their rear
  protected by the Sigeum ridge. Given naval superiority their sea communications
  could not be cut" (p. 36). Fig. 1 marks no harbour; the word "Kesik" does not
  occur in the article; the only harbour on either of his maps is the "Achaean
  Harbour" of Fig. 2, which is Leaf's and which he is rejecting.
- **His own objection 3 to Beşika presses against the Kesik route.** Access "first
  across a low ridge and then across a wide expanse of low-lying and marshy
  ground" (p. 41) is a description of the Kesik saddle and the Kesik plain, and in
  1984 it is an argument *against* a camp there.
- **He rejects the embayment's south side outright** — it "brings it too close to
  Troy besides putting it athwart the Scamander delta" (p. 41). Kesik is at the
  ridge's southern end.
- **The main text extracts no stade figure from Strabo — but Note 5 does.** The
  body says only that "from Strabo (13, 1, 36) it appears that the distance
  question was also much discussed in Hellenistic circles" (p. 41) and declines to
  settle it. **His Note 5 (p. 43), however, reports the range in Strabo's
  Demetrius material: the distance "fell within the limits of 6 and 20 stades
  (1 to 3 km)"** — a report of the ancient debate's bounds, not a figure Luce
  adopts for his own camp. (An earlier draft of this entry claimed he prints no
  stade figure at all — corrected at Grok verification.) **Adopting 20 stades as
  a working number still enters with Luce 2003, not 1984** — which reinforces
  §6's second entry, now with the precision that 1984 already knew the 6–20 band.

**Caption consequence, revised 2026-07-30.** "Luce" on a plate must carry a year,
and now the years are separable on evidence:

- `Luce 1984` = camp on the ridge's **eastern** flank, inside the bay, **4–5 km**,
  **no harbour anywhere**, Kesik unmentioned.
- `Luce 1998, as drawn in Kraft et al. 2003b` = camp on the ridge's **outer,
  Aegean** flank in an embayment between two headlands, **5.4 km at bearing 279°**
  as plotted, **20 stades** asserted in the text, **Kesik = Nestor's wall and
  ditch**. First-hand from the figures (§1.3a, §1.9). Luce 1998 itself is still
  unread (§5 item 9).
- `Kraft et al. 2003a` (Springer, §1.4) = Kesik as **harbour**. Different paper,
  different claim, and it is the one the "Luce 2003 = Kesik harbour" shorthand was
  really pointing at.

Do not merge them, do not cite 1984 for a harbour claim, and do not cite the
*Geology* paper for a harbour site — it names none.

**Why the dissent still belongs on the page — restated, because the 2003 full text
moves it.** Luce is a co-author of the 2003 *Geology* paper (§1.3), so the
disagreement is internal to one project and to one man. Two parts of it now read
differently:

- **On the harbour, 1984 and 2003b agree, and it is 2003a that is the outlier.** The
  *Geology* paper's only sheltering claim is that the bay itself was a "long-term
  sheltered marine embayment" (164) — Luce 1984's position in geologists' words.
- **On the camp's *flank*, 1984 and 2003b disagree flatly**, east versus west of the
  ridge, and 2003b does not cite 1984. That is the live dissent, and it is now
  drawable: our own `shore-bronze`'s 20 m-contour branch carries the 1984 strip
  (§3.6), and the 2003b camp sits on the *other* side of the same branch.
- What both reject, with Kraft 1980 and 2003a, is the received Schliemann–Leaf
  north-shore camp (§1.1, §1.9, §4 items 10, 12).

- **Related, unseen:** Luce, J. V. *Celebrating Homer's Landscapes: Troy and
  Ithaca Revisited* (New Haven: Yale University Press, 1998); "The Case for
  Historical Significance in Homer's Landmarks at Troia," in *Troia and the
  Troad: Scientific Approaches*, 9–30 (Berlin: Springer, 2003). Also *Homer and
  the Heroic Age* (London: Thames & Hudson, 1975), Fig. 95 — the map he recants
  (p. 42 n. 3). One access note gained from 1984: n. 1 says the article "features
  the same maps and sketch plans as the Monograph and deploys the argument in
  substantial detail," so **Fig. 1 also appears in Rapp and Gifford's 1982
  supplement** (§5 item 1) — which is a second route to the same plate, and a
  reason not to expect anything new from it cartographically.

### 1.12 Beşik Tepe's Mycenaean pottery — NOT verified

`TROAD-SOURCES.md` §A states that Korfmann's Beşik Tepe cemetery produced c. 100
graves with Mycenaean/Mycenaeanising LH IIIB wares at about one third of the fine
wares, against under 1% in Troia VI/VII levels. I could not reach a source for
those proportions in this pass. The same figures circulate on non-scholarly web
pages, which is a warning sign, not a confirmation. Treat as **unverified** (§6)
until the Beşik excavation reports or Mountjoy's pottery study are checked.

---

## 2. The features, as the sources constrain them

A compact synthesis. Every number traces to §1.

| Feature | What the sources fix | Register |
|---|---|---|
| Marine embayment, maximum extent | Head **17 km inland** from the present plain's north end, immediately NW of Pınarbaşı, at **7000–6000 BP** (Kayan et al. 2003; Brückner et al. 2005 §16); alternatively **"nearly 10 kilometers south of the site of Troy at Hisarlik"** (Kraft, Kayan & Erol 1980, 776 — exact wording, and the origin is the citadel), which the same paper states again as **"approximately 15 km south of the present shoreline of the Dardanelles"** at the c. 7000 BP peak (1980, 782). *(full text, 2026-07-29: was "roughly 10 km south of Hisarlık"; the two 1980 figures are one measurement from two origins — see §3.2a.)* | geographic, but the head is a **buried** feature |
| Fill thickness | **Over 50 m** of strata between the Sigeum ridge and the Hisarlık/Yenikumkale cuestas; ~250–318 cores (Kayan's campaign). Kraft's 1980 sections reach ~−70 m and rest on **seven** drill holes *(full text, 2026-07-29)* — cite Brückner/Kayan for the thickness, not 1980 | geographic |
| Progradation past the city | Coastline reaches **west of Troia c. 4000 BP** (Kayan 2019); direct sea access lost soon after **2200 BC** on Kayan's scenario, retained much later on Kraft's — on Kraft's own 1980 Fig. 6, Troy VI/VII at 3250 BP still sits **on a promontory at the edge of the estuary**, the water to its west and north-west *(full text, 2026-07-29)* | the two scenarios disagree; pick one and name it |
| LBA shore, c. 1200 BC | **Two incompatible numbers, and they are in the same paper.** (a) **~1.2 km**: Kraft, Rapp, Kayan & Luce 2003, 166 — "~6 stades (~1200 m) at the time of the *Iliad*", Strabo's 12 stades halved at 200 m to the stade, which the authors say is "well supported by the environmental lithosome distributions and the radiocarbon dates" *(full text, 2026-07-30 — §1.3; the attribution `shore-bronze` prints is CORRECT, with the qualifications there)*. (b) **2.17 km at bearing 334°**: the nearest open water to the Troy dot on that paper's own *Iliad* plate, Fig. 5, measured *(§1.3a)* — with alluvium and marsh drawn between. Same authors, facing pages. Brückner's "ca. 1.2 km" (§1.6) is (a) again, not a second witness. **Kraft, Kayan & Erol 1980 give no citadel-to-water distance at all**, only "Fortification Troy VI and VII lay on a projection or promontory at the edge of a marine embayment" (782), and read Strabo as describing **his own** time (778–79). **Luce 1984 is not a second opinion:** his Fig. 1 is Kraft's line redrawn (33) — no alternative shore to draw (§1.11, §4 item 12). | (a) identification-via-Strabo, **not** survey; (b) geographic-as-drawn, ±~1 km, coordinates unusable (§1.3a) |
| Sea-level change | Local relative fall of **2 m** (Kayan et al. 2003) or **2–3 m** (Kayan 2019) in the LBA, derived from Kelletat's 1975 curve. Independently and earlier, Kraft, Kayan & Erol 1980's Fig. 6 gives the **endpoints**: **+2 m at 4500 BP → present level at 3250 BP and at 2000 BP**, i.e. a 2 m fall *to* today's datum, from Erol's unpublished curve (ref. 17); the authors call it "valid as a **local, relative,** sea level curve for the Biga Peninsula" (781). The NE Aegean RSL database shows **continuous rise** (Seeliger et al. 2021) *(full text, 2026-07-29)* | state as **local/relative**, never regional; state the endpoints, never a bare "fell 2 m" |
| Barrier | A **wide sandy coastal barrier** closing the remaining water into a shallow lagoon after that fall. The barrier-and-lagoon facies language is **Brückner et al. 2005**; the Kayan et al. 2003 and Kayan 2019 *abstracts* describe the fall and the swamp but do not themselves say "barrier" or "lagoon" — the full texts are unseen (see Needs paywalled access). **Kraft, Kayan & Erol 1980, read in full, has neither word**: its terms are sandy/clay-silt estuary, marsh, swamp, beaches, shoals and brackish–freshwater swamp *(full text, 2026-07-29)*. **DENIED outright by Kraft, Rapp, Kayan & Luce 2003, 164, citing their own 1980 paper: littoral currents sorted sands into "nearshore shoals and possibly thin beaches, although no barrier lineaments are evident on the lower Scamander delta"** *(full text, 2026-07-30 — §1.3b)*. Independently, Strabo 13.1.31 describes a **blind (barred) river mouth with salt lakes and marshes** | geographic; width unsurveyed; **now worse than not-drawing-ready — one arm of the same research group states there is no barrier to draw. Do not draw it as geographic until a Kayan full text or figure is seen (§3.3)** |
| Lagoon | Shallow, behind the barrier; ancient name **Stomalimne** attested between Sigeium and the Scamander mouths (Strabo 13.1.31) | geographic + identification |
| Swamp / marsh | The area west of the city was a **broad deltaic swamp** in Troia IV–VI; the land was **swamp-covered throughout the progradation period**, and the coastal sea **very shallow** (Kayan et al. 2003). Corroborated first-hand: Kraft's Fig. 2 maps modern swamp over the Kesik/Yeniköy plain and the Scamander's western and south-western flanks, and the text allows that "low-lying swamps occurred around the base of Troy" at 3250 BP — with the honest rider "although further drilling would be required to verify this" (1980, 782) *(full text, 2026-07-29)* | geographic, extent approximate |
| Kesik cut | **400 × 50 × 30 m** (Kayan's/Zangger's figures, never Cook's), floor **13.7 m a.s.l.**, ~150 m from the sea, 2–2.5 m of colluvium on the floor. **Contested origin, corrected 2026-07-30 — the two authorities disagree and must not be blended:** Kayan reads a natural **tectonic depression** widened by foot traffic (Kayan 2009, 124; 2014, 723–24); Cook independently calls it "an artificial cut… never completed", floor "perhaps 12–15 m a.s.l." (brackets Kayan's 13.7 m), his own guess **drainage, late-Roman** (Constantine's new city) (Cook 1973, 166–67; `RESEARCH-TROAD-TOPOGRAPHY.md` §9.2). A tectonic depression cannot be "unfinished" — rival origin theories, not compatible attributes. **Cook is never citable for Bronze Age harbour engineering.** **Fourth reading added 2026-07-30, first-hand: Kraft, Rapp, Kayan & Luce 2003, 166 make the cut "a great wall and ditch (Kayan, 1995)… proposed by Nestor", i.e. the Achaean fortification of *Il.* 7.336–43** — a Late Bronze Age military work on the same ground where Cook puts an unfinished late-Roman drainage trench. Drawn on Figs. 4 **and** 5 as a hatched band ~5.35 km due west of the Troy dot, ~0.6 × 0.33 km as symbolised (≈1.5× and ≈6× the surveyed cut) — §1.9, §1.3a | geographic; **not** a harbour entrance; **four mutually exclusive identifications, three of them 2003** |
| Kesik plain | Basin ~**800 m** wide; silted **before 1300 BC**; "could not have been used as harbours during the Later Bronze Age" (Kayan et al. 2003, 400) — against Kraft et al. **2003a**'s choice of it as the harbour. Note that Kraft et al. **2003b** (*Geology*, read in full 2026-07-30) proposes **no** harbour at Kesik and no harbour site anywhere: the Kesik cut is Nestor's ditch and the shelter is the bay (§1.3b, §1.9). **= the Lisgar marsh = Ilıca** (Cook 1973, 166; one basin, three names — §1.9) | contested identification; **cite the letter, a or b** |
| Beşik Bay | The project's original harbour candidate, stated first-hand in **Kraft, Kayan & Erol 1980, 782** ("the Beşika embayment was indeed the site of the Achaean camp"; "an indentation approximately **2 km inland**" at 4000–5000 BP) and again at Kraft et al. 1982, 40 and Kayan 1991, 91. **Rejected by Luce 1984, 40–41** on three stated grounds: too exposed to the Aegean for a permanent ship station; **8½ km from Troy against 4 to 5 km for his Sigeum ridge site**; and bad access to the Scamander plain, "first across a low ridge and then across a wide expanse of low-lying and marshy ground". He adds that Mey's 1924 trenches there found "nothing to confirm his Achaean camp hypothesis" (40). Cook 1973, 171–72 is on the *other* side ("a very much more satisfactory situation for the Homerists") and Luce says so and disagrees *(full texts: Kraft 2026-07-29 — cite 1980, not the second-hand 1982 quotation; Luce 2026-07-30 — the objections are now first-hand and one of them is a measurement)* | contested identification |
| Harbour, in general | Kayan et al. 2003: the environment "has never been suitable for the establishment of an important harbour". **And the paper titled "Harbor areas at ancient Troy" names no harbour area:** its positive claim is that river-sand redistribution "was limited by the very low wave activity in this **long-term sheltered marine embayment**" (Kraft, Rapp, Kayan & Luce 2003, 164) — the shelter is the bay, which is Luce 1984's position in geologists' words *(full text, 2026-07-30 — §1.3b, §1.11c)* | prose; the strongest deflationary claim in the literature, and the title of the "harbour paper" is not evidence against it |
| Water depth in the embayment | "frequently ~1 m and could vary to 3–4 m" (Kraft, Rapp, Kayan & Luce 2003, 164); Yang's biofacies IV runs "to 40 m" for the class as a whole *(full text, 2026-07-30 — §1.3b)* | geographic; the ~1 m figure is what makes "beach the ships anywhere" plausible and "harbour" unnecessary |
| Ancient river channels | **Not locatable, by the authors' own statement:** "With as much as 20 m of alluvium on the southern Scamander floodplain, we cannot hope to locate the river channels of antiquity" (Kraft, Rapp, Kayan & Luce 2003, 164) — yet their Fig. 5 draws the Scamander, the Simois, a Ford and the "Bridges of War" *(§1.3b)* | **no geographic register exists for these.** Schematic only, and never sourced to Fig. 5 |

---

## 3. Our drawn geometry against the published constraints

### 3.1 The 10 m contour choice — the *result* is inside the constraint; the *derivation* does not reproduce

**Verified inside.** DEM measurement (this dossier): the nearest vertex of the
drawn `shore-bronze` line to Hisarlık (39.957, 26.239) is **1.22 km** away, at
39.9611, 26.2257 — north-north-west, as `lagoon-bronze`'s note says. Against
Strabo's 6 stades (1.07–1.11 km; "ca. 1.2 km" as Brückner rounds it) that is
**inside the constraint, to within about 10%**. Against Kayan's independent
statement that the coastline reached west of Troia by c. 4000 BP, a shore ~1 km
out at 3200 BP is also consistent. **The drawn line's position is defensible.**

**And now, against the only published *Iliad*-time plate we have seen (2026-07-30).**
Kraft, Rapp, Kayan & Luce 2003's Fig. 5, measured (§1.3a), puts its nearest water
**2.17 km at bearing 334°** from the Troy dot. Our line is **1.22 km at NNW**.

| | distance from citadel | bearing | provenance |
|---|---|---|---|
| our `shore-bronze` | 1.22 km | NNW | 10 m contour on SRTM |
| Kraft et al. 2003, **text** (166) | ~1.2 km | "the plain to the north of the city towards the sea" | Strabo 13.1.36, halved, at 200 m/stade |
| Kraft et al. 2003, **Fig. 5** | 2.17 km | 334° (NNW) | drawn |
| Strabo's 6 stades at 177.6 m | 1.07 km | — | ancient testimony |

**Our line agrees with the paper's text and Strabo, and disagrees with the paper's
map, by ~0.95 km.** Which is the honest way to state it in a plate note: the drawn
position sits at the *near* end of a published spread that is itself a factor of two
wide, and the spread is internal to one paper. Do not tighten the claim; widen the
note. The bearing agrees on all four rows, which is the part worth asserting
without hedging: **the Bronze Age water lay north-north-west of the citadel.**

**But the stated reasoning is not reproducible.** `shore-bronze`'s note says the
8 m contour "puts it 2.8 km north and the 12 m only 0.7 km, both outside the
published range". DEM measurement (this dossier), nearest cell to Hisarlık within
the plain sector (lat ≥ 39.93, lon 26.16–26.31):

| level | raw 30 m grid | blur×10 + decimate×2 (the grid the bronze geometry was cut on) |
|---|---|---|
| 5 m | 3.24 km | 3.62 km |
| 8 m | **1.28 km** | 1.41 km |
| 10 m | **0.41 km** | 0.48 km |
| 12 m | 0.24 km | 0.26 km |

Neither 2.8 km nor 0.7 km reproduces on either grid. The reason is visible in the
profile due north from Hisarlık along lon 26.239 (raw DEM): 14.9 m at 0.22 km,
then **11.2, 10.6, 11.7, 10.6, 11.2, 9.9, 10.7 m** from 0.45 to 1.78 km, then
13.9 m at 2.0 km. **The delta surface north of the citadel is flat at 10–11 m for
nearly 2 km.** On ground that flat, which ring a marching-squares tracer keeps and
where it runs depends on the smoothing and the minimum-span filter as much as on
the level; a 1 m change in level, or a change in blur passes, moves the line by
kilometres; and the DEM's own vertical noise is of the same order as the
difference between the candidate levels.

**What to do about it** (recommendation, not a mandate):

1. Keep the 10 m line. It lands where the ancient testimony puts the shore.
2. **Restate the derivation honestly**: the level was chosen because it produces a
   shore of the order of 1 km from the citadel, which is what Strabo 13.1.36
   requires — not because 8 m and 12 m are arithmetically excluded. Record the
   smoothing parameters (blur 10, decimate 2, tolerance 0.0009°) in the note,
   because without them the contour is not a reproducible object.
   *(Amended, full text, 2026-07-29: an earlier draft of this line added "and what
   Kraft's scenario endorses". Drop that clause. Kraft, Kayan & Erol 1980 endorse a
   shore whose water reaches the citadel's own promontory, west and north-west, and
   they publish no distance; they are consistent with ~1 km but do not assert it,
   and they read Strabo's stades as evidence for Strabo's own century. §1.1, §1.3.)*
3. There **is** a real quantitative argument available, and it is better than the
   one in the note. Strabo gives two shorelines: 6 stades in Homer's day and 12 in
   his own. DEM measurement (this dossier): the surface at 1.11 km north of
   Hisarlık is **10.6 m** and at 2.00 km is **13.9 m**. So the two Strabonic
   shorelines sit about **3.3 m apart vertically**, i.e. ~2.8 mm/yr of aggradation
   over the ~1,200 years between them — the right order for a Mediterranean delta
   plain. That makes 10 m the level consistent with the 6-stade shore *and* ~14 m
   the level consistent with the 12-stade shore, from one internally coherent
   aggradation rate. (My arithmetic on the DEM plus Strabo; not a published
   result. Grok or a geomorphologist should check it before it is printed.)
4. Consider drawing a **band** between the 8 m and 12 m lines rather than a single
   stroke, which is what `TROAD-SOURCES.md` §A recommended in the first place and
   what the ±1 km honesty statement already implies.

### 3.2 The 7.5 km vs 10 km fill extent — RESOLVED, and it is a category error, not a conflict

The handoff records this as the one constraint that could not be confirmed: "the
marine embayment/fill runs ~7.5 km S inside the sheet against a published figure
of 10 km." Three findings close it.

**(a) The two published figures are not the same measurement, and they do not
agree with each other either.** Kraft et al. 1980 measure **"nearly 10 kilometers
south of the site of Troy at Hisarlik"** (p. 776, exact wording; full text read
2026-07-29). Kayan et al. 2003 and Brückner et al. 2005 measure **~17 km inland,
"up to the area immediately northwest of Pınarbaşı"**. [OSM/Nominatim](https://nominatim.openstreetmap.org/)
puts Pınarbaşı (Ezine) at **39.8880 N, 26.2715 E**, which is **7.7 km south of
Hisarlık**. So the same embayment head is published at 10 km south by one team and
at ~7.7 km south by the other. **Our ~7.5 km is inside the published range — it
sits on Kayan's value, not outside Kraft's.**

**(a′) The 10 km's origin and direction are now settled, and the figure is
internally cross-checked (full text, 2026-07-29).** Three statements in the 1980
paper agree:

- the summary's "nearly 10 kilometers **south of the site of Troy at Hisarlik**"
  (p. 776) — so the origin is the **citadel**, and the direction is **south** along
  the valley, which is exactly what the handoff's open question needed;
- the body's independent restatement of the same peak, from the other end: at
  "approximately 7000 years ago… marine waters with both muddy and sandy bottom
  sediments extended approximately **15 km south of the present shoreline of the
  Dardanelles**" (p. 782);
- and the paper's own placement of Hisarlık, "approximately **5 kilometers south
  of the Dardanelles**" (p. 776).

15 − 5 = 10. The two figures are **one measurement stated from two origins**, not a
spread. Fig. 3's section is drawn on the same convention: it runs 0–18 km from the
Dardanelles shore with Troy marked at ~6 km.

**(a″) And Kraft's Fig. 2 settles which Pınarbaşı is meant.** Fig. 2 (p. 778)
plots **Pınarbaşı at the southern end of the Kara Menderes plain, immediately
beside drill hole T7, at the mouth of the gorge where the Scamander leaves the high
plateau**, with Mahmudiye to its west-south-west and Üvecik further west. That is
the same village OSM puts at 39.8880, 26.2715 (Üvecik Tepe at 39.9003, 26.1992
sits west of it, as on Fig. 2), and it is where Brückner's "immediately northwest
of Pınarbaşı" must land if his 17 km is to reach it. The §6 caveat about several
Troad Pınarbaşıs is therefore **resolved for Kraft's own map** and, by the
geometry, strongly supported for Brückner's — the residual doubt is only that we
have not seen Brückner's Fig. 3.
The 10 km / 7.7 km spread between the two teams stands: it is a real disagreement
about how far the water reached, not a units confusion.

**(b) The head of the maximum transgression is a BURIED feature, and no modern
surface contour can reach it.** DEM measurement (this dossier), minimum elevation
of the Karamenderes valley floor within lon 26.19–26.29, going south from Troy:

| km south of Hisarlık | valley-floor minimum |
|---|---|
| 0.8–3.0 | 9.0–9.2 m |
| 3.45 | **11.5 m** |
| 4.3–5.2 | 13.0–13.6 m |
| 6.6–7.5 | 14.0–16.1 m |
| 8.4 | 21.4 m |
| 9.7–10.6 | 20.8–27.3 m |

The floodplain surface **crosses 10 m at about 3.4 km south of Hisarlık** and rises
steadily upstream, standing at ~16 m near Pınarbaşı's latitude. A shoreline that
stood at approximately present sea level 6000 years ago is therefore under
**~16 m of fill** at the embayment head. **The 10 m contour cannot mark the fill
limit south of ~3.4 km, and should never have been expected to.**

**Corroborated by Kraft's own surveyed elevations (full text, 2026-07-29).** Fig. 2
prints the surface elevation at each drill hole: **T6 at 14.7 m** in mid-valley and
**T7 at 19.6 m** immediately beside Pınarbaşı — against the DEM's 14.0–16.1 m at
6.6–7.5 km south and ~16 m near Pınarbaşı's latitude. The two independent
measurements agree to about a metre or two (T7 sits on the valley side at the gorge
mouth, so it should read a little high). And Fig. 3 draws the point directly: the
**3250 BP and 4500 BP time-depositional surfaces lie below the present floodplain
surface along the whole 18 km section**, with the sandy embayment at its head
interfingering into a **brackish–freshwater swamp** near T7. The buried-feature
argument is not our inference from a DEM; it is what the paper's own cross-section
shows.

**(c) The sheet's 10 m contour does run to the south edge — but not on the
plain.** `sources/terrain-tiles/trojan-plain-contours.json`, level 10 m, feature 1
spans lat 39.8602–40.05, i.e. to the sheet's southern boundary 10.8 km south of
Troy. Its southern vertices sit at **lon 26.144–26.172** — the modern Aegean
coastal slope on the *west* side of the Sigeum/Yeniköy ridge, about 5 km west of
the valley axis. Whatever "the fill runs 7.5 km S" was measured on, it was that
segment, which is not the Trojan plain's fill at all.

**Verdict.** `shore-bronze` is right to stop at the bay head, and right for a
stronger reason than its note gives: south of ~3.4 km the 10 m contour is not
tracking anything relevant. The correct statement in the note is that the
maximum-transgression head (7.7–10 km south, depending on whose figure) is a
**buried Middle Holocene feature**, ~4,800 years older than the shore this layer
draws, and is deliberately **not** drawn on this sheet. If we ever want to draw
it, it needs Kraft's or Kayan's core-based line, not a contour.
**Update (full text, 2026-07-29): that line now exists in front of us** — Fig. 6's
7000 BP panel — but it does not change the verdict, for two reasons. Kraft's Fig. 6
is **copyrighted expression and must never be traced** (the posture at the head of
this file); drawing the head would mean re-deriving it from the cores, and the 1980
paper prints no core logs, only the sections. And the seven-hole basis (§1.1) is too
thin to hang a 10 km shoreline on when Kayan's 318 holes put the same head ~2 km
nearer. Leave it off the sheet and **label the absence**, as the register rule
requires.

### 3.3 The barrier — geometry verified, provenance to fix

DEM measurement (this dossier): all 11 vertices of `barrier-bronze` sit on land
today at **2.8–7.8 m** (median ~5 m), consistent with the layer's stated
derivation from the 5 m contour and with its claim to be entirely on land. Its
nearest vertex to Hisarlık is 4.42 km, against 4.65 km for `coast-modern` — so at
its closest approach the drawn barrier lies only ~230 m inside the modern shore.
That is worth a second look: 3,200 years of continued progradation should have
carried the modern shore further out than that along this meridian, and Kayan's
barrier is a Bronze Age feature, not a modern one. Not a proven defect — the two
lines are at different longitudes — but it wants checking against Kayan 2014
fig. 8 when that is in hand.

Provenance to fix: the "2 to 2.5 m" fall (see §1.5) matches no published range.

**Escalated 2026-07-30 — the provenance problem is now a contradiction.** Kraft,
Rapp, Kayan & Luce 2003, 164 states, citing Kraft, Kayan & Erol 1980: "**no barrier
lineaments are evident on the lower Scamander delta**" (§1.3b). So the same research
group that Brückner 2005 reports for the barrier facies denies, in print, that a
barrier lineament can be seen on this delta. Add to that: the 1980 full text uses
neither "barrier" nor "lagoon" (§2), the 2003 *Geology* paper offers no sea-level
number at all, and the "2 to 2.5 m" fall behind the barrier's stated derivation
matches nothing published. **`barrier-bronze` is now the weakest layer on the
sheet.** Either re-found it on a Kayan full text/figure (§5 items 4, 5) or demote it
from the geographic register — and until then it must not be captioned as though
Kraft's group supports it.

### 3.4 A real defect: the eastern tail of `shore-bronze` is not on the 10 m contour

DEM measurement (this dossier), elevation at each of the 24 `shore-bronze`
vertices: the first seven read **19–21 m** (the Sigeion-ridge stretch cut from the
20 m contour, exactly as the note declares), the next fourteen read **10–11 m**
(the 10 m contour, as declared), and the last three read **13 m, 14 m and
−0.4 m**. The final vertex (40.0169, 26.3205), the "Rhoiteion spur" end, is
**below sea level on the modern DEM** — it is in the Dardanelles. The eastern tail
is neither the 10 m contour nor the 20 m contour, and its terminal vertex is
offshore. Either re-cut that stretch from a stated contour or truncate the line
where the declared derivation ends.

### 3.5 Terrain sanity checks, re-measured

Hisarlık **36.3 m** (published c. 38); Sigeion crest **35.0 m** at 39.9835,
26.1809 (Cook's "thirty to forty"). Modern shore due north of Hisarlık along lon
26.239 reaches 0 m at **4.9 km**.

**Corrected (full text, 2026-07-29).** This dossier previously called Kraft's
"about 6 km" an along-delta migration figure. It is not. The paper states it of
the coast itself: deposition drove the delta north "past the site of Troy toward
**the present-day coast about 6 kilometers north of the site**" (Kraft, Kayan &
Erol 1980, 776), and Fig. 3's section, drawn from the Dardanelles shore southward,
marks Troy at ~6 km along. So Kraft's 6 km and our DEM's 4.9 km are **the same
measurement, and they differ by about 1.1 km** — 22%. The likeliest explanation is
that Kraft measures to the Dardanelles shore on the section's axis, which runs
north-north-east of the citadel toward Yenikumkale/Kum Burnu rather than due north
along lon 26.239, and rounds. Not a defect in either number, but **do not print
"6 km due north": say "about 6 km to the Dardanelles coast (Kraft, Kayan & Erol
1980, 776); ~4.9 km measured due north on the SRTM DEM."** `TROAD-SOURCES.md`'s
"roughly 6 km" is Kraft's figure and should carry Kraft's citation.

### 3.6 Luce's camp against our own `shore-bronze` — it is drawable, and his three distances are not

DEM/geometry measurement (this dossier), the seven `shore-bronze` vertices that
§3.4 identifies as the Sigeion-ridge stretch cut from the 20 m contour, each
measured from Hisarlık (39.957, 26.239):

| vertex | lat, lon | west of Hisarlık | straight-line distance | bearing |
|---|---|---|---|---|
| 0 | 39.9950, 26.1900 | 4.18 km | **5.95 km** | 315° |
| 1 | 39.9924, 26.1908 | 4.11 km | 5.70 km | 314° |
| 2 | 39.9855, 26.1848 | 4.62 km | 5.61 km | 304° |
| 3 | 39.9784, 26.1814 | 4.91 km | 5.46 km | 296° |
| 4 | 39.9719, 26.1886 | 4.30 km | 4.61 km | 291° |
| 5 | 39.9676, 26.1873 | 4.41 km | 4.57 km | 285° |
| 6 | 39.9658, 26.1898 | 4.20 km | **4.31 km** | 283° |

Three findings, and the third is the one to carry forward.

1. **The plate can already draw Luce's camp.** His 4–5 km (1984, 41) is satisfied by
   vertices 4–6, the branch's southern half — the ground at bearings 283–291° from
   the citadel, which is "west by south" to within a point of the compass. Nothing
   needs to be invented: the camp is an **extent along vertices 4–6** of a line the
   sheet carries for an independent reason. His 5–6 km "across the expanse of water"
   (35) is satisfied by vertices 0–3, the branch's northern half. So a strip running
   the whole branch has no single distance to Troy, which is the mundane reason his
   two body figures differ.
2. **That is an explanation, not a reconciliation, and the abstract still does not
   fit.** "About four miles west" is 6.44 km. The largest *westward* offset anywhere
   on the branch is 4.91 km and the largest straight-line distance is 5.95 km at the
   ridge's northern tip by Kum Kale — which is not where Fig. 1 puts the strip
   either. **No point on the Sigeum ridge's eastern flank is four miles west of
   Hisarlık.** The discrepancy stands recorded (§1.11a).
3. **The tension inside Fig. 1.** Luce's strip runs from "a break in the line of the
   ridge just south of … 'Spratt's plateau'" (36) — and his own Fig. 1 prints
   "Spratt's Plateau" in the ridge's *northern* third, above the ridge label and
   below Yenişehir. So the strip he draws reaches into the 5.5–6 km band while the
   number he argues from is 4–5 km. Draw the extent, state the range 4.3–6.0 km, and
   do not print a single distance for "Luce's camp".

Method note: plate-carré with cos(latitude) scaling, as everywhere else in this
file; the vertices are read straight out of `apparatus/plates/trojan-plain.json`
(`shore-bronze`, first ring). Reproducible in six lines — no new tooling.

### 3.7 How the Kraft et al. 2003 figures were measured, so the numbers can be checked

Every figure number in §1.3 and §1.3a is a *figure measurement (this dossier)* and
was taken like this. No new tooling; poppler and Pillow only.

1. `pdfimages -png` on `research-cache/kraft-rapp-kayan-luce-2003-geology.pdf`
   yields the six figures as **1-bit stencils at 300 dpi**, one PNG each
   (`fig-000` = Fig. 1, `fig-001` = Fig. 2, `fig-002` = Fig. 3, `fig-003` = Fig. 4,
   `fig-004` = Fig. 5, `fig-005` = Fig. 6). **Polarity trap: in these stencils the
   ink is the *bright* value.** Getting it backwards makes every seed land "on ink".
2. **Scale.** The printed 0–1–2 km bar on Figs. 4–6 spans x = 164→328 in figure
   pixels ⇒ **82 px/km**. Cross-check on the "12 stades" and "20 stades" arcs gives
   ~76 px/km; the ~8% gap is the paper's, not the method's (§1.3a).
3. **Anchors.** Troy / New Ilium dot centre at (587, 506) on Figs. 4–5 and
   (585, 504) on Fig. 6, read off ×9 nearest-neighbour crops with a labelled pixel
   grid. Graticule ticks found by scanning the frame for inward marks: **39°58′N at
   y = 522**, **26°15′E at x = 609**. The frame is x 4–1073, y 5–1121.
4. **Water regions.** Dilate ink by one pixel (`MaxFilter(3)`) to close hairline
   gaps, then 4-connected flood fill from a seed inside the Aegean (Figs. 4–5) or
   inside "Troia Bay" (Fig. 6). **Leak test, mandatory:** six probe points in the
   stippled alluvium and on the eastern plateau must all fall *outside* the fill.
   Figs. 5 and 6 pass. **Fig. 4 fails** — its dotted "sandy coastline" band and thin
   channel lines let the fill into the plain — which is why no Fig. 4 distance is
   quoted (§1.3a).
5. **Radial profile.** March outward from the Troy dot at 15° steps until the first
   fill pixel; that is the table in §1.3a. Bearings are map-north (the sheets carry a
   north arrow and are north-up).
6. **Do not convert to lat/lon.** Step 3's ticks *permit* it and the result is
   wrong: the Troy dot lands 1.4 km NE of Hisarlık on the figure's own graticule,
   and the "CAPE RHOETEUM" dot ~6 km west of Rhoiteion. Distance-and-bearing from the
   citadel is the only output of this method that may be used (§1.3a).

---

## 4. Corrections this dossier owes to files it must not edit

Findings only — no tracked file outside `docs/research/` was touched.

1. `apparatus/plates/trojan-plain.json`, `shore-bronze`: **the "1.2 km north of
   Hisarlik, where Kraft, Rapp, Kayan and Luce put the bay head" attribution is
   VERIFIED as to the number — the phrase "~6 stades (~1200 m) at the time of the
   *Iliad*" is theirs, on p. 166 (§1.3).** Two amendments the note still owes:
   (a) "put the bay head" overstates it — they halve Strabo's 12 stades and assert
   their cores support it; they do not measure it, and their own Fig. 5 draws the
   water at 2.17 km (§1.3a, §3.1); (b) "north" should be **north-north-west**, which
   is what every source and our own line agree on. The 8 m / 12 m arithmetic still
   does not reproduce (§3.1).
2. Same file, `barrier-bronze`: "2 to 2.5 m" is not a published range; sources say
   about 2 m (Kayan et al. 2003) or 2–3 m (Kayan 2019). And the fall must be
   labelled **local/relative**, because the NE Aegean RSL database shows
   continuous rise (§1.8).
3. Same file, sources array: the "Troian Bay" chapter is by **Kayan, Öner, Uncu,
   Hocaoğlu and Vardar**, pp. 379–401 — currently cited as sole-author, no pages.
4. `docs/TROAD-SOURCES.md` §A: the **330 × 230 m** basin is at **Pylos**, not
   Kesik (§1.9). Delete or relocate.
5. `docs/TROAD-SOURCES.md` §A: "modern coast … at Kumkale" — OSM puts Kumkale
   village at 39.9816, 26.2370, **2.7 km north of Hisarlık and well inland**. The
   coastal settlement in the literature is **Yenikumkale**; Brückner names the
   Yenikumkale cuesta. Check the name before printing it on a sheet.
6. `docs/TROAD-SOURCES.md` §A: Beşik Tepe's LH IIIB pottery proportions are
   uncited and unverified (§1.12, §6).
7. Kraft et al. 1980's "10 km south" and Kayan's "17 km inland" are **not** simply
   "consistent, different measures" as §A says — converted to a common origin they
   differ by ~2 km (§3.2a). Say so; it is a real spread in the literature and it
   is the spread our own line sits inside. *(Firmed up with the 1980 full text: the
   10 km is "nearly 10 kilometers south of the site of Troy at Hisarlik", p. 776,
   cross-checked by the same paper's "approximately 15 km south of the present
   shoreline of the Dardanelles", p. 782 — §3.2a′.)*

New, from the 1980 full text (2026-07-29):

8. `apparatus/plates/trojan-plain.json`, `shore-bronze`: whatever the note says
   about **Kraft** and the bay head must change. The 1980 paper gives no
   citadel-to-water distance, puts the water west and north-west of a citadel
   standing on a promontory at the estuary's edge, and reads Strabo's measurements
   as describing c. 2000 BP rather than the war (§1.1, §1.3). Re-attribute the
   ~1 km to **Strabo 13.1.36 as read by Brückner et al. 2005**.
9. Same file, `barrier-bronze`: the sea-level note should give the **endpoints**,
   not a bare fall. Kraft, Kayan & Erol 1980's Fig. 6 prints **+2 m at 4500 BP and
   present level at 3250 BP** — the fall ends at today's datum. Combined with §1.8,
   the defensible wording is "a local relative fall of about 2 m from a
   mid-Holocene high back to roughly today's level, between c. 4500 and c. 3250 BP".
10. Any plate note that reads "the sheet draws Kraft" for the Achaean camp: name
    the year. **Kraft, Kayan & Erol 1980, 782 put the camp at the Beşika embayment**
    and the battlefield axis south of Troy and east of that bay; Kraft et al. 2003a
    put the harbour at Kesik. The two are on opposite sides of the ridge (§1.9).
11. `docs/TROAD-SOURCES.md` §A: the "roughly 6 km" to the modern coast is
    **Kraft's own figure for the coast's distance north of the site** (1980, 776),
    not a delta-migration distance, and it runs ~1.1 km longer than the DEM's
    due-north measurement. Cite it, and state the direction (§3.5).

New, from the Luce 1984 full text (2026-07-30):

12. `apparatus/plates/trojan-plain.json`, the sheet note. Three things in it are
    now falsified by Luce's own pages (§1.11).
    (a) "**Luce (1984) puts the shoreline west by south of the site with a broad
    embayment between the city and the Sigeum ridge … Both cannot be drawn on one
    sheet; this one draws Kraft.**" There is no second shoreline. Luce's Fig. 1 is
    captioned "After Kraft, Kayan and Erol 1980, fig. 2 with additions from fig. 6"
    (Luce 1984, 33); his "west by south" (32) is a description of Kraft's line, not
    a rival to it. The sentence should say that Luce **accepts** this shoreline and
    differs only about the camp and the fighting axis.
    (b) "**some four miles west of Hisarlik**" is the abstract's figure and it
    contradicts the body twice — 4 to 5 km at p. 41, 5 to 6 km across the water at
    p. 35. Print "4 to 5 km (Luce 1984, 41)" or say nothing.
    (c) "**which rotates the battlefield from north-south to roughly east-west.**"
    Defensible, but Luce states the bearing three ways (east–west at 38 and in the
    abstract; "south-west from the hill of Hisarlik" at 36) and Kraft 1980, 782 a
    fourth. Say "west or south-west of the city"; do not imply one bearing is his.
13. `apparatus/places.json`, `fig-tree` (line ~7840, `tradition`; line ~7874, the
    source entry): the record has "Fixed only by the poem's own narrative geography
    (Leaf 1912; **Luce 1984**)" and cites the *OJA* article. **Luce 1984 does not
    mention the fig tree.** No `ἐρινεός`, no 6.433, no treatment of 11.167 as a
    fig-tree passage, nothing on the two-fig problem, in any of pp. 31–43. The
    nearest thing is his reading of 6.4**34** — the city "most approachable," which
    he locates on "the apron-like plateau on its south-west flank" (36) — and that
    is a bearing for the *approach*, not a placement of the tree. Either drop Luce
    from that record or re-cite it to 6.434 and say what it actually supports. This
    also answers `RESEARCH-POEM-TOPOGRAPHY.md` §9 item 5, which asked exactly this
    question and flagged the citation as unread.
14. `apparatus/plates/trojan-plain.json`, `simoeis` note: "The equation with the
    modern Dumrek Su is a Strabonic tradition that Leaf, Cook and **Luce** all
    accept" — now first-hand for Luce and citable: "there is no good reason to doubt
    its identification with the Dümrek" (Luce 1984, 38).

---

## 5. Needs paywalled access

Ordered by how much they unblock. For each: what it is, and which claim it
settles.

0. **✅ OBTAINED 2026-07-29 — Kraft, Kayan & Erol 1980**, "Geomorphic
   Reconstructions in the Environs of Ancient Troy," *Science* 209 (4458):
   **776–82**. JSTOR scan cached at
   `research-cache/kraft-kayan-erol-1980-science.pdf` (8 pp. incl. cover). Entry
   kept so the ledger shows what a pull actually buys. **Settled:** the 10 km
   figure's exact wording, origin and direction (§3.2a′); the whole five-panel map
   series and its sea levels, including the LBA position (§1.1); the drill-hole
   count and surface elevations (§1.1); Beşika-as-camp first-hand (§1.9); the
   Pınarbaşı identification on Kraft's own base map (§3.2a″); the sea-level
   curve's provenance as Erol's unpublished data. **Did NOT settle:** the
   "1.2 km north of Hisarlık" bay head — the paper does not contain it, which
   redirects that question wholly to item 2 below; and the core logs, which are not
   printed here (item 1).

1. **Kraft, Kayan & Erol 1982**, "Geology and Paleogeographic Reconstructions of
   the Vicinity of Troy," in *Troy: The Archaeological Geology*, ed. Rapp &
   Gifford (Princeton), **11–41**. The long version of the 1980 *Science* paper.
   *(Priority lowered, 2026-07-29: the map series and the 10 km measurement are now
   in hand from the 1980 full text, so this is wanted for the **core logs** — the
   seven T-hole descriptions behind Fig. 3 — and for the Beşik quotation at p. 40,
   whose claim we can already cite first-hand from 1980, 782. Catalogue note: the
   1980 paper's ref. 20 lists it as "Geology and paleogeographic reconstructions in
   the vicinity of ancient Troy", **Troy Supplementary Monograph 4**, Princeton,
   **1980** — try both titles and both years.)*
   **Settles:** the core logs; whether the 1982 map series differs from Fig. 6.
   Print book, likely borrowable.
2. **✅ OBTAINED 2026-07-30 — Kraft, Rapp, Kayan & Luce 2003**, *Geology* 31 (2):
   **163–66**, DOI `10.1130/0091-7613(2003)031<0163:HAAATS>2.0.CO;2`. Scan cached
   at `research-cache/kraft-rapp-kayan-luce-2003-geology.pdf`; text and all six
   figures read, figures measured (§1.3, §1.3a–d, §3.7). Entry kept so the ledger
   shows what a pull buys.
   **Settled — and this was the dossier's number-one question:** the "~1200 m at the
   time of the *Iliad*" IS in the paper, p. 166, in those words, with the authors'
   claim that their lithosomes and radiocarbon dates support it. So the attribution
   we print on `shore-bronze` is sound; §4 item 1 now asks only for wording
   amendments. **Settled against expectation, three times:** (a) their *Iliad* plate
   (Fig. 5) draws the water **2.17 km** out, not 1.2 km — the paper contradicts
   itself across facing pages; (b) they name **no harbour site at all** — the Kesik
   cut is Nestor's wall and ditch and the shelter is the bay itself, so the
   Kesik-as-harbour claim belongs to item 3 (2003a) and not here; (c) they **deny
   the barrier**: "no barrier lineaments are evident on the lower Scamander delta".
   Also settled: the whole Strabo apparatus (Luce's own translation, the 200 m
   stade, the 20-stade camp reading — §1.10); Luce's camp on the ridge's **outer**
   Aegean flank, reversing his 1984 position (§1.11c); and the Fig. 2/Fig. 3 core
   data, including a **3500 BP shell at ~−2 m** on the Simois axis (§1.3a).
   **Did NOT settle:** any coordinate — the figures' own graticule misplaces Troy by
   1.4 km and "Cape Rhoeteum" by ~6 km, so they are relative-geometry authority only
   (§1.3a); any sea-level value; the Kesik cut's date, which this paper asserts as
   Bronze Age against Cook's late-Roman without citing him (§1.9); and what **Kayan
   1995** actually says about Kesik, which this paper cites for "a great wall and
   ditch" — now the sharpest reason to pull item 6.
3. **Kraft, Kayan, Brückner & Rapp 2003**, "Sedimentary Facies Patterns…," in
   *Troia and the Troad*, **361–77** (esp. 367, 375). **Settles:** Scenario II's
   shoreline positions per period; the Kesik-as-harbour argument; the
   "nothing … negates Homer" quotation in context.
4. **Kayan et al. 2003**, same volume, **379–401** (esp. 396 fig. 6, 400, 401).
   **Settles:** Scenario I's shoreline positions; the barrier and lagoon geometry;
   the "could not have been used as harbours" statement in its own words rather
   than through Zangger's footnote.
5. **Kayan 2014**, "Geoarchaeological Research at Troia and Its Environs," *Studia
   Troica Monographien* 5, **694–727** (esp. 703, 709 fig. 8, 723–24). **Settles:**
   the sea-level curve Kayan actually plots (fig. 8) — the single most useful
   figure for our barrier and lagoon; the coring campaign's parameters; his final
   position on Kesik.
6. **Kayan 1995**, "The Troia Bay and Supposed Harbour Sites in the Bronze Age,"
   *Studia Troica* 5, **211–35** (esp. 217, 220–21, 231, fig. 8). **Settles:** the
   17 km measurement's basis; the Yeniköy and Kesik cores; the "abrupt change in
   sediment character". *(Priority raised, 2026-07-30: this is the paper Kraft,
   Rapp, Kayan & Luce 2003, 166 cite for the claim that the Kesik cut is "a great
   wall and ditch" — the Achaean fortification of Il. 7 — and everything else we
   have from Kayan on Kesik reads it as a natural tectonic depression, cited to 2009
   and 2014. Either 1995 says something none of our other sources reports, or the
   2003 citation is loose. That is the load-bearing question for §1.9's four-way
   contradiction and for whether Kesik may appear on a plate at all.)*
7. **Kayan 2009**, "Kesik Plain and Alacalıgöl Mound," *Studia Troica* 18,
   **105–28** (esp. 105, 108 fig. 3, 124). **Settles:** the Kesik plain's geometry
   and its siltation date, first-hand.
8. **✅ OBTAINED 2026-07-30 — Luce 1984**, *OJA* 3 (1): **31–43**. Scan cached at
   `research-cache/luce-1984-oja.pdf`; text and both figures read (§1.11, §1.11a–c).
   **Settled:** where his camp sits — a *strip* (X X on his Fig. 1) on the eastern
   flank of the Sigeum ridge, **4 to 5 km** from Troy (p. 41), which lands on the
   20 m-contour branch our own `shore-bronze` already draws; the three Beşika
   objections, first-hand (pp. 40–41); the fighting-axis spread; that his 1984
   argument names **no harbour** and never mentions Kesik. **Settled negatively —
   and this was the load-bearing question:** there is **no Luce shoreline** to draw
   as an alternative. Fig. 1's water lines are Kraft's, captioned as such (p. 33).
   **Did NOT settle:** the strip's two endpoints, which depend on Cook 1973, 165's
   "Spratt's plateau" (item 12 below); and anything about the fig tree, which the
   article does not discuss (§4 item 13).
9. **Luce 2003**, "The Case for Historical Significance in Homer's Landmarks at
   Troia," in *Troia and the Troad*, **9–30** (esp. 22). Also **Luce 1998**,
   *Celebrating Homer's Landscapes* (Yale). **Settles:** whether Luce charts the
   fighting scene by scene (a standing question in `TROAD-CARTOGRAPHY.md`), and
   his final camp placement. *(Priority raised, 2026-07-30: now that 1984 is read,
   these are the papers that carry the Kesik harbour and the 20-stade reading, and
   1984 contradicts them on three points — §1.11c. Partial answer to the standing
   question already: **1984 charts no scenes.** Its Fig. 1 is a single static sheet
   with the camp, ford, throsmos, tombs and divine stations on it, so if a
   scene-by-scene reconstruction exists it is in 1998, not here.)*
10. **Kayan 1991**, "Holocene Geomorphic Evolution of the Beşik Plain," *Studia
    Troica* 1, **79–92** (esp. 91). **Settles:** Beşik Bay's Bronze Age geometry —
    which is also the missing coordinate problem for `besik-bay`.
11. **Vacchi et al. 2013**, *Quaternary International* 328–29, **301–10**; and
    **Lambeck & Purcell 2005**, *QSR* 24, **1969–88**. **Settles:** the actual RSL
    value for the NE Aegean at ~3.2 ka BP, which is what tells us how much of
    Kayan's "fall" can be regional at all.
12. **✅ CLOSED 2026-07-30 — Cook 1973**, *The Troad*, **165–67** (borrowable
    scan; lending, not PD). Read off the page images by
    `RESEARCH-TROAD-TOPOGRAPHY.md` §9.2 (Grade A). **Settled:** Cook's own
    words are "an artificial cut… never completed", floor "perhaps 12–15 m
    a.s.l.", purpose-guess drainage of late-Roman date — first-hand, not
    Zangger's Turkish paraphrase, and it disagrees with Kayan's tectonic
    reading rather than confirming it. Applied at §1.9 and §2 above.
13. **Alfred Brückner 1912** (*AA* 26: 616–33) and **1925** (*AA* 39: 230–48, esp.
    246). Pre-1931, so **PD in the US** — worth hunting for a scan rather than a
    library visit. **Settles:** the two Yeniköy cuts and the Sigeion-harbour
    proposal at their origin.
14. **Kelletat 1975**, *NJb Geol. Paläont. Mh.* 6, **360–74**. **Settles:** the
    curve on which Kayan's Bronze Age fall rests.

---

## 6. Unverified — do not claim publicly

Two items left this list on 2026-07-29, when the 1980 *Science* full text arrived,
and one more on 2026-07-30 with the 2003 *Geology* full text; each is noted below
with the § that now carries it. Everything else stands.

- ~~**That Kraft, Rapp, Kayan & Luce 2003 put the LBA bay head ~1.2 km north of
  Hisarlık.**~~ — **SETTLED 2026-07-30 → now carried by §1.3, §2 and §3.1.** The
  paper says it, p. 166: "~6 stades (~1200 m) at the time of the *Iliad*", and
  claims their lithosomes and radiocarbon dates support it. **The attribution in
  `shore-bronze`'s note may stand.** Three things remain binding, and they are
  publishable caveats, not blockers:
  1. **It is Strabo halved, endorsed — not a measurement.** No core, no date and no
     figure in the paper is tied to that distance. Register `identification`, never
     `certain`.
  2. **Their own *Iliad* plate contradicts it**, drawing the nearest water 2.17 km
     out at bearing 334° with alluvium and marsh between (§1.3a). Say so; do not
     average the two.
  3. **"1.2 km" and Brückner's "ca. 1.2 km" and Strabo's 6 stades are one figure,
     not three witnesses** (§1.10). A plate note that stacks them is manufacturing
     agreement.
- **The "20 stades from Troia to the Achaean harbour" as Strabo's own statement.**
  Still not Strabo's own words: it is Luce's translation choice, and the PD
  Hamilton–Falconer translation attaches the 20 stadia to the Scamander's mouth
  (§1.10). **Now sourced exactly (2026-07-30):** the reading is printed in Kraft,
  Rapp, Kayan & Luce 2003, 165, in Luce's own translation, attributed "(J.V.
  Luce)", with his bracketed dates and a 200 m stade — and asserted at 166 as
  "Strabo's comment that the Homeric Greek ship station and camp were actually 20
  stades (4000 m) from Ilium (Troy)". **Two further findings that keep this on the
  list:** the same paper's figures draw the arcs at ~181–187 m to the stade, and the
  camp it plots sits at **5.4 km ≈ 27–29 stades**, not 20 (§1.3a, §1.11c). So
  "Strabo says 20 stades" is wrong; "Luce reads 20 stades" is right; and **"the camp
  is 20 stades from Troy" is contradicted by the only figure that draws it.**
  Earlier reinforcements stand: the 1980 paper prints no stade figure at all
  (§1.1), and Luce 1984's Note 5 reports the ancient debate's 6–20 band without
  adopting a figure (§1.11c).
- **That the Kesik cut existed in the Late Bronze Age.** New to this list,
  2026-07-30. Kraft, Rapp, Kayan & Luce 2003, 166 assert it as Nestor's wall and
  ditch and draw it on their 3250 BP plate; Cook 1973, 166–67 reads an unfinished
  artificial cut of probable late-Roman date; Kayan reads a natural tectonic
  depression; Kayan et al. 2003 say the bay there was unusable by Troia VI. Four
  readings, no cross-citation, İlhan Kayan on three sides (§1.9). **Nothing at Kesik
  goes on a geographic plate, and no Kesik feature is dated in our data until Kayan
  1995 and 2009 are read** (§5 items 6, 7).
- ~~**Anything about Luce's camp beyond his abstract**~~ — **SETTLED 2026-07-30 →
  now carried by §1.11.** The full text is in hand. **Still binding, and now for a
  sharper reason:** the "about four miles west" of the abstract is contradicted by
  the body's own two figures (4–5 km, p. 41; 5–6 km across the water, p. 35), so
  **no anchor may be placed from it**. What may be used is an **extent** along the
  Sigeum ridge's eastern flank at 4–5 km — the line `shore-bronze` already carries.
  **Still unverified:** the strip's northern and southern ends, which rest on Cook
  1973, 165 ("Spratt's plateau") and on a wall-and-ditch line Luce proposes without
  evidence; and any harbour attributed to Luce 1984, which names none.
- **Luce 1984 on sea level or the barrier.** He works under Kraft et al.'s stated
  premise — "Assuming that the sea-level of the Aegean stabilised about 5,000
  years ago, THEY have been able to determine…" (p. 31; the assumption is
  reported as theirs, not asserted by Luce independently) — which is not what
  Kraft's own Fig. 6 prints (§1.8). Do not cite him for either (§1.11).
- **Beşik Tepe's LH IIIB proportions** (c. 100 graves, ~1/3 of fine wares, <1% in
  Troia VI/VII). Repeated in our own `TROAD-SOURCES.md` and on amateur sites; no
  scholarly source reached (§1.12).
- ~~**The identification of Brückner's "Pınarbaşı" with the OSM village at 39.8880,
  26.2715.**~~ **SETTLED for practical purposes, 2026-07-29 → now carried by §3.2a″.**
  Kraft's Fig. 2 (1980, 778) plots Pınarbaşı at the southern end of the Kara
  Menderes plain beside drill hole T7, at the gorge mouth, with Mahmudiye and
  Üvecik to its west — the same village OSM names, and the only Pınarbaşı a 17 km
  inland measurement can reach. Residual doubt: we still have not seen Brückner's
  own Fig. 3, so this is an inference from two maps agreeing, not from his caption.
  The 7.7 km figure may be used.
- ~~**Kayan's plotted sea-level curve**, and therefore any statement of the LBA
  sea-level position in metres relative to today~~ — **PARTLY SETTLED, 2026-07-29 →
  now carried by §1.8 and the sea-level row of §2.** A published LBA sea-level
  *position* now exists in a source we have read: Kraft, Kayan & Erol 1980's Fig. 6
  puts sea level **at present level at 3250 BP** and **+2 m at 4500 BP**, from
  Erol's curve. **Still unverified:** Kayan's own plotted curve (Kayan 2014, fig. 8),
  and any figure between those panel values — no interpolation, and no metre value
  for any date the panels do not label. Also note what the 1980 curve is: **ref. 17,
  "O. Erol, unpublished data"** — cite it as the paper's stated basis, never as an
  independently published curve.
- **The width of the Bronze Age barrier.** Nothing surveys it. Our layer already
  says the band's width is a symbol; keep it that way.
- **Any claim that a Bronze Age harbour has been located.** The literature's
  positions are: Beşik (**Kraft, Kayan & Erol 1980, 782** — first-hand, and the
  earliest of them; then Kraft et al. 1982, Kayan 1991, Korfmann), Kesik
  (A. Brückner for Sigeion; Zangger 1992; Kraft et al. 2003a; **Luce 2003 — not
  Luce 1984**, which names no harbour at all and never mentions Kesik: in 1984 the
  shelter *is* the embayment, §1.11c), an artificial
  basin (Zangger & Mutlu 2015, explicitly a working hypothesis), and no viable
  harbour at all (Kayan et al. 2003). A map that picks one must name whose it is
  **and which year** — Kraft moved from Beşika to Kesik between 1980 and 2003, and
  Luce moved from the received view (1975) to the Sigeum ridge (1984) to Kesik
  (by 2003), so "Luce" without a year names three incompatible things
  (§1.9, §1.11c).
- **The Kesik cut's date and purpose.** Unresolved, and now sharper (2026-07-30,
  `RESEARCH-TROAD-TOPOGRAPHY.md` §9.2): Kayan reads it as **natural**, a tectonic
  depression widened by foot traffic; Cook reads it as **artificial**, "never
  completed", and guesses late-Roman drainage (Constantine's new city) — the two
  disagree on whether it was dug at all, not merely on when. Korfmann dated the
  (different) Yeniköy canal to the 18th century AD; an 18th-century engineer
  thought that one Bronze Age. Its floor at 13.7 m a.s.l. (Kayan) / "perhaps
  12–15 m" (Cook, independently bracketing it) is the one hard fact both sides
  share.

---

## 7. Appendix — coordinates for three gazetteer gaps, from OSM

The handoff (§3.8, §3.12) flags `besik-bay`, `uvecik-tepe` and `adramyttion` as
`certain` with no coordinates. Two of the three have OSM points. **These are
geometry from a licensed database, not identifications** — the gazetteer lane
should confirm each against a second source before use, and the coordinates come
with OpenStreetMap's ODbL attribution.

| id | OSM point | OSM feature | note |
|---|---|---|---|
| `besik-bay` | 39.9171, 26.1594 | `Beşiktepe`, Yeniköy, Ezine (attraction) | This is **Beşik Tepe the mound**, not the bay; the bay lies immediately west, ~8 km SW of Hisarlık. Use the mound as the anchor and say so, or take the bay's centroid from the Copernicus water mask. |
| `uvecik-tepe` | 39.9003, 26.1992 | `Üvecik Tepe`, Kumburun, Ezine (archaeological_site) | ~6.3 km S, 3.4 km W of Hisarlık. Consistent with the Roman tumulus of Festus. |
| — | 39.9608, 26.1680 | `Demetrius tumulus`, Çanakkale (archaeological_site) | Returned by a search for "Kesik". Probably Kesik Tepe, the mound near Sigeion that the fourth century took for Achilles' tomb — but OSM's name is a different tradition. **Do not adopt without checking. Corrected 2026-07-30: it is not a tumulus.** Cook 1973, 165–66 (Grade A, `RESEARCH-TROAD-TOPOGRAPHY.md` §9.2): Schliemann himself probed it with Virchow and Burnouf in 1879 and found "a natural tertiary hump with never more than 5 ft. of earth on top" — Forchhammer and Ulrichs had already called it natural. "Demetrius" names the adjacent Christian chapel, not a hero. **Three heroic traditions attach, none certain:** Antilochus (the 19th-c. travellers, per Cook), Achilles (the fourth century, per this row), Festus (Schliemann's own reading in 1868 — before he moved the Festus identification to `uvecik-tepe` by 1879). Tier no higher than `traditional`; name whichever tradition is cited. |
| `adramyttion` | not looked up | — | Out of this dossier's area; belongs to the Troad-topography lane. |

Source: [Nominatim / OpenStreetMap](https://nominatim.openstreetmap.org/),
queried 2026-07-29; © OpenStreetMap contributors, ODbL 1.0.

---

## 8. Reproducing the DEM measurements in this file

All of them run offline against the tiles already cached in
`build/terrain-tiles/` (z13 over the plain sheet's bbox), using the PNG decoder
and Web-Mercator helpers in `scripts/prep-terrain-contours.py` loaded as a module.
The three scripts are in this session's scratchpad
(`valley_profile.py`, `valley2.py`, `check_derivation.py`, `check2.py`); each is
about 30 lines and none writes to the repo. The one thing to get right: sample the
valley floor within **lon 26.19–26.29**. A wider window finds the Aegean west of
the Sigeum ridge and reports sea level as the "valley floor" — which is how the
first cut of §3.2 got the wrong answer.
