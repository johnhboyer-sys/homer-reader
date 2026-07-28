// Pure library for build-time illustrated SVG "plates" — larger, hand-drawn-
// looking Landmark-style panel maps (the Trojan plain, the Troad, the Troy
// citadel, Achilles' shield), as opposed to shared/lib/scenemap.ts's small
// per-scene context-panel maps. Plate *geometry* is authored in
// apparatus/plates/<id>.json (see docs/APPARATUS-SCHEMAS.md) either as real
// [lat, lon] pairs (`kind: "geographic"`, projected through the SAME
// equirectangular projection scenemap.ts and the gazetteer pins use — see
// shared/lib/geo.ts) or as unit [u, v] pairs in 0..1 (`kind: "schematic"`,
// for panels with no defensible real-world coordinates, e.g. a shield
// device). This module is the RENDERER only: given already-authored plate
// geometry and a set of gazetteer places, it projects and draws. The actual
// map geometry (real coastlines, real river courses) is a later phase — this
// module works against whatever geometry the plate JSON already contains,
// however provisional.
//
// No DOM, no file I/O, no Math.random()/clock reads — pure data-in,
// string-out transforms, same posture as scenemap.ts, maps.ts, genealogy.ts.
// Determinism is a hard requirement (rebuild diffs must not churn): every
// primitive with a stochastic "hand-drawn" look derives all randomness from
// the plate's own `seed` field via the small seeded PRNG below.
//
// Theming: every fill/stroke in the emitted SVG is a CSS custom-property
// reference (var(--...)), never a literal colour, so the plate recolors for
// free across the site's light/dark/Aegean-Wine-dark theme layers (see
// shared/styles/global.css). Reused existing tokens: --scene-map-land
// (parchment ground), --scene-map-sea / --scene-map-coast (water/coast
// linework — the same "water" concept as the scene-map inset), --flaxman-ink
// (already named for exactly this "engraving ink, light ground" plate-art
// role — see global.css's .book-plate comment), --accent / --accent-light /
// --text-mid (certainty-tier pin styling, matching scenemap.ts's language).
// One genuinely new concept has no existing token: a translucent area tint
// for `region`/`band` layers (e.g. "the Achaean camp") — introduced here as
// --plate-tint; a later phase defines its value in global.css.
// --flaxman-hachure (2026-07-28, contrast fix) is a SEPARATE token from
// --flaxman-ink, used only by the relief/hachure fill: --flaxman-ink is
// itself alpha-composited in dark theme (see its own global.css comment —
// "ink A: bone, subtle, not inverted"), so stacking a fixed fill-opacity on
// top of it (the old approach) multiplied two alphas together and produced
// nearly double the rendered contrast in light vs dark for the identical
// declaration. --flaxman-hachure bakes the intended ink shade in as an
// OPAQUE colour per theme instead, tuned so the two themes' rendered
// contrast against --scene-map-land is comparable (see global.css).

import { project, viewportFromBBox } from './geo';
import type { LatLon, Viewport } from './geo';

export type { Viewport } from './geo';

export type Certainty = 'certain' | 'traditional' | 'speculative' | 'mythical';

export type PlateKind = 'geographic' | 'schematic';

export type LayerKind =
  | 'coast'
  | 'river'
  | 'relief'
  | 'shipRow'
  | 'wall'
  | 'route'
  | 'region'
  | 'band';

const LAYER_KINDS: readonly LayerKind[] = [
  'coast',
  'river',
  'relief',
  'shipRow',
  'wall',
  'route',
  'region',
  'band',
];

// A flat [x, y] pair — [lat, lon] on a geographic plate, [u, v] (0..1) on a
// schematic one. Named distinctly from geo.ts's LatLon because on a
// schematic plate it is NOT a lat/lon.
export type PlatePoint = [number, number];

export interface PlateSource {
  cite: string;
  url?: string;
}

export interface PlateLayer {
  id: string;
  kind: LayerKind;
  placeId?: string;
  note?: string;
  sources?: PlateSource[];
  default?: 'on' | 'off';
  style?: string;
  width?: number;
  shading?: string;
  rows?: number;
  count?: number;
  rings?: PlatePoint[][];
  path?: PlatePoint[];
  polygon?: PlatePoint[];
  baseline?: PlatePoint[];
  trace?: PlatePoint[];
}

export interface Plate {
  id: string;
  title: string;
  kind: PlateKind;
  status: string;
  seed?: number;
  bbox: [number, number, number, number]; // [minLat, minLon, maxLat, maxLon]
  size: [number, number]; // [widthPx, heightPx]
  layers: PlateLayer[];
}

// Mirrors the fields of apparatus/places.json this module needs, trimmed the
// same way scenemap.ts's ScenePlace is — deliberately NOT imported from
// maps.ts/places.json (a concurrent, unstable lane as of this writing).
// `plateAnchors`/`positionBasis` mirror the pairing documented in
// docs/APPARATUS-SCHEMAS.md: the honesty mechanism for placing a pin on a
// SCHEMATIC plate (unit space) that has no defensible real-world coords.
export interface PlatePlace {
  id: string;
  name: string;
  coords?: LatLon;
  certainty?: Certainty;
  plateAnchors?: Record<string, [number, number]>;
  positionBasis?: 'conjectural';
}

export interface PlateOptions {
  /** Prefix for internal element ids (clipPath). Set distinctly per instance when inlining more than one plate on the same page. */
  idPrefix?: string;
}

const DEFAULT_PLATE_OPTIONS: Required<PlateOptions> = {
  idPrefix: 'plate',
};

// A drawn layer or pin, in already-projected plate-pixel space — lets a
// caller (computeCamera, or a future component) reason about "where is
// feature X" without re-projecting or re-parsing the SVG string.
export interface RenderedFeature {
  id: string;
  type: 'layer' | 'place';
  kind: string; // layer.kind for a layer; place.certainty (default 'certain') for a place
  bbox: [number, number, number, number]; // [minX, minY, maxX, maxY] in plate-pixel space
}

export interface PlateResult {
  svg: string;
  viewport: Viewport;
  features: RenderedFeature[];
  unlocated: PlatePlace[];
}

export interface Camera {
  scale: number;
  tx: number;
  ty: number;
}

export interface CameraOptions {
  /** Extra room left around the focused features' bbox, as a fraction of that bbox's own width/height. */
  padFraction?: number;
  /** Upper bound on `scale`, so a focus set that resolves to a single point (or a tight cluster) doesn't zoom toward infinity. */
  maxScale?: number;
  /** Gazetteer places `focusIds` may also match, by place id — resolved through the same honesty rules as renderPlate (see resolvePlacePosition): a place with no defensible position on this plate contributes nothing. */
  places?: PlatePlace[];
}

const DEFAULT_CAMERA_OPTIONS: Required<CameraOptions> = {
  padFraction: 0.12,
  maxScale: 8,
  places: [],
};

// ── parsePlate ───────────────────────────────────────────────────────────

function fail(msg: string): never {
  throw new Error(`plate: ${msg}`);
}

function isFiniteNumber(n: unknown): n is number {
  return typeof n === 'number' && Number.isFinite(n);
}

function isPoint(p: unknown): p is PlatePoint {
  return Array.isArray(p) && p.length === 2 && isFiniteNumber(p[0]) && isFiniteNumber(p[1]);
}

// Checks every coordinate pair in every geometry field of `layer` lies
// within `bbox` (geographic plates only — on a schematic plate the bbox is
// documented as not a coordinate constraint, so this is skipped there).
function assertPointsInBBox(
  layer: PlateLayer,
  bbox: [number, number, number, number],
): void {
  const [minLat, minLon, maxLat, maxLon] = bbox;
  const eps = 1e-9;
  const check = (p: PlatePoint) => {
    const [lat, lon] = p;
    if (lat < minLat - eps || lat > maxLat + eps || lon < minLon - eps || lon > maxLon + eps) {
      fail(
        `coordinate [${lat}, ${lon}] in layer "${layer.id}" is outside the plate bbox [${bbox.join(', ')}]`,
      );
    }
  };
  for (const ring of layer.rings ?? []) for (const p of ring) check(p);
  for (const p of layer.path ?? []) check(p);
  for (const p of layer.polygon ?? []) check(p);
  for (const p of layer.baseline ?? []) check(p);
  for (const p of layer.trace ?? []) check(p);
}

function parseLayer(raw: unknown, plate: { kind: PlateKind; bbox: [number, number, number, number] }): PlateLayer {
  if (!raw || typeof raw !== 'object') fail('a layer must be an object');
  const l = raw as Record<string, unknown>;
  if (typeof l.id !== 'string' || !l.id) fail('a layer is missing its id');
  if (typeof l.kind !== 'string' || !LAYER_KINDS.includes(l.kind as LayerKind)) {
    fail(`unknown layer kind "${String(l.kind)}" in layer "${l.id}"`);
  }

  const geometryArray = (key: string): PlatePoint[] | undefined => {
    if (l[key] === undefined) return undefined;
    if (!Array.isArray(l[key]) || !(l[key] as unknown[]).every(isPoint)) {
      fail(`layer "${l.id}" has a malformed "${key}" field`);
    }
    return l[key] as PlatePoint[];
  };
  const ringsRaw = l.rings;
  let rings: PlatePoint[][] | undefined;
  if (ringsRaw !== undefined) {
    if (!Array.isArray(ringsRaw) || !ringsRaw.every((r) => Array.isArray(r) && r.every(isPoint))) {
      fail(`layer "${l.id}" has a malformed "rings" field`);
    }
    rings = ringsRaw as PlatePoint[][];
  }

  const layer: PlateLayer = {
    id: l.id,
    kind: l.kind as LayerKind,
    placeId: typeof l.placeId === 'string' ? l.placeId : undefined,
    note: typeof l.note === 'string' ? l.note : undefined,
    sources: Array.isArray(l.sources) ? (l.sources as PlateSource[]) : undefined,
    default: l.default === 'on' || l.default === 'off' ? l.default : undefined,
    style: typeof l.style === 'string' ? l.style : undefined,
    width: isFiniteNumber(l.width) ? l.width : undefined,
    shading: typeof l.shading === 'string' ? l.shading : undefined,
    rows: isFiniteNumber(l.rows) ? l.rows : undefined,
    count: isFiniteNumber(l.count) ? l.count : undefined,
    rings,
    path: geometryArray('path'),
    polygon: geometryArray('polygon'),
    baseline: geometryArray('baseline'),
    trace: geometryArray('trace'),
  };

  if (plate.kind === 'geographic') assertPointsInBBox(layer, plate.bbox);
  return layer;
}

// Validates + narrows an already-JSON.parsed plate payload (an
// apparatus/plates/<id>.json file). No file I/O — callers do the reading.
// Throws a distinct, named Error for each malformed-input class documented
// in docs/APPARATUS-SCHEMAS.md's plates/<id>.json section.
export function parsePlate(data: unknown): Plate {
  if (!data || typeof data !== 'object') fail('plate data must be an object');
  const d = data as Record<string, unknown>;

  if (typeof d.id !== 'string' || !d.id) fail('missing id');
  if (typeof d.title !== 'string' || !d.title) fail('missing title');
  if (d.kind !== 'geographic' && d.kind !== 'schematic') fail(`unknown plate kind "${String(d.kind)}"`);
  if (typeof d.status !== 'string' || !d.status) fail('missing status');
  if (!Array.isArray(d.bbox) || d.bbox.length !== 4 || !d.bbox.every(isFiniteNumber)) {
    fail('missing bbox');
  }
  const bbox = d.bbox as [number, number, number, number];
  if (bbox[0] >= bbox[2] || bbox[1] >= bbox[3]) fail('bbox is degenerate (min >= max)');
  if (!Array.isArray(d.size) || d.size.length !== 2 || !d.size.every(isFiniteNumber)) {
    fail('missing size');
  }
  const size = d.size as [number, number];
  if (!Array.isArray(d.layers)) fail('missing layers');
  // Already runtime-checked above (fail() is `never`, so any value other
  // than these two literals has already thrown); cast rather than lean on
  // cross-statement narrowing of a Record<string, unknown> index access.
  const kind = d.kind as PlateKind;

  const layers = (d.layers as unknown[]).map((raw) => parseLayer(raw, { kind, bbox }));

  return {
    id: d.id,
    title: d.title,
    kind,
    status: d.status,
    seed: isFiniteNumber(d.seed) ? d.seed : undefined,
    bbox,
    size,
    layers,
  };
}

// ── Seeded PRNG (mulberry32) ────────────────────────────────────────────
// ~5 lines, no dependency, deterministic: same seed -> same stream, forever.
// Never Math.random(). Used ONLY by the stochastic "hand-drawn" primitives
// (hachure, stipple) — every other primitive is purely geometric.

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return function next(): number {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Combines the plate's own seed with a per-layer salt (FNV-1a over the
// layer id) so different layers on the same plate don't draw identical
// hachure/stipple patterns, while staying fully deterministic.
function fnv1a(str: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

function deriveSeed(seed: number, salt: string): number {
  return (seed ^ fnv1a(salt)) >>> 0;
}

// ── Small helpers (own copies — see report: scenemap.ts's escapeXml/round1 are private) ──

function escapeXml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function round1(n: number): number {
  return Math.round(n * 10) / 10;
}

function circlePathD(cx: number, cy: number, r: number): string {
  // Two-arc trick for a filled circle expressed as path data (keeps every
  // primitive returning the same "path d string" shape).
  const x0 = round1(cx - r);
  const x1 = round1(cx + r);
  const y = round1(cy);
  const rr = round1(r);
  return `M ${x0} ${y} A ${rr} ${rr} 0 1 0 ${x1} ${y} A ${rr} ${rr} 0 1 0 ${x0} ${y} Z`;
}

// ── Draw primitives — the source of the "illustrated" look ─────────────
// Pure functions, pixel-space in, SVG path `d` string out. hachure/stipple
// take a `seed` and derive ALL randomness from it (mulberry32); the rest are
// purely geometric (no stochastic element, so no seed parameter).

export interface HachureOptions {
  seed: number;
  spacing?: number; // px between successive stroke lines, stepped along the ridge axis
  angleDeg?: number; // override for the downhill (stroke) direction; default: computed from the polygon's own shape (see below)
  weight?: number; // ink-stroke width at a stroke's fattest point, px
  jitter?: number; // px of positional wobble, for a hand-drawn feel
}

// The polygon's principal (long) axis angle, via a closed-form 2x2 PCA
// (eigen-decomposition of the vertex covariance matrix). Real cartographic
// hachures run DOWNHILL, perpendicular to the contour/ridge line; lacking
// real elevation data (a later, cartography-phase input), this module's
// standing assumption is that a hand-authored relief polygon's own long
// axis approximates its ridge line, so strokes are drawn perpendicular to
// it, spaced out along it — a reasonable placeholder reading, not a claimed
// survey. `angleDeg` lets a caller override this once real ridge data
// exists.
function principalAxisAngle(polygon: PlatePoint[]): number {
  const n = polygon.length;
  let cx = 0;
  let cy = 0;
  for (const [x, y] of polygon) {
    cx += x;
    cy += y;
  }
  cx /= n;
  cy /= n;
  let sxx = 0;
  let syy = 0;
  let sxy = 0;
  for (const [x, y] of polygon) {
    const dx = x - cx;
    const dy = y - cy;
    sxx += dx * dx;
    syy += dy * dy;
    sxy += dx * dy;
  }
  return 0.5 * Math.atan2(2 * sxy, sxx - syy);
}

// One tapered "ink stroke" — a thin filled lens, fat at the middle and
// pointed at both ends (the classic engraver's trick for a variable-weight
// line without CSS variable-width strokes) — running from parameter t0 to
// t1 along `dir` from `p0`, at most `halfWidth` px wide, with per-sample
// jitter for an organic edge.
function inkStrokePath(p0: PlatePoint, dir: PlatePoint, nrm: PlatePoint, t0: number, t1: number, halfWidth: number, rand: () => number): string {
  const samples = 4;
  const top: [number, number][] = [];
  const bot: [number, number][] = [];
  for (let i = 0; i <= samples; i++) {
    const u = i / samples;
    const t = t0 + (t1 - t0) * u;
    const w = halfWidth * Math.sin(Math.PI * u) * (0.85 + rand() * 0.3);
    const bx = p0[0] + dir[0] * t;
    const by = p0[1] + dir[1] * t;
    top.push([bx + nrm[0] * w, by + nrm[1] * w]);
    bot.push([bx - nrm[0] * w, by - nrm[1] * w]);
  }
  return pathD([...top, ...bot.reverse()], true);
}

// Cartographic hill-shading: strokes run downhill (perpendicular to the
// polygon's long/ridge axis), spaced out along that ridge, clipped to
// `polygon` (a simple, possibly non-convex, closed ring of pixel points —
// closing edge implied). Density and stroke weight both peak at the ridge
// (the polygon's own centre line) and fall off toward its flanks — "density
// carries steepness," standing in for real slope data per the module
// comment above. Each stroke is a tapered ink shape (see inkStrokePath),
// not a uniform-width line, so the shading reads as a landform rather than
// a texture swatch. Returns a single filled `d` string (fill-rule
// nonzero — every stroke is its own small closed lens).
export function hachure(polygon: PlatePoint[], opts: HachureOptions): string {
  if (polygon.length < 3) return '';
  const spacing = opts.spacing ?? 7;
  const angleRad = opts.angleDeg !== undefined ? (opts.angleDeg * Math.PI) / 180 : principalAxisAngle(polygon) + Math.PI / 2;
  const baseHalfWidth = (opts.weight ?? 1.6) / 2;
  const jitter = opts.jitter ?? 1.2;
  const rand = mulberry32(opts.seed);

  const dir: PlatePoint = [Math.cos(angleRad), Math.sin(angleRad)];
  const nrm: PlatePoint = [-Math.sin(angleRad), Math.cos(angleRad)];

  const cx = polygon.reduce((s, p) => s + p[0], 0) / polygon.length;
  const cy = polygon.reduce((s, p) => s + p[1], 0) / polygon.length;

  // Range of the polygon's projection onto the normal axis (the ridge
  // axis), so the family of parallel stroke-lines fully covers the shape.
  let minK = Infinity;
  let maxK = -Infinity;
  for (const [x, y] of polygon) {
    const k = (x - cx) * nrm[0] + (y - cy) * nrm[1];
    if (k < minK) minK = k;
    if (k > maxK) maxK = k;
  }
  const maxAbsK = Math.max(Math.abs(minK), Math.abs(maxK), 1e-6);

  const parts: string[] = [];
  const edges: [PlatePoint, PlatePoint][] = polygon.map((p, i) => [p, polygon[(i + 1) % polygon.length]]);

  for (let k = minK; k <= maxK; k += spacing) {
    const ridgeFactor = Math.abs(k) / maxAbsK; // 0 at the ridge, 1 at the flank
    if (rand() < ridgeFactor * 0.55) continue; // density falls off toward the flank

    const p0: PlatePoint = [cx + nrm[0] * k, cy + nrm[1] * k];
    const ts: number[] = [];
    for (const [a, b] of edges) {
      const ex = b[0] - a[0];
      const ey = b[1] - a[1];
      const denom = dir[0] * ey - dir[1] * ex;
      if (Math.abs(denom) < 1e-12) continue; // parallel to this edge
      const t = ((a[0] - p0[0]) * ey - (a[1] - p0[1]) * ex) / denom;
      const s = ((a[0] - p0[0]) * dir[1] - (a[1] - p0[1]) * dir[0]) / denom;
      if (s >= 0 && s <= 1) ts.push(t);
    }
    ts.sort((a, b) => a - b);
    for (let i = 0; i + 1 < ts.length; i += 2) {
      const spanLen = ts[i + 1] - ts[i];
      // Strokes fall short of the polygon boundary — more so toward the
      // flank — rather than running flush to the edge: "thin out toward
      // the edges of the polygon."
      const trim = spanLen * (0.08 + ridgeFactor * 0.24);
      const t0 = ts[i] + trim + (rand() - 0.5) * jitter * 0.4;
      const t1 = ts[i + 1] - trim + (rand() - 0.5) * jitter * 0.4;
      if (t1 - t0 < 1) continue;
      const halfWidth = baseHalfWidth * (1 - ridgeFactor * 0.65) * (0.7 + rand() * 0.6);
      parts.push(inkStrokePath(p0, dir, nrm, t0, t1, halfWidth, rand));
    }
  }
  return parts.join(' ');
}

export interface StippleOptions {
  seed: number;
  spacing?: number; // px between dots along the path, at the densest (innermost) band
  radius?: number; // dot radius at the densest band
  bands?: number; // number of parallel bands fading away from the path (default 3)
  bandSpacing?: number; // px between bands, perpendicular to the path
  side?: 1 | -1 | 0; // which perpendicular side fades outward; 0 (default) = both sides
}

// The classic layered/stippled coastline: dots hug the path itself and fade
// — sparser, smaller, further apart — moving away from it on each side, so
// the line reads as a coast dissolving into open sea rather than a ruled
// row of evenly spaced dots. Each of `bands` parallel offset bands is
// sparser and lighter than the last; positions within a band are lightly
// seeded-jittered for a scattered, hand-stippled feel.
export function stipple(path: PlatePoint[], opts: StippleOptions): string {
  if (path.length < 2) return '';
  const spacing = opts.spacing ?? 5;
  const radius = opts.radius ?? 1.1;
  const bands = opts.bands ?? 3;
  const bandSpacing = opts.bandSpacing ?? 3.2;
  const sides: (1 | -1)[] = opts.side === undefined || opts.side === 0 ? [1, -1] : [opts.side];
  const rand = mulberry32(opts.seed);

  const parts: string[] = [];
  for (let i = 0; i + 1 < path.length; i++) {
    const [x1, y1] = path[i];
    const [x2, y2] = path[i + 1];
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy);
    if (len < 1e-9) continue;
    const ux = dx / len;
    const uy = dy / len;
    const nx = -uy;
    const ny = ux;

    for (const side of sides) {
      for (let b = 0; b < bands; b++) {
        const fade = b / bands; // 0 right at the line, ->1 at the outermost band
        const bandDensity = 1 - fade * 0.82;
        const stepSpacing = spacing / Math.max(bandDensity, 0.12);
        const bandRadius = Math.max(radius * (1 - fade * 0.55), 0.35);
        const offsetBase = b * bandSpacing * (0.7 + rand() * 0.6);
        const steps = Math.max(1, Math.round(len / stepSpacing));
        for (let s = 0; s <= steps; s++) {
          if (rand() > bandDensity) continue; // further seeded thinning per band
          const along = (s / steps) * len + (rand() - 0.5) * spacing * 0.5;
          const across = side * (offsetBase + (rand() - 0.5) * bandSpacing * 0.5);
          const cx = x1 + ux * along + nx * across;
          const cy = y1 + uy * along + ny * across;
          parts.push(circlePathD(cx, cy, bandRadius));
        }
      }
    }
  }
  return parts.join(' ');
}

export interface WaterlineOptions {
  seed: number;
  /** Cumulative px offsets from the shore, closest line first. Default: Huffman's growing-gap sequence (2 / 2.6 / 3.4 / 4.4 — each gap ~1.3x the last). */
  offsets?: number[];
  /** Per-line stroke weight, px, matching `offsets` by index (must be the same length). */
  weights?: number[];
  /** Per-line stroke opacity, matching `offsets` by index (must be the same length). */
  opacities?: number[];
  /** px of positional wobble per vertex, for a hand-drawn feel. Kept small: the growing gaps themselves read as organic (Huffman's point), jitter is a light finish, not the mechanism. */
  jitter?: number;
}

export interface WaterlineStroke {
  d: string;
  width: number;
  opacity: number;
}

// Huffman, "On Waterlines: Arguments for their Employment, Advice on their
// Generation," Cartographic Perspectives 66 (2010): 23-30. Each successive
// gap should grow by roughly 1.3x (monospaced gaps read as stylised;
// growing gaps read as waves compressing toward the shore); the shore-to-
// first-line gap is the variable that matters most; lines are confined to a
// narrow band near the coast, not filled across the whole basin.
const DEFAULT_WATERLINE_OFFSETS = [2, 2.6, 3.4, 4.4];
const DEFAULT_WATERLINE_WEIGHTS = [0.55, 0.42, 0.3, 0.2];
const DEFAULT_WATERLINE_OPACITIES = [0.85, 0.65, 0.48, 0.32];

// Whole-ring winding side, the same shoelace-style pseudo-area trick
// wallGlyph uses for its tick side (see that function's own comment): the
// open polyline is treated as if closed so ONE consistent side is chosen
// for the whole ring, rather than flipping per vertex. wallGlyph's ticks
// face the ring's enclosed (inland) side; waterlines face the opposite
// (seaward) side, so this is that same sign, negated.
function ringSeaSide(ring: [number, number][]): 1 | -1 {
  let signedArea = 0;
  for (let i = 0; i + 1 < ring.length; i++) {
    signedArea += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1];
  }
  return signedArea >= 0 ? -1 : 1;
}

// Offsets one ring perpendicular to itself by `dist` px on `side`. Each
// vertex's normal is the (normalized) average of its two adjacent edge
// normals — a simple polyline offset, not a full polygon-offset algorithm,
// so tight concavities CAN self-intersect (accepted per this module's
// standing "hand-drawn, not survey-grade" posture — see the file header).
// Consecutive duplicate points are dropped first (degenerate edges); if
// fewer than 2 usable points remain, returns undefined rather than emitting
// a garbage/zero-length path.
function offsetRing(
  ring: [number, number][],
  dist: number,
  side: 1 | -1,
  rand: () => number,
  jitter: number,
): [number, number][] | undefined {
  const pts: [number, number][] = [];
  for (const p of ring) {
    const last = pts[pts.length - 1];
    if (!last || Math.hypot(p[0] - last[0], p[1] - last[1]) > 1e-6) pts.push(p);
  }
  if (pts.length < 2) return undefined;

  const edgeNormals: [number, number][] = [];
  for (let i = 0; i + 1 < pts.length; i++) {
    const [x1, y1] = pts[i];
    const [x2, y2] = pts[i + 1];
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy);
    edgeNormals.push([-dy / len, dx / len]);
  }

  const out: [number, number][] = [];
  for (let i = 0; i < pts.length; i++) {
    let nx: number;
    let ny: number;
    if (i === 0) {
      [nx, ny] = edgeNormals[0];
    } else if (i === pts.length - 1) {
      [nx, ny] = edgeNormals[edgeNormals.length - 1];
    } else {
      const [n1x, n1y] = edgeNormals[i - 1];
      const [n2x, n2y] = edgeNormals[i];
      let ax = n1x + n2x;
      let ay = n1y + n2y;
      const alen = Math.hypot(ax, ay);
      // Adjacent edges facing opposite ways (a sharp cusp) average to
      // ~[0,0] — fall back to the incoming edge's own normal rather than an
      // undefined direction.
      if (alen < 1e-9) {
        ax = n1x;
        ay = n1y;
      } else {
        ax /= alen;
        ay /= alen;
      }
      nx = ax;
      ny = ay;
    }
    const wobble = 1 + (rand() - 0.5) * jitter;
    out.push([pts[i][0] + nx * dist * side * wobble, pts[i][1] + ny * dist * side * wobble]);
  }
  return out;
}

// Concentric waterlines echoing `rings` (already-projected coast rings, same
// pixel-space convention as hachure/stipple's inputs), per Huffman 2010:
// several lines at growing cumulative offsets from the shore, each thinner
// and fainter than the last. A ring that degenerates at a given offset (see
// offsetRing) simply contributes nothing to that line; a line with no
// surviving ring contributes nothing to the result, rather than an
// empty/garbage stroke. NEVER call this for a river layer — waves do not
// start in midstream and push out (Huffman); renderLayer enforces this
// structurally by only reaching this function from the 'coast' case.
export function waterlines(rings: [number, number][][], opts: WaterlineOptions): WaterlineStroke[] {
  const offsets = opts.offsets ?? DEFAULT_WATERLINE_OFFSETS;
  const weights = opts.weights ?? DEFAULT_WATERLINE_WEIGHTS;
  const opacities = opts.opacities ?? DEFAULT_WATERLINE_OPACITIES;
  if (offsets.length !== weights.length || offsets.length !== opacities.length) {
    fail('waterlines: offsets/weights/opacities must have equal length');
  }
  const jitter = opts.jitter ?? 0.06;
  const rand = mulberry32(opts.seed);
  const sides = rings.map(ringSeaSide);

  const strokes: WaterlineStroke[] = [];
  for (let i = 0; i < offsets.length; i++) {
    const dParts: string[] = [];
    for (let r = 0; r < rings.length; r++) {
      const offset = offsetRing(rings[r], offsets[i], sides[r], rand, jitter);
      if (!offset) continue;
      dParts.push(pathD(offset, false));
    }
    if (dParts.length === 0) continue;
    strokes.push({ d: dParts.join(' '), width: weights[i], opacity: opacities[i] });
  }
  return strokes;
}

export interface ShipRowOptions {
  seed: number;
}

// Small stylized beached-ship glyphs — a curved hull with a raised, kicked
// prow, plus a mast — spaced along `baseline`, stacked in `rows` ranks
// offset perpendicular to it. Each ship's proportions, position, and mast
// height are lightly seeded-jittered so a row of many ships doesn't read as
// a stamped pattern, while staying fully deterministic for a given seed.
// Returns a single filled `d` string (every hull/mast is its own small
// closed shape).
export function shipRow(baseline: [PlatePoint, PlatePoint], rows: number, count: number, opts: ShipRowOptions): string {
  const [[x1, y1], [x2, y2]] = baseline;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy);
  if (len < 1e-9 || rows < 1 || count < 1) return '';
  const ux = dx / len;
  const uy = dy / len;
  const nx = -uy;
  const ny = ux;
  const rand = mulberry32(opts.seed);

  const baseHalfLen = Math.min(len / count, 18) * 0.42;
  const rankSpacing = baseHalfLen * 0.9;
  const slotWidth = len / count;

  // A hull is authored in local (u = along the ship, v = across it) space,
  // then mapped into world space via the same affine frame (dir, nrm) used
  // everywhere else in this module. Quadratic Bezier control points are
  // affine-invariant, so the curves stay exact after the transform.
  const toWorld = (bx: number, by: number, u: number, v: number): [number, number] => [
    round1(bx + ux * u + nx * v),
    round1(by + uy * u + ny * v),
  ];

  const parts: string[] = [];
  for (let r = 0; r < rows; r++) {
    const rankOffset = r * rankSpacing * (1.6 + rand() * 0.3);
    for (let i = 0; i < count; i++) {
      const jitterAlong = (rand() - 0.5) * slotWidth * 0.35;
      const t = (i + 0.5) / count;
      const bx = x1 + ux * (len * t + jitterAlong) + nx * rankOffset;
      const by = y1 + uy * (len * t + jitterAlong) + ny * rankOffset;

      const L = baseHalfLen * (0.82 + rand() * 0.36);
      const W = L * 0.3 * (0.85 + rand() * 0.3);
      const prowLift = W * (1.1 + rand() * 0.5);
      const prowKick = L * (0.12 + rand() * 0.08);
      const sternRise = W * (0.25 + rand() * 0.25);

      const A = toWorld(bx, by, -L, 0); // stern base
      const Cctrl = toWorld(bx, by, 0, W * 1.15); // belly bulge control
      const C = toWorld(bx, by, L * 0.68, 0); // bow base
      const D = toWorld(bx, by, L + prowKick, -prowLift); // raised, kicked prow tip
      const Ectrl = toWorld(bx, by, 0, -W * 0.55); // sheer-line control
      const E = toWorld(bx, by, -L * 0.86, -sternRise); // stern top

      parts.push(`M ${A[0]} ${A[1]} Q ${Cctrl[0]} ${Cctrl[1]} ${C[0]} ${C[1]} L ${D[0]} ${D[1]} Q ${Ectrl[0]} ${Ectrl[1]} ${E[0]} ${E[1]} Z`);

      // Mast: a thin filled needle, not a stroked tick, so it stays part
      // of the same fill-only path as the hull.
      const mastHalf = W * 0.16;
      const mastHeight = W * 1.6 * (0.7 + rand() * 0.6);
      const M1 = toWorld(bx, by, -mastHalf, -W * 0.1);
      const M2 = toWorld(bx, by, mastHalf, -W * 0.1);
      const M3 = toWorld(bx, by, 0, -W * 0.1 - mastHeight);
      parts.push(`M ${M1[0]} ${M1[1]} L ${M2[0]} ${M2[1]} L ${M3[0]} ${M3[1]} Z`);
    }
  }
  return parts.join(' ');
}

export interface WallGlyphResult {
  line: string; // the trace itself
  ticks: string; // the perpendicular tick marks, on ONE consistent side — see below
}

// A fortification line with regular tick marks on its inner side (the
// standard convention), along `trace` — purely geometric, no randomness.
// Which side is "inner" is COMPUTED, not guessed: the sign of the trace's
// own shoelace-style pseudo-area (treating the open polyline as if it were
// closed) tells us which way it curls on the whole, and every segment's
// tick is drawn on that same side, consistently, rather than flipping
// per-segment or defaulting to an arbitrary left/right.
export function wallGlyph(trace: PlatePoint[]): WallGlyphResult {
  if (trace.length < 2) return { line: '', ticks: '' };

  let signedArea = 0;
  for (let i = 0; i + 1 < trace.length; i++) {
    signedArea += trace[i][0] * trace[i + 1][1] - trace[i + 1][0] * trace[i][1];
  }
  const side = signedArea >= 0 ? 1 : -1;

  const tickSpacing = 12;
  const tickLen = 4;
  const lineParts: string[] = [`M ${round1(trace[0][0])} ${round1(trace[0][1])}`];
  const tickParts: string[] = [];
  let carry = 0;

  for (let i = 0; i + 1 < trace.length; i++) {
    const [x1, y1] = trace[i];
    const [x2, y2] = trace[i + 1];
    lineParts.push(`L ${round1(x2)} ${round1(y2)}`);
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy);
    if (len < 1e-9) continue;
    const ux = dx / len;
    const uy = dy / len;
    const nx = -uy * side;
    const ny = ux * side;
    let d = tickSpacing - carry;
    while (d < len) {
      const tx = x1 + ux * d;
      const ty = y1 + uy * d;
      const t1x = round1(tx + nx * tickLen);
      const t1y = round1(ty + ny * tickLen);
      tickParts.push(`M ${round1(tx)} ${round1(ty)} L ${t1x} ${t1y}`);
      d += tickSpacing;
    }
    carry = len - (d - tickSpacing);
  }
  return { line: lineParts.join(' '), ticks: tickParts.join(' ') };
}

export interface TumulusOptions {
  radius?: number;
}

// A burial-mound glyph: a low dome in section (a filled/stroked profile,
// not a circle) sitting on `point`, with two shorter nested arcs inside
// suggesting the dome's curvature — the standard engraved-contour shorthand
// for shading in a monochrome-ink plate (no second colour available or
// wanted, per the theming rule). Purely geometric, no randomness. Returns a
// single `d` string of open (stroked, not filled) subpaths.
export function tumulus(point: PlatePoint, opts: TumulusOptions = {}): string {
  const r = opts.radius ?? 7;
  const [x, y] = point;
  const domeHeight = r * 0.6;

  const outer = `M ${round1(x - r)} ${round1(y)} Q ${round1(x)} ${round1(y - domeHeight)} ${round1(x + r)} ${round1(y)}`;

  const y1 = y - domeHeight * 0.18;
  const r1 = r * 0.62;
  const h1 = domeHeight * 0.55;
  const inner1 = `M ${round1(x - r1)} ${round1(y1)} Q ${round1(x)} ${round1(y1 - h1)} ${round1(x + r1)} ${round1(y1)}`;

  const y2 = y - domeHeight * 0.38;
  const r2 = r * 0.32;
  const h2 = domeHeight * 0.4;
  const inner2 = `M ${round1(x - r2)} ${round1(y2)} Q ${round1(x)} ${round1(y2 - h2)} ${round1(x + r2)} ${round1(y2)}`;

  const base = `M ${round1(x - r)} ${round1(y)} L ${round1(x + r)} ${round1(y)}`;

  return `${outer} ${inner1} ${inner2} ${base}`;
}

// ── Certainty pin styling ───────────────────────────────────────────────
// Mirrors scenemap.ts's certaintyPinStyle (private there) so a place reads
// with the same certainty-tier visual language on a plate as on a scene map
// and on app/src/components/maps/LandmarkMap.svelte: certain = solid,
// traditional = ring, speculative = outline, mythical = dashed outline.

interface PinStyle {
  fill: string;
  fillOpacity: number;
  stroke: string;
  dasharray?: string;
}

function certaintyPinStyle(certainty: Certainty | undefined): PinStyle {
  switch (certainty) {
    case 'traditional':
      return { fill: 'var(--accent)', fillOpacity: 0.16, stroke: 'var(--accent)' };
    case 'speculative':
      return { fill: 'none', fillOpacity: 0, stroke: 'var(--text-mid)' };
    case 'mythical':
      return { fill: 'none', fillOpacity: 0, stroke: 'var(--text-mid)', dasharray: '2 2' };
    case 'certain':
    default:
      return { fill: 'var(--accent)', fillOpacity: 0.9, stroke: 'var(--accent)' };
  }
}

// `conjectural` marks a pin resolved via a schematic plate's `plateAnchors`
// (see resolvePlacePosition) rather than real coordinates — the honesty
// register from docs/APPARATUS-SCHEMAS.md. It renders in its own dashed
// stroke (distinct from the certainty-tier dash used for `mythical`) plus a
// `data-position-basis="conjectural"` attribute a consuming component can
// key off for e.g. an "approximate" label.
const CONJECTURAL_DASHARRAY = '1 3';

function pinMarkup(id: string, name: string, x: number, y: number, style: PinStyle, conjectural: boolean, r = 5.5): string {
  const headCy = y - r * 1.7;
  const tip = `M ${round1(x - r * 0.55)} ${round1(y - r * 0.9)} L ${round1(x + r * 0.55)} ${round1(y - r * 0.9)} L ${round1(x)} ${round1(y)} Z`;
  const dasharray = conjectural ? CONJECTURAL_DASHARRAY : style.dasharray;
  const dash = dasharray ? ` stroke-dasharray="${dasharray}"` : '';
  const basisAttr = conjectural ? ' data-position-basis="conjectural"' : '';
  return (
    `<g data-place-id="${escapeXml(id)}"${basisAttr}>` +
    `<title>${escapeXml(name)}</title>` +
    `<circle cx="${round1(x)}" cy="${round1(headCy)}" r="${r}" fill="${style.fill}" fill-opacity="${style.fillOpacity}" stroke="${style.stroke}" stroke-width="1.25"${dash}/>` +
    `<path d="${tip}" fill="${style.fill}" fill-opacity="${style.fillOpacity}" stroke="${style.stroke}" stroke-width="1.25"${dash}/>` +
    `</g>`
  );
}

function pinBBox(x: number, y: number, r = 5.5): [number, number, number, number] {
  return [x - r, y - r * 2.7, x + r, y];
}

// ── Projection ───────────────────────────────────────────────────────────

// Projects one plate point into plate-pixel space. On a `geographic` plate
// the point is a real [lat, lon] pair, run through geo.ts's project() — the
// same projection that places gazetteer pins, per this module's whole
// premise. On a `schematic` plate the point is a unit [u, v] pair (0..1,
// top-left origin, same sense as SVG y-down) scaled directly by plate.size.
function projectPoint(plate: Plate, p: PlatePoint, viewport: Viewport): [number, number] {
  if (plate.kind === 'schematic') {
    return [p[0] * plate.size[0], p[1] * plate.size[1]];
  }
  return project(p as LatLon, viewport);
}

function projectPoints(plate: Plate, pts: PlatePoint[], viewport: Viewport): [number, number][] {
  return pts.map((p) => projectPoint(plate, p, viewport));
}

function bboxOf(points: [number, number][]): [number, number, number, number] {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const [x, y] of points) {
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
  }
  return [minX, minY, maxX, maxY];
}

function pathD(points: [number, number][], close: boolean): string {
  if (points.length === 0) return '';
  const d = points
    .map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${round1(x)},${round1(y)}`)
    .join(' ');
  return close ? `${d} Z` : d;
}

// Resolves a place's plate-pixel position, or undefined if it has no
// defensible location on THIS plate. Apparatus honesty (CLAUDE.md hard
// rule): never force-pin. Geographic plates need `coords`; schematic plates
// need a `plateAnchors[plate.id]` unit anchor keyed for THIS plate, AND
// `positionBasis: "conjectural"` — docs/APPARATUS-SCHEMAS.md documents the
// two as required together (the pipeline validator, apparatus_places.py,
// rejects one without the other). A `plateAnchors` entry present without the
// matching `positionBasis` is NOT quietly honoured here either — it renders
// as unlocated, same as having no anchor at all.
function resolvePlacePosition(plate: Plate, place: PlatePlace, viewport: Viewport): [number, number] | undefined {
  if (plate.kind === 'schematic') {
    if (place.positionBasis !== 'conjectural') return undefined;
    const anchor = place.plateAnchors?.[plate.id];
    return anchor ? projectPoint(plate, anchor, viewport) : undefined;
  }
  return place.coords ? projectPoint(plate, place.coords, viewport) : undefined;
}

// ── Line-weight hierarchy ────────────────────────────────────────────────
// A small, deliberately short list of stroke widths (px, not colours — the
// theming rule governs colour, not weight) so the plate reads with a clear
// visual hierarchy rather than many near-identical linework weights: the
// coastline is the heaviest mark on the sheet; rivers next; built features
// (walls, routes) lighter still; fine marks (wall tick shorthand) lightest.
const STROKE_WEIGHT = {
  coast: 2,
  river: 1.4,
  wall: 1.15,
  route: 1,
  tick: 0.75,
} as const;

// ── Layer rendering ──────────────────────────────────────────────────────

function renderLayer(plate: Plate, layer: PlateLayer, viewport: Viewport): { markup: string; feature: RenderedFeature } | undefined {
  const allPixelPoints: [number, number][] = [];
  const collect = (pts: PlatePoint[] | undefined) => {
    if (!pts) return [];
    const px = projectPoints(plate, pts, viewport);
    allPixelPoints.push(...px);
    return px;
  };

  let markup = '';
  const seed = deriveSeed(plate.seed ?? 0, layer.id);

  switch (layer.kind) {
    case 'coast': {
      const rings = layer.rings;
      if (!rings?.length) return undefined;
      const ringsPx = rings.map((ring) => {
        const px = projectPoints(plate, ring, viewport);
        allPixelPoints.push(...px);
        return px;
      });
      if (layer.style === 'stipple') {
        const dParts = ringsPx.map((px) => stipple(px, { seed }));
        markup = `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-coast" d="${dParts.join(' ')}" fill="var(--flaxman-ink)" stroke="none"/>`;
      } else if (layer.style === 'waterline') {
        const coastD = ringsPx.map((px) => pathD(px, false)).join(' ');
        const strokes = waterlines(ringsPx, { seed });
        const strokeMarkup = strokes
          .map(
            (ln, i) =>
              `<path data-feature-id="${escapeXml(layer.id)}-waterline-${i}" class="plate-layer plate-layer-waterline" d="${ln.d}" fill="none" stroke="var(--scene-map-sea)" stroke-width="${ln.width}" stroke-opacity="${ln.opacity}"/>`,
          )
          .join('');
        markup =
          `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-coast" d="${coastD}" fill="none" stroke="var(--scene-map-coast)" stroke-width="${layer.width ?? STROKE_WEIGHT.coast}"/>` +
          strokeMarkup;
      } else {
        const d = ringsPx.map((px) => pathD(px, false)).join(' ');
        markup = `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-coast" d="${d}" fill="none" stroke="var(--scene-map-coast)" stroke-width="${layer.width ?? STROKE_WEIGHT.coast}"/>`;
      }
      break;
    }
    case 'river': {
      const px = collect(layer.path);
      if (px.length < 2) return undefined;
      markup = `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-river" d="${pathD(px, false)}" fill="none" stroke="var(--scene-map-sea)" stroke-width="${layer.width ?? STROKE_WEIGHT.river}" stroke-linecap="round"/>`;
      break;
    }
    case 'relief': {
      const px = collect(layer.polygon);
      if (px.length < 3) return undefined;
      const d = hachure(px, { seed });
      markup = `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-relief" d="${d}" fill="var(--flaxman-hachure)" stroke="none"/>`;
      break;
    }
    case 'shipRow': {
      const px = collect(layer.baseline);
      if (px.length < 2) return undefined;
      const d = shipRow([px[0], px[1]], layer.rows ?? 1, layer.count ?? 1, { seed });
      markup = `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-shiprow" d="${d}" fill="var(--flaxman-ink)" stroke="none"/>`;
      break;
    }
    case 'wall': {
      const px = collect(layer.trace);
      if (px.length < 2) return undefined;
      const { line, ticks } = wallGlyph(px);
      markup =
        `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-wall" d="${line}" fill="none" stroke="var(--flaxman-ink)" stroke-width="${STROKE_WEIGHT.wall}"/>` +
        (ticks
          ? `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-wall-ticks" d="${ticks}" fill="none" stroke="var(--flaxman-ink)" stroke-width="${STROKE_WEIGHT.tick}"/>`
          : '');
      break;
    }
    case 'route': {
      const px = collect(layer.path);
      if (px.length < 2) return undefined;
      markup = `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-route" d="${pathD(px, false)}" fill="none" stroke="var(--accent-light)" stroke-width="${STROKE_WEIGHT.route}" stroke-dasharray="1 4" stroke-linecap="round"/>`;
      break;
    }
    case 'region':
    case 'band': {
      const px = collect(layer.polygon);
      if (px.length < 3) return undefined;
      markup = `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-${layer.kind}" d="${pathD(px, true)}" fill="var(--plate-tint)" fill-opacity="0.35" stroke="var(--plate-tint)" stroke-width="0.8"/>`;
      break;
    }
    default:
      return undefined;
  }

  if (allPixelPoints.length === 0) return undefined;
  return {
    markup,
    feature: { id: layer.id, type: 'layer', kind: layer.kind, bbox: bboxOf(allPixelPoints) },
  };
}

// ── Full render ──────────────────────────────────────────────────────────

// Assembles a plate's layers + gazetteer pins into one self-contained SVG
// string. Pure and deterministic: identical inputs always produce an
// identical `svg` string (see hachure/stipple's seeded PRNG above).
export function renderPlate(plate: Plate, places: PlatePlace[], options: PlateOptions = {}): PlateResult {
  const opts = { ...DEFAULT_PLATE_OPTIONS, ...options };
  const viewport = viewportFromBBox(plate.bbox, plate.size);
  const [width, height] = plate.size;

  const features: RenderedFeature[] = [];
  const layerMarkup: string[] = [];
  for (const layer of plate.layers) {
    const rendered = renderLayer(plate, layer, viewport);
    if (!rendered) continue;
    layerMarkup.push(rendered.markup);
    features.push(rendered.feature);
  }

  const located: PlatePlace[] = [];
  const unlocated: PlatePlace[] = [];
  const pinMarkupParts: string[] = [];
  for (const place of places) {
    const pos = resolvePlacePosition(plate, place, viewport);
    if (!pos) {
      unlocated.push(place);
      continue;
    }
    located.push(place);
    const [x, y] = pos;
    const style = certaintyPinStyle(place.certainty);
    // Any place resolved on a schematic plate got there via plateAnchors +
    // positionBasis: "conjectural" (see resolvePlacePosition) — there is no
    // other path to a position on a schematic plate.
    const conjectural = plate.kind === 'schematic';
    pinMarkupParts.push(pinMarkup(place.id, place.name, x, y, style, conjectural));
    features.push({ id: place.id, type: 'place', kind: place.certainty ?? 'certain', bbox: pinBBox(x, y) });
  }

  const clipId = `${opts.idPrefix}-clip`;
  const ariaLabel = escapeXml(plate.title);

  const svg =
    `<svg viewBox="0 0 ${width} ${height}" width="100%" height="100%" role="img" aria-label="${ariaLabel}" xmlns="http://www.w3.org/2000/svg">` +
    `<defs><clipPath id="${clipId}"><rect x="0" y="0" width="${width}" height="${height}"/></clipPath></defs>` +
    `<g clip-path="url(#${clipId})">` +
    `<rect class="plate-ground" x="0" y="0" width="${width}" height="${height}" fill="var(--scene-map-land)"/>` +
    layerMarkup.join('') +
    pinMarkupParts.join('') +
    `</g>` +
    `</svg>`;

  return { svg, viewport, features, unlocated };
}

// ── Camera ───────────────────────────────────────────────────────────────

// Computes a pure {scale, tx, ty} value that, applied as a CSS transform to
// a group already in plate-pixel space (out = in * scale + [tx, ty]), frames
// the geometry named in `focusIds` inside the canvas. The library never
// touches the DOM — a component applies this as `transform:
// translate(tx,ty) scale(scale)` (note CSS transform order: scale first
// then translate reads right-to-left in `transform`, i.e. the string is
// `translate(${tx}px, ${ty}px) scale(${scale})`).
//
// `focusIds` is matched against TWO id spaces: `plate.layers` (by layer id,
// as before) and `options.places` (by place id — pass the same PlatePlace[]
// given to renderPlate, or a relevant subset; the Chart Room's use case is
// framing an Iliad scene on ITS OWN gazetteer places, which are not layers).
// An id matching neither contributes nothing rather than throwing. A place
// resolves through the same `resolvePlacePosition` honesty rules renderPlate
// uses: no `coords` (geographic) or no `plateAnchors[plate.id]` +
// `positionBasis: "conjectural"` (schematic) means it contributes nothing —
// never an invented position. If NO id resolves to any geometry (including
// the all-ids-unlocated case), this returns the identity camera
// `{scale:1,tx:0,ty:0}`, showing the whole plate rather than a degenerate or
// NaN transform. A focus set that resolves to a single point (or several
// coincident points) is padded by a fixed pixel amount rather than
// `padFraction * 0`, and the final scale is clamped to `options.maxScale`,
// so a lone pin can't zoom toward infinity.
export function computeCamera(
  plate: Plate,
  viewport: Viewport,
  focusIds: string[],
  options: CameraOptions = {},
): Camera {
  const opts = { ...DEFAULT_CAMERA_OPTIONS, ...options };
  const idSet = new Set(focusIds);
  const points: [number, number][] = [];

  for (const layer of plate.layers) {
    if (!idSet.has(layer.id)) continue;
    const geometries: (PlatePoint[] | undefined)[] = [
      layer.path,
      layer.polygon,
      layer.baseline,
      layer.trace,
      ...(layer.rings ?? []),
    ];
    for (const geo of geometries) {
      if (!geo) continue;
      points.push(...projectPoints(plate, geo, viewport));
    }
  }

  for (const place of opts.places) {
    if (!idSet.has(place.id)) continue;
    const pos = resolvePlacePosition(plate, place, viewport);
    if (pos) points.push(pos);
  }

  if (points.length === 0) return { scale: 1, tx: 0, ty: 0 };

  const [minX, minY, maxX, maxY] = bboxOf(points);
  const bboxW = Math.max(maxX - minX, 1e-6);
  const bboxH = Math.max(maxY - minY, 1e-6);
  // A focus bbox that collapsed to (near-)zero width/height — one point, or
  // several coincident ones — gets a fixed plate-pixel pad instead of
  // `span * padFraction` (which would itself be ~0): otherwise paddedW/H
  // stays microscopic and `scale` below explodes before the maxScale clamp
  // even has a normal-sized denominator to reason about.
  const DEGENERATE_PAD_PX = 24;
  const padW = bboxW <= 1e-6 ? DEGENERATE_PAD_PX : bboxW * opts.padFraction;
  const padH = bboxH <= 1e-6 ? DEGENERATE_PAD_PX : bboxH * opts.padFraction;
  const paddedW = bboxW + padW * 2;
  const paddedH = bboxH + padH * 2;

  const scale = Math.min(viewport.width / paddedW, viewport.height / paddedH, opts.maxScale);
  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  const tx = viewport.width / 2 - scale * centerX;
  const ty = viewport.height / 2 - scale * centerY;

  return { scale, tx, ty };
}
