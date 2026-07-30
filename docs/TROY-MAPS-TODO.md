# Troy maps — TODO (2026-07-29, post-research session)

All six dossiers are written, Grok-verified, and committed. PR #16 is shrunk
to plain + Troad. Gazetteer defects fixed. What remains:

## John (whenever you have a minute, in priority order)

1. **JSTOR/uni login in Chrome**, then tell the session — I pull
   `docs/research/PAYWALLED-ACCESS-QUEUE.md` top-down (25 items; the top 7
   each settle a load-bearing claim).
2. **Contested identifications** (can wait until Cook 1973 is pulled):
   chryse (our tradition string reverses Strabo 13.1.63), dardania,
   callicolone, the Scaean/Dardanian gate pairing, thymbra re-anchor.
3. **Shield visual register**: literal metallics (gold/silver on dark inlay,
   the Mycenaean dagger precedent) vs the site's terracotta family.
   RESEARCH-SHIELD.md has the evidence for both.
4. **PR #16** — still draft, review whenever.

## Next work session (no input from John needed)

1. **Contour re-cut** per RESEARCH-BASEMAP-DATA.md spec: relief `tol_deg`
   → 0.00100 (Troad) / 0.00012 (plain), plain `decimate` → 1, no smoothing,
   cull degenerate rings. Re-render and LOOK at 3.5×+ crops.
2. **Anchor the 38 places on the schematic sheet** from
   RESEARCH-POEM-TOPOGRAPHY.md (31 have anchoring passages; scamandrian-plain
   resolves to the unzoomed sheet; 3 want coords not anchors; 4 want nothing).
   Route the Chart Room to the schematic when a scene's places are
   schematic-only → ~280 scenes gain a real frame.
3. **Label work**: collision avoidance pass + text-on-path direction fix.
4. **Plate UX**: in-panel pan/zoom, scale bar tracks zoom, labels don't
   magnify, certainty filter replaces the 28 debug checkboxes.
5. **Attribution page**: Copernicus 6(b) modified-data wording + 6(c)
   liability sentence + SRTM/USGS credit (RESEARCH-BASEMAP-DATA.md §5).
6. **Hardening**: `sources` mandatory on plates in `validate_plate`;
   fix the `shore-bronze` Rhoiteion terminus (−0.4 m vertex);
   add ἴστωρ to the lexicon slices (reader-facing gap at 18.501).
7. **Citadel rebuild** from Dörpfeld Tafel V (georectify on features, grid as
   scale check) — after Messmer Abb. 2 is pulled (Jablonka email shelved for now, 2026-07-29).
8. **Shield figuration design** — after John's register call (his #3).
