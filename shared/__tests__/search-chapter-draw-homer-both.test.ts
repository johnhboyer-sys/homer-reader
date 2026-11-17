// The Greek and English walks of search-chapter-draw-homer.test.ts, in a file
// (so a worker) of their own. Since pages are rows (aristotle-reader PR #201)
// a walk lays out every book with a hit, and an English search also reads
// them for the phrase list; with the other walks in one worker the heap ran
// out (16 Nov, lane E).
import { describe, expect, it } from 'vitest';
import { walk, walkSetup } from './walk-pages';

walkSetup('search-chapter-draw-homer-both');

describe('every results page draws rows, and they add up to the bar', () => {
  it.each([
    ['θάλασσα + sea, and', 'g=θάλασσα&e=sea&op=and'],
    ['θάλασσα + sea, and/or', 'g=θάλασσα&e=sea&op=or'],
  ])('%s', async (_name, query) => {
    const { bar, scenes, pages, drawn } = await walk(query);
    console.info(`${query}: ${bar} → ${drawn} scenes drawn over ${pages} pages`);
    expect(drawn).toBe(scenes);
  }, 600000);
});
