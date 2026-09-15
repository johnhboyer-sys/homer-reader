#!/usr/bin/env node
// Measures what a plate label's contrast ACTUALLY is on the rendered sheet,
// not what the token pair says it is.
//
// Why this exists (2026-08-13, plate-label legibility lane): shared/lib/
// plate.ts treats label contrast as a fixed pair — --text-mid over
// --scene-map-label-halo — and by that measure both themes pass AA
// comfortably (light 7.48:1, dark 8.15:1). But the halo only IS the label's
// background if it is wide enough to cover the pixels a reader's eye
// actually compares the glyph against. At the 0.65px it was cut to, it is
// not: the real surround a few pixels out is the hypsometric relief ramp,
// and MOUNT IDA measured 2.54:1 there in dark theme. shared/__tests__/
// plate-map-contrast.test.ts guards the token matrix; this guards the
// rendered result, which is the thing a reader sees.
//
// Method — per sheet, per theme:
//   1. render the real plate (the same esbuild-bundled shared/lib/plate.ts
//      the site ships, no fixtures) to PNG via chrome-headless-shell, and in
//      the same page dump every .plate-label's getBoundingClientRect();
//   2. decode the PNG (zlib + the PNG scanline filters — no image
//      dependency; see decodePng);
//   3. inside each label's rect, mark the pixels that are the glyph ink
//      (nearest to the theme's ink token, within INK_TOLERANCE);
//   4. dilate that ink mask outward and read two rings:
//        ADJACENT — 1..2 device px off the glyph edge: the halo, if there is
//                   one thick enough to be a background at all;
//        TERRAIN  — HALO_CLEAR_PX.. device px out: what the label is really
//                   sitting on once the halo has run out;
//   5. report the WCAG ratio of the sampled ink against each ring.
//
// A label PASSES when its ADJACENT ratio clears 4.5:1 (the AA floor for
// normal-size text — every label class on these plates is below the 18.66px
// bold / 24px regular large-text threshold). TERRAIN is reported alongside
// it and is expected to be worse: that gap is the halo doing its job.
//
// Usage:
//   node scripts/measure-label-contrast.mjs
//   node scripts/measure-label-contrast.mjs --sheet troad --theme dark
//   node scripts/measure-label-contrast.mjs --json out.json
//
// Requires the same toolchain as scripts/render-plates.mjs: Node 22
// (`nvm use 22`), shared/node_modules/.bin/esbuild, and a cached Playwright
// chrome-headless-shell.

import { execFileSync } from 'node:child_process';
import { inflateSync } from 'node:zlib';
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SHARED = path.join(REPO, 'shared');
const BUNDLE_DIR = path.join(REPO, 'build', '.render-plates-bundle');
const ESBUILD = path.join(SHARED, 'node_modules', '.bin', 'esbuild');
const PLATES_DIR = path.join(REPO, 'apparatus', 'plates');
const PLACES_PATH = path.join(REPO, 'apparatus', 'places.json');
const GLOBAL_CSS = path.join(SHARED, 'styles', 'global.css');
const WORK_DIR = path.join(REPO, 'build', '.measure-label-contrast');

// Device-scale factor for the measured render. 2 keeps a 0.65px stroke from
// vanishing into a single antialiased pixel row, so a thin halo is measured
// as generously as it can honestly be.
const SCALE = 2;
const AA_FLOOR = 4.5;
// How close (0-255 per channel, Euclidean) a pixel must be to the theme's
// ink token to count as glyph ink rather than antialiasing.
const INK_TOLERANCE = 48;
// Device-px rings, at SCALE=2 (so 2 device px = 1 CSS px).
//
// ADJACENT is one glyph stem wide. That is the scale the choice has to be
// made at, and it is not arbitrary: a halo is doing its job when it protects
// the letterform out to about the width of the letterform's own strokes —
// the distance at which the eye resolves the glyph edge. The smallest label
// class here is 9.5px at weight 400, a stem of ~1.2 CSS px, so the ring runs
// to 3 device px. It starts at 1, not 2, which is the CONSERVATIVE choice:
// distance-1 pixels are the glyph's own antialiasing fringe, blended toward
// the ink, and blending toward the ink lowers the measured ratio.
//
// Widening this ring would flatter any halo (more of it falls inside), and
// narrowing it would flatter a thin one (the fringe dominates). It is pinned
// to the stem so that neither the halo width nor the result can move it.
const ADJACENT_RING = [1, 3];
// Where the halo is assumed spent. 0.65px halo => ~0.3px outside the glyph
// edge; even the restored width stops well inside 4 CSS px.
const HALO_CLEAR_PX = 8;
const TERRAIN_RING = [HALO_CLEAR_PX, HALO_CLEAR_PX + 3];

// Same map tag table as scripts/render-plates.mjs.
const MAP_TAG = {
  troad: 'troad',
  'trojan-plain': 'troad-plain',
  'trojan-plain-schematic': 'troad-plain',
  'troy-citadel': 'troy-citadel',
};

// ── WCAG 2.1 contrast, same ~15 lines as shared/__tests__/plate-map-contrast.test.ts ──

const srgbToLinear = (c) => { const v = c / 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
const luminance = ([r, g, b]) => 0.2126 * srgbToLinear(r) + 0.7152 * srgbToLinear(g) + 0.0722 * srgbToLinear(b);
function contrast(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}
const hexToRgb = (hex) => { const n = parseInt(hex.replace('#', ''), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
const rgbToHex = ([r, g, b]) => '#' + [r, g, b].map((c) => Math.round(c).toString(16).padStart(2, '0')).join('');

// ── Minimal PNG decode: 8-bit truecolour (type 2) / truecolour+alpha (type 6),
//    non-interlaced — which is everything chrome-headless-shell --screenshot
//    emits. Standard library only (CLAUDE.md rule 7: no new dependency for a
//    build-time measurement tool). ──

function decodePng(buf) {
  if (buf.readUInt32BE(0) !== 0x89504e47) throw new Error('not a PNG');
  let pos = 8;
  let width = 0, height = 0, bitDepth = 0, colorType = 0, interlace = 0;
  const idat = [];
  while (pos < buf.length) {
    const len = buf.readUInt32BE(pos);
    const type = buf.toString('ascii', pos + 4, pos + 8);
    const data = buf.subarray(pos + 8, pos + 8 + len);
    if (type === 'IHDR') {
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      bitDepth = data[8];
      colorType = data[9];
      interlace = data[12];
    } else if (type === 'IDAT') idat.push(data);
    else if (type === 'IEND') break;
    pos += 12 + len;
  }
  if (bitDepth !== 8 || interlace !== 0 || (colorType !== 2 && colorType !== 6)) {
    throw new Error(`unsupported PNG: depth ${bitDepth}, colour type ${colorType}, interlace ${interlace}`);
  }
  const channels = colorType === 6 ? 4 : 3;
  const raw = inflateSync(Buffer.concat(idat));
  const stride = width * channels;
  const out = Buffer.alloc(height * stride);
  // Undo the per-scanline PNG filters (RFC 2083 §6).
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)];
    const line = raw.subarray(y * (stride + 1) + 1, y * (stride + 1) + 1 + stride);
    const cur = out.subarray(y * stride, (y + 1) * stride);
    const prev = y > 0 ? out.subarray((y - 1) * stride, y * stride) : null;
    for (let i = 0; i < stride; i++) {
      const a = i >= channels ? cur[i - channels] : 0;
      const b = prev ? prev[i] : 0;
      const c = prev && i >= channels ? prev[i - channels] : 0;
      let v = line[i];
      if (filter === 1) v += a;
      else if (filter === 2) v += b;
      else if (filter === 3) v += (a + b) >> 1;
      else if (filter === 4) {
        const p = a + b - c;
        const pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
        v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
      } else if (filter !== 0) throw new Error(`bad PNG filter ${filter}`);
      cur[i] = v & 255;
    }
  }
  return { width, height, channels, data: out };
}

const pixel = (img, x, y) => {
  const i = (y * img.width + x) * img.channels;
  return [img.data[i], img.data[i + 1], img.data[i + 2]];
};

// ── Chrome ──

function findChromeHeadlessShell() {
  const cacheDir = path.join(process.env.HOME, 'Library', 'Caches', 'ms-playwright');
  const dirs = readdirSync(cacheDir).filter((d) => d.startsWith('chromium_headless_shell-')).sort();
  if (!dirs.length) throw new Error(`no chromium_headless_shell build under ${cacheDir}`);
  const bin = path.join(cacheDir, dirs[dirs.length - 1], 'chrome-headless-shell-mac-arm64', 'chrome-headless-shell');
  if (!existsSync(bin)) throw new Error(`expected chrome-headless-shell at ${bin}`);
  return bin;
}

// The page carries the plate AND a script that publishes every label's laid-out
// rect, so the rects come from the same layout that produced the screenshot
// rather than from re-deriving glyph boxes out of the SVG source (which would
// miss textPath labels entirely, and would re-implement estimateLabelWidth's
// approximation instead of measuring the real thing).
function pageHtml(svg, theme, width, height) {
  const css = readFileSync(GLOBAL_CSS, 'utf8');
  return `<!doctype html><html data-theme="${theme}"><head><meta charset="utf-8"><style>
${css}
html,body{margin:0;padding:0;}
.plate-frame{width:${width}px;height:${height}px;overflow:hidden;position:relative;}
.plate-frame svg{display:block;width:${width}px;height:${height}px;}
</style></head><body><div class="plate-frame">${svg}</div>
<script>
document.addEventListener('DOMContentLoaded', function () {
  var out = [];
  document.querySelectorAll('.plate-label').forEach(function (el) {
    var r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return;
    var role = (el.getAttribute('class') || '').split(/\\s+/)
      .filter(function (c) { return c.indexOf('plate-label-') === 0 && c !== 'plate-label-along'; })
      .map(function (c) { return c.slice('plate-label-'.length); })[0] || 'unknown';
    out.push({ text: el.textContent.trim(), role: role, id: el.getAttribute('data-label-for') || '',
               x: r.x, y: r.y, w: r.width, h: r.height });
  });
  var pre = document.createElement('pre');
  pre.id = 'label-rects';
  pre.textContent = JSON.stringify(out);
  document.body.appendChild(pre);
});
</script></body></html>`;
}

function shoot(chromeBin, htmlPath, pngPath, width, height) {
  execFileSync(chromeBin, [
    '--headless', '--disable-gpu', '--hide-scrollbars',
    `--force-device-scale-factor=${SCALE}`,
    `--window-size=${width},${height}`,
    `--screenshot=${pngPath}`,
    `file://${htmlPath}`,
  ], { stdio: ['ignore', 'ignore', 'ignore'] });
}

function dumpLabelRects(chromeBin, htmlPath, width, height) {
  const dom = execFileSync(chromeBin, [
    '--headless', '--disable-gpu', '--hide-scrollbars',
    `--window-size=${width},${height}`,
    '--virtual-time-budget=2000',
    '--dump-dom',
    `file://${htmlPath}`,
  ], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, stdio: ['ignore', 'pipe', 'ignore'] });
  const m = dom.match(/<pre id="label-rects">([\s\S]*?)<\/pre>/);
  if (!m) throw new Error('label rects not found in dumped DOM — did the page script run?');
  const decoded = m[1].replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
  return JSON.parse(decoded);
}

// ── Per-label sampling ──

// The ink token each label class is painted in (shared/lib/plate.ts's
// LABEL_STYLES). Read out of global.css so a retune can't silently
// invalidate the measurement.
function inkTokens(css, theme) {
  const block = themeBlock(css, theme);
  const tok = (name) => {
    const m = block.match(new RegExp(`--${name}:\\s*(#[0-9A-Fa-f]{6})`));
    if (!m) throw new Error(`token --${name} not found in the ${theme} block`);
    return m[1];
  };
  return {
    region: tok('text-mid'), feature: tok('text-mid'), water: tok('text-mid'), minor: tok('text-mid'),
    settlement: tok('text'), river: tok('plate-river'), unknown: tok('text-mid'),
  };
}

// The light tokens live in the FIRST `:root {` block, the dark ones in the
// first `:root[data-theme="dark"] {` — same convention plate-map-contrast.test.ts
// relies on.
function themeBlock(css, theme) {
  const selector = theme === 'dark' ? ':root[data-theme="dark"] {' : ':root {';
  const start = css.indexOf(selector);
  if (start === -1) throw new Error(`selector not found in global.css: ${selector}`);
  let depth = 0, i = css.indexOf('{', start);
  const from = i;
  for (; i < css.length; i++) {
    if (css[i] === '{') depth++;
    else if (css[i] === '}' && --depth === 0) return css.slice(from + 1, i);
  }
  throw new Error(`unbalanced block for ${selector}`);
}

function measureLabel(img, rect, inkHex) {
  // Rect is in CSS px; the screenshot is SCALE x.
  const pad = HALO_CLEAR_PX + 6;
  const x0 = Math.max(0, Math.floor(rect.x * SCALE) - pad);
  const y0 = Math.max(0, Math.floor(rect.y * SCALE) - pad);
  const x1 = Math.min(img.width - 1, Math.ceil((rect.x + rect.w) * SCALE) + pad);
  const y1 = Math.min(img.height - 1, Math.ceil((rect.y + rect.h) * SCALE) + pad);
  const w = x1 - x0 + 1, h = y1 - y0 + 1;
  if (w <= 0 || h <= 0) return null;

  const ink = hexToRgb(inkHex);
  const isInk = new Uint8Array(w * h);
  const inkPixels = [];
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const p = pixel(img, x0 + x, y0 + y);
      const d = Math.hypot(p[0] - ink[0], p[1] - ink[1], p[2] - ink[2]);
      if (d <= INK_TOLERANCE) { isInk[y * w + x] = 1; inkPixels.push(p); }
    }
  }
  if (inkPixels.length < 12) return null; // not enough glyph found to trust

  // Chebyshev distance from the nearest ink pixel, by repeated dilation —
  // the rings are only a few px wide, so this is cheaper and simpler than a
  // full distance transform.
  const dist = new Int16Array(w * h).fill(-1);
  let frontier = [];
  for (let i = 0; i < w * h; i++) if (isInk[i]) { dist[i] = 0; frontier.push(i); }
  for (let d = 1; d <= TERRAIN_RING[1] && frontier.length; d++) {
    const next = [];
    for (const i of frontier) {
      const cx = i % w, cy = (i / w) | 0;
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          const nx = cx + dx, ny = cy + dy;
          if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
          const j = ny * w + nx;
          if (dist[j] === -1) { dist[j] = d; next.push(j); }
        }
      }
    }
    frontier = next;
  }

  const ringPixels = (lo, hi) => {
    const out = [];
    for (let i = 0; i < w * h; i++) {
      if (dist[i] >= lo && dist[i] <= hi) out.push(pixel(img, x0 + (i % w), y0 + ((i / w) | 0)));
    }
    return out;
  };

  // Median per channel: robust against a contour hairline or a pin edge
  // clipping the ring, which a mean would smear across the whole reading.
  const median = (pixels) => {
    if (!pixels.length) return null;
    return [0, 1, 2].map((c) => {
      const vals = pixels.map((p) => p[c]).sort((a, b) => a - b);
      return vals[vals.length >> 1];
    });
  };
  // Worst case: a label that is legible on median but crosses one pale ramp
  // step is still half-illegible, and the median hides that. Taken as the
  // 10th percentile rather than the outright minimum — a single stray pixel
  // (a contour hairline crossing the ring, a leftover antialiased edge) is
  // not a legibility failure, a tenth of the surround is.
  const worst = (pixels, inkRgb) => {
    if (!pixels.length) return null;
    const ratios = pixels.map((p) => contrast(inkRgb, p)).sort((a, b) => a - b);
    return { ratio: ratios[Math.floor(ratios.length * 0.1)] };
  };

  const inkSample = median(inkPixels);
  const adjacent = ringPixels(ADJACENT_RING[0], ADJACENT_RING[1]);
  const terrain = ringPixels(TERRAIN_RING[0], TERRAIN_RING[1]);
  const adjMedian = median(adjacent);
  const terMedian = median(terrain);
  return {
    inkPx: inkPixels.length,
    ink: rgbToHex(inkSample),
    adjacent: adjMedian && { hex: rgbToHex(adjMedian), ratio: contrast(inkSample, adjMedian) },
    adjacentWorst: worst(adjacent, inkSample),
    terrain: terMedian && { hex: rgbToHex(terMedian), ratio: contrast(inkSample, terMedian) },
    terrainWorst: worst(terrain, inkSample),
  };
}

// ── Plate build (mirrors scripts/render-plates.mjs) ──

function bundle() {
  mkdirSync(BUNDLE_DIR, { recursive: true });
  const plateOut = path.join(BUNDLE_DIR, 'plate.mjs');
  const geoOut = path.join(BUNDLE_DIR, 'geo.mjs');
  execFileSync(ESBUILD, ['lib/plate.ts', '--bundle', '--format=esm', '--platform=node', `--outfile=${plateOut}`], { cwd: SHARED, stdio: ['ignore', 'ignore', 'inherit'] });
  execFileSync(ESBUILD, ['lib/geo.ts', '--bundle', '--format=esm', '--platform=node', `--outfile=${geoOut}`], { cwd: SHARED, stdio: ['ignore', 'ignore', 'inherit'] });
  return { plateOut, geoOut };
}

function placesForSheet(sheet) {
  const tag = MAP_TAG[sheet];
  if (!tag) throw new Error(`no places.json map tag for sheet ${sheet}`);
  const doc = JSON.parse(readFileSync(PLACES_PATH, 'utf8'));
  return doc.places
    .filter((p) => (p.maps ?? []).includes(tag))
    .map((p) => ({ id: p.id, name: p.name, coords: p.coords, certainty: p.certainty,
                   plateAnchors: p.plateAnchors, positionBasis: p.positionBasis, kind: p.kind, rank: p.rank }));
}

function parseArgs(argv) {
  const out = { sheets: ['troad', 'trojan-plain'], themes: ['light', 'dark'], json: null, all: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--sheet') out.sheets = argv[++i].split(',');
    else if (argv[i] === '--theme') out.themes = argv[++i].split(',');
    else if (argv[i] === '--json') out.json = argv[++i];
    else if (argv[i] === '--all') out.all = true;
    else throw new Error(`unknown arg ${argv[i]}`);
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  mkdirSync(WORK_DIR, { recursive: true });
  const { plateOut, geoOut } = bundle();
  const plateMod = await import(pathToFileURL(plateOut).href);
  const geoMod = await import(pathToFileURL(geoOut).href);
  const chromeBin = findChromeHeadlessShell();
  const css = readFileSync(GLOBAL_CSS, 'utf8');

  const rows = [];
  for (const sheet of args.sheets) {
    const raw = JSON.parse(readFileSync(path.join(PLATES_DIR, `${sheet}.json`), 'utf8'));
    const plate = plateMod.parsePlate(raw);
    const places = placesForSheet(sheet);
    const [width, height] = plate.size;
    const { svg } = plateMod.renderPlate(plate, places, { idPrefix: `m-${sheet}`, geo: geoMod });

    for (const theme of args.themes) {
      const htmlPath = path.join(WORK_DIR, `${sheet}-${theme}.html`);
      const pngPath = path.join(WORK_DIR, `${sheet}-${theme}.png`);
      writeFileSync(htmlPath, pageHtml(svg, theme, width, height));
      shoot(chromeBin, htmlPath, pngPath, width, height);
      const rects = dumpLabelRects(chromeBin, htmlPath, width, height);
      const img = decodePng(readFileSync(pngPath));
      const inks = inkTokens(css, theme);

      for (const r of rects) {
        const m = measureLabel(img, r, inks[r.role] ?? inks.unknown);
        if (!m) continue;
        rows.push({ sheet, theme, text: r.text, role: r.role, ...m });
      }
    }
  }

  const shown = args.all ? rows : rows.filter((r) => r.role === 'region' || r.role === 'feature');
  shown.sort((a, b) => (a.adjacent?.ratio ?? 99) - (b.adjacent?.ratio ?? 99));

  const pad = (s, n) => String(s).padEnd(n);
  console.log(`\nRendered-pixel label contrast — AA floor ${AA_FLOOR}:1 on ADJACENT`);
  console.log(`  ADJACENT = ${ADJACENT_RING[0]}-${ADJACENT_RING[1]} device px off the glyph (the halo, if it is thick enough to be one)`);
  console.log(`  TERRAIN  = ${TERRAIN_RING[0]}-${TERRAIN_RING[1]} device px out (what the label really sits on)\n`);
  console.log(`  ${pad('sheet', 14)}${pad('theme', 6)}${pad('label', 26)}${pad('role', 11)}${pad('adjacent', 20)}${pad('worst', 10)}terrain`);
  let failures = 0;
  for (const r of shown) {
    const ok = (r.adjacent?.ratio ?? 0) >= AA_FLOOR;
    if (!ok) failures++;
    const adj = r.adjacent ? `${r.adjacent.ratio.toFixed(2)}:1 ${r.adjacent.hex}` : '—';
    const wst = r.adjacentWorst ? `${r.adjacentWorst.ratio.toFixed(2)}:1` : '—';
    const ter = r.terrain ? `${r.terrain.ratio.toFixed(2)}:1 ${r.terrain.hex}` : '—';
    console.log(`  ${ok ? ' ' : '!'} ${pad(r.sheet, 13)}${pad(r.theme, 6)}${pad(r.text.slice(0, 25), 26)}${pad(r.role, 11)}${pad(adj, 20)}${pad(wst, 10)}${ter}`);
  }
  console.log(`\n  ${shown.length - failures}/${shown.length} labels clear ${AA_FLOOR}:1 on the adjacent ring` +
    (failures ? ` — ${failures} BELOW` : ''));

  if (args.json) {
    writeFileSync(path.resolve(REPO, args.json), JSON.stringify(rows, null, 2));
    console.log(`  wrote ${args.json}`);
  }
  process.exitCode = failures ? 1 : 0;
}

main().catch((err) => { console.error(err); process.exit(2); });
