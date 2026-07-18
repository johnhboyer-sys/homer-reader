import { describe, expect, it } from 'vitest';
import { chunksForScene, mergeSceneFlowChunks, type TickChunkRange } from '../lib/scene-paging';

// A run of ~5-line tick chunks (as Reader.svelte derives from
// Segment.english.bekker), covering lines 1-49 with NO gap — the common case.
const chunks: TickChunkRange[] = [
  { startLine: 1, endLine: 4 },
  { startLine: 5, endLine: 9 },
  { startLine: 10, endLine: 14 },
  { startLine: 15, endLine: 19 },
  { startLine: 20, endLine: 24 },
  { startLine: 25, endLine: 29 },
  { startLine: 30, endLine: 34 },
  { startLine: 35, endLine: 39 },
  { startLine: 40, endLine: 44 },
  { startLine: 45, endLine: 49 },
];

describe('chunksForScene', () => {
  it('includes every chunk the scene range overlaps, even at misaligned edges', () => {
    // Scene 8-32 (Il. 1's second scene, real data): opens mid chunk[1]
    // (5-9) and closes mid chunk[6] (30-34) — neither edge is a tick
    // boundary, so both boundary chunks must be included WHOLE.
    expect(chunksForScene(chunks, { startLine: 8, endLine: 32 })).toEqual([1, 2, 3, 4, 5, 6]);
  });

  it('returns a single chunk for a scene fully inside one tick span', () => {
    expect(chunksForScene(chunks, { startLine: 11, endLine: 13 })).toEqual([2]);
  });

  it('handles a scene whose range starts exactly on a tick boundary', () => {
    expect(chunksForScene(chunks, { startLine: 10, endLine: 12 })).toEqual([2]);
  });

  it('handles a scene whose range ends exactly on a tick boundary', () => {
    expect(chunksForScene(chunks, { startLine: 27, endLine: 29 })).toEqual([5]);
  });

  it('treats a missing endLine as a single-line (open-ended) scene', () => {
    expect(chunksForScene(chunks, { startLine: 22 })).toEqual([4]);
  });

  it('never splits a chunk mid-way: a one-line scene inside a chunk still returns the WHOLE chunk index, not a partial', () => {
    // The contract is index-level inclusion, not line-level slicing — the
    // caller renders chunk[i]'s full flowParts, never a trimmed sub-range.
    const idxs = chunksForScene(chunks, { startLine: 21, endLine: 21 });
    expect(idxs).toEqual([4]);
    expect(chunks[idxs[0]]).toEqual({ startLine: 20, endLine: 24 });
  });

  it('is correct across the first and last scene of a book (proem + open-ended-style edges)', () => {
    expect(chunksForScene(chunks, { startLine: 1, endLine: 7 })).toEqual([0, 1]);
    expect(chunksForScene(chunks, { startLine: 45, endLine: 49 })).toEqual([9]);
  });

  it('vulgate-gap case: a chunk boundary that itself skips numbered lines is handled by real line numbers, not array arithmetic', () => {
    // A chunk list carrying a real vulgate gap (e.g. Il. 9.457→462, lines
    // 458-461 never existed in the vulgate and are absent from every chunk's
    // range) — chunk endLine/startLine are the real surrounding line numbers,
    // not lo+4 arithmetic, so a scene spanning the gap still resolves by
    // simple numeric overlap.
    const gappy: TickChunkRange[] = [
      { startLine: 450, endLine: 456 }, // lines 457-461 do not exist (gap)
      { startLine: 462, endLine: 466 },
      { startLine: 467, endLine: 471 },
    ];
    // Scene opens before the gap and closes after it: both flanking chunks
    // are included; nothing "in the gap" is expected or missing.
    expect(chunksForScene(gappy, { startLine: 453, endLine: 464 })).toEqual([0, 1]);
    // Scene entirely on the far side of the gap.
    expect(chunksForScene(gappy, { startLine: 463, endLine: 470 })).toEqual([1, 2]);
    // A degenerate scene whose single line falls inside the gap itself (not
    // expected from real apparatus data, since scene lines are drawn from
    // the actual text) degrades to the nearest chunk rather than a blank page.
    expect(chunksForScene(gappy, { startLine: 459 })).toEqual([0]);
  });

  it('returns an empty array against an empty chunk list', () => {
    expect(chunksForScene([], { startLine: 1, endLine: 5 })).toEqual([]);
  });
});

describe('mergeSceneFlowChunks', () => {
  it('joins a mid-paragraph scene seam into one continuous prose part', () => {
    const merged = mergeSceneFlowChunks([
      {
        flowParts: [{ text: 'in Argos, far from her native land,', n: null, real: false }],
        otables: {},
      },
      {
        flowParts: [{ text: 'as she walks to and fro before the loom', n: null, real: false }],
        otables: {},
      },
    ]);

    expect(merged.flowParts).toEqual([
      { text: 'in Argos, far from her native land, as she walks to and fro before the loom', n: null, real: false },
    ]);
  });

  it('keeps a TEI paragraph marker as a real prose boundary', () => {
    const merged = mergeSceneFlowChunks([
      { flowParts: [{ text: 'But go, do not anger me.', n: null, real: false }], otables: {} },
      {
        flowParts: [
          { text: null, n: null, real: false, para: true },
          { text: 'So he spoke, and the old man was seized with fear.', n: null, real: false },
        ],
        otables: {},
      },
    ]);

    expect(merged.flowParts).toEqual([
      { text: 'But go, do not anger me.', n: null, real: false },
      { text: null, n: null, real: false, para: true },
      { text: 'So he spoke, and the old man was seized with fear.', n: null, real: false },
    ]);
  });

  it('preserves footnote text and tables from every selected chunk', () => {
    const merged = mergeSceneFlowChunks([
      {
        flowParts: [{ text: 'First[^1].', n: null, real: false }],
        otables: { third: [{ n: 25, rows: [['first table']] }] },
      },
      {
        flowParts: [{ text: 'Second[^2].', n: null, real: false }],
        otables: { third: [{ n: 30, rows: [['second table']] }] },
      },
    ]);

    expect(merged.flowParts[0].text).toBe('First[^1]. Second[^2].');
    expect(merged.otables).toEqual({
      third: [
        { n: 25, rows: [['first table']] },
        { n: 30, rows: [['second table']] },
      ],
    });
  });

  it('does not add a second space or separate text adjoining a dash', () => {
    const spaced = mergeSceneFlowChunks([
      { flowParts: [{ text: 'already ', n: null, real: false }], otables: {} },
      { flowParts: [{ text: 'spaced', n: null, real: false }], otables: {} },
    ]);
    const dashed = mergeSceneFlowChunks([
      { flowParts: [{ text: 'the eye—', n: null, real: false }], otables: {} },
      { flowParts: [{ text: 'even the godlike Polyphemus', n: null, real: false }], otables: {} },
    ]);
    const leadingDash = mergeSceneFlowChunks([
      { flowParts: [{ text: 'he answered', n: null, real: false }], otables: {} },
      { flowParts: [{ text: '—without hesitation', n: null, real: false }], otables: {} },
    ]);

    expect(spaced.flowParts[0].text).toBe('already spaced');
    expect(dashed.flowParts[0].text).toBe('the eye—even the godlike Polyphemus');
    expect(leadingDash.flowParts[0].text).toBe('he answered—without hesitation');
  });
});
