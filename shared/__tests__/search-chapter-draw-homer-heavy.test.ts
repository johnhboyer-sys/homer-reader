// The two largest walks of search-chapter-draw-homer.test.ts, in a file (so a
// worker) of their own: run after the others in one worker, they took the
// heap past its limit, the books every walk reads staying cached.
import { describe, expect, it } from 'vitest';
import { walk, walkSetup } from './walk-pages';

walkSetup('search-chapter-draw-homer-heavy');

describe('every results page draws rows, and they add up to the bar', () => {
  it.each([
    ['ἄναξ ἀνδρῶν, any word', 'g=ἄναξ ἀνδρῶν&gm=any'],
    ['ἄναξ ἀνδρῶν, all words', 'g=ἄναξ ἀνδρῶν&gm=all'],
  ])('%s', async (_name, query) => {
    const { bar, scenes, pages, drawn } = await walk(query);
    console.info(`${query}: ${bar} → ${drawn} scenes drawn over ${pages} pages`);
    expect(drawn).toBe(scenes);
  }, 600000);
});
