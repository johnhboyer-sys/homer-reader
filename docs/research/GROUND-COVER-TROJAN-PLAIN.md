# GROUND-COVER-TROJAN-PLAIN.md — what the ground IS, for "The Ships, the Bay, and Ilios"

**Date:** 2026-08-14. **Commissioned by:** John's ruling that a raised-oblique plate
must not colour ground by elevation (the geometry already carries height; colouring
by height again reads the plate as a draped flat map). **Consumed by:** whichever
lane draws the ground-cover fill for `apparatus/plates/trojan-plain.json`'s oblique
render. **Scope:** classes and their extents only. No palette, no colour values, no
SVG, no renderer changes — that is a separate lane's decision.

**Sources read for this file:** `docs/research/RESEARCH-PALEOGEOGRAPHY.md` (the
paleoenvironment dossier — Kraft, Kayan, Brückner, Strabo), `docs/research/
RESEARCH-TROY-APPEARANCE.md` §1.9–1.11, §4, §6.2, §7, `docs/TROAD-SOURCES.md`, the
live `apparatus/plates/trojan-plain.json` (to see what DEM rules already exist and
avoid re-deriving them badly), and the Iliad's Greek text directly, checked against
`sources/perseus/tlg0012.tlg001.perseus-grc2.xml` (Perseus, public domain) for every
line quoted below. `docs/research/RESEARCH-POEM-TOPOGRAPHY.md` was searched for
vegetation and land-use terms and confirmed to carry no additional material beyond
what is used here. No pollen core in the dossier constrains Bronze Age vegetation:
the one pollen study on file (Kayan 2009, drilling 201) is explicitly "in progress,"
dated to 2500–2350 BP — Iron Age, not Bronze Age — and its own author says "cite the
¹⁴C numbers, not the pollen work," with "no coordinate may be lifted from any of its
maps." **There is no paleobotanical evidence for Late Bronze Age vegetation on this
plain.** Everything below that is not a bare geomorphological facies (swamp vs. dry
alluvium) is either the poem's own testimony or a stated climate-analogue default,
and each is labelled as such.

---

## 1. The classes

Six classes. Each is defensible; nothing decorative was added to round out the set.

1. **Wet delta / swamp** — low, flat, seasonally or permanently waterlogged
   delta ground behind the Bronze Age shore. Existence: Kayan et al. 2003, 384,
   389 ("a broad deltaic swamp," "covered by swamps during the entire
   progradation period"). **Evidence grade: INFERABLE** (existence is
   physically attested in prose; the mapped extent is a DEM inference, not a
   traced published boundary — see §2).
2. **Dry delta fan** — the firm, dry, sand-covered surface immediately at the
   citadel's western foot, standing above the swamp. Existence: Kayan 2002,
   1003 (full citation §6), read in full: a specific, named, dry surface,
   distinguished explicitly from the wet ground further west. **Evidence
   grade: INFERABLE** (the surface is attested and located in prose; its
   boundary is not mapped and must be derived by elimination — see §2, §3).
3. **Riverbank thicket** — a fringe of trees and marsh-herbs directly on the
   river's edge: elm, willow, tamarisk overstorey; lotus, rush, galingale
   underneath. Existence: *Iliad* 21.350–52 (quoted in full at §4). **Evidence
   grade: POEM-ONLY.**
4. **Ridge scrub / bare slope** — thin-soiled, exposed ground on the Sigeion,
   Troy-spur and Rhoiteion ridges, standing clear of the delta fill.
   Existence: no site-specific source; a Mediterranean-Aegean climate default
   for exposed limestone at this elevation and slope, stated as a default, not
   a finding. **Evidence grade: INFERABLE**, and the weakest INFERABLE of the
   four (see §2).
5. **Sand dune / coastal barrier — Scamander front, Bronze Age.** Proposed only
   to be rejected. **Evidence grade: NOT KNOWABLE**, and worse than merely
   unknown — it is **contradicted by four independent statements** in the
   literature (§2.5, §5). Listed here because the live plate already draws it
   (`barrier-bronze`) and the drawing lane must not re-derive it as if it were
   live ground cover.
6. *(Not a spatial class — see §4.)* The poem's fertility epithets
   (`ἐριβώλαξ`, `ζείδωρος ἄρουρα`) attest that the dry plain (class 2) was
   good, tillable soil. They give no way to distinguish tilled ground from
   untilled ground *within* class 2, so they qualify class 2 rather than
   drawing a seventh class. Recorded here so the drawing lane does not invent
   a separate "farmland" boundary that no source supports.

---

## 2. Extents

### 2.1 Wet delta / swamp — **INFERABLE, DEM rule already exists**

No source draws a Bronze Age swamp boundary. What exists: (a) Kraft, Kayan &
Erol 1980's Fig. 2 maps *modern* swamp over the Kesik/Yeniköy plain and the
Scamander's western and south-western flanks — a real published map, but of
the wrong period, and it is copyrighted expression that may never be traced;
(b) Kayan et al. 2003's prose, quoted above, gives the fact of a broad Bronze
Age swamp with no boundary at all; (c) the plain's flatness and low relief are
independently measured off the DEM (§1.4a, §3.1 of the paleogeography
dossier: the delta surface north of the citadel sits flat at 10–11 m for
nearly 2 km).

**The extent already drawn on this sheet is the right model and should be
reused, not re-derived.** `apparatus/plates/trojan-plain.json`'s `delta-swamp`
layer defines the wet-ground mask as: SRTM (AWS Terrain Tiles Terrarium PNG,
this sheet's pinned Bronze Age grid — blur 10, decimate 2) cells between the
10 m contour (which `shore-bronze` is cut from) and 15 m, on slope under
1.2%, kept only where 4-connected to the published bay head (39.9582 N,
26.2062 E; Kayan 2003) — i.e. only wet ground that is actually continuous
with the bay, so an unrelated flat patch elsewhere cannot join it by
coincidence. Measured area ≈ 15 km². This is INFERABLE, not MAPPED: the rule
is this project's own construction against a real geomorphological fact, not
a traced published polygon. It should not be re-derived independently for
ground cover — it is the same ground.

### 2.2 Dry delta fan — **INFERABLE, new rule, derived by elimination**

Kayan 2002, 1003, gives no coordinate, only: the delta-fan surface at the
citadel's western foot is "about 0.5 m above present sea level" against a sea
then "about 2 m below its present level," and reads it as matching Homer's
battlefield — "there is no need to look for a battlefield in the distance."
**This licenses a prose annotation, not a shape**, per the paleogeography
dossier's own reading of the same passage (§1.4b there). What CAN be derived
honestly is the **complement**: within the plain sector, ground that is
neither water, nor the swamp mask (§2.1), nor part of a ridge relief band
(§2.4) is, by elimination, dry delta-fan ground. That is a legitimate rule —
it follows directly from the same DEM already trusted for the swamp and the
ridges — but it must be presented as an elimination rule, not as a mapped
fan boundary, because no source draws where the fan itself ends short of the
swamp.

### 2.3 Riverbank thicket — **POEM-ONLY, no DEM rule**

The passages (§4) locate this flora **at the river's edge**, explicitly
("which grew thick around the river's fair streams," 21.352) — but the
paleogeography dossier is explicit that **the Bronze Age river channels are
not locatable**: "With as much as 20 m of alluvium on the southern Scamander
floodplain, we cannot hope to locate the river channels of antiquity" (Kraft,
Rapp, Kayan & Luce 2003, 164, quoted in full at RESEARCH-PALEOGEOGRAPHY.md
§2, final row). The `scamander` and `simoeis` lines this sheet already draws
are therefore **schematic**, not geographic (same source, same row: "Schematic
only, never sourced to Fig. 5"). A riverbank-thicket class inherits that
register exactly. **There is no defensible width for the fringe** — the poem
says the flora grows thick at the water's edge, not how far back from it it
runs. The honest instruction is: tie this class to the schematic river line as
a schematic band, and do not print a metre value for its width; if a width
must be chosen for legibility, caption it as an artist's convention, not a
measurement.

### 2.4 Ridge scrub / bare slope — **INFERABLE, reuses existing relief geometry**

No vegetation survey exists for these ridges. The default rests on ordinary
Mediterranean-Aegean ecology: thin, well-drained soil on exposed limestone at
this latitude defaults to maquis/garrigue scrub or bare rock in the absence of
irrigation, not on any Troad-specific study. This is the weakest of the four
INFERABLE classes and should be captioned as a general default, not a
finding. Its extent, however, is cheap and already exists: this sheet's own
`relief-sigeion-ridge`, `relief-troy-ridge` and `relief-rhoiteion-ridge`
layers already isolate exactly this ground by elevation and slope for the
hypsometric bands being replaced. Reuse those polygons as the ridge-scrub
mask rather than re-deriving elevation thresholds.

### 2.5 Sand dune / coastal barrier, Scamander front — **NOT KNOWABLE, and contradicted**

Four independent, first-hand-verified statements deny a Bronze Age barrier on
this delta:

- Kayan 1997, 438: "coastal barriers and lagoonal features **did not develop**
  on the coast of the retreating sea in the Karamenderes valley."
- Kayan 2002, 1002: "Coastal spit, barrier, beach and lagoon sediments might be
  expected in this area; **however they do not exist**."
- Kayan et al. 2003, 390: "**There is no beach or lagoon formation.** Instead,
  sediments indicate swampy or seasonally wet environments."
- Kayan 2014, 712: the 2003 sentence repeated word for word, and "no
  Scamander-front barrier appears in the chapter's text or on any of its
  twenty figures at any date."
- Kraft et al. 2003b, 164, from the collaborating side: "no barrier lineaments
  are evident on the lower Scamander delta."

**Every source that draws a Bronze Age barrier draws it at Beşik Bay**, a
different embayment roughly 8 km from Troy, dated there to "around the period
of Troia VI" (Kayan 2014, 704) and plotted with four dated shoreline positions
(Kayan 2014, 707–08, figs. 6–7). That geometry is real, dated, and belongs on
a Beşik plate if one is ever drawn — and even there the published figures are
copyrighted expression that may only be re-expressed, never traced. It is not
this plate's ground.

**Standing defect, flagged for the record, not fixed here:** the live
`apparatus/plates/trojan-plain.json` still carries a `barrier-bronze` coast
layer drawing a Scamander-front Bronze Age sand barrier, citing a "2 to 2.5 m"
sea-level fall that matches no published number (the dossier's own §3.3
resolves this: "`barrier-bronze` is now the weakest layer on the sheet... not
supported by any source in this dossier and is contradicted by three,"
recommending deletion, re-dating to Strabo's era, or relocation to Beşik).
This ground-cover document does not touch that layer — it is out of this
task's scope — but a ground-cover scheme for this sheet must not treat
`barrier-bronze`'s footprint as source for a "beach" or "dune" ground-cover
class, because the geometry it is asking to be coloured is itself unresolved.

---

## 3. DEM-derivable rule table

Grid convention throughout: SRTM via AWS Open Data Terrain Tiles (Terrarium
PNG), this sheet's own pinned Bronze Age grid (box-blur 10 passes, decimate
2×) — the same grid `shore-bronze` and `delta-swamp` are already cut from.
Reference points: bay head 39.9582 N, 26.2062 E (Kayan 2003); Hisarlık
39.957 N, 26.239 E.

| Class | Rule | Elevation | Slope | Connectivity | Rule status |
|---|---|---|---|---|---|
| Wet delta / swamp | reuse `delta-swamp` | 10–15 m | < 1.2% | 4-connected flood fill from bay head; excludes lagoon interior | **Existing** — do not re-derive |
| Dry delta fan | plain-sector cells not in `delta-swamp`, not in `lagoon-bronze`/`shore-bronze` water, not in any ridge relief-band polygon | — (by exclusion) | — (by exclusion) | must lie within the `scamandrian-plain` sector polygon | **New, by elimination** — code-specifiable, not published |
| Ridge scrub / bare slope | reuse `relief-sigeion-ridge`, `relief-troy-ridge`, `relief-rhoiteion-ridge` polygons | matches those layers' own thresholds | matches those layers' own thresholds | n/a | **Existing** — do not re-derive |
| Riverbank thicket | **no DEM rule** — schematic buffer along `scamander`/`simoeis` lines only | n/a | n/a | tied to schematic line, not terrain | **None** — state so, do not fabricate a width |
| Sand dune / barrier (Scamander) | **no rule; omit the class** | — | — | — | **None** — contradicted, not merely absent |

**Three of the six proposed classes have a DEM-derivable rule** (swamp and
ridge-scrub by reusing geometry that already exists on this sheet; dry delta
fan by a new elimination rule this document specifies precisely enough to
code). The riverbank thicket has none by the sources' own admission (the
underlying river position is schematic). The Scamander-front barrier has none
because it should not be drawn at all.

---

## 4. What the poem adds (kept separate — schematic/literary register, never mixed with the physical register above)

Method: only passages that state a plant grows in a place are used; a passage
that merely names a plant at a narrative moment, with no locative claim, is
recorded as *not* extending the flora's known range.

**Riverbank flora, explicitly located at the water.** *Iliad* 21.350–52, of
what Hephaestus's fire burns along the Scamander:

> καίοντο πτελέαι τε καὶ ἰτέαι ἠδὲ μυρῖκαι,
> καίετο δὲ λωτός τε ἰδὲ θρύον ἠδὲ κύπειρον,
> τὰ περὶ καλὰ ῥέεθρα ἅλις ποταμοῖο πεφύκει·

"Elms and willows and tamarisks were burning, and lotus and rush and galingale
were burning, which grew in abundance about the river's fair streams." The
third line is a locative claim in the poem's own words: this flora grows
*around the river's streams*, not broadcast over the plain. This is the single
strongest textual anchor in this file — a named assemblage, explicitly sited.

**Tamarisk recurs at the riverbank specifically.** *Iliad* 21.18: Achilles
leaves his spear "κεκλιμένον μυρίκῃσιν" — leaning against tamarisks — on the
bank he has just come from, mid-river-fight. *Iliad* 10.466–68: Odysseus hangs
Dolon's spoils "ἀνὰ μυρίκην," binding reed-stems (`δόνακας`) and tamarisk
shoots together as a way-marker on the road back to the ships. Three
tamarisk passages, two of them explicitly riverside, one on the road — read
together they support tamarisk as a common, way-marking shrub of wet or
riparian ground, not a claim about its density or range beyond the water's
edge.

**The plain's drying is a fire-simile detail, not a hydrology claim.** *Iliad*
21.345–49 ("πᾶν δ' ἐξηράνθη πεδίον," "the whole plain was dried") describes
the heat of Hephaestus's fire on the river itself, compared to an autumn wind
drying a newly watered vineyard (346–47). It is not evidence that the plain
was normally wet and dried by season; it is a simile about heat, and it is
recorded here only so a drawing lane does not mis-cite it as a hydrological
fact.

**The dry, dusty plain and Kayan's own move from geology to poem.** Kayan
2002, 1003 (full text): "Characteristics of the surface recall Homer's
descriptions of the battlefield: a sand-covered and dusty plain and some
river channels... there is no need to look for a battlefield in the distance
for the period of Troy VI." This is the one place in the dossier where a
geologist makes the physical/poetic correlation himself, in his own voice —
recorded as **both** (§1) rather than poem-only, because the physical surface
and the poem's description are explicitly the same claim in his text.

**Fertility epithets qualify, but do not bound, the dry plain.** `Τροίῃ
ἐριβώλακι` (6.315, "deep-soiled Troy") and the mares' pasture at `ζείδωρον
ἄρουραν` (20.226, "grain-giving plowland") attest that the poem imagines the
dry plain as good, tillable soil. Neither gives an extent distinct from class
2 (§1.6). **Poem-only.**

**Erichthonius's mares (20.221–29) — a mythic vignette, not a topographic
description.** Dardanus's grandson Erichthonius owns 3,000 mares that graze
"ἕλος κάτα" (down in/throughout the marsh-meadow), then gambol over the
grain-plowland without breaking a tassel, or over the sea's surf-line without
wetting a hoof. This is a simile-register passage establishing divine-adjacent
wealth (the North Wind sires foals on them), not a survey of the plain. It
corroborates that the poem's world contains a marsh-meadow (`ἕλος`), a
grain-plain, and a shore as distinct landscape types — consistent with classes
1 and 2 above — but `κατά` gives no boundary, and this passage must not be
used to place or size the marsh. **Poem-only, and non-locating.**

**θρωσμὸς πεδίοιο — the Trojan bivouac's high ground.** Attested three times,
always of the Trojan position and always near the ships (10.160, 11.56, 20.3;
10.161 adds "ἄγχι νεῶν"). This is a *place* (already a gazetteer entry,
`RESEARCH-POEM-TOPOGRAPHY.md` §5), not a ground-cover class — it corroborates
that dry, raised ground existed within reach of the camp, consistent with
class 2, and is not drawn separately here.

**Summary — attested where:**

| Claim | Physical | Poem | Both |
|---|---|---|---|
| Broad deltaic swamp exists | ✓ (Kayan 2003) | — | |
| Dry, sand-covered fan at citadel's western foot | ✓ (Kayan 2002) | ✓ (battlefield description) | ✓ |
| Elm/willow/tamarisk/lotus/rush/galingale at the river's edge | — | ✓ (21.350–52) | |
| Fertile, tillable soil generally | — (deltas are fertile generically; not surveyed here) | ✓ (epithets) | |
| Ridge scrub/bare rock | — (climate default only) | — | |
| Marsh-meadow, grain-plain and shore as distinct types | — | ✓ (20.221–29, non-locating) | |
| Bronze Age barrier/dune on the Scamander front | ✗ denied ×4 | — | |

---

## 5. DO NOT DRAW

Generic Bronze Age landscape-illustration clichés this evidence does not
support, in the manner of `RESEARCH-TROY-APPEARANCE.md` §6.2:

1. **A sandy dune/barrier belt across the Scamander mouth at any Bronze Age
   date** — contradicted by four independent statements (§2.5); the only
   dated Bronze Age barrier in the literature is at Beşik Bay, off this sheet.
2. **Tropical or Nilotic wetland dressing** — papyrus stands, mangrove-style
   fringing vegetation, reed forests taller than a person. The poem's own
   marsh flora is lotus, rush and galingale — low, herbaceous, riverside — not
   a jungle register.
3. **Continuous furrowed grainfields with visible plot boundaries across the
   dry plain** — no cadastral, field-boundary or agricultural-plot evidence
   exists for Bronze Age Troy; the epithets attest fertility, not a mapped
   field pattern, and the one pollen sample on file cannot be used for the
   period at all (§0).
4. **Vineyard or olive terracing on the ridge slopes** — no source, physical
   or poetic, puts orchards on the Sigeion or Rhoiteion ridges; the poem's fig
   and oak are individually named trees at specific gates, not orchard rows.
5. **Forest canopy over the plain or the ridges** — no forest evidence exists;
   the climate default for the ridges is scrub or bare rock (§2.4), and the
   plain is delta, not woodland.
6. **Salt pans or white salt-flat texture on the plain itself** — Strabo's
   salt lakes (13.1.31) belong to a barred river mouth in *his own* era (c. 0
   BC/AD), are not located on this delta by any source, and must not be
   projected back onto the Bronze Age scene.
7. **A flat, uniform "steppe" or "grassland" wash treating wet and dry ground
   identically** — this collapses the one physical distinction this file
   actually establishes (swamp vs. firm plain); using one wash for both
   defeats the purpose of a ground-cover scheme entirely.
8. **Lotus/rush/galingale colour or texture spread broadcast across the whole
   swamp** rather than confined to the river's immediate margin — the poem
   locates this flora "around the river's fair streams" (21.352), not over
   the delta generally.
9. **A beach or strand line of bare sand along the Bronze Age shore** — no
   source describes or maps one; the shore this sheet draws (`shore-bronze`)
   is a reconstructed low-ground contour, not a surveyed beach facies.
10. **Precise, surveyed field-parcel geometry of any kind** — nothing in
    either dossier supports property lines, terracing plans, or plot shapes
    for the Bronze Age plain.

---

## 6. Sources

Kayan, İlhan. "Paleogeographical Reconstructions on the Plain Along the
Western Footslope of Troy." In *Mauerschau: Festschrift für Manfred
Korfmann*, edited by Rüstem Aslan, Stephan Blum, Gabriele Kastl, Frank
Schweizer, and Diane Thumm, vol. 3, 993–1004. Remshalden-Grunbach: Verlag
Bernhard Albert Greiner, 2002.

Kayan, İlhan, Ertuğ Öner, Levent Uncu, Beycan Hocaoğlu, and Serdar Vardar.
"Geoarchaeological Interpretations of the 'Troian Bay.'" In *Troia and the
Troad: Scientific Approaches*, edited by Günther A. Wagner, Ernst Pernicka,
and Hans-Peter Uerpmann, 379–401. Berlin: Springer, 2003.
https://doi.org/10.1007/978-3-662-05308-9_25

Kayan, İlhan. "Geoarchaeological Research at Troia and Its Environs." In
*Troia 1987–2012: Grabungen und Forschungen I — Forschungsgeschichte,
Methoden und Landschaft*, Teil 2, edited by Ernst Pernicka, Charles Brian
Rose, and Peter Jablonka, 694–727. Studia Troica Monographien 5. Bonn: Habelt,
2014.

Kraft, John C., İlhan Kayan, and Oğuz Erol. "Geomorphic Reconstructions in the
Environs of Ancient Troy." *Science* 209, no. 4458 (1980): 776–82.
https://doi.org/10.1126/science.209.4458.776

Kraft, John C., İlhan Kayan, Helmut Brückner, and George Rapp. "Sedimentary
Facies Patterns and the Interpretation of Paleogeographies of Ancient Troia."
In *Troia and the Troad: Scientific Approaches*, edited by Günther A. Wagner,
Ernst Pernicka, and Hans-Peter Uerpmann, 361–77. Berlin: Springer, 2003.

Kraft, John C., George (Rip) Rapp, İlhan Kayan, and John V. Luce. "Harbor
Areas at Ancient Troy: Sedimentology and Geomorphology Complement Homer's
*Iliad*." *Geology* 31, no. 2 (2003): 163–66.
https://doi.org/10.1130/0091-7613(2003)031<0163:HAAATS>2.0.CO;2

Homer. *Iliad*. Greek text checked against the Perseus Digital Library edition
(ed. rev. from the Allen/Perseus text), `sources/perseus/tlg0012.tlg001.perseus-grc2.xml`,
[Perseus](https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0133).

Strabo. *Geography* 13.1.31, 13.1.36. Trans. H. C. Hamilton and W. Falconer.
London: George Bell & Sons, 1903.
[Perseus](https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.01.0239%3Abook%3D13%3Achapter%3D1).

`docs/research/RESEARCH-PALEOGEOGRAPHY.md` and `docs/research/
RESEARCH-TROY-APPEARANCE.md` (this repository) — internal dossiers collating
and verifying the above against full texts; cited throughout for the exact
page numbers and verbatim quotations, which are not repeated a second time
here.
