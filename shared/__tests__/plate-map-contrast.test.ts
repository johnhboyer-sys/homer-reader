// Contrast regression guard for the plate/scene-map land/sea/coast/hachure
// tokens (shared/styles/global.css). Parses the REAL global.css (not a
// hard-coded copy of its values) so this fails the moment someone retunes
// the palette back into the two defects fixed 2026-07-28:
//   1. land/sea fill separation collapsing toward 1:1 (indistinguishable),
//      or the land-lighter-than-sea polarity flipping between themes.
//   2. the hachure ink token's rendered contrast against land diverging
//      between themes (the old bug: a fixed fill-opacity stacked on an
//      already-alpha-composited dark-mode ink, so the identical declaration
//      bought ~8.7:1 in light and only ~4.7:1 in dark).
// No third-party contrast library exists in this repo (shared/__tests__/
// a11y.test.ts only wraps axe-core, which needs a live DOM/computed style,
// not raw CSS custom-property text) — the WCAG relative-luminance/contrast
// formulas below are the standard ~15-line implementation, kept local
// rather than adding a dependency.
import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const CSS_PATH = path.resolve(process.cwd(), 'styles/global.css');
const css = fs.readFileSync(CSS_PATH, 'utf-8');

// ── WCAG 2.1 contrast (see https://www.w3.org/TR/WCAG21/#contrast-minimum) ──

function hexToRgb(hex: string): [number, number, number] {
  const h = hex.replace('#', '');
  const n = parseInt(h, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function srgbToLinear(c: number): number {
  const v = c / 255;
  return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
}

function relativeLuminance([r, g, b]: [number, number, number]): number {
  const [R, G, B] = [r, g, b].map(srgbToLinear);
  return 0.2126 * R + 0.7152 * G + 0.0722 * B;
}

function contrastRatio(hexA: string, hexB: string): number {
  const la = relativeLuminance(hexToRgb(hexA));
  const lb = relativeLuminance(hexToRgb(hexB));
  const lighter = Math.max(la, lb);
  const darker = Math.min(la, lb);
  return (lighter + 0.05) / (darker + 0.05);
}

// ── Minimal CSS block/token extraction (real file, not re-typed values) ──

// Finds the FIRST top-level rule whose selector text contains `selector`
// (exact substring match, e.g. `:root[data-theme="dark"] {`) and returns
// its brace-balanced body, so later unrelated rules reusing the same bare
// `:root {` selector elsewhere in the file (e.g. the speaker-colour palette
// further down) can't be mistaken for the theme block that actually carries
// the scene-map tokens — those tokens are always declared in the FIRST
// occurrence of each of the four selectors below.
function extractBlock(selector: string): string {
  const selIdx = css.indexOf(selector);
  if (selIdx === -1) throw new Error(`plate-map-contrast test: selector not found in global.css: ${selector}`);
  const braceStart = css.indexOf('{', selIdx);
  let depth = 0;
  let i = braceStart;
  for (; i < css.length; i++) {
    if (css[i] === '{') depth++;
    else if (css[i] === '}') {
      depth--;
      if (depth === 0) break;
    }
  }
  return css.slice(braceStart, i + 1);
}

function readToken(block: string, name: string): string {
  const m = block.match(new RegExp(`${name}:\\s*([^;]+);`));
  if (!m) throw new Error(`plate-map-contrast test: token ${name} not found in the given block`);
  return m[1].trim();
}

interface ThemeBlock {
  name: string;
  sea: string;
  land: string;
  coast: string;
  hachure: string;
}

function readThemeBlock(name: string, selector: string): ThemeBlock {
  const block = extractBlock(selector);
  return {
    name,
    sea: readToken(block, '--scene-map-sea'),
    land: readToken(block, '--scene-map-land'),
    coast: readToken(block, '--scene-map-coast'),
    hachure: readToken(block, '--flaxman-hachure'),
  };
}

// The four theme blocks that declare the scene-map/plate tokens (see
// CLAUDE.md's brief for this defect: lines 89-92 / 171-174 / 195-198 /
// 222-225 as of 2026-07-28 — selectors below, not line numbers, so this
// survives the file being edited around them).
const THEME_BLOCKS: ThemeBlock[] = [
  readThemeBlock('light (:root default)', ':root {'),
  readThemeBlock('dark (prefers-color-scheme, no data-theme)', ':root:not([data-theme]) {'),
  readThemeBlock('dark (data-theme="dark")', ':root[data-theme="dark"] {'),
  readThemeBlock('light (data-theme="light")', ':root[data-theme="light"] {'),
];

const MIN_COAST_CONTRAST = 3; // WCAG non-text (graphical object) minimum
// The measured defect was 1.022 (dark) / 1.086 (light) — land and sea all but
// identical, and the polarity inverted between themes. The fix is a genuinely
// blue sea against warm land (John, 2026-07-28: "colour is free, this is
// digital, not print"), which measures 1.67 light / 1.66 dark.
//
// The bar sits at 1.5 rather than just above the defect deliberately: a lower
// bar would pass a desaturated blue-grey sea, which is exactly the print-era
// restraint this palette was changed to get away from. Luminance ratio also
// understates the real separation here, since most of the work is done by hue —
// so a value that clears 1.5 on luminance is emphatically water.
const MIN_LAND_SEA_SEPARATION = 1.5;
const MIN_HACHURE_CONTRAST = 4.5; // floor per theme
const MIN_HACHURE_RATIO = 0.7; // min(light,dark)/max(light,dark) — "comparable rendered contrast"; the old defect scored ~0.54

describe('plate/scene-map token contrast (parsed from the real global.css)', () => {
  it.each(THEME_BLOCKS)('$name: coast clears 3:1 against both land and sea', ({ coast, land, sea }) => {
    expect(contrastRatio(coast, land)).toBeGreaterThanOrEqual(MIN_COAST_CONTRAST);
    expect(contrastRatio(coast, sea)).toBeGreaterThanOrEqual(MIN_COAST_CONTRAST);
  });

  it.each(THEME_BLOCKS)('$name: land and sea fills are perceivably different (>= $MIN_LAND_SEA_SEPARATION:1)', ({ land, sea }) => {
    expect(contrastRatio(land, sea)).toBeGreaterThanOrEqual(MIN_LAND_SEA_SEPARATION);
  });

  it('land is lighter than sea in EVERY theme block (consistent polarity — the inversion defect)', () => {
    const polarities = THEME_BLOCKS.map((t) => relativeLuminance(hexToRgb(t.land)) > relativeLuminance(hexToRgb(t.sea)));
    expect(polarities.every((landLighter) => landLighter === true)).toBe(true);
  });

  it.each(THEME_BLOCKS)('$name: hachure ink clears a $MIN_HACHURE_CONTRAST:1 floor against land', ({ hachure, land }) => {
    expect(contrastRatio(hachure, land)).toBeGreaterThanOrEqual(MIN_HACHURE_CONTRAST);
  });

  it('hachure-vs-land contrast is comparable across every theme block (the fill-opacity double-alpha-stacking defect)', () => {
    const ratios = THEME_BLOCKS.map((t) => contrastRatio(t.hachure, t.land));
    const min = Math.min(...ratios);
    const max = Math.max(...ratios);
    expect(min / max).toBeGreaterThanOrEqual(MIN_HACHURE_RATIO);
  });
});
