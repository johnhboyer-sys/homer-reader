import { describe, expect, it } from 'vitest';
import { filterRepetitions, isCrossEpic } from '../lib/repetitions';
import type { Repetition } from '../lib/data';

const repetitions: Repetition[] = [
  { key: 'a', text: 'ἄνδρα μοι ἔννεπε', count: 3, refs: [{ work: 'odyssey', book: 1, line: 1 }] },
  { key: 'b', text: 'πόδας ὠκὺς Ἀχιλλεύς', count: 2, refs: [
    { work: 'iliad', book: 1, line: 1 }, { work: 'odyssey', book: 24, line: 1 },
  ] },
];

describe('repetition filters', () => {
  it('recognizes references shared by both epics', () => {
    expect(isCrossEpic(repetitions[0])).toBe(false);
    expect(isCrossEpic(repetitions[1])).toBe(true);
  });

  it('finds Greek without requiring accents and combines the cross-epic filter', () => {
    expect(filterRepetitions(repetitions, 'ανδρα', false)).toEqual([repetitions[0]]);
    expect(filterRepetitions(repetitions, '', true)).toEqual([repetitions[1]]);
  });
});
