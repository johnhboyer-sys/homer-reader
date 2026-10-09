# TROY-RENDITIONS-APPARATUS — captions, labels, and sources for the two Troy pictures

**Date:** 2026-08-10.
**Consumed by:** the two artist's-reconstruction images of Troy VI generated per
`docs/research/TROY-PROMPT-PACK.md` (View A, top-down; View B, oblique bird's-eye over
the Bay of Troy) once John picks the winning variant of each. Not a plate — these are
pictures, their own register, sitting alongside the engraved map plates rather than
pretending to be one.

**Sources consumed:** `docs/research/RESEARCH-TROY-APPEARANCE.md`,
`docs/research/RESEARCH-CITADEL.md`, `docs/research/TROY-PROMPT-PACK.md`,
`apparatus/plates/troy-citadel.json` (for the plate JSON `sources`-block shape),
`docs/APPARATUS-SCHEMAS.md`, `apparatus/places.json` (existing certainty/tradition
treatment for the Scaean Gate, Dardanian Gate, the oak, the two springs).

**Register rule followed throughout:** the certainty framing carries the honesty; the
prose states what the poem and the spade say as fact and does not re-apologise for the
gaps between them (CLAUDE.md, "Rich, not hedging," John 2026-07-28). Dates are BC/AD.

---

## 1. Captions

Both captions name the image as an artist's reconstruction, state plainly that it was
generated with an image model from a researched brief (John's ruling, not optional),
and separate three tiers of claim: **attested** (excavated fact), **inferred by
analogy** (§3 of `RESEARCH-TROY-APPEARANCE.md`, ranked), and **artist's licence**
(§7's blanks). Neither hedges past that.

### 1.1 Top-down view — 135 words

> An artist's reconstruction of Troy VI, the city of the Iliad, seen from directly
> overhead, circa 1200 BC. The image was generated with an image model, prompted from
> a research brief built on Dörpfeld's 1902 excavation and the poem's own architectural
> lines. Attested by the spade: the wall's inward-battered limestone face, a faceted
> circuit of roughly 540 to 550 metres enclosing about two hectares, the gates and
> towers at Dörpfeld's own letters, and flat clay roofs, which he recorded directly
> rather than inferred. The terraced streets, the packed courtyard-chamber palace, and
> the second storeys argue from the nearest defensible analogy: Hittite Hattusa's
> fortification profile and the region's stone-below, timber-above house form. The
> exact height of the mudbrick collar, tower roofs, window placement, and Priam's floor
> plan are the artist's licence, drawn where no excavation reaches.

### 1.2 Oblique bird's-eye view — 131 words

> An artist's reconstruction of Troy VI, the Iliad's city, seen obliquely over the Bay
> of Troy, circa 1200 BC, walls rising toward the citadel's crown. Generated with an
> image model, prompted from a research brief built on Dörpfeld's excavation and the
> poem's own lines. Attested by the spade: the battered stone face, its published scarp
> 13 to 22 degrees off vertical by sector; gates and towers by Dörpfeld's own letters;
> flat clay roofs, his own recorded finding. Terraced houses climbing toward the
> summit, some two storeys, argue from the nearest defensible analogy: Hittite
> Hattusa's wall profile, Aegean house form at Akrotiri. The mudbrick collar's height,
> tower roofs, windows, and storey counts city-wide are the artist's licence, drawn
> where excavation does not reach. Mount Ida stands real and regional on the horizon.

### 1.3 Notes on drafting

- "Circa 1200 BC" is the date `TROY-PROMPT-PACK.md` uses throughout for the generated
  scene and is the safest one to caption with; it names the Late Bronze Age setting
  without asserting a specific destruction year, which neither research file settles.
- Wall thickness (4.5–5 m) was cut from both drafts for length; it is covered by the
  `sources` block (§3) and belongs more naturally on a future plate's dimension table
  than in an 80–140-word caption already carrying three tiers of claim.
- "Priam's floor plan" (top-down) stands in for the fuller §7 line "Palace centre on
  the summit … Plan of Priam's house as excavated (destroyed by later levelling)" —
  the caption states the gap, not the reason for it; the reason is available in the
  overlay note (§2, item 1) and the research file for a reader who wants it.
- Neither caption states a fall date or the Trojan War's traditional date (Eratosthenes'
  1184 BC and kin) — that claim belongs to a different apparatus surface (chronology)
  and isn't sourced in the two files this brief scoped me to.

---

## 2. Label overlay — top-down view only

The top-down image ships pictorially; labels ride a separate toggleable SVG layer over
it. This project's actual plate typography implements **four** label roles
(`shared/lib/plate.ts` `LabelRole`), not five: `region` (letterspaced caps, area
names), `settlement` (bold roman, point features — the heaviest mark despite not being
the largest, per `docs/TROAD-CARTOGRAPHY.md` §5's Imhof rule), `water` (italic), and
`minor` (small roman, secondary point/line features). The brief's "settlement/feature/
region, five-class system" is the print Landmark's own convention
(`docs/TROAD-CARTOGRAPHY.md` line 440, "Five type classes") describing continents,
two weights of city, peoples, water, and mountains — it is the print *inspiration*,
not what ships here. I map every candidate below onto the four roles this codebase
actually renders, and flag the mapping explicitly so it isn't mistaken for a fifth
role that doesn't exist.

| # | Label text | Class | Citation | How securely placed |
|---|---|---|---|---|
| 1 | **Priam's house** | `settlement` | Il. 2.788 (agora at his doors), 6.242–250 (fifty + twelve dressed-stone chambers, polished porticoes, courtyard) | Placed at the citadel's high point by narrative logic (`ἐν πόλει ἄκρῃ`, near Hector's and Paris's houses); the actual excavated summit was levelled in later periods, so no plan survives under this label. Certainty: `traditional` — the high-point location is the standard equation since Dörpfeld, not a surveyed footprint. |
| 2 | **The agora** | `region` | Il. 2.788–789, 7.345–346 ("at Priam's doors … on the acropolis") | An area label immediately adjacent to Priam's house, not a separate point. No dimension or shape is given by the poem; drawn as open ground abutting the palace front. Certainty: `traditional`. |
| 3 | **House of Hector** | `minor` | Il. 6.313–317 (built near Priam's and Paris's, `ἐν πόλει ἄκρῃ`), 6.370 (`δόμους εὖ ναιετάοντας`) | Clustered near Priam's house per the text; no independent plot. Certainty: `traditional`. |
| 4 | **House of Paris** | `minor` | Il. 6.313–317 | Same clustering, same basis. Certainty: `traditional`. |
| 5 | **Temple of Athena** | `settlement` | Il. 6.88, 6.297–300 (`νηόν … ἐν πόλει ἄκρῃ`, doors a priestess opens) | On the acropolis with the royal houses; no excavated Bronze Age temple survives at Hisarlık to anchor it to (a much later Athena temple stands on the site, a different period entirely — see DO-NOT-DRAW item in `RESEARCH-TROY-APPEARANCE.md` §6.2 against bleeding Roman Ilion into this view). Certainty: `traditional`. |
| 6 | **Shrine of Apollo (in Pergamos)** | `minor` | Il. 4.508, 5.446, 5.460, 6.512, 7.21, 24.700 | "High Pergamos" is the citadel's own high ground, the same zone as #5; if both are drawn, they need visibly separate positions or the label reads as one duplicate mark. Certainty: `traditional`. |
| 7 | **The great tower** | `settlement` | Il. 3.145–154 (elders on the tower over the gate), 3.384, 6.373, 6.386, 21.526–535, 22.6, 22.97 | Dominant skyline feature paired with the gate below it (#8/#9 — see the honesty constraint, §2.1). Certainty: `traditional` as a paired complex; the specific excavated tower it corresponds to is unsettled (`RESEARCH-CITADEL.md` §1.3 records Dörpfeld's own uncertainty between VI g and a lost gate tower). |
| 8/9 | **The Scaean Gate** / **the Dardanian Gate** | `settlement` | Scaean: Il. 3.145, 6.393, 18.453, 22.360, 6.237=9.354=11.170 (paired with the oak). Dardanian: Il. 5.789, 22.194, 22.413 | See §2.1 below — treatment recommended, not decided. |
| 10 | **The wagon-road** | `minor` (route) | Il. 22.146 (`ἀμαξιτόν`, running under the wall) | Traced hugging the exterior wall face on the plain-facing side; exact course beyond "under the wall" is not given. Certainty: `traditional`. |
| 11 | **The two springs of the Scamander** | `water` | Il. 22.147–152 | Existing gazetteer entry (`two-springs-of-scamander`) is already `speculative`: no thermal pair survives at the site (Wolkersdorfer et al. 2021). Carry that tier through to the overlay rather than upgrading it for the picture. |
| 12 | **The oak** | `minor` | Il. 6.237 = 9.354 = 11.170 (formulaically paired with the Scaean Gate), 5.693, 7.60 | Position is dependent on wherever the Scaean Gate label lands (§2.1) — moving one moves the other. Certainty: `speculative` (gazetteer's existing `oak-of-zeus` tier). |
| 13 | **The wild fig tree** | `minor` | Il. 6.433–434 (the wall's weak point), 11.166–167, 22.145 | The gazetteer's own `fig-tree` entry records that the poem sets a fig in two places that don't agree, and that its anchor takes the tree under the wall by the scalable stretch — carry that same choice and the same caveat here rather than resolving it silently for the picture. No "fig-tree hill" is named or dimensioned anywhere in the corpus; if the picture wants elevated ground at that spot it is `[artist's licence]` per `TROY-PROMPT-PACK.md`, not a poem fact. Certainty: `speculative`. |

### 2.1 The Scaean Gate naming question — recommendation, John's call

**The constraint.** No excavated gate is securely the Scaean or Dardanian Gate.
Dörpfeld himself calls his Scaean placement *vermutungsweise* (conjecturally) and puts
it at the north-west corner — precisely where nothing survives to check him
(`RESEARCH-CITADEL.md` §1.4, §5). The standing project ruling for the *cartographic*
plates (Plate A/B of `troy-citadel.json`) is to label gates by Dörpfeld's excavated
letters (VI S, VI T, VI U) and keep the Homeric names in the note only
(`RESEARCH-CITADEL.md`, "Gates as Dörpfeld letters (2e-ii)").

**Recommendation: do not carry that convention onto this picture. Use the Homeric
names — "the Scaean Gate," "the Dardanian Gate" — as the primary overlay text,
directly.**

**Reasoning.** The cartographic plates carry Dörpfeld's letters *because* they claim to
trace real excavated geometry, and the letter/note split is how they stay honest about
the difference between a surveyed structure and a Homeric guess about what it was
called. This picture makes no such claim anywhere else on its face: every other label in
this table — Priam's house, the agora, Hector's and Paris's houses, both shrines — is a
Homeric name with no Dörpfeld-letter equivalent, because the picture is confessedly the
poem's city throughout, generated art with no surveyed line under it at all. Introducing
Dörpfeld letters for the gates alone would import the cartographic register's vocabulary
into the one place on this specific image where it doesn't belong, and would read to a
reader as if the gates were more certain than the palace next to them, when the opposite
is true. The honesty work here is better done the way the rest of this table already
does it: an unmistakably `speculative`-tier mark (broken inner ring, per the pin
convention `docs/APPARATUS-SCHEMAS.md` documents) and a note that says outright there is
no scholarly consensus and names the candidates Dörpfeld himself named (the lost
north-west gate, his own preference; the gate beside tower VI g, his stated
alternative; and, against him, the surviving South Gate VI T, which is where the
Dardanian Gate is traditionally placed instead).

**Two traps to build against, whichever way this goes:**

- **Vici.org record 20632** publishes a "Scaean Gate" point at 39.957352, 26.237906
  with a false "±0–5 m" accuracy claim and cites no source at all
  (`RESEARCH-CITADEL.md` §4.5). Never let this coordinate reach the overlay by any
  automated path.
- **The UNESCO/ICOMOS 1998 nomination form's own "Exact location" field** (26°19′E,
  39°55′N) is a clerical error roughly 8 km off the actual site
  (`RESEARCH-CITADEL.md` §6 item 8). Never harvest it for anything.

Neither trap is a live risk for a hand-authored overlay, but both are worth naming here
because a future automated pass (tying this overlay to the gazetteer, say) could pull
either in without a human noticing.

---

## 3. `sources` block (draft JSON, both images)

Modelled on the plate `sources` shape (`apparatus/plates/troy-citadel.json`: an array
of `{cite, url?}`, Chicago for books/articles, hyperlinks for web resources and
databases). Both images draw the same evidentiary base, so one array serves both; a
`claims` note beside each entry (not part of the JSON — added here for review only)
names which caption/overlay assertions it backs.

```json
[
  {
    "cite": "Dörpfeld, Wilhelm. Troja und Ilion: Ergebnisse der Ausgrabungen in den vorhistorischen und historischen Schichten von Ilion, 1870–1894. 2 vols. Athens: Beck & Barth, 1902.",
    "url": "https://archive.org/details/trojaundilionerg02dorp"
  },
  {
    "cite": "Tolman, Herbert Cushing, and Gilbert Campbell Scoggin. Mycenaean Troy: Based on Dörpfeld's Excavations in the Sixth of the Nine Buried Cities at Hissarlik. New York: American Book Company, 1903."
  },
  {
    "cite": "Blegen, Carl W. Troy and the Trojans. New York: Praeger, 1963."
  },
  {
    "cite": "Rose, C. Brian. The Archaeology of Greek and Roman Troy. Cambridge: Cambridge University Press, 2014."
  },
  {
    "cite": "Korfmann, Manfred, and Dietrich Mannsperger. Troia: Ein historischer Überblick und Rundgang. Stuttgart: Theiss, 1998."
  },
  {
    "cite": "Rutter, Jeremy B. \"Troy VI.\" In Aegean Prehistoric Archaeology, Lesson 23. Dartmouth College.",
    "url": "https://sites.dartmouth.edu/aegean-prehistory/lessons/lesson-23-narrative/"
  },
  {
    "cite": "UNESCO / ICOMOS. Nomination documentation and evaluation, Archaeological Site of Troy (WHC 849), 1998."
  },
  {
    "cite": "Kraft, John C., İlhan Kayan, and Oğuz Erol. \"Geomorphic Reconstructions in the Environs of Ancient Troy.\" Science 209, no. 4458 (1980): 776–82."
  },
  {
    "cite": "Kraft, John C., George Rapp, İlhan Kayan, and John V. Luce. \"Harbor Areas at Ancient Troy: Sedimentology and Geomorphology Complement Homer's Iliad.\" Geology 31, no. 2 (2003): 163–66."
  },
  {
    "cite": "Wolkersdorfer, Christian, et al. \"Hydrochemical investigations to locate Homer's hot and cold springs of Troia (Troy)/Turkey.\" CATENA 200 (2021): 105070.",
    "url": "https://doi.org/10.1016/j.catena.2020.105070"
  },
  {
    "cite": "Leaf, Walter. Troy: A Study in Homeric Geography. London: Macmillan, 1912."
  },
  {
    "cite": "Cook, J. M. The Troad: An Archaeological and Topographical Study. Oxford: Clarendon Press, 1973."
  }
]
```

Claim map (review-only, not shipped):

- **Wall batter, scarp ratios, ashlar coursing, thickness, gate/tower letters** —
  Dörpfeld 1902 (primary geometry); Tolman & Scoggin 1903 (PD English digest of the same
  dimensions); Rutter Lesson 23 (secondary synthesis of Blegen's re-excavation).
- **Flat clay roofs, attested not inferred** — Dörpfeld 1902 (Tolman & Scoggin §9).
- **Circuit ~540–550 m, ~2 ha, gate/tower dimensions** — Tolman & Scoggin 1903;
  UNESCO/ICOMOS 1998.
- **Hittite Hattusa analogy for wall profile** — Rutter Lesson 23; Rose 2014;
  Korfmann & Mannsperger 1998 (the standard framing of Troy as an Anatolian, not
  Mycenaean, fortification tradition).
- **Aegean house-form analogy (Akrotiri)** — carried in `RESEARCH-TROY-APPEARANCE.md`
  §3.4 without its own primary citation in that file; if this analogy is drawn on
  directly in a future caption revision, add a Thera/Akrotiri excavation citation
  (Marinatos or Doumas) rather than leaving the claim uncited — flagged in §4 below as
  too thin to caption past what §3.4 already states in prose.
- **Landscape: plain, springs, shoreline, Mount Ida, Samothrace** — Kraft, Kayan &
  Erol 1980; Kraft et al. 2003; Wolkersdorfer et al. 2021 (springs specifically).
- **Scaean/Dardanian Gate identification dispute** — Dörpfeld 1902; Leaf 1912; Cook
  1973 (all three already carried in `apparatus/places.json`'s existing entries for
  `scaean-gate`, `dardanian-gates`, `great-tower-of-ilios`, `oak-of-zeus`).

---

## 4. Integration notes

Where these wire in, one line each. **None of these files were edited by this lane** —
`shared/lib/plate.ts` and `app/src/components/MapsPage.svelte` are being worked by
another lane in a separate worktree; the rest are named only as a map of what a future
integration pass touches.

- `shared/lib/plate.ts` — owns `LabelRole`/`LAYER_LABEL_ROLE` and the pin-tier
  symbol drawing (§2's `settlement`/`region`/`water`/`minor` roles and the
  certainty-tier marks used by the recommendation in §2.1). A picture overlay isn't a
  plate layer, so this file's renderer isn't the natural home for it as-is; it's named
  here because the overlay's visual vocabulary (label roles, tier marks) should stay
  visually consistent with what this file already draws for the map plates, even
  though the overlay itself needs its own rendering path.
- `app/src/components/MapsPage.svelte` — the page that currently hosts `PlatePanel`
  for `troad`, `trojan-plain`, and (per code comments) an unwired `troy-citadel`
  plate. Whichever component ends up showing these two pictures likely lives near or
  inside this page's Troy section.
- `app/src/components/maps/PlatePanel.svelte` — the existing plate-rendering
  component (`plateId`/`places`/`title` props, `shared/lib/plate.ts` under it). Not a
  natural fit for a static image + toggleable label layer as-is; a sibling component
  (e.g. `TroyRenditionPanel.svelte`) is more likely than extending this one, since
  these images have no `bbox`/`kind: geographic|schematic` geometry to project.
- `apparatus/plates/troy-citadel.json` — the only existing plate carrying Troy VI
  geometry; not where these pictures' data belongs (they have no lat/lon or unit-space
  geometry to be a `layers` entry), but its `sources` block (§3 above) is the template
  this document's own JSON follows, and the `troy-citadel` plate is itself still
  unwired to `MapsPage.svelte` (WIP per project memory) — worth resolving both at once
  rather than shipping the pictures ahead of the plate they'll sit beside.
- **No schema yet exists** for "a picture + a toggleable label overlay" as an
  apparatus type — `docs/APPARATUS-SCHEMAS.md` defines `scenes`, `places`, `plates`,
  `characters`, `catalogue`, `speeches`, but nothing for a generated image with a
  caption and an SVG label layer. That schema decision (a new `renditions.json`? an
  extension of the plate schema? component-local data?) is itself an integration item
  for whoever picks this up, not decided here.

---

## 5. Too thin in the research to caption honestly

- **Storey count for Priam's palace specifically.** §7 of `RESEARCH-TROY-APPEARANCE.md`
  gives "several two-storey indicators" for Troy VI houses generally (stairs, pillar
  supports), and separately notes Helen's chamber is `ὑψόροφον` ("high-roofed," 3.423)
  — but nothing ties either fact to Priam's house by name. The captions state storey
  counts as licence in general terms rather than claiming a specific number for the
  palace.
- **The Akrotiri/Thera analogy's own citation.** `RESEARCH-TROY-APPEARANCE.md` §3.4
  describes what the Akrotiri frescoes show (multi-storey houses, windows, balconies)
  without citing a specific excavation report in that section's own text — the file's
  §8.3 citation list doesn't carry a Thera source either. I used the analogy in both
  captions and the sources-claim map (§3) because the research file treats it as
  settled enough to rank ("Rank 4"), but a primary Akrotiri citation (Marinatos's
  excavation reports, or Doumas's synthesis) should be added before this ships if the
  analogy is named as specifically as I've named it here.
- **A defensible position for the agora's extent.** The poem gives a location ("at
  Priam's doors") and nothing else — no size, shape, or paving. The overlay entry
  (§2, row 2) says this plainly; I did not attempt to infer a footprint from any
  analogy, because none of the three research files offers one for an open assembly
  space specifically (the Hattusa/Mycenae analogies in §3 are about walls and gates,
  not civic open ground).
- **Which of the two shrine buildings (Athena, Apollo) the image actually drew where.**
  Until John picks the winning variant, I don't know whether the generated image shows
  one shrine cluster or two distinguishable buildings at the summit — the prompt pack
  asks for "two small flat-roofed shrine buildings" in most variants, but the overlay
  table in §2 was written from the prompt brief, not from a specific rendered image.
  Whoever wires the overlay to the chosen image needs to check both shrine marks land
  on buildings that are actually visible and separated in the picture, not on empty
  roofscape.
