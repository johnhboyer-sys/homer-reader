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
§1.3a–d and the method note at §3.7); **Kraft, Kayan, Brückner & Rapp 2003
(= 2003a), all seventeen pages and all ten figures**, and **Kayan, Öner, Uncu,
Hocaoğlu & Vardar 2003, all twenty-three pages and all seven figures** (both in
`research-cache/troia-troad-2003-kayan-chapters.pdf`, an author-shared 70-page
extract of the Springer volume from İlhan Kayan's academia.edu page, obtained and
read 2026-07-30 — §§1.4, 1.4a, 1.5, 1.5a–c; the colour plates were measured the
same way as the *Geology* figures, §3.7a); **Kayan 2014, all thirty-four pages and
all twenty figures** (author-shared copy from İlhan Kayan's ResearchGate page,
cached at `research-cache/kayan-2014-troia-geoarchaeology.pdf`, obtained and read
2026-07-30 — §1.5d; figures measured per §3.7b).

**Ten more read in full on 2026-07-30**, from the author's academia.edu
click-list, each with an extraction note in `research-cache/`:

| source | notes file | what it settled |
|---|---|---|
| Kraft, Kayan & Erol **1982**, 11–41 | `kayan-1982-notes.md` | §1.2 is no longer unseen; Erol's separate curve (§1.5a); a **third** stade conversion (§1.10); the Beşika hypothesis at its origin (§1.11c) |
| Kayan **1988**, *PPP* 68, 205–18 | `kayan-1988-sea-level-notes.md` | the Beşik barrier's first drilling-based treatment, with Troy VI sherds in it (the earliest *print* is 1982 — §1.5b) |
| Kayan **1995**, *ST* 5, 211–35 | `kayan-1995-troia-bay-notes.md` | the Kesik measurements at first hand, the "Bronze Age Regression" coinage, and **the 2003b wall-and-ditch citation does not check out** (§1.9) |
| Kayan **1996**, *ST* 6, 239–49 | `kayan-1996-st6-notes.md` | an independent stratigraphic proof of the ~2 m fall; the north-foot land surface at ~3500 BP (§1.5b) |
| Kayan **1997** (= 1997a), NATO ASI I/49, 431–50 | `kayan-1997-regression-notes.md` | argues **against** tectonics — one leg of the now-closed 2003 misattribution (§1.5a, §6) |
| Kayan **2000**, *ST* 10, 135–44 | `kayan-2000-water-supply-notes.md` | the springs and the buried-hot-spring hypothesis (`RESEARCH-TROAD-TOPOGRAPHY.md` §6.8) |
| Kayan **2002**, *Mauerschau* 3, 993–1004 | `kayan-2002-footslope-notes.md` | the 5000–3500 BP interval; the north-footslope platform's depth; the **battlefield surface** (§1.4b) |
| Kayan **1997b**, *ST* 7, 489–507 (Çıplak valley) | `kayan-1997-ciplak-notes.md` | that this paper carries **no causal argument at all** — which is what breaks the 2003 tectonic citation (§1.5a, §1.5e, §6); a destruction layer and a second rock-cut ditch at the Lower City's southern foot (§1.5e) |
| Kayan **1999**, *QSR* 18, 541–48 | `kayan-1999-qsr-notes.md` | **the letter assignment**, from Kayan's own reference list — 1997a = NATO, 1997b = Çıplak (§1.5a, §6); a fifth printing of 5000–3500 BP / ~2 m; the anti-tectonic position restated in 1999's own voice (§1.5a, §1.5f) |
| Kayan **2009**, *ST* 18, 105–28 (Kesik / Alacalıgöl) | `kayan-2009-kesik-notes.md` | the Kesik canal first-hand at 13 m and <2 m fill; **the "800 m" and "before 1300 BC" expectations NOT met** (§1.9); the wall-and-ditch absence a second time; Alacalıgöl; Kesiktepe's 20th-century military use |

**Abstract or publisher metadata only:** Kayan 2019; Seeliger et al. 2021.

**Not seen at all** (the Kayan papers in the table above are now excepted):
**Kayan 1991**; Kayan 2001 and 2006;
Cook 1973; Luce 1995, 1998, 2003; Kelletat 1975; Vacchi et al. 2013. Their
content appears below **only** where a source I did read quotes or reports them,
and it is labelled as second-hand every time. §5 lists them for the library.

**What the Kayan 2014 PDF is, and the page range CONFIRMED (2026-07-30).** 39 PDF
pages. **PDF pp. 1–5 are the volume's front matter for *Teil 2*** — series title
(printed 538), title page (539), imprint and ISBN (540), part of the contents
(542), addresses of the authors (543). That is where the "Seite 538" layout marker
on the first page comes from, and it is **not** the chapter's page. **PDF pp. 6–39
are the chapter, printed pp. 694–727**, verified two ways: the InDesign layout
marker in every page header runs "Seite 694" … "Seite 727" consecutively, and the
printed running heads and folios read 695, 696, 697 … 727 on the pages themselves.
**The dossier's expected 694–727 is correct and no citation needs repair.** So is
the expectation that **fig. 8 is the sea-level curve** — it is, at printed p. 709.
Imprint detail worth carrying into the citation: the volume is *Teil 2*, and the
publisher is **Bonn: Habelt** (ISBN 978-3-7749-3902-8), not Tübingen.

**What the author-shared extract carries, checked chapter-opening by
chapter-opening (2026-07-30).** Front matter (title page, editors, foreword,
preface, the complete table of contents, pp. v–xi), then **three consecutive
chapters and nothing else**, plus the back cover:

| chapter | authors | title | printed pp. | PDF pp. |
|---|---|---|---|---|
| 23 | J. Göbel, M. Satır, A. Kadereit, G. A. Wagner, İ. Kayan | "Stratigraphy, Geochemistry and Geochronometry of Sedimentary Archives Around Hisarlık Hill — a Pilot Study" | 341–59 | 11–29 |
| 24 | J. C. Kraft, İ. Kayan, H. Brückner, G. Rapp | "Sedimentary Facies Patterns and the Interpretation of Paleogeographies of Ancient Troia" | 361–77 | 30–46 |
| 25 | İ. Kayan, E. Öner, L. Uncu, B. Hocaoğlu, S. Vardar | "Geoarchaeological Interpretations of the 'Troian Bay'" | 379–401 | 47–69 |

**Luce's chapter is NOT in the extract.** "2 The Case for Historical Significance
in Homer's Landmarks at Troia … 9 · J. V. Luce" appears in the table of contents
(PDF p. 8) and nowhere else. §5 item 9 stays open, and §1.11c's third position is
still second-hand. Neither is Zangger's ch. 21 ("Some Open Questions About the
Plain of Troia," 317–24), which ch. 24 cites as "this Vol." Both chapters' own
reference lists are also absent — each ends "All references of the chapters are
presented altogether end of the book. Total 30 pages of the list are not included
here," so **no bibliographic claim may be made about what these two chapters
cite**, only about what they name in their text.

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

### 1.2 Kraft, Kayan and Erol 1982 — the long version, READ IN FULL 2026-07-30

**Claim (existence and scope only).** A 31-page treatment of the same work, in a
book devoted to the archaeological geology of Troy.

- Citation: Kraft, John C., İlhan Kayan, and Oğuz Erol. "Geology and
  Paleogeographic Reconstructions of the Vicinity of Troy." In *Troy: The
  Archaeological Geology*, edited by George Rapp and John A. Gifford, 11–41.
  Princeton: Princeton University Press, 1982.
- Authority: **geometry** for Figs. 7–10 and the five dated panels; **prose** for
  the Besika argument and the causal discussion.
- Verified how: **full text, pp. 11–41**, from the author-shared copy cached at
  `research-cache/kayan-1982-rapp-gifford-geology-ch.pdf`, read 2026-07-30;
  extraction note at `research-cache/kayan-1982-notes.md`. The chapter identity
  matches this dossier's citation exactly — editors Rapp and Gifford, Troy
  Supplementary Monograph 4, Princeton, chapter I at pp. 11–41.
- **What the pull bought, and what it did not.** The **core logs are not here.**
  The volume's appendices (sediment-sample catalogue, grain-size statistics,
  pp. 141–197) are outside the cached extract and are the only likely home of
  depth-by-depth logs; the chapter itself prints **four interpretive
  cross-sections**, not log sheets: **Fig. 7 (p. 22)** N–S across the Simois
  valley (hole T4, ~45 m of sediment); **Fig. 8 (p. 23)** E–W from the mound to
  the Sigeum promontory (T3, T5; marine clay-silt floor ~9800 BP, molluscan sand
  7663–8547 BP); **Fig. 9 (p. 25)** N–S along the paleo-Scamander axis, six
  holes, its radiocarbon dates "corrected to the 5730-year half-life, **but not
  calibrated**" (p. 24 — flag before quoting any one of them as a calendar year);
  **Fig. 10 (p. 26)**, the facies-correlation schematic.
- **The five dated panels are the 1980 Fig. 6 series built up from data, one
  period at a time:** Fig. 13 (p. 33, ca. 10,000 BP, "very schematic"); Fig. 14
  (p. 33, ca. 7000 BP); Fig. 15 (p. 33, ca. 4500 BP, Troy I–II); **Fig. 17
  (p. 35, ca. 3250 BP, Troy VI/VII — the Trojan-War panel)**; Fig. 19 (p. 37,
  ca. 2000 BP, built from "our drilling program and the description of Strabo").
  The chapter's own hedge on the Trojan-War panel, verbatim (p. 35): "We believe
  that the major marine embayment shown in Figure 17 is realistic and
  well-supported by our data. **The precise location of the shoreline is, of
  course, arguable due to our limited number of boreholes and assumptions of
  contemporary sea level.**"
- **Inland reach, in the running text:** "The radiocarbon dates prove the
  existence of a marine reentrant **up to 16 km. south of the Dardanelles** and
  possibly to the vicinity of Pınarbaşı" (p. 25–26), and in the conclusions "a
  major marine embayment stretching **about 15 km.** south of the Dardanelles at
  the peak of the Versilian Transgression" (p. 39). Both sit inside the range
  §1.5/§3.2 already carries, and predate Kayan et al. 2003's "17 km" by 21 years.
- **Bay at the citadel, Troy I–II** (p. 34): "The marine embayment schematically
  reconstructed in Figure 15 extended to **within a few hundred meters of the
  citadel** in the time of Troy I and II… the Trojans could easily have used some
  part of the nearby shoreline as a landing place for ships of their own." No
  narrower figure is given; do not over-read "a few hundred meters".
- **No Kesik.** A full-text search for "Kesik" in every case variant returns
  **zero hits** — the chapter's only western-embayment discussion is Besika
  (§1.11c). Recorded as a positive absence: Kesik enters this group's literature
  with Kayan's *Studia Troica* series, not with either 1980 or 1982 (§1.9).
- **Figure-measurement caveat.** Nothing in this chapter was measured
  pixel-by-pixel the way §3.7's figures were; the OCR text layer garbles Turkish
  diacritics throughout. Values above are the chapter's own printed numbers, not
  remeasurements, and no bearing or distance may be lifted from its plates.
- **Confirmed as the same work, from the 1980 paper's own reference list**
  (full text, 2026-07-29): ref. 20, p. 782, cites it as forthcoming — "J. C.
  Kraft, I. Kayan, O. Erol, in 'Geology and paleogeographic reconstructions in the
  vicinity of ancient Troy,' G. Rapp, Jr., and J. Gifford, Eds. (Troy Supplementary
  Monograph 4, Princeton Univ. Press, Princeton, N.J., 1980)". Note the drift:
  the title as printed in 1980 differs from the 1982 published title, the series is
  named *Troy Supplementary Monograph 4*, and the imprint year was expected to be
  1980. Anyone hunting the volume in a catalogue should try both titles.
- ~~What the 1980 full text does **not** relieve: the long version is still the
  only place the seven core logs are printed at length…~~ **ANSWERED
  2026-07-30 by the chapter itself: the core logs are not in it** (above). The
  p. 40 Beşika quotation is here and is quoted at §1.11c; the map series was
  already in hand as Fig. 6 of the 1980 paper (§1.1).

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
  - **⚠ CHALLENGED 2026-07-30 by the colour plates of the companion chapter, and
    the challenge should be taken seriously (§1.4a).** Kraft et al. 2003a's Fig. 10
    (p. 374) is the same group's *Iliad*-time plate at the same nominal date on a
    kindred base, it is in **colour with a printed legend**, and its sea reaches
    **0.28 km at bearing 330°** — a factor of eight nearer. Two reasons to suspect
    the method here rather than the disagreement: this figure is a **1-bit stencil**
    in which the sea is unpatterned white, and **white is also used for at least one
    land feature on this very sheet** — the strip labelled "Swelling of plain",
    which is the Homeric *thrōsmos pedioio*, a rise of dry ground. A flood fill
    seeded in the Aegean will stop at the first outline it cannot cross, whether or
    not that outline is a coast. **Re-run §3.7's steps 4–5 on Fig. 5 with probes
    inside the "Swelling of plain" strip and inside the Simois inlet before quoting
    2.17 km again.** Until that is done, §2's LBA-shore row carries both numbers and
    neither is the dossier's answer.
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

### 1.4 Kraft, Kayan, Brückner and Rapp 2003 (= 2003a) — the facies chapter, READ IN FULL 2026-07-30

- Citation: Kraft, John C., İlhan Kayan, Helmut Brückner, and George Rapp.
  "Sedimentary Facies Patterns and the Interpretation of Paleogeographies of
  Ancient Troia." In *Troia and the Troad: Scientific Approaches*, edited by
  Günther A. Wagner, Ernst Pernicka, and Hans-Peter Uerpmann, 361–77. Berlin:
  Springer, 2003.
- Verified how: **full text, pp. 361–77, and all ten figures**, in the
  author-shared extract `research-cache/troia-troad-2003-kayan-chapters.pdf`
  (Kayan's academia.edu copy; provenance and contents at §0). Figures rendered at
  500 dpi and measured against their own printed scale bars; method at §3.7a.
- **Shape of the thing.** Seventeen pages, ten figures. Four of the ten are
  *Aegean analogues* and not Troad geography at all — Spherchios/Thermopylae
  (Fig. 4, p. 367), Meander (Fig. 5, p. 368), Pamisos (Fig. 6, p. 369), Cayster/
  Ephesus (Figs. 7–8, pp. 370–71). The Troad content is Fig. 1 (p. 363, air-photo
  lineaments after Erol 1972), Fig. 2 (p. 365, Spratt 1839 — **and it carries the
  legend for the whole chapter**, §1.4a), Fig. 3 (p. 366, cross section), and the
  two reconstruction plates **Fig. 9 (p. 373) and Fig. 10 (p. 374)**, which are
  Brückner's Scenario I and Scenario II drawn out. The Strabo argument is §5,
  pp. 375–76.

**THE CORRECTION THIS CHAPTER FORCES: it does NOT say the Kesik plain was the
harbour.** The dossier has carried that claim since §1.6 on Brückner et al. 2005's
report of it. The chapter's own words, p. 376, entire:

> "E. Zangger, (this Vol.), proposes that the Kesik cut was either a failed attempt
> to create a ship canal from the Aegean Sea to the 'harbor' or a deep cut to
> facilitate the dragging of ships into an interior harbor to avoid the strong
> currents of the Dardanelles. Zangger further proposes that three possible harbors
> were used in the three western embayments of the Scamandrian Gulf in Bronze Age
> times. **We agree that all three embayments southwest, west, and northwest of
> Troia, at the foot of the Sigeum ridge, had excellent harbor potentials.
> However, the southerly embayment northeast of Beşik Bay was bypassed by the
> prograding Scamander delta before Late Bronze Age times.** Finally, we agree,
> along with J.V. Luce that the Beşik embayment always provided a place of shelter
> for ships; particularly, those wishing to sail up the Dardanelles against its
> strong currents."

Read exactly: they endorse **Zangger's** three-embayment proposal in the weak form
"had excellent harbor potentials", **name no single best candidate**, strike out
the southernmost (Yeniköy) as already silted, and end by agreeing with Luce about
**Beşik**. "Kesik plain as the best candidate for a natural harbour" is Brückner's
paraphrase (2005 §§20–21), not this chapter's sentence. **Fix §1.6, §1.9 and §2
accordingly, and do not attribute a Kesik harbour to Kraft et al. 2003a in those
words again.**

**And on the Kesik cut itself, 2003a agrees with 2003b, not with Kayan** (p. 376,
verbatim and entire):

> "The Kesik cut immediately south of the Greek camp and Ship station may be a
> defensive trench before a palisade constructed by the Greeks if proven to be of
> three millennia or greater age (Luce 1998). It is certainly a manmade trench as
> proven by Kayan (1996)."

Two things follow. (a) The wall-and-ditch reading is **2003a's as well as 2003b's**
— so the five-cornered table at §1.9 has one corner occupied twice, and the two
papers source it to *different* publications (2003a → **Luce 1998**; 2003b →
**Kayan 1995**). (b) "It is certainly a manmade trench as proven by Kayan (1996)"
is asserted **over the signature of İlhan Kayan**, who in the facing chapter of
the same volume writes that "there is no information about the purpose and time of
construction" and floats "perhaps it is an unfinished canal construction"
(Kayan et al. 2003, 399; §1.5b). One volume, two chapters, one co-author, two
positions. Record both; do not average them.

- **The summary line, first-hand and confirmed at p. 375:** "In our research over
  the past three decades, we attempted to test phrases in the *Iliad*. **Nothing in
  our research negates the writings of Homer!**" Brückner's page cite is right.
- **The Strabo apparatus is the same as 2003b's, in Luce's same translation
  (p. 375) — but WITHOUT the metric conversions.** p. 376: "Note the 12 stades to
  the 'Achaian's harbour' as thought by New Ilium peoples of 0 B.C./A.D., and
  Strabo's note that the 12 stade distance would have only been half that, ca. 6
  stades at the time of the *Iliad*. Further note Strabo's comment that the
  (Homeric) Ship Station is actually 20 stades from Ilion and close to Sigeum."
  **No metres appear anywhere in this chapter.** So the "~1200 m", "2400 m" and
  "4000 m" that our `shore-bronze` attribution rests on are **unique to 2003b**
  (*Geology*, p. 166, §1.3), and the 200 m stade is 2003b's alone. Cite the letter.
- **The chapter's own disclaimer, p. 362**, in a softer form than 2003b's: "With up
  to 20 m of alluvium on the southern Scamander plain, **we cannot hope to locate
  precisely** the river channels of antiquity." (*Geology* drops "precisely" —
  §1.3b. Same sentence, two strengths, same year.)
- **Fig. 10's caption is the only place either 2003 paper says what its Homeric
  marks are** (p. 374): "Selected ¹⁴C dates from Kayan (1995, 1996, 1997a) are
  shown along with J.V. Luce's (1998) location of the Greek camp and ship station
  at 20 stades (*A*) from Troia and (*B*) the Achaean harbor as perceived by the
  people of New Ilion at 12 stades from Troia (false harbor of Strabo 13, 1, 36).
  Note that all ¹⁴C dates are from molluscs, indicating marine to brackish salinity
  environments of deposition."
- Authority: **geometry** for Figs. 9 and 10 (relative geometry, §1.4a);
  **identification** for the Kesik cut, the camp and the Beşik shelter; **prose**
  for the Strabo argument and the analogues.

#### 1.4a The two reconstruction plates, measured — and they put the sea at the citadel's foot

**The legend is printed once, on Fig. 2 (p. 365), and its caption says so:
"Legend applies for most figures herein."** That matters, because it is what makes
the colour plates readable without guessing. Verbatim, the fourteen entries:
Modern Town or Village · Mountainous Terrain · Low Plateau · **Shallow Marine Sand
Shoals** · High Plateau · **Alluvium** · **Sand Dunes and Coastal Barriers** ·
**Marsh** · Travertine Fan · Distributary Channels · Meandering River · **Sandy
Coastline** · Archaeological Sites · Ancient Towns. Open water carries no swatch —
it is the pale blue, and it is unambiguous. **So on these plates "is it sea?" is a
colour question, not a pattern question**, which is exactly what the *Geology*
paper's 1-bit stencils are not (§1.3a, §3.7).

**Fig. 9 (p. 373) = Kayan's scenario.** Caption: "Holocene Epoch paleogeographies
of Troia and its environs from Neolithic to present times using the present
asmak-dominated coastline of the Dardanelles as the interpretive model and a 2-m
sea level drop to ca. 1400 B.C. as an indicator of accelerated delta progradation.
(Kayan 1995)." Labelled shoreline stages: **3500–4000 BC · 2500–3000 BC ·
500–1000 BC · Present Coastline**, plus **1500 BC** on a yellow dune/barrier band
across Besika Bay. Text at p. 372: "The location of shorelines in Fig. 9 is based
on Kayan's explanation of a sea-level drop to −2 m ca. 3400 years ago and back to
the sea level of today."

**Fig. 10 (p. 374) = Kraft's own.** Caption: "…in Neolithic-Early Bronze Age times,
**1250 B.C. ca. the time of the *Iliad***, 0 B.C./A.D. in Strabo's time, and the
present coastline. This interpretation emphasizes quiescent embayment coastal
environments gradually changing to the current dominated Dardanelles shoreline of
present time." Labelled: **3000–3500 BC · 1250 BC · 2000 BC/AD** (i.e. 2000 BP,
the Strabo shore, drawn as a yellow **Sand Dunes and Coastal Barriers** band) ·
Present Coastline, plus **1280 BC** on the Besika barrier; "Greek Camp and ship
Station" with a double arrow on the ridge's **Aegean** flank; "Kesik cut" hatched
across the ridge immediately south of it; ¹⁴C points at 3850, 3550, 3350, 2550,
1450 BC (west), 1550, 1250 BC (centre), 3750, 3250, 2250 BC (east).

**Measured (figure measurement, this dossier; both plates are the same base at the
same scale — bar 0–1–2 km = 175 px/km at 500 dpi; Troia dot at (1655, 1690) on
Fig. 9 and (1650, 1670) on Fig. 10; nearest pale-blue blob per bearing):**

| bearing from Troia | Fig. 9 (Kayan scenario) | Fig. 10 (Kraft, 1250 BC) |
|---|---|---|
| 000° (N) | 0.35 km | 0.33 km |
| 015° | 0.41 km | 0.38 km |
| 030° | 0.70 km | 0.49 km |
| 045° | 1.92 km | 0.70 km |
| 060° | 1.87 km | 1.57 km |
| 075°–135° | no water | no water |
| 195° | 1.47 km | 0.39 km |
| 225° | 0.41 km | 0.54 km |
| 255° | 0.44 km | 0.31 km |
| 270° (W) | 0.35 km | 0.29 km |
| **285°** | 0.31 km | **0.27 km** ← nearest |
| 300°–330° | 0.31 km | 0.28–0.29 km |
| 345° | 0.33 km | 0.30 km |

**Both plates put open water 0.27–0.41 km from the citadel dot through the whole
W–NW–N sector.** Troia sits on the eastern shore of a water body that runs north
along the foot of its own ridge while the bird's-foot delta lobes prograde north
up the middle of the plain — an interdistributary embayment, which is the shape
Kraft, Kayan & Erol 1980's "projection or promontory at the edge of a marine
embayment" describes (§1.1) and which Kayan's own Fig. 7 draws for 6000 BP
(§1.5c).

**AND THIS CONTRADICTS THE DOSSIER'S OWN MEASUREMENT OF THE *GEOLOGY* PLATE.**
§1.3a measures the nearest water on *Geology* Fig. 5 — the same group, the same
year, the same nominal date (ca. 3250 BP / 1250 BC) — at **2.17 km, bearing 334°**,
with alluvium and marsh drawn between. Fig. 10 here says **0.28 km at 330°**. A
factor of eight. Recorded, not harmonised, and with the two caveats that bear on
which to trust:
1. **The colour plate is the less ambiguous artefact.** On Fig. 10 the sea is a
   flat pale blue against a legend; on *Geology* Fig. 5 the sea is unpatterned
   white in a 1-bit stencil, and white is also used for at least one *land* feature
   on that sheet (the strip labelled "Swelling of plain" — the Homeric *thrōsmos*,
   which is a rise of the plain and not water). **§1.3a's flood-fill and its
   six-probe leak test should be re-run before its 2.17 km is quoted again**, and
   until it is, §2's LBA-shore row must carry both numbers.
2. **Neither is a survey.** The two 2003 chapters draw the same ground from the
   same cores at the same date and disagree by 1.9 km. That spread *is* the
   finding: it is the error bar on "where the Bronze Age shore was", and it is
   wider than the 1.2-vs-2.17 km argument the dossier has been having with itself.

**The barrier symbol, and where each plate puts it** (figure measurement, this
dossier; "Sand Dunes and Coastal Barriers" is the yellow-with-triangles swatch,
"Sandy Coastline" the yellow dotted arc):

- **Fig. 9 (Kayan): no barrier anywhere on the Scamander delta front.** The only
  yellow is the Besika band ("1500 BC") and the Kum Kale dunes, first hit at
  **5.49 km, bearing 330°** from Troia.
- **Fig. 10 (Kraft): a barrier IS drawn on the Scamander front — and it is dated
  2000 BP, not Bronze Age.** The yellow band runs east from the Sigeum ridge along
  the "2000 BC/AD" shoreline, first hit at **2.55 km (330°) and 3.04 km (315°)**.
  Besika again carries its own band, here labelled "1280 BC".

That is the barrier question answered on the plates, and it agrees with both
chapters' prose (§1.5b, §2, §3.3): **the Bronze Age barrier-and-lagoon of this
literature is at Beşik Bay; the Scamander-front barrier is Roman-period.**

#### 1.4b The battlefield surface — Kayan's own move from the geology to the poem, NEW 2026-07-30

The dossier's battlefield-axis material (§1.3a, §1.4a) has come entirely from the
Kraft chapters. **Kayan makes the argument himself, in his own voice, in 2002.**
Conclusions, point 2 (Kayan 2002, 1003, verbatim and entire):

> "The transition zone ends with a delta plain in the western surroundings of
> Troy. Although this surface is about 0.5 m above present sea level, sea at that
> time was about 2 m below its present level, and the coastline was distant.
> **Characteristics of the surface recall Homer's descriptions of the
> battlefield: a sand-covered and dusty plain and some river channels, which were
> probably distributary 'azmak' channels. Thus, there is no need to look for a
> battlefield in the distance for the period of Troy VI.** Furthermore, it must be
> taken into account that the surface of the Karamenderes plain to the west was
> generally wet or covered by swamps in this period, and was not suitable for
> passage or battle."

- Authority: **prose**, and the chapter is explicit that it is interpretation —
  "there is no need to look for a battlefield in the distance" is a reading, not a
  measurement. **It carries no coordinate and must not be drawn as a shape on any
  plate.** What it licenses is a **prose annotation** saying which zone of the
  existing reconstruction was dry and passable at the relevant date.
- Verified how: full text, `research-cache/kayan-2002-footslope-notes.md`;
  page range 993–1004 confirmed against the volume's table of contents.
- **Two things it does, and one it does not.** It supplies a positive
  geomorphological case for the battle at the citadel's **immediate western foot**
  — a dry, sand-covered delta-fan surface — rather than out on the Karamenderes
  plain, which the same sentence rules unsuitable "for passage or battle". And it
  comes from the author who elsewhere insists the plain was never suitable for
  harbour activity (§1.5, abstract): the two claims are compatible — a dry
  delta-fan near the ridge against a shallow swampy bay farther west — but they
  are **separate sentences on separate pages and must be cited separately, never
  blended into one**.
- **Citation form.** The volume's table of contents prints the title as
  "Paleogeographical **Reconstruction**… Western **Foot-Slope**"; the article's own
  first page and running head print "**Reconstructions**… **Footslope**". Use the
  article's form, per the convention this dossier already applies to
  "Troian"/"Trojan" (§1.5). Full citation: Kayan, İlhan. "Paleogeographical
  Reconstructions on the Plain Along the Western Footslope of Troy." In
  *Mauerschau: Festschrift für Manfred Korfmann*, edited by Rüstem Aslan, Stephan
  Blum, Gabriele Kastl, Frank Schweizer, and Diane Thumm, vol. 3, 993–1004.
  Remshalden-Grunbach: Verlag Bernhard Albert Greiner, 2002. (§1.5's "unseen
  series" list carried this with neither editors nor publisher; both are now
  supplied, and the editors are the five festschrift co-editors — Korfmann is the
  honorand, not an editor.)
- **Scope warning.** This chapter is **not** about Kesik, the Yeniköy ridge or the
  Kesik canal — a search of the full text returns nothing for "Kesik". Its area is
  the plain immediately north and west of the citadel: the Çıplak valley mouth,
  the ground between the Kalafatlı Azmak and the old Dümrek channel, and the
  bedrock platform under the north/northwest footslope (§1.5b).

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
- Verified how: **full text, pp. 379–401, and all seven figures** (author-shared
  extract, §0), 2026-07-30 — the abstract above is now confirmed word-for-word
  against the printed page 379. Page range and authorship confirmed on the
  chapter opening.
- **Two corrections to our data fall out of this.** (a) Our plate cites this
  chapter as sole-authored by Kayan and without pages — it has five authors and
  runs 379–401. (b) Springer's own page renders the title with "Trojan"; Brückner
  and the volume use "Troian". Use the volume's form.
- **The 17 km is in the abstract and NOWHERE in the body.** The body's statement
  of the same fact is qualitative: "about 7000–6000 years ago, an estuarine bay in
  the present lower Karamenderes valley west of Troia, extended southwards as far
  as the north of Pınarbaşı–Mahmudiye (Fig. 1)" (384); "By 7000 years ago, the old
  valley bottom was completely covered by sea water and the shoreline was near
  Pınarbaşı–Mahmudiye to the south" (389). So the 17 km is the abstract's own
  reduction of a place-name, and §3.2's reconciliation of it with Kraft's 10 km
  (§3.2a) stands unaltered — but the figure may not be cited to a body page.

#### 1.5a The sea-level curve, plotted, dated and measured — this is the one the dossier has been missing

**Fig. 2, p. 383: "Middle–Late Holocene relative sea-level changes in the Troia
area. (Kayan 1991)."** A single plotted curve, −3 m to +2 m against 7000 BP → today,
carrying **two** annotation bars: the cultural periods (Beşik Sivritepe, Kumtepe I
A, Beşik Yassıtepe, Troia I–IX, İlion, İlium) and, keyed on to them, the labels
**"Trojan War"**, **"Homer's time"** and **"Strabo's time"**. Kayan therefore
publishes, himself, a sea level *for the Trojan War*, which is precisely what §6
has been refusing to state.

**Measured** (figure measurement, this dossier; 300 dpi render, axis bar segments
86.7 px per metre with 0 m at y = 748, time ticks 178.9 px per 1000 yr with 0 ka at
x = 1578; the curve is the heavy line bounding the stipple):

| ka BP | RSL (m) | ka BP | RSL (m) |
|---|---|---|---|
| 6.8 | −3.1 | 3.45 | −1.97 |
| 6.5 | −1.9 | **3.29** | **−2.01** ← minimum |
| 6.3 | −0.6 | 3.12 | −1.97 |
| 6.0–5.1 | **0.0** (at present level) | 2.95 | −1.82 |
| 4.6 | −0.35 | 2.62 | −1.13 |
| 4.3 | −0.81 | 2.28 | −0.58 |
| 4.1 | −1.11 | **2.11** | **−0.43** (≈ Strabo) |
| 3.8 | −1.66 | 1.44 | −0.20 |
| 3.6 | −1.86 | 1.27 → 0 | 0.0 |

Read off that, and each line is publishable:

- **The minimum is −2.0 m at ~3300 BP, and the "Trojan War" label sits on it.** The
  "about 2 m" of the abstract is the *depth of this trough*, not a drop between two
  arbitrary dates. Quote it as "about 2 m below present, at its Late Bronze Age
  minimum (Kayan et al. 2003, 383 fig. 2, after Kayan 1991)".
- **The fall is slow and the recovery is fast.** 0 m at 5.1 ka → −2.0 m at 3.3 ka
  (1.1 m/millennium), then −2.0 → −0.4 m in 1.2 millennia. Any drawn shoreline that
  treats the Bronze Age as a step change is wrong on this curve.
- **The text and the curve disagree about the time of Christ, mildly.** The body
  says the sea "rose again to its present level at the time of Christ" (384) and
  "by the time of Christ rose again to its present level" (387); **the curve is at
  about −0.4 m at 2000 BP and does not reach 0 until ~1300 BP.** Record both.
- **The curve is Kayan 1991's, from the Beşik plain, not from the Karamenderes.**
  p. 384: eighty hand drillings on the Beşik plain "made it possible to delineate
  small relative sea-level changes during the middle and late Holocene. Thus, the
  sea, which had reached its present level about 6000 years ago, fell about 2 m in
  the period 5000–3500 years ago, then rose again to its present level at the time
  of Christ." So the sea-level control for the whole Troad is a *Beşik* record,
  which is where the barrier and lagoon are too (§1.5b). Say so.
- **Its cause is asserted, not shown, and it is tectonic:** "These are relative sea
  level changes and the reasons are not entirely known. However, the sea level fall
  during the Bronze Age is attributed to tectonic movements (**Bronze Age
  Regression**; Kayan 1997b)" (387). No Kelletat here — the dossier's §1.8 line
  deriving Kayan's fall "from Kelletat's 1975 curve" is **not supported by this
  chapter**, which cites Kayan 1988a and Kayan 1991 for the curve and Kayan 1997b
  for the mechanism. Kelletat is not named in this chapter's text at all.
- **Kraft's chapter reports the same curve two ways and neither is −2.0 at 3.3 ka
  exactly:** "Aegean sea levels fluctuated to a low of **−1 to −2 m ca. 3500 years
  ago**" (2003a, 361, citing Kayan 1995), and "a sea-level drop to **−2 m ca. 3400
  years ago**" (2003a, 372), and on Fig. 9's caption "a 2-m sea level drop **to ca.
  1400 B.C.**" (373). Four statements of one curve in two chapters of one volume,
  spread over 3500–3300 BP. **Our `barrier-bronze`'s "2 to 2.5 m" still matches
  none of them** (§3.3).
- Authority: **geometry** — this is a plotted, dated, published relative-sea-level
  curve, and it is the strongest thing the dossier now has on sea level. Register
  it exactly as its own author does: **local and relative**, from Beşik, cause
  attributed to tectonics.

**DO NOT CONFLATE THIS CURVE WITH EROL'S, added 2026-07-30 on the 1982 chapter
(§1.2).** Kraft, Kayan and Erol 1982 print a sea-level curve of their own at
**Fig. 4, p. 18**, and it is **Erol's**, not Kayan's — captioned "A eustatic sea
level curve for Anatolia constructed by O. Erol", footnoted to Erol 1975, 1976
and Göçmen 1976. Its Holocene readings are a **double high stand**, verbatim
(p. 18–19): "**+2 m. at about 6500-5500 B.P. and of +1 m. at about 3000-2000
B.P.**, with a +0.5 m. high sea level stand at about 800-900 B.P." **There is no
−2 m Bronze Age trough on it at all**; the chapter's Bronze Age reading is
instead four inferred "surges" of accelerated sedimentation (Fig. 10, p. 26,
points A–D: 5500–5000, 4000–3200, 2200–1500 BP and the past 500 years), each
tied to "a minor drop in sea level" with **no metre value attached**. So the 1982
Bronze Age window (3000–2000 BP) sits on the **high** limb of a different curve
from a different author. The two must never be merged, averaged, or presented as
one curve updated: Erol's is a regional eustatic-with-tectonic-noise curve;
Kayan's is a later, Beşik-specific, more tightly dated relative curve first
published in 1991. The 1982 chapter neither cites nor anticipates the −2 m
minimum.

**A fourth and fifth printing of Kayan's curve, and the tightest interval
re-stated (2026-07-30).** The same Beşik curve after Kayan 1991 is printed again
at **Kayan 1997, 435 fig. 2** ("Relative sea level changes along the Aegean
coast of Turkey during the last 7000 years") — same shape, same
archaeological-period bar, one extra "?" on the steep pre-6 ka limb, **not
independently re-measured** (the scan will not support it; §1.5a's and §3.7b's
numbers off the 2003 and 2014 prints remain the authority). What the later papers
do move is the **interval of the fall**, and they narrow it:

| source | interval | magnitude |
|---|---|---|
| Kayan et al. 2003, 384 | 5000–3500 BP | about 2 m |
| Kayan 1997, 434 | fall 5000–4000 BP; **below present** 4000–3000 BP | "a few meters below the present (generally about 2 m)" |
| Kayan 1996, 246 | begins c. 5000 BP; **at ~2 m by 3500–3000 BP**; back to present 3000–2000 BP | about 2 m |
| **Kayan 2002, 1003** | **5000–3500 BP** — same width as 2003's, independently stated a year earlier | about 2 m |
| **Kayan 1999, 545–46** | **5000–3500 BP** — a fifth printing, same width again, three years before 2002 | about 2 m |

Kayan 2002's Conclusions, verbatim: "the development of the wide riverbed and its
delta occurred about **5000–3500 years ago** as sea level fell about **2 m**."
Kayan 1999, 545–46, verbatim: "Old coastal morphologies and sediments and ¹⁴C
datings of the Troia area as well as archaeological evidence indicate **a 2 m
sea-level fall between 5000–3500 BP** (Kayan, 1995, 1997a). Geomorphological and
archaeological evidence of this Bronze Age event can be found along the entire
Aegean coast of Turkey."
Add them **alongside** the other ranges, never in place of them: the chapter does
not flag its interval as a revision, and the underlying ¹⁴C/OSL sample lists have
not been compared across the three papers.

**CORROBORATED AND DIVERGED, 2026-07-30, by Kayan 2014, 709 fig. 8 (§1.5d).** The
2014 chapter prints **the same curve** — same caption ("Middle-Late Holocene
relative sea level changes in the Troia area (Kayan 1991)"), same two annotation
bars, same "Trojan War" / "Homer's time" / "Strabo's time" labels. Re-measured
independently off the 2014 print at 600 dpi (§3.7b), the numbers reproduce to
**±0.03 m across the whole 4.3–2.3 ka span**, minimum included: **−1.99 m at
3.28 ka BP** against 2003's −2.01 m at 3.29 ka. **The −2.0 m at ~3300 BP is
therefore a two-print, two-measurement figure and may be quoted without hedging.**
What does *not* corroborate: **the cause as 2003 states it**. 2003, 387 attributes
the fall to tectonics ("Bronze Age Regression"; Kayan 1997b) — a citation now known
to be a **misattribution** (see the closure below: neither Kayan 1997 text carries a
tectonic argument). 2014, 719 states the eustatic/climatic position — "tectonic
reasons are not convincing explanations for uniform sea-level changes. Thus, an
**eustatic reason concerning a climatic effect** must be taken into account" — which
is **continuity with Kayan 1997a and 1999, not a reversal**. The only tectonic
attribution in the record is 2003's, and it cites a paper that does not contain it. One measurement note in the other direction: on the **steep pre-6.2 ka
limb** the two readings part company by up to 0.7 m (6.5 ka: −1.9 m in 2003,
−1.17 m in 2014), which is what a ~0.15 ka horizontal registration error costs on a
limb that steep — not a redraw, and not a stretch of the curve anyone should quote.

**THE "1997b" PROBLEM — opened 2026-07-30 and CLOSED the same day. It is a
misattribution in Kayan et al. 2003, and the tectonic reading of the Bronze Age
fall has no first-hand Kayan authority anywhere in the record.** The tectonic
attribution above rests on a short-form citation, "Kayan 1997b", which this
dossier had never seen. A Kayan 1997 whose **title is the phrase 2003 attaches to
the citation** has now been read in full — "Bronze Age Regression and Change of
Sedimentation on the Aegean Coastal Plains of Anatolia (Turkey)," in *Third
Millennium BC Climate Change and Old World Collapse*, ed. H. Nüzhet Dalfes,
George Kukla and Harvey Weiss, 431–50, NATO ASI Series I: Global Environmental
Change 49 (Berlin and Heidelberg: Springer, 1997) — **and it argues the
opposite.** Its conclusions, verbatim (pp. 449–50):

> "the Aegean region has been formed by tectonic movements in many blocks and it
> is difficult to suppose that all of the blocks moved in the same order and by
> the same amount without any distortion or tilting. Therefore, the general
> configuration of the transition layer **cannot be explained by tectonic
> movements**. In addition, **no geomorphological feature has ever been found** up
> to now to indicate any tectonic movement of the Aegean blocks during the last
> 6000 years."

> "**Briefly, according to the present evidence, climatic-eustatic sea-level
> changes** can be taken into consideration as the most reasonable explanation
> for the change of sedimentation throughout the Aegean coast of Anatolia in the
> third millennium BC."

The abstract (p. 431) says the same up front: "local or regional tectonic
movements and sediment compactions are not important here." Its argument for
preferring eustasy is the regional synchrony of the transition layer across five
plains — Troia, Tuzla, Ephesos, Klaros — which is easier to explain by a shared
driver than by independent blocks moving in lockstep (p. 449).

**RESOLVED 2026-07-30, and it took two more papers. The letters are Kayan's own,
and neither of the two candidates supports 2003.**

1. **Kayan assigns the letters himself.** His reference list in *QSR* 1999
   (pp. 547–48) prints all three 1997 items lettered: **"Kayan, I. (1997a).
   Bronze Age regression and change of sedimentation on the Aegean coastal plains
   of Anatolia (Turkey)… NATO ASI series… 431–450"**; **"Kayan, I. (1997b).
   Geomorphological evolution of the Çıplak valley and archaeological material in
   the alluvial sediments to the south of the Lower City of Troia. *Studia
   Troica*, 7, 489–507"**; 1997c the Turkish Ephesos paper. The same usage runs in
   the prose: at 1999, 544 the Çıplak valley's buried incision is cited to
   "**Kayan, 1997b**". So **"1997b" is the Çıplak paper** and "1997a" is the NATO
   chapter quoted above.
2. **And the Çıplak paper carries no causal argument at all.** Read in full
   (§1.5e): its single sentence on the question, p. 501, is a declared blank —
   "**No new evidence, however, was found here concerning the Bronze Age marine
   regression discussed in previous publications**" — footnoted (p. 506) to
   "Kayan 1991, 89; Kayan 1995, 230" and nothing else. The words "tectonic",
   "eustatic" and "climatic" never touch the regression anywhere in it.
3. **Kayan 1999 restates the anti-tectonic position in its own voice**, three
   years before the paper that cites him for the opposite. Its conclusion,
   p. 548, verbatim: "In addition, **tectonic deformation in the Middle–Late
   Holocene sedimentary units and geomorphology of the coastal plains has not
   been observed in spite of tectonic activity in this region.** This is one of
   the more interesting point of our conclusions and is open to further
   discussion."

**What this settles.** Kayan et al. 2003, 387's attribution of a **tectonic**
mechanism to "Kayan 1997b" is **supported by no Kayan 1997 text**: not by 1997b,
which argues nothing, and not by 1997a, which argues the reverse at length.
**The tectonic reading of the Bronze Age fall therefore has no first-hand Kayan
authority anywhere in the record this dossier has now read** — 1991 and 1995
excepted only because they remain unread on this point, and 1997b's own footnote
points at them. And **Kayan 2014's eustatic-climatic position is not a reversal
but a continuity**: 1997a, 1999 and 2014 hold one line, and the outlier is a
single sentence in a 2003 chapter citing a paper that does not say it. Write it
that way — **1997 climatic → 1999 climatic → 2003 tectonic (miscited) → 2014
climatic** — and **never print "Kayan attributes the fall to tectonics (1997b)"**
in any form. §5 item 15 is closed; §6 carries the corrected form.

**Where the term "Bronze Age Regression" comes from (2026-07-30).** Not from the
1997 paper that carries it in its title, and not from 2003, which is where this
dossier first met it. Kayan coins it two years earlier, in **Kayan 1995, 216**,
for the c. 2 m fall of **4000–3000 BP**, in the caption discussion of his Fig. 3
("Relative changes in sea-level on the Beşik coast during the last 6000 years,
after Kayan 1991"). So the phrase, the curve and the magnitude all originate in
the Beşik plain work, and 1995 is the earliest print of the name.
- Authority: **prose/citation** — Fig. 3 in 1995 is a reprint of the 1991 curve,
  not a new measurement.

#### 1.5b The chapter's own words on Kesik, the barrier and the lagoon — first-hand at last

**Kesik, in full and in his own order (pp. 397–99).** The dossier has had this
through Zangger's Turkish footnotes and through Kayan 2009/2014. The 2003 text is
different in kind from both, and it is *undecided*:

- **Geometry, p. 398, verbatim:** "To the west of the Kesik plain, the Yeniköy
  ridge is only about 600 m wide. Elevation is a little more than 20 m at the top.
  … The **highest point in the bottom is 13.7 m above sea level at a distance of
  about 150 m from the sea**, but the inner side profile is gentle and opens on to
  the Kesik plain at an elevation of **6.3 m about 400 m east of the top**. … The
  Kesik 'canal' has no floor. It looks like a V-shaped valley, but there is only an
  earth road at the bottom … Drilling holes and trench profiles on the bottom of
  Kesik 'canal' clearly showed that the **Neogene marl is covered by 2 m
  colluvium**. **No archaeological material was encountered** in the many drillings
  which were made in the bottom of the cut (Kayan 1995)."
  - **Three corrections to §1.9's numbers, and they matter.** (a) 13.7 m is the
    **highest point of the cut's bottom** — a saddle — not "the floor", which
    descends to 6.3 m at the inner end. (b) The **400 m** is the distance from that
    saddle east to the Kesik plain, not the cut's length as §1.9 has had it. (c) The
    colluvium is **2 m** here; "2–2.5 m" is Zangger's rounding. **The
    "400 × 50 × 30 m" triple is Zangger's summary, not Kayan's**: this chapter gives
    no width and no depth, and its "600 m" is the *ridge's* width.
- **Origin, p. 399, verbatim and entire — and it is agnostic:** "The Kesik 'canal'
  was never used as a waterway. **Although the shape of the Kesik implies that it
  was dug by man, there is no information about the purpose and time of
  construction.** The only obvious feature is that it facilitates passage from the
  steep, high and continuous cliff coast to the inner plain on foot. It might have
  been opened, and deepened from time to time, for the transportation needs of the
  inhabitants of Sigeion and then Yenişehir. **Perhaps it took shape slowly rather
  than in one planned excavation. Or perhaps it is an unfinished canal
  construction.** Finally, there is an unanswered question; where are the earth
  piles resulting from the excavation? There is no trace of additional earth in the
  area."
  - **This is not the tectonic-depression reading.** In 2003 Kayan says the shape
    *implies it was dug by man*, offers foot traffic and an unfinished canal as
    alternatives, and asks Cook's own spoil question. **The natural/tectonic
    reading the dossier attributes to him is dated 2009 and 2014** (§1.9). So
    Kayan's position moved, and a caption saying "Kayan: natural" without a year is
    wrong. And "**Or perhaps it is an unfinished canal construction**" lands within
    a word of Cook's "the work was never completed" (Cook 1973, 167) — the two are
    closer in 2003 than §1.9's five-cornered table allows.
- **THE CORRECTION TO §1.9's "opposite mood" QUOTE.** §1.9 sets Kayan's "One can
  easily imagine that the Kesik plain could have been an excellent harbor…" (there
  cited to Kayan 2014, 723) against his own denial, as though he wrote in two
  moods. **The sentence is here too, at p. 398, and in context it is the setup of a
  refutation, not a concession:**

  > "…one can easily imagine that the Kesik plain could have been an excellent
  > harbour which was connected to the Aegean Sea by the Kesik 'canal'. Concerning
  > this idea, there are various interpretations in the literature (Cook 1973) …
  > **Although** the present configuration and paleogeographical characteristics of
  > the Kesik plain imply that this area could have been used as a harbour in
  > ancient times, **all geomorphological and various drilling evidence, including
  > ¹⁴C datings, clearly show that the Kesik bay was covered with very shallow sea
  > water which was not convenient for boats, and was then swampy during the Bronze
  > Age**" (398–99).

  It is a concessive clause. §1.9's "Elsewhere he writes the opposite mood" should
  be struck for the 2003 instance; whether the 2014 instance is also concessive is
  unchecked, and until Kayan 2014 is read the quotation must not be used to show
  Kayan contradicting himself.
- **Siltation dates, and an internal spread the chapter does not reconcile.**
  p. 398: "¹⁴C dates indicate that **marine conditions continued up to 3500 years
  ago**. Then, the area of Kesik bay silted up rapidly and changed into swampy land
  (Fig. 7)." Conclusion 2, p. 400: "the Yeniköy and Kesik embayments changed into
  land following alluviation and deltaic progradation about **5000 and 4000 years
  ago**, respectively (Fig. 7)." Fig. 6's Kesik section carries the actual dates:
  **3400, 4200 and 4500 BP** at or just below present sea level, with the caption
  noting that the 4200 BP hole (no. 18) sits on the embayment's south edge and is
  "in concordance with the other dates of the end of marine sedimentation." So
  3500 / 4000 are two roundings of a 3400–4500 BP spread. **Quote the spread, not
  either rounding**, and note that Zangger's "silting up before 1300 BC" (§1.9, via
  Kayan 2001/2009) is later than anything this chapter prints.

**The barrier and the lagoon — located, at last, and they are not where our layer
puts them.**

- **At Beşik, they exist** (p. 384, verbatim): "We showed that the present Beşik
  plain formed as a small bay about 6000 years ago. **Afterwards, a coastal barrier
  separated a small lagoon.** … **A small sea-level fall in the Late Bronze Age may
  have caused widening of the coastal barrier and reduced the lagoon (Fig. 2).**
  Thus, it can be interpreted that no Bronze Age natural harbour with an open water
  surface seems to have been possible here (Kayan 1991)." Kraft's chapter says the
  same of the same place: "Kayan's pioneering study of the Beşik coastal plain
  demonstrates a mid-Holocene marine embayment, evolving to a **barrier-lagoon**,
  and accretion plain backed by a coastal swamp (now drained)" (2003a, 372).
- **On the Karamenderes, they are denied in one sentence** (p. 390, of the
  transition zone that caps the marine unit right across the plain, "generally 2 m
  below the present sea level under almost the whole surface of the present
  plain"): "**There is no beach or lagoon formation. Instead, sediments indicate
  swampy or seasonally wet environments.**"
- Kraft's chapter, p. 364: "**Coast-parallel lineaments occur only in the lower
  2 km of the Scamander floodplain. Barrier accretion ridges do occur on the Beşik
  coastal plain.**" — which is *2003b's* "no barrier lineaments are evident on the
  lower Scamander delta" (§1.3b) in a softer, more exact form: there are
  coast-parallel lineaments, but only in the last 2 km before the Dardanelles, and
  the accretion ridges are at Beşik.

**So the barrier-and-lagoon language Brückner et al. 2005 supplies, traced to its
sources, is Beşik Bay's.** Applied at §2 and §3.3.

**THE BEŞIK BARRIER NOW HAS THREE INDEPENDENT PRINTS ACROSS TWENTY-ONE YEARS
(2026-07-30).**

1. **1982** (§1.2, pp. 38–39). Fig. 21's own diagram legend reads "BARRIER…
   3-4 METERS", and the text reports "the central spit or barrier in the
   embayment noted by Erol" as evidence "for a higher sea level stand three to
   five thousand years ago" (citing Erol 1972, 4). Same feature, same place,
   twenty-one years before the 2003 chapters.
2. **1988** (Kayan, *PPP* 68, 212–16). A 70-hole hand-boring campaign at
   "Beşige" finds **two stacked coastal-barrier generations**: "the deeper one is
   characterised by grey, coarse sand and pebbles; while the upper one consists
   of yellowish, finer but still coarse sand" (p. 214). Dated stages: bay at
   ~6000 BP; the grey barrier forms under the sea surface ~5000 BP and the inner
   bay "turned into a lagoon"; the grey barrier widens and rises into the
   yellowish one by **3500–3000 BP**. The dating anchor is archaeological, not
   radiocarbon: potsherds from the **upper levels of the yellowish barrier** were
   dated by Korfmann's team to "**Troy VI (about 3500 yr B.P.)**", which
   establishes "that the sea level was lower than the present one at that time"
   (p. 215).
3. **2003** — the print §1.5b already carries, repeated and dated in Kayan 2014,
   704 ("around the period of Troia VI").

**One caveat that must travel with the 1988 leg, and it is the author's own.**
1988 gives **no metre value** for the Beşik low stand: "A precise sea-level curve
has not been drawn for the Beşige area separately yet **because of some dating
problems**" (abstract, and p. 214). Its Conclusions offer only a direction and a
band — "sea level descended **about 1–2 m** [and] people used the coastal strips
about 3000 years ago because these areas had dried up behind the receding sea"
(pp. 216–17). **Kayan 1988 may not be cited for "exactly 2 m."** Its own figure
is a provisional range, pending the precise curve that arrives in 1991. (The
paper's second study site, **Dalacak** on the Datça peninsula, is a comparandum
from the southern Aegean and has **no bearing on the Troad** — do not carry any
Dalacak number into a Troad claim; the paper's own argument is only that the two
curves run parallel, "however, more detailed local studies are necessary to
confirm this conclusion.")

**AND THE KARAMENDERES DENIAL NOW HAS FOUR INDEPENDENT STATEMENTS
(2026-07-30).** In publication order:

| source | wording |
|---|---|
| **Kayan 1997, 438** | "coastal barriers and lagoonal features **did not develop** on the coast of the retreating sea in the Karamenderes valley. Instead, a swampy, bird's-foot type ('azmak' in Turkish) delta coast was dominant" |
| **Kayan 2002, 1002** | "Coastal spit, barrier, beach and lagoon sediments might be expected in this area; **however they do not exist**, because the bottom of the old Karamenderes 'bay' was very shallow and wave energy was too low to form sandy coastal formations" |
| Kayan et al. 2003, 390 | "There is no beach or lagoon formation. Instead, sediments indicate swampy or seasonally wet environments" |
| Kayan 2014, 712 | the 2003 sentence repeated word for word |

Plus Kraft et al. 2003a, 364 and 2003b, 164 from the other side of the
collaboration. **One hedge the later wordings drop, and it belongs on the record:**
1997, 438 adds that "the undulating lower boundary of the coarse sandy transition
layer **at the mouth of the Dümrek river** indicates that some coastal barrier and
lagoon formations behind them are possible" — a possibility, at the Dümrek mouth
specifically, never asserted as fact and never repeated.

**Coring count corroborated (2026-07-30).** Kayan 2002, 995, published the year
before the Springer chapter and independently of it: the drillings "reached **285
in 2001**. 100 of these were carried out to the west in the Beşik Plain and on
the Yeniköy Ridge," at ~10 m for the Eijkelkamp hand tool, ~20 m for Unimog and
Cobra, to 30 m in places, test drillings to 50 m, trenches to ~2.5 m. So **285 by
2001** is a two-source figure, and **318** remains Kayan 2006/2014's later total.

**The ~2 m fall gains an independent stratigraphic proof, and it is local
(2026-07-30, Kayan 1996).** A campaign of 25+ holes at the foot of Troia's steep
**northern** slope, along the Dümrek (Simoeis) edge, prints at **Fig. 4 (p. 245)
a channel cutting the marine-sediment unit** on the old sea-bottom surface, with
the caption, verbatim: "**This is a new proof that Bronze Age sea-level fell by
about 2 m. (Kayan 1991)**." The surface on the marine sediments is inferred to
have formed **about 3500 years ago**. That is a second line of evidence for a
number the dossier had only from the Beşik curve — a stratigraphic relationship
read off a measured section, not a new metre value. Two further numbers from the
same paper: a **narrow bedrock platform about 10 m below the present surface** at
the foot of the slope, its Early Holocene marine cover shelled at **5800 BP** at
the east end and **5200 BP** at the west (Fig. 6, pp. 246–47, with **no artefacts
in any of the marine sediments**); and the **oldest Dümrek channel** north of the
platform, its bed at about **35 m below present surface**, filled with marine
sediment to 2–3 m below present sea level, implying ~2–3 m of water at the end of
marine sedimentation there (p. 247).

**And a periodization discrepancy that must be recorded rather than resolved.**
Kayan 1996, 247: "**the surface along the foot of the northern slope of Troia
first became land about 3500 years ago**, and people started to use this surface
during the early periods of Troia," with the deepest sherds dated by Troia's own
archaeologists to "**Troia VI, or more probably VII**" (246, 247–48). The
dossier's §2 "Progradation past the city" row carries the same phenomenon from
Kayan et al. 2003, 392–94 as "**During Troia IV–VI**, a strip of dry land formed
between the slope and the old Dümrek channel." Same north foot, same drying-out,
**two different period labels** — VI/VII in the primary 1996 report, IV–VI in the
2003 paraphrase. Neither overwrites the other; the underlying stratigraphy is not
in dispute, only how the period was later summarised. Note also that the 1996
dating is **identification at one remove** — Kayan reports the excavation's
ceramic dating and names no ceramicist.

**The north-footslope platform: two measurements, two papers, and they are not
the same measurement (2026-07-30, Kayan 2002).** Kayan 2002, 1000, verbatim:
"there is a platform on the bedrock along the foot of the northern slope under
alluvium **about 4–5 m below present sea level** (fig. 6). The bedrock profile
descends steeply northward from the platform and goes down to **35–40 m** in a
short distance. Towards the west, the platform gradually deepens and disappears."
Kayan et al. 2003, 392–94 gives that platform a **width** — "about 50 m wide just
below present sea level" — and **no depth**; 2002 gives a **depth** and no width.
**Cite each number to its own source and never write "a platform 50 m wide, 4–5 m
deep"** — no source states both of the same feature in the same sentence.

**The buried Bronze Age Dümrek riverbed, and OSL enters this record
(2026-07-30).** Kayan 2002, 1003, conclusions point 1: "a coarse sandy, gravelly
**riverbed about 200 m wide** along the northern footslope of Troy and a delta fan
extending westward… Stratigraphical evidence, **¹⁴C and OSL datings** reveal that
the development of the wide riverbed and its delta occurred about **5000–3500
years ago** as sea level fell about 2 m." Both the 200 m width and the OSL method
are new to the dossier, which has carried the old Dümrek channel only
qualitatively and has cited ¹⁴C alone for the equivalent Karamenderes-side dating.
- Authority: **geometry** (drilling-derived widths and depths). No coordinate:
  the chapter carries no lat/long and its figures are measured sections, not
  georeferenced sheets.

**The rest of the chapter's numbers, first-hand:**

- **Coring campaign:** 285 holes by 2001 (not 318 — that is Kayan 2006/2014's later
  total, §1.9); seven rotary cores in 1977 with MTA, "the deepest went down 75 m to
  pre-Holocene bedrock"; 80 hand drillings 7–8 m on the Beşik plain under Korfmann
  1983–88; the Daimler-Benz Unimog rig to 20.50 m from 1988; Cobra percussion from
  the later 1990s, "15–20 m is a good depth", 85 Cobra holes by 2001 (382–86).
- **Depths and dates:** last-glacial valley floor "about 30 m below the present
  plain" (386, 389); large marine shells from ~50 m below the present surface dated
  ~10,000 BP (389); marine-coastal shells at about present sea level along the foot
  of the Neogene slopes "always found to be close to 6000 years ago" (389).
- **North of the citadel** (392–94): the surface north of the Troia ridge is "about
  7 m above sea level"; drilling north of the Schliemann trench found a Neogene
  bedrock **platform about 50 m wide just below present sea level**, its surface
  covered with marine sediments up to present sea level, the coarse sandy coastal
  sediments dated **5800–5200 BP**. "It is understood that the **sea was right at
  the foot of the 'Schliemann trench' during the earliest periods of Troia, i.e.
  Troia I and II. During Troia IV–VI, a strip of dry land formed between the slope
  and the old Dümrek channel**, which was located about 50 m north of the foot of
  the steep Troia slope." That is the chapter's one hard statement about the water's
  edge *at the citadel*, it is a **borehole** statement rather than a map one, and
  it says the sea had left the north foot by Troia IV.
- **Ridge heights:** "The surface of the ridges around Troia is at an elevation of
  40–50 m and to the east rises to an elevation of up to [1]00 m", above which "a
  slightly undulating higher plateau surface at an elevation of 200–250 m" (386).
  Fig. 7's legend prints the same two bands: Low plateau 40–80 m, High plateau
  200–250 m. Compare Kayan 2019's "about 50–100 m" (§1.5, abstract) — the same
  ridges, two roundings.
- **Why the fine sediment defeats channel mapping** (389): the bedrock is entirely
  fine Miocene marine rock and the Karamenderes drops its coarse load in the
  Bayramiç–Ezine basin behind the Araplar gorge, so "the homogeneously fine grained
  nature of the Holocene sediments causes difficulties of detailed interpretation …
  such as **delineating old river channels or old shoreline positions**." **The
  chapter's own account of why nobody can draw the ancient shore precisely.**

#### 1.5c The seven figures, and what Fig. 6 and Fig. 7 actually are

| fig. | p. | what it is | after |
|---|---|---|---|
| 1 | 380 | geomorphological outline map of the Troia area (plateau bands, Karamenderes plain, old swamps, scarps, cliffs, beaches, springs; **YE / KE / KT** for the Yeniköy, Kesik and Kumtepe plains; K = Kesik canal, A = Araplar gorge; the cross-section lines of Figs. 3–6) | Kayan 1995 |
| 2 | 383 | **the relative sea-level curve**, with the Troia-period and "Trojan War / Homer's time / Strabo's time" bars (§1.5a) | Kayan 1991 |
| 3 | 388 | cross section of the steep northern slope of Troia, drill cores numbered | Kayan 1996, 2000 |
| 4 | 391 | drill-hole details along the foot of Schliemann's north–south trench, colluvium with potsherds/charcoal/bones over the transition zone over shallow marine fine sandy mud | Kayan 1996 |
| 5 | 393 | N–S section, Lower City of Troia to Kalafatlı, holes 101–106, archaeological findings in colluvium | — |
| 6 | 396 | **three cross sections, NOT a map** (§ below) | Kayan 1995 |
| 7 | 397 | **the reconstruction map, one sheet with dated coastline isochrones** (§ below) | Kayan 2000 |

**Fig. 6 (p. 396) is not a reconstruction with dated stages.** §5 item 4 expected
"the barrier and lagoon geometry" there. It is headed "CROSS-SECTIONS OF THE
YENİKÖY, KESİK AND KUMTEPE EMBAYMENTS ON THE WESTERN EDGE OF THE KARAMENDERES
(SCAMANDER) PLAIN (WEST OF TROİA)" — three stacked sections, boreholes numbered,
"Four and five digit numbers indicate C14 dates … calibrated age with 400 yrs
reservoir correction but rounded here as simply Before Present." Facies bands:
soil formation / fine sandy flood plain–delta sediments / swamp sediments above
P.M.S.L.; deltaic coarse sand, fine sandy shallow marine sediments, coarse coastal
sand, Neogene bedrock below. Dates: **Kumtepe 5500, 7000 BP · Kesik 3400, 4200,
4500 BP · Yeniköy 5500, 5800, 5300, 12,500 BP**. The Kesik section carries the cut
itself as two line profiles across the ridge ("Canal bottom profile", "Northern
ridge profile"), and the Yeniköy section carries the Beşik–Yeniköy threshold with
its "Old canal profile" and the water-mill (Hanım değirmeni). **On all three
sections the threshold bedrock stands well above present sea level — which is the
whole argument of §5 of the chapter, drawn.** No barrier and no lagoon appears on
any of the three.

**Fig. 7 (p. 397) is the reconstruction, and it is one sheet, not a series.**
"Geomorphological development of the Karamenderes (Scamander) plain. (Kayan 2000)."
Legend: High plateau 200–250 m · Low plateau 40–80 m · **Flood plains about
6000 BP** · **Troia and Beşik bays 6000 BP** · Swamps · Scarps · Cliffs · Beaches ·
Rivers · Springs · elevations · villages · archaeological sites · YE/KE/KT ·
**"Coastline positions (Years Before Present)"**.

**The dated isochrones on it are four, and one of them is missing from the set that
matters: 6000–5500 BP · 5000–4500 BP · 2000 B.P. · Present** (plus "6000 BP" and
"Present" at Beşik). **There is no Late Bronze Age line.** The LBA falls in the
unlabelled interval between the 5000–4500 BP and 2000 BP shores.

**So the answer to "what does Kayan et al. 2003 commit for the LBA shoreline
position relative to the citadel" is: nothing, on the map.** What it commits is
(a) the 6000 BP bay's edge, (b) the 5000–4500 BP and 2000 BP shores as brackets,
and (c) the borehole statement at pp. 392–94 that the sea had left the citadel's
**north** foot by Troia IV. Any LBA shoreline drawn from this chapter is an
interpolation, and must be labelled as one.

Measured off Fig. 7 (figure measurement, this dossier; scale bar 0–3 km = 442 px at
500 dpi ⇒ 147.3 px/km; Troia dot at (2065, 1432); nearest dark-green "Troia bay
6000 BP" blob per bearing):

| bearing from Troia | 6000 BP bay |
|---|---|
| 000° (N) | 0.31 km |
| 015° | 0.35 km |
| 030° | 0.41 km |
| 045° | 0.52 km |
| 060° | 1.10 km |
| 075°–120° | no water (the Dümrek/Simois floodplain) |
| 165° | 1.49 km |
| 195°–255° | 0.47–0.65 km |
| 270° (W) | 0.39 km |
| 300°–345° | **0.27–0.33 km** |

**The 6000 BP bay laps the citadel on Kayan's own sheet at 0.27–0.41 km through the
NW–N–W sector**, which is within measurement noise of Kraft's Figs. 9 and 10
(§1.4a) and of *Geology* Fig. 6's 5000–5500 BP plate (0.39–0.46 km, §1.3a). **Four
plates from this research group agree that the bay reached the citadel's western
foot; they disagree only about when it left.** That is the honest shape of the
constraint.

One further measurement, offered with its caveat: the boundary from the mid-green
delta to the pale post-2000 BP delta lies at **3.35 km (315°) and 3.44 km (330°)**
from Troia, which is where the "2000 B.P." label sits — so the Strabo-time shore on
Fig. 7 is ~3.4 km NW of the citadel. Bearings N through NE are not measurable this
way (the grey Dümrek floodplain reads as the same tone), so no number is offered
there.

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
*Studia Troica* 1 (1991): 79–92. · ~~"The Troia Bay and Supposed Harbour Sites in
the Bronze Age." *Studia Troica* 5 (1995): 211–35.~~ **— READ IN FULL,
2026-07-30; see §1.9.** · ~~"Holocene Stratigraphy of the
Lower Karamenderes–Dümrek Plain and Archaeological Material in the Alluvial
Sediments to the North of the Troia Ridge." *Studia Troica* 6 (1996): 239–49.~~
**— READ IN FULL, 2026-07-30; see §1.5b.** ·
~~"The Water Supply of Troia." *Studia Troica* 10 (2000): 135–44.~~ **— READ IN
FULL, 2026-07-30; its springs material sits in
`RESEARCH-TROAD-TOPOGRAPHY.md` §6.8, and it carries nothing on Kesik or on
sea-level values.** · "Die troianische
Landschaft: Geomorphologie und paläogeographische Rekonstruktion der
Alluvialebenen." In *Troia: Traum und Wirklichkeit*, 309–14. Stuttgart, 2001. ·
~~"Paleogeographical Reconstructions on the Plain along the Western Foot-Slope of
Troy." In *Mauerschau: Festschrift für Manfred Korfmann*, 993–1004. 2002.~~
**— READ IN FULL, 2026-07-30; full citation and content at §1.4b.** · "Mit
dem Kernbohrer in die Vergangenheit." In *Troia: Archäologie eines
Siedlungshügels und seiner Landschaft*, edited by Manfred Korfmann, 317–28. Mainz,
2006. · "Kesik Plain and Alacalıgöl Mound: An Assessment of the Paleogeography
around Troia." *Studia Troica* 18 (2009): 105–28. *(Kayan 2014's own bibliography,
p. 727, prints this as "Studia Troica 18, **2008**, 105–128" — one digit off from
every other citation of it, including Kayan 2019's. Treat 2009 as right and the
2014 list as the typo, but note that a reader chasing it will meet both.)* ·
~~"Geoarchaeological Research at Troia and Its Environs." … 694–727. Bonn, 2014.~~
**— READ IN FULL, 2026-07-30; see §1.5d.**

- Verified how: all page ranges from **two independent bibliographies** — Kayan
  2019's own reference list and Zangger & Mutlu 2015, 576–77. The titles and
  pages are therefore solid; **the contents are not**, except where §1.9 quotes
  them and except for 2014, now first-hand.

#### 1.5d Kayan 2014 — the *Endpublikation* chapter, READ IN FULL 2026-07-30

- Citation: Kayan, İlhan. "Geoarchaeological Research at Troia and Its Environs."
  In *Troia 1987–2012: Grabungen und Forschungen I — Forschungsgeschichte,
  Methoden und Landschaft*, Teil 2, edited by Ernst Pernicka, Charles Brian Rose,
  and Peter Jablonka, 694–727. Studia Troica Monographien 5. Bonn: Habelt, 2014.
- Authority: **prose and geometry**, but read the author's own disclaimer first.
- Verified how: **full text, printed pp. 694–727, and all twenty figures**,
  author-shared copy from İlhan Kayan's ResearchGate page, cached at
  `research-cache/kayan-2014-troia-geoarchaeology.pdf`, 2026-07-30. Page range
  confirmed two ways (§0). Figures measured per §3.7b.

**Read the epigraph before citing anything from it.** The chapter opens, above the
author's name, with an unsigned editorial line: "**This paper is written to explain
the research methods applied in the Troia area and to discuss the obtained results.
Therefore it is based on former data and interpretations, instead of new research
results.**" Kayan's own acknowledgement note repeats it: "This paper has been
compiled from my previous publications on paleogeographical, geoarchaeological
research at Troia" (694 n. *). **So 2014 is a synthesis, not a new dataset**, and
every figure in it is credited to an earlier paper (Kayan 1991, 1995, 1996, 2000).
Where 2014 and 2003 print the same figure, they are **one witness, not two** — the
value of 2014 is that it is his last word, and that in two places the last word has
changed.

**1. THE CURVE — Fig. 8, p. 709. Same plate; corroborates §1.5a's measurement to
±0.03 m; diverges on the cause.**

Caption, verbatim: "Middle-Late Holocene relative sea level changes in the Troia
area (Kayan 1991)." Same two annotation bars as 2003's Fig. 2 — the cultural bar
(Beşik Sivritepe, Kumtepe I A, Beşik Yassıtepe, Troia I–IX, İlion, İlium) with
**"Troian War"** (in quotation marks on the plate; the plate's own Troian/Trojan
orthography could not be settled between independent reads and is not load-bearing
— the 2003 printing of the same plate reads "Trojan War"), **Homer's time** and
**Strabo's time** keyed on to it. The curve itself is a single heavy line bounding
a grey fill, labelled along its length "RELATIVELY CHANGING SEA LEVEL", with a **?**
under its left end before ~6.9 ka — the plate's only uncertainty marking.

*Reading the plate correctly:* it carries **two time axes**, and they are not the
same. The main axis under the curve is **7→0 thousand years BP**; the cultural bar
above it has its own axis ticked **3, 2, 1, 0**, which is **thousand years BC/AD**.
The two are registered 2000 years apart (cultural 3000 BC sits over main 5 ka BP),
so the bar is aligned to the curve, but a reader who takes the upper "3" for 3 ka BP
will misdate every period on it by two millennia.

Measured independently off the 2014 print (figure measurement, this dossier;
600 dpi; metre scale from the alternating left-axis bar, 188.6 px/m with 0 m at
y = 1100; time ticks on the zero line at 385.4 px per 1000 yr with 0 ka at
x = 3064 — §3.7b):

| ka BP | RSL (m) | 2003 fig. 2 | ka BP | RSL (m) | 2003 fig. 2 |
|---|---|---|---|---|---|
| 6.3 | −0.57 | −0.6 | 3.60 | −1.86 | −1.86 |
| 6.1 | −0.17 | — | 3.45 | −1.95 | −1.97 |
| 6.0–5.2 | **+0.05 to +0.12** | 0.0 | **3.28** | **−1.99** ← min | −2.01 at 3.29 |
| 4.8 | −0.17 | — | 3.12 | −1.96 | −1.97 |
| 4.6 | −0.35 | −0.35 | 2.95 | −1.80 | −1.82 |
| 4.4 | −0.61 | — | 2.62 | −1.11 | −1.13 |
| 4.3 | −0.77 | −0.81 | 2.30 | −0.59 | −0.58 |
| 4.1 | −1.13 | −1.11 | 2.11 | −0.41 | −0.43 |
| 3.8 | −1.63 | −1.66 | 1.5 → 0.1 | −0.17 → −0.03 | 0.0 from 1.27 |

What follows, and it is the point of the acquisition:

- **The minimum is −2.0 m at ~3.3 ka BP in both prints, and the "Troian War" label
  sits on it in both.** Two independent measurements off two different printings
  agree to two centimetres. §1.5a's number is not a measurement artefact.
- **The recovery limb is slower than either chapter's prose.** The curve is at
  **−0.41 m at 2.11 ka** and only reaches within 0.15 m of present by ~1.3 ka. The
  2014 text says the sea "rose again to its present level **around 2000 years
  ago**" (719); 2003 said "at the time of Christ" (384, 387). **Both texts run about
  0.4 m ahead of both plots of the same curve.** Record the discrepancy; it is the
  chapter's, not ours.
- **THE DIVERGENCE — between the 2003 chapter's attribution and everything Kayan
  wrote first-hand (it is NOT a reversal by Kayan; resolved 2026-07-30, §1.5a).**
  2003, 387: "the sea level fall during the Bronze Age is attributed to **tectonic
  movements** (Bronze Age Regression; Kayan 1997b)" — but neither Kayan 1997 text
  carries that argument (1997a NATO argues against tectonics; 1997b Çıplak carries
  no causal argument at all). 2014, 719, verbatim (the … elides sentences on
  marine/coastal sediments and >30,000-yr dates — Grok page-image check,
  2026-07-30):

  > "Although we have enough evidence for small sea-level changes during the last
  > 6,000 years, **there is no proof for the cause of these events.** … there is no
  > indicator denoting any uplift of the pre-Holocene surface on which Holocene
  > marine sediments accumulated. In addition, the middle-late Holocene sea-level
  > changes can be followed in the same order and magnitude all along the Aegean
  > coast of Anatolia. The Aegean coastal region has faulted-blocky structure and
  > **tectonic reasons are not convincing explanations for uniform sea-level
  > changes. Thus, an eustatic reason concerning a climatic effect must be taken
  > into account for sea-level changes**, otherwise new evidence must be produced
  > if any different explanations are to be considered."

  So 2014 restates the position Kayan printed in 1997 (NATO) and 1999 (QSR); the
  tectonic clause is the 2003 chapter's alone. **A caption saying "Kayan attributes
  the fall to tectonics" is simply wrong** — the attribution has no first-hand Kayan
  text behind it. And the mechanism matters beyond attribution: a *tectonic* fall is local by
  construction and cannot be checked against a regional database, while an
  *eustatic* one can — and Seeliger et al. 2021's NE Aegean RSL database shows
  continuous rise across this window (§1.8). **In 2014 Kayan puts his own curve on
  the ground where it is falsifiable, and it conflicts.** Do not smooth that; it is
  the single most consequential thing this chapter says.
- **Error discussion: none on the curve, and a serious one elsewhere that bears on
  it.** The plate has no error bars, no data points, no envelope — only the "?" at
  the left end. But pp. 707–08 discuss vertical error at length, and the numbers are
  large against a 2 m signal: the project's levelling still uses **Dörpfeld's datum,
  which is 60 cm below the Turkish National Geodetic System**; GPS and 1/25000-derived
  measurements "have provided different data", and the incompatibility "causes great
  difficulty for the correlation of subsurface sedimentary units"; **"about 20 cm
  difference of altitude … can cause an abnormally inclined view"** on the sections
  and "**may imply tectonic deformation (like tilting), but this is not
  intentional**"; and agricultural levelling means "**vertical shifts of up to
  50 cm** must be taken into account in certain drill-hole correlations". Cite this
  when anyone treats the −2.0 m as a tenth-of-a-metre quantity: **its author reports
  0.2–0.6 m of datum and levelling error in the machinery that produced it.**
- **The curve remains a Beşik-plain record.** p. 704: the 80 Eijkelkamp hand
  drillings on the Beşik plain "made it possible to delineate small relative
  sea-level changes … in particular, that **the sea fell about 2 m in the Late
  Bronze Age**"; p. 719 gives the interval as "first fell about 2 m **between
  5,000–3,500 years ago**, and rose again to its present level around 2000 years
  ago (Fig. 8)". Same provenance, same magnitude, as 2003.

**2. KESIK, FIRST-HAND AT LAST — pp. 720–24, and the fifth corner of §1.9's table
is NOT what Zangger's paraphrase made it.**

The §1.9 table has carried "Kayan 2009, 124 and 2014, 723–24: a **natural tectonic
depression**, later widened by foot traffic", second-hand through Zangger's Turkish
footnotes. **What Kayan 2014 actually says is narrower on both halves, and it
explicitly refuses the Holocene-tectonic reading.** The operative passage, p. 723,
verbatim and entire:

> "The origin of the Kesik canal between the Kesik depression and the Aegean Sea is
> a subject of discussion. Our interpretations on this matter have been explained in
> former publications. **In the new stage of our research we have obtained no
> evidence to change our former interpretation.** In brief, **the Kesik canal
> appears artificial with its very straight direction. However, no evidence has been
> discovered to suggest that it was dug out, nor has any trace of dumped material
> been found in surrounding fields.** The canal is very narrow and the bedrock forms
> a threshold in the middle at a height of about 13 m above sea level. Therefore,
> the canal cannot possibly be used as a waterway between the Kesik depression and
> the sea. In addition, any archaeological material or any trace of human impact
> were not found in colluvial deposition about 2 m thick in trenches which we dug
> across the canal with the Unimog digger.
>
> On the other hand, **there is some evidence implying that the canal depression is
> naturally formed on a fault line.** This is based on differences in elevation
> between two sides (north and south) of the canal, and the morphology of the
> bedrock along the eastern extension of the canal on the surface (Ballıkaya ridge)
> and underlying alluvium (drilling data). **However, sedimentological and
> stratigraphical features of the Holocene deposits in the Kesik depression do not
> support such tectonic activity for the Holocene.** According to available data,
> the most probable explanation may be as follows:"

And the explanation, p. 724, opening sentence: "**The Kesik canal may have
originally formed on a fault line before the Holocene, long before human activity in
this area.**"

Four corrections fall out, and none of them is cosmetic:

- **It is a PRE-Holocene fault line, not a Holocene tectonic depression.** Kayan
  states in the same breath that his own Holocene sediments **do not support**
  tectonic activity in the Kesik depression during the Holocene — which is the same
  finding he generalises at pp. 716–17 for the whole plain ("the sedimentary units
  have not been subjected to tectonic deformation… **tectonic activity or
  deformations are not visible on the landforms and have not been a primary factor
  for the geomorphological development of the region since the middle Holocene**").
  So "Kayan: tectonic depression" is a half-truth that inverts his actual claim
  about the epoch anyone drawing a Bronze Age map cares about.
- **It is hedged three ways in one paragraph**: "appears artificial"; "no evidence
  … that it was dug out"; "*some* evidence implying" a fault origin; "may have
  originally formed"; "the **most probable** explanation **may be** as follows".
  This is not a verdict. **His 2003 position has not moved to a verdict — he says so
  himself: "we have obtained no evidence to change our former interpretation."** The
  2003 chapter's agnosticism (§1.5b) and this are the same position, with a
  preferred hypothesis attached.
- **"Widened by foot traffic" is not the 2014 claim either.** What p. 724 says is
  that in recent centuries people trying to drain the Alacalıgöl part of the plain
  "tried to dig some small trenches to accomplish this, **but nothing as large as
  the Kesik canal**. It seems that such attempts could not been successfully
  completed. **The canal has been used continuously for land passage** between the
  Kesik plain and the coast of the Aegean Sea. This usage may have been more
  important during the wars of the last century." Continuous *use* as a footpath —
  he does not say the traffic cut it. And "such attempts could not been successfully
  completed" is a *third* echo of Cook's "the work was never completed", now applied
  to modern drainage rather than to the cut itself.
- **The Bronze Age is ruled out on environmental, not archaeological, grounds** —
  p. 724: "the Bronze Age, especially the period of Troia VI/VIIa, remains under
  discussion as a period of possible canal construction. **During this period the
  Kesik depression was not a marine embayment; instead, it was covered by a swamp.
  Therefore, a harbor is not a subject of discussion for the Kesik depression and a
  canal was not necessary for a waterway connection with the Aegean Sea.** In fact,
  there is no archaeological evidence later than the Chalcolithic period in this
  area."

**And the "one can easily imagine" quotation is concessive in 2014 too — §6's open
question is now closed.** The sentence stands at p. 723, and the paragraph it opens
runs straight into the literature it is setting up to refute: "…one can easily
imagine that the Kesik plain could have been an excellent harbour which was
connected to the Aegean Sea by the Kesik 'canal.' **Concerning this idea, there are
various interpretations in the literature**, and the Kesik 'canal' has been the
subject of great interest in this respect. **It is thought that** the canal was
opened by man… **Although the canal is too high for direct water connection**, there
are some ideas that it could have been used as a dry slipway to transport ships"
(723, footnotes to Cook 1973 and Zangger et al. 1999). The refutation lands on the
next page in the swamp sentence quoted above. **Both instances of that sentence,
2003 and 2014, are the setup of a refutation. The quotation may not be used to show
Kayan in two minds — it never was two minds.**

Numbers repeated verbatim from 2003 (so: one witness, not two): ridge "only about
600 m wide", "a little more than 20 m at the top"; "the highest point in the bottom
is 13.7 m above sea level at a distance of about 150 m from the sea"; "the inner
side profile … opens on to the Kesik plain at an elevation of **6.3 m about 400 m
east of the top**"; "**the Neogene bedrock (sandy marl here) is covered by 2 m of
colluvium**"; "**no archaeological material was encountered**". 2014 adds one
figure 2003 lacked: the mid-cut bedrock threshold "at a height of **about 13 m**
above sea level" — his own rounding of the 13.7 m. **Still no width and no depth in
Kayan's own text; the 400 × 50 × 30 m triple remains Zangger's.**

**3. THE LBA SHORELINE — NO. There is no Late Bronze Age isochrone on any 2014 map.
This was the last chance and it does not come.**

**Fig. 16, p. 718** — "Geomorphological development of the Karamenderes (Scamander)
plain (Kayan 2000)" — is **the same sheet as 2003's Fig. 7**, same legend, same
colours, reprinted at a smaller scale (126 px/km at 600 dpi here against 147.3 px/km
at 500 dpi there). Its dated coastline positions are the same four and no more:
**6000–5500 BP · 5000–4500 BP · 2000 B.P. · Present**, plus **6000 BP** and
**Present** at Beşik. **No Bronze Age line. No 3500 BP line.** The LBA still falls
in the unlabelled gap between the 5000–4500 BP and 2000 BP shores.

Re-measured on the 2014 print as a cross-check of the method (figure measurement,
this dossier; §3.7b), nearest "Troia and Beşik bays 6000 BP" pixel to the Troia dot
per bearing, against §1.5c's reading of the same plate in the 2003 print:

| bearing | 2014 print | 2003 print (§1.5c) |
|---|---|---|
| 300°–345° | **0.31–0.33 km** | 0.27–0.33 km |
| 000° (N) | 0.35 km | 0.31 km |
| 270°–285° | 0.39–0.47 km | 0.39 km |
| 225°–255° | 0.69–0.78 km | 0.47–0.65 km |
| 045° | 0.60 km | 0.52 km |

Two prints, two measurements, same plate: **the NW–W sector reproduces to within
0.06 km; the S–SW sector to within 0.15 km.** The method is sound and §1.5c's table
stands. What it measures is still the **6000 BP** bay, not an LBA shore.

**What 2014 *does* commit for the Bronze Age, and it is a section, not a map.**
**Fig. 15, p. 716** is a new plate (no prior-publication credit in its caption): a
N–S cross-section "near the foot of western slope of Troia", running from the lower
Dümrek valley south to the western slope, boreholes 126, 43, 127, 129, 182, 15 and
75. On it, at about +1 m, runs a labelled horizon: "**End of delta formation about
3500 years ago**". Below it "Delta 1" (coarse sandy delta sediments), "Delta 2",
"Interchannel", "Coastal platform" and "Last marine sediments"; above it flood-plain
sediments and colluvium. Three blue arrows on the left carry the sea-level story in
his own captioning: **1 "Sea-level rise until 6000 years ago" · 2 "Sea-level fall
5000–3500 years ago" · 3 "Sea-level rise until 2000 years ago"**. The caption reads:
"a bedrock platform along the foot of northern slope of Troia, about 10 m below
present surface **was a narrow coastal environment in the Bronze Age. Deltaic
shoreline in the Karamenderes valley reached here with various sedimentary facies,
towards the end of this period.**"

**That is as close as Kayan ever comes to an *Iliad*-time shoreline, and it is a
statement about a section line at the citadel's western foot, not a distance.** It
says deltaic sedimentation at the foot of Troia's western slope **ended about
3500 BP** — i.e. the delta front had passed the citadel by then and the shore lay
beyond it. It commits **no** distance, and **no distance may be derived from it**:
a section gives you a date at a place, not a shore at a date. Anyone drawing an LBA
line still draws an interpolation, exactly as §1.5c concluded — but the interpolation
now has a *lower* bound in Kayan's own hand: **by ~3500 BP the water was already
past the western foot.**

One further 2014 number, textual and new: the delta "presently reach[es] **about
4 km northwest of Troia**" (703). Measured on Fig. 16 (§3.7b) the present coast is
~4.4 km due north and beyond 4.9 km NNW, so his "about 4 km" is the map's number
rounded down; the two are consistent within the ±10% these plates carry (§3.7a).

**4. BARRIER AND LAGOON, 2014 — the Beşik-only picture is unchanged, and now it is
DATED and DRAWN.** This is the acquisition §5 item 4 was hoping for and did not get.

- **The Karamenderes denial is repeated verbatim**, p. 712, of the transition zone
  capping the marine unit: "**There is no beach or lagoon formation. Instead,
  sediments indicate swampy or seasonally wet environments.**" Word for word what
  2003, 390 says. **No Scamander-front barrier at any date, in text or on any
  plate.** (Kraft's 2000 BP Scamander barrier, §1.4a, remains the only one anyone
  has ever drawn, and it is not in this chapter.)
- **At Beşik the barrier is now dated to Troia VI**, p. 704 — a date 2003 did not
  give: "We showed that the present Beşik plain formed as a small bay about 6,000
  years ago. Afterwards, **around the period of Troia VI, a coastal barrier
  separated a small lagoon** (Figs. 6–7). … the sea fell about 2 m in the Late
  Bronze Age and **caused widening of the coastal barrier and reduced the lagoon.
  This implies that no Bronze Age natural harbour with an open water surface seems
  to have been possible here** (Fig. 8)."
- **Fig. 6, p. 707** — "The west-east cross-section of the Beşik plain… Based on 80
  shallow hand-drilling sediment samples, **a coastal barrier system separating a
  laggon [sic] has been outlined in several periods (H1–5)**. (Modified from Fig. 4
  in Kayan 1991)." The section runs W–E across ~1.4 km with the Aegean at the left,
  and it carries a legend of **dated shoreline positions: ① 6000 BP · ② 3500 BP ·
  ③ 2000 BP · ④ Present**, each plotted at its place on the profile. Units drawn:
  Beach, Dune field, **Old barrier**, **Lagoon**, Lagoonal mud, Coastal sand,
  Coastal barrier (H2/H3), Older coastal sediments (H1), Colluvial footslope,
  Shallow marine sediments, Shallow marine Pleistocene, Neogene bedrock. ¹⁴C dates
  in position: **8000, 6700, 5200, 4500, 3500, 5800, >24000?** and 2000.
- **Fig. 7, p. 708** — "Geomorphological development periods of the Beşik plain.
  (Modified from Plate 5 in Kayan 1991)" — is the same thing in plan: LAGOON, OLD
  BARRIER, DUNE FIELD, LAGOONAL CHANNEL, DUNE RIDGE, SANDY BEACH, with the same four
  numbered coastline positions on the map and Beşik-Yassıtepe and Sivritepe on the
  bounding slopes.
- **What the two figures fix, and it is drawable geometry for a Beşik plate:** at
  **3500 BP — position ② — the shoreline is on the SEAWARD flank of the coastal
  barrier**, with the lagoon behind it landward, at roughly −1.5 to −2 m on the
  section (a soft read off a small figure; Grok's independent read leans −2 m). The
  LBA sea at Beşik is therefore *outside* a barrier, and the enclosed water behind
  it is a shrinking lagoon, not a bay. **That is what "no Bronze Age natural harbour
  with an open water surface" means, drawn.**
- Authority: **geometry**, for Beşik only, and **±** whatever the 1991 hand-drilling
  survey is worth — 80 holes to 8 m with a hand auger, samples that "could not be
  taken under undisturbed conditions" by the chapter's own admission (Fig. 5
  caption, p. 706).

**5. THE BAY'S SOUTHERN EXTENT AND THE PROGRADATION STAGES — no revision, no new
dates, and the 17 km is gone.**

- The southern limit is stated twice, both times by place-name and never in
  kilometres: "By 7,000–6,000 years ago, a ria type bay in the present lower
  Karamenderes valley west of Troia, extended southwards **as far as just north of
  Pınarbaşı-Mahmudiye** (Fig. 4)" (703); "the coastline continued to advance south,
  covering former delta plains and **reaching the vicinity of Pınarbaşı** (Fig. 4)"
  (718). **The abstract's "17 km" of 2003 appears nowhere in this chapter** — which
  strengthens §1.5's finding that the 17 km is the 2003 abstract's own reduction of
  a place-name and cannot be cited to a body page in either chapter.
- **Fig. 4, p. 705 is a NEW plate** and the only wholly new map in the chapter:
  "Paleogeographical reconstruction of the lower parts of the Karamenderes
  (Scamander) and Dümrek (Simois) valleys in the Middle Holocene, about 7000–6000
  years ago." Blue sea on a yellow low plateau, legend "**Bay in the Middle Holocene
  (7000–6000 years ago)**", with **KESİK INLET** labelled as open water, Beşik as a
  separate small bay, swamp stipple along the southern and eastern fringes, and the
  caption "A Troia settlement did not exist yet. However, the Alacalıgöl and
  Kumtepe Neolithic settlements were already established on the shoreline of the
  embayment."
  Measured (figure measurement, this dossier; §3.7b): **open water 0.19–0.26 km from
  the Troia dot through the whole 300°–030° sector**, 0.30–0.46 km at 240°–270°, and
  the embayment's head **3.2–3.8 km south to south-south-east**. So Fig. 4 puts the
  mid-Holocene water *closer* to the citadel than Fig. 16's 6000 BP bay does
  (0.31–0.35 km) — the same research group's two plates of the same event, ~0.1 km
  apart, which is the honest size of the noise on these sheets and a useful
  calibration for §3.7a's ±10%.
- The stage sequence is unchanged and is stated as three units, not four shorelines:
  Early–Middle Holocene marine embayment; **Middle Holocene (Bronze Age) deltaic
  progradation, "a period of faster development because of small sea level fall"**;
  Late Holocene slower progradation and alluvial-colluvial sedimentation (abstract,
  694). Dates repeated from earlier work: sea into the incised channel ~10,000 BP;
  bay at maximum ~7000 BP; sea level stops rising ~6000 BP; regressive sequence
  **5000–3500 BP**; delta formation at Troia's western foot ends **~3500 BP**
  (Fig. 15).
- One new number worth keeping, p. 717: "**6 to 7 m of sediment has been deposited
  on the bottom near environs of Troia since Troia VI (over the last 3,250 years)**."
  That both dates Troia VI at ~3250 BP in Kayan's own hand — matching the position of
  the "Troian War" label on Fig. 8 — and gives an aggradation rate of ~1.9–2.2 mm/yr
  at the citadel's foot. Compare §3.1's Strabo-derived ~2.8 mm/yr on the DEM: the
  same order, from a wholly independent route. That is a genuine cross-check and it
  is worth saying so.

**6. HARBOURS, THE CAMP AND HOMER IN HIS OWN 2014 VOICE — and the trajectory has
moved, in the direction nobody expected.**

- **He now says Troia had harbours.** p. 720, opening the harbour section: "**Since
  the Karamenderes plain was a long bay for several millennia after 7,000 years ago,
  Troia must have had a harbour or harbours in different places following changes of
  coastline positions during deltaic progradation. An important question then arises
  as to where the Troia harbours were.**" Set that against the 2003 abstract's "the
  geographical environment has never been suitable for the establishment of an
  important harbour" (§1.5). **The 2014 opening is an affirmative, and the chapter
  never answers the question it raises** — it goes on to dismantle the three western
  candidates (Yeniköy, Kesik, Kumtepe) one at a time and stops. Combined with the
  2003 conclusions' concession that "suitable places on the changing shoreline could
  have been used according to necessity as natural harbours" (401, §1.9), **Kayan's
  settled position is: harbours yes, harbour *works* no, location unknown.** The
  flat "Kayan denies a harbour" that §2 has been carrying is not his 2014 voice.
- **Kumtepe is dispatched too**, p. 725, and on a ground worth having: "This lowest
  part of the Karamenderes plain was described by Strabo at the time of Christ, and
  mapped by Leake based on his descriptions. **No marine indentation was shown on
  this map.** Also, there is no evidence indicating that Kumtepe indentation was used
  as harbour." Kayan citing **Leake 1824** against a harbour is a datum for the
  Strabo lane (§1.10), and it is the only place in this literature where an
  early-modern reconstruction is used as negative evidence.
- **Yeniköy**: no natural or artificial marine connection over the Beşik–Yeniköy
  threshold ever; the ditch across it is "almost certain[ly]" a freshwater channel
  from the Pınarbaşı springs to the Beşik plain, last cleaned in the 1950s, feeding
  the Hanımdeğirmeni water-mill (721). That is 2003's reading unchanged and it
  corroborates §1.9's Yeniköy paragraph first-hand.
- **On Homer, twice, and unusually warmly for a geomorphologist.** p. 695: "the most
  important reason for this interest is the detailed description of the geographical
  environment made by Homer… descriptions of the geographical environment of around
  **2700 or 3250 years ago — depending if one assumes Homer describes the landscape
  at his own lifetime, or at the supposedly earlier time of the Trojan War** — which
  have reached the present day as written text are an important original feature of
  Troia offered by Homer." And p. 696: "**Thus, in one respect, Homer has constituted
  a basis for environmental approaches in modern archaeology and the rise of
  geoarchaeology.**" He states the two-date problem exactly as our own apparatus has
  to, and he does not adjudicate it.
- **No camp claim.** The word "camp" does not occur in the chapter; Beşik is
  discussed only as a barrier-lagoon system with no open water in the Bronze Age.
  **Kayan 2014 is not a source for the Achaean camp anywhere** — do not let the 1980
  and 1982 Kraft-and-Kayan camp statements be re-attributed to it.
- **Tsunami: denied, flatly, and this is new material.** pp. 717–18: "In our core
  drillings, which reached 318 in number… **we have never encountered any evidence of
  a tsunami**"; a wave's intrusion up the strait or over the Yeniköy ridge is "hard
  to postulate"; and the marine shells others read as inundation evidence are food
  waste, mud-brick temper and ornament — "**the existence of shell remains at a site
  about 30 m above sea level like Troia is not an evidence of an inundation caused by
  a tsunami**". Useful if any plate or note ever reaches for a tsunami.
- **Earthquakes: agnostic, and he says why the question is unanswerable by his
  methods.** pp. 716–17: no tilting or deformation detected on the marine unit's top
  surface, so "severe tectonic activity of a magnitude that could have had an effect
  on the morphology has not occured during the last 7,000 years" — with the honest
  rider "**of course, this is not evidence for the stability of the region**" — and
  the trench-depth argument: since Troia VI, 6–7 m of sediment has accumulated, while
  earthquake trenches "only reach depths of about 4–5 m", so "**it makes no sense to
  try to find marks of tectonic deformation from supposed earthquakes in the Troia VI
  period in these younger sediment layers**". His conclusion: "earth science research
  techniques alone are not enough to obtain evidence to prove one way or the other if
  earthquakes destroyed Troia VI."

**7. The campaign's parameters, first-hand — and the 318 is confirmed with its
composition.** 7 MTA rotary holes in 1977, deepest **75 m** to pre-Holocene bedrock;
80 Eijkelkamp hand drillings to 8 m on the Beşik plain from 1983; the Daimler-Benz
Unimog screw rig from 1988, to **20.50 m**, plus trenches to 2.5–3 m; Cobra
percussion gouge-coring from the later 1990s (corer 35/50/60 mm, "possible to reach
down to 30 m… however, **15–20 m is a good depth**"), hydraulic lifter from 1997.
"**In 2006, the number of Cobra core-drillings reached 118 and the total number of
the Troia drillings 318**" (706); Fig. 2's caption (p. 700) breaks it down —
**1–100 Unimog, 101–218 Cobra, plus 100 on the Beşik plain and Yeniköy–Sigeion
ridge**, "thus, the total number of the drillings reached 318 in 2006". So the
dossier's "285 by 2001 / 318 by 2006" reading (§1.5b) is right, and **Zangger's "318
holes between 1977 and 2006" (§1.9) checks out against the source**.

**The twenty figures, so nobody hunts for one twice:**

| fig. | p. | what it is | after |
|---|---|---|---|
| 1 | 695 | geomorphological outlines of the Troia area | — |
| 2 | 700 | locations of the 318 core-drilling points | — |
| 3 | 704 | photo: MTA rotary drilling (ÇKM 4) north of Troia | — |
| 4 | 705 | **NEW: paleogeographical reconstruction, 7000–6000 BP**, blue bay, "KESİK INLET" | — |
| 5 | 706 | photo: Eijkelkamp hand-drilling profile | — |
| 6 | 707 | **Beşik plain W–E cross-section, barrier + lagoon, H1–5, dated shorelines ①–④** | Kayan 1991 fig. 4 |
| 7 | 708 | **Beşik plain in plan: lagoon, old barrier, dune field, shorelines ①–④** | Kayan 1991 pl. 5 |
| 8 | 709 | **the relative sea-level curve** (§1.5d.1) | Kayan 1991 |
| 9 | 710 | photo: Unimog screw drilling | — |
| 10 | 711 | photo: Unimog trench, two fills in the Troia defence ditch | — |
| 11 | 712 | photo: screw-corer sediment samples | — |
| 12 | 713 | photo: Cobra gouge-corer operation | — |
| 13 | 714 | photo: core profile, drilling 213 north of Troia | — |
| 14 | 715 | drilling log 213 in the standard computer form | — |
| 15 | 716 | **N–S section at Troia's western foot; "End of delta formation about 3500 years ago"** | — |
| 16 | 718 | **the reconstruction map** = 2003's fig. 7, four isochrones, **no LBA line** | Kayan 2000 |
| 17 | 719 | simplified W–E section of the lower Karamenderes–Dümrek plain | Kayan 1995 |
| 18 | 720 | photo: western slope of Troia, drillings 183 and 129 | — |
| 19 | 722 | drill-hole details along Schliemann's N–S trench | Kayan 1996 |
| 20 | 724 | **Yeniköy / Kesik / Kumtepe cross-sections** = 2003's fig. 6, + a locator inset | Kayan 1995 |

Fig. 20 confirms §1.5c's reading of the 2003 Fig. 6 in every particular: three
stacked sections, the Kesik one carrying "Canal bottom profile" and "Northern ridge
profile" as line traces over the ridge, the Yeniköy one carrying the Beşik–Yeniköy
threshold with its "Old canal profile" and the water-mill, dates **Kumtepe 5500,
7000 BP · Kesik 3400, 4200, 4500 BP · Yeniköy 5500, 5800, 5300, 12,500 BP**,
thresholds standing well above present sea level on all three, and **no barrier and
no lagoon on any of them**.

#### 1.5e Kayan 1997b — the Çıplak valley paper, READ IN FULL 2026-07-30

- Citation: Kayan, İlhan. "Geomorphological Evolution of the Çıplak Valley and
  Archaeological Material in the Alluvial Sediments to the South of the Lower
  City of Troia." *Studia Troica* 7 (1997): 489–507.
- **Cite the article's own title, not the volume's table of contents**, which
  prints a different subtitle ("…and Geo-archaeological Interpretations
  Concerning the Lower City of Troia"). The running head and first page carry the
  title given above; so does Kayan's own 1999 reference list (§1.5a).
- Verified how: full text, offprint scan, note at
  `research-cache/kayan-1997-ciplak-notes.md`. **OCR caveat:** the text layer is
  badly degraded (Turkish diacritics and several common letters render as
  mojibake); the quotations below were cleaned by hand against the visible
  English and should be re-checked against page images before any of them is
  published to the site.

**Why it matters most:** it is "1997b", and it argues nothing about the
regression — see §1.5a, where the whole citation question is closed.

**The Middle Holocene maximum in the valley, and the first archaeological
material (p. 489 abstract, p. 501).** The Çıplak plain lies in a **pre-Holocene
structural depression** between two 30–50 m Neogene sandstone ridges; the Middle
Holocene transgression reached its maximum extension into the valley about
**7000 BP**, on two ¹⁴C dates from drillholes near the Troia ridge — **no ¹⁴C
date from inside the valley itself**. Beyond that maximum, at about **13 m below
present surface**, drilling found sherds, marine shells (probable food remains)
and charcoal, estimated by comparison rather than measured at **about the 7th
millennium BP**. Drillhole 22 gives the same picture: sherds, shells and a large
stone on the pre-Holocene fill 13 m down, unevaluable archaeologically because
rotary-auger drilling disturbed them.
- Authority: **geometry** (depths, the 7000 BP maximum) with Kayan's own "no
  absolute date is available" printed twice on the same page.

**NEW — a destruction layer at the Lower City's southern foot (pp. 489, 503–4).**
An approximately **1 m thick layer, 2–4 m below present surface**, at the foot of
the southern slope near the Lower City, made mostly of **small sherd grains and
charcoal** in sandy alluvial-colluvial mud, running south to an old river channel
where it breaks off; a second, less sherd-rich band follows the channel's south
edge. Kayan's own reading, verbatim (p. 489): "**Both of these layers suggest a
destruction, perhaps by fire, of the Lower City. Material washed downslope from
the ruins must have formed this sediment layer.**" The grains are too small and
eroded to date directly; **Troia's archaeologists judge a Hellenistic-Roman date
most probable**, and Kayan reports the sedimentology and geomorphology as
consistent with that.
- Authority: **geometry** for the layer's depth and thickness; **identification,
  and second-hand within the paper** for the date — it is the excavation team's
  period judgment, reported by Kayan, not a measurement. Never print it as a
  dated destruction horizon.

**NEW — a SECOND rock-cut ditch, at the foot of the Lower City slope, and it is
NOT the Kesik cut (p. 504).** Geophysical prospection in 1995 found a rock-cut
ditch running **east–west along the foot of the southern slope**, on the wide
bedrock platform the same pages describe (a "rather wide surface" exposed in
earlier habitation periods, covered directly by colluvial habitation material —
stone blocks, broken tiles, sherds, bone). **Dr. P. Jablonka proposed it was
first dug in the Bronze Age, Troia VI, then widened and deepened in the
Hellenistic period.** Kayan's drilling settled one thing about it: the deeper
fill is calm-water mud with an undisturbed seasonal mud-crack structure and no
flow structure, so — his words — "**This ditch, then, cannot have been dug as a
water canal.**" Sherd-bearing mud bands in its wider upper part resemble those in
the destruction layer above, which he reads as a connection between the two.
- **DO NOT CONFLATE THIS WITH THE KESIK CUT (§1.9).** Different feature,
  different place: this one is a few hundred metres of rock-cut ditch at the
  southern foot of Troia's own Lower City slope; the Kesik cut is ~5 km west,
  through the Yeniköy/Sigeum ridge, and is the one the Nestor-wall-and-ditch
  reading attaches to. Nothing in this paper touches Kesik, the Achaean wall,
  Nestor or the *Iliad*.
- **Probably, but not verifiably, the same feature as the Troia VI
  *Verteidigungsgraben*** already in §1.9's last block (Jablonka, König & Riehl
  1994; Becker & Jansen 1994) — same author of the identification, same period,
  same quarter of the site. This dossier has not seen either 1994 paper, so
  record the likeness and **do not merge the two entries**.
- Authority: **identification, second-hand** (Jablonka's, reported by Kayan) for
  Troia VI; **geometry/prose, first-hand** for the not-a-canal finding.

**The ceiling claim, a fourth printing (p. 501, verbatim).** "A careful
examination of the sea level revealed that marine sediments did not occur higher
than the present sea level, and the highest position of marine sandy sediments,
probably coastal sand deposits, was located almost at present sea level… This
confirms that the sea level during the Holocene was never higher than its present
position." Carried at §1.8.

**Two smaller things, recorded so nobody re-reads the paper for them.** The 1996
campaign's drilling totals: 53 holes around Troia (33 earlier + 20 new), 235 m of
combined length, deepest single hole 27 m, first use of percussion gouge-auger
equipment; 210 drilling points in the wider Troia area by 1996 (pp. 489, 492).
And a **paleoclimatic aside** (p. 501): limy-concretion sediments in the
marine-to-terrestrial transition are read as hot, dry summers and high
evaporation during the Climatic Optimum, c. 6000–5000 BP — a climatic inference
about the Early/Middle Holocene transition, **not** about the Bronze Age
regression. Do not recruit it to that argument.

**Absent from this paper:** springs and Troia's water supply (that is Kayan 2000);
Kesik; Beşik; any harbour question; any coordinate — no figure was measured.

#### 1.5f Kayan 1999 — the *QSR* regional synthesis, READ IN FULL 2026-07-30

- Citation: Kayan, İlhan. "Holocene Stratigraphy and Geomorphological Evolution
  of the Aegean Coastal Plains of Anatolia." *Quaternary Science Reviews* 18
  (1999): 541–48. **The issue numbers "4–5" are not printed on the extracted
  pages** — the dossier may keep them where it already prints them, flagged as
  unverified, and should not add them anywhere new.
- Verified how: full text, note at `research-cache/kayan-1999-qsr-notes.md`.

**What it is for this dossier: a synthesis, not a new measurement.** Three-stage
regional model (p. 541) — Early Holocene transgression; Middle Holocene sea level
reaching present level and stopping, with alluviation and deltaic progradation
dominant; Late Holocene progradation slowing under floodplain cover — and the
regional-synchrony claim that carries the causal argument: "**These
characteristics can be observed in the same sequence throughout the Aegean coast
of Turkey.**" Sea reaches present level **about 6000 BP** on ¹⁴C dates of marine
molluscs, citing Kayan 1988 and 1991 (pp. 544–45).

**It resolves the "1997b" letters and restates the anti-tectonic position** —
both quoted and applied at §1.5a. It supplies the **fifth printing** of the
5000–3500 BP / ~2 m interval (§1.5a table) and a regional form of the **ceiling**
claim (§1.8).

**What it does NOT carry, so nobody hunts for it.** **No plotted sea-level
curve** — this is the one paper in the series with no RSL time series to measure.
Its Fig. 4 (Karamenderes plain) and Fig. 5 (Çıplak valley) are schematic
stratigraphic cross-sections, both credited "modified from Kraft et al. (1980)
with reinterpretation based on new drilling evidence"; nothing was lifted from
either. Nothing new on the Beşik barrier, the lagoon or Kesik.

**The post-Bronze-Age recovery, restated (p. 546):** "the slowly rising sea again
reached nearly the present level around the time of Christ. However this rise was
slower than deltaic progradation, and marine intrusion was not repeated." Same
prose as Kayan et al. 2003's; since this paper prints no curve, the mismatch
§1.5a records between that sentence and the plotted −0.4 m at 2000 BP is neither
helped nor worsened here.

**And a Late Holocene human-impact strand (p. 546),** citing "Kayan, 1996, 1997b
and c": accelerated sedimentation from agriculture and deforestation, distinct
from the natural progradation phase. Worth noting only because it is a **second**
in-text use of "1997b" for the Çıplak paper, on a point the Çıplak paper actually
makes — which is what makes the letter assignment (§1.5a) solid rather than a
reference-list artifact.

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
  conversions); **identification** (Kesik as harbour candidate — **Brückner's own,
  see below**); **prose** (the two-scenario framing).
- **CORRECTION, 2026-07-30, and it reassigns the dossier's most-repeated
  identification.** This dossier has treated "The best candidate for a natural
  harbour at that time is the present-day Kesik plain" as Brückner *reporting*
  Kraft, Kayan, Brückner & Rapp 2003a, and cited it to that chapter at §1.4, §1.9,
  §1.11c and §2. **The chapter does not contain it** (§1.4, first-hand): its own
  sentence endorses Zangger's three embayments as having "had excellent harbor
  potentials" and picks none. Nor is the sentence attributed to anyone in
  Brückner's own text — it stands in his voice, in a survey paper, in the same
  paragraph as the Strabo distances. **So the claim is Helmut Brückner's, made in
  2005, in a paper of his own**, by an author who is fourth-named on 2003a and who
  may well be summarising a view he holds; but it is **his** claim and must be
  cited to him. Cite: Brückner et al. 2005, §21. Do not launder it into a Kraft
  citation, and note the standing of a claim that its own author's co-authored
  chapter declines to make.
- **Second correction, same day, same paragraph: the two scenarios are now in hand
  as drawings.** Brückner's "Scenario I" (Kayan) and "Scenario II" (Kraft) are
  Figs. 9 and 10 of the 2003a chapter, pp. 373–74 (§1.4a). His prose summary of
  Scenario II — "bird's-foot delta in a quiescent embayment until c. 0 BC/AD" — is
  a fair reading of Fig. 10. His summary of Scenario I — "delta passes the city
  soon after 2200 BC" — is **not** what Fig. 9 draws, whose labelled shorelines run
  3500–4000 BC, 2500–3000 BC, 500–1000 BC, and it is not what Kayan's own Fig. 7
  draws either (6000–5500, 5000–4500, 2000 BP — §1.5c). Both Kayan plates leave a
  water strip against the citadel's western foot. Use Brückner for the *framing*;
  read the shorelines off the plates.
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

**Claim (the ceiling: the Holocene sea never stood above present level here) —
now stated five times by Kayan himself, 2026-07-30.** This is the constraint
that makes the whole Bronze Age argument run, and the dossier had it only from
the later chapters. Its earlier printings:

- **Kayan 1995, 217**, after the 1988–93 re-drilling: "**no marine sediment was
  found higher than the present sea-level**. We can therefore see that the
  sea-level did not rise higher than its present level during the Holocene."
- **Kayan 1997, 438**, generalised to the whole Aegean coast of Anatolia: the
  6000 BP coastline "can be recognized by coarse sandy coastal sediments with
  plenty of shells below the recent alluvium along the present inner edge of the
  plain. **This coastline has never been detected above its present sea-level in
  any place.**"
- **Kayan 1997b, 501** (the Çıplak valley, §1.5e), at the scale of a single
  secondary embayment: "marine sediments did not occur higher than the present
  sea level… **This confirms that the sea level during the Holocene was never
  higher than its present position.**"
- **Kayan 1999, 547** (Fig. 6 caption, §1.5f), at regional scale across the four
  Aegean coastal plains he compares: "**Marine sediments have not been found
  above present sea level at any place.**" The same paper dates the sea's arrival
  at present level to **about 6000 BP** on ¹⁴C marine molluscs (544–45), citing
  Kayan 1988 and 1991.
- Kayan et al. 2003 and Kayan 2014, as already carried above.

Six printings across 1995, 1997 (NATO), 1997b, 1999, 2003 and 2014 — but **one
drilling campaign**, restated. It is a well-attested negative result, not five
independent tests of it.

- Authority: **geometry**, at the level of a stated negative result from a
  borehole campaign.
- **Note what this contradicts, and do not smooth it over.** Erol's 1982 curve
  (§1.2, §1.5a) puts Anatolian sea level **+2 m at 6500–5500 BP and +1 m at
  3000–2000 BP**, and the 1982 chapter uses those high stands to explain the
  Beşik deposits lying above present sea level (p. 39) rather than invoking
  tectonic uplift. Kayan's own later drilling denies any Holocene stand above
  present. **One research group, two positions, twenty years apart** — record
  both with their years; never present the high stand and the ~2 m fall as parts
  of one curve.

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
  - ~~**Kayan: natural.** A **tectonic depression** (Kayan 2009, 124; Kayan 2014,
    723), later **widened by foot traffic** between coast and plain (Kayan 2014,
    724) — never a dug work at all.~~
    **REWRITTEN 2026-07-30, first-hand from Kayan 2014 (§1.5d.2). The second-hand
    version overstated him on both halves.** 2014, 723 says the canal "**appears
    artificial with its very straight direction**", that "**no evidence has been
    discovered to suggest that it was dug out**", that "there is **some evidence
    implying** that the canal depression is naturally formed **on a fault line**" —
    and then, in the same paragraph, that "**sedimentological and stratigraphical
    features of the Holocene deposits in the Kesik depression do NOT support such
    tectonic activity for the Holocene**". His preferred explanation is a
    **pre-Holocene** fault line: "The Kesik canal **may have originally formed on a
    fault line before the Holocene**, long before human activity in this area"
    (724). He is explicit that this is not a new position: "**In the new stage of
    our research we have obtained no evidence to change our former
    interpretation**" (723) — the 2003 agnosticism (§1.5b) stands, with a preferred
    hypothesis attached. And "**widened by foot traffic**" is not in him: 724 says
    the canal "has been **used** continuously for land passage", and attributes the
    only digging to modern drainage attempts that produced "nothing as large as the
    Kesik canal". **Never write "Kayan: tectonic depression" flat** — it inverts his
    Holocene claim, which is the only epoch a Bronze Age plate cares about. The
    Kayan 2009, 123–24 leg is now first-hand (read 2026-07-30) and is 2014's own
    source text — one position, two printings (§5 item 7).
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

**THE KESIK MEASUREMENTS ARE NOW PRIMARY, NOT SECOND-HAND (2026-07-30, Kayan
1995, 223–27).** The figures §1.5b took from Kayan et al. 2003, 398 originate
here, eight years earlier, and they reproduce exactly: the cut's crosswise
profile is asymmetrical (steeper south, gentler north); its **highest bottom
point is 13.7 m above sea level, about 150 m from the seaward mouth**; the
profile then descends gently inland and opens on to the Kesik plain at **6.3 m,
about 400 m east of the top** (223). **Twelve boreholes along the canal floor
found no fill that is either marine or fluvial** — only colluvium "not more than
**2–2.5 m thick**", passing down into disaggregated bedrock (226). So the
colluvium figure the dossier had recorded as "Zangger's rounding" of 2003's flat
2 m is **Kayan's own printed range in the primary paper**; both are his, eight
years apart. On origin, 1995 explicitly rejects the earthquake theory
("completely unsupported by any evidence", 226) and rejects the missing-spoil
argument for hand-digging (no spoil heap; **two boreholes were sunk specifically
to look for one**, 226), leaving the question open with a natural structural
origin preferred and later human use and widening as a crossing — forming
"**slowly rather than in one planned excavation**" (227). That is the same
agnostic-with-a-preferred-natural-origin position 2003 and 2014 restate, at its
first printing.
- Authority: **geometry** (measured elevations and distances, twelve boreholes)
  and **prose** (origin, explicitly undecided).
- Verified how: full text, `research-cache/kayan-1995-troia-bay-notes.md`; every
  page and figure legible, no transcription caveat needed.

**AND THE "NO GREAT HARBOUR THEORIES" VERDICT IS 1995'S, EIGHT YEARS BEFORE THE
SENTENCE THE DOSSIER QUOTES.** Kayan 1995, 231, verbatim: "it is quite possible
that on the changing coast some convenient sites were used as civil or military
harbours as necessary in the course of the various cultural periods of Troia.
However, **no clear evidence has been found up to now to show that the natural
indentations along the western edge of the 'Troia Bay' were organized and used as
main harbours. Therefore we believe it is not necessary to discuss ambitious
theories concerning the harbours of Troia.**" That is Kayan et al. 2003, 401
almost word for word — including **both** halves, the concession of ordinary
beaching places and the denial of *organized* harbours (§2's "Harbour, in
general" row). The 2003 statement is a restatement, not a second witness. His
own ¹⁴C dates in the same paper: the Yeniköy plain silted about **5000** years
ago, the Kesik plain about **4000**; the Kesik embayment persisted "until
4500–4000 B.P.", so it "could only have been used as harbour during the Early
Bronze Age. **But it could not have been so used during the Late Bronze Age,
during the period of Troia VI**" (228). Rounded ages from his table (p. 220,
Heidelberg lab, marine shells): Kesik 3400 / 4500 / 4200 BP, Yeniköy 5500 / 5800
/ 5300 BP (plus one deep sample at 12,500 BP), Kumtepe 5500 and 7000 BP — the
same 3400/4200/4500 spread Fig. 6 of the 2003 chapter prints (§1.5b).

**Kayan's rebuttal of the artificial-canal hypothesis is also 1995's, twenty
years before Zangger & Mutlu 2015.** The Discussion (232–33) answers Zangger's
1992 *The Flood from Heaven* directly, reproducing "Zangger's hypothetical map of
Troia VIIh" as Fig. 15 and countering on five geomorphological grounds: over 100
boreholes and "it is impossible that every single one should by chance have
struck the canals of Atlantis"; marine stratigraphy is distinguishable from
channel fill and the plain was "definitely a marine embayment", still "covered by
a wide swamp" in the Late Bronze Age; a river as flood-prone and
sediment-charged as the Karamenderes could not be confined to artificial canals
without engineering traces, and would open new courses regardless; **no deltaic
formation exists at the mouth of any supposed canal**, and at the Kesik-canal
mouth "the coastline is straight and cliffy and no trace of deltaic formation can
be seen"; and the sand patches read as excavation spoil are wind-blown sand over
deserted villages and cemeteries. His conclusion, verbatim (233): "**it is my
opinion that, from a geomorphological point of view, Zangger's theory that the
plain of Troia is the site of Atlantis does not have the necessary proof.**"
Nothing here changes the dossier's Zangger & Mutlu 2015 extraction; it supplies
the earlier, first-hand version of the argument in Kayan's own words rather than
in Zangger's paraphrase of him.

**Four positive absences on Kesik, recorded so nobody mis-cites them
(2026-07-30).** **Kraft, Kayan & Erol 1982** — zero hits for "Kesik" in the full
chapter (§1.2). **Kayan 1988** — its two case studies are Dalacak and Beşige
only; no Kesik, no Karamenderes delta, no camp candidate. **Kayan 2000** — a
water-supply paper; silent on Kesik. **Kayan 2002** — a north-and-west-footslope
paper; a full-text search returns nothing for "Kesik" (§1.4b). Together with
1980's silence, this confirms that **Kesik enters this research group's
literature with Kayan's *Studia Troica* series and the 2003 chapters**, not
before.

**Naming note, added 2026-07-30 (`RESEARCH-TROAD-TOPOGRAPHY.md` §9.2):** the Kesik
plain, the Lisgar marsh (§1.7), and **Ilıca** are **one basin under three names**.
Cook, independently: "east of it [Kesik Tepe] Spratt's map shows a large marsh
(Lisgar, = Ilıca); it now seems to be drained and cultivated" (Cook 1973, 166;
Grade A). Use whichever name a source uses, but do not treat a change of name as
a change of feature.

**Claim — the Kesik plain.** ~~The basin is **about 800 m wide**, bounded in places
by anomalously steep water-cut cliffs (Kayan 2009, 108 fig. 3); a lake sometimes
forms in it in winter, reaching the cut. Radiocarbon on marine shells puts its
**silting up before 1300 BC** (Kayan 2001, 313; Kayan 2009, 105).~~ **BOTH FIGURES
CORRECTED 2026-07-30 on reading Kayan 2009 in full — neither is in that paper.
See the block below; the plain has no published linear width, and the paper's own
siltation figure is 4000–3500 BP.** What survives unchanged: the basin is bounded
in places by anomalously steep water-cut cliffs, and a lake sometimes forms in it
in winter, reaching the cut. Kayan's own
verdict, verbatim in English: **"Yeniköy and Kesik bays could not have been used
as harbours during the Later Bronze Age, especially during Troia VI"** (Kayan et
al. 2003, 400), and there is **"no evidence"** that the natural bays along the
western margin of the Troian bay were developed as harbours (Kayan et al. 2003,
401).

**CONFIRMED FIRST-HAND, 2026-07-30, and the page cite needs one repair.** The
sentence runs across the page break and must be cited **400–401**, not 400. Its
conclusion 2, entire, from the printed page:

> "Based on chrono-stratigraphical evidence, after the maximum extension of the
> marine environment, the Yeniköy and Kesik embayments changed into land following
> alluviation and deltaic progradation about 5000 and 4000 years ago, respectively
> (Fig. 7). Therefore, **Yeniköy and Kesik bays could not have been used as
> harbours during the Later Bronze Age, especially during Troia VI.** Since the
> water coming from the Pınarbaşı springs spread along this edge of the
> Karamenderes plain, the area was continuously covered by swamps until drainage
> canals were dug in the 1950s…"

And the "no evidence" is at 401, in a fuller and stronger form than the dossier has
been quoting, ending in a sentence that is the flattest thing anyone in this
literature says:

> "…there is **no evidence to indicate that the natural embayments along the
> western edge of 'Troia Bay' were arranged and used as principal harbours**. In
> addition, the progressive coastal environment of the Karamenderes delta plain has
> always been covered with very shallow water or swamps. This is not a suitable
> place for big harbour sites. **Therefore, we suggest there is no reason to create
> great harbour theories relating to Troia.**"

Two qualifications the fuller text adds, and both cut *for* the sources and against
a flat "no harbour": the denial is of **"principal"** and **"big"** harbours, and
conclusion 3 concedes the ordinary case — "**Suitable places on the changing
shoreline could have been used according to necessity as natural harbours during
the various periods of Troia culture** (Fig. 7)" (401). So Kayan denies a harbour
*installation*, not a place to beach ships. That is a narrower claim than §2's
"harbour, in general" row has been carrying, and it is compatible with Kraft's
"had excellent harbor potentials" (§1.4) in a way the dossier has been treating as
a head-on clash. Record the narrowing; the clash over **Kesik specifically**
survives it. ~~Elsewhere he writes the opposite mood: **"One can easily imagine that the
Kesik plain could have been an excellent harbor which was connected to the Aegean
Sea by the Kesik 'canal'"** (Kayan 2014, 723).~~ **STRUCK 2026-07-30, first-hand:
there is no opposite mood.** That sentence stands at Kayan 2014, 723 as the opening
of a paragraph that immediately turns on it — "**Concerning this idea, there are
various interpretations in the literature** … It is thought that the canal was
opened by man … **Although the canal is too high for direct water connection**,
there are some ideas that it could have been used as a dry slipway" (723, citing
Cook 1973 and Zangger et al. 1999) — and is refuted on the next page: "**During this
period the Kesik depression was not a marine embayment; instead, it was covered by a
swamp. Therefore, a harbor is not a subject of discussion for the Kesik
depression**" (724). The 2003 instance is concessive (§1.5b) and **the 2014 instance
is the setup of a refutation too**. §6's open question on this is closed. The
quotation may never be used to show Kayan contradicting himself.
- Authority: **identification** (not an LBA harbour). The geometry that used to
  sit on this line — "800 m", "pre-1300 BC" — has been withdrawn; see below.
- Verified how: **first-hand from the printed pages 398–401** (author-shared
  extract, §0), 2026-07-30. Zangger & Mutlu 2015, 566 and 569–70, fnn. 37, 60–65,
  is no longer needed for these two quotations and his page numbers check out apart
  from the 400/400–401 split above. The **800 m** width and the **pre-1300 BC**
  siltation are **not** in this chapter, whose own dates are 3400/4200/4500 BP
  (§1.5b) — and, as of 2026-07-30, they are not in Kayan 2009 either. **Kayan
  2001, 313 is now the sole surviving source for "before 1300 BC", and it is
  still unread** (§5 item 7). The "800 m" has no source left at all.
- ~~**This is a head-on contradiction with §1.4**, where Kraft et al. take the Kesik
  plain as the best harbour candidate at c. 1200 BC.~~ **WITHDRAWN 2026-07-30 on
  reading 2003a in full (§1.4): that chapter never calls the Kesik plain the best
  candidate.** What it says is that all three western embayments "had excellent
  harbor potentials" and that the southernmost was already silted. The
  "Kesik-as-harbour" attribution to Kraft et al. 2003a was **Brückner's paraphrase
  in 2005, taken over by us**, and it should not be repeated. The live
  disagreements that remain are real and narrower — see the five-cornered table
  below, as revised.

**KAYAN 2009 READ IN FULL, 2026-07-30 — the most detailed Kesik paper there is,
and it does not give the dossier the two numbers it was pulled for.**

- Citation: Kayan, İlhan. "Kesik Plain and Alacalıgöl Mound: An Assessment of the
  Paleogeography around Troia." *Studia Troica* 18 (2009): 105–28.
- **The year is 2009.** The title page reads "STUDIA TROICA / Band 18 · 2009",
  and the volume's contents place the article at 105–28 among companion papers
  themselves dated 2009. **Kayan 2014's bibliography, p. 727, misprints it as
  "2008" — the dossier's suspicion (§5 item 7) is confirmed, and the error is
  2014's.** Cite 2009.
- Verified how: full text, all 23 figures, read from page images (the scan's
  embedded OCR text exists but was not relied on; print clean throughout). Note
  at `research-cache/kayan-2009-kesik-notes.md`.

**The canal, measured, and it rounds the older figure rather than revising it
(pp. 109, 123–24).** The bedrock threshold in the canal floor stands **13 m above
sea level** — "we discovered that the depth of bedrock was 13 m above sea level,
even at the lowest part of the Kesik canal" (109); "the bedrock forms a threshold
in the middle at a height of 13 m above sea level" (123–24). **That is
1995/2003's 13.7 m stated to the nearest metre, not a re-measurement**; nothing
in the text reports new drilling on the threshold. Likewise the colluvial floor
fill, "a layer of natural colluvial soil **less than 2 m thick** on the bedrock"
(109), against 1995/2003's 2–2.5 m — a looser paraphrase of the same
observation. **Quote 13.7 m and 2–2.5 m from 1995, where they are measured; use
2009 only to show the figure held.**

**And 2009 is 2014's source text, close to verbatim.** The Conclusion (123–24)
carries the whole paragraph §1.5d.2 quotes from 2014, 723 — "In brief, the Kesik
canal appears artificial with its very straight direction. However, no evidence
has been discovered to suggest that it was dug out, nor has any trace of dumped
material been found in surrounding fields. The canal is very narrow and the
bedrock forms a threshold in the middle… **Therefore, the canal cannot possibly
be used as a waterway**" — introduced by the sentence 2014 reuses word for word,
"**In the new stage of our research we have obtained no evidence to change our
former interpretation.**" So does the fault hedge (124): "there is some evidence
implying that the canal depression is naturally formed on a fault line… However,
sedimentological and stratigraphical features of the Holocene deposits in the
Kesik depression **do not support such tectonic activity** during the Holocene…
**The Kesik canal may have originally formed on a fault line before the
Holocene**, long before human activity in this area." **Consequence for the
five-cornered table below: 1995 → 2003 → 2009 → 2014 is one position restated
four times, not four tests of it.** Kayan 2009 is no longer a second-hand corner.

**CORRECTION 1 — the "~800 m" is the Yeniköy RIDGE, not the Kesik plain, and no
plain-width figure exists in this paper.** The Kesik, Yeniköy and Kumtepe plains
are each given as "**an area of about 1 km²**" (105, and again at 110: "Each
indentation covers an area of about 1 km²"). The 800 m in Kayan's Kesik writing
belongs to the ridge: "In contrast to its 8 km length from north to south, the
**Yeniköy ridge is only 800–1000 m wide**, with a maximum height of 60 m" (110).
Fig. 3 (p. 108), which the dossier was citing for the plain's width, is a
**photograph** — a ground view south across the plain — and its caption gives no
figure at all. **Stop citing "Kayan 2009, 108 fig. 3" for an 800 m Kesik-plain
width; the claim is not in the paper.** An area is not a width and must not be
converted into one.
- **And note a disagreement inside Kayan's own ridge figure, unresolved.** Kayan
  et al. 2003, 398 (§1.5b): "To the west of the Kesik plain, the Yeniköy ridge is
  only about **600 m** wide." Kayan 2009, 110: **800–1000 m**. Same author, same
  ridge, six years apart, no note of a change; the measuring line is not stated
  in either. Record both with their years and print neither as *the* width.

**CORRECTION 2 — "before 1300 BC" is not this paper's date.** 2009 dates in BP
throughout. Its operative sentence (105): the rising sedimentation and falling
sea met at a surface about 1 m below present sea level, "This surface is
represented by a swampy sedimentation unit **dated to about 4000–3500 BP**" —
roughly **2050–1550 BC** on the BP-1950 convention, uncalibrated, and Kayan says
at 127 n. 2 that his ¹⁴C dates are "used as rounded values". That range sits
wholly before Troia VI and is therefore **compatible with** "before 1300 BC"
while being a different and earlier claim; 1550 BC is two and a half centuries
off 1300 BC, and the paper never narrows toward the later date. The core spread
behind it (122–23): drilling 18, shell at **4200 BP** about 1 m below surface;
drilling 17, a similar unit a metre deeper, **4400 BP**; drilling 201 in the
middle of the plain, same stratigraphic level, **2500 BP** — read as a real
spread produced by the c. 2 m fall, marginal coastal sediment predating the swamp
that later covered the basin's middle. **Print "4000–3500 BP (c. 2050–1550 BC),
Kayan 2009, 105", and attribute "before 1300 BC" to Kayan 2001, 313 — the one
remaining unread source for it — or to this dossier's own rounding, never to
Kayan 2009.**

**The wall-and-ditch absence, a second time, and now it is evidence.** The paper's
24 pages contain **no wall, no ditch in the fortification sense, no Nestor and no
*Iliad* line**; the words "wall" and "ditch" do not occur. Its only Homeric
sentences are framing — the Alacalıgöl mound and its surroundings were unsettled
"including the period of Troia VI and the period of the following (supposed)
Trojan Wars" (105), and an aside on seismic-destruction theories citing "the
mythology of earthquakes in Homeric poetry and the story of the alleged Troian
War" (121), with no line number and no identification. **An absence in one Kayan
paper could be an omission; an absence in two — 1995 and 2009, both of which
discuss the canal's origin, dimensions and non-use at length — is positive
evidence the identification is not Kayan's.** The Kraft, Rapp, Kayan & Luce
2003b, 166 citation "The Kesik cut, a great wall and ditch (Kayan, 1995)" fails
against both, and the reading now rests on **Luce 1998 alone** (§5 item 9), still
unread.

**NEW — the Alacalıgöl mound (105–8, 119–21).** A Neolithic–Chalcolithic
settlement on the tip of a low flat ridge of Upper Miocene sediment on the Kesik
plain's southwest edge, covering "about 2–3 decares", found by Kayan's own
geomorphological survey rather than by excavation after farmers plowed up
potsherds, stone tools and shell. Dated, verbatim (120): "this settlement can be
dated to the **5th millennium BC (7000–6000 BP)**, which means that it is as
early as the oldest settlements around Troia (Kumtepe, Beşik Sivritepe)." During
occupation the mound sat 3–4 m above a small marine indentation of the Kesik
inlet, itself about 4 m deep, with a **freshwater spring on the western shore** —
"probably important reasons why this place was chosen for settlement" (105). As
the sea fell about 2 m and the basin silted, the shoreline withdrew and the site
was **abandoned and never reoccupied**: "archaeologists working at the site have
not mentioned the existence of any material belonging to the Chalcolithic, Early
Bronze Age, or following periods" (121). Kayan reads the abandonment and the
arrival of swamp conditions as one event — "These two events… are chronologically
in very well accord with each other" (121).
- Authority: **identification** (the Troia Project's own field team, not a
  third-party tradition) and **geometry/dating** (BP dates, elevations, area).
- **Editorially this is the Kesik harbour question's other end**: the one period
  when the inlet was open water is the 5th millennium BC, and it has a settlement
  on it; by Troia VI there is a swamp and nobody living there.

**NEW — Kesiktepe's military use is 20th-century, and 1995's vague note is now
closed.** `kayan-1995-troia-bay-notes.md` flagged an unexplained reference to
"the last great wars" at Kesiktepe with no conflict named. 2009, 111 supplies it:
"Kesiktepe was even used for military observations in **20th century, during the
World Wars and the Çanakkale War**. A round pit at the top of the hill
constitutes remains from this period, and the hill is therefore named 'Kesiktepe
(Cut-hill)'." Likewise the canal at 124: continuous use "for land passage", which
"may have been more important during **the wars of the last century**." **Both
passages are about foot passage and observation posts in the 20th century AD, two
dozen centuries after Troia VI, and neither may be recruited to the
wall-and-ditch reading.**

**Two more things 2009 adds, for the record.** A flat rejection of a Troia
tsunami (122–23: "There is no specific evidence in favor of this argument"), and
the statement that the region's tectonic activity "has not affected and deformed
the geomorphology" of the Holocene sediments (122) — the same conclusion 1999 and
2014 draw (§1.5a, §1.8), from a third paper. Its two pollen-dated samples
(drilling 201, 600 cm and 530 cm, "about 2500 and 2350 years BP") belong to a
study explicitly in progress; cite the ¹⁴C numbers, not the pollen work. **No
coordinate may be lifted from any of its maps** — all are small-scale outline or
satellite images with no grid.

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
  harbour readings.
- **CHECKED 2026-07-30, AND THE CITATION DOES NOT HOLD.** Kayan 1995 has now been
  read cover to cover (pp. 211–35, all fifteen figures and the table;
  `research-cache/kayan-1995-troia-bay-notes.md`). **It contains no mention of a
  defensive wall, a ditch, Nestor, or the *Iliad*'s fortification anywhere.** Its
  Kesik material treats the cut solely as a candidate **harbour-canal**, which it
  rejects, and weighs only natural/structural against human-dug origins
  (pp. 223–27). Whatever Kraft, Rapp, Kayan & Luce 2003b, 166 is invoking "Kayan
  (1995)" for, **it is not this text**. Either the idea is the 2003 authors' own
  and the attribution is loose, or it points at something not present in this
  paper as printed. **The wall-and-ditch identification must not be attributed to
  Kayan 1995**, and wherever the dossier repeats that identification it must say
  that the sole citation offered for it does not check out against its own source.
  What survives is §1.9's point 1: the reading has **two independent-looking
  citations and one idea**, and one of the two has now failed — leaving **Luce
  1998** (§5 item 9) as the only unchecked authority for it.
- **STRENGTHENED 2026-07-30 by Kayan 2009.** *Studia Troica* 18 — a later, longer
  and more detailed Kesik paper by the same author — is **equally silent**: no
  wall, no ditch, no Nestor, no *Iliad* line in 24 pages (above). Two Kayan
  papers, both centred on this feature, neither of which contains the
  identification. The absence is now positive evidence, not a gap.
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

**The contradiction, REVISED 2026-07-30 on reading both Springer chapters in full.
Five positions now; the corners have moved, and two of them turn out to be
closer than the dossier had them while a new and worse one has opened.**

| who | what Kesik is | when | sourced to |
|---|---|---|---|
| Kraft, Kayan, Brückner & Rapp **2003a**, 376 (§1.4) | "may be a **defensive trench before a palisade constructed by the Greeks** if proven to be of three millennia or greater age"; and flatly, "**it is certainly a manmade trench as proven by Kayan (1996)**" | LBA, **conditionally** | **Luce 1998** |
| Kraft, Rapp, Kayan & Luce **2003b**, 166 (§1.3) | "The Kesik cut, **a great wall and ditch**… was proposed by Nestor: Il. 7, 336–343", drawn across the ridge neck on both plates | c. 1250 BC, **unconditionally** | **"Kayan 1995" — and the citation FAILS: Kayan 1995, read in full 2026-07-30, contains no wall, no ditch, no Nestor and no *Iliad* fortification (above)** |
| Kayan, Öner, Uncu, Hocaoğlu & Vardar **2003**, 398–401 (§1.5b) | **undecided about origin, decided about use**: "the shape of the Kesik implies that it was dug by man, **there is no information about the purpose and time of construction**"; foot passage, or "**perhaps it is an unfinished canal construction**"; and "**the Kesik 'canal' was never used as a waterway**"; the bay itself unusable by the LBA | unknown | its own drilling |
| Cook **1973**, 166–67 (§1.9) | "an artificial cut… never completed", purpose-guess **drainage**, occasion-guess Constantine's new city | **fourth century AD** | field observation |
| ~~Kayan **2009**, 124 and **2014**, 723–24 (second-hand via Zangger)~~ **REPLACED, first-hand 2026-07-30 — and BOTH are now read: Kayan 2009, 123–24 is the source text 2014 condenses, near-verbatim (above), so this corner is one position, not two** — Kayan **2009**, 123–24 and **2014**, 723–24 (§1.5d.2) | a depression **"naturally formed on a fault line"** on "some evidence", the canal itself "appears artificial" but with "no evidence… that it was dug out" — and **the Holocene sediments explicitly do NOT support Holocene tectonic activity there**, so the fault is **pre-Holocene**; "no evidence to change our former interpretation" | **before the Holocene** (the fault); the canal's own date never established | its own drilling and the ridge/Ballıkaya bedrock morphology |

Five things follow, and none may be smoothed over:

1. **2003a and 2003b hold the same reading and cite different authorities for it.**
   One says Luce 1998, the other says Kayan 1995. Neither cites the other. So "the
   Kesik cut is Nestor's ditch" has **two independent-looking citations and one
   idea**, exactly the manufactured-agreement pattern §6 warns about for the
   "1.2 km". ~~Anyone repeating it must chase **Luce 1998** and **Kayan 1995**
   (§5 items 6, 9), because neither 2003 paper is a source for it.~~ **HALF
   CHASED, 2026-07-30: Kayan 1995 is read, and it does not say it** (above). So
   the idea now rests on **Luce 1998 alone** (§5 item 9) — one unread book behind
   both 2003 chapters, and behind D6's leading reading on the plate.
2. **The worse problem: "as proven by Kayan (1996)".** 2003a asserts over Kayan's
   own signature that the trench is *certainly* man-made, citing a Kayan paper;
   Kayan's own chapter in the same volume, seventeen pages later, says the purpose
   and date are unknown. **One book, two chapters, one co-author, two positions,
   no cross-reference.** Do not cite "Kayan" on the Kesik cut without a year, a
   page and which chapter.
3. ~~**Cook and Kayan-in-2003 are nearer than §1.9 has had them.** … The flat
   "Kayan: natural / Cook: artificial" opposition is a **2009/2014-vs-1973**
   opposition, not a 2003 one. **Kayan's position moved between 2003 and 2009**;
   date every attribution.~~
   **REVISED 2026-07-30 on the Kayan 2014 full text, and the first half survives
   while the second does not.** Cook and Kayan are still nearer than the dossier
   had them — "perhaps it is an unfinished canal construction" (Kayan et al. 2003,
   399), "the work was never completed" (Cook 1973, 167), and now a third echo,
   Kayan 2014, 724 on the modern drainage attempts: "**such attempts could not been
   successfully completed**". Both men still ask the same question about the missing
   spoil, and 2014 asks it again ("**nor has any trace of dumped material been found
   in surrounding fields**", 723). **But "Kayan's position moved" is now retracted.**
   He says in terms that it did not — "In the new stage of our research we have
   obtained no evidence to change our former interpretation" (723) — and what he
   holds in 2014 is 2003's agnosticism with a *pre-Holocene* fault line as the
   preferred hypothesis, plus an explicit denial that his Holocene sediments support
   tectonic activity there. So the opposition is **Cook's artificial-and-unfinished
   vs. Kayan's natural-but-undated**, at every date from 1995 to 2014, and it was
   Zangger's paraphrase — not Kayan — that manufactured the 2003→2009 shift. Date
   every attribution anyway; but the reason is now precision, not a real change of
   mind.
4. **The one thing all five agree on is negative**, and it is the only Kesik
   statement that is safe: the cut's bottom stands well above sea level (13.7 m at
   its saddle, 6.3 m at its inner end — Kayan et al. 2003, 398; "perhaps 12–15 m",
   Cook 1973, 166) and **it was never a waterway**. Kayan et al. 2003, 400 puts it
   in the conclusions: "the low thresholds which separate these bays from the
   Aegean Sea to the west have **never been covered by sea**… the man-made canal or
   ditches on the Yeniköy and Kesik thresholds **were not dug for use as a water
   connection**."
5. **What we may draw. Unchanged.** Nothing at Kesik on a *geographic* plate. If
   Kesik appears at all it is on a **schematic** plate, labelled with whose reading
   it is and dated, at tier `speculative`, with the disagreement stated. A feature
   whose own excavator-adjacent authorities cannot agree whether it is natural,
   Bronze Age military, an unfinished canal or late-Roman civil engineering is not
   map-ready. What the two full texts *do* license is the negative caption: **no
   ship ever passed through it.**

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
20.5 m with a Unimog rig (Kayan 2006, 322–23; Kayan 2014, 703). **Checked
first-hand 2026-07-30 and it holds, but the page cite is short:** the 75 m is at
**703**, the Unimog's 20.50 m and the "318 in 2006" at **706**, and the breakdown
(1–100 Unimog, 101–218 Cobra, +100 at Beşik/Yeniköy) in Fig. 2's caption at **700**
(§1.5d.7). Cite **703, 706 and 700 fig. 2**. Zangger's
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
  now merit reevaluation." ~~**Cite 1980, 782 rather than 1982, 40** — same claim,
  a source we have actually read.~~ **Both are readable now (§1.2); cite whichever
  fits, and see the next block for what 1982 adds.**
- **THE 1982 CHAPTER'S "BESIKA HYPOTHESIS" — the earliest full treatment in this
  lineage, read 2026-07-30 (§1.2, pp. 37–40).** The chapter gives the question its
  own named subsection, twenty years before the 2003 *Geology* paper, and its
  evidence is the **Mey/Dörpfeld/Schede trench**, not new fieldwork: "Mey and
  others excavated a **3 m.-deep trench**… approximately **one km. landward of the
  present shoreline** on the plain at Besika" (37), at "an elevation of **3 to 4
  m. above sea level**" (Fig. 20 caption, 38), yielding over-fired ceramic
  fragments ~1.3 m down and, in the lower sand, abundant *Cerastoderma glaucum*,
  "three large potsherds and a flint flake" that "**were believed by Schede to be
  comparable in age to pottery types excavated from Troy I strata**" (37–38,
  citing Schede 1930, 362). The Besika embayment is reconstructed on the **same
  three dated panels** as the Scamander one — Figs. 15, 17 and 19, i.e. 4500,
  3250 and 2000 BP — and Fig. 15's caption notes "the enlargement of the marine
  embayment at Besika Bay" (33, 38).
  - **The chapter's verdict is conditional and declines to choose**, verbatim
    (40): "Thus, **if one believes the Iliad to be at least semi-factual**, one
    must seriously consider the possibility that the Greek fleet was beached in
    the embayment at Besika, particularly in light of the shoreline adjacent to
    Troy." That is weaker than the flat sentence Zangger's footnote reports —
    a recommendation to take the hypothesis seriously, resting on Besika being
    better sheltered and better watered than the exposed Hellespont side, **not
    on any measurement placing the camp there**. It does not choose between
    Besika and the Scamander/Hellespont side.
  - **Leake's camp calculation is reported, not endorsed** (28–29): Leake "made
    the interesting, **if questionable**, calculation that at least **1.5 mi.² of
    the plain** would have been required to beach the ships of the Achaeans and
    provide camp space for their fifty to one hundred thousand troops." The
    chapter sets it beside Leaf's rebuttal (29–30) and Cook's discussion (30) as
    history of the question. **Never cite the 1.5 mi.² as this chapter's own
    figure**, and note that Leake's "Troja" was at Pınarbaşı, not Hisarlık.
  - **Its mechanism for the raised Besika deposits is eustatic, not tectonic**
    (39): rather than invoking uplift, it appeals to Erol's own Holocene high
    stands (§1.5a, §1.8) — "repeated episodes of slightly higher sea level are
    indicated on the relative sea level curve used in this study (Fig. 4)".
    Compare the 1980 paper's tectonic caveat two years earlier, and Kayan's later
    denial of any Holocene stand above present (§1.8). **Three positions, one
    group; date every attribution.**
  - Authority: **geometry** for the trench data (all of it at second hand from
    Mey 1926, Dörpfeld and Schede 1930); **prose/identification** for the Homeric
    argument, which the chapter itself keeps separable from the geology.
  - **Consequence for §1.11c's caption rule:** the Beşika camp is not a Kraft-1980
    novelty and not a 2003 afterthought — it is the lineage's opening position,
    stated conditionally in 1982 and never chosen between. A plate note saying
    "Kraft 1980: Beşika" is right as far as it goes; "the 1982 chapter declines to
    choose" is the fuller truth.
- ~~**And note where this leaves Kraft.** In 1980 Kraft's camp is Beşika; in 2003a
  (§1.4) it is the Kesik plain.~~ **CORRECTED 2026-07-30, first-hand.** 2003a puts
  the camp nowhere near Kesik: its Fig. 10 (p. 374) labels "Greek Camp and ship
  Station" on the ridge's **Aegean** flank after Luce 1998, and its text ends the
  harbour discussion by agreeing with Luce that "**the Beşik embayment always
  provided a place of shelter for ships**; particularly, those wishing to sail up
  the Dardanelles against its strong currents. Beşik Bay was an important roadstead
  for sailing ships until late in the nineteenth century" (376). **So Kraft does not
  abandon Beşika between 1980 and 2003** — he adds the Luce camp on the outer coast
  and keeps Beşika as a roadstead. The two Krafts are compatible; it was our
  reading of Brückner's paraphrase that made them opposites. A plate note may say
  "Kraft 1980 and 2003a both keep Beşik Bay as shelter" and must still name the
  year for the *camp*, which is 1980 = Beşika, 2003a/b = the ridge's outer flank.
- **Kayan's own Beşik verdict is the deflationary one, first-hand** (Kayan et al.
  2003, 382): the Beşik plain was a small bay by ~6000 BP, then "a coastal barrier
  separated a small lagoon", and the LBA sea-level fall widened the barrier and
  shrank the lagoon — "thus, it can be interpreted that **no Bronze Age natural
  harbour with an open water surface seems to have been possible here** (Kayan
  1991)." So the 1991 paper Zangger quotes for "it is obvious that the Beşik bay
  could have been used as a harbor" is the same paper Kayan cites in 2003 for the
  opposite. **Do not stack Kayan 1991 on the pro-harbour side without reading it**
  (§5 item 10).

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
- **See also §1.5e's rock-cut ditch** at the foot of the Lower City's southern
  slope (Kayan 1997b, 504) — east–west along the slope foot, Troia VI on
  Jablonka's geophysics and Hellenistic in its widening, and shown by drilling
  **not** to have been a water canal. Same quarter of the site, same author of
  the identification, and plausibly the same feature as Jablonka, König & Riehl's
  *Verteidigungsgraben*; this dossier has read neither 1994 paper, so the two
  entries stay separate. **Neither has anything to do with the Kesik cut.**

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
  - **A THIRD conversion, from the same lead author twenty-one years earlier
    (2026-07-30, §1.2).** Kraft, Kayan and Erol 1982, 35–36, verbatim: "Strabo
    notes specific distances; from Troy to the seacoast is given as **12 stadia,
    or about 2.2 km.**, and he estimates the distance to have been half that
    figure at the time of the Trojan War." 2200 ÷ 12 = **~183 m to the stade** —
    nearer the Attic 177.6 m than the 2003 paper's 200 m, and identical to
    neither. So this research group has printed **three** conversions of the same
    ancient figure: 183 m (1982 text), ~181–187 m (2003 figures), 200 m (2003
    text). **"200 m to the stade" is not their settled convention**, and any note
    that treats a metric conversion of Strabo as though it were fixed is wrong
    about the sources as well as about the arithmetic.
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
- ~~`Kraft et al. 2003a` (Springer, §1.4) = Kesik as **harbour**.~~ **STRUCK
  2026-07-30, first-hand (§1.4): 2003a names no harbour at Kesik either.** It puts
  the camp on the ridge's outer flank after Luce 1998, exactly as 2003b does, and
  calls the Kesik cut a possible Greek defensive trench, again after Luce 1998.
  **So "Luce 2003 = Kesik harbour" now has no referent in either 2003 paper.** If
  the claim exists at all it is in **Luce 2003** or **Luce 1998** themselves, and
  both are still unread (§5 item 9). Until one of them is in hand, do not attribute
  a Kesik harbour to Luce.

Do not merge them, do not cite 1984 for a harbour claim, and do not cite either
2003 paper for a harbour site — neither names one.

**And the camp question has an earlier corner than any of these (2026-07-30).**
Kraft, Kayan and Erol **1982, 37–40** devote a named subsection, "The Besika
Hypothesis", to whether the fleet beached at Beşika — the earliest treatment in
this lineage, twenty years before the *Geology* paper — and it **explicitly
declines to choose** between Beşika and the Scamander/Hellespont side, resting on
a conditional ("if one believes the Iliad to be at least semi-factual… one must
seriously consider the possibility", 40). It also reports, without endorsing,
Leake's 1824 calculation that the camp needed at least **1.5 mi.²** of plain.
Both are set out at §1.9. So a plate carrying rival attributed camp zones (D4)
has four positions to date, not three, and the earliest of them is undecided
rather than a placement.

**Luce 2003 itself is still unread, and the volume told us so (2026-07-30).** The
author-shared extract carries chapters 23–25 only; Luce's ch. 2, "The Case for
Historical Significance in Homer's Landmarks at Troia," 9–30, is in the table of
contents and nowhere else (§0). Two pointers gained anyway, both from ch. 24:
Kraft signposts it — "J. V. Luce expands upon Homeric Troia and its ancient
geography and 'locales' **in another chapter of this volume**" (2003a, 376) — and
credits him with the volume's Strabo translation, "We are indebted to J. V. Luce
for his detailed translation as follows" (375), the same translation *Geology*
prints (§1.10). So Luce's 2003 contribution to the Kraft chapters is the philology;
what he argues in his own thirty pages remains §5 item 9's question.

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
| Progradation past the city | Coastline reaches **west of Troia c. 4000 BP** (Kayan 2019); direct sea access lost soon after **2200 BC** on Kayan's scenario, retained much later on Kraft's — on Kraft's own 1980 Fig. 6, Troy VI/VII at 3250 BP still sits **on a promontory at the edge of the estuary**, the water to its west and north-west *(full text, 2026-07-29)*. **The one borehole statement, first-hand 2026-07-30** (Kayan et al. 2003, 392–94): a Neogene bedrock platform ~50 m wide just below present sea level north of the Schliemann trench, its marine cover dated **5800–5200 BP**, above which colluvium with Troia IV, V and VI sherds — "the sea was right at the foot of the 'Schliemann trench' during the earliest periods of Troia, i.e. Troia I and II. **During Troia IV–VI, a strip of dry land formed between the slope and the old Dümrek channel**". That is the **north** side only, and it is coring rather than mapping. **And the primary report of that same coring gives a different period label** (2026-07-30, §1.5b): Kayan 1996, 246–48 says the north-foot surface "first became land about **3500 years ago**", with its deepest sherds dated by the excavation's own archaeologists to "**Troia VI, or more probably VII**". Same stratigraphy, two summaries — **VI/VII in 1996, IV–VI in 2003.** Record both; do not pick. **The WEST side arrives 2026-07-30 with Kayan 2014, 716 fig. 15** — a N–S section at the citadel's western foot with the horizon "**End of delta formation about 3500 years ago**" drawn on it, and the caption "Deltaic shoreline in the Karamenderes valley reached here… towards the end of this period". Kayan's text adds the present figure for scale: the plain now "**presently reach[es] about 4 km northwest of Troia**" (703), and 6–7 m of sediment has accumulated at the citadel's foot "since Troia VI (over the last 3,250 years)" (717) — ~2 mm/yr, the same order as §3.1's independent Strabo-and-DEM estimate | the two scenarios disagree; pick one and name it. **And note that all four of the group's plates keep water against the citadel's WESTERN foot while this borehole clears its NORTHERN one by Troia IV — the two are compatible and the plates should not be read as contradicting the cores** (§1.4a, §1.5b–c) |
| LBA shore, c. 1200 BC | **Two incompatible numbers, and they are in the same paper.** (a) **~1.2 km**: Kraft, Rapp, Kayan & Luce 2003, 166 — "~6 stades (~1200 m) at the time of the *Iliad*", Strabo's 12 stades halved at 200 m to the stade, which the authors say is "well supported by the environmental lithosome distributions and the radiocarbon dates" *(full text, 2026-07-30 — §1.3; the attribution `shore-bronze` prints is CORRECT, with the qualifications there)*. (b) **2.17 km at bearing 334°**: the nearest open water to the Troy dot on that paper's own *Iliad* plate, Fig. 5, measured *(§1.3a)* — with alluvium and marsh drawn between. Same authors, facing pages. Brückner's "ca. 1.2 km" (§1.6) is (a) again, not a second witness. **Kraft, Kayan & Erol 1980 give no citadel-to-water distance at all**, only "Fortification Troy VI and VII lay on a projection or promontory at the edge of a marine embayment" (782), and read Strabo as describing **his own** time (778–79). **Luce 1984 is not a second opinion:** his Fig. 1 is Kraft's line redrawn (33) — no alternative shore to draw (§1.11, §4 item 12). | (a) identification-via-Strabo, **not** survey; (b) geographic-as-drawn, ±~1 km, coordinates unusable (§1.3a) |
| **LBA shore, c. 1200 BC — the two Springer chapters added, 2026-07-30, and they widen the spread rather than closing it** | **(c) ~0.3 km.** Kraft, Kayan, Brückner & Rapp 2003a, **374 fig. 10**, the plate whose caption reads "1250 B.C. ca. the time of the *Iliad*": nearest open water **0.27–0.33 km** from the Troia dot through the whole W–NW–N sector, with the delta lobes prograding north up the middle of the plain and Troia on the bay's eastern shore. Its Scenario-I twin, **373 fig. 9**, gives 0.31–0.41 km on the same base at the same scale *(figure measurement, this dossier — §1.4a)*. **(d) not committed.** Kayan et al. 2003, **397 fig. 7**, draws isochrones at **6000–5500 BP, 5000–4500 BP, 2000 BP and Present and no Late Bronze Age line at all**; its 6000 BP bay laps the citadel at 0.27–0.41 km and its 2000 BP shore is ~3.4 km NW. Its one *borehole* statement on the water's edge at the citadel is that the sea was at the foot of the Schliemann trench in Troia I–II and that "**during Troia IV–VI, a strip of dry land formed between the slope and the old Dümrek channel**" (392–94) — north side only *(§1.5b, §1.5c)*. **So four plates from one research group put the bay at the citadel's foot and disagree only about when it left, and (c) sits a factor of eight from the 2.17 km measured off *Geology* Fig. 5 at (b).** Do not average. If one number must be printed, print the range and name the plate. **(e) STILL not committed, and this was the last chance — Kayan 2014** (§1.5d.3). Its reconstruction map, **718 fig. 16**, is the same sheet as 2003's fig. 7 reprinted: the same four isochrones, **6000–5500 BP · 5000–4500 BP · 2000 B.P. · Present**, and **no Bronze Age line**. Re-measured on the 2014 print, the 6000 BP bay laps the citadel at **0.31–0.33 km through 300°–345°** — reproducing §1.5c's 0.27–0.33 km to within 0.06 km, so the method is sound and the absence is real. His **new** 7000–6000 BP plate, **705 fig. 4**, is closer still: open water **0.19–0.26 km** through 300°–030°. What 2014 *does* commit for the LBA is a **section, not a map**: **716 fig. 15**, a N–S profile at Troia's western foot, carries the labelled horizon "**End of delta formation about 3500 years ago**", with the caption saying the deltaic shoreline "reached here… towards the end of this period". That fixes a **date at a place** — by ~3500 BP the delta front had passed the citadel's western foot — and **no distance may be derived from it** | (c) geographic-as-drawn on a legend-bearing colour plate — the least ambiguous of the four; (d)/(e) **no LBA commitment exists on any Kayan map, in either chapter**, only brackets and one dated section horizon |
| Sea-level change | Local relative fall of **2 m** (Kayan et al. 2003) or **2–3 m** (Kayan 2019) in the LBA — a derivation the sources themselves no longer support as "Kelletat's": the plotted 2003 curve attributes the fall to tectonics and never names Kelletat (see below; the Kelletat attribution survives only in Zangger's report of the older work). Independently and earlier, Kraft, Kayan & Erol 1980's Fig. 6 gives the **endpoints**: **+2 m at 4500 BP → present level at 3250 BP and at 2000 BP**, i.e. a 2 m fall *to* today's datum, from Erol's unpublished curve (ref. 17); the authors call it "valid as a **local, relative,** sea level curve for the Biga Peninsula" (781). The NE Aegean RSL database shows **continuous rise** (Seeliger et al. 2021) *(full text, 2026-07-29)*. **THE PLOTTED CURVE IS NOW IN HAND (2026-07-30): Kayan et al. 2003, 383 fig. 2** ("Middle–Late Holocene relative sea-level changes in the Troia area", after Kayan 1991), with the Troia periods and the labels "Trojan War", "Homer's time" and "Strabo's time" printed on it. Measured: at present level **6000–5100 BP**, falling to a minimum of **−2.0 m at ~3300 BP — the point the "Trojan War" label sits on** — then rising to **about −0.4 m at 2000 BP** and to 0 by ~1300 BP *(figure measurement, this dossier — §1.5a)*. It is a **Beşik-plain record** (80 hand drillings, Kayan 1991), and the chapter attributes the fall to **tectonic movements** ("Bronze Age Regression", Kayan 1997b, at 387) — **not** to Kelletat, who is not named in it. Kraft's chapter states the same curve three more ways: "−1 to −2 m ca. 3500 years ago" (2003a, 361), "−2 m ca. 3400 years ago" (372), "a 2-m sea level drop to ca. 1400 B.C." (373 fig. 9 caption). **CORROBORATED AND DIVERGED 2026-07-30 by Kayan 2014, 709 fig. 8** (§1.5a, §1.5d.1): the same plate, re-measured off a second printing, reproduces to **±0.03 m across 4.3–2.3 ka** — minimum **−1.99 m at 3.28 ka BP**. **But the cause is not what 2003 says it is — and this is a miscitation, not a change of mind (RESOLVED 2026-07-30, §1.5a, §6): "Kayan 1997b" is the Çıplak paper, which argues nothing about causation, while 1997a and 1999 both argue against tectonics in Kayan's own voice.** 2014, 719 says "**tectonic reasons are not convincing explanations for uniform sea-level changes. Thus, an eustatic reason concerning a climatic effect must be taken into account**". And 2014, 707–08 reports the error budget behind it — Dörpfeld's datum is **60 cm** below the national one, GPS and map-derived heights disagree, 20 cm of altitude error "may imply tectonic deformation… but this is not intentional", agricultural levelling shifts points by up to **50 cm** | state as **local/relative**, never regional; state the endpoints, never a bare "fell 2 m"; **a Bronze Age RSL of about −2 m is now quotable from a plotted, published curve measured twice** — with its date (~3300 BP) and its provenance (Beşik). **Do NOT print a cause without a year: tectonic in 2003 (on a citation that fails), eustatic/climatic in 1997a, 1999 and 2014.** And do not quote it to a tenth of a metre — its author reports 0.2–0.6 m of datum and levelling error |
| Barrier | A **wide sandy coastal barrier** closing the remaining water into a shallow lagoon after that fall. The barrier-and-lagoon facies language is **Brückner et al. 2005**; the Kayan et al. 2003 and Kayan 2019 *abstracts* describe the fall and the swamp but do not themselves say "barrier" or "lagoon" (the 2003 full text has since been read — see the SETTLED note below; Kayan 2019's body remains unseen). **Kraft, Kayan & Erol 1980, read in full, has neither word**: its terms are sandy/clay-silt estuary, marsh, swamp, beaches, shoals and brackish–freshwater swamp *(full text, 2026-07-29)*. **DENIED outright by Kraft, Rapp, Kayan & Luce 2003, 164, citing their own 1980 paper: littoral currents sorted sands into "nearshore shoals and possibly thin beaches, although no barrier lineaments are evident on the lower Scamander delta"** *(full text, 2026-07-30 — §1.3b)*. Independently, Strabo 13.1.31 describes a **blind (barred) river mouth with salt lakes and marshes**. **SETTLED 2026-07-30, and against our layer: the Kayan full text was seen, and the barrier is at BEŞIK.** Kayan et al. 2003, 382: the Beşik plain "formed as a small bay about 6000 years ago. **Afterwards, a coastal barrier separated a small lagoon**… A small sea-level fall in the Late Bronze Age may have caused **widening of the coastal barrier and reduced the lagoon**." Kraft et al. 2003a, 372, of the same place: Beşik "evolving to a **barrier-lagoon**". On the Karamenderes, Kayan denies it in one sentence (390, of the transition zone that caps the marine unit under almost the whole plain): "**There is no beach or lagoon formation. Instead, sediments indicate swampy or seasonally wet environments.**" And Kraft et al. 2003a, 364: "**Coast-parallel lineaments occur only in the lower 2 km of the Scamander floodplain. Barrier accretion ridges do occur on the Beşik coastal plain**" — 2003b's flat denial (164) in a more exact form. **On the plates:** Kayan's Fig. 9 (2003a, 373) draws the "Sand Dunes and Coastal Barriers" symbol only at Beşika ("1500 BC") and Kum Kale; Kraft's Fig. 10 (374) draws one on the Scamander front too — **dated 2000 BP, ~2.5–3.0 km NNW of Troia**, on the "2000 BC/AD" shoreline — plus Besika's, there labelled "1280 BC" *(figure measurement, this dossier — §1.4a)*. **CONFIRMED AND DATED 2026-07-30 by Kayan 2014** (§1.5d.4): the Karamenderes denial is repeated word for word at **712** ("There is no beach or lagoon formation. Instead, sediments indicate swampy or seasonally wet environments"), and **no Scamander-front barrier appears in the chapter's text or on any of its twenty figures at any date**. At Beşik the barrier is now **dated**: "**around the period of Troia VI, a coastal barrier separated a small lagoon**", and the LBA fall "caused widening of the coastal barrier and reduced the lagoon" (704). It is also **drawn twice**, in section (**707 fig. 6**, barrier phases H1–5, ¹⁴C at 8000/6700/5200/4500/3500 BP) and in plan (**708 fig. 7**), both carrying dated shoreline positions **① 6000 BP · ② 3500 BP · ③ 2000 BP · ④ Present** — and at ② the shore is on the barrier's **seaward** flank with the shrunken lagoon behind it | **NOT drawing-ready as a Bronze Age Scamander-front feature, and now for a positive reason rather than an absence: every source that draws a Bronze Age barrier draws it at BEŞIK BAY, and the only Scamander-front barrier anyone draws is Roman-period.** `barrier-bronze` must be demoted or moved (§3.3). **At Beşik, by contrast, the barrier-and-lagoon is now geometry with dates on it and could be drawn** (§1.5d.4) |
| Lagoon | Shallow, behind the barrier; ancient name **Stomalimne** attested between Sigeium and the Scamander mouths (Strabo 13.1.31). **Same correction as the barrier row (2026-07-30): the located, dated lagoon in this literature is Beşik's** (Kayan et al. 2003, 382; Kraft et al. 2003a, 372); on the Karamenderes plain Kayan states there is "no beach or lagoon formation" (390) and the lagoons in Kraft's vocabulary stay a facies class, unlocated (§1.3b). Kraft's own pre-modern base map does label one — "**Salt Lagoon**", on the Dardanelles shore by Intepe/Rhoiteion (2003a, 365 fig. 2, after Spratt 1839) — i.e. an *asmak* on the strait, not a bay-mouth lagoon west of Troy | geographic + identification, **but the geography is Beşik's and the Dardanelles shore's, not the Trojan plain's** |
| Swamp / marsh | The area west of the city was a **broad deltaic swamp** in Troia IV–VI; the land was **swamp-covered throughout the progradation period**, and the coastal sea **very shallow** (Kayan et al. 2003). Corroborated first-hand: Kraft's Fig. 2 maps modern swamp over the Kesik/Yeniköy plain and the Scamander's western and south-western flanks, and the text allows that "low-lying swamps occurred around the base of Troy" at 3250 BP — with the honest rider "although further drilling would be required to verify this" (1980, 782) *(full text, 2026-07-29)* | geographic, extent approximate |
| Kesik cut | **400 × 50 × 30 m** (Kayan's/Zangger's figures, never Cook's), floor **13.7 m a.s.l.**, ~150 m from the sea, 2–2.5 m of colluvium on the floor. **Contested origin, corrected 2026-07-30 — the two authorities disagree and must not be blended:** ~~Kayan reads a natural **tectonic depression** widened by foot traffic (Kayan 2009, 124; 2014, 723–24)~~ **— rewritten first-hand the same day (§1.5d.2): Kayan reads a canal that "appears artificial" but shows "no evidence… that it was dug out", on a depression "naturally formed on a fault line" that is *pre-Holocene*, because "sedimentological and stratigraphical features of the Holocene deposits… do not support such tectonic activity for the Holocene"; he adds "no evidence to change our former interpretation" and never says foot traffic widened it (2014, 723–24)**; Cook independently calls it "an artificial cut… never completed", floor "perhaps 12–15 m a.s.l." (brackets Kayan's 13.7 m), his own guess **drainage, late-Roman** (Constantine's new city) (Cook 1973, 166–67; `RESEARCH-TROAD-TOPOGRAPHY.md` §9.2). A tectonic depression cannot be "unfinished" — rival origin theories, not compatible attributes. **Cook is never citable for Bronze Age harbour engineering.** **Fourth reading added 2026-07-30, first-hand: Kraft, Rapp, Kayan & Luce 2003, 166 make the cut "a great wall and ditch (Kayan, 1995)… proposed by Nestor", i.e. the Achaean fortification of *Il.* 7.336–43** — **and that citation FAILS (2026-07-30): Kayan 1995, read in full, contains no wall, ditch, Nestor or *Iliad* fortification, so the reading rests on Luce 1998 alone** (§1.9) — a Late Bronze Age military work on the same ground where Cook puts an unfinished late-Roman drainage trench. Drawn on Figs. 4 **and** 5 as a hatched band ~5.35 km due west of the Troy dot, ~0.6 × 0.33 km as symbolised (≈1.5× and ≈6× the surveyed cut) — §1.9, §1.3a. **REVISED 2026-07-30 from Kayan's own printed measurements** (Kayan et al. 2003, 398): the **13.7 m is the HIGHEST point of the cut's bottom**, at ~150 m from the sea; the bottom then falls to **6.3 m about 400 m east of that saddle**, where it opens on the Kesik plain — so "400 m" is the saddle-to-plain distance, not a length, and the ridge there is "only about 600 m wide" at "a little more than 20 m at the top". Colluvium on the bottom is **2 m**, and "**no archaeological material was encountered** in the many drillings which were made in the bottom of the cut". **The 400 × 50 × 30 m triple is Zangger's, not Kayan's** — this chapter prints no width and no depth. **Fourth and fifth readings, first-hand:** 2003a, 376 makes it "a defensive trench before a palisade constructed by the Greeks… certainly a manmade trench as proven by Kayan (1996)", after **Luce 1998**, while Kayan's own chapter in the same volume leaves purpose and date unknown and floats "an unfinished canal construction" (399) — §1.9's revised table. **Kayan 2014, 723 adds one figure 2003 lacked** — the mid-cut bedrock threshold "at a height of **about 13 m** above sea level", his own rounding of the 13.7 m — **and still prints no width and no depth**, so the 400 × 50 × 30 m triple remains Zangger's in both chapters | geographic; **not** a harbour entrance; **five identifications across two chapters of one book plus Cook and the later Kayan; the only shared positive is that no ship ever passed through it** |
| Kesik plain | Basin area "about 1 km²" (Kayan 2009, first-hand — **no linear plain-width figure exists in Kayan's own text**; the once-repeated "~800 m" is the **Yeniköy ridge's** width, 800–1000 m at 2009, 110, and the "before 1300 BC" date traces only to Zangger via Kayan 2001, 313, unread — §1.9); **"could not have been used as harbours during the Later Bronze Age, especially during Troia VI"** (Kayan et al. 2003, **400–401**, first-hand 2026-07-30 — the sentence crosses the page break and the old "400" cite was short). Its own siltation dates are **3400 / 4200 / 4500 BP** on Fig. 6's Kesik section (396), rounded in the text to "marine conditions continued up to 3500 years ago" (398) and "changed into land… about 4000 years ago" (400); Zangger's "before 1300 BC" is later than anything the chapter prints. ~~Against Kraft et al. 2003a's choice of it as the harbour~~ — **that choice was Brückner's paraphrase, not 2003a's sentence** (§1.4): 2003a says only that all three western embayments "had excellent harbor potentials" and names none. Kraft et al. **2003b** likewise proposes no harbour at Kesik (§1.3b). **= the Lisgar marsh = Ilıca** (Cook 1973, 166; one basin, three names — §1.9). **Kayan 2014, 724 gives the Bronze Age verdict in one sentence and on environmental grounds:** "During this period [Troia VI/VIIa] the Kesik depression was **not a marine embayment; instead, it was covered by a swamp. Therefore, a harbor is not a subject of discussion for the Kesik depression** and a canal was not necessary for a waterway connection with the Aegean Sea. In fact, there is **no archaeological evidence later than the Chalcolithic period** in this area." Still no 800 m width and no "before 1300 BC" in Kayan's own text | contested identification; **cite the letter, a or b — and do not cite either 2003 chapter for a Kesik harbour** |
| Beşik Bay | The project's original harbour candidate, stated first-hand in **Kraft, Kayan & Erol 1980, 782** ("the Beşika embayment was indeed the site of the Achaean camp"; "an indentation approximately **2 km inland**" at 4000–5000 BP) and again at Kraft et al. 1982, 40 and Kayan 1991, 91. **Rejected by Luce 1984, 40–41** on three stated grounds: too exposed to the Aegean for a permanent ship station; **8½ km from Troy against 4 to 5 km for his Sigeum ridge site**; and bad access to the Scamander plain, "first across a low ridge and then across a wide expanse of low-lying and marshy ground". He adds that Mey's 1924 trenches there found "nothing to confirm his Achaean camp hypothesis" (40). Cook 1973, 171–72 is on the *other* side ("a very much more satisfactory situation for the Homerists") and Luce says so and disagrees *(full texts: Kraft 2026-07-29 — cite 1980, not the second-hand 1982 quotation; Luce 2026-07-30 — the objections are now first-hand and one of them is a measurement)*. **Kayan 2014 rejects it on his own ground and now draws why** (§1.5d.4): the barrier separated the lagoon "**around the period of Troia VI**" and the LBA fall widened it, so "**no Bronze Age natural harbour with an open water surface seems to have been possible here**" (704); Figs. 6 and 7 (707–08) plot the barrier, the lagoon and four dated shorelines, with **3500 BP on the barrier's seaward flank**. **Kayan 2014 contains no camp claim at all** — the word does not occur — so it may not be cited for the Achaean camp in either direction | contested identification |
| Harbour, in general | Kayan et al. 2003: the environment "has never been suitable for the establishment of an important harbour". **Narrowed, first-hand 2026-07-30 (§1.9): the denial is of *principal* and *big* harbours, and the same conclusions concede the ordinary case** — "**Suitable places on the changing shoreline could have been used according to necessity as natural harbours during the various periods of Troia culture**" (401), before the flattest line in the literature: "**Therefore, we suggest there is no reason to create great harbour theories relating to Troia**" (401). Kraft et al. 2003a, 376 is compatible in that register, not opposed to it: all three western embayments "had excellent harbor potentials", the southernmost already bypassed "before Late Bronze Age times", and Beşik "always provided a place of shelter for ships". **And the paper titled "Harbor areas at ancient Troy" names no harbour area:** its positive claim is that river-sand redistribution "was limited by the very low wave activity in this **long-term sheltered marine embayment**" (Kraft, Rapp, Kayan & Luce 2003, 164) — the shelter is the bay, which is Luce 1984's position in geologists' words *(full text, 2026-07-30 — §1.3b, §1.11c)*. **AND KAYAN'S LAST WORD IS AFFIRMATIVE, first-hand 2026-07-30 (§1.5d.6).** Kayan 2014, 720 opens the harbour section: "**Since the Karamenderes plain was a long bay for several millennia after 7,000 years ago, Troia must have had a harbour or harbours in different places following changes of coastline positions during deltaic progradation. An important question then arises as to where the Troia harbours were.**" He then dismantles Yeniköy, Kesik and Kumtepe in turn (721–25) and **never answers his own question**. With 2003's concession that ordinary beaching places "could have been used according to necessity" (401), the settled position is **harbours yes, harbour *works* no, location unknown** | prose; the strongest deflationary claim in the literature is about *installations*, and it is **not** a denial that Troy had harbours — Kayan 2014, 720 says the opposite in his own voice. The title of the "harbour paper" is not evidence against it either |
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
lines are at different longitudes — ~~but it wants checking against Kayan 2014
fig. 8 when that is in hand.~~ **CHECKED 2026-07-30, and fig. 8 cannot answer it:
Kayan 2014, 709 fig. 8 is the sea-level curve, not a map** (§1.5d.1). The 2014
chapter's own maps decide the row a different way — its reconstruction sheet
(718 fig. 16) is 2003's fig. 7 reprinted and draws no Scamander barrier at any
date, and 712 repeats the Karamenderes denial verbatim. **The layer's problem was
never its vertical placement; it is that no source puts a barrier on this delta in
the Bronze Age at all.** See the verdict below.

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

**RESOLVED 2026-07-30 — the Kayan full text and figure arrived, and they decide
against the layer. This is a verdict, not another escalation.**

The barrier row had been waiting on Kayan et al. 2003 to say whether "barrier" and
"lagoon" are the group's own words for the Trojan plain or Brückner's gloss. They
are the group's own words, and they belong to **a different bay**. Four
independent statements, three of them first-hand today:

1. **Kayan et al. 2003, 382 — the barrier and lagoon are Beşik's**, formed after
   ~6000 BP, and it is the Late Bronze Age sea-level fall that *widens the barrier
   and shrinks the lagoon* there. The whole barrier-lagoon story our layer tells is
   in this sentence, at the wrong bay.
2. **Kayan et al. 2003, 390 — the Karamenderes is denied outright:** "There is no
   beach or lagoon formation. Instead, sediments indicate swampy or seasonally wet
   environments." Said of the transition zone that caps the marine unit "generally
   2 m below the present sea level under almost the whole surface of the present
   plain" — i.e. of exactly the horizon and exactly the ground our barrier crosses.
3. **Kraft et al. 2003a, 364 and 372** — barrier accretion ridges "do occur on the
   Beşik coastal plain"; coast-parallel lineaments on the Scamander floodplain
   "occur only in the lower 2 km"; Beşik "evolving to a barrier-lagoon". Plus
   2003b, 164's flat "no barrier lineaments are evident on the lower Scamander
   delta" (§1.3b).
4. **The plates agree with the prose** (§1.4a). Kayan's Fig. 9 puts the
   "Sand Dunes and Coastal Barriers" symbol only at Besika ("1500 BC") and Kum
   Kale. Kraft's Fig. 10 puts one on the Scamander front as well — **on the
   "2000 BC/AD" shoreline, 2.5–3.0 km NNW of Troia, i.e. Strabo's day, not the
   Bronze Age**.

**Verdict.** There is no live conflict left to adjudicate: 2003b's denial and
Kayan's full text point the same way, and the apparent disagreement with Brückner
2005 dissolves once the bay is named. `barrier-bronze` as drawn — a Bronze Age
sandy barrier closing the Trojan bay — **is not supported by any source in this
dossier and is contradicted by three.** Three honest options, in order of
preference:

- **Delete it** from the geographic register of `trojan-plain.json`. Nothing on the
  sheet depends on it, and its "2 to 2.5 m" provenance never resolved either
  (§1.5a: the published numbers are −1 to −2 m, −2 m, and a plotted minimum of
  −2.0 m at ~3300 BP; 2–3 m in Kayan 2019; **never 2–2.5**).
- **Or re-date it to c. 0 BC/AD** and caption it as Kraft's Strabo-time sandy
  coastline (2003a, 374 fig. 10), which is a real published feature at a real
  published date — but it then belongs on a Roman-period plate, not the Bronze Age
  one, and it is a *symbol* on a Spratt-derived base, so §1.3a's "never lift a
  coordinate" applies.
- **Or move it to Beşik Bay**, where the sources put a Bronze Age barrier and
  lagoon and where they also say the result was that **no harbour was possible**.
  Drawing it there means drawing what it was for. **Upgraded from "possible" to
  "supported by drawn, dated geometry", 2026-07-30:** Kayan 2014, 704 dates the
  barrier's formation to "**around the period of Troia VI**", and 707–08 figs. 6
  and 7 plot the barrier, the lagoon, the dune field and the lagoonal channel in
  section and in plan with **four dated shoreline positions (6000 / 3500 / 2000 BP /
  Present)** on both — the **3500 BP** shore lying on the barrier's seaward flank
  (§1.5d.4). That is the only Bronze Age barrier-and-lagoon in this literature for
  which we now hold a dated drawing, and it is at Beşik. It remains **copyrighted
  expression that may not be traced** (§0); what may be re-expressed is the
  arrangement and the dates.

**A fifth strike, added 2026-07-30.** Kayan 2014 repeats the Karamenderes denial in
the same words at **712** and draws no Scamander-front barrier on any of its twenty
figures. That is **four independent statements plus a reprint**, across three
publications and two authors, against a Bronze Age barrier on this delta. The
question is closed; only the disposition of `barrier-bronze` is open.

What may **not** happen is the layer staying where it is with a citation to Kayan
or to Brückner. Both authors are now on record about which bay this is.

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

### 3.7a How the two Springer chapters' colour plates were measured

Different problem, easier method, and it is worth saying why: **these plates are
colour, with a printed legend (§1.4a), so "is this pixel sea?" is answered by a
colour class rather than by a flood fill that can leak through a hairline.** No
seed, no leak test, no polarity trap. Poppler and Pillow only.

1. `pdftoppm -r 500 -png` on
   `research-cache/troia-troad-2003-kayan-chapters.pdf`, one page at a time
   (PDF p. 42 = Kraft Fig. 9 / printed 373; p. 43 = Fig. 10 / 374; p. 65 = Kayan
   Fig. 7 / 397; p. 51 at 300 dpi = Kayan Fig. 2 / 383).
2. **Scale** from each plate's own bar, found by scanning for the longest
   horizontal dark run inside the frame. Kraft Figs. 9 and 10: 0–1–2 km with ticks
   at x = 790/965/1140 and 680/855/1030 ⇒ **175 px/km on both** (so the two plates
   are the same base at the same scale, and a difference between them is a claim).
   Kayan Fig. 7: 0–3 km bar spanning x = 426→868 ⇒ **147.3 px/km**.
3. **Anchors.** The Troia archaeological-site dot, read off ×4 nearest-neighbour
   crops with a labelled pixel grid: (1655, 1690) on Fig. 9, (1650, 1670) on
   Fig. 10, (2065, 1432) on Fig. 7.
4. **Classes.** Sea on Kraft's plates = pale blue, `B > R + 30 ∧ B > 140 ∧ G > R`.
   Bay on Kayan's Fig. 7 = the legend swatch "Troia and Beşik bays 6000 BP",
   sampled at (480–510, 820–850) as RGB ≈ (85, 166, 70), matched within Euclidean
   distance 55. "Sand Dunes and Coastal Barriers" = `R > 200 ∧ G > 190 ∧ B < 110`.
   **Sample the legend swatch, never a guess** — the maps are halftone screens and
   eyeballed hex values will not match.
5. **Radial profile** at 15° steps from the Troia dot, first hit requiring a
   *blob* (≥110 class pixels in a 13×13 window for Kraft's plates, ≥25 in 7×7 for
   Kayan's) so that a label's letterform or a hairline river cannot register as
   coast. Bearings are map-north; all three sheets are north-up with a north arrow.
6. **The sea-level curve (Fig. 2, p. 383)** is a different measurement again: the
   metre scale comes from the alternating black/white segments of the left axis
   bar at x ≈ 292–299, which run 489/575/661/748/834/922/1009/1098 ⇒ **86.7 px per
   metre with 0 m at y = 748**; the time scale from the tick digits on the zero
   line at x = 325/505/685/865/1042/1220/1400/1578 ⇒ **178.9 px per 1000 yr, 0 ka
   at x = 1578**. The curve is then the topmost dark pixel below the zero line at
   each x. Two artefacts to ignore: the "RELATIVELY CHANGING SEA LEVEL" lettering
   crosses the curve near 5.3 ka, and the left axis bar reads as a false zero at
   6.98 ka.
7. **Same rule as §3.7: distance-and-bearing from the citadel only.** These sheets
   carry no graticule at all, so the temptation does not even arise — but they are
   redrawn from the same Spratt-derived base as the *Geology* plates (Fig. 2,
   p. 365, is Spratt 1839 explicitly), which is the base §1.3a showed to be
   internally inconsistent at the 10–20% level. **Treat every number in §1.4a and
   §1.5c as ±10%.**

### 3.7b How the Kayan 2014 figures were measured

Same tools, same discipline; the differences are worth recording because two of them
bit, and because §1.5d's whole claim to corroborate §1.5a rests on this being an
**independent** measurement of a **second printing**, not a copy of the first.

1. `pdftoppm -r 600 -png` on `research-cache/kayan-2014-troia-geoarchaeology.pdf`
   for the two load-bearing plates (**PDF p. 21 = printed 709, fig. 8**; **PDF p. 30
   = printed 718, fig. 16**), 400 dpi for the rest. **Page arithmetic: printed = PDF
   page + 688**, because PDF pp. 1–5 are the volume's front matter (§0).
2. **Fig. 8, the curve.** Metre scale from the alternating black/white segments of
   the left axis bar at x ≈ 290: boundaries at y = 725, 909, 1104, 1287, 1485, 1668
   for +2 … −3 m ⇒ **188.6 px per metre, 0 m at y = 1100**. Time scale from the eight
   tick marks on the zero line at x = 366, 750, 1134, 1519, 1903, 2292, 2677, 3064
   for 7 … 0 ka ⇒ **385.4 px per 1000 yr, 0 ka at x = 3064**. The curve is the top of
   the grey fill (RGB ≈ 162 grey): walk **upward from y = 1700**, not from the frame,
   allowing an 80 px gap so the white "RELATIVELY CHANGING SEA LEVEL" lettering does
   not truncate the trace.
   - **Trap 1: the fill ends at y ≈ 1720, not at the frame.** Seeding the walk at
     y = 1860 returns the *baseline* and yields a flat −4.03 m everywhere. If a
     column reports the same value as its neighbours to two decimals, the walk has
     hit the floor.
   - **Trap 2: the axis numerals 7 … 1 sit above the zero line** and register as
     "curve" wherever the curve is near 0. On the recovery limb, scan **downward
     from y = 1105** (just below the line) instead; the columns at 2.0, 1.0 and
     0.5 ka still return the zero line itself and must be discarded, not read as
     "sea level reached present".
   - **Trap 3, and it is an interpretive one: the plate carries two time axes.** The
     cultural bar's ticks read 3, 2, 1, 0 in **thousand years BC/AD**, registered
     2000 years off the main BP axis (§1.5d.1). Do not read "Troian War" against the
     lower scale.
3. **Fig. 16, the map.** Scale from its own 0–3 km bar, ends at x = 2654 and 3032 ⇒
   **126.0 px/km** (the 2003 print of the same sheet gave 147.3 px/km at 500 dpi, so
   the 2014 printing is ~0.71× — a reminder that a px/km constant is a property of a
   *printing*, never of a plate). Troia dot centre at (4737.5, 3441) off a ×2 crop
   with a labelled grid.
   - **Sample the legend swatch, and sample it on a single row.** A 12 × 12 mean over
     a swatch pulls in the hatch border and shifts the colour: "flood plains about
     6000 BP" reads (111, 199, 53) that way and **(113, 200, 52)** on a clean row;
     "Troia and Beşik bays 6000 BP" is **(13, 170, 82)**.
   - **The map has five greens and the legend names two.** A colour census of the map
     area returns (13,170,82), (50,158,62), (57,183,61), (74,191,121) and
     (113,200,52). The intermediate three are unlabelled delta stages. **Only the two
     legend colours may be reported as classes**; a first-hit on (57,183,61)
     immediately west of the citadel is *not* the 6000 BP bay and reporting it as one
     would have put the shore 0.15 km further out than it is.
   - Radial first-hit at 15° steps, requiring ≥20 of the next 30 pixels along the ray
     to stay in class, so a swamp glyph or a label serif cannot register.
4. **Fig. 4, the new 7000–6000 BP plate.** Sea is a single flat blue **(24, 170,
   232)**, so the class test is trivial; scale bar 1152→1648 px at 400 dpi ⇒
   **165.3 px/km**; Troia dot at (2377.7, 2378.7).
   - **Flood-fill caveat, and it fired here.** A 4-connected fill seeded west of the
     citadel does **not** reach the Aegean or the strait: the black coastline stroke
     and the dark-blue "MIDDLE HOLOCENE MARINE EMBAYMENT" lettering laid over the
     water both close the region. Its bbox is therefore a **lower bound** on the
     embayment, and the 3.2–3.8 km bay-head figure in §1.5d.5 is a **ray
     measurement** (last in-class pixel along a bearing), not a fill extent. Do not
     quote a fill bbox off this sheet.
5. **Same rule as §3.7 and §3.7a: distance-and-bearing from the citadel only**, and
   the same ±10% (Fig. 16 is the same Spratt-derived base). One calibration this
   acquisition buys: **Fig. 4 and Fig. 16, two plates of the same mid-Holocene bay by
   the same author in the same chapter, disagree by ~0.1 km** on the water's distance
   from the citadel. That is the internal noise floor of these sheets, measured
   rather than assumed.

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
   about 2 m (Kayan et al. 2003; Kayan 2014, 704 and 719) or 2–3 m (Kayan 2019).
   And the fall must be labelled **local/relative**, because the NE Aegean RSL
   database shows continuous rise (§1.8). *(Added 2026-07-30: if any note names a
   **cause** for the fall, it must name a **year** — Kayan 2003, 387 says tectonic;
   Kayan 2014, 719 says the tectonic reading "is not convincing" and reaches for
   eustasy and climate. §1.5a, §6.)*
3. Same file, sources array: the "Troian Bay" chapter is by **Kayan, Öner, Uncu,
   Hocaoğlu and Vardar**, pp. 379–401 — currently cited as sole-author, no pages.
   *(And if Kayan 2014 is cited anywhere, the imprint is **Bonn: Habelt**, the
   volume's *Teil 2*, ISBN 978-3-7749-3902-8 — §1.5d.)*
3a. **Any plate note or caption anywhere that reads "Kayan: Kesik is a tectonic
   depression".** New, 2026-07-30. It inverts him: Kayan 2014, 723 says his own
   Holocene deposits "**do not support such tectonic activity for the Holocene**"
   and puts the fault line **before** the Holocene, while calling the canal itself
   "appears artificial" with "no evidence… that it was dug out". The phrase
   "widened by foot traffic" is Zangger's, not Kayan's. **Checked 2026-07-30:
   `apparatus/plates/` and `docs/TROAD-SOURCES.md` contain no occurrence of
   "tectonic" today, so this is a rule for the next draft rather than a repair
   owed** (§1.5d.2, §1.9).
3b. `docs/TROY-MAPS-TODO.md:50` lists "Kayan 2014 (Studia Troica Mon. 5, fig. 8)"
   as a **lower-priority** pull. It has been pulled and read (§1.5d); the line
   should be closed. Fig. 8 is indeed the sea-level curve, and it corroborates the
   2003 plate rather than replacing it — so "lower priority" was the right call and
   the entry can be marked done rather than escalated.
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

New, from the two *Troia and the Troad* chapters read in full (2026-07-30). **These
five are the most consequential in this section: two of them ask for a layer to be
withdrawn, and three retract attributions this dossier itself supplied.**

15. `apparatus/plates/trojan-plain.json`, `barrier-bronze`: **withdraw it from the
    geographic register.** A Bronze Age sandy barrier across the Trojan bay is
    supported by no source in this dossier and contradicted by three — Kayan et al.
    2003, 390 ("There is no beach or lagoon formation") of exactly that horizon;
    Kraft et al. 2003a, 364 (barrier accretion ridges are at Beşik, coast-parallel
    lineaments only in the Scamander's lowest 2 km); Kraft et al. 2003b, 164 ("no
    barrier lineaments are evident on the lower Scamander delta"). Every Bronze Age
    barrier-and-lagoon in this literature is at **Beşik Bay** (Kayan et al. 2003,
    384; Kraft et al. 2003a, 372), and the only Scamander-front barrier anyone draws
    is on the **2000 BP** shoreline (Kraft et al. 2003a, 374 fig. 10). Delete,
    re-date to c. 0 BC/AD, or move to Beşik — the three options at §3.3. Item 2
    above (the "2 to 2.5 m") becomes moot if the layer goes.
16. Same file, and anywhere else the phrase has travelled: **"where Kraft et al.
    2003a put the harbour at Kesik" must come out.** The chapter says all three
    western embayments "had excellent harbor potentials" and names none (2003a,
    376). The Kesik attribution is **Brückner et al. 2005 §21's own sentence**
    (§1.6), not a report of the chapter. Re-cite it to Brückner or drop it. Item 10
    above is superseded in its second half for the same reason: Kraft did **not**
    move from Beşika to Kesik — 2003a, 376 still calls Beşik a place of shelter, and
    its camp is on the ridge's Aegean flank after Luce 1998.
17. Same file, any Kesik note: the geometry needs three repairs from Kayan's own
    page (Kayan et al. 2003, 398). **13.7 m is the highest point of the cut's
    bottom**, ~150 m from the sea, not "the floor"; the bottom falls to **6.3 m
    about 400 m east** of that saddle, so the "400 m" is not a length; the colluvium
    is **2 m**. The **400 × 50 × 30 m** triple is Zangger's summary — this chapter
    prints no width and no depth. Add, because it is the strongest negative
    available: "**no archaeological material was encountered** in the many drillings
    which were made in the bottom of the cut."
18. Same file, the sea-level note: a **plotted, dated, period-labelled** curve now
    exists and may be cited — Kayan et al. 2003, 383 fig. 2, minimum about **−2 m at
    ~3300 BP**, with "Trojan War" printed on that minimum. It **disagrees** with
    Kraft, Kayan & Erol 1980 fig. 6 (present level at 3250 BP, +2 m at 4500 BP) by
    about 2 m and 4 m at those dates. A note that states one must name whose it is;
    a note that states a bare "the sea fell 2 m" states neither. Both are **local
    and relative**, and Kayan's cause is **tectonic** (2003, 387), not eustatic.
19. `docs/TROAD-SOURCES.md` and any place record for Kesik: **no Kesik feature may
    carry a Bronze Age date.** Both 2003 Kraft chapters call the cut the Greek wall
    and ditch — one conditionally ("if proven to be of three millennia or greater
    age", 2003a, 376), one flatly (2003b, 166) — on two different authorities
    (Luce 1998; Kayan 1995), neither of which we have read. Kayan's own chapter in
    the same volume says "there is no information about the purpose and time of
    construction" (399). The one claim all five readings license is negative and
    should be the caption: **it was never a waterway** (Kayan et al. 2003, 399–400).

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

1. **✅ OBTAINED 2026-07-30 — Kraft, Kayan & Erol 1982**, "Geology and
   Paleogeographic Reconstructions of the Vicinity of Troy," in *Troy: The
   Archaeological Geology*, ed. Rapp & Gifford (Princeton), **11–41**. Chapter
   scan cached at `research-cache/kayan-1982-rapp-gifford-geology-ch.pdf`; read in
   full, extraction note at `research-cache/kayan-1982-notes.md` (§1.2).
   **Settled:** the chapter's identity and page range, against the catalogue drift
   the 1980 paper's ref. 20 introduced; the five dated panels and what each rests
   on; the inland reach in the group's own earliest words (15–16 km); **Erol's
   separate sea-level curve**, which must never be conflated with Kayan's (§1.5a);
   a **third** stade conversion, ~183 m (§1.10); the Besika hypothesis at its
   origin, with Mey's trench, Schede's Troy I sherds and Leake's 1.5 mi.²
   calculation (§1.9, §1.11c); and Kesik's **absence** from the chapter entirely.
   **Did NOT settle — and this is the pull's disappointment: the core logs are not
   in it.** The chapter prints four interpretive cross-sections (Figs. 7–10), not
   depth-by-depth logs; if tabulated logs exist they are in the volume's
   appendices (pp. 141–197), which are outside the cached extract. Also not
   settled: any measurement off its plates — nothing here was measured at print
   resolution, and the OCR garbles Turkish diacritics throughout.
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
3. **✅ OBTAINED 2026-07-30 — Kraft, Kayan, Brückner & Rapp 2003 (= 2003a)**,
   "Sedimentary Facies Patterns and the Interpretation of Paleogeographies of
   Ancient Troia," in *Troia and the Troad*, **361–77**. Author-shared extract
   cached at `research-cache/troia-troad-2003-kayan-chapters.pdf` (İlhan Kayan's
   academia.edu copy, 70 pp.); text and all ten figures read, the two Troad plates
   measured (§1.4, §1.4a, §3.7a). Entry kept so the ledger shows what a pull buys.
   **Settled:** Scenario I and Scenario II as *drawn* — Fig. 9 (p. 373, Kayan's,
   with shorelines at 3500–4000 BC, 2500–3000 BC, 500–1000 BC and a Besika barrier
   at 1500 BC) and Fig. 10 (p. 374, Kraft's own, captioned "1250 B.C. ca. the time
   of the *Iliad*", with 3000–3500 BC, 1250 BC and 2000 BC/AD shorelines, the
   Kesik cut, the Greek camp after Luce 1998, and eleven ¹⁴C points); the
   "Nothing in our research negates the writings of Homer!" line **confirmed at
   p. 375** exactly as Brückner reports it; the Strabo apparatus in Luce's
   translation at pp. 375–76 **without any metric conversion**, which localises
   the "~1200 m" wholly to 2003b; the printed legend (p. 365) that makes the
   colour plates readable. **Settled against expectation, twice:** (a) **this
   chapter does not make the Kesik plain the harbour** — that was Brückner's 2005
   paraphrase; its own sentence endorses Zangger's three embayments as having "had
   excellent harbor potentials" and names none (§1.4); (b) its Kesik cut is
   **the Greek defensive trench after Luce 1998**, "certainly a manmade trench as
   proven by Kayan (1996)" — the same reading as 2003b but on a different
   authority, and asserted over Kayan's signature against Kayan's own chapter
   seventeen pages later (§1.9). **Did NOT settle:** any coordinate (same
   Spratt-derived base, §3.7a); the Kesik cut's date, which it makes conditional
   ("if proven to be of three millennia or greater age"); what **Luce 1998** and
   **Kayan 1995/1996** actually say, which both 2003 chapters now depend on.
4. **✅ OBTAINED 2026-07-30 — Kayan, Öner, Uncu, Hocaoğlu & Vardar 2003**, same
   volume, **379–401**, in the same cached extract; text and all seven figures read
   and measured (§1.5, §1.5a–c, §3.7a).
   **Settled — and this was the barrier row's blocker:** the barrier and lagoon are
   **Beşik Bay's**, stated at p. 384, and the Karamenderes gets an explicit denial
   at p. 390 ("There is no beach or lagoon formation") — §3.3 now carries a verdict
   rather than an escalation. Also settled: **the plotted relative-sea-level curve**
   (383 fig. 2, after Kayan 1991), with "Trojan War", "Homer's time" and "Strabo's
   time" printed on it and a measured minimum of **−2.0 m at ~3300 BP** (§1.5a) —
   the single most useful figure the dossier has gained, and it arrived from item 4
   rather than from item 5 as expected; the **"could not have been used as
   harbours" sentence first-hand at 400–401** (the old "400" cite was short), with
   its "principal"/"big" qualifiers and its concession that ordinary beaching places
   "could have been used according to necessity" (401); Kesik's own measurements
   (13.7 m is the *saddle*, 6.3 m at the inner end 400 m east, 2 m colluvium, no
   archaeological material) and his **undecided** 2003 position on its origin,
   which is not the 2009/2014 tectonic reading (§1.5b, §1.9). **Settled against
   expectation, twice:** (a) **Fig. 6 (p. 396) is not a reconstruction map** — it is
   three borehole cross sections of the Yeniköy, Kesik and Kumtepe embayments after
   Kayan 1995, and it carries the Kesik siltation dates 3400/4200/4500 BP; the
   reconstruction is **Fig. 7 (p. 397)**; (b) **Fig. 7 draws no Late Bronze Age
   shoreline** — its isochrones are 6000–5500 BP, 5000–4500 BP, 2000 BP and Present,
   so the chapter commits nothing for the *Iliad*-time shore and any LBA line drawn
   from it is an interpolation (§1.5c). **Did NOT settle:** the abstract's **17 km**,
   which appears nowhere in the body (the body says "as far as the north of
   Pınarbaşı–Mahmudiye"); the **800 m** Kesik-plain width and the "before 1300 BC"
   siltation, both still Zangger-via-Kayan-2001/2009; whether Kelletat 1975 is
   behind the curve at all — this chapter cites Kayan 1988a, 1991 and 1997b and
   never names him, so §1.8's derivation needs re-checking (§5 item 14).
5. **✅ OBTAINED 2026-07-30 — Kayan 2014**, "Geoarchaeological Research at Troia and
   Its Environs," in *Troia 1987–2012: Grabungen und Forschungen I*, Teil 2, Studia
   Troica Monographien 5, **694–727**. Author-shared copy from İlhan Kayan's
   ResearchGate page, cached at
   `research-cache/kayan-2014-troia-geoarchaeology.pdf`; text and all twenty figures
   read, figs. 4, 8 and 16 measured (§1.5d, §3.7b). Entry kept so the ledger shows
   what a pull buys.
   **Page range confirmed, not corrected.** The expected **694–727** is right; the
   "Seite 538" marker on the PDF's first page belongs to the volume's front matter,
   which occupies PDF pp. 1–5 (§0). **Fig. 8 is the sea-level curve**, as the
   bibliography predicted, at printed **709**.
   **Settled:** the curve, **corroborating §1.5a's measurement to ±0.03 m off a
   second printing** — minimum **−1.99 m at 3.28 ka BP**, "Troian War" on the trough
   (§1.5d.1); the coring campaign's parameters and the **318** total with its
   composition (706, and Fig. 2's caption at 700), which checks Zangger's figure;
   the Kesik position first-hand, which is **not** the tectonic depression Zangger's
   paraphrase reported (§1.5d.2); that the **2014 "one can easily imagine … an
   excellent harbour" sentence is the setup of a refutation, exactly as the 2003 one
   is** — §6's open question closed and §1.9's "opposite mood" struck; the
   **Beşik barrier and lagoon dated to Troia VI and drawn twice with four dated
   shorelines** (704, 707–08 figs. 6–7), which is the geometry §5 item 4 had hoped
   for from the 2003 chapter's Fig. 6 and did not get; the Karamenderes barrier
   denial repeated verbatim (712).
   **Settled against expectation, three times.** (a) **The tectonic attribution is
   reversed by its own author** — 2014, 719 says tectonic reasons "are not convincing"
   and an "eustatic reason concerning a climatic effect must be taken into account",
   against 2003, 387's Bronze Age Regression (§1.5a, §1.5d.1). (b) **Kayan says Troia
   had harbours** — "Troia must have had a harbour or harbours in different places"
   (720) — and then never says where (§1.5d.6). (c) **There is still no Late Bronze
   Age isochrone**: fig. 16 (718) is 2003's fig. 7 reprinted, same four dated
   coastlines, no LBA line (§1.5d.3).
   **Did NOT settle:** any LBA distance from the citadel — the closest the chapter
   comes is fig. 15's section horizon "End of delta formation about 3500 years ago"
   at Troia's western foot (716), which is a date at a place, not a shore; the
   **17 km**, which does not appear in this chapter either; the **800 m** Kesik-plain
   width and the "before 1300 BC" siltation, still Zangger-via-Kayan-2001/2009; what
   **Kayan 1991, 1995, 1996 and 2000** say, on which every figure in this chapter
   depends (items 6, 7, 10); and **Kelletat**, who is not named here any more than in
   2003 (item 14). Note for the ledger: this chapter is **a synthesis by its own
   declaration** — "based on former data and interpretations, instead of new research
   results" (694) — so where it and 2003 agree they are one witness, and the pull's
   value lies in the two places where they do not.
6. **✅ OBTAINED 2026-07-30 — Kayan 1995**, "The Troia Bay and Supposed Harbour
   Sites in the Bronze Age," *Studia Troica* 5, **211–35**. Read in full, all
   fifteen figures and the table; note at
   `research-cache/kayan-1995-troia-bay-notes.md`.
   **Settled — and this was the load-bearing question: the 2003b citation does not
   check out.** The paper contains **no wall, no ditch, no Nestor and no *Iliad*
   fortification anywhere**; its Kesik material is a rejected harbour-canal
   candidacy and an undecided origin question (§1.9). Also settled: the Kesik
   measurements as **primary** (13.7 m saddle 150 m from the sea, 6.3 m at 400 m
   east, 2–2.5 m colluvium, twelve boreholes, no marine or fluvial fill); the
   **"no reason to discuss ambitious harbour theories" verdict eight years before
   the 2003 sentence** (231); the ¹⁴C table (Kesik 3400/4200/4500 BP, Yeniköy
   5300–5800 BP, Kumtepe 5500/7000 BP) and the Kesik-unusable-in-Troia-VI
   conclusion (228); the coinage of "**Bronze Age Regression**" (216, §1.5a); the
   Holocene sea-level ceiling (217, §1.8); and a **first-hand rebuttal of
   Zangger's 1992 canal hypothesis** twenty years before Zangger & Mutlu 2015
   (232–33).
   **Did NOT settle:** the abstract's **17 km**, which this paper does not derive
   either; the **800 m** Kesik-plain width and the "before 1300 BC" siltation,
   still Zangger-via-Kayan-2001/2009; anything about Beşik as harbour or about the
   Achaean camp — the paper is silent on both and **must not be cited for either**;
   and any coordinate, its maps being small-scale schematics with no grid.
7. **✅ OBTAINED 2026-07-30 — Kayan 2009**, "Kesik Plain and Alacalıgöl Mound: An
   Assessment of the Paleogeography around Troia," *Studia Troica* 18, **105–28**.
   Read in full, all 23 figures; note at `research-cache/kayan-2009-kesik-notes.md`
   (§1.9). **The catalogue trap is confirmed and it is 2014's error:** the title
   page reads Band 18 · **2009**, and Kayan 2014's bibliography (p. 727) misprints
   **2008**.
   **Settled:** the canal first-hand — bedrock threshold **13 m** a.s.l. and
   colluvial fill "**less than 2 m**" (109, 123–24), i.e. 1995/2003's 13.7 m and
   2–2.5 m stated to coarser precision, not re-measured; that **2009, 123–24 is
   the source text Kayan 2014, 723 condenses near-verbatim**, so the Kesik corner
   of §1.9's table is one position restated, not two witnesses; the
   **wall-and-ditch absence a second time**, which turns §1.9's absence into
   positive evidence and leaves Luce 1998 alone (item 9); the **Alacalıgöl
   mound**, 5th millennium BC (7000–6000 BP), abandoned when the inlet silted and
   never reoccupied; **Kesiktepe's military use dated to the 20th century** (World
   Wars / Çanakkale, p. 111), closing the vague "last great wars" note in the 1995
   extraction.
   **DID NOT SETTLE — and this is the pull's disappointment: both numbers it was
   pulled for came back negative.** (a) The "**800 m**" is the **Yeniköy ridge's**
   width (800–1000 m, p. 110), **not** the Kesik plain's; the plain is given only
   as "about 1 km²" and **no linear plain-width figure exists in the paper**, so
   the old "Kayan 2009, 108 fig. 3" cite (a photograph, no figure in its caption)
   must go. It also disagrees with Kayan et al. 2003, 398's "about 600 m" for the
   same ridge — recorded, unresolved. (b) "**Before 1300 BC**" is not the paper's
   date: it says "a swampy sedimentation unit **dated to about 4000–3500 BP**"
   (105), c. 2050–1550 BC uncalibrated — compatible with the summary but earlier
   and different. **Kayan 2001, 313 is now the sole remaining source for "before
   1300 BC", and it is unread** — the one second-hand dependency left in the Kayan
   material.
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
   **PRIORITY RAISED AGAIN, and the two are now the load-bearing gap in the whole
   §1.9 knot (2026-07-30).** The author-shared Springer extract **does not include
   Luce's chapter** — it carries chs. 23–25 only, and Luce ch. 2 appears solely in
   the table of contents (§0). Meanwhile both Kraft chapters turn out to rest on
   **Luce 1998** for the things we most want to cite: the camp's position on the
   ridge's outer flank (2003b, Fig. 5 caption; 2003a, Fig. 10 caption), the
   embayment between the headlands (2003b, 166), and — newly — **the Kesik cut as
   the Greek defensive trench** (2003a, 376). So Luce 1998 is not a supplement to
   the 2003 papers; it is their source. **And "Luce 2003 = Kesik harbour" now has no
   referent anywhere in the dossier** (§1.11c): neither 2003 chapter says it. Either
   Luce 2003 or Luce 1998 says it, or nobody does. Getting Luce 1998 pp. 111–63
   (the stretch 2003b, 166 refers the reader to) would settle more than any other
   single pull now outstanding.
10. **Kayan 1991**, "Holocene Geomorphic Evolution of the Beşik Plain," *Studia
    Troica* 1, **79–92** (esp. 91). **Settles:** Beşik Bay's Bronze Age geometry —
    which is also the missing coordinate problem for `besik-bay`. **PRIORITY RAISED
    to the top of the unpulled items, 2026-07-30.** Kayan 2014 turns out to rest on
    this one paper for **three** of the dossier's load-bearing objects: the
    **sea-level curve** (fig. 8 = Kayan 1991), the **Beşik barrier-lagoon section**
    (fig. 6 = "modified from Fig. 4 in Kayan 1991") and the **Beşik plan with its
    four dated shorelines** (fig. 7 = "modified from Plate 5 in Kayan 1991"). So the
    curve on which our whole sea-level statement rests, and the only dated Bronze Age
    barrier anyone draws, are **both** derivatives of an 80-hole hand-auger survey
    published in 1991 that nobody in this dossier has read. Everything else is
    reprint. **This is now the single largest unexamined foundation in the file**,
    and it is also where any error bars, any core log and any radiocarbon
    laboratory numbers behind the −2.0 m would have to be.
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
15. **✅ OBTAINED AND CLOSED 2026-07-30 — Kayan 1997b (Çıplak valley)**,
    "Geomorphological Evolution of the Çıplak Valley and Archaeological Material
    in the Alluvial Sediments to the South of the Lower City of Troia," *Studia
    Troica* 7, **489–507**. Read in full; note at
    `research-cache/kayan-1997-ciplak-notes.md` (§1.5e).
    **Settled, and it took Kayan 1999 alongside it (below) to finish the job:**
    the letters are **Kayan's own** — 1999's reference list and running prose make
    1997a the NATO chapter and **1997b this paper** — and **this paper carries no
    causal argument for the regression at all**, only the declared blank at p. 501
    ("No new evidence, however, was found here concerning the Bronze Age marine
    regression discussed in previous publications"). So **Kayan et al. 2003, 387's
    tectonic attribution to "Kayan 1997b" is a misattribution**, and the tectonic
    reading has no first-hand Kayan authority anywhere in the record (§1.5a, §6).
    Also settled, as new material: a **destruction layer** at the Lower City's
    southern foot, 2–4 m down, Hellenistic-Roman on the excavators' judgment; a
    **second rock-cut ditch** at the slope foot, Troia VI per Jablonka, shown by
    drilling not to be a water canal — **not the Kesik cut**; a fourth printing of
    the Holocene sea-level ceiling (§1.8).
    **Did NOT settle:** anything about the 2003/2014 reference lists themselves,
    which remain unseen (the Springer extract omits both, §0) — the letters were
    settled from 1999's list instead; and any figure measurement, the OCR being
    too degraded to work from.

**Acquired 2026-07-30 outside the numbered queue** (from İlhan Kayan's
academia.edu profile; each read in full, each with an extraction note in
`research-cache/`):

- **Kayan 1988**, "Late Holocene Sea-Level Changes on the Western Anatolian
  Coast," *Palaeogeography, Palaeoclimatology, Palaeoecology* 68: **205–18**.
  `kayan-1988-sea-level-notes.md`. **Settled:** the Beşik barrier's first
  systematic (drilling-based) treatment — the earliest *print* remains the 1982
  chapter's report of Erol's spit — with two stacked barrier generations and Troy VI sherds
  in the upper one (§1.5b); an independent third confirmation of the 1980 and
  1982 citations from its own reference list. **Did NOT settle:** any metre value
  for the Beşik low stand — the author says a precise curve had not yet been
  drawn, and offers only "about 1–2 m".
- **Kayan 1997**, "Bronze Age Regression and Change of Sedimentation on the
  Aegean Coastal Plains of Anatolia (Turkey)," in *Third Millennium BC Climate
  Change and Old World Collapse*, ed. Dalfes, Kukla & Weiss, **431–50**, NATO ASI
  I/49 (Springer). `kayan-1997-regression-notes.md`. **Settled:** the
  climatic-eustatic argument, at length and in the conclusions (§1.5a, §6); the
  Karamenderes barrier denial six years before 2003 (§1.5b); the Holocene
  sea-level ceiling as an Aegean-wide finding (§1.8). **Did NOT settle:** whether
  it is "1997b" (item 15).
- **Kayan 1996**, *Studia Troica* 6: **239–49**. `kayan-1996-st6-notes.md`.
  **Settled:** an independent stratigraphic proof of the ~2 m fall (Fig. 4's
  channel cutting the marine unit); the north-foot land surface first forming
  ~3500 BP, with the oldest sherds dated Troia VI/VII — a **minor periodization
  discrepancy** against 2003's "Troia IV–VI" paraphrase, recorded not resolved
  (§1.5b).
- **Kayan 2000**, "The Water Supply of Troia," *Studia Troica* 10: **135–44**.
  `kayan-2000-water-supply-notes.md`. **Settled:** the Pınarbaşı/Düden springs'
  elevation and Bronze Age burial depth, and the **buried-hot-spring hypothesis**
  that the CATENA survey later closes — carried in
  `RESEARCH-TROAD-TOPOGRAPHY.md` §6.8, not here. **Nothing for this dossier's
  sea-level or Kesik questions:** the paper carries no curve, no metre value and
  no Kesik.
- **Kayan 1999**, "Holocene Stratigraphy and Geomorphological Evolution of the
  Aegean Coastal Plains of Anatolia," *Quaternary Science Reviews* 18: **541–48**.
  `kayan-1999-qsr-notes.md` (§1.5f). **Settled:** the **1997a/1997b letter
  assignment**, from Kayan's own reference list (547–48) and his running prose
  (544) — the single fact that closes item 15 and §6's tectonic question; the
  anti-tectonic position restated in his own voice three years before 2003
  ("tectonic deformation… has not been observed in spite of tectonic activity in
  this region", 548); a **fifth** printing of the 5000–3500 BP / ~2 m interval
  (545–46, §1.5a); a regional form of the sea-level ceiling (Fig. 6 caption, 547)
  and the ~6000 BP present-level dating (544–45). **Did NOT settle:** anything
  measurable — this is the one paper in the series with **no plotted sea-level
  curve**; nothing on Beşik, the barrier or Kesik; and the issue numbers "4–5",
  which are not printed on the extracted pages.
- **Kayan 2002**, *Mauerschau: Festschrift für Manfred Korfmann* 3: **993–1004**.
  `kayan-2002-footslope-notes.md`. **Settled:** the **battlefield-surface
  argument** in Kayan's own voice (§1.4b); the 5000–3500 BP interval for the
  fall, matching 2003's and independently stated a year earlier (§1.5a); the north-footslope platform's **depth**, 4–5 m
  below present sea level, which is not the 2003 chapter's **width** and must not
  be merged with it (§1.5b); the buried Dümrek riverbed, ~200 m wide, ¹⁴C **and
  OSL** dated; the 285-by-2001 coring count independently; the full citation this
  dossier had been carrying without editors or publisher. **Did NOT settle:** any
  coordinate — no lat/long appears anywhere in the chapter.

---

## 6. Unverified — do not claim publicly

Two items left this list on 2026-07-29, when the 1980 *Science* full text arrived,
and one more on 2026-07-30 with the 2003 *Geology* full text; two more the same day
with the two Springer chapters (the plotted sea-level curve, and the barrier's
width — the latter superseded by a harder question); and **two more the same day
with Kayan 2014** (the undated "Kayan reads Kesik as natural", and the "opposite
mood" question, both settled against the dossier's own reading). Each is noted below
with the § that now carries it. **Four items were added on 2026-07-30** from the
Springer full texts, and **two more later that day from Kayan 2014** — the
tectonic-to-eustatic reversal, and the retirement of "Kayan denies Troy had a
harbour". All six are corrections to things this dossier had been asserting.
Everything else stands.

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
  **KAYAN 1995 IS NOW READ, AND IT REMOVES A CITATION RATHER THAN ADDING ONE
  (2026-07-30).** The paper 2003b names for the wall-and-ditch reading contains no
  wall, no ditch, no Nestor and no *Iliad* fortification; it treats Kesik solely
  as a rejected harbour-canal candidate (§1.9). **So the reading now rests on Luce
  1998 alone**, still unread (§5 item 9) — which matters for D6, whose plate note
  leads with it. Do not write "Kayan 1995 identifies the Kesik cut as the Achaean
  wall and ditch"; write that Kraft, Rapp, Kayan & Luce 2003b, 166 cite Kayan 1995
  for it and that the cited paper does not contain it.
  **STANDS, and hardened later the same day on the two Springer full texts.** Both
  2003 chapters now hold the wall-and-ditch reading, but they cite **different**
  authorities for it (2003a → Luce 1998; 2003b → Kayan 1995), so it is one idea
  wearing two citations; 2003a states it **conditionally** ("if proven to be of
  three millennia or greater age"); and Kayan's own chapter in the same volume
  says in terms that "**there is no information about the purpose and time of
  construction**" (399). **An LBA date for the Kesik cut is asserted by nobody who
  has dated it.** Do not print one.
  **HARDENED AGAIN 2026-07-30 on Kayan 2014, and this is now as strong as a negative
  gets.** 2014, 724 takes the Bronze Age candidacy seriously enough to name it —
  "the Bronze Age, especially the period of Troia VI/VIIa, remains under discussion
  as a period of possible canal construction" — and rules it out on two grounds:
  **there was no bay to serve** ("the Kesik depression was **not a marine
  embayment**; instead, it was covered by a swamp… a canal was not necessary for a
  waterway connection") and **there is nothing there** ("**no archaeological evidence
  later than the Chalcolithic period in this area**"; and in the cut itself, "any
  archaeological material or any trace of human impact were not found in colluvial
  deposition about 2 m thick in trenches which we dug across the canal", 723). So the
  one member of the group who has actually dug the feature rules out the date the
  other two chapters assert.
- ~~**That "Kayan reads the Kesik cut as natural" without a year.**~~ — **SETTLED
  2026-07-30 on the Kayan 2014 full text → now carried by §1.5d.2 and §1.9, and it
  settled against the dossier's own reading.** There was no change of position to
  date: 2014, 723 says "**In the new stage of our research we have obtained no
  evidence to change our former interpretation**", and what it holds is 2003's
  agnosticism ("appears artificial"; "no evidence… that it was dug out") with a
  **pre-Holocene fault line** as the preferred hypothesis — plus an explicit denial
  that "the Holocene deposits in the Kesik depression" support tectonic activity in
  the Holocene. **Two things remain binding.** (1) "Kayan: tectonic depression" is
  never writable flat — it inverts his Holocene claim. (2) "Widened by foot traffic"
  is Zangger's, not Kayan's: 2014, 724 says only that the canal "has been **used**
  continuously for land passage". **Kayan 2009 has now been read (§1.9, §5 item 7)
  and it says what 2014 says — in fact 2014 condenses 2009's paragraph
  near-verbatim, so the two are one witness.**
- ~~**That Kayan writes about the Kesik plain "in the opposite mood."**~~ —
  **SETTLED 2026-07-30 → §1.5d.2, and the answer is no.** The near-identical Kayan
  2014, 723 sentence **is also concessive**: it opens a paragraph that turns on it
  within two sentences ("Concerning this idea, there are various interpretations in
  the literature… **Although the canal is too high for direct water connection**…")
  and is refuted at 724 ("the Kesik depression was **not a marine embayment**;
  instead, it was covered by a swamp. **Therefore, a harbor is not a subject of
  discussion**"). Both instances, 2003 and 2014, are the setup of a refutation.
  **The quotation may never be used to show Kayan contradicting himself**, and
  §1.9's "opposite mood" sentence has been struck.
- **That Kayan attributes the Bronze Age sea-level fall to tectonics.** Opened
  2026-07-30 as a contradiction *inside* our best source, **and closed the same
  day as a misattribution in that source** — see the resolution at the foot of
  this item. **2003, 387:** "the sea level fall during the Bronze Age is attributed to
  **tectonic movements** (Bronze Age Regression; Kayan 1997b)." **2014, 719:**
  "there is **no proof for the cause**… **tectonic reasons are not convincing
  explanations** for uniform sea-level changes. Thus, an **eustatic reason
  concerning a climatic effect** must be taken into account for sea-level
  changes." **Print no cause without a year.** And note what the eustatic reading
  costs: a tectonic fall is
  local by construction and unfalsifiable from regional data, while an eustatic one
  is checkable — and Seeliger et al. 2021's NE Aegean database shows continuous rise
  across this window (§1.8). **In his last statement Kayan puts his own curve where
  it can be contradicted, and it is.** That is a live problem for any note that
  quotes −2 m, and it is not ours to resolve.
  **RESOLVED 2026-07-30, and it is not a reversal — it is a bad citation in 2003
  (§1.5a).** Two papers acquired that afternoon settle it. **Kayan 1999's own
  reference list (547–48) and prose (544) assign the letters**: 1997a is the NATO
  ASI chapter, **1997b is *Studia Troica* 7 (1997): 489–507**, the Çıplak valley
  paper. That paper has now been read (§1.5e) and it **argues nothing** about the
  regression — its one sentence on the subject is a declared blank (p. 501: "No
  new evidence, however, was found here concerning the Bronze Age marine
  regression discussed in previous publications"), footnoted only to Kayan 1991
  and 1995. And **Kayan 1999, 548 states the anti-tectonic position in his own
  voice** three years before 2003: "tectonic deformation in the Middle–Late
  Holocene sedimentary units and geomorphology of the coastal plains **has not
  been observed** in spite of tectonic activity in this region." So **no Kayan
  1997 text supports 2003, 387 — not 1997b, which says nothing, and not 1997a,
  which says the reverse — and the tectonic reading of the Bronze Age fall has no
  first-hand Kayan authority anywhere in the record.** 2014 is therefore
  **continuous** with 1997a and 1999, not a reversal of a position he ever held;
  the outlier is one sentence in 2003 citing a paper that does not say it. The
  honest form is now: **1997 climatic → 1999 climatic → 2003 tectonic, miscited →
  2014 climatic.** **Do not print "Kayan 1997b: tectonic" at all**, and do not
  print "Kayan changed his mind about the cause" either.
- **That Kayan denies Troy had a harbour.** New, 2026-07-30, as a **retired**
  claim, and this dossier has been carrying it. **Kayan 2014, 720 opens the harbour
  section affirmatively:** "Troia **must have had a harbour or harbours** in
  different places following changes of coastline positions during deltaic
  progradation." What he denies — in both chapters — is a harbour *installation*:
  "no reason to create **great** harbour theories" (2003, 401), no *principal* or
  *big* harbour, and none of the three western embayments. Combined with 2003, 401's
  concession that ordinary beaching places "could have been used according to
  necessity", the settled reading is **harbours yes, harbour works no, location
  unknown — and Kayan never answers his own question** (§1.5d.6, §2). A caption
  saying "Kayan: no harbour" is wrong.
- **That Kraft et al. 2003a put the harbour at Kesik.** New to this list,
  2026-07-30, as a **retired** claim: the chapter says all three western embayments
  "had excellent harbor potentials" and names none (376). The Kesik attribution was
  Brückner et al. 2005's paraphrase (§§20–21), which we adopted. It has been struck
  at §1.4, §1.9, §1.11c and §2 and must not return. **What Brückner reports of a
  paper we have not read is a lead, not a citation** — this is the second time that
  rule has cost the dossier something (cf. the "1.2 km", §1.3).
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
  Erol's curve. ~~**Still unverified:** Kayan's own plotted curve (Kayan 2014,
  fig. 8)~~ — **NOW SETTLED, 2026-07-30 → §1.5a, and it did not need Kayan 2014.**
  The curve is printed at **Kayan et al. 2003, 383 fig. 2** (after Kayan 1991), with
  "Trojan War", "Homer's time" and "Strabo's time" keyed on to it; measured minimum
  **−2.0 m at ~3300 BP**, present level 6000–5100 BP, ~−0.4 m at 2000 BP. **And it
  disagrees with Kraft's 1980 Fig. 6, which is the reason to keep both on the
  page:** Erol's curve puts sea level **at present level at 3250 BP** and **+2 m at
  4500 BP**; Kayan's puts it at **−2 m at 3300 BP** and at **present level at
  4500 BP** — the two are about 2 m and 4 m apart at those dates, and they are the
  same research group twenty-three years apart. Do not merge them; name whose curve
  a caption is using. **Still unverified:** any metre value at a date neither curve
  labels — no interpolation. Also note what the 1980 curve is: **ref. 17,
  "O. Erol, unpublished data"** — cite it as the paper's stated basis, never as an
  independently published curve; and what the 2003 curve is: a hand-drawn line from
  **Beşik-plain** hand drillings, with a tectonic cause asserted (387).
  **RE-MEASURED OFF A SECOND PRINTING, 2026-07-30 (Kayan 2014, 709 fig. 8 — §1.5a,
  §1.5d.1, §3.7b).** Same plate, independent measurement: **−1.99 m at 3.28 ka BP**
  against 2003's −2.01 at 3.29, and ±0.03 m across the whole 4.3–2.3 ka span. **The
  −2.0 m at ~3300 BP may now be printed without hedging as to its value.** Two
  riders that are facts, not hedges: the **cause** is stated one way in 2003 and the
  opposite way in 2014 (see the tectonic/eustatic item above), and the author reports
  **0.2–0.6 m of datum and levelling error** in the survey behind it (2014, 707–08).
  And the whole object is one 1991 hand-auger survey reprinted three times (§5
  item 10) — not three witnesses.
- ~~**The width of the Bronze Age barrier.**~~ **SUPERSEDED 2026-07-30 → §3.3.**
  The question is no longer how wide the barrier was but **whether it is on the
  right bay**. Kayan et al. 2003, 382 puts the Bronze Age barrier and lagoon at
  **Beşik**; p. 390 denies beach and lagoon formation on the Karamenderes; Kraft et
  al. 2003a, 364 puts the accretion ridges at Beşik and coast-parallel lineaments
  only in the Scamander's lowest 2 km; and the only Scamander-front barrier drawn on
  any plate is Kraft's, on the **2000 BP** shoreline (2003a, 374 fig. 10 — §1.4a).
  `barrier-bronze` should be deleted, re-dated to c. 0 BC/AD, or moved to Beşik
  (§3.3). Its width was never the problem.
- **The relative sea level at any date the curve does not label.** New, 2026-07-30.
  A plotted curve now exists (Kayan et al. 2003, 383 fig. 2) and §1.5a tabulates it
  at 15 points, but it is a **hand-drawn interpretive line from Beşik-plain hand
  drillings**, not a data series with error bars: no points, no envelope, no
  publication of the underlying dates in that figure. Quote the **minimum**
  (−2.0 m at ~3300 BP) and the **crossings** (present level 6000–5100 BP; ~−0.4 m
  at 2000 BP), which the figure commits; do not read a value off it to a tenth of a
  metre at an arbitrary date, and never present it as regional — Seeliger et al.
  2021's NE Aegean database shows continuous rise (§1.8).
- **Any claim that a Bronze Age harbour has been located.** The literature's
  positions are: Beşik (**Kraft, Kayan & Erol 1980, 782** — first-hand, and the
  earliest of them; then Kraft et al. 1982, Kayan 1991, Korfmann; **and Kraft et al.
  2003a, 376 still keeps it**, "the Beşik embayment always provided a place of
  shelter for ships"), Kesik (A. Brückner for Sigeion; **Zangger 1992 and 2003, and
  it is Zangger's proposal that Kraft et al. 2003a is agreeing to**), an artificial
  basin (Zangger & Mutlu 2015, explicitly a working hypothesis), and no *principal*
  harbour anywhere though ordinary beaching places yes (Kayan et al. 2003, 401).
  A map that picks one must name whose it is **and which year**.
  **CORRECTED 2026-07-30, twice over.** (a) ~~Kraft moved from Beşika to Kesik
  between 1980 and 2003~~ — he did not; 2003a keeps Beşik as shelter and puts the
  *camp* on the Sigeum ridge's outer flank after Luce 1998 (§1.9). (b) ~~Kraft et
  al. 2003a~~ does not belong on the Kesik list at all; that was Brückner's
  paraphrase (§1.4). What survives: **"Luce" without a year still names three
  incompatible things** (1975 received view → 1984 Sigeum ridge → 1998/2003
  outer flank), and **the Kesik harbour, if anyone holds it, is Zangger's and
  possibly Luce's — not Kraft's and not Kayan's** (§1.11c, §5 item 9).
- **The Kesik cut's date and purpose.** Unresolved, and now sharper (2026-07-30,
  `RESEARCH-TROAD-TOPOGRAPHY.md` §9.2): Kayan reads it as **natural** — **restated
  first-hand later the same day (§1.5d.2): a canal that "appears artificial" on a
  depression "naturally formed on a fault line" that is *pre-Holocene*, with "no
  evidence… that it was dug out" and no trace of spoil, and NOT a Holocene tectonic
  feature by his own sediments; "widened by foot traffic" is Zangger's phrase, not
  his** — while Cook reads it as **artificial**, "never
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
