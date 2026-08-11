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
  // Surveyed masonry: a wall, a tower, a house block traced off an excavation
  // plan (2026-07-30, citadel plate). Its own register, not a decorative tint,
  // because on a plan of a dug site the difference between "these stones were
  // measured" and "this line is restored" is the whole content of the sheet.
  // Dörpfeld printed his own masonry in red — "bei der Festungsmauer ist der
  // Unterbau hellrot, die dünnere Obermauer dunkelrot getönt" (1902, 2:650) —
  // so the token stays in that family rather than inventing a colour for a
  // convention the source already fixed; what it adds is opacity and an INK
  // edge, so a wall band reads as built stone with a drawn face instead of a
  // wash. See the `region` case in renderLayer for the edge.
  masonry: 'var(--plate-masonry)',
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
  // Opaque: masonry is a body of stone, not a wash over ground.
  masonry: 1,
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
  /**
   * The words this layer's own key row is to read (2026-07-30, citadel plate).
   * The auto-derived rows name a REGISTER — "Fortification", "Dry plain" — which
   * is right for a sheet whose registers are self-explaining and wrong for one
   * where the same register carries two different claims: on the citadel plate
   * the tinted bands are surveyed masonry and the open bands are Dörpfeld's
   * restoration, and a key reading "Apparatus zone" against either of them tells
   * a reader nothing about which. Set it and the row keeps its swatch and takes
   * these words; leave it and nothing changes.
   */
  legend?: string;
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
  /**
   * Plate pixels per metre of ground — a schematic plate's declaration that it
   * IS drawn to a true and constant scale (2026-07-30, citadel plate). A
   * schematic plate normally has none: the Trojan plain laid out as the poem
   * lays it out has no metre in it, and drawing a bar scale on such a sheet
   * would be a fabricated claim, which is why the bar is otherwise
   * geographic-only. The citadel plate is the other case — every vertex on it
   * is traced off Dörpfeld's 1:800 Tafel V, so there is a real metre on the
   * sheet and withholding the bar would be the dishonesty. Declare it only
   * where the whole sheet is one rectified survey; a plate that mixes a
   * measured plan with placed-by-eye material has no single figure to give.
   */
  pxPerMetre?: number;
  /**
   * The caption under this plate's north arrow (2026-07-30, citadel plate).
   * Its presence is what draws the arrow at all, and the words are the caveat:
   * a plan on an 1890s magnetic bearing is not on true north, and the sheet
   * should say which it is rather than leaving a reader to assume. Omit it and
   * no arrow is drawn — the honest default for a plate with no declared
   * orientation.
   */
  north?: string;
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
  /**
   * The gazetteer's own fine-grained category (`settlement`, `river`,
   * `mountain`, `island`, `strait`, `hill`, `plain`, ...) — see
   * apparatus/places.json. Used only on a GEOGRAPHIC plate (see
   * `placeLabelClass` below) to derive which of the five Landmark label
   * classes — region / water / river / settlement / feature — a place
   * prints as; a schematic plate ignores it entirely and keeps its existing
   * pin+label treatment, unchanged. Optional and best-effort: a place with
   * no `kind` (most of the gazetteer, as of this writing) defaults to
   * `settlement`, which is exactly today's behaviour for every such place.
   */
  kind?: string;
  /**
   * Editorial settlement hierarchy — 1 (Troy), 2 (often met in the poem), 3
   * (minor) — from docs/research/AUDIT-PLATE-LABELS.md's rank column. NOT a
   * certainty claim (that is `certainty`); only changes a settlement
   * label's type weight/size on a geographic plate. Undefined reads as
   * rank 2, the ordinary case.
   */
  rank?: 1 | 2 | 3;
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
  // Ids (place or layer) whose label was DROPPED rather than printed
  // illegibly — only ever an id that opted into suppression via
  // LabelRequest.priority (geographic settlement rank 3 / feature, see
  // renderPlate), and only when its own best placement was still badly
  // overlapped (see SUPPRESS_OVERLAP_FRACTION). Reported, not silent: this
  // is the honesty mechanism item 7 asks for — a name that cannot be read is
  // worse than an absent one, but the absence itself is never quiet. Always
  // empty for a schematic plate, which suppresses nothing.
  suppressedLabels: string[];
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
  // A legend override that is present but blank is an authoring slip, not an
  // instruction to key the row with an empty string — reject it rather than
  // silently falling back to the derived words (mirrors apparatus_places.py).
  if (l.legend !== undefined && (typeof l.legend !== 'string' || !l.legend.trim())) {
    fail(`layer "${l.id}" has a malformed "legend" (must be a non-empty string)`);
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
    legend: typeof l.legend === 'string' && l.legend.trim() ? l.legend : undefined,
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

  // See Plate.pxPerMetre / Plate.north. Both are claims a reader will measure
  // the sheet against — a bar scale and a bearing — so a malformed one is
  // rejected rather than coerced away: a zero or negative scale would draw a
  // bar of nonsense, and a blank caption would draw an arrow that says nothing
  // about which north it points to.
  if (d.pxPerMetre !== undefined && !(isFiniteNumber(d.pxPerMetre) && d.pxPerMetre > 0)) {
    fail('pxPerMetre must be a number > 0');
  }
  if (d.north !== undefined && (typeof d.north !== 'string' || !d.north.trim())) {
    fail('north must be a non-empty string (the caption under the arrow)');
  }

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
    pxPerMetre: isFiniteNumber(d.pxPerMetre) ? d.pxPerMetre : undefined,
    north: typeof d.north === 'string' && d.north.trim() ? d.north : undefined,
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
export function traceSide(trace: PlatePoint[]): 1 | -1 {
  let signedArea = 0;
  for (let i = 0; i + 1 < trace.length; i++) {
    signedArea += trace[i][0] * trace[i + 1][1] - trace[i + 1][0] * trace[i][1];
  }
  return signedArea >= 0 ? 1 : -1;
}

// One side of a polyline, offset by `dist` along the vertex normals. The
// normal at an interior vertex is the bisector of its two segment normals,
// lengthened by 1/cos(half-angle) — a plain average pinches the offset shut
// through a bend, which on a wall band shows up as the band narrowing at every
// one of Dörpfeld's offsets, i.e. exactly where a reader is looking. The miter
// is clamped so a near-reversal (a spur, a gate return) can't throw the offset
// vertex to infinity.
const MAX_MITER = 4;
export function offsetPolyline(pts: PlatePoint[], dist: number): [number, number][] {
  const n = pts.length;
  if (n < 2) return pts.map((p) => [p[0], p[1]]);
  const seg: [number, number][] = [];
  for (let i = 0; i + 1 < n; i++) {
    const dx = pts[i + 1][0] - pts[i][0];
    const dy = pts[i + 1][1] - pts[i][1];
    const len = Math.hypot(dx, dy) || 1;
    seg.push([-dy / len, dx / len]); // unit normal, left of travel
  }
  // A polyline that comes back to its own first point (the citadel's terrace
  // rings) is mitred across the seam too — otherwise the closing vertex takes a
  // one-sided normal and the band shows a notch at whichever arbitrary point
  // the author happened to start the ring.
  const closed =
    Math.hypot(pts[n - 1][0] - pts[0][0], pts[n - 1][1] - pts[0][1]) < 1e-6 && seg.length > 1;
  const out: [number, number][] = [];
  for (let i = 0; i < n; i++) {
    const a = seg[i === 0 ? (closed ? seg.length - 1 : 0) : i - 1];
    const b = seg[i === n - 1 ? (closed ? 0 : seg.length - 1) : i];
    let nx = a[0] + b[0];
    let ny = a[1] + b[1];
    const mag = Math.hypot(nx, ny);
    if (mag < 1e-9) {
      nx = b[0];
      ny = b[1];
    } else {
      nx /= mag;
      ny /= mag;
      const cos = nx * b[0] + ny * b[1];
      const miter = Math.min(MAX_MITER, cos > 1e-3 ? 1 / cos : MAX_MITER);
      nx *= miter;
      ny *= miter;
    }
    out.push([pts[i][0] + nx * dist, pts[i][1] + ny * dist]);
  }
  return out;
}

export interface WallBandGlyphResult {
  /** The two faces of the band, as one `d` of two open subpaths. */
  faces: string;
  /** Sparse slant strokes spanning the band, as one `d`. '' when there is no room. */
  hatch: string;
}

// A RESTORED length of wall: the same wall, drawn hollow. Two fine faces at the
// wall's own width with an open interior and a sparse slant hatch inside it —
// the archaeological plan's oldest distinction, solid for what was dug and
// outline for what was reasoned, and the reason this replaced a ticked hairline
// (2026-07-30): drawn as a line beside 5 m bands of surveyed masonry, a
// restored stretch did not read as the same wall continuing, it read as a
// different kind of object, and a reader's eye lost the circuit at the join.
// Width is the caller's, in plate pixels, because it is a DRAWING convention
// and not a measurement — nobody has measured the thickness of a wall nobody
// has seen; matching the surveyed band beside it is what says "this wall, here,
// restored", and the layer's own note says the rest.
export function wallBandGlyph(trace: PlatePoint[], width: number): WallBandGlyphResult {
  if (trace.length < 2 || !(width > 0)) return { faces: '', hatch: '' };
  const half = width / 2;
  const left = offsetPolyline(trace, half);
  const right = offsetPolyline(trace, -half);
  const faces = `${pathD(left, false)} ${pathD(right, false)}`;

  // Arc length along the centre line, so the hatch keeps an even rhythm
  // through the offsets rather than bunching where vertices crowd.
  const cum: number[] = [0];
  for (let i = 0; i + 1 < trace.length; i++) {
    cum.push(cum[i] + Math.hypot(trace[i + 1][0] - trace[i][0], trace[i + 1][1] - trace[i][1]));
  }
  const total = cum[cum.length - 1];
  const spacing = Math.max(width * 1.6, 14);
  if (!(total > spacing * 2)) return { faces, hatch: '' };
  const at = (pts: [number, number][], s: number): [number, number] => {
    const t = Math.min(Math.max(s, 0), total);
    let i = 1;
    while (i < cum.length - 1 && cum[i] < t) i++;
    const span = cum[i] - cum[i - 1] || 1;
    const f = (t - cum[i - 1]) / span;
    return [
      pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f,
      pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f,
    ];
  };
  const parts: string[] = [];
  // The slant: each stroke runs from one face to the other one band-width
  // further along, so it lies at about 45° to the wall all the way round and
  // stays a hatch rather than becoming a ladder of rungs.
  for (let s = spacing; s <= total - width - 1; s += spacing) {
    const a = at(left, s);
    const b = at(right, s + width);
    parts.push(`M ${round1(a[0])} ${round1(a[1])} L ${round1(b[0])} ${round1(b[1])}`);
  }
  return { faces, hatch: parts.join(' ') };
}

export function wallGlyph(trace: PlatePoint[]): WallGlyphResult {
  if (trace.length < 2) return { line: '', ticks: '' };

  const side = traceSide(trace);

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

// ── Dot symbology (geographic plates only, 2026-08-10) ─────────────────────
// The Landmark-style comp's approved replacement for the teardrop pin above,
// which stays exactly as it was and stays in use on every SCHEMATIC plate
// (the citadel, the shield, the Trojan-plain schematic sheet — see the
// LabelRole/layerLabelRole comments for why the split is on plate.kind).
// A dot has no tip to anchor a leader to the way a pin's point does, so its
// box (see dotBBox) is centred on the coordinate, not tip-anchored — the
// honest shape for a symbol that MEANS "this point," not "this point is at
// my bottom corner."
//
// Certainty keeps the colour split the teardrop pins used (--accent for a
// tier the gazetteer stands behind, --text-mid for one it does not) and adds
// shape: solid disc / open disc / open square, plus a dashed open disc for
// `mythical` (the audit's own note: "same visual family as traditional").
// "Open" fills with --scene-map-label-halo rather than `none` — the same
// non-transparency argument certaintyPinStyle's own comment makes: a hollow
// marker over hachured relief must still read as ground covered by a symbol,
// not as the terrain simply continuing through it.
interface DotStyle {
  shape: 'circle' | 'square';
  fill: string;
  stroke: string;
  dasharray?: string;
}

function certaintyDotStyle(certainty: Certainty | undefined): DotStyle {
  switch (certainty) {
    case 'traditional':
      return { shape: 'circle', fill: 'var(--scene-map-label-halo)', stroke: 'var(--accent)' };
    case 'speculative':
      return { shape: 'square', fill: 'var(--scene-map-label-halo)', stroke: 'var(--text-mid)' };
    case 'mythical':
      return { shape: 'circle', fill: 'var(--scene-map-label-halo)', stroke: 'var(--text-mid)', dasharray: '2 2' };
    case 'certain':
    default:
      return { shape: 'circle', fill: 'var(--accent)', stroke: 'var(--accent)' };
  }
}

const DOT_STROKE_WIDTH = 1;

function dotSymbol(x: number, y: number, style: DotStyle, r: number): string {
  const dash = style.dasharray ? ` stroke-dasharray="${style.dasharray}"` : '';
  if (style.shape === 'square') {
    const half = round1(r * 0.9); // a square at the dot's own radius reads oversized next to a circle of the same r
    return (
      `<rect x="${round1(x - half)}" y="${round1(y - half)}" width="${round1(half * 2)}" height="${round1(half * 2)}" ` +
      `fill="${style.fill}" stroke="${style.stroke}" stroke-width="${DOT_STROKE_WIDTH}"${dash}/>`
    );
  }
  return `<circle cx="${round1(x)}" cy="${round1(y)}" r="${round1(r)}" fill="${style.fill}" stroke="${style.stroke}" stroke-width="${DOT_STROKE_WIDTH}"${dash}/>`;
}

function dotMarkup(id: string, name: string, x: number, y: number, style: DotStyle, r: number): string {
  return `<g data-place-id="${escapeXml(id)}"><title>${escapeXml(name)}</title>${dotSymbol(x, y, style, r)}</g>`;
}

function dotBBox(x: number, y: number, r: number): [number, number, number, number] {
  return [x - r, y - r, x + r, y + r];
}

// Small — 2.5-4px at 1x (the brief's own range) — and ranked: a settlement's
// dot grows with its rank the same way its label's weight does, so Troy
// reads as the biggest mark on the sheet by BOTH registers, not just one.
const SETTLEMENT_DOT_R: Record<1 | 2 | 3, number> = { 1: 4, 2: 3.2, 3: 2.6 };
const FEATURE_DOT_R = 2.6;

// ── Label class (geographic places only) ────────────────────────────────
// Which of the five Landmark classes — region / water / river / settlement /
// feature — a place prints as. Derived from the gazetteer's own fine-grained
// `kind` (apparatus/places.json), which every place this renders already
// carries (docs/research/AUDIT-PLATE-LABELS.md spot-checked all 73 places on
// the two shipping sheets against it). A handful of ids read differently
// than their raw `kind` in context — Sigeion/Rhoiteion are inhabited
// headlands, not bare capes; Tenedos is a small island CITY, not a
// landmass; Dardania is a territory the gazetteer happens to type
// `settlement` — and those are the audit's own recommended overrides, not a
// re-reading of `kind` itself. A place with no `kind` at all (most of the
// gazetteer, as of this writing, and every synthetic test fixture) defaults
// to `settlement` — exactly today's pin+bold-label treatment.
const KIND_LABEL_CLASS: Record<string, LabelRole> = {
  settlement: 'settlement',
  river: 'river',
  mountain: 'feature',
  island: 'region',
  strait: 'water',
  hill: 'feature',
  plain: 'region',
  spring: 'feature',
  region: 'region',
  wall: 'feature',
  gate: 'feature',
  tower: 'feature',
  tree: 'feature',
  tomb: 'feature',
  ford: 'feature',
  harbour: 'water',
  camp: 'region',
  promontory: 'feature',
};

const LABEL_CLASS_OVERRIDE: Record<string, LabelRole> = {
  dardania: 'region', // a territory name, not the city of Dardanos
  sigeion: 'settlement', // inhabited headland city, not a bare cape
  rhoiteion: 'settlement', // inhabited headland city, not a bare cape
  tenedos: 'settlement', // a small island CITY (Landmark convention), unlike Lesbos/Imbros/Lemnos/Samothrace
};

function placeLabelClass(place: PlatePlace): LabelRole {
  return LABEL_CLASS_OVERRIDE[place.id] ?? (place.kind ? KIND_LABEL_CLASS[place.kind] : undefined) ?? 'settlement';
}

/** Classes that never carry a marker on a geographic plate (item 3: "Regions, water and rivers get NO marker"). */
const MARKERLESS_LABEL_CLASSES: ReadonlySet<LabelRole> = new Set<LabelRole>(['region', 'water', 'river']);

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

// `river` and `feature` (2026-08-10, landmark-label lane) are ADDITIVE: the
// four original roles keep their exact styling and every existing call site
// (schematic plates, and any place/layer that never resolves to one of the
// two new roles) is byte-for-byte unchanged. The two new roles are assigned
// ONLY on a GEOGRAPHIC plate — see `layerLabelRole` and `placeLabelClass` —
// so a schematic sheet (the citadel, the shield, the Trojan-plain schematic)
// never emits them and never sees a pixel of difference from this lane.
type LabelRole = 'region' | 'settlement' | 'water' | 'minor' | 'river' | 'feature';

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
  // Geographic-plate-only (see the LabelRole comment above). A river is
  // running water, the same claim `water` makes, so it takes the same
  // --plate-river ink (already 3:1-tested against every relief step) —
  // but set mixed-case, not letterspaced caps, because it is read ALONG a
  // line via textPath, not centred over an area: caps+tracking is the
  // area convention (region, water), and a channel name in that register
  // reads as a second bay, not a river.
  river: { size: 11.5, weight: 400, italic: true, caps: false, tracking: 0, fill: 'var(--plate-river)' },
  // A hill, tumulus, cape or spring is not a town: italic marks it as the
  // "not built" register `water`/`river` already use, caps keeps it in the
  // area-ish family (a feature is a spot on the ground, not an inhabited
  // place), and it sits at the type floor — smaller and muted, so it never
  // competes with a settlement pin's roman weight.
  feature: { size: 9.5, weight: 400, italic: true, caps: true, tracking: 0.08, fill: 'var(--text-mid)' },
};

// Settlement rank (docs/research/AUDIT-PLATE-LABELS.md's rank column, thread
// through PlatePlace.rank) overlays weight/size on the base `settlement`
// style rather than replacing it — rank 2 (the ordinary case, and every
// place with no rank set at all) is the base style, UNCHANGED. Weight leads
// the hierarchy, per the dossier's own "rank by weight, not size" rule; size
// moves too, but modestly, so Troy is unmistakably the heaviest mark on the
// sheet without a region name outsizing every settlement under it.
const SETTLEMENT_RANK_STYLE: Record<1 | 2 | 3, Partial<LabelStyle>> = {
  1: { weight: 700, size: 16 },
  2: {},
  3: { weight: 500, size: 11.5 },
};

export type LabelAnchor = 'start' | 'middle' | 'end';

export type LabelBox = [number, number, number, number]; // [x1, y1, x2, y2]

type Box = LabelBox;

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

function overlapArea(a: Box, b: Box): number {
  return Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) * Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
}

export type LabelPosition = 'E' | 'W' | 'N' | 'S' | 'NE' | 'NW' | 'SE' | 'SW';

interface LabelPoint {
  x: number;
  y: number; // baseline
  anchor: LabelAnchor;
}

export interface LabelCandidate extends LabelPoint {
  position: LabelPosition;
}

function labelBox(c: LabelPoint, textWidth: number, style: Pick<LabelStyle, 'size'>): Box {
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

export function labelCandidates(anchorBox: LabelBox, fontSize: number): LabelCandidate[] {
  const [x1, y1, x2, y2] = anchorBox;
  const cx = (x1 + x2) / 2;
  const cy = (y1 + y2) / 2;
  const half = fontSize * 0.36; // roughly half a cap height, to centre a side-set name
  const out: LabelCandidate[] = [];
  for (const gap of LABEL_GAPS) {
    out.push(
      { position: 'NE', x: x2 + gap, y: y1 + half, anchor: 'start' },
      { position: 'E', x: x2 + gap, y: cy + half, anchor: 'start' },
      { position: 'N', x: cx, y: y1 - gap, anchor: 'middle' },
      { position: 'S', x: cx, y: y2 + gap + fontSize * 0.72, anchor: 'middle' },
      { position: 'W', x: x1 - gap, y: cy + half, anchor: 'end' },
      { position: 'NW', x: x1 - gap, y: y1 + half, anchor: 'end' },
      { position: 'SE', x: x2 + gap, y: y2 + gap + fontSize * 0.6, anchor: 'start' },
      { position: 'SW', x: x1 - gap, y: y2 + gap + fontSize * 0.6, anchor: 'end' },
    );
  }
  return out;
}

export interface LabelPlacementInput {
  id: string;
  anchorBox: LabelBox;
  textWidth: number;
  fontSize: number;
}

export interface LabelPlacement {
  id: string;
  candidate: LabelCandidate;
  candidateIndex: number;
  box: LabelBox;
  penalty: number;
}

export interface LabelPlacementOptions {
  width: number;
  height: number;
  margin: number;
  markerBoxes?: LabelBox[];
  placedBoxes?: LabelBox[];
}

function offViewBoxArea(box: Box, width: number, height: number, margin: number): number {
  const visibleWidth = Math.max(0, Math.min(box[2], width - margin) - Math.max(box[0], margin));
  const visibleHeight = Math.max(0, Math.min(box[3], height - margin) - Math.max(box[1], margin));
  return Math.max(0, (box[2] - box[0]) * (box[3] - box[1]) - visibleWidth * visibleHeight);
}

// Places pin labels from a fixed candidate set. Large multipliers make a
// visible collision more costly than a modestly longer leader, while the
// candidate index gives exact ties a stable, deliberate outcome.
export function placeLabelCandidates(
  inputs: LabelPlacementInput[],
  options: LabelPlacementOptions,
): LabelPlacement[] {
  const placed = [...(options.placedBoxes ?? [])];
  const markerBoxes = options.markerBoxes ?? [];
  const results: LabelPlacement[] = [];

  for (const input of [...inputs].sort((a, b) => a.id.localeCompare(b.id))) {
    const candidates = labelCandidates(input.anchorBox, input.fontSize);
    let best: LabelPlacement | undefined;
    for (let index = 0; index < candidates.length; index++) {
      const candidate = candidates[index];
      const box = labelBox(candidate, input.textWidth, { size: input.fontSize });
      const labelOverlap = placed.reduce((total, other) => total + overlapArea(box, other), 0);
      const markerOverlap = markerBoxes.reduce((total, marker) => total + overlapArea(box, marker), 0);
      const offView = offViewBoxArea(box, options.width, options.height, options.margin);
      const penalty = offView * 10_000 + labelOverlap * 1_000 + markerOverlap * 100 + index / 1_000;
      const placement = { id: input.id, candidate, candidateIndex: index, box, penalty };
      if (!best || placement.penalty < best.penalty) best = placement;
    }
    if (!best) continue;
    results.push(best);
    placed.push(best.box);
  }
  return results;
}

// A label eligible for suppression (LabelRequest.priority set) is dropped
// once its own box is covered this much by already-placed labels — a third
// or more of the name simply isn't there to read. Below this it keeps its
// placement, exactly like every label that never opted into suppression at
// all.
const SUPPRESS_OVERLAP_FRACTION = 0.4;

interface LabelRequest {
  id: string;
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
  /** Overlays onto `LABEL_STYLES[role]` — currently only settlement rank (see SETTLEMENT_RANK_STYLE). Absent for every existing caller: zero behaviour change unless set. */
  styleOverride?: Partial<LabelStyle>;
  /**
   * Opt-in suppression eligibility (item 7, 2026-08-10): a LOWER number is
   * higher priority. Absent (every existing caller — schematic-plate places,
   * every layer name) means what it always meant: this name is NEVER
   * dropped, however crowded the sheet — the file's own long-standing
   * anti-omission stance ("Silently deleting a place name... is exactly the
   * class of quiet omission CLAUDE.md's honesty rule exists to prevent").
   * Setting it makes a label ELIGIBLE to be dropped, and only when its own
   * best candidate is still badly overlapped (see SUPPRESS_OVERLAP_FRACTION)
   * — never merely for being present on a crowded sheet. A suppressed label
   * is reported, not silently vanished: see `suppressed` in layoutLabels's
   * return and `PlateResult.suppressedLabels`.
   */
  priority?: number;
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
export function orientPathForReading(pts: [number, number][]): [number, number][] {
  const dx = pts[pts.length - 1][0] - pts[0][0];
  return dx < 0 ? [...pts].reverse() : pts;
}

// A stored river is an OSM polyline sampled every ~10-20m, which on a river
// with a genuine tight meander can put a dozen vertices inside a single
// glyph's width. Fine for the drawn LINE — a viewer's eye integrates
// continuous curvature over a whole stroke — but ruinous for a name riding
// it: `method="align"` rotates every glyph to the path's LOCAL tangent, and
// that many almost-coincident vertices each contributing their own direction
// makes the letters flutter and overlap (2026-08-10, LOOK gate: "Scamander"
// scattered into "am / d / e / r" down the Trojan-plain sheet's river). Corner
// rounding (smoothPathD) does not fix this — it rounds the SAME noisy corners,
// it does not remove them. This drops any vertex closer than `minDist` to the
// last one KEPT, which is the textPath guide's own business, never the
// visible line's: the guide only has to carry a smoothly turning tangent
// under a dozen or so letters, not survey the river.
const TEXTPATH_GUIDE_MIN_SEGMENT = 10;

function thinForTextPathGuide(points: [number, number][], minDist = TEXTPATH_GUIDE_MIN_SEGMENT): [number, number][] {
  if (points.length <= 2) return points;
  const out: [number, number][] = [points[0]];
  for (let i = 1; i < points.length - 1; i++) {
    const last = out[out.length - 1];
    if (Math.hypot(points[i][0] - last[0], points[i][1] - last[1]) >= minDist) out.push(points[i]);
  }
  out.push(points[points.length - 1]);
  return out;
}

function cumulativeLengths(points: [number, number][]): number[] {
  const cum = [0];
  for (let i = 0; i + 1 < points.length; i++) {
    cum.push(cum[i] + Math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1]));
  }
  return cum;
}

function pointAtLength(points: [number, number][], cum: number[], len: number): [number, number] {
  const total = cum[cum.length - 1];
  const target = Math.max(0, Math.min(total, len));
  for (let i = 0; i + 1 < points.length; i++) {
    if (target <= cum[i + 1] || i === points.length - 2) {
      const segLen = cum[i + 1] - cum[i];
      const t = segLen > 0 ? (target - cum[i]) / segLen : 0;
      return [points[i][0] + (points[i + 1][0] - points[i][0]) * t, points[i][1] + (points[i + 1][1] - points[i][1]) * t];
    }
  }
  return points[points.length - 1];
}

// Where along a path a name reads most cleanly. Thinning the guide (above)
// fixes vertex-level noise; it does nothing for genuine curvature at the
// scale of the text itself — a river that bends through its own middle turns
// "Scamander" set dead-centre into a scattered, overlapping S (2026-08-10,
// LOOK gate). `method="align"` rotates every glyph to the LOCAL tangent, so
// what actually matters is not the path's overall length (the existing
// length check above) but how STRAIGHT the specific stretch under the text
// is. Candidates are tried centre-out, closest to 50% first, so a genuinely
// straight river keeps its name dead centre and only a bend gets nudged off
// it — never further than it has to be. `straightness` is chord/arc over the
// window the text would occupy; 1.0 is a straight line, lower means more bend.
const PATH_LABEL_OFFSET_CANDIDATES = [0.5, 0.42, 0.58, 0.34, 0.66, 0.26, 0.74];
const PATH_LABEL_STRAIGHT_ENOUGH = 0.97;

function bestPathLabelOffset(points: [number, number][], textWidth: number): { frac: number; point: [number, number] } {
  const cum = cumulativeLengths(points);
  const total = cum[cum.length - 1];
  const half = textWidth / 2;
  let bestFrac = 0.5;
  let bestPoint = pointAtLength(points, cum, total * 0.5);
  let bestStraightness = -1;
  for (const frac of PATH_LABEL_OFFSET_CANDIDATES) {
    const centreLen = total * frac;
    const lo = Math.max(0, centreLen - half);
    const hi = Math.min(total, centreLen + half);
    const arc = hi - lo;
    const p0 = pointAtLength(points, cum, lo);
    const p1 = pointAtLength(points, cum, hi);
    const chord = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]);
    const straightness = arc > 0 ? chord / arc : 0;
    if (straightness > bestStraightness) {
      bestFrac = frac;
      bestPoint = pointAtLength(points, cum, centreLen);
      bestStraightness = straightness;
    }
    if (straightness >= PATH_LABEL_STRAIGHT_ENOUGH) break;
  }
  return { frac: bestFrac, point: bestPoint };
}

// Knockout width for a label's halo — was 2.5px, an opaque stroke thick
// enough to read as its own shape rather than as a gap cut around the
// letterforms (2026-08-10, landmark-label lane, "kill the white halo").
// 0.65px keeps just enough of a knockout to hold a label legible where it
// crosses a coastline or a contour, tinted to --scene-map-label-halo (the
// map's own background token, not a literal colour) exactly as before.
const LABEL_HALO_WIDTH = 0.65;

function textPathElement(
  text: string,
  pathId: string,
  style: LabelStyle,
  role: LabelRole,
  id: string,
  offsetPct: number,
): string {
  const tracking = style.tracking ? ` letter-spacing="${round1(style.size * style.tracking)}"` : '';
  // `data-label-for` names the place/layer id this text belongs to (2026-
  // 07-30, plate UX): a viewer component uses it to (a) counter-scale the
  // label against its own anchor under camera zoom rather than the text's
  // rendered bbox, and (b) hide a place's label together with its pin when
  // the certainty filter hides that pin. Not a trusted selector fragment —
  // consumers must match it via dataset comparison (see the id-injection
  // finding on data-layer-id), never interpolate it into a CSS selector.
  return (
    `<text class="plate-label plate-label-${role} plate-label-along" data-label-for="${escapeXml(id)}" ` +
    `font-family="var(--font-ui)" font-size="${style.size}" font-weight="${style.weight}"` +
    `${style.italic ? ' font-style="italic"' : ''}${tracking} fill="${style.fill}" ` +
    `paint-order="stroke" stroke="var(--scene-map-label-halo)" stroke-width="${LABEL_HALO_WIDTH}" ` +
    `stroke-linejoin="round" dy="-3.5" style="font-variant-ligatures:none">` +
    // startOffset is normally the run's own straightest window (see
    // bestPathLabelOffset), NOT always dead centre — see that function's
    // comment for why 50% can print a name through a bend.
    `<textPath href="#${pathId}" startOffset="${round1(offsetPct)}%" text-anchor="middle" method="align" spacing="exact">` +
    `${escapeXml(labelText(text, style))}</textPath></text>`
  );
}

function labelElement(
  text: string,
  c: LabelPoint,
  style: LabelStyle,
  role: LabelRole,
  forceItalic: boolean,
  id: string,
): string {
  const italic = style.italic || forceItalic;
  const tracking = style.tracking ? ` letter-spacing="${round1(style.size * style.tracking)}"` : '';
  return (
    `<text class="plate-label plate-label-${role}" data-label-for="${escapeXml(id)}" x="${round1(c.x)}" y="${round1(c.y)}" ` +
    `text-anchor="${c.anchor}" font-family="var(--font-ui)" font-size="${style.size}" ` +
    `font-weight="${style.weight}"${italic ? ' font-style="italic"' : ''}${tracking} ` +
    `fill="${style.fill}" paint-order="stroke" stroke="var(--scene-map-label-halo)" ` +
    `stroke-width="${LABEL_HALO_WIDTH}" stroke-linejoin="round">${escapeXml(labelText(text, style))}</text>`
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
// A name whose candidates all cross the neatline is NOT dropped: it keeps the
// least-cost direction, then clamps it inside the frame. Silently deleting a
// place name off an apparatus map would be exactly the class of quiet omission
// CLAUDE.md's honesty rule exists to prevent — an overlap is visible and fixable,
// an absence is neither.
function layoutLabels(
  requests: LabelRequest[],
  width: number,
  height: number,
  margin: number,
  markerBoxes: LabelBox[],
  // Geographic plates only (2026-08-10, LOOK-gate catch): a river's textPath
  // GUIDE — the invisible <path> a name rides along — used to be drawn from
  // the RAW stored polyline (`pathD`), while the river's own visible line
  // draws from the smoothed one (smoothPathD, see renderLayer's `lineD`).
  // A geographic river is an OSM polyline sampled every ~100m, noisy enough
  // at that resolution that the raw guide zigzags under a name set along it
  // — every glyph rotates to the local raw tangent (`method="align"`), and
  // the name reads as scattered, rotated fragments instead of a smooth
  // italic running along the visible curve beside it. Only surfaced once a
  // river actually GOT a textPath label rather than being pinned as a
  // settlement (see the settlement-role fix in renderPlate) — nothing on a
  // schematic plate is affected; its guide stays the raw polyline exactly as
  // before, matching every other schematic drawing convention in this file.
  smoothSize?: [number, number],
): { markup: string; defs: string; placedBoxes: Box[]; suppressed: string[] } {
  const placed: Box[] = [];
  const parts: string[] = [];
  const defs: string[] = [];
  const suppressed: string[] = [];
  const byId = (a: LabelRequest, b: LabelRequest) => a.id.localeCompare(b.id);
  // Priority (see LabelRequest.priority) orders the non-centred group too, so
  // a high-priority name claims a clean candidate before a low-priority one
  // is even tried — the low-priority request is then the one left holding a
  // bad placement, which is exactly what makes it eligible for suppression
  // below. Every existing caller leaves `priority` unset on every request,
  // so `priorityRank` ties uniformly and this sort is byId, same as before.
  const priorityRank = (r: LabelRequest) => r.priority ?? -Infinity;
  const ordered = [
    ...requests.filter((r) => r.centred).sort(byId),
    ...requests.filter((r) => !r.centred).sort((a, b) => priorityRank(a) - priorityRank(b) || byId(a, b)),
  ];
  // One name, one place on the sheet. A layer and a pin can resolve to the
  // same gazetteer place (the shore layer named `bay-of-troy` and a pin for
  // the bay), and lettering it twice reads as two features.
  const lettered = new Set<string>();

  for (const req of ordered) {
    if (!req.text.trim()) continue;
    const dedupeKey = req.text.trim().toLocaleLowerCase();
    if (lettered.has(dedupeKey)) continue;
    lettered.add(dedupeKey);
    const style = req.styleOverride ? { ...LABEL_STYLES[req.role], ...req.styleOverride } : LABEL_STYLES[req.role];
    const textWidth = estimateLabelWidth(labelText(req.text, style), style);

    // A linear feature is named along its own run whenever the run is long
    // enough to carry the name; otherwise it falls through to point placement
    // below rather than being squeezed onto a stub.
    if (req.path && req.pathId && req.path.length >= 2 && polylineLength(req.path) > textWidth * 1.15) {
      const oriented = orientPathForReading(req.path);
      // Reserve only the stretch the name actually occupies — its own
      // straightest window near the centre (see bestPathLabelOffset), not
      // the whole polyline's bounding box, which for a river crossing the
      // sheet would push every other name out of half the map.
      const { frac, point: mid } = bestPathLabelOffset(oriented, textWidth);
      const box: Box = [mid[0] - textWidth / 2, mid[1] - style.size, mid[0] + textWidth / 2, mid[1] + style.size * 0.3];
      if (!placed.some((p) => boxesOverlap(p, box))) {
        // Thinned for the guide only (see thinForTextPathGuide) — `oriented`
        // itself, used above for the reserved box and for reading direction,
        // is untouched.
        const guidePts = smoothSize ? thinForTextPathGuide(oriented) : oriented;
        const guideD = smoothSize ? smoothPathD(guidePts, false, smoothSize) : pathD(guidePts, false);
        defs.push(`<path id="${req.pathId}" d="${guideD}" fill="none" stroke="none"/>`);
        parts.push(textPathElement(req.text, req.pathId, style, req.role, req.id, frac * 100));
        placed.push(box);
        continue;
      }
      // Too crowded along the line — fall through to point placement.
    }

    let chosen: LabelPoint;
    let box: Box;
    let detached = false;
    if (req.centred) {
      const cx = (req.anchorBox[0] + req.anchorBox[2]) / 2;
      const cy = (req.anchorBox[1] + req.anchorBox[3]) / 2;
      chosen = { x: cx, y: cy + style.size * 0.3, anchor: 'middle' };
      box = labelBox(chosen, textWidth, style);
    } else {
      const candidates = labelCandidates(req.anchorBox, style.size);
      const best = placeLabelCandidates(
        [{ id: req.id, anchorBox: req.anchorBox, textWidth, fontSize: style.size }],
        { width, height, margin, markerBoxes, placedBoxes: placed },
      )[0];
      // A name that had to travel to the outer candidate ring gets a hairline
      // leader back to its own mark.
      detached = !best || best.candidateIndex >= NEAR_CANDIDATE_COUNT;
      if (best) {
        chosen = best.candidate;
        box = best.box;
        // If every candidate crosses the neatline, retain the least-bad
        // direction but bring its box back into view. A map must not lose a
        // place name merely because a pin lies near its edge.
        if (offViewBoxArea(box, width, height, margin) > 0) {
          const dx = Math.min(0, width - margin - box[2]) + Math.max(0, margin - box[0]);
          const dy = Math.min(0, height - margin - box[3]) + Math.max(0, margin - box[1]);
          chosen = { ...chosen, x: chosen.x + dx, y: chosen.y + dy };
          box = labelBox(chosen, textWidth, style);
        }
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

    // Suppression (item 7): only for a request that opted in via `priority`
    // (every existing caller leaves it unset — unconditionally kept, as
    // before), and only when the placement THIS FUNCTION ACTUALLY FOUND is
    // still badly overlapped — never merely for sharing a busy sheet with
    // other names. `id` goes to `suppressed` so the caller can report it;
    // nothing about it is silent.
    if (!req.centred && req.priority !== undefined) {
      const boxArea = Math.max(1e-6, (box[2] - box[0]) * (box[3] - box[1]));
      const overlapFrac = placed.reduce((sum, p) => sum + overlapArea(box, p), 0) / boxArea;
      if (overlapFrac > SUPPRESS_OVERLAP_FRACTION) {
        suppressed.push(req.id);
        continue;
      }
    }

    if (!req.centred && (req.conjectural || detached)) {
      parts.push(leaderElement(req.anchorBox, box, !!req.conjectural));
    }
    parts.push(labelElement(req.text, chosen, style, req.role, !!req.conjectural, req.id));
    placed.push(box);
  }
  return { markup: parts.join(''), defs: defs.join(''), placedBoxes: placed, suppressed };
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
  masonry: 'Masonry, surveyed',
  none: '',
};

// One key row per drawn register. `undefined` means the layer needs no row
// (its meaning is carried by its own name on the sheet). A layer's own
// `legend` string, when it has one, replaces the derived words and re-keys the
// row on them, so two layers in the SAME register but making different claims
// (the citadel's restored circuit and its restored terrace lines) each get a
// row instead of the first one silently swallowing the second in
// legendMarkup's first-wins dedupe.
function layerLegendEntry(layer: PlateLayer): LegendEntry | undefined {
  const entry = derivedLegendEntry(layer);
  if (!entry || !layer.legend) return entry;
  return { ...entry, key: `${entry.key}:${layer.legend}`, text: layer.legend };
}

function derivedLegendEntry(layer: PlateLayer): LegendEntry | undefined {
  // The poem's register keys once, whatever kind of thing carries it — a house,
  // a temple, a street. Wording mirrors the conjectural-pin row the schematic
  // sheets already use, because it is the same claim about the same kind of
  // knowledge; the swatch is a scrap of the drawing, an open dashed outline.
  if (layer.style === 'poem') {
    return {
      key: 'poem',
      rank: 9,
      text: 'Set by the poem, not by survey',
      swatch: (x, y) =>
        `<rect x="${round1(x + 2)}" y="${round1(y - 4)}" width="${LEGEND_SWATCH_W - 4}" height="8" ` +
        `fill="none" stroke="var(--text-mid)" stroke-width="${POEM_STROKE_WIDTH}" ` +
        `stroke-dasharray="${POEM_DASHARRAY}"/>`,
    };
  }
  switch (layer.kind) {
    case 'coast': {
      // The soft-band register is this project's honest treatment of a
      // RECONSTRUCTED shoreline (see trojan-plain.json's own note); a plain
      // stroked coast is a surveyed one. Two different claims, two rows.
      // The swatch fakes the blur with three stacked strokes rather than
      // referencing the filter: at legend size the steps are invisible, and
      // it keeps the key independent of the sheet's element ids.
      // A barrier bar is not a shoreline at all — it is ground, and it keys
      // as ground: the swatch is a body of the lowest hypsometric step, the
      // same tint the sheet draws it in.
      if (layer.style === 'barrier') {
        return {
          key: 'coast-barrier',
          rank: 1.5,
          text: 'Sandy barrier, reconstructed — width not surveyed',
          swatch: (x, y) => legendSwatchRect(x, y, reliefRampToken(1), 1, 'var(--flaxman-ink)'),
        };
      }
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
      // Restored and surveyed are two claims, so they are two rows. The swatch
      // is the drawing in miniature: two faces with the interior left open and
      // one slant stroke across it, which is the whole of what the register
      // means — this wall, at its width, not dug.
      if (layer.style === 'restored') {
        return {
          key: 'wall-restored',
          rank: 5.5,
          text: 'Wall restored — not surveyed',
          swatch: (x, y) =>
            `<path d="M ${round1(x)} ${round1(y - 3)} h ${LEGEND_SWATCH_W} M ${round1(x)} ${round1(y + 3)} h ${LEGEND_SWATCH_W}" ` +
            `fill="none" stroke="var(--flaxman-ink)" stroke-width="${STROKE_WEIGHT.restoredFace}"/>` +
            `<path d="M ${round1(x + 7)} ${round1(y - 3)} L ${round1(x + 13)} ${round1(y + 3)} ` +
            `M ${round1(x + 15)} ${round1(y - 3)} L ${round1(x + 21)} ${round1(y + 3)}" ` +
            `fill="none" stroke="var(--flaxman-ink)" stroke-width="${STROKE_WEIGHT.restoredHatch}" stroke-opacity="0.6"/>`,
        };
      }
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

// The dot-symbology counterpart, geographic plates only — same row text and
// dedupe key as certaintyLegendEntry (the two are never emitted for the same
// render, so there is no collision), swatched with the dot the sheet itself
// draws rather than the teardrop pin.
const LEGEND_DOT_R = 4;

function legendDot(x: number, y: number, style: DotStyle): string {
  return dotSymbol(x + LEGEND_SWATCH_W / 2, y, style, LEGEND_DOT_R);
}

function certaintyDotLegendEntry(certainty: Certainty): LegendEntry {
  const style = certaintyDotStyle(certainty);
  return {
    key: `certainty-${certainty}`,
    rank: 40 + ['certain', 'traditional', 'speculative', 'mythical'].indexOf(certainty),
    text: CERTAINTY_LEGEND_TEXT[certainty],
    swatch: (x, y) => legendDot(x, y, style),
  };
}

// The four corners a legend panel could sit in, nearest-to-farthest from the
// sheet's own bottom-right reading convention — a tie (nothing to avoid
// anywhere) keeps the original bottom-right placement.
const LEGEND_CORNERS = ['br', 'bl', 'tr', 'tl'] as const;
type LegendCorner = (typeof LEGEND_CORNERS)[number];

function legendCornerBox(corner: LegendCorner, panelW: number, panelH: number, width: number, height: number): Box {
  const margin = LABEL_MARGIN + 4;
  const left = corner === 'bl' || corner === 'tl' ? margin : width - margin - panelW;
  const top = corner === 'tl' || corner === 'tr' ? margin : height - margin - panelH;
  return [left, top, left + panelW, top + panelH];
}

// Renders the key into whichever corner of the sheet, inside the neatline,
// overlaps the FEWEST already-placed labels and pins — the same penalty
// spirit as placeLabelCandidates (2026-07-30, legend occlusion finding: on
// trojan-plain-schematic the hardcoded bottom-right corner sat directly on
// top of four Achilles'-end labels, because that sector is itself drawn in
// the sheet's bottom-right). `avoidBoxes` is the caller's placed label boxes
// plus pin marker boxes; an empty list (nothing on the sheet yet to avoid,
// or a caller that hasn't wired this up) keeps the original bottom-right
// corner exactly as before. On its own halo-coloured panel so it stays
// legible over whatever terrain falls under it. Returns '' when there is
// nothing to key.
function legendMarkup(entries: LegendEntry[], width: number, height: number, avoidBoxes: Box[] = []): string {
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

  let bestBox = legendCornerBox('br', panelW, panelH, width, height);
  let bestPenalty = Infinity;
  for (const corner of LEGEND_CORNERS) {
    const box = legendCornerBox(corner, panelW, panelH, width, height);
    const penalty = avoidBoxes.reduce((total, b) => total + overlapArea(box, b), 0);
    if (penalty < bestPenalty) {
      bestPenalty = penalty;
      bestBox = box;
    }
  }
  const [x0, y0] = bestBox;

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
//
// Exported (2026-07-30, plate UX) so an interactive viewer can keep the bar
// honest under its own camera zoom: pass `{ ...viewport, scale: viewport.
// scale * zoomFactor }` to recompute the same bar for the current zoom
// level, and splice the returned `<g class="plate-scale">` markup in place
// of the one this module emitted at zoom 1. This keeps the renderer itself
// pure — it always draws for zoom 1, unaware any camera exists — while the
// component owns the zoom-dependent re-render.
const NICE_METRES = [5, 10, 20, 25, 50, 100, 200, 500];

function scaleLabel(x: number, y: number, s: string, anchor: LabelAnchor): string {
  return (
    `<text class="plate-scale-label" x="${round1(x)}" y="${round1(y)}" text-anchor="${anchor}" ` +
    `font-family="var(--font-ui)" font-size="${SCALE_FONT}" fill="var(--text-mid)" paint-order="stroke" ` +
    `stroke="var(--scene-map-label-halo)" stroke-width="2" stroke-linejoin="round">${escapeXml(s)}</text>`
  );
}

function scalePanelRect(x0: number, top: number, w: number, h: number): string {
  return (
    `<rect class="plate-scale-panel" x="${round1(x0 - 6)}" y="${round1(top)}" ` +
    `width="${round1(w)}" height="${round1(h)}" rx="2" ` +
    `fill="var(--scene-map-label-halo)" fill-opacity="0.72" stroke="none"/>`
  );
}

// The METRE bar, for a schematic plate that declares a true `pxPerMetre` (see
// Plate.pxPerMetre). One bar, not two: a stade is 185 m and the citadel of Troy
// is barely more than that across, so a stade bar here would run off its own
// panel and tell a reader nothing — the sheet's unit is the excavator's, and
// his own Fig. 470 carries a 0–200 m bar for exactly this reason. Same
// alternating filled/open engraving as the geographic bar, so the two read as
// one family of furniture.
function metreBarMarkup(pxPerMetre: number, width: number, height: number): string {
  if (!Number.isFinite(pxPerMetre) || pxPerMetre <= 0) return '';
  const maxPx = Math.min(width * 0.34, 240);
  const metres = niceLength(NICE_METRES, pxPerMetre, maxPx);
  const barPx = metres * pxPerMetre;
  if (!(barPx > 2)) return '';

  const x0 = SCALE_X0;
  const baseY = height - LABEL_MARGIN - 16;
  const barH = SCALE_BAR_H;
  const top = baseY - barH - SCALE_FONT - 9;
  return (
    `<g class="plate-scale">` +
    scalePanelRect(x0, top, barPx + 46, barH + SCALE_FONT + 17) +
    `<path class="plate-scale-bar" d="${barSegments(x0, baseY - barH, barPx, barH, 4)}" ` +
    `fill="var(--flaxman-ink)" stroke="none"/>` +
    `<path class="plate-scale-bar-outline" d="M ${round1(x0)} ${round1(baseY - barH)} h ${round1(barPx)} v ${barH} h ${round1(-barPx)} Z" ` +
    `fill="none" stroke="var(--flaxman-ink)" stroke-width="0.6"/>` +
    scaleLabel(x0, baseY - barH - 3, '0', 'middle') +
    scaleLabel(x0 + barPx + 3, baseY - barH - 3, `${metres} m`, 'start') +
    `</g>`
  );
}

export interface ScaleBarOptions {
  /**
   * Plate pixels per metre. Given, the bar is drawn in METRES off this figure
   * and the viewport is not consulted — the mode a schematic plate drawn to a
   * true scale takes (see Plate.pxPerMetre and metreBarMarkup). Omitted, the
   * bar is the geographic stades-over-kilometres pair computed from `viewport`.
   */
  pxPerMetre?: number;
}

// The geographic scale bar's own on-sheet box, mirroring the panel rect
// `scaleBarMarkup` actually draws (see scalePanelRect there) — so the
// legend's own corner-avoidance (legendMarkup's `avoidBoxes`) can steer clear
// of it too. A gap the 2026-07-30 occlusion fix never closed: the scale bar
// was never in that list, invisible only because the "least-occluded corner"
// score happened to keep landing on bottom-right anyway. Sized for the
// widest the panel can ever draw (`niceLength`'s own `maxPx` cap) rather than
// the actual computed bar width, which is cheap here and never wrong in the
// dangerous direction — it can only push the legend a few px further from a
// corner it did not strictly need to avoid.
function scaleBarBox(width: number, height: number): Box {
  const maxBarPx = Math.min(width * 0.34, 240);
  const x0 = SCALE_X0;
  const top = scalePanelTop(height);
  const w = maxBarPx + 46;
  const h = SCALE_BAR_H * 2 + SCALE_FONT * 2 + 16;
  return [x0 - 6, top, x0 - 6 + w, top + h];
}

export function scaleBarMarkup(
  viewport: Viewport,
  width: number,
  height: number,
  opts: ScaleBarOptions = {},
): string {
  if (opts.pxPerMetre !== undefined) return metreBarMarkup(opts.pxPerMetre, width, height);
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

  const panel = scalePanelRect(x0, scalePanelTop(height), barW + 46, barH * 2 + font * 2 + 16);

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

  const text = scaleLabel;

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

// ── North arrow ──────────────────────────────────────────────────────────
// A needle, half-filled, with N above it and the plate's own caption below —
// the engraved register the rest of the furniture is in, no compass rose and
// no ornament. Drawn only when the plate declares `north`, and the caption IS
// the caveat: a plan surveyed on an 1890s magnetic bearing is not on true
// north, and a bare arrow would quietly claim it was. Sits in the sheet's
// top-left, the corner the legend's own placement pass ranks last.
const NORTH_NEEDLE_H = 34;
const NORTH_HALF_W = 5;
const NORTH_FONT = 8.5;

const NORTH_TOP = LABEL_MARGIN + 16;

/** Half the caption's rendered width, so the arrow can sit far enough inboard for it. */
function northCaptionHalf(caption: string): number {
  return Math.max(NORTH_HALF_W + 4, (caption.length * (NORTH_FONT * 0.55 + 0.6)) / 2);
}

/**
 * The arrow's centre. Pushed inboard by whatever its caption needs, because the
 * caption is centred under the needle and a needle parked at the margin sends
 * half of it off the sheet (2026-07-30, LOOK gate: "...tic north, 1890s").
 */
function northArrowCx(caption: string): number {
  return LABEL_MARGIN + 6 + northCaptionHalf(caption);
}

/** The sheet space the arrow and its caption occupy, for the legend to avoid. */
function northArrowBox(caption: string): Box {
  const cx = northArrowCx(caption);
  const half = northCaptionHalf(caption);
  return [cx - half, NORTH_TOP - NORTH_FONT - 6, cx + half, NORTH_TOP + NORTH_NEEDLE_H + NORTH_FONT + 6];
}

function northArrowMarkup(caption: string): string {
  if (!caption.trim()) return '';
  const cx = northArrowCx(caption);
  const top = NORTH_TOP;
  const base = top + NORTH_NEEDLE_H;
  const p = (x: number, y: number) => `${round1(x)} ${round1(y)}`;
  return (
    `<g class="plate-north">` +
    // The two halves of the needle: the leading one solid, the trailing one
    // open, which is how a plan's arrow is engraved and how it stays legible
    // at 34 px without a fill heavy enough to read as a blot.
    `<path class="plate-north-needle" d="M ${p(cx, top)} L ${p(cx + NORTH_HALF_W, base)} L ${p(cx, base - 7)} Z" ` +
    `fill="var(--flaxman-ink)" stroke="none"/>` +
    `<path class="plate-north-needle-open" d="M ${p(cx, top)} L ${p(cx - NORTH_HALF_W, base)} L ${p(cx, base - 7)} Z" ` +
    `fill="none" stroke="var(--flaxman-ink)" stroke-width="0.7" stroke-linejoin="round"/>` +
    `<text class="plate-north-label" x="${round1(cx)}" y="${round1(top - 4)}" text-anchor="middle" ` +
    `font-family="var(--font-ui)" font-size="${NORTH_FONT + 1.5}" letter-spacing="1" ` +
    `fill="var(--text)" paint-order="stroke" stroke="var(--scene-map-label-halo)" stroke-width="2" ` +
    `stroke-linejoin="round">N</text>` +
    `<text class="plate-north-caption" x="${round1(cx)}" y="${round1(base + NORTH_FONT + 3)}" text-anchor="middle" ` +
    `font-family="var(--font-ui)" font-size="${NORTH_FONT}" letter-spacing="0.6" ` +
    `fill="var(--text-mid)" paint-order="stroke" stroke="var(--scene-map-label-halo)" stroke-width="2" ` +
    `stroke-linejoin="round">${escapeXml(caption)}</text>` +
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
// A third strength for the sandy barrier (2026-07-29). It is a BODY of ground
// rather than a line, so what is soft is its WIDTH: the 5 m contour locates
// its axis, nothing surveys how wide the bar was, and 6 px of blur says that
// without a legend. See the `barrier` case in renderLayer.
const SOFT_BLUR = { coast: 4, marsh: 8, barrier: 6 } as const;
type SoftKind = keyof typeof SOFT_BLUR;
const APPROX_BAND_WIDTH = 9;
const APPROX_BAND_OPACITY = 0.4;
const APPROX_CORE_WIDTH = 0.9;
// The drawn width of a barrier bar. Not a measurement — see BARRIER above and
// the layer's own note; the blur is what says so.
const BARRIER_BAND_WIDTH = 11;

const STROKE_WEIGHT = {
  coast: 2,
  river: 1.4,
  wall: 1.15,
  route: 1,
  tick: 0.75,
  tumulus: 1,
  /** The two faces of a restored wall band (see wallBandGlyph). */
  restoredFace: 0.9,
  /** The slant strokes inside it: lighter than the faces, so the band reads open. */
  restoredHatch: 0.55,
} as const;

/** The drawn face of a surveyed masonry band. See the `region` case in renderLayer. */
const MASONRY_EDGE_WIDTH = 1;
/** The dotted register a restored line takes when it has no width to be drawn at. */
const RESTORED_LINE_WIDTH = 0.85;
const RESTORED_LINE_DASH = '1 3.2';
/**
 * The poem's own register (`style: "poem"`): a longer, plainly OPEN dash, so it
 * cannot be mistaken for either evidential register beside it — Dörpfeld's
 * restoration is a tight dot in the sheet's ink, this is a stroke in the mid-ink
 * every conjectural position on a plate already uses.
 */
const POEM_STROKE_WIDTH = 0.95;
const POEM_DASHARRAY = '4 3';

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

// A river layer's role on a GEOGRAPHIC plate only (2026-08-10, landmark-label
// lane): `river`, not `water` — set along the channel in mixed case, not
// letterspaced caps over an area (see the `river` LABEL_STYLES entry). Every
// other layer kind, and a river layer on a SCHEMATIC plate, keeps exactly
// LAYER_LABEL_ROLE's existing mapping — the citadel plate, the shield and the
// Trojan-plain schematic sheet author no `river` layers as of this writing,
// but the gate is on plate kind, not on absence, so a future one stays safe.
function layerLabelRole(kind: LayerKind, plateKind: PlateKind): LabelRole {
  if (plateKind === 'geographic' && kind === 'river') return 'river';
  return LAYER_LABEL_ROLE[kind];
}

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
  /** The rings whose crossing changes `contains` — see runsWhere. */
  edges: [number, number][][];
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
    else bodies.push({ layerId: layer.id, contains: (p) => insideRings(rings, p), edges: rings });
  }
  if ((plate.ground ?? 'land') === 'sea') {
    bodies.push({
      layerId: null,
      contains: (p) => !landBodies.some((rings) => insideRings(rings, p)),
      edges: landBodies.flat(),
    });
  }
  return bodies;
}

// ── The paint stack (2026-07-29) ─────────────────────────────────────────
// The order layers are PAINTED in, which is deliberately not the order they
// are authored in.
//
// The defect: two independent derivations of "where the land ends" are on
// these sheets — the hypsometric bands are contour polygons cut from the SRTM
// terrain grid (`scripts/prep-terrain-contours.py`), the shorelines are traced
// from the Copernicus GLO-30 water-body mask (`scripts/prep-troad-basemap.py`)
// — and they were generalised with different tolerances. They cannot be made
// to agree to the metre, and on the Trojan-plain sheet the lowest band
// overshot the drawn coast by a pixel or two, leaving a pale cream fringe
// sitting on the water outboard of the coast stroke. `sea-modern` was
// authored FIRST, under everything, so every relief band painted on top of it.
//
// The fix is paint order, not a re-cut of geometry: a land band cannot render
// over sea if the water is painted after the relief, whatever the two
// derivations disagree about, and nothing has to be clipped, buffered or
// re-traced. Same principle as the submerged river reaches above — where two
// honest drawings collide, the one that is water wins, and it wins by being
// painted later.
//
// Four slots, STABLE within each, so authored order still decides everything
// else and a layer that does not move emits byte-identical markup:
//   0  land bodies      a `fill: "land"` body IS the ground the relief sits on
//                       (the Troad sheet's mainland and islands, on a
//                       `ground: "sea"` plate) — it must stay under the bands
//   1  relief           land only, and never over water
//   2  water bodies     open sea and lagoon
//   3  everything else  the marsh (a TRANSLUCENT wash over terrain, with
//                       contours reading through it — never swept into the
//                       water group), coasts, rivers, walls, ship rows,
//                       tumuli, lettering zones
function paintRank(layer: PlateLayer): number {
  const fill =
    layer.fill ?? (layer.kind === 'region' || layer.kind === 'band' ? DEFAULT_REGION_FILL : undefined);
  if (fill === 'land') return 0;
  if (layer.kind === 'relief') return 1;
  if (fill !== undefined && WATER_FILLS.has(fill)) return 2;
  // Restoration goes UNDER survey, always (2026-07-30, citadel plate). It is the
  // oldest rule on an excavation plan and it is a rule about paint order, not
  // about geometry: a restored line runs behind the stone that was actually
  // found, so where the two meet the survey is what a reader sees. It buys three
  // things at once here — the restored circuit slides under the broken wall face
  // at each end instead of floating past it, the terrace lines pass behind the
  // house blocks they cross rather than through them, and Dörpfeld's completed
  // building plans sit behind the fragments of them that survive.
  if (layer.kind === 'wall' && layer.style === 'restored') return 2.5;
  // And the poem goes under the restoration, for the same reason one step
  // further out: it is the least evidenced of the three registers, so where it
  // meets either of the others, the other is what a reader sees.
  if (layer.style === 'poem') return 2.4;
  return 3;
}

// Where segment a→b crosses the edges of `rings`, as parameters in (0, 1),
// ascending. Exact, not searched: the boundary is a polygon, so the crossing
// is the intersection of two line segments and there is nothing to bisect
// toward.
function segmentCrossings(
  a: [number, number],
  b: [number, number],
  rings: [number, number][][],
): number[] {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const ts: number[] = [];
  for (const ring of rings) {
    for (let i = 0; i < ring.length; i++) {
      const c = ring[i];
      const d = ring[(i + 1) % ring.length];
      const ex = d[0] - c[0];
      const ey = d[1] - c[1];
      const den = dx * ey - dy * ex;
      if (den === 0) continue; // parallel, including both degenerate cases
      const t = ((c[0] - a[0]) * ey - (c[1] - a[1]) * ex) / den;
      const u = ((c[0] - a[0]) * dy - (c[1] - a[1]) * dx) / den;
      if (t > 0 && t < 1 && u >= 0 && u <= 1) ts.push(t);
    }
  }
  return [...new Set(ts)].sort((p, q) => p - q);
}

// The maximal runs of `px` over which `inside` holds, cut at the exact
// crossings so that the runs on the two sides of a shoreline share a point:
// the line is split, never gapped.
//
// `boundaries` are the rings that can change `inside`'s answer, and passing
// them is not an optimisation — it is the whole correctness of this function
// (2026-07-29). Sampling `inside` at the polyline's own VERTICES misses any
// reach shorter than the gap between two of them: where two water bodies are
// separated by less ground than one segment of a river, both of that
// segment's ends are wet, no run opens on the dry reach between them, and
// that stretch of river is drawn by nobody. Measured on the plain sheet
// before this fix: 141 m of the Karamenderes, crossing the sandy bar between
// the Bronze Age lagoon and the modern sea inside a single 255 m segment.
// So each segment is split at every crossing first, and each piece is then
// decided by its MIDPOINT — a point that cannot sit on a boundary, where a
// containment test is ill-defined.
function runsWhere(
  px: [number, number][],
  inside: (p: [number, number]) => boolean,
  boundaries: [number, number][][] = [],
): [number, number][][] {
  const nodes: [number, number][] = [];
  for (let i = 0; i < px.length; i++) {
    nodes.push(px[i]);
    if (i + 1 === px.length) break;
    for (const t of segmentCrossings(px[i], px[i + 1], boundaries)) {
      nodes.push([px[i][0] + (px[i + 1][0] - px[i][0]) * t, px[i][1] + (px[i + 1][1] - px[i][1]) * t]);
    }
  }
  const out: [number, number][][] = [];
  let run: [number, number][] | null = null;
  for (let i = 0; i + 1 < nodes.length; i++) {
    const [a, b] = [nodes[i], nodes[i + 1]];
    if (a[0] === b[0] && a[1] === b[1]) continue; // a crossing that landed on a vertex
    if (inside([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2])) {
      if (!run) {
        run = [a];
        out.push(run);
      }
      run.push(b);
    } else {
      run = null;
    }
  }
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
  const px = projectPoints(plate, pts, viewport);
  // A restored wall is drawn as a BAND, not a line, so its name has to be set
  // clear of the band or the label's halo punches a hole through the masonry it
  // is naming. Offset to the band's outer side — the opposite of the side
  // wallGlyph ticks, which is the field side of a fortification — by half the
  // width plus the label's own baseline offset.
  if (layer.kind === 'wall' && layer.style === 'restored' && layer.width !== undefined) {
    return offsetPolyline(px as PlatePoint[], -traceSide(px as PlatePoint[]) * (layer.width / 2 + 4));
  }
  return px;
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
      } else if (layer.style === 'barrier') {
        // A SANDY BAR — a body of ground with water on both sides, not a
        // shoreline. Authored as a `coast` layer because its geometry is a
        // contour line (the 5 m level running east across the bay mouth), and
        // drawn as a line it read as a watercourse in the water: a dark
        // hairline with a glow, running out across the lagoon (2026-07-29,
        // John: "a river where it shouldn't be").
        //
        // So it draws as ground: a wide band filled in the sheet's own LOWEST
        // hypsometric step, which is what the bar is — the lowest land on the
        // plate. Using the ramp's first step rather than a new sand token is
        // the honest choice and the cheap one: it says "this is the lowest
        // ground here" in the same tint the contoured relief already uses for
        // that, and it inherits the ramp's contrast guards (the palest step is
        // already asserted 1.5:1 clear of sea and lagoon in every theme —
        // shared/__tests__/plate-map-contrast.test.ts).
        //
        // No hairline down its middle: that mark IS what made it read as a
        // river. The band's WIDTH is not surveyed — only its axis is — so the
        // edges are blurred rather than drawn, the same argument the marsh's
        // margin is made with. Three registers, three drawings: the modern
        // coast is a solid stroke, the reconstructed shore a soft grey band
        // with an opaque hairline, the barrier a soft pale body.
        markup =
          body +
          `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-barrier" ` +
          `d="${ringsPx.map((px) => lineD(px, false)).join(' ')}" fill="none" ` +
          `stroke="${reliefRampToken(1)}" stroke-width="${BARRIER_BAND_WIDTH}" ` +
          `stroke-linecap="round" stroke-linejoin="round" filter="url(#${softId('barrier')})"/>`;
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
      const shorelines = waters.flatMap((w) => w.edges);
      markup = runsWhere(px, (p) => !waters.some((w) => w.contains(p)), shorelines).map(reach).join('');
      submerged = waters
        .filter((w): w is WaterBody & { layerId: string } => w.layerId !== null)
        .map((w) => ({ layerId: w.layerId, markup: runsWhere(px, (p) => w.contains(p), w.edges).map(reach).join('') }))
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
      if (layer.style === 'restored' && layer.width === undefined) {
        // The restoration register at its lightest: a fine dotted line, which is
        // what a restored feature gets when it HAS no width to be drawn at —
        // Dörpfeld's own terrace fronts and completed house plans are dotted on
        // Fig. 470 for exactly that reason. Drawn as a band they read as three
        // more walls and the sheet becomes a target (2026-07-30, LOOK gate).
        markup =
          `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-wall-restored-line" ` +
          `d="${pathD(px, false)}" fill="none" stroke="var(--flaxman-ink)" ` +
          `stroke-width="${RESTORED_LINE_WIDTH}" stroke-dasharray="${RESTORED_LINE_DASH}" ` +
          `stroke-opacity="0.75" stroke-linecap="round" stroke-linejoin="round"/>`;
        break;
      }
      if (layer.style === 'restored') {
        const { faces, hatch } = wallBandGlyph(px, layer.width);
        markup =
          `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-wall-restored" ` +
          `d="${faces}" fill="none" stroke="var(--flaxman-ink)" stroke-width="${STROKE_WEIGHT.restoredFace}" ` +
          `stroke-linejoin="round" stroke-linecap="round"/>` +
          (hatch
            ? `<path data-feature-id="${escapeXml(layer.id)}-hatch" class="plate-layer plate-layer-wall-restored-hatch" ` +
              `d="${hatch}" fill="none" stroke="var(--flaxman-ink)" stroke-width="${STROKE_WEIGHT.restoredHatch}" ` +
              `stroke-opacity="0.6" stroke-linecap="round"/>`
            : '');
        break;
      }
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
      // A street the poem walks and nobody has dug: same register as a poem
      // building above, so the way and the houses it runs between read as one
      // claim rather than as a road drawn to a house.
      if (layer.style === 'poem') {
        markup =
          `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-poem" ` +
          `d="${pathD(px, false)}" fill="none" stroke="var(--text-mid)" ` +
          `stroke-width="${POEM_STROKE_WIDTH}" stroke-dasharray="${POEM_DASHARRAY}" stroke-linecap="round"/>`;
        break;
      }
      markup = `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-route" d="${pathD(px, false)}" fill="none" stroke="var(--accent-light)" stroke-width="${STROKE_WEIGHT.route}" stroke-dasharray="1 4" stroke-linecap="round"/>`;
      break;
    }
    case 'region':
    case 'band': {
      const px = collect(layer.polygon);
      if (px.length < 3) return undefined;
      // ── The POEM's register ────────────────────────────────────────────
      // A third claim on this sheet, and the one that needs the plainest
      // marking: not surveyed masonry, not Dörpfeld's restoration of it, but a
      // building the Iliad says stood here, drawn where the poem's own
      // description puts it. Fine, openly dashed, no fill, in the mid-ink the
      // rest of this project already spends on a conjectural position — so it
      // cannot be read as either of the two evidential registers, and its name
      // is lettered in italic like every other conjectural thing on a plate.
      // `rings` is drawn with the polygon, which is how a court inside a range
      // of chambers gets onto the sheet as one building and one name.
      if (layer.style === 'poem') {
        const parts = [px, ...(layer.rings ?? []).map((r) => collect(r))].filter((p) => p.length >= 3);
        markup =
          `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-poem" ` +
          `d="${parts.map((p) => pathD(p, true)).join(' ')}" fill="none" stroke="var(--text-mid)" ` +
          `stroke-width="${POEM_STROKE_WIDTH}" stroke-dasharray="${POEM_DASHARRAY}" ` +
          `stroke-linejoin="round" stroke-linecap="round"/>`;
        break;
      }
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
      // Masonry is the one fill whose EDGE is a surveyed thing in its own
      // right — the face of a wall, drawn on the excavation plan to the
      // centimetre — so it gets the sheet's ink at a weight a reader can see
      // the offsets in, where a terrain patch only wants enough of a line to
      // hold its shape. Without it the wall bands read as a wash (2026-07-30).
      const strokeToken = WATER_FILLS.has(fill)
        ? 'var(--scene-map-coast)'
        : fill === 'masonry'
          ? 'var(--flaxman-ink)'
          : fillToken;
      const strokeWidth = fill === 'masonry' ? MASONRY_EDGE_WIDTH : 0.8;
      const strokeOpacity =
        fill === 'masonry' ? 0.85 : fill === 'tint' ? 1 : WATER_FILLS.has(fill) ? 0.7 : 0.5;
      markup = soft
        ? `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-${layer.kind}" d="${d}" ` +
          `fill="${fillToken}" fill-opacity="${REGION_FILL_OPACITY[fill]}" stroke="none" filter="url(#${softId('marsh')})"/>`
        : `<path data-feature-id="${escapeXml(layer.id)}" class="plate-layer plate-layer-${layer.kind}" d="${d}" ` +
          `fill="${fillToken}" fill-opacity="${REGION_FILL_OPACITY[fill]}" stroke="${strokeToken}" stroke-width="${strokeWidth}" stroke-opacity="${strokeOpacity}" stroke-linejoin="round"/>`;
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

  // Every case above stamps `data-feature-id` on its own auxiliary elements
  // too (`<id>-body`, `<id>-band`, `<id>-waterline-N`, ...) — a coast's
  // reconstructed-shore halo and a relief's filled body are drawn as
  // distinct features so tests and CSS can target them individually. But a
  // consumer asking "does this element belong to LAYER X" (PlatePanel's
  // layer-visibility toggle) cannot recover that from the feature id alone:
  // several plates' layer ids collide by prefix (`relief-ida` is a prefix of
  // `relief-ida-north-spurs`; `lower-city` is a prefix of `lower-city-ditch`),
  // so a startsWith/prefix match would hide unrelated sibling layers. Rather
  // than have PlatePanel infer the relationship from string shape (and drift
  // from this module's suffix vocabulary the next time a new aux suffix is
  // added), stamp the relationship explicitly: every element this layer
  // emits — auxiliaries included — also gets `data-layer-id`, always the
  // bare, unsuffixed layer id. `data-feature-id` itself is untouched, both in
  // value AND in position — appended at the very END of the tag rather than
  // beside it, so it can't shift the `data-feature-id="…" class="…"`
  // adjacency several existing tests (and pathsFor's own regex) already rely
  // on. Every element carrying `data-feature-id` in this module is a
  // self-closing `<path … />`, so "find the tag, splice before its `/>`" is
  // exact, not a heuristic. Single injection point: `markup`/`submerged`
  // above only ever contain THIS layer's own already-built markup, so the
  // regex can't cross-contaminate another layer's ids.
  const layerIdAttr = ` data-layer-id="${escapeXml(layer.id)}"`;
  const withLayerId = (s: string) =>
    s.replace(/<path\b[^>]*\/>/g, (tag) =>
      tag.includes('data-feature-id="') ? `${tag.slice(0, -2)}${layerIdAttr}/>` : tag,
    );
  markup = withLayerId(markup);
  if (submerged) {
    submerged = submerged.map((s) => ({ ...s, markup: withLayerId(s.markup) }));
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
    // A poem building is lettered as a NAMED PLACE, not as a tract of country:
    // the `region` role is 15.5px letterspaced caps, the register PERGAMOS is
    // set in, and "House of Priam" set that way would be both grander than the
    // claim and wider than the summit.
    labelRole: layer.style === 'poem' ? 'settlement' : layerLabelRole(layer.kind, plate.kind),
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
  const drawn: { layerId: string; markup: string; rank: number }[] = [];
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
    barrier: plate.layers.some((l) => l.kind === 'coast' && l.style === 'barrier'),
  };
  for (const layer of plate.layers) {
    const rendered = renderLayer(plate, layer, viewport, softId, waters);
    if (!rendered) continue;
    drawn.push({ layerId: layer.id, markup: rendered.markup, rank: paintRank(layer) });
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

  // Into the paint stack (see paintRank). Array#sort is stable in every
  // engine this ships to, so layers sharing a rank keep the order the plate
  // file authored them in. A water layer's submerged river reaches travel
  // with it, because they are keyed to its id and joined here, after the
  // sort — so moving the sea later moves the drowned reaches under it too.
  const layerMarkup = [...drawn]
    .sort((a, b) => a.rank - b.rank)
    .map(({ layerId, markup }) => (submergedByWater.get(layerId) ?? []).join('') + markup);

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

    if (plate.kind === 'geographic') {
      // Five Landmark classes, not one flat "settlement" for every located
      // place (the bug docs/research/AUDIT-PLATE-LABELS.md's §2.1 names: a
      // river or bay with a coordinate used to get a teardrop and lose its
      // own along-channel/area name to it). `region`/`water`/`river` never
      // get a marker at all (item 3); when the SAME place is also carried by
      // a rendered layer (a river's own channel, a bay's own polygon), it is
      // fully silent here and the layer's own fallback-name lookup below
      // (keyed off `labeledPointIds`) picks up its gazetteer name instead —
      // one name, one source, never a duplicate. When no layer carries it
      // (Hellespont, Thymbra, Dardania, Lesbos — a coordinate but no drawn
      // geometry of its own on this sheet), it still prints, in its class's
      // own register, just with no dot.
      const cls = placeLabelClass(place);
      if (MARKERLESS_LABEL_CLASSES.has(cls)) {
        if (!layerPlaceIds.has(place.id)) {
          pinLabelRequests.push({
            id: place.id,
            text: mapLabelText(place.name),
            role: cls,
            anchorBox: [x, y, x, y],
          });
        }
        continue;
      }
      // settlement or feature: the two classes that DO carry a small dot
      // (item 3 — solid/open/open-square by certainty tier, 2.5-4px at 1x).
      const dotStyle = certaintyDotStyle(place.certainty);
      const r = cls === 'settlement' ? SETTLEMENT_DOT_R[place.rank ?? 2] : FEATURE_DOT_R;
      pinMarkupParts.push(dotMarkup(place.id, place.name, x, y, dotStyle, r));
      features.push({ id: place.id, type: 'place', kind: place.certainty ?? 'certain', bbox: dotBBox(x, y, r) });
      pinLabelRequests.push({
        id: place.id,
        text: mapLabelText(place.name),
        role: cls,
        anchorBox: dotBBox(x, y, r),
        styleOverride: cls === 'settlement' ? SETTLEMENT_RANK_STYLE[place.rank ?? 2] : undefined,
        // Item 7's label budget: only the two least load-bearing prints on a
        // geographic sheet — a rank-3 settlement (the minor headlands and
        // allied towns) and a feature (a hill, tumulus, cape) — are eligible
        // to drop if their best placement is still badly overlapped. Troy,
        // every rank-1/2 settlement, and every region/water/river name is
        // never eligible (`priority` left unset), matching this file's own
        // long-standing "never silently omit" stance for anything load-
        // bearing enough to matter at a glance.
        priority: cls === 'settlement' ? (place.rank === 3 ? 1 : undefined) : cls === 'feature' ? 1 : undefined,
      });
      legendEntries.push(certaintyDotLegendEntry(place.certainty ?? 'certain'));
      continue;
    }

    // ── Schematic plate: unchanged (teardrop pin, always role 'settlement') ──
    const style = certaintyPinStyle(place.certainty);
    // Any place resolved on a schematic plate got there via plateAnchors +
    // positionBasis: "conjectural" (see resolvePlacePosition) — there is no
    // other path to a position on a schematic plate.
    const conjectural = plate.kind === 'schematic';
    pinMarkupParts.push(pinMarkup(place.id, place.name, x, y, style, conjectural));
    features.push({ id: place.id, type: 'place', kind: place.certainty ?? 'certain', bbox: pinBBox(x, y) });
    pinLabelRequests.push({
      id: place.id,
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
  // has not already been given a point label above, so a feature is never
  // lettered twice. Sourced from the point-label requests actually built,
  // not from `located`: a geographic place in a markerless class that IS
  // carried by a layer never enters `pinLabelRequests` (see the loop above),
  // which is exactly what lets that layer's own fallback name fire instead.
  const labeledPointIds = new Set(pinLabelRequests.map((r) => r.id));
  const layerLabelRequests: LabelRequest[] = [];
  for (const { layer, rendered } of layerLabelCandidates) {
    const gazName = layer.placeId && !labeledPointIds.has(layer.placeId) ? placeById.get(layer.placeId)?.name : undefined;
    const fallback = gazName ? mapLabelText(gazName) : undefined;
    const text = layer.label ?? fallback;
    if (!text) continue;
    layerLabelRequests.push({
      id: layer.id,
      text,
      role: rendered.labelRole,
      anchorBox: rendered.labelAnchor,
      centred: rendered.labelCentred,
      // A name the poem gives to a place the poem alone locates is lettered
      // italic, the same mark every conjectural pin's name already carries.
      conjectural: layer.style === 'poem',
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
    // Furniture the lettering has to keep off: the pin markers, and the north
    // arrow, which is drawn after the labels and would otherwise be lettered over.
    [
      ...pinLabelRequests.map((request) => request.anchorBox),
      ...(plate.north ? [northArrowBox(plate.north)] : []),
    ],
    plate.kind === 'geographic' ? plate.size : undefined,
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
    legendMarkup(legendEntries, width, height, [
      ...pinLabelRequests.map((request) => request.anchorBox),
      ...labels.placedBoxes,
      ...(plate.north ? [northArrowBox(plate.north)] : []),
      // Geographic only (see scaleBarBox): the metre-bar schematic path is
      // untouched, out of this lane's scope.
      ...(plate.kind === 'geographic' ? [scaleBarBox(width, height)] : []),
    ]) +
    `</g>` +
    // Frame, bar scale and north arrow sit OUTSIDE the clip: their strokes run
    // along the sheet edge and would be shaved in half by it. The bar is drawn
    // from this plate's own geometry, so it is honest by construction: from the
    // viewport for a geographic plate, and from a declared `pxPerMetre` for a
    // schematic one that IS a rectified survey (see Plate.pxPerMetre). A
    // schematic plate that declares neither gets no bar, because it has no
    // scale and drawing one would be a fabricated claim.
    (plate.kind === 'geographic'
      ? scaleBarMarkup(viewport, width, height)
      : plate.pxPerMetre !== undefined
        ? scaleBarMarkup(viewport, width, height, { pxPerMetre: plate.pxPerMetre })
        : '') +
    (plate.north ? northArrowMarkup(plate.north) : '') +
    hypsometricKeyMarkup(plate, width, height) +
    neatlineMarkup(width, height) +
    `</svg>`;

  return { svg, viewport, features, unlocated, offCanvas, drawnByLayer, suppressedLabels: labels.suppressed };
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
