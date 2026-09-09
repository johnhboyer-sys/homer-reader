# Troy & Troad plates — handoff to the drawing session (2026-07-30, evening)

Supersedes `TROY-MAPS-HANDOFF-2.md` as the working brief. That file and
`TROY-MAPS-HANDOFF.md` are **historical** — annotated where superseded, kept for
the record; do not take drawing instructions from them. This session's job is
DRAWING. The research campaign is complete: every source read or scope-closed,
every editorial decision ruled (one deferral: dardania). No input from John is
needed until the review gate.

## 0. Session discipline (before anything)

- John runs concurrent Claude Code sessions in this checkout. Before branching,
  diff `git status` against a clean start; if files you do not own are dirty,
  STOP and ask. Prefer a worktree (`git worktree add ../homer-reader-plates
  claude/build`), symlinking `build/` from the main checkout (read-only) to
  avoid the 6-minute rebuild.
- Base branch: `claude/build`. Stacked PR into `claude/build` per CLAUDE.md.
- 5-agent cap; every spawn passes `model:` explicitly; Codex is BACK on roster
  (Sol adversarial review, Terra implementer); Grok takes content gates.
- Stage explicit FILES, never directories, while any agent runs.

## 1. The work queue, in order

`docs/TROY-MAPS-TODO.md` § "Next work session (no input from John needed)" is
the authoritative list. Summary and sequencing:

1. **Item 0 — apply the rulings to data** (small, verifiable, commit first):
   - Callicolone → Kara Tepe pin `39.95653/26.33947` (already in places.json
     from the morning) — **raise tier to `traditional`**, tradition names
     Spratt/Forchhammer/Cook/Luce, Leaf's Ophrynion in the note as dissent
     (ruling 2d; RESEARCH-TROAD-TOPOGRAPHY §9.1).
   - chryse: correct the tradition string to Strabo 13.1.63's actual direction
     (2e-i; RESEARCH-TROAD-TOPOGRAPHY §8.1).
   - thymbra: re-anchor to Pleiades **550929**, Thymbras Pedion (2e-iii).
   - Citadel gate labels: Dörpfeld letters **VI T / VI U / VI S** on any sheet;
     the Scaean/Dardanian pairing lives in notes only (2e-ii — supersedes D9).
   - Achaean camp on the GEOGRAPHIC plate: **one** attributed zone, the Sigeum
     ridge (Kraft, Rapp, Kayan & Luce 2003, after Luce 1998); Beşika in the
     note as the named rival; never a coordinate pin (2e-iv — supersedes D4).
   - D6 note text: use the reworded citation chain verbatim from the D6 block
     in TROY-MAPS-TODO ("the reading of the cut as the Achaean wall and ditch
     is Luce's (1998); Kraft, Rapp, Kayan & Luce 2003 print it, but the
     paper's citation for it — Kayan 1995 — does not contain it").
2. **Contour re-cut** per RESEARCH-BASEMAP-DATA.md: relief `tol_deg` → 0.00100
   (Troad) / 0.00012 (plain), plain `decimate` → 1, **no smoothing**, cull
   degenerate rings. This fixes the measured defect (contours decimated 4–7×
   coarser than coasts, then spline-smoothed into lobes). Re-render and LOOK
   at 3.5×+ crops before reporting done.
3. **Anchor the 38 schematic places** from RESEARCH-POEM-TOPOGRAPHY (31
   anchorable; camp block first). Sector labels by holder — "Ajax's end",
   "Achilles' end" — never the words left/right; PLACEMENT follows the
   Greek-side axis: **Ajax east toward Rhoiteion, Achilles west toward
   Sigeion** (ruling 2a extended; Hainsworth's dissent goes in the note; tier
   speculative). `scamandrian-plain` resolves to the unzoomed sheet. Then
   route the Chart Room to the schematic plate when a scene's places are
   schematic-only → ~280 scenes gain a real frame. Anchors are
   `plateAnchors` + `positionBasis: "conjectural"`, schematic sheet ONLY —
   a conjectural anchor on the geographic sheet is a fabricated coordinate.
4. **Label work**: collision avoidance (candidate positions + penalty
   function, no hand-nudging) and the text-on-path direction fix (flip when
   net direction is leftward).
5. **Plate UX**: in-panel pan/zoom (wheel + drag + keys + reset) as a camera
   `<g>` transform; **scale bar tracks zoom**; **labels never magnify**;
   the 28 debug checkboxes become the certainty filter (+ relief, rivers,
   shoreline toggle).
6. **Plate A — Troy VI, the citadel** per RESEARCH-CITADEL.md DESIGN SPEC:
   trace Tafel V (`research-cache/dorpfeld-1902-tafel-5.jpg`, cached, opened,
   verified); the missing north side drawn as absent OR completed from
   Fig. 470 with the restoration visibly distinguished (line style/tone,
   stated in the layer note); gates by Dörpfeld letters; dimensions from
   Tolman & Scoggin 1903 as PD prose; georeference per CITADEL §2
   (feature-rectified, grid as scale check). This is the plate the reader
   meets: "what did Troy look like when Hector ran its walls?" — one phase,
   never mixed. **Plate B (phase-coloured excavation history) is NOT built
   this session** — optional, after A ships, John's call.
7. **Hardening**: `sources` mandatory on every plate in `validate_plate`;
   fix the `shore-bronze` Rhoiteion terminus (−0.4 m vertex); add ἴστωρ to
   the lexicon slices (18.501); shore-bronze layer note re-attribution.
8. **Attribution page**: Copernicus 6(b) wording + 6(c) liability sentence +
   SRTM/USGS credit (RESEARCH-BASEMAP-DATA §5).

The Shield redesign (RESEARCH-SHIELD; register ruled: refined Metallmalerei
metallics, no bard, Edwards's split siege ring) is its own lane — take it this
session only if the queue above lands with room to spare.

## 2. The rulings digest (all John's, 2026-07-30 — full texts in TROY-MAPS-TODO)

| # | Ruling |
|---|---|
| 2a | Camp sectors named by holder; no left/right words; placement follows the Greek-side axis (Ajax E/Rhoiteion, Achilles W/Sigeion); Hainsworth dissent in the note |
| 2b | **No bard** on the dancing floor (18.603–6); vulgate as printed, tumblers lead; vineyard Linos-boy (569–72) unaffected (supersedes D11) |
| 2c | City at war: **Edwards** — one besieged city, siege ring split L/R of the walls; Taplin's two-armies in the caption |
| 2d | Callicolone = **Kara Tepe**, tier traditional (supersedes D15's tier) |
| 2e-i | chryse tradition string corrected (Strabo 13.1.63) |
| 2e-ii | Gates: Dörpfeld letters only on the sheet (supersedes D9) |
| 2e-iii | thymbra → Pleiades 550929 |
| 2e-iv | Camp zone: Sigeum ridge only; Beşika to the note (supersedes D4) |
| 2f | Shield register: **metallics, refined** — Metallmalerei, burnished flat fields on dark ground; NO chrome gradients, NO jewel-tone bands ("not gaudy or tacky. I want this to look GOOD and refined") |
| D6 | Kesik note wording updated — see item 0 above |
| Scope | **"This is a HOMER reader, not an archeology site."** Literary purpose gates everything; archaeology is a source of accuracy, never the subject. Plate B, Blegen, Jablonka all closed under this rule |

Still deferred (do not rule, do not draw): **dardania**.

## 3. Register discipline (unchanged, absolute)

Geographic plates carry only what survey/archaeology supports; schematic
plates carry the poem's logic, labelled as such; the two never mix. Anchors
never enter the gazetteer as coords. Tiers do the honesty work — notes never
re-apologise. Dates BC/AD. Never a fabricated coordinate. Known coordinate
traps: Vici.org's "Scaean Gate" point (CITADEL §4.5) and the UNESCO
nomination form's location field (~8 km off; CITADEL §6 item 8) — harvest
neither.

## 4. Gates (what "done" means)

- **LOOK gate**: anything whose output is an image is rendered and LOOKED AT
  by its maker — both themes, 3.5×+ crops for linework — before reporting
  done. The render harness recipe is in TROY-MAPS-HANDOFF-2 §2 (esbuild
  bundle + headless chrome screenshot); rebuild it in-repo if wanted.
- **Cross-family review both ways**: Claude lanes reviewed by Sol (code) or
  Grok (content); Codex lanes get a Sonnet competence pass + design-fidelity
  check before commit.
- Tests: `npx vitest run` in `shared/` and `app/`; `npm run build` in `app/`
  (expect ~4705 pages); preflight 0 errors. After ANY pipeline re-emit:
  apparatus re-merge both works + 48/48 scenes check, or run `build:public`.
- `nvm use 22` before any npm/vitest/astro command. `astro dev` binds 4322
  here (siblings hold 4321) — read the port from the log.
- Every sourced claim carries its citation in the DATA, not just prose.
  `sources` on every plate and layer.

## 5. Where everything is

| Thing | Path |
|---|---|
| Work queue | `docs/TROY-MAPS-TODO.md` (next-work-session list + rulings) |
| Plate A spec | `docs/research/RESEARCH-CITADEL.md` (DESIGN SPEC + VERDICT + §1–2) |
| Dörpfeld Tafeln 1–8 | `research-cache/dorpfeld-1902-tafel-{1..8}.jpg` (PD, _w4000) |
| Anchor evidence | `docs/research/RESEARCH-POEM-TOPOGRAPHY.md` (38 places, camp block, C-crux states) |
| Basemap parameters | `docs/research/RESEARCH-BASEMAP-DATA.md` |
| Shore/bay/barrier facts | `docs/research/RESEARCH-PALEOGEOGRAPHY.md` (10 Kayan sources, all verified) |
| Identifications/tiers | `docs/research/RESEARCH-TROAD-TOPOGRAPHY.md` + `TROAD-SOURCES.md` |
| Shield brief | `docs/research/RESEARCH-SHIELD.md` (scene inventory, materials, ruled register) |
| Cartographic craft + PD art | `docs/TROAD-CARTOGRAPHY.md` |
| Extraction notes (all sources) | `research-cache/*-notes.md` (gitignored, local only) |
| Defect ledger for the existing sheets | `TROY-MAPS-HANDOFF-2.md` §3 (historical but the measurements stand) |

The plain and Troad sheets are good and stay: they need the contour re-cut and
label work, not rebuilding (HANDOFF-2 §7). PR #16 stays draft.
