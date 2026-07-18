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
  wanderingsStory,
  splitStoryByCoords,
  captionSummary,
  humanizeId,
  leaderDisplayName,
  resolveLegs,
  resolveJourneyLegs,
  journeysPlaceSplit,
  wanderingsReturnTail,
  arcPoints,
  curvedRoute,
  fadeStub,
  primaryDuration,
  allDurations,
  durationLine,
  chipLabel,
  durationExtras,
  voyageDurationByPlaceId,
  journeyLegNote,
  JOURNEY_LEG_NOTES,
  wanderingsPlaybackLegs,
  type Place,
  type Contingent,
  type CharacterRef,
  type Journey,
  type JourneyLeg,
  type VoyageStation,
  type StationDuration,
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

describe('wanderingsStory (real apparatus/places.json)', () => {
  const raw = JSON.parse(readFileSync('../apparatus/places.json', 'utf-8'));
  const story = wanderingsStory(raw.places);

  it('produces the 17-station Troy-to-Ithaca telling order, numbered from 1', () => {
    expect(story.map((s) => s.place.id)).toEqual([
      'troy', 'ismarus', 'cape-malea', 'cythera', 'lotus-eaters-land',
      'cyclopes-land', 'aeolia', 'laestrygonia', 'aeaea',
      'cimmerians-underworld', 'sirens-island', 'scylla', 'charybdis',
      'thrinacia', 'ogygia', 'scheria', 'ithaca',
    ]);
    expect(story.map((s) => s.number)).toEqual(
      Array.from({ length: 17 }, (_, i) => i + 1),
    );
  });

  it('numbers Ismarus 2nd and Ogygia 15th (Troy opens the voyage, Ogygia sits after the Thrinacia wreck)', () => {
    expect(story.find((s) => s.place.id === 'ismarus')?.number).toBe(2);
    expect(story.find((s) => s.place.id === 'ogygia')?.number).toBe(15);
  });

  it('splits into 15 located (map-badge) and 2 unlocated ("beyond the map\'s edge") stations', () => {
    const { located, unlocated } = splitStoryByCoords(story);
    expect(located).toHaveLength(15);
    expect(unlocated.map((s) => s.place.id)).toEqual(['cimmerians-underworld', 'ogygia']);
    expect(unlocated.map((s) => s.number)).toEqual([10, 15]);
  });

  it('skips an id absent from the places array rather than inventing a placeholder', () => {
    const trimmed = raw.places.filter((p: Place) => p.id !== 'ithaca');
    const trimmedStory = wanderingsStory(trimmed);
    expect(trimmedStory.map((s) => s.place.id)).not.toContain('ithaca');
    expect(trimmedStory).toHaveLength(16);
  });
});

describe('captionSummary', () => {
  it('returns short notes unchanged', () => {
    expect(captionSummary('A short note.')).toBe('A short note.');
  });

  it('returns an empty string for an undefined note (never invents text)', () => {
    expect(captionSummary(undefined)).toBe('');
  });

  it('truncates at a word boundary near maxLen with a trailing ellipsis, never mid-word', () => {
    const note = 'City of the Cicones sacked by Odysseus\'s men on leaving Troy.';
    const summary = captionSummary(note, 40);
    expect(summary.length).toBeLessThanOrEqual(41); // 40 + ellipsis char
    expect(summary.endsWith('…')).toBe(true);
    expect(note.startsWith(summary.slice(0, -1))).toBe(true);
    // No trailing partial word before the ellipsis.
    expect(summary.slice(0, -1).endsWith(' ')).toBe(false);
  });

  it('falls back to a hard cut only when there is no space to break on', () => {
    const noSpaces = 'x'.repeat(100);
    const summary = captionSummary(noSpaces, 60);
    expect(summary).toBe(`${'x'.repeat(60)}…`);
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

describe('arcPoints', () => {
  it('starts and ends exactly at the given endpoints, for any bow', () => {
    const pts = arcPoints([10, 20], [12, 24], 0.15, 8);
    expect(pts[0]).toEqual([10, 20]);
    expect(pts[pts.length - 1]).toEqual([12, 24]);
    expect(pts).toHaveLength(9); // steps + 1
  });

  it('bow=0 degenerates to the straight segment (midpoint = linear midpoint)', () => {
    const pts = arcPoints([0, 0], [0, 2], 0, 2);
    expect(pts[1]).toEqual([0, 1]);
  });

  it('a positive bow displaces the midpoint perpendicular to the segment, by the expected sign and magnitude', () => {
    // From (0,0) to (0,2): due "east" in lon, lat constant. The perpendicular
    // unit vector (see arcPoints doc) is (-1, 0) for this segment, so a
    // positive bow should DECREASE the interior midpoint's lat.
    const pts = arcPoints([0, 0], [0, 2], 0.1, 2);
    const mid = pts[1];
    expect(mid[1]).toBeCloseTo(1, 10); // lon unaffected at the arc's own midpoint
    expect(mid[0]).toBeCloseTo(-0.1, 10); // lat pulled by bow(0.1) * length(2) * perpLat(-1) / 2... see below
  });

  it('flips sides for a negative bow of the same magnitude', () => {
    const pos = arcPoints([0, 0], [0, 2], 0.12, 2)[1];
    const neg = arcPoints([0, 0], [0, 2], -0.12, 2)[1];
    expect(pos[0]).toBeCloseTo(-neg[0], 10);
    expect(neg[0]).toBeGreaterThan(0);
  });

  it('treats an identical from/to as a degenerate two-point line (no NaN)', () => {
    const pts = arcPoints([5, 5], [5, 5], 0.2, 4);
    expect(pts).toEqual([[5, 5], [5, 5]]);
  });
});

describe('curvedRoute', () => {
  it('strings consecutive arcs into one continuous point list with no duplicate join points', () => {
    const points: [number, number][] = [[0, 0], [0, 2], [0, 4]];
    const steps = 4;
    const out = curvedRoute(points, () => 0.1, steps);
    expect(out).toHaveLength(2 * steps + 1); // two legs, steps+1 points each, joins de-duplicated
    expect(out[0]).toEqual([0, 0]);
    expect(out[out.length - 1]).toEqual([0, 4]);
  });

  it('passes each leg its own index to bowFor', () => {
    const points: [number, number][] = [[0, 0], [0, 2], [0, 4], [0, 6]];
    const seen: number[] = [];
    curvedRoute(points, (i) => { seen.push(i); return 0.05; }, 2);
    expect(seen).toEqual([0, 1, 2]);
  });

  it('returns the input unchanged for fewer than 2 points', () => {
    expect(curvedRoute([[1, 1]], () => 0.1)).toEqual([[1, 1]]);
    expect(curvedRoute([], () => 0.1)).toEqual([]);
  });
});

describe('fadeStub', () => {
  it('starts exactly at the given point', () => {
    const pts = fadeStub([10, 20], 90, 2, 4);
    expect(pts[0]).toEqual([10, 20]);
    expect(pts).toHaveLength(5); // steps + 1
  });

  it('bearing 0 (north) moves lat up, lon unchanged', () => {
    const pts = fadeStub([10, 20], 0, 2, 1);
    expect(pts[1][0]).toBeCloseTo(12, 10);
    expect(pts[1][1]).toBeCloseTo(20, 10);
  });

  it('bearing 90 (east) moves lon up, lat unchanged', () => {
    const pts = fadeStub([10, 20], 90, 2, 1);
    expect(pts[1][0]).toBeCloseTo(10, 10);
    expect(pts[1][1]).toBeCloseTo(22, 10);
  });

  it('the last point is exactly lengthDeg from the start, along bearingDeg', () => {
    const pts = fadeStub([0, 0], 45, 3, 6);
    const last = pts[pts.length - 1];
    const dist = Math.sqrt(last[0] * last[0] + last[1] * last[1]);
    expect(dist).toBeCloseTo(3, 10);
  });
});

describe('resolveLegs / resolveJourneyLegs', () => {
  const fixturePlaces: Place[] = [
    { id: 'a', name: 'Alpha', greek: 'Α', certainty: 'certain', coords: [1, 1], maps: [], mentions: [] },
    { id: 'b', name: 'Beta', greek: 'Β', certainty: 'traditional', maps: [], mentions: [] }, // no coords
  ];
  const byId = placesById(fixturePlaces);
  const legs: JourneyLeg[] = [
    { from: 'a', to: 'b', refs: [], certainty: 'certain', note: 'a to b', unlocatable: false },
    { from: 'b', to: 'ghost', refs: [], certainty: 'speculative', note: 'b to nowhere', unlocatable: true },
  ];

  it('resolves known ids to their Place, null for coordless-but-known and for unknown ids', () => {
    const resolved = resolveLegs(legs, byId);
    expect(resolved[0].fromPlace?.id).toBe('a');
    expect(resolved[0].toPlace?.id).toBe('b'); // known place, even though it has no coords
    expect(resolved[1].fromPlace?.id).toBe('b');
    expect(resolved[1].toPlace).toBeNull(); // unknown id -- never invents a place
    expect(resolved[1].unlocatable).toBe(true);
  });

  it('resolveJourneyLegs resolves a whole Journey\'s legs the same way', () => {
    const journey: Journey = { id: 'j', name: 'J', traveler: 'x', color_role: 'secondary', legs };
    expect(resolveJourneyLegs(journey, byId).map((l) => l.from)).toEqual(['a', 'b']);
  });
});

describe('journeysPlaceSplit', () => {
  const fixturePlaces: Place[] = [
    { id: 'a', name: 'Alpha', greek: '', certainty: 'certain', coords: [1, 1], maps: [], mentions: [] },
    { id: 'b', name: 'Beta', greek: '', certainty: 'certain', coords: [2, 2], maps: [], mentions: [] },
    { id: 'c', name: 'Gamma', greek: '', certainty: 'mythical', maps: [], mentions: [] }, // no coords
  ];
  const byId = placesById(fixturePlaces);
  const journeys: Journey[] = [
    { id: 'j1', name: 'J1', traveler: 'x', color_role: 'secondary', legs: [
      { from: 'a', to: 'b', refs: [], certainty: 'certain', note: '', unlocatable: false },
      { from: 'b', to: 'c', refs: [], certainty: 'mythical', note: '', unlocatable: true },
    ] },
    { id: 'j2', name: 'J2', traveler: 'y', color_role: 'secondary', legs: [
      { from: 'a', to: 'unknown-id', refs: [], certainty: 'speculative', note: '', unlocatable: true },
    ] },
  ];

  it('dedupes places touched by multiple legs/journeys, in first-appearance order', () => {
    const { located } = journeysPlaceSplit(journeys, byId);
    expect(located.map((p) => p.id)).toEqual(['a', 'b']);
  });

  it('splits coordless-but-known places into unlocated, and skips unknown ids entirely', () => {
    const { unlocated } = journeysPlaceSplit(journeys, byId);
    expect(unlocated.map((p) => p.id)).toEqual(['c']);
  });
});

describe('wanderingsReturnTail (real apparatus/journeys.json)', () => {
  const raw = JSON.parse(readFileSync('../apparatus/journeys.json', 'utf-8'));
  const journeys: Journey[] = raw.journeys;

  it('returns exactly the Thrinacia->Ogygia->Scheria->Ithaca tail, in order', () => {
    const tail = wanderingsReturnTail(journeys);
    expect(tail.map((l) => `${l.from}-${l.to}`)).toEqual([
      'thrinacia-ogygia',
      'ogygia-scheria',
      'scheria-ithaca',
    ]);
  });

  it('flags the Thrinacia->Ogygia leg unlocatable and ends solid at Ithaca', () => {
    const tail = wanderingsReturnTail(journeys);
    expect(tail[0].unlocatable).toBe(true);
    expect(tail[tail.length - 1].to).toBe('ithaca');
    expect(tail[tail.length - 1].unlocatable).toBe(false);
  });

  it('returns [] for a journeys list with no odysseus-return journey', () => {
    expect(wanderingsReturnTail([])).toEqual([]);
  });
});

describe('voyage durations (apparatus/voyage-chronology.json)', () => {
  const raw = JSON.parse(readFileSync('../apparatus/voyage-chronology.json', 'utf-8'));
  const stations: VoyageStation[] = raw.stations;
  const byPlaceId = voyageDurationByPlaceId(stations);

  it('primaryDuration prefers stayDuration over duration (Ogygia: seven years, not nine days)', () => {
    const ogygia = stations.find((s) => s.id === 'ogygia')!;
    const d = primaryDuration(ogygia);
    expect(d).toEqual({ value: 7, unit: 'years', greek: 'ἑπτάετες', cite: 'Od. 7.259', label: 'kept by Calypso' });
  });

  it('primaryDuration falls back to duration when there is no stayDuration (Lotus-eaters: nine days)', () => {
    const lotus = stations.find((s) => s.id === 'lotus-eaters-land')!;
    expect(primaryDuration(lotus)).toEqual({ value: 9, unit: 'days', greek: 'ἐννῆμαρ', cite: 'Od. 9.82' });
  });

  it('primaryDuration is null where the poem states nothing (never invented)', () => {
    const cyclopes = stations.find((s) => s.id === 'cyclopes-land')!;
    expect(primaryDuration(cyclopes)).toBeNull();
  });

  it('allDurations lists the stay figure before the arrival figure', () => {
    const ogygia = stations.find((s) => s.id === 'ogygia')!;
    const all = allDurations(ogygia);
    expect(all).toHaveLength(2);
    expect(all[0]!.label).toBe('kept by Calypso');
    expect(all[1]!.label).toBe('adrift, arriving');
  });

  it('allDurations is empty (never invented) for a station with no stated duration', () => {
    expect(allDurations(stations.find((s) => s.id === 'scylla')!)).toEqual([]);
  });

  it('durationLine composes value/unit/greek/cite', () => {
    const d: StationDuration = { value: 9, unit: 'days', greek: 'ἐννῆμαρ', cite: 'Od. 9.82' };
    expect(durationLine(d)).toBe('9 days — ἐννῆμαρ, Od. 9.82');
  });

  it('durationLine omits the Greek clause and marks approximate when greek is null (Ithaca)', () => {
    const ithaca = stations.find((s) => s.id === 'ithaca')!;
    const d = primaryDuration(ithaca)!;
    expect(d.greek).toBeNull();
    expect(d.approximate).toBe(true);
    expect(durationLine(d)).toBe('~1 night — Od. 13.78-95');
  });

  it('chipLabel has no citation, just the amount', () => {
    expect(chipLabel({ value: 1, unit: 'month', greek: 'μῆνα', cite: 'Od. 10.14' })).toBe('1 month');
    expect(chipLabel({ value: 1, unit: 'night', greek: null, cite: 'x', approximate: true })).toBe('~1 night');
  });

  it('durationExtras capitalizes the label and formats each row, stay first', () => {
    const ogygia = stations.find((s) => s.id === 'ogygia')!;
    const extras = durationExtras(ogygia);
    expect(extras).toEqual([
      { label: 'Kept by Calypso', value: '7 years — ἑπτάετες, Od. 7.259' },
      { label: 'Adrift, arriving', value: '9 days — ἐννῆμαρ, Od. 12.447' },
    ]);
  });

  it('durationExtras falls back to the generic "Duration" label when the JSON supplies none', () => {
    const aeolia1 = stations.find((s) => s.id === 'aeolia-1')!;
    expect(durationExtras(aeolia1)).toEqual([{ label: 'Duration', value: '1 month — μῆνα, Od. 10.14' }]);
  });

  it('voyageDurationByPlaceId keeps the FIRST landfall\'s duration for a place visited twice (Aeolia, Aeaea)', () => {
    expect(byPlaceId.get('aeolia')?.id).toBe('aeolia-1');
    expect(primaryDuration(byPlaceId.get('aeolia')!)).toEqual({ value: 1, unit: 'month', greek: 'μῆνα', cite: 'Od. 10.14' });
    expect(byPlaceId.get('aeaea')?.id).toBe('aeaea-1');
    expect(primaryDuration(byPlaceId.get('aeaea')!)).toEqual({ value: 1, unit: 'year', greek: 'ἐνιαυτός', cite: 'Od. 10.467-470' });
  });

  it('voyageDurationByPlaceId skips digression stations with no placeId (never a phantom map key)', () => {
    expect(byPlaceId.has('raft-building')).toBe(false); // id, not placeId -- confirms the lookup key space
    for (const s of stations) {
      if (s.placeId == null) expect([...byPlaceId.values()]).not.toContain(s);
    }
  });
});

describe('JOURNEY_LEG_NOTES / journeyLegNote', () => {
  it('Menelaus\'s eighth-year note is keyed to his arrival leg (egypt -> sparta) and cites Od. 4.82', () => {
    const note = journeyLegNote('egypt', 'sparta');
    expect(note?.travelerId).toBe('menelaus');
    expect(note?.cite).toBe('Od. 4.82');
    expect(note?.greek).toContain('ὀγδοάτῳ');
  });

  it('Nestor\'s note is keyed to his arrival leg (geraistos -> pylos), hedged, cites Od. 3.180/182-183', () => {
    const note = journeyLegNote('geraistos', 'pylos');
    expect(note?.travelerId).toBe('nestor');
    expect(note?.cite).toBe('Od. 3.180, 182–183');
  });

  it('Telemachus\'s note carries the narrative-calendar line, no Greek/citation invented', () => {
    const note = journeyLegNote('ithaca', 'pylos');
    expect(note?.travelerId).toBe('telemachus');
    expect(note?.greek).toBe('');
    expect(note?.gloss).toContain('Days 2–6');
  });

  it('returns undefined for a leg with no verified note (never invented)', () => {
    expect(journeyLegNote('troy', 'ismarus')).toBeUndefined();
  });

  it('every table entry resolves to a real leg in apparatus/journeys.json', () => {
    const raw = JSON.parse(readFileSync('../apparatus/journeys.json', 'utf-8'));
    const journeys: Journey[] = raw.journeys;
    const allLegPairs = new Set(journeys.flatMap((j) => j.legs.map((l) => `${l.from}-${l.to}`)));
    for (const key of Object.keys(JOURNEY_LEG_NOTES)) {
      expect(allLegPairs.has(key)).toBe(true);
    }
  });
});

describe('wanderingsPlaybackLegs (real apparatus/places.json)', () => {
  const raw = JSON.parse(readFileSync('../apparatus/places.json', 'utf-8'));
  const story = wanderingsStory(raw.places);

  it('produces 16 legs for the 17-station telling order, each carrying real Place records', () => {
    const legs = wanderingsPlaybackLegs(story);
    expect(legs).toHaveLength(16);
    expect(legs[0]).toEqual({ from: story[0]!.place, to: story[1]!.place, toNumber: 2 });
    expect(legs[legs.length - 1]!.to.id).toBe('ithaca');
    expect(legs[legs.length - 1]!.toNumber).toBe(17);
  });

  it('flags a leg as coordless whenever either endpoint has no coords (cimmerians-underworld, ogygia)', () => {
    const legs = wanderingsPlaybackLegs(story);
    const intoCimmerians = legs.find((l) => l.to.id === 'cimmerians-underworld')!;
    expect(intoCimmerians.to.coords).toBeUndefined();
    const outOfCimmerians = legs.find((l) => l.from.id === 'cimmerians-underworld')!;
    expect(outOfCimmerians.from.coords).toBeUndefined();
    const intoOgygia = legs.find((l) => l.to.id === 'ogygia')!;
    expect(intoOgygia.to.coords).toBeUndefined();
  });

  it('returns [] for fewer than 2 stations', () => {
    expect(wanderingsPlaybackLegs([])).toEqual([]);
    expect(wanderingsPlaybackLegs([story[0]!])).toEqual([]);
  });
});
