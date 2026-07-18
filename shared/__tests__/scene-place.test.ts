import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  buildSceneTimeline,
  resolveScenePlaces,
  joinScenesToPlaces,
  type PlacesFile,
  type JourneysFile,
} from '../lib/scene-place';
import type { Scene } from '../lib/data';

const PLACES_PATH = '../apparatus/places.json';
const JOURNEYS_PATH = '../apparatus/journeys.json';
const SCENES_ODYSSEY_PATH = '../apparatus/scenes/odyssey.json';
const SCENES_ILIAD_PATH = '../apparatus/scenes/iliad.json';

const placesFile: PlacesFile = JSON.parse(readFileSync(PLACES_PATH, 'utf-8'));
const journeysFile: JourneysFile = JSON.parse(readFileSync(JOURNEYS_PATH, 'utf-8'));

interface RawSceneBook {
  book: number;
  scenes: { lines: [number, number]; summary: string; location?: string; dayNumber?: number | null }[];
}
interface RawScenesFile {
  books: RawSceneBook[];
}

function scenesForBook(raw: RawScenesFile, book: number): Scene[] {
  const b = raw.books.find((x) => x.book === book);
  if (!b) throw new Error(`no book ${book}`);
  return b.scenes.map((s) => ({
    summary: s.summary,
    startLine: s.lines[0],
    endLine: s.lines[1],
    place: s.location,
    day: s.dayNumber,
  }));
}

describe('buildSceneTimeline (real apparatus data)', () => {
  it('merges journey-leg refs and place mentions for Od. 9, sorted ascending by line', () => {
    const timeline = buildSceneTimeline('odyssey', 9, placesFile, journeysFile);
    const lines = timeline.map((e) => e.line);
    expect(lines).toEqual([...lines].sort((a, b) => a - b));
    expect(timeline.some((e) => e.place.id === 'cyclopes-land')).toBe(true);
  });

  it('a tie between a journey-leg ref and a place mention on the same line prefers the leg (carries a route)', () => {
    // Od. 9: the lotus-eaters-land -> cyclopes-land leg refs [105,106]; the
    // cyclopes-land place mention is [106,106] — both land on line 106.
    const timeline = buildSceneTimeline('odyssey', 9, placesFile, journeysFile);
    const at106 = timeline.filter((e) => e.line === 105 || e.line === 106);
    const cyclopsEntries = at106.filter((e) => e.place.id === 'cyclopes-land');
    expect(cyclopsEntries.length).toBeGreaterThan(0);
    expect(cyclopsEntries[0].route?.to.id).toBe('cyclopes-land');
    expect(cyclopsEntries[0].route?.from.id).toBe('lotus-eaters-land');
  });

  it('returns an empty timeline for a (work, book) with no mentions or refs at all', () => {
    const timeline = buildSceneTimeline('odyssey', 9, { places: [] }, { journeys: [] });
    expect(timeline).toEqual([]);
  });
});

describe('resolveScenePlaces / joinScenesToPlaces (real apparatus data)', () => {
  const odyssey: RawScenesFile = JSON.parse(readFileSync(SCENES_ODYSSEY_PATH, 'utf-8'));
  const iliad: RawScenesFile = JSON.parse(readFileSync(SCENES_ILIAD_PATH, 'utf-8'));

  it('Od. 9 scene 12 (lines 345-374, Polyphemus\'s cave) resolves to the Land of the Cyclopes with a route from the Lotus-eaters', () => {
    const scenes = scenesForBook(odyssey, 9);
    expect(scenes).toHaveLength(17);
    const scene12 = scenes[11]; // 0-based index 11 = "Scene 12 of 17"
    expect(scene12.startLine).toBe(345);
    const resolved = joinScenesToPlaces('odyssey', 9, scenes, placesFile, journeysFile);
    expect(resolved[11]).not.toBeNull();
    expect(resolved[11]!.place.id).toBe('cyclopes-land');
    expect(resolved[11]!.place.coords).toBeDefined();
    expect(resolved[11]!.route?.from.id).toBe('lotus-eaters-land');
    expect(resolved[11]!.route?.to.id).toBe('cyclopes-land');
  });

  it('every scene of Od. 9 from the Cyclopes-shore landing onward resolves to the same anchor (no premature place change)', () => {
    const scenes = scenesForBook(odyssey, 9);
    const resolved = joinScenesToPlaces('odyssey', 9, scenes, placesFile, journeysFile);
    // Scenes 5 (islet) through 15 (escape) all precede the NEXT journey leg
    // (cyclopes-land -> aeolia, book 10 line 1), so all resolve to cyclopes-land.
    for (let i = 4; i <= 14; i++) {
      expect(resolved[i]?.place.id).toBe('cyclopes-land');
    }
  });

  it('Il. 1 scene 1 (the proem, before any place is named) falls back to the book\'s earliest real mention', () => {
    const scenes = scenesForBook(iliad, 1);
    const scene1 = scenes[0];
    expect(scene1.startLine).toBe(1);
    const resolved = joinScenesToPlaces('iliad', 1, scenes, placesFile, journeysFile);
    expect(resolved[0]).not.toBeNull();
    // The earliest-line mention in Il. 1 is Chryse (line 37) — a real,
    // Troad-tagged place near Troy, not a fabricated identification.
    expect(resolved[0]!.place.id).toBe('chryse');
    expect(resolved[0]!.place.coords).toBeDefined();
  });

  it('a mythical-tier anchor with no coords (e.g. the Cimmerians\' land, Od. 11) is reported coordless, never fabricated', () => {
    const timeline = buildSceneTimeline('odyssey', 11, placesFile, journeysFile);
    const cimmerian = timeline.find((e) => e.place.id === 'cimmerians-underworld');
    expect(cimmerian).toBeDefined();
    expect(cimmerian!.place.coords).toBeUndefined();
  });

  it('a book with zero mappable places resolves every scene to null', () => {
    const scenes: Scene[] = [{ summary: 'x', startLine: 1, endLine: 10 }];
    const resolved = joinScenesToPlaces('odyssey', 9, scenes, { places: [] }, { journeys: [] });
    expect(resolved).toEqual([null]);
  });

  it('is deterministic for the same inputs', () => {
    const scenes = scenesForBook(odyssey, 9);
    const a = joinScenesToPlaces('odyssey', 9, scenes, placesFile, journeysFile);
    const b = joinScenesToPlaces('odyssey', 9, scenes, placesFile, journeysFile);
    expect(a).toEqual(b);
  });
});
