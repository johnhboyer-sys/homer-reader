// No empty results page, on the real corpus: for each baseline query of
// docs/search-port/search-counts-new.mjs (the two ἄναξ ἀνδρῶν
// queries are in search-chapter-draw-homer-heavy, and θάλασσα + sea in
// search-chapter-draw-homer-both, each in a worker of its own:
// together these walk most of the corpus), walk every page, and check that each
// draws at least one row and that the scenes drawn over all the pages are the
// bar's count. Pages are rows since aristotle-reader PR #201: every page but
// the last draws exactly 40, and a scene may run on to the next page (and no
// further; see walk-pages.ts). (Aristotle's counting PR fixed a page
// the pager counted but which drew no rows: shared/__tests__/
// search-chapter-draw.test.ts at aristotle-reader 7ddd67b7ef.) Without the
// data every test skips, loudly.
import { describe, expect, it } from 'vitest';
import { walk, walkSetup } from './walk-pages';

walkSetup('search-chapter-draw-homer');
describe('every results page draws rows, and they add up to the bar', () => {
  it.each([
    ['θάλασσα', 'g=θάλασσα'],
    ['every form of ἔπος', 'l=epos'],
    ['θεός, speeches only', 'g=θεός&spo=1'],
  ])('%s', async (_name, query) => {
    const { bar, scenes, pages, drawn } = await walk(query);
    console.info(`${query}: ${bar} → ${drawn} scenes drawn over ${pages} pages`);
    expect(drawn).toBe(scenes);
  }, 600000);
});
