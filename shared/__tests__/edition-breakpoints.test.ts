// Round-2 review finding: a CSS rule hid the English column on side-by-side
// rows up to 690px, but Reader.svelte only swaps those rows for stacked groups
// at its own phoneWidth (680px). Between the two, Both view showed no English.
// The rules that depend on the swap must live at the width the swap happens.
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.cwd(), '..');
const css = readFileSync(path.join(root, 'shared/styles/global.css'), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '');
const reader = readFileSync(path.join(root, 'shared/components/Reader.svelte'), 'utf8');

/** Every rule whose selector matches, with the @media preludes that enclose it. */
function rulesMatching(source: string, test: (selector: string) => boolean) {
  const found: { selector: string; body: string; media: string[] }[] = [];
  const stack: string[] = [];
  let i = 0;
  let chunk = '';
  while (i < source.length) {
    const ch = source[i];
    if (ch === '{') {
      const prelude = chunk.trim();
      chunk = '';
      if (prelude.startsWith('@')) {
        stack.push(prelude);
      } else {
        const end = source.indexOf('}', i);
        const body = source.slice(i + 1, end);
        if (test(prelude)) found.push({ selector: prelude, body, media: stack.filter((s) => s.startsWith('@media')) });
        i = end;
      }
    } else if (ch === '}') {
      stack.pop();
      chunk = '';
    } else {
      chunk += ch;
    }
    i++;
  }
  return found;
}

describe('the reader phone breakpoint', () => {
  const m = reader.match(/phoneWidth\s*=[^;]*matchMedia\('\(max-width:\s*(\d+)px\)'\)/);
  it('Reader.svelte still states its phone width as a max-width media query', () => {
    expect(m).not.toBeNull();
  });
  const phone = Number(m?.[1]);

  it('the rule that hides the English column before stacking uses that same width', () => {
    const rules = rulesMatching(css, (s) => /:not\(\.stacked-both\)/.test(s) && /\.english-col/.test(s))
      .filter((r) => /display:\s*none/.test(r.body));
    expect(rules.length).toBeGreaterThan(0);
    for (const r of rules) {
      // `@media screen` (the skin's wrapper) carries no width; the one width
      // query around the rule must be the phone's.
      expect(r.media.filter((q) => /width/.test(q))).toEqual([`@media (max-width: ${phone}px)`]);
    }
  });

  it('that rule stands down while a saved single-language view or Reader mode is pending', () => {
    const rules = rulesMatching(css, (s) => /:not\(\.stacked-both\)/.test(s) && /\.english-col/.test(s))
      .filter((r) => /display:\s*none/.test(r.body));
    for (const r of rules) {
      expect(r.selector).toContain(':not([data-rview])');
      expect(r.selector).toContain(':not([data-rposture])');
    }
  });

  it('every rule that styles the stacked groups lives at or inside the phone width', () => {
    const rules = rulesMatching(css, (s) => /\.stacked-both/.test(s) && !/:not\(\.stacked-both\)/.test(s));
    expect(rules.length).toBeGreaterThan(0);
    for (const r of rules) {
      const widths = r.media.flatMap((q) => Array.from(q.matchAll(/max-width:\s*(\d+)px/g)).map((x) => Number(x[1])));
      // Print rules and unconditional rules are fine: .stacked-both only exists
      // on screen at phone width. A max-width wider than the phone's is the bug.
      for (const w of widths) expect(w).toBeLessThanOrEqual(phone);
    }
  });
});
