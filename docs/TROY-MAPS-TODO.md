# Troy maps — TODO (updated 2026-07-30, post-acquisition morning)

All six dossiers written, source-verified, and now enriched with full texts:
Kraft 1980, Taplin, Hardie, Revermann, Luce 1984, CATENA + erratum read cover
to cover; Cook 1973 and Cambridge commentary vols III/V/VI read at the key
pages from live archive.org borrows (26 page images in
`research-cache/page-captures/`). PR #16 shrunk to plain + Troad. Two waves of
gazetteer corrections applied. Every extraction Grok-verified before commit.

## Rulings (John, 2026-07-30)

- **D1 — DECIDED: Option A.** Camp sectors are named by who holds them
  ("Ajax's end" / "the middle: Odysseus's ships, the assembly" /
  "Achilles' end"); the words "left" and "right" appear nowhere on the
  schematic sheet. Binds every anchor brief and caption.
- **D4 — DECIDED: Option A + recency tiebreak.** Geographic plates carry
  the camp as rival attributed zones (Kraft 1980 Beşika / Luce 1984 inner
  ridge / 2003 outer ridge), each speculative, under the certainty filter.
  Where the Chart Room (or any single-frame context) must pick ONE, **the
  most recently published scholarly placement wins the camera** — currently
  the 2003 Kraft/Rapp/Kayan/Luce outer-ridge camp — and the caption names
  whose placement is framed. Later scholarship supersedes automatically.
- **D2, D3 — CONFIRMED as settled**: the wagon gate is drawn and captioned
  without a side-word; no scale bar on the schematic, the pyre carries its
  cited 100-ft dimension label.

## John (in priority order)

1. **ILL requests — file these two and every drawn layer has its source
   spine** (full citations in `docs/research/PAYWALLED-ACCESS-QUEUE.md`):
   a. Kraft/Rapp/Kayan/Luce, *Geology* 31.2 (2003): 163–66 — THE FIGURES.
      Now the only possible source for the "bay head ~1.2 km" claim.
   b. Wagner/Pernicka/Uerpmann, eds., *Troia and the Troad* (Springer 2003)
      — one volume, three needed chapters (Kayan 379–401 above all; the
      barrier row is not drawing-ready until it is read).
   Lower priority: Kayan 2014 (Studia Troica Mon. 5, fig. 8); Janko vol. IV
   (two notes; not on archive.org; non-blocking).
2. **Decisions queued from the research** (each with its evidence table in
   the named dossier):
   a. Left/right labelling: the axis holds, the sense is undecidable
      (Hainsworth vs Clay) — recommended re-spec: name camp sectors by who
      holds them, no left/right on the sheet. RESEARCH-POEM-TOPOGRAPHY §3.1.
   b. The singer caption (18.603–6): three read authorities, no bard 2–1;
      recommended: draw as printed, caption the crux. RESEARCH-SHIELD §2.2.
   c. Taplin vs Edwards on the city at war: two armies vs one split siege
      ring — a figuration choice. RESEARCH-SHIELD §1.2.
   d. Callicolone pin: current coordinate matches no authority; Kara Tepe
      (Spratt/Forchhammer/Cook/Luce, ~8.5 km E, OSM peak candidate exists)
      vs Leaf's Ophrynion. RESEARCH-TROAD-TOPOGRAPHY §9.1.
   e. Chryse / dardania / zeleia-style contested IDs (chryse's tradition
      string reverses Strabo 13.1.63); Scaean/Dardanian pairing; thymbra
      re-anchor; Achaean-camp treatment on the GEOGRAPHIC plate (rival
      attributed zones: Beşika per Kraft 1980 vs Sigeum ridge per Luce 1984).
   f. Shield visual register: metallics vs terracotta. RESEARCH-SHIELD.
3. **PR #16** — still draft, review whenever.

## Next work session (no input from John needed)

1. **Contour re-cut** per RESEARCH-BASEMAP-DATA.md: relief `tol_deg` →
   0.00100 (Troad) / 0.00012 (plain), plain `decimate` → 1, no smoothing,
   cull degenerate rings. Re-render and LOOK at 3.5×+ crops.
2. **Anchor the 38 places on the schematic sheet** from
   RESEARCH-POEM-TOPOGRAPHY (31 anchorable; camp block first — best-sourced;
   sector labels by holder, never left/right; scamandrian-plain resolves to
   the unzoomed sheet). Route the Chart Room to the schematic when a scene's
   places are schematic-only → ~280 scenes gain a real frame.
3. **Label work**: collision avoidance + text-on-path direction fix.
4. **Plate UX**: in-panel pan/zoom, scale bar tracks zoom, labels don't
   magnify, certainty filter replaces the 28 debug checkboxes.
5. **Attribution page**: Copernicus 6(b) wording + 6(c) liability sentence +
   SRTM/USGS credit (RESEARCH-BASEMAP-DATA §5).
6. **Hardening**: `sources` mandatory on plates in `validate_plate`; fix the
   `shore-bronze` Rhoiteion terminus (−0.4 m vertex); add ἴστωρ to the
   lexicon slices (18.501); shore-bronze layer note re-attribution (the
   "1.2 km, Kraft" claim is dead until the Geology figures arrive).
7. **Cheap reading tasks against live borrows** (before they lapse): Cook
   p. 293 (Virchow doubts) and pp. 141–46, 159–65; Edwards printed p. 230 and
   the 18.481–82 lemma note and pp. 203–208; Hainsworth 11.5–7n. and the
   p. 243 continuation; page-FOOT re-captures (current captures crop the last
   ~6–8 lines of every page — the cheapest verification item in the file).
8. **Citadel rebuild** from Dörpfeld Tafel V (georectify on features; Tafel I
   found at leaf n268) — after Messmer Abb. 2. **Shield figuration design** —
   after John's register call.
