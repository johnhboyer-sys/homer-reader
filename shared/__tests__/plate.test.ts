import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it, vi } from 'vitest';
import { project, viewportFromBBox } from '../lib/geo';
import {
  parsePlate,
  renderPlate,
  computeCamera,
  hachure,
  shipRow,
  wallGlyph,
  wallBandGlyph,
  tumulus,
  waterlines,
  labelCandidates,
  placeLabelCandidates,
  orientPathForReading,
  reliefHachureParams,
  hypsometricLevels,
  hypsometricStep,
  scaleBarMarkup,
  lineworkExtent,
  columnDots,
  lineworkReserveHalfWidth,
  wallInkHalfWidth,
  discClearsWallInk,
  traceSide,
  type Plate,
  type PlatePlace,
  type PlateLayer,
} from '../lib/plate';

const SEED_PLATE_PATH = '../apparatus/plates/trojan-plain.json';
const SCHEMATIC_SEED_PLATE_PATH = '../apparatus/plates/trojan-plain-schematic.json';
const SHIELD_SEED_PLATE_PATH = '../apparatus/plates/shield-of-achilles.json';

// A synthetic geographic plate fixture — deliberately NOT the live
// apparatus/plates/trojan-plain.json content for most tests (that file is
// read once below, in its own smoke test, since another lane is mid-flight
// on apparatus/places.json and this suite must not depend on its
// stability). bbox mirrors the seed plate's Troad-scale span.
const BBOX: [number, number, number, number] = [39.86, 26.12, 40.02, 26.36];
const SIZE: [number, number] = [400, 300];

const testPlate: Plate = {
  id: 'test-plate',
  title: 'Test Plate',
  kind: 'geographic',
  status: 'draft',
  seed: 42,
  bbox: BBOX,
  size: SIZE,
  layers: [
    {
      id: 'coast-1',
      kind: 'coast',
      style: 'approximate',
      rings: [
        [
          [39.98, 26.18],
          [39.97, 26.19],
          [39.96, 26.2],
        ],
      ],
    },
    {
      id: 'river-1',
      kind: 'river',
      path: [
        [39.9, 26.15],
        [39.95, 26.2],
      ],
      width: 2,
    },
    {
      id: 'relief-1',
      kind: 'relief',
      polygon: [
        [39.9, 26.15],
        [39.92, 26.3],
        [39.88, 26.3],
      ],
    },
    {
      id: 'wall-1',
      kind: 'wall',
      trace: [
        [39.95, 26.2],
        [39.96, 26.22],
        [39.97, 26.24],
      ],
    },
    {
      id: 'ships-1',
      kind: 'shipRow',
      baseline: [
        [39.9, 26.12],
        [39.9, 26.36],
      ],
      rows: 2,
      count: 6,
    },
    {
      id: 'camp-1',
      kind: 'region',
      polygon: [
        [39.91, 26.16],
        [39.93, 26.18],
        [39.91, 26.2],
      ],
    },
  ],
};

const troy: PlatePlace = { id: 'troy', name: 'Troy', coords: [39.957, 26.239], certainty: 'certain' };
const scamander: PlatePlace = { id: 'scamander-mouth', name: 'Scamander mouth', coords: [39.93, 26.2], certainty: 'traditional' };
const ghost: PlatePlace = { id: 'ghost-place', name: 'Unlocated Ghost', certainty: 'mythical' }; // no coords, per honesty rule

// A schematic plate (unit [u,v] space, e.g. a shield device) for exercising
// the plateAnchors/positionBasis honesty path — no defensible lat/lon.
const schematicPlate: Plate = {
  id: 'shield',
  title: 'Shield',
  kind: 'schematic',
  status: 'draft',
  size: [200, 200],
  layers: [],
};

const anchoredPlace: PlatePlace = {
  id: 'anchored-place',
  name: 'Anchored Place',
  certainty: 'certain',
  plateAnchors: { shield: [0.25, 0.75] },
  positionBasis: 'conjectural',
};

const anchorWithoutBasis: PlatePlace = {
  id: 'anchor-no-basis',
  name: 'Anchor Without Basis',
  plateAnchors: { shield: [0.5, 0.5] },
  // positionBasis deliberately omitted — pairing invalid per
  // apparatus_places.py's validate_plate; the renderer must not honour it.
};

const anchorForOtherPlate: PlatePlace = {
  id: 'anchor-other-plate',
  name: 'Anchor For Other Plate',
  plateAnchors: { 'some-other-plate': [0.1, 0.1] },
  positionBasis: 'conjectural',
};

describe('parsePlate', () => {
  it('parses the live seed plate (apparatus/plates/trojan-plain.json)', () => {
    const raw = JSON.parse(readFileSync(SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    expect(plate.id).toBe('trojan-plain');
    expect(plate.kind).toBe('geographic');
    expect(plate.layers.length).toBeGreaterThanOrEqual(2);
  });

  it('rejects a plate missing bbox', () => {
    const bad = { id: 'x', title: 'X', kind: 'geographic', status: 'draft', size: [100, 100], layers: [] };
    expect(() => parsePlate(bad)).toThrow(/missing bbox/);
  });

  it('rejects a layer coordinate outside the plate bbox', () => {
    const bad = {
      id: 'x',
      title: 'X',
      kind: 'geographic',
      status: 'draft',
      bbox: BBOX,
      size: SIZE,
      layers: [{ id: 'stray', kind: 'river', path: [[0, 0], [1, 1]] }],
    };
    expect(() => parsePlate(bad)).toThrow(/outside the plate bbox/);
  });

  it('rejects an unknown layer kind', () => {
    const bad = {
      id: 'x',
      title: 'X',
      kind: 'geographic',
      status: 'draft',
      bbox: BBOX,
      size: SIZE,
      layers: [{ id: 'mystery', kind: 'volcano' }],
    };
    expect(() => parsePlate(bad)).toThrow(/unknown layer kind/);
  });

  it('round-trips a valid plate unchanged in shape', () => {
    const plate = parsePlate(JSON.parse(JSON.stringify(testPlate)));
    expect(plate.layers.map((l) => l.id)).toEqual(testPlate.layers.map((l) => l.id));
  });

  // ── Gap 1: a schematic plate carries neither bbox nor a geographic
  // requirement — demanding one would demand a coordinate for something
  // that has none (mirrors apparatus_places.py's validate_plate exactly).

  it('parses the live trojan-plain-schematic.json as a bboxed schematic plate (east-up, right margin)', () => {
    const raw = JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8'));
    const geo = JSON.parse(readFileSync(SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    expect(plate.kind).toBe('schematic');
    expect(plate.bbox).toEqual(geo.bbox);
    expect(plate.rotationDeg).toBe(90);
    // Two furniture columns since ruling 12 (2026-09-03): the keys keep the
    // 340px measure they were designed at, the second column carries the three
    // inset panels. The MAP frame is unchanged at 1416 — the sheet grew to the
    // right only, so nothing on the face moved. Grew again for ruling 13 (the
    // citadel panel widened to 500 to hold the city plan): 792 -> 872.
    expect(plate.marginRight).toBe(872);
    expect(plate.size[0] - (plate.marginRight ?? 0)).toBe(1416);
    expect(plate.layers.length).toBeGreaterThan(0);
  });

  it('parses a schematic plate declaring only bands, no layers, no bbox (live seed plate: shield-of-achilles.json)', () => {
    const raw = JSON.parse(readFileSync(SHIELD_SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    expect(plate.kind).toBe('schematic');
    expect(plate.bbox).toBeUndefined();
    expect(plate.bands?.length).toBeGreaterThan(0);
    expect(plate.layers).toEqual([]);
  });

  it('rejects a schematic plate declaring neither bands nor layers (an empty schematic draws nothing)', () => {
    const bad = { id: 'x', title: 'X', kind: 'schematic', status: 'draft', size: [100, 100] };
    expect(() => parsePlate(bad)).toThrow(/must declare bands or layers/);
  });

  it('accepts a schematic layer with unit [u, v] coordinates in 0..1', () => {
    const ok = {
      id: 'x',
      title: 'X',
      kind: 'schematic',
      status: 'draft',
      size: [100, 100],
      layers: [{ id: 'river-u', kind: 'river', path: [[0.1, 0.2], [0.5, 0.6]] }],
    };
    expect(() => parsePlate(ok)).not.toThrow();
  });

  it('rejects a schematic layer with lat/lon-looking coordinates (outside 0..1)', () => {
    const bad = {
      id: 'x',
      title: 'X',
      kind: 'schematic',
      status: 'draft',
      size: [100, 100],
      layers: [{ id: 'river-latlon', kind: 'river', path: [[39.9, 26.15], [39.95, 26.2]] }],
    };
    expect(() => parsePlate(bad)).toThrow(/unit \[u, v\] pair in 0\.\.1/);
  });

  it('still rejects a geographic plate missing bbox (the schematic exemption does not leak to geographic)', () => {
    const bad = { id: 'x', title: 'X', kind: 'geographic', status: 'draft', size: [100, 100], layers: [] };
    expect(() => parsePlate(bad)).toThrow(/missing bbox/);
  });

  // ── Finding 6 (2026-07-28): duplicate layer ids defeat seed isolation —
  // per-layer hachure/stipple randomness is salted solely by layer id (see
  // deriveSeed in plate.ts), so two layers sharing an id draw byte-
  // identical texture. Message shape mirrors the Python validator's.

  it('rejects a plate with duplicate layer ids', () => {
    const bad = {
      id: 'dup-plate',
      title: 'Dup',
      kind: 'geographic',
      status: 'draft',
      bbox: BBOX,
      size: SIZE,
      layers: [
        { id: 'ships-1', kind: 'river', path: [[39.9, 26.15], [39.95, 26.2]] },
        { id: 'ships-1', kind: 'river', path: [[39.91, 26.16], [39.96, 26.21]] },
      ],
    };
    expect(() => parsePlate(bad)).toThrow(/plate dup-plate: duplicate layer id 'ships-1'/);
  });

  // ── Finding 3, TS side (2026-07-28): schema drift against
  // apparatus_places.py's validate_plate.

  it('rejects a non-positive size (zero/negative used to be accepted)', () => {
    const zero = { id: 'x', title: 'X', kind: 'geographic', status: 'draft', bbox: BBOX, size: [0, 100], layers: [] };
    expect(() => parsePlate(zero)).toThrow(/size must be two positive numbers/);
    const negative = { id: 'x', title: 'X', kind: 'geographic', status: 'draft', bbox: BBOX, size: [100, -5], layers: [] };
    expect(() => parsePlate(negative)).toThrow(/size must be two positive numbers/);
  });

  it('requires seed when a layer uses a stochastic style (stipple/hachure), and accepts it once supplied', () => {
    const stochasticLayers = [
      { id: 'coast-1', kind: 'coast', style: 'stipple', rings: [[[39.98, 26.18], [39.97, 26.19]]] },
    ];
    const missingSeed = { id: 'x', title: 'X', kind: 'geographic', status: 'draft', bbox: BBOX, size: SIZE, layers: stochasticLayers };
    expect(() => parsePlate(missingSeed)).toThrow(/seed is required/);
    const withSeed = { ...missingSeed, seed: 1 };
    expect(() => parsePlate(withSeed)).not.toThrow();
  });

  it('does not require seed when no layer uses a stochastic style', () => {
    const ok = {
      id: 'x', title: 'X', kind: 'geographic', status: 'draft', bbox: BBOX, size: SIZE,
      layers: [{ id: 'r', kind: 'river', path: [[39.9, 26.15], [39.95, 26.2]] }],
    };
    expect(() => parsePlate(ok)).not.toThrow();
  });

  it('rejects a whitespace-only status (accepted before trimming was enforced)', () => {
    const bad = { id: 'x', title: 'X', kind: 'geographic', status: '   ', bbox: BBOX, size: SIZE, layers: [] };
    expect(() => parsePlate(bad)).toThrow(/missing status/);
  });

  it('rejects an invalid layer default instead of silently dropping it to undefined', () => {
    const bad = {
      id: 'x', title: 'X', kind: 'geographic', status: 'draft', bbox: BBOX, size: SIZE,
      layers: [{ id: 'r', kind: 'river', default: 'true', path: [[39.9, 26.15], [39.95, 26.2]] }],
    };
    expect(() => parsePlate(bad)).toThrow(/unknown default/);
  });

  describe('sources validation', () => {
    it('rejects a source with no cite', () => {
      const bad = {
        id: 'x', title: 'X', kind: 'geographic', status: 'draft', bbox: BBOX, size: SIZE,
        layers: [{ id: 'r', kind: 'river', path: [[39.9, 26.15], [39.95, 26.2]], sources: [{ url: 'https://example.com' }] }],
      };
      expect(() => parsePlate(bad)).toThrow(/cite must be a non-empty string/);
    });

    it('rejects a blank (whitespace-only) cite', () => {
      const bad = {
        id: 'x', title: 'X', kind: 'geographic', status: 'draft', bbox: BBOX, size: SIZE,
        layers: [{ id: 'r', kind: 'river', path: [[39.9, 26.15], [39.95, 26.2]], sources: [{ cite: '   ' }] }],
      };
      expect(() => parsePlate(bad)).toThrow(/cite must be a non-empty string/);
    });

    it('rejects a source url that is not http(s)', () => {
      const bad = {
        id: 'x', title: 'X', kind: 'geographic', status: 'draft', bbox: BBOX, size: SIZE,
        layers: [{ id: 'r', kind: 'river', path: [[39.9, 26.15], [39.95, 26.2]], sources: [{ cite: 'Some Book', url: 'ftp://example.com' }] }],
      };
      expect(() => parsePlate(bad)).toThrow(/url must be http\(s\)/);
    });

    it('accepts a well-formed source (cite only, and cite + https url)', () => {
      const ok = {
        id: 'x', title: 'X', kind: 'geographic', status: 'draft', bbox: BBOX, size: SIZE,
        layers: [{ id: 'r', kind: 'river', path: [[39.9, 26.15], [39.95, 26.2]], sources: [{ cite: 'Some Book' }, { cite: 'Some Site', url: 'https://example.com' }] }],
      };
      expect(() => parsePlate(ok)).not.toThrow();
    });
  });
});

describe('renderPlate: determinism', () => {
  it('produces byte-identical SVG for identical input', () => {
    const a = renderPlate(testPlate, [troy, scamander]);
    const b = renderPlate(testPlate, [troy, scamander]);
    expect(a.svg).toBe(b.svg);
  });

  it('a different seed produces different SVG (the seed is actually wired to the stochastic primitives)', () => {
    const a = renderPlate(testPlate, [troy]);
    const b = renderPlate({ ...testPlate, seed: 999999 }, [troy]);
    expect(a.svg).not.toBe(b.svg);
  });
});

// Finding F5 (stage 6 review, 2026-09-03): toLocaleUpperCase()/localeCompare()
// read the runtime locale, so the same plate rendered SSR (Node's default
// locale) versus a browser set to e.g. tr-TR could disagree byte-for-byte —
// determinism the previous block's own test claims, undermined by two calls
// that read outside process state. Spying across a full render (which
// exercises labelText's caps path and the label solver's id-sort) proves
// neither is reachable any more.
describe('renderPlate: locale-independent output (F5, stage 6 review)', () => {
  it('never calls String.prototype.toLocaleUpperCase during renderPlate', () => {
    const spy = vi.spyOn(String.prototype, 'toLocaleUpperCase');
    renderPlate(testPlate, [troy, scamander]);
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });

  it('never calls String.prototype.localeCompare during renderPlate', () => {
    const spy = vi.spyOn(String.prototype, 'localeCompare');
    renderPlate(testPlate, [troy, scamander]);
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });

  it('uppercases a caps-styled label with toUpperCase, not toLocaleUpperCase (region role, kind "island")', () => {
    const lowerNamePlace: PlatePlace = {
      id: 'lower-name-place',
      name: 'island of ida',
      kind: 'island',
      coords: [39.9, 26.2],
      certainty: 'certain',
    };
    const result = renderPlate(testPlate, [lowerNamePlace]);
    expect(result.labelBoxes['lower-name-place']).toBeDefined();
    const match = result.svg.match(/<text[^>]*data-label-for="lower-name-place"[^>]*>([^<]*)<\/text>/);
    expect(match).not.toBeNull();
    expect(match![1]).toBe('ISLAND OF IDA');
  });
});

// ── Finding 7 (2026-07-28): the old colour test only checked that fills/
// strokes were SHAPED like var(--...) references, never that the token
// NAME they named was actually defined — a fabricated var(--...) passed
// silently. This reads the REAL global.css (same approach as
// plate-map-contrast.test.ts's extractBlock: parse the live stylesheet,
// not a hand-copied list) and asserts every var(--token) the renderer
// emits resolves against it.
const GLOBAL_CSS = readFileSync(path.resolve(process.cwd(), 'styles/global.css'), 'utf-8');
const DEFINED_CSS_TOKENS = new Set(
  [...GLOBAL_CSS.replace(/\/\*[\s\S]*?\*\//g, '').matchAll(/--([a-zA-Z0-9-]+)\s*:/g)].map((m) => m[1]),
);

function assertEveryVarTokenDefined(svg: string): void {
  const used = new Set([...svg.matchAll(/var\(--([a-zA-Z0-9-]+)\)/g)].map((m) => m[1]));
  expect(used.size).toBeGreaterThan(0);
  for (const token of used) {
    if (!DEFINED_CSS_TOKENS.has(token)) {
      expect.fail(`var(--${token}) is referenced in the emitted plate SVG but is not defined anywhere in shared/styles/global.css`);
    }
  }
}

describe('renderPlate: theming (no baked colour)', () => {
  const FORBIDDEN_KEYWORDS = ['red', 'blue', 'green', 'black', 'white', 'orange', 'purple', 'yellow', 'brown', 'grey', 'gray'];

  it('emits no hex/rgb()/hsl() colours and no bare colour keywords in fill/stroke', () => {
    const result = renderPlate(testPlate, [troy, scamander, ghost]);
    const hex = result.svg.match(/#[0-9a-fA-F]{3,8}/g);
    expect(hex).toBeNull();
    expect(result.svg).not.toMatch(/rgb\(/i);
    expect(result.svg).not.toMatch(/hsl\(/i);

    const attrMatches = [...result.svg.matchAll(/(fill|stroke)="([^"]*)"/g)];
    expect(attrMatches.length).toBeGreaterThan(0);
    for (const [, attr, value] of attrMatches) {
      const isVar = value.startsWith('var(--');
      const isNone = value === 'none';
      if (!isVar && !isNone) {
        expect.fail(`${attr}="${value}" is not a var(--...) reference (and not "none")`);
      }
      if (FORBIDDEN_KEYWORDS.includes(value.toLowerCase())) {
        expect.fail(`${attr}="${value}" is a bare colour keyword, not a CSS custom property`);
      }
    }
  });

  it('every var(--token) referenced in the emitted SVG is actually defined in global.css (finding 7)', () => {
    const result = renderPlate(testPlate, [troy, scamander, ghost]);
    assertEveryVarTokenDefined(result.svg);
  });
});

// The label halo is the only thing standing between a name and the
// hypsometric relief ramp it is lettered over: measured on rendered pixels
// (scripts/measure-label-contrast.mjs, 2026-08-13) the 0.65px halo left 17 of
// 28 region/feature labels below the 4.5:1 AA floor, MOUNT IDA at 2.36:1. See
// shared/lib/plate.ts's RELIEF_HALO_WIDTH for why no flat ink can substitute.
// These assertions pin the two halves of that fix: the geographic sheets get
// a halo wide enough to be a background, and the schematic sheets — whose
// flat token fills never had the problem — keep the hairline exactly.
describe('renderPlate: label halo', () => {
  const haloOf = (svg: string) =>
    [...svg.matchAll(/<text class="plate-label[^"]*"[^>]*>/g)].map((m) => ({
      width: m[0].match(/stroke-width="([\d.]+)"/)?.[1],
      opacity: m[0].match(/stroke-opacity="([\d.]+)"/)?.[1],
      stroke: m[0].match(/stroke="([^"]+)"/)?.[1],
    }));

  it('a geographic plate letters over relief, so every label carries the wide translucent halo', () => {
    const haloes = haloOf(renderPlate(testPlate, [troy, scamander]).svg);
    expect(haloes.length).toBeGreaterThan(0);
    for (const h of haloes) {
      expect(h.stroke).toBe('var(--scene-map-label-halo)');
      expect(Number(h.width)).toBeGreaterThanOrEqual(2.5);
      // Translucent, not a knockout: an opaque stroke this wide is the
      // "white halo" the 2026-08-10 lane retired, and it reads as its own
      // shape rather than as the terrain dimming around the letterforms.
      expect(Number(h.opacity)).toBeGreaterThan(0.5);
      expect(Number(h.opacity)).toBeLessThan(1);
    }
  });

  it('a schematic plate keeps the 0.65px opaque hairline, unchanged', () => {
    const haloes = haloOf(renderPlate(schematicPlate, [anchoredPlace]).svg);
    expect(haloes.length).toBeGreaterThan(0);
    for (const h of haloes) {
      expect(h.stroke).toBe('var(--scene-map-label-halo)');
      expect(h.width).toBe('0.65');
      expect(h.opacity).toBeUndefined();
    }
  });
});

describe('renderPlate: unlocated honesty', () => {
  it('a place with no coords is reported unlocated and never pinned', () => {
    const result = renderPlate(testPlate, [troy, ghost]);
    expect(result.unlocated.map((p) => p.id)).toEqual(['ghost-place']);
    expect(result.svg).not.toContain('data-place-id="ghost-place"');
    expect(result.svg).toContain('data-place-id="troy"');
  });
});

describe('renderPlate: offCanvas honesty (finding 1)', () => {
  // A defensible position that projects OUTSIDE this plate's own canvas is
  // not the same thing as "no defensible position at all." Before the fix,
  // both fell into `unlocated`, which is what actually dropped 18 Troad
  // places silently (they had real coords, just off the Trojan-plain
  // sheet) — neither drawn (the clip-path hid the pin) nor listed as
  // "named, not drawn."
  const farOff: PlatePlace = { id: 'far-off', name: 'Far Off Place', coords: [39.94, 30.0], certainty: 'certain' }; // lon 30 is far east of BBOX's maxLon 26.36

  it('a place with real coords outside the plate canvas is bucketed offCanvas, not unlocated, and never pinned', () => {
    const result = renderPlate(testPlate, [troy, farOff]);
    expect(result.offCanvas.map((p) => p.id)).toEqual(['far-off']);
    expect(result.unlocated).toEqual([]);
    expect(result.svg).not.toContain('data-place-id="far-off"');
    expect(result.svg).toContain('data-place-id="troy"');
    expect(result.features.find((f) => f.id === 'far-off')).toBeUndefined();
  });

  it('a place resolving to no position at all stays unlocated, distinct from offCanvas (the two buckets never merge)', () => {
    const result = renderPlate(testPlate, [ghost, farOff]);
    expect(result.unlocated.map((p) => p.id)).toEqual(['ghost-place']);
    expect(result.offCanvas.map((p) => p.id)).toEqual(['far-off']);
  });

  it('a projected point exactly on the canvas edge counts as located, not offCanvas (inclusive-bounds decision)', () => {
    // Same aspect-matching trick as the computeCamera "near-identity" test
    // below: bbox and size chosen so the cos-corrected bbox aspect exactly
    // matches the canvas aspect, so the bbox's own max corner projects to
    // EXACTLY (width, 0) — a genuine boundary case, not an approximation.
    const centerLat = 40;
    const cosLat = Math.cos((centerLat * Math.PI) / 180);
    const latSpan = 4;
    const width = 400;
    const height = 200;
    const lonSpan = ((width / height) * latSpan) / cosLat;
    const bbox: [number, number, number, number] = [
      centerLat - latSpan / 2,
      -lonSpan / 2,
      centerLat + latSpan / 2,
      lonSpan / 2,
    ];
    const edgePlate: Plate = { id: 'edge', title: 'Edge', kind: 'geographic', status: 'draft', bbox, size: [width, height], layers: [] };
    const edgePlace: PlatePlace = { id: 'edge-place', name: 'Edge Place', coords: [bbox[2], bbox[3]] }; // maxLat, maxLon -> (width, 0)

    const result = renderPlate(edgePlate, [edgePlace]);
    expect(result.offCanvas).toEqual([]);
    expect(result.unlocated).toEqual([]);
    expect(result.svg).toContain('data-place-id="edge-place"');
  });
});

describe('renderPlate: drawnByLayer honesty (Problem 2)', () => {
  // A place with no defensible pin position can still be visibly drawn via a
  // layer's own geometry (a wall trace, a region polygon) rather than a pin
  // — e.g. the Troy citadel plate's wall-circuit layers and summit region
  // all carry `placeId`s with no coords/plateAnchors of their own. Before
  // this fix, such a place fell into `unlocated` ("named, not drawn"), which
  // is false: the map plainly draws it, just not as a marker.
  const layerPlate: Plate = {
    id: 'layer-plate',
    title: 'Layer Plate',
    kind: 'geographic',
    status: 'draft',
    bbox: BBOX,
    size: SIZE,
    layers: [
      {
        id: 'wall-circuit',
        kind: 'wall',
        placeId: 'wall-of-troy',
        trace: [
          [39.95, 26.2],
          [39.96, 26.22],
        ],
      },
      {
        id: 'summit-region',
        kind: 'region',
        placeId: 'pergamos',
        polygon: [
          [39.91, 26.16],
          [39.93, 26.18],
          [39.91, 26.2],
        ],
      },
      {
        // A layer whose own geometry is empty never renders (renderLayer
        // returns undefined) — its placeId must NOT count as "drawn."
        id: 'empty-wall',
        kind: 'wall',
        placeId: 'wall-of-heracles',
        trace: [],
      },
    ],
  };
  const wallOfTroy: PlatePlace = { id: 'wall-of-troy', name: 'The wall of Troy', certainty: 'certain' }; // no coords
  const pergamos: PlatePlace = { id: 'pergamos', name: 'Pergamos', certainty: 'traditional' }; // no coords
  const wallOfHeracles: PlatePlace = { id: 'wall-of-heracles', name: 'Wall of Heracles', certainty: 'speculative' }; // no coords; its only layer never renders
  const trulyUnlocated: PlatePlace = { id: 'ghost-place', name: 'Unlocated Ghost', certainty: 'mythical' }; // no coords, no layer names it

  it('a place with no pin position but named as a rendered layer\'s placeId is bucketed drawnByLayer, not unlocated', () => {
    const result = renderPlate(layerPlate, [wallOfTroy, pergamos]);
    expect(result.drawnByLayer.map((p) => p.id).sort()).toEqual(['pergamos', 'wall-of-troy']);
    expect(result.unlocated).toEqual([]);
    // Never pinned: no data-place-id marker for either.
    expect(result.svg).not.toContain('data-place-id="wall-of-troy"');
    expect(result.svg).not.toContain('data-place-id="pergamos"');
    // But the layer itself is present in the drawn markup.
    expect(result.svg).toContain('data-feature-id="wall-circuit"');
    expect(result.svg).toContain('data-feature-id="summit-region"');
  });

  it('a placeId on a layer that fails to render (empty geometry) does not count as drawn', () => {
    const result = renderPlate(layerPlate, [wallOfHeracles]);
    expect(result.drawnByLayer).toEqual([]);
    expect(result.unlocated.map((p) => p.id)).toEqual(['wall-of-heracles']);
  });

  it('a place named by no layer at all stays unlocated, distinct from drawnByLayer', () => {
    const result = renderPlate(layerPlate, [trulyUnlocated, wallOfTroy]);
    expect(result.unlocated.map((p) => p.id)).toEqual(['ghost-place']);
    expect(result.drawnByLayer.map((p) => p.id)).toEqual(['wall-of-troy']);
  });

  it('a place WITH its own pin position is located, not drawnByLayer, even if a layer also names its id', () => {
    // troy has real coords in this bbox and is not named by any layer here,
    // but exercise the precedence explicitly: give wall-of-troy coords too.
    const pinnedWallOfTroy: PlatePlace = { ...wallOfTroy, coords: [39.957, 26.239] };
    const result = renderPlate(layerPlate, [pinnedWallOfTroy]);
    expect(result.drawnByLayer).toEqual([]);
    expect(result.unlocated).toEqual([]);
    expect(result.svg).toContain('data-place-id="wall-of-troy"');
  });
});

describe('renderPlate: registration invariant', () => {
  it('a located place projects to the same pixel as geo.ts project() against the plate viewport', () => {
    const result = renderPlate(testPlate, [troy, scamander]);
    const viewport = viewportFromBBox(testPlate.bbox!, testPlate.size);

    for (const place of [troy, scamander]) {
      const [expectedX, expectedY] = project(place.coords!, viewport);
      const feature = result.features.find((f) => f.id === place.id);
      expect(feature).toBeDefined();
      const [minX, minY, maxX, maxY] = feature!.bbox;
      const actualX = (minX + maxX) / 2;
      // testPlate is geographic, so a located place draws as a DOT (2026-08-
      // 10), whose box is centred on the coordinate — unlike the teardrop
      // pin it replaced there, a dot has no tip to anchor a bbox edge to.
      const actualY = (minY + maxY) / 2;
      expect(actualX).toBeCloseTo(expectedX, 6);
      expect(actualY).toBeCloseTo(expectedY, 6);
    }
    expect(result.viewport).toEqual(viewport);
  });
});

describe('renderPlate: XSS', () => {
  it('escapes a place name containing XML-sensitive characters', () => {
    const hostile: PlatePlace = { id: 'hostile', name: 'Odysseus\'s <script>alert(1)</script> "Men"', coords: [39.957, 26.239] };
    const result = renderPlate(testPlate, [hostile]);
    expect(result.svg).not.toContain('<script>');
    expect(result.svg).toContain('&lt;script&gt;');
    expect(result.svg).toContain('&quot;Men&quot;');
  });

  // Finding 8 (2026-07-28): idPrefix is caller-supplied and lands directly
  // in an SVG element id (the clipPath id) — an id attribute has no
  // attribute-VALUE quoting to escape into, so a hostile prefix used to
  // produce literal markup, not just an escaped-but-inert string. Mirrors
  // shield.ts's own safeIdFragment sanitizer.
  it('sanitizes a hostile idPrefix instead of interpolating it raw into the SVG', () => {
    const result = renderPlate(testPlate, [], { idPrefix: '"><script>alert(1)</script>' });
    expect(result.svg).not.toContain('<script>');
    expect(result.svg).not.toContain('</script>');
    expect(result.svg).toMatch(/clipPath id="[a-zA-Z0-9_-]+-clip"/);
  });

  it('falls back to a safe default id when idPrefix is empty', () => {
    const result = renderPlate(testPlate, [], { idPrefix: '' });
    expect(result.svg).toContain('clipPath id="plate-clip"');
  });

  // Finding F2 (stage 6 review, 2026-09-03): placeLabelClass looked up
  // place.id/place.kind — plain strings off apparatus data — on ordinary
  // object literals, so a value matching a real Object.prototype member name
  // resolved to the inherited function instead of `undefined`, and
  // LABEL_STYLES[role] then threw on a role that was never a LabelRole at
  // all. Mirrors the already-fixed labelBoxes trap (renderPlate's own
  // Object.create(null) comment).
  it.each(['constructor', 'toString', 'valueOf', 'hasOwnProperty', '__proto__'] as const)(
    'a place with kind "%s" does not crash renderPlate and falls back to the settlement label class',
    (kind) => {
      const hostile: PlatePlace = { id: 'hostile-kind', name: 'Hostile Kind', coords: [39.957, 26.239], kind };
      let svg = '';
      expect(() => {
        svg = renderPlate(testPlate, [hostile]).svg;
      }).not.toThrow();
      expect(svg).toContain('plate-label-settlement');
    },
  );

  it.each(['constructor', 'toString', 'valueOf', 'hasOwnProperty', '__proto__'] as const)(
    'a place with id "%s" does not crash renderPlate (geographic plate)',
    (id) => {
      const hostile: PlatePlace = { id, name: 'Hostile Id', coords: [39.957, 26.239] };
      expect(() => renderPlate(testPlate, [hostile])).not.toThrow();
    },
  );

  it('a schematic-plate place with kind "constructor" does not crash renderPlate', () => {
    const hostile: PlatePlace = {
      id: 'hostile-schematic',
      name: 'Hostile',
      kind: 'constructor',
      plateAnchors: { shield: [0.5, 0.5] },
      positionBasis: 'conjectural',
    };
    let svg = '';
    expect(() => {
      svg = renderPlate(schematicPlate, [hostile]).svg;
    }).not.toThrow();
    expect(svg).toContain('plate-label-settlement');
  });
});

describe('renderPlate: schematic plateAnchors / positionBasis honesty', () => {
  it('places a valid anchored+conjectural place at the anchored unit position, and keeps the honesty attribute on it', () => {
    const result = renderPlate(schematicPlate, [anchoredPlace]);
    expect(result.unlocated).toEqual([]);
    const feature = result.features.find((f) => f.id === 'anchored-place');
    expect(feature).toBeDefined();
    const [minX, minY, maxX, maxY] = feature!.bbox;
    // The mark is CENTRED on its coordinate, not hung by a tip below it: the
    // teardrop is gone (2026-08-13) and a dot means "this point", so its box
    // is symmetric about the anchor. u=0.25, v=0.75 scaled directly by
    // plate.size [200,200] (schematic projection, per projectPoint).
    expect((minX + maxX) / 2).toBeCloseTo(0.25 * 200, 6);
    expect((minY + maxY) / 2).toBeCloseTo(0.75 * 200, 6);

    // The claim survives the symbology change: a data attribute a component
    // can key off is still stamped on every schematic mark.
    expect(result.svg).toContain('data-position-basis="conjectural"');
    const gMatch = result.svg.match(/<g[^>]*data-place-id="anchored-place"[^>]*>[\s\S]*?<\/g>/);
    expect(gMatch).not.toBeNull();
    expect(gMatch![0]).toContain('data-position-basis="conjectural"');
  });

  it('does NOT repeat the conjectural claim on every mark, because on a schematic plate it is true of every mark', () => {
    // resolvePlacePosition has exactly ONE path to a position on a schematic
    // plate — plateAnchors + positionBasis: "conjectural" — so a per-mark
    // dash distinguished nothing from nothing, and a dashed leader per name
    // drew the same sheet-wide fact thirty times. `anchoredPlace` is
    // `certain`, whose tier register is a plain solid disc: no dasharray of
    // any kind should reach it, and no leader should be drawn for it.
    const svg = renderPlate(schematicPlate, [anchoredPlace]).svg;
    const g = svg.match(/<g[^>]*data-place-id="anchored-place"[^>]*>[\s\S]*?<\/g>/)![0];
    expect(g).not.toContain('stroke-dasharray');
    expect(svg).not.toContain('class="plate-leader"');
  });

  it('does NOT honour plateAnchors without positionBasis: "conjectural" (invalid pairing per apparatus_places.py)', () => {
    const result = renderPlate(schematicPlate, [anchorWithoutBasis]);
    expect(result.unlocated.map((p) => p.id)).toEqual(['anchor-no-basis']);
    expect(result.svg).not.toContain('data-place-id="anchor-no-basis"');
  });

  it('ignores a plateAnchors entry keyed for a different plate id', () => {
    const result = renderPlate(schematicPlate, [anchorForOtherPlate]);
    expect(result.unlocated.map((p) => p.id)).toEqual(['anchor-other-plate']);
    expect(result.svg).not.toContain('data-place-id="anchor-other-plate"');
  });
});

describe('renderPlate: general smoke', () => {
  it('produces a valid non-degenerate SVG with a data-feature-id per drawn layer', () => {
    const result = renderPlate(testPlate, [troy]);
    expect(result.svg).toContain('<svg');
    expect(result.svg).toContain('viewBox="0 0 400 300"');
    for (const layer of testPlate.layers) {
      expect(result.svg).toContain(`data-feature-id="${layer.id}"`);
    }
  });

  it('skips a layer whose required geometry is absent, without throwing', () => {
    const sparse: Plate = { ...testPlate, layers: [{ id: 'empty-river', kind: 'river' }] };
    expect(() => renderPlate(sparse, [])).not.toThrow();
    const result = renderPlate(sparse, []);
    expect(result.features).toEqual([]);
  });
});

// ── data-layer-id: the toggle relationship, stated, not inferred (2026-07-29) ──
// PlatePanel's layer toggle used to match `data-feature-id` exactly, which
// missed the auxiliary elements several registers draw for one logical layer
// (a coast's `-body`, its reconstructed shore's `-band`, a barrier's
// `-waterline-N`) -- switching a layer off left its auxiliaries lit on the
// sheet. The tempting fix, a `startsWith(layer.id)` prefix match, is a worse
// bug: real plates' layer ids collide by prefix ("relief-ida" prefixes
// "relief-ida-north-spurs"/"relief-ida-800"/"relief-ida-1200" on troad.json;
// "lower-city" prefixes "lower-city-ditch" on troy-citadel.json), and a
// prefix match would hide those unrelated sibling layers too. renderLayer
// now stamps every element it draws -- auxiliaries included -- with a second,
// unsuffixed `data-layer-id` attribute (see its own comment), so a consumer
// states the relationship instead of inferring it from string shape.
describe('renderLayer: data-layer-id names the layer that drew each element, auxiliaries included', () => {
  it('every data-feature-id in a rendered plate also carries data-layer-id, equal to the layer\'s own (unsuffixed) id', () => {
    const result = renderPlate(testPlate, [troy]);
    for (const layer of testPlate.layers) {
      const m = result.svg.match(new RegExp(`data-feature-id="${layer.id}"[^>]*data-layer-id="([^"]*)"`));
      expect(m, `layer "${layer.id}" has no matching data-layer-id`).not.toBeNull();
      expect(m![1]).toBe(layer.id);
    }
  });

  it('an auxiliary element (a suffixed feature id) carries the PARENT layer id, not its own suffixed id (real trojan-plain.json: shore-bronze / shore-bronze-band)', () => {
    const raw = JSON.parse(readFileSync(SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    const svg = renderPlate(plate, []).svg;
    const baseMatch = svg.match(/data-feature-id="shore-bronze"[^>]*data-layer-id="([^"]*)"/);
    const bandMatch = svg.match(/data-feature-id="shore-bronze-band"[^>]*data-layer-id="([^"]*)"/);
    expect(baseMatch![1]).toBe('shore-bronze');
    expect(bandMatch![1]).toBe('shore-bronze');
  });

  it('does not let a prefix collision leak: relief-ida-800 / -1200 / -north-spurs each carry their OWN data-layer-id, never "relief-ida" (real troad.json)', () => {
    const plate = parsePlate(
      JSON.parse(readFileSync(path.resolve(process.cwd(), '../apparatus/plates/troad.json'), 'utf-8')),
    );
    const svg = renderPlate(plate, []).svg;
    for (const id of ['relief-ida-800', 'relief-ida-1200', 'relief-ida-north-spurs']) {
      const m = svg.match(new RegExp(`data-feature-id="${id}"[^>]*data-layer-id="([^"]*)"`));
      expect(m![1]).toBe(id);
    }
    const ida = svg.match(/data-feature-id="relief-ida"[^>]*data-layer-id="([^"]*)"/);
    expect(ida![1]).toBe('relief-ida');
  });

  it('same collision, the citadel sheet: circuit-southeast-east carries its own data-layer-id, never "circuit-south" (real troy-citadel.json)', () => {
    // The citadel sheet's colliding pair changed with the 2026-07-30 rebuild
    // (the lower-city / lower-city-ditch layers went with Korfmann's
    // reconstruction, which the Troy VI plate does not carry). The wall
    // segments supply the same shape of collision: "circuit-south" is a
    // prefix of "circuit-southeast-east".
    const plate = parsePlate(
      JSON.parse(readFileSync(path.resolve(process.cwd(), '../apparatus/plates/troy-citadel.json'), 'utf-8')),
    );
    const svg = renderPlate(plate, []).svg;
    const east = svg.match(/data-feature-id="circuit-southeast-east"[^>]*data-layer-id="([^"]*)"/);
    const south = svg.match(/data-feature-id="circuit-south"[^>]*data-layer-id="([^"]*)"/);
    expect(east![1]).toBe('circuit-southeast-east');
    expect(south![1]).toBe('circuit-south');
  });
});

describe('renderPlate: schematic plates (gap 1)', () => {
  it('renders the live trojan-plain-schematic.json into a map frame inset by the right margin', () => {
    const raw = JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    const result = renderPlate(plate, []);
    expect(result.svg).toContain(`viewBox="0 0 ${plate.size[0]} ${plate.size[1]}"`);
    expect(result.viewport.width).toBe(plate.size[0] - (plate.marginRight ?? 0));
    expect(result.viewport.height).toBe(plate.size[1]);
    expect(plate.rotationDeg).toBe(90);
  });

  it('renders the live shield-of-achilles.json (bands only, no layers, no bbox) without throwing', () => {
    const raw = JSON.parse(readFileSync(SHIELD_SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    expect(() => renderPlate(plate, [])).not.toThrow();
    const result = renderPlate(plate, []);
    expect(result.svg).toContain('<svg');
    // No `layers` on this plate — renderShield (shield.ts) draws the bands
    // themselves; renderPlate's job here is only to not throw on a
    // bbox-less, layer-less schematic plate.
    expect(result.features).toEqual([]);
  });

  it('a schematic layer point projects to [size[0]*u, size[1]*v] — a real unit-space viewport, not an invented bbox', () => {
    const plate: Plate = {
      id: 'unit-test',
      title: 'Unit Test',
      kind: 'schematic',
      status: 'draft',
      size: [500, 300],
      layers: [{ id: 'diag', kind: 'route', path: [[0, 0], [1, 1]] }],
    };
    const result = renderPlate(plate, []);
    const feature = result.features.find((f) => f.id === 'diag')!;
    expect(feature.bbox).toEqual([0, 0, 500, 300]);
  });

  // PlateResult.frame (stage 5a, 2026-09-02): the MAP frame's own size,
  // `[size[0] - marginRight, size[1]]`, as opposed to `plate.size` (the
  // whole sheet, margin band included). A caller sizing a postcard's
  // aspect-ratio box off `plate.size` on this sheet reserves a slot ~30%
  // wider than the map itself and shows blank band down the right edge —
  // this is what it should read instead.
  it('exposes `frame` — the map frame\'s own size, inset by marginRight — on the live schematic plate', () => {
    const raw = JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    const result = renderPlate(plate, []);
    expect(plate.marginRight).toBeGreaterThan(0);
    expect(result.frame).toEqual([plate.size[0] - plate.marginRight!, plate.size[1]]);
    expect(result.frame).toEqual([result.viewport.width, result.viewport.height]);
  });

  it('`frame` equals `plate.size` on a plate with no marginRight (every geographic plate today)', () => {
    const result = renderPlate(testPlate, []);
    expect(testPlate.marginRight).toBeUndefined();
    expect(result.frame).toEqual(testPlate.size);
  });
});

// A label on open water asserts a place IN THE SEA, which is false on a
// schematic register (John, 2026-08-15, d0c4e947d "known, not fixed"): the
// beach corridor (see lineworkReserveHalfWidth) reserves only a band along
// the shoreline, not the open water beyond it, so the solver's cost
// function (placeLabelCandidates) sees the sea as free space — cheaper than
// any candidate that so much as grazes the shore corridor or a neighbouring
// label. The `mound-of-patroclus` layer's name ("Patroclus: pyre, barrow,
// games") is the label that regression actually hit, because the camp band
// at the Achilles end is full (see e966484dd) and its own anchor sits right
// at the shoreline.
describe('renderPlate: a label never seats on open water (d0c4e947d regression)', () => {
  // Ray-casting point-in-polygon, even-odd rule — mirrors plate.ts's own
  // private `pointInPolygon` (not exported), used here only to test against
  // the sheet's own sea geometry rather than a hardcoded y.
  function pointInPolygon(pt: [number, number], polygon: [number, number][]): boolean {
    const [px, py] = pt;
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const [xi, yi] = polygon[i];
      const [xj, yj] = polygon[j];
      const crosses = yi > py !== yj > py && px < ((xj - xi) * (py - yi)) / (yj - yi) + xi;
      if (crosses) inside = !inside;
    }
    return inside;
  }

  // Nine samples (corners, edge midpoints, centre) rather than a single
  // point: a box that only PARTLY overlaps the sea is still a false claim.
  // The sea's boundary here is a shallow wave-like curve (see the `sea`
  // layer's own polygon), not a hard edge close to any sampled point, so
  // this is not a coin-flip near a boundary — a genuine overlap lands at
  // least one sample inside.
  function boxTouchesPolygon(box: [number, number, number, number], polygon: [number, number][]): boolean {
    const [x1, y1, x2, y2] = box;
    const xs = [x1, (x1 + x2) / 2, x2];
    const ys = [y1, (y1 + y2) / 2, y2];
    for (const x of xs) for (const y of ys) if (pointInPolygon([x, y], polygon)) return true;
    return false;
  }

  it('the Patroclus label (pyre, barrow, games) does not sit on the sea layer\'s own polygon', () => {
    const raw = JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    const allPlaces = (JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[]).filter(
      (p) => (p as unknown as { maps?: string[] }).maps?.includes('troad-plain'),
    );
    const result = renderPlate(plate, allPlaces);

    const seaLayer = plate.layers.find((l) => l.id === 'sea-modern')!;
    expect(seaLayer.polygon).toBeDefined();
    const seaPolygon: [number, number][] = seaLayer.polygon!.map((p) => project(p as [number, number], result.viewport));

    const mound = plate.layers.find((l) => l.id === 'mound-of-patroclus')!;
    const moundPx = project(mound.path![0] as [number, number], result.viewport);
    expect(pointInPolygon(moundPx, seaPolygon), 'the mound itself must sit on land').toBe(false);

    // Stage 5c: Patroclus is keyed (item 4), so the face mark is a numeral
    // badge, not the old name. The regression was a mark sent out onto the
    // open Hellespont — the badge must stay near its own mound.
    const badge = [...result.svg.matchAll(/<g class="plate-key-badge"[^>]*>[\s\S]*?<\/g>/g)]
      .map((m) => m[0])
      .find((g) => g.includes('data-layer-id="mound-of-patroclus"'));
    expect(badge, 'mound-of-patroclus must have a keyed badge').toBeDefined();
    const circle = badge!.match(/<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([-\d.]+)"/);
    const cx = Number(circle?.[1]);
    const cy = Number(circle?.[2]);
    expect(Math.hypot(cx - moundPx[0], cy - moundPx[1])).toBeLessThan(150);
  });
});

describe('renderPlate: the no-label-on-water rule binds the schematic register only (John, ruling 2e-iv/5, 2026-09-02)', () => {
  // The open-water label reservation above exists to stop a schematic label
  // from asserting a place IN THE SEA (see the d0c4e947d comment on the
  // Patroclus test). A GEOGRAPHIC sheet is a different register: it already
  // draws coastal names over water with a leader line (Sigeion, on this same
  // sheet), so reserving open water against the solver there was never the
  // right rule — it was a schematic-register fix applied plate-wide.
  //
  // Superseded here: an earlier version of this test asserted besik-sivritepe
  // and uvecik-tepe placed while kesik-tepe and kum-tepe were HONESTLY
  // suppressed, because their best candidate positions genuinely fell inside
  // the sea/lagoon polygon — true under the old plate-wide rule, where any
  // water overlap was a defect. Once the rule is scoped to schematic plates
  // only, that same overlap is no longer a defect on a geographic sheet: a
  // coastal name sitting over open water, with a leader to its point, is
  // exactly what this register draws (John's ruling 5: "Kum Tepe, Kesik Tepe
  // come back"). So all four now regain a labelBox on the real
  // trojan-plain.json — the SET of placed ids is the gate here, per the
  // 2026-09-02 CLAUDE.md lesson that a positions-only diff cannot see a
  // dropped (or regained) label.
  it('regains kum-tepe and kesik-tepe on the geographic trojan-plain sheet, alongside besik-sivritepe and uvecik-tepe', () => {
    const raw = JSON.parse(readFileSync(SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    expect(plate.kind).toBe('geographic');
    const allPlaces = (JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[]).filter(
      (p) => (p as unknown as { maps?: string[] }).maps?.includes('troad-plain'),
    );
    const result = renderPlate(plate, allPlaces);

    for (const id of ['besik-sivritepe', 'uvecik-tepe', 'kum-tepe', 'kesik-tepe']) {
      expect(result.labelBoxes[id], `expected a labelBox for "${id}"`).toBeDefined();
    }
  });
});

// ── Geographic sheet geo-enrich labels (2026-09-02) ────────────────────────
// John's ruling: add Beşik Bay, Thymbrios, Pınarbaşı, Ajax's tomb, the Kesik
// cut, and the Aegean to the geographic Trojan Plain sheet. The gate is the
// SET of placed ids (CLAUDE.md 2026-09-02: a positions-only diff cannot see
// a dropped label). The 14 ids already on the sheet must all still place.

const TROJAN_PLAIN_PREEXISTING_LABEL_IDS = [
  'achaean-camp-zone',
  'besik-sivritepe',
  'callicolone',
  'kesik-tepe',
  'kum-tepe',
  'lagoon-bronze',
  'rhoiteion',
  'scamander',
  'scamandrian-plain',
  'sigeion',
  'simoeis',
  'thymbra',
  'troy',
  'uvecik-tepe',
] as const;

const TROJAN_PLAIN_GEO_ENRICH_LABEL_IDS = [
  'besik-bay',
  'pinarbasi',
  'tomb-of-ajax-in-tepe',
  'kesik-basin',
  'thymbrios',
  'aegean',
] as const;

describe('renderPlate: geographic trojan-plain geo-enrich labels (2026-09-02)', () => {
  it('places the new labels and keeps every pre-existing label id', () => {
    const raw = JSON.parse(readFileSync(SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    expect(plate.kind).toBe('geographic');
    const allPlaces = (JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[]).filter(
      (p) => (p as unknown as { maps?: string[] }).maps?.includes('troad-plain'),
    );
    const result = renderPlate(plate, allPlaces);

    for (const id of TROJAN_PLAIN_PREEXISTING_LABEL_IDS) {
      expect(result.labelBoxes[id], `pre-existing label "${id}" must still be placed`).toBeDefined();
    }
    for (const id of TROJAN_PLAIN_GEO_ENRICH_LABEL_IDS) {
      expect(result.labelBoxes[id], `expected a labelBox for "${id}"`).toBeDefined();
    }
  });

  // Both `achaean-camp-zone` and `kesik-basin` are `centred` region requests
  // — laid at their own polygon's bounding-box centre with NO collision check
  // against each other (layoutLabels's own comment: "Area (`centred`) names
  // are laid first... a point name yields to them"). The first cut of the
  // kesik-basin polygon landed its centroid on top of achaean-camp-zone's,
  // and the two labels printed through each other. The fix moved the zone
  // further south; this pins the two boxes disjoint so a future edit to
  // either polygon that reintroduces the collision fails loudly.
  it('the Kesik cut lettering zone does not overprint the Achaean camp label', () => {
    const raw = JSON.parse(readFileSync(SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    const allPlaces = (JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[]).filter(
      (p) => (p as unknown as { maps?: string[] }).maps?.includes('troad-plain'),
    );
    const result = renderPlate(plate, allPlaces);
    const camp = result.labelBoxes['achaean-camp-zone'];
    const kesik = result.labelBoxes['kesik-basin'];
    expect(camp, 'achaean-camp-zone must place').toBeDefined();
    expect(kesik, 'kesik-basin must place').toBeDefined();
    const disjoint = camp[2] < kesik[0] || kesik[2] < camp[0] || camp[3] < kesik[1] || kesik[3] < camp[1];
    expect(disjoint, `camp box ${JSON.stringify(camp)} and kesik box ${JSON.stringify(kesik)} must not overlap`).toBe(
      true,
    );
  });

  // tomb-of-ajax-in-tepe's `coords` are deliberately Rhoiteion's own point
  // (its note: "This is Rhoiteion's coordinate, not a survey of the mound").
  // Drawing both places' dots put two discs on one pixel, the second
  // (open, traditional-tier) entirely hidden under Rhoiteion's solid one —
  // present in the DOM, invisible on the sheet. It still gets its own label.
  it('tomb-of-ajax-in-tepe prints its label but draws no marker of its own', () => {
    const raw = JSON.parse(readFileSync(SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    const allPlaces = (JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[]).filter(
      (p) => (p as unknown as { maps?: string[] }).maps?.includes('troad-plain'),
    );
    const result = renderPlate(plate, allPlaces);
    expect(result.labelBoxes['tomb-of-ajax-in-tepe'], 'tomb-of-ajax-in-tepe must still print a label').toBeDefined();
    const ownMarker = result.features.find((f) => f.id === 'tomb-of-ajax-in-tepe' && f.type === 'place');
    expect(ownMarker, 'tomb-of-ajax-in-tepe must not draw its own marker over Rhoiteion\'s').toBeUndefined();
    const rhoiteionMarker = result.features.find((f) => f.id === 'rhoiteion' && f.type === 'place');
    expect(rhoiteionMarker, 'rhoiteion must keep its own marker').toBeDefined();
  });
});

describe('renderPlate: tumulus layer kind (gap 2)', () => {
  it('a tumulus layer emits the dome glyph, stroked in ink, not filled', () => {
    const plate: Plate = {
      ...testPlate,
      layers: [{ id: 'tomb-of-ilos', kind: 'tumulus', path: [[39.93, 26.2]] }],
    };
    const result = renderPlate(plate, []);
    expect(result.svg).toContain('data-feature-id="tomb-of-ilos"');
    expect(result.svg).toContain('plate-layer-tumulus');
    // A leading space in ` d="` (not bare `d="`) matters now that renderLayer
    // also stamps a `data-layer-id` attribute at the end of the tag
    // (2026-07-29): "data-layer-id" itself contains the bare substring
    // `d="` (inside "...layer-id=\""), which a spaceless pattern's greedy
    // backtracking would latch onto instead of the real `d` attribute.
    const match = result.svg.match(/<path data-feature-id="tomb-of-ilos"[^>]*? d="([^"]*)"[^>]*\/>/);
    expect(match).not.toBeNull();
    expect(match![0]).toContain('fill="none"');
    expect(match![0]).toContain('stroke="var(--flaxman-ink)"');
    // dome + two nested shading arcs + base line = 4 subpaths, per tumulus()'s own contract.
    expect(match![1].split('M').length - 1).toBe(4);
  });

  it('draws one glyph per point when a tumulus layer carries multiple points', () => {
    const plate: Plate = {
      ...testPlate,
      layers: [{ id: 'two-mounds', kind: 'tumulus', path: [[39.9, 26.15], [39.95, 26.3]] }],
    };
    const result = renderPlate(plate, []);
    // See the sibling test above for why the space in ` d="` matters here.
    const match = result.svg.match(/<path data-feature-id="two-mounds"[^>]*? d="([^"]*)"[^>]*\/>/);
    expect(match![1].split('M').length - 1).toBe(8); // 2 points * 4 subpaths each
  });
});

describe('renderPlate: region fill role (gap 3)', () => {
  // CHANGED 2026-07-28 (the "it's just shapes, no geography" defect): the
  // default used to be `tint`, which resolves to var(--accent-light) — the
  // site's wine wayfinding accent — so every undeclared landform on the
  // geographic plate was painted in the UI highlight colour and the whole
  // sheet read pink. A landform is not a highlight: the default is now the
  // terrain token, and the accent wash is opt-in (see the next test).
  it('a region layer with no fill declared defaults to the terrain token, NOT the UI accent', () => {
    const result = renderPlate(testPlate, []); // camp-1 is a plain region layer, no fill declared
    const match = result.svg.match(/<path data-feature-id="camp-1"[^>]*\/>/);
    expect(match![0]).toContain('fill="var(--plate-plain)"');
    expect(match![0]).not.toContain('var(--plate-tint)');
    expect(match![0]).not.toContain('var(--accent');
  });

  it('a region layer with fill: "tint" still opts in to --plate-tint, translucent', () => {
    const campPolygon = testPlate.layers.find((l) => l.id === 'camp-1')!.polygon;
    const zone: PlateLayer = { id: 'zone-1', kind: 'region', fill: 'tint', polygon: campPolygon };
    const result = renderPlate({ ...testPlate, layers: [zone] }, []);
    const match = result.svg.match(/<path data-feature-id="zone-1"[^>]*\/>/);
    expect(match![0]).toContain('fill="var(--plate-tint)"');
    expect(match![0]).toContain('fill-opacity="0.35"');
  });

  it.each(['lagoon', 'marsh', 'plain', 'land'] as const)(
    'the terrain fill role "%s" resolves to its own token and is opaque',
    (role) => {
      const campPolygon = testPlate.layers.find((l) => l.id === 'camp-1')!.polygon;
      const layer: PlateLayer = { id: `t-${role}`, kind: 'region', fill: role, polygon: campPolygon };
      const result = renderPlate({ ...testPlate, layers: [layer] }, []);
      const match = result.svg.match(new RegExp(`<path data-feature-id="t-${role}"[^>]*/>`));
      expect(match).not.toBeNull();
      expect(match![0]).not.toContain('var(--plate-tint)');
      expect(match![0]).toMatch(/fill="var\(--(plate-lagoon|plate-marsh|plate-plain|scene-map-land)\)"/);
    },
  );

  it('a region layer with fill: "sea" uses --scene-map-sea, not --plate-tint', () => {
    const campPolygon = testPlate.layers.find((l) => l.id === 'camp-1')!.polygon;
    const seaLayer: PlateLayer = { id: 'sea-1', kind: 'region', fill: 'sea', polygon: campPolygon };
    const plate: Plate = { ...testPlate, layers: [seaLayer] };
    const result = renderPlate(plate, []);
    const match = result.svg.match(/<path data-feature-id="sea-1"[^>]*\/>/);
    expect(match![0]).toContain('fill="var(--scene-map-sea)"');
    expect(match![0]).not.toContain('var(--plate-tint)');
  });

  it('rejects an unknown fill role at parse time (arbitrary CSS cannot pass through from data)', () => {
    const bad = {
      id: 'x',
      title: 'X',
      kind: 'geographic',
      status: 'draft',
      bbox: BBOX,
      size: SIZE,
      layers: [{ id: 'hostile', kind: 'region', fill: 'red', polygon: [[39.9, 26.15], [39.92, 26.3], [39.88, 26.3]] }],
    };
    expect(() => parsePlate(bad)).toThrow(/unknown fill/);
  });

  // Finding F1 (stage 6 review, 2026-09-03): the whitelist check used
  // `l.fill in REGION_FILL_TOKENS`, and `in` also matches inherited
  // Object.prototype members. "constructor" (a real property of every plain
  // object) used to pass this "whitelist" clean, and renderLayer's
  // REGION_FILL_TOKENS[fill] then read the native Function constructor off
  // the prototype instead of a CSS token string — a hostile fill must be
  // rejected at parse the same as any other unknown one.
  it.each(['constructor', 'toString', 'valueOf', 'hasOwnProperty', '__proto__'] as const)(
    'rejects fill: "%s" as an unknown fill, not an inherited Object.prototype member',
    (fill) => {
      const bad = {
        id: 'x',
        title: 'X',
        kind: 'geographic',
        status: 'draft',
        bbox: BBOX,
        size: SIZE,
        layers: [{ id: 'hostile', kind: 'region', fill, polygon: [[39.9, 26.15], [39.92, 26.3], [39.88, 26.3]] }],
      };
      expect(() => parsePlate(bad)).toThrow(/unknown fill/);
    },
  );
});

describe('computeCamera', () => {
  it('framing all ids is (near-)identity when the geometry already fills the canvas', () => {
    // bbox/size chosen (per geo.test.ts's trick) so the cos-corrected bbox
    // aspect matches the canvas aspect: the projected bbox corners land
    // exactly on the canvas corners.
    const centerLat = 40;
    const cosLat = Math.cos((centerLat * Math.PI) / 180);
    const latSpan = 4;
    const width = 400;
    const height = 200;
    const lonSpan = ((width / height) * latSpan) / cosLat;
    const bbox: [number, number, number, number] = [
      centerLat - latSpan / 2,
      -lonSpan / 2,
      centerLat + latSpan / 2,
      lonSpan / 2,
    ];
    const fullPlate: Plate = {
      id: 'full',
      title: 'Full',
      kind: 'geographic',
      status: 'draft',
      bbox,
      size: [width, height],
      layers: [
        {
          id: 'corners',
          kind: 'route',
          path: [
            [bbox[2], bbox[1]], // top-left corner
            [bbox[0], bbox[3]], // bottom-right corner
          ],
        },
      ],
    };
    const viewport = viewportFromBBox(bbox, [width, height]);
    const camera = computeCamera(fullPlate, viewport, ['corners'], { padFraction: 0 });
    expect(camera.scale).toBeCloseTo(1, 6);
    expect(camera.tx).toBeCloseTo(0, 6);
    expect(camera.ty).toBeCloseTo(0, 6);
  });

  it('framing a subset of ids yields a camera whose transform maps those features inside the canvas', () => {
    const viewport = viewportFromBBox(testPlate.bbox!, testPlate.size);
    const camera = computeCamera(testPlate, viewport, ['river-1']);

    const layer = testPlate.layers.find((l) => l.id === 'river-1')!;
    for (const [lat, lon] of layer.path!) {
      const [x, y] = project([lat, lon], viewport);
      const outX = x * camera.scale + camera.tx;
      const outY = y * camera.scale + camera.ty;
      expect(outX).toBeGreaterThanOrEqual(-1e-6);
      expect(outX).toBeLessThanOrEqual(testPlate.size[0] + 1e-6);
      expect(outY).toBeGreaterThanOrEqual(-1e-6);
      expect(outY).toBeLessThanOrEqual(testPlate.size[1] + 1e-6);
    }
  });

  it('falls back to an identity camera when no layer matches focusIds', () => {
    const viewport = viewportFromBBox(testPlate.bbox!, testPlate.size);
    const camera = computeCamera(testPlate, viewport, ['does-not-exist']);
    expect(camera).toEqual({ scale: 1, tx: 0, ty: 0 });
  });

  it('frames a gazetteer place (not a layer) supplied via options.places', () => {
    const viewport = viewportFromBBox(testPlate.bbox!, testPlate.size);
    const camera = computeCamera(testPlate, viewport, ['troy', 'scamander-mouth'], {
      places: [troy, scamander],
    });

    for (const place of [troy, scamander]) {
      const [x, y] = project(place.coords!, viewport);
      const outX = x * camera.scale + camera.tx;
      const outY = y * camera.scale + camera.ty;
      expect(outX).toBeGreaterThanOrEqual(-1e-6);
      expect(outX).toBeLessThanOrEqual(testPlate.size[0] + 1e-6);
      expect(outY).toBeGreaterThanOrEqual(-1e-6);
      expect(outY).toBeLessThanOrEqual(testPlate.size[1] + 1e-6);
    }
  });

  it('mixes a layer id and a place id in the same focus set', () => {
    const viewport = viewportFromBBox(testPlate.bbox!, testPlate.size);
    const camera = computeCamera(testPlate, viewport, ['river-1', 'troy'], { places: [troy] });
    expect(Number.isFinite(camera.scale)).toBe(true);
    expect(camera.scale).toBeGreaterThan(0);
  });

  it('an id matching neither a layer nor a supplied place contributes nothing (falls back to identity), without throwing', () => {
    const viewport = viewportFromBBox(testPlate.bbox!, testPlate.size);
    expect(() => computeCamera(testPlate, viewport, ['nonexistent-place'], { places: [troy] })).not.toThrow();
    const camera = computeCamera(testPlate, viewport, ['nonexistent-place'], { places: [troy] });
    expect(camera).toEqual({ scale: 1, tx: 0, ty: 0 });
  });

  // Codex finding (2026-09-02): a focus id equal to a real Object property
  // name is apparatus-adjacent data reachable through a user-facing query
  // string (MapsPage's `?focus=` sanitizes to an id charset -- letters,
  // digits, hyphens -- which "constructor" and "__proto__" both pass). A
  // plain `{}` labelBoxes dictionary resolves `labelBoxes['constructor']` to
  // Object.prototype.constructor (a function, not undefined) instead of
  // "no entry" -- truthy, so the old `if (!box) continue` guard let it
  // through, and destructuring a function as `[x1,y1,x2,y2]` threw. Fixed at
  // the source (renderPlate's own labelBoxes, and CameraOptions' default) by
  // building that dictionary with Object.create(null), which has no
  // inherited properties to collide with.
  it('an id equal to a real Object/Array property name contributes nothing, without throwing (reachable via /maps/?focus=constructor)', () => {
    const viewport = viewportFromBBox(testPlate.bbox!, testPlate.size);
    const rendered = renderPlate(testPlate, [troy]);
    for (const hostileId of ['constructor', '__proto__', 'toString', 'hasOwnProperty', 'valueOf']) {
      // The default path: no labelBoxes option at all (DEFAULT_CAMERA_OPTIONS).
      expect(() => computeCamera(testPlate, viewport, [hostileId], { places: [troy] })).not.toThrow();
      expect(computeCamera(testPlate, viewport, [hostileId], { places: [troy] })).toEqual({ scale: 1, tx: 0, ty: 0 });

      // The real path every caller (Reader.svelte, PlatePanel.svelte) uses:
      // labelBoxes sourced straight from a renderPlate result.
      expect(() =>
        computeCamera(testPlate, viewport, [hostileId], { places: [troy], labelBoxes: rendered.labelBoxes }),
      ).not.toThrow();
      expect(
        computeCamera(testPlate, viewport, [hostileId], { places: [troy], labelBoxes: rendered.labelBoxes }),
      ).toEqual({ scale: 1, tx: 0, ty: 0 });
    }
  });

  it('a place with no coords contributes nothing (honesty rule) — an all-unlocated focus set falls back to identity', () => {
    const viewport = viewportFromBBox(testPlate.bbox!, testPlate.size);
    const camera = computeCamera(testPlate, viewport, ['ghost-place'], { places: [ghost] });
    expect(camera).toEqual({ scale: 1, tx: 0, ty: 0 });
  });

  it('a single located place (degenerate/zero-extent bbox) does not produce an infinite or NaN zoom, and stays inside the canvas', () => {
    const viewport = viewportFromBBox(testPlate.bbox!, testPlate.size);
    const camera = computeCamera(testPlate, viewport, ['troy'], { places: [troy] });
    expect(Number.isFinite(camera.scale)).toBe(true);
    expect(Number.isFinite(camera.tx)).toBe(true);
    expect(Number.isFinite(camera.ty)).toBe(true);
    expect(camera.scale).toBeLessThanOrEqual(8); // default maxScale
    const [x, y] = project(troy.coords!, viewport);
    const outX = x * camera.scale + camera.tx;
    const outY = y * camera.scale + camera.ty;
    expect(outX).toBeGreaterThanOrEqual(-1e-6);
    expect(outX).toBeLessThanOrEqual(testPlate.size[0] + 1e-6);
    expect(outY).toBeGreaterThanOrEqual(-1e-6);
    expect(outY).toBeLessThanOrEqual(testPlate.size[1] + 1e-6);
  });

  it('a custom maxScale option clamps a single-point focus below the default', () => {
    const viewport = viewportFromBBox(testPlate.bbox!, testPlate.size);
    const camera = computeCamera(testPlate, viewport, ['troy'], { places: [troy], maxScale: 2 });
    expect(camera.scale).toBeLessThanOrEqual(2);
  });
});

// The Chart Room postcard camera (2026-09-02): a camera sized round the
// focus pin ALONE (the tests above) sliced 92/163 framed schematic scenes'
// labels mid-word at the resulting zoom, and 45/163 panned past the sheet
// into white. These cover the fix: labelBoxes widens the framed bbox to
// include the focus's own rendered name, and computeCamera's own clamp
// (never scale < 1, translation never past the sheet edge) replaces what
// used to be the caller's problem.
describe('computeCamera: label box framing + sheet clamp (postcard camera)', () => {
  it('frames a focus place\'s rendered LABEL box, not just its pin — mirrors the pin-only test above', () => {
    const viewport = viewportFromBBox(testPlate.bbox!, testPlate.size);
    const rendered = renderPlate(testPlate, [troy]);
    const labelBox = rendered.labelBoxes['troy'];
    expect(labelBox).toBeDefined();
    const camera = computeCamera(testPlate, viewport, ['troy'], {
      places: [troy],
      labelBoxes: rendered.labelBoxes,
    });
    const [x1, y1, x2, y2] = labelBox!;
    for (const [x, y] of [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]) {
      const outX = x * camera.scale + camera.tx;
      const outY = y * camera.scale + camera.ty;
      expect(outX).toBeGreaterThanOrEqual(-1e-6);
      expect(outX).toBeLessThanOrEqual(testPlate.size[0] + 1e-6);
      expect(outY).toBeGreaterThanOrEqual(-1e-6);
      expect(outY).toBeLessThanOrEqual(testPlate.size[1] + 1e-6);
    }
  });

  it('never zooms below 1 or pans past the sheet edge, for a focus point near each of the four corners (the 45/163 white-overrun regression)', () => {
    const [minLat, minLon, maxLat, maxLon] = testPlate.bbox!;
    // Just inside each corner, not exactly on it — a point exactly at the
    // bbox edge is itself a degenerate case this isn't testing.
    const corners: PlatePlace[] = [
      { id: 'corner-nw', name: 'NW', coords: [maxLat - 0.002, minLon + 0.002], certainty: 'certain' },
      { id: 'corner-ne', name: 'NE', coords: [maxLat - 0.002, maxLon - 0.002], certainty: 'certain' },
      { id: 'corner-sw', name: 'SW', coords: [minLat + 0.002, minLon + 0.002], certainty: 'certain' },
      { id: 'corner-se', name: 'SE', coords: [minLat + 0.002, maxLon - 0.002], certainty: 'certain' },
    ];
    const viewport = viewportFromBBox(testPlate.bbox!, testPlate.size);
    const [W, H] = testPlate.size;
    for (const corner of corners) {
      const camera = computeCamera(testPlate, viewport, [corner.id], { places: [corner] });
      expect(camera.scale).toBeGreaterThanOrEqual(1);
      expect(camera.tx).toBeLessThanOrEqual(1e-6);
      expect(camera.tx).toBeGreaterThanOrEqual(W - camera.scale * W - 1e-6);
      expect(camera.ty).toBeLessThanOrEqual(1e-6);
      expect(camera.ty).toBeGreaterThanOrEqual(H - camera.scale * H - 1e-6);
    }
  });

  it('renderPlate.labelBoxes has an entry for every feature that got a label, and none for one the solver suppressed', () => {
    // `kind: 'tomb'` resolves to the 'feature' label role (KIND_LABEL_CLASS),
    // which is unconditionally suppression-eligible (priority: 1) on a
    // geographic plate — piling ten long names on the same point is enough
    // to force at least one below the SUPPRESS_OVERLAP_FRACTION floor.
    const crowd: PlatePlace[] = Array.from({ length: 10 }, (_, i) => ({
      id: `tomb-${i}`,
      name: `Barrow of the Nameless Warrior Number ${i}`,
      coords: [39.95, 26.2] as [number, number],
      certainty: 'certain' as const,
      kind: 'tomb',
    }));
    const result = renderPlate(testPlate, crowd);
    expect(result.suppressedLabels.length).toBeGreaterThan(0); // sanity: the fixture actually triggers suppression
    for (const p of crowd) {
      if (result.suppressedLabels.includes(p.id)) expect(result.labelBoxes[p.id]).toBeUndefined();
      else expect(result.labelBoxes[p.id]).toBeDefined();
    }
  });

  it('the achaean-assembly-place worst case (370px label, the flattest camera-scale outlier measured) fits inside the camera frame it earns, off the REAL schematic plate', () => {
    const plate = parsePlate(JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8')));
    // Mirrors the real apparatus/places.json record verbatim (name, kind,
    // plateAnchors, positionBasis) — not a shortened stand-in — so the
    // measured label width is the real one, not a synthetic best case.
    const gaz = (JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[]).find(
      (p) => p.id === 'achaean-assembly-place',
    )!;
    const place: PlatePlace = {
      id: 'achaean-assembly-place',
      name: "The assembly and law-place, with the gods' altars",
      certainty: 'certain',
      kind: 'camp',
      plateAnchors: gaz.plateAnchors,
      positionBasis: 'conjectural',
    };
    const result = renderPlate(plate, [place]);
    // Stage 5c: the assembly is keyed, so the camera frames the pin (tighter
    // than the old 370px name). Design G: that fallback must still sit
    // inside maxScale and not frame nothing.
    const pinFeat = result.features.find((f) => f.id === 'achaean-assembly-place');
    expect(pinFeat, 'the assembly pin must still draw').toBeDefined();
    const camera = computeCamera(plate, result.viewport, ['achaean-assembly-place'], {
      places: [place],
      labelBoxes: result.labelBoxes,
      maxScale: 4, // Reader.svelte's own Chart Room ceiling (part B)
    });
    expect(camera.scale).toBeLessThanOrEqual(4);
    const [x1, y1, x2, y2] = pinFeat!.bbox;
    const [W, H] = plate.size;
    for (const [x, y] of [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]) {
      const outX = x * camera.scale + camera.tx;
      const outY = y * camera.scale + camera.ty;
      expect(outX).toBeGreaterThanOrEqual(-1e-6);
      expect(outX).toBeLessThanOrEqual(W + 1e-6);
      expect(outY).toBeGreaterThanOrEqual(-1e-6);
      expect(outY).toBeLessThanOrEqual(H + 1e-6);
    }
  });
});

function parseSvgFragment(markup: string): Element {
  const scratch = document.createElement('div');
  scratch.innerHTML = markup;
  return scratch.firstElementChild!;
}

// Codex review finding (2026-09-02): Reader.svelte used to wrap the camera
// group itself via a caller-side regex (wrapPlateCamera) that assumed the
// document ended `</g></svg>` — wrong, since the legend/scale bar/north
// arrow/hypsometric key/neatline are drawn AFTER the clip group closes (see
// the SVG assembly's own comment on why), so the regex's closing `</g>`
// never landed where intended and that furniture silently ended up panning
// and scaling with the map. Fixed at the source: renderPlate itself now
// emits the wrap when asked.
describe('renderPlate: cameraGroup option', () => {
  it('off by default — no .plate-camera at all (unchanged behavior for every existing caller, esp. PlatePanel.svelte, which builds its own client-side camera wrapper)', () => {
    const result = renderPlate(testPlate, [troy]);
    expect(result.svg).not.toContain('plate-camera');
  });

  it('wraps ground + layers + pins + labels in .plate-camera — the furniture (legend, scale bar, neatline) stays OUTSIDE it, never panning/scaling with the map', () => {
    const result = renderPlate(testPlate, [troy], { cameraGroup: true });
    const root = parseSvgFragment(result.svg);
    const cameraG = root.querySelector('.plate-camera');
    expect(cameraG).not.toBeNull();

    // Map content IS inside .plate-camera.
    expect(cameraG!.querySelector('.plate-ground')).not.toBeNull();
    expect(cameraG!.querySelector('[data-place-id="troy"]')).not.toBeNull();

    // Furniture is NOT inside .plate-camera...
    expect(cameraG!.querySelector('.plate-neatline')).toBeNull();
    expect(cameraG!.querySelector('.plate-scale')).toBeNull();
    expect(cameraG!.querySelector('.plate-legend')).toBeNull();
    // ...but IS still present in the document — never dropped, only moved
    // outside the pannable group.
    expect(root.querySelector('.plate-neatline')).not.toBeNull();
    expect(root.querySelector('.plate-scale')).not.toBeNull();
    expect(root.querySelector('.plate-legend')).not.toBeNull();
  });
});

describe('draw primitives', () => {
  const square: [number, number][] = [
    [0, 0],
    [40, 0],
    [40, 40],
    [0, 40],
  ];

  it('hachure is deterministic for the same seed and differs for a different seed', () => {
    const a = hachure(square, { seed: 1 });
    const b = hachure(square, { seed: 1 });
    const c = hachure(square, { seed: 2 });
    expect(a).toBe(b);
    expect(a).not.toBe(c);
    expect(a).toContain('M');
  });

  it('shipRow is deterministic for the same seed and differs for a different seed (hull/position variation is seed-derived, not Math.random)', () => {
    const baseline: [[number, number], [number, number]] = [[0, 0], [100, 0]];
    const a = shipRow(baseline, 2, 4, { seed: 3 });
    const b = shipRow(baseline, 2, 4, { seed: 3 });
    const c = shipRow(baseline, 2, 4, { seed: 4 });
    expect(a).toBe(b);
    expect(a).not.toBe(c);
    expect(a).toContain('M');
    expect(a).toContain('Q'); // curved hull, not a stamped rectangle
  });

  it('wallGlyph produces a line and separate, thinner tick marks, consistently on one side', () => {
    const { line, ticks } = wallGlyph([[0, 0], [50, 0], [50, 30]]);
    expect(line).toContain('M');
    expect(line).toContain('L');
    expect(ticks).toContain('M');
    expect(ticks).toContain('L');

    // Every tick on the first (horizontal) segment should land on the same
    // side (same sign of y-offset from the trace), not alternate.
    const firstSegmentTicks = [...ticks.matchAll(/M ([\d.-]+) ([\d.-]+) L ([\d.-]+) ([\d.-]+)/g)]
      .filter(([, , y0]) => Math.abs(Number(y0)) < 1); // ticks whose base sits on the y=0 segment
    expect(firstSegmentTicks.length).toBeGreaterThan(0);
    const signs = firstSegmentTicks.map(([, , , , y1]) => Math.sign(Number(y1)));
    expect(new Set(signs).size).toBe(1); // all on one consistent side
  });

  it('wallGlyph is deterministic (purely geometric, no seed)', () => {
    const a = wallGlyph([[0, 0], [50, 0], [50, 30]]);
    const b = wallGlyph([[0, 0], [50, 0], [50, 30]]);
    expect(a).toEqual(b);
  });

  it('wallBandGlyph’s hatch reaches the same ends as its faces (2026-09-03, citadel wall-fix: the circuit-restored stub at the West Gate)', () => {
    // A straight trace keeps offsetPolyline's two faces straight too, so the
    // faces' own start/end points are trivial to read back out of `faces`.
    const trace: [number, number][] = [[0, 0], [200, 0]];
    const width = 10;
    const { faces, hatch } = wallBandGlyph(trace, width);
    expect(hatch).not.toBe('');

    // `faces` pairs its numbers with a comma ("M0,5"), `hatch` with a space
    // ("M 0 5") — pull every number out in order and pair them up so both
    // read the same way.
    const points = (s: string) => {
      const nums = [...s.matchAll(/-?[\d.]+/g)].map((m) => Number(m[0]));
      const pts: [number, number][] = [];
      for (let i = 0; i + 1 < nums.length; i += 2) pts.push([nums[i], nums[i + 1]]);
      return pts;
    };
    // `faces` is "M x,y L x,y" (left) + " " + "M x,y L x,y" (right): four
    // points in order — left's start, left's end, right's start, right's end.
    const facePoints = points(faces);
    const leftStart = facePoints[0];
    const rightEnd = facePoints[3];

    // `hatch` is a run of "M x,y L x,y" strokes; the first point of the first
    // stroke and the last point of the last stroke are what matter here.
    const hatchPoints = points(hatch);
    const firstStrokeStart = hatchPoints[0];
    const lastStrokeEnd = hatchPoints[hatchPoints.length - 1];

    // The hatch's very first point sits ON the left face's own start — no
    // bare, unhatched run at the near end (the faces are drawn the FULL
    // trace, so the old hatch, starting one `spacing` in, left a stretch of
    // open double-line with no crosshatch, which read as a stray mark rather
    // than a restored wall wherever it fell beside rather than under the
    // masonry it was meeting).
    expect(firstStrokeStart[0]).toBeCloseTo(leftStart[0], 0);
    expect(firstStrokeStart[1]).toBeCloseTo(leftStart[1], 0);
    // And its last point sits ON the right face's own end — the far end
    // closes the same way, so centreline and hatch end together.
    expect(lastStrokeEnd[0]).toBeCloseTo(rightEnd[0], 0);
    expect(lastStrokeEnd[1]).toBeCloseTo(rightEnd[1], 0);
  });

  it('tumulus produces a dome profile with nested shading arcs, not a bare circle', () => {
    const d = tumulus([10, 20]);
    expect(d).toContain('M');
    expect(d).toContain('Q');
    // Outer dome + two nested shading arcs + base line = 4 subpaths.
    expect(d.split('M').length - 1).toBe(4);
  });
});

describe('waterlines', () => {
  const straightRing: [number, number][] = [[0, 0], [40, 0]];

  it('is deterministic for the same seed and differs for a different seed', () => {
    const a = waterlines([straightRing], { seed: 5 });
    const b = waterlines([straightRing], { seed: 5 });
    const c = waterlines([straightRing], { seed: 6 });
    expect(a).toEqual(b);
    expect(a).not.toEqual(c);
  });

  it('emits the default four lines at growing cumulative offsets from the shore (jitter off for exact geometry)', () => {
    const strokes = waterlines([straightRing], { seed: 1, jitter: 0 });
    expect(strokes).toHaveLength(4);
    // A straight 2-point ring offsets to a parallel line at exactly `dist`
    // px away (both endpoints share the single edge's normal) — the
    // cumulative Huffman offsets (2 / 2.6 / 3.4 / 4.4), verbatim.
    expect(strokes[0].d).toBe('M0,-2 L40,-2');
    expect(strokes[1].d).toBe('M0,-2.6 L40,-2.6');
    expect(strokes[2].d).toBe('M0,-3.4 L40,-3.4');
    expect(strokes[3].d).toBe('M0,-4.4 L40,-4.4');
  });

  it('tapers stroke weight and opacity, shore-adjacent line heaviest and most opaque', () => {
    const strokes = waterlines([straightRing], { seed: 1 });
    const widths = strokes.map((s) => s.width);
    const opacities = strokes.map((s) => s.opacity);
    for (let i = 1; i < widths.length; i++) {
      expect(widths[i]).toBeLessThan(widths[i - 1]);
      expect(opacities[i]).toBeLessThan(opacities[i - 1]);
    }
  });

  it('successive gaps grow by roughly the 1.3x factor from Huffman 2010 ("On Waterlines")', () => {
    const offsets = [2, 2.6, 3.4, 4.4];
    const gaps = offsets.slice(1).map((o, i) => o - offsets[i]);
    for (let i = 1; i < gaps.length; i++) {
      const ratio = gaps[i] / gaps[i - 1];
      expect(ratio).toBeGreaterThan(1.2);
      expect(ratio).toBeLessThan(1.4);
    }
  });

  it('drops a ring that degenerates to fewer than 2 usable points, without throwing, and contributes no strokes', () => {
    const degenerate: [number, number][] = [[5, 5], [5, 5], [5, 5]]; // collapses to 1 point after dedup
    expect(() => waterlines([degenerate], { seed: 1 })).not.toThrow();
    expect(waterlines([degenerate], { seed: 1 })).toEqual([]);
  });

  it('rejects mismatched offsets/weights/opacities lengths', () => {
    expect(() => waterlines([straightRing], { seed: 1, offsets: [1, 2], weights: [1], opacities: [1, 1] })).toThrow(/equal length/);
  });
});

describe('renderPlate: waterline coast style', () => {
  const waterlineCoast: PlateLayer = {
    id: 'coast-wl',
    kind: 'coast',
    style: 'waterline',
    rings: [
      [
        [39.98, 26.18],
        [39.97, 26.19],
        [39.96, 26.2],
      ],
    ],
  };
  const riverWithWaterlineStyle: PlateLayer = {
    ...(testPlate.layers.find((l) => l.id === 'river-1') as PlateLayer),
    style: 'waterline', // deliberately mislabeled -- rivers must ignore this
  };

  it('draws the coast boundary plus the default four fainter, thinner offset strokes', () => {
    const plate: Plate = { ...testPlate, layers: [waterlineCoast] };
    const result = renderPlate(plate, []);
    expect(result.svg).toContain('class="plate-layer plate-layer-coast"');
    // --plate-river, not --scene-map-sea (2026-07-28): a waterline stroked in
    // the sea's own FILL colour is invisible on the water it is drawn on, and
    // in dark theme that fill is near-black. The river/waterline ink is a
    // separate token, contrast-guarded in plate-map-contrast.test.ts.
    const widths = [...result.svg.matchAll(/plate-layer-waterline" d="[^"]*" fill="none" stroke="var\(--plate-river\)" stroke-width="([\d.]+)" stroke-opacity="([\d.]+)"/g)].map((m) => [Number(m[1]), Number(m[2])]);
    expect(widths).toEqual([
      [0.55, 0.85],
      [0.42, 0.65],
      [0.3, 0.48],
      [0.2, 0.32],
    ]);
  });

  it('never waterlines a river layer, even when the layer\'s own style is explicitly set to "waterline" (structural: the river case never reads layer.style)', () => {
    const plate: Plate = { ...testPlate, layers: [riverWithWaterlineStyle] };
    const result = renderPlate(plate, []);
    expect(result.svg).toContain('plate-layer-river');
    expect(result.svg).not.toContain('plate-layer-waterline');
  });
});

describe('renderLayer: relief hachure ink token', () => {
  it('relief fill uses the dedicated --flaxman-hachure token, with no separate fill-opacity stacked on top', () => {
    const result = renderPlate(testPlate, []);
    const reliefMatch = result.svg.match(/<path data-feature-id="relief-1"[^>]*\/>/);
    expect(reliefMatch).not.toBeNull();
    expect(reliefMatch![0]).toContain('fill="var(--flaxman-hachure)"');
    expect(reliefMatch![0]).not.toContain('fill-opacity');
  });
});

// ── 2026-07-28, hachure lane: "the relief hachuring is too heavy and too
// uniform" ── hachure() itself only ever drew one polygon at one fixed
// spacing/weight; these tests hold down the fix, which lives entirely at
// the case 'relief' call site in renderLayer (reliefHachureParams), not
// inside hachure() itself — hachure()'s own spacing/weight defaults (7 /
// 1.6, asserted nowhere by name here) are untouched and still apply to any
// caller that doesn't pass explicit values.
describe('reliefHachureParams: density carries steepness', () => {
  const bbox: [number, number, number, number] = [0, 0, 10, 10];
  const size: [number, number] = [1000, 1000];
  const viewport = viewportFromBBox(bbox, size);

  const basePlate: Plate = {
    id: 'relief-steepness-plate',
    title: 'Relief Steepness Test',
    kind: 'geographic',
    status: 'draft',
    seed: 1,
    bbox,
    size,
    layers: [],
  };

  it('a relief layer with no relief siblings gets the gentle (sparse, thin) end outright — lighter than hachure()\'s own old flat 7px/1.6px defaults', () => {
    const lone: PlateLayer = {
      id: 'lone', kind: 'relief',
      polygon: [[1, 1], [1, 4], [4, 4], [4, 1]],
    };
    const plate: Plate = { ...basePlate, layers: [lone] };
    const params = reliefHachureParams(plate, lone, viewport);
    expect(params.spacing).toBeGreaterThan(7);
    expect(params.weight).toBeLessThan(1.6);
  });

  it('three concentrically nested polygons (an Ida-800/1200-style family) draw denser and heavier the more deeply nested they are', () => {
    // Outer: a broad low band; middle and inner: successively smaller bands
    // stacked over the same footprint, same shape as a real 200/600/1200 m
    // contour family.
    const outer: PlateLayer = {
      id: 'outer', kind: 'relief',
      polygon: [[0.5, 0.5], [0.5, 9], [9, 9], [9, 0.5]],
    };
    const middle: PlateLayer = {
      id: 'middle', kind: 'relief',
      polygon: [[3, 3], [3, 7], [7, 7], [7, 3]],
    };
    const inner: PlateLayer = {
      id: 'inner', kind: 'relief',
      polygon: [[4.5, 4.5], [4.5, 5.5], [5.5, 5.5], [5.5, 4.5]],
    };
    const plate: Plate = { ...basePlate, layers: [outer, middle, inner] };

    const pOuter = reliefHachureParams(plate, outer, viewport);
    const pMiddle = reliefHachureParams(plate, middle, viewport);
    const pInner = reliefHachureParams(plate, inner, viewport);

    // Density carries steepness: spacing shrinks (denser strokes)...
    expect(pOuter.spacing).toBeGreaterThan(pMiddle.spacing);
    expect(pMiddle.spacing).toBeGreaterThan(pInner.spacing);
    // ...and weight grows (heavier strokes) the more deeply nested the band.
    expect(pOuter.weight).toBeLessThan(pMiddle.weight);
    expect(pMiddle.weight).toBeLessThan(pInner.weight);
  });

  it('two UNNESTED sibling bodies (same depth) are still differentiated by relative area — a small isolated body reads denser than a broad one, not identical to it', () => {
    const broad: PlateLayer = {
      id: 'broad', kind: 'relief',
      polygon: [[0.5, 0.5], [0.5, 9], [9, 9], [9, 0.5]],
    };
    const knob: PlateLayer = {
      id: 'knob', kind: 'relief',
      polygon: [[0.5, 0.5], [0.5, 1.2], [1.2, 1.2], [1.2, 0.5]],
    };
    const plate: Plate = { ...basePlate, layers: [broad, knob] };

    const pBroad = reliefHachureParams(plate, broad, viewport);
    const pKnob = reliefHachureParams(plate, knob, viewport);

    expect(pKnob.spacing).toBeLessThan(pBroad.spacing);
    expect(pKnob.weight).toBeGreaterThan(pBroad.weight);
  });

  it('is deterministic and pure (same plate/layer/viewport in, same params out)', () => {
    const a: PlateLayer = { id: 'a', kind: 'relief', polygon: [[1, 1], [1, 3], [3, 3], [3, 1]] };
    const b: PlateLayer = { id: 'b', kind: 'relief', polygon: [[4, 4], [4, 6], [6, 6], [6, 4]] };
    const plate: Plate = { ...basePlate, layers: [a, b] };
    expect(reliefHachureParams(plate, a, viewport)).toEqual(reliefHachureParams(plate, a, viewport));
  });
});

// A wiring regression guard: reliefHachureParams being correct in isolation
// (above) doesn't prove renderLayer's case 'relief' actually calls it — this
// checks the rendered SVG itself changes stroke density when nesting
// changes, so a future edit reverting the call site to the bare
// `hachure(px, { seed })` this lane replaced would fail here even if it left
// reliefHachureParams itself untouched.
describe('renderLayer: relief nesting changes the rendered hachure, not just the isolated helper', () => {
  it('a deeply nested relief polygon renders more stroke subpaths than an isolated one of similar size', () => {
    const bbox: [number, number, number, number] = [0, 0, 10, 10];
    const size: [number, number] = [1000, 1000];
    const isolated: PlateLayer = {
      id: 'isolated', kind: 'relief',
      polygon: [[1, 1], [1, 3], [3, 3], [3, 1]],
    };
    const isolatedPlate: Plate = {
      id: 'p1', title: 'p1', kind: 'geographic', status: 'draft', seed: 5, bbox, size,
      layers: [isolated],
    };

    const outer: PlateLayer = { id: 'outer', kind: 'relief', polygon: [[0.5, 0.5], [0.5, 9], [9, 9], [9, 0.5]] };
    const middleNested: PlateLayer = { id: 'nested', kind: 'relief', polygon: [[1, 1], [1, 3], [3, 3], [3, 1]] };
    const nestedPlate: Plate = {
      id: 'p2', title: 'p2', kind: 'geographic', status: 'draft', seed: 5, bbox, size,
      layers: [outer, middleNested],
    };

    const countStrokes = (svg: string, id: string) => {
      // Non-greedy up to a SPACE-prefixed ` d="` (not bare `d="`) so this
      // doesn't latch onto the `d="..."` substring embedded in the
      // `data-layer-id="..."` attribute renderLayer now also stamps on the
      // tag (see the tumulus tests above for the same fix).
      const match = svg.match(new RegExp(`<path data-feature-id="${id}"[^>]*? d="([^"]*)"`));
      expect(match).not.toBeNull();
      return (match![1].match(/M/g) ?? []).length;
    };

    const isolatedCount = countStrokes(renderPlate(isolatedPlate, []).svg, 'isolated');
    const nestedCount = countStrokes(renderPlate(nestedPlate, []).svg, 'nested');
    expect(nestedCount).toBeGreaterThan(isolatedCount);
  });
});

// ── Light/dark comparability, in the spirit of the hachure-contrast test in
// plate-map-contrast.test.ts (out of scope for this lane) ── that suite
// asserts RAW contrast ratio is comparable; this lane's finding is that raw
// ratio parity is not the same as PERCEIVED strength parity for reversed
// (light-on-dark) ink, so the fix is an intentional ASYMMETRY: dark's
// --flaxman-hachure is retuned to read as LESS contrasty than light's
// against the surface it actually renders on (--plate-upland), not equally.
describe('global.css: relief hachure ink is intentionally under-contrasted in dark theme (compensates light-on-dark irradiation)', () => {
  const CSS_PATH = path.resolve(process.cwd(), 'styles/global.css');
  const css = readFileSync(CSS_PATH, 'utf-8');

  function extractBlock(selector: string): string {
    const selIdx = css.indexOf(selector);
    if (selIdx === -1) throw new Error(`selector not found in global.css: ${selector}`);
    const braceStart = css.indexOf('{', selIdx);
    let depth = 0;
    let i = braceStart;
    for (; i < css.length; i++) {
      if (css[i] === '{') depth++;
      else if (css[i] === '}') {
        depth--;
        if (depth === 0) break;
      }
    }
    return css.slice(braceStart, i + 1);
  }

  function readToken(block: string, name: string): string {
    const m = block.match(new RegExp(`${name}:\\s*([^;]+);`));
    if (!m) throw new Error(`token ${name} not found`);
    return m[1].trim();
  }

  function hexToRgb(hex: string): [number, number, number] {
    const n = parseInt(hex.replace('#', ''), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function srgbToLinear(c: number): number {
    const v = c / 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  }
  function relativeLuminance([r, g, b]: [number, number, number]): number {
    return 0.2126 * srgbToLinear(r) + 0.7152 * srgbToLinear(g) + 0.0722 * srgbToLinear(b);
  }
  function contrastRatio(a: string, b: string): number {
    const la = relativeLuminance(hexToRgb(a));
    const lb = relativeLuminance(hexToRgb(b));
    return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
  }

  const light = extractBlock(':root {');
  const darkMedia = extractBlock(':root:not([data-theme]) {');
  const darkTheme = extractBlock(':root[data-theme="dark"] {');
  const lightTheme = extractBlock(':root[data-theme="light"] {');

  const lightContrast = contrastRatio(readToken(light, '--flaxman-hachure'), readToken(light, '--plate-upland'));
  const lightThemeContrast = contrastRatio(readToken(lightTheme, '--flaxman-hachure'), readToken(lightTheme, '--plate-upland'));

  it.each([
    ['dark (prefers-color-scheme)', darkMedia],
    ['dark (data-theme="dark")', darkTheme],
  ])('%s: hachure-vs-upland contrast is LOWER than light\'s, not matched to it, and still clears the 4.5:1 floor', (_name, block) => {
    const darkContrast = contrastRatio(readToken(block, '--flaxman-hachure'), readToken(block, '--plate-upland'));
    expect(darkContrast).toBeGreaterThanOrEqual(4.5);
    expect(darkContrast).toBeLessThan(lightContrast);
    expect(darkContrast).toBeLessThan(lightThemeContrast);
  });

  it('the two light theme blocks (:root default and data-theme="light") agree with each other (unchanged by this lane)', () => {
    expect(lightThemeContrast).toBeCloseTo(lightContrast, 3);
  });

  // Finding F6 (stage 6 review, 2026-09-03): --plate-schematic-ink was
  // defined at :root (light) and at :root[data-theme="dark"], but missing
  // from THIS block -- a reader on system dark theme with no explicit
  // data-theme (:root:not([data-theme])) fell through to the light-tuned
  // value and lost contrast. Must match the explicit dark-theme value.
  it('--plate-schematic-ink is defined in the OS-dark block and matches :root[data-theme="dark"]', () => {
    expect(readToken(darkMedia, '--plate-schematic-ink')).toBe(readToken(darkTheme, '--plate-schematic-ink'));
  });
});

// ── 2026-07-28: "that looks awful, it's just shapes, no geography at all" ──
// Four diagnosed causes. Three are the renderer's: the whole canvas was
// painted --scene-map-land so nothing was ever water; ZERO <text> elements
// were emitted, so no feature was ever named; and region layers defaulted to
// --plate-tint, i.e. var(--accent-light), so every landform was drawn in the
// site's wine UI accent. These tests hold the fixes down.

describe('renderPlate: the sheet declares its own land and water', () => {
  it('defaults to a land ground (every plate authored before `ground` existed is unchanged)', () => {
    const result = renderPlate(testPlate, []);
    expect(result.svg).toContain('class="plate-ground" x="0" y="0" width="400" height="300" fill="var(--scene-map-land)"');
  });

  it('`ground: "sea"` paints the bare sheet as water', () => {
    const result = renderPlate({ ...testPlate, ground: 'sea' }, []);
    expect(result.svg).toContain('class="plate-ground" x="0" y="0" width="400" height="300" fill="var(--scene-map-sea)"');
  });

  it('parsePlate rejects an unknown ground rather than silently dropping it', () => {
    expect(() =>
      parsePlate({ id: 'x', title: 'X', kind: 'geographic', status: 'draft', bbox: BBOX, size: SIZE, ground: 'lava', layers: [] }),
    ).toThrow(/ground/);
  });

  it('a coast layer with a fill draws its rings as a filled body under the shoreline (evenodd), so a `ground: "sea"` plate reads as a coast', () => {
    const island: PlateLayer = {
      id: 'island', kind: 'coast', fill: 'land',
      rings: [[[39.9, 26.15], [39.95, 26.15], [39.95, 26.2], [39.9, 26.2], [39.9, 26.15]]],
    };
    const result = renderPlate({ ...testPlate, ground: 'sea', layers: [island] }, []);
    const body = result.svg.match(/<path data-feature-id="island-body"[^>]*\/>/);
    expect(body).not.toBeNull();
    expect(body![0]).toContain('fill="var(--scene-map-land)"');
    expect(body![0]).toContain('fill-rule="evenodd"');
    // The shoreline itself is still stroked on top, unfilled.
    expect(result.svg).toMatch(/<path data-feature-id="island" [^>]*fill="none"[^>]*stroke="var\(--scene-map-coast\)"/);
  });

  it('a coast layer with no fill is pure linework, exactly as before', () => {
    const result = renderPlate(testPlate, []);
    expect(result.svg).not.toContain('plate-layer-coast-body');
  });
});

describe('renderPlate: lettering (a map with no names is not a map)', () => {
  it('reverses a leftward text path for reading', () => {
    const path: [number, number][] = [[80, 20], [50, 30], [10, 40]];
    expect(orientPathForReading(path)).toEqual([[10, 40], [50, 30], [80, 20]]);
  });

  it('keeps a rightward text path unchanged', () => {
    const path: [number, number][] = [[10, 40], [50, 30], [80, 20]];
    expect(orientPathForReading(path)).toBe(path);
  });

  it('places overlapping pin labels in non-overlapping candidate boxes', () => {
    const inputs = [
      { id: 'alpha', anchorBox: [100, 100, 110, 110] as [number, number, number, number], textWidth: 40, fontSize: 12 },
      { id: 'beta', anchorBox: [104, 104, 114, 114] as [number, number, number, number], textWidth: 40, fontSize: 12 },
    ];
    const defaultBox = (input: (typeof inputs)[number]) => {
      const candidate = labelCandidates(input.anchorBox, input.fontSize)[0];
      return [candidate.x, candidate.y - input.fontSize * 0.8, candidate.x + input.textWidth, candidate.y + input.fontSize * 0.25];
    };
    const [defaultFirst, defaultSecond] = inputs.map(defaultBox);
    const defaultOverlap = Math.max(0, Math.min(defaultFirst[2], defaultSecond[2]) - Math.max(defaultFirst[0], defaultSecond[0])) *
      Math.max(0, Math.min(defaultFirst[3], defaultSecond[3]) - Math.max(defaultFirst[1], defaultSecond[1]));
    expect(defaultOverlap).toBeGreaterThan(0);
    const placements = placeLabelCandidates(inputs, { width: 300, height: 200, margin: 8 });
    expect(labelCandidates(inputs[0].anchorBox, 12).map((candidate) => candidate.position)).toEqual(
      expect.arrayContaining(['E', 'W', 'N', 'S', 'NE', 'NW', 'SE', 'SW']),
    );
    const [first, second] = placements;
    const overlap = Math.max(0, Math.min(first.box[2], second.box[2]) - Math.max(first.box[0], second.box[0])) *
      Math.max(0, Math.min(first.box[3], second.box[3]) - Math.max(first.box[1], second.box[1]));
    expect(overlap).toBe(0);
  });

  it('places label candidates identically for the same input', () => {
    const inputs = [
      { id: 'beta', anchorBox: [104, 104, 114, 114] as [number, number, number, number], textWidth: 40, fontSize: 12 },
      { id: 'alpha', anchorBox: [100, 100, 110, 110] as [number, number, number, number], textWidth: 40, fontSize: 12 },
    ];
    const options = { width: 300, height: 200, margin: 8, markerBoxes: [[100, 100, 110, 110]] as [number, number, number, number][] };
    expect(placeLabelCandidates(inputs, options)).toEqual(placeLabelCandidates(inputs, options));
  });

  it('names every located place — none is silently dropped, however crowded the sheet', () => {
    const crowd: PlatePlace[] = Array.from({ length: 12 }, (_, i) => ({
      id: `p${i}`, name: `Place${i}`, coords: [39.95 + i * 0.0005, 26.2 + i * 0.0005] as [number, number], certainty: 'certain' as const,
    }));
    const result = renderPlate(testPlate, crowd);
    for (const p of crowd) expect(result.svg).toContain(`>${p.name}</text>`);
  });

  it('draws a leader when a crowded point label moves to an outer candidate ring', () => {
    const outerPlacement = placeLabelCandidates(
      [{ id: 'outer', anchorBox: [95, 95, 105, 105], textWidth: 20, fontSize: 12 }],
      { width: 300, height: 200, margin: 8, placedBoxes: [[70, 85, 130, 117]] },
    )[0];
    expect(outerPlacement.candidateIndex).toBeGreaterThanOrEqual(8);
    const crowd: PlatePlace[] = Array.from({ length: 12 }, (_, i) => ({
      id: `crowded-${i}`,
      name: `Crowded place ${i}`,
      coords: [39.95, 26.2] as [number, number],
      certainty: 'certain' as const,
    }));
    const result = renderPlate(testPlate, crowd);
    expect(result.svg).toContain('class="plate-leader"');
  });

  it('letters a pin with the map SHORT form, keeping the full catalogue name on the pin title', () => {
    const place: PlatePlace = { id: 'troy', name: 'Troy (Ilios)', coords: [39.957, 26.239], certainty: 'certain' };
    const result = renderPlate(testPlate, [place]);
    expect(result.svg).toContain('>Troy</text>');
    expect(result.svg).toContain('<title>Troy (Ilios)</title>');
  });

  it('drops a leading article and re-capitalises ("The wall of Troy" -> "Wall of Troy")', () => {
    const place: PlatePlace = { id: 'w', name: 'The wall of Troy', coords: [39.957, 26.239] };
    expect(renderPlate(testPlate, [place]).svg).toContain('>Wall of Troy</text>');
  });

  it('escapes a hostile place name in the label, not just in the title', () => {
    const nasty: PlatePlace = { id: 'x', name: '<script>alert&"1"</script>', coords: [39.95, 26.2] };
    const result = renderPlate(testPlate, [nasty]);
    expect(result.svg).not.toContain('<script>');
    expect(result.svg).toContain('&lt;script&gt;');
  });

  it('names a linear feature ALONG its own run, via a textPath into a defs path', () => {
    const river: PlateLayer = {
      id: 'scamander', kind: 'river', label: 'Scamander',
      path: [[39.88, 26.14], [39.92, 26.2], [39.96, 26.3]],
    };
    const result = renderPlate({ ...testPlate, layers: [river] }, []);
    expect(result.svg).toMatch(/<path id="plate-lp-scamander" d="[^"]+" fill="none" stroke="none"\/>/);
    expect(result.svg).toContain('<textPath href="#plate-lp-scamander"');
    expect(result.svg).toContain('>Scamander</textPath>');
  });

  it('names an area feature across its extent in letterspaced caps', () => {
    const region: PlateLayer = {
      id: 'plain', kind: 'region', label: 'Scamandrian plain',
      polygon: [[39.9, 26.15], [39.95, 26.15], [39.95, 26.3], [39.9, 26.3]],
    };
    const result = renderPlate({ ...testPlate, layers: [region] }, []);
    expect(result.svg).toContain('>SCAMANDRIAN PLAIN</text>');
    expect(result.svg).toMatch(/plate-label-region[^>]*letter-spacing="/);
  });

  it('letters a name once: a layer naming a place that is also pinned yields to the pin', () => {
    const river: PlateLayer = { id: 'r', kind: 'river', placeId: 'troy', path: [[39.88, 26.14], [39.96, 26.3]] };
    const troyPlace: PlatePlace = { id: 'troy', name: 'Troy', coords: [39.957, 26.239] };
    const result = renderPlate({ ...testPlate, layers: [river] }, [troyPlace]);
    // (the pin's own <title>Troy</title> is not lettering — count <text> only)
    expect([...result.svg.matchAll(/>Troy<\/text>/g)]).toHaveLength(1);
    expect(result.svg).not.toContain('</textPath>');
  });

  it('haloes labels via the paint-order ATTRIBUTE, not the CSS property', () => {
    const result = renderPlate(testPlate, [troy]);
    expect(result.svg).toMatch(/<text[^>]*paint-order="stroke"[^>]*stroke="var\(--scene-map-label-halo\)"/);
  });

  it('uses four size steps, at least 2px apart, none below 9.5px', () => {
    const region: PlateLayer = { id: 'reg', kind: 'region', label: 'A region', polygon: [[39.9, 26.15], [39.95, 26.15], [39.95, 26.3]] };
    const river: PlateLayer = { id: 'riv', kind: 'river', label: 'A river', path: [[39.88, 26.14], [39.96, 26.34]] };
    const wall: PlateLayer = { id: 'wal', kind: 'wall', label: 'A wall', trace: [[39.87, 26.13], [39.99, 26.35]] };
    const result = renderPlate({ ...testPlate, layers: [region, river, wall] }, [troy]);
    const sizes = [...new Set([...result.svg.matchAll(/plate-label[^>]*font-size="([\d.]+)"/g)].map((m) => Number(m[1])))].sort((a, b) => a - b);
    expect(sizes).toHaveLength(4);
    expect(sizes[0]).toBeGreaterThanOrEqual(9.5);
    for (let i = 1; i < sizes.length; i++) expect(sizes[i] - sizes[i - 1]).toBeGreaterThanOrEqual(2);
  });

  it('letters a schematic plate in ranked classes, not one flat register (the sheet\'s own headline defect)', () => {
    // Before 2026-08-13 every located place on a schematic plate lettered as
    // `settlement`, one size, one weight — so on the Trojan-plain sheet "Pyre
    // of Patroclus" printed exactly as loudly as Troy. The gazetteer's own
    // `kind` now selects a class, and the classes must be separated the way
    // docs/TROAD-CARTOGRAPHY.md requires: at least 2px apart, never under 9.5.
    const kinds: [string, string][] = [['camp', 'a-camp'], ['tomb', 'b-tomb'], ['spring', 'c-spring']];
    const places: PlatePlace[] = kinds.map(([kind, id], i) => ({
      id,
      name: `Name ${id}`,
      kind,
      certainty: 'speculative' as const,
      plateAnchors: { shield: [0.2 + i * 0.25, 0.3 + i * 0.2] as [number, number] },
      positionBasis: 'conjectural' as const,
    }));
    const svg = renderPlate(schematicPlate, places).svg;
    const sizes = [...new Set([...svg.matchAll(/plate-label[^>]*font-size="([\d.]+)"/g)].map((m) => Number(m[1])))].sort((a, b) => a - b);
    expect(sizes.length).toBeGreaterThanOrEqual(3);
    expect(sizes[0]).toBeGreaterThanOrEqual(9.5);
    for (let i = 1; i < sizes.length; i++) expect(sizes[i] - sizes[i - 1]).toBeGreaterThanOrEqual(2);
  });
});

describe('renderPlate: frame, scale and legend', () => {
  it('draws a double neatline', () => {
    const rects = [...renderPlate(testPlate, []).svg.matchAll(/<rect class="plate-neatline"[^>]*stroke-width="([\d.]+)"/g)].map((m) => Number(m[1]));
    expect(rects).toEqual([1.2, 0.4]);
  });

  it('computes the bar scale from the plate\'s OWN viewport, so it cannot lie', () => {
    const wide = renderPlate(testPlate, []).svg;
    // Half the geographic span across the same pixel canvas = half the ground distance per bar.
    const zoomed = renderPlate({ ...testPlate, bbox: [39.94, 26.2, 39.98, 26.26] }, []).svg;
    const km = (svg: string) => Number(svg.match(/>([\d.]+) km</)![1]);
    expect(km(wide)).toBeGreaterThan(km(zoomed));
  });

  it('gives a schematic plate no scale bar (it has no scale, and drawing one would be a fabricated claim)', () => {
    expect(renderPlate(schematicPlate, [anchoredPlace]).svg).not.toContain('plate-scale');
  });

  it('keys only registers the sheet actually drew, and every register it drew', () => {
    const svg = renderPlate(testPlate, [troy, scamander]).svg;
    expect(svg).toContain('class="plate-legend"');
    expect(svg).toContain('>River</text>'); // river-1 is drawn
    expect(svg).toContain('>Location secure</text>'); // troy is `certain`
    expect(svg).toContain('>Traditional identification</text>'); // scamander is `traditional`
    expect(svg).not.toContain('>Mythical'); // no mythical place is pinned here
    expect(svg).not.toContain('>Tumulus<'); // no tumulus layer on this fixture
  });

  it('keys one row per register, not one per layer', () => {
    const rivers: PlateLayer[] = [1, 2, 3].map((i) => ({
      id: `river-${i}`, kind: 'river' as const, path: [[39.9, 26.15], [39.95, 26.2]] as [number, number][],
    }));
    const svg = renderPlate({ ...testPlate, layers: rivers }, []).svg;
    expect([...svg.matchAll(/>River</g)]).toHaveLength(1);
  });

  // ── 2026-07-30, plate UX lane ────────────────────────────────────────────

  it('is exported so an interactive camera can recompute an honest bar at its own zoom factor without the renderer knowing a camera exists', () => {
    const { viewport } = renderPlate(testPlate, []);
    const native = scaleBarMarkup(viewport, SIZE[0], SIZE[1]);
    // Zooming in 3x means each screen px now covers a third of the ground it
    // did at zoom 1 -- pass viewport.scale * zoomFactor (exactly what
    // PlatePanel's updateScaleBar does) and the recomputed bar must claim a
    // shorter (or equal, at the "nice" step's granularity) distance, never a
    // longer one.
    const zoomedIn = scaleBarMarkup({ ...viewport, scale: viewport.scale * 3 }, SIZE[0], SIZE[1]);
    const km = (s: string) => Number(s.match(/>([\d.]+) km</)![1]);
    expect(km(zoomedIn)).toBeLessThanOrEqual(km(native));
    expect(zoomedIn).toContain('class="plate-scale"');
  });

  it('tags every label with data-label-for naming the place or layer id it letters, so a viewer can key off it (certainty filter, no-magnify pivot)', () => {
    const svg = renderPlate(testPlate, [troy, scamander]).svg;
    expect(svg).toContain('data-label-for="troy"');
    expect(svg).toContain('data-label-for="scamander-mouth"');
  });

  it('a tier-2 place label carries data-label-tier="2" and class plate-label-tier2', () => {
    const place: PlatePlace = {
      id: 'oak',
      name: 'Oak',
      coords: [39.95, 26.2],
      certainty: 'certain',
      kind: 'settlement',
      labelTier: 2,
    };
    const svg = renderPlate(testPlate, [place]).svg;
    const tag = svg.match(/<text class="plate-label[^"]*" data-label-for="oak"[^>]*>/)?.[0];
    expect(tag, svg).toBeTruthy();
    expect(tag).toContain('data-label-tier="2"');
    expect(tag).toContain('plate-label-tier2');
  });

  it('a default (tier-1) place label carries neither the tier attribute nor the tier class', () => {
    const place: PlatePlace = {
      id: 'oak',
      name: 'Oak',
      coords: [39.95, 26.2],
      certainty: 'certain',
      kind: 'settlement',
    };
    const svg = renderPlate(testPlate, [place]).svg;
    const tag = svg.match(/<text class="plate-label[^"]*" data-label-for="oak"[^>]*>/)?.[0];
    expect(tag).toBeTruthy();
    expect(tag).not.toContain('data-label-tier');
    expect(tag).not.toContain('plate-label-tier2');
  });

  // Stage 5a (2026-09-02): a zoom-gated consumer hides a tier-2 label below
  // its threshold and must hide the dashed/hairline leader pointing at it
  // in the same pass — the leader carried no tier of its own before this,
  // so a hidden tier-2 name would leave a leader dangling on the sheet.
  it('a tier-2 place\'s LEADER carries data-label-tier="2" and class plate-leader-tier2 too, when one is drawn', () => {
    const crowd: PlatePlace[] = Array.from({ length: 12 }, (_, i) => ({
      id: `crowded-${i}`,
      name: `Crowded place ${i}`,
      coords: [39.95, 26.2] as [number, number],
      certainty: 'certain' as const,
      labelTier: 2 as const,
    }));
    const result = renderPlate(testPlate, crowd);
    expect(result.svg).toContain('class="plate-leader plate-leader-tier2"');
    const leaderTag = result.svg.match(/<path class="plate-leader plate-leader-tier2"[^>]*>/)?.[0];
    expect(leaderTag, result.svg).toBeTruthy();
    expect(leaderTag).toContain('data-label-tier="2"');
    // The leader still carries data-label-for, unchanged by this fix — a
    // consumer hides it by matching that id, never by tier alone.
    expect(leaderTag).toMatch(/data-label-for="crowded-\d+"/);
  });

  it('a tier-1 (default) place\'s leader carries neither the tier attribute nor the tier class', () => {
    const crowd: PlatePlace[] = Array.from({ length: 12 }, (_, i) => ({
      id: `crowded-${i}`,
      name: `Crowded place ${i}`,
      coords: [39.95, 26.2] as [number, number],
      certainty: 'certain' as const,
    }));
    const result = renderPlate(testPlate, crowd);
    expect(result.svg).toContain('class="plate-leader"');
    const leaderTag = result.svg.match(/<path class="plate-leader"[^>]*>/)?.[0];
    expect(leaderTag, result.svg).toBeTruthy();
    expect(leaderTag).not.toContain('data-label-tier');
    expect(leaderTag).not.toContain('plate-leader-tier2');
  });

  it('labelSize small uses the minor style (9.5px) instead of the settlement default (13.5px)', () => {
    const base: PlatePlace = {
      id: 'oak',
      name: 'Oak',
      coords: [39.95, 26.2],
      certainty: 'certain',
      kind: 'settlement',
    };
    const smallSvg = renderPlate(testPlate, [{ ...base, labelSize: 'small' }]).svg;
    const defaultSvg = renderPlate(testPlate, [base]).svg;
    const smallTag = smallSvg.match(/<text class="plate-label[^"]*" data-label-for="oak"[^>]*>/)?.[0];
    const defaultTag = defaultSvg.match(/<text class="plate-label[^"]*" data-label-for="oak"[^>]*>/)?.[0];
    expect(smallTag).toContain('font-size="9.5"');
    expect(defaultTag).toContain('font-size="13.5"');
  });

  it('parsePlate accepts labelTier 1|2 and labelSize small|base on a layer, and rejects others', () => {
    const layer = {
      id: 'r',
      kind: 'region' as const,
      polygon: [
        [39.9, 26.15],
        [39.91, 26.16],
        [39.9, 26.17],
      ] as [number, number][],
    };
    expect(() => parsePlate({ ...testPlate, layers: [{ ...layer, labelTier: 2, labelSize: 'small' }] })).not.toThrow();
    expect(() => parsePlate({ ...testPlate, layers: [{ ...layer, labelTier: 1, labelSize: 'base' }] })).not.toThrow();
    expect(() => parsePlate({ ...testPlate, layers: [{ ...layer, labelTier: 3 as 1 }] })).toThrow(/labelTier/);
    expect(() => parsePlate({ ...testPlate, layers: [{ ...layer, labelSize: 'tiny' as 'small' }] })).toThrow(/labelSize/);
  });

  // 2026-09-03 review, finding 5: a layer had no honesty tier of its own —
  // fine for drawn geometry, wrong for a layer that IS a claim (the
  // citadel's poem-drawn buildings, which have no gazetteer place of their
  // own to carry PlatePlace.certainty through). Mirrors that same enum.
  it('parsePlate accepts a layer certainty tier and rejects an unknown one', () => {
    const layer = {
      id: 'r',
      kind: 'region' as const,
      polygon: [
        [39.9, 26.15],
        [39.91, 26.16],
        [39.9, 26.17],
      ] as [number, number][],
    };
    for (const tier of ['certain', 'traditional', 'speculative', 'mythical'] as const) {
      const parsed = parsePlate({ ...testPlate, layers: [{ ...layer, certainty: tier }] });
      expect(parsed.layers[0].certainty).toBe(tier);
    }
    expect(() => parsePlate({ ...testPlate, layers: [{ ...layer, certainty: 'confirmed' as 'certain' }] })).toThrow(
      /certainty/,
    );
  });

  it('moves the legend out of a corner that already holds labels/pins, picking whichever corner overlaps least (occlusion finding, 2026-07-30: on trojan-plain-schematic the hardcoded bottom-right corner sat on top of four Achilles\'-end labels)', () => {
    const size: [number, number] = [400, 300];
    const crowded: Plate = { ...schematicPlate, size, layers: [] };
    // A tight cluster of speculative places anchored deep in the sheet's own
    // bottom-right -- exactly the corner legendMarkup always used before this
    // fix, regardless of what else was drawn there.
    const crowdedPlaces: PlatePlace[] = [
      { id: 'hut-of-achilles', name: 'Hut of Achilles', certainty: 'speculative', plateAnchors: { shield: [0.86, 0.82] }, positionBasis: 'conjectural' },
      { id: 'tomb-of-achilles-and-patroclus', name: 'Tomb of Achilles and Patroclus', certainty: 'speculative', plateAnchors: { shield: [0.88, 0.9] }, positionBasis: 'conjectural' },
      { id: 'pyre-of-patroclus', name: 'Pyre of Patroclus', certainty: 'speculative', plateAnchors: { shield: [0.82, 0.9] }, positionBasis: 'conjectural' },
      { id: 'funeral-games-ground', name: 'Funeral Games Ground', certainty: 'speculative', plateAnchors: { shield: [0.76, 0.9] }, positionBasis: 'conjectural' },
    ];
    const svg = renderPlate(crowded, crowdedPlaces).svg;
    const m = svg.match(/<rect class="plate-legend-panel" x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"/);
    expect(m).toBeTruthy();
    const [, xs, ys, ws, hs] = m!;
    const legendBox = [Number(xs), Number(ys), Number(xs) + Number(ws), Number(ys) + Number(hs)];
    // The crowded quadrant, generously padded for label overhang.
    const crowdedQuadrant = [size[0] * 0.6, size[1] * 0.6, size[0], size[1]];
    const overlaps =
      legendBox[0] < crowdedQuadrant[2] &&
      legendBox[2] > crowdedQuadrant[0] &&
      legendBox[1] < crowdedQuadrant[3] &&
      legendBox[3] > crowdedQuadrant[1];
    expect(overlaps).toBe(false);
  });

  it('keeps the legend in its original bottom-right corner when nothing crowds it (no regression on the ordinary case)', () => {
    const size: [number, number] = [400, 300];
    // A river up in the sheet's TOP-LEFT is the only thing to key or avoid --
    // bottom-right is genuinely the least-cost corner here, and the tie-break
    // (LEGEND_CORNERS tried 'br' first) keeps it there.
    const plateWithKey: Plate = { ...schematicPlate, size, layers: [{ id: 'river-x', kind: 'river', path: [[0.02, 0.02], [0.1, 0.1]] }] };
    const svg = renderPlate(plateWithKey, []).svg;
    const m = svg.match(/<rect class="plate-legend-panel" x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"/);
    expect(m).toBeTruthy();
    const [, xs, ys, ws, hs] = m!;
    // Bottom-right placement: right/bottom edges sit past the sheet's own
    // midline, not hugging the left/top.
    expect(Number(xs) + Number(ws)).toBeGreaterThan(size[0] * 0.5);
    expect(Number(ys) + Number(hs)).toBeGreaterThan(size[1] * 0.5);
  });
});

// ── 2026-07-29, the hypsometric lane ──────────────────────────────────────
// "It's better but still too crude. Not pretty enough." — five flat relief
// polygons on the plain and eleven on the Troad, every one the same tan under
// the same hachure, is a diagram OF terrain. `elevation` on a relief layer is
// what switches it into the hypsometric register: filled from a graduated
// ramp, edged with a hairline, not hachured. These hold that switch down at
// BOTH ends — the new path and the old one, which must still work for the two
// plates whose relief is hand-authored and has no elevations to give.

describe('hypsometric relief bands', () => {
  const bbox: [number, number, number, number] = [0, 0, 10, 10];
  const size: [number, number] = [400, 400];
  const box = (lo: number, hi: number): [number, number][] => [
    [lo, lo],
    [hi, lo],
    [hi, hi],
    [lo, hi],
  ];
  const banded: Plate = {
    id: 'banded',
    title: 'Banded',
    kind: 'geographic',
    status: 'draft',
    seed: 7,
    bbox,
    size,
    layers: [
      { id: 'b-100', kind: 'relief', elevation: 100, rings: [box(1, 9)] },
      { id: 'b-200', kind: 'relief', elevation: 200, rings: [box(2, 8), box(2.2, 3)] },
      { id: 'b-400', kind: 'relief', elevation: 400, polygon: box(3, 7) },
    ],
  };

  it('hypsometricLevels reports the sheet\'s own distinct elevations, ascending', () => {
    expect(hypsometricLevels(banded)).toEqual([100, 200, 400]);
    // A plate whose relief is hand-authored has no elevations, which is what
    // keeps the hachure register alive for it.
    expect(hypsometricLevels(testPlate)).toEqual([]);
  });

  it('the ramp runs from step 1 at the lowest band to the top step at the highest, monotonically', () => {
    const levels = [10, 20, 40, 60, 100, 150, 200, 320];
    const steps = levels.map((l) => hypsometricStep(levels, l));
    expect(steps[0]).toBe(1);
    expect(steps[steps.length - 1]).toBe(12);
    for (let i = 1; i < steps.length; i++) expect(steps[i]).toBeGreaterThan(steps[i - 1]);
  });

  it('a band is filled from the ramp and edged with the contour hairline — never hachured', () => {
    const svg = renderPlate(banded, []).svg;
    const band = svg.match(/<path data-feature-id="b-400"[^>]*\/>/);
    expect(band).not.toBeNull();
    expect(band![0]).toContain('fill="var(--plate-relief-12)"');
    expect(band![0]).toContain('stroke="var(--plate-contour)"');
    expect(svg).toContain('plate-layer-relief-band');
    // The hachure register is gone from this sheet entirely: no comb of
    // strokes, and none of the tokens that drew one.
    expect(svg).not.toContain('var(--flaxman-hachure)');
    expect(svg).not.toContain('var(--plate-upland)');
    // Lowest band takes step 1, so it steps out of the sheet ground with no seam.
    expect(svg).toContain('fill="var(--plate-relief-1)"');
  });

  it('a relief layer may carry several disjoint bodies at one level as `rings`', () => {
    const svg = renderPlate(banded, []).svg;
    const band = svg.match(/<path data-feature-id="b-200"[^>]*\/>/)![0];
    // Two rings, two subpaths — each closed.
    expect(band.match(/Z/g)?.length).toBe(2);
  });

  it('band edges are drawn as curves, not as the polygon they were simplified to', () => {
    const band = renderPlate(banded, []).svg.match(/<path data-feature-id="b-400"[^>]*\/>/)![0];
    expect(band).toContain('Q');
    expect(band).not.toMatch(/ L\d/);
  });

  it('a relief layer WITHOUT an elevation still hachures (the hand-authored plates)', () => {
    const svg = renderPlate(testPlate, []).svg;
    expect(svg).toContain('fill="var(--flaxman-hachure)"');
    expect(svg).toContain('plate-layer-relief-body');
    expect(svg).not.toContain('plate-layer-relief-band');
  });

  it('the sheet carries a graduated elevation key naming its own levels in metres', () => {
    const svg = renderPlate(banded, []).svg;
    expect(svg).toContain('plate-hypsometric-key');
    expect(svg).toContain('Elevation, meters');
    expect(svg).toContain('>400<');
    // The band legend row is gone with it — the key says what the tints mean.
    expect(svg).not.toContain('High ground (hachured)');
  });

  it('an elevation must be a number at or above sea level', () => {
    const bad = (elevation: unknown) => () =>
      parsePlate({
        id: 'p', title: 'P', kind: 'geographic', status: 'draft', bbox, size,
        layers: [{ id: 'r', kind: 'relief', elevation, polygon: box(1, 9) }],
      });
    expect(bad(-5)).toThrow(/elevation/);
    expect(bad('400')).toThrow(/elevation/);
    expect(bad(Number.NaN)).toThrow(/elevation/);
    expect(() => bad(0)()).not.toThrow();
  });

  it('a banded sheet bakes no colour of its own — every fill is still a var() token', () => {
    const svg = renderPlate(banded, []).svg;
    expect(svg).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(svg).not.toMatch(/\b(rgb|rgba|hsl|hsla)\(/);
  });
});

// ── The curve pass, and the proof it does not move the line ────────────────
//
// Every measured line on a geographic sheet is now drawn as a curve rather
// than as the polygon it is stored as (smoothPathD in plate.ts, 2026-07-29).
// The whole objection to doing that to a coastline is that smoothing might
// move it, and the Bronze Age shore on apparatus/plates/trojan-plain.json is
// a calibrated line: it was derived from the 10 m contour BECAUSE that level
// passes 1.2 km north of Hisarlık, where Kraft, Rapp, Kayan and Luce put the
// bay head, and the 8 m and 12 m contours (2.8 km and 0.7 km) are both
// outside the published range. So these tests do not check that a curve was
// emitted. They re-measure the drawing.
//
// The projection is equirectangular and therefore AFFINE (see geo.ts:
// x and y are each a linear function of lon and lat), and the smoothing is
// built entirely out of midpoints, so smoothing commutes with projection:
// measuring the deviation in plate pixels and converting by the sheet's own
// scale is exact, not an approximation.
describe('the curve pass does not move the Bronze Age shoreline', () => {
  const raw = JSON.parse(readFileSync(SEED_PLATE_PATH, 'utf-8'));
  const livePlate = parsePlate(raw);
  const viewport = viewportFromBBox(livePlate.bbox!, livePlate.size);
  // Metres per plate pixel, from the plate's own projection: one degree of
  // latitude is 111_320 m and the viewport scales latitude by `scale`.
  const M_PER_PX = 111_320 / viewport.scale;

  const shoreLayer = livePlate.layers.find((l) => l.id === 'shore-bronze')!;
  const shorePx = shoreLayer.rings![0].map((p) => project(p as [number, number], viewport));

  // Samples the emitted `d` of a curve, walking M/L/Q commands.
  function samplePathD(d: string, per = 24): [number, number][] {
    const out: [number, number][] = [];
    let cur: [number, number] = [0, 0];
    for (const m of d.matchAll(/([MLQ])([-\d.,\s]+)/g)) {
      const n = m[2].trim().split(/[\s,]+/).map(Number);
      if (m[1] === 'M' || m[1] === 'L') {
        cur = [n[0], n[1]];
        out.push(cur);
      } else {
        const [cx, cy, ex, ey] = n;
        for (let i = 1; i <= per; i++) {
          const t = i / per;
          const u = 1 - t;
          out.push([
            u * u * cur[0] + 2 * u * t * cx + t * t * ex,
            u * u * cur[1] + 2 * u * t * cy + t * t * ey,
          ]);
        }
        cur = [ex, ey];
      }
    }
    return out;
  }

  function distToPolyline(p: [number, number], line: [number, number][]): number {
    let best = Infinity;
    for (let i = 0; i + 1 < line.length; i++) {
      const [ax, ay] = line[i];
      const [bx, by] = line[i + 1];
      const dx = bx - ax;
      const dy = by - ay;
      const len2 = dx * dx + dy * dy;
      const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / len2));
      best = Math.min(best, Math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy)));
    }
    return best;
  }

  function shoreCurve(): [number, number][] {
    const svg = renderPlate(livePlate, []).svg;
    const d = svg.match(/data-feature-id="shore-bronze" class="[^"]*" d="([^"]+)"/)![1];
    expect(d).toContain('Q'); // it really is drawn as a curve
    return samplePathD(d);
  }

  it('every point of the drawn curve is within a fraction of the declared generalisation tolerance of the stored line', () => {
    const worst = Math.max(...shoreCurve().map((p) => distToPolyline(p, shorePx) * M_PER_PX));
    // Measured: 215 m, at the bay head, where Douglas-Peucker left facets up
    // to 3.8 km long and the curve therefore has the most corner to cut. The
    // line is stored generalised to 275 m (SHORE_TOL in
    // scripts/prep-terrain-contours.py) and its own note declares it accurate
    // "to on the order of a kilometre", so the curve stays INSIDE the
    // generalisation the line already carries and nowhere near its stated
    // uncertainty. The bound below is the declared tolerance itself: if a
    // future change to the geometry or the smoothing pushes the drawing
    // outside the generalisation it claims, that is a real defect and this
    // test is where it is caught.
    expect(worst).toBeLessThan(275);
    // Lower bound recalibrated 2026-08-11: shore-bronze was re-derived as a
    // sea-connected sub-10 m region (flood fill on the DEM, not stitched
    // contour arcs — see scripts/fix-lagoon-connectivity.py and the layer's
    // own note) after an Opus review found the old line was itself a
    // "generalised 10 m contour... that doubles back on itself" at its
    // 275 m (SHORE_TOL) simplification, which is what let a 3.8 km facet
    // exist to cut a 215 m corner off of. The new line is traced at this
    // sheet's own tighter 0.00012 deg (~13 m) tolerance and carries roughly
    // 6x the vertices (121 vs 21), so there is far less corner left for the
    // curve pass to cut — measured worst point 30.2 m. 20 stays comfortably
    // below that while still asserting the same thing the bound always
    // asserted: the curve deviates from the stored polyline by a real,
    // non-trivial amount, not a no-op flattening.
    expect(worst).toBeGreaterThan(20);
  });

  it('the shore still passes 1.2 km north of Hisarlık — the measurement the 10 m level was chosen for', () => {
    const troyCoords = JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places.find(
      (p: { id: string }) => p.id === 'troy',
    ).coords as [number, number];
    const troyPx = project(troyCoords, viewport);
    const near = Math.min(...shoreCurve().map((p) => Math.hypot(p[0] - troyPx[0], p[1] - troyPx[1]))) * M_PER_PX;
    expect(near).toBeGreaterThan(1050);
    expect(near).toBeLessThan(1350);
  });

  it('a vertex on the sheet frame is never rounded, so a water polygon still meets the neatline', () => {
    // sea-modern runs along two edges of the sheet; rounding those corners
    // pulled the water off the frame and left wedges of land in the corners.
    const svg = renderPlate(livePlate, []).svg;
    const d = svg.match(/data-feature-id="sea-modern" class="[^"]*" d="([^"]+)"/)![1];
    expect(d).toContain('M0,0');
    const [w, h] = livePlate.size;
    const sea = livePlate.layers.find((l) => l.id === 'sea-modern')!;
    const frameVertices = sea
      .polygon!.map((p) => project(p as [number, number], viewport))
      .filter(([x, y]) => Math.abs(x) < 0.5 || Math.abs(y) < 0.5 || Math.abs(x - w) < 0.5 || Math.abs(y - h) < 0.5)
      .map(([x, y]) => `${Math.round(x * 10) / 10},${Math.round(y * 10) / 10}`);
    expect(frameVertices.length).toBeGreaterThan(3);
    // Every one of them survives as a straight-line vertex, verbatim.
    for (const v of frameVertices) expect(d).toMatch(new RegExp(`[ML]${v.replace(/\./g, '\\.')}`));
    expect(d).not.toMatch(/Q0,0/);
  });
});

describe('the soft registers: an indefinite edge drawn as one', () => {
  const raw = JSON.parse(readFileSync(SEED_PLATE_PATH, 'utf-8'));
  const livePlate = parsePlate(raw);
  // With the gazetteer, so a layer whose only name comes from its `placeId`
  // is actually lettered (the `none` region's whole purpose).
  const livePlaces = (JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[]).filter(
    (p) => p.id === 'scamandrian-plain',
  );
  const svg = renderPlate(livePlate, livePlaces).svg;

  it('the delta wetland draws with no outline at all, and through the blur filter', () => {
    const m = svg.match(/data-feature-id="delta-swamp"[^>]*>/)!;
    expect(m[0]).toContain('stroke="none"');
    expect(m[0]).toMatch(/filter="url\(#[^"]+\)"/);
    expect(svg).toContain('<feGaussianBlur');
  });

  it('the reconstructed shoreline is a soft band with an opaque hairline, and the surveyed one is neither', () => {
    expect(svg).toContain('plate-layer-coast-band');
    const band = svg.match(/data-feature-id="shore-bronze-band"[^>]*>/)![0];
    expect(band).toMatch(/filter="url\(#[^"]+\)"/);
    expect(band).toContain('stroke-opacity="0.4"');
    // The modern coastline carries neither: crisp, solid, twice the weight.
    const modern = svg.match(/data-feature-id="coast-modern"[^>]*>/)![0];
    expect(modern).not.toContain('filter=');
    expect(modern).not.toContain('stroke-opacity=');
  });

  it('the blur filter is declared only when the sheet actually has an indefinite feature', () => {
    const noSoft: Plate = { ...testPlate, layers: [testPlate.layers[1]] };
    expect(renderPlate(noSoft, []).svg).not.toContain('feGaussianBlur');
  });

  it('a `none` region draws nothing and keys nothing — it carries only its name', () => {
    const m = svg.match(/data-feature-id="scamandrian-plain"[^>]*>/)![0];
    expect(m).toContain('fill="none"');
    expect(m).toContain('stroke="none"');
    expect(svg).not.toContain('Dry plain');
    // ...but the name is still lettered on the sheet.
    expect(svg).toContain('SCAMANDRIAN PLAIN');
  });

  it('the soft registers bake no colour of their own', () => {
    expect(svg).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(svg).not.toMatch(/\b(rgb|rgba|hsl|hsla)\(/);
    assertEveryVarTokenDefined(svg);
  });
});

// ── The paint stack: water is painted after relief (2026-07-29) ──────────
// The defect: the hypsometric bands are cut from the SRTM terrain grid and
// the shorelines are traced from the Copernicus GLO-30 water mask — two
// independent derivations of "where the land ends," generalised with
// different tolerances — so on the plain sheet the lowest band overshot the
// drawn coast and a pale cream fringe sat on the water outboard of the coast
// stroke. `sea-modern` was authored FIRST, under everything, so every band
// painted over it. Measured before the fix: 151 sheet pixels of relief
// standing on the modern sea; after: 0.
//
// These guard the ORDER rather than the geometry, because order is the fix:
// a land band cannot render over sea if the water is painted later, whatever
// the two derivations disagree about. See paintRank in shared/lib/plate.ts.

/** The document-order index of the first element carrying `cls`, or -1. */
function firstIndexOfClass(svg: string, cls: string): number {
  return svg.indexOf(`class="plate-layer ${cls}"`);
}

/** The document-order index of the LAST element carrying `cls`, or -1. */
function lastIndexOfClass(svg: string, cls: string): number {
  return svg.lastIndexOf(`class="plate-layer ${cls}"`);
}

describe('the paint stack: a land band can never render over water', () => {
  const livePlain = parsePlate(JSON.parse(readFileSync(SEED_PLATE_PATH, 'utf-8')));
  const plainSvg = renderPlate(livePlain, []).svg;

  it('on the live plain sheet, every relief band is emitted before every water body', () => {
    const lastRelief = lastIndexOfClass(plainSvg, 'plate-layer-relief-band');
    const firstWater = firstIndexOfClass(plainSvg, 'plate-layer-region');
    expect(lastRelief).toBeGreaterThan(-1);
    expect(firstWater).toBeGreaterThan(-1);
    expect(lastRelief).toBeLessThan(firstWater);
    // ...and the water bodies really are the sea and the lagoon, not some
    // other region that happens to sort first.
    expect(plainSvg.indexOf('data-feature-id="sea-modern"')).toBeGreaterThan(lastRelief);
    expect(plainSvg.indexOf('data-feature-id="lagoon-bronze"')).toBeGreaterThan(lastRelief);
  });

  it('the order is the RENDERER\'s, not the plate file\'s — authoring water first cannot reintroduce the bleed', () => {
    const sea: PlateLayer = {
      id: 'sea', kind: 'region', fill: 'sea',
      polygon: [[39.87, 26.13], [39.87, 26.35], [40.01, 26.35], [40.01, 26.13]],
    };
    const band: PlateLayer = {
      id: 'band', kind: 'relief', elevation: 10,
      polygon: [[39.9, 26.16], [39.9, 26.2], [39.94, 26.2], [39.94, 26.16]],
    };
    // Authored water-first, exactly as trojan-plain.json still is.
    const svg = renderPlate({ ...testPlate, layers: [sea, band] }, []).svg;
    expect(svg.indexOf('data-feature-id="band"')).toBeLessThan(svg.indexOf('data-feature-id="sea"'));
  });

  it('a `fill: "land"` body stays UNDER the relief it carries (the Troad sheet\'s construction)', () => {
    const land: PlateLayer = {
      id: 'island', kind: 'coast', fill: 'land',
      rings: [[[39.9, 26.15], [39.95, 26.15], [39.95, 26.2], [39.9, 26.2], [39.9, 26.15]]],
    };
    const band: PlateLayer = {
      id: 'band', kind: 'relief', elevation: 200,
      polygon: [[39.91, 26.16], [39.91, 26.19], [39.94, 26.19], [39.94, 26.16]],
    };
    // Authored relief-first, to prove the rank and not the array decides.
    const svg = renderPlate({ ...testPlate, ground: 'sea', layers: [band, land] }, []).svg;
    expect(svg.indexOf('data-feature-id="island-body"')).toBeLessThan(svg.indexOf('data-feature-id="band"'));
  });

  it('the marsh is NOT swept into the water group: it stays a translucent wash OVER the terrain', () => {
    const swamp = plainSvg.indexOf('data-feature-id="delta-swamp"');
    expect(swamp).toBeGreaterThan(lastIndexOfClass(plainSvg, 'plate-layer-relief-band'));
    expect(swamp).toBeGreaterThan(plainSvg.indexOf('data-feature-id="lagoon-bronze"'));
    const m = plainSvg.match(/data-feature-id="delta-swamp"[^>]*>/)![0];
    // Translucent, so the contours read through it, and no outline at all —
    // the layer note's "a wetland has no boundary" claim, still drawn.
    expect(m).toContain('fill-opacity="0.55"');
    expect(m).toContain('stroke="none"');
    expect(m).toMatch(/filter="url\(#[^"]+\)"/);
  });

  it('the sort is stable — layers sharing a rank keep the order the plate file authored them in', () => {
    const rings: [number, number][][] = [[[39.9, 26.15], [39.95, 26.15], [39.95, 26.2], [39.9, 26.15]]];
    const a: PlateLayer = { id: 'coast-a', kind: 'coast', rings };
    const b: PlateLayer = { id: 'coast-b', kind: 'coast', rings };
    const svg = renderPlate({ ...testPlate, layers: [a, b] }, []).svg;
    expect(svg.indexOf('data-feature-id="coast-a"')).toBeLessThan(svg.indexOf('data-feature-id="coast-b"'));
  });
});

// ── The sandy barrier is ground, not a line (2026-07-29) ──────────────────
// `barrier-bronze` is the bar that closed the Bronze Age lagoon off from the
// open sea. Authored as a `coast` layer because its geometry IS a contour
// line (the 5 m level across the bay mouth), it drew as a dark hairline in a
// glow — and at zoom that read as a river running out across the water
// (John, 2026-07-29). It now draws as what it is: a body of the sheet's
// lowest ground, with a blurred margin because its width was never surveyed.

describe('the sandy barrier draws as ground, not as a watercourse', () => {
  const livePlain = parsePlate(JSON.parse(readFileSync(SEED_PLATE_PATH, 'utf-8')));
  const svg = renderPlate(livePlain, []).svg;
  const barrier = svg.match(/data-feature-id="barrier-bronze"[^>]*>/)![0];

  it('is filled in the sheet\'s lowest hypsometric step, which is what a sand bar is', () => {
    expect(barrier).toContain('class="plate-layer plate-layer-barrier"');
    expect(barrier).toContain('stroke="var(--plate-relief-1)"');
  });

  it('carries no hairline down its middle — that mark is what made it read as a river', () => {
    expect(svg).not.toContain('data-feature-id="barrier-bronze-band"');
    expect(svg.match(/data-feature-id="barrier-bronze"/g)!.length).toBe(1);
    expect(barrier).not.toContain('var(--plate-river)');
  });

  it('its width is a symbol, so its edges are blurred rather than drawn', () => {
    expect(barrier).toMatch(/filter="url\(#[^"]+\)"/);
    expect(svg).toContain('<feGaussianBlur');
  });

  it('stays visually distinct from BOTH shorelines — three registers, three drawings', () => {
    const reconstructed = svg.match(/data-feature-id="shore-bronze-band"[^>]*>/)![0];
    const modern = svg.match(/data-feature-id="coast-modern"[^>]*>/)![0];
    // The reconstructed shore is a soft band in the coast ink with an opaque
    // hairline; the modern coast is a solid stroke; the barrier is neither.
    expect(reconstructed).toContain('stroke="var(--scene-map-coast)"');
    expect(modern).toContain('stroke="var(--scene-map-coast)"');
    expect(barrier).not.toContain('var(--scene-map-coast)');
    expect(modern).not.toContain('filter=');
  });

  it('keys as ground in the legend, not as a shoreline', () => {
    expect(svg).toContain('Sandy barrier, reconstructed — width not surveyed');
  });

  it('bakes no colour of its own', () => {
    expect(barrier).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    assertEveryVarTokenDefined(svg);
  });
});

// ── A river is painted beneath any water it crosses (2026-07-29) ──────────
// The defect: our rivers are modern OSM watercourses, and their lower reaches
// cross ground that was under water in 1200 BC — so on the plain sheet the
// Scamander and the Simoeis ran north past the reconstructed shoreline and
// out into the lagoon, asserting a Bronze Age river where the plate's own
// evidence says there was sea. See shared/lib/plate.ts's WaterBody block.

/** Every `d` attribute the emitted SVG carries for one feature id, in paint order. */
function pathsFor(svg: string, featureId: string): string[] {
  const re = new RegExp(`<path data-feature-id="${featureId}" class="[^"]*" d="([^"]*)"`, 'g');
  return [...svg.matchAll(re)].map((m) => m[1]);
}

function pointsOf(d: string): [number, number][] {
  return [...d.matchAll(/(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)/g)].map((m) => [Number(m[1]), Number(m[2])]);
}

function distToSegment(p: [number, number], a: [number, number], b: [number, number]): number {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const len2 = dx * dx + dy * dy;
  const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / len2));
  return Math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy));
}

function inPolygon([px, py]: [number, number], polygon: [number, number][]): boolean {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];
    if (yi > py !== yj > py && px < ((xj - xi) * (py - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

describe('renderLayer: a river is painted beneath the water it crosses', () => {
  // Schematic so the geometry is drawn as straight segments: every number in
  // the emitted `d` is then a point ON the line, which makes the containment
  // assertions exact rather than approximate.
  const bay: Plate = {
    id: 'bay',
    title: 'Bay',
    kind: 'schematic',
    status: 'draft',
    size: [100, 100],
    layers: [
      { id: 'the-bay', kind: 'region', fill: 'sea', polygon: [[0, 0.6], [1, 0.6], [1, 1], [0, 1]] },
      { id: 'the-river', kind: 'river', path: [[0.5, 0.1], [0.5, 0.5], [0.5, 0.9]] },
    ],
  };
  // u,v map straight across size [100,100] (projectPoint's schematic branch),
  // so the bay is the band y >= 60 and the river runs down x = 50.
  const svg = renderPlate(bay, []).svg;
  const reaches = pathsFor(svg, 'the-river');

  it('splits the river into a drawn reach and a submerged one', () => {
    expect(reaches).toHaveLength(2);
  });

  it('draws the submerged reach BEFORE the water, so the water covers it', () => {
    const water = svg.indexOf('data-feature-id="the-bay"');
    const [first, second] = [svg.indexOf('data-feature-id="the-river"'), svg.lastIndexOf('data-feature-id="the-river"')];
    expect(first).toBeLessThan(water);
    expect(second).toBeGreaterThan(water);
  });

  it('draws nothing of the river over the water in the river\'s own paint slot', () => {
    // The reach after the water is the one nothing covers.
    const dry = pointsOf(reaches[1]);
    for (const [, y] of dry) expect(y).toBeLessThanOrEqual(60 + 1e-3);
  });

  it('splits the line rather than gapping it: the two reaches share their cut point', () => {
    const wet = pointsOf(reaches[0]);
    const dry = pointsOf(reaches[1]);
    // The cut lands on the shoreline itself, and both reaches end there.
    expect(dry[dry.length - 1][1]).toBeCloseTo(60, 1);
    expect(wet[0][1]).toBeCloseTo(60, 1);
    expect(wet[0][0]).toBeCloseTo(dry[dry.length - 1][0], 1);
  });

  it('keeps every reach under the river\'s OWN feature id, so one toggle still governs the whole river', () => {
    // PlatePanel toggles by exact data-feature-id match — a suffixed id (the
    // trap the coast band's `-band` id already falls into) would leave half a
    // river on the sheet after its own layer was switched off.
    expect(svg.match(/data-feature-id="the-river"/g)).toHaveLength(2);
  });

  it.each(['sea', 'lagoon'] as const)(
    'the "%s" fill a drowned reach hides under is fully opaque — a translucent one would leak the river back',
    (fill) => {
      const plate: Plate = { ...bay, layers: [{ ...bay.layers[0], fill }, bay.layers[1]] };
      const water = renderPlate(plate, []).svg.match(/<path data-feature-id="the-bay"[^>]*\/>/)![0];
      expect(water).toContain('fill-opacity="1"');
    },
  );

  it('leaves a river alone on a sheet with no water at all', () => {
    const dry: Plate = { ...bay, layers: [bay.layers[1]] };
    expect(pathsFor(renderPlate(dry, []).svg, 'the-river')).toHaveLength(1);
  });

  it('does not treat marsh as water — a channel through a wetland is a channel', () => {
    const wet: Plate = {
      ...bay,
      layers: [{ ...bay.layers[0], id: 'the-swamp', fill: 'marsh' }, bay.layers[1]],
    };
    expect(pathsFor(renderPlate(wet, []).svg, 'the-river')).toHaveLength(1);
  });

  it('drops the reach drowned by a `ground: "sea"` sheet: nothing can be drawn beneath the ground', () => {
    const seaGround: Plate = {
      ...bay,
      ground: 'sea',
      layers: [
        { id: 'the-island', kind: 'coast', fill: 'land', rings: [[[0, 0], [1, 0], [1, 0.6], [0, 0.6]]] },
        bay.layers[1],
      ],
    };
    const svgSea = renderPlate(seaGround, []).svg;
    const reachesSea = pathsFor(svgSea, 'the-river');
    expect(reachesSea).toHaveLength(1);
    for (const [, y] of pointsOf(reachesSea[0])) expect(y).toBeLessThanOrEqual(60 + 1e-3);
  });
});

describe('the live plain sheet: the rivers stop at the Bronze Age shore', () => {
  const plate = parsePlate(JSON.parse(readFileSync(path.resolve(process.cwd(), SEED_PLATE_PATH), 'utf-8')));
  const svg = renderPlate(plate, []).svg;
  const lagoonRing = pointsOf(pathsFor(svg, 'lagoon-bronze')[0]);

  // The river's own paint slot is everything emitted after the water that
  // could drown it.
  function ownReaches(id: string): [number, number][][] {
    const water = svg.lastIndexOf('data-feature-id="lagoon-bronze"');
    return [...svg.matchAll(new RegExp(`<path data-feature-id="${id}" class="[^"]*" d="([^"]*)"`, 'g'))]
      .filter((m) => m.index! > water)
      .map((m) => pointsOf(m[1]));
  }

  it('the Scamander is drawn in three reaches — the plain, the lagoon, the modern sea', () => {
    // Recalibrated 2026-08-11: lagoon-bronze (and shore-bronze) were
    // re-derived as a sea-connected sub-10 m region (flood fill on the DEM,
    // not stitched contour arcs -- scripts/fix-lagoon-connectivity.py) after
    // an Opus review found the shipped polygon a ray-casting artifact. Under
    // the old, hand-cut boundary the sandy bar was cut back to its landfall
    // (2026-07-29) so the lagoon and the sea did not overlap there, leaving
    // 141 m of dry bar as its own fourth reach. The re-derived lagoon
    // boundary now reaches the barrier's own landfall directly (both are
    // anchored to the same shipped barrier-bronze vertex — see the fix
    // script), so there is no dry gap left for the river to cross there: the
    // lagoon and modern-sea reaches meet with nothing of the bar between
    // them on this crossing, and own reaches drops from two (the plain, the
    // dry bar) to one (the plain).
    expect(pathsFor(svg, 'scamander')).toHaveLength(3);
    expect(ownReaches('scamander')).toHaveLength(1);
    expect(pathsFor(svg, 'simoeis')).toHaveLength(2);
  });

  it('no stretch of a river is drawn by nobody: every reach of the stored line lands in some paint slot', () => {
    // The defect above, stated as the general property it violated. The union
    // of everything drawn — own slot and submerged alike — must cover the
    // whole stored polyline.
    const viewport = viewportFromBBox(plate.bbox!, plate.size);
    for (const id of ['scamander', 'simoeis']) {
      const stored = plate.layers
        .find((l) => l.id === id)!
        .path!.map((p) => project(p as [number, number], viewport));
      const drawn = pathsFor(svg, id).map(pointsOf);
      const near = (p: [number, number]) =>
        drawn.some((line) =>
          line.some((q, i) => i + 1 < line.length && distToSegment(p, line[i], line[i + 1]) < 0.5),
        );
      for (let i = 0; i + 1 < stored.length; i++) {
        for (const t of [0.25, 0.5, 0.75]) {
          const p: [number, number] = [
            stored[i][0] + (stored[i + 1][0] - stored[i][0]) * t,
            stored[i][1] + (stored[i + 1][1] - stored[i][1]) * t,
          ];
          expect(near(p)).toBe(true);
        }
      }
    }
  });

  it('each drowned reach is drawn before the water that drowns it', () => {
    const idsInOrder = [...svg.matchAll(/data-feature-id="([^"]+)"/g)].map((m) => m[1]);
    const nth = (id: string, n: number) => idsInOrder.reduce<number[]>((acc, v, i) => (v === id ? [...acc, i] : acc), [])[n];
    expect(nth('scamander', 0)).toBeLessThan(nth('sea-modern', 0));
    expect(nth('scamander', 1)).toBeLessThan(nth('lagoon-bronze', 0));
    expect(nth('simoeis', 0)).toBeLessThan(nth('lagoon-bronze', 0));
  });

  it('nothing of a river is drawn over the lagoon in the river\'s own paint slot', () => {
    for (const id of ['scamander', 'simoeis']) {
      for (const own of ownReaches(id)) {
        // A reach ends ON the shore, so its own end points may sit a rounding
        // either side of it; everything between them must be clear of the
        // water by the width of the line that draws it.
        for (const p of own.slice(1, -1)) expect(inPolygon(p, lagoonRing)).toBe(false);
      }
    }
  });

  it('the Scamander still crosses the delta swamp: marsh is wet ground, not open water', () => {
    const swamp = pointsOf(pathsFor(svg, 'delta-swamp')[0]);
    expect(ownReaches('scamander').some((own) => own.some((p) => inPolygon(p, swamp)))).toBe(true);
  });

  it('the calibrated Bronze Age geometry is untouched by the clip', () => {
    // Clipping rivers against the shore must not move the shore. These are
    // the three lines the 10 m calibration is carried by.
    const before = JSON.parse(readFileSync(path.resolve(process.cwd(), SEED_PLATE_PATH), 'utf-8'));
    for (const id of ['shore-bronze', 'barrier-bronze', 'lagoon-bronze']) {
      const layer = before.layers.find((l: PlateLayer) => l.id === id)!;
      const live = plate.layers.find((l) => l.id === id)!;
      expect(live.rings ?? live.polygon).toEqual(layer.rings ?? layer.polygon);
    }
  });
});

describe('the live Troad sheet: the rivers stop at the coast', () => {
  const plate = parsePlate(JSON.parse(readFileSync(path.resolve(process.cwd(), '../apparatus/plates/troad.json'), 'utf-8')));
  const viewport = viewportFromBBox(plate.bbox!, plate.size);
  const svg = renderPlate(plate, []).svg;

  it('does not draw the seaward tail the generalised coastline leaves hanging in the water', () => {
    // Was river-scamander until 2026-07-29. Cleaning the water mask's tidal
    // intrusions off the coastline moved the Scamander's surveyed mouth onto
    // the drawn shore — it now ends 0.025px from its final vertex, which is a
    // BETTER outcome, not a regression: the clipping machinery is unchanged,
    // the fixture simply stopped having a tail to clip. The Satnioeis still
    // hangs 3.2px past the generalised coast (Granicus 0.03, Aesepus 0.01), so
    // it is the remaining case that exercises this.
    const river = plate.layers.find((l) => l.id === 'river-satnioeis')!;
    const mouth = project(river.path!.at(-1)! as [number, number], viewport);
    const drawn = pointsOf(pathsFor(svg, 'river-satnioeis')[0]);
    const end = drawn.at(-1)!;
    // The drawn line stops short of the surveyed final vertex — on the coast.
    expect(Math.hypot(end[0] - mouth[0], end[1] - mouth[1])).toBeGreaterThan(1);
  });

  it('cuts each river once, at its mouth, and nowhere mid-course', () => {
    for (const id of ['river-scamander', 'river-granikos', 'river-aisepos', 'river-satnioeis']) {
      expect(pathsFor(svg, id)).toHaveLength(1);
    }
  });
});

// ── Markers are opaque (2026-07-29; dot symbology 2026-08-10) ────────────
// John, zooming a pin over the hypsometric ramp: the contour lines ran
// straight through the middle of it. The certainty register survives on the
// GEOGRAPHIC-plate dot that replaced the teardrop pin (see certaintyDotStyle)
// exactly the way it survived on the pin: an "open" marker fills with the
// sheet's own halo token, never `fill: none` — a hole would let the terrain
// under it show through, which is the defect this whole register exists to
// prevent. testPlate is geographic, so every place here draws as a dot.

describe('renderPlate: a marker is never transparent to its own basemap', () => {
  const TIERS = ['certain', 'traditional', 'speculative', 'mythical'] as const;
  const dotFor = (certainty: (typeof TIERS)[number]) => {
    const place: PlatePlace = { id: `p-${certainty}`, name: certainty, coords: [39.957, 26.239], certainty };
    const svg = renderPlate(testPlate, [place]).svg;
    return svg.match(new RegExp(`<g data-place-id="p-${certainty}"[^>]*>[\\s\\S]*?</g>`))![0];
  };

  it.each(TIERS)('the %s dot has an opaque body — no fill-opacity, and an "open" tier fills with the halo token rather than none', (certainty) => {
    const dot = dotFor(certainty);
    expect(dot).not.toContain('fill-opacity');
    expect(dot).not.toContain('fill="none"');
    expect(dot).toMatch(/fill="var\(--(accent|scene-map-label-halo)\)"/);
  });

  it('draws each tier as a single primitive shape, not a compound of parts', () => {
    // A dot has no seam to begin with (unlike the teardrop pin it replaced,
    // built from an arc-plus-triangle outline) — this is the equivalent
    // sanity check: exactly one <circle> or <rect> shape per marker.
    for (const t of TIERS) {
      const dot = dotFor(t);
      const shapes = [...dot.matchAll(/<(circle|rect)\b/g)];
      expect(shapes).toHaveLength(1);
    }
  });

  it('keeps the four tiers distinguishable without relying on colour alone', () => {
    // Three signals, none of them hue: shape (circle vs square), fill state
    // (solid ink vs the halo token, i.e. filled disc vs open ring), and a
    // dashed outline. All four tiers land on a distinct combination.
    const signature = (t: (typeof TIERS)[number]) => {
      const dot = dotFor(t);
      const isSquare = dot.includes('<rect');
      const isSolid = /fill="var\(--accent\)"/.test(dot);
      const isDashed = dot.includes('stroke-dasharray');
      return [isSquare, isSolid, isDashed].join('|');
    };
    expect(new Set(TIERS.map(signature)).size).toBe(4);
  });

  it('draws a schematic mark with the same opaque dot symbology as a geographic one', () => {
    // The teardrop is retired on every plate kind (2026-08-13): an engraved
    // plan does not use a web-map pin, and one symbology across both registers
    // is one fewer thing for a reader to learn. What must NOT change is that
    // the mark is a single opaque closed body — no fill-opacity, nothing of the
    // basemap reading through the middle of it.
    const mark = renderPlate(schematicPlate, [anchoredPlace]).svg.match(/<g[^>]*data-place-id="anchored-place"[^>]*>[\s\S]*?<\/g>/)![0];
    expect(mark).not.toContain('fill-opacity');
    expect(mark).not.toContain('A '); // no arc-and-tip teardrop path
    expect([...mark.matchAll(/<(circle|rect)\b/g)]).toHaveLength(1);
  });

  it('keys the legend with the SAME symbols the sheet draws', () => {
    const places: PlatePlace[] = TIERS.map((c, i) => ({
      id: `q-${c}`,
      name: c,
      coords: [39.9 + i * 0.01, 26.2] as [number, number],
      certainty: c,
    }));
    const svg = renderPlate(testPlate, places).svg;
    const legend = svg.match(/<g class="plate-legend">[\s\S]*?$/)![0];
    // Three circular tiers (certain, traditional, mythical) at the legend's
    // own dot radius, plus one open square (speculative) — no other legend
    // row on this fixture draws a circle or a 7.2px-square swatch.
    expect(legend.match(/<circle[^>]*r="4"/g)).toHaveLength(3);
    expect(legend.match(/<rect[^>]*width="7.2"/g)).toHaveLength(1);
    for (const text of ['Location secure', 'Traditional identification', 'Identification speculative', 'Mythical — no known site']) {
      expect(legend).toContain(text);
    }
    // The dashed (mythical) register reaches the key too.
    expect(legend).toContain('stroke-dasharray="2 2"');
  });

  it('bakes no colour of its own into a marker or its key row', () => {
    const svg = renderPlate(testPlate, [troy, scamander, ghost]).svg;
    expect(svg).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    assertEveryVarTokenDefined(svg);
  });
});

// ── The barrier's honesty claim, guarded ─────────────────────────────────────
//
// `barrier-bronze`'s note asserts a machine-checkable fact: every vertex of the
// bar is on land today, 30-600 m inside the modern shoreline. That claim was
// FALSE for months and nobody noticed — the note said the eastern stretch "lies
// outboard of the modern coast, under water now" while 14 of its 15 vertices
// were on land, because the 5 m contour it is cut from stops being a bar east of
// the Rhoiteion landfall and becomes the coastal slope.
//
// It shipped undetected for exactly one reason: no test read the claim. A prose
// note that states a measurable fact and is checked by nothing is a liability,
// not scholarship. This is the guard.
describe('the live Trojan-plain sheet: the barrier is where its note says it is', () => {
  const plate = parsePlate(
    JSON.parse(readFileSync(path.resolve(process.cwd(), '../apparatus/plates/trojan-plain.json'), 'utf-8')),
  );
  const layer = (id: string) => plate.layers.find((l) => l.id === id)!;
  const ringsOf = (id: string): [number, number][][] => {
    const l = layer(id) as { rings?: [number, number][][]; polygon?: [number, number][]; path?: [number, number][] };
    if (l.rings) return l.rings;
    if (l.polygon) return [l.polygon];
    return l.path ? [l.path] : [];
  };

  // Ray casting in lat/lon. Both are plate-space coordinates, so no projection
  // is needed and none is assumed.
  const inside = (pt: [number, number], ring: [number, number][]): boolean => {
    let hit = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [ay, ax] = ring[i];
      const [by, bx] = ring[j];
      if ((ay > pt[0]) !== (by > pt[0]) && pt[1] < ((bx - ax) * (pt[0] - ay)) / (by - ay) + ax) hit = !hit;
    }
    return hit;
  };

  it('every vertex of the bar is on land, as the note claims', () => {
    const sea = ringsOf('sea-modern');
    const bar = ringsOf('barrier-bronze').flat();
    expect(bar.length).toBeGreaterThan(5); // the assertion below is worthless on an empty array
    const onWater = bar.filter((p) => sea.some((ring) => inside(p, ring)));
    expect(onWater).toEqual([]);
  });

  it('the bar does not run along the modern coastline', () => {
    // The defect's visible symptom: an 11px symbol band straddling a line whose
    // axis sat 7-12 m away. Nearest approach is now 31 m; assert it stays clear
    // of the coast's own 13 m generalisation by a real margin.
    const coast = ringsOf('coast-modern').flat();
    const bar = ringsOf('barrier-bronze').flat();
    expect(coast.length).toBeGreaterThan(50);
    expect(bar.length).toBeGreaterThan(5);
    const M_PER_DEG_LAT = 111_320;
    let nearest = Infinity;
    for (const [blat, blon] of bar) {
      for (const [clat, clon] of coast) {
        const dy = (blat - clat) * M_PER_DEG_LAT;
        const dx = (blon - clon) * M_PER_DEG_LAT * Math.cos((blat * Math.PI) / 180);
        nearest = Math.min(nearest, Math.hypot(dx, dy));
      }
    }
    expect(nearest).toBeGreaterThan(20);
  });
});

// ── Reserving drawn linework (2026-08-14) ─────────────────────────────────
// The defect: on the schematic Trojan plain, the label solver had been taught
// to reserve the ship rows but nothing else, so names walked straight over the
// shoreline and the fortifications — "ACHAEAN WALL AND DITCH" printed through
// its own wall, and the Book 23 names printed through the beach into the open
// sea. The fix reserves the drawn linework of the band kinds (coast, wall) as a
// CORRIDOR following the run. These tests lock both halves of that: the
// corridor geometry, and the property it exists to guarantee.
describe('linework reservation', () => {
  it('reserves a corridor along the run, not its bounding rectangle', () => {
    // A 45° diagonal is the case that separates the two: its bounding box is
    // enormous next to the ink it actually covers.
    const halfWidth = 5;
    const diagonal: [number, number][] = [
      [0, 0],
      [200, 200],
    ];
    const boxes = lineworkExtent(diagonal, halfWidth);
    expect(boxes.length).toBeGreaterThan(10); // sub-divided, not one box

    const reserved = boxes.reduce((sum, b) => sum + (b[2] - b[0]) * (b[3] - b[1]), 0);
    const boundingArea = (200 + 2 * halfWidth) ** 2;
    expect(reserved).toBeLessThan(boundingArea * 0.25);

    // Every box still straddles the line it follows.
    for (const [x1, y1, x2, y2] of boxes) {
      const cx = (x1 + x2) / 2;
      const cy = (y1 + y2) / 2;
      expect(Math.abs(cx - cy)).toBeLessThan(1e-9);
    }
  });

  it('inflates the corridor by the band half-width on both sides', () => {
    const boxes = lineworkExtent(
      [
        [0, 50],
        [10, 50],
      ],
      4,
    );
    expect(boxes).toHaveLength(1);
    expect(boxes[0]).toEqual([-4, 46, 14, 54]);
  });

  it('degenerate runs reserve nothing', () => {
    expect(lineworkExtent([], 5)).toEqual([]);
    expect(lineworkExtent([[1, 1]], 5)).toEqual([]);
  });

  // The property the whole mechanism exists for, asserted end to end on a
  // rendered sheet: a place anchored ON a fortification and a place anchored
  // just inland of a shoreline both used to be lettered straight across the
  // linework, because a wall's ink and a shore's ink were invisible to the
  // solver. Deliberately synthetic rather than read from apparatus/places.json
  // — see the note at the top of this file on that file's stability.
  it('no point label is laid across drawn coast or wall linework', () => {
    const sheet: Plate = {
      id: 'reservation-fixture',
      title: 'Reservation Fixture',
      kind: 'schematic',
      status: 'draft',
      seed: 7,
      size: [480, 320],
      layers: [
        {
          id: 'shore',
          kind: 'coast',
          style: 'waterline',
          width: 1.6,
          rings: [
            [
              [0.02, 0.84],
              [0.35, 0.87],
              [0.7, 0.86],
              [0.98, 0.83],
            ],
          ],
        },
        {
          id: 'rampart',
          kind: 'wall',
          trace: [
            [0.05, 0.4],
            [0.5, 0.42],
            [0.95, 0.4],
          ],
        },
      ],
    };
    const places: PlatePlace[] = [
      // Straddling the wall, and named at length so a lazy placement overlaps it.
      { id: 'on-the-wall', name: 'The rampart gate and its towers', certainty: 'speculative', positionBasis: 'conjectural', plateAnchors: { 'reservation-fixture': [0.5, 0.42] } },
      // On the beach, with the sea immediately below it.
      { id: 'on-the-beach', name: 'The barrow raised above the strand', certainty: 'speculative', positionBasis: 'conjectural', plateAnchors: { 'reservation-fixture': [0.62, 0.82] } },
      { id: 'beside-it', name: 'The hut of the far-shooting lord', certainty: 'speculative', positionBasis: 'conjectural', plateAnchors: { 'reservation-fixture': [0.4, 0.8] } },
    ];

    const { svg } = renderPlate(parsePlate(sheet), places);

    // Rebuild each point label's box from what the element itself declares,
    // by the same arithmetic the solver used (estimateLabelWidth/labelBox):
    // a caps style is emitted already uppercased, and `letter-spacing` is the
    // style's own size * tracking. <textPath> names carry no x/y and are
    // exempt by design — a name set ALONG a line rides that line.
    const attr = (tag: string, name: string) => tag.match(new RegExp(`${name}="([^"]*)"`))?.[1];
    const labelBoxes: { id: string; box: [number, number, number, number] }[] = [];
    for (const m of svg.matchAll(/<text\b([^>]*)>([\s\S]*?)<\/text>/g)) {
      const tag = m[1];
      const id = attr(tag, 'data-label-for');
      const x = Number(attr(tag, 'x'));
      if (!id || !Number.isFinite(x)) continue;
      const y = Number(attr(tag, 'y'));
      const size = Number(attr(tag, 'font-size'));
      const tracking = Number(attr(tag, 'letter-spacing') ?? 0);
      const anchor = attr(tag, 'text-anchor') ?? 'start';
      const text = m[2].replace(/&apos;/g, "'").replace(/&amp;/g, '&');
      const width = text.length * (size * (/[a-z]/.test(text) ? 0.56 : 0.64) + tracking);
      const x1 = anchor === 'start' ? x : anchor === 'end' ? x - width : x - width / 2;
      labelBoxes.push({ id, box: [x1, y - size * 0.8, x1 + width, y + size * 0.25] });
    }
    expect(labelBoxes.map((l) => l.id).sort()).toEqual(['beside-it', 'on-the-beach', 'on-the-wall']);

    // The corridors, rebuilt from the plate's own geometry in plate pixels.
    const [W, H] = sheet.size;
    const corridors: [number, number, number, number][] = [
      ...lineworkExtent(
        sheet.layers[0].rings![0].map(([u, v]) => [u * W, v * H] as [number, number]),
        1.6 / 2 + 4.4,
      ),
      ...lineworkExtent(
        sheet.layers[1].trace!.map(([u, v]) => [u * W, v * H] as [number, number]),
        1.15 / 2 + 4,
      ),
    ];
    expect(corridors.length).toBeGreaterThan(20);

    const overlaps = (a: number[], b: number[]) =>
      !(a[2] < b[0] || b[2] < a[0] || a[3] < b[1] || b[3] < a[1]);
    const offenders = labelBoxes
      .filter((l) => corridors.some((c) => overlaps(l.box, c)))
      .map((l) => l.id);
    expect(offenders).toEqual([]);
  });
});

describe('parsePlate: rotationDeg, marginRight, groundOpacity', () => {
  const base = {
    id: 'x',
    title: 'X',
    kind: 'geographic' as const,
    status: 'draft',
    bbox: BBOX,
    size: SIZE,
    layers: [] as PlateLayer[],
  };

  it('reads finite rotationDeg / non-negative marginRight / groundOpacity in (0, 1]', () => {
    const plate = parsePlate({ ...base, rotationDeg: 90, marginRight: 200, groundOpacity: 0.55 });
    expect(plate.rotationDeg).toBe(90);
    expect(plate.marginRight).toBe(200);
    expect(plate.groundOpacity).toBe(0.55);
  });

  it('defaults the three fields to today when they are omitted', () => {
    const plate = parsePlate(base);
    expect(plate.rotationDeg).toBeUndefined();
    expect(plate.marginRight).toBeUndefined();
    expect(plate.groundOpacity).toBeUndefined();
  });

  it('rejects a non-finite rotationDeg', () => {
    expect(() => parsePlate({ ...base, rotationDeg: Infinity })).toThrow(/rotationDeg/);
    expect(() => parsePlate({ ...base, rotationDeg: NaN })).toThrow(/rotationDeg/);
  });

  it('rejects a negative marginRight', () => {
    expect(() => parsePlate({ ...base, marginRight: -1 })).toThrow(/marginRight/);
  });

  // Finding F4 (stage 6 review, 2026-09-03): marginRight >= size[0] used to
  // parse clean; renderPlate's frameWidth = width - marginRight then went
  // zero or negative and the map frame projected off-canvas.
  it('rejects a marginRight equal to or greater than size[0]', () => {
    expect(() => parsePlate({ ...base, marginRight: SIZE[0] })).toThrow(/marginRight/);
    expect(() => parsePlate({ ...base, marginRight: SIZE[0] + 100 })).toThrow(/marginRight/);
  });

  it('accepts a marginRight just under size[0]', () => {
    const plate = parsePlate({ ...base, marginRight: SIZE[0] - 1 });
    expect(plate.marginRight).toBe(SIZE[0] - 1);
  });

  it('rejects a groundOpacity outside (0, 1]', () => {
    expect(() => parsePlate({ ...base, groundOpacity: 0 })).toThrow(/groundOpacity/);
    expect(() => parsePlate({ ...base, groundOpacity: 1.5 })).toThrow(/groundOpacity/);
    expect(() => parsePlate({ ...base, groundOpacity: -0.1 })).toThrow(/groundOpacity/);
  });
});

describe('renderPlate: schematic plate with a geographic bbox (lat/lon space)', () => {
  const geoSchematic: Plate = {
    id: 'schematic-geo',
    title: 'Schematic with geography',
    kind: 'schematic',
    status: 'draft',
    bbox: BBOX,
    size: SIZE,
    layers: [
      {
        id: 'river-geo',
        kind: 'river',
        path: [
          [39.9, 26.15],
          [39.95, 26.2],
        ],
      },
    ],
  };

  it('projects a lat/lon layer point through project(), not unit scaling', () => {
    const result = renderPlate(geoSchematic, []);
    const vp = viewportFromBBox(BBOX, SIZE);
    const [x0, y0] = project([39.9, 26.15], vp);
    const [x1, y1] = project([39.95, 26.2], vp);
    const feature = result.features.find((f) => f.id === 'river-geo')!;
    expect(feature.bbox[0]).toBeCloseTo(Math.min(x0, x1), 6);
    expect(feature.bbox[1]).toBeCloseTo(Math.min(y0, y1), 6);
    expect(feature.bbox[2]).toBeCloseTo(Math.max(x0, x1), 6);
    expect(feature.bbox[3]).toBeCloseTo(Math.max(y0, y1), 6);
  });

  it('draws a scale bar (a sheet with a bbox has a metre)', () => {
    expect(renderPlate(geoSchematic, []).svg).toContain('plate-scale');
  });

  it('parsePlate accepts lat/lon layer points on a schematic plate with a geographic bbox', () => {
    expect(() =>
      parsePlate({
        id: 'schematic-geo',
        title: 'Schematic with geography',
        kind: 'schematic',
        status: 'draft',
        bbox: BBOX,
        size: SIZE,
        layers: [{ id: 'river-geo', kind: 'river', path: [[39.9, 26.15], [39.95, 26.2]] }],
      }),
    ).not.toThrow();
  });

  it('parsePlate rejects a layer point outside that bbox', () => {
    expect(() =>
      parsePlate({
        id: 'schematic-geo',
        title: 'Schematic with geography',
        kind: 'schematic',
        status: 'draft',
        bbox: BBOX,
        size: SIZE,
        layers: [{ id: 'stray', kind: 'river', path: [[0, 0], [1, 1]] }],
      }),
    ).toThrow(/outside the plate bbox/);
  });
});

describe('renderPlate: marginRight and rotationDeg flow into the sheet', () => {
  it('a 200px right margin on a [1320, 1265] sheet leaves a 1120px map frame, keeps ground in it, and parks the legend in the band', () => {
    const plate: Plate = { ...testPlate, size: [1320, 1265], marginRight: 200 };
    const result = renderPlate(plate, []);
    expect(result.viewport.width).toBe(1120);
    expect(result.viewport.height).toBe(1265);
    for (const f of result.features.filter((feat) => feat.type === 'layer')) {
      expect(f.bbox[2]).toBeLessThanOrEqual(1120 + 1e-6);
    }
    const legendX = result.svg.match(/<rect class="plate-legend-panel" x="([-\d.]+)"/);
    expect(legendX).toBeTruthy();
    expect(Number(legendX![1])).toBeGreaterThanOrEqual(1120);
    expect(result.svg).toMatch(/<line class="plate-neatline"[^>]*x1="1120"/);
  });

  it('rotationDeg: 90 wraps the north needle in rotate(-90 …) about the arrow centre', () => {
    const plate: Plate = { ...testPlate, rotationDeg: 90, north: 'True north' };
    const svg = renderPlate(plate, []).svg;
    expect(svg).toMatch(/class="plate-north"/);
    expect(svg).toMatch(/transform="rotate\(-90 /);
  });
});

describe('renderPlate: groundOpacity wash', () => {
  function washGroup(svg: string): { opacity: string; inner: string } | null {
    const open = svg.match(/<g class="plate-ground-wash" opacity="([^"]+)">/);
    if (!open || open.index === undefined) return null;
    const start = open.index + open[0].length;
    let depth = 1;
    let i = start;
    while (i < svg.length && depth > 0) {
      if (svg.startsWith('</g>', i)) {
        depth--;
        if (depth === 0) return { opacity: open[1], inner: svg.slice(start, i) };
        i += 4;
      } else if (svg.startsWith('<g', i)) {
        depth++;
        i += 2;
      } else {
        i++;
      }
    }
    return null;
  }

  it('wraps region/band/relief fills in one plate-ground-wash group and leaves the river outside it', () => {
    const plate: Plate = { ...testPlate, groundOpacity: 0.55 };
    const svg = renderPlate(plate, []).svg;
    expect([...svg.matchAll(/class="plate-ground-wash"/g)]).toHaveLength(1);
    const wash = washGroup(svg);
    expect(wash).not.toBeNull();
    expect(wash!.opacity).toBe('0.55');
    expect(wash!.inner).toContain('data-feature-id="camp-1"');
    expect(wash!.inner).toContain('data-feature-id="relief-1"');
    expect(wash!.inner).not.toContain('plate-layer-river');
    expect(svg).toContain('data-feature-id="river-1"');
  });

  it('emits no wash group when groundOpacity is omitted', () => {
    expect(renderPlate(testPlate, []).svg).not.toContain('plate-ground-wash');
  });
});

// The ground layers on trojan-plain-schematic.json are a copy of the
// geographic sheet, kept in sync by scripts/sync-schematic-ground.py. The
// gazetteer-side geographic sheet is the source of truth.
const SCHEMATIC_V2_GROUND_IDS = [
  'sea-modern',
  'scamandrian-plain',
  'relief-band-0010',
  'relief-band-0015',
  'relief-band-0020',
  'relief-band-0025',
  'relief-band-0030',
  'relief-band-0040',
  'relief-band-0060',
  'relief-band-0100',
  'relief-band-0150',
  'relief-band-0200',
  'relief-band-0320',
  'relief-sigeion-ridge',
  'relief-plain-south',
  'relief-troy-ridge',
  'relief-rhoiteion-ridge',
  'relief-plain-east-200',
  'lagoon-bronze',
  'delta-swamp',
  'shore-bronze',
  'barrier-bronze',
  'coast-modern',
  'scamander',
  'simoeis',
  'besik-bay',
  'aegean',
] as const;

describe('trojan-plain-schematic ground layers match the geographic sheet', () => {
  it('deep-equals each of the listed ground layers by id', () => {
    const geo = JSON.parse(
      readFileSync(path.resolve(process.cwd(), '../apparatus/plates/trojan-plain.json'), 'utf-8'),
    );
    const schematic = JSON.parse(
      readFileSync(path.resolve(process.cwd(), '../apparatus/plates/trojan-plain-schematic.json'), 'utf-8'),
    );
    const geoById = new Map((geo.layers as { id: string }[]).map((l) => [l.id, l]));
    const schematicById = new Map((schematic.layers as { id: string }[]).map((l) => [l.id, l]));
    for (const id of SCHEMATIC_V2_GROUND_IDS) {
      expect(
        schematicById.get(id),
        'the gazetteer-side geographic sheet is the source of truth; run the sync script',
      ).toEqual(geoById.get(id));
    }
  });
});

// ── Stage 3b fixes: the real v2 sheet's furniture (2026-09-02) ─────────────
//
// trojan-plain-schematic-v2 is the first plate that is BOTH `kind:
// "schematic"` (the register is about content — the camp/road layout Homer's
// own text lays out — not coordinate space) AND carries a real bbox (it
// projects the geographic sheet's own ground, rotated). Several places in
// this file gated behaviour on `kind === 'geographic'` where the real test
// should have been usesLatLon(plate)/bbox presence — the rule plate.ts's own
// "Coordinate space is declared by the PRESENCE of a bbox, not by kind"
// comment already states. Each defect below traces to exactly that
// kind-vs-bbox conflation.
const V2_SEED_PLATE_PATH = '../apparatus/plates/trojan-plain-schematic.json';

describe('trojan-plain-schematic-v2: river textPath guides are thinned, not raw (2026-09-02, "Sca m ander")', () => {
  const raw = JSON.parse(readFileSync(path.resolve(process.cwd(), V2_SEED_PLATE_PATH), 'utf-8'));
  const plate = parsePlate(raw);
  // A river layer's name comes from its placeId fallback (neither carries an
  // explicit `label`), so the gazetteer has to be passed for either to be
  // lettered at all — same as the real render-plates.mjs harness's
  // placesForSheet.
  const rivers = (JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[]).filter(
    (p) => p.id === 'scamander' || p.id === 'simoeis',
  );
  const result = renderPlate(plate, rivers);

  it.each(['scamander', 'simoeis'])(
    '%s: the guide has far fewer points than the raw stored river (thinned to >=10px segments, matching the geographic sheet)',
    (id) => {
      expect(result.svg, `${id} must still letter`).toMatch(new RegExp(`data-label-for="${id}"`));
      const rawPath = (plate.layers.find((l) => l.id === id) as { path: [number, number][] }).path;
      const guideMatch = result.svg.match(new RegExp(`id="plate-lp-${id}" d="([^"]+)"`));
      // Stage 5c: a river whose along-path window now hits a numeral badge
      // falls through to point placement (no guide). Thinning still binds
      // whenever a guide is drawn.
      if (!guideMatch) return;
      const guidePointCount = (guideMatch[1].match(/[ML]/g) ?? []).length;
      // An un-thinned guide (one point per raw vertex) is exactly what
      // produced "Sca m ander": method="align" rotates every glyph to a
      // noisy local tangent between near-coincident points. A thinned guide
      // (>=10px between kept points, see TEXTPATH_GUIDE_MIN_SEGMENT) is a
      // small fraction of the raw count, never a near 1:1 copy.
      expect(guidePointCount).toBeLessThan(rawPath.length * 0.5);
    },
  );
});

describe('trojan-plain-schematic-v2: the hypsometric key stacks above the scale bar, not on top of it (2026-09-02)', () => {
  const plate = parsePlate(JSON.parse(readFileSync(path.resolve(process.cwd(), V2_SEED_PLATE_PATH), 'utf-8')));
  const svg = renderPlate(plate, []).svg;

  const boxOf = (re: RegExp): [number, number, number, number] => {
    const m = svg.match(re);
    expect(m, `pattern not found: ${re}`).toBeTruthy();
    const [, x, y, w, h] = m!.map(Number);
    return [x, y, x + w, y + h];
  };

  it('the hypsometric panel and the scale panel do not overlap', () => {
    const hyps = boxOf(/<rect class="plate-hypsometric-panel" x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"/);
    const scale = boxOf(/<rect class="plate-scale-panel" x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"/);
    const intersects =
      hyps[0] < scale[2] && hyps[2] > scale[0] && hyps[1] < scale[3] && hyps[3] > scale[1];
    expect(intersects, `hypsometric ${JSON.stringify(hyps)} overlaps scale ${JSON.stringify(scale)}`).toBe(false);
    // Not just non-overlapping — stacked, the key strictly above the bar
    // (the geographic-sheet convention this schematic-but-bboxed sheet
    // should share; see trojan-plain-light.png).
    expect(hyps[3]).toBeLessThanOrEqual(scale[1]);
  });
});

describe('trojan-plain-schematic-v2: the legend fits its own margin band (2026-09-02, "Sandy barrier… width not surveyed" clipped)', () => {
  const plate = parsePlate(JSON.parse(readFileSync(path.resolve(process.cwd(), V2_SEED_PLATE_PATH), 'utf-8')));
  const svg = renderPlate(plate, []).svg;

  it('the long barrier legend row wraps instead of clipping past the sheet', () => {
    const panelMatch = svg.match(/<rect class="plate-legend-panel" x="([-\d.]+)"/);
    expect(panelMatch).toBeTruthy();
    const legend = svg.match(/<g class="plate-legend">([\s\S]*?)<\/g>/);
    expect(legend, 'legend group missing').toBeTruthy();
    const chunk = legend![1];
    expect(chunk).toMatch(/Sandy barrier/);
    expect(chunk).toMatch(/width not surveyed/);
    const rowTexts = [...chunk.matchAll(/<text x="([-\d.]+)" y="[-\d.]+" font-family="var\(--font-ui\)" font-size="9\.5" fill="var\(--text\)">([^<]*)<\/text>/g)];
    const tspanTexts = [...chunk.matchAll(/<tspan x="([-\d.]+)" y="[-\d.]+">([^<]*)<\/tspan>/g)];
    const barrier = [...rowTexts, ...tspanTexts].filter((m) =>
      /Sandy barrier|reconstructed|width not surveyed/.test(m[2]),
    );
    expect(barrier.length).toBeGreaterThan(0);
    for (const m of barrier) {
      const x = Number(m[1]);
      const text = m[2];
      const estRightEdge = x + text.length * 9.5 * 0.54;
      expect(estRightEdge, `"${text}" estimated right edge ${estRightEdge} vs sheet width ${plate.size[0]}`).toBeLessThanOrEqual(
        plate.size[0] - 12,
      );
    }
  });
});

describe('trojan-plain-schematic-v2: north arrow renders, needle left, N upright (2026-09-02)', () => {
  const plate = parsePlate(JSON.parse(readFileSync(path.resolve(process.cwd(), V2_SEED_PLATE_PATH), 'utf-8')));

  it('the plate declares a north caption', () => {
    expect(plate.north).toBeTruthy();
  });

  it('the rendered sheet carries the needle group, rotated -90deg (east-up, per rotationDeg: 90), fully inside the sheet', () => {
    const svg = renderPlate(plate, []).svg;
    expect(svg).toMatch(/class="plate-north"/);
    expect(svg).toMatch(/transform="rotate\(-90 /);
    const needleMatch = svg.match(/<g transform="rotate\(-90 ([\d.]+) ([\d.]+)\)">/);
    expect(needleMatch).toBeTruthy();
    const [, cx, cy] = needleMatch!.map(Number);
    expect(cx).toBeGreaterThan(0);
    expect(cx).toBeLessThan(plate.size[0]);
    expect(cy).toBeGreaterThan(0);
    expect(cy).toBeLessThan(plate.size[1]);
  });
});

describe('legendMarkup: a right-margin band wraps an entry too long for it instead of clipping (synthetic)', () => {
  const bandPlate: Plate = {
    ...testPlate,
    bbox: undefined,
    marginRight: 120,
    layers: [
      { id: 'a', kind: 'region', legend: 'A very long legend entry that will not fit a 120px band on one line', fill: 'plain', polygon: [[0, 0], [0.1, 0], [0.1, 0.1], [0, 0.1]] },
    ],
  };
  it('wraps the long entry across multiple tspans, each estimated within the band', () => {
    const svg = renderPlate(bandPlate, []).svg;
    const tspans = [...svg.matchAll(/<tspan x="([-\d.]+)" y="[-\d.]+">([^<]*)<\/tspan>/g)];
    expect(tspans.length).toBeGreaterThan(1);
    const panelMatch = svg.match(/<rect class="plate-legend-panel" x="([-\d.]+)" y="[-\d.]+" width="([\d.]+)"/);
    expect(panelMatch).toBeTruthy();
    const panelRight = Number(panelMatch![1]) + Number(panelMatch![2]);
    expect(panelRight).toBeLessThanOrEqual(bandPlate.size[0]);
  });

  it('a short entry in the same band is untouched (still a single <text>, not wrapped)', () => {
    const shortPlate: Plate = {
      ...testPlate,
      bbox: undefined,
      marginRight: 120,
      layers: [{ id: 'a', kind: 'region', legend: 'Short', fill: 'plain', polygon: [[0, 0], [0.1, 0], [0.1, 0.1], [0, 0.1]] }],
    };
    const svg = renderPlate(shortPlate, []).svg;
    expect(svg).toContain('>Short</text>');
    expect(svg).not.toContain('<tspan');
  });
});

describe('renderPlate: inset layer frame in sheet pixels', () => {
  it('without frame, the panel is still the polygon in plate space', () => {
    const plate = parsePlate({
      id: 'unframed-inset',
      title: 'Unframed',
      kind: 'schematic',
      status: 'draft',
      size: [200, 200],
      layers: [
        {
          id: 'title-block',
          kind: 'region',
          style: 'inset',
          polygon: [
            [0.1, 0.1],
            [0.5, 0.1],
            [0.5, 0.5],
            [0.1, 0.5],
          ],
        },
      ],
    });
    const result = renderPlate(plate, []);
    const panel = result.svg.match(
      /class="plate-layer plate-layer-inset-panel" x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"/,
    );
    expect(panel).toBeTruthy();
    expect(Number(panel![1])).toBeCloseTo(20, 5);
    expect(Number(panel![2])).toBeCloseTo(20, 5);
    expect(Number(panel![3])).toBeCloseTo(80, 5);
    expect(Number(panel![4])).toBeCloseTo(80, 5);
  });

  it('an inset layer with frame in the margin renders its rect at the frame and its points scaled into it', () => {
    const frame: [number, number, number, number] = [320, 20, 160, 120];
    const plate = parsePlate({
      id: 'framed-inset',
      title: 'Framed inset',
      kind: 'schematic',
      status: 'draft',
      bbox: BBOX,
      size: [500, 300],
      marginRight: 200,
      layers: [
        {
          id: 'locator',
          kind: 'region',
          style: 'inset',
          label: 'Locator',
          frame,
          // Inner rectangle: without a frame this would be the panel; with
          // one the panel is the frame and these are unit coords inside it.
          polygon: [
            [0.25, 0.25],
            [0.75, 0.25],
            [0.75, 0.75],
            [0.25, 0.75],
          ],
        },
      ],
    });
    const result = renderPlate(plate, []);
    const panel = result.svg.match(
      /class="plate-layer plate-layer-inset-panel" x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"/,
    );
    expect(panel).toBeTruthy();
    expect(Number(panel![1])).toBeCloseTo(320, 5);
    expect(Number(panel![2])).toBeCloseTo(20, 5);
    expect(Number(panel![3])).toBeCloseTo(160, 5);
    expect(Number(panel![4])).toBeCloseTo(120, 5);
    const feat = result.features.find((f) => f.id === 'locator');
    expect(feat).toBeTruthy();
    // Scaled inner points: 320+0.25*160=360, 20+0.25*120=50, 320+0.75*160=440, 20+0.75*120=110.
    expect(feat!.bbox[0]).toBeLessThanOrEqual(360 + 1e-6);
    expect(feat!.bbox[1]).toBeLessThanOrEqual(50 + 1e-6);
    expect(feat!.bbox[2]).toBeGreaterThanOrEqual(440 - 1e-6);
    expect(feat!.bbox[3]).toBeGreaterThanOrEqual(110 - 1e-6);
    expect(feat!.bbox[0]).toBeGreaterThanOrEqual(320 - 1e-6);
    expect(feat!.bbox[2]).toBeLessThanOrEqual(480 + 1e-6);
  });

  it('a margin inset (frame.x >= frameWidth) is furniture: it sits OUTSIDE .plate-camera, never panning or scaling with the map', () => {
    const frame: [number, number, number, number] = [320, 20, 160, 120];
    const plate = parsePlate({
      id: 'framed-inset-camera',
      title: 'Framed inset camera',
      kind: 'schematic',
      status: 'draft',
      bbox: BBOX,
      size: [500, 300],
      marginRight: 200,
      layers: [
        {
          id: 'locator',
          kind: 'region',
          style: 'inset',
          label: 'Locator',
          frame,
          polygon: [
            [0.25, 0.25],
            [0.75, 0.25],
            [0.75, 0.75],
            [0.25, 0.75],
          ],
        },
      ],
      sceneKey: [{ letter: 'A', title: 'Inner box', ref: 'Il. 1.1', layerId: 'locator' }],
    });
    const result = renderPlate(plate, [], { cameraGroup: true });
    const root = parseSvgFragment(result.svg);
    const cameraG = root.querySelector('.plate-camera');
    expect(cameraG).not.toBeNull();

    // The inset panel (and its zone letter, since sceneKey names this same
    // layer) must NOT be inside the pannable camera group...
    expect(cameraG!.querySelector('[data-layer-id="locator"]')).toBeNull();
    expect(cameraG!.querySelector('.plate-zone-letter')).toBeNull();
    // ...but must still be present in the document, alongside the legend.
    expect(root.querySelector('[data-layer-id="locator"]')).not.toBeNull();
    expect(root.querySelector('.plate-zone-letter')).not.toBeNull();
  });

  it('parsePlate rejects a frame that sits outside the sheet', () => {
    expect(() =>
      parsePlate({
        id: 'framed-inset',
        title: 'Framed inset',
        kind: 'schematic',
        status: 'draft',
        bbox: BBOX,
        size: [500, 300],
        layers: [
          {
            id: 'locator',
            kind: 'region',
            style: 'inset',
            frame: [400, 10, 200, 100],
            polygon: [
              [0, 0],
              [1, 0],
              [1, 1],
              [0, 1],
            ],
          },
        ],
      }),
    ).toThrow(/frame/);
  });
});

// 2026-09-03 review, finding 7: an insetOf layer is the SAME lat/lon points
// reprojected through the window's own viewport, which is fitted to the
// window's insetBBox but never clamped to it — geometry running past that
// bbox used to draw straight past the panel's own frame with nothing
// upstream to stop it (the live citadel sheet happens to be clean, which is
// why this went unnoticed). Fixed with one <clipPath> per window, applied to
// that window's projected copies.
describe('renderPlate: an insetOf layer overrunning its window is clipped to the panel (finding 7)', () => {
  it('emits a clip-path for the window and wraps the overrunning copy in a group that references it', () => {
    const plate = parsePlate({
      id: 'inset-clip-test',
      title: 'Inset clip test',
      kind: 'geographic',
      status: 'draft',
      bbox: BBOX,
      size: [400, 300],
      layers: [
        {
          id: 'panel',
          kind: 'region',
          style: 'inset',
          frame: [20, 20, 120, 120],
          insetBBox: [39.95, 26.2, 39.97, 26.22],
          polygon: [
            [0, 0],
            [1, 0],
            [1, 1],
            [0, 1],
          ],
        },
        {
          id: 'overrun',
          kind: 'wall',
          insetOf: 'panel',
          // Runs from well outside the window's bbox to well outside it on
          // the other side — guaranteed to draw past the panel frame if
          // nothing clips it.
          trace: [
            [39.87, 26.13],
            [40.0, 26.35],
          ],
        },
      ],
    });
    const { svg } = renderPlate(plate, []);
    const clipMatch = svg.match(/<clipPath id="([^"]*inset-clip[^"]*)"><rect [^/]*\/><\/clipPath>/);
    expect(clipMatch, 'a per-window clip-path must be emitted').toBeTruthy();
    const clipId = clipMatch![1];
    const wrapped = new RegExp(`<g clip-path="url\\(#${clipId}\\)">[\\s\\S]*?data-feature-id="overrun--inset"`);
    expect(svg, 'the overrunning copy must be drawn inside a group referencing that clip-path').toMatch(wrapped);
  });
});

// 2026-09-03, citadel wall-fix: a `kind: "wall", style: "poem"` layer never
// invents a fortification of its own — every one so far (citadel-weak-wall,
// Il. 6.433-39) names a stretch of a wall that IS surveyed or restored
// elsewhere on the sheet. Drawing it with the plain wall's tick glyph treated
// it as a second fortification, and the ticks flip side at every jog in the
// trace, which on the live sheet reads as a scribble laid over the real
// masonry it was meant to highlight (the "wall open to assault" defect,
// citadel-city-panel). The fix is a highlight: one stroke, no ticks.
describe('renderPlate: a poem-style wall highlights a stretch, it never draws a second fortification (2026-09-03, citadel wall-fix)', () => {
  const plate = parsePlate({
    id: 'poem-wall-test',
    title: 'Poem wall test',
    kind: 'schematic',
    status: 'draft',
    bbox: [39.95, 26.23, 39.96, 26.24],
    size: [400, 300],
    layers: [
      {
        id: 'panel',
        kind: 'region',
        style: 'inset',
        frame: [20, 20, 200, 200],
        insetBBox: [39.9555, 26.2375, 39.957, 26.2395],
        polygon: [
          [0, 0],
          [1, 0],
          [1, 1],
          [0, 1],
        ],
      },
      {
        id: 'weak-stretch',
        kind: 'wall',
        style: 'poem',
        insetOf: 'panel',
        trace: [
          [39.9561, 26.238],
          [39.9563, 26.2382],
          [39.9565, 26.2385],
        ],
      },
    ],
  });
  const { svg } = renderPlate(plate, []);

  it('emits no tick paths, on the face or inside the panel', () => {
    expect(svg).not.toContain('plate-layer-wall-ticks');
  });

  it('draws a single stroked path in the poem register, not a wall-band or plain-wall glyph', () => {
    const onFace = svg.match(/<path data-feature-id="weak-stretch"[^>]*\/>/);
    const inPanel = svg.match(/<path data-feature-id="weak-stretch--inset"[^>]*\/>/);
    expect(onFace, 'the face copy must render').toBeTruthy();
    expect(inPanel, 'the panel copy must render').toBeTruthy();
    for (const el of [onFace![0], inPanel![0]]) {
      expect(el).toContain('plate-layer-wall-poem');
      expect(el).toContain('stroke="var(--text-mid)"');
      expect(el).not.toContain('plate-layer-wall-restored');
      expect(el).not.toContain('plate-layer-wall"'); // the plain fortification class
    }
    // Exactly one <path> per copy — no separate tick element alongside it
    // (the old wallGlyph markup emitted a second <path> sharing the same
    // data-feature-id for its ticks).
    expect(svg.match(/data-feature-id="weak-stretch"/g)).toHaveLength(1);
    expect(svg.match(/data-feature-id="weak-stretch--inset"/g)).toHaveLength(1);
  });
});

// 2026-09-03 review, finding 6: INSET_BADGE_MARGIN (3px) is a flat constant,
// smaller than most numeral discs' own radius (6px minimum, more for a
// two-digit number) — so a badge could sit as close as 3px from its panel's
// drawing rectangle, less than one radius, and badge 29 (Batieia) did. The
// fix makes the margin the badge's OWN radius, so its disc keeps a full
// radius of air inside the panel on every side.
describe('inset numeral discs keep a full radius of padding inside their panel (finding 6)', () => {
  it('on the live schematic sheet, every inset badge disc sits at least its own radius inside its panel', () => {
    const plate = parsePlate(JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8')));
    const places = JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[];
    const { svg } = renderPlate(plate, places);
    const clipRects = [...svg.matchAll(/<clipPath id="([^"]*inset-clip[^"]*)"><rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"\/><\/clipPath>/g)].map(
      ([, id, x, y, w, h]) => ({ id, x: Number(x), y: Number(y), w: Number(w), h: Number(h) }),
    );
    expect(clipRects.length).toBeGreaterThan(0);
    const discs = [...svg.matchAll(/<g class="plate-key-badge"[^>]*data-key-n="(\d+)"[^>]*>[\s\S]*?<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([-\d.]+)"/g)].map(
      ([, n, cx, cy, r]) => ({ n: Number(n), cx: Number(cx), cy: Number(cy), r: Number(r) }),
    );
    expect(discs.length).toBeGreaterThan(0);
    // round1 rounds emitted coordinates to one decimal — allow that much slack.
    const SLACK = 0.15;
    let checked = 0;
    for (const d of discs) {
      const panel = clipRects.find((c) => d.cx >= c.x - 1 && d.cx <= c.x + c.w + 1 && d.cy >= c.y - 1 && d.cy <= c.y + c.h + 1);
      if (!panel) continue; // a map-face badge, not one seated in a window
      checked++;
      expect(d.cx - d.r, `badge ${d.n} left edge`).toBeGreaterThanOrEqual(panel.x + d.r - SLACK);
      expect(d.cx + d.r, `badge ${d.n} right edge`).toBeLessThanOrEqual(panel.x + panel.w - d.r + SLACK);
      expect(d.cy - d.r, `badge ${d.n} top edge`).toBeGreaterThanOrEqual(panel.y + d.r - SLACK);
      expect(d.cy + d.r, `badge ${d.n} bottom edge`).toBeLessThanOrEqual(panel.y + panel.h - d.r + SLACK);
    }
    expect(checked, 'at least one inset badge must have been checked').toBeGreaterThan(0);
  });
});

describe('parsePlate: sceneKey', () => {
  const base = {
    id: 'keyed',
    title: 'Keyed',
    kind: 'schematic' as const,
    status: 'draft',
    size: [400, 300] as [number, number],
    layers: [
      {
        id: 'zone-camp',
        kind: 'region' as const,
        fill: 'none' as const,
        polygon: [
          [0.1, 0.1],
          [0.3, 0.1],
          [0.3, 0.3],
          [0.1, 0.3],
        ],
      },
    ],
  };

  it('reads a well-formed sceneKey', () => {
    const plate = parsePlate({
      ...base,
      sceneKey: [{ letter: 'A', title: 'The camp', ref: 'Il. 8.222–26', layerId: 'zone-camp' }],
    });
    expect(plate.sceneKey).toEqual([
      { letter: 'A', title: 'The camp', ref: 'Il. 8.222–26', layerId: 'zone-camp' },
    ]);
  });

  it('rejects a layerId that is not a layer', () => {
    expect(() =>
      parsePlate({
        ...base,
        sceneKey: [{ letter: 'A', title: 'The camp', ref: 'Il. 8.222–26', layerId: 'no-such' }],
      }),
    ).toThrow(/layerId/);
  });
});

describe('renderPlate: sceneKey', () => {
  it('letters each zone at its polygon centroid and stacks the key below the legend in the margin band', () => {
    const plate = parsePlate({
      id: 'keyed',
      title: 'Keyed',
      kind: 'schematic',
      status: 'draft',
      size: [400, 300],
      marginRight: 120,
      layers: [
        {
          id: 'plain',
          kind: 'region',
          fill: 'plain',
          polygon: [
            [0, 0],
            [0.05, 0],
            [0.05, 0.05],
            [0, 0.05],
          ],
        },
        {
          id: 'zone-camp',
          kind: 'region',
          fill: 'none',
          polygon: [
            [0.1, 0.1],
            [0.3, 0.1],
            [0.3, 0.3],
            [0.1, 0.3],
          ],
        },
        {
          id: 'zone-road',
          kind: 'region',
          fill: 'none',
          polygon: [
            [0.5, 0.4],
            [0.7, 0.4],
            [0.7, 0.6],
            [0.5, 0.6],
          ],
        },
      ],
      sceneKey: [
        { letter: 'A', title: 'The camp', ref: 'Il. 8.222–26', layerId: 'zone-camp' },
        { letter: 'B', title: 'The road', ref: 'Il. 11.806–8', layerId: 'zone-road' },
      ],
    });
    const svg = renderPlate(plate, []).svg;
    const letters = [...svg.matchAll(/<text class="plate-zone-letter"[^>]*x="([-\d.]+)" y="([-\d.]+)"[^>]*>([^<]*)<\/text>/g)];
    expect(letters).toHaveLength(2);
    const byLetter = Object.fromEntries(letters.map((m) => [m[3], { x: Number(m[1]), y: Number(m[2]) }]));
    expect(byLetter.A.x).toBeCloseTo(80, 5);
    expect(byLetter.A.y).toBeCloseTo(60, 0);
    expect(byLetter.B.x).toBeCloseTo(240, 5);
    expect(byLetter.B.y).toBeCloseTo(150, 0);

    const legendPanel = svg.match(
      /<rect class="plate-legend-panel" x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"/,
    );
    expect(legendPanel).toBeTruthy();
    const legendBottom = Number(legendPanel![2]) + Number(legendPanel![4]);
    expect(svg).toContain('class="plate-scene-key"');
    const keyTop = svg.match(/<g class="plate-scene-key"[^>]*>[\s\S]*?y="([-\d.]+)"/);
    expect(keyTop).toBeTruthy();
    expect(Number(keyTop![1])).toBeGreaterThan(legendBottom);

    const keyRows = [...svg.matchAll(/class="plate-scene-key-row"[^>]*>([^<]*)<\/text>/g)].map((m) => m[1]);
    const keyTspans = [...svg.matchAll(/<g class="plate-scene-key"[\s\S]*?<\/g>/g)][0]?.[0].match(/<tspan[^>]*>([^<]*)<\/tspan>/g) ?? [];
    expect(keyRows.length + keyTspans.length).toBeGreaterThanOrEqual(2);
    const bandRight = plate.size[0] - 12;
    for (const m of svg.matchAll(/<g class="plate-scene-key"[\s\S]*?<\/g>/g)) {
      for (const tm of m[0].matchAll(/<(?:text|tspan)[^>]*x="([-\d.]+)"[^>]*>([^<]*)</g)) {
        const estRight = Number(tm[1]) + tm[2].length * 9.5 * 0.54;
        expect(estRight).toBeLessThanOrEqual(bandRight);
      }
    }
  });
});

describe('parsePlate: featureKey', () => {
  const base = {
    id: 'keyed',
    title: 'Keyed',
    kind: 'schematic' as const,
    status: 'draft',
    size: [400, 300] as [number, number],
    layers: [
      {
        id: 'mound-of-patroclus',
        kind: 'tumulus' as const,
        path: [[0.2, 0.2]],
      },
    ],
  };

  it('reads a well-formed featureKey', () => {
    const plate = parsePlate({
      ...base,
      featureKey: [
        {
          title: 'The camp and its wall',
          items: [
            { placeId: 'wagon-gate', label: 'The chariot gate' },
            { layerId: 'mound-of-patroclus', label: 'Patroclus: pyre, barrow and games' },
          ],
        },
      ],
    });
    expect(plate.featureKey).toEqual([
      {
        title: 'The camp and its wall',
        items: [
          { placeId: 'wagon-gate', label: 'The chariot gate' },
          { layerId: 'mound-of-patroclus', label: 'Patroclus: pyre, barrow and games' },
        ],
      },
    ]);
  });

  it('rejects an empty title', () => {
    expect(() =>
      parsePlate({
        ...base,
        featureKey: [{ title: '  ', items: [{ placeId: 'wagon-gate' }] }],
      }),
    ).toThrow(/title/);
  });

  it('rejects an item that names both placeId and layerId', () => {
    expect(() =>
      parsePlate({
        ...base,
        featureKey: [
          {
            title: 'The camp and its wall',
            items: [{ placeId: 'wagon-gate', layerId: 'mound-of-patroclus' }],
          },
        ],
      }),
    ).toThrow(/exactly one/);
  });

  it('rejects an item that names neither placeId nor layerId', () => {
    expect(() =>
      parsePlate({
        ...base,
        featureKey: [{ title: 'The camp and its wall', items: [{ label: 'The chariot gate' }] }],
      }),
    ).toThrow(/exactly one/);
  });

  it('rejects a layerId that is not a layer of this plate', () => {
    expect(() =>
      parsePlate({
        ...base,
        featureKey: [{ title: 'The camp and its wall', items: [{ layerId: 'no-such' }] }],
      }),
    ).toThrow(/layerId/);
  });

  it('rejects an id used twice across the key', () => {
    expect(() =>
      parsePlate({
        ...base,
        featureKey: [
          {
            title: 'The camp and its wall',
            items: [{ placeId: 'wagon-gate' }, { placeId: 'wagon-gate' }],
          },
        ],
      }),
    ).toThrow(/twice/);
  });
});

describe('parsePlate: suppressLayerLabels', () => {
  const base = {
    id: 'suppressed',
    title: 'Suppressed',
    kind: 'schematic' as const,
    status: 'draft',
    size: [400, 300] as [number, number],
    layers: [
      {
        id: 'ridge',
        kind: 'relief' as const,
        placeId: 'troy',
        polygon: [
          [0.1, 0.1],
          [0.3, 0.1],
          [0.3, 0.3],
          [0.1, 0.3],
        ],
      },
    ],
  };

  it('reads a well-formed suppressLayerLabels list', () => {
    const plate = parsePlate({ ...base, suppressLayerLabels: ['ridge'] });
    expect(plate.suppressLayerLabels).toEqual(['ridge']);
  });

  it('rejects an id that is not a layer of this plate', () => {
    expect(() => parsePlate({ ...base, suppressLayerLabels: ['no-such'] })).toThrow(/suppressLayerLabels/);
  });
});

describe('renderPlate: suppressLayerLabels (2026-09-02, stage 4b LOOK-gate fix)', () => {
  // A ground layer whose only name is its `placeId`'s gazetteer fallback
  // (see PlateLayer.label): the case a synced ground ridge is in on the
  // Trojan-plain schematic sheet -- `relief-troy-ridge`/`relief-sigeion-
  // ridge` carry `placeId: "troy"`/`"sigeion"` and no `label` of their own.
  function plateWith(suppressLayerLabels: string[] | undefined) {
    return parsePlate({
      id: 'suppressed-render',
      title: 'Suppressed render',
      kind: 'schematic',
      status: 'draft',
      size: [400, 300],
      layers: [
        {
          id: 'ridge',
          kind: 'relief',
          placeId: 'troy',
          polygon: [
            [0.1, 0.1],
            [0.3, 0.1],
            [0.3, 0.3],
            [0.1, 0.3],
          ],
        },
      ],
      suppressLayerLabels,
    });
  }
  const places = [{ id: 'troy', name: 'Troy' } as PlatePlace];

  it('without suppressLayerLabels, the ridge letters its placeId fallback name', () => {
    // A `relief` layer's label role is letterspaced caps (see LABEL_STYLES.region),
    // so the gazetteer name "Troy" prints as "TROY".
    const svg = renderPlate(plateWith(undefined), places).svg;
    expect(svg).toContain('>TROY<');
  });

  it('with the ridge listed, the fallback name is withheld', () => {
    const svg = renderPlate(plateWith(['ridge']), places).svg;
    expect(svg).not.toContain('>TROY<');
    expect(svg).not.toContain('plate-label-region');
  });

  it('an explicit layer.label survives suppressLayerLabels (only the fallback is withheld)', () => {
    const plate = parsePlate({
      id: 'suppressed-explicit',
      title: 'Suppressed explicit',
      kind: 'schematic',
      status: 'draft',
      size: [400, 300],
      layers: [
        {
          id: 'ridge',
          kind: 'relief',
          placeId: 'troy',
          label: 'Ilios',
          polygon: [
            [0.1, 0.1],
            [0.3, 0.1],
            [0.3, 0.3],
            [0.1, 0.3],
          ],
        },
      ],
      suppressLayerLabels: ['ridge'],
    });
    const svg = renderPlate(plate, places).svg;
    expect(svg).toContain('>ILIOS<');
  });
});

describe('legendMarkup: a right-margin band never folds into multiple columns (2026-09-02, stage 4b LOOK-gate fix)', () => {
  // Before this fix, the fold loop's width check was bounded by the FULL
  // SHEET width, not the band's own width -- a key with enough distinct
  // rows to want two columns folded even though the band itself (120px of
  // a 400px sheet) could not take a second column, and the swatch column
  // landed past the sheet's own right edge. Six distinct-fill region rows
  // plus a wall row are enough to make the old height check want to fold.
  const fills = ['sea', 'lagoon', 'marsh', 'plain', 'land', 'masonry'] as const;
  const bandPlate: Plate = {
    ...testPlate,
    bbox: undefined,
    marginRight: 120,
    layers: [
      ...fills.map((fill, i) => ({
        id: `region-${fill}`,
        kind: 'region' as const,
        fill,
        polygon: [
          [i * 0.1, 0],
          [i * 0.1 + 0.05, 0],
          [i * 0.1 + 0.05, 0.05],
          [i * 0.1, 0.05],
        ] as [number, number][],
      })),
      { id: 'wall-1', kind: 'wall' as const, trace: [[0, 0.5], [0.2, 0.6]] as [number, number][] },
    ],
  };

  it('lays every row out in a single column, clear of the sheet edge', () => {
    const svg = renderPlate(bandPlate, []).svg;
    const panelMatch = svg.match(/<rect class="plate-legend-panel" x="([-\d.]+)" y="[-\d.]+" width="([\d.]+)"/);
    expect(panelMatch).toBeTruthy();
    const panelRight = Number(panelMatch![1]) + Number(panelMatch![2]);
    expect(panelRight).toBeLessThanOrEqual(bandPlate.size[0]);

    // Single column: every legend row's own SWATCH (a wrapped row's <text>
    // has no x of its own -- only its <tspan> lines do -- but every row's
    // swatch rect/line always carries one) sits at the same x. A second
    // column would put half the rows at colX + colW + GAP instead.
    const legend = svg.match(/<g class="plate-legend">([\s\S]*?)<\/g>/)![1];
    const swatchXs = [...legend.matchAll(/<rect x="([-\d.]+)" y="[-\d.]+" width="22"/g)].map((m) => Number(m[1]));
    expect(swatchXs.length).toBe(fills.length); // one filled-region swatch per distinct fill
    expect(new Set(swatchXs).size).toBe(1);
  });
});

// ── Stage 5b: camp label declutter + wall/ditch/ship-rank geometry ─────────
//
// John's LOOK-gate verdict on the camp crop ("that's a mess"): six tier-1
// labels stacked on ~450px of beach; the wall traced the shared camp zone's
// own 37-vertex inland polygon edge instead of a line behind the sterns; the
// ship ranks crossed the shoreline. The fix: exactly one camp-wide name
// (`achaean-camp`) plus three sector names by holder (`station-of-achilles`,
// `station-of-odysseus`, `station-of-ajax`) at tier 1 — every individual
// feature (huts, the assembly, the wall-and-ditch pin) demoted to tier 2;
// the wall/ditch rebuilt as a landward offset from the rearmost ship rank,
// not the zone's own edge; every ship-rank vertex repositioned onto dry
// land.

function distToPolyline(p: [number, number], pts: [number, number][]): number {
  let best = Infinity;
  for (let i = 0; i < pts.length - 1; i++) best = Math.min(best, distToSegment(p, pts[i], pts[i + 1]));
  return best;
}

// Same convention shipRow() uses internally: n = (-uy, ux) turned 90° from
// the segment's own direction u. Verified against the live data (Python
// prototype, stage 5b) that +n is seaward and -n is landward for every one
// of the three camp shipRow baselines on this rotated (90°) sheet.
function segmentNormal(a: [number, number], b: [number, number]): [number, number] {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const len = Math.hypot(dx, dy);
  return [-dy / len, dx / len];
}

describe('renderPlate: camp label declutter (stage 5b)', () => {
  const raw = JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8'));
  const plate = parsePlate(raw);
  const allPlaces = JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[];
  const result = renderPlate(plate, allPlaces);

  function labelTag(id: string): string | undefined {
    const re = new RegExp(`<text[^>]*data-label-for="${id}"[^>]*>[\\s\\S]*?</text>`);
    return result.svg.match(re)?.[0];
  }

  // The three sector zones are `region`-role layer labels, centred on their
  // own polygon and lettered in caps (see LABEL_STYLES.region). `achaean-camp`
  // is deliberately NOT one of these: a `region` reading of the same shared
  // camp polygon was tried and withdrawn before this fix (see the "No id
  // overrides on a schematic sheet" comment in shared/lib/plate.ts) because
  // its centroid sits ON the ship/wall drawing it names, and — new finding,
  // this stage — on top of `station-of-odysseus`'s own centroid only 24px
  // away (both are "centred" requests; plate.ts's own label layout gives
  // centred area labels no collision check against each other, see the
  // Kesik-cut test above). So `achaean-camp` stays the place-level pin: a
  // small settlement-class dot+label at its own hand-placed `plateAnchors`
  // point, independent of any polygon centroid.
  const TIER1_SECTOR_LABELS: Record<string, string> = {
    'station-of-achilles': "Achilles' end",
    'station-of-odysseus': 'The center',
    'station-of-ajax': "Ajax's end",
  };

  // Stage 5c: sector captions leave the face (their labels are deleted; the
  // polygons still draw). The camp-wide pin stays; its name is the group
  // heading in the numbered key, not a map label.
  it('does not letter the three sector captions (Achilles, the center, Ajax)', () => {
    for (const id of Object.keys(TIER1_SECTOR_LABELS)) {
      expect(labelTag(id), `"${id}" must not emit a map label`).toBeUndefined();
    }
  });

  it('keeps the camp-wide pin but does not letter its name (the heading covers it)', () => {
    expect(result.svg).toMatch(/<g[^>]*data-place-id="achaean-camp"/);
    expect(labelTag('achaean-camp'), 'achaean-camp must not emit a map label').toBeUndefined();
  });

  const KEYED_CAMP_FEATURES = [
    'achaean-wall-and-ditch',
    'achaean-assembly-place',
    'hut-of-odysseus',
    'hut-of-ajax',
    'hut-of-achilles',
  ];

  it('does not letter the individual camp features that the numbered key now names', () => {
    for (const id of KEYED_CAMP_FEATURES) {
      expect(labelTag(id), `"${id}" is keyed, so it must not emit a map label`).toBeUndefined();
    }
  });
});

describe('renderPlate: camp wall, ditch and ship ranks sit on the beach (stage 5b)', () => {
  const raw = JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8'));
  const plate = parsePlate(raw);
  const frameWidth = plate.size[0] - (plate.marginRight ?? 0);
  const viewport = viewportFromBBox(plate.bbox!, [frameWidth, plate.size[1]], plate.rotationDeg);
  const layerById = new Map(plate.layers.map((l) => [l.id, l]));

  const SHIP_ROW_IDS = ['ships-achilles-end', 'ships-centre', 'ships-ajax-end'] as const;
  const SHIP_RANK_GAP = 1.55; // must track shipRow()'s own constant, shared/lib/plate.ts

  function rankLine(layer: PlateLayer): [number, number][][] {
    const [a, b] = (layer.baseline ?? []).map((p) => project(p, viewport)) as [number, number][];
    const [nx, ny] = segmentNormal(a, b);
    const length = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const slotWidth = length / (layer.count ?? 1);
    const baseHalfLen = Math.min(slotWidth, 32) * 0.46;
    const rankSpacing = baseHalfLen * SHIP_RANK_GAP;
    const rows = layer.rows ?? 1;
    const lines: [number, number][][] = [];
    for (let r = 0; r < rows; r++) {
      const off = r * rankSpacing;
      lines.push([
        [a[0] + nx * off, a[1] + ny * off],
        [b[0] + nx * off, b[1] + ny * off],
      ]);
    }
    return lines;
  }

  it('every ship-rank vertex (all three ranks, all three stations) lies outside sea-modern', () => {
    const sea = (layerById.get('sea-modern')!.polygon ?? []).map((p) => project(p, viewport)) as [number, number][];
    for (const lid of SHIP_ROW_IDS) {
      const ranks = rankLine(layerById.get(lid)!);
      ranks.forEach((rank, r) => {
        rank.forEach((pt) => {
          expect(inPolygon(pt, sea), `${lid} rank ${r} vertex ${JSON.stringify(pt)} sits in the sea`).toBe(
            false,
          );
        });
      });
    }
  });

  it('the seaward-most rank (last row) comes within 40m of the coast-modern shoreline', () => {
    const coastRings = (layerById.get('coast-modern')!.rings ?? []) as PlatePoint[][];
    const coastPx = coastRings.map((ring) => ring.map((p) => project(p, viewport)) as [number, number][]);
    const pxPerMetre = viewport.scale / 111320;
    for (const lid of SHIP_ROW_IDS) {
      const layer = layerById.get(lid)!;
      const ranks = rankLine(layer);
      const lastRank = ranks[ranks.length - 1];
      const dists = lastRank.map((pt) => Math.min(...coastPx.map((ring) => distToPolyline(pt, ring))) / pxPerMetre);
      expect(Math.min(...dists), `${lid}'s seaward rank never comes within 40m of the shore`).toBeLessThanOrEqual(40);
    }
  });

  it('the wall sits landward of the rearmost (row 0) ship rank, and the ditch landward of the wall', () => {
    const pxPerMetre = viewport.scale / 111320;
    // The three baselines, bridged end to end, stand in for "the beach line"
    // at rank-3 (row 0) depth — see shipRow()'s own comment: row 0, the
    // baseline itself, is the landward-most, first-hauled rank.
    const row0Line = SHIP_ROW_IDS.flatMap((lid) => {
      const [a, b] = (layerById.get(lid)!.baseline ?? []).map((p) => project(p, viewport)) as [number, number][];
      return [a, b];
    });

    function minLandwardOffset(tracePoints: [number, number][], ref: [number, number][]): number {
      let worst = Infinity;
      for (const pt of tracePoints) {
        // Nearest reference segment, then the signed perpendicular offset in
        // that segment's own local frame (+n = seaward, matching shipRow()).
        let bestD = Infinity;
        let bestSeg: [[number, number], [number, number]] | undefined;
        let bestClosest: [number, number] = pt;
        for (let i = 0; i < ref.length - 1; i++) {
          const a = ref[i];
          const b = ref[i + 1];
          const dx = b[0] - a[0];
          const dy = b[1] - a[1];
          const l2 = dx * dx + dy * dy;
          const t = l2 < 1e-9 ? 0 : Math.max(0, Math.min(1, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / l2));
          const closest: [number, number] = [a[0] + t * dx, a[1] + t * dy];
          const d = Math.hypot(pt[0] - closest[0], pt[1] - closest[1]);
          if (d < bestD) {
            bestD = d;
            bestSeg = [a, b];
            bestClosest = closest;
          }
        }
        const [nx, ny] = segmentNormal(bestSeg![0], bestSeg![1]);
        const vx = pt[0] - bestClosest[0];
        const vy = pt[1] - bestClosest[1];
        const landward = -(vx * nx + vy * ny) / pxPerMetre; // positive == landward
        worst = Math.min(worst, landward);
      }
      return worst;
    }

    const wallTrace = (layerById.get('achaean-wall')!.trace ?? []).map((p) => project(p, viewport)) as [
      number,
      number,
    ][];
    const ditchTrace = (layerById.get('achaean-ditch')!.trace ?? []).map((p) => project(p, viewport)) as [
      number,
      number,
    ][];

    const wallLandward = minLandwardOffset(wallTrace, row0Line);
    expect(wallLandward, 'every achaean-wall vertex must be landward of rank 3 (row 0)').toBeGreaterThan(0);

    const ditchLandward = minLandwardOffset(ditchTrace, wallTrace);
    expect(ditchLandward, 'every achaean-ditch vertex must be landward of achaean-wall').toBeGreaterThan(0);
  });

  it('the wall turns by no more than 25° between consecutive vertices', () => {
    const wallTrace = (layerById.get('achaean-wall')!.trace ?? []).map((p) => project(p, viewport)) as [
      number,
      number,
    ][];
    let maxTurn = 0;
    for (let i = 1; i < wallTrace.length - 1; i++) {
      const [ax, ay] = wallTrace[i - 1];
      const [bx, by] = wallTrace[i];
      const [cx, cy] = wallTrace[i + 1];
      const v1 = [bx - ax, by - ay];
      const v2 = [cx - bx, cy - by];
      const n1 = Math.hypot(v1[0], v1[1]);
      const n2 = Math.hypot(v2[0], v2[1]);
      if (n1 < 1e-6 || n2 < 1e-6) continue;
      const cos = Math.max(-1, Math.min(1, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)));
      maxTurn = Math.max(maxTurn, (Math.acos(cos) * 180) / Math.PI);
    }
    expect(maxTurn, `wall turning angle ${maxTurn.toFixed(1)}° exceeds the 25° smoothness bar`).toBeLessThanOrEqual(
      25,
    );
  });

  it('thins the three main shipRow layers to 8 glyphs per rank (three ranks kept, Il. 14.30-36)', () => {
    for (const lid of SHIP_ROW_IDS) {
      const layer = layerById.get(lid)!;
      expect(layer.count, `${lid} should carry 8 ships/rank`).toBe(8);
      expect(layer.rows, `${lid} keeps three ranks`).toBe(3);
    }
  });
});

// ── Stage 5c: Pope's numbered feature key ────────────────────────────────
// Design: build/stage5c-design.md §§ B, C, E1–E6, E9. Orchestrator: drop
// achaean-camp from the key (heading covers it) and suppress its map label;
// 32 items, contiguous 1…N.

const FEATURE_KEY_HEADINGS = [
  'The camp and its wall',
  "Achilles' end of the line",
  "Odysseus's ships, the assembly and altars",
  "Ajax's end of the line",
  'Inside the walls (see inset)',
  'Before the walls (see inset)',
  'The plain',
] as const;

// The zone letters as ruling 9 leaves them (John, 2026-09-03: "let's not have
// things overlap"). This fixture used to record the raw polygon centroids and
// was named ...BEFORE because it locked in a pure refactor — generalizing
// zoneLetterMarkup to badgeMarkup — as changing nothing. That refactor is
// still unchanged; what moved is the seats, and it had to: at the centroids F
// ("the walls of Troy") and G ("the circuit of the chase") were drawn at the
// SAME point, one letter invisible under the other, and four of the seven sat
// on a pin. The lock stays, on the placed positions.
//
// Moved once more on 2026-09-03, by the review's finding 2: D ("the fan before
// Troy") stood on the Bay of Troy, which ruling 5 forbids in the schematic
// register, so it falls through its own polygon to the nearest open DRY
// sample.
//
// A and B moved again the same day (ruling 9 round 3): `glyphBoxes` now
// counts an UNKEYED shipRow as an obstacle too (see the comment on
// `glyphBoxes` in plate.ts), and both letters' old spots sat over one of the
// Achaean camp's three ship-row blocks, which nothing had ever told the zone
// letter pass about before. C through G are unmoved.
//
// Re-recorded 2026-09-03 for the citadel inset (ruling 10): the sheet is
// larger — 1756x1600, the map face 1416 wide, so the margin can carry a
// second inset — and every seat moved with it. The map face's aspect is
// unchanged (frameWidth/height still matches the bbox's own), so this is one
// uniform enlargement of the same solution, not a re-solve.
//
// Re-recorded again 2026-09-03 by the merge of the citadel-inset and
// badge-no-overlap lanes: this sheet now carries BOTH the wider
// `markGlyphBoxes` obstacle set (every tumulus/shipRow layer, keyed or not)
// AND the citadel inset panels, so all seven seats were recomputed fresh
// against the merged geometry rather than assembled from either side's
// recorded numbers. A, F and G moved from both sides' prior recordings; B, C,
// D and E landed back on the same seats either side had already recorded.
const ZONE_LETTER_MARKUP: readonly string[] = [
  '<g class="plate-zone-letter"><circle cx="762" cy="1166.9" r="7.6" fill="var(--scene-map-label-halo)" fill-opacity="0.86" stroke="var(--text-mid)" stroke-width="0.7"/><text class="plate-zone-letter" x="762" y="1166.9" text-anchor="middle" dominant-baseline="central" font-family="var(--font-ui)" font-size="9.5" font-weight="600" fill="var(--text-mid)" paint-order="stroke" stroke="var(--scene-map-label-halo)" stroke-width="0.65" stroke-linejoin="round">A</text></g>',
  '<g class="plate-zone-letter"><circle cx="739" cy="1169.1" r="7.6" fill="var(--scene-map-label-halo)" fill-opacity="0.86" stroke="var(--text-mid)" stroke-width="0.7"/><text class="plate-zone-letter" x="739" y="1169.1" text-anchor="middle" dominant-baseline="central" font-family="var(--font-ui)" font-size="9.5" font-weight="600" fill="var(--text-mid)" paint-order="stroke" stroke="var(--scene-map-label-halo)" stroke-width="0.65" stroke-linejoin="round">B</text></g>',
  '<g class="plate-zone-letter"><circle cx="708.9" cy="1060.6" r="7.6" fill="var(--scene-map-label-halo)" fill-opacity="0.86" stroke="var(--text-mid)" stroke-width="0.7"/><text class="plate-zone-letter" x="708.9" y="1060.6" text-anchor="middle" dominant-baseline="central" font-family="var(--font-ui)" font-size="9.5" font-weight="600" fill="var(--text-mid)" paint-order="stroke" stroke="var(--scene-map-label-halo)" stroke-width="0.65" stroke-linejoin="round">C</text></g>',
  '<g class="plate-zone-letter"><circle cx="734.2" cy="880.8" r="7.6" fill="var(--scene-map-label-halo)" fill-opacity="0.86" stroke="var(--text-mid)" stroke-width="0.7"/><text class="plate-zone-letter" x="734.2" y="880.8" text-anchor="middle" dominant-baseline="central" font-family="var(--font-ui)" font-size="9.5" font-weight="600" fill="var(--text-mid)" paint-order="stroke" stroke="var(--scene-map-label-halo)" stroke-width="0.65" stroke-linejoin="round">D</text></g>',
  '<g class="plate-zone-letter"><circle cx="654.9" cy="972.1" r="7.6" fill="var(--scene-map-label-halo)" fill-opacity="0.86" stroke="var(--text-mid)" stroke-width="0.7"/><text class="plate-zone-letter" x="654.9" y="972.1" text-anchor="middle" dominant-baseline="central" font-family="var(--font-ui)" font-size="9.5" font-weight="600" fill="var(--text-mid)" paint-order="stroke" stroke="var(--scene-map-label-halo)" stroke-width="0.65" stroke-linejoin="round">E</text></g>',
  '<g class="plate-zone-letter"><circle cx="673.9" cy="796.1" r="7.6" fill="var(--scene-map-label-halo)" fill-opacity="0.86" stroke="var(--text-mid)" stroke-width="0.7"/><text class="plate-zone-letter" x="673.9" y="796.1" text-anchor="middle" dominant-baseline="central" font-family="var(--font-ui)" font-size="9.5" font-weight="600" fill="var(--text-mid)" paint-order="stroke" stroke="var(--scene-map-label-halo)" stroke-width="0.65" stroke-linejoin="round">F</text></g>',
  '<g class="plate-zone-letter"><circle cx="674.7" cy="816.2" r="7.6" fill="var(--scene-map-label-halo)" fill-opacity="0.86" stroke="var(--text-mid)" stroke-width="0.7"/><text class="plate-zone-letter" x="674.7" y="816.2" text-anchor="middle" dominant-baseline="central" font-family="var(--font-ui)" font-size="9.5" font-weight="600" fill="var(--text-mid)" paint-order="stroke" stroke="var(--scene-map-label-halo)" stroke-width="0.65" stroke-linejoin="round">G</text></g>',
];

function boxesIntersect(a: [number, number, number, number], b: [number, number, number, number]): boolean {
  return !(a[2] < b[0] || b[2] < a[0] || a[3] < b[1] || b[3] < a[1]);
}

function textLabelIds(svg: string): Set<string> {
  return new Set([...svg.matchAll(/<text[^>]*data-label-for="([^"]+)"/g)].map((m) => m[1]));
}

// ── Ruling 9's machine check (John, 2026-09-03: "let's not have things
// overlap") ────────────────────────────────────────────────────────────────
// Read back off the RENDERED SVG, not off the placer's own bookkeeping: the
// ruling gates on what the sheet actually draws. Four claims, one per class of
// collision John's circle covered — a numeral badge or zone letter on another
// disc, a badge on someone else's pin, a leader through a disc it does not
// belong to or through a pin, and two leaders crossing.
interface MarkDisc {
  label: string;
  id: string;
  cx: number;
  cy: number;
  r: number;
}
interface MarkSeg {
  label: string;
  n: string;
  ax: number;
  ay: number;
  bx: number;
  by: number;
}

function markDiscs(svg: string, className: string): MarkDisc[] {
  const out: MarkDisc[] = [];
  const re = new RegExp(`<g class="${className}"([^>]*)>([\\s\\S]*?)<\\/g>`, 'g');
  for (const m of svg.matchAll(re)) {
    const circle = m[2].match(/<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([-\d.]+)"/);
    if (!circle) continue;
    const id = m[1].match(/data-place-id="([^"]+)"/)?.[1] ?? m[1].match(/data-layer-id="([^"]+)"/)?.[1] ?? '';
    const n = m[1].match(/data-key-n="(\d+)"/)?.[1];
    const letter = m[2].match(/>([^<]*)<\/text>/)?.[1] ?? '';
    out.push({
      label: n ? `badge ${n} (${id})` : `zone letter ${letter}`,
      id,
      cx: Number(circle[1]),
      cy: Number(circle[2]),
      r: Number(circle[3]),
    });
  }
  return out;
}

/**
 * The drawn pin/dot marks: a `<g data-place-id>` that is NOT one of the badge
 * groups. Keyed off the two badge class names rather than off "carries no
 * class at all" (the 2026-09-03 review's finding 1): a pin group that ever
 * gains a class of its own would have gone silently invisible to this check.
 */
function markPins(svg: string): { id: string; box: [number, number, number, number] }[] {
  const out: { id: string; box: [number, number, number, number] }[] = [];
  for (const m of svg.matchAll(
    /<g (?![^>]*class="plate-(?:key-badge|zone-letter)")[^>]*data-place-id="([^"]+)"[^>]*>([\s\S]*?)<\/g>/g,
  )) {
    const circle = m[2].match(/<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([-\d.]+)"/);
    const rect = m[2].match(/<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"/);
    if (circle) {
      const [x, y, r] = [Number(circle[1]), Number(circle[2]), Number(circle[3])];
      out.push({ id: m[1], box: [x - r, y - r, x + r, y + r] });
    } else if (rect) {
      const [x, y, w, h] = [Number(rect[1]), Number(rect[2]), Number(rect[3]), Number(rect[4])];
      out.push({ id: m[1], box: [x, y, x + w, y + h] });
    }
  }
  return out;
}

// ── The rest of what the sheet actually draws (2026-09-03 review, finding 1)
// The first cut of this check saw four classes of ink — badge discs, zone
// letters, key leaders, place pins — and nothing else, so it passed a sheet
// green while four leaders ran through the word "Ilios" and badge 32 sat on
// the Callicolone mound it was pointing at. Everything below is read off the
// SAME rendered SVG; the plate is consulted only to say WHICH drawn feature
// is water and which is keyed, never for a position.

/** Every coordinate pair in a path `d`, in order — the drawn geometry itself. */
function pathPoints(d: string): [number, number][] {
  return [...d.matchAll(/(-?\d+(?:\.\d+)?)[ ,](-?\d+(?:\.\d+)?)/g)].map(
    (m) => [Number(m[1]), Number(m[2])] as [number, number],
  );
}

/** Every `<path data-feature-id="id" class="plate-layer …">` drawn for one layer. */
function layerPaths(svg: string, layerId: string): [number, number][][] {
  const re = new RegExp(
    `<path data-feature-id="${layerId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}" class="plate-layer[^"]*" d="([^"]+)"`,
    'g',
  );
  // A `d` may hold several subpaths; each `M` starts a new ring.
  return [...svg.matchAll(re)].flatMap((m) =>
    m[1]
      .split('M')
      .map((chunk) => pathPoints(chunk))
      .filter((ring) => ring.length >= 3),
  );
}

const WATER_FILL_NAMES = new Set(['sea', 'lagoon']);

/** The drawn water bodies (ruling 5's register), as rings in plate pixels. */
function markWaterRings(svg: string, plate: Plate): { id: string; ring: [number, number][] }[] {
  const out: { id: string; ring: [number, number][] }[] = [];
  for (const layer of plate.layers) {
    if (layer.style === 'inset') continue;
    const fill = layer.fill ?? (layer.kind === 'region' || layer.kind === 'band' ? 'plain' : undefined);
    if (fill === undefined || !WATER_FILL_NAMES.has(fill)) continue;
    for (const ring of layerPaths(svg, layer.id)) out.push({ id: layer.id, ring });
  }
  return out;
}

function pointInRing(ring: [number, number][], px: number, py: number): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > py !== yj > py && px < ((xj - xi) * (py - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function discHitsRing(ring: [number, number][], cx: number, cy: number, r: number): boolean {
  if (pointInRing(ring, cx, cy)) return true;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const seg: MarkSeg = { label: '', n: '', ax: ring[j][0], ay: ring[j][1], bx: ring[i][0], by: ring[i][1] };
    if (pointSegDistance(cx, cy, seg) < r) return true;
  }
  return false;
}

/**
 * The painted extent of a layer-drawn GLYPH — a tumulus mound, a row of
 * beached ships. `drawnMarkBoxes` in plate.ts only ever held place DOTS, so
 * these had no obstacle at all: badge 32 was drawn across the Callicolone
 * mound, which is the one thing on the sheet it exists to point at. `owner`
 * is the keyed id the glyph belongs to, when it has one; its own leader
 * starts inside the glyph and is exempt, its own disc is not.
 *
 * Widened (2026-09-03, ruling 9 round 3, Grok's independent collision count):
 * this used to require `owner` — a numbered key item naming the glyph — before
 * counting it as an obstacle at all, which is right for the EXEMPTION but
 * wrong for the obstacle itself: the Achaean camp draws three `shipRow` ranks
 * under one heading, with no item keying any single one, so all three were
 * invisible here and badges 3, 6 and 7 were drawn straight across them (a
 * leader crossed a fourth). Every layer of a glyph kind is now an obstacle
 * whether or not anything keys it; `owner` stays `undefined` for the unkeyed
 * ones, which correctly grants no badge an exemption from them.
 *
 * Only the compact kinds. A wall or a route is keyed too, but its ink is a
 * corridor running the length of the sheet, and its own numeral has to sit
 * somewhere along it — a bounding box there would be a reservation over
 * ground the badge is entitled to (see `markWallLines` below for how a wall's
 * corridor is checked instead).
 */
const GLYPH_LAYER_KINDS = new Set(['tumulus', 'shipRow']);

function markGlyphBoxes(svg: string, plate: Plate): { id: string; owner?: string; box: [number, number, number, number] }[] {
  const keyed = new Set<string>();
  for (const group of plate.featureKey ?? []) {
    for (const item of group.items) {
      const id = item.placeId ?? item.layerId;
      if (id) keyed.add(id);
    }
  }
  const out: { id: string; owner?: string; box: [number, number, number, number] }[] = [];
  for (const layer of plate.layers) {
    if (layer.style === 'inset' || !GLYPH_LAYER_KINDS.has(layer.kind)) continue;
    const owner = [layer.id, layer.placeId, ...(layer.claims ?? [])].find(
      (id): id is string => !!id && keyed.has(id),
    );
    // `${id}--inset` is renderPlate's second drawing of a layer that carries
    // `insetOf` (ruling 10). It is ink on the sheet like any other, and the
    // numerals inside the panel must keep off it.
    for (const id of [layer.id, ...(layer.insetOf ? [`${layer.id}--inset`] : [])]) {
      const pts = layerPaths(svg, id).flat();
      if (!pts.length) continue;
      const xs = pts.map((p) => p[0]);
      const ys = pts.map((p) => p[1]);
      out.push({ id, owner, box: [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)] });
    }
  }
  return out;
}

/**
 * The Achaean wall's (and any other wall's) own drawn INK, checked as a
 * polyline rather than a bounding box — see the comment on `GLYPH_LAYER_KINDS`
 * above for why a wall cannot be treated as a compact glyph. Read off the
 * SAME rendered centreline the renderer draws (`plate-layer-wall` /
 * `plate-layer-wall-restored(-line)?`), with the clearance measured by
 * `wallInkHalfWidth` — plate.ts's own real INK extent for this exact layer,
 * NOT `lineworkReserveHalfWidth`'s wider name-reservation corridor (2026-09-03,
 * ruling 9 round 4: that wider, symmetric half-width called a disc 9.19px
 * from the achaean-wall centreline — clear of even the 4.375px tick band, on
 * the side with no tick at all — an offender).
 *
 * This is VERIFICATION, not a SEPARATE obstacle the placer enforces on its
 * own terms: `renderPlate` now gives a wall's own ink (this same extent) as a
 * HARD obstacle for numeral badges and zone-letter discs (ruling 9 round 4;
 * round 3's attempt, at the wider reserve half-width and lineworkExtent's
 * axis-aligned boxes, stranded badges and doubled the cold render — the boxes
 * over-reach on a shallow diagonal leg, which is the same defect that made
 * the wide half-width flag badge 5 here). This function exists so a FUTURE
 * regression — some other change putting a badge back on a wall — is still
 * caught, at the SAME extent the placer now protects.
 */
function markWallLines(
  svg: string,
  plate: Plate,
): { id: string; owner?: string; side: 1 | -1; halfWidths: [number, number]; points: [number, number][] }[] {
  const keyed = new Set<string>();
  for (const group of plate.featureKey ?? []) {
    for (const item of group.items) {
      const id = item.placeId ?? item.layerId;
      if (id) keyed.add(id);
    }
  }
  const out: { id: string; owner?: string; side: 1 | -1; halfWidths: [number, number]; points: [number, number][] }[] =
    [];
  for (const layer of plate.layers) {
    if (layer.style === 'inset' || layer.kind !== 'wall') continue;
    const halfWidths = wallInkHalfWidth(layer);
    if (halfWidths === undefined) continue;
    const re = new RegExp(
      `<path data-feature-id="${layer.id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}" class="plate-layer plate-layer-wall(?:-restored(?:-line)?)?"[^>]*\\sd="([^"]+)"`,
    );
    const m = svg.match(re);
    if (!m) continue;
    const points = pathPoints(m[1]);
    if (points.length < 2) continue;
    const owner = [layer.id, layer.placeId, ...(layer.claims ?? [])].find(
      (id): id is string => !!id && keyed.has(id),
    );
    out.push({ id: layer.id, owner, side: traceSide(points), halfWidths, points });
  }
  return out;
}

/**
 * The placed NAME boxes. Which names the sheet actually prints is read off the
 * SVG (`data-label-for`); their rects come from `PlateResult.labelBoxes`,
 * which the module documents as the only honest source of a laid label's
 * width — a `<text>` element carries no measured extent.
 */
function markNameBoxes(svg: string, result: { labelBoxes: Record<string, [number, number, number, number]> }) {
  const out: { id: string; box: [number, number, number, number] }[] = [];
  for (const id of textLabelIds(svg)) {
    const box = result.labelBoxes[id];
    if (box) out.push({ id, box });
  }
  return out;
}

/** Sheet furniture drawn over the map face: the panels, and the north arrow. */
function markFurnitureBoxes(
  svg: string,
): { id: string; kind: string; box: [number, number, number, number] }[] {
  const out: { id: string; kind: string; box: [number, number, number, number] }[] = [];
  const re =
    /<rect(?: data-feature-id="([^"]*)")? class="(?:plate-layer )?(plate-legend-panel|plate-scale-panel|plate-hypsometric-panel|plate-layer-inset-panel)"[^>]*x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"/g;
  for (const m of svg.matchAll(re)) {
    const [x, y, w, h] = [Number(m[3]), Number(m[4]), Number(m[5]), Number(m[6])];
    out.push({ id: m[1] || m[2], kind: m[2], box: [x, y, x + w, y + h] });
  }
  // Fixed (2026-09-03, ruling 9 round 3, Grok finding 2): the schematic
  // sheet's needle is rotated, so its markup nests one `<g transform>` inside
  // `<g class="plate-north">` — `<g class="plate-north"><g transform>…</g>
  // <text>…</text><text>…</text></g>` — and the old regex, which wanted TWO
  // `</g>` immediately back to back, never matched that (or the unrotated
  // form, which has only one `</g>` total). Matched instead up through the
  // caption `<text>`'s own close, which every north-arrow markup — rotated or
  // not — always emits right before the ONE `</g>` that closes `plate-north`.
  const north = svg.match(
    /<g class="plate-north">([\s\S]*?<text class="plate-north-caption"[^>]*>[\s\S]*?<\/text>)<\/g>/,
  );
  if (north) {
    const pts = [...north[1].matchAll(/ d="([^"]+)"/g)].flatMap((m) => pathPoints(m[1]));
    if (pts.length) {
      const xs = pts.map((p) => p[0]);
      const ys = pts.map((p) => p[1]);
      out.push({
        id: 'north arrow',
        kind: 'plate-north',
        box: [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)],
      });
    }
  }
  return out;
}

function markKeyLeaders(svg: string): MarkSeg[] {
  const re = /<path class="plate-key-leader" data-key-n="(\d+)" d="M ([-\d.]+) ([-\d.]+) L ([-\d.]+) ([-\d.]+)"/g;
  return [...svg.matchAll(re)].map((m) => ({
    label: `leader ${m[1]}`,
    n: m[1],
    ax: Number(m[2]),
    ay: Number(m[3]),
    bx: Number(m[4]),
    by: Number(m[5]),
  }));
}

function pointSegDistance(px: number, py: number, s: MarkSeg): number {
  const dx = s.bx - s.ax;
  const dy = s.by - s.ay;
  const len2 = dx * dx + dy * dy;
  const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, ((px - s.ax) * dx + (py - s.ay) * dy) / len2));
  return Math.hypot(px - (s.ax + t * dx), py - (s.ay + t * dy));
}

/** Liang–Barsky: does the segment enter the axis-aligned box at all? */
function segmentHitsBox(s: MarkSeg, box: [number, number, number, number]): boolean {
  let t0 = 0;
  let t1 = 1;
  const dx = s.bx - s.ax;
  const dy = s.by - s.ay;
  const p = [-dx, dx, -dy, dy];
  const q = [s.ax - box[0], box[2] - s.ax, s.ay - box[1], box[3] - s.ay];
  for (let i = 0; i < 4; i++) {
    if (p[i] === 0) {
      if (q[i] < 0) return false;
    } else {
      const t = q[i] / p[i];
      if (p[i] < 0) t0 = Math.max(t0, t);
      else t1 = Math.min(t1, t);
    }
  }
  return t0 <= t1;
}

/**
 * How far outside a box the origin of a leader may lie and still count as
 * starting INSIDE it (see the exemptions below). It exists so this check and
 * the placer agree: the placer tests its leaders against every obstacle grown
 * by BADGE_CLEARANCE (0.4px, chosen to survive the 0.1px the emitted path
 * rounds to) and exempts an origin inside that grown box, while this check
 * tests the box as drawn. Without the same tolerance here, a mark 0.14px
 * outside a name box would be exempt to the placer and an offender here, and
 * no seat on the sheet could satisfy both.
 */
const LEADER_ORIGIN_TOLERANCE = 0.5;

function originInside(s: MarkSeg, box: [number, number, number, number]): boolean {
  const t = LEADER_ORIGIN_TOLERANCE;
  return s.ax >= box[0] - t && s.ax <= box[2] + t && s.ay >= box[1] - t && s.ay <= box[3] + t;
}

function segmentsCross(a: MarkSeg, b: MarkSeg): boolean {
  const side = (px: number, py: number, qx: number, qy: number, rx: number, ry: number) =>
    (qx - px) * (ry - py) - (qy - py) * (rx - px);
  const d1 = side(a.ax, a.ay, a.bx, a.by, b.ax, b.ay);
  const d2 = side(a.ax, a.ay, a.bx, a.by, b.bx, b.by);
  const d3 = side(b.ax, b.ay, b.bx, b.by, a.ax, a.ay);
  const d4 = side(b.ax, b.ay, b.bx, b.by, a.bx, a.by);
  return d1 > 0 !== d2 > 0 && d3 > 0 !== d4 > 0;
}

/** Every ruling-9 violation on a rendered sheet, named. Empty means the sheet is clean. */
function badgeOverlapOffenders(
  svg: string,
  plate: Plate,
  result: { labelBoxes: Record<string, [number, number, number, number]> },
): string[] {
  const numerals = markDiscs(svg, 'plate-key-badge');
  const zones = markDiscs(svg, 'plate-zone-letter');
  const discs = [...numerals, ...zones];
  const pins = markPins(svg);
  const leaders = markKeyLeaders(svg);
  // Ruling 5: the no-label-on-water rule binds the SCHEMATIC register only —
  // a geographic sheet sets coastal names over water with a leader by design.
  const water = plate.kind === 'schematic' ? markWaterRings(svg, plate) : [];
  const glyphs = markGlyphBoxes(svg, plate);
  const names = markNameBoxes(svg, result);
  const furniture = markFurnitureBoxes(svg);
  const discByN = new Map(
    numerals.map((d) => [d.label.slice('badge '.length, d.label.indexOf(' (')), d] as const),
  );
  const offenders: string[] = [];

  for (let i = 0; i < discs.length; i++) {
    for (let j = i + 1; j < discs.length; j++) {
      const gap = Math.hypot(discs[i].cx - discs[j].cx, discs[i].cy - discs[j].cy) - discs[i].r - discs[j].r;
      if (gap < 0) offenders.push(`disc/disc: ${discs[i].label} overlaps ${discs[j].label}`);
    }
  }
  for (const disc of discs) {
    for (const pin of pins) {
      if (pin.id === disc.id) continue; // its own mark: a badge may sit on the pin it numbers
      const nx = Math.max(pin.box[0], Math.min(disc.cx, pin.box[2]));
      const ny = Math.max(pin.box[1], Math.min(disc.cy, pin.box[3]));
      if (Math.hypot(disc.cx - nx, disc.cy - ny) < disc.r) {
        offenders.push(`disc/pin: ${disc.label} sits on pin ${pin.id}`);
      }
    }
  }
  for (const leader of leaders) {
    const own = discByN.get(leader.n);
    for (const disc of discs) {
      if (own && disc === own) continue; // the leader ends ON its own badge, by construction
      if (pointSegDistance(disc.cx, disc.cy, leader) < disc.r) {
        offenders.push(`leader/disc: ${leader.label} crosses ${disc.label}`);
      }
    }
    for (const pin of pins) {
      if (own && pin.id === own.id) continue; // it starts at its own mark
      // A mark the leader BEGINS inside. Eight pairs of dots on the schematic
      // sheet physically overlap — the citadel puts eleven inside 25px, closer
      // than their own radius — so a leader out of one starts inside its
      // neighbour whichever way it goes. Ruling 9 forbids a leader CROSSING a
      // pin; a line whose origin is already in there is not crossing the sheet
      // to reach it, and no placement could avoid it. The marks sitting on
      // each other is its own defect, in the poem's own positions, and the
      // placer has no business moving those.
      if (originInside(leader, pin.box)) continue;
      if (segmentHitsBox(leader, pin.box)) offenders.push(`leader/pin: ${leader.label} crosses pin ${pin.id}`);
    }
  }
  for (let i = 0; i < leaders.length; i++) {
    for (let j = i + 1; j < leaders.length; j++) {
      if (segmentsCross(leaders[i], leaders[j])) {
        offenders.push(`leader/leader: ${leaders[i].label} crosses ${leaders[j].label}`);
      }
    }
  }

  // Water (schematic register only). A numeral on the bay asserts a feature
  // where there is open sea, which is exactly the false claim the name solver
  // already refuses to make (ruling 5, 2026-09-02). A LEADER may cross water —
  // it draws no claim, it only points — so only the discs are checked, and the
  // badge disc IS its leader's far end.
  for (const disc of discs) {
    for (const body of water) {
      if (discHitsRing(body.ring, disc.cx, disc.cy, disc.r)) {
        offenders.push(`disc/water: ${disc.label} sits on ${body.id}`);
      }
    }
  }

  // Layer-drawn glyphs. A badge over the mound it numbers hides the mound.
  for (const glyph of glyphs) {
    for (const disc of discs) {
      if (boxesIntersect([disc.cx - disc.r, disc.cy - disc.r, disc.cx + disc.r, disc.cy + disc.r], glyph.box)) {
        offenders.push(`disc/glyph: ${disc.label} covers glyph ${glyph.id}`);
      }
    }
    for (const leader of leaders) {
      // Same exemption the pins get: a leader whose origin is already inside
      // the ink is not crossing the sheet to reach it. That is how a keyed
      // glyph's OWN numeral still gets a line back to its mound.
      if (originInside(leader, glyph.box)) continue;
      if (segmentHitsBox(leader, glyph.box)) offenders.push(`leader/glyph: ${leader.label} crosses glyph ${glyph.id}`);
    }
  }

  // Wall ink (2026-09-03, ruling 9 round 4; originally round 3, Grok finding
  // 1): a VERIFICATION check, and now one that agrees BY CONSTRUCTION with
  // what the placer enforces — see `markWallLines`'s own comment. Checked as
  // a true point-to-segment distance against each leg (`discClearsWallInk`),
  // at the SAME per-side half-widths `wallInkHalfWidth` computes for this
  // exact layer — never `lineworkExtent`'s axis-aligned boxes, which
  // over-reach on a shallow diagonal leg (that is what made the wide,
  // symmetric `lineworkReserveHalfWidth` flag a disc 9.19px from the
  // centreline, comfortably clear of the ink, as round 3's regression here).
  // Numerals only — a zone letter has no leader and this check exists for the
  // disc Grok found sitting on the stroke, not to extend zone-letter
  // coverage (the placer itself does keep zone letters off a wall's ink; see
  // renderPlate). The wall's own numeral is exempt from its own line; every
  // other numeral is not.
  const wallLines = markWallLines(svg, plate);
  // 2026-09-03, ruling 9 round 3 review: the guard once parsed zero walls
  // (its regex took the id= inside data-layer-id for the d= attribute) and
  // passed vacuously. A sheet that draws a wall must yield at least one.
  if (plate.layers.some((l) => l.kind === 'wall' && l.style !== 'inset')) expect(wallLines.length).toBeGreaterThan(0);
  for (const wall of wallLines) {
    for (const disc of numerals) {
      if (wall.owner && disc.id === wall.owner) continue;
      if (!discClearsWallInk(wall.points, wall.side, wall.halfWidths, disc.cx, disc.cy, disc.r)) {
        offenders.push(`disc/wall: ${disc.label} sits on wall ${wall.id}`);
      }
    }
    // Leaders are NOT checked against walls (2026-09-03, round 3 review):
    // ruling 9 forbids a leader crossing a badge, a pin or another leader,
    // not linework — leaders cross roads and contours everywhere, and the
    // citadel's gates sit ON the wall ring, so their leaders must cross it
    // to reach any seat. Once the regex above actually parsed walls, a
    // leader clause here named eighteen such crossings; it was a wrong claim.
  }

  // Placed names and sheet furniture. A name's position carries meaning and
  // cannot move; the numeral's carries none, so the numeral is what yields.
  // An inset panel is a sheet within the sheet (ruling 10): the numerals of a
  // featureKey group routed into one are drawn INSIDE it, and a mark wholly
  // within a panel is a mark ON that panel's own little map, not a mark
  // fouling a piece of furniture. Anything sticking out is still an offender,
  // which is the check that matters — the ladder must not walk a numeral
  // through the frame.
  const insetPanel = (target: { kind: string }) => target.kind === 'plate-layer-inset-panel';
  const inside = (box: [number, number, number, number], outer: [number, number, number, number]) =>
    box[0] >= outer[0] && box[1] >= outer[1] && box[2] <= outer[2] && box[3] <= outer[3];
  for (const target of [...names.map((n) => ({ ...n, kind: 'name' })), ...furniture]) {
    for (const disc of discs) {
      const discBox: [number, number, number, number] = [
        disc.cx - disc.r,
        disc.cy - disc.r,
        disc.cx + disc.r,
        disc.cy + disc.r,
      ];
      if (insetPanel(target) && inside(discBox, target.box)) continue;
      if (boxesIntersect(discBox, target.box)) {
        offenders.push(`disc/name: ${disc.label} overlaps ${target.id}`);
      }
    }
    for (const leader of leaders) {
      if (originInside(leader, target.box)) continue;
      if (
        insetPanel(target) &&
        inside([leader.ax, leader.ay, leader.ax, leader.ay], target.box) &&
        inside([leader.bx, leader.by, leader.bx, leader.by], target.box)
      ) {
        continue;
      }
      if (segmentHitsBox(leader, target.box)) offenders.push(`leader/name: ${leader.label} crosses ${target.id}`);
    }
  }
  return offenders;
}

// The citadel panel's GROUND, and the checks that keep it honest. Ruling 12
// (John, 2026-09-03: "the citadel insert is too coarse grained") replaced the
// derived poem ring — a circle got by dividing `wall-of-troy` by the 55% its
// own note declares — with the surveyed thing itself: Dörpfeld's Troy VI
// circuit off Tafel V, ported from troy-citadel.json at that plate's own
// pxPerMetre and laid on the sheet's own centre for Ilios. A survey has a size
// and a shape, and both are assertable; the three gate anchors then have to
// land ON it, or the panel draws a gate floating off its wall.
describe('the citadel inset draws the surveyed Troy VI circuit', () => {
  const plate = parsePlate(JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8')));
  const places = JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[];
  const CENTRE: [number, number] = [39.957, 26.239];
  const cos = Math.cos((CENTRE[0] * Math.PI) / 180);
  const METRES_PER_DEG_LAT = 111320;
  const radius = ([lat, lon]: [number, number]) => Math.hypot(lat - CENTRE[0], (lon - CENTRE[1]) * cos);
  const meanRadius = (pts: [number, number][]) => pts.reduce((a, p) => a + radius(p), 0) / pts.length;
  const trace = (id: string) => plate.layers.find((l) => l.id === id)!.trace as [number, number][];
  // Every vertex the panel draws for the circuit: the four surveyed arcs, plus
  // the north/north-west stretch Dörpfeld restored and never surveyed.
  const circuit: [number, number][] = [
    'citadel-circuit-west',
    'citadel-circuit-south',
    'citadel-circuit-southeast-east',
    'citadel-circuit-northeast',
  ]
    .flatMap((id) => plate.layers.find((l) => l.id === id)!.polygon as [number, number][])
    .concat(trace('citadel-circuit-restored'));

  it('is Dörpfeld’s circuit at Tafel V’s own scale — about 191 by 168 m', () => {
    const lats = circuit.map((p) => p[0]);
    const lons = circuit.map((p) => p[1]);
    const northSouth = (Math.max(...lats) - Math.min(...lats)) * METRES_PER_DEG_LAT;
    const eastWest = (Math.max(...lons) - Math.min(...lons)) * METRES_PER_DEG_LAT * cos;
    expect(northSouth).toBeGreaterThan(160);
    expect(northSouth).toBeLessThan(180);
    expect(eastWest).toBeGreaterThan(182);
    expect(eastWest).toBeLessThan(200);
    // A polygon of straight stretches, not a ring: Dörpfeld 1902, 2:611. The
    // old derived circle had a constant radius; this one does not.
    const radii = circuit.map((p) => radius(p) * METRES_PER_DEG_LAT);
    expect(Math.max(...radii) - Math.min(...radii)).toBeGreaterThan(20);
  });

  it('puts the Scaean Gate, the great tower and the Dardanian Gates on the line', () => {
    for (const id of ['scaean-gate', 'great-tower-of-ilios', 'dardanian-gates']) {
      const anchor = places.find((p) => p.id === id)!.plateAnchors!['trojan-plain-schematic'] as [number, number];
      const off =
        Math.min(...circuit.map((p) => Math.hypot(p[0] - anchor[0], (p[1] - anchor[1]) * cos))) * METRES_PER_DEG_LAT;
      expect(off, `${id} is ${off.toFixed(1)} m off the drawn circuit`).toBeLessThan(10);
    }
  });

  it('would have put all three inside the wall the map face draws', () => {
    const drawn = meanRadius(trace('wall-of-troy')) * METRES_PER_DEG_LAT;
    for (const id of ['scaean-gate', 'great-tower-of-ilios', 'dardanian-gates']) {
      const anchor = places.find((p) => p.id === id)!.plateAnchors!['trojan-plain-schematic'] as [number, number];
      expect(radius(anchor) * METRES_PER_DEG_LAT).toBeLessThan(drawn);
    }
  });
});

describe('renderPlate: featureKey (stage 5c)', () => {
  const raw = JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8'));
  const plate = parsePlate(raw);
  const allPlaces = JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[];
  const result = renderPlate(plate, allPlaces);
  const groups = plate.featureKey ?? [];
  const keyedItems = groups.flatMap((g) => g.items);
  const keyedIds = new Set(keyedItems.map((item) => item.placeId ?? item.layerId).filter((id): id is string => !!id));
  const keyedPlaceIds = new Set(keyedItems.map((item) => item.placeId).filter((id): id is string => !!id));
  const keyedLayerIds = new Set(keyedItems.map((item) => item.layerId).filter((id): id is string => !!id));
  const coveredByKeyedLayer = new Set(
    plate.layers
      .filter((l) => keyedLayerIds.has(l.id))
      .flatMap((l) => [l.placeId, ...(l.claims ?? [])].filter((id): id is string => !!id)),
  );

  it('E1: every anchored schematic place is either in featureKey or emits a data-label-for text; never both, never neither', () => {
    expect(groups.length, 'featureKey must be present on the live sheet').toBeGreaterThan(0);
    const labeled = textLabelIds(result.svg);
    const headingCovered = new Set(['achaean-camp']);
    const anchored = allPlaces.filter(
      (p) => p.positionBasis === 'conjectural' && p.plateAnchors?.['trojan-plain-schematic'],
    );
    for (const place of anchored) {
      const inKey = keyedPlaceIds.has(place.id) || coveredByKeyedLayer.has(place.id);
      const layerIdsForPlace = plate.layers.filter((l) => l.placeId === place.id).map((l) => l.id);
      const hasText = labeled.has(place.id) || layerIdsForPlace.some((id) => labeled.has(id));
      if (headingCovered.has(place.id)) {
        expect(inKey, `${place.id} is heading-covered, must not be keyed`).toBe(false);
        expect(hasText, `${place.id} is heading-covered, must not letter`).toBe(false);
        continue;
      }
      expect(
        inKey || hasText,
        `${place.id} is neither keyed nor lettered`,
      ).toBe(true);
      expect(inKey && labeled.has(place.id), `${place.id} is both keyed and lettered`).toBe(false);
    }
  });

  it('E2: numerals are unique and contiguous 1…N in group order; every item resolves to a drawn pin or layer', () => {
    expect(groups.map((g) => g.title)).toEqual([...FEATURE_KEY_HEADINGS]);
    expect(keyedItems.length).toBe(42);
    const ns = [...result.svg.matchAll(/<g class="plate-key-badge"[^>]*data-key-n="(\d+)"/g)].map((m) => Number(m[1]));
    // Sorted, not in document order: a group routed into an inset (ruling 10)
    // draws its numerals with the panel, in the furniture stream after the
    // map face, so 12-22 are emitted last. The claim is that the numerals are
    // unique and contiguous 1…N — the printed key's own order, which
    // featureKeyMarkup walks — not the order the SVG happens to paint them.
    expect(new Set(ns).size, 'a numeral is drawn twice').toBe(ns.length);
    expect([...ns].sort((a, b) => a - b)).toEqual(Array.from({ length: keyedItems.length }, (_, i) => i + 1));
    const drawnIds = new Set(result.features.map((f) => f.id));
    const pinIds = new Set(
      [...result.svg.matchAll(/<g(?![^>]*plate-key-badge)[^>]*data-place-id="([^"]+)"/g)].map((m) => m[1]),
    );
    for (const item of keyedItems) {
      const id = item.placeId ?? item.layerId!;
      const drawn = drawnIds.has(id) || pinIds.has(id);
      expect(drawn, `${id} must resolve to a drawn pin or layer`).toBe(true);
    }
  });

  it('E3: no data-label-for text (or its leader) is emitted for any keyed id', () => {
    const labeled = textLabelIds(result.svg);
    const leaderIds = new Set(
      [...result.svg.matchAll(/<path class="plate-leader[^"]*" data-label-for="([^"]+)"/g)].map((m) => m[1]),
    );
    for (const id of keyedIds) {
      expect(labeled.has(id), `keyed id ${id} still has a text label`).toBe(false);
      expect(leaderIds.has(id), `keyed id ${id} still has a name leader`).toBe(false);
    }
  });

  it('E4: badge boxes are disjoint from label boxes and each other; each is within 30px of its pin or leadered', () => {
    const badgeGroups = [...result.svg.matchAll(/<g class="plate-key-badge"[^>]*>[\s\S]*?<\/g>/g)].map((m) => m[0]);
    const badgeBoxes: { n: number; id: string; box: [number, number, number, number]; cx: number; cy: number }[] = [];
    for (const g of badgeGroups) {
      const n = Number(g.match(/data-key-n="(\d+)"/)?.[1]);
      const id = g.match(/data-place-id="([^"]+)"/)?.[1] ?? g.match(/data-layer-id="([^"]+)"/)?.[1] ?? '';
      const circle = g.match(/<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([-\d.]+)"/);
      const cx = Number(circle?.[1]);
      const cy = Number(circle?.[2]);
      const r = Number(circle?.[3]);
      badgeBoxes.push({ n, id, box: [cx - r, cy - r, cx + r, cy + r], cx, cy });
    }
    expect(badgeBoxes.length).toBe(keyedItems.length);

    for (let i = 0; i < badgeBoxes.length; i++) {
      for (let j = i + 1; j < badgeBoxes.length; j++) {
        expect(
          boxesIntersect(badgeBoxes[i].box, badgeBoxes[j].box),
          `badge ${badgeBoxes[i].n} intersects badge ${badgeBoxes[j].n}`,
        ).toBe(false);
      }
    }
    for (const [id, box] of Object.entries(result.labelBoxes)) {
      for (const badge of badgeBoxes) {
        expect(boxesIntersect(box, badge.box), `label ${id} intersects badge ${badge.n} (${badge.id})`).toBe(false);
      }
    }

    // Zone letters (A, B, C…) are their own disc, drawn with the same
    // badgeMarkup but placed at a fixed centroid outside the solver — a
    // numeral badge must not be placed on top of one (review fix,
    // 2026-09-02: badge 8 originally landed on zone A).
    const zoneLetterBoxes = [...result.svg.matchAll(/<g class="plate-zone-letter">[\s\S]*?<\/g>/g)].map((m) => {
      const circle = m[0].match(/<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([-\d.]+)"/);
      const cx = Number(circle?.[1]);
      const cy = Number(circle?.[2]);
      const r = Number(circle?.[3]);
      const letter = m[0].match(/>([^<]*)<\/text>/)?.[1] ?? '';
      return { letter, box: [cx - r, cy - r, cx + r, cy + r] as [number, number, number, number] };
    });
    expect(zoneLetterBoxes.length).toBeGreaterThan(0);
    for (const badge of badgeBoxes) {
      for (const zone of zoneLetterBoxes) {
        expect(
          boxesIntersect(badge.box, zone.box),
          `badge ${badge.n} intersects zone letter ${zone.letter}`,
        ).toBe(false);
      }
    }

    const pinCentres = new Map<string, [number, number]>();
    for (const m of result.svg.matchAll(/<g(?![^>]*plate-key-badge)[^>]*data-place-id="([^"]+)"[^>]*>[\s\S]*?<\/g>/g)) {
      const circle = m[0].match(/<circle cx="([-\d.]+)" cy="([-\d.]+)"/);
      const rect = m[0].match(/<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"/);
      if (circle) pinCentres.set(m[1], [Number(circle[1]), Number(circle[2])]);
      else if (rect) {
        pinCentres.set(m[1], [Number(rect[1]) + Number(rect[3]) / 2, Number(rect[2]) + Number(rect[4]) / 2]);
      }
    }
    const leadered = new Set(
      [...result.svg.matchAll(/<path class="plate-key-leader"[^>]*data-key-n="(\d+)"/g)].map((m) => Number(m[1])),
    );
    for (const badge of badgeBoxes) {
      const pin = pinCentres.get(badge.id);
      // A numeral keyed to a LINE — a wall, a ring road — points at the line,
      // not at the middle of the rectangle round it: measured against the
      // drawn geometry, so "22, the wagon-road" sitting on the ring counts as
      // being at its mark, while the same badge at the ring's empty centre
      // (where its place anchor is) does not.
      const drawnId = [`${badge.id}--inset`, badge.id].find((id) => layerPaths(result.svg, id).length > 0);
      const feature =
        result.features.find((f) => f.id === `${badge.id}--inset`) ??
        result.features.find((f) => f.id === badge.id);
      let dist: number;
      if (pin) {
        dist = Math.hypot(badge.cx - pin[0], badge.cy - pin[1]);
      } else if (drawnId) {
        // To the nearest point ON the line, not to its nearest VERTEX
        // (2026-09-03, ruling 12's citadel panel): the house of Priam is a
        // rotated rectangle 106 x 133px, so a badge seated 12px off the middle
        // of one side measured 49px to the nearest corner and read as adrift.
        // The claim was always "the numeral sits at its mark"; a vertex is not
        // the mark, the drawn line is.
        dist = Math.min(
          ...layerPaths(result.svg, drawnId).map((line) =>
            line.length === 1
              ? Math.hypot(badge.cx - line[0][0], badge.cy - line[0][1])
              : Math.min(
                  ...line.slice(1).map((_, i) => distToSegment([badge.cx, badge.cy], line[i], line[i + 1])),
                ),
          ),
        );
      } else if (feature) {
        dist = Math.hypot(
          badge.cx - (feature.bbox[0] + feature.bbox[2]) / 2,
          badge.cy - (feature.bbox[1] + feature.bbox[3]) / 2,
        );
      } else {
        dist = NaN;
      }
      const near = dist <= 30;
      expect(
        near || leadered.has(badge.n),
        `badge ${badge.n} (${badge.id}) is ${dist.toFixed(1)}px from its mark and has no leader`,
      ).toBe(true);
    }
  });

  it('E5: no centred label box intersects a wall/shipRow/tumulus/route reserved box or a badge box', () => {
    const frameWidth = plate.size[0] - (plate.marginRight ?? 0);
    const viewport = viewportFromBBox(plate.bbox!, [frameWidth, plate.size[1]], plate.rotationDeg);
    const reserved: [number, number, number, number][] = [];
    for (const layer of plate.layers) {
      if (layer.style === 'inset') continue;
      if (layer.kind === 'shipRow' || layer.kind === 'tumulus') {
        const feat = result.features.find((f) => f.id === layer.id);
        if (feat) reserved.push(feat.bbox);
      } else if (layer.kind === 'wall' && layer.trace) {
        const run = layer.trace.map((p) => project(p, viewport)) as [number, number][];
        reserved.push(...lineworkExtent(run, 1.15 / 2 + 4));
      } else if (layer.kind === 'route' && layer.path) {
        const run = layer.path.map((p) => project(p, viewport)) as [number, number][];
        reserved.push(...lineworkExtent(run, 0.5));
      }
    }
    const badgeBoxes = [...result.svg.matchAll(/<g class="plate-key-badge"[^>]*>[\s\S]*?<\/g>/g)].map((m) => {
      const circle = m[0].match(/<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([-\d.]+)"/);
      const cx = Number(circle?.[1]);
      const cy = Number(circle?.[2]);
      const r = Number(circle?.[3]);
      return [cx - r, cy - r, cx + r, cy + r] as [number, number, number, number];
    });
    const centredIds = plate.layers
      .filter((l) => (l.kind === 'region' || l.kind === 'band' || l.kind === 'relief') && l.style !== 'inset')
      .map((l) => l.id)
      .filter((id) => result.labelBoxes[id]);
    for (const id of centredIds) {
      const box = result.labelBoxes[id];
      for (const other of reserved) {
        expect(boxesIntersect(box, other), `centred ${id} intersects reserved ink`).toBe(false);
      }
      for (const badge of badgeBoxes) {
        expect(boxesIntersect(box, badge), `centred ${id} intersects a badge`).toBe(false);
      }
    }
  });

  // Was "key bottom + 10 ≤ inset top", which is the one-column rule. Ruling 12
  // (2026-09-03) gives the margin two columns — keys on the left at their own
  // 340px measure, the three panels on the right — so the keys and the panels
  // no longer stack, they sit side by side. The claim that survives is the one
  // that always mattered: the key text and the panels do not collide. Stacked
  // or beside, either separation satisfies it.
  it('E6: the keys never collide with a panel; every key row estimated width ≤ 282px', () => {
    const keyYs = [
      ...result.svg.matchAll(/<text class="plate-key-row"[^>]*y="([-\d.]+)"/g),
      ...result.svg.matchAll(/<g class="plate-feature-key"[\s\S]*?<tspan[^>]*y="([-\d.]+)"/g),
    ].map((m) => Number(m[1]));
    expect(keyYs.length, 'feature key rows must render').toBeGreaterThan(0);
    const keyBottom = Math.max(...keyYs);
    const wrapW = 282;
    const keyRight = plate.size[0] - (plate.marginRight ?? 0) + 12 + 8 + wrapW + 22;
    const panels = plate.layers.filter((l) => l.style === 'inset' && l.frame);
    expect(panels.length, 'the sheet must carry inset panels').toBeGreaterThan(0);
    for (const panel of panels) {
      const [fx, fy] = panel.frame!;
      expect(
        keyBottom + 10 <= fy || keyRight <= fx,
        `key block (bottom ${keyBottom}, right ${keyRight.toFixed(0)}) collides with panel ${panel.id} at ${fx},${fy}`,
      ).toBe(true);
    }
    for (const item of keyedItems) {
      const label = item.label ?? '';
      const est = label.length * 9.5 * 0.54;
      expect(est, `"${label}" estimated width ${est} exceeds ${wrapW}px (must wrap or shorten)`).toBeLessThanOrEqual(
        wrapW + 1e-6,
      );
    }
  });

  // Ruling 9 (John, 2026-09-03 13:21, circling zone letter B with a numeral's
  // leader driven straight through it and another's ending inside it): "let's
  // not have things overlap." Gated on the rendered SVG, not on a look.
  it('E7: nothing overlaps — no disc on a disc, a foreign pin, water, a glyph, a name or furniture; no leader through any of them', () => {
    expect(badgeOverlapOffenders(result.svg, plate, result)).toEqual([]);
  });

  it('E7b: the geographic sheets pass the same check', () => {
    for (const p of [SEED_PLATE_PATH, '../apparatus/plates/troad.json']) {
      const sheetPlate = parsePlate(JSON.parse(readFileSync(p, 'utf-8')));
      const sheet = renderPlate(sheetPlate, allPlaces);
      expect(badgeOverlapOffenders(sheet.svg, sheetPlate, sheet), p).toEqual([]);
    }
  });

  it('zone letters stay byte-identical to their recorded placement', () => {
    const groupsNow = [...result.svg.matchAll(/<g class="plate-zone-letter">[\s\S]*?<\/g>/g)].map((m) => m[0]);
    expect(groupsNow).toEqual([...ZONE_LETTER_MARKUP]);
  });

  // Ruling 10 (John, 2026-09-03): "the citadel is an inset". The group's
  // numerals go INSIDE the panel; the map face keeps one mark and its zone
  // letter. E7 above proves nothing in the panel overlaps anything; these two
  // prove it is in the panel at all, and that the face was actually cleared —
  // an inset that draws a second copy while the spider stays would pass every
  // overlap check and fix nothing.
  // Two routed groups since ruling 12 (2026-09-03): "Inside the walls" into the
  // citadel panel, "Before the walls" into the ground panel below it. Each
  // group's numerals belong to ITS panel and to no other.
  const insetGroupNs = () => {
    const out = new Map<string, Set<number>>();
    let n = 0;
    for (const g of groups) {
      for (const _item of g.items) {
        n += 1;
        if (!g.inset) continue;
        const set = out.get(g.inset) ?? new Set<number>();
        set.add(n);
        out.set(g.inset, set);
      }
    }
    return out;
  };

  it('E8: every numeral of an inset group is drawn inside its panel, with its leader', () => {
    const byPanel = insetGroupNs();
    expect(byPanel.size, 'the sheet must route groups into insets').toBe(2);
    expect([...byPanel.values()].reduce((a, s) => a + s.size, 0)).toBe(21);
    const anyInset = new Set([...byPanel.values()].flatMap((s) => [...s]));
    for (const [panelId, insetNs] of byPanel) {
      const panel = plate.layers.find((l) => l.id === panelId);
      const [fx, fy, fw, fh] = panel!.frame!;
      const inPanel = (x: number, y: number) => x >= fx && x <= fx + fw && y >= fy && y <= fy + fh;
      const seen = new Set<number>();
      for (const disc of markDiscs(result.svg, 'plate-key-badge')) {
        const num = Number(disc.label.slice('badge '.length, disc.label.indexOf(' (')));
        if (!insetNs.has(num)) {
          expect(inPanel(disc.cx, disc.cy), `numeral ${num} is inside panel ${panelId}, which is not its own`).toBe(
            false,
          );
          continue;
        }
        seen.add(num);
        expect(inPanel(disc.cx - disc.r, disc.cy - disc.r), `numeral ${num} runs out of ${panelId}`).toBe(true);
        expect(inPanel(disc.cx + disc.r, disc.cy + disc.r), `numeral ${num} runs out of ${panelId}`).toBe(true);
      }
      expect([...seen].sort((a, b) => a - b)).toEqual([...insetNs].sort((a, b) => a - b));
      for (const leader of markKeyLeaders(result.svg)) {
        if (!insetNs.has(Number(leader.n))) continue;
        expect(
          inPanel(leader.ax, leader.ay) && inPanel(leader.bx, leader.by),
          `leader ${leader.n} leaves ${panelId}`,
        ).toBe(true);
      }
    }
    expect(anyInset.size).toBe(21);
  });

  it("E9: the inset groups' marks are off the map face; the citadel keeps its wall and its zone letters", () => {
    const frameWidth = plate.size[0] - (plate.marginRight ?? 0);
    for (const group of groups.filter((g) => g.inset)) {
      const panel = plate.layers.find((l) => l.id === group.inset)!;
      const [fx, fy] = panel.frame!;
      expect(fx).toBeGreaterThanOrEqual(frameWidth);
      for (const item of group.items) {
        const id = item.placeId ?? item.layerId!;
        for (const pin of markPins(result.svg)) {
          if (pin.id !== id) continue;
          expect(pin.box[0] >= fx && pin.box[1] >= fy, `${id} is still marked on the map face`).toBe(true);
        }
      }
    }
    // The one mark the ruling leaves at Ilios, and the letters.
    expect(result.svg).toContain('data-feature-id="wall-of-troy"');
    expect([...result.svg.matchAll(/<g class="plate-zone-letter">/g)].length).toBe(plate.sceneKey!.length);
  });

  it('numeral badges carry the contract attributes and no tabindex', () => {
    const badges = [...result.svg.matchAll(/<g class="plate-key-badge"[^>]*>[\s\S]*?<\/g>/g)].map((m) => m[0]);
    expect(badges.length).toBe(42);
    for (const g of badges) {
      expect(g).toMatch(/role="img"/);
      expect(g).toMatch(/aria-label="/);
      expect(g).toContain('<title>');
      expect(g).toMatch(/data-key-n="\d+"/);
      expect(g).toMatch(/data-(?:place|layer)-id="/);
      expect(g).not.toContain('tabindex');
      expect(g).not.toContain('class="plate-label');
    }
  });
});

// Ruling 9's last line of defence (2026-09-03 review, finding 6): a numeral
// the placer cannot seat clear used to be DRAWN ANYWAY, on top of whatever it
// collided with, because seatBadge always returned a best. It now comes off
// the map face and says so. The live sheets never reach this — they place all
// thirty-two — so it is exercised here on a plate built to make placement
// impossible: one schematic sheet that is open water from edge to edge, which
// ruling 5 forbids a numeral to sit on, with three keyed features on it.
describe('renderPlate: an unplaceable numeral is dropped and reported, never drawn overlapping (finding 6)', () => {
  const drowned: PlatePlace[] = [1, 2, 3].map((n) => ({
    id: `sunk-${n}`,
    name: `Sunk ${n}`,
    certainty: 'certain' as const,
    plateAnchors: { shield: [0.3 + n * 0.1, 0.5] },
    positionBasis: 'conjectural' as const,
  }));
  const plate: Plate = {
    ...schematicPlate,
    size: [300, 300],
    marginRight: 100,
    layers: [
      {
        id: 'all-sea',
        kind: 'region',
        fill: 'sea',
        polygon: [
          [0, 0],
          [1, 0],
          [1, 1],
          [0, 1],
        ],
      },
    ],
    featureKey: [
      { title: 'Group', items: drowned.map((p, i) => ({ placeId: p.id, label: `Sunkkey${i + 1}` })) },
    ],
  };
  const result = renderPlate(plate, drowned);

  it('draws no badge it cannot place clear', () => {
    expect([...result.svg.matchAll(/<g class="plate-key-badge"/g)].length).toBe(0);
  });

  it('reports every dropped numeral in unplacedKeyNumerals', () => {
    expect(result.unplacedKeyNumerals).toEqual([1, 2, 3]);
  });

  it('keeps the key rows, marked unplaced', () => {
    expect(result.svg).toContain('Sunkkey1');
    const rows = [...result.svg.matchAll(/<text class="plate-key-row" data-key-n="(\d+)" data-unplaced="1"/g)];
    expect([...new Set(rows.map((m) => Number(m[1])))]).toEqual([1, 2, 3]);
  });

  it('leaves the sheet clean by E7', () => {
    expect(badgeOverlapOffenders(result.svg, plate, result)).toEqual([]);
  });

  it('renders rather than throwing', () => {
    expect(result.svg.startsWith('<svg')).toBe(true);
  });
});

// Finding F3 (stage 6 review, 2026-09-03): a featureKey item whose place
// never resolves to an anchor on THIS plate (no plateAnchors entry) used to
// keep its numbered key row and skip its numeral -- badges [1], key rows
// [1, 2], row 2 naming a feature the sheet never drew. `keyedGroups` is now
// built once from only the items that resolved, so both the badges and the
// key text derive from the same list.
describe('renderPlate: featureKey drops an unanchored item cleanly (F3, stage 6 review)', () => {
  const anchored: PlatePlace = {
    id: 'fk-anchored',
    name: 'Anchored Place',
    certainty: 'certain',
    plateAnchors: { shield: [0.4, 0.4] },
    positionBasis: 'conjectural',
  };
  const ghost: PlatePlace = {
    id: 'fk-ghost',
    name: 'Ghost Place',
    certainty: 'certain',
    // No plateAnchors entry for "shield" -- never resolves to a position on
    // this plate, the same shape as the finding's own repro.
  };
  const plate: Plate = {
    ...schematicPlate,
    size: [300, 300],
    marginRight: 100,
    featureKey: [
      {
        title: 'Group',
        items: [
          { placeId: 'fk-anchored', label: 'Anchoredkey' },
          { placeId: 'fk-ghost', label: 'Ghostkey' },
        ],
      },
    ],
  };

  it('numerals stay dense (no gap for the dropped item)', () => {
    const result = renderPlate(plate, [anchored, ghost]);
    const ns = [...result.svg.matchAll(/<g class="plate-key-badge"[^>]*data-key-n="(\d+)"/g)].map((m) => Number(m[1]));
    expect(ns).toEqual([1]);
  });

  it('the dropped item prints no key row and no badge', () => {
    const result = renderPlate(plate, [anchored, ghost]);
    expect(result.svg).not.toContain('Ghostkey');
    expect(result.svg).not.toContain('data-place-id="fk-ghost"');
  });

  it('the kept item still prints its key row and badge', () => {
    const result = renderPlate(plate, [anchored, ghost]);
    expect(result.svg).toContain('Anchoredkey');
    expect(result.svg).toContain('data-place-id="fk-anchored" data-key-n="1"');
  });

  it('the dropped place is recorded in unlocated exactly once (not duplicated with the main honesty pass)', () => {
    const result = renderPlate(plate, [anchored, ghost]);
    const ghostEntries = result.unlocated.filter((p) => p.id === 'fk-ghost');
    expect(ghostEntries.length).toBe(1);
  });
});

describe('renderPlate: geographic label-set parity (stage 5c E9)', () => {
  function idsFromSvg(svg: string): Set<string> {
    return textLabelIds(svg);
  }
  function idsFromHtml(html: string): Set<string> {
    return textLabelIds(html);
  }

  // geo-enrich-2 is the last LOOK-gated geographic render. This lane must
  // not drop any of those ids (2026-09-02 registry: a positions-only diff
  // misses a suppression). Ids added since that render (pergamos, wall-of-
  // troy, and on troad a later geo-enrich wave) are frozen from the
  // pre-lane live set so this lane cannot change the set either way.
  const GEO_ENRICH_PLUS_LIVE: Record<'trojan-plain' | 'troad', readonly string[]> = {
    'trojan-plain': [
      'achaean-camp-zone',
      'aegean',
      'besik-bay',
      'besik-sivritepe',
      'callicolone',
      'kesik-basin',
      'kesik-tepe',
      'kum-tepe',
      'lagoon-bronze',
      'pergamos',
      'pinarbasi',
      'rhoiteion',
      'scamander',
      'scamandrian-plain',
      'sigeion',
      'simoeis',
      'thymbra',
      'thymbrios',
      'tomb-of-ajax-in-tepe',
      'troy',
      'uvecik-tepe',
      'wall-of-troy',
    ],
    troad: [
      'abydos',
      'adramyttion',
      'arisbe',
      'besik-sivritepe',
      'callicolone',
      'chryse',
      'dardania',
      'hellespont',
      'ida',
      'kesik-tepe',
      'kum-tepe',
      'lekton',
      'lesbos',
      'lyrnessus',
      'percote',
      'pergamos',
      'pinarbasi',
      'practius',
      'relief-imbros',
      'relief-samothrace',
      'rhoiteion',
      'river-aisepos',
      'river-granikos',
      'river-satnioeis',
      'river-scamander',
      'sestos',
      'sigeion',
      'simoeis',
      'tenedos',
      'thymbra',
      'thymbrios',
      'tomb-of-ajax-in-tepe',
      'troy',
      'uvecik-tepe',
      'wall-of-troy',
    ],
  };

  it('trojan-plain and troad keep the same data-label-for set as geo-enrich-2 (plus live ids this lane must not touch)', () => {
    const places = JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[];
    for (const sheet of ['trojan-plain', 'troad'] as const) {
      const plate = parsePlate(
        JSON.parse(readFileSync(path.resolve(process.cwd(), `../apparatus/plates/${sheet}.json`), 'utf-8')),
      );
      const now = idsFromSvg(renderPlate(plate, places).svg);
      const baseline = new Set(GEO_ENRICH_PLUS_LIVE[sheet]);
      const archived = idsFromHtml(
        readFileSync(path.resolve(process.cwd(), `../build/plate-review/geo-enrich-2/${sheet}-light.html`), 'utf-8'),
      );
      const droppedArchived = [...archived].filter((id) => !now.has(id)).sort();
      expect(droppedArchived, `${sheet} dropped a geo-enrich-2 label`).toEqual([]);
      const added = [...now].filter((id) => !baseline.has(id)).sort();
      const dropped = [...baseline].filter((id) => !now.has(id)).sort();
      expect({ sheet, added, dropped }).toEqual({ sheet, added: [], dropped: [] });
    }
  });
});

// ── The plan register and the quiet masonry (ruling 13, 2026-09-03) ──────
// John, on the first citadel supplement's six dashed rectangles: "c'mon" and
// "fill in the city!" A building the poem describes is drawn as an engraved
// plan (walls at their thickness in metres, partitions, column rows, seats),
// and the survey under it drops to ground.
describe('columnDots', () => {
  it('spaces columns evenly and centres the row on the run', () => {
    expect(columnDots([[0, 0], [10, 0]], 4)).toEqual([[1, 0], [5, 0], [9, 0]]);
  });
  it('a run shorter than one spacing gets one column at its middle', () => {
    expect(columnDots([[0, 0], [2, 0]], 4)).toEqual([[1, 0]]);
  });
  it('walks a bent run by arc length', () => {
    expect(columnDots([[0, 0], [4, 0], [4, 4]], 4)).toEqual([[0, 0], [4, 0], [4, 4]]);
  });
  it('returns nothing for a degenerate run or spacing', () => {
    expect(columnDots([[0, 0]], 4)).toEqual([]);
    expect(columnDots([[0, 0], [1, 0]], 0)).toEqual([]);
  });
});

describe('renderPlate: the plan register (style "plan")', () => {
  // A 222 m window at 400 x 300: about 1.35 px per metre, so a 2 m wall is
  // 2.7 px of bar. The Troad-scale fixture below is 0.017 px per metre, where
  // the same layer must draw nothing but its outline reservation.
  const TIGHT: [number, number, number, number] = [39.956, 26.238, 39.958, 26.24];
  const planLayer: PlateLayer = {
    id: 'plan-1',
    kind: 'region',
    style: 'plan',
    fill: 'none',
    wallM: 2,
    columnM: 3,
    polygon: [
      [39.9568, 26.2385],
      [39.9568, 26.2395],
      [39.9572, 26.2395],
      [39.9572, 26.2385],
    ],
    rings: [
      [
        [39.9569, 26.2387],
        [39.9569, 26.2393],
        [39.9571, 26.2393],
        [39.9571, 26.2387],
      ],
    ],
    lines: [[[39.9568, 26.239], [39.9572, 26.239]]],
    columns: [[[39.95695, 26.2388], [39.95695, 26.2392]]],
    solids: [
      [
        [39.95705, 26.2388],
        [39.95705, 26.23885],
        [39.9571, 26.23885],
        [39.9571, 26.2388],
      ],
    ],
  };
  const tight: Plate = { ...testPlate, bbox: TIGHT, layers: [planLayer] };

  it('parses the plan fields, and rejects a non-positive wallM', () => {
    const parsed = parsePlate(JSON.parse(JSON.stringify(tight)));
    const l = parsed.layers[0];
    expect(l.lines?.length).toBe(1);
    expect(l.columns?.length).toBe(1);
    expect(l.solids?.length).toBe(1);
    expect(l.wallM).toBe(2);
    expect(() => parsePlate({ ...JSON.parse(JSON.stringify(tight)), layers: [{ ...planLayer, wallM: 0 }] })).toThrow(/wallM/);
    expect(() => parsePlate({ ...JSON.parse(JSON.stringify(tight)), layers: [{ ...planLayer, lines: 'nope' }] })).toThrow(/lines/);
  });

  it('draws walls as bars at wallM metres in the conjectural ink, partitions at half, columns as dots, solids filled', () => {
    const svg = renderPlate(tight, []).svg;
    const viewport = viewportFromBBox(TIGHT, SIZE, 0);
    const a = project([39.957, 26.239], viewport);
    const b = project([39.957 + 1 / 111320, 26.239], viewport);
    const ppm = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const walls = svg.match(/<path data-feature-id="plan-1" class="plate-layer plate-layer-plan" d="[^"]+" fill="none" stroke="var\(--text-mid\)" stroke-width="([\d.]+)"/);
    expect(walls).toBeTruthy();
    expect(Number(walls![1])).toBeCloseTo(2 * ppm, 0);
    const thin = svg.match(/data-feature-id="plan-1-lines"[^>]*stroke-width="([\d.]+)"/);
    expect(Number(thin![1])).toBeCloseTo(ppm, 0);
    expect(svg).toMatch(/data-feature-id="plan-1-solids"[^>]*fill="var\(--text-mid\)"/);
    const dots = svg.match(/data-feature-id="plan-1-columns"[^>]* d="([^"]+)"/);
    expect(dots).toBeTruthy();
    // 0.0004 deg of longitude at 39.957 N is about 34 m: at 3 m spacing, twelve columns.
    expect((dots![1].match(/ a /g) ?? []).length / 2).toBe(12);
    // Two wall rings in one path: the house and the court.
    expect((walls![0].match(/ Z/g) ?? []).length).toBe(2);
  });

  it('at a scale where the wall is under a third of a pixel it draws only its outline reservation', () => {
    const svg = renderPlate({ ...testPlate, layers: [planLayer] }, []).svg;
    expect(svg).toMatch(/data-feature-id="plan-1" class="plate-layer plate-layer-plan" d="[^"]+" fill="none" stroke="none"/);
    expect(svg).not.toContain('plan-1-columns');
  });

  it('keys one legend row for the plan register, distinct from the poem dash', () => {
    const svg = renderPlate(tight, []).svg;
    expect(svg).toContain('Building drawn from the poem, not surveyed');
  });
});

describe('renderPlate: masonry-ground', () => {
  const square = (dlat: number): [number, number][] => [
    [39.9 + dlat, 26.2],
    [39.9 + dlat, 26.21],
    [39.91 + dlat, 26.21],
    [39.91 + dlat, 26.2],
  ];
  const plate: Plate = {
    ...testPlate,
    layers: [
      { id: 'm', kind: 'region', fill: 'masonry', legend: 'Masonry, surveyed (Dörpfeld 1902)', polygon: square(0) },
      { id: 'g', kind: 'region', fill: 'masonry-ground', legend: 'Masonry, surveyed (Dörpfeld 1902)', polygon: square(0.02) },
    ],
  };
  it('draws the masonry token at 0.42 opacity with a lighter ink edge', () => {
    const svg = renderPlate(plate, []).svg;
    expect(svg).toMatch(/data-feature-id="g"[^>]*fill="var\(--plate-masonry\)" fill-opacity="0.42" stroke="var\(--flaxman-ink\)" stroke-width="0.7" stroke-opacity="0.45"/);
    expect(svg).toMatch(/data-feature-id="m"[^>]*fill-opacity="1" stroke="var\(--flaxman-ink\)" stroke-width="1" stroke-opacity="0.85"/);
  });
  it('keys on the masonry row: one legend row for both', () => {
    const svg = renderPlate(plate, []).svg;
    expect((svg.match(/Masonry, surveyed \(Dörpfeld 1902\)/g) ?? []).length).toBe(1);
  });
  it('is rejected by the fill whitelist under any other spelling', () => {
    expect(() => parsePlate({ ...plate, layers: [{ ...plate.layers[1], fill: 'masonry_ground' }] })).toThrow(/fill/);
  });
});

describe('the citadel panel draws the poem’s city as a built fabric (ruling 13)', () => {
  const plate = parsePlate(JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8')));
  const inPanel = plate.layers.filter((l) => l.insetOf === 'citadel-city-panel');
  const plans = inPanel.filter((l) => l.style === 'plan');
  const survey = inPanel
    .filter((l) => l.fill === 'masonry-ground')
    .map((l) => l.polygon as [number, number][]);
  const ringOuter = plate.layers.find((l) => l.id === 'citadel-terrace-ring-outer')!.trace as [number, number][];
  const inside = (p: [number, number], poly: [number, number][]) => {
    let hit = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const [yi, xi] = poly[i];
      const [yj, xj] = poly[j];
      if (yi > p[0] !== yj > p[0] && p[1] < ((xj - xi) * (p[0] - yi)) / (yj - yi) + xi) hit = !hit;
    }
    return hit;
  };
  const vertices = (l: PlateLayer): [number, number][] =>
    [l.polygon ?? [], ...(l.rings ?? []), ...(l.lines ?? []), ...(l.columns ?? []), ...(l.solids ?? [])].flat() as [number, number][];

  it('draws the six named buildings and the two fabric layers as plans, on Dörpfeld’s ported houses', () => {
    expect(plans.map((l) => l.id).sort()).toEqual(
      [
        'citadel-fabric-summit',
        'citadel-fabric-terrace',
        'citadel-poem-house-of-hector',
        'citadel-poem-house-of-paris',
        'citadel-poem-house-of-priam',
        'citadel-poem-shrine-of-apollo',
        'citadel-poem-temple-of-athena',
      ].sort(),
    );
    expect(survey.length).toBeGreaterThanOrEqual(12); // four circuit arcs, VI g, VI R, and six house blocks
    // Priam’s house is a court with colonnades and more than one wall ring.
    const priam = plans.find((l) => l.id === 'citadel-poem-house-of-priam')!;
    expect(priam.columns!.length).toBe(4);
    expect(priam.rings!.length).toBeGreaterThanOrEqual(2);
    // The fabric is many houses in one layer, and says so.
    const terrace = plans.find((l) => l.id === 'citadel-fabric-terrace')!;
    expect(terrace.rings!.length).toBeGreaterThanOrEqual(10);
    expect(terrace.note).toMatch(/not evidence/);
  });

  it('every plan vertex lies within the outer terrace front, and none inside surveyed masonry', () => {
    for (const l of plans) {
      for (const v of vertices(l)) {
        expect(inside(v, ringOuter), `${l.id} vertex ${v} is outside the outer terrace front`).toBe(true);
        for (const s of survey) {
          expect(inside(v, s), `${l.id} vertex ${v} is inside surveyed masonry`).toBe(false);
        }
      }
    }
  });

  it('the poem-drawn layers carry their own certainty tier (2026-09-03 review, finding 5)', () => {
    // These layers have no gazetteer place of their own to carry
    // PlatePlace.certainty through — they ARE the claim, placed by the
    // poem's stated relations rather than a measured position, which is
    // exactly what `speculative` means.
    const poemLayerIds = [
      'citadel-poem-house-of-priam',
      'citadel-poem-agora',
      'citadel-poem-house-of-hector',
      'citadel-poem-house-of-paris',
      'citadel-poem-temple-of-athena',
      'citadel-poem-shrine-of-apollo',
      'citadel-weak-wall',
      'citadel-poem-way-to-south-gate',
      'citadel-poem-way-to-scaean-gate',
    ];
    for (const id of poemLayerIds) {
      const layer = plate.layers.find((l) => l.id === id);
      expect(layer, `layer ${id} must exist`).toBeTruthy();
      expect(layer!.certainty, `layer ${id} certainty`).toBe('speculative');
    }
  });

  it('no fabric house intersects surveyed masonry — full polygon test, not vertices only (2026-09-03 review, findings 8-9)', () => {
    // The vertex-in-polygon test above (`inside`) only catches an overlap
    // where one polygon's own CORNER lands inside the other. Two
    // similarly-sized rectangles that cross near a shared edge, with neither
    // one's corners inside the other, pass that test clean and still
    // overlap — which is exactly the shape fabric ring house 9 made against
    // surveyed House VI A, and ring house 12 against Gate VI T (both counted
    // as drawn on the sheet; this file's `rings` array is 0-indexed, so
    // index 8 and 11). `survey` above also only covers `fill:
    // 'masonry-ground'` layers, and VI A and the gates are drawn `fill:
    // 'none'` (an outline, no wash), so they never entered that check at
    // all. This test uses real segment-intersection, against every surveyed
    // house, tower, gate and circuit arc regardless of fill.
    const allSurvey = inPanel
      .filter((l) => /^citadel-(houses?-vi-|tower-vi-|gate-vi-|circuit-)/.test(l.id) && Array.isArray(l.polygon))
      .map((l) => l.polygon as [number, number][]);
    expect(allSurvey.length).toBeGreaterThan(survey.length); // picks up the fill:'none' gates/houses/towers `survey` misses
    const orient = (a: [number, number], b: [number, number], c: [number, number]) =>
      (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
    const segsCross = (p1: [number, number], p2: [number, number], p3: [number, number], p4: [number, number]) => {
      const d1 = orient(p3, p4, p1);
      const d2 = orient(p3, p4, p2);
      const d3 = orient(p1, p2, p3);
      const d4 = orient(p1, p2, p4);
      return ((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) && ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0));
    };
    const polysIntersect = (a: [number, number][], b: [number, number][]) => {
      for (let i = 0; i < a.length; i++) {
        for (let j = 0; j < b.length; j++) {
          if (segsCross(a[i], a[(i + 1) % a.length], b[j], b[(j + 1) % b.length])) return true;
        }
      }
      return a.some((p) => inside(p, b)) || b.some((p) => inside(p, a));
    };
    const terrace = plans.find((l) => l.id === 'citadel-fabric-terrace')!;
    const summit = plans.find((l) => l.id === 'citadel-fabric-summit')!;
    // Finding 3 (count): 12 terrace + 5 summit = 17 fabric houses.
    expect(terrace.rings!.length).toBe(12);
    expect(summit.rings!.length).toBe(5);
    for (const fab of [terrace, summit]) {
      for (const [i, ring] of (fab.rings ?? []).entries()) {
        for (const s of allSurvey) {
          expect(polysIntersect(ring, s), `${fab.id} house ${i} intersects surveyed masonry`).toBe(false);
        }
      }
    }
  });

  it('the Scaean Gate and the great tower stand at the north-west corner of the restored circuit (ruling 14)', () => {
    const places = JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[];
    const cos = Math.cos((39.957 * Math.PI) / 180);
    // Angle from east, counter-clockwise, so the north-west quadrant is 90-180.
    for (const [id, lo, hi] of [
      ['scaean-gate', 120, 165],
      ['great-tower-of-ilios', 120, 165],
    ] as const) {
      const [lat, lon] = places.find((p) => p.id === id)!.plateAnchors!['trojan-plain-schematic'] as [number, number];
      const bearing = (Math.atan2(lat - 39.957, (lon - 26.239) * cos) * 180) / Math.PI;
      const deg = (bearing + 360) % 360;
      expect(deg, `${id} bears ${deg.toFixed(0)} deg from the centre`).toBeGreaterThan(lo);
      expect(deg).toBeLessThan(hi);
    }
    const scaean = places.find((p) => p.id === 'scaean-gate')!;
    expect(scaean.certainty).toBe('speculative');
    expect(scaean.tradition).toMatch(/Fig\. 470/);
    // The street of the poem runs to it, and no street runs to the walled-up West Gate.
    expect(plate.layers.some((l) => l.id === 'citadel-poem-way-to-scaean-gate')).toBe(true);
    expect(plate.layers.some((l) => l.id === 'citadel-poem-way-to-west-gate')).toBe(false);
  });
});

// Ruling 9 round 3 (2026-09-03, Grok finding 4): the badge placement cache is
// a WeakMap keyed on the PLATE OBJECT, with an inner key covering only which
// places resolve where — so mutating `plate.layers` on that same object
// (moving a tumulus, redrawing a ship row, re-tracing a wall) left the cache
// unable to tell the two renders apart and served the FIRST render's seats
// against the SECOND render's geometry. Grok moved the Callicolone mound and
// re-rendered; badge 32 stayed exactly where the first render put it, still
// centred on the mound's old position.
describe('renderPlate: mutating a glyph layer on the same plate object gets a fresh badge solution (round 3, finding 4)', () => {
  it('moving the Callicolone tumulus in place moves its own badge on the next render', () => {
    const raw = JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    const allPlaces = JSON.parse(readFileSync('../apparatus/places.json', 'utf-8')).places as PlatePlace[];

    const before = renderPlate(plate, allPlaces);
    const badgeAt = (svg: string) => {
      const m = svg.match(/<g class="plate-key-badge"[^>]*data-layer-id="callicolone"[^>]*>[\s\S]*?<circle cx="([-\d.]+)" cy="([-\d.]+)"/);
      expect(m, 'badge 32 (callicolone) must render').toBeTruthy();
      return [Number(m![1]), Number(m![2])] as const;
    };
    const beforePos = badgeAt(before.svg);

    // Mutate the SAME layer object the plate already carries — not a fresh
    // plate — so the WeakMap's outer key (the plate object itself) is
    // unchanged and only the inner, place-keyed cache key is what could catch
    // this.
    const layer = plate.layers.find((l) => l.id === 'callicolone');
    expect(layer, 'fixture must still carry the callicolone layer').toBeTruthy();
    layer!.path = [[39.9565 + 0.01, 26.3395 + 0.01]];

    const after = renderPlate(plate, allPlaces);
    const afterPos = badgeAt(after.svg);

    expect(afterPos, 'moving the mound must move its own badge — a stale cached seat would not').not.toEqual(
      beforePos,
    );
    expect(badgeOverlapOffenders(after.svg, plate, after), 'the re-rendered sheet must still clear E7').toEqual([]);
  });
});
