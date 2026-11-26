// The night heroes (home, /start/, the poem indexes, the landing pages, the
// poem cards) take their colours from --hero-* tokens in
// shared/styles/global.css, so the skin reverts by a variable swap. Round-3
// review finding: the values were written into the selectors, five times over.
//
// Two checks: no colour literal is left in those styles, and every --hero-*
// token a page reads is declared in BOTH theme blocks (a var() that names a
// token nobody declared paints nothing, and no other test would notice).
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const read = (rel: string) => readFileSync(path.resolve(process.cwd(), rel), 'utf-8');
const noComments = (css: string) => css.replace(/\/\*[\s\S]*?\*\//g, '');
/** The CSS of a file: the whole of a .css, the <style> blocks of an .astro. */
const cssOf = (rel: string) => {
  const src = read(rel);
  if (rel.endsWith('.css')) return noComments(src);
  return noComments(Array.from(src.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)).map((m) => m[1]).join('\n'));
};

const HERO_FILES = [
  'src/pages/index.astro',
  'src/pages/start/index.astro',
  'src/components/Landing.astro',
  'src/components/SeoLanding.astro',
  'src/styles/edition-pages.css',
];

/** Declarations whose value holds a colour literal. A mask's #000 is an alpha
    mask, not a colour on screen; black scrims and shadows are not skin. */
const literals = (css: string) =>
  Array.from(css.matchAll(/([\w-]+)\s*:\s*([^;{}]*(?:#[0-9a-fA-F]{3,8}\b|rgba?\()[^;{}]*)/g))
    .filter((m) => !/mask-image$/.test(m[1]))
    .filter((m) => !/^(?:[^#]*rgba?\(0,\s*0,\s*0,[^)]*\)[^#]*)$/.test(m[2]))
    .map((m) => `${m[1]}: ${m[2].trim()}`);

describe('hero colours are tokens', () => {
  for (const file of HERO_FILES) {
    it(`${file} writes no colour literal`, () => {
      expect(literals(cssOf(file))).toEqual([]);
    });
  }

  it('every --hero-* token a page reads is declared in both theme blocks', () => {
    const global = noComments(read('../shared/styles/global.css'));
    const block = (open: string) => {
      const at = global.indexOf(open);
      expect(at, `no ${open} block`).toBeGreaterThan(-1);
      return global.slice(at, global.indexOf('\n}', at));
    };
    const light = block(':root {');
    const dark = block(':root[data-theme="dark"] {');
    const used = new Set<string>();
    for (const file of HERO_FILES) {
      const css = cssOf(file);
      // Names a file declares for itself (--hero-accent, --hero-pad) are its own.
      const local = new Set(Array.from(css.matchAll(/(--hero-[\w-]+)\s*:/g)).map((m) => m[1]));
      for (const m of css.matchAll(/var\((--hero-[\w-]+)/g)) if (!local.has(m[1])) used.add(m[1]);
    }
    expect(used.size).toBeGreaterThan(8);
    for (const name of used) {
      expect(light, `${name} missing from :root`).toMatch(new RegExp(`${name}\\s*:`));
      expect(dark, `${name} missing from the dark block`).toMatch(new RegExp(`${name}\\s*:`));
    }
  });
});
