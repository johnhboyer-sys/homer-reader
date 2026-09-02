import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { project, viewportFromBBox } from '../lib/geo';
import {
  parsePlate,
  renderPlate,
  computeCamera,
  hachure,
  shipRow,
  wallGlyph,
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

  it('parses a schematic plate with no bbox, unit-space layers (live seed plate: trojan-plain-schematic.json)', () => {
    const raw = JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    expect(plate.kind).toBe('schematic');
    expect(plate.bbox).toBeUndefined();
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

describe('renderPlate: schematic plates without bbox (gap 1)', () => {
  it('renders the live trojan-plain-schematic.json (unit-space layers, no bbox), mapping u,v across plate.size', () => {
    const raw = JSON.parse(readFileSync(SCHEMATIC_SEED_PLATE_PATH, 'utf-8'));
    const plate = parsePlate(raw);
    const result = renderPlate(plate, []);
    expect(result.svg).toContain(`viewBox="0 0 ${plate.size[0]} ${plate.size[1]}"`);
    expect(result.features.length).toBe(plate.layers.length);
    expect(result.viewport.width).toBe(plate.size[0]);
    expect(result.viewport.height).toBe(plate.size[1]);
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

    const seaLayer = plate.layers.find((l) => l.id === 'sea')!;
    expect(seaLayer.polygon).toBeDefined();
    const [width, height] = plate.size;
    const seaPolygon: [number, number][] = seaLayer.polygon!.map(([u, v]) => [u * width, v * height]);

    const box = result.labelBoxes['mound-of-patroclus'];
    expect(box).toBeDefined();
    expect(boxTouchesPolygon(box, seaPolygon)).toBe(false);
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
    const place: PlatePlace = {
      id: 'achaean-assembly-place',
      name: "The assembly and law-place, with the gods' altars",
      certainty: 'certain',
      kind: 'camp',
      plateAnchors: { 'trojan-plain-schematic': [0.52, 0.748] },
      positionBasis: 'conjectural',
    };
    const result = renderPlate(plate, [place]);
    const labelBox = result.labelBoxes['achaean-assembly-place'];
    expect(labelBox).toBeDefined();
    const camera = computeCamera(plate, result.viewport, ['achaean-assembly-place'], {
      places: [place],
      labelBoxes: result.labelBoxes,
      maxScale: 4, // Reader.svelte's own Chart Room ceiling (part B)
    });
    const [x1, y1, x2, y2] = labelBox!;
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
    expect(svg).toContain('Elevation, metres');
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

// The 25 ground layers on trojan-plain-schematic-v2.json are a copy of the
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
] as const;

describe('trojan-plain-schematic-v2 ground layers match the geographic sheet', () => {
  it('deep-equals each of the 25 ground layers by id', () => {
    const geo = JSON.parse(
      readFileSync(path.resolve(process.cwd(), '../apparatus/plates/trojan-plain.json'), 'utf-8'),
    );
    const v2 = JSON.parse(
      readFileSync(path.resolve(process.cwd(), '../apparatus/plates/trojan-plain-schematic-v2.json'), 'utf-8'),
    );
    const geoById = new Map((geo.layers as { id: string }[]).map((l) => [l.id, l]));
    const v2ById = new Map((v2.layers as { id: string }[]).map((l) => [l.id, l]));
    for (const id of SCHEMATIC_V2_GROUND_IDS) {
      expect(
        v2ById.get(id),
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
const V2_SEED_PLATE_PATH = '../apparatus/plates/trojan-plain-schematic-v2.json';

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
      const rawPath = (plate.layers.find((l) => l.id === id) as { path: [number, number][] }).path;
      const guideMatch = result.svg.match(new RegExp(`id="plate-lp-${id}" d="([^"]+)"`));
      expect(guideMatch, `no textPath guide drawn for ${id}`).toBeTruthy();
      const guidePointCount = (guideMatch![1].match(/[ML]/g) ?? []).length;
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

  it('every legend row text\'s estimated right edge sits inside the sheet, with room to spare', () => {
    const panelMatch = svg.match(/<rect class="plate-legend-panel" x="([-\d.]+)"/);
    expect(panelMatch).toBeTruthy();
    const rowTexts = [...svg.matchAll(/<text x="([-\d.]+)" y="[-\d.]+" font-family="var\(--font-ui\)" font-size="9\.5" fill="var\(--text\)">([^<]*)<\/text>/g)];
    // Also account for wrapped rows (rendered as <text><tspan x="…">…) —
    // every tspan under a legend text carries the same x, so checking those
    // too catches a wrap-path regression as well as the single-line one.
    const tspanTexts = [...svg.matchAll(/<tspan x="([-\d.]+)" y="[-\d.]+">([^<]*)<\/tspan>/g)];
    const all = [...rowTexts, ...tspanTexts];
    expect(all.length).toBeGreaterThan(0);
    for (const m of all) {
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
