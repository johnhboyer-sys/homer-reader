# Where the Achaean camp goes — state at 2026-08-16, parked

Everything below is measured against this repo's own DEM and layers. Nothing
here is drawn yet; no coordinate has been written into `apparatus/places.json`.

## Settled

**The camp is on the seaward (west) flank of the Sigeum ridge** (John, 2026-08-16),
following Luce 1984 (*OJA* 3:31–43) and Kraft, Rapp, Kayan & Luce 2003 (*Geology*
31:163–66). Luce explicitly rejects the older north-shore siting. The geographic
plate already letters ACHAEAN CAMP AND SHIPS there, so the signed-off sheet was
right and the panorama is the artifact that drifted.

Three independent lines converge on it:

1. **Geomorphology** — Luce and Kayan; the ship station is north of the Kesik cut,
   on the coast south of Sigeion.
2. **The fighting needs dry ground.** The panorama currently beaches the fleet
   north of the bay's head (39.9586–39.9823 N); half the sight line from there to
   Ilios is open water. South of 39.9583 N nothing drawn as water is in the way.
3. **The poem's own sense of scale.** Achilles' withdrawal is non-attendance, not
   distance — μήνιε νηυσὶ παρήμενος, οὔτέ ποτ' εἰς ἀγορὴν … αὖθι μένων (1.488–92);
   he watches the rout from his own stern and recognises Machaon (11.599–601); the
   embassy simply walks the beach to him (9.182). That is a compact camp. Centre to
   end is 1.6 km on the west flank, 3.5 km on the barrier, 8 km on the north shore.

## Killed, with the reason

- **North shore / bay mouth.** Has the Alexandrian orientation (Aristarchus and
  Janko IV 130–31: Ajax's end east toward Rhoiteion, Achilles' west toward Sigeion
  — see `docs/research/RESEARCH-POEM-TOPOGRAPHY.md:90, 308, 323`) but in 1200 BC
  that shore IS the bay's mouth. Traced length 16.4 km.
- **The barrier** (`barrier-bronze`). Same position on Bronze Age ground. Eleven
  vertices, 7.0 km, and the sheet's own note says its WIDTH is not surveyed — so we
  cannot say it held a fleet.
- **"Strabo's 12 stades."** NOT a candidate: 13.1.32 reports twelve stades as the
  *present* interval to the Achaean harbour, and 13.1.36 uses it to argue the site
  is too close to be Homer's Troy. It is the datum he rejects the identification
  with, not a proposal. (My error, caught by Codex.)
- **The horse-haul as evidence.** Checked by two independent agents: Homer gives no
  site, no route, no distance (Od. 8.504, the Trojans hauled it to the acropolis
  themselves, no breach). The Little Iliad, Virgil and Quintus breach a wall;
  Apollodorus does not; Tryphiodorus has the gate widened by Hera and Poseidon and
  calls the route long and cut by rivers. **No scholar has ever used the haul to
  locate the camp** — a clean negative from both passes. It cannot bear weight.

## The open question — pick one before generating coordinates

The west coast is mostly bank, not beach: it climbs 19–34 % within 60 m of the
waterline. Landable frontage is **3.10 km in six broken runs**:

| run | length | mean shore height |
|---|---|---|
| 39.9908 – 40.0025 N | 1,300 m | 2.7 m |
| 39.9625 – 39.9692 N | 750 m | 8.5 m |
| 39.9517 – 39.9562 N | 500 m | 8.7 m |
| 39.9400 – 39.9431 N | 350 m | 4.4 m |
| + two shorter | 150 m, 50 m | |

1,186 ships need 1.66 km at five ranks, 2.77 km at three, so **no single run holds
the fleet** — which is the poem's own complaint at 14.31–36 (the beach could not
hold them, so they hauled up προκρόσσας, in ranks).

- **A** — the 1,300 m northern run. Best beach, worst geography: it is at the bay
  mouth and puts the water back between camp and city.
- **B** — the two central runs, 39.9517–39.9692 (~1.9 km with a gap), around Kesik
  Tepe. Kayan's ship station; the head of the one firm corridor east to Troy;
  Kesik Tepe (the fourth century's "tomb of Achilles") stands in the middle of it.
  **Recommended.**
- **C** — all six runs, 39.940–40.003. Most honest about the ground, but gives the
  Chart Room pane nothing specific to frame.

## Also measured, for whoever picks this up

- **The seaward Bronze Age shoreline needs no cutting**: on this flank the 10 m
  contour lies 0–34 m inland of today's waterline at every latitude sampled
  (39.940–39.990) — within one 29.3 m grid cell. The modern coast IS the Bronze Age
  shore here. Only the bay side needed reconstruction.
- **The corridor to Troy.** Tolerating soft going, 6.7 km with 44 % across delta;
  refusing it, 13.1 km swinging 4 km south round the bay head. Both real; the truth
  depends on how bad the delta was, which the sources do not settle.
- **The Scamander's "peninsula" is real** — the river's own delta, 854 cells
  sampled, median 10.89 m, 95 % at or above the 10 m cut. Do not "fix" it; the
  earlier diagnosis that it was a fill artefact measured the channel bed (8.5 m)
  instead of the banks.
- **The panorama's fleet cannot fit this beach**: it draws three ranks at 13 m
  pitch, needing 5.1 km. Either the pitch or the rank count gives when it moves.
- **The camp is placed by nothing.** `achaean-camp-zone`'s own note says "no
  coordinate is ever given for the camp itself", so `camp()` in
  `scripts/panorama-stage3.py` places the fleet graphically — it marches forward
  from the camera and beaches at the first water it meets, which from that viewpoint
  is the bay. Fix the data, not the drawing rule.
- **The camera probably has to move.** The correct camp sits behind the left edge
  of the panorama's 72° cone from 39.9755, 26.1785 on heading 104°.

## Register shape agreed

Every place gets a coordinate; `positionBasis` carries the honesty:
`measured` · `tradition` (named) · `derived` (the poem states the relation, we
project it) · `editorial` (ours, declared). Of 44 Troad places, 7 are measured,
7 traditional, 10 derived (the panorama already carries a stated rule for each),
20 editorial. **This supersedes CLAUDE.md's "never a fabricated coordinate" for the
poem's places** (John, 2026-08-16: "we pick locations as best we can for what is not
scholarly attested … otherwise they have NO location"). The geographic plate stays
survey-only.

## Codex findings still to apply to `build/locations/camp-register.json`

Not yet actioned — the register will be regenerated once a run is chosen.

- 13.675 does not equal 13.679–81: 674–78 say Hector does not know his men are
  losing on the ships' left; 679 contrasts that with the breach where he stands.
- The chariot gate is at 12.120–23, not 12.118–19.
- Αἴαντος at 13.681 is a crux — Aristarchus and Janko read Locrian Ajax, Leaf
  Telamonian; 13.312–13 puts both Ajaxes among the middle ships. Do not resolve it
  silently.
- ἀκτή is not "headland"; 23.255–57 is the mound round the pyre, not the joint tomb
  (that is 23.243–48 planned, Od. 24.76–84 completed); no "marked ring" is stated.
- The citations attached to Agamemnon, Nestor and Idomeneus do not support the
  sectors claimed. There is no scholarly reconstruction placing individual berths;
  the ceiling is Pope's relay of Eustathius and Spondanus — the strongest at the
  ends, Odysseus in the middle for counsel — which places them *among the middle
  ships* and no closer.
- Six huts landed on or beside the ridge crown; inland offsets of 120–320 m are too
  large for a ridge this narrow.
