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
- **D6 — DECIDED (09:28): draw the Kesik cut; the note LEADS with "the
  Achaean wall and ditch itself" (Kraft, Rapp, Kayan & Luce 2003, citing
  Luce 1998), then the other readings as the hedge** (harbour candidate,
  2003a; undecided/unfinished canal, Kayan's own 2003 chapter; late-Roman
  drainage never completed, Cook 1973, 166-67). Feature certain,
  identification speculative, every reading attributed.
- **D9 — DECIDED (09:29): Option A.** Gate names follow Dörpfeld: VI T =
  the Dardanian Gate (his confident identification, 2:630); the Scaean
  marked conjectural at the lost NW corner with his own vermutungsweise
  hedge quoted, stated as reversible. The unsourced guidebook
  "South Gate = Scaean" never appears.
- **D11 — DECIDED (09:34): side with Taplin — the dance scene includes
  the bard**, with a note carrying the disagreement: our printed text
  (vulgate/Aristarchus) lacks him; Edwards calls the line a supplement,
  Revermann rejects it too; Taplin — with Schadewaldt, Reinhardt and Marg
  (who take the singer for Homer himself) — would have him. The caption
  must state that the drawing follows Taplin's reading so plate and
  printed text never look accidentally inconsistent.
- **D14 — DECIDED (09:34): Option A — literal metallics.** Gold, silver,
  bronze, tin figures on dark kyanos-inlay ground, per Il. 18.474-75 +
  the Mycenaean inlay precedent.
- **D15 — DECIDED (09:34): Callicolone moves to Kara Tepe** (the
  Spratt/Forchhammer identification, defended by Cook, adopted by Luce),
  pinned at the surveyed OSM peak 39.95653/26.33947 (ele 207 m = Cook's
  680 ft), tier stays speculative, tradition names the chain and Leaf's
  Ophrynion alternative. Applied to places.json same day.
- **D12 — DECIDED (09:36): Edwards's reading for the city at war** — one
  besieged city with forces on either side (the drawable reading; Taplin's
  two-armies would leave the second army's position speculative), with a
  note carrying the disagreement (Taplin: "two besieging armies, their
  relation obscure").
- **D16 — DEFERRED** until John can sit with the dossiers (chryse,
  dardania, thymbra).
- **D2, D3, D7, D8, D13 — ALL settled-by-evidence items CONFIRMED**
  (John, 09:26): wagon gate captioned without a side-word; no schematic
  scale bar (pyre keeps its cited 100-ft label); shore-bronze note
  re-attributed (Strabo-endorsed, not measured); rivers/ford never lean on
  the 2003 reconstruction figures and no coordinate is ever lifted from
  them; the Shield figuration brief inherits scenes-not-ring-count.

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
