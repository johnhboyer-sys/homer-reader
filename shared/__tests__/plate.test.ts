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
  reliefHachureParams,
  hypsometricLevels,
  hypsometricStep,
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
  bbox: [0, 0, 1, 1],
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
      const actualY = maxY; // pin apex sits exactly at the projected point
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
  it('places a valid anchored+conjectural place at the anchored unit position, in a distinct conjectural register', () => {
    const result = renderPlate(schematicPlate, [anchoredPlace]);
    expect(result.unlocated).toEqual([]);
    const feature = result.features.find((f) => f.id === 'anchored-place');
    expect(feature).toBeDefined();
    const [minX, minY, maxX, maxY] = feature!.bbox;
    const actualX = (minX + maxX) / 2;
    const actualY = maxY; // pin apex
    // u=0.25, v=0.75 scaled directly by plate.size [200,200] (schematic
    // projection, per projectPoint).
    expect(actualX).toBeCloseTo(0.25 * 200, 6);
    expect(actualY).toBeCloseTo(0.75 * 200, 6);

    // Visually distinct conjectural register: a data attribute a component
    // can key off, plus a dashed stroke not implied by its certainty tier
    // ('certain' is normally solid, no dasharray at all).
    expect(result.svg).toContain('data-place-id="anchored-place" data-position-basis="conjectural"');
    const gMatch = result.svg.match(/<g data-place-id="anchored-place"[^>]*>[\s\S]*?<\/g>/);
    expect(gMatch).not.toBeNull();
    expect(gMatch![0]).toMatch(/stroke-dasharray="[^"]+"/);
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

describe('renderPlate: tumulus layer kind (gap 2)', () => {
  it('a tumulus layer emits the dome glyph, stroked in ink, not filled', () => {
    const plate: Plate = {
      ...testPlate,
      layers: [{ id: 'tomb-of-ilos', kind: 'tumulus', path: [[39.93, 26.2]] }],
    };
    const result = renderPlate(plate, []);
    expect(result.svg).toContain('data-feature-id="tomb-of-ilos"');
    expect(result.svg).toContain('plate-layer-tumulus');
    const match = result.svg.match(/<path data-feature-id="tomb-of-ilos"[^>]*d="([^"]*)"[^>]*\/>/);
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
    const match = result.svg.match(/<path data-feature-id="two-mounds"[^>]*d="([^"]*)"[^>]*\/>/);
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
      const match = svg.match(new RegExp(`<path data-feature-id="${id}"[^>]*d="([^"]*)"`));
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
  it('names every located place — none is silently dropped, however crowded the sheet', () => {
    const crowd: PlatePlace[] = Array.from({ length: 12 }, (_, i) => ({
      id: `p${i}`, name: `Place${i}`, coords: [39.95 + i * 0.0005, 26.2 + i * 0.0005] as [number, number], certainty: 'certain' as const,
    }));
    const result = renderPlate(testPlate, crowd);
    for (const p of crowd) expect(result.svg).toContain(`>${p.name}</text>`);
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

  it('a conjectural position gets an italic name and a DASHED leader (the dash is the claim)', () => {
    const result = renderPlate(schematicPlate, [anchoredPlace]);
    expect(result.svg).toMatch(/<text[^>]*font-style="italic"/);
    expect(result.svg).toMatch(/class="plate-leader"[^>]*stroke-dasharray="2 2"/);
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
    expect(worst).toBeGreaterThan(150); // and it is genuinely curving, not a no-op
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

  it('the Scamander is drawn in three reaches — the plain, the lagoon, the modern sea', () => {
    expect(pathsFor(svg, 'scamander')).toHaveLength(3);
    expect(pathsFor(svg, 'simoeis')).toHaveLength(2);
  });

  it('each drowned reach is drawn before the water that drowns it', () => {
    const idsInOrder = [...svg.matchAll(/data-feature-id="([^"]+)"/g)].map((m) => m[1]);
    const nth = (id: string, n: number) => idsInOrder.reduce<number[]>((acc, v, i) => (v === id ? [...acc, i] : acc), [])[n];
    expect(nth('scamander', 0)).toBeLessThan(nth('sea-modern', 0));
    expect(nth('scamander', 1)).toBeLessThan(nth('lagoon-bronze', 0));
    expect(nth('simoeis', 0)).toBeLessThan(nth('lagoon-bronze', 0));
  });

  it('nothing of a river is drawn over the lagoon in the river\'s own paint slot', () => {
    // The last reach of each river is the one drawn after every water layer.
    for (const id of ['scamander', 'simoeis']) {
      const reaches = pathsFor(svg, id);
      const own = pointsOf(reaches[reaches.length - 1]);
      // The reach ends ON the shore, so its own final point may sit a
      // bisection's width either side of it; everything before it must be
      // clear of the water by the width of the line that draws it.
      for (const p of own.slice(0, -1)) expect(inPolygon(p, lagoonRing)).toBe(false);
    }
  });

  it('the Scamander still crosses the delta swamp: marsh is wet ground, not open water', () => {
    const swamp = pointsOf(pathsFor(svg, 'delta-swamp')[0]);
    const own = pointsOf(pathsFor(svg, 'scamander').at(-1)!);
    expect(own.some((p) => inPolygon(p, swamp))).toBe(true);
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
    const river = plate.layers.find((l) => l.id === 'river-scamander')!;
    const mouth = project(river.path!.at(-1)! as [number, number], viewport);
    const drawn = pointsOf(pathsFor(svg, 'river-scamander')[0]);
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

// ── Pins are opaque (2026-07-29) ─────────────────────────────────────────
// John, zooming a pin over the hypsometric ramp: the contour lines ran
// straight through the middle of it. The certainty register survives; it is
// carried by an inner mark instead of by a hole.

describe('renderPlate: a pin is never transparent to its own basemap', () => {
  const TIERS = ['certain', 'traditional', 'speculative', 'mythical'] as const;
  const pinFor = (certainty: (typeof TIERS)[number]) => {
    const place: PlatePlace = { id: `p-${certainty}`, name: certainty, coords: [39.957, 26.239], certainty };
    const svg = renderPlate(testPlate, [place]).svg;
    return svg.match(new RegExp(`<g data-place-id="p-${certainty}"[^>]*>[\\s\\S]*?</g>`))![0];
  };

  it.each(TIERS)('the %s pin has an opaque body — no fill-opacity, no fill:none', (certainty) => {
    const pin = pinFor(certainty);
    expect(pin).not.toContain('fill-opacity');
    // The body is one closed outline filled with a colour token. (The inner
    // mark is a stroke-only ring and legitimately carries fill="none"; it is
    // drawn ON the body, not through it.)
    const body = pin.match(/<path d="[^"]*"[^>]*\/>/)![0];
    expect(body).not.toContain('fill="none"');
    expect(body).toMatch(/d="M [\d.-]+ [\d.-]+ A [\d.-]+ [\d.-]+ 0 1 1 [\d.-]+ [\d.-]+ L [\d.-]+ [\d.-]+ Z" fill="var\(--[a-z-]+\)"/);
  });

  it('draws the pin as ONE closed outline, so an opaque body shows no seam across itself', () => {
    // A circle plus a separate triangle leaves two stroked edges crossing the
    // middle of the symbol once the fill stops being transparent.
    expect(pinFor('certain')).not.toContain('<circle');
  });

  it('keeps the four tiers distinguishable by SHAPE, not only by colour', () => {
    const shapes = TIERS.map((t) => {
      const pin = pinFor(t);
      return [
        /stroke-dasharray="2 2"/.test(pin), // broken outline
        /<circle[^>]*stroke="var\(--scene-map-label-halo\)"/.test(pin), // an inner mark at all
        /<circle[^>]*stroke-dasharray/.test(pin), // a BROKEN inner mark
      ].join('|');
    });
    expect(new Set(shapes).size).toBe(4);
  });

  it('carries the inner mark in the sheet\'s own paper colour, never as a hole', () => {
    const pin = pinFor('traditional');
    expect(pin).toContain('stroke="var(--scene-map-label-halo)"');
    expect(pin).not.toContain('fill-opacity');
  });

  it('still marks a conjectural position with its own dashed outline', () => {
    const pin = renderPlate(schematicPlate, [anchoredPlace]).svg.match(/<g data-place-id="anchored-place"[^>]*>[\s\S]*?<\/g>/)![0];
    expect(pin).toContain('stroke-dasharray="1 3"');
    expect(pin).not.toContain('fill-opacity');
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
    // Four keyed tiers, each drawn as the pin itself (arc + point), not as a
    // disc; and each of the four rows present.
    expect(legend.match(/A 4 4 0 1 1/g)).toHaveLength(4);
    for (const text of ['Location secure', 'Traditional identification', 'Identification speculative', 'Mythical — no known site']) {
      expect(legend).toContain(text);
    }
    // The broken registers reach the key too.
    expect(legend).toContain('stroke-dasharray="2 2"');
    expect(legend).toContain(`stroke-dasharray="2.1 2.1"`);
  });

  it('bakes no colour of its own into a pin or its key row', () => {
    const svg = renderPlate(testPlate, [troy, scamander, ghost]).svg;
    expect(svg).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    assertEveryVarTokenDefined(svg);
  });
});
