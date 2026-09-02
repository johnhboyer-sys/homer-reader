# Panorama lane — paused 2026-08-10 21:14, resume after usage reset

## What this is

**"The Plain of Troy from the Achaean Camp"** — an annotated panorama, a third
register alongside the map plates and the generated renditions. The reader's
point of view for the whole Iliad: everything the action crosses lies on one
sightline in depth order.

John's brief: "the view from the Achaean camp to Troy... Rich detail. Not
overstated. Stylized tastefully. Landmark style." Labels must be **dynamic so
they don't overcrowd**.

## State at pause

Worktree `../homer-reader-panorama` (branch off `claude/build`), nothing
committed. Two new untracked files:

- `scripts/panorama-profile.py`
- `scripts/panorama-fragment.py`

The lane was mid-work adding `--pp-sky-top` / `--pp-sky-horizon` gradient tokens
to `THEME_TOKENS` when stopped. **It had not yet reported the DEM profile
numbers**, which was its first checkpoint — so nothing is verified yet.

## Decisions already made (do not re-open)

- **Register: schematic.** The terrain profile is a true DEM-derived sightline
  and says so; the waypoints are the poem's own order along that line and say
  so. Almost nothing on the plain has a defensible coordinate — the ford, the
  oak, the fig tree, the tomb of Ilos, the two springs, the Achaean wall and
  ditch, the Scaean Gate. Carry them all with `positionBasis: "conjectural"`.
  **Never fabricate a coordinate.**
- **Visual register: engraved line-and-tint**, the family the map plates live
  in — NOT the photoreal look of the generated renditions. It must sit
  coherently beside the sheets. Colour is free; WCAG AA binds both themes;
  every colour a `var()` token.
- **Labels are zoom-tiered**, and the declutter comes from the form, not from a
  smarter solver. Depth bands (foreground camp / midground plain / background
  city and Ida) mean labels cannot collide by construction.
  - Tier 1, always: Troy, Scamander, Ida, the ships/camp, the sea.
  - Tier 2, on zoom: Simoeis, the ford, Rhoiteion, Sigeion, Callicolone, the
    wall and ditch.
  - Tier 3, deepest: the oak, the fig tree, the tomb of Ilos, the springs, the
    wagon-road, camp sectors by holder.
  - Labels must not magnify (`pp-label-descale`).

## The sequence — unchanged, and the checkpoints are the point

1. **DEM profile first.** Viewpoint on the Sigeum ridge (the attested camp zone,
   ruling 2e-iv: Kraft, Rapp, Kayan & Luce 2003 after Luce 1998), looking ESE to
   Hisarlık, ~4–5 km. Sample `sources/terrain-tiles/*-contours.json` and
   `sources/copernicus-dem/`. Control points: Hisarlık 36 m, ground rising to
   58 m ~1.5 km east, Ida far SE. **Report the numbers. If the DEM will not give
   a usable profile, STOP — do not draw a horizon by hand.**
2. **One fragment at final quality** — the city on its spur, ~quarter frame,
   two or three labels. Render, LOOK, report the PNG path. If the technique
   misses the bar it dies here for the cost of a fragment.
3. Only then, the full panorama.

## Content, in depth order

- **Foreground** — ships on the beach, the camp, the wall and ditch (Il.
  7.436–41). Sectors by holder, never left/right: Ajax's end east toward
  Rhoiteion, Achilles' end west toward Sigeion (ruling 2a). The 2026-09-02
  outer-flank beach does not change this: Sigeion is still the northern end
  of the ridge, Rhoiteion the other headland.
- **Midground** — the plain; Scamander and Simoeis; the ford; the wagon-road;
  the tomb of Ilos (11.166–72); the oak; the fig tree; the two springs
  (22.145–56).
- **Background** — Troy on its spur, walls and towers, the great tower and the
  Scaean Gate (3.145–53, 22.6); Callicolone; higher ground east; Ida.
- **Framing** — the Sigeion and Rhoiteion headlands.

Citations from `docs/research/RESEARCH-POEM-TOPOGRAPHY.md` and
`docs/research/RESEARCH-TROY-APPEARANCE.md` §1. Every waypoint carries its Iliad
citation in the DATA, not just the prose.

## Do not touch

`shared/lib/plate.ts`, `app/src/components/MapsPage.svelte`,
`app/src/components/maps/PlatePanel.svelte` — the map lane's branch
`plates/label-class-symbology` (commit `3c4a4a9e2`, worktree
`../homer-reader-plates`) holds changes to the first of these and is unmerged.
Rebase or merge that first, or stay clear of it.

## Why the panorama matters

It carries the Iliad's topography that neither existing sheet can. The ford, the
oak, the fig tree, the tomb of Ilos, the wagon-road, the springs have been
unmappable all along — putting them at guessed coordinates on a geographic sheet
is the exact failure John ruled against. On a schematic panorama they are not
guesses; they are the poem's own order along a sightline.

## Two plates (2026-09-02)

John, 14:47: the single oblique "The Ships, the Bay, and Ilios" is two plates
from the same script. One camera cannot show the fleet on the Aegean flank and
Troy across the bay at once — Troy is invisible from the camp (Luce's
placement; ruling 4 in `docs/TROY-MAPS-TODO.md` § "Rulings 2026-09-02").

- **Plate A, "The Bay and Ilios"** — the previous composition, looking
  east-south-east from above the camp. Fleet and huts off-plate (they sit
  behind the camera). Wall and ditch stay where they fall in frame.
- **Plate B, "The Ships on the Aegean Shore"** — camera over the sea looking
  at the flank. Fleet, huts, wall and ditch draw as now. Presets B1 and B2
  are both stored; `B` aliases B1 until the orchestrator picks.

`--plate A|B|B1|B2` applies the named camera before the existing camera
flags, which still override. Outputs are `stage3-<plate>-full<tag>.{svg,png}`
and `stage3-<plate>-camera-targets<tag>.json`. Nothing is copied into
`apparatus/`.
