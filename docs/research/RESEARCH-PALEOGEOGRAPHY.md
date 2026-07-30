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
to sit on, and §1.1 now carries page and figure numbers).

**Abstract or publisher metadata only:** Kraft, Rapp,
Kayan & Luce 2003; Kayan et al. 2003; Kayan 2019; Luce 1984; Seeliger et al.
2021.

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
   the 2003 *Geology* paper, which remains unverified (§1.3) — but 1980 can no
   longer be offered as its support, and 1980's own Strabo reading points the
   other way. Our drawn line stays defensible on the Strabo arithmetic (§3.1); the
   **attribution** does not.
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

### 1.3 Kraft, Rapp, Kayan and Luce 2003 — the harbour paper

**Claim.** "For at least two thousand years scholars have debated the location of
Troy and the events and geographic features described in Homer's *Iliad*.
Geologic evidence is used to present a series of maps of the Trojan plain that
show the geomorphic changes over the past six millennia. The geologic evidence
correlates very well with the relevant Homeric geography."

- Citation: Kraft, John C., George (Rip) Rapp, İlhan Kayan, and John V. Luce.
  "Harbor Areas at Ancient Troy: Sedimentology and Geomorphology Complement
  Homer's *Iliad*." *Geology* 31, no. 2 (2003): 163–66.
  https://doi.org/10.1130/0091-7613(2003)031<0163:HAAATS>2.0.CO;2
- Authority: **prose**. That is the whole abstract, verbatim: **it contains no
  number at all.** Every quantity anyone attributes to this paper — bay-head
  position, harbour locations, the six-millennia map series — is in the figures
  and the body, which are paywalled.
- Verified how: abstract via
  [NASA ADS](https://ui.adsabs.harvard.edu/abs/2003Geo....31..163K/abstract) and
  the GeoScienceWorld landing text mirrored in
  [OpenAlex](https://api.openalex.org/works/doi:10.1130/0091-7613(2003)031%3C0163:HAAATS%3E2.0.CO;2).
- **Consequence for our data.** `shore-bronze`'s note says the 10 m contour
  "passes 1.2 km north of Hisarlik, **where Kraft, Rapp, Kayan and Luce put the
  bay head**". That attribution is still **unverified** — the claim is not in
  the abstract and I have not seen the figures. What *is* verified is the
  underlying constraint, from Strabo and from Kraft's reading of him reported by
  Brückner: §1.6 and §1.10. Either re-attribute or pull the paper (§5, item 2).
- **Narrowed, not settled, by the 1980 full text (2026-07-29).** The 1980 paper —
  same lead author, same coring campaign — contains **no bay-head distance from the
  citadel at all**, and its Bronze Age statement is that Troy VI/VII "lay on a
  projection or promontory at the edge of a marine embayment" with the water to the
  west and south-west (§1.1, p. 782). It also treats Strabo's description as
  evidence for c. 2000 BP rather than for the war, so the Strabo-6-stades → LBA
  shore chain is *not* Kraft's 1980 reasoning. So: **the "1.2 km" cannot have come
  from the 1980 paper.** If it is genuinely Kraft's, it must be new in 2003 — and
  that is a claim about a figure nobody in this project has seen. Until item 2 of
  §5 is pulled, the honest note attributes the ~1 km order of magnitude to
  **Strabo 13.1.36 as read by Brückner** (§1.6, §1.10), not to Kraft.

### 1.4 Kraft, Kayan, Brückner and Rapp 2003 — the facies chapter (UNSEEN)

**Claim, at second hand.** Their reconstruction ("Scenario II" in Brückner et al.
2005, Fig. 3) keeps a **bird's-foot delta in a quiescent, low-wave-energy
embayment until c. 0 BC/AD**, after which the strong east–west Dardanelles
current takes over, eroding distributary arms and building sand spits. They take
**the Kesik plain, a former marine embayment on the eastern slope of the Sigeum
ridge, as the best candidate for a natural harbour** at the time of the war, and
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
marsh) was the harbour basin of classical **Sigeion**. *Helmut* Brückner is the
modern geoarchaeologist of §1.6.

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
linking the Kesik plain to the Aegean shore. But Kayan's drilling in it found a
**2–2.5 m colluvium fill** on its floor, and **the floor stands about 13.7 m above
sea level, some 150 m from the sea**, while the ridge surface there reaches 30 m.
So, deep as it is, the cut's floor is nowhere near sea level: **it was neither
navigable nor a drainage channel.** Kayan takes it for a tectonic depression
(Kayan 2009, 124; Kayan 2014, 723) widened by foot traffic between coast and
plain (Kayan 2014, 724); J. M. Cook had already concluded that the work was never
finished (Cook 1973, 167).
- Authority: **geometry** (400 × 50 × 30 m; floor at 13.7 m a.s.l.; 150 m from
  the sea), second-hand from Kayan's cores; **identification** (not a harbour
  entrance).
- Verified how: Zangger & Mutlu 2015, 565 and 569, fnn. 36–37, 57–59 (Turkish;
  translated by me).

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
  whose it is, or draw neither.

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

### 1.11 Luce — the dissent, verified, and it is not a fringe position

**Claim (Luce 1984, verbatim abstract).** "Homeric passages bearing on the
location of the Achaean camp at Troy are re-examined in the light of new
scientific data on the time-scale for the alluviation of the Trojan plain. The new
data confirm the accuracy of Strabo's account of the plain, and in particular of
the shore-line having come close to the Hisarlik site (*Novum Ilium*) in
Hellenistic times. **In the era of Troy VI/VII, c. 3,250 years BP, the shore-line
appears to have run west by south of the site, and a broad marine embayment lay
between the city and the Sigeum ridge.** It is therefore no longer possible to
accept the received view (deriving from Schliemann and Leaf) that the Achaean camp
was sited on the present shore-line by the Hellespont. **A new site is proposed for
the camp on the lower slopes of the Sigeum ridge about four miles west of
Hisarlik.** It is argued that the indications in the *Iliad* are not inconsistent
with such a siting, and in fact suit it better than the received view. This is
shown with regard to the course of the Scamander, evidently pictured by Homer as
running between camp and city, and also with respect to **the general axis of the
fighting on the plain, which is indicated to lie in an east-west rather than a
north-south direction**. The Besika Bay site, first proposed in 1912, is rejected
as inconsistent with the Homeric data and unsatisfactory in itself."

- Citation: Luce, J. V. "The Homeric Topography of the Trojan Plain
  Reconsidered." *Oxford Journal of Archaeology* 3, no. 1 (1984): 31–43.
  https://doi.org/10.1111/j.1468-0092.1984.tb00114.x
- Authority: **identification** (camp position; fighting axis); **geometry** for
  "four miles west" and the embayment's position, both approximate.
- Verified how: full abstract via
  [OpenAlex](https://api.openalex.org/works/doi:10.1111/j.1468-0092.1984.tb00114.x)
  (Wiley and Semantic Scholar both withhold it; OpenAlex carries the publisher
  abstract). Body and figures unseen.
- **Why it must be on the page, not buried.** Luce is a co-author of the *Geology*
  paper (§1.3), so his reconstruction is not an outsider's objection to the
  geoarchaeology — it is the classicist half of the same project. His camp is
  **west** of Troy on the Sigeum ridge, not **north-west** on the Hellespont
  beach; his battlefield axis is **east–west**. Our plate note already says this
  and says the sheet draws Kraft instead. That is the right posture; the note
  should also say that Luce's placement is the same Kesik-side ground that Kraft
  et al. pick for the harbour, i.e. the two are one reconstruction, not two.
- **And "Kraft instead" will not do as a contrast (full text, 2026-07-29).** Kraft,
  Kayan and Erol 1980, 782 put the Achaean camp at **Beşika** and the battlefield
  axis "to the south of Troy and to the east of the Beşika embayment" — further
  south-west than Luce's Sigeum-ridge camp, not opposite it. On the camp's *side of
  the city* there is no Kraft/Luce disagreement to draw: 1980 Kraft, 2003a Kraft
  and Luce all put the fleet west or south-west, and none of them puts it on the
  Hellespont beach. The received Schliemann–Leaf placement is the position all
  three reject. Any note that sets "Kraft" against "Luce" here is contrasting the
  wrong pair (§1.1, §1.9, §4 item 10).
- **One number to flag.** "About four miles west" is ~6.4 km. DEM measurement
  (this dossier): from Hisarlık (39.957, 26.239) the east foot of the Sigeum
  ridge — where the ground rises past 20 m — is ~5.4 km west, and the crest is at
  lon 26.17–26.18. Four miles west of Hisarlık would be at or beyond the ridge's
  seaward side. Luce's own figure is needed before any anchor is placed for his
  camp; without it, "the lower eastern slopes of the Sigeum ridge, c. 5 km west"
  is the defensible paraphrase.
- **Related, unseen:** Luce, J. V. *Celebrating Homer's Landscapes: Troy and
  Ithaca Revisited* (New Haven: Yale University Press, 1998); "The Case for
  Historical Significance in Homer's Landmarks at Troia," in *Troia and the
  Troad: Scientific Approaches*, 9–30 (Berlin: Springer, 2003). Brückner's Fig. 3
  caption reports Luce 2003 as identifying the Greek camp and ship station from
  Strabo's 20 stades; Zangger reports (2015, 562, fn. 25, citing "Luce 1995,
  211" = the German *Archäologie auf den Spuren Homers*) that Luce adopted the
  Kesik harbour claim.

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
| LBA shore, c. 1200 BC | **Of the order of 1 km** from the citadel, north to north-west. The number is **Strabo 13.1.36's 6 stades as read by Brückner** (§1.6, §1.10) — *not* Kraft's: **Kraft, Kayan & Erol 1980 give no citadel-to-water distance at all**, only "Fortification Troy VI and VII lay on a projection or promontory at the edge of a marine embayment" (782), and they read Strabo as describing **his own** time, not the war (778–79). Luce 1984 puts the shore **west by south** instead. *(full text, 2026-07-29: attribution corrected.)* | geographic, ±~1 km |
| Sea-level change | Local relative fall of **2 m** (Kayan et al. 2003) or **2–3 m** (Kayan 2019) in the LBA, derived from Kelletat's 1975 curve. Independently and earlier, Kraft, Kayan & Erol 1980's Fig. 6 gives the **endpoints**: **+2 m at 4500 BP → present level at 3250 BP and at 2000 BP**, i.e. a 2 m fall *to* today's datum, from Erol's unpublished curve (ref. 17); the authors call it "valid as a **local, relative,** sea level curve for the Biga Peninsula" (781). The NE Aegean RSL database shows **continuous rise** (Seeliger et al. 2021) *(full text, 2026-07-29)* | state as **local/relative**, never regional; state the endpoints, never a bare "fell 2 m" |
| Barrier | A **wide sandy coastal barrier** closing the remaining water into a shallow lagoon after that fall. The barrier-and-lagoon facies language is **Brückner et al. 2005**; the Kayan et al. 2003 and Kayan 2019 *abstracts* describe the fall and the swamp but do not themselves say "barrier" or "lagoon" — the full texts are unseen (see Needs paywalled access). **Kraft, Kayan & Erol 1980, read in full, has neither word**: its terms are sandy/clay-silt estuary, marsh, swamp, beaches, shoals and brackish–freshwater swamp *(full text, 2026-07-29)*. Independently, Strabo 13.1.31 describes a **blind (barred) river mouth with salt lakes and marshes** | geographic; width unsurveyed; **not drawing-ready geometry until a Kayan full text or figure is seen** |
| Lagoon | Shallow, behind the barrier; ancient name **Stomalimne** attested between Sigeium and the Scamander mouths (Strabo 13.1.31) | geographic + identification |
| Swamp / marsh | The area west of the city was a **broad deltaic swamp** in Troia IV–VI; the land was **swamp-covered throughout the progradation period**, and the coastal sea **very shallow** (Kayan et al. 2003). Corroborated first-hand: Kraft's Fig. 2 maps modern swamp over the Kesik/Yeniköy plain and the Scamander's western and south-western flanks, and the text allows that "low-lying swamps occurred around the base of Troy" at 3250 BP — with the honest rider "although further drilling would be required to verify this" (1980, 782) *(full text, 2026-07-29)* | geographic, extent approximate |
| Kesik cut | **400 × 50 × 30 m**, floor **13.7 m a.s.l.**, ~150 m from the sea, 2–2.5 m of colluvium on the floor; unfinished (Cook 1973, 167); read as a tectonic depression by Kayan | geographic; **not** a harbour entrance |
| Kesik plain | Basin ~**800 m** wide; silted **before 1300 BC**; "could not have been used as harbours during the Later Bronze Age" (Kayan et al. 2003, 400) — against Kraft et al.'s choice of it as the harbour | contested identification |
| Beşik Bay | The project's original harbour candidate, stated first-hand in **Kraft, Kayan & Erol 1980, 782** ("the Beşika embayment was indeed the site of the Achaean camp"; "an indentation approximately **2 km inland**" at 4000–5000 BP) and again at Kraft et al. 1982, 40 and Kayan 1991, 91; rejected by Luce 1984 as inconsistent with the *Iliad* *(full text, 2026-07-29: cite 1980, not the second-hand 1982 quotation)* | contested identification |
| Harbour, in general | Kayan et al. 2003: the environment "has never been suitable for the establishment of an important harbour" | prose; the strongest deflationary claim in the literature |

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

---

## 4. Corrections this dossier owes to files it must not edit

Findings only — no tracked file outside `docs/research/` was touched.

1. `apparatus/plates/trojan-plain.json`, `shore-bronze`: the "1.2 km north of
   Hisarlik, where Kraft, Rapp, Kayan and Luce put the bay head" attribution is
   unverified (§1.3). The 8 m / 12 m arithmetic does not reproduce (§3.1).
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
2. **Kraft, Rapp, Kayan & Luce 2003**, *Geology* 31 (2): **163–66**, DOI
   `10.1130/0091-7613(2003)031<0163:HAAATS>2.0.CO;2`. **Settles:** whether the
   c. 1200 BC shoreline in their figures really passes ~1.2 km north of Hisarlık
   (the attribution in `shore-bronze`'s note), and which harbour areas they name.
   **We need the figures, not the abstract** — the abstract contains no number
   (§1.3). *(Priority raised to first, 2026-07-29: the 1980 full text ruled itself
   out as the source of the 1.2 km, so this paper is now the **only** candidate for
   an attribution we are currently printing on a plate.)*
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
   sediment character".
7. **Kayan 2009**, "Kesik Plain and Alacalıgöl Mound," *Studia Troica* 18,
   **105–28** (esp. 105, 108 fig. 3, 124). **Settles:** the Kesik plain's geometry
   and its siltation date, first-hand.
8. **Luce 1984**, *OJA* 3 (1): **31–43**. **Settles:** where exactly Luce's camp
   sits ("about four miles west" needs his map), and his shoreline for
   c. 3250 BP — the dissenting line we may want to draw as an alternative.
9. **Luce 2003**, "The Case for Historical Significance in Homer's Landmarks at
   Troia," in *Troia and the Troad*, **9–30** (esp. 22). Also **Luce 1998**,
   *Celebrating Homer's Landscapes* (Yale). **Settles:** whether Luce charts the
   fighting scene by scene (a standing question in `TROAD-CARTOGRAPHY.md`), and
   his final camp placement.
10. **Kayan 1991**, "Holocene Geomorphic Evolution of the Beşik Plain," *Studia
    Troica* 1, **79–92** (esp. 91). **Settles:** Beşik Bay's Bronze Age geometry —
    which is also the missing coordinate problem for `besik-bay`.
11. **Vacchi et al. 2013**, *Quaternary International* 328–29, **301–10**; and
    **Lambeck & Purcell 2005**, *QSR* 24, **1969–88**. **Settles:** the actual RSL
    value for the NE Aegean at ~3.2 ka BP, which is what tells us how much of
    Kayan's "fall" can be regional at all.
12. **Cook 1973**, *The Troad*, **167** (borrowable scan exists — lending, not PD).
    **Settles:** his verdict on the Kesik cut, first-hand rather than through
    Zangger's Turkish paraphrase.
13. **Alfred Brückner 1912** (*AA* 26: 616–33) and **1925** (*AA* 39: 230–48, esp.
    246). Pre-1931, so **PD in the US** — worth hunting for a scan rather than a
    library visit. **Settles:** the two Yeniköy cuts and the Sigeion-harbour
    proposal at their origin.
14. **Kelletat 1975**, *NJb Geol. Paläont. Mh.* 6, **360–74**. **Settles:** the
    curve on which Kayan's Bronze Age fall rests.

---

## 6. Unverified — do not claim publicly

Two items left this list on 2026-07-29, when the 1980 *Science* full text arrived;
each is noted below with the § that now carries it. Everything else stands.

- **That Kraft, Rapp, Kayan & Luce 2003 put the LBA bay head ~1.2 km north of
  Hisarlık.** Still unverified: not in the abstract; figures unseen. Currently
  asserted in `shore-bronze`'s note. **Narrowed 2026-07-29:** the 1980 paper, read
  in full, does not contain the claim in any form, so it cannot be the source and
  cannot be offered as support (§1.1, §1.3). The 2003 *Geology* figures are now the
  only candidate — §5 item 2, raised to first priority.
- **The "20 stades from Troia to the Achaean harbour" as Strabo's own statement.**
  It is Kraft's and Luce's reading of 13.1.36; the PD translation attaches the 20
  stadia to the Scamander's mouth (§1.10). **Reinforced 2026-07-29:** the 1980
  paper prints **no stade figure at all** and reads Strabo as describing his own
  century, so the stade readings enter with the 2003 papers and belong to them
  (§1.1).
- **Anything about Luce's camp beyond his abstract** — in particular any anchor
  placed from "about four miles west", which does not agree with the measured
  distance to the Sigeum ridge's eastern foot (§1.11).
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
  (A. Brückner for Sigeion; Zangger 1992; Kraft et al. 2003a; Luce), an artificial
  basin (Zangger & Mutlu 2015, explicitly a working hypothesis), and no viable
  harbour at all (Kayan et al. 2003). A map that picks one must name whose it is
  **and which year** — Kraft moved from Beşika to Kesik between 1980 and 2003
  (§1.9).
- **The Kesik cut's date and purpose.** Unresolved in every source read: Kayan
  calls it tectonic, Cook calls it unfinished, Korfmann dated the Yeniköy canal to
  the 18th century AD, an 18th-century engineer thought it Bronze Age. Its floor
  at 13.7 m a.s.l. is the one hard fact.

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
| — | 39.9608, 26.1680 | `Demetrius tumulus`, Çanakkale (archaeological_site) | Returned by a search for "Kesik". Probably Kesik Tepe, the mound near Sigeion that the fourth century took for Achilles' tomb — but OSM's name is a different tradition. **Do not adopt without checking.** |
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
