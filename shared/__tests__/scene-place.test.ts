import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  buildSceneTimeline,
  resolveScenePlaces,
  joinScenesToPlaces,
  SCHEMATIC_PLATE_ID,
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

// NOTE ON THIS REWRITE (2026-07-18): the previous version of this file
// encoded the OLD mention-timeline resolver's behavior — e.g. asserting that
// Il. 1's proem "falls back" to Chryse (line 37's mention), and that Od. 9
// scene 12 resolves via a mention/journey tie-break. That resolver was
// content-audited and found systemically wrong (see
// scratchpad/SCENE-PLACE-AUDIT-REPORT.md): mentions are almost always
// SPEECH material (homelands, catalogues, lying tales), not scene settings,
// so the old tests were encoding wrong claims about the world. Per project
// doctrine ("wrong tests get replaced, not appeased"), those assertions are
// gone; this file tests the rewritten resolver (curated setting dictionary
// first, journey-leg timeline as fallback, no mention timeline, no
// establishing fallback) against the specific disasters the audit found and
// the mechanisms that still make it work.

describe('buildSceneTimeline (journey-leg-only; real apparatus data)', () => {
  it('carries ONLY journey-leg entries — no place-mention entries — for Od. 9', () => {
    const timeline = buildSceneTimeline('odyssey', 9, placesFile, journeysFile);
    const lines = timeline.map((e) => e.line);
    expect(lines).toEqual([...lines].sort((a, b) => a - b));
    // cyclopes-land arrives via the lotus-eaters-land -> cyclopes-land leg.
    expect(timeline.some((e) => e.place.id === 'cyclopes-land')).toBe(true);
    // Every entry must carry a route (journey legs always do) — proves no
    // bare mention entries have leaked back in.
    expect(timeline.every((e) => !!e.route)).toBe(true);
  });

  it('returns an empty timeline for a (work, book) with no journey-leg refs at all', () => {
    const timeline = buildSceneTimeline('odyssey', 9, { places: [] }, { journeys: [] });
    expect(timeline).toEqual([]);
  });

  it('returns an empty timeline even when places.json has rich mentions but journeysFile is omitted', () => {
    // Il. 1 has plenty of places.json mentions (Chryse, Phthia, Thebe, Cilla)
    // but no journey legs — the old resolver used those mentions as a
    // timeline; the new one must not.
    const timeline = buildSceneTimeline('iliad', 1, placesFile, undefined);
    expect(timeline).toEqual([]);
  });
});

describe('resolveScenePlaces / joinScenesToPlaces — audit-confirmed defects, fixed', () => {
  const odyssey: RawScenesFile = JSON.parse(readFileSync(SCENES_ODYSSEY_PATH, 'utf-8'));
  const iliad: RawScenesFile = JSON.parse(readFileSync(SCENES_ILIAD_PATH, 'utf-8'));

  it('Il. 1.285-317 (the assembly disperses at the ships) no longer resolves to Phthia', () => {
    // Seed defect: Achilles' threat "I will go to Phthia" at 1.155/1.169 used
    // to hijack this and six other scenes via the mention timeline. The
    // scene's own location prose is "Achaean assembly" -> the Troad camp pin.
    const scenes = scenesForBook(iliad, 1);
    const scene = scenes.find((s) => s.startLine === 285)!;
    expect(scene.place).toBe('Achaean assembly');
    const resolved = joinScenesToPlaces('iliad', 1, scenes, placesFile, journeysFile);
    const idx = scenes.indexOf(scene);
    expect(resolved[idx]).not.toBeNull();
    expect(resolved[idx]!.place.id).toBe('troy');
    expect(resolved[idx]!.place.id).not.toBe('phthia');
  });

  it('all of Il. 10 (the Doloneia) resolves to the Troad camp/plain, never Thymbra', () => {
    // Old defect: Dolon's own speech describing the camp layout (~10.430)
    // hijacked all 16 scenes of the book to Thymbra.
    const scenes = scenesForBook(iliad, 10);
    const resolved = joinScenesToPlaces('iliad', 10, scenes, placesFile, journeysFile);
    expect(resolved).toHaveLength(16);
    for (const r of resolved) {
      expect(r).not.toBeNull();
      expect(r!.place.id).toBe('troy');
    }
  });

  it('every Od. 23 scene (recognition through the marriage bed) resolves to Ithaca, never the Lotus-eaters', () => {
    // Old defect: Odysseus's own post-reunion recap, "how he came to the
    // Lotus-eaters" (23.311), hijacked the entire book.
    const scenes = scenesForBook(odyssey, 23);
    const resolved = joinScenesToPlaces('odyssey', 23, scenes, placesFile, journeysFile);
    expect(resolved.length).toBeGreaterThan(0);
    for (const r of resolved) {
      expect(r).not.toBeNull();
      expect(r!.place.id).toBe('ithaca');
      expect(r!.place.id).not.toBe('lotus-eaters-land');
    }
  });

  it('Od. 14 (at Eumaeus\'s hut) resolves to Ithaca throughout, never Egypt (the Cretan lying tale)', () => {
    // Old defect: the Cretan lying tale's "we came to fair-flowing Egypt"
    // (14.257-258) hijacked the whole book even though the scene's own
    // location prose never leaves the hut.
    const scenes = scenesForBook(odyssey, 14);
    const resolved = joinScenesToPlaces('odyssey', 14, scenes, placesFile, journeysFile);
    expect(resolved.length).toBeGreaterThan(0);
    for (const r of resolved) {
      expect(r).not.toBeNull();
      expect(r!.place.id).toBe('ithaca');
      expect(r!.place.id).not.toBe('egypt');
    }
  });

  it('every scene whose location prose names Olympus resolves to olympus — never a mortal toponym', () => {
    // Gazetteer entry "olympus" (Mount Olympus, Thessaly/Macedonia) was
    // added so divine-council scenes get an honest map pin. Split strings
    // ("Olympus / X", "Troy / Olympus", "Olympus; Ithaca") pin to olympus
    // too: the divine frame dominates (John, 2026-07-18). Dictionary
    // coverage replaces the old null-guard that existed only because no
    // entry existed — journey-leg hijack (e.g. Od. 13 "Olympus / Scheria"
    // → Ithaca) must still not occur.
    let olympusSceneCount = 0;
    for (const [work, raw] of [['iliad', iliad] as const, ['odyssey', odyssey] as const]) {
      for (const book of raw.books) {
        const scenes = scenesForBook(raw, book.book);
        const resolved = joinScenesToPlaces(work, book.book, scenes, placesFile, journeysFile);
        scenes.forEach((s, i) => {
          if (s.place && /olympus/i.test(s.place)) {
            olympusSceneCount += 1;
            expect(resolved[i]).not.toBeNull();
            expect(resolved[i]!.place.id).toBe('olympus');
            expect(resolved[i]!.place.id).not.toBe('ithaca');
            expect(resolved[i]!.place.id).not.toBe('troy');
            expect(resolved[i]!.place.id).not.toBe('scheria');
          }
        });
      }
    }
    expect(olympusSceneCount).toBeGreaterThan(0);
  });

  it('a scene whose location does not mention Olympus never resolves to olympus spuriously', () => {
    // Spot-check well-known mortal settings that must stay on their own pins.
    const il1 = scenesForBook(iliad, 1);
    const il1r = joinScenesToPlaces('iliad', 1, il1, placesFile, journeysFile);
    const assemblyIdx = il1.findIndex((s) => s.place === 'Achaean assembly');
    expect(assemblyIdx).toBeGreaterThanOrEqual(0);
    expect(il1r[assemblyIdx]!.place.id).toBe('troy');
    expect(il1r[assemblyIdx]!.place.id).not.toBe('olympus');

    const od14 = scenesForBook(odyssey, 14);
    const od14r = joinScenesToPlaces('odyssey', 14, od14, placesFile, journeysFile);
    for (const r of od14r) {
      expect(r).not.toBeNull();
      expect(r!.place.id).toBe('ithaca');
      expect(r!.place.id).not.toBe('olympus');
    }
  });

  it('the Apologoi telling-frame scenes (Alcinous\'s palace / "Ithaca (described)") resolve to Scheria, not the told place', () => {
    const scenes = scenesForBook(odyssey, 9);
    const resolved = joinScenesToPlaces('odyssey', 9, scenes, placesFile, journeysFile);
    const palaceIdx = scenes.findIndex((s) => s.place === 'the palace of Alcinous');
    const describedIdx = scenes.findIndex((s) => s.place === 'Ithaca (described)');
    expect(palaceIdx).toBeGreaterThanOrEqual(0);
    expect(describedIdx).toBeGreaterThanOrEqual(0);
    expect(resolved[palaceIdx]!.place.id).toBe('scheria');
    expect(resolved[describedIdx]!.place.id).toBe('scheria');
    expect(resolved[describedIdx]!.place.id).not.toBe('ithaca');

    // Also true of the Od. 11 intermezzo, where narration briefly returns to
    // the frame mid-Nekyia (11.333-384).
    const od11 = scenesForBook(odyssey, 11);
    const od11Resolved = joinScenesToPlaces('odyssey', 11, od11, placesFile, journeysFile);
    const intermezzoIdx = od11.findIndex((s) => s.place === 'the palace of Alcinous');
    expect(intermezzoIdx).toBeGreaterThanOrEqual(0);
    expect(od11Resolved[intermezzoIdx]!.place.id).toBe('scheria');
  });

  it('a journey-leg wandering scene not covered by the dictionary still resolves via the leg (Od. 12 strait, book-scoped entry)', () => {
    // Od. 12.222-259 ("the strait of Scylla and Charybdis") is NOT a
    // work-wide dictionary entry (that string is transit-generic elsewhere),
    // but IS a book-scoped entry for book 12 specifically, resolving to
    // Charybdis rather than the journey-leg timeline's own anticipatory
    // ref lines (which sit inside Circe's speech at 12.39-127 and would
    // otherwise resolve this scene to Thrinacia).
    const scenes = scenesForBook(odyssey, 12);
    const resolved = joinScenesToPlaces('odyssey', 12, scenes, placesFile, journeysFile);
    const idx = scenes.findIndex((s) => s.startLine === 222);
    expect(scenes[idx].place).toBe('the strait of Scylla and Charybdis');
    expect(resolved[idx]).not.toBeNull();
    expect(resolved[idx]!.place.id).toBe('charybdis');
  });

  it('a line-spanned book-scoped rule splits Od. 12 "at sea": Sirens approach pins, post-Thrinacia wreck is explicit null', () => {
    // "at sea" names different waters at its two Od. 12 occurrences (caught
    // by the 2026-07-18 verification gate): 12.201-221 sits just past the
    // Sirens, but 12.404-425 is the open-water wreck after leaving Thrinacia
    // (12.403-404: no land in sight). The wreck scene must resolve null —
    // and specifically NOT fall through to the journey-leg timeline, whose
    // Circe's-speech ref lines would hijack it.
    const scenes = scenesForBook(odyssey, 12);
    const resolved = joinScenesToPlaces('odyssey', 12, scenes, placesFile, journeysFile);
    const sirensIdx = scenes.findIndex((s) => s.place === 'at sea' && s.startLine === 201);
    const wreckIdx = scenes.findIndex((s) => s.place === 'at sea' && s.startLine === 404);
    expect(sirensIdx).toBeGreaterThanOrEqual(0);
    expect(wreckIdx).toBeGreaterThanOrEqual(0);
    expect(resolved[sirensIdx]!.place.id).toBe('sirens-island');
    expect(resolved[wreckIdx]).toBeNull();
  });

  it('a genuine journey-leg fallback case still works: Od. 13.70-92 (Phaeacian ship at sea) resolves to Ithaca via the scheria->ithaca leg', () => {
    // "at sea" is deliberately NOT in the dictionary (too generic across the
    // corpus) so this scene must resolve via the journey-leg timeline alone —
    // and the scheria->ithaca leg's ref (13.70-125) covers it exactly.
    const scenes = scenesForBook(odyssey, 13);
    const resolved = joinScenesToPlaces('odyssey', 13, scenes, placesFile, journeysFile);
    const idx = scenes.findIndex((s) => s.startLine === 70);
    expect(scenes[idx].place).toBe('at sea');
    expect(resolved[idx]).not.toBeNull();
    expect(resolved[idx]!.place.id).toBe('ithaca');
    expect(resolved[idx]!.route?.from.id).toBe('scheria');
    expect(resolved[idx]!.route?.to.id).toBe('ithaca');
  });

  it('an unmappable location string (no dictionary entry, no journey leg covering it) resolves null, never a fabricated anchor', () => {
    // Il. 1's proem (1-7) names no place at all; the old resolver's
    // "establishing fallback" invented an anchor (Chryse) for it. The new
    // resolver has no such fallback.
    const scenes = scenesForBook(iliad, 1);
    const scene1 = scenes[0];
    expect(scene1.startLine).toBe(1);
    expect(scene1.place).toBe('proem');
    const resolved = joinScenesToPlaces('iliad', 1, scenes, placesFile, journeysFile);
    expect(resolved[0]).toBeNull();
  });

  it('a mythical-tier journey-leg anchor with no coords (the Cimmerians\' land, Od. 11 Nekyia) is reported coordless, never fabricated', () => {
    const scenes = scenesForBook(odyssey, 11);
    const resolved = joinScenesToPlaces('odyssey', 11, scenes, placesFile, journeysFile);
    const idx = scenes.findIndex((s) => s.place === 'the edge of Ocean' && s.startLine === 51);
    expect(idx).toBeGreaterThanOrEqual(0);
    expect(resolved[idx]).not.toBeNull();
    expect(resolved[idx]!.place.id).toBe('cimmerians-underworld');
    expect(resolved[idx]!.place.coords).toBeUndefined();
  });

  it('a book with zero mappable places (no dictionary hits, no journey legs) resolves every scene to null', () => {
    const scenes: Scene[] = [{ summary: 'x', startLine: 1, endLine: 10, place: 'nowhere in the dictionary' }];
    const resolved = joinScenesToPlaces('odyssey', 9, scenes, { places: [] }, { journeys: [] });
    expect(resolved).toEqual([null]);
  });

  it('is deterministic for the same inputs', () => {
    const scenes = scenesForBook(odyssey, 9);
    const a = joinScenesToPlaces('odyssey', 9, scenes, placesFile, journeysFile);
    const b = joinScenesToPlaces('odyssey', 9, scenes, placesFile, journeysFile);
    expect(a).toEqual(b);
  });

  it('Phase P7a: scene.places[] takes precedence over a SETTING_DICTIONARY match for the same scene', () => {
    // Il. 1's "Achaean assembly" would normally resolve to 'troy' via the
    // dictionary; authoring scene.places must override that.
    const scenes = scenesForBook(iliad, 1);
    const scene = scenes.find((s) => s.startLine === 285)!;
    expect(scene.place).toBe('Achaean assembly'); // dictionary would say 'troy'
    const authored: Scene = { ...scene, places: ['olympus'] };
    const timeline = buildSceneTimeline('iliad', 1, placesFile, journeysFile);
    const resolved = resolveScenePlaces('iliad', 1, [authored], timeline, placesFile);
    expect(resolved[0]).not.toBeNull();
    expect(resolved[0]!.place.id).toBe('olympus');
    expect(resolved[0]!.places.map((p) => p.id)).toEqual(['olympus']);
  });

  it('a scene.places[] id that resolves to a coordless gazetteer record does not become a located place', () => {
    // 'ogygia' (mythical tier) has no coords in the real gazetteer.
    const scene: Scene = { summary: 'x', startLine: 1, endLine: 10, places: ['ogygia'] };
    const resolved = resolveScenePlaces('odyssey', 5, [scene], [], placesFile);
    expect(resolved[0]).not.toBeNull();
    expect(resolved[0]!.place.id).toBe('ogygia'); // still counts for `place` — unchanged coordless posture
    expect(resolved[0]!.places).toEqual([]); // never force-pinned into the located list
  });

  it('an unresolvable scene.places[] id is dropped without throwing, falling through to the dictionary', () => {
    const scenes = scenesForBook(iliad, 1);
    const scene = scenes.find((s) => s.startLine === 285)!; // 'Achaean assembly' -> dictionary hit 'troy'
    const authored: Scene = { ...scene, places: ['no-such-place-id'] };
    const timeline = buildSceneTimeline('iliad', 1, placesFile, journeysFile);
    expect(() => resolveScenePlaces('iliad', 1, [authored], timeline, placesFile)).not.toThrow();
    const resolved = resolveScenePlaces('iliad', 1, [authored], timeline, placesFile);
    expect(resolved[0]).not.toBeNull();
    expect(resolved[0]!.place.id).toBe('troy'); // fell through to the dictionary, per precedence
  });

  it('every existing resolution still carries `places` mirroring the singular `place` (steps 1/2, no authored scene.places[])', () => {
    // Existing callers only ever read `place` — this asserts the new `places`
    // field is well-formed alongside it for the dictionary and journey-leg
    // paths, without changing `place`'s own meaning.
    const scenes = scenesForBook(odyssey, 9);
    const resolved = joinScenesToPlaces('odyssey', 9, scenes, placesFile, journeysFile);
    for (const r of resolved) {
      if (r === null) continue;
      if (r.place.coords !== undefined) {
        expect(r.places.map((p) => p.id)).toEqual([r.place.id]);
      } else {
        expect(r.places).toEqual([]); // coordless anchor (e.g. mythical tier) — never force-pinned
      }
    }
  });

  it('the setting dictionary takes precedence over the journey-leg timeline when both would apply', () => {
    // Od. 9 scene "Polyphemus's cave" (193-460) falls well inside the
    // lotus-eaters-land -> cyclopes-land leg's coverage AND has its own
    // dictionary entry (both resolve to cyclopes-land here, so this also
    // doubles as the "journey-leg case still works" precedent for the
    // dictionary-covered portion of the Apologoi) — the dictionary entry is
    // what actually fires, per resolveScenePlaces's documented precedence.
    const scenes = scenesForBook(odyssey, 9);
    const resolved = joinScenesToPlaces('odyssey', 9, scenes, placesFile, journeysFile);
    const idx = scenes.findIndex((s) => s.startLine === 193);
    expect(scenes[idx].place).toBe("Polyphemus's cave");
    expect(resolved[idx]!.place.id).toBe('cyclopes-land');
  });
});

describe('resolveScenePlaces — schematic-only routing (queue item 3b, 2026-07-30)', () => {
  // A local copy of scenesForBook that ALSO carries scene.places[] through.
  // Deliberately NOT folded into the shared scenesForBook above: several
  // existing tests in this file call scenesForBook on real Il. 1/10 data and
  // rely on it NOT authoring places[], to exercise the dictionary/journey
  // precedence tiers specifically. In the real corpus, Il. 1 and Il. 10 are
  // now almost entirely authored with places[] (19/20 and 16/16 scenes) —
  // wiring places[] into the shared helper would silently move those
  // existing tests onto precedence step 0 instead of the tiers they mean to
  // test. This helper is used only by the tests below.
  interface RawSceneBookWithPlaces {
    book: number;
    scenes: {
      lines: [number, number];
      summary: string;
      location?: string;
      dayNumber?: number | null;
      places?: string[];
    }[];
  }
  interface RawScenesFileWithPlaces {
    books: RawSceneBookWithPlaces[];
  }
  function scenesForBookWithPlaces(raw: RawScenesFileWithPlaces, book: number): Scene[] {
    const b = raw.books.find((x) => x.book === book);
    if (!b) throw new Error(`no book ${book}`);
    return b.scenes.map((s) => ({
      summary: s.summary,
      startLine: s.lines[0],
      endLine: s.lines[1],
      place: s.location,
      day: s.dayNumber,
      places: s.places,
    }));
  }

  it('a scene naming only an anchored, coordless poem-place routes to the schematic plate', () => {
    // scaean-gate: no real-world coords, plateAnchors['trojan-plain-schematic']
    // + positionBasis:'conjectural' — exactly the honesty pair
    // resolvePlacePosition (plate.ts) requires.
    const scene: Scene = { summary: 'x', startLine: 1, endLine: 5, places: ['scaean-gate'] };
    const resolved = resolveScenePlaces('iliad', 3, [scene], [], placesFile);
    expect(resolved[0]).not.toBeNull();
    expect(resolved[0]!.places).toEqual([]); // no coords-bearing place — the live scene map has nothing to draw
    expect(resolved[0]!.schematic).toEqual({
      plateId: SCHEMATIC_PLATE_ID,
      focusIds: ['scaean-gate'],
      unzoomed: false,
    });
  });

  it('a scene naming a geographic (coords-bearing) place does not switch to schematic, even a dual-anchored one', () => {
    // thymbra carries BOTH real coords AND a trojan-plain-schematic anchor —
    // a genuine dual-plate place. The geographic path must still win.
    const scene: Scene = { summary: 'x', startLine: 1, endLine: 5, places: ['thymbra'] };
    const resolved = resolveScenePlaces('iliad', 10, [scene], [], placesFile);
    expect(resolved[0]).not.toBeNull();
    expect(resolved[0]!.places.map((p) => p.id)).toEqual(['thymbra']);
    expect(resolved[0]!.schematic).toBeUndefined();
  });

  it('a plain geographic place alongside an anchored poem-place still does not switch to schematic', () => {
    const scene: Scene = { summary: 'x', startLine: 1, endLine: 5, places: ['troy', 'scaean-gate'] };
    const resolved = resolveScenePlaces('iliad', 3, [scene], [], placesFile);
    expect(resolved[0]!.places.map((p) => p.id)).toEqual(['troy']);
    expect(resolved[0]!.schematic).toBeUndefined();
  });

  it('scamandrian-plain yields the unzoomed frame — no anchor of its own, the whole sheet is the honest camera', () => {
    // Per its own places.json note: "a pin would put the plain at one point
    // of itself" — it carries no plateAnchors at all.
    const scene: Scene = { summary: 'x', startLine: 1, endLine: 5, places: ['scamandrian-plain'] };
    const resolved = resolveScenePlaces('iliad', 5, [scene], [], placesFile);
    expect(resolved[0]!.schematic).toEqual({
      plateId: SCHEMATIC_PLATE_ID,
      focusIds: [],
      unzoomed: true,
    });
  });

  it('scamandrian-plain alongside a point-anchored place still reports unzoomed:true', () => {
    // unzoomed must survive even when the scene also names a framable point —
    // the caller (Reader.svelte) is the one that lets unzoomed override
    // focusIds; this asserts the resolver reports both honestly rather than
    // picking a side.
    const scene: Scene = { summary: 'x', startLine: 1, endLine: 5, places: ['scamandrian-plain', 'scaean-gate'] };
    const resolved = resolveScenePlaces('iliad', 5, [scene], [], placesFile);
    expect(resolved[0]!.schematic).toEqual({
      plateId: SCHEMATIC_PLATE_ID,
      focusIds: ['scaean-gate'],
      unzoomed: true,
    });
  });

  it('never reports schematic for a scene resolved only via the dictionary or journey-leg timeline (real Od. 9 data)', () => {
    // Confirms the module comment's claim: none of the ~30 schematic-anchored
    // ids are reachable through SETTING_DICTIONARY or a journey leg today.
    const odyssey: RawScenesFileWithPlaces = JSON.parse(readFileSync(SCENES_ODYSSEY_PATH, 'utf-8'));
    const scenes = scenesForBookWithPlaces(odyssey, 9);
    const resolved = joinScenesToPlaces('odyssey', 9, scenes, placesFile, journeysFile);
    expect(resolved.every((r) => r === null || r.schematic === undefined)).toBe(true);
  });

  it('counts scenes actually gaining a schematic frame across the real Iliad corpus (dossier predicted ~280)', () => {
    const iliad: RawScenesFileWithPlaces = JSON.parse(readFileSync(SCENES_ILIAD_PATH, 'utf-8'));
    let schematicCount = 0;
    for (const b of iliad.books) {
      const scenes = scenesForBookWithPlaces(iliad, b.book);
      const timeline = buildSceneTimeline('iliad', b.book, placesFile, journeysFile);
      const resolved = resolveScenePlaces('iliad', b.book, scenes, timeline, placesFile);
      for (const r of resolved) {
        if (r?.schematic) schematicCount += 1;
      }
    }
    // Not a pinned regression value — apparatus growth will move it. Loose
    // bound around the dossier's ~280 prediction; the real number is logged
    // for the record.
    // eslint-disable-next-line no-console
    console.log(`[schematic-only routing] scenes gaining a frame: ${schematicCount}`);
    expect(schematicCount).toBeGreaterThan(200);
    expect(schematicCount).toBeLessThan(400);
  });
});
