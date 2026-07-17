// Pure data helpers for the four Landmark-style maps (/maps/ — Ships/Catalogue
// explorer, Troad, Wanderings, Greece), drawn from apparatus/places.json and
// apparatus/catalogue.json. Homer-only; no plato-reader counterpart (Plato's
// corpus has no geographic apparatus) — same posture as shared/lib/genealogy.ts.
// Pure transforms only: no DOM, no Leaflet. The Leaflet-facing Svelte
// components (app/src/components/maps/*) call these and are exercised by the
// Playwright pass instead of vitest, per the project's UI-vs-logic test split.

export type Certainty = 'certain' | 'traditional' | 'speculative' | 'mythical';

export interface Mention {
  work: string;
  book: number;
  lines: [number, number];
}

export interface Place {
  id: string;
  name: string;
  greek: string;
  certainty: Certainty;
  tradition?: string;
  pleiades?: string;
  coords?: [number, number]; // [lat, lon]
  maps: string[];
  mentions: Mention[];
  note?: string;
}

// Minimal shape of an apparatus/characters.json entry, as needed to display a
// catalogue leader's name/Greek beside the contingent panel.
export interface CharacterRef {
  id: string;
  name: string;
  greek?: string;
}

export interface Contingent {
  id: string;
  name: string;
  lines: [number, number];
  leaders: string[];
  ships: number | null;
  places: string[]; // place ids, in catalogue-text order
  note?: string;
}

// ── Map membership ──────────────────────────────────────────────────────────

// Every place tagged for a given map (places.json's `maps` array), in the
// file's own order (catalogue order for "ships", otherwise source order).
export function placesForMap(places: Place[], tag: string): Place[] {
  return places.filter((p) => p.maps.includes(tag));
}

// Split a map's places into pinnable (has coords) and "not locatable" (listed,
// never force-pinned — CLAUDE.md apparatus honesty). Order preserved in both.
export function splitByCoords(places: Place[]): { located: Place[]; unlocated: Place[] } {
  const located: Place[] = [];
  const unlocated: Place[] = [];
  for (const p of places) (p.coords ? located : unlocated).push(p);
  return { located, unlocated };
}

// ── Catalogue sort toggles ──────────────────────────────────────────────────

export type CatalogueSort = 'catalogue' | 'ships-desc' | 'alpha';

// Sort a contingent list per the panel's sort toggle. 'catalogue' is Homer's
// own itinerary (the array's given order — the default) and returns a COPY,
// not the same array, so callers can freely mutate/reorder without touching
// the source. 'ships-desc' pushes null-ship entries (the Trojan tab, which
// Homer gives no ship count) to the end, stable otherwise. 'alpha' sorts by
// display name, locale-aware.
export function sortContingents(list: Contingent[], mode: CatalogueSort): Contingent[] {
  const copy = [...list];
  if (mode === 'catalogue') return copy;
  if (mode === 'ships-desc') {
    return copy.sort((a, b) => {
      if (a.ships == null && b.ships == null) return 0;
      if (a.ships == null) return 1;
      if (b.ships == null) return -1;
      return b.ships - a.ships;
    });
  }
  return copy.sort((a, b) => a.name.localeCompare(b.name));
}

// ── Ship-count circle scaling ───────────────────────────────────────────────

// Leaflet circleMarker radius (px) for a contingent's ship count, scaled so
// CIRCLE AREA is proportional to ship count: area = pi*r^2, and r here is
// maxRadius * sqrt(ships/maxShips), so r^2 / maxRadius^2 = ships/maxShips —
// area scales linearly with ships, not radius. `minRadius` is a visibility
// floor for tiny contingents (e.g. the 3-ship Symaeans) so they never vanish
// to a sub-pixel dot; it does NOT distort the area ratio between any two
// contingents both above the floor.
export function shipCircleRadius(
  ships: number,
  maxShips: number,
  maxRadius = 26,
  minRadius = 4,
): number {
  if (maxShips <= 0 || ships <= 0) return minRadius;
  const r = maxRadius * Math.sqrt(ships / maxShips);
  return Math.max(minRadius, r);
}

// ── Contingent → place / reader resolution ──────────────────────────────────

// The contingent's principal region for its map pin/circle: the first place
// in its (catalogue-text-ordered) `places` list that actually has coords.
// Never invents a position — returns null if none of the contingent's places
// are locatable (e.g. a contingent whose one named place has no fixed site).
export function principalPlace(
  contingent: Contingent,
  placesById: Map<string, Place>,
): Place | null {
  for (const id of contingent.places) {
    const p = placesById.get(id);
    if (p?.coords) return p;
  }
  return null;
}

export function placesById(places: Place[]): Map<string, Place> {
  return new Map(places.map((p) => [p.id, p]));
}

// Title-case an id ("ajax-oileus" -> "Ajax Oileus") for a leader with no
// characters.json entry of its own — most of the ~90 named Catalogue leaders
// are minor figures characters.json doesn't carry (only 16 of 73 leader
// refs resolve there); this is a plain, non-inventive display fallback, the
// same posture as shared/lib/genealogy.ts's `humanize` for an external
// parent id. Never a substitute for real biographical data.
export function humanizeId(id: string): string {
  return id.split('-').map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w)).join(' ');
}

// A Catalogue leader's display name: the real name/Greek from
// apparatus/characters.json when the leader has an entry there, else the
// humanized id (see humanizeId) with no Greek. Never invents a name.
export function leaderDisplayName(
  id: string,
  charactersById: Map<string, CharacterRef>,
): { name: string; greek?: string; known: boolean } {
  const c = charactersById.get(id);
  return c ? { name: c.name, greek: c.greek, known: true } : { name: humanizeId(id), known: false };
}

// The reader deep-link `?loc=` VALUE for a contingent's line span — its
// catalogue entry's FIRST line, verse-line scheme (colon grammar: see
// shared/lib/citation.ts formatLocValue — "2:494", not the dot copy-citation
// form "2.494"). Callers compose the full href as
// `${base}${workPath(workId, book)}?loc=${contingentLocValue(book, contingent)}`.
export function contingentLocValue(book: number, contingent: Contingent): string {
  return `${book}:${contingent.lines[0]}`;
}

// ── Wanderings route (the Apologoi, Od. 9-12) ───────────────────────────────

// The place ids that make up Odysseus's OWN sea-voyage route, in narrative
// (= voyage-chronological, for this span) order — i.e. the classic Landmark
// "Wanderings of Odysseus" line: Ismarus through Thrinacia. Restricted to
// Odyssey books 9-12 (the Apologoi, Odysseus's first-person account, is the
// literary unit actually called "the Wanderings"); other wanderings-tagged
// places (Ithaca, Sparta, Menelaus's Egypt/Cyprus/Libya travels, Ogygia,
// Scheria, etc.) are real map pins but are not stations ON this route, so
// connecting them would misrepresent the voyage — apparatus honesty over
// completeness. One explicit, documented exclusion within the 9-12 span:
// Zacynthus (Od. 9.24) is named in Odysseus's description of Ithaca's
// neighboring islands, immediately before the voyage narrative begins at
// Ismarus (9.39) — it is not itself a waypoint.
const WANDERINGS_ROUTE_MIN_BOOK = 9;
const WANDERINGS_ROUTE_MAX_BOOK = 12;
const WANDERINGS_ROUTE_EXCLUDE = new Set<string>(['zacynthus']);

// Ordered, coord-bearing, non-mythical stations of Odysseus's sea voyage for
// the Wanderings map's dashed polyline. Skips no-coord stations (all of which
// happen to be the mythical-tier ones — the underworld, the Planctae — since
// Homer gives them no real-world geography) and any mythical-tier place even
// if it somehow carried coords, per "do not invent positions". Sorted by
// (book, line) ascending, which — restricted to this narrow 9-12 span — is
// exactly voyage order (the Apologoi narrate the voyage linearly).
export function wanderingsRoute(places: Place[]): Place[] {
  return placesForMap(places, 'wanderings')
    .filter((p) => p.coords)
    .filter((p) => p.certainty !== 'mythical')
    .filter((p) => {
      const m = p.mentions[0];
      return !!m && m.work === 'odyssey'
        && m.book >= WANDERINGS_ROUTE_MIN_BOOK && m.book <= WANDERINGS_ROUTE_MAX_BOOK;
    })
    .filter((p) => !WANDERINGS_ROUTE_EXCLUDE.has(p.id))
    .sort((a, b) => {
      const ma = a.mentions[0];
      const mb = b.mentions[0];
      return ma.book !== mb.book ? ma.book - mb.book : ma.lines[0] - mb.lines[0];
    });
}
