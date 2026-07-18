// Pure library for build-time SVG "scene maps" — small, self-contained,
// stylized maps for the reader's context panel (~300-400px wide, per the
// approved mocks in design-board/context-panel-mocks/). Given a scene's
// place(s) (drawn from apparatus/places.json) and, optionally, a journey leg
// (drawn from apparatus/journeys.json), this module emits an SVG string:
// duotone Mediterranean-basin coastline (vendored from Natural Earth, see
// sources/naturalearth/), the scene's pin(s), an optional gentle route arc,
// and a place label.
//
// No DOM, no file I/O, no randomness/clock reads — pure data-in, string-out
// transforms, same posture as shared/lib/maps.ts and shared/lib/genealogy.ts.
// Callers (a future Svelte/Astro component) load+parse
// sources/naturalearth/mediterranean-coastline.json themselves (through
// whatever this app's data-loading convention is at that call site — see
// shared/lib/data.ts's data-root override, CLAUDE.md's hard rule) and pass
// the parsed Coastline in; this module never reads it off disk.
//
// Colors are ALWAYS emitted as `var(--...)` custom-property references, never
// hex, so the SVG recolors for free across the site's light/dark/Aegean theme
// layer. Tokens referenced here (see shared/styles/global.css for their
// definitions): --page-bg, --border, --text-mid, --text, --accent,
// --accent-light, --font-ui.
//
// Projection: equirectangular (Plate Carrée), recentered per scene at the
// fitted viewport's own midpoint, with longitude scaled by cos(centerLat) so
// East-West distances read proportionally at Mediterranean latitudes (a pin
// at 36N isn't stretched the same as one at 45N). This is the simplest
// projection that keeps local shapes undistorted enough for a small
// "suggestive, not cartographic" panel map at a ~2-6 degree span — no need
// for a true conformal projection at this scale/purpose.
//
// Apparatus honesty (CLAUDE.md hard rule): a place with no `coords` is never
// force-pinned or force-routed. renderSceneMap() silently skips unlocatable
// places into its `unlocated` return list; renderRoute() degrades a leg whose
// `from` (or `to`) has no coords into a short, visually distinct symbolic
// stub rather than drawing a line to a fabricated position.

export type LatLon = [number, number]; // [lat, lon] — matches apparatus/places.json `coords`

export type Certainty = 'certain' | 'traditional' | 'speculative' | 'mythical';

// Mirrors the fields of apparatus/places.json / shared/lib/maps.ts's `Place`
// that this module actually needs. Deliberately NOT imported from maps.ts —
// that file is a concurrent lane (the /maps/ Leaflet explorer); this module
// stays a standalone, independently testable library.
export interface ScenePlace {
  id: string;
  name: string;
  coords?: LatLon;
  certainty?: Certainty;
}

// The vendored, pre-clipped/simplified Mediterranean coastline (see
// sources/naturalearth/mediterranean-coastline.json + its README). `rings`
// are already in this project's [lat, lon] convention.
export interface Coastline {
  bbox: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
  rings: LatLon[][];
}

// One leg of a journey (apparatus/journeys.json shape, trimmed to what this
// module needs: the two endpoints' resolved places). Either endpoint may lack
// coords — see renderRoute()'s degraded treatment.
export interface RouteLeg {
  from: ScenePlace;
  to: ScenePlace;
}

export interface SceneMapOptions {
  width?: number;
  height?: number;
  /** Extra span added around the located bbox on each side, as a fraction of the raw span. */
  padFraction?: number;
  /** Floor on the fitted lat/lon span (degrees), so a lone pin doesn't zoom to a meaningless extent. */
  minExtentDeg?: number;
  fontSizePx?: number;
  /** Prefix for internal element ids (clipPath). Set distinctly per instance when inlining more than one scene map on the same page, so ids don't collide. */
  idPrefix?: string;
}

export const DEFAULT_SCENE_MAP_OPTIONS: Required<SceneMapOptions> = {
  width: 320,
  height: 220,
  padFraction: 0.35,
  minExtentDeg: 3,
  fontSizePx: 11,
  idPrefix: 'scenemap',
};

// Fallback camera center used ONLY when fitViewport() is given zero located
// places (defensive edge case — callers should normally always have at least
// the scene's own location). The Aegean/Ionian center is a plain rendering
// default, not a claimed identification of anything.
const FALLBACK_CENTER: LatLon = [37.9, 23.7];

export interface Viewport {
  width: number;
  height: number;
  centerLat: number;
  centerLon: number;
  latSpan: number; // degrees
  lonSpan: number; // degrees of longitude (pre cos-correction)
  scale: number; // px per (cos-corrected) degree
}

// ── Projection ───────────────────────────────────────────────────────────

export function project(latlon: LatLon, viewport: Viewport): [number, number] {
  const [lat, lon] = latlon;
  const cosLat = Math.cos((viewport.centerLat * Math.PI) / 180);
  const x = viewport.width / 2 + (lon - viewport.centerLon) * cosLat * viewport.scale;
  const y = viewport.height / 2 - (lat - viewport.centerLat) * viewport.scale;
  return [x, y];
}

// Inverse of project(); exercised by the round-trip test. Not used by
// rendering itself.
export function unproject(point: [number, number], viewport: Viewport): LatLon {
  const [x, y] = point;
  const cosLat = Math.cos((viewport.centerLat * Math.PI) / 180);
  const lon = viewport.centerLon + (x - viewport.width / 2) / (cosLat * viewport.scale);
  const lat = viewport.centerLat - (y - viewport.height / 2) / viewport.scale;
  return [lat, lon];
}

// ── Viewport fitting ─────────────────────────────────────────────────────

// Fits a viewport around `places`' located coords (unlocated places are
// ignored here — never force-pinned). Applies `padFraction` padding around
// the raw bbox and enforces `minExtentDeg` as a floor on both spans, so a
// single pin still renders with meaningful surrounding coastline instead of
// zooming to a point.
export function fitViewport(places: ScenePlace[], options: SceneMapOptions = {}): Viewport {
  const opts = { ...DEFAULT_SCENE_MAP_OPTIONS, ...options };
  const located = places.filter((p): p is ScenePlace & { coords: LatLon } => !!p.coords);

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

  const cosLat = Math.cos((centerLat * Math.PI) / 180);
  const scaleX = opts.width / (lonSpan * Math.max(cosLat, 0.01));
  const scaleY = opts.height / latSpan;
  const scale = Math.min(scaleX, scaleY);

  return { width: opts.width, height: opts.height, centerLat, centerLon, latSpan, lonSpan, scale };
}

// ── Coastline ────────────────────────────────────────────────────────────

export interface CoastlinePathResult {
  d: string;
  ringCount: number;
}

// Projects the coastline into a single (possibly multi-subpath) SVG path `d`
// string, keeping only rings whose own bbox overlaps the viewport (plus a
// little slack) — a lone-pin scene draws a handful of nearby rings, not all
// ~70 Mediterranean-basin rings.
export function coastlinePathData(coastline: Coastline, viewport: Viewport): CoastlinePathResult {
  const minLat = viewport.centerLat - viewport.latSpan / 2;
  const maxLat = viewport.centerLat + viewport.latSpan / 2;
  const minLon = viewport.centerLon - viewport.lonSpan / 2;
  const maxLon = viewport.centerLon + viewport.lonSpan / 2;
  const slack = 1.0; // degrees

  const parts: string[] = [];
  let ringCount = 0;
  for (const ring of coastline.rings) {
    let rMinLat = Infinity;
    let rMaxLat = -Infinity;
    let rMinLon = Infinity;
    let rMaxLon = -Infinity;
    for (const [lat, lon] of ring) {
      if (lat < rMinLat) rMinLat = lat;
      if (lat > rMaxLat) rMaxLat = lat;
      if (lon < rMinLon) rMinLon = lon;
      if (lon > rMaxLon) rMaxLon = lon;
    }
    const intersects =
      rMaxLat >= minLat - slack && rMinLat <= maxLat + slack &&
      rMaxLon >= minLon - slack && rMinLon <= maxLon + slack;
    if (!intersects) continue;

    const d = ring
      .map((ll, i) => {
        const [x, y] = project(ll, viewport);
        return `${i === 0 ? 'M' : 'L'}${round1(x)},${round1(y)}`;
      })
      .join(' ') + ' Z';
    parts.push(d);
    ringCount++;
  }
  return { d: parts.join(' '), ringCount };
}

// Validates + narrows an already-JSON.parsed coastline payload. No file I/O —
// callers (a component, or a test reading the vendored JSON) do the reading;
// this just checks the shape is what renderSceneMap()/coastlinePathData()
// expect.
export function parseCoastline(data: unknown): Coastline {
  if (!data || typeof data !== 'object') {
    throw new Error('scenemap: coastline data must be an object');
  }
  const d = data as Record<string, unknown>;
  if (!Array.isArray(d.bbox) || d.bbox.length !== 4) {
    throw new Error('scenemap: coastline data missing a 4-element bbox');
  }
  if (!Array.isArray(d.rings)) {
    throw new Error('scenemap: coastline data missing rings');
  }
  return { bbox: d.bbox as [number, number, number, number], rings: d.rings as LatLon[][] };
}

// ── Pins ─────────────────────────────────────────────────────────────────

interface PinStyle {
  fill: string;
  fillOpacity: number;
  stroke: string;
  dasharray?: string;
}

// Mirrors app/src/components/maps/LandmarkMap.svelte's tier styling
// (.lm-pin.tier-*) so a place reads with the same certainty-tier visual
// language across both map systems: certain = solid fill, traditional = ring
// only, speculative = outline in the muted ink, mythical = dashed outline
// (one step further from "confirmed" than speculative). Certainty absent
// (rare — most callers pass it) falls back to the 'certain' look.
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

// A small "balloon" pin (circular head + triangular tip) whose APEX sits
// exactly at the projected coordinate — a plain <circle> + tip <path>, not a
// single fragile bezier teardrop, kept simple on purpose.
function pinMarkup(x: number, y: number, style: PinStyle, r = 5.5): string {
  const headCy = y - r * 1.7;
  const tip = `M ${round1(x - r * 0.55)} ${round1(y - r * 0.9)} L ${round1(x + r * 0.55)} ${round1(y - r * 0.9)} L ${round1(x)} ${round1(y)} Z`;
  const dash = style.dasharray ? ` stroke-dasharray="${style.dasharray}"` : '';
  return (
    `<circle cx="${round1(x)}" cy="${round1(headCy)}" r="${r}" fill="${style.fill}" fill-opacity="${style.fillOpacity}" stroke="${style.stroke}" stroke-width="1.25"${dash}/>` +
    `<path d="${tip}" fill="${style.fill}" fill-opacity="${style.fillOpacity}" stroke="${style.stroke}" stroke-width="1.25"${dash}/>`
  );
}

// ── Labels ───────────────────────────────────────────────────────────────

export interface PlacedLabel {
  x: number;
  y: number;
  anchor: 'start' | 'end';
  text: string;
}

// Average glyph-width heuristic for the site's UI font stack — no DOM measurement
// available in a pure/build-time module, so this is deliberately approximate;
// it only needs to keep the label inside the viewBox, not kern perfectly.
function estimateTextWidth(text: string, fontSizePx: number): number {
  return text.length * fontSizePx * 0.56;
}

// Places a pin's label so it never leaves the viewBox: anchors toward
// whichever side of the pin has more room, then clamps against the estimated
// text extent. Flips above/below the pin similarly near the top edge. Label
// collision with the coastline itself is out of scope for v1 (per brief).
export function placeLabel(
  place: ScenePlace,
  pinX: number,
  pinY: number,
  viewport: Viewport,
  fontSizePx: number = DEFAULT_SCENE_MAP_OPTIONS.fontSizePx,
): PlacedLabel {
  const margin = 6;
  const clearance = 10;
  const estWidth = estimateTextWidth(place.name, fontSizePx);

  let anchor: 'start' | 'end' = pinX < viewport.width * 0.62 ? 'start' : 'end';
  let x = anchor === 'start' ? pinX + clearance : pinX - clearance;

  if (anchor === 'start' && x + estWidth > viewport.width - margin) {
    x = Math.max(margin, viewport.width - margin - estWidth);
  }
  if (anchor === 'end' && x - estWidth < margin) {
    // No room on the left either (narrow viewport, wide name) — fall back to
    // starting flush against the left margin rather than running off-canvas.
    anchor = 'start';
    x = margin;
  }

  const preferAbove = pinY > viewport.height * 0.28;
  let y = preferAbove ? pinY - clearance * 1.4 : pinY + clearance * 1.4 + fontSizePx * 0.5;
  y = Math.min(Math.max(y, fontSizePx + margin), viewport.height - margin);

  return { x, y, anchor, text: place.name };
}

// ── Route arc ────────────────────────────────────────────────────────────

// shared/lib/maps.ts (the concurrent /maps/ Leaflet lane) has no
// arc-interpolation helper as of this writing (checked via `git log --
// shared/lib/maps.ts`: last commits are "Add wanderings Story mode" and the
// original four-maps feature — neither adds a quadratic/bezier route-arc
// helper; routes there are Leaflet polylines drawn from raw lat/lon, not
// projected SVG arcs). This module therefore implements its own small,
// local, DETERMINISTIC quadratic-arc helper below. If/when a shared
// arc-interpolation helper lands in maps.ts (or a future shared/lib/geo.ts),
// this should be deduplicated into one implementation — noted, not actioned
// here; out of this lane's scope.
function quadraticArcPath([x1, y1]: [number, number], [x2, y2]: [number, number], bend = 0.18): string {
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const dx = x2 - x1;
  const dy = y2 - y1;
  // Perpendicular offset from the midpoint, a fixed fraction of the segment
  // length, always to the same side of the from->to vector — deterministic
  // and stable across re-renders of the same leg.
  const cx = mx - dy * bend;
  const cy = my + dx * bend;
  return `M ${round1(x1)} ${round1(y1)} Q ${round1(cx)} ${round1(cy)} ${round1(x2)} ${round1(y2)}`;
}

function arrowheadPath([x, y]: [number, number], angleRad: number, size = 6): string {
  const a1 = angleRad + Math.PI * 0.82;
  const a2 = angleRad - Math.PI * 0.82;
  const p1: [number, number] = [x + size * Math.cos(a1), y + size * Math.sin(a1)];
  const p2: [number, number] = [x + size * Math.cos(a2), y + size * Math.sin(a2)];
  return `M ${round1(x)} ${round1(y)} L ${round1(p1[0])} ${round1(p1[1])} L ${round1(p2[0])} ${round1(p2[1])} Z`;
}

// A short, fading, symbolic stub near a pin — used when a route leg's origin
// (or destination) is unlocatable. Fixed deterministic angle/length so it
// never implies a real position: apparatus honesty means we draw "arrives
// from off the map," never a line to a fabricated coordinate.
function stubPath([x, y]: [number, number], angleRad: number, length = 26): string {
  const x2 = x + length * Math.cos(angleRad);
  const y2 = y + length * Math.sin(angleRad);
  return `M ${round1(x2)} ${round1(y2)} L ${round1(x)} ${round1(y)}`;
}

const BROKEN_STUB_ANGLE = (-135 * Math.PI) / 180; // fixed up-and-out direction, not a claimed bearing

export interface RouteRenderResult {
  status: 'none' | 'full' | 'broken-origin' | 'broken-destination';
  pathD?: string;
  arrowD?: string;
  brokenD?: string;
}

// Renders a journey leg's route arc against an already-fitted viewport.
// - Both endpoints located: a full gentle dotted arc + a small solid
//   arrowhead at the destination.
// - Origin unlocatable, destination located: 'broken-origin' — a short
//   symbolic stub near the destination pin ONLY, never a line to a
//   fabricated origin (e.g. Od. 5's Ogygia -> Scheria leg).
// - Destination unlocatable: 'broken-destination' — nothing locatable to
//   anchor a route to; caller renders no arc at all.
// - No leg passed: 'none'.
export function renderRoute(leg: RouteLeg | undefined, viewport: Viewport): RouteRenderResult {
  if (!leg) return { status: 'none' };
  if (!leg.to.coords) return { status: 'broken-destination' };

  const toXY = project(leg.to.coords, viewport);

  if (!leg.from.coords) {
    return { status: 'broken-origin', brokenD: stubPath(toXY, BROKEN_STUB_ANGLE) };
  }

  const fromXY = project(leg.from.coords, viewport);
  const pathD = quadraticArcPath(fromXY, toXY);
  const angle = Math.atan2(toXY[1] - fromXY[1], toXY[0] - fromXY[0]);
  const arrowD = arrowheadPath(toXY, angle);
  return { status: 'full', pathD, arrowD };
}

// ── Full render ──────────────────────────────────────────────────────────

export interface SceneMapResult {
  svg: string;
  viewport: Viewport;
  located: ScenePlace[];
  unlocated: ScenePlace[];
  route: RouteRenderResult;
}

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

// Assembles the scene's place(s) + coastline + optional route into one
// self-contained SVG string. Pure and deterministic: identical inputs always
// produce an identical `svg` string.
export function renderSceneMap(
  places: ScenePlace[],
  coastline: Coastline,
  options: SceneMapOptions = {},
  route?: RouteLeg,
): SceneMapResult {
  const opts = { ...DEFAULT_SCENE_MAP_OPTIONS, ...options };
  const located = places.filter((p) => !!p.coords);
  const unlocated = places.filter((p) => !p.coords);

  const fitInput = [...located];
  if (route?.from.coords) fitInput.push(route.from);
  if (route?.to.coords) fitInput.push(route.to);

  const viewport = fitViewport(fitInput.length ? fitInput : located, opts);
  const { d: coastD } = coastlinePathData(coastline, viewport);
  const routeResult = renderRoute(route, viewport);

  const pinsMarkup = located
    .map((p) => {
      const [x, y] = project(p.coords!, viewport);
      const style = certaintyPinStyle(p.certainty);
      return pinMarkup(x, y, style);
    })
    .join('');

  const labelsMarkup = located
    .map((p) => {
      const [x, y] = project(p.coords!, viewport);
      const label = placeLabel(p, x, y, viewport, opts.fontSizePx);
      return `<text x="${round1(label.x)}" y="${round1(label.y)}" text-anchor="${label.anchor}" font-size="${opts.fontSizePx}" font-family="var(--font-ui)" fill="var(--text)">${escapeXml(label.text)}</text>`;
    })
    .join('');

  let routeMarkup = '';
  if (routeResult.status === 'full') {
    routeMarkup =
      `<path d="${routeResult.pathD}" fill="none" stroke="var(--accent-light)" stroke-width="1.6" stroke-dasharray="1 4" stroke-linecap="round"/>` +
      `<path d="${routeResult.arrowD}" fill="var(--accent)"/>`;
  } else if (routeResult.status === 'broken-origin') {
    routeMarkup = `<path d="${routeResult.brokenD}" fill="none" stroke="var(--text-mid)" stroke-width="1.4" stroke-dasharray="1 5" stroke-linecap="round" stroke-opacity="0.55"/>`;
  }

  const clipId = `${opts.idPrefix}-clip`;
  const ariaLabel = escapeXml(
    located.length ? `Map: ${located.map((p) => p.name).join(', ')}` : 'Map',
  );

  const svg =
    `<svg viewBox="0 0 ${opts.width} ${opts.height}" width="100%" height="100%" role="img" aria-label="${ariaLabel}" xmlns="http://www.w3.org/2000/svg">` +
    `<defs><clipPath id="${clipId}"><rect x="0" y="0" width="${opts.width}" height="${opts.height}" rx="6"/></clipPath></defs>` +
    `<g clip-path="url(#${clipId})">` +
    `<rect x="0" y="0" width="${opts.width}" height="${opts.height}" fill="var(--page-bg)"/>` +
    `<path d="${coastD}" fill="var(--border)" fill-opacity="0.9" fill-rule="evenodd" stroke="var(--text-mid)" stroke-width="0.75" stroke-opacity="0.35"/>` +
    routeMarkup +
    pinsMarkup +
    labelsMarkup +
    `</g>` +
    `</svg>`;

  return { svg, viewport, located, unlocated, route: routeResult };
}
