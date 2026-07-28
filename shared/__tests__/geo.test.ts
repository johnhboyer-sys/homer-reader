import { describe, expect, it } from 'vitest';
import { project, unproject, fitViewport, viewportFromBBox, type Viewport } from '../lib/geo';

const AEGEAN: [number, number][] = [
  [37.9, 23.7],
  [36.4, 25.4],
  [38.42, 20.71], // Ithaca-ish
];

const TROAD: [number, number][] = [
  [39.957, 26.239], // Troy
  [39.1, 26.6],
];

describe('project / unproject', () => {
  it('round-trips Aegean coordinates through project then unproject', () => {
    const viewport = fitViewport(AEGEAN.map((coords) => ({ coords })));
    for (const coords of AEGEAN) {
      const px = project(coords, viewport);
      const back = unproject(px, viewport);
      expect(back[0]).toBeCloseTo(coords[0], 9);
      expect(back[1]).toBeCloseTo(coords[1], 9);
    }
  });

  it('round-trips Troad coordinates through project then unproject', () => {
    const viewport = fitViewport(TROAD.map((coords) => ({ coords })));
    for (const coords of TROAD) {
      const px = project(coords, viewport);
      const back = unproject(px, viewport);
      expect(back[0]).toBeCloseTo(coords[0], 9);
      expect(back[1]).toBeCloseTo(coords[1], 9);
    }
  });
});

describe('viewportFromBBox', () => {
  it('maps the top-left corner [maxLat, minLon] to pixel [0, 0] when bbox aspect matches size', () => {
    // Aspect ratio of size (400/200 = 2) matches lonSpan*cos(centerLat)/latSpan
    // when we pick a bbox whose raw aspect (before cos-correction) is tuned
    // for it: centerLat = 40, cos(40deg) ~= 0.766.
    const centerLat = 40;
    const cosLat = Math.cos((centerLat * Math.PI) / 180);
    const latSpan = 4;
    const width = 400;
    const height = 200;
    const lonSpan = (width / height) * latSpan / cosLat; // makes scaleX === scaleY
    const bbox: [number, number, number, number] = [
      centerLat - latSpan / 2,
      -lonSpan / 2,
      centerLat + latSpan / 2,
      lonSpan / 2,
    ];
    const vp = viewportFromBBox(bbox, [width, height]);

    const topLeft = project([bbox[2], bbox[1]], vp); // [maxLat, minLon]
    expect(topLeft[0]).toBeCloseTo(0, 9);
    expect(topLeft[1]).toBeCloseTo(0, 9);

    const bottomRight = project([bbox[0], bbox[3]], vp); // [minLat, maxLon]
    expect(bottomRight[0]).toBeCloseTo(width, 9);
    expect(bottomRight[1]).toBeCloseTo(height, 9);
  });

  it('fits inside and centers (letterboxes) rather than distorting when bbox aspect does not match size', () => {
    // A tall/narrow bbox squeezed into a wide/short size: exact-corner mapping
    // is impossible without a non-uniform scale, which Viewport doesn't carry
    // (see the comment on viewportFromBBox in geo.ts). Assert the weaker,
    // real invariant instead: the box is centered, undistorted (uniform
    // scale), and entirely contained within size.
    const bbox: [number, number, number, number] = [36, 20, 44, 22]; // latSpan 8, lonSpan 2
    const size: [number, number] = [400, 200];
    const vp = viewportFromBBox(bbox, size);

    expect(vp.centerLat).toBeCloseTo(40, 9);
    expect(vp.centerLon).toBeCloseTo(21, 9);
    expect(vp.width).toBe(400);
    expect(vp.height).toBe(200);

    // Both bbox corners land inside the canvas (letterboxed, not clipped).
    const topLeft = project([bbox[2], bbox[1]], vp);
    const bottomRight = project([bbox[0], bbox[3]], vp);
    for (const [x, y] of [topLeft, bottomRight]) {
      expect(x).toBeGreaterThanOrEqual(-1e-6);
      expect(x).toBeLessThanOrEqual(size[0] + 1e-6);
      expect(y).toBeGreaterThanOrEqual(-1e-6);
      expect(y).toBeLessThanOrEqual(size[1] + 1e-6);
    }

    // The projected box is centered on the canvas.
    const midX = (topLeft[0] + bottomRight[0]) / 2;
    const midY = (topLeft[1] + bottomRight[1]) / 2;
    expect(midX).toBeCloseTo(size[0] / 2, 6);
    expect(midY).toBeCloseTo(size[1] / 2, 6);
  });
});

describe('longitude compression', () => {
  it('at latitude ~40, a 1deg longitude span projects to ~cos(40deg) of the pixels a 1deg latitude span does', () => {
    const viewport: Viewport = {
      width: 400,
      height: 400,
      centerLat: 40,
      centerLon: 25,
      latSpan: 10,
      lonSpan: 10,
      scale: 20, // px per (cos-corrected) degree
    };
    const [x0] = project([40, 25], viewport);
    const [x1] = project([40, 26], viewport); // +1 degree longitude
    const lonPx = Math.abs(x1 - x0);

    const [, y0] = project([40, 25], viewport);
    const [, y1] = project([41, 25], viewport); // +1 degree latitude
    const latPx = Math.abs(y1 - y0);

    const ratio = lonPx / latPx;
    const expected = Math.cos((40 * Math.PI) / 180); // ~0.766
    expect(ratio).toBeCloseTo(expected, 6);
  });
});

describe('fitViewport (moved from scenemap.ts — regression guard)', () => {
  it('enforces a minimum extent for a lone pin instead of zooming to a point', () => {
    const troy = { coords: [39.957, 26.239] as [number, number] };
    const viewport = fitViewport([troy]);
    expect(viewport.latSpan).toBeGreaterThanOrEqual(3); // DEFAULT_FIT_VIEWPORT_OPTIONS.minExtentDeg
    expect(viewport.lonSpan).toBeGreaterThanOrEqual(3);
    expect(viewport.centerLat).toBeCloseTo(troy.coords[0], 6);
    expect(viewport.centerLon).toBeCloseTo(troy.coords[1], 6);
  });

  it('a custom minExtentDeg is honored', () => {
    const troy = { coords: [39.957, 26.239] as [number, number] };
    const viewport = fitViewport([troy], { minExtentDeg: 8 });
    expect(viewport.latSpan).toBeGreaterThanOrEqual(8);
    expect(viewport.lonSpan).toBeGreaterThanOrEqual(8);
  });

  it('spans grow to cover two widely separated pins, with padding', () => {
    const troy = { coords: [39.957, 26.239] as [number, number] };
    const cyclops = { coords: [37.75, 15.02] as [number, number] };
    const viewport = fitViewport([troy, cyclops]);
    const rawLatSpan = Math.abs(troy.coords[0] - cyclops.coords[0]);
    expect(viewport.latSpan).toBeGreaterThan(rawLatSpan); // padding was added
  });

  it('ignores unlocatable places (no coords) without throwing, falling back to a finite center', () => {
    const noCoords = { coords: undefined };
    expect(() => fitViewport([noCoords])).not.toThrow();
    const viewport = fitViewport([noCoords]);
    expect(Number.isFinite(viewport.centerLat)).toBe(true);
    expect(Number.isFinite(viewport.centerLon)).toBe(true);
  });
});
