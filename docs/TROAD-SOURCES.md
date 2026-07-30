# Drawing Troy and the Troad: source base, evidence, and citations

**Date:** 2026-07-28

**What this is:** a SOURCE dossier — facts, coordinates, tiers, and citations assembled
so we can draw our own maps of Troy and the Troad. It is **not site copy.** Nothing here
is written for a reader; it is written for the agent who builds the gazetteer and the
agent who draws the SVG.

**Copyright warning:** the copyrighted works listed in §D (Kraft et al. 1980 and 2003,
Kayan 2003 and 2019, Cook 1973, Luce 1998, Rose 2014, Rose & Körpe 2016, Studia Troica)
are cited here **as sources only.** Their maps, plates, and figures must **never be traced,
reproduced, or redrawn line-for-line.** Facts (shoreline positions, dates, elevations,
borehole results) are not copyrightable and may be re-expressed in our own drawing on our
own base; the expression in their figures is protected and is off limits.

---

## Open questions for John (human-gated)

Five decisions on existing records in `build/dist/places.json` that this dossier
disagrees with. All five are judgement calls, not mechanical fixes.

1. **`callicolone` coordinates** — currently `[39.96, 26.28]`, but the note itself cites
   Cook 1973 as *tentative*. A tentative identification should not carry a hard point.
   Recommend `null` plus note, or a visibly fuzzy marker.
2. **`thymbra` coordinates** — currently `[39.9, 26.33]`. Pleiades (550927) states its own
   point is a *rough rectangle centroid* (26.0–26.5 E, 39.5–40.0 N) reflecting scholarly
   uncertainty, and the ancient sources disagree whether Thymbra was a *polis*, a *topos*,
   or a *pedion*. Recommend anchoring to the Thymbrios–Scamander confluence and labelling
   it a district, not a dot.
3. **`lyrnessus` coordinates** — currently `[39.4, 26.85]`, while Pleiades 550703 gives
   39.508 / 27.082 — and even that is a Barrington 1:500,000 *representative* point, not a
   site. Pleiades 652355 is a second, explicitly *unlocated* Lyrnessos. Two disagreeing
   uncited numbers are worse than `null`.
4. **`simoeis` tier** — currently `certain`. The river is certain; the identification of
   Homer's Simoeis with the Dümrek Su is a Strabonic tradition that modern topographers
   accept. Recommend `traditional`, with the tradition named.
5. **`washing-troughs` tier** — currently `traditional`. Given the 2020 hydrochemical survey
   finding no hot spring *sensu Homer* anywhere near Troia, `speculative` is the honest tier.

---

## Scope note and one thing to fix first

The repo already ships a `troad` map layer: 22 places in `build/dist/places.json` (`troy`,
`scamander`, `simoeis`, `ida`, `tenedos`, `imbros`, `samothrace`, `lemnos`, `chryse`,
`cilla`, `thebe-hypoplacia`, `lyrnessus`, `pedasus-troad`, `abydos`, `sestos`, `hellespont`,
`batieia`, `callicolone`, `thymbra`, `dardania`, `zeleia`, `washing-troughs`). Everything
below is additive to that, but **four existing records disagree with the sources and should
be reviewed before they get drawn onto a detailed map** — see §E.

All Iliad line references below were verified by grep against the local Greek corpus
(`build/dist/iliad/book-*.json`), not from memory. Where I could not verify a coordinate I
have written `null` and said why.

---

## (A) Bronze-Age paleogeography of the Trojan plain

### The core result

Troy did not sit 6 km inland, as it does today. It sat at the head of a marine embayment
that has since been filled by the Scamander (Karamenderes) and Simoeis (Dümrek Su).

The foundational study is Kraft, Kayan, and Erol in *Science* (1980). Their abstract states:
at maximum Holocene transgression a marine embayment extended **c. 10 km south of Hisarlık**;
as sea level stabilised c. 6000 BP, deltaic progradation drove the delta and floodplain
northward past the site toward the **present coast about 6 km north of Hisarlık**. Their
conclusion, in their own framing: if the Trojan War happened, **the battlefield lay to the
south and west of the city** — not on the ground north of it that most modern illustrations
use.

İlhan Kayan's coastal work refines it and gives a different (not contradictory) measure: the
Holocene ria-type "Troian Bay" intruded **c. 17 km up the lower Karamenderes valley** at
c. 7000–6000 BP; progradation brought the coastline **west of Troia by c. 4000 BP**; and in
the Late Bronze Age a relative sea-level fall of **2–2.5 m** turned the remaining water body
into a **shallow lagoon separated from the open sea by a wide sandy barrier**, with swamp
over much of the delta plain throughout.

**Be careful not to conflate the two numbers.** Kraft's "10 km" is measured south from
Hisarlık at maximum transgression; Kayan's "17 km" is measured inland from the *present*
coast. They are consistent; a map legend that quotes one as if it were the other will be
wrong.

### The shoreline trace we can defend

- **Modern coast:** roughly 6 km north of Hisarlık, at Kumkale, with the Karamenderes mouth
  near 40.02 N / 26.19 E.
- **c. 1200 BC (LBA):** open water/lagoon reached considerably further south than today, but
  **not** to the foot of Hisarlık. The consensus reconstruction puts the LBA shoreline
  north-northwest of Troy, with a shallow lagoon behind a barrier — Troy overlooking a
  wetland, a lagoon, and a distant sea rather than a deep-water bay. Kraft, Rapp, Kayan, and
  Luce (*Geology*, 2003) mapped this as a sequence over six millennia and used the
  paleoenvironments explicitly to "specify areas that could have served as harbors for
  ancient Troy and for the Greek camp."
- **What the literature does NOT give us:** a published coordinate string for the 1200 BC
  shoreline. Every reconstruction is a figure in a copyrighted paper. **We can legitimately
  redraw the shoreline from the facts** (positions, dates, elevations, borehole logs) — facts
  are not copyrightable — **but we must not trace their figure.** If we want a defensible
  line, the honest approach is to draw a *band* rather than a line and label it "approximate;
  after Kraft et al. 1980, 2003 and Kayan 2003, 2019," with a note that the exact 1200 BC
  position is uncertain to on the order of a kilometre.

### The harbour question

- **Beşik Bay** (SW of Troy, opening to the Aegean past Tenedos) was excavated by Korfmann
  1982–87. He found a cemetery of c. 100 graves below Beşik Tepe with a strikingly high
  proportion of Mycenaean/Mycenaeanising LH IIIB fine ware (~1/3 of fine wares, against <1%
  in the Troia VI/VII levels). By LH IIIB the Troian bay had silted enough that a Beşik
  harbour would have been useful. This is the strongest archaeological candidate for a
  working LBA port.
- **The "Bay of Troy"/Kesik basin** hypothesis (Zangger; Jablonka and Kayan on water
  engineering) proposes cutting a naval station through the 40 m Yeniköy ridge at Kesik.
  **This is contested and thinly evidenced** — sedimentation patterns are ambiguous and
  diagnostic artefacts are absent. Flag it as a hypothesis, not a finding. **Corrected
  2026-07-29:** the c. 330 × 230 m rectangular basin cited in earlier drafts of this note is
  not at Kesik — that figure belongs to the paper's Pylos analogy (the Port of Nestor, beside
  the Osmanağa lagoon), from which the Troy hypothesis is generalised; no basin of that size
  is claimed at Kesik itself (Zangger and Mutlu 2015, 557–58, 565, 568–69).
- **For the Homeric camp specifically**, the poem itself is decisive on shape if not on
  place: *Il.* 14.30–36 says the ships were drawn up "on the shore of the grey sea," in rows
  (προκρόσσας), because the beach, wide as it was, could not hold them all, and they "filled
  the whole long mouth of the shore, as much as the headlands enclosed" (ἠϊόνος στόμα μακρόν,
  ὅσον συνεέργαθον ἄκραι, 14.36). **A beach between two headlands** is what we must draw. The
  traditional headlands are Sigeion and Rhoiteion; that identification is post-Homeric
  (Strabo), not Homeric — neither name occurs in the Iliad.

---

## (B) The named features — see the JSON block at the end

Records follow the schema specified in the brief. Highlights and the judgement calls:

**Which level is "Homer's Troy."** Dörpfeld (1902) argued Troy VI, on the strength of the
Mycenaean-scale citadel walls and the fire traces. Blegen (Cincinnati, 1932–38) reassigned
VIh's destruction to an earthquake and made **Troy VIIa** the Homeric city, destroyed by fire
c. 1190–1180 with arrowheads and sling stones in the destruction layer. Korfmann's team
(1988–2005) broadly confirmed the split: earthquake at VIh, human destruction at VIIa;
Mountjoy's pottery puts the VIh event near 1300. Frank Kolb (AJA 2004) attacked Korfmann's
reconstruction of a large lower city and of Troy as a trading centre; Jablonka and Rose
answered in the same issue. **Both AJA papers are open access** — good, citable, linkable.

**The two springs (22.147–56) are the sharpest philological problem on the map.** Homer
describes twin springs of the Scamander, one steaming hot, one ice-cold, with broad stone
washing-troughs beside them, on the wagon-road that Achilles and Hector run past. There is no
such pair at Hisarlık, and travellers have hunted for it since the 1st c. BC. The 2020
hydrochemical survey (Wolkersdorfer, Stadler et al., in *CATENA* 200 (2021): 105070) measured candidate
springs and concluded flatly that **there is no indication of a hot spring *sensu Homer* near
modern Troia**; the springs locals call "hot and cold" hold nearly constant temperature
(±0.1–0.3 K), so they *feel* warm in winter and cold in summer. Their proposal: Homer may
describe one spring perceived two ways across the seasons. That is a genuinely useful,
citable modern result, and it is the honest thing to put on the map — a labelled absence, not
an invented dot.

**The Achaean wall and ditch (7.436–41; 9.349–50) leave no trace, by design.** The poem itself
provides for its erasure: Poseidon and Apollo turn the eight Idaean rivers against it after
the war (12.17–24). Aristotle's remark, preserved in Strabo 13.1.36 — that the poet who built
it also made it disappear — is the ancient acknowledgement that it was never findable. Draw
it as a dashed, explicitly literary feature.

**The camp layout is well specified by the text and unlocatable on the ground.** Odysseus's
ship lies in the middle, so a shout carries both ways; Ajax at one end, Achilles at the other,
both hauled up ἔσχατα (8.222–26 = 11.5–9, verbatim repetition). The assembly and law-place
with the gods' altars is by Odysseus's ships (11.806–8). That gives us an orderable
schematic — Ajax / … / Odysseus + agora + altars / … / Achilles — which is exactly what a
Landmark-style camp diagram needs, and it is textually certain even though the beach it sat
on is not.

**Sigeion and Rhoiteion do not appear in the Iliad.** Verified by grep: zero hits. They are
Strabonic/Hellenistic geography imported into the Homeric map. Label them as later reference
points, not Homeric places.

**The tumuli.** Rose and Körpe's survey work is the modern authority, and their finding is
deflationary: several of the mounds traditionally shown as hero tombs are **settlement
mounds** of Neolithic-to-Bronze-Age date, not tumuli at all. Meanwhile the mounds that *are*
tumuli are largely Hellenistic and Roman — Üvecik Tepe is the tomb of Festus, a favourite of
Caracalla (r. 211–17), the largest in the Troad after its construction; Kesik Tepe near
Sigeion is the one that was *regarded* as Achilles' tomb in the 4th century, where Alexander
is said (Arrian, *Anabasis*) to have sacrificed. **Every "tomb of Achilles" on the Troad is a
cult identification, not a burial.** That is a `traditional` tier with the tradition named,
never `certain`.

---

## (C) The spatial layout — the standard reconstruction and the dissent

### The standard reconstruction

1. **City on a rise at the southeast**: Hisarlık, a low spur at the end of a ridge,
   overlooking the plain to its west and north; citadel (Pergamos) on the mound, lower city
   extending south and southeast.
2. **Plain between**, the Scamandrian plain (2.465, 2.467), crossed by a wagon-road
   (ἀμαξιτός, 22.146) running out from the Scaean Gate past the springs, the fig tree, and
   the lookout.
3. **Camp on the shore to the northwest**, ships in rows filling a beach closed by headlands
   (14.31–36), wall and ditch on the landward side (7.436–41).
4. **Rivers on the flanks**: Scamander/Xanthus down the west, Simoeis coming in from the
   northeast, joining somewhere on the plain (5.774) — the confluence being the standard
   divine landmark. A ford (πόρος, 14.433, 21.1, 24.692) is where the road crosses.
5. **Intermediate landmarks strung along the road**: tomb of Ilos (10.415, 11.166, 11.371,
   24.349) roughly mid-plain, the fig tree and lookout close under the wall, Batieia/tomb of
   Myrine "before the city" as the Trojan mustering ground (2.811–15), the tomb of Aesyetes
   as the Trojan watch-post facing the ships (2.792–94).
6. **Callicolone** near the Simoeis as the pro-Trojan gods' grandstand (20.53, 20.151),
   balancing the Achaean wall where the pro-Greek gods sit (20.144–48).

Luce (1984, 1998) is the fullest and most confident defence: he argues Homer's landscape is
accurate in every detail, integrates the geophysical alluviation data and Korfmann's enlarged
city, and traces the ebb and flow of the battle across the reconstructed plain. Kraft, Rapp,
Kayan, and Luce (2003) is the geological arm of the same case, and its title is the argument:
sedimentology and geomorphology "complement Homer's Iliad."

### The dissent — and it should be on the page

The opposing position is that the Iliad's Troad is **a poetic construction, not a survey**.
Hainsworth, in the Cambridge commentary (vol. III, Books 9–12, 1993), takes the view that
except in the most general terms the epic geography of the Troad is clearly a poetical
construction. *(Caveat: I have this at second hand from a secondary discussion and could not
verify the page in the print volume. Verify before quoting it on the site.)*

The dissenters' strongest cards are:

- The **two springs simply are not there**, and no amount of alluviation explains it — springs
  would not vanish. The 2020 hydrochemistry closes the last escape route.
- The **wall and ditch are self-erasing** in the poem, an ancient admission (Aristotle *ap.*
  Strabo 13.1.36).
- Some landmarks are **narrative furniture**: they appear exactly when the action needs a
  waypoint (the oak, the fig tree, the lookout, all three clustered on the chase-route of
  Book 22) and never otherwise.
- **Alexandrian and Roman-era "identifications"** — of Ilos's tomb, of Achilles' tomb, of the
  Scaean Gate — are tourist-industry constructions retrofitted to a mound-strewn plain, not
  survivals.

There is also the **Kolb/Korfmann controversy** (2001–04), which is not about topography but
bears on how grand a city we draw: Kolb held that Troy VI was not a commercial city and
cannot be shown to have been a city at all, the lower city and its ditch not surviving
scrutiny; Jablonka and Rose replied. If our map draws Korfmann's lower-city circuit, the
caption must say whose reconstruction it is.

**Recommendation for the site:** draw two registers rather than one. A **geographical map**
(real, coordinated, coastline-reconstructed, only defensible features) and a **schematic
diagram** (the poem's own spatial logic — camp / plain / city, ships in order, road with its
waypoints) with the schematic explicitly labelled as the poem's mental map. That structure is
honest about exactly the split the scholarship is arguing over, and it lets us show the Book
22 chase and the Book 8–11 camp order without pretending we know where the fig tree stood.

---

## (D) Licensing

### Public domain in the US (pre-1931), safe to reproduce or trace

| Source | Why PD | Where |
|---|---|---|
| **Spratt & Graves, Admiralty chart of the Dardanelles and the Troad**, surveyed 1839–40, published 1844 | Pre-1931 publication; UK Crown copyright long expired | Commercially scanned copies widely available; [Wikimedia Commons: T. A. B. Spratt](https://commons.wikimedia.org/wiki/Category:Thomas_Abel_Brimage_Spratt). **Historically the most important Troad map** — it is what led Calvert and Schliemann to Hisarlık, and it plots both candidate Troys (Hisarlık = "Ilium Novum", Bunarbashi = "Ilium Vetus"). Excellent for a "how Troy was found" panel. |
| **Dörpfeld, *Troja und Ilion* (Athens, 1902)**, 2 vols, 76 plates | Pre-1931 | [vol. 1](https://archive.org/details/trojaundilionerg00drpf), [vol. 2](https://archive.org/details/trojaundilionerg02dorp); also Heidelberg digi.ub. Includes the great citadel plan and Brückner's topographical/geological treatment of the plain — **the single best PD source for the Troy VI fortification plan.** |
| **Schliemann, *Ilios* (1880/81) and *Troja* (1884)** | Pre-1931 | archive.org |
| **Leaf, *Troy: A Study in Homeric Geography* (Macmillan, 1912)**, with maps and plans | Pre-1931 | [archive.org](https://archive.org/details/troyastudyinhom00leafgoog). The classic topographic argument; his maps are traceable. |
| **Leaf, *Strabo on the Troad* (CUP, 1923)** | Pre-1931 | Text + maps; the standard PD treatment of the ancient geography |
| **Choiseul-Gouffier, *Voyage pittoresque de la Grèce* (1782–1822)** | Pre-1931 | Handsome 18th-c. plans of the plain; period flavour |
| **Kiepert, 19th-c. maps of the Troad** | Pre-1931 | |
| **Strabo, *Geography* 13.1** (Greek + Jones trans.) | Text PD | [Perseus](https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0198:book%3D13:chapter%3D1) — the source for nearly every `traditional` identification below |

### In copyright — cite as sources, never reproduce the figures

- **Kraft, Kayan & Erol 1980** (*Science*, AAAS) — figures © AAAS
- **Kraft, Rapp, Kayan & Luce 2003** (*Geology*, GSA) — the paleogeographic map series © GSA
- **Kayan 2003, 2019** (Springer chapters)
- **Cook, *The Troad* (Clarendon, 1973)** — maps in copyright; [borrowable scan](https://archive.org/details/troadarchaeologi0000cook) is *lending*, not PD
- **Luce, *Celebrating Homer's Landscapes* (Yale, 1998)**
- **Rose, *The Archaeology of Greek and Roman Troy* (CUP, 2014)**; **Rose & Körpe 2016** (De Gruyter)
- **Studia Troica** (Korfmann excavation reports)

### Openly licensed data we can build on

- **Pleiades** — CC-BY 3.0. Coordinates, place IDs, and "unlocated" flags are reusable with
  attribution. Most of the coordinates in the JSON below come from here and are already the
  repo's convention.
- **Vici.org** — CC-BY-SA. Useful for tumulus points, but see the warning on the Ajax record.
- **AJA open-access PDFs** — [Kolb 2004](https://ajaonline.org/wp-content/uploads/2012/11/1084_Kolb.pdf),
  [Jablonka & Rose 2004](https://ajaonline.org/wp-content/uploads/2012/11/1084_Jablonka.pdf).
  Directly linkable.
- **OSM / SRTM** for modern terrain and hydrology under their own terms.

### The principle to write into the data

The **facts** in a copyrighted geoarchaeological figure — a shoreline position, a date, a
borehole depth — are not protected. The **expression** is. We may state "the LBA shoreline
lay approximately here, after Kraft et al. 2003" and draw our own line on our own base; we
may not trace their line off their plate. Every derived feature in our SVG should carry, in
the data, the citation of the study whose *facts* it encodes.

---

## (E) Four existing records to review before drawing

1. **`callicolone` has `coords: [39.96, 26.28]`** with the note citing Cook 1973 as
   "tentative." A tentative identification should not carry a hard point. Recommend `null` +
   note, or a visibly fuzzy marker.
2. **`thymbra` has `coords: [39.9, 26.33]`.** Pleiades (550927) explicitly states its point is
   a *rough rectangle centroid* (26.0–26.5 E, 39.5–40.0 N) reflecting scholarly uncertainty,
   and ancient sources disagree whether Thymbra was a *polis*, a *topos*, or a *pedion*.
   Recommend anchoring to the Thymbrios (Kemer Su)–Scamander confluence and labelling it a
   district, not a dot.
3. **`lyrnessus` has `coords: [39.4, 26.85]`** while Pleiades 550703 gives 39.508 / 27.082 —
   and even that is a Barrington 1:500,000 *representative* point, not a site. There is also
   a second, explicitly *unlocated* Lyrnessos in Pleiades (652355). Two different numbers with
   no cited basis is worse than `null`.
4. **`simoeis` is tiered `certain`.** The river is certain; the identification of Homer's
   Simoeis with the Dümrek Su is a Strabonic tradition that modern topographers accept.
   `traditional` with the tradition named is the more defensible tier. Same argument, more
   weakly, for `washing-troughs`, currently `traditional` — given the 2020 hydrochemistry,
   `speculative` is the honest tier.

---

```json
[
  { "id": "troy-ilios", "greek": "Ἴλιος / Τροίη", "translit": "Ilios / Troiē", "english": "Troy", "tier": "certain", "lat": 39.9575, "lon": 26.2389, "kind": "city", "iliad_refs": ["1.129", "20.216-217", "22.6"], "note": "The mound of Hisarlık, excavated since Schliemann 1870. Which level is 'Homer's Troy' is the live question: Dörpfeld argued Troy VIh (destroyed c.1300, now generally read as earthquake damage); Blegen argued Troy VIIa (violent fire destruction c.1190-1180, with arrowheads and sling stones in the debris), and Korfmann's team broadly confirmed that split. The site identification is certain; the level is not.", "tradition": null, "citations": ["Dörpfeld, Wilhelm. Troja und Ilion: Ergebnisse der Ausgrabungen in den vorhistorischen und historischen Schichten von Ilion, 1870–1894. 2 vols. Athens: Beck & Barth, 1902.", "Rose, C. Brian. The Archaeology of Greek and Roman Troy. Cambridge: Cambridge University Press, 2014.", "https://pleiades.stoa.org/places/550595"] },

  { "id": "pergamos", "greek": "Πέργαμος", "translit": "Pergamos", "english": "The citadel of Troy", "tier": "traditional", "lat": 39.9575, "lon": 26.2389, "kind": "other", "iliad_refs": ["4.508", "5.446", "5.460", "6.512", "7.21", "24.700"], "note": "Homer's word for Troy's acropolis, where Apollo's temple stands (5.446) and from which he and Ares survey the fighting. Given the certain Hisarlık identification, Pergamos is the excavated citadel mound; but the equation is an inference from the poem, not an excavated label.", "tradition": "Standard equation of Homeric Pergamos with the Hisarlık citadel, from Dörpfeld onward", "citations": ["Dörpfeld, Wilhelm. Troja und Ilion. 2 vols. Athens: Beck & Barth, 1902."] },

  { "id": "troy-lower-city", "greek": null, "translit": null, "english": "The lower city of Troy", "tier": "traditional", "lat": null, "lon": null, "kind": "other", "iliad_refs": [], "note": "Not named as such by Homer. Korfmann's magnetometry and excavation from 1988 argued for a substantial lower city south of the citadel with a defensive ditch, making Troy VI roughly ten times the previously assumed area — a claim Luce relies on. Frank Kolb argued the evidence does not bear scrutiny and Troy VI cannot be shown to have been a city at all; Jablonka and Rose replied. If drawn, the circuit must be captioned as Korfmann's reconstruction.", "tradition": "Manfred Korfmann and the Tübingen Troia project, 1988–2005", "citations": ["Kolb, Frank. \"Troy VI: A Trading Center and Commercial City?\" American Journal of Archaeology 108, no. 4 (2004): 577–614. https://ajaonline.org/wp-content/uploads/2012/11/1084_Kolb.pdf", "Jablonka, Peter, and C. Brian Rose. \"Late Bronze Age Troy: A Response to Frank Kolb.\" American Journal of Archaeology 108, no. 4 (2004): 615–30. https://ajaonline.org/wp-content/uploads/2012/11/1084_Jablonka.pdf"] },

  { "id": "wall-of-troy", "greek": "τεῖχος", "translit": "teichos", "english": "The wall of Troy", "tier": "certain", "lat": 39.9575, "lon": 26.2389, "kind": "other", "iliad_refs": ["7.452-453", "21.446-447", "6.434"], "note": "The Troy VI fortification circuit survives and is planned in Dörpfeld 1902 — this is one of the few Homeric features with a real, drawable footprint. In the poem Poseidon built it for Laomedon (21.446-447) 'wide and very fair, so that the city should be unbreachable'; Apollo herded his cattle on Ida meanwhile. Andromache says the wall is scalable at one point, by the fig tree (6.433-434).", "tradition": null, "citations": ["Dörpfeld, Wilhelm. Troja und Ilion. 2 vols. Athens: Beck & Barth, 1902."] },

  { "id": "scaean-gate", "greek": "Σκαιαὶ πύλαι", "translit": "Skaiai pylai", "english": "The Scaean Gate", "tier": "speculative", "lat": null, "lon": null, "kind": "gate", "iliad_refs": ["3.145", "3.149", "6.237", "6.393", "9.354", "11.170", "16.712", "18.453", "22.6", "22.360"], "note": "The gate of the poem: the elders sit above it with Helen (3.145-149), Hector meets Andromache going out through it (6.393), the fighting rages round it all day (18.453), and Hector prophesies Achilles' death in it (22.360). It is always paired with the oak (6.237, 9.354, 11.170). Candidates at Hisarlık are Troy VI's South Gate (VI T) and the West/Southwest gate; there is no consensus, and the South Gate is at least as often identified with the Dardanian Gate. Do not place a point.", "tradition": null, "citations": ["Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973.", "Dörpfeld, Wilhelm. Troja und Ilion. 2 vols. Athens: Beck & Barth, 1902."] },

  { "id": "dardanian-gates", "greek": "πύλαι Δαρδάνιαι", "translit": "pylai Dardaniai", "english": "The Dardanian Gates", "tier": "speculative", "lat": null, "lon": null, "kind": "gate", "iliad_refs": ["5.789", "22.194", "22.413"], "note": "A second named gate, three times mentioned; Hector keeps trying to dart toward it during the chase (22.194) and Priam is barely restrained from going out through it (22.413). Sometimes identified with Troy VI's South Gate (VI T), on the reasoning that Dardania lay to the southeast. Whether Homer means a distinct gate or an alternative name for the Scaean Gate is disputed.", "tradition": null, "citations": ["Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973."] },

  { "id": "great-tower-of-ilios", "greek": "πύργος μέγας Ἰλίου", "translit": "pyrgos megas Iliou", "english": "The great tower of Ilios", "tier": "speculative", "lat": null, "lon": null, "kind": "other", "iliad_refs": ["3.153-154", "3.384", "6.373", "6.386", "6.431", "21.526", "22.97", "22.447"], "note": "The vantage point of the poem's civilian scenes: the elders and Helen on it (3.153-154), Andromache running to it (6.386), Priam standing on it as Achilles drives the Trojans in (21.526), Hector setting his shield against it (22.97, 'the jutting tower'). Structurally it belongs with the Scaean Gate; no specific tower at Hisarlık is securely identified with it.", "tradition": null, "citations": ["Leaf, Walter. Troy: A Study in Homeric Geography. London: Macmillan, 1912. https://archive.org/details/troyastudyinhom00leafgoog"] },

  { "id": "oak-of-zeus", "greek": "φηγός", "translit": "phēgos", "english": "The oak tree", "tier": "speculative", "lat": null, "lon": null, "kind": "tree", "iliad_refs": ["5.693", "6.237", "7.22", "7.60", "9.354", "11.170", "21.549"], "note": "Formulaically bound to the Scaean Gate ('the Scaean Gates and the oak', 6.237 = 9.354 = 11.170). Sarpedon is laid under 'the beautiful oak of aegis-bearing Zeus' (5.693); Athena and Apollo meet beside it (7.22) and perch in it as vultures (7.60); Agenor leans against it (21.549). A living landmark just outside the gate, unlocatable by definition.", "tradition": null, "citations": ["Luce, J. V. Celebrating Homer's Landscapes: Troy and Ithaca Revisited. New Haven: Yale University Press, 1998."] },

  { "id": "fig-tree", "greek": "ἐρινεός", "translit": "erineos", "english": "The wild fig tree", "tier": "speculative", "lat": null, "lon": null, "kind": "tree", "iliad_refs": ["6.433", "11.167", "22.145"], "note": "A tactical landmark: Andromache tells Hector to post the army by the fig tree, 'where the city is most scalable and the wall assailable' (6.433-434), the Achaean champions having tried there three times. It lies on the wagon-road out of the city (11.167, 22.145, 'the windy fig tree'). Note that the ἐρινεός of 21.37, where Achilles catches Lycaon cutting branches, is by the river and is probably a different tree.", "tradition": null, "citations": ["Luce, J. V. \"The Homeric Topography of the Trojan Plain Reconsidered.\" Oxford Journal of Archaeology 3, no. 1 (1984).", "Leaf, Walter. Troy: A Study in Homeric Geography. London: Macmillan, 1912."] },

  { "id": "lookout-skopie", "greek": "σκοπιή", "translit": "skopiē", "english": "The lookout point", "tier": "speculative", "lat": null, "lon": null, "kind": "other", "iliad_refs": ["22.145"], "note": "Named once, paired with the fig tree on the chase-route: 'past the lookout and the windy fig tree, always out from under the wall, along the wagon-road' (22.145-146). Whether a natural rise or a built watch-post is not said. Distinct from the tomb of Aesyetes, the Trojan watch-post of 2.793.", "tradition": null, "citations": ["Luce, J. V. Celebrating Homer's Landscapes: Troy and Ithaca Revisited. New Haven: Yale University Press, 1998."] },

  { "id": "wagon-road", "greek": "ἀμαξιτός", "translit": "hamaxitos", "english": "The wagon-road", "tier": "speculative", "lat": null, "lon": null, "kind": "other", "iliad_refs": ["22.146"], "note": "The road running from the Scaean Gate out across the plain, past the lookout, the fig tree, and the springs — the track Achilles and Hector run three times around the city. The single most useful organising line for a schematic map of the plain, and the one feature the chase demands but no survey can fix.", "tradition": null, "citations": ["Luce, J. V. Celebrating Homer's Landscapes: Troy and Ithaca Revisited. New Haven: Yale University Press, 1998."] },

  { "id": "two-springs-of-scamander", "greek": "κρουνὼ καλλιρρόω", "translit": "krounō kallirroō", "english": "The two fair-flowing springs of the Scamander", "tier": "speculative", "lat": null, "lon": null, "kind": "spring", "iliad_refs": ["22.147-152", "22.208"], "note": "Twin springs, one running warm with steam rising 'as from a burning fire', the other cold as hail or snow or ice even in summer (22.149-152). No thermal pair in the strict sense exists at or near Hisarlık, and travellers have hunted since the 1st century BC (numerous springs DO qualify in Homer's relative sense, λιαρός = lukewarm — the identification fails from a surplus of candidates, not an absence; aligned 2026-07-30 with apparatus/places.json and RESEARCH-TROAD-TOPOGRAPHY.md §6). The hydrochemical survey (field campaigns 2001-2006, published 2021) found four springs with elevated geothermometric reservoir temperatures; thermal scalings were absent, though the survey separately reports up to 10 m of calcite sinter terraces at Kemerdere/Civlar and travertine at most Ca-HCO3 discharge points, mineralogically distinct from the deposits at the region's real thermal springs (correction dated 2026-07-30, per RESEARCH-TROAD-TOPOGRAPHY.md §6.6). The survey concluded there is no thermal spring in the STRICT sense near modern Troia (its own p. 3 distinction — Homer's sense is the relative one many springs meet); springs locally called 'hot and cold' vary by only ±0.1–0.3 K, i.e. they feel warm in winter and cold in summer. The authors propose Homer describes one spring perceived two ways across the seasons. This is the strongest single piece of evidence for the 'poetic construction' view of the Troad.", "tradition": null, "citations": ["Wolkersdorfer, Christian, et al. \"Hydrochemical investigations to locate Homer's hot and cold springs of Troia (Troy)/Turkey.\" CATENA 200 (2021): 105070. https://doi.org/10.1016/j.catena.2020.105070", "https://www.livius.org/articles/place/scamander/"] },

  { "id": "washing-troughs", "greek": "πλυνοὶ εὐρέες", "translit": "plynoi eurees", "english": "The broad washing-troughs", "tier": "speculative", "lat": null, "lon": null, "kind": "other", "iliad_refs": ["22.153-156"], "note": "'Broad washing-troughs, fine ones of stone, where the wives and fair daughters of the Trojans used to wash their shining clothes, in the time of peace before the sons of the Achaeans came.' Attached to the two springs, and unlocatable with them. One of the poem's great images of the lost civilian world; a labelled absence on a map is more honest than a dot.", "tradition": null, "citations": ["Wolkersdorfer, Christian, et al. \"Hydrochemical investigations to locate Homer's hot and cold springs of Troia (Troy)/Turkey.\" CATENA 200 (2021): 105070. https://doi.org/10.1016/j.catena.2020.105070"] },

  { "id": "tomb-of-ilos", "greek": "σῆμα Ἴλου", "translit": "sēma Ilou", "english": "The tomb of Ilus", "tier": "speculative", "lat": null, "lon": null, "kind": "tomb", "iliad_refs": ["10.415", "11.166", "11.371-372", "24.349"], "note": "Barrow of 'ancient Ilus son of Dardanus' out on the plain: Hector holds council beside it away from the din (10.415), the routed Trojans stream past it (11.166), Paris shoots Diomedes from behind its grave-stele (11.371-372), and Priam's wagon passes it on the way to the ships (24.349). Its position — between city and camp, near the road, with a standing stele — is well fixed narratively and not at all archaeologically. Strabo 13.1.36-37 already discusses the plain's tombs as identification problems.", "tradition": null, "citations": ["Leaf, Walter. Troy: A Study in Homeric Geography. London: Macmillan, 1912.", "Rose, C. Brian, and Reyhan Körpe. \"The Tumuli of Troy and the Troad.\" In Tumulus as Sema, edited by Olivier Henry and Ute Kelp. Berlin: De Gruyter, 2016."] },

  { "id": "tomb-of-aesyetes", "greek": "τύμβος Αἰσυήταο", "translit": "tymbos Aisyētao", "english": "The barrow of old Aesyetes", "tier": "speculative", "lat": null, "lon": null, "kind": "tomb", "iliad_refs": ["2.792-794"], "note": "The Trojan watch-post: Polites sits on its summit 'trusting in his swiftness of foot, waiting for when the Achaeans should set out from the ships' (2.793-794). Its function fixes its position — high enough to see the camp, close enough to the city to run back — but no mound is securely identified with it.", "tradition": null, "citations": ["Leaf, Walter. Troy: A Study in Homeric Geography. London: Macmillan, 1912."] },

  { "id": "batieia", "greek": "Βατίεια", "translit": "Batieia", "english": "Batieia, the barrow of Myrine", "tier": "speculative", "lat": null, "lon": null, "kind": "hill", "iliad_refs": ["2.811-815"], "note": "'There is before the city a steep mound out in the plain, standing clear with a way round it on either side, which men call Batieia but the immortals the barrow of much-leaping Myrine' (2.811-814) — the Trojan mustering ground where the contingents form up. The double naming (men's name / gods' name) is the poem's marker for genuinely old material. No surviving mound is securely matched to it.", "tradition": "Discussed among the tombs of the plain since Strabo 13.1.36-37; no ancient or modern survey, including Leaf 1912, matches a surviving mound to it", "citations": ["Leaf, Walter. Troy: A Study in Homeric Geography. London: Macmillan, 1912.", "Strabo, Geography 13.1.36-37. https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0198:book%3D13:chapter%3D1"] },

  { "id": "callicolone", "greek": "Καλλικολώνη", "translit": "Kallikolōnē", "english": "Callicolone, 'Fair Hill'", "tier": "speculative", "lat": null, "lon": null, "kind": "hill", "iliad_refs": ["20.53", "20.151"], "note": "A rise beside the Simoeis where Ares rallies the Trojans (20.53) and the pro-Trojan gods take their seats (20.151), balanced against the Achaean wall where the pro-Greek gods sit (20.144-148). Cook proposed a ridge east of Troy near the Simoeis, tentatively. Recommend no hard coordinate. NOTE: the repo's places.json currently gives [39.96, 26.28] for a tentative identification — review.", "tradition": "A ridge east of Troy near the Simoeis (J. M. Cook, tentative)", "citations": ["Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973."] },

  { "id": "scamander-xanthus", "greek": "Σκάμανδρος / Ξάνθος", "translit": "Skamandros / Xanthos", "english": "The Scamander, called Xanthus by the gods", "tier": "certain", "lat": null, "lon": null, "kind": "river", "iliad_refs": ["2.465", "5.36", "12.21", "20.73-74", "21.1-2", "21.223", "21.305", "22.148"], "note": "The principal river of the plain, modern Karamenderes. Homer gives it both names explicitly: 'which the gods call Xanthus, but men Scamander' (20.74). Its god fights Achilles through Book 21. Draw as a line, not a point: the modern channel is not the Bronze Age channel, which lay further west and discharged into the then-open embayment. The mouth is now near 40.02 N / 26.19 E.", "tradition": null, "citations": ["Kayan, İlhan. \"Landscape Development and Changing Environment of Troia (North-western Anatolia).\" In Landscapes and Landforms of Turkey, edited by Catherine Kuzucuoğlu, Attila Çiner, and Nizamettin Kazancı, 277–91. Cham: Springer, 2019.", "https://pleiades.stoa.org/places/550871"] },

  { "id": "simoeis", "greek": "Σιμόεις", "translit": "Simoeis", "english": "The Simoeis", "tier": "traditional", "lat": null, "lon": null, "kind": "river", "iliad_refs": ["4.475", "5.774", "5.777", "6.4", "12.22", "20.53", "21.307"], "note": "The Scamander's partner river, coming down from Ida; the fighting on the plain is bounded 'between the streams of Simoeis and Xanthus' (6.4). Standardly identified with the Dümrek Su, on Strabo's authority and modern topography — a tradition, not an excavated fact. NOTE: the repo currently tiers this 'certain'; 'traditional' is the more defensible call.", "tradition": "Identification with the Dümrek Su, following Strabo 13.1 and accepted by Leaf, Cook, and Luce", "citations": ["Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973.", "https://pleiades.stoa.org/places/550883"] },

  { "id": "scamander-simoeis-confluence", "greek": null, "translit": null, "english": "The confluence of Simoeis and Scamander", "tier": "speculative", "lat": null, "lon": null, "kind": "river", "iliad_refs": ["5.774"], "note": "'Where the Simoeis and Scamander join their streams' (5.774) — where Hera unyokes her horses and Simoeis makes ambrosia grow for them. A real divine landmark in the poem. Its Bronze Age position cannot be fixed: the whole delta has prograded 6+ km north since, and both channels have shifted.", "tradition": null, "citations": ["Kraft, John C., George Rapp, İlhan Kayan, and John V. Luce. \"Harbor areas at ancient Troy: Sedimentology and geomorphology complement Homer's Iliad.\" Geology 31, no. 2 (2003): 163–66."] },

  { "id": "ford-of-the-scamander", "greek": "πόρος ποταμοῖο", "translit": "poros potamoio", "english": "The ford of the fair-flowing river", "tier": "speculative", "lat": null, "lon": null, "kind": "river", "iliad_refs": ["14.433", "21.1-2", "24.692-693"], "note": "A fixed crossing named by a repeated formula: 'but when they came to the ford of the fair-flowing river, eddying Xanthus, whom immortal Zeus begot' (14.433 = 21.1-2 = 24.692-693). It marks the boundary between camp-side and city-side of the plain, and Achilles splits the rout there (21.3). Position unrecoverable.", "tradition": null, "citations": ["Luce, J. V. Celebrating Homer's Landscapes: Troy and Ithaca Revisited. New Haven: Yale University Press, 1998."] },

  { "id": "scamandrian-plain", "greek": "πεδίον Σκαμάνδριον", "translit": "pedion Skamandrion", "english": "The Scamandrian plain", "tier": "certain", "lat": null, "lon": null, "kind": "plain", "iliad_refs": ["2.465", "2.467"], "note": "The battlefield: the Achaeans 'poured out onto the Scamandrian plain' and 'took their stand in the flowery Scamandrian meadow' (2.465-467). Kraft, Kayan and Erol's conclusion is that the usable plain in the Late Bronze Age lay south and west of Hisarlık, not north of it — the reverse of most popular illustrations.", "tradition": null, "citations": ["Kraft, John C., İlhan Kayan, and Oğuz Erol. \"Geomorphic Reconstructions in the Environs of Ancient Troy.\" Science 209, no. 4458 (1980): 776–82."] },

  { "id": "bay-of-troy", "greek": null, "translit": null, "english": "The Bay of Troy (the silted embayment)", "tier": "certain", "lat": null, "lon": null, "kind": "harbour", "iliad_refs": [], "note": "Not named by Homer, but the single most important thing to get right on the map. A marine embayment once extended c.10 km south of Hisarlık (Kraft/Kayan/Erol 1980); the ria intruded c.17 km up the lower Karamenderes valley at 7000–6000 BP (Kayan); progradation carried the coast west of Troia by c.4000 BP; a 2–2.5 m relative sea-level fall in the Late Bronze Age left a shallow lagoon behind a wide sandy barrier, with swamp over much of the delta. The modern coast lies c.6 km north of the site. Draw as a labelled uncertainty band, not a hard line.", "tradition": null, "citations": ["Kraft, John C., İlhan Kayan, and Oğuz Erol. \"Geomorphic Reconstructions in the Environs of Ancient Troy.\" Science 209, no. 4458 (1980): 776–82.", "Kraft, John C., George Rapp, İlhan Kayan, and John V. Luce. \"Harbor areas at ancient Troy: Sedimentology and geomorphology complement Homer's Iliad.\" Geology 31, no. 2 (2003): 163–66.", "Kayan, İlhan. \"Geoarchaeological Interpretations of the 'Troian Bay.'\" In Troia and the Troad: Scientific Approaches, edited by Günther A. Wagner, Ernst Pernicka, and Hans-Peter Uerpmann. Berlin: Springer, 2003."] },

  { "id": "achaean-camp", "greek": "κλισίαι καὶ νῆες Ἀχαιῶν", "translit": "klisiai kai nēes Achaiōn", "english": "The Achaean camp and ships", "tier": "speculative", "lat": null, "lon": null, "kind": "camp", "iliad_refs": ["8.220-226", "11.5-9", "14.30-36"], "note": "The poem's own description is precise about shape: the ships were drawn up in rows (προκρόσσας) because the beach, wide as it was, could not hold them all, and they 'filled the whole long mouth of the shore, as much as the headlands enclosed' (14.31-36). A BEACH BETWEEN TWO HEADLANDS is the requirement. The Sigeion-Rhoiteion shore is the traditional answer; Beşik Bay is the archaeological alternative. Kraft et al. 2003 explicitly used the reconstructed paleoenvironments to specify candidate areas for the Greek camp.", "tradition": null, "citations": ["Kraft, John C., George Rapp, İlhan Kayan, and John V. Luce. \"Harbor areas at ancient Troy: Sedimentology and geomorphology complement Homer's Iliad.\" Geology 31, no. 2 (2003): 163–66.", "Luce, J. V. Celebrating Homer's Landscapes: Troy and Ithaca Revisited. New Haven: Yale University Press, 1998."] },

  { "id": "achaean-wall-and-ditch", "greek": "τεῖχος καὶ τάφρος", "translit": "teichos kai taphros", "english": "The Achaean wall and ditch", "tier": "speculative", "lat": null, "lon": null, "kind": "other", "iliad_refs": ["7.435-441", "9.349-350", "12.17-24", "14.32"], "note": "Built in Book 7 round the common barrow: a wall with high towers, gates wide enough for a chariot road, and outside it a deep, wide ditch set with stakes (7.436-441). It leaves no trace, and the poem provides for that: after the war Poseidon and Apollo turn the eight Idaean rivers against it (12.17-24). Aristotle's remark preserved in Strabo 13.1.36 — that the poet who invented it made it vanish — is the ancient acknowledgement. Draw dashed and label it a literary structure.", "tradition": null, "citations": ["Strabo, Geography 13.1.36. https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0198:book%3D13:chapter%3D1", "Hainsworth, Bryan. The Iliad: A Commentary, Volume III: Books 9–12. Cambridge: Cambridge University Press, 1993."] },

  { "id": "achaean-assembly-place", "greek": "ἀγορή τε θέμις τε", "translit": "agorē te themis te", "english": "The assembly and law-place, with the gods' altars", "tier": "speculative", "lat": null, "lon": null, "kind": "camp", "iliad_refs": ["11.806-808"], "note": "Located precisely within the camp: 'when he came running to the ships of godlike Odysseus, where their place of assembly and of justice was, and where the altars of the gods had been built for them' (11.806-808). Combined with 8.222-226, this puts the civic centre of the camp at its midpoint — a fact a camp schematic can render exactly.", "tradition": null, "citations": ["Luce, J. V. Celebrating Homer's Landscapes: Troy and Ithaca Revisited. New Haven: Yale University Press, 1998."] },

  { "id": "hut-of-odysseus", "greek": "νηῦς Ὀδυσσῆος", "translit": "nēus Odyssēos", "english": "The ship and hut of Odysseus", "tier": "speculative", "lat": null, "lon": null, "kind": "camp", "iliad_refs": ["8.222-223", "11.5-6", "11.806"], "note": "At the exact middle of the line of ships — Agamemnon and Strife both stand on its deck 'to shout to either side' (8.222-223 = 11.5-6). The camp's midpoint and civic centre.", "tradition": null, "citations": [] },

  { "id": "hut-of-ajax", "greek": "κλισίαι Αἴαντος Τελαμωνιάδαο", "translit": "klisiai Aiantos Telamōniadao", "english": "The huts of Ajax son of Telamon", "tier": "speculative", "lat": null, "lon": null, "kind": "camp", "iliad_refs": ["8.224-226", "11.7-9"], "note": "One extremity of the camp; he and Achilles 'had drawn up their balanced ships at the ends, trusting in their manhood and the strength of their hands' (8.225-226 = 11.8-9). Which end is Ajax's and which Achilles' is not stated.", "tradition": null, "citations": [] },

  { "id": "hut-of-achilles", "greek": "κλισίη Ἀχιλλῆος", "translit": "klisiē Achillēos", "english": "The hut of Achilles", "tier": "speculative", "lat": null, "lon": null, "kind": "camp", "iliad_refs": ["8.225-226", "11.8-9"], "note": "The other extremity, opposite Ajax. The setting of the Embassy (Book 9) and of Priam's supplication (Book 24). Its distance from the centre is a plot device — Achilles cannot see what is happening at the ships and must send Patroclus to find out (11.599 ff.).", "tradition": null, "citations": [] },

  { "id": "hut-of-agamemnon", "greek": "κλισίη Ἀγαμέμνονος", "translit": "klisiē Agamemnonos", "english": "The hut of Agamemnon", "tier": "speculative", "lat": null, "lon": null, "kind": "camp", "iliad_refs": ["1.185", "2.402", "9.669"], "note": "The command tent, where the councils of elders meet and the returning embassy reports (9.669). Homer never fixes its position in the line of ships; it is near the centre by implication only.", "tradition": null, "citations": [] },

  { "id": "tomb-of-achilles-and-patroclus", "greek": "τύμβος", "translit": "tymbos", "english": "The barrow of Achilles and Patroclus", "tier": "speculative", "lat": null, "lon": null, "kind": "tomb", "iliad_refs": ["23.245-248"], "note": "Achilles orders a modest barrow for Patroclus now, to be made 'broad and high' later by the Achaeans who survive him (23.245-248). The Odyssey delivers the sequel: their bones mixed in one urn, with Antilochus's apart, under 'a great and faultless barrow on a jutting headland by the broad Hellespont, so as to be visible far off from the sea to men now alive and those to come' (Od. 24.80-84). Every Troad 'tomb of Achilles' is a later cult identification with a pre-existing mound, not a burial.", "tradition": null, "citations": ["Rose, C. Brian, and Reyhan Körpe. \"The Tumuli of Troy and the Troad.\" In Tumulus as Sema, edited by Olivier Henry and Ute Kelp. Berlin: De Gruyter, 2016."] },

  { "id": "tomb-of-hector", "greek": "σῆμα Ἕκτορος", "translit": "sēma Hektoros", "english": "The tomb of Hector", "tier": "speculative", "lat": null, "lon": null, "kind": "tomb", "iliad_refs": ["24.797-801"], "note": "The last thing in the poem: the bones laid in a hollow grave, covered with great close-set stones, the barrow heaped quickly with lookouts posted all round in case the Achaeans attacked (24.797-801). No location is given and none is claimed in antiquity in the Troad.", "tradition": null, "citations": [] },

  { "id": "kesik-tepe", "greek": null, "translit": null, "english": "Kesik Tepe (the 'Demetrius tumulus'), claimed tomb of Achilles", "tier": "traditional", "lat": 39.9608, "lon": 26.1682, "kind": "tomb", "iliad_refs": [], "note": "The most impressive mound on the Trojan plain, close to ancient Sigeion. In the 4th century BC it was regarded as the tomb of Achilles, and Arrian reports Alexander sacrificing to Achilles on landing near Sigeion. Coordinate is from Vici.org and has not been checked against a published survey plan — verify before publishing.", "tradition": "Fourth-century BC and later hero-cult identification with Achilles' tomb (Arrian, Anabasis 1.12)", "citations": ["https://www.livius.org/articles/place/troy/troy-5/", "https://vici.org/vici/11135/", "Rose, C. Brian, and Reyhan Körpe. \"The Tumuli of Troy and the Troad.\" In Tumulus as Sema, edited by Olivier Henry and Ute Kelp. Berlin: De Gruyter, 2016."] },

  { "id": "besik-sivritepe", "greek": null, "translit": null, "english": "Beşik-Sivritepe (Achilleion), claimed tomb of Achilles", "tier": "traditional", "lat": 39.9171, "lon": 26.1591, "kind": "tomb", "iliad_refs": [], "note": "Hellenistic tumulus c.2 km SSW of Yeniköy at the north end of Beşik Bay, associated with the Achilleion sanctuary. A rival 'tomb of Achilles' to Kesik Tepe — which is itself evidence that these are cult claims competing for pilgrims, not burials.", "tradition": "Hellenistic hero cult of Achilles at the Achilleion sanctuary, Beşik-Yassıtepe", "citations": ["https://vici.org/vici/27329/", "Rose, C. Brian, and Reyhan Körpe. \"The Tumuli of Troy and the Troad.\" In Tumulus as Sema, edited by Olivier Henry and Ute Kelp. Berlin: De Gruyter, 2016."] },

  { "id": "kum-tepe", "greek": null, "translit": null, "english": "Kum Tepe", "tier": "traditional", "lat": 39.9936, "lon": 26.1926, "kind": "tomb", "iliad_refs": [], "note": "Mound near the Hellespont entrance which Schliemann took for the tomb of Achilles. Rose and Körpe's work indicates that several such mounds in the Troad are in fact SETTLEMENT mounds of Neolithic to Bronze Age date, not tumuli — Kum Tepe is a known prehistoric settlement site. Label with that caution.", "tradition": "Schliemann's identification with Achilles' tomb; the Achilleum of ancient sources", "citations": ["https://vici.org/vici/11136/", "Rose, C. Brian, and Reyhan Körpe. \"The Tumuli of Troy and the Troad.\" In Tumulus as Sema, edited by Olivier Henry and Ute Kelp. Berlin: De Gruyter, 2016."] },

  { "id": "tomb-of-ajax-in-tepe", "greek": "Αἰάντειον", "translit": "Aianteion", "english": "The tomb of Ajax at İn Tepe (Aianteion)", "tier": "traditional", "lat": null, "lon": null, "kind": "tomb", "iliad_refs": [], "note": "A conical mound on a spur of the Rhoiteion promontory, west of İntepe village. Pliny says a town was built beside Ajax's tomb; the tumulus was renovated and vaulted in the 2nd century AD. COORDINATE DELIBERATELY NULL: the Vici.org record (39.9916 / 26.2420) places it in Kumkale, which is c.8 km west of İntepe and is almost certainly an error. Anchor from Rhoiteion at 40.010 / 26.303 (Pleiades 550856) until a published survey point is found.", "tradition": "Ancient hero cult of Ajax at Rhoiteion; Pliny, Natural History 5.125; Strabo 13.1.30", "citations": ["https://pleiades.stoa.org/places/550856", "Rose, C. Brian. The Archaeology of Greek and Roman Troy. Cambridge: Cambridge University Press, 2014."] },

  { "id": "uvecik-tepe", "greek": null, "translit": null, "english": "Üvecik Tepe", "tier": "certain", "lat": null, "lon": null, "kind": "tomb", "iliad_refs": [], "note": "South of Troy on the road to Alexandria Troas. NOT a heroic tomb: it is the tomb of Festus, a favourite of the emperor Caracalla (r.211-217), himself a great admirer of Achilles — built c.214 AD, and the largest tumulus in the Troad thereafter. Worth mapping precisely because it shows how the Homeric landscape was manufactured under Rome. No verified coordinate found.", "tradition": null, "citations": ["https://www.livius.org/articles/place/troy/troy-5/", "Rose, C. Brian. The Archaeology of Greek and Roman Troy. Cambridge: Cambridge University Press, 2014."] },

  { "id": "sigeion", "greek": "Σίγειον", "translit": "Sigeion", "english": "Sigeion", "tier": "certain", "lat": 39.9835, "lon": 26.1809, "kind": "promontory", "iliad_refs": [], "note": "NOT NAMED IN THE ILIAD — verified by exhaustive search of the Greek text. A later Greek settlement at the mouth of the Scamander forming the NW corner of the Troad, and the traditional western headland of the Achaean beach. Map it as later geography, not Homeric.", "tradition": null, "citations": ["https://pleiades.stoa.org/places/550877", "https://pleiades.stoa.org/places/550878", "Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973."] },

  { "id": "rhoiteion", "greek": "Ῥοίτειον", "translit": "Rhoiteion", "english": "Rhoiteion", "tier": "certain", "lat": 40.010, "lon": 26.303, "kind": "promontory", "iliad_refs": [], "note": "NOT NAMED IN THE ILIAD — verified. An Archaic-to-Hellenistic city on the Baba Kale spur of Çakal Tepe, north of Halileli and west of İntepe; its Aeantion promontory served as a harbour in Roman times. The traditional eastern headland of the Achaean beach, paired with Sigeion.", "tradition": null, "citations": ["https://pleiades.stoa.org/places/550856", "Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973."] },

  { "id": "besik-bay", "greek": null, "translit": null, "english": "Beşik Bay", "tier": "certain", "lat": null, "lon": null, "kind": "harbour", "iliad_refs": [], "note": "Bay on the Aegean coast SW of Troy, facing Tenedos. Korfmann excavated a cemetery of c.100 graves here, 1982-87, in which Mycenaean and Mycenaeanising pottery (mostly LH IIIB) makes up nearly a third of the fine wares — against under 1% in the Troia VI/VII levels. Since the Troian bay had largely silted by LH IIIB, a Beşik harbour would have been increasingly necessary for coastal trade. The best archaeological candidate for a Late Bronze Age port, and a serious candidate for the Achaean anchorage. Coordinate left null; anchor the bay from Beşik Tepe at 39.9171 / 26.1591, at its northern end.", "tradition": null, "citations": ["Korfmann, Manfred. Beşik-Tepe excavation reports, 1982–1987.", "Kraft, John C., George Rapp, İlhan Kayan, and John V. Luce. \"Harbor areas at ancient Troy.\" Geology 31, no. 2 (2003): 163–66."] },

  { "id": "kesik-basin", "greek": null, "translit": null, "english": "The Kesik basin / Kesik cut", "tier": "speculative", "lat": null, "lon": null, "kind": "harbour", "iliad_refs": [], "note": "An artificial cut through the 40 m Yeniköy ridge west of the plain, and a former marsh (drained in the 1960s) shown by drilling to have been a marine basin in the Early Bronze Age. Zangger, with Jablonka and Kayan on the water engineering, proposed the Kesik plain as a harbour basin and trans-shipment point. (The rectangular basin c. 330 x 230 m earlier repeated here belongs to the paper's PYLOS analogy, the Port of Nestor — corrected 2026-07-29 per RESEARCH-PALEOGEOGRAPHY.md.) CONTESTED: sedimentation patterns are ambiguous and diagnostic artefacts absent. Present as hypothesis only.", "tradition": "Eberhard Zangger's port hypothesis, with Jablonka and Kayan on the associated water-engineering system", "citations": ["https://www.academia.edu/31276138/Searching_for_the_Ports_of_Troy", "https://www.researchgate.net/publication/283762579_Artificial_Ports_and_Water_Engineering_at_Troy_A_Geoarchaeological_Working_Hypothesis"] },

  { "id": "hellespont", "greek": "Ἑλλήσποντος", "translit": "Hellēspontos", "english": "The Hellespont", "tier": "certain", "lat": 40.15, "lon": 26.40, "kind": "other", "iliad_refs": ["2.845", "7.86", "24.346"], "note": "The modern Dardanelles; the northern edge of the Troad and of the Achaeans' world. Od. 24.82 places the barrow of Achilles on a headland 'by the broad Hellespont'.", "tradition": null, "citations": ["https://pleiades.stoa.org/places/501434"] },

  { "id": "mount-ida", "greek": "Ἴδη", "translit": "Idē", "english": "Mount Ida", "tier": "certain", "lat": 39.70, "lon": 26.90, "kind": "mountain", "iliad_refs": ["8.47", "14.283", "15.151", "20.218", "21.449"], "note": "Modern Kaz Dağı. 'Many-fountained Ida' (πολυπίδαξ) is the source of the eight rivers of 12.19-22 and Zeus's grandstand from Book 8 onward. Dardanus's people lived on its lower slopes before Ilios was built on the plain (20.218).", "tradition": null, "citations": ["https://pleiades.stoa.org/places/550592"] },

  { "id": "gargaron", "greek": "Γάργαρον", "translit": "Gargaron", "english": "Gargaron, the topmost peak of Ida", "tier": "traditional", "lat": null, "lon": null, "kind": "mountain", "iliad_refs": ["8.48", "14.292", "14.352", "15.152"], "note": "Zeus's seat: 'Gargaron, where he has his precinct and his fragrant altar' (8.48); Hera comes to 'topmost Gargaron' (14.292); Zeus sleeps and later wakes there (14.352, 15.152). Traditionally the summit of Kaz Dağı. DO NOT CONFUSE with the historical town of Gargara on the coast below (c.39.586 N / 26.534 E), which is a different place.", "tradition": "Identification with the summit of Mount Ida / Kaz Dağı, following Strabo 13.1.5", "citations": ["Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973.", "Strabo, Geography 13.1. https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0198:book%3D13:chapter%3D1"] },

  { "id": "lekton", "greek": "Λεκτόν", "translit": "Lekton", "english": "Cape Lekton", "tier": "certain", "lat": 39.4783, "lon": 26.0633, "kind": "promontory", "iliad_refs": ["14.284"], "note": "Modern Cape Baba (Baba Burnu), the westernmost point of Asia Minor. Named once: Hera and Sleep 'came to Lekton, where first they left the sea' and went on over the dry land to Ida (14.284). A precise, verifiable Homeric coordinate — one of very few.", "tradition": null, "citations": ["https://pleiades.stoa.org/places/550691"] },

  { "id": "wall-of-heracles", "greek": "τεῖχος Ἡρακλῆος", "translit": "teichos Hēraklēos", "english": "The heaped-up wall of Heracles", "tier": "mythical", "lat": null, "lon": null, "kind": "other", "iliad_refs": ["20.144-148"], "note": "The pro-Greek gods' vantage point: 'the high heaped-up wall of divine Heracles, which the Trojans and Pallas Athena had made for him, so that he might escape the sea-monster when it drove him from the shore to the plain' (20.145-148). A wholly mythical structure, balancing Callicolone. Mark as such.", "tradition": null, "citations": [] },

  { "id": "thymbra", "greek": "Θύμβρη", "translit": "Thymbrē", "english": "Thymbra", "tier": "traditional", "lat": null, "lon": null, "kind": "plain", "iliad_refs": ["10.430"], "note": "Named once, in Dolon's account of the allied dispositions: 'toward Thymbra the Lycians and the lordly Mysians drew their lot' (10.430). Later the site of the Thymbraion, the sanctuary of Apollo Thymbraeus, and by legend where Achilles ambushed Troilus. Anchor to the Thymbrios (Kemer Su) - Scamander confluence rather than a point: Pleiades explicitly gives only a rough rectangle (26.0-26.5 E, 39.5-40.0 N), and the sources disagree whether Thymbra was a polis, a topos, or a pedion. NOTE: the repo currently carries [39.9, 26.33] — review.", "tradition": "The Thymbrios-Scamander confluence, following Strabo 13.1.35; a possible site near Akçaköy, debated", "citations": ["https://pleiades.stoa.org/places/550927", "Strabo, Geography 13.1.35. https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0198:book%3D13:chapter%3D1"] },

  { "id": "satnioeis", "greek": "Σατνιόεις", "translit": "Satnioeis", "english": "The Satnioeis river", "tier": "traditional", "lat": null, "lon": null, "kind": "river", "iliad_refs": ["6.34", "14.445", "21.87"], "note": "'The banks of fair-flowing Satnioeis' (6.34); Satnios was born to a nymph by a herdsman there (14.445); Pedasos stands on it (21.87). Standardly identified with the Tuzla Çayı in the southern Troad.", "tradition": "Identification with the Tuzla Çayı, following Strabo 13.1.50", "citations": ["Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973."] },

  { "id": "aisepos", "greek": "Αἴσηπος", "translit": "Aisēpos", "english": "The Aesepus river", "tier": "certain", "lat": null, "lon": null, "kind": "river", "iliad_refs": ["2.825", "4.91", "12.21"], "note": "Modern Gönen Çayı. The eastern limit of Trojan-allied territory: Pandarus's Zeleians 'drink the dark water of Aesepus' (2.825), and it is one of the eight Idaean rivers turned against the Achaean wall (12.21). Draw as a line; Pleiades gives a MultiLineString, not a point.", "tradition": null, "citations": ["https://pleiades.stoa.org/places/511141"] },

  { "id": "granikos", "greek": "Γρήνικος", "translit": "Grēnikos", "english": "The Granicus river", "tier": "traditional", "lat": null, "lon": null, "kind": "river", "iliad_refs": ["12.21"], "note": "One of the eight Idaean rivers of 12.19-22. Identified with the Biga Çayı — later famous as the site of Alexander's first victory in Asia. Rose and Körpe surveyed the lower Granicus valley tombs.", "tradition": "Identification with the Biga Çayı, standard since antiquity", "citations": ["Rose, C. Brian. The Archaeology of Greek and Roman Troy. Cambridge: Cambridge University Press, 2014."] },

  { "id": "rhodios", "greek": "Ῥοδίος", "translit": "Rhodios", "english": "The Rhodius river", "tier": "speculative", "lat": null, "lon": null, "kind": "river", "iliad_refs": ["12.20"], "note": "One of the eight Idaean rivers (12.20). Variously identified in antiquity with streams east of the Scamander; no secure modern identification.", "tradition": null, "citations": ["Leaf, Walter. Strabo on the Troad: Book XIII, Cap. I. Cambridge: Cambridge University Press, 1923."] },

  { "id": "rhesos-heptaporos-karesos", "greek": "Ῥῆσος, Ἑπτάπορος, Κάρησος", "translit": "Rhēsos, Heptaporos, Karēsos", "english": "The Rhesus, Heptaporus and Caresus rivers", "tier": "speculative", "lat": null, "lon": null, "kind": "river", "iliad_refs": ["12.20"], "note": "Three of the eight Idaean rivers named in a single line (12.20) and nowhere else in Homer. None is securely identified with a modern watercourse; already puzzling to ancient geographers. Honest treatment on a map: list them as unlocated Idaean streams.", "tradition": null, "citations": ["Leaf, Walter. Strabo on the Troad: Book XIII, Cap. I. Cambridge: Cambridge University Press, 1923."] },

  { "id": "thymbrios", "greek": null, "translit": "Thymbrios", "english": "The Thymbrios river", "tier": "traditional", "lat": null, "lon": null, "kind": "river", "iliad_refs": [], "note": "Not named by Homer. A Scamander tributary, identified with the Kemer Su; the anchor for locating Thymbra. Included because the confluence is a needed drafting reference.", "tradition": "Strabo 13.1.35", "citations": ["https://pleiades.stoa.org/places/550927"] },

  { "id": "thebe-hypoplakia", "greek": "Θήβη Ὑποπλακίη", "translit": "Thēbē Hypoplakiē", "english": "Thebe under Placus", "tier": "traditional", "lat": null, "lon": null, "kind": "city", "iliad_refs": ["1.366", "2.691", "6.397", "6.416"], "note": "Andromache's home, ruled by her father Eetion over the Cilicians; Achilles sacked it, killed Eetion, and took Chryseis from it (1.366) and Andromache's mother from it (6.416). Strabo 13.1.61 puts Thebe in a fertile plain c.60 stadia from Adramyttium, deserted in his day. No excavated site is securely identified. The repo's [39.4, 26.9] should be reviewed against that: anchor to Adramyttium instead of asserting a point.", "tradition": "Near Adramyttium (modern Edremit region), following Strabo 13.1.61-65", "citations": ["Strabo, Geography 13.1.61-65. https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0198:book%3D13:chapter%3D1", "Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973."] },

  { "id": "lyrnessus", "greek": "Λυρνησσός", "translit": "Lyrnēssos", "english": "Lyrnessus", "tier": "speculative", "lat": null, "lon": null, "kind": "city", "iliad_refs": ["2.690-691", "19.60", "20.92", "20.191"], "note": "Where Achilles took Briseis (2.690-691, 19.60) and from which he once chased Aeneas down off Ida (20.191). Pleiades has TWO Lyrnessos entries: 550703 with a Barrington 1:500,000 REPRESENTATIVE point at 39.508 / 27.082 — explicitly a representative point, not a site — and 652355 flagged unlocated. The repo currently carries a third, uncited figure [39.4, 26.85]. Two disagreeing uncited numbers are worse than an honest null.", "tradition": "Southern Troad / Gulf of Adramyttium region, following Strabo 13.1.60-70, who already calls the site uncertain", "citations": ["https://pleiades.stoa.org/places/550703", "https://pleiades.stoa.org/places/652355", "Strabo, Geography 13.1.60-70."] },

  { "id": "pedasos", "greek": "Πήδασος", "translit": "Pēdasos", "english": "Pedasus", "tier": "speculative", "lat": null, "lon": null, "kind": "city", "iliad_refs": ["6.35", "20.92", "21.87"], "note": "'Steep Pedasus on the Satnioeis' (21.87), sacked with Lyrnessus (20.92). Not securely located; anchor to the Satnioeis (Tuzla Çayı) rather than a point. Note that the Pedasos of 6.35 and the Pedasos of 9.152/9.294 (in Agamemnon's Messenian offer) are different places, and Pedasos at 16.152 and 16.467 is Achilles' trace-horse.", "tradition": "On the Satnioeis, following Strabo 13.1.51; site unrecovered", "citations": ["Strabo, Geography 13.1.51.", "Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973."] },

  { "id": "chryse", "greek": "Χρύση", "translit": "Chrysē", "english": "Chryse", "tier": "speculative", "lat": null, "lon": null, "kind": "city", "iliad_refs": ["1.37", "1.100", "1.390", "1.431", "1.451"], "note": "The town of Chryses, priest of Apollo, whose daughter Agamemnon takes — the place the whole poem starts from. Its site is genuinely disputed and was already lost by Strabo's day. The Barrington Atlas records THREE relevant entries: Chryse (56 D2, Aeolis, queried), Chrysa (56 C2), and a wholly unlocated Chryse — which is itself the evidence for a null. Candidates are the SW Troad near Hamaxitos and the Smintheion at Gülpınar, versus a Chrysa on the Gulf of Adramyttium near Thebe. NOTE: the repo carries [39.55, 26.17], i.e. the Smintheion option, tiered speculative; the note should say a rival candidate exists.", "tradition": "Near Hamaxitos and the sanctuary of Apollo Smintheus (Strabo 13.1.47-48, 13.1.63), against a rival Adramyttene Chrysa", "citations": ["https://pleiades.stoa.org/places/550501", "https://pleiades.stoa.org/places/550500", "https://pleiades.stoa.org/places/554214", "https://pleiades.stoa.org/places/550892", "Strabo, Geography 13.1.47-48, 13.1.63."] },

  { "id": "killa", "greek": "Κίλλα", "translit": "Killa", "english": "Cilla", "tier": "speculative", "lat": null, "lon": null, "kind": "city", "iliad_refs": ["1.38", "1.452"], "note": "Named only in Chryses' prayer formula, twice identically: 'you who guard Chryse and sacred Cilla and rule mightily over Tenedos' (1.38 = 1.452). The Barrington Atlas lists Killa as UNLOCATED (56, unlocated) — this is a documented, not a guessed, null. A Mount Killaios (probably Adatepe) and a Killaios river exist nearby but neither is the town.", "tradition": null, "citations": ["https://pleiades.stoa.org/places/554254", "https://pleiades.stoa.org/places/550645"] },

  { "id": "adramyttion", "greek": null, "translit": null, "english": "Adramyttium", "tier": "certain", "lat": null, "lon": null, "kind": "city", "iliad_refs": [], "note": "NOT NAMED IN THE ILIAD — verified. An Aeolian city on the Karataş peninsula at Ören, Balıkesir province. Included only because Strabo measures Homeric Thebe from it (60 stadia), so it is the anchor for a whole cluster of southern-Troad identifications. Should appear on a map as a modern/later reference point, clearly distinguished from Homeric places.", "tradition": null, "citations": ["https://pleiades.stoa.org/places/550403", "Strabo, Geography 13.1.61-65."] },

  { "id": "tenedos", "greek": "Τένεδος", "translit": "Tenedos", "english": "Tenedos", "tier": "certain", "lat": 39.82, "lon": 26.06, "kind": "island", "iliad_refs": ["1.38", "1.452", "11.625", "13.33"], "note": "Modern Bozcaada, off the mouth of Beşik Bay. Under Apollo's protection (1.38), sacked by Achilles (11.625), and a waypoint for Poseidon striding from Samothrace 'midway between Tenedos and rugged Imbros' (13.33). Its position matters for the Beşik Bay harbour case: any ship coming to Troy from the south passes it.", "tradition": null, "citations": ["https://pleiades.stoa.org/places/550912"] },

  { "id": "lesbos", "greek": "Λέσβος", "translit": "Lesbos", "english": "Lesbos", "tier": "certain", "lat": 39.20, "lon": 26.30, "kind": "island", "iliad_refs": ["9.129", "9.271", "9.664", "24.544"], "note": "Taken by Achilles; seven Lesbian women are part of Agamemnon's offer (9.129 = 9.271), and Diomede of Lesbos sleeps beside him (9.664). Priam's realm is bounded by 'Lesbos above, seat of Macar' (24.544). Coordinate is an island centroid, not a site.", "tradition": null, "citations": [] },

  { "id": "imbros", "greek": "Ἴμβρος", "translit": "Imbros", "english": "Imbros", "tier": "certain", "lat": 40.17, "lon": 25.85, "kind": "island", "iliad_refs": ["13.33", "14.281", "24.78", "24.753"], "note": "Modern Gökçeada. 'Rugged Imbros' on Poseidon's route (13.33) and in Iris's dive to Thetis (24.78); Hera and Sleep leave 'the city of Lemnos and Imbros' for the Troad (14.281).", "tradition": null, "citations": ["https://pleiades.stoa.org/places/501438"] },

  { "id": "samothrace", "greek": "Σάμος Θρηϊκίη", "translit": "Samos Thrēïkiē", "english": "Thracian Samos (Samothrace)", "tier": "certain", "lat": 40.50, "lon": 25.53, "kind": "island", "iliad_refs": ["13.11-14", "24.78", "24.753"], "note": "Poseidon's grandstand, and a real optical fact: 'high on the topmost peak of wooded Thracian Samos, for from there all Ida was visible, and the city of Priam was visible, and the ships of the Achaeans' (13.12-14). Mount Fengari is over 1600 m and Ida is genuinely visible from it in clear weather — one of the poem's most defensible topographic claims, and worth a sightline on the map.", "tradition": null, "citations": ["https://pleiades.stoa.org/places/501597", "Luce, J. V. Celebrating Homer's Landscapes: Troy and Ithaca Revisited. New Haven: Yale University Press, 1998."] },

  { "id": "lemnos", "greek": "Λῆμνος", "translit": "Lēmnos", "english": "Lemnos", "tier": "certain", "lat": 39.92, "lon": 25.24, "kind": "island", "iliad_refs": ["1.593", "2.722", "14.281", "21.40", "21.79"], "note": "Where Hephaestus fell (1.593), where Philoctetes was left (2.722), the market Achilles sold Lycaon into (21.40, 21.79), and the wine-supply for the camp. Not on the Trojan plain but structurally part of the Troad map: it is the Achaeans' rear base.", "tradition": null, "citations": ["https://pleiades.stoa.org/places/550693"] },

  { "id": "abydos", "greek": "Ἄβυδος", "translit": "Abydos", "english": "Abydos", "tier": "certain", "lat": 40.19, "lon": 26.41, "kind": "city", "iliad_refs": ["2.836", "4.500", "17.584"], "note": "On the Asian shore at the narrowest point of the Hellespont; Trojan-allied territory under Asius (2.836). Democoon comes 'from Abydos, from the swift mares' (4.500).", "tradition": null, "citations": ["https://pleiades.stoa.org/places/501325"] },

  { "id": "sestos", "greek": "Σηστός", "translit": "Sēstos", "english": "Sestos", "tier": "certain", "lat": 40.22, "lon": 26.41, "kind": "city", "iliad_refs": ["2.836"], "note": "On the European shore opposite Abydos, named once in the Trojan Catalogue with Percote, Practius, Abydos and Arisbe (2.835-836) — the only European territory in the Trojan alliance, which is worth flagging on a map.", "tradition": null, "citations": ["https://pleiades.stoa.org/places/501609"] },

  { "id": "percote", "greek": "Περκώτη", "translit": "Perkōtē", "english": "Percote", "tier": "traditional", "lat": 40.2739, "lon": 26.5888, "kind": "city", "iliad_refs": ["2.835", "11.229", "15.548"], "note": "On the Hellespont NE of Troy. Iphidamas was reared there and left his ships there before coming overland to Troy (11.229) — a rare glimpse of allied logistics. Coordinate is a Barrington Atlas point, c.4 miles east of Umurbey; treat as approximate.", "tradition": "Barrington Atlas 51 H4, c.4 miles east of Umurbey", "citations": ["https://pleiades.stoa.org/places/501556"] },

  { "id": "arisbe", "greek": "Ἀρίσβη", "translit": "Arisbē", "english": "Arisbe", "tier": "traditional", "lat": 40.1943, "lon": 26.5358, "kind": "city", "iliad_refs": ["2.836", "2.838", "6.13", "12.96", "21.43"], "note": "'Shining Arisbe' on the Selleeis; Asius's horses are brought from there (2.838, 12.96), Axylus lived there (6.13), and Lycaon was sold and sent 'to shining Arisbe' (21.43). Possibly modern Musaköy; a Milesian colony according to Anaximenes of Lampsacus.", "tradition": "Possible identification with modern Musaköy (Pleiades, after Anaximenes of Lampsacus)", "citations": ["https://pleiades.stoa.org/places/501359"] },

  { "id": "dardanie", "greek": "Δαρδανίη", "translit": "Dardaniē", "english": "Dardania", "tier": "speculative", "lat": null, "lon": null, "kind": "city", "iliad_refs": ["20.216-218"], "note": "Aeneas's genealogy gives the Troad's foundation story and its topographic logic in three lines: Zeus fathered Dardanus, 'and he founded Dardania, since sacred Ilios was not yet built as a city of mortal men on the plain, but they still lived on the slopes of many-fountained Ida' (20.216-218). Site not recovered; ancient tradition places it inland/south of Abydos toward Çanakkale. The repo's [40.14, 26.42] is that tradition, not a site.", "tradition": "Inland south of Abydos, near modern Çanakkale, following Strabo 13.1.25-33", "citations": ["https://pleiades.stoa.org/places/501393", "Strabo, Geography 13.1.25-33."] },

  { "id": "zeleia", "greek": "Ζέλεια", "translit": "Zeleia", "english": "Zeleia", "tier": "traditional", "lat": null, "lon": null, "kind": "city", "iliad_refs": ["2.824-825", "4.103", "4.121"], "note": "Pandarus's city, 'under the lowest foot of Ida' on the Aesepus (2.824-825); he twice vows a hecatomb on returning home to 'the sacred city of Zeleia' (4.103 = 4.121). Traditionally in the Aesepus valley near Sarıköy. The repo's [40.35, 27.15] is that tradition; left null here pending a verified point.", "tradition": "Aesepus valley near modern Sarıköy, following Strabo 13.1.9", "citations": ["https://pleiades.stoa.org/places/511461", "Strabo, Geography 13.1.9."] }
]
```

---

## Bottom line for whoever draws this

Three things carry the map, and all three are defensible:

1. **The coastline is the story.** Kraft/Kayan/Erol 1980 and Kayan give us the facts to redraw
   it ourselves, and their conclusion — that the battlefield lay *south and west* of Troy, not
   north — inverts the picture most readers arrive with. That alone justifies the map's
   existence.
2. **The camp has a shape even though it has no place.** *Il.* 14.31–36 plus 8.222–26 gives an
   exact order: Ajax at one end, Odysseus with the assembly and altars at the centre, Achilles
   at the other end, ships in rows filling a beach between two headlands. Draw that as a
   schematic and it is textually certain.
3. **The absences are content, not gaps.** No two springs. No Achaean wall. No findable oak,
   fig tree, or tomb of Ilos. A Landmark-style apparatus that labels those honestly — with the
   2020 hydrochemistry, with Aristotle's remark in Strabo, with Rose and Körpe on the tumuli
   that turned out to be settlement mounds — is doing something no print atlas of Troy has
   done.
