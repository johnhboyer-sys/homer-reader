// The bar's big count was set in Big Caslon, whose old-style "1" reads as a
// capital I (11 as "II"). It takes a face of Homer's own with lining figures
// (Palatino's stack: Palatino, Palatino Linotype, Times New Roman), at the
// same size.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const css = readFileSync(path.resolve(process.cwd(), 'styles/b-search.css'), 'utf8');
// The rules that set its face (others only resize it).
const rules = [...css.matchAll(/\.rc-n\s*\{([^}]*)\}/g)].map(m => m[1]).filter(r => /font:/.test(r));

describe('the count numeral', () => {
  it('is set in two rules (wide and narrow), both at their old sizes', () => {
    expect(rules).toHaveLength(2);
    expect(rules[0]).toMatch(/700 56px\/\.95/);
    expect(rules[1]).toMatch(/700 min\(46px, calc\(150px \/ var\(--d, 3\)\)\)\/\.95/);
  });

  it('uses the numeral face, with lining figures, never the display face', () => {
    for (const rule of rules) {
      expect(rule).not.toMatch(/--tface|--font-display/);
      expect(rule).toMatch(/var\(--nface\)/);
      expect(rule).toMatch(/font-variant-numeric:\s*lining-nums tabular-nums/);
    }
    expect(css).toMatch(/--nface:\s*var\(--font-greek\);/);
  });
});
