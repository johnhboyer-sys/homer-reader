// Pure equirectangular (Plate Carrée) projection and viewport-fitting math.
// Factored out of shared/lib/scenemap.ts (the scene-map SVG renderer) so a
// second consumer — an illustrated-plate renderer — can share the exact same
// projection instead of re-deriving it. No DOM, no file I/O, no
// randomness/clock reads — pure data-in, data-out transforms, same posture
// as shared/lib/maps.ts and shared/lib/genealogy.ts.
//
// Projection: equirectangular (Plate Carrée), recentered per scene at the
// fitted viewport's own midpoint, with longitude scaled by cos(centerLat) so
// East-West distances read proportionally at Mediterranean latitudes (a pin
// at 36N isn't stretched the same as one at 45N). This is the simplest
// projection that keeps local shapes undistorted enough for a small
// "suggestive, not cartographic" panel map at a ~2-6 degree span — no need
// for a true conformal projection at this scale/purpose.

export type LatLon = [number, number]; // [lat, lon] — matches apparatus/places.json `coords`

export interface Viewport {
  width: number;
  height: number;
  centerLat: number;
  centerLon: number;
  latSpan: number; // degrees
  lonSpan: number; // degrees of longitude (pre cos-correction)
  scale: number; // px per (cos-corrected) degree
}

// Fallback camera center used ONLY when fitViewport() is given zero located
// places (defensive edge case — callers should normally always have at least
// the scene's own location). The Aegean/Ionian center is a plain rendering
// default, not a claimed identification of anything.
const FALLBACK_CENTER: LatLon = [37.9, 23.7];

// This repo only ever maps the Aegean/Mediterranean at Landmark-panel scale
// (see the file header) — true polar correctness is out of scope. Below this
// floor, cos(centerLat) is close enough to zero that dividing by it (in
// unproject, and in the scaleX computations below) blows up, and multiplying
// by it (in project) collapses every longitude onto the same pixel. Both
// directions go through this one floor so a viewport's fitted `scale` and
// the coordinates later projected into it always agree — before this fix,
// viewportFromBBox/fitViewport floored their scaleX computation but
// project()/unproject() used the true, unfloored cosine, so the two
// disagreed as centerLat approached 90.
const MIN_COS_LAT = 0.01;

function clampedCosLat(latDeg: number): number {
  return Math.max(Math.cos((latDeg * Math.PI) / 180), MIN_COS_LAT);
}

// Coordinates outside real Earth range are an authoring error, not a valid
// input — clamped (not thrown) to match this module's existing "pure
// data-in, data-out, never throws" posture (unlike plate.ts/shield.ts, which
// validate and throw). A bbox like [89, 0, 91, 1] is both polar and
// out-of-range; clamping the latitude keeps viewportFromBBox from silently
// accepting nonsense while still returning a usable, finite viewport.
function clampLat(lat: number): number {
  return Math.min(90, Math.max(-90, lat));
}

function clampLon(lon: number): number {
  return Math.min(180, Math.max(-180, lon));
}

// ── Projection ───────────────────────────────────────────────────────────

export function project(latlon: LatLon, viewport: Viewport): [number, number] {
  const [lat, lon] = latlon;
  const cosLat = clampedCosLat(viewport.centerLat);
  const x = viewport.width / 2 + (lon - viewport.centerLon) * cosLat * viewport.scale;
  const y = viewport.height / 2 - (lat - viewport.centerLat) * viewport.scale;
  return [x, y];
}

// Inverse of project(); exercised by the round-trip test. Not used by
// rendering itself.
export function unproject(point: [number, number], viewport: Viewport): LatLon {
  const [x, y] = point;
  const cosLat = clampedCosLat(viewport.centerLat);
  const lon = viewport.centerLon + (x - viewport.width / 2) / (cosLat * viewport.scale);
  const lat = viewport.centerLat - (y - viewport.height / 2) / viewport.scale;
  return [lat, lon];
}

// ── Viewport fitting ─────────────────────────────────────────────────────

// Narrower than shared/lib/scenemap.ts's `ScenePlace` — fitViewport only
// ever reads `coords`. Kept local (rather than importing ScenePlace from
// scenemap.ts) so this module has no dependency on scenemap.ts — scenemap.ts
// depends on geo.ts, not the other way around. ScenePlace is a structural
// superset of this, so a ScenePlace[] still passes here without any cast.
export interface Locatable {
  coords?: LatLon;
}

// Narrower than shared/lib/scenemap.ts's `SceneMapOptions` — fitViewport
// only ever reads these four fields (fontSizePx/idPrefix are scene-map
// rendering concerns, not projection/fitting ones). Kept local for the same
// no-dependency-on-scenemap.ts reason as `Locatable` above. SceneMapOptions
// is a structural superset, so it still passes here without a cast. If
// these numeric defaults are ever retuned, scenemap.ts's
// DEFAULT_SCENE_MAP_OPTIONS must be retuned to match by hand — the two are
// independent copies by construction.
export interface FitViewportOptions {
  width?: number;
  height?: number;
  /** Extra span added around the located bbox on each side, as a fraction of the raw span. */
  padFraction?: number;
  /** Floor on the fitted lat/lon span (degrees), so a lone pin doesn't zoom to a meaningless extent. */
  minExtentDeg?: number;
}

const DEFAULT_FIT_VIEWPORT_OPTIONS: Required<FitViewportOptions> = {
  width: 320,
  height: 220,
  padFraction: 0.35,
  minExtentDeg: 3,
};

// Fits a viewport around `places`' located coords (unlocated places are
// ignored here — never force-pinned). Applies `padFraction` padding around
// the raw bbox and enforces `minExtentDeg` as a floor on both spans, so a
// single pin still renders with meaningful surrounding coastline instead of
// zooming to a point.
//
// Generic (`T extends Locatable`) rather than typed as `places: Locatable[]`
// directly: existing callers (e.g. shared/__tests__/scenemap.test.ts, unedited
// by this refactor) pass fresh object literals shaped like scenemap.ts's
// wider `ScenePlace` (with `id`/`name`/`certainty` alongside `coords`).
// TypeScript's excess-property check would reject those literals against the
// narrower `Locatable` if the parameter were typed as `Locatable[]` directly;
// with a generic, T is inferred from the literal itself and merely checked
// against the `Locatable` constraint, so no excess-property error and no
// behavior change.
export function fitViewport<T extends Locatable>(places: T[], options: FitViewportOptions = {}): Viewport {
  const opts = { ...DEFAULT_FIT_VIEWPORT_OPTIONS, ...options };
  const located = places.filter((p): p is T & { coords: LatLon } => !!p.coords);

  let centerLat: number;
  let centerLon: number;
  let rawLatSpan = 0;
  let rawLonSpan = 0;

  if (located.length === 0) {
    [centerLat, centerLon] = FALLBACK_CENTER;
  } else {
    const lats = located.map((p) => p.coords[0]);
    const lons = located.map((p) => p.coords[1]);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);
    centerLat = (minLat + maxLat) / 2;
    centerLon = (minLon + maxLon) / 2;
    rawLatSpan = maxLat - minLat;
    rawLonSpan = maxLon - minLon;
  }

  const latSpan = Math.max(rawLatSpan * (1 + opts.padFraction * 2), opts.minExtentDeg);
  const lonSpan = Math.max(rawLonSpan * (1 + opts.padFraction * 2), opts.minExtentDeg);

  const cosLat = clampedCosLat(centerLat);
  const scaleX = opts.width / (lonSpan * cosLat);
  const scaleY = opts.height / latSpan;
  const scale = Math.min(scaleX, scaleY);

  return { width: opts.width, height: opts.height, centerLat, centerLon, latSpan, lonSpan, scale };
}

// Returns a Viewport for a FIXED extent — no padding, no minimum-span floor
// (unlike fitViewport, which pads and floors for auto-fitted scene panels).
// For the illustrated-plate renderer, which is handed an explicit bounding
// box to fill rather than a set of places to auto-fit a camera around.
//
// Viewport carries one uniform `scale` (px per cos-corrected degree), shared
// between both axes — see project()/unproject() above, and the longitude-
// compression invariant that depends on it. When bbox's aspect ratio doesn't
// match size's aspect ratio, honoring BOTH corners exactly is therefore
// impossible without a non-uniform (per-axis) scale, which Viewport doesn't
// have and shouldn't grow just for this. Rather than silently distort
// (stretching one axis to force both corners to match), this fits the bbox
// entirely inside `size` at one uniform scale and centers it — the same
// letterboxing policy fitViewport already uses via `scale = Math.min(scaleX,
// scaleY)`. Callers that need the box flush to all four edges must pass a
// bbox whose aspect ratio already matches `size`; when it does, both corners
// land exactly (see the geo.test.ts contract test).
// A hand-authored bbox is normally never degenerate (validate_plate and
// parsePlate both reject minLat >= maxLat before this function ever runs),
// but this function is pure math with no validation of its own — a zero (or
// near-zero) span must still produce a finite, usable viewport rather than
// dividing by zero (previously: scale: Infinity, every projected point
// [NaN, NaN]). The floor is a few metres of latitude, small enough that it
// never visibly perturbs any real plate's span — it only rescues the
// degenerate case.
const MIN_BBOX_SPAN_DEG = 1e-6;

export function viewportFromBBox(
  bbox: [number, number, number, number], // [minLat, minLon, maxLat, maxLon]
  size: [number, number], // [widthPx, heightPx]
): Viewport {
  const [minLat, minLon, maxLat, maxLon] = bbox;
  const [width, height] = size;

  // Clamp to real Earth range first (see clampLat/clampLon) — a bbox like
  // [89, 0, 91, 1] is both polar and out-of-range.
  const clampedMinLat = clampLat(minLat);
  const clampedMaxLat = clampLat(maxLat);
  const clampedMinLon = clampLon(minLon);
  const clampedMaxLon = clampLon(maxLon);

  const centerLat = (clampedMinLat + clampedMaxLat) / 2;
  const centerLon = (clampedMinLon + clampedMaxLon) / 2;
  const latSpan = Math.max(clampedMaxLat - clampedMinLat, MIN_BBOX_SPAN_DEG);
  const lonSpan = Math.max(clampedMaxLon - clampedMinLon, MIN_BBOX_SPAN_DEG);

  const cosLat = clampedCosLat(centerLat);
  const scaleX = width / (lonSpan * cosLat);
  const scaleY = height / latSpan;
  const scale = Math.min(scaleX, scaleY);

  return { width, height, centerLat, centerLon, latSpan, lonSpan, scale };
}
