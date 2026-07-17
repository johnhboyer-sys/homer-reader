# Design decisions — The Homer Reader

## John's verdict on the four v1 directions (2026-07-17)

- **Winner (John, confirmed): Chart-Room as the BASE — layout, restraint
  ("nicely restrained and stylish"), hairline discipline, small-cap labels,
  margin apparatus — recolored with the AEGEAN PALETTE** (marble ground,
  wine-dark indigo night mode, metallic bronze; terracotta reserved for the
  draft badge) and Aegean's type roles. Book header = Chart-Room's compact
  double-hairline cartouche (Aegean's full-screen banner rejected as too big;
  its argument + where/who/when content kept). Scholar's Bench rejected
  ("too Loeb skeuomorphism" — no spine creases, no book-modeling). On-Ramp
  rejected as too simple.
- **Hard requirement: actual parallel columns**, Greek | English, and **line
  numbers applied to the English side as well** (English gutter carries the
  Greek line-range ticks at the 5-line alignment cadence).
- **Book plate: compact.** The v1 Aegean full-banner plate takes too much
  screen. Keep the content John likes — argument line + where/who/when strip
  (scene description) — in a compact band.
- Aegean type roles adopted: Big Caslon display / Palatino Greek /
  Iowan Old Style English / Optima UI.
- **Lookup UX — DECIDED (John, 2026-07-17, on the v2 page):**
  **docked lexicon sidebar on desktop; anchored popup on mobile.** The
  definition shows a short gloss with an **EXPAND** control that opens the
  full entry in place (no navigation). **Nothing opens a new tab except the
  Logeion external link.** Tabs: LSJ · Cunliffe · Logeion ↗.

## Palette — LOCKED (John, 2026-07-17): WINE-DARK

From the four-palette explorer: **Wine-dark** (οἴνοπα garnet lead accent,
cool grey-biased bone grounds, deep indigo-black night; slate-blue draft
badge — NOT terracotta, NOT bronze/brown). Values per the explorer's
contrast-verified table (light: ground #E7E7E9, panel #DBD8DC, ink #241827,
ink-soft #5B4C58, rule-strong #5C2A40, accent #6E1F3A, accent-bright
#8C3A57, draft #375065; dark: #181120/#211828/#EDE6E8/#B7A9B4/#C77E97/
#D98BA3/#E8A6BA/#8FB0C9). "We might revisit particular shades" — shade
tweaks welcome later; the system is locked. Supersedes the bronze/marble
Aegean values in global.css (which themselves remain recorded for revert).

## Homepage hero animation spec (John's steers, 2026-07-17)

- Ambient background animation: subtle, SEAMLESS loops only (no visible
  resets); transform/opacity only; loops ≥20s (twinkle ≥6s); fully static
  under prefers-reduced-motion.
- Per-epic backgrounds sharing one vocabulary of glowing points, split by
  the diagonal horizon-seam (warrant: Il. 8.553–565, watchfires likened to
  stars): ILIAD = warm ember watchfires, low, clustered, irregular slow
  flicker; ODYSSEY = cool silver stars, high, sparse, slow twinkle;
  moonlight glint on the sea side only.
- Slight theme response: light = DUSK (hero lifted toward violet-slate,
  rose cast at the seam, 3–5 faint stars, fires kindling); dark = DEEP
  NIGHT (full treatment). Both must read as siblings; AA on hero text in
  both.

## Homepage (John, 2026-07-17: "looks great")

Homepage v1 mock APPROVED (with header-margin fix): monumental asymmetric
ΙΛΙΑΣ/ΟΔΥΣΣΕΙΑ hero on fixed wine-dark ground (both themes), contour band
promoted to diagonal horizon-seam signature, real line-1 epigraphs, three
Start Here doors on the homepage, factual apparatus band, no catalog
cards, no "Landmark" wording. Implementation target: app/src/pages/
index.astro + Landing.astro, pending the palette decision (mock is
token-driven — palette swap re-skins it).

## Phase 3 implications

- Token system starts from Aegean's custom-property palette (marble ground,
  wine-dark indigo dark mode, metallic bronze, terracotta reserved for the
  draft badge).
- Margin apparatus follows the Landmark block anatomy (ref · place small caps ·
  summary; day markers) per docs' landmark-conventions note — but never at the
  cost of parallel-column width (Chart-Room's column-starving risk rejected
  implicitly by the parallel-columns requirement).
- Reading Mode remains a separate posture; its design revisits On-Ramp ideas
  only insofar as they serve the single-column reading view.
