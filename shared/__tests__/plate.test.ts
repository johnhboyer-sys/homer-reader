import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { project, viewportFromBBox } from '../lib/geo';
import {
  parsePlate,
  renderPlate,
  computeCamera,
  hachure,
  stipple,
  shipRow,
  wallGlyph,
  tumulus,
  waterlines,
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
      style: 'stipple',
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
});

describe('renderPlate: unlocated honesty', () => {
  it('a place with no coords is reported unlocated and never pinned', () => {
    const result = renderPlate(testPlate, [troy, ghost]);
    expect(result.unlocated.map((p) => p.id)).toEqual(['ghost-place']);
    expect(result.svg).not.toContain('data-place-id="ghost-place"');
    expect(result.svg).toContain('data-place-id="troy"');
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
  it('a region layer with no fill declared keeps using --plate-tint (unchanged default)', () => {
    const result = renderPlate(testPlate, []); // camp-1 is a plain region layer, no fill declared
    const match = result.svg.match(/<path data-feature-id="camp-1"[^>]*\/>/);
    expect(match![0]).toContain('fill="var(--plate-tint)"');
    expect(match![0]).not.toContain('var(--scene-map-sea)');
  });

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

  it('stipple is deterministic for the same seed and differs for a different seed', () => {
    const path: [number, number][] = [[0, 0], [40, 0], [40, 40]];
    const a = stipple(path, { seed: 7 });
    const b = stipple(path, { seed: 7 });
    const c = stipple(path, { seed: 8 });
    expect(a).toBe(b);
    expect(a).not.toBe(c);
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
    const widths = [...result.svg.matchAll(/plate-layer-waterline" d="[^"]*" fill="none" stroke="var\(--scene-map-sea\)" stroke-width="([\d.]+)" stroke-opacity="([\d.]+)"/g)].map((m) => [Number(m[1]), Number(m[2])]);
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
