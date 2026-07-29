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
// (parchment ground — now only the DEFAULT ground; see `ground` on Plate),
// --scene-map-sea / --scene-map-coast (water fill / coast linework — the same
// "water" concept as the scene-map inset; running water is --plate-river, NOT
// --scene-map-sea, which is a fill and is near-black in dark theme), --flaxman-ink
// (already named for exactly this "engraving ink, light ground" plate-art
// role — see global.css's .book-plate comment), --accent / --accent-light /
// --text-mid (certainty-tier pin styling, matching scenemap.ts's language).
// One genuinely new concept has no existing token: a translucent area tint
// for `region`/`band` layers (e.g. "the Achaean camp") — introduced here as
// --plate-tint; a later phase defines its value in global.css.
// --plate-lagoon / --plate-marsh / --plate-plain / --plate-upland (2026-07-28)
// are the TERRAIN tokens: --plate-tint resolves to var(--accent-light), the
// site's wine wayfinding accent, and a `region` layer used to default to it —
// so every landform on the geographic plate was painted in the UI highlight
// colour ("it's just shapes"). Landforms now default to --plate-plain and a
// layer opts IN to the accent with `fill: "tint"`, which is the only role that
// colour ever had.
// --flaxman-hachure (2026-07-28, contrast fix) is a SEPARATE token from
// --flaxman-ink, used only by the relief/hachure fill: --flaxman-ink is
// itself alpha-composited in dark theme (see its own global.css comment —
// "ink A: bone, subtle, not inverted"), so stacking a fixed fill-opacity on
// top of it (the old approach) multiplied two alphas together and produced
// nearly double the rendered contrast in light vs dark for the identical
// declaration. --flaxman-hachure bakes the intended ink shade in as an
// OPAQUE colour per theme instead, tuned so the two themes' rendered
// contrast against --scene-map-land is comparable (see global.css).
// Follow-up (2026-07-28, same day): matching raw WCAG contrast ratio turned
// out not to be the same as matching PERCEIVED strength — light ink on a
// dark ground reads bolder than dark ink on a light ground at an identical
// measured ratio (irradiation), and this token's dark value was in fact
// measurably HIGHER-contrast than light's against the surface it actually
// renders on (--plate-upland: 6.95:1 dark vs 6.59:1 light), compounding the
// effect rather than offsetting it. Dark's hex is now deliberately
// under-contrasted relative to light's (still well clear of the 4.5:1
// floor) to compensate — see global.css's per-theme comments and the
// comparability test in plate.test.ts. Density/weight for the relief fill
// itself is handled separately, geometrically, by reliefHachureParams below
// — this token change is colour-only.

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
  | 'band'
  | 'tumulus';

const LAYER_KINDS: readonly LayerKind[] = [
  'coast',
  'river',
  'relief',
  'shipRow',
  'wall',
  'route',
  'region',
  'band',
  'tumulus',
];

// The only fill tokens a `region`/`band` layer's `fill` field may resolve
// to (gap 3: the "is this a body of water" honesty mechanism). Kept as a
// closed whitelist mapping data -> a fixed var(--...) reference, never a
// pass-through of the JSON value itself, so a hostile/malformed apparatus
// file can never inject arbitrary CSS into the emitted SVG (same posture
// as every other colour in this module — see the file header).
//
// `tint` is the decorative UI-accent wash (an apparatus zone, e.g. "the
// Achaean camp"); everything else is TERRAIN. The default is `plain`, not
// `tint` (2026-07-28): a landform is not a highlight, and defaulting to the
// accent is what painted the whole geographic plate wine-pink.
//
// `none` draws nothing at all: a lettering zone for a named tract of country
// whose extent nobody surveyed (see the `region` case in renderLayer).
const REGION_FILL_TOKENS = {
  tint: 'var(--plate-tint)',
  sea: 'var(--scene-map-sea)',
  lagoon: 'var(--plate-lagoon)',
  land: 'var(--scene-map-land)',
  marsh: 'var(--plate-marsh)',
  plain: 'var(--plate-plain)',
  none: 'none',
} as const;

type RegionFill = keyof typeof REGION_FILL_TOKENS;

const DEFAULT_REGION_FILL: RegionFill = 'plain';

// Terrain reads as ground, so it paints opaque; only the decorative `tint`
// wash stays translucent (it is meant to sit OVER terrain). `marsh` is a
// shade under opaque so a wetland reads as a damp overlay on the plain it
// covers rather than a hard-edged patch — the one place a partial alpha is
// the intended look rather than an accident (contrast is measured on the
// token itself, see shared/__tests__/plate-map-contrast.test.ts).
const REGION_FILL_OPACITY: Record<RegionFill, number> = {
  tint: 0.35,
  sea: 1,
  lagoon: 1,
  land: 1,
  // Marsh lowered from 0.9 to 0.55 (2026-07-29): with the hypsometric ramp
  // under it there is real terrain to be a damp overlay ON, and at 0.9 the
  // delta swamp read as a flat green wedge laid over the plain instead of as
  // wet ground within it. Its own outline is unchanged and it is still
  // plainly the greenest thing on the sheet.
  marsh: 0.55,
  plain: 1,
  none: 0,
};

// Water fills get the coast token as their edge (a shoreline), land fills a
// faint version of the same ink so a terrain patch has definition without
// competing with the real coastline.
const WATER_FILLS: ReadonlySet<RegionFill> = new Set<RegionFill>(['sea', 'lagoon']);

// What the bare sheet is, under every layer. A plate whose subject is a
// coast with the sea at its edge declares `ground: "sea"` and draws its
// landmasses as `region` layers with `fill: "land"`; a plate whose subject
// is an inland/mostly-dry extent (the Trojan plain) leaves the default and
// draws its water bodies as `region` layers with `fill: "sea"`/`"lagoon"`.
// Default 'land' — every plate authored before this field existed drew onto
// a land ground, so the default preserves them exactly.
export type PlateGround = 'land' | 'sea';

const GROUND_FILL_TOKENS: Record<PlateGround, string> = {
  land: 'var(--scene-map-land)',
  sea: 'var(--scene-map-sea)',
};

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
  /**
   * The name to letter onto the sheet for this feature. Optional: when it is
   * absent the renderer falls back to the gazetteer name of `placeId`, and
   * only when that place is not itself pinned on this plate (a feature is
   * lettered once, not twice — see renderPlate). Author it whenever the
   * gazetteer name is a catalogue entry rather than a map label ("The Bay of
   * Troy (the silted embayment)" is the former).
   */
  label?: string;
  note?: string;
  sources?: PlateSource[];
  default?: 'on' | 'off';
  style?: string;
  width?: number;
  shading?: string;
  rows?: number;
  count?: number;
  /** `region`/`band` only (gap 3): which fixed fill token to use. Default 'tint'. See REGION_FILL_TOKENS. */
  fill?: RegionFill;
  /**
   * `relief` only (2026-07-29): the contour level, in metres above sea level,
   * this body was cut at. Its presence is what switches the layer from the
   * hand-authored hachure register to the hypsometric one — a band with an
   * elevation is filled in the ramp step that elevation earns among the
   * elevations present on the SAME plate (see hypsometricLevels), and edged
   * with a hairline instead of hachured. A relief layer without it (the
   * schematic plain, the citadel) draws exactly as it always did.
   */
  elevation?: number;
  rings?: PlatePoint[][];
  path?: PlatePoint[];
  polygon?: PlatePoint[];
  baseline?: PlatePoint[];
  trace?: PlatePoint[];
}

// A schematic plate's concentric band (the Shield of Achilles). Mirrors
// docs/APPARATUS-SCHEMAS.md's `{id, title, greek, lines: [from, to],
// summary, ring}` shape. The pipeline validator (validate_plate) only
// checks `id` (non-empty, unique) — it does not type-check the rest of a
// band's fields — so parsePlate mirrors that same leniency rather than
// inventing stricter checks the Python side doesn't enforce (see parseBands).
export interface PlateBand {
  id: string;
  title: string;
  greek: string;
  lines: [number, number];
  summary: string;
  ring: number;
}

export interface Plate {
  id: string;
  title: string;
  kind: PlateKind;
  status: string;
  seed?: number;
  // Required for a `geographic` plate (it projects lat/lon through this
  // extent); absent for a `schematic` plate with no defensible bbox — see
  // parsePlate and the module header. May still be present on a schematic
  // plate (not forbidden, just not required), mirroring apparatus_places.py.
  bbox?: [number, number, number, number]; // [minLat, minLon, maxLat, maxLon]
  size: [number, number]; // [widthPx, heightPx]
  /** What the bare sheet is under every layer. See PlateGround. Default 'land'. */
  ground?: PlateGround;
  layers: PlateLayer[];
  // Schematic-only: concentric bands (see PlateBand). A schematic plate
  // declares `bands` or `layers` (or both); geographic plates never carry
  // this field.
  bands?: PlateBand[];
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
  // A place with NO defensible position at all on this plate (no coords /
  // no honest anchor — see resolvePlacePosition). Never pinned.
  unlocated: PlatePlace[];
  // A place WITH a defensible position, but one that projects outside this
  // plate's own canvas (0..width, 0..height) — it belongs on a different
  // sheet, not "nobody knows where it is." Deliberately a separate bucket
  // from `unlocated` (2026-07-28, finding 1): conflating "off this map"
  // with "no honest anchor" would itself be an apparatus-honesty bug — a
  // consuming component needs to say "not on this sheet" for one and
  // "not securely located" for the other. Never pinned.
  offCanvas: PlatePlace[];
  // A place with NO defensible pin position (same test as `unlocated`), but
  // that IS visibly drawn anyway because some rendered layer names it as
  // `placeId` — e.g. `wall-of-troy` is the placeId on every stretch of the
  // citadel's wall circuit, `pergamos` is the placeId on the summit region.
  // Kept OUT of `unlocated` and out of a fourth silent nowhere (2026-07-28):
  // "named, not drawn" is a specific, false claim about a place the map
  // plainly shows via its own linework, and a reader asking "is Pergamos on
  // this map?" deserves a yes, not an absence. Never pinned — this bucket
  // only ever holds places carried by geometry, not markers.
  drawnByLayer: PlatePlace[];
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

// The schematic-plate mirror of assertPointsInBBox: every coordinate pair
// in every geometry field must be a unit [u, v] pair in 0..1 — mirrors
// apparatus_places.py's validate_plate exactly (`0 <= a <= 1 and 0 <= b <=
// 1`), which is how that validator catches a lat/lon pair (tens of
// degrees) mistakenly authored on a schematic plate, with no separate
// "looks like lat/lon" heuristic needed (see that function's own comment).
function assertPointsInUnitRange(layer: PlateLayer): void {
  const eps = 1e-9;
  const check = (p: PlatePoint) => {
    const [u, v] = p;
    if (u < -eps || u > 1 + eps || v < -eps || v > 1 + eps) {
      fail(
        `coordinate [${u}, ${v}] in layer "${layer.id}" must be a unit [u, v] pair in 0..1 (schematic plate)`,
      );
    }
  };
  for (const ring of layer.rings ?? []) for (const p of ring) check(p);
  for (const p of layer.path ?? []) check(p);
  for (const p of layer.polygon ?? []) check(p);
  for (const p of layer.baseline ?? []) check(p);
  for (const p of layer.trace ?? []) check(p);
}

// Finding 3 (schema drift, 2026-07-28): `sources` used to pass through
// unvalidated (any array, any shape) — CLAUDE.md's apparatus-sourcing rule
// requires every sourced claim to carry its citation, so a malformed
// source is a data bug worth failing on, not silently accepting. Mirrors
// apparatus_places.py's `_validate_sources` exactly: every entry needs a
// non-empty `cite`; a `url`, if present, must be http(s).
function parseSources(raw: unknown, layerId: string): PlateSource[] | undefined {
  if (raw === undefined) return undefined;
  if (!Array.isArray(raw)) fail(`layer "${layerId}" has a malformed "sources" field`);
  return (raw as unknown[]).map((s, i) => {
    if (!s || typeof s !== 'object') fail(`layer "${layerId}" sources[${i}] must be an object`);
    const src = s as Record<string, unknown>;
    if (typeof src.cite !== 'string' || !src.cite.trim()) {
      fail(`layer "${layerId}" sources[${i}].cite must be a non-empty string`);
    }
    if (src.url !== undefined && (typeof src.url !== 'string' || !/^https?:\/\//i.test(src.url))) {
      fail(`layer "${layerId}" sources[${i}].url must be http(s)`);
    }
    return { cite: src.cite as string, url: typeof src.url === 'string' ? src.url : undefined };
  });
}

function parseLayer(raw: unknown, plate: { kind: PlateKind; bbox?: [number, number, number, number] }): PlateLayer {
  if (!raw || typeof raw !== 'object') fail('a layer must be an object');
  const l = raw as Record<string, unknown>;
  if (typeof l.id !== 'string' || !l.id) fail('a layer is missing its id');
  if (typeof l.kind !== 'string' || !LAYER_KINDS.includes(l.kind as LayerKind)) {
    fail(`unknown layer kind "${String(l.kind)}" in layer "${l.id}"`);
  }
  if (l.fill !== undefined && (typeof l.fill !== 'string' || !(l.fill in REGION_FILL_TOKENS))) {
    fail(`layer "${l.id}" has an unknown fill "${String(l.fill)}" (must be one of ${Object.keys(REGION_FILL_TOKENS).join(', ')})`);
  }
  // Finding 3 (schema drift, 2026-07-28): an invalid `default` used to be
  // silently dropped to undefined rather than rejected (the ternary below
  // only ever assigned 'on'/'off'/undefined — a typo like "true" vanished
  // with no error). Reject it, matching apparatus_places.py's
  // validate_plate ("default must be 'on' or 'off'").
  if (l.default !== undefined && l.default !== 'on' && l.default !== 'off') {
    fail(`layer "${l.id}" has an unknown default "${String(l.default)}" (must be "on" or "off")`);
  }
  // Mirrors apparatus_places.py's validate_plate: an elevation is a real
  // measurement off the DEM, so a non-numeric or negative one is a data
  // error, not something to coerce away. (Sea level itself, 0, is legal.)
  if (l.elevation !== undefined && !(isFiniteNumber(l.elevation) && l.elevation >= 0)) {
    fail(`layer "${l.id}" has a malformed "elevation" (must be a number >= 0)`);
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
    label: typeof l.label === 'string' && l.label.trim() ? l.label : undefined,
    note: typeof l.note === 'string' ? l.note : undefined,
    sources: parseSources(l.sources, l.id),
    default: l.default === 'on' || l.default === 'off' ? l.default : undefined,
    style: typeof l.style === 'string' ? l.style : undefined,
    width: isFiniteNumber(l.width) ? l.width : undefined,
    shading: typeof l.shading === 'string' ? l.shading : undefined,
    rows: isFiniteNumber(l.rows) ? l.rows : undefined,
    count: isFiniteNumber(l.count) ? l.count : undefined,
    fill: typeof l.fill === 'string' && l.fill in REGION_FILL_TOKENS ? (l.fill as RegionFill) : undefined,
    elevation: isFiniteNumber(l.elevation) ? l.elevation : undefined,
    rings,
    path: geometryArray('path'),
    polygon: geometryArray('polygon'),
    baseline: geometryArray('baseline'),
    trace: geometryArray('trace'),
  };

  if (plate.kind === 'geographic') {
    // parsePlate never reaches parseLayer for a geographic plate without a
    // bbox (it fails first) — bbox is guaranteed defined here.
    assertPointsInBBox(layer, plate.bbox!);
  } else {
    assertPointsInUnitRange(layer);
  }
  return layer;
}

// Mirrors validate_plate's own leniency on a band: only `id` (non-empty,
// unique) is checked. The rest of a band's fields (title, greek, lines,
// summary, ring) are NOT type-validated by the Python validator either, so
// this deliberately doesn't invent stricter checks the pipeline side
// doesn't enforce — two implementations of one contract must not drift.
function parseBands(raw: unknown, plateLabel: string): PlateBand[] {
  if (!Array.isArray(raw) || raw.length === 0) fail(`${plateLabel}: bands must be a non-empty list`);
  const seen = new Set<string>();
  return (raw as unknown[]).map((b, i) => {
    if (!b || typeof b !== 'object') fail(`${plateLabel}: bands[${i}] must be an object`);
    const band = b as Record<string, unknown>;
    if (typeof band.id !== 'string' || !band.id) fail(`${plateLabel}: bands[${i}].id must be a non-empty string`);
    if (seen.has(band.id)) fail(`${plateLabel}: duplicate band id "${band.id}"`);
    seen.add(band.id);
    return band as unknown as PlateBand;
  });
}

// Validates + narrows an already-JSON.parsed plate payload (an
// apparatus/plates/<id>.json file). No file I/O — callers do the reading.
// Throws a distinct, named Error for each malformed-input class documented
// in docs/APPARATUS-SCHEMAS.md's plates/<id>.json section.
//
// Mirrors pipeline/homer_pipeline/apparatus_places.py's validate_plate
// exactly on the point that matters (gap 1, found by a cartography lane): a
// `geographic` plate must carry `bbox` and `layers` (it projects lat/lon
// through shared/lib/geo.ts, so it has to declare the extent it projects
// into); a `schematic` plate carries neither requirement — demanding a bbox
// of it would be demanding a coordinate for something that has none — but
// must declare at least one of `bands` (concentric rings, e.g. the Shield
// of Achilles) or `layers` (unit [u, v] coordinates, e.g. the Trojan plain
// as the poem lays it out). A schematic plate MAY still carry a `bbox`
// (not forbidden, just not required); when present it is validated like
// any other bbox.
export function parsePlate(data: unknown): Plate {
  if (!data || typeof data !== 'object') fail('plate data must be an object');
  const d = data as Record<string, unknown>;

  if (typeof d.id !== 'string' || !d.id) fail('missing id');
  if (typeof d.title !== 'string' || !d.title) fail('missing title');
  if (d.kind !== 'geographic' && d.kind !== 'schematic') fail(`unknown plate kind "${String(d.kind)}"`);
  // Finding 3 (schema drift, 2026-07-28): must be non-empty AFTER
  // trimming, matching apparatus_places.py's validate_plate
  // (`doc["status"].strip()`) — a whitespace-only status used to pass.
  if (typeof d.status !== 'string' || !d.status.trim()) fail('missing status');
  const kind = d.kind as PlateKind;

  let bbox: [number, number, number, number] | undefined;
  if (d.bbox !== undefined) {
    if (!Array.isArray(d.bbox) || d.bbox.length !== 4 || !d.bbox.every(isFiniteNumber)) {
      fail('malformed bbox');
    }
    bbox = d.bbox as [number, number, number, number];
    if (bbox[0] >= bbox[2] || bbox[1] >= bbox[3]) fail('bbox is degenerate (min >= max)');
  } else if (kind === 'geographic') {
    fail('missing bbox');
  }

  // Finding 3 (schema drift, 2026-07-28): must be two POSITIVE numbers,
  // matching apparatus_places.py's validate_plate (`v > 0 for v in size`)
  // — zero/negative used to pass here (a plate that draws onto a
  // zero-area or mirrored canvas).
  if (!Array.isArray(d.size) || d.size.length !== 2 || !d.size.every((n) => isFiniteNumber(n) && n > 0)) {
    fail('size must be two positive numbers');
  }
  const size = d.size as [number, number];

  if (d.ground !== undefined && d.ground !== 'land' && d.ground !== 'sea') {
    fail(`unknown ground "${String(d.ground)}" (must be "land" or "sea")`);
  }
  const ground = d.ground as PlateGround | undefined;

  if (kind === 'geographic' && d.layers === undefined) fail('missing layers');
  if (d.layers !== undefined && !Array.isArray(d.layers)) fail('layers must be an array');
  if (kind === 'schematic' && d.bands === undefined && d.layers === undefined) {
    fail('a schematic plate must declare bands or layers');
  }

  const layers = Array.isArray(d.layers)
    ? (d.layers as unknown[]).map((raw) => parseLayer(raw, { kind, bbox }))
    : [];

  // Finding 6 (2026-07-28): duplicate layer ids defeat seed isolation —
  // deriveSeed salts per-layer randomness solely by id (see its own
  // comment), so two layers sharing an id draw byte-identical
  // hachure. Message shape matches the Python validator's
  // (`plate <id>: duplicate layer id 'x'`) — a parallel lane adds the
  // same rule to apparatus_places.py's validate_plate.
  const seenLayerIds = new Set<string>();
  for (const layer of layers) {
    if (seenLayerIds.has(layer.id)) {
      throw new Error(`plate ${d.id}: duplicate layer id '${layer.id}'`);
    }
    seenLayerIds.add(layer.id);
  }

  // Finding 3 (schema drift, 2026-07-28): seed is required whenever any
  // layer's `style` selects a stochastic primitive — see STOCHASTIC_STYLES in
  // apparatus_places.py, which this mirrors: the check is on the `style`
  // field's value, not the layer `kind`. Without a seed, hachure() derives
  // from `plate.seed ?? 0` (see deriveSeed) — silently drawing from seed 0
  // rather than failing honestly. `stipple` is still listed on both sides
  // although the primitive is gone (2026-07-29, replaced by the blurred
  // `approximate` band): the rule is about a style value that once implied
  // randomness, and demanding a seed for it costs a plate nothing.
  const needsSeed = layers.some((l) => l.style === 'stipple' || l.style === 'hachure');
  if (needsSeed && !isFiniteNumber(d.seed)) {
    fail('seed is required when a layer uses a stochastic style (stipple/hachure)');
  }

  const bands = d.bands !== undefined ? parseBands(d.bands, d.id) : undefined;

  return {
    id: d.id,
    title: d.title,
    kind,
    status: d.status,
    seed: isFiniteNumber(d.seed) ? d.seed : undefined,
    bbox,
    size,
    ground,
    layers,
    bands,
  };
}

// ── Seeded PRNG (mulberry32) ────────────────────────────────────────────
// ~5 lines, no dependency, deterministic: same seed -> same stream, forever.
// Never Math.random(). Used ONLY by the stochastic "hand-drawn" primitives
// (hachure) — every other primitive is purely geometric.

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
// hachure patterns, while staying fully deterministic.
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

// Mirrors shield.ts's safeIdFragment exactly (own copy — same posture as
// escapeXml/round1 above): `idPrefix` is caller-supplied and interpolated
// directly into an SVG element id, which has no attribute-value quoting to
// escape into (escapeXml would not help), so it is sanitized to a safe
// character set instead (2026-07-28, finding 8).
function safeIdFragment(s: string): string {
  const safe = s.replace(/[^a-zA-Z0-9_-]/g, '-');
  return safe || 'plate';
}


// ── Draw primitives — the source of the "illustrated" look ─────────────
// Pure functions, pixel-space in, SVG path `d` string out. hachure
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
// pixel-space convention as hachure's inputs), per Huffman 2010:
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
// The four tiers keep the register they always had — certain solid,
// traditional ringed, speculative broken, mythical dashed — but a MAP SYMBOL
// IS NEVER TRANSPARENT TO ITS OWN BASEMAP (2026-07-29, John, zooming a pin
// over the hypsometric ramp: the contour lines ran straight through the
// middle of it). Three of the four tiers used to carry their meaning as a
// HOLE — `fill: none`, or a 0.16 wash — so the terrain under the pin was part
// of the symbol, and at 3.5x a pin over contoured relief read as a bracelet
// of bands rather than as a marker.
//
// So the body is opaque in every tier, and the tier is carried by an INNER
// MARK drawn in the sheet's label-halo colour (the same token the lettering
// haloes with, so it is the paper's own colour in both themes and needs no
// new token):
//
//   certain      solid, no inner mark
//   traditional  solid + a closed inner ring     (the old "ring" tier)
//   speculative  solid + a BROKEN inner ring     (the old "outline" tier)
//   mythical     solid + a broken OUTLINE        (unchanged, now over a body)
//
// Colour separates the two pairs as before: --accent for a location the
// gazetteer stands behind, --text-mid for one it does not. Shape alone still
// separates all four, which is what an inner mark buys over colour.
//
// This is now a deliberate DIVERGENCE from scenemap.ts's certaintyPinStyle
// and app/src/components/maps/LandmarkMap.svelte, which this used to mirror:
// those draw 6-8 px dots on a small inset over flat land, where a hole shows
// only the ground colour. A plate is a full-column engraving over contoured
// relief and gets read at 3x.

interface PinStyle {
  /** The pin body. Opaque, always — no fill-opacity is emitted anywhere. */
  fill: string;
  stroke: string;
  /** A broken outline: the mythical tier. */
  dasharray?: string;
  /** The tier's inner mark, or absent for a plain solid pin. */
  inner?: { dasharray?: string };
}

// Geometry of the pin: head radius r, head centre 1.7r above the tip, inner
// mark at 0.48r. The inner ring is broken with a dash pattern tuned to leave
// four visible arcs at 1:1 on a 5.5 px head (its circumference is ~16.6 px).
const PIN_HEAD_RISE = 1.7;
const PIN_INNER_RATIO = 0.48;
const PIN_INNER_WIDTH = 1.1;
const PIN_INNER_BROKEN = '2.1 2.1';

function certaintyPinStyle(certainty: Certainty | undefined): PinStyle {
  switch (certainty) {
    case 'traditional':
      return { fill: 'var(--accent)', stroke: 'var(--accent)', inner: {} };
    case 'speculative':
      return { fill: 'var(--text-mid)', stroke: 'var(--text-mid)', inner: { dasharray: PIN_INNER_BROKEN } };
    case 'mythical':
      // The broken outline is stroked in the halo colour, not in the body's
      // own: a dash the same colour as the fill it rims does not read as a
      // broken line at all, it reads as a bitten edge — the gaps notch the
      // silhouette and the pin turns ragged at zoom.
      return { fill: 'var(--text-mid)', stroke: 'var(--scene-map-label-halo)', dasharray: '2 2' };
    case 'certain':
    default:
      return { fill: 'var(--accent)', stroke: 'var(--accent)' };
  }
}

// `conjectural` marks a pin resolved via a schematic plate's `plateAnchors`
// (see resolvePlacePosition) rather than real coordinates — the honesty
// register from docs/APPARATUS-SCHEMAS.md. It renders in its own dashed
// stroke (distinct from the certainty-tier dash used for `mythical`) plus a
// `data-position-basis="conjectural"` attribute a consuming component can
// key off for e.g. an "approximate" label.
const CONJECTURAL_DASHARRAY = '1 3';

// The pin as ONE closed outline: the head circle and the point are a single
// path, joined along the two tangents from the tip. Drawn as a circle plus a
// separate triangle (which is what this was) an opaque body shows the seam
// where the two overlap — two stroked edges crossing the middle of the
// symbol, which is the same defect as a transparent one, arriving from the
// other side.
function pinBodyPath(x: number, y: number, r: number): string {
  const cy = y - r * PIN_HEAD_RISE;
  const cosA = 1 / PIN_HEAD_RISE; // = r / |tip - centre|
  const sinA = Math.sqrt(1 - cosA * cosA);
  const [tx, ty] = [r * sinA, r * cosA];
  return (
    `M ${round1(x - tx)} ${round1(cy + ty)} ` +
    `A ${round1(r)} ${round1(r)} 0 1 1 ${round1(x + tx)} ${round1(cy + ty)} ` +
    `L ${round1(x)} ${round1(y)} Z`
  );
}

function pinInnerMark(cx: number, cy: number, r: number, style: PinStyle): string {
  if (!style.inner) return '';
  const dash = style.inner.dasharray ? ` stroke-dasharray="${style.inner.dasharray}"` : '';
  return (
    `<circle cx="${round1(cx)}" cy="${round1(cy)}" r="${round1(r * PIN_INNER_RATIO)}" fill="none" ` +
    `stroke="var(--scene-map-label-halo)" stroke-width="${PIN_INNER_WIDTH}"${dash}/>`
  );
}

function pinSymbol(x: number, y: number, style: PinStyle, dasharray: string | undefined, r: number): string {
  const dash = dasharray ? ` stroke-dasharray="${dasharray}"` : '';
  return (
    `<path d="${pinBodyPath(x, y, r)}" fill="${style.fill}" stroke="${style.stroke}" ` +
    `stroke-width="1.25" stroke-linejoin="round"${dash}/>` +
    pinInnerMark(x, y - r * PIN_HEAD_RISE, r, style)
  );
}

function pinMarkup(id: string, name: string, x: number, y: number, style: PinStyle, conjectural: boolean, r = 5.5): string {
  const basisAttr = conjectural ? ' data-position-basis="conjectural"' : '';
  return (
    `<g data-place-id="${escapeXml(id)}"${basisAttr}>` +
    `<title>${escapeXml(name)}</title>` +
    pinSymbol(x, y, style, conjectural ? CONJECTURAL_DASHARRAY : style.dasharray, r) +
    `</g>`
  );
}

function pinBBox(x: number, y: number, r = 5.5): [number, number, number, number] {
  return [x - r, y - r * 2.7, x + r, y];
}

// ── Lettering ────────────────────────────────────────────────────────────
// A map with no names is not a map. This module emitted zero <text> elements
// until 2026-07-28. The approach mirrors scenemap.ts's placeLabel + its
// average-glyph-width estimator (both private there, so this is an own copy,
// same posture as escapeXml/round1 above) and adds the two things a plate
// needs that a 320px scene inset does not: Imhof's candidate ORDER, and
// collision rejection against already-placed labels.
//
// Typographic rules from docs/TROAD-CARTOGRAPHY.md §5 (Axis Maps / Imhof):
//   - four size steps, >= 2px apart, never below 9.5px;
//   - rank by WEIGHT, not size: the settlement is the heaviest mark though a
//     region name is the largest, because letterspacing and grey DEMOTE while
//     weight PROMOTES — so a big tracked grey capital reads as background
//     geography and a small bold roman reads as the town;
//   - area features in letterspaced caps, visually centred; water in italic;
//   - haloes via the `paint-order` ATTRIBUTE (not the CSS property), which has
//     shipped far longer;
//   - a conjectural position gets an italic name and a dashed leader.

type LabelRole = 'region' | 'settlement' | 'water' | 'minor';

interface LabelStyle {
  size: number;
  weight: number;
  italic: boolean;
  caps: boolean;
  /** Letterspacing as a fraction of the font size (0 = none). */
  tracking: number;
  fill: string;
}

// Every label colour is --text or --text-mid over a --scene-map-label-halo
// halo, deliberately NOT a per-terrain colour: the halo IS the label's
// background, so contrast is a fixed pair per theme rather than a matrix of
// text-over-every-fill combinations that would have to be re-measured every
// time a terrain token is retuned.
const LABEL_STYLES: Record<LabelRole, LabelStyle> = {
  region: { size: 15.5, weight: 400, italic: false, caps: true, tracking: 0.16, fill: 'var(--text-mid)' },
  settlement: { size: 13.5, weight: 600, italic: false, caps: false, tracking: 0, fill: 'var(--text)' },
  water: { size: 11.5, weight: 400, italic: true, caps: false, tracking: 0.04, fill: 'var(--text-mid)' },
  minor: { size: 9.5, weight: 400, italic: false, caps: false, tracking: 0.02, fill: 'var(--text-mid)' },
};

type LabelAnchor = 'start' | 'middle' | 'end';

type Box = [number, number, number, number]; // [x1, y1, x2, y2]

// Same average-glyph-width heuristic as scenemap.ts's estimateTextWidth (no
// DOM measurement in a pure build-time module), widened for caps and for the
// tracking this module adds. It only has to keep a label inside the neatline
// and off its neighbours, not kern.
function estimateLabelWidth(text: string, style: LabelStyle): number {
  const perGlyph = style.size * (style.caps ? 0.64 : 0.56) + style.size * style.tracking;
  return text.length * perGlyph;
}

function labelText(text: string, style: LabelStyle): string {
  return style.caps ? text.toLocaleUpperCase() : text;
}

// The gazetteer's `name` is a CATALOGUE entry — "Kesik Tepe (the 'Demetrius
// tumulus'), claimed tomb of Achilles", "Scamander (Xanthus)". Lettered onto
// the sheet verbatim it runs across half the plain and collides with its
// neighbours (measured, 2026-07-28: the first render of this lane). A map
// label is the short form: the head of the name, before the first
// parenthetical or appositive, without a leading article. Nothing is lost —
// the full catalogue name still rides on the pin's <title> (so it is what a
// hover and a screen reader get) and in the panel's own place list. Applied
// ONLY to gazetteer-derived names; a layer's explicit `label` is already
// authored as a map label and passes through untouched.
function mapLabelText(name: string): string {
  const head = name.split(/\s*[(,;—]/)[0].trim();
  const base = head || name.trim();
  const deArticled = base.replace(/^[Tt]he\s+/, '');
  if (!deArticled) return base;
  // "The wall of Troy" -> "Wall of Troy": dropping the article must not leave
  // a lowercase initial on a map label.
  return deArticled[0].toLocaleUpperCase() + deArticled.slice(1);
}

function boxesOverlap(a: Box, b: Box, pad = 1.5): boolean {
  return !(a[2] + pad < b[0] || b[2] + pad < a[0] || a[3] + pad < b[1] || b[3] + pad < a[1]);
}

function boxInside(b: Box, width: number, height: number, margin: number): boolean {
  return b[0] >= margin && b[1] >= margin && b[2] <= width - margin && b[3] <= height - margin;
}

interface LabelCandidate {
  x: number;
  y: number; // baseline
  anchor: LabelAnchor;
}

function labelBox(c: LabelCandidate, textWidth: number, style: LabelStyle): Box {
  const x1 = c.anchor === 'start' ? c.x : c.anchor === 'end' ? c.x - textWidth : c.x - textWidth / 2;
  return [x1, c.y - style.size * 0.8, x1 + textWidth, c.y + style.size * 0.25];
}

// Imhof's ranking, via the 2024 reassessment cited in the cartography
// dossier: top-right > right > top > bottom > left. His reason is that Latin
// ascenders outnumber descenders, so a name set above a point sits visually
// closer to it than the same name set below.
// The ring is tried twice, close then further out, before anything is given
// up on: on a crowded sheet a name pushed a few px clear is still attached to
// its own pin, whereas the clamped fallback is a last resort that can land on
// a neighbour. Measured on the Trojan plain (2026-07-28): with one ring, four
// of nine names fell through to the fallback and overprinted the region caps.
const LABEL_GAPS = [5, 14, 26];
/** Candidates from the first (closest) ring; beyond these a name reads as detached from its mark. */
const NEAR_CANDIDATE_COUNT = 8;

function labelCandidates(anchorBox: Box, style: LabelStyle): LabelCandidate[] {
  const [x1, y1, x2, y2] = anchorBox;
  const cx = (x1 + x2) / 2;
  const cy = (y1 + y2) / 2;
  const half = style.size * 0.36; // roughly half a cap height, to centre a side-set name
  const out: LabelCandidate[] = [];
  for (const gap of LABEL_GAPS) {
    out.push(
      { x: x2 + gap, y: y1 + half, anchor: 'start' }, // top-right
      { x: x2 + gap, y: cy + half, anchor: 'start' }, // right
      { x: cx, y: y1 - gap, anchor: 'middle' }, // top
      { x: cx, y: y2 + gap + style.size * 0.72, anchor: 'middle' }, // bottom
      { x: x1 - gap, y: cy + half, anchor: 'end' }, // left
      { x: x1 - gap, y: y1 + half, anchor: 'end' }, // top-left
      { x: x2 + gap, y: y2 + gap + style.size * 0.6, anchor: 'start' }, // bottom-right
      { x: x1 - gap, y: y2 + gap + style.size * 0.6, anchor: 'end' }, // bottom-left
    );
  }
  return out;
}

interface LabelRequest {
  text: string;
  role: LabelRole;
  /** The feature point a leader would run to, and the box a pin's label must clear. */
  anchorBox: Box;
  /** Area features are set at their own centre rather than beside a point (Axis Maps: "visually centred"). */
  centred?: boolean;
  /** A conjectural position: italic name plus a dashed leader (docs/TROAD-CARTOGRAPHY.md §6). */
  conjectural?: boolean;
  /**
   * A linear feature's own projected run. When the name fits along it, it is
   * set ON the line with <textPath> — a river is named along its channel, not
   * beside a dot in the middle of its bounding box.
   */
  path?: [number, number][];
  /** Stable element id for that path when it is emitted into <defs>. Required with `path`. */
  pathId?: string;
}

function polylineLength(pts: [number, number][]): number {
  let total = 0;
  for (let i = 0; i + 1 < pts.length; i++) total += Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]);
  return total;
}

// A name set along a path reads upside-down and backwards wherever the path
// runs right-to-left. The dossier's advice is explicit: never use
// `side="right"` — reverse the path instead. Direction is judged on the run's
// net displacement, so one wiggle mid-course doesn't flip the whole name.
function orientForReading(pts: [number, number][]): [number, number][] {
  const dx = pts[pts.length - 1][0] - pts[0][0];
  return dx < 0 ? [...pts].reverse() : pts;
}

function textPathElement(
  text: string,
  pathId: string,
  style: LabelStyle,
  role: LabelRole,
): string {
  const tracking = style.tracking ? ` letter-spacing="${round1(style.size * style.tracking)}"` : '';
  return (
    `<text class="plate-label plate-label-${role} plate-label-along" ` +
    `font-family="var(--font-ui)" font-size="${style.size}" font-weight="${style.weight}"` +
    `${style.italic ? ' font-style="italic"' : ''}${tracking} fill="${style.fill}" ` +
    `paint-order="stroke" stroke="var(--scene-map-label-halo)" stroke-width="2.5" ` +
    `stroke-linejoin="round" dy="-3.5" style="font-variant-ligatures:none">` +
    `<textPath href="#${pathId}" startOffset="50%" text-anchor="middle" method="align" spacing="exact">` +
    `${escapeXml(labelText(text, style))}</textPath></text>`
  );
}

function labelElement(
  text: string,
  c: LabelCandidate,
  style: LabelStyle,
  role: LabelRole,
  forceItalic: boolean,
): string {
  const italic = style.italic || forceItalic;
  const tracking = style.tracking ? ` letter-spacing="${round1(style.size * style.tracking)}"` : '';
  return (
    `<text class="plate-label plate-label-${role}" x="${round1(c.x)}" y="${round1(c.y)}" ` +
    `text-anchor="${c.anchor}" font-family="var(--font-ui)" font-size="${style.size}" ` +
    `font-weight="${style.weight}"${italic ? ' font-style="italic"' : ''}${tracking} ` +
    `fill="${style.fill}" paint-order="stroke" stroke="var(--scene-map-label-halo)" ` +
    `stroke-width="2.5" stroke-linejoin="round">${escapeXml(labelText(text, style))}</text>`
  );
}

// A leader from the feature to a name that could not sit against it. Drawn in
// two cases, and the two are visually distinct because they claim different
// things:
//   - DASHED, for a conjectural position: the dash is the claim (this name is
//     attached to a guess), per docs/TROAD-CARTOGRAPHY.md §6;
//   - SOLID hairline, when a crowded sheet pushed the name clear of its own
//     pin: it says nothing about certainty, only "this name belongs to that
//     mark." On the Troad sheet ten places sit inside ~40px around Hisarlik,
//     and the alternative to a leader is dropping names, which the project
//     owner's calibration rules out ("omission is not honesty").
// Never drawn when the name is already touching its feature — a leader across
// 4px is clutter, not information.
function leaderElement(anchorBox: Box, box: Box, dashed: boolean): string {
  const ax = (anchorBox[0] + anchorBox[2]) / 2;
  const ay = (anchorBox[1] + anchorBox[3]) / 2;
  const bx = box[0] < ax ? box[2] : box[0];
  const by = (box[1] + box[3]) / 2;
  if (Math.hypot(bx - ax, by - ay) < 12) return '';
  return (
    `<path class="plate-leader" d="M ${round1(ax)} ${round1(ay)} L ${round1(bx)} ${round1(by)}" ` +
    `fill="none" stroke="var(--text-mid)" stroke-width="0.6" stroke-opacity="${dashed ? 1 : 0.7}"` +
    `${dashed ? ' stroke-dasharray="2 2"' : ''}/>`
  );
}

// Lays out every requested label against the sheet, rejecting candidates that
// leave the neatline or collide with a label already placed. Area (`centred`)
// names are laid first — they are the sheet's background geography and their
// position is meaningful (the shape's own centre), so a point name yields to
// them rather than the other way round.
//
// A name whose every candidate is rejected is NOT dropped: it falls back to
// its first candidate, clamped inside the frame. Silently deleting a place
// name off an apparatus map would be exactly the class of quiet omission
// CLAUDE.md's honesty rule exists to prevent — an overlap is visible and
// fixable, an absence is neither.
function layoutLabels(
  requests: LabelRequest[],
  width: number,
  height: number,
  margin: number,
): { markup: string; defs: string } {
  const placed: Box[] = [];
  const parts: string[] = [];
  const defs: string[] = [];
  const ordered = [...requests.filter((r) => r.centred), ...requests.filter((r) => !r.centred)];
  // One name, one place on the sheet. A layer and a pin can resolve to the
  // same gazetteer place (the shore layer named `bay-of-troy` and a pin for
  // the bay), and lettering it twice reads as two features.
  const lettered = new Set<string>();

  for (const req of ordered) {
    if (!req.text.trim()) continue;
    const dedupeKey = req.text.trim().toLocaleLowerCase();
    if (lettered.has(dedupeKey)) continue;
    lettered.add(dedupeKey);
    const style = LABEL_STYLES[req.role];
    const textWidth = estimateLabelWidth(labelText(req.text, style), style);

    // A linear feature is named along its own run whenever the run is long
    // enough to carry the name; otherwise it falls through to point placement
    // below rather than being squeezed onto a stub.
    if (req.path && req.pathId && req.path.length >= 2 && polylineLength(req.path) > textWidth * 1.15) {
      const oriented = orientForReading(req.path);
      // Reserve only the stretch the name actually occupies — the middle of
      // the run, where startOffset="50%" puts it — not the whole polyline's
      // bounding box, which for a river crossing the sheet would push every
      // other name out of half the map.
      const mid = oriented[Math.floor(oriented.length / 2)];
      const box: Box = [mid[0] - textWidth / 2, mid[1] - style.size, mid[0] + textWidth / 2, mid[1] + style.size * 0.3];
      if (!placed.some((p) => boxesOverlap(p, box))) {
        defs.push(`<path id="${req.pathId}" d="${pathD(oriented, false)}" fill="none" stroke="none"/>`);
        parts.push(textPathElement(req.text, req.pathId, style, req.role));
        placed.push(box);
        continue;
      }
      // Too crowded along the line — fall through to point placement.
    }

    let chosen: LabelCandidate;
    let box: Box;
    let detached = false;
    if (req.centred) {
      const cx = (req.anchorBox[0] + req.anchorBox[2]) / 2;
      const cy = (req.anchorBox[1] + req.anchorBox[3]) / 2;
      chosen = { x: cx, y: cy + style.size * 0.3, anchor: 'middle' };
      box = labelBox(chosen, textWidth, style);
    } else {
      const candidates = labelCandidates(req.anchorBox, style);
      let best: { c: LabelCandidate; b: Box } | undefined;
      for (const c of candidates) {
        const b = labelBox(c, textWidth, style);
        if (!boxInside(b, width, height, margin)) continue;
        if (placed.some((p) => boxesOverlap(p, b))) continue;
        best = { c, b };
        break;
      }
      // A name that had to travel to find room, or that fell through to the
      // clamped fallback, gets a hairline leader back to its own mark.
      detached = !best || candidates.indexOf(best.c) >= NEAR_CANDIDATE_COUNT;
      if (best) {
        chosen = best.c;
        box = best.b;
      } else {
        // Every candidate rejected — keep the name, clamped into the frame.
        const c = candidates[0];
        const raw = labelBox(c, textWidth, style);
        const dx = Math.min(0, width - margin - raw[2]) + Math.max(0, margin - raw[0]);
        const dy = Math.min(0, height - margin - raw[3]) + Math.max(0, margin - raw[1]);
        chosen = { ...c, x: c.x + dx, y: c.y + dy };
        box = labelBox(chosen, textWidth, style);
      }
    }

    if (!req.centred && (req.conjectural || detached)) {
      parts.push(leaderElement(req.anchorBox, box, !!req.conjectural));
    }
    parts.push(labelElement(req.text, chosen, style, req.role, !!req.conjectural));
    placed.push(box);
  }
  return { markup: parts.join(''), defs: defs.join('') };
}

// ── Legend ───────────────────────────────────────────────────────────────
// Derived from what this sheet ACTUALLY drew — never a fixed list. A register
// that appears in the key is one the reader can find on the map, and every
// register on the map appears in the key. That is also where the uncertainty
// goes: the calibration for this lane is that caution belongs in the label,
// not in the line, so a reconstructed shoreline is drawn confidently and the
// key says "approximate extent" (the Landmark's own caveat, verbatim).

interface LegendEntry {
  /** Dedupe key: five river layers put ONE "River" row in the key, not five. */
  key: string;
  /** Sort key, so the key's order is stable regardless of layer order in the JSON. */
  rank: number;
  swatch: (x: number, y: number) => string;
  text: string;
}

const LEGEND_FONT = 9.5;
const LEGEND_ROW_H = 14;
const LEGEND_SWATCH_W = 22;

function legendLine(x: number, y: number, stroke: string, width: number, dash = '', opacity = 1): string {
  return (
    `<path d="M ${round1(x)} ${round1(y)} h ${LEGEND_SWATCH_W}" fill="none" stroke="${stroke}" ` +
    `stroke-width="${width}"${dash ? ` stroke-dasharray="${dash}"` : ''}` +
    `${opacity === 1 ? '' : ` stroke-opacity="${opacity}"`}/>`
  );
}

function legendSwatchRect(x: number, y: number, fill: string, fillOpacity: number, stroke: string): string {
  return (
    `<rect x="${round1(x)}" y="${round1(y - 4.5)}" width="${LEGEND_SWATCH_W}" height="9" ` +
    `fill="${fill}" fill-opacity="${fillOpacity}" stroke="${stroke}" stroke-width="0.5" stroke-opacity="0.6"/>`
  );
}

const CERTAINTY_LEGEND_TEXT: Record<Certainty, string> = {
  certain: 'Location secure',
  traditional: 'Traditional identification',
  speculative: 'Identification speculative',
  mythical: 'Mythical — no known site',
};

const REGION_LEGEND_TEXT: Record<RegionFill, string> = {
  sea: 'Open sea',
  lagoon: 'Lagoon and shallow water',
  marsh: 'Marsh and wet delta — margin indefinite',
  plain: 'Dry plain',
  land: 'Land',
  tint: 'Apparatus zone',
  none: '',
};

// One key row per drawn register. `undefined` means the layer needs no row
// (its meaning is carried by its own name on the sheet).
function layerLegendEntry(layer: PlateLayer): LegendEntry | undefined {
  switch (layer.kind) {
    case 'coast': {
      // The soft-band register is this project's honest treatment of a
      // RECONSTRUCTED shoreline (see trojan-plain.json's own note); a plain
      // stroked coast is a surveyed one. Two different claims, two rows.
      // The swatch fakes the blur with three stacked strokes rather than
      // referencing the filter: at legend size the steps are invisible, and
      // it keeps the key independent of the sheet's element ids.
      const reconstructed = layer.style === 'approximate';
      return {
        key: reconstructed ? 'coast-approximate' : 'coast-line',
        rank: reconstructed ? 1 : 2,
        text: reconstructed ? 'Shoreline, reconstructed — approximate extent' : 'Shoreline',
        swatch: (x, y) =>
          reconstructed
            ? legendLine(x, y, 'var(--scene-map-coast)', 7, undefined, 0.14) +
              legendLine(x, y, 'var(--scene-map-coast)', 4, undefined, 0.22) +
              legendLine(x, y, 'var(--scene-map-coast)', APPROX_CORE_WIDTH)
            : legendLine(x, y, 'var(--scene-map-coast)', STROKE_WEIGHT.coast),
      };
    }
    case 'river':
      return { key: 'river', rank: 3, text: 'River', swatch: (x, y) => legendLine(x, y, 'var(--plate-river)', STROKE_WEIGHT.river) };
    case 'relief':
      // A contoured band is keyed by the graduated elevation scale drawn in
      // the sheet's own margin (hypsometricKeyMarkup), which says what the
      // tints MEAN in metres — a one-line legend row saying "high ground"
      // would say less and crowd out the rows that carry real claims.
      if (layer.elevation !== undefined) return undefined;
      return {
        key: 'relief',
        rank: 4,
        text: 'High ground (hachured)',
        swatch: (x, y) =>
          legendSwatchRect(x, y, 'var(--plate-upland)', 1, 'var(--scene-map-coast)') +
          `<path d="${[4, 9, 14, 19].map((o) => `M ${round1(x + o)} ${round1(y - 3.5)} v 7`).join(' ')}" fill="none" stroke="var(--flaxman-hachure)" stroke-width="0.9"/>`,
      };
    case 'wall':
      return { key: 'wall', rank: 5, text: 'Fortification', swatch: (x, y) => legendLine(x, y, 'var(--flaxman-ink)', STROKE_WEIGHT.wall) };
    case 'shipRow':
      return { key: 'shipRow', rank: 6, text: 'Beached ships', swatch: (x, y) => `<path d="${shipRow([[x + 2, y + 2], [x + 20, y + 2]], 1, 2, { seed: 7 })}" fill="var(--flaxman-ink)" stroke="none"/>` };
    case 'tumulus':
      return { key: 'tumulus', rank: 7, text: 'Tumulus', swatch: (x, y) => `<path d="${tumulus([x + LEGEND_SWATCH_W / 2, y + 3], { radius: 6 })}" fill="none" stroke="var(--flaxman-ink)" stroke-width="${STROKE_WEIGHT.tumulus}"/>` };
    case 'route':
      return { key: 'route', rank: 8, text: 'Route', swatch: (x, y) => legendLine(x, y, 'var(--accent-light)', STROKE_WEIGHT.route, '1 4') };
    case 'region':
    case 'band':
      return regionFillLegendEntry(layer.fill ?? DEFAULT_REGION_FILL);
    default:
      return undefined;
  }
}

function regionFillLegendEntry(fill: RegionFill): LegendEntry | undefined {
  // A `none` region draws nothing, so it keys nothing — its name on the sheet
  // is the whole of its claim.
  if (fill === 'none') return undefined;
  return {
    key: `region-${fill}`,
    rank: 20 + Object.keys(REGION_FILL_TOKENS).indexOf(fill),
    text: REGION_LEGEND_TEXT[fill],
    swatch: (x, y) =>
      legendSwatchRect(
        x,
        y,
        REGION_FILL_TOKENS[fill],
        REGION_FILL_OPACITY[fill],
        WATER_FILLS.has(fill) ? 'var(--scene-map-coast)' : 'var(--flaxman-ink)',
      ),
  };
}

// A key row shows the SYMBOL, not an abstraction of it: the same pin the
// sheet draws, at legend size (r=4, so the whole 10.8 px pin sits inside a
// 14 px row), tip on the row's own baseline.
const LEGEND_PIN_R = 4;

function legendPin(x: number, y: number, style: PinStyle, dasharray?: string): string {
  return pinSymbol(x + LEGEND_SWATCH_W / 2, y + LEGEND_PIN_R * 1.35, style, dasharray, LEGEND_PIN_R);
}

function certaintyLegendEntry(certainty: Certainty): LegendEntry {
  const style = certaintyPinStyle(certainty);
  return {
    key: `certainty-${certainty}`,
    rank: 40 + ['certain', 'traditional', 'speculative', 'mythical'].indexOf(certainty),
    text: CERTAINTY_LEGEND_TEXT[certainty],
    swatch: (x, y) => legendPin(x, y, style, style.dasharray),
  };
}

// Renders the key into the sheet's bottom-right corner, inside the neatline,
// on its own halo-coloured panel so it stays legible over whatever terrain
// falls under it. Returns '' when there is nothing to key.
function legendMarkup(entries: LegendEntry[], width: number, height: number): string {
  const byKey = new Map<string, LegendEntry>();
  for (const e of entries) if (!byKey.has(e.key)) byKey.set(e.key, e);
  if (byKey.size === 0) return '';
  const rows = [...byKey.values()].sort((a, b) => a.rank - b.rank || a.text.localeCompare(b.text));
  const textW = Math.max(...rows.map((r) => r.text.length * LEGEND_FONT * 0.54));
  const padX = 8;
  const padY = 8;
  const panelW = padX * 2 + LEGEND_SWATCH_W + 7 + textW;
  const panelH = padY * 2 + rows.length * LEGEND_ROW_H;
  // A key that overruns its own sheet is worse than no key. Small schematic
  // devices (the Shield at 200px) have no room for one and no use for one —
  // they are not maps, and every band already carries its own label.
  if (panelW > width - LABEL_MARGIN * 2 || panelH > height - LABEL_MARGIN * 2) return '';
  const x0 = width - LABEL_MARGIN - 4 - panelW;
  const y0 = height - LABEL_MARGIN - 4 - panelH;

  const parts: string[] = [
    `<rect class="plate-legend-panel" x="${round1(x0)}" y="${round1(y0)}" width="${round1(panelW)}" ` +
      `height="${round1(panelH)}" rx="2" fill="var(--scene-map-label-halo)" fill-opacity="0.86" ` +
      `stroke="var(--flaxman-ink)" stroke-width="0.5" stroke-opacity="0.5"/>`,
  ];
  rows.forEach((row, i) => {
    const cy = y0 + padY + LEGEND_ROW_H * i + LEGEND_ROW_H / 2;
    parts.push(row.swatch(x0 + padX, cy));
    parts.push(
      `<text x="${round1(x0 + padX + LEGEND_SWATCH_W + 7)}" y="${round1(cy + LEGEND_FONT * 0.35)}" ` +
        `font-family="var(--font-ui)" font-size="${LEGEND_FONT}" fill="var(--text)">${escapeXml(row.text)}</text>`,
    );
  });
  return `<g class="plate-legend">${parts.join('')}</g>`;
}

// ── Frame and bar scale ──────────────────────────────────────────────────

// Double neatline: outer 1.2px, inner 0.4px, 3px apart — docs/TROAD-
// CARTOGRAPHY.md §5. No graticule across the face.
const FRAME_OUTER_WIDTH = 1.2;
const FRAME_INNER_WIDTH = 0.4;
const FRAME_GAP = 3;
const FRAME_OUTER_INSET = FRAME_OUTER_WIDTH / 2;
const FRAME_INNER_INSET = FRAME_OUTER_INSET + FRAME_GAP + FRAME_INNER_WIDTH / 2;
/** Keep lettering clear of the inner neatline. */
const LABEL_MARGIN = FRAME_INNER_INSET + 4;

function neatlineMarkup(width: number, height: number): string {
  const rect = (inset: number, strokeWidth: number) =>
    `<rect class="plate-neatline" x="${inset}" y="${inset}" width="${round1(width - inset * 2)}" ` +
    `height="${round1(height - inset * 2)}" fill="none" stroke="var(--flaxman-ink)" stroke-width="${strokeWidth}"/>`;
  return rect(FRAME_OUTER_INSET, FRAME_OUTER_WIDTH) + rect(FRAME_INNER_INSET, FRAME_INNER_WIDTH);
}

// Mean km per degree of latitude (WGS84). The viewport's single `scale` is
// px per cos-corrected degree and is shared by both axes (see geo.ts), so one
// figure converts it for the whole sheet.
const KM_PER_DEG_LAT = 110.574;
/** The Attic stade, 600 Greek feet — the unit the sources this apparatus cites actually use. */
const KM_PER_STADE = 0.185;

// Bar-scale geometry, hoisted out of scaleBarMarkup so the hypsometric key
// below can sit directly on top of the scale panel without re-deriving (and
// drifting from) its arithmetic.
const SCALE_BAR_H = 4;
const SCALE_FONT = 9.5;
const SCALE_X0 = LABEL_MARGIN + 6;
function scalePanelTop(height: number): number {
  return height - LABEL_MARGIN - 16 - SCALE_BAR_H - SCALE_FONT - 8;
}

const NICE_KM = [0.25, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500];
const NICE_STADES = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000];

// Picks the largest value from `steps` whose bar fits `maxPx`, or the
// smallest step if even that overruns (a sheet too small for any honest bar).
function niceLength(steps: number[], pxPerUnit: number, maxPx: number): number {
  let chosen = steps[0];
  for (const s of steps) {
    if (s * pxPerUnit <= maxPx) chosen = s;
  }
  return chosen;
}

function barSegments(x0: number, y: number, len: number, height: number, segments: number): string {
  const parts: string[] = [];
  const w = len / segments;
  for (let i = 0; i < segments; i++) {
    if (i % 2 === 0) continue; // alternating filled / open
    parts.push(
      `M ${round1(x0 + i * w)} ${round1(y)} h ${round1(w)} v ${round1(height)} h ${round1(-w)} Z`,
    );
  }
  return parts.join(' ');
}

// A bar scale computed from the plate's OWN viewport, so it is honest by
// construction rather than a drawn decoration: stades over kilometres with
// coincident zeros, alternating filled and open segments (dossier §5).
// Geographic plates only — a schematic plate has no scale, and drawing one
// would be a fabricated claim.
function scaleBarMarkup(viewport: Viewport, width: number, height: number): string {
  if (!Number.isFinite(viewport.scale) || viewport.scale <= 0) return '';
  const kmPerPx = KM_PER_DEG_LAT / viewport.scale;
  if (!Number.isFinite(kmPerPx) || kmPerPx <= 0) return '';
  const pxPerKm = 1 / kmPerPx;
  const maxPx = Math.min(width * 0.34, 240);

  const km = niceLength(NICE_KM, pxPerKm, maxPx);
  const stades = niceLength(NICE_STADES, pxPerKm * KM_PER_STADE, maxPx);
  const kmPx = km * pxPerKm;
  const stadePx = stades * KM_PER_STADE * pxPerKm;
  if (!(kmPx > 2) || !(stadePx > 2)) return '';

  const barW = Math.max(kmPx, stadePx);
  const x0 = SCALE_X0;
  const baseY = height - LABEL_MARGIN - 16;
  const barH = SCALE_BAR_H;
  const font = SCALE_FONT;

  const panel =
    `<rect class="plate-scale-panel" x="${round1(x0 - 6)}" y="${round1(scalePanelTop(height))}" ` +
    `width="${round1(barW + 46)}" height="${round1(barH * 2 + font * 2 + 16)}" rx="2" ` +
    `fill="var(--scene-map-label-halo)" fill-opacity="0.72" stroke="none"/>`;

  const rule =
    `<path class="plate-scale-rule" d="M ${round1(x0)} ${round1(baseY)} H ${round1(x0 + barW)}" ` +
    `fill="none" stroke="var(--flaxman-ink)" stroke-width="0.6"/>`;

  const stadeBar =
    `<path class="plate-scale-bar" d="${barSegments(x0, baseY - barH, stadePx, barH, 4)}" ` +
    `fill="var(--flaxman-ink)" stroke="none"/>` +
    `<path class="plate-scale-bar-outline" d="M ${round1(x0)} ${round1(baseY - barH)} h ${round1(stadePx)} v ${barH} h ${round1(-stadePx)} Z" ` +
    `fill="none" stroke="var(--flaxman-ink)" stroke-width="0.6"/>`;

  const kmBar =
    `<path class="plate-scale-bar" d="${barSegments(x0, baseY, kmPx, barH, 4)}" ` +
    `fill="var(--flaxman-ink)" stroke="none"/>` +
    `<path class="plate-scale-bar-outline" d="M ${round1(x0)} ${round1(baseY)} h ${round1(kmPx)} v ${barH} h ${round1(-kmPx)} Z" ` +
    `fill="none" stroke="var(--flaxman-ink)" stroke-width="0.6"/>`;

  const text = (x: number, y: number, s: string, anchor: LabelAnchor) =>
    `<text class="plate-scale-label" x="${round1(x)}" y="${round1(y)}" text-anchor="${anchor}" ` +
    `font-family="var(--font-ui)" font-size="${font}" fill="var(--text-mid)" paint-order="stroke" ` +
    `stroke="var(--scene-map-label-halo)" stroke-width="2" stroke-linejoin="round">${escapeXml(s)}</text>`;

  return (
    `<g class="plate-scale">` +
    panel +
    stadeBar +
    kmBar +
    rule +
    text(x0, baseY - barH - 3, '0', 'middle') +
    text(x0 + stadePx + 3, baseY - barH - 3, `${stades} stades`, 'start') +
    text(x0 + kmPx + 3, baseY + barH + font, `${km} km`, 'start') +
    `</g>`
  );
}

// ── Hypsometric key ──────────────────────────────────────────────────────
// A graduated elevation scale: the sheet's own ground colour, then one cell
// per contour band up the ramp, with the metres marked under the boundaries.
// It replaces the single "High ground (hachured)" legend row a contoured
// plate used to get, which told a reader the colour meant height but never
// which height. Drawn only where there are at least two bands to graduate
// between; a hand-authored relief plate carries no elevations and gets
// nothing here.
const HYPS_CELL_W = 14;
const HYPS_CELL_H = 7;
const HYPS_FONT = 8;
/** At most this many numerals under the bar, always including the summit. */
const HYPS_MAX_TICKS = 5;

function hypsometricKeyMarkup(plate: Plate, width: number, height: number): string {
  const levels = hypsometricLevels(plate);
  if (levels.length < 2) return '';
  const barW = (levels.length + 1) * HYPS_CELL_W;
  const padX = 6;
  const padY = 5;
  const titleH = HYPS_FONT + 3;
  const panelW = barW + padX * 2;
  const panelH = padY * 2 + titleH + HYPS_CELL_H + 3 + HYPS_FONT;
  // A key wider than the sheet can spare, or with no room above the bar
  // scale, is not drawn at all: a truncated scale is worse than none.
  if (panelW > width * 0.62) return '';
  const x0 = SCALE_X0 - padX;
  const bottom = plate.kind === 'geographic' ? scalePanelTop(height) - 6 : height - LABEL_MARGIN - 4;
  const y0 = bottom - panelH;
  if (y0 < LABEL_MARGIN) return '';

  const barX = x0 + padX;
  const barY = y0 + padY + titleH;

  const cells: string[] = [];
  // Cell 0 is the ground below the lowest contour — on both Troy sheets the
  // parchment the coast fills, so the ramp visibly starts from the sheet's
  // own lowland rather than from an unrelated colour.
  cells.push(
    `<rect x="${round1(barX)}" y="${round1(barY)}" width="${HYPS_CELL_W}" height="${HYPS_CELL_H}" ` +
      `fill="var(--scene-map-land)"/>`,
  );
  levels.forEach((lv, i) => {
    cells.push(
      `<rect x="${round1(barX + (i + 1) * HYPS_CELL_W)}" y="${round1(barY)}" width="${HYPS_CELL_W}" ` +
        `height="${HYPS_CELL_H}" fill="${reliefRampToken(hypsometricStep(levels, lv))}"/>`,
    );
  });

  // Numerals: the first level, the last, and an evenly strided few between —
  // dropping any that would land within two cells of the summit numeral,
  // since a four-digit metre figure is wider than one cell and "200" printed
  // over "320" reads as neither.
  const stride = Math.max(1, Math.ceil(levels.length / (HYPS_MAX_TICKS - 1)));
  const last = levels.length - 1;
  const ticks = [0];
  for (let i = stride; i < last; i += stride) {
    if (last - i >= 2) ticks.push(i);
  }
  ticks.push(last);

  const label = (x: number, y: number, s: string, anchor: LabelAnchor) =>
    `<text x="${round1(x)}" y="${round1(y)}" text-anchor="${anchor}" font-family="var(--font-ui)" ` +
    `font-size="${HYPS_FONT}" fill="var(--text-mid)" paint-order="stroke" ` +
    `stroke="var(--scene-map-label-halo)" stroke-width="2" stroke-linejoin="round">${escapeXml(s)}</text>`;

  const numerals = ticks.map((i) =>
    label(barX + (i + 1) * HYPS_CELL_W, barY + HYPS_CELL_H + 3 + HYPS_FONT, String(levels[i]), 'middle'),
  );

  return (
    `<g class="plate-hypsometric-key">` +
    `<rect class="plate-hypsometric-panel" x="${round1(x0)}" y="${round1(y0)}" width="${round1(panelW)}" ` +
    `height="${round1(panelH)}" rx="2" fill="var(--scene-map-label-halo)" fill-opacity="0.72" stroke="none"/>` +
    label(barX, y0 + padY + HYPS_FONT, 'Elevation, metres', 'start') +
    cells.join('') +
    `<rect x="${round1(barX)}" y="${round1(barY)}" width="${round1(barW)}" height="${HYPS_CELL_H}" ` +
    `fill="none" stroke="var(--plate-contour)" stroke-width="0.5" stroke-opacity="0.55"/>` +
    label(barX, barY + HYPS_CELL_H + 3 + HYPS_FONT, '0', 'middle') +
    numerals.join('') +
    `</g>`
  );
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

// A vertex this close to the sheet edge is where the neatline cut the
// geometry, not a place where the ground turns: it is a clipping artefact and
// must stay exactly where it is. Without this, rounding the corners of
// `sea-modern` (a polygon that runs along two frame edges) pulled the water
// off the frame and left wedges of land colour in the corners of the sheet.
const FRAME_EPS = 0.5;

function onFrame([x, y]: [number, number], width: number, height: number): boolean {
  return (
    Math.abs(x) <= FRAME_EPS ||
    Math.abs(x - width) <= FRAME_EPS ||
    Math.abs(y) <= FRAME_EPS ||
    Math.abs(y - height) <= FRAME_EPS
  );
}

/**
 * A polyline or ring drawn as a smooth curve rather than as a polygon:
 * quadratic Béziers from edge midpoint to edge midpoint, each vertex used as
 * the control point. The classic polyline-rounding construction — C1
 * continuous, deterministic, no extra data, and every piece of it stays
 * inside the triangle (midpoint, vertex, midpoint) whose three corners all
 * lie ON the original line. That containment is the honesty guarantee: the
 * curve cannot wander outside the polygon it rounds, and its distance from
 * the original line is bounded by the corner it cuts.
 *
 * Why it exists (2026-07-29, "when you zoom in, it's just big old lines"): a
 * line cut from a DEM and simplified with Douglas-Peucker is smooth ground
 * drawn as a spiky polygon, because DP keeps outliers and drops everything
 * between them. Smoothing the GEOMETRY instead would multiply the vertex
 * count in a file a human has to review; rounding it at draw time costs
 * nothing and is what a contour looks like.
 *
 * Extended 2026-07-29 from relief bands to every measured line on a
 * GEOGRAPHIC sheet — coast, region, band and river. The argument that was
 * used to hold coastlines back ("a coastline is a surveyed line and keeps its
 * vertices") is exactly backwards for the reconstructed Bronze Age shore,
 * whose own note declares it accurate to about a kilometre and generalised to
 * 275 m: drawn as straight facets meeting at sharp corners it asserts a
 * precision the data does not have, and the facets are an artefact of
 * Douglas-Peucker, not a claim about the ground. Smoothing it is the more
 * honest drawing, and it provably does not move the line (see
 * shared/__tests__/plate.test.ts, which measures the deviation in metres
 * against the declared tolerance and re-checks the shore's own calibration
 * against Hisarlık). Schematic plates are exempt: they are not surveys of
 * anything, and their zones are authored shapes.
 *
 * Two kinds of vertex are never rounded: the endpoints of an open line, and
 * any vertex lying on the sheet's frame (see FRAME_EPS).
 */
// The construction shared by the two consumers of the smoothing below: which
// vertices are hard, and where each rounded corner enters and leaves. Factored
// so the curve that is DRAWN and the curve a river is clipped against cannot
// drift apart — they are the same curve, read out two ways.
interface SmoothFrame {
  hard: boolean[];
  entry: (i: number) => [number, number];
  exit: (i: number) => [number, number];
}

function smoothFrame(points: [number, number][], closed: boolean, size: [number, number]): SmoothFrame {
  const n = points.length;
  const [width, height] = size;
  const hard = points.map(
    (p, i) => (!closed && (i === 0 || i === n - 1)) || onFrame(p, width, height),
  );
  const mid = (i: number, j: number): [number, number] => [
    (points[i][0] + points[j][0]) / 2,
    (points[i][1] + points[j][1]) / 2,
  ];
  return {
    hard,
    entry: (i) => (hard[i] ? points[i] : mid((i - 1 + n) % n, i)),
    exit: (i) => (hard[i] ? points[i] : mid(i, (i + 1) % n)),
  };
}

// Samples per rounded corner when the smoothed curve is flattened back to a
// polyline (see smoothPolyline). Four segments hold a quadratic to well under
// a tenth of a pixel at the corner sizes these sheets carry.
const SMOOTH_SAMPLES = 4;

/**
 * The same curve smoothPathD draws, flattened to a polyline. Used to test
 * containment against a water body's DRAWN edge rather than against the
 * polygon it is stored as: at a sharp inlet — a river's own valley cutting
 * into the shore — the rounded curve pulls back from the stored corner by
 * more than the line weight, so a river cut at the stored edge visibly poked
 * out into the water it was supposed to end at.
 */
function smoothPolyline(points: [number, number][], closed: boolean, size: [number, number]): [number, number][] {
  const n = points.length;
  if (n < 3) return points;
  const { hard, entry, exit } = smoothFrame(points, closed, size);
  const out: [number, number][] = [];
  const push = (p: [number, number]) => {
    const last = out[out.length - 1];
    if (!last || last[0] !== p[0] || last[1] !== p[1]) out.push(p);
  };
  for (let i = 0; i < n; i++) {
    const e = entry(i);
    push(e);
    if (hard[i]) continue;
    const x = exit(i);
    for (let s = 1; s <= SMOOTH_SAMPLES; s++) {
      const t = s / SMOOTH_SAMPLES;
      const u = 1 - t;
      push([
        u * u * e[0] + 2 * u * t * points[i][0] + t * t * x[0],
        u * u * e[1] + 2 * u * t * points[i][1] + t * t * x[1],
      ]);
    }
  }
  return out;
}

function smoothPathD(points: [number, number][], closed: boolean, size: [number, number]): string {
  const n = points.length;
  if (n < 3) return pathD(points, closed);
  const { hard, entry, exit } = smoothFrame(points, closed, size);
  const fmt = (p: [number, number]) => `${round1(p[0])},${round1(p[1])}`;

  const parts: string[] = [];
  let last = '';
  const lineTo = (p: [number, number]) => {
    const s = fmt(p);
    if (s === last) return;
    parts.push(`${parts.length === 0 ? 'M' : 'L'}${s}`);
    last = s;
  };
  for (let i = 0; i < n; i++) {
    lineTo(entry(i));
    if (hard[i]) continue;
    const e = exit(i);
    parts.push(`Q${fmt(points[i])} ${fmt(e)}`);
    last = fmt(e);
  }
  // A closed ring needs no explicit return to its start: whatever is left
  // between the last exit point and the first entry point is a straight run
  // along an original edge, which is exactly what Z draws.
  return closed ? `${parts.join(' ')} Z` : parts.join(' ');
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
// ── The soft register ────────────────────────────────────────────────────
// One Gaussian blur, shared by the two features on these sheets whose extent
// is genuinely indefinite: the reconstructed Bronze Age shoreline (accurate
// to about a kilometre by its own note) and the delta wetland (which has no
// boundary at all). A blur is the only softening that is the same drawing at
// every magnification — a fade built out of nested bands has visible steps,
// and a fade built out of marks has countable marks. It carries no colour, so
// it costs the theming contract nothing.
//
// Two strengths, because the two claims are not equally vague. The shoreline
// has a POSITION -- it was derived from the 10 m contour precisely because
// that level passes 1.2 km north of Hisarlık, where the geoarchaeology puts
// the bay head -- so its band is tight: 4 px, about 110 m of ground on these
// sheets, enough that the edge is a gradient and not a line. The wetland has
// no position to soften, only a margin that never existed as a line at all,
// so it fades over roughly twice that.
const SOFT_BLUR = { coast: 4, marsh: 8 } as const;
type SoftKind = keyof typeof SOFT_BLUR;
const APPROX_BAND_WIDTH = 9;
const APPROX_BAND_OPACITY = 0.4;
const APPROX_CORE_WIDTH = 0.9;

const STROKE_WEIGHT = {
  coast: 2,
  river: 1.4,
  wall: 1.15,
  route: 1,
  tick: 0.75,
  tumulus: 1,
} as const;

// ── Layer rendering ──────────────────────────────────────────────────────

// Which lettering register a layer's own name belongs to (see LABEL_STYLES).
const LAYER_LABEL_ROLE: Record<LayerKind, LabelRole> = {
  coast: 'water',
  river: 'water',
  relief: 'region',
  shipRow: 'minor',
  wall: 'minor',
  route: 'minor',
  region: 'region',
  band: 'region',
  tumulus: 'minor',
};

// An area name is set at the shape's own centre; a linear feature's name is
// set beside the middle of its run, not beside the centre of its bounding box
// (which for a curving river is often not on the river at all).
const AREA_LAYER_KINDS: ReadonlySet<LayerKind> = new Set<LayerKind>(['region', 'band', 'relief']);

interface RenderedLayer {
  markup: string;
  feature: RenderedFeature;
  labelAnchor: Box;
  labelCentred: boolean;
  labelRole: LabelRole;
  /** The feature's own run, for a name set along the line (rivers, coasts, walls, routes). */
  labelPath?: [number, number][];
  /**
   * Markup this layer needs drawn UNDER another layer rather than in its own
   * paint slot — the drowned reaches of a river (see the water section
   * below). Keyed by the layer id it must precede.
   */
  submerged?: { layerId: string; markup: string }[];
}

// ── Water, and where a river stops ───────────────────────────────────────
// A river is painted BENEATH any water it crosses (2026-07-29). The defect
// this fixes was substantive, not cosmetic: our rivers are modern OSM
// watercourses, and their lower reaches cross ground that was under water in
// 1200 BC. Drawn over the reconstructed lagoon they asserted a Bronze Age
// river exactly where the plate's own evidence says there was sea.
//
// The mechanism is paint ORDER, not a cut, and that is the whole point of it:
// no geometry is discarded and none is invented — the union of everything
// drawn is still exactly the surveyed course. The renderer splits a river at
// the edge of every water body on the sheet and hands each submerged reach to
// that water layer's own paint slot, immediately under its fill. So:
//
//   - the water is drawn: its opaque fill covers the reach, and the river
//     visibly ends at that shoreline, exactly where the DRAWN edge falls
//     (which is why the split needs no sub-pixel accuracy — the cut is under
//     the fill, and the smoothed curve, not the split point, is what shows);
//   - the water is toggled off: the fill goes with it, the reach is revealed,
//     and the river runs on to the next shoreline it meets. A river's mouth
//     is a function of which shoreline you are drawing, so it follows the
//     layer toggles for free, with no state for the component to track — the
//     water itself is what hides the reach.
//
// A reach drowned by the sheet's own `ground: "sea"` (the Troad sheet) is
// simply not drawn: the ground is the bottom of the paint stack, so "beneath
// the sea" means invisible there, and the ground carries no toggle.
//
// No plate field configures any of this, deliberately. There is nothing to
// author, nothing to forget on the next river, and nothing for the two
// implementations of the plate schema to drift on — the rule is a property of
// the drawing, not a claim in the data. `marsh` is not water for this
// purpose: a channel through a wetland is a channel, and the Scamander
// crossing the delta swamp is drawn as it always was.
interface WaterBody {
  /** The layer whose fill paints this water; null for the sheet's sea ground. */
  layerId: string | null;
  contains(p: [number, number]): boolean;
}

/** Even-odd across a body's rings — matches the `fill-rule="evenodd"` the coast body is painted with. */
function insideRings(rings: [number, number][][], p: [number, number]): boolean {
  let inside = false;
  for (const ring of rings) if (pointInPolygon(p, ring)) inside = !inside;
  return inside;
}

// A body's rings as they are DRAWN: smoothed on a geographic sheet, exactly
// as renderLayer's own `lineD` smooths them, so a river ends on the line the
// reader sees and not on the polyline behind it.
function bodyRings(plate: Plate, layer: PlateLayer, viewport: Viewport): [number, number][][] {
  const asDrawn = (pts: PlatePoint[]): [number, number][] => {
    const px = projectPoints(plate, pts, viewport);
    return plate.kind === 'geographic' ? smoothPolyline(px, true, plate.size) : px;
  };
  const rings: [number, number][][] = [];
  if (layer.polygon && layer.polygon.length >= 3) rings.push(asDrawn(layer.polygon));
  for (const ring of layer.rings ?? []) {
    if (ring.length >= 3) rings.push(asDrawn(ring));
  }
  return rings;
}

// Every body of water on the sheet, in paint order. A `land`-filled body is
// collected too, but only to define the sea ground's own extent: on a
// `ground: "sea"` plate the water is everything the land bodies do not cover.
function collectWaterBodies(plate: Plate, viewport: Viewport): WaterBody[] {
  const bodies: WaterBody[] = [];
  const landBodies: [number, number][][][] = [];
  for (const layer of plate.layers) {
    const fill =
      layer.fill ?? (layer.kind === 'region' || layer.kind === 'band' ? DEFAULT_REGION_FILL : undefined);
    if (fill === undefined || (!WATER_FILLS.has(fill) && fill !== 'land')) continue;
    const rings = bodyRings(plate, layer, viewport);
    if (rings.length === 0) continue;
    if (fill === 'land') landBodies.push(rings);
    else bodies.push({ layerId: layer.id, contains: (p) => insideRings(rings, p) });
  }
  if ((plate.ground ?? 'land') === 'sea') {
    bodies.push({ layerId: null, contains: (p) => !landBodies.some((rings) => insideRings(rings, p)) });
  }
  return bodies;
}

// Bisections used to find where a line crosses a shoreline. 24 halvings put
// the crossing within a millionth of the segment, which is far finer than the
// geometry it is cutting; the count is fixed so the result is deterministic.
const CROSSING_BISECTIONS = 24;

function crossingPoint(
  a: [number, number],
  b: [number, number],
  inside: (p: [number, number]) => boolean,
): [number, number] {
  const insideA = inside(a);
  let lo = 0;
  let hi = 1;
  for (let i = 0; i < CROSSING_BISECTIONS; i++) {
    const m = (lo + hi) / 2;
    if (inside([a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m]) === insideA) lo = m;
    else hi = m;
  }
  const t = (lo + hi) / 2;
  return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
}

// The maximal runs of `px` over which `inside` holds, each carried out to the
// exact crossing at either end so that the runs on the two sides of a
// shoreline share a point: the line is split, never gapped.
function runsWhere(px: [number, number][], inside: (p: [number, number]) => boolean): [number, number][][] {
  const out: [number, number][][] = [];
  let run: [number, number][] | null = null;
  for (let i = 0; i < px.length; i++) {
    if (inside(px[i])) {
      if (!run) {
        run = [];
        if (i > 0) run.push(crossingPoint(px[i - 1], px[i], inside));
      }
      run.push(px[i]);
    } else if (run) {
      run.push(crossingPoint(px[i - 1], px[i], inside));
      out.push(run);
      run = null;
    }
  }
  if (run) out.push(run);
  return out.filter((r) => r.length >= 2);
}

// The single run a linear layer's name is set along: its path/trace, or — for
// a coast, which may carry several rings — the longest one, since that is the
// stretch with room for the name.
function linearRun(plate: Plate, layer: PlateLayer, viewport: Viewport): [number, number][] | undefined {
  let pts: PlatePoint[] | undefined;
  if (layer.kind === 'river' || layer.kind === 'route') pts = layer.path;
  else if (layer.kind === 'wall') pts = layer.trace;
  else if (layer.kind === 'coast') {
    for (const ring of layer.rings ?? []) {
      if (!pts || ring.length > pts.length) pts = ring;
    }
  }
  if (!pts || pts.length < 2) return undefined;
  return projectPoints(plate, pts, viewport);
}

// ── Relief steepness signal (2026-07-28, hachure lane) ──────────────────
// hachure() itself draws one polygon at one fixed density; a relief BODY cut
// by the terrain lane into nested contour bands (Ida at 200/400/600/800/
// 1200 m, the plain at 20-100 m) needs the density read back out of that
// nesting, because geometry alone can't hand "how steep" to the drawing
// routine — that has to happen here, at the renderer. Two signals, both
// already visible in the plate's own polygons (no slope invented, no
// elevation parsed out of a `note` string):
//   - nesting depth: how many OTHER relief polygons on this plate contain
//     this one's centroid. Bands stacked tightly over the same footprint
//     (Ida's 600/800/1200 m family) mean the ground climbs fast there.
//   - relative area: a polygon small next to the plate's biggest relief body
//     reads as a knob or a summit, not a plateau.
// The two average into one 0..1 "steepness" score; RELIEF_SPACING_*/
// RELIEF_WEIGHT_* interpolate against it below — a tightly nested, small
// polygon draws dense and a little heavier (a massif); a broad, unnested one
// draws sparse and light (open ground). A plate with only one relief layer
// (or a relief layer with no siblings surviving projection) has nothing to
// compare against and gets the gentle end outright, not a divide-by-zero.

function polygonArea(pts: [number, number][]): number {
  let a = 0;
  for (let i = 0; i < pts.length; i++) {
    const [x1, y1] = pts[i];
    const [x2, y2] = pts[(i + 1) % pts.length];
    a += x1 * y2 - x2 * y1;
  }
  return Math.abs(a) / 2;
}

function polygonCentroid(pts: [number, number][]): [number, number] {
  let cx = 0;
  let cy = 0;
  for (const [x, y] of pts) {
    cx += x;
    cy += y;
  }
  return [cx / pts.length, cy / pts.length];
}

// Standard ray-casting point-in-polygon test (even-odd rule) — purely
// geometric, same posture as wallGlyph's own shoelace-style side test.
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

function clamp01(n: number): number {
  return Math.min(1, Math.max(0, n));
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

// Both ends are lighter than the module's old flat 7px spacing / 1.6px
// weight defaults (2026-07-28: "the eastern half of the plain reads as a
// broad tan field competing with the labels") — relief sits UNDER the map,
// so even the steep end is thinner than the old uniform weight; density,
// not ink weight, is what is meant to read as "massif."
const RELIEF_SPACING_GENTLE = 11;
const RELIEF_SPACING_STEEP = 4.5;
const RELIEF_WEIGHT_GENTLE = 0.9;
const RELIEF_WEIGHT_STEEP = 1.5;

export interface ReliefHachureParams {
  spacing: number;
  weight: number;
}

// ── Hypsometric tinting (2026-07-29) ─────────────────────────────────────
// The relief above is the HAND-AUTHORED register: one polygon, one flat
// fill, hachures on top, density read out of how the polygons nest. It is
// what you draw when you have no elevations. These two Troy sheets are cut
// from a real 30 m DEM, so they carry `elevation` on every relief layer and
// take the register a physical map has used since Sydow and Imhof instead:
// many graduated bands, coloured up a ramp, with a hairline contour between
// them. Depth comes from the ramp; the hairlines dissolve the polygon edge
// that a flat fill shows as a hard outline. Hachures survive only for the
// plates that genuinely have no elevation data (the schematic plain, the
// citadel), which is exactly the historical division of labour between the
// two techniques.
//
// The ramp is keyed to the SHEET's own elevations, not to an absolute
// height, because that is what a physical map does: the plain runs 0-300 m
// and the Troad 0-1750 m, and forcing one absolute scale on both would wash
// the plain into a single tint. The mapping is by rank among the distinct
// elevations present, so it is stable under any interval choice and needs no
// hard-coded table.
const RELIEF_RAMP_STEPS = 12;
/** Hairline between bands: structure, not an outline. */
const RELIEF_CONTOUR_WIDTH = 0.45;
const RELIEF_CONTOUR_OPACITY = 0.42;

/** Every distinct relief elevation on a plate, ascending. Empty on a plate whose relief is hand-authored. */
export function hypsometricLevels(plate: Plate): number[] {
  const seen = new Set<number>();
  for (const l of plate.layers) {
    if (l.kind === 'relief' && l.elevation !== undefined) seen.add(l.elevation);
  }
  return [...seen].sort((a, b) => a - b);
}

/**
 * Which ramp step (1..RELIEF_RAMP_STEPS) an elevation earns on a sheet whose
 * relief levels are `levels`. The lowest level takes step 1, which is tuned
 * to sit a hair off the sheet's own ground colour, and the highest takes the
 * summit tint, so every sheet uses the whole ramp. An elevation not in the
 * list (nothing produces one today) is placed by how many levels it clears,
 * rather than dropped.
 */
export function hypsometricStep(levels: number[], elevation: number): number {
  if (levels.length === 0) return RELIEF_RAMP_STEPS;
  if (levels.length === 1) return RELIEF_RAMP_STEPS;
  const exact = levels.indexOf(elevation);
  const rank = exact >= 0 ? exact : Math.max(0, levels.filter((l) => l <= elevation).length - 1);
  return 1 + Math.round(((RELIEF_RAMP_STEPS - 1) * rank) / (levels.length - 1));
}

function reliefRampToken(step: number): string {
  const clamped = Math.min(RELIEF_RAMP_STEPS, Math.max(1, Math.round(step)));
  return `var(--plate-relief-${clamped})`;
}

// Computes {spacing, weight} for ONE relief layer's hachure from the
// nesting/area of every relief layer on the SAME plate (siblings only —
// region/band layers aren't contour bands and don't participate). Exported
// so the steepness signal itself is unit-testable independent of the SVG it
// eventually feeds into (same posture as hachure/wallGlyph below).
export function reliefHachureParams(plate: Plate, layer: PlateLayer, viewport: Viewport): ReliefHachureParams {
  const gentle = { spacing: RELIEF_SPACING_GENTLE, weight: RELIEF_WEIGHT_GENTLE };
  const siblings = plate.layers.filter(
    (l): l is PlateLayer & { polygon: PlatePoint[] } => l.kind === 'relief' && !!l.polygon && l.polygon.length >= 3,
  );
  if (siblings.length <= 1) return gentle;

  const projected = siblings.map((l) => ({ id: l.id, px: projectPoints(plate, l.polygon, viewport) }));
  const areaById = new Map(projected.map((p) => [p.id, polygonArea(p.px)]));
  const maxArea = Math.max(...areaById.values(), 1e-6);

  const depthById = new Map(
    projected.map((p) => {
      const centroid = polygonCentroid(p.px);
      let depth = 0;
      for (const other of projected) {
        if (other.id === p.id) continue;
        if (pointInPolygon(centroid, other.px)) depth++;
      }
      return [p.id, depth] as const;
    }),
  );
  const maxDepth = Math.max(1, ...depthById.values());

  const area = areaById.get(layer.id);
  const depth = depthById.get(layer.id);
  if (area === undefined || depth === undefined) return gentle; // this layer's own polygon didn't survive projection

  const normArea = 1 - area / maxArea; // 0 = the plate's biggest relief body, ->1 a small one
  const normDepth = depth / maxDepth; // 0 = unnested (a lone band), 1 = the most deeply nested band on the plate
  const steepness = clamp01(0.5 * normArea + 0.5 * normDepth);

  return {
    spacing: lerp(RELIEF_SPACING_GENTLE, RELIEF_SPACING_STEEP, steepness),
    weight: lerp(RELIEF_WEIGHT_GENTLE, RELIEF_WEIGHT_STEEP, steepness),
  };
}

function renderLayer(
  plate: Plate,
  layer: PlateLayer,
  viewport: Viewport,
  softId: (kind: SoftKind) => string,
  waters: WaterBody[],
): RenderedLayer | undefined {
  const allPixelPoints: [number, number][] = [];
  const collect = (pts: PlatePoint[] | undefined) => {
    if (!pts) return [];
    const px = projectPoints(plate, pts, viewport);
    allPixelPoints.push(...px);
    return px;
  };

  // Every measured line on a geographic sheet is drawn as a curve; a
  // schematic plate's authored zones stay the polygons they were drawn as.
  // See smoothPathD for why this is the honest drawing and not a cosmetic.
  const geographic = plate.kind === 'geographic';
  const lineD = (px: [number, number][], close: boolean) =>
    geographic ? smoothPathD(px, close, plate.size) : pathD(px, close);

  let markup = '';
  let submerged: { layerId: string; markup: string }[] | undefined;
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
      // A coast layer whose rings are CLOSED landmasses (the Troad sheet's
      // mainland and its islands) may declare the terrain they enclose, and
      // the body is filled under the shoreline — the same evenodd
      // land-over-sea construction shared/lib/scenemap.ts already uses for
      // the Mediterranean coastline. This is what turns a `ground: "sea"`
      // plate from outlines on parchment into a coastal map, and it costs the
      // plate file two words. Omit `fill` and nothing changes: the layer is
      // pure linework, exactly as before.
      const body = layer.fill
        ? `<path data-feature-id="${escapeXml(layer.id)}-body" class="plate-layer plate-layer-coast-body" ` +
          `d="${ringsPx.map((px) => lineD(px, true)).join(' ')}" fill="${REGION_FILL_TOKENS[layer.fill]}" ` +
          `fill-opacity="${REGION_FILL_OPACITY[layer.fill]}" fill-rule="evenodd" stroke="none"/>`
        : '';
      if (layer.style === 'approximate') {
        // A RECONSTRUCTED shoreline. Drawn as a soft graded band — a wide,
        // blurred stroke with a hairline down its middle — rather than as the
        // scatter of dots this register used to be. Two reasons, one of each
        // kind. Perceptual: every treatment built out of discrete marks has a
        // magnification at which it stops being tone and becomes countable
        // marks, and this SVG renders at 100% of a browser column, so it
        // reaches 3x routinely; a blurred stroke is the same drawing at every
        // scale. Cartographic: a fuzzy edge IS the claim. This line's own note
        // puts it within about a kilometre, and a band that fades out says so
        // without a legend, where dots only said "special".
        //
        // The hairline down the middle stays fully opaque and is what carries
        // WCAG 1.4.11 (3:1 for graphical objects): the soft band is a wash and
        // may not be relied on for contrast. It also keeps the reconstructed
        // shore plainly distinct from the surveyed modern one, which is a
        // solid line at twice the weight and no glow at all.
        const d = ringsPx.map((px) => lineD(px, false)).join(' ');
        markup =
          body +
          `<path data-feature-id="${escapeXml(layer.id)}-band" class="plate-layer plate-layer-coast-band" ` +
          `d="${d}" fill="none" stroke="var(--scene-map-coast)" stroke-width="${APPROX_BAND_WIDTH}" ` +
          `stroke-opacity="${APPROX_BAND_OPACITY}" stroke-linecap="round" stroke-linejoin="round" filter="url(#${softId('coast')})"/>` +
          `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-coast" ` +
          `d="${d}" fill="none" stroke="var(--scene-map-coast)" stroke-width="${APPROX_CORE_WIDTH}" ` +
          `stroke-linecap="round" stroke-linejoin="round"/>`;
      } else if (layer.style === 'waterline') {
        const coastD = ringsPx.map((px) => lineD(px, false)).join(' ');
        const strokes = waterlines(ringsPx, { seed });
        const strokeMarkup = strokes
          .map(
            (ln, i) =>
              `<path data-feature-id="${escapeXml(layer.id)}-waterline-${i}" class="plate-layer plate-layer-waterline" d="${ln.d}" fill="none" stroke="var(--plate-river)" stroke-width="${ln.width}" stroke-opacity="${ln.opacity}"/>`,
          )
          .join('');
        markup =
          body +
          `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-coast" d="${coastD}" fill="none" stroke="var(--scene-map-coast)" stroke-width="${layer.width ?? STROKE_WEIGHT.coast}"/>` +
          strokeMarkup;
      } else {
        const d = ringsPx.map((px) => lineD(px, false)).join(' ');
        markup = body + `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-coast" d="${d}" fill="none" stroke="var(--scene-map-coast)" stroke-width="${layer.width ?? STROKE_WEIGHT.coast}" stroke-linejoin="round"/>`;
      }
      break;
    }
    case 'river': {
      const px = collect(layer.path);
      if (px.length < 2) return undefined;
      // Rivers are OSM polylines sampled every hundred metres or so. Drawn as
      // segments they read as a chain of straight cuts at zoom; a watercourse
      // does not turn corners.
      const reach = (run: [number, number][]) =>
        `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-river" d="${lineD(run, false)}" fill="none" stroke="var(--plate-river)" stroke-width="${layer.width ?? STROKE_WEIGHT.river}" stroke-linecap="butt" stroke-linejoin="round"/>`;
      if (waters.length === 0) {
        markup = reach(px);
        break;
      }
      // Every reach that is not under water, drawn here; each drowned reach
      // handed to the water that drowns it, to be drawn beneath its fill.
      // See the WaterBody block above for why this is paint order and not a
      // cut of the data.
      markup = runsWhere(px, (p) => !waters.some((w) => w.contains(p))).map(reach).join('');
      submerged = waters
        .filter((w): w is WaterBody & { layerId: string } => w.layerId !== null)
        .map((w) => ({ layerId: w.layerId, markup: runsWhere(px, (p) => w.contains(p)).map(reach).join('') }))
        .filter((s) => s.markup !== '');
      break;
    }
    case 'relief': {
      if (layer.elevation !== undefined) {
        // Hypsometric register. A band carries either one `polygon` (a named
        // landform — Ida, the Sigeion ridge) or `rings`, several disjoint
        // bodies at the same contour level sharing one layer so the plate
        // file does not need sixty layers with sixty notes to say one thing.
        const parts: [number, number][][] = [];
        const poly = collect(layer.polygon);
        if (poly.length >= 3) parts.push(poly);
        for (const ring of layer.rings ?? []) {
          const ringPx = projectPoints(plate, ring, viewport);
          if (ringPx.length < 3) continue;
          allPixelPoints.push(...ringPx);
          parts.push(ringPx);
        }
        if (parts.length === 0) return undefined;
        const step = hypsometricStep(hypsometricLevels(plate), layer.elevation);
        markup =
          `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-relief-band" ` +
          `d="${parts.map((p) => lineD(p, true)).join(' ')}" fill="${reliefRampToken(step)}" ` +
          `stroke="var(--plate-contour)" stroke-width="${RELIEF_CONTOUR_WIDTH}" ` +
          `stroke-opacity="${RELIEF_CONTOUR_OPACITY}" stroke-linejoin="round"/>`;
        break;
      }
      const px = collect(layer.polygon);
      if (px.length < 3) return undefined;
      const { spacing, weight } = reliefHachureParams(plate, layer, viewport);
      const d = hachure(px, { seed, spacing, weight });
      // The hachure strokes used to be the ONLY thing drawn for a relief
      // layer, so they read as a free-floating comb with no ridge under
      // them (2026-07-28). The body goes down first, opaque — never a
      // fill-opacity on an already-composited ink token, which is the
      // double-alpha defect --flaxman-hachure exists to prevent.
      markup =
        `<path data-feature-id="${escapeXml(layer.id)}-body" class="plate-layer plate-layer-relief-body" d="${pathD(px, true)}" fill="var(--plate-upland)" stroke="var(--scene-map-coast)" stroke-width="0.5" stroke-opacity="0.45"/>` +
        `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-relief" d="${d}" fill="var(--flaxman-hachure)" stroke="none"/>`;
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
      // A region/band layer names the TERRAIN it is (plain, marsh, lagoon,
      // sea, land) through the closed REGION_FILL_TOKENS whitelist — never a
      // pass-through of the JSON value, so a plate file can never inject CSS.
      // `tint` is now an explicit opt-in for the one thing that colour was
      // ever for, a decorative apparatus zone; it is no longer the default,
      // because defaulting a landform to the site's wine accent is what made
      // the geographic plate read as shapes rather than geography.
      const fill = layer.fill ?? DEFAULT_REGION_FILL;
      const d = lineD(px, true);
      // `none` is a region that carries a NAME and nothing else — the lettering
      // zone for a tract of country whose extent nobody surveyed. It exists
      // because the alternative on this sheet was worse: an eleven-vertex
      // hand-drawn wash with a ruler-straight edge, presented as a landform,
      // sitting on top of a hypsometric ramp cut from a DEM. The ramp already
      // draws the ground; the region only ever had to say where the name goes.
      if (fill === 'none') {
        markup =
          `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-${layer.kind}" ` +
          `d="${d}" fill="none" stroke="none"/>`;
        break;
      }
      // A wetland has no boundary. It is a gradient from open water through
      // reed and seasonal flood to dry ground, and it moves with the season
      // and the year, so a crisp vector edge round it asserts a precision that
      // exists nowhere in the evidence. The marsh register therefore draws
      // with NO outline and a blurred fill, so the wet ground dissolves into
      // the plain over a few hundred metres of sheet — which is what the note
      // on the layer says in words (2026-07-29, John: "that green area is too
      // sharp at the edges"). Smoothing alone would only have bought a curvy
      // hard edge.
      const soft = fill === 'marsh';
      const fillToken = REGION_FILL_TOKENS[fill];
      const strokeToken = WATER_FILLS.has(fill) ? 'var(--scene-map-coast)' : fillToken;
      const strokeOpacity = fill === 'tint' ? 1 : WATER_FILLS.has(fill) ? 0.7 : 0.5;
      markup = soft
        ? `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-${layer.kind}" d="${d}" ` +
          `fill="${fillToken}" fill-opacity="${REGION_FILL_OPACITY[fill]}" stroke="none" filter="url(#${softId('marsh')})"/>`
        : `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-${layer.kind}" d="${d}" ` +
          `fill="${fillToken}" fill-opacity="${REGION_FILL_OPACITY[fill]}" stroke="${strokeToken}" stroke-width="0.8" stroke-opacity="${strokeOpacity}" stroke-linejoin="round"/>`;
      break;
    }
    case 'tumulus': {
      const px = collect(layer.path);
      if (px.length === 0) return undefined;
      const d = px.map((p) => tumulus(p)).join(' ');
      markup = `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-tumulus" d="${d}" fill="none" stroke="var(--flaxman-ink)" stroke-width="${layer.width ?? STROKE_WEIGHT.tumulus}"/>`;
      break;
    }
    default:
      return undefined;
  }

  if (allPixelPoints.length === 0) return undefined;
  const bbox = bboxOf(allPixelPoints);
  const isArea = AREA_LAYER_KINDS.has(layer.kind);
  let labelAnchor: Box;
  if (isArea) {
    labelAnchor = bbox;
  } else {
    const mid = allPixelPoints[Math.floor(allPixelPoints.length / 2)];
    labelAnchor = [mid[0] - 1, mid[1] - 1, mid[0] + 1, mid[1] + 1];
  }
  return {
    markup,
    feature: { id: layer.id, type: 'layer', kind: layer.kind, bbox },
    labelAnchor,
    labelCentred: isArea,
    labelRole: LAYER_LABEL_ROLE[layer.kind],
    labelPath: isArea ? undefined : linearRun(plate, layer, viewport),
    submerged,
  };
}

// ── Full render ──────────────────────────────────────────────────────────

// A bbox-less schematic plate has no geography to fit a geographic viewport
// around (gap 1's second half): projectPoint's schematic branch reads
// plate.size directly and never touches project()/the viewport's
// geographic fields (centerLat/centerLon/latSpan/lonSpan/scale), so this
// synthetic viewport exists only to give computeCamera and PlateResult's
// returned `viewport` a width/height to reason about — a unit-space plate
// maps its u,v in 0..1 across exactly that canvas. Its geographic fields
// are meaningless placeholders, never read on a bbox-less plate.
function unitViewport(size: [number, number]): Viewport {
  const [width, height] = size;
  return { width, height, centerLat: 0, centerLon: 0, latSpan: 1, lonSpan: 1, scale: 1 };
}

// Assembles a plate's layers + gazetteer pins into one self-contained SVG
// string. Pure and deterministic: identical inputs always produce an
// identical `svg` string (see hachure's seeded PRNG above).
export function renderPlate(plate: Plate, places: PlatePlace[], options: PlateOptions = {}): PlateResult {
  const opts = { ...DEFAULT_PLATE_OPTIONS, ...options };
  const viewport = plate.bbox ? viewportFromBBox(plate.bbox, plate.size) : unitViewport(plate.size);
  const [width, height] = plate.size;

  const features: RenderedFeature[] = [];
  // Each drawn layer's own markup, in paint order, plus the reaches of other
  // layers that must be drawn UNDER it (see WaterBody): a river's submerged
  // reach belongs to the water's paint slot, and the water is drawn before
  // the river, so the two are assembled after the whole pass rather than
  // pushed as they are rendered.
  const drawn: { layerId: string; markup: string }[] = [];
  const submergedByWater = new Map<string, string[]>();
  const waters = collectWaterBodies(plate, viewport);
  // Every place id actually carried by a rendered layer (Problem 2, gap
  // fixed 2026-07-28): a layer that failed to render (renderLayer returned
  // undefined — e.g. its geometry field was empty) contributes nothing, so
  // this can never claim a place is "drawn" when its only layer silently
  // dropped out.
  const layerPlaceIds = new Set<string>();
  // Layers that could be lettered, paired with where their name would sit.
  // Resolved AFTER the pin pass, because a feature is lettered once: a layer
  // whose `placeId` is also pinned on this sheet takes its name from the pin.
  const layerLabelCandidates: { layer: PlateLayer; rendered: RenderedLayer }[] = [];
  const legendEntries: LegendEntry[] = [];
  // The blurred-edge filters (see SOFT_BLUR). Each is declared only when
  // something on the sheet actually uses it, so a plate with no indefinite
  // features emits exactly what it did before.
  const softId = (kind: SoftKind) => `${safeIdFragment(opts.idPrefix)}-soft-${kind}`;
  const needsSoft: Record<SoftKind, boolean> = {
    coast: plate.layers.some((l) => l.kind === 'coast' && l.style === 'approximate'),
    marsh: plate.layers.some((l) => l.fill === 'marsh'),
  };
  for (const layer of plate.layers) {
    const rendered = renderLayer(plate, layer, viewport, softId, waters);
    if (!rendered) continue;
    drawn.push({ layerId: layer.id, markup: rendered.markup });
    for (const under of rendered.submerged ?? []) {
      const bucket = submergedByWater.get(under.layerId);
      if (bucket) bucket.push(under.markup);
      else submergedByWater.set(under.layerId, [under.markup]);
    }
    features.push(rendered.feature);
    if (layer.placeId) layerPlaceIds.add(layer.placeId);
    if (layer.label || layer.placeId) layerLabelCandidates.push({ layer, rendered });
    const legend = layerLegendEntry(layer);
    if (legend) legendEntries.push(legend);
    // A coast layer that fills its rings also keys the terrain it encloses.
    if (layer.kind === 'coast' && layer.fill) {
      const fillEntry = regionFillLegendEntry(layer.fill);
      if (fillEntry) legendEntries.push(fillEntry);
    }
  }

  const layerMarkup = drawn.map(
    ({ layerId, markup }) => (submergedByWater.get(layerId) ?? []).join('') + markup,
  );

  const placeById = new Map(places.map((p) => [p.id, p]));

  const located: PlatePlace[] = [];
  const offCanvas: PlatePlace[] = [];
  const unlocated: PlatePlace[] = [];
  const drawnByLayer: PlatePlace[] = [];
  const pinMarkupParts: string[] = [];
  const pinLabelRequests: LabelRequest[] = [];
  for (const place of places) {
    const pos = resolvePlacePosition(plate, place, viewport);
    if (!pos) {
      // A place with no defensible pin position may still be visibly drawn
      // via a layer's own geometry (see `drawnByLayer`'s doc comment above)
      // — that is a true, distinct claim from "named, not drawn," so it
      // gets its own bucket rather than landing in `unlocated`.
      if (layerPlaceIds.has(place.id)) {
        drawnByLayer.push(place);
      } else {
        unlocated.push(place);
      }
      continue;
    }
    const [x, y] = pos;
    // Finding 1 (2026-07-28, an apparatus-honesty bug): a defensible
    // position is not the same thing as a position ON THIS PLATE. Before
    // this check, every place resolvePlacePosition returned ANY [x, y]
    // for was bucketed as "located," even when that point fell outside
    // the plate's own canvas — the SVG clip-path then hid the pin, so the
    // place appeared neither on the map nor in the "named, not drawn"
    // list: silently dropped. A point exactly on the canvas edge counts
    // as located (inclusive bounds) — it is still honestly ON the sheet.
    if (x < 0 || x > width || y < 0 || y > height) {
      offCanvas.push(place);
      continue;
    }
    located.push(place);
    const style = certaintyPinStyle(place.certainty);
    // Any place resolved on a schematic plate got there via plateAnchors +
    // positionBasis: "conjectural" (see resolvePlacePosition) — there is no
    // other path to a position on a schematic plate.
    const conjectural = plate.kind === 'schematic';
    pinMarkupParts.push(pinMarkup(place.id, place.name, x, y, style, conjectural));
    features.push({ id: place.id, type: 'place', kind: place.certainty ?? 'certain', bbox: pinBBox(x, y) });
    pinLabelRequests.push({
      text: mapLabelText(place.name),
      role: 'settlement',
      anchorBox: pinBBox(x, y),
      conjectural,
    });
    legendEntries.push(certaintyLegendEntry(place.certainty ?? 'certain'));
    if (conjectural) {
      legendEntries.push({
        key: 'conjectural',
        rank: 50,
        text: 'Position conjectural — set by the poem, not by survey',
        swatch: (lx, ly) =>
          legendPin(lx, ly, { fill: 'var(--text-mid)', stroke: 'var(--text-mid)' }, CONJECTURAL_DASHARRAY),
      });
    }
  }

  // A layer's own name: its explicit `label` if it has one, else the
  // gazetteer name of its `placeId` — and that fallback only when the place
  // is NOT pinned here, so a feature is never lettered twice.
  const pinnedIds = new Set(located.map((p) => p.id));
  const layerLabelRequests: LabelRequest[] = [];
  for (const { layer, rendered } of layerLabelCandidates) {
    const gazName = layer.placeId && !pinnedIds.has(layer.placeId) ? placeById.get(layer.placeId)?.name : undefined;
    const fallback = gazName ? mapLabelText(gazName) : undefined;
    const text = layer.label ?? fallback;
    if (!text) continue;
    layerLabelRequests.push({
      text,
      role: rendered.labelRole,
      anchorBox: rendered.labelAnchor,
      centred: rendered.labelCentred,
      path: rendered.labelPath,
      pathId: `${safeIdFragment(opts.idPrefix)}-lp-${safeIdFragment(layer.id)}`,
    });
  }

  // When a layer and a pin would letter the same name, the PIN keeps it: the
  // pin is the thing a reader clicks and the thing the certainty tier is
  // attached to, so an unlabelled pin beside a named line is the worse of the
  // two failures. Filtered here rather than inside layoutLabels because only
  // this scope knows which request came from which source.
  const pinnedNames = new Set(pinLabelRequests.map((r) => r.text.trim().toLocaleLowerCase()));
  const labels = layoutLabels(
    [...layerLabelRequests.filter((r) => !pinnedNames.has(r.text.trim().toLocaleLowerCase())), ...pinLabelRequests],
    width,
    height,
    LABEL_MARGIN,
  );

  // Finding 8 (2026-07-28): idPrefix is caller-supplied and lands directly
  // in an SVG element id — sanitize it the same way shield.ts does (see
  // safeIdFragment), rather than interpolating it raw.
  const clipId = `${safeIdFragment(opts.idPrefix)}-clip`;
  const ariaLabel = escapeXml(plate.title);

  const svg =
    `<svg viewBox="0 0 ${width} ${height}" width="100%" height="100%" role="img" aria-label="${ariaLabel}" xmlns="http://www.w3.org/2000/svg">` +
    `<defs><clipPath id="${clipId}"><rect x="0" y="0" width="${width}" height="${height}"/></clipPath>` +
    (Object.keys(SOFT_BLUR) as SoftKind[])
      .filter((k) => needsSoft[k])
      .map(
        (k) =>
          `<filter id="${softId(k)}" x="-25%" y="-25%" width="150%" height="150%" ` +
          `filterUnits="objectBoundingBox" color-interpolation-filters="sRGB">` +
          `<feGaussianBlur stdDeviation="${SOFT_BLUR[k]}"/></filter>`,
      )
      .join('') +
    `${labels.defs}</defs>` +
    `<g clip-path="url(#${clipId})">` +
    `<rect class="plate-ground" x="0" y="0" width="${width}" height="${height}" fill="${GROUND_FILL_TOKENS[plate.ground ?? 'land']}"/>` +
    layerMarkup.join('') +
    pinMarkupParts.join('') +
    labels.markup +
    legendMarkup(legendEntries, width, height) +
    `</g>` +
    // Frame and bar scale sit OUTSIDE the clip: their strokes run along the
    // sheet edge and would be shaved in half by it. The scale bar is drawn
    // from this plate's own viewport, so it is honest by construction, and
    // only for a geographic plate — a schematic sheet has no scale, and
    // drawing one would be a fabricated claim.
    (plate.kind === 'geographic' ? scaleBarMarkup(viewport, width, height) : '') +
    hypsometricKeyMarkup(plate, width, height) +
    neatlineMarkup(width, height) +
    `</svg>`;

  return { svg, viewport, features, unlocated, offCanvas, drawnByLayer };
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
