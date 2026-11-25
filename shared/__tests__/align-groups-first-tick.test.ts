import { describe, expect, it } from 'vitest';
import { alignGroups, flowParts } from '../lib/tick-chunks';

// Od. 9: the first tick (line 1) snaps forward to a speech opening at line 2.
// The first group must still open on the block's first line, or the phone's
// stacked Greek+English view drops line 9.1.
describe('alignGroups: first tick snapped past the block start', () => {
  const lines = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => ({ n }));
  const text = 'first run second run';
  const flow = flowParts(text, [
    { n: 1, real: true, off: 0 },
    { n: 6, real: true, off: 10 },
  ]);

  it('covers every line exactly once, in order, starting at index 0', () => {
    const groups = alignGroups(lines, flow, [2]);
    expect(groups[0].lines[0]).toBe(lines[0]);
    expect(groups.flatMap(g => g.lines.map(l => l.n))).toEqual(lines.map(l => l.n));
  });
});
