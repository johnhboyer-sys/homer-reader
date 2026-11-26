// One map of the site (lib/site-nav.ts) for the header and the "you are here"
// line. shared/__tests__/palette.test.ts holds the Go-to palette's page list
// to the same paths.
import { describe, it, expect } from 'vitest';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { ALL_NAV_PATHS, GROUPS, POEMS, isCurrent, locate } from '../lib/site-nav';

const PAGES = resolve(process.cwd(), 'src/pages');
const hasPage = (path: string) => {
  const p = path.replace(/^\/|\/$/g, '');
  return existsSync(resolve(PAGES, `${p}.astro`)) || existsSync(resolve(PAGES, p, 'index.astro'));
};

describe('site map', () => {
  it('every header path is a page of the site', () => {
    for (const path of ALL_NAV_PATHS) {
      // The two poems are served by the [work] route.
      if (POEMS.some((p) => p.path === path)) continue;
      expect(hasPage(path), path).toBe(true);
    }
  });

  it('locates a page in its group, and a page under it in the same place', () => {
    expect(locate('/places/')?.group.label).toBe('Atlas');
    expect(locate('/places/')?.item.label).toBe('Places');
    expect(locate('/lemma/menis/')?.item.label).toBe('Lexicon');
    expect(locate('/vocabulary/iliad/')?.item.label).toBe('Vocabulary');
    expect(locate('/genealogies')?.group.label).toBe('People');
    expect(locate('/')).toBeNull();
    expect(locate('/about')).toBeNull();
  });

  it('does not take a longer name for a shorter one', () => {
    const maps = GROUPS[0].items.find((i) => i.label === 'Maps')!;
    expect(isCurrent('/maps/', maps)).toBe(true);
    expect(isCurrent('/mapsmith', maps)).toBe(false);
  });
});
