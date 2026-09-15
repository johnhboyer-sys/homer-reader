#!/usr/bin/env node
// Render harness for apparatus/plates/*.json — bundles the real shared/lib
// TS renderer with esbuild (no fixtures, no mocks) and screenshots the
// result with headless Chrome, so a maker can actually LOOK at linework
// (coastlines, relief contours) before reporting a plate change done
// (CLAUDE.md: "for anything whose output is an image, rendering it and
// LOOKING is a required gate"). Recipe: docs/TROY-MAPS-HANDOFF-2.md §2.
//
// Requires:
//   - shared/node_modules/.bin/esbuild (already a shared/ devDependency)
//   - a cached Playwright chrome-headless-shell build, e.g.
//     ~/Library/Caches/ms-playwright/chromium_headless_shell-*/
//   - Node 22 (`source ~/.nvm/nvm.sh && nvm use 22`)
//
// Usage — full plates, both themes, native size:
//   node scripts/render-plates.mjs --sheet troad,trojan-plain \
//     --theme light,dark --out build/plate-review/recut
//
// Usage — a named crop, a lat/lon window rendered at Nx zoom so linework can
// be judged up close (never trust a thumbnail):
//   node scripts/render-plates.mjs --sheet troad --theme light \
//     --out build/plate-review/recut \
//     --crop ida-ridge:39.60,26.60,39.80,26.90:4
//
// Usage — a crop in the plate's own pixel space (the lat/lon --crop cannot
// address a window that is not geography, e.g. the right-margin legend band):
//   node scripts/render-plates.mjs --sheet trojan-plain-schematic --theme light \
//     --out build/plate-review/schematic-ground \
//     --pxcrop camp-band:280,800,860,1080:3
//
// --places a,b,c keeps only those gazetteer ids after placesForSheet (the
// tag lookup and toPlatePlace mapping stay). Repeat --crop or --pxcrop for
// more than one window per run. --scale sets Chrome's device-scale-factor
// (supersampling) for every shot in the run, default 2. --tiers 1|all
// (default all) applies ONLY to the full-sheet render: '1' hides every
// labelTier === 2 label and its leader, so a full-sheet review shows what a
// reader sees unzoomed; crops always render every tier regardless.
//
// Bundles are written to build/.render-plates-bundle/ (gitignored, rebuilt
// every run) — never edits shared/lib/*.ts, only reads it.

import { execFileSync } from 'node:child_process';
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

// Sheet id -> the tag places.json's `maps` arrays use for that sheet
// (mirrors app/src/components/MapsPage.svelte's troadRegionalPlatePlaces /
// troadPlainPlatePlaces split, 2026-07-28). trojan-plain-schematic shares
// the 'troad-plain' tag with the geographic trojan-plain sheet (2026-07-30):
// a schematic-only place (e.g. hut-of-achilles) carries no `coords`, only a
// `plateAnchors.trojan-plain-schematic` anchor, so it resolves to nothing on
// the geographic sheet and to a conjectural pin here — same tag, two
// different, honest outcomes per plate.kind. MapsPage.svelte does not wire
// this sheet into a tab yet (item 3's Chart Room routing is separate,
// unfinished work); this harness only needs the tag to fetch the same place
// set the eventual UI will.
// troy-citadel carries its own tag (2026-07-30). None of the eight places tagged
// for it declares a `plateAnchors['troy-citadel']`, and a schematic plate only
// resolves a pin through that field (resolvePlacePosition), so every one of them
// lands in `unlocated`/`drawnByLayer` and the sheet draws no pins at all — which
// is the intended outcome, not an oversight: no gate at Hisarlık has been shown
// to be a gate Homer names, so there is no honest point to mark. The tag is
// wired anyway so this harness fetches the same place set the UI will.
const MAP_TAG = {
  troad: 'troad',
  'trojan-plain': 'troad-plain',
  'trojan-plain-schematic': 'troad-plain',
  'troy-citadel': 'troy-citadel',
};

function findChromeHeadlessShell() {
  const cacheDir = path.join(process.env.HOME, 'Library', 'Caches', 'ms-playwright');
  if (!existsSync(cacheDir)) {
    throw new Error(`no Playwright cache at ${cacheDir} — install a Playwright browser first`);
  }
  const dirs = readdirSync(cacheDir).filter((d) => d.startsWith('chromium_headless_shell-')).sort();
  if (dirs.length === 0) throw new Error(`no chromium_headless_shell build under ${cacheDir}`);
  const latest = dirs[dirs.length - 1];
  const bin = path.join(cacheDir, latest, 'chrome-headless-shell-mac-arm64', 'chrome-headless-shell');
  if (!existsSync(bin)) throw new Error(`expected chrome-headless-shell binary at ${bin}`);
  return bin;
}

function bundle() {
  mkdirSync(BUNDLE_DIR, { recursive: true });
  const plateOut = path.join(BUNDLE_DIR, 'plate.mjs');
  const geoOut = path.join(BUNDLE_DIR, 'geo.mjs');
  execFileSync(ESBUILD, ['lib/plate.ts', '--bundle', '--format=esm', '--platform=node', `--outfile=${plateOut}`], { cwd: SHARED, stdio: 'inherit' });
  execFileSync(ESBUILD, ['lib/geo.ts', '--bundle', '--format=esm', '--platform=node', `--outfile=${geoOut}`], { cwd: SHARED, stdio: 'inherit' });
  return { plateOut, geoOut };
}

function toPlatePlace(p) {
  // Mirrors MapsPage.svelte's toPlatePlace: trimmed to the fields plate.ts's
  // PlatePlace actually reads. `kind`/`rank` (2026-08-10, landmark-label
  // lane) drive the five geographic-plate label classes and settlement
  // hierarchy — see shared/lib/plate.ts's placeLabelClass/SETTLEMENT_RANK_STYLE.
  // `labelTier`/`labelSize` (2026-09-02, stage 4b LOOK-gate fix: both this
  // harness and MapsPage.svelte dropped them, so every place-anchored label
  // rendered at full settlement size regardless of its JSON `labelSize` —
  // see the sibling fix in MapsPage.svelte's own toPlatePlace).
  return {
    id: p.id,
    name: p.name,
    coords: p.coords,
    certainty: p.certainty,
    plateAnchors: p.plateAnchors,
    positionBasis: p.positionBasis,
    kind: p.kind,
    rank: p.rank,
    labelTier: p.labelTier,
    labelSize: p.labelSize,
  };
}

function placesForSheet(sheet) {
  const tag = MAP_TAG[sheet];
  if (!tag) throw new Error(`no places.json map tag known for sheet ${sheet}`);
  const doc = JSON.parse(readFileSync(PLACES_PATH, 'utf8'));
  return doc.places.filter((p) => (p.maps ?? []).includes(tag)).map(toPlatePlace);
}

// --tiers 1 (see parseArgs): hides every tier-2 label so a full-sheet review
// shows what a reader sees unzoomed, without the solver's own boxes moving
// (those stay reserved — see the flag's own doc comment below). CSS alone
// hides the label TEXT (tier is stamped as a class, `plate-label-tier2`),
// but a label's leader line is a separate element that carries no tier of
// its own, only the `data-label-for` id the two share — so hiding it needs
// a script pass, run once the SVG is in the DOM, matching leaders to the
// ids of the labels CSS just hid.
const HIDE_TIER2_STYLE = '<style>.plate-label-tier2{display:none}</style>';
const HIDE_TIER2_SCRIPT =
  '<script>' +
  'document.querySelectorAll(".plate-label-tier2[data-label-for]").forEach(function(l){' +
  'document.querySelectorAll(\'.plate-leader[data-label-for="\'+l.getAttribute("data-label-for")+\'"]\').forEach(function(p){p.style.display="none";});' +
  '});' +
  '</script>';

function pageHtml(svg, theme, width, height, hideTier2 = false) {
  const css = readFileSync(GLOBAL_CSS, 'utf8');
  return `<!doctype html><html data-theme="${theme}"><head><meta charset="utf-8"><style>
${css}
html,body{margin:0;padding:0;}
.plate-frame{width:${width}px;height:${height}px;overflow:hidden;position:relative;}
.plate-frame svg{display:block;width:${width}px;height:${height}px;}
</style>${hideTier2 ? HIDE_TIER2_STYLE : ''}</head><body><div class="plate-frame">${svg}</div>${hideTier2 ? HIDE_TIER2_SCRIPT : ''}</body></html>`;
}

function cropHtml(svg, theme, plateW, plateH, x0, y0, x1, y1, zoom, hideTier2 = false) {
  const css = readFileSync(GLOBAL_CSS, 'utf8');
  const cw = Math.round((x1 - x0) * zoom);
  const ch = Math.round((y1 - y0) * zoom);
  const html = `<!doctype html><html data-theme="${theme}"><head><meta charset="utf-8"><style>
${css}
html,body{margin:0;padding:0;}
.crop-frame{width:${cw}px;height:${ch}px;overflow:hidden;position:relative;}
.crop-inner{position:absolute;left:${Math.round(-x0 * zoom)}px;top:${Math.round(-y0 * zoom)}px;width:${plateW * zoom}px;height:${plateH * zoom}px;}
.crop-inner svg{display:block;width:${plateW * zoom}px;height:${plateH * zoom}px;}
</style>${hideTier2 ? HIDE_TIER2_STYLE : ''}</head><body><div class="crop-frame"><div class="crop-inner">${svg}</div></div>${hideTier2 ? HIDE_TIER2_SCRIPT : ''}</body></html>`;
  return { html, cw, ch };
}

function shoot(chromeBin, htmlPath, pngPath, width, height, scale) {
  execFileSync(chromeBin, [
    '--headless', '--disable-gpu', '--hide-scrollbars',
    `--force-device-scale-factor=${scale}`,
    `--window-size=${width},${height}`,
    `--screenshot=${pngPath}`,
    `file://${htmlPath}`,
  ], { stdio: 'inherit' });
}

function parseArgs(argv) {
  const out = {
    sheets: ['troad', 'trojan-plain'],
    themes: ['light', 'dark'],
    out: path.join('build', 'plate-review', 'recut'),
    scale: 2,
    crops: [], // { sheet, label, box: [minLat, minLon, maxLat, maxLon], zoom }
    pxcrops: [], // { label, box: [x0, y0, x1, y1], zoom } — plate-pixel space, see --pxcrop
    places: null, // optional id filter applied after placesForSheet, see --places
    // Full-sheet review vs. up-close crops (see HIDE_TIER2_STYLE): '1' hides
    // every PlatePlace/PlateLayer.labelTier === 2 label (and its leader) so
    // a full-sheet render shows what a reader sees unzoomed; 'all' (default)
    // renders every label regardless of tier, unchanged from before this
    // flag existed. The solver still reserves a hidden label's box — this
    // flag changes what paints, not what the layout solver sees.
    tiers: 'all',
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--sheet') out.sheets = argv[++i].split(',');
    else if (a === '--theme') out.themes = argv[++i].split(',');
    else if (a === '--out') out.out = argv[++i];
    else if (a === '--scale') out.scale = Number(argv[++i]);
    else if (a === '--places') out.places = argv[++i].split(',');
    else if (a === '--tiers') {
      const v = argv[++i];
      if (v !== '1' && v !== 'all') throw new Error(`--tiers must be "1" or "all", got ${v}`);
      out.tiers = v;
    }
    else if (a === '--pxcrop') {
      // label:x0,y0,x1,y1:zoom — a crop in the plate's OWN pixel space. The
      // lat/lon --crop below cannot address a schematic sheet at all (it has no
      // geography to project), and the citadel plate is the sheet whose linework
      // most needs looking at up close.
      const [label, box, zoomStr] = argv[++i].split(':');
      const [x0, y0, x1, y1] = box.split(',').map(Number);
      out.pxcrops.push({ label, box: [x0, y0, x1, y1], zoom: Number(zoomStr) });
    } else if (a === '--crop') {
      // label:minLat,minLon,maxLat,maxLon:zoom — applies to every --sheet
      // given (a crop spec that doesn't apply to a sheet's own bbox will
      // just clip to empty space, which the maker will notice at a glance).
      const [label, coords, zoomStr] = argv[++i].split(':');
      const [minLat, minLon, maxLat, maxLon] = coords.split(',').map(Number);
      out.crops.push({ label, box: [minLat, minLon, maxLat, maxLon], zoom: Number(zoomStr) });
    } else {
      throw new Error(`unknown arg ${a}`);
    }
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const outDir = path.resolve(REPO, args.out);
  mkdirSync(outDir, { recursive: true });

  console.log('[render-plates] bundling shared/lib/plate.ts + geo.ts with esbuild...');
  const { plateOut, geoOut } = bundle();
  const plateMod = await import(pathToFileURL(plateOut).href);
  const geoMod = await import(pathToFileURL(geoOut).href);
  const chromeBin = findChromeHeadlessShell();
  console.log(`[render-plates] chrome-headless-shell: ${chromeBin}`);

  const written = [];
  for (const sheet of args.sheets) {
    const raw = JSON.parse(readFileSync(path.join(PLATES_DIR, `${sheet}.json`), 'utf8'));
    const plate = plateMod.parsePlate(raw);
    let places = placesForSheet(sheet);
    if (args.places) {
      const want = new Set(args.places);
      places = places.filter((p) => want.has(p.id));
    }
    const result = plateMod.renderPlate(plate, places);
    const [plateW, plateH] = plate.size;

    for (const theme of args.themes) {
      const html = pageHtml(result.svg, theme, plateW, plateH, args.tiers === '1');
      const htmlPath = path.join(outDir, `${sheet}-${theme}.html`);
      const pngPath = path.join(outDir, `${sheet}-${theme}.png`);
      writeFileSync(htmlPath, html);
      shoot(chromeBin, htmlPath, pngPath, plateW, plateH, args.scale);
      written.push(pngPath);
      console.log(`[render-plates] wrote ${pngPath} (${plateW}x${plateH} @${args.scale}x)`);
    }

    for (const crop of args.pxcrops) {
      const [x0, y0, x1, y1] = crop.box;
      for (const theme of args.themes) {
        const { html, cw, ch } = cropHtml(result.svg, theme, plateW, plateH, x0, y0, x1, y1, crop.zoom);
        const htmlPath = path.join(outDir, `${sheet}-crop-${crop.label}-${theme}.html`);
        const pngPath = path.join(outDir, `${sheet}-crop-${crop.label}-${theme}.png`);
        writeFileSync(htmlPath, html);
        shoot(chromeBin, htmlPath, pngPath, cw, ch, args.scale);
        written.push(pngPath);
        console.log(`[render-plates] wrote ${pngPath} (pxcrop ${crop.label} @${crop.zoom}x, ${cw}x${ch} px)`);
      }
    }

    for (const crop of args.crops) {
      const [minLat, minLon, maxLat, maxLon] = crop.box;
      const corners = [
        [minLat, minLon], [minLat, maxLon], [maxLat, minLon], [maxLat, maxLon],
      ].map((ll) => geoMod.project(ll, result.viewport));
      const xs = corners.map((c) => c[0]);
      const ys = corners.map((c) => c[1]);
      const x0 = Math.min(...xs), x1 = Math.max(...xs);
      const y0 = Math.min(...ys), y1 = Math.max(...ys);
      for (const theme of args.themes) {
        const htmlSvg = plateMod.renderPlate(plate, places).svg; // fresh markup, same content
        const { html, cw, ch } = cropHtml(htmlSvg, theme, plateW, plateH, x0, y0, x1, y1, crop.zoom);
        const htmlPath = path.join(outDir, `${sheet}-crop-${crop.label}-${theme}.html`);
        const pngPath = path.join(outDir, `${sheet}-crop-${crop.label}-${theme}.png`);
        writeFileSync(htmlPath, html);
        shoot(chromeBin, htmlPath, pngPath, cw, ch, args.scale);
        written.push(pngPath);
        console.log(`[render-plates] wrote ${pngPath} (crop ${crop.label} @${crop.zoom}x zoom, ${cw}x${ch} px, device-scale ${args.scale}x)`);
      }
    }
  }
  console.log(`[render-plates] done: ${written.length} PNG(s) in ${outDir}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
