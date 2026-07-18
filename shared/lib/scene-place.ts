// Pure library that joins a book's Landmark-style scene apparatus (Scene, see
// shared/lib/data.ts) to real geographic data — apparatus/journeys.json's
// per-leg `refs`, and a curated dictionary keyed on the scenes' own authored
// `location` prose — so Reading Mode's per-scene figure plate (see
// shared/lib/scenemap.ts) knows which place (and, where a journey leg covers
// the moment, which route) to draw for a given scene page.
//
// HISTORY / WHY THIS LOOKS THE WAY IT DOES (2026-07-18 rewrite): the previous
// version built a timeline from apparatus/places.json's per-place `mentions`
// (Greek-name-occurrence line ranges) and treated the most recent mention at
// or before a scene's startLine as "the narrative is here now." A content
// audit (scratchpad/SCENE-PLACE-AUDIT-REPORT.md) proved this systemically
// wrong: of 790 scenes, only ~155 resolved to the narratively correct place.
// Homeric place-names occur overwhelmingly inside SPEECH — homelands,
// catalogues, paradeigmata, lying tales, oath formulas — not as scene-setting.
// One speech mention (e.g. Achilles threatening at 1.155 "I will go to
// Phthia") poisoned every later scene in the book until the next mention
// overwrote it (all of Il. 1's assembly scenes resolved to Phthia; all of
// Il. 10's Doloneia resolved to Thymbra from Dolon's own speech; all of Od.
// 23 resolved to the Lotus-eaters from Odysseus's post-reunion recap; Od. 14
// resolved to Egypt from the Cretan lying tale). Mentions are no longer used
// to establish "current place" at all — see buildSceneTimeline below, which
// now carries ONLY journey-leg entries.
//
// THE JOIN, NOW: a scene's own `place` field (apparatus/scenes/<work>.json's
// `location`, carried onto Scene.place — see shared/lib/data.ts) is free
// prose ("Achaean assembly", "Eumaeus's hut", "Olympus") authored by the
// apparatus itself as the scene's setting — not a mention, a claim about
// where the scene IS. That prose still doesn't match any places.json id or
// name directly, so SETTING_DICTIONARY below (hand-curated, reviewed against
// every one of the 137 distinct location strings across all 790 scenes, see
// scratchpad/il-scenes-dump.txt and od-scenes-dump.txt) maps only the strings
// that identify a single gazetteer place with confidence. Precedence:
//   1. SETTING_DICTIONARY, keyed on the scene's own `place` prose (checked
//      book-scoped first, then work-wide) — authored ground truth wins.
//   2. journeys.json leg timeline (unchanged mechanism, kept because the
//      audit found it basically sound for the Apologoi's wandering legs,
//      e.g. Od. 6/9/10) — for scenes whose location prose isn't in the
//      dictionary (typically one-off wandering stops already well anchored
//      by their leg's `to`).
//   3. null — the plate renders title/metadata only, never a fabricated or
//      anticipatory pin. No "establishing fallback" to the book's earliest
//      timeline entry any more: that fallback was itself a defect class
//      (Il. 1's proem anticipating Chryse, Il. 22's chase anticipating the
//      washing-troughs before Achilles reaches them).
//
// APPARATUS HONESTY: a resolved anchor whose place has no `coords` (mythical
// tier, e.g. Ogygia, the Cimmerians' land) is reported with `place.coords`
// undefined — callers (the plate component) must render NO map for that
// scene, never a fabricated pin. This mirrors scenemap.ts's own posture
// exactly and composes with it: renderSceneMap/renderRoute already degrade a
// route whose origin (but not destination) lacks coords into a symbolic
// stub, which this module leans on rather than reimplementing.

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

// ── Curated setting dictionary ──────────────────────────────────────────────
//
// Maps a scene's own authored `location` prose (apparatus/scenes/<work>.json)
// to a places.json id, ONLY where the string identifies a single narrative
// setting with confidence. Reviewed against all 137 distinct location strings
// across all 790 scenes (48 books); every entry below was checked against the
// actual scene summaries it covers, not assumed from the string alone.
//
// Keys are looked up book-scoped first (`work|book|location`), then work-wide
// (`work|location`). In this dataset NO string actually needed book-scoped
// disambiguation — recurring strings like "the hall" and "the palace of
// Alcinous" turned out to be single-referent across every book they occur in
// (verified by grep across the full scene corpus, not sampled). The
// book-scoped tier exists for robustness / future apparatus growth, and is
// used for nothing today; every entry below is registered work-wide.
//
// Two strings are deliberately mapped to the FRAME rather than their literal
// content — the "telling-vs-told" fix the audit called for:
//   - "Ithaca (described)" (Od. 9.15-38): Odysseus, at Alcinous's table,
//     describes his homeland before starting the Apologoi. The location is
//     Scheria (the telling), not Ithaca (the told) — matches the treatment
//     of "the palace of Alcinous" itself, which recurs as the Apologoi's
//     frame in Od. 9 and 11's intermezzo (11.333-384).
//   - "Egypt (narrated)" (Od. 4.351-570): Menelaus, at Sparta, narrates his
//     Proteus encounter off Egypt to Telemachus. The apparatus's own
//     "(narrated)" marker signals this is told, not shown; the scene's frame
//     is Sparta throughout Od. 4. (Previously this whole span mis-resolved to
//     Libya/Argos/Pharos/Egypt/Sidon via speech-mention hijack — audit runs
//     #43-47.)
//
// Deliberately NOT mapped (left for journeys.json fallback or null):
//   - Generic transit strings with no fixed referent: "at sea", "the open
//     sea", "aboard ship", "near Ithaca, then Aeolia", "the road to Sparta",
//     "the open sea, near Scheria" — each spans wandering that a journey leg
//     already anchors more precisely, or is genuinely in-transit.
//   - Divine-tier "Olympus" and every "Olympus / X" split-scene string: no
//     "olympus" id exists in apparatus/places.json (confirmed by full-text
//     search) — CLAUDE.md's apparatus-honesty rule forbids a divine scene
//     inheriting a mortal toponym, so these resolve null rather than to
//     Ida/the battlefield/whatever mortal place the scene also touches.
//   - Nekyia strings ("the edge of Ocean", "the underworld", "the house of
//     Hades"): mythic-tier, no confident single pin — left out per the brief
//     ("when in doubt, leave it out"). journeys.json's aeaea<->
//     cimmerians-underworld legs (Od. 11.13-14, 12.1-2) already anchor these
//     scenes via the journey-leg fallback, coordless (honest — matches the
//     pre-existing "mythical-tier anchor with no coords" test).
//   - "the strait of Scylla and Charybdis": a one-off wandering stop the
//     journeys.json scylla->charybdis leg (Od. 12.101-104) already anchors
//     correctly; no need to duplicate it here.
//   - "Hephaestus's forge", "the depths of the sea", "the sea near
//     Samothrace and Imbros", "narrator's frame", "Olympus; Ithaca",
//     "proem": no confident single-place referent.
const SETTING_DICTIONARY: Record<string, string> = {
  // ── Iliad: Troad battlefield / camp (coarse but honest — the gazetteer
  // carries one Troad pin, `troy`; camp, plain, ships, and walls all render
  // as that single pin rather than nothing) ─────────────────────────────────
  'iliad|the Trojan plain': 'troy',
  'iliad|Trojan plain': 'troy',
  'iliad|Achaean camp': 'troy',
  'iliad|Achaean camp (night)': 'troy',
  "iliad|Achilles' camp": 'troy',
  'iliad|the plain before Troy': 'troy',
  'iliad|Achaean assembly': 'troy',
  'iliad|the Achaean ships': 'troy',
  "iliad|Achilles's hut": 'troy',
  'iliad|Troy': 'troy',
  'iliad|Achaean trench': 'troy',
  'iliad|Achaean wall': 'troy',
  'iliad|the Achaean wall': 'troy',
  'iliad|the Trojan wall': 'troy',
  'iliad|before Troy': 'troy',
  'iliad|the funeral games ground': 'troy',
  'iliad|the Achaean huts': 'troy',
  'iliad|Troy (the walls)': 'troy',
  'iliad|Troy (Scaean gates)': 'troy',
  'iliad|the pyre site': 'troy',
  'iliad|between the armies': 'troy',
  'iliad|the walls of Troy': 'troy',
  'iliad|Trojan camp': 'troy',
  "iliad|Priam's palace, Troy": 'troy',
  'iliad|Troy / the Trojan plain': 'troy',
  "iliad|Nestor's hut": 'troy',
  'iliad|the Trojan assembly': 'troy',
  'iliad|the oak tree, Trojan plain': 'troy',
  'iliad|the ships of Aias and Protesilaus': 'troy',
  'iliad|the Trojan ranks': 'troy',
  'iliad|shore near Troy': 'troy',
  'iliad|seashore': 'troy',
  'iliad|the trench': 'troy',
  'iliad|before the Scaean gate': 'troy',
  "iliad|Paris's chamber": 'troy',
  "iliad|Agamemnon's hut": 'troy',
  "iliad|Eurypylus's hut": 'troy',

  // ── Iliad: real, distinct Troad-region places the narrative actually
  // visits (not just a speech mentioning them) ──────────────────────────────
  'iliad|Chryse': 'chryse', // Il. 1.428-487: Odysseus sails to Chryse and back — an actual visit, not a mention.
  'iliad|Mount Ida': 'ida', // Zeus repeatedly withdraws to watch/act from Ida (8.47, 14.292-353 seduction, 15.1-33).
  'iliad|the river Xanthus': 'scamander', // Il. 21: the river fight; Xanthus = Scamander, same id.
  'iliad|Lemnos': 'lemnos', // Il. 14.230-291: Hera physically flies to Lemnos to persuade Sleep.

  // ── Odyssey: Ithaca (palace hall, farm, town — all confirmed Ithaca-only
  // by a full-corpus grep; "the hall" never denotes Sparta's or Scheria's
  // hall in this apparatus, which uses distinct strings for those) ─────────
  'odyssey|the hall': 'ithaca',
  'odyssey|hall of the palace': 'ithaca',
  "odyssey|Odysseus's palace, Ithaca": 'ithaca',
  'odyssey|Ithaca': 'ithaca',
  'odyssey|Ithacan assembly': 'ithaca',
  "odyssey|Laertes's farm": 'ithaca',
  'odyssey|palace of Odysseus': 'ithaca',
  "odyssey|Penelope's chamber": 'ithaca',
  'odyssey|Ithaca, the shore': 'ithaca',
  'odyssey|the portico': 'ithaca',
  'odyssey|the storeroom': 'ithaca',
  "odyssey|Ithaca, Eumaeus's hut": 'ithaca',
  "odyssey|Eumaeus's hut": 'ithaca', // Cretan lying tale (Od. 14) is SPOKEN there — the scene's own setting stays the hut.
  "odyssey|Ithaca, Eumaeus's farmstead": 'ithaca',
  'odyssey|upper chamber': 'ithaca',
  'odyssey|the courtyard': 'ithaca',
  'odyssey|the bedchamber': 'ithaca', // Od. 23's marriage bed — NOT the Lotus-eaters (23.311's mention was inside Odysseus's post-reunion recap).
  'odyssey|the assembly-place, Ithaca town': 'ithaca',
  'odyssey|the shore, Ithaca': 'ithaca',
  'odyssey|Ithaca; the sea': 'ithaca', // Od. 2.371-434: Athena gathers the crew on Ithaca; departure is the scene's tail end, not its setting.
  'odyssey|Ithaca, harbor of Phorcys': 'ithaca',
  'odyssey|Ithaca, the cave of the Naiads': 'ithaca',
  'odyssey|Ithaca harbor': 'ithaca',
  'odyssey|town, place of assembly': 'ithaca',
  'odyssey|outside the palace / road to town': 'ithaca',
  'odyssey|road to town': 'ithaca',
  'odyssey|the fountain of the nymphs': 'ithaca',
  'odyssey|outside the palace': 'ithaca',
  'odyssey|courtyard of the palace': 'ithaca',
  'odyssey|the palace, Ithaca': 'ithaca',
  'odyssey|Ithaca town': 'ithaca',
  'odyssey|palace threshold': 'ithaca',
  // Od. 4.768-847: the scene's own viewpoint is Penelope on Ithaca (fasting,
  // praying, visited by Athena's dream-phantom); the suitors' ambush at
  // Asteris is reported within it, not the scene's own vantage.
  'odyssey|Ithaca; the strait of Asteris': 'ithaca',

  // ── Odyssey: Scheria/Phaeacia, including the Apologoi's TELLING frame
  // (the narrated content of Od. 9-12 is Ithaca/the wanderings, but the
  // scene the reader is IN is Alcinous's hall) ──────────────────────────────
  'odyssey|the palace of Alcinous': 'scheria',
  "odyssey|Alcinous's palace, Scheria": 'scheria',
  'odyssey|Scheria': 'scheria',
  'odyssey|the river, Scheria': 'scheria',
  'odyssey|the road to the city, Scheria': 'scheria',
  'odyssey|the road to the city': 'scheria', // Od. 7.14-19: Odysseus nearing the Phaeacian city — no "Scheria" suffix on this occurrence, but same referent.
  'odyssey|outside the Phaeacian city': 'scheria',
  'odyssey|the assembly ground': 'scheria', // Od. 8.1-45: Phaeacian assembly.
  'odyssey|the games ground': 'scheria', // Od. 8.104-265: Phaeacian games (Iliad's funeral games use a distinct string, "the funeral games ground").
  'odyssey|Scheria, palace of Alcinous': 'scheria',
  'odyssey|the grove of Athena, Scheria': 'scheria',
  'odyssey|the coast of Scheria': 'scheria', // Od. 5.412-435: Odysseus washed ashore — arrival, not still-at-sea.
  'odyssey|a river mouth, Scheria': 'scheria',
  'odyssey|a wood near the river, Scheria': 'scheria',
  'odyssey|Ithaca (described)': 'scheria', // Od. 9.15-38: Odysseus describes Ithaca AT Scheria's table — telling, not told.

  // ── Odyssey: Sparta ────────────────────────────────────────────────────
  'odyssey|Sparta': 'sparta',
  'odyssey|Sparta, palace of Menelaus': 'sparta',
  "odyssey|Menelaus's palace, Sparta": 'sparta',
  // Od. 4.351-570: Menelaus's Proteus tale, apparatus-marked "(narrated)" —
  // the scene the reader is in is Sparta throughout Od. 4.
  'odyssey|Egypt (narrated)': 'sparta',

  // ── Odyssey: Pylos ─────────────────────────────────────────────────────
  'odyssey|Pylos': 'pylos',
  "odyssey|Nestor's palace, Pylos": 'pylos',
  'odyssey|Pylos, the shore': 'pylos',

  // ── Odyssey: Pherae (Diocles' house, the Pylos<->Sparta waystop) ──────────
  'odyssey|Pherae': 'pherae-messenia',

  // ── Odyssey: the Apologoi's wandering stops, keyed directly off the
  // scene's own location prose rather than left to journey-leg timing —
  // this is what fixes Od. 12's Circe-instruction scenes (12.59-141), whose
  // location is "Aeaea" throughout even though Circe's speech there NAMES
  // Sirens/Scylla/Charybdis/Thrinacia well before Odysseus reaches them ─────
  'odyssey|Ismarus': 'ismarus',
  'odyssey|the land of the Lotus-eaters': 'lotus-eaters-land',
  "odyssey|islet off the Cyclopes' land": 'cyclopes-land',
  'odyssey|the goat island': 'cyclopes-land',
  "odyssey|the Cyclopes' shore": 'cyclopes-land',
  "odyssey|Polyphemus's cave": 'cyclopes-land',
  'odyssey|the shore': 'cyclopes-land', // Od. 9.461-490 only occurrence: the Cyclopes' shore, right after escaping the cave.
  'odyssey|Aeolia': 'aeolia',
  'odyssey|the land of the Laestrygonians': 'laestrygonia',
  'odyssey|Aeaea': 'aeaea',
  "odyssey|Circe's house": 'aeaea',
  'odyssey|the isle of the Sirens': 'sirens-island',
  'odyssey|Thrinacia': 'thrinacia',
  'odyssey|Ogygia': 'ogygia', // Mythical tier, no coords — resolves but renders no pin (honest degradation, fixes the old "carry-forward-stale" Scheria mispin).
};

// Book-scoped tier: `${work}|${book}|${location}`. Checked before the
// work-wide tier above. In this dataset the ONLY strings that actually need
// book-scoping are three Od. 12 transit strings ("aboard ship", "at sea",
// "the strait of Scylla and Charybdis") that are generic elsewhere in the
// corpus (so can't take a work-wide entry without mis-mapping Od. 9/13/15's
// own "at sea" scenes) but have a single, confidently-identifiable referent
// within book 12 specifically. Root cause: journeys.json's four Od. 12 legs
// (aeaea->sirens, sirens->scylla, scylla->charybdis, scylla->thrinacia) all
// carry `refs` inside CIRCE'S OWN SPEECH (12.39-127, while the party is still
// at Aeaea — see her instructions run 12.28-141, all dictionary-mapped to
// "aeaea" above) rather than at the actual later arrivals; that's apparatus
// data this module's blast radius doesn't cover (apparatus/journeys.json).
// Left as journey-leg fallback, every scene between the real Sirens landfall
// (12.166) and the real Thrinacia arrival (12.260) would silently inherit
// whichever leg-entry line happens to be numerically closest — i.e. the SAME
// anticipatory-mention-hijack failure mode the mention-based timeline had,
// just relocated into journeys.json's ref lines. These three entries pin the
// three scenes it actually affects directly from their own location prose.
// A rule is either a plain place id, or line-spanned verdicts for a string
// that names DIFFERENT waters at different points in the same book: each
// span applies to scenes whose startLine <= upTo, first match wins, and an
// `id: null` span is an EXPLICIT no-pin verdict — it blocks the journey-leg
// fallback too, because for these scenes the fallback would reintroduce the
// anticipatory hijack (Circe's-speech ref lines) the dictionary exists to
// prevent.
type BookScopedRule = string | Array<{ upTo: number; id: string | null }>;
const BOOK_SCOPED_SETTING_DICTIONARY: Record<string, BookScopedRule> = {
  // Od. 12.142-165: "At dawn Circe departs" — the party is just weighing
  // anchor away from Aeaea, not yet anywhere else.
  'odyssey|12|aboard ship': 'aeaea',
  // "at sea" occurs twice in Od. 12 and names different waters each time
  // (caught by the verification gate, 2026-07-18):
  //   12.201-221 "Past the Sirens, seeing smoke and surf ahead" — between
  //   the Sirens (just passed) and the strait (not yet reached);
  //   12.404-425 the post-Thrinacia wreck — Thrinacia already out of sight
  //   (12.403-404: no land visible, only sky and sea) and Zeus's storm
  //   destroys the ship in open water: no honest pin exists, so explicit
  //   null rather than letting the journey fallback drift it anywhere.
  'odyssey|12|at sea': [
    { upTo: 259, id: 'sirens-island' },
    { upTo: Infinity, id: null },
  ],
  // Od. 12.222-259 (first pass, Scylla snatches six men) and 12.426-446
  // (second pass, clinging above Charybdis after the wreck): same string,
  // same strait: Charybdis is the strait's single named whirlpool-point in
  // both, and the second occurrence is explicitly IN Charybdis's grip.
  'odyssey|12|the strait of Scylla and Charybdis': 'charybdis',
};

// Returns a RawPlace pin, `null` for an explicit no-pin verdict (the caller
// must NOT fall through to the journey timeline), or `undefined` when the
// dictionary has no opinion (fallback may proceed).
function lookupSettingDictionary(
  work: string,
  book: number,
  location: string | undefined,
  startLine: number,
  byId: Map<string, RawPlace>,
): RawPlace | null | undefined {
  if (!location) return undefined;
  const rule = BOOK_SCOPED_SETTING_DICTIONARY[`${work}|${book}|${location}`];
  if (rule !== undefined) {
    const id = typeof rule === 'string'
      ? rule
      : rule.find((span) => startLine <= span.upTo)?.id;
    if (id === null) return null;
    return id ? byId.get(id) : undefined;
  }
  const id = SETTING_DICTIONARY[`${work}|${location}`];
  return id ? byId.get(id) : undefined;
}

// Builds the (work, book) JOURNEY-LEG timeline: one entry per journey leg
// whose ref falls in this book (entry line = the ref's opening line; place =
// the leg's `to`; route = {from, to} so a caller can draw the arc — even when
// `to` lacks coords, since a mythical-tier arrival is still a real narrative
// event, just not one this module or scenemap.ts will draw a pin for).
//
// Place MENTIONS (apparatus/places.json's `mentions`) are deliberately not
// part of this timeline any more — see the module comment above for why.
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

  return entries.sort((a, b) => a.line - b.line);
}

// No "olympus" id exists anywhere in apparatus/places.json (checked by full-
// text search) — the gazetteer has no pin for it. CLAUDE.md's apparatus-
// honesty rule ("divine scenes must never inherit a mortal toponym") means a
// scene whose own location prose names Olympus must resolve null rather than
// silently falling through to whatever mortal place a journey leg happens to
// be passing through at that line (the residual bug this guard closes: Od.
// 13.121-164 "Olympus / Scheria", a Poseidon-Zeus council, was landing on
// "Ithaca" purely because the scheria->ithaca leg's entry line preceded it —
// same anticipatory-hijack failure mode as the old mention timeline, just
// arrived at via a different mechanism). This check runs BEFORE the journey
// fallback (dictionary is still checked first — if a future entry ever maps
// an Olympus-containing string to a real id, this guard would need revising,
// but none exists today, by design).
const OLYMPUS_LOCATION_RE = /olympus/i;

// Resolves each scene in `scenes` (already in document order) to its current
// place. Precedence per scene:
//   1. SETTING_DICTIONARY, keyed on the scene's own authored `place` prose —
//      authored ground truth, checked first because it beats any inference.
//   2. Olympus guard (above) — forces null rather than journey fallback.
//   3. The journey-leg timeline built above: the LAST leg-arrival at or
//      before the scene's startLine (a wandering stop's own leg, not a
//      mention).
//   4. null — no fabricated "establishing" anchor any more.
// Pure and deterministic: identical inputs always produce identical output,
// no mutation of `scenes`.
export function resolveScenePlaces(
  work: string,
  book: number,
  scenes: Scene[],
  timeline: SceneTimelineEntry[],
  placesFile: PlacesFile,
): (ScenePlaceResolution | null)[] {
  const byId = new Map<string, RawPlace>(placesFile.places.map((p) => [p.id, p]));
  return scenes.map((scene) => {
    const dictionaryHit = lookupSettingDictionary(work, book, scene.place, scene.startLine, byId);
    if (dictionaryHit) {
      return { place: toScenePlace(dictionaryHit) };
    }
    if (dictionaryHit === null) {
      return null; // explicit dictionary verdict: open water, no honest pin — journey fallback would hijack.
    }
    if (scene.place && OLYMPUS_LOCATION_RE.test(scene.place)) {
      return null;
    }

    let best: SceneTimelineEntry | null = null;
    for (const entry of timeline) {
      if (entry.line > scene.startLine) break; // timeline is sorted ascending — nothing further can qualify
      // A later timeline entry for the SAME place (e.g. a journey leg's
      // arrival at line 105 followed by that place's plain mention at line
      // 106 — both "we're at the Cyclopes' land now") re-confirms rather than
      // supersedes: keep the richer (route-bearing) entry's route instead of
      // letting a later plain entry silently drop it.
      best = best && best.place.id === entry.place.id
        ? { line: entry.line, place: entry.place, route: best.route ?? entry.route }
        : entry;
    }
    if (!best) return null; // no dictionary hit, no journey-leg cover — honest null, not a fabricated anchor.
    return { place: best.place, route: best.route };
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
  return resolveScenePlaces(work, book, scenes, timeline, placesFile);
}
