import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  project,
  unproject,
  fitViewport,
  coastlinePathData,
  parseCoastline,
  placeLabel,
  renderRoute,
  renderSceneMap,
  DEFAULT_SCENE_MAP_OPTIONS,
  type ScenePlace,
  type Coastline,
  type Viewport,
} from '../lib/scenemap';

const COASTLINE_PATH = '../sources/naturalearth/mediterranean-coastline.json';
const SIZE_BUDGET_BYTES = 150 * 1024;

const cyclops: ScenePlace = { id: 'cyclopes-land', name: 'Land of the Cyclopes', certainty: 'traditional', coords: [37.75, 15.02] };
const troy: ScenePlace = { id: 'troy', name: 'Troy', certainty: 'certain', coords: [39.957, 26.239] };
const ithaca: ScenePlace = { id: 'ithaca', name: 'Ithaca', certainty: 'certain', coords: [38.42, 20.71] };
const ogygia: ScenePlace = { id: 'ogygia', name: 'Ogygia', certainty: 'mythical' }; // no coords, per apparatus/places.json
const scheria: ScenePlace = { id: 'scheria', name: 'Scheria', certainty: 'traditional', coords: [39.62, 19.92] };

// A tiny synthetic coastline (independent of the real vendored data) for
// tests that only care about the projection/fitting/labeling math.
const fakeCoastline: Coastline = {
  bbox: [10, 30, 30, 45],
  rings: [
    [[36, 15], [36.5, 15.5], [36.2, 16], [36, 15]], // near Sicily, closed ring
    [[41, 5], [41.2, 5.2], [41, 5.4], [41, 5]], // far west, should get filtered out of a Sicily-zoomed viewport
  ],
};

describe('project / unproject', () => {
  it('round-trips a coordinate through project then unproject', () => {
    const viewport = fitViewport([cyclops, troy]);
    for (const place of [cyclops, troy, ithaca]) {
      const px = project(place.coords!, viewport);
      const back = unproject(px, viewport);
      expect(back[0]).toBeCloseTo(place.coords![0], 6);
      expect(back[1]).toBeCloseTo(place.coords![1], 6);
    }
  });

  it('projects the viewport center to the middle of the canvas', () => {
    const viewport = fitViewport([cyclops]);
    const [x, y] = project([viewport.centerLat, viewport.centerLon], viewport);
    expect(x).toBeCloseTo(viewport.width / 2, 6);
    expect(y).toBeCloseTo(viewport.height / 2, 6);
  });

  it('north is up: a place north of center projects to a smaller y', () => {
    const viewport = fitViewport([troy, ithaca]);
    const [, yNorth] = project([viewport.centerLat + 1, viewport.centerLon], viewport);
    const [, ySouth] = project([viewport.centerLat - 1, viewport.centerLon], viewport);
    expect(yNorth).toBeLessThan(ySouth);
  });
});

describe('fitViewport', () => {
  it('enforces a minimum extent for a lone pin instead of zooming to a point', () => {
    const viewport = fitViewport([troy]);
    expect(viewport.latSpan).toBeGreaterThanOrEqual(DEFAULT_SCENE_MAP_OPTIONS.minExtentDeg);
    expect(viewport.lonSpan).toBeGreaterThanOrEqual(DEFAULT_SCENE_MAP_OPTIONS.minExtentDeg);
    expect(viewport.centerLat).toBeCloseTo(troy.coords![0], 6);
    expect(viewport.centerLon).toBeCloseTo(troy.coords![1], 6);
  });

  it('a custom minExtentDeg is honored', () => {
    const viewport = fitViewport([troy], { minExtentDeg: 8 });
    expect(viewport.latSpan).toBeGreaterThanOrEqual(8);
    expect(viewport.lonSpan).toBeGreaterThanOrEqual(8);
  });

  it('spans grow to cover two widely separated pins, with padding', () => {
    const viewport = fitViewport([troy, cyclops]); // Troad to Sicily: wide span
    const rawLatSpan = Math.abs(troy.coords![0] - cyclops.coords![0]);
    expect(viewport.latSpan).toBeGreaterThan(rawLatSpan); // padding was added
  });

  it('ignores unlocatable places (no coords) without throwing', () => {
    expect(() => fitViewport([ogygia])).not.toThrow();
    const viewport = fitViewport([ogygia]);
    // Falls back to a sensible fixed center rather than NaN.
    expect(Number.isFinite(viewport.centerLat)).toBe(true);
    expect(Number.isFinite(viewport.centerLon)).toBe(true);
  });

  it('both pins land inside the fitted canvas', () => {
    const viewport = fitViewport([troy, cyclops]);
    for (const place of [troy, cyclops]) {
      const [x, y] = project(place.coords!, viewport);
      expect(x).toBeGreaterThanOrEqual(0);
      expect(x).toBeLessThanOrEqual(viewport.width);
      expect(y).toBeGreaterThanOrEqual(0);
      expect(y).toBeLessThanOrEqual(viewport.height);
    }
  });
});

describe('placeLabel', () => {
  const viewport: Viewport = fitViewport([troy]);

  it('keeps the label within the viewBox for a pin near the right edge', () => {
    const label = placeLabel(
      { id: 'x', name: 'A Very Long Place Name Indeed', coords: [0, 0] },
      viewport.width - 5,
      viewport.height / 2,
      viewport,
    );
    const estWidth = label.text.length * DEFAULT_SCENE_MAP_OPTIONS.fontSizePx * 0.56;
    if (label.anchor === 'start') {
      expect(label.x + estWidth).toBeLessThanOrEqual(viewport.width + 0.01);
    } else {
      expect(label.x - estWidth).toBeGreaterThanOrEqual(-0.01);
    }
  });

  it('keeps the label within the viewBox for a pin near the top-left corner', () => {
    const label = placeLabel({ id: 'x', name: 'Ismarus', coords: [0, 0] }, 3, 3, viewport);
    expect(label.y).toBeGreaterThanOrEqual(0);
    expect(label.y).toBeLessThanOrEqual(viewport.height);
  });

  it('is deterministic for the same inputs', () => {
    const a = placeLabel(troy, 100, 100, viewport);
    const b = placeLabel(troy, 100, 100, viewport);
    expect(a).toEqual(b);
  });
});

describe('coastlinePathData', () => {
  it('only includes rings that intersect the viewport (filters far-away rings)', () => {
    const viewport = fitViewport([cyclops]); // zoomed on Sicily
    const { ringCount, d } = coastlinePathData(fakeCoastline, viewport);
    expect(ringCount).toBe(1); // the Sicily ring only; the far-west ring is dropped
    expect(d).toContain('M');
    expect(d).toContain('Z');
  });

  it('returns an empty path with zero rings when nothing intersects', () => {
    const viewport = fitViewport([{ id: 'far', name: 'Far', coords: [0, 0] }], { minExtentDeg: 1 });
    const { ringCount, d } = coastlinePathData(fakeCoastline, viewport);
    expect(ringCount).toBe(0);
    expect(d).toBe('');
  });
});

describe('renderRoute', () => {
  const viewport = fitViewport([cyclops, troy]);

  it('renders a full dotted arc + arrowhead when both endpoints are located', () => {
    const result = renderRoute({ from: troy, to: cyclops }, viewport);
    expect(result.status).toBe('full');
    expect(result.pathD).toMatch(/^M .* Q .* /);
    expect(result.arrowD).toBeTruthy();
  });

  it('degrades to broken-origin when the origin has no coords (Ogygia -> Scheria)', () => {
    const result = renderRoute({ from: ogygia, to: scheria }, fitViewport([scheria]));
    expect(result.status).toBe('broken-origin');
    expect(result.brokenD).toBeTruthy();
    // Never invents a from-coordinate: no arc, only a short local stub.
    expect(result.pathD).toBeUndefined();
  });

  it('degrades to broken-destination when the destination has no coords', () => {
    const result = renderRoute({ from: troy, to: ogygia }, fitViewport([troy]));
    expect(result.status).toBe('broken-destination');
    expect(result.pathD).toBeUndefined();
    expect(result.brokenD).toBeUndefined();
  });

  it('is none when no leg is passed', () => {
    expect(renderRoute(undefined, viewport).status).toBe('none');
  });

  it('is deterministic for the same leg + viewport', () => {
    const a = renderRoute({ from: troy, to: cyclops }, viewport);
    const b = renderRoute({ from: troy, to: cyclops }, viewport);
    expect(a).toEqual(b);
  });
});

describe('renderSceneMap', () => {
  it('skips an unlocatable place without throwing, and reports it separately', () => {
    expect(() => renderSceneMap([cyclops, ogygia], fakeCoastline)).not.toThrow();
    const result = renderSceneMap([cyclops, ogygia], fakeCoastline);
    expect(result.located.map((p) => p.id)).toEqual(['cyclopes-land']);
    expect(result.unlocated.map((p) => p.id)).toEqual(['ogygia']);
  });

  it('lone-pin case still produces a valid, non-degenerate SVG', () => {
    const result = renderSceneMap([troy], fakeCoastline);
    expect(result.svg).toContain('<svg');
    expect(result.svg).toContain('viewBox="0 0');
    expect(result.svg).toMatch(/<circle/); // the pin head
  });

  it('every emitted color is a CSS custom property, never a hardcoded hex', () => {
    const result = renderSceneMap([troy, cyclops], fakeCoastline, {}, { from: troy, to: cyclops });
    const hexColors = result.svg.match(/#[0-9a-fA-F]{3,8}/g);
    expect(hexColors).toBeNull();
    expect(result.svg).toContain('var(--accent)');
    expect(result.svg).toContain('var(--scene-map-sea)');
    expect(result.svg).toContain('var(--scene-map-land)');
    expect(result.svg).toContain('var(--scene-map-coast)');
    expect(result.svg).toContain('<rect class="scene-map-sea"');
    expect(result.svg).toContain('fill="var(--scene-map-sea)"');
    expect(result.svg).toContain('<path class="scene-map-land"');
    expect(result.svg).toContain('fill="var(--scene-map-land)"');
  });

  it('escapes a place name containing XML-sensitive characters', () => {
    const hostile: ScenePlace = { id: 'x', name: 'Odysseus\'s <Crew> & "Men"', coords: [38, 21] };
    const result = renderSceneMap([hostile], fakeCoastline);
    expect(result.svg).not.toContain('<Crew>');
    expect(result.svg).toContain('&lt;Crew&gt;');
    expect(result.svg).toContain('&amp;');
  });

  it('is fully deterministic: identical input produces identical SVG', () => {
    const a = renderSceneMap([cyclops, troy], fakeCoastline, {}, { from: troy, to: cyclops });
    const b = renderSceneMap([cyclops, troy], fakeCoastline, {}, { from: troy, to: cyclops });
    expect(a.svg).toBe(b.svg);
  });

  it('two different idPrefix options avoid clipPath id collisions', () => {
    const a = renderSceneMap([troy], fakeCoastline, { idPrefix: 'panel-a' });
    const b = renderSceneMap([troy], fakeCoastline, { idPrefix: 'panel-b' });
    expect(a.svg).toContain('id="panel-a-clip"');
    expect(b.svg).toContain('id="panel-b-clip"');
  });
});

describe('vendored Mediterranean coastline (sources/naturalearth/)', () => {
  const raw = readFileSync(COASTLINE_PATH, 'utf-8');

  it('is under the 150KB size budget', () => {
    expect(Buffer.byteLength(raw, 'utf-8')).toBeLessThan(SIZE_BUDGET_BYTES);
  });

  it('parses into a well-formed Coastline via parseCoastline', () => {
    const coastline = parseCoastline(JSON.parse(raw));
    expect(coastline.bbox).toHaveLength(4);
    expect(coastline.rings.length).toBeGreaterThan(10);
    for (const ring of coastline.rings.slice(0, 5)) {
      expect(ring.length).toBeGreaterThanOrEqual(3);
      for (const [lat, lon] of ring) {
        expect(typeof lat).toBe('number');
        expect(typeof lon).toBe('number');
      }
    }
  });

  it('renders a real scene map (Od. 9 Cyclopes) against the real vendored coastline', () => {
    const coastline = parseCoastline(JSON.parse(raw));
    const result = renderSceneMap([cyclops], coastline);
    expect(result.svg).toContain('<svg');
    expect(result.viewport.width).toBe(DEFAULT_SCENE_MAP_OPTIONS.width);
  });
});
