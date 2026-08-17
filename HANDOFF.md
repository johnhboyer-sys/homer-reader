# HANDOFF: the Chart Room pane, and the locations everything waits on
Generated: 2026-08-17 00:40 CDT · Session focus: the panorama margin, then the camp pane — which turned into sorting out where things actually are

## 1. Goal

The Chart Room's scene-location pane should open on a picture of where a scene
happens. It cannot, because two thirds of the places the poem names have no
coordinate, so the three artifacts that draw the Troad — the geographic plate,
the schematic sheet, the panorama — each invented their own positions in their
own coordinate system and disagree with each other. **Sorting the locations is
the whole job now; the pane is downstream of it.**

## 2. Why this matters / background

John's two observations drove the session. The panorama "looks like a video
game" work was finished last session; this one started on its margin, then he
asked whether the bay lies between the Achaeans and Troy. It does, in the
panorama, and it should not — which unwound into the camp never having been
placed at all. Then he rejected the schematic sheet outright ("ugly, too busy,
too small, tries to do the panorama and top down look, doesn't match").

He directs from rendered images and is reliably right about the symptom. Three
times this session my first diagnosis of a cause was wrong and measurement
corrected it. Measure before fixing; it saved us from deleting a real landform.

## 3. Current state

**`claude/build` @ `922b035c8`, pushed.** The geographic plate is unchanged and
still correct — it letters ACHAEAN CAMP AND SHIPS on the seaward flank, which
is where the scholarship puts it. Two new documents:
`docs/CAMP-LOCATION-STATE.md` (read this first) and the previously untracked
research dossiers.

**`plates/schematic-comp` @ `d0c4e947d`, pushed.** All 22 scene locations now
resolve (was 14 of 22). Five features added — Agamemnon's and Nestor's huts,
the Thracian camp, the Trojan bivouac, the Scamander/Simoeis confluence — and
`PlateLayer.claims` added to `shared/lib/plate.ts` so one drawn feature can BE
several places (the pyre, the barrow and the games ring are one ground with
three names). **John has rejected this sheet's design**, so the data is sound
and the drawing is not.

**`panorama/lit-plate` @ `742068e3d`, pushed.** Margin re-set to a measure
(five 380-character lines became five wrapped columns under headings, anchored
to the sheet foot so it cannot overrun again); 153 tests pass. John's verdict
on the result: **still too long.** The ground-cover specification is now
committed here.

Nothing is deployed. `main` still contains none of the plate system.

## 4. Key decisions (and why)

- **The camp is on the seaward (west) flank of the Sigeum ridge**, per Luce 1984
  and Kraft/Rapp/Kayan/Luce 2003. Three independent lines converge: the
  geomorphology, the fighting needing dry ground, and the poem's own scale —
  Achilles' withdrawal is non-attendance rather than distance (1.488-92), he
  sees and recognises Machaon from his own stern (11.599-601), the embassy walks
  the beach to him (9.182). Full argument in `docs/CAMP-LOCATION-STATE.md`.
- **Every place gets a coordinate**, with `positionBasis` carrying the honesty:
  `measured` · `tradition` · `derived` · `editorial`. This supersedes CLAUDE.md's
  "never a fabricated coordinate" for the poem's places (John: "we pick locations
  as best we can for what is not scholarly attested … otherwise they have NO
  location"). The geographic plate stays survey-only.
- **One ground may carry several names** rather than several anchors, where the
  poem gives one site (Il. 23.255-58).
- **The top-down plate, not the panorama, is the pane's workhorse.** It crops to
  any lat/lon, so all 466 coords-bearing scenes get a frame free; the panorama
  needs a hand-authored camera target per place and covers 33 scenes.

## 5. Traps and dead ends

- **Measure before fixing.** The Scamander's "peninsula" looked like a fill
  artefact; it is the river's own delta (854 cells, median 10.89 m, 95 % above
  the 10 m cut). My first measurement sampled the channel BED and concluded
  there was no landform. Three hypotheses died before that one; the correct
  outcome was no change at all.
- **`BLUR_PASSES`, the swamp overlap and the edge smoothing are all red
  herrings** for that defect — swept and disproved, don't re-run them.
- **"Strabo's 12 stades" is not a camp proposal.** 13.1.32 reports it as the
  *present* interval; 13.1.36 uses it to argue the site is too CLOSE to be
  Homer's Troy. I used it backwards for an hour.
- **The horse-haul cannot locate the camp.** Two independent passes: Homer gives
  no site, route or distance, and no scholar has ever made the argument.
- **The seaward Bronze Age shoreline does not need cutting** — the 10 m contour
  lies within one grid cell of today's waterline all along that flank.
- **Codex is a second opinion, not an oracle** (John). It caught real citation
  errors and measured six huts onto the ridge crown; it does not know our
  dossiers, and where it contradicts what we verified first-hand, our record
  stands. Run it via `codex exec … < /dev/null` — the plugin's forwarder
  backgrounds the task and cannot retrieve it.
- The browser pane suspends `requestAnimationFrame` when backgrounded, which
  looks exactly like a broken scroll handler. It isn't.

## 6. Relevant files and pointers

- `docs/CAMP-LOCATION-STATE.md` — **start here.** What is settled, what is
  killed and why, the six landable runs with lengths, and the one pick waiting.
- `docs/research/RESEARCH-POEM-TOPOGRAPHY.md:90, 308, 323` — Janko IV 130-31 and
  Aristarchus on left/right; the orientation the west flank cannot inherit.
- `docs/TROAD-CARTOGRAPHY.md` — the camp's textual layout (§2) and the drawing
  conventions; note its schematic register is Pope 1716, which is why that sheet
  has no bay and cannot match the others.
- `apparatus/plates/trojan-plain.json` — the geographic sheet, signed off.
- `scripts/render-plates.mjs` — renders any sheet or a lat/lon crop at N×; the
  only honest way to judge a plate change.
- `scripts/panorama-stage3.py` (in `../homer-reader-takeA`) — the panorama.
  `camp()` places the fleet graphically and is the thing to fix once the camp
  has a coordinate.

---
## Prompt for the fresh agent

You are picking up the Troy work on `~/Developer/homer-reader` — a digital
Landmark-style edition of the Iliad and Odyssey. Read `CLAUDE.md` first; it
carries the standing rules and this file does not repeat them. Then read
`docs/CAMP-LOCATION-STATE.md` in full, and the pointers in §6 above.

The immediate question is one pick: **which of the six landable runs on the west
coast the Achaean camp occupies** (the file sets out three arrangements; B, the
two central runs around Kesik Tepe, is recommended). Nothing downstream can be
generated until John rules on it — not the camp's twelve features, not the
seventeen remaining locations, not the panorama's fleet, and not the pane.

Do not draw anything on the schematic sheet: John has rejected its design, and
the open question there is whether to keep a schematic register at all or draw
the poem's places on the geographic basemap at a closer zoom.

Treat every claim here as context to verify, not fact to trust. Rendering an
image and looking at it is a required gate — tests have repeatedly stayed green
while a plate was visibly wrong, and this session's most expensive errors were
all confident diagnoses that measurement disproved.
