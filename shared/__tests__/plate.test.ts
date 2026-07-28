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
  type Plate,
  type PlatePlace,
} from '../lib/plate';

const SEED_PLATE_PATH = '../apparatus/plates/trojan-plain.json';

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
    const viewport = viewportFromBBox(testPlate.bbox, testPlate.size);

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
    const viewport = viewportFromBBox(testPlate.bbox, testPlate.size);
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
    const viewport = viewportFromBBox(testPlate.bbox, testPlate.size);
    const camera = computeCamera(testPlate, viewport, ['does-not-exist']);
    expect(camera).toEqual({ scale: 1, tx: 0, ty: 0 });
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
