import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  placesForMap,
  splitByCoords,
  sortContingents,
  shipCircleRadius,
  principalPlace,
  placesById,
  contingentLocValue,
  wanderingsRoute,
  humanizeId,
  leaderDisplayName,
  type Place,
  type Contingent,
  type CharacterRef,
} from '../lib/maps';

// A small fixture mirroring the shapes actually found in apparatus/places.json
// / apparatus/catalogue.json, plus the real corpus files for the data-shape
// regression checks (route order, sort order) that only mean something
// against the actual apparatus.
const places: Place[] = [
  { id: 'a', name: 'Alpha', greek: 'Α', certainty: 'certain', coords: [1, 1], maps: ['greece'], mentions: [{ work: 'odyssey', book: 1, lines: [1, 1] }] },
  { id: 'b', name: 'Beta', greek: 'Β', certainty: 'traditional', maps: ['greece'], mentions: [{ work: 'odyssey', book: 1, lines: [2, 2] }] }, // no coords
  { id: 'c', name: 'Gamma', greek: 'Γ', certainty: 'mythical', maps: ['wanderings'], mentions: [{ work: 'odyssey', book: 11, lines: [3, 3] }] }, // no coords
];

describe('placesForMap / splitByCoords', () => {
  it('filters by map tag and splits located vs. unlocated', () => {
    const greece = placesForMap(places, 'greece');
    expect(greece.map((p) => p.id)).toEqual(['a', 'b']);
    const { located, unlocated } = splitByCoords(greece);
    expect(located.map((p) => p.id)).toEqual(['a']);
    expect(unlocated.map((p) => p.id)).toEqual(['b']);
  });

  it('never force-pins a coordless place (unlocated list, not dropped)', () => {
    const { unlocated } = splitByCoords(places);
    expect(unlocated.map((p) => p.id).sort()).toEqual(['b', 'c']);
  });
});

describe('sortContingents', () => {
  const list: Contingent[] = [
    { id: 'z', name: 'Zeta Force', lines: [1, 2], leaders: [], ships: 30, places: [] },
    { id: 'a', name: 'Alpha Force', lines: [3, 4], leaders: [], ships: 100, places: [] },
    { id: 'm', name: 'Mid Force', lines: [5, 6], leaders: [], ships: null, places: [] },
  ];

  it('catalogue order returns a copy in the given (Homer itinerary) order', () => {
    const out = sortContingents(list, 'catalogue');
    expect(out.map((c) => c.id)).toEqual(['z', 'a', 'm']);
    expect(out).not.toBe(list);
  });

  it('ships-desc sorts descending and pushes null-ship (Trojan) entries last', () => {
    const out = sortContingents(list, 'ships-desc');
    expect(out.map((c) => c.id)).toEqual(['a', 'z', 'm']);
  });

  it('alpha sorts by display name', () => {
    const out = sortContingents(list, 'alpha');
    expect(out.map((c) => c.id)).toEqual(['a', 'm', 'z']);
  });

  it('does not mutate the input array', () => {
    const before = list.map((c) => c.id);
    sortContingents(list, 'ships-desc');
    expect(list.map((c) => c.id)).toEqual(before);
  });
});

describe('shipCircleRadius', () => {
  it('scales AREA proportionally to ship count (radius ~ sqrt(ships))', () => {
    const rMax = shipCircleRadius(100, 100);
    const rHalfArea = shipCircleRadius(50, 100);
    // area(rMax) / area(rHalfArea) should be ~2 (100 ships / 50 ships)
    const ratio = (rMax * rMax) / (rHalfArea * rHalfArea);
    expect(ratio).toBeCloseTo(2, 5);
  });

  it('floors tiny contingents at minRadius without breaking monotonicity above the floor', () => {
    const r3 = shipCircleRadius(3, 100, 26, 4);
    const r7 = shipCircleRadius(7, 100, 26, 4);
    const r100 = shipCircleRadius(100, 100, 26, 4);
    expect(r3).toBeLessThan(r7);
    expect(r7).toBeLessThan(r100);
    expect(r100).toBe(26);
  });

  it('never returns 0 or negative for a 0/negative ship count', () => {
    expect(shipCircleRadius(0, 100)).toBeGreaterThan(0);
    expect(shipCircleRadius(-5, 100)).toBeGreaterThan(0);
  });
});

describe('principalPlace', () => {
  it('picks the first place in catalogue order that actually has coords', () => {
    const p1: Place = { id: 'p1', name: 'P1', greek: '', certainty: 'certain', maps: [], mentions: [] }; // no coords
    const p2: Place = { id: 'p2', name: 'P2', greek: '', certainty: 'certain', coords: [5, 5], maps: [], mentions: [] };
    const byId = placesById([p1, p2]);
    const c: Contingent = { id: 'x', name: 'X', lines: [1, 2], leaders: [], ships: 10, places: ['p1', 'p2'] };
    const result = principalPlace(c, byId);
    expect(result?.id).toBe('p2');
  });

  it('returns null (never invents a position) when no listed place is locatable', () => {
    const p1: Place = { id: 'p1', name: 'P1', greek: '', certainty: 'certain', maps: [], mentions: [] };
    const byId = placesById([p1]);
    const c: Contingent = { id: 'x', name: 'X', lines: [1, 2], leaders: [], ships: 10, places: ['p1'] };
    expect(principalPlace(c, byId)).toBeNull();
  });
});

describe('contingentLocValue', () => {
  it('composes the verse-line ?loc= colon grammar from the contingent\'s first line', () => {
    const c: Contingent = { id: 'boeotians', name: 'Boeotians', lines: [494, 510], leaders: [], ships: 50, places: [] };
    expect(contingentLocValue(2, c)).toBe('2:494');
  });
});

describe('wanderingsRoute (fixture)', () => {
  it('skips no-coord and mythical-tier places, keeps only Od. 9-12 stations, sorted by (book, line)', () => {
    const fixture: Place[] = [
      { id: 'route-2', name: 'R2', greek: '', certainty: 'traditional', coords: [2, 2], maps: ['wanderings'], mentions: [{ work: 'odyssey', book: 10, lines: [5, 5] }] },
      { id: 'route-1', name: 'R1', greek: '', certainty: 'certain', coords: [1, 1], maps: ['wanderings'], mentions: [{ work: 'odyssey', book: 9, lines: [50, 50] }] },
      { id: 'no-coords', name: 'NC', greek: '', certainty: 'mythical', maps: ['wanderings'], mentions: [{ work: 'odyssey', book: 11, lines: [14, 14] }] },
      { id: 'out-of-range', name: 'OOR', greek: '', certainty: 'certain', coords: [3, 3], maps: ['wanderings'], mentions: [{ work: 'odyssey', book: 4, lines: [83, 83] }] },
      { id: 'zacynthus', name: 'Zacynthus', greek: '', certainty: 'certain', coords: [4, 4], maps: ['wanderings'], mentions: [{ work: 'odyssey', book: 9, lines: [24, 24] }] },
    ];
    const route = wanderingsRoute(fixture);
    expect(route.map((p) => p.id)).toEqual(['route-1', 'route-2']);
  });
});

describe('wanderingsRoute (real apparatus/places.json)', () => {
  it('produces the classic Ismarus-through-Thrinacia voyage order', () => {
    const raw = JSON.parse(readFileSync('../apparatus/places.json', 'utf-8'));
    const route = wanderingsRoute(raw.places);
    expect(route.map((p: Place) => p.id)).toEqual([
      'ismarus', 'cape-malea', 'cythera', 'lotus-eaters-land', 'cyclopes-land',
      'aeolia', 'laestrygonia', 'aeaea', 'sirens-island', 'scylla', 'charybdis', 'thrinacia',
    ]);
  });
});

describe('humanizeId / leaderDisplayName', () => {
  it('title-cases a plain id', () => {
    expect(humanizeId('peneleos')).toBe('Peneleos');
  });

  it('title-cases each hyphen-joined word', () => {
    expect(humanizeId('ajax-oileus')).toBe('Ajax Oileus');
  });

  it('resolves a known character to its real name/greek', () => {
    const chars = new Map<string, CharacterRef>([['achilles', { id: 'achilles', name: 'Achilles', greek: 'Ἀχιλλεύς' }]]);
    expect(leaderDisplayName('achilles', chars)).toEqual({ name: 'Achilles', greek: 'Ἀχιλλεύς', known: true });
  });

  it('falls back to a humanized id (no invented data) for an unknown leader', () => {
    const chars = new Map<string, CharacterRef>();
    expect(leaderDisplayName('peneleos', chars)).toEqual({ name: 'Peneleos', known: false });
  });
});

describe('catalogue.json ship-order regression (real apparatus)', () => {
  it('matches the expected descending ship order used by QA (Mycenae 100 ... Symaeans 3)', () => {
    const raw = JSON.parse(readFileSync('../apparatus/catalogue.json', 'utf-8'));
    const sorted = sortContingents(raw.achaean, 'ships-desc');
    expect(sorted[0].id).toBe('mycenaeans');
    expect(sorted[0].ships).toBe(100);
    expect(sorted[1].id).toBe('pylians');
    expect(sorted[1].ships).toBe(90);
    expect(sorted[sorted.length - 1].id).toBe('symaeans');
    expect(sorted[sorted.length - 1].ships).toBe(3);
    // Monotonically non-increasing.
    for (let i = 1; i < sorted.length; i++) {
      expect((sorted[i].ships ?? 0)).toBeLessThanOrEqual(sorted[i - 1].ships ?? Infinity);
    }
  });
});
