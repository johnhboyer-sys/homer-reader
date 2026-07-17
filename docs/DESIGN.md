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
- **Open question (v2 explores it)**: lookup UX — anchored popup at the
  clicked word vs a docked lexicon sidebar. v2 page demos both; John picks.

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
