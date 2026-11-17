// Homer's speech filter on the new search page: the results held to the lines
// inside speeches (spo) or inside one speaker's (spk), Greek by each word's
// line and English by each word's estimated line, before anything counts them.
import { describe, expect, it } from 'vitest';
import { buildSpanIndex, speechCut } from '../lib/search-filters';
import type { Speech } from '../lib/data';
import type { SearchResult } from '../lib/search';

const speech = (book: number, lines: [number, number], speaker: string[]): Speech =>
  ({ book, lines, speaker, addressee: [] } as unknown as Speech);
const spans = { iliad: buildSpanIndex([speech(1, [17, 21], ['chryses']), speech(1, [59, 67], ['achilles'])]) };
const r = (p: Partial<SearchResult>): SearchResult => ({
  work: 'iliad', meta: { id: '1', book: 1, column: '1' } as SearchResult['meta'],
  grkMatch: false, engMatch: false, grkPositions: [], ...p,
});
// Greek token n stands at line n; English word n at line 10 + n.
const place = {
  grkLine: (_r: SearchResult, pos: number) => pos,
  engLine: (_r: SearchResult, _t: string, word: number) => 10 + word,
};

describe('speechCut', () => {
  it('keeps the Greek words inside any speech (spo)', () => {
    const out = speechCut([r({ grkMatch: true, grkPositions: [5, 18, 60] })], { kind: 'speeches' }, spans, place);
    expect(out).toHaveLength(1);
    expect(out[0].grkPositions).toEqual([18, 60]);
  });
  it('keeps only one speaker’s words (spk)', () => {
    const out = speechCut([r({ grkMatch: true, grkPositions: [5, 18, 60] })], { kind: 'speaker', id: 'achilles' }, spans, place);
    expect(out[0].grkPositions).toEqual([60]);
  });
  it('drops a result left with nothing, and one whose work has no spans', () => {
    expect(speechCut([r({ grkMatch: true, grkPositions: [5] })], { kind: 'speeches' }, spans, place)).toEqual([]);
    expect(speechCut([r({ work: 'odyssey', grkMatch: true, grkPositions: [18] })], { kind: 'speeches' }, spans, place)).toEqual([]);
  });
  it('holds a window by its first word', () => {
    const out = speechCut([r({ grkMatch: true, grkPositions: [16, 17, 20, 22], windows: [[16, 17], [20, 22]] })], { kind: 'speeches' }, spans, place);
    expect(out[0].windows).toEqual([[20, 22]]);
    expect(out[0].grkPositions).toEqual([20, 22]);
  });
  it('holds English words to their lines, and keeps the Greek of a result whose English goes', () => {
    const out = speechCut([r({
      grkMatch: true, grkPositions: [18], engMatch: true,
      engHits: [{ translation: 'murray', positions: [1, 8] }, { translation: 'pope', positions: [1] }],
    })], { kind: 'speeches' }, spans, place);
    expect(out[0].engHits).toEqual([{ translation: 'murray', positions: [8] }]);
    expect(out[0].engMatch).toBe(true);
    const greekOnly = speechCut([r({ grkMatch: true, grkPositions: [18], engMatch: true, engHits: [{ translation: 'pope', positions: [1] }] })], { kind: 'speeches' }, spans, place);
    expect(greekOnly[0]).toMatchObject({ grkMatch: true, engMatch: false, engHits: [] });
  });
  it('cuts a phrase’s match heads with its positions', () => {
    const out = speechCut([r({ engMatch: true, engHits: [{ translation: 'murray', positions: [1, 2, 8, 9], matches: [1, 8] }] })], { kind: 'speeches' }, spans, place);
    expect(out[0].engHits).toEqual([{ translation: 'murray', positions: [8, 9], matches: [8] }]);
  });
  it('drops a word whose line is unknown', () => {
    const out = speechCut([r({ grkMatch: true, grkPositions: [18, 19] })], { kind: 'speeches' },
      spans, { ...place, grkLine: (_r: SearchResult, pos: number) => (pos === 19 ? null : pos) });
    expect(out[0].grkPositions).toEqual([18]);
  });
});

import { englishLines } from '../lib/english-place';
import type { Segment } from '../lib/data';

describe('englishLines', () => {
  it('reads each word’s line off the ticks, snapped to a line the book has', () => {
    const greek = Array.from({ length: 10 }, (_, i) => ({ n: i + 1, text: 'α', tokens: [{ t: 'α', o: 0, k: 'a' }] }));
    const text = 'one two three four five six seven eight nine ten';
    const seg = { id: '1', column: '1', greek, english: { text, notes: [], markers: [], bekker: [
      { n: 1, offset: 0, real: true }, { n: 6, offset: text.indexOf('six'), real: true },
    ] } } as unknown as Segment;
    // Past the last tick a word is read at that tick, as englishPlace reads it.
    expect(englishLines(seg, { id: 'murray', slot: 'english' }, [0, 5, 9, 40])).toEqual([1, 6, 6, null]);
  });
});
