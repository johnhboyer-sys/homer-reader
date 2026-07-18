import { describe, expect, it } from 'vitest';
import { buildSpanIndex, lineInAnySpeech, lineMatchesSpeaker, speechesAtLine } from '../lib/search-filters';
import type { Speech } from '../lib/data';

const chryses: Speech = {
  id: 'iliad-1', book: 1, lines: [17, 21],
  speaker: ['chryses'], addressee: ['agamemnon', 'greeks'],
  level: 0, cluster: 1, part: 1, type: 'G',
};
const achilles: Speech = {
  id: 'iliad-2', book: 1, lines: [59, 67],
  speaker: ['achilles'], addressee: ['greeks'],
  level: 0, cluster: 2, part: 1, type: 'G',
};
// The Od. 9.2-11.332 Apologoi frame: opens book 9, closes in book 11.
const apologoi9: Speech = {
  id: 'odyssey-890', book: 9, lines: [2, 332],
  speaker: ['odysseus'], addressee: ['alcinous'],
  level: 0, cluster: 2077, part: 2, type: 'G', crossBook: true,
};

describe('buildSpanIndex / speechesAtLine', () => {
  it('groups speeches by their recorded book', () => {
    const idx = buildSpanIndex([chryses, achilles]);
    expect(speechesAtLine(idx, 1, 18)).toEqual([chryses]);
    expect(speechesAtLine(idx, 1, 60)).toEqual([achilles]);
    expect(speechesAtLine(idx, 1, 30)).toEqual([]); // between the two spans
    expect(speechesAtLine(idx, 2, 18)).toEqual([]); // wrong book
  });

  it('a line outside every span in a book matches nothing', () => {
    const idx = buildSpanIndex([chryses]);
    expect(speechesAtLine(idx, 1, 16)).toEqual([]); // before lines[0]
    expect(speechesAtLine(idx, 1, 22)).toEqual([]); // after lines[1]
  });
});

describe('lineInAnySpeech ("speeches only")', () => {
  it('true inside a span, false outside, false in an unindexed book', () => {
    const idx = buildSpanIndex([chryses]);
    expect(lineInAnySpeech(idx, 1, 19)).toBe(true);
    expect(lineInAnySpeech(idx, 1, 1)).toBe(false); // Il. 1.1-6 proem: narrator, not speech
    expect(lineInAnySpeech(idx, 5, 19)).toBe(false);
  });
});

describe('lineMatchesSpeaker', () => {
  it('matches only the named speaker\'s own span', () => {
    const idx = buildSpanIndex([chryses, achilles]);
    expect(lineMatchesSpeaker(idx, 1, 60, 'achilles')).toBe(true);
    expect(lineMatchesSpeaker(idx, 1, 60, 'hector')).toBe(false); // Hector never speaks this line
    expect(lineMatchesSpeaker(idx, 1, 18, 'achilles')).toBe(false); // right book, wrong span
  });

  it('a line inside no span never matches, regardless of speaker id', () => {
    const idx = buildSpanIndex([chryses]);
    expect(lineMatchesSpeaker(idx, 1, 1, 'chryses')).toBe(false);
  });

  it('an unknown speaker id simply never matches (no invented identification)', () => {
    const idx = buildSpanIndex([chryses]);
    expect(lineMatchesSpeaker(idx, 1, 18, 'nobody')).toBe(false);
  });
});

describe('crossBook spans (the Apologoi frame)', () => {
  it('matches from lines[0] onward, unbounded, within the recorded opening book', () => {
    const idx = buildSpanIndex([apologoi9]);
    expect(lineInAnySpeech(idx, 9, 2)).toBe(true);
    expect(lineInAnySpeech(idx, 9, 332)).toBe(true);
    // Unbounded past lines[1] within the SAME book — the true close is in a
    // later book, so anything from lines[0] to book 9's real end is inside.
    expect(lineInAnySpeech(idx, 9, 566)).toBe(true);
    expect(lineMatchesSpeaker(idx, 9, 500, 'odysseus')).toBe(true);
  });

  it('never claims a match in a book it merely passes through — no endBook to trust', () => {
    const idx = buildSpanIndex([apologoi9]);
    // Books 10 and 11 are genuinely inside the Apologoi frame narratively,
    // but this index has no data placing the span there, so it must not
    // invent a match (honest under-match, never an over-claim).
    expect(lineInAnySpeech(idx, 10, 1)).toBe(false);
    expect(lineInAnySpeech(idx, 11, 100)).toBe(false);
  });

  it('before the opening line, no match even in the opening book', () => {
    const idx = buildSpanIndex([apologoi9]);
    expect(lineInAnySpeech(idx, 9, 1)).toBe(false);
  });
});
