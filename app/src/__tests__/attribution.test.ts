// The attribution page must not claim a Shield of Achilles illustrated panel
// unless a reader can actually reach one. MapsPage mounts PlatePanel only for
// `troad` and `trojan-plain`; no page or component loads `shield-of-achilles`.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

describe('attribution.astro illustrated plates', () => {
  it('does not name the Shield of Achilles among the Maps page illustrated panels', () => {
    const src = readFileSync(path.resolve(process.cwd(), 'src/pages/attribution.astro'), 'utf-8');
    const heading = src.indexOf('<h2>Illustrated Plates</h2>');
    expect(heading).toBeGreaterThanOrEqual(0);
    const after = src.slice(heading);
    const nextH2 = after.indexOf('<h2>', 1);
    const section = nextH2 === -1 ? after : after.slice(0, nextH2);
    expect(section).not.toMatch(/Shield of Achilles/);
  });
});
