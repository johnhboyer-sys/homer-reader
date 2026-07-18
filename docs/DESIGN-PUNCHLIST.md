# Design punch list (Opus design-director critique, 2026-07-17)

Evidence screenshots: session scratchpad design-critique/shots/.
Waves tracked as tasks #17 (A) and #18 (B). Keepers are protected.

## Wave A — bugs + branding (task #17)

1. BUG: Reading Mode scene chips all render at one rect (x200,y406) —
   garbled overlap on load. Offset each to its scene's start line. M/high
2. BRANDING: og-default.png + og-support.png are un-forked PLATO cards
   (teal, "The Plato Reader"); og:url still example.invalid. Regenerate
   Wine-dark Homer cards. S/high
3. BUG: Genealogies SVG has 14 connectors, 0 text nodes — labels sit in
   a collapsed flat list; legend describes a tree that isn't drawn.
   Position labels at node coords. L/high
5. TOKEN: native radios/checkboxes browser-blue (accent-color: auto) —
   set accent-color: var(--accent) globally + style selects. S/high
9. Draft badge has two forms — maps' full-width empty bar reads as a
   blank input; unify to the compact badge. S/med
11. Search placeholders are philosophy vocab ("virtue, happiness",
    φρόνησις) — swap to Homeric (μῆνις, πολύτροπος). S/med

## Wave B — cohesion + system (task #18)

4. Three different headers/wordmarks across surfaces — unify; reader
   toolbar extends the shell. M/high
6. Maps: generic green/blue tiles clash + grey tile voids at default
   framing — duotone/mute treatment + bounds clamp. M-L/high
7. Ships map: Argolid marker clump illegible — cluster/spiderfy/jitter
   + opacity. M/med-high
8. No spacing scale — four side-panel widths (368/352/320/319);
   introduce --space-* tokens. M/med systemic
10. Three-doors cards differ homepage vs /start (fill + labels) — one
    component, one label set. S/med
12. Docked lexicon: gloss floats in a void; LSJ·Cunliffe·Logeion tabs
    not surfaced upfront. S-M/med
13. Start Here cards uneven heights, CTAs unaligned; page trails empty.
    S/med
14. Reader header 102px, ~9 controls + books strip; Support at equal
    weight with reading tools — group secondary into overflow, demote
    Support. M/med
15. Formulas/repetitions right-floated counts leave mid-row void — cap
    row width or move counts adjacent. S/low-med
16. ⌘K hint shows on coarse pointers — hide. S/low
17. "All works" on a two-poem site — rename ("The Poems") or drop. S/low
18. Homepage "Three ways in" cards inert beside the hero — slight hover
    lift or small-cap accent header. S/low

## KEEPERS — do not fix into mediocrity

- The homepage hero (asymmetric split, atmospheres, epigraphs, seam).
- The reader core (cartouche, true parallel columns + dual line ticks,
  scene rail).
- The editorial type system on index/SEO/formula pages; Greek-token
  focus ring is correct.
