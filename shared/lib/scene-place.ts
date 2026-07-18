// Pure library that joins a book's Landmark-style scene apparatus (Scene, see
// shared/lib/data.ts) to real geographic data — apparatus/places.json's per-
// place `mentions` and apparatus/journeys.json's per-leg `refs` — so Reading
// Mode's per-scene figure plate (see docs/... the scene-map foundation,
// shared/lib/scenemap.ts) knows which place (and, where a journey leg covers
// the moment, which route) to draw for a given scene page.
//
// THE JOIN PROBLEM: a scene's own `location` field (apparatus/scenes/<work>.json)
// is free prose ("Polyphemus's cave") that does NOT match any places.json id or
// name directly — there is no per-scene placeId in the emitted data. What DOES
// exist, and is real (not invented): every places.json place carries `mentions`
// (work/book/line-range where the Greek names it), and every journeys.json leg
// carries `refs` (work/book/line-range where that leg of the journey happens),
// with `to` being the place the narrative has just arrived at. Both are anchored
// to the SAME vulgate line numbering scenes use.
//
// THE ALGORITHM: build one ascending-by-line timeline per (work, book) merging
// both sources (journeys.json first, so a tie on line prefers the richer
// journey-leg entry — its route arc — over a bare place mention). For a given
// scene, the resolved "current place" is the LAST timeline entry at or before
// the scene's own startLine (the most recently established location — e.g. once
// Od. 9 lines 105-106 establish "Land of the Cyclopes", every later scene in
// that book up to the next journey leg still reads as the Cyclopes' shore/cave,
// matching the approved Variant B mock's scene 12 (the cave) showing the
// Cyclopes plate). A scene with NO timeline entry before it (e.g. Il. 1's
// proem, before the book names anything) falls back to the book's EARLIEST
// timeline entry — an "establishing" anchor, honest because it's still real
// mention data, just temporally anticipatory rather than retrospective.
//
// APPARATUS HONESTY: a resolved anchor whose place has no `coords` (mythical
// tier, e.g. Ogygia, the Cimmerians' land) is reported with `place.coords`
// undefined — callers (the plate component) must render NO map for that scene,
// never a fabricated pin. This mirrors scenemap.ts's own posture exactly and
// composes with it: renderSceneMap/renderRoute already degrade a
// route whose origin (but not destination) lacks coords into a symbolic stub,
// which this module leans on rather than reimplementing.
//
// A book with NO mentions and NO journey-leg refs at all (timeline empty) means
// every scene in it resolves to `null` — the plate renders title/metadata only.

import type { ScenePlace, RouteLeg, Certainty } from './scenemap';
import type { Scene } from './data';

// ── Input shapes (apparatus/places.json, apparatus/journeys.json) ──────────

export interface PlaceMention {
  work: string;
  book: number;
  lines: [number, number];
}

export interface RawPlace {
  id: string;
  name: string;
  certainty?: Certainty;
  coords?: [number, number];
  mentions?: PlaceMention[];
}

export interface PlacesFile {
  places: RawPlace[];
}

export interface JourneyLegRef {
  work: string;
  book: number;
  lines: [number, number];
}

export interface JourneyLeg {
  from: string; // places.json id
  to: string;   // places.json id
  refs: JourneyLegRef[];
  unlocatable?: boolean;
}

export interface Journey {
  id: string;
  legs: JourneyLeg[];
}

export interface JourneysFile {
  journeys: Journey[];
}

export interface SceneTimelineEntry {
  line: number;
  place: ScenePlace;
  route?: RouteLeg;
}

export interface ScenePlaceResolution {
  place: ScenePlace;
  route?: RouteLeg;
}

function toScenePlace(raw: RawPlace): ScenePlace {
  return { id: raw.id, name: raw.name, coords: raw.coords, certainty: raw.certainty };
}

// Builds the (work, book) timeline: one entry per places.json mention in this
// book, plus one entry per journey leg whose ref falls in this book (entry
// line = the ref's opening line; place = the leg's `to`; route = {from, to}
// so a caller can draw the arc — even when `to` lacks coords, since a
// mythical-tier arrival is still a real narrative event, just not one this
// module or scenemap.ts will draw a pin for).
export function buildSceneTimeline(
  work: string,
  book: number,
  placesFile: PlacesFile,
  journeysFile?: JourneysFile,
): SceneTimelineEntry[] {
  const byId = new Map<string, RawPlace>(placesFile.places.map((p) => [p.id, p]));
  const entries: SceneTimelineEntry[] = [];

  for (const journey of journeysFile?.journeys ?? []) {
    for (const leg of journey.legs) {
      const to = byId.get(leg.to);
      if (!to) continue; // defensive: a leg referencing an id absent from places.json
      const from = byId.get(leg.from);
      for (const ref of leg.refs) {
        if (ref.work !== work || ref.book !== book) continue;
        entries.push({
          line: ref.lines[0],
          place: toScenePlace(to),
          route: from ? { from: toScenePlace(from), to: toScenePlace(to) } : undefined,
        });
      }
    }
  }

  for (const raw of placesFile.places) {
    for (const m of raw.mentions ?? []) {
      if (m.work !== work || m.book !== book) continue;
      entries.push({ line: m.lines[0], place: toScenePlace(raw) });
    }
  }

  // Stable sort: entries pushed above (journey legs) precede same-book
  // mentions pushed below, so a tie on `line` prefers the journey-leg entry
  // (and its route) — Array.prototype.sort is stable per spec.
  return entries.sort((a, b) => a.line - b.line);
}

// Resolves each scene in `scenes` (already in document order) to its current
// place per the timeline built above, or null when the book's timeline is
// empty (no mappable place anywhere in it). Pure and deterministic: identical
// inputs always produce identical output, no mutation of `scenes`.
export function resolveScenePlaces(
  scenes: Scene[],
  timeline: SceneTimelineEntry[],
): (ScenePlaceResolution | null)[] {
  if (!timeline.length) return scenes.map(() => null);
  return scenes.map((scene) => {
    let best: SceneTimelineEntry | null = null;
    for (const entry of timeline) {
      if (entry.line > scene.startLine) break; // timeline is sorted ascending — nothing further can qualify
      // A later timeline entry for the SAME place (e.g. a journey leg's
      // arrival at line 105 followed by that place's plain mention at line
      // 106 — both "we're at the Cyclopes' land now") re-confirms rather than
      // supersedes: keep the richer (route-bearing) entry's route instead of
      // letting the plain mention silently drop it.
      best = best && best.place.id === entry.place.id
        ? { line: entry.line, place: entry.place, route: best.route ?? entry.route }
        : entry;
    }
    // No entry at or before this scene (e.g. Il. 1's proem, before the book
    // names anything yet): fall back to the book's earliest entry, an
    // "establishing" anchor rather than leaving the scene unmapped.
    const resolved = best ?? timeline[0];
    return { place: resolved.place, route: resolved.route };
  });
}

// Convenience one-shot combining both steps for a single (work, book, scenes)
// call — what the reader component actually calls.
export function joinScenesToPlaces(
  work: string,
  book: number,
  scenes: Scene[],
  placesFile: PlacesFile,
  journeysFile?: JourneysFile,
): (ScenePlaceResolution | null)[] {
  const timeline = buildSceneTimeline(work, book, placesFile, journeysFile);
  return resolveScenePlaces(scenes, timeline);
}
