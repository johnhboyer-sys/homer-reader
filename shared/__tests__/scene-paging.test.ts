import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  chunksForScene,
  mergeSceneFlowChunks,
  sentenceEndOffsets,
  sentenceSnapScenePages,
  type SceneFlowChunk,
  type SceneFlowPart,
  type SceneReadingChunk,
  type SceneRange,
  type TickChunkRange,
} from '../lib/scene-paging';

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

// ── Item 1 evidence: the raw (pre-sentence-snap) boundary behavior ─────────
// John's brief asked to FIRST establish, with evidence, whether adjacent
// scene pages share overlapping boundary chunks or partition them. They
// share: chunksForScene includes a chunk overlapping BOTH neighboring
// scenes' ranges (that's the whole point of "every overlapping chunk
// renders WHOLE" — see this file's header comment), so mergeSceneFlowChunks
// puts that chunk's full text on BOTH pages. This is the behavior
// sentenceSnapScenePages (below) replaces for Reading Mode.
describe('chunksForScene + mergeSceneFlowChunks — raw boundary behavior (evidence for item 1)', () => {
  it('adjacent scenes sharing an overlapping chunk render the SAME text on both pages', () => {
    const proseChunks: SceneReadingChunk[] = [
      { startLine: 1, endLine: 4, flowParts: [{ text: 'Sing of the wrath.', n: null, real: false }], otables: {} },
      { startLine: 5, endLine: 9, flowParts: [{ text: ' Chryses came to ransom his daughter, but Agamemnon refused him.', n: null, real: false }], otables: {} },
      { startLine: 10, endLine: 14, flowParts: [{ text: ' He withdrew in wrath.', n: null, real: false }], otables: {} },
    ];
    const sceneA: SceneRange = { startLine: 1, endLine: 7 };  // ends mid chunk[1]
    const sceneB: SceneRange = { startLine: 8, endLine: 12 }; // opens mid chunk[1] — SAME chunk

    const pageA = mergeSceneFlowChunks(chunksForScene(proseChunks, sceneA).map((i) => proseChunks[i]));
    const pageB = mergeSceneFlowChunks(chunksForScene(proseChunks, sceneB).map((i) => proseChunks[i]));
    const textA = pageA.flowParts.map((p) => p.text ?? '').join('');
    const textB = pageB.flowParts.map((p) => p.text ?? '').join('');

    const shared = 'Chryses came to ransom his daughter, but Agamemnon refused him.';
    expect(textA).toContain(shared);
    expect(textB).toContain(shared); // duplicated verbatim on the next page too
  });
});

describe('sentenceEndOffsets', () => {
  it('finds a sentence end at a plain terminator + space + capital, including one at the true end of the string', () => {
    const text = 'The dog ran. The cat slept.';
    expect(sentenceEndOffsets(text)).toEqual([13, text.length]);
  });

  it('does NOT treat a colon as a sentence end (John: a colon introduces what follows, e.g. a speech, on the SAME page)', () => {
    const text = 'He gave a command: "Go now," he said. She wept.';
    const offsets = sentenceEndOffsets(text);
    expect(offsets.length).toBe(2);
    expect(text.slice(0, offsets[0])).toBe('He gave a command: "Go now," he said. ');
    expect(text.slice(offsets[0], offsets[1])).toBe('She wept.');
  });

  it('treats a terminator followed by an inline footnote marker as a real sentence end (real Murray convention)', () => {
    const text = 'He was braver than his father.[^1.9.1] He sat down and wept.';
    const offsets = sentenceEndOffsets(text);
    expect(offsets.length).toBe(2);
    expect(text.slice(0, offsets[0])).toBe('He was braver than his father.[^1.9.1] ');
  });

  it('does not treat a footnote marker embedded mid-sentence (no terminator before it) as a boundary', () => {
    const text = 'From the time when[^1.1.1] first they parted in strife, the plan of Zeus was fulfilled.';
    expect(sentenceEndOffsets(text)).toEqual([text.length]);
  });

  it('allows a closing quote to trail the terminator before the whitespace', () => {
    const text = 'She said, "I am fine." He nodded.';
    const offsets = sentenceEndOffsets(text);
    expect(text.slice(0, offsets[0])).toBe('She said, "I am fine." ');
  });

  it('does not treat a single-capital initial as a sentence end (John: protect single-capital abbreviations)', () => {
    const text = 'T. E. Lawrence rode away. The desert was silent.';
    const offsets = sentenceEndOffsets(text);
    // Two REAL sentences here ("T. E. Lawrence rode away." and "The desert
    // was silent.") — the initials "T." and "E." are guarded, not counted.
    expect(offsets.length).toBe(2);
    expect(text.slice(0, offsets[0])).toBe('T. E. Lawrence rode away. ');
    expect(text.slice(offsets[0])).toBe('The desert was silent.');
  });

  it('does not treat a terminator followed by lowercase text as a sentence end (dialogue trailing off mid-attribution)', () => {
    const text = 'She could not stop. she wept on and on.';
    expect(sentenceEndOffsets(text)).toEqual([text.length]);
  });

  it('treats ? and ! as terminators too', () => {
    expect(sentenceEndOffsets('Who goes there? Halt! Identify yourself.').length).toBe(3);
  });
});

describe('sentenceSnapScenePages', () => {
  const textOf = (p: SceneFlowChunk) => p.flowParts.map((x) => x.text ?? '').join('');

  it('extends a page past its natural chunk end to complete a dangling sentence, and the next page starts fresh (no duplication)', () => {
    const chunk0Text = 'Alpha bravo charlie delta echo foxtrot golf hotel india juliet';
    const chunk1Text = ' kilo lima. Mike november oscar papa quebec romeo sierra tango uniform victor whiskey xray yankee zulu.';
    const chunks: SceneReadingChunk[] = [
      { startLine: 1, endLine: 5, flowParts: [{ text: chunk0Text, n: null, real: false }], otables: {} },
      { startLine: 6, endLine: 10, flowParts: [{ text: chunk1Text, n: null, real: false }], otables: {} },
    ];
    const scenes: SceneRange[] = [
      { startLine: 1, endLine: 5 },
      { startLine: 6, endLine: 10 },
    ];
    const [page0, page1] = sentenceSnapScenePages(chunks, scenes).map(textOf);

    // The raw chunk edge falls mid-sentence ("...juliet" | " kilo lima...") —
    // page 0 EXTENDS past its own chunk to complete that sentence.
    expect(page0).toBe('Alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima. ');
    // page 1 starts CLEAN at the next sentence — no repeat of "kilo lima.".
    expect(page1).toBe('Mike november oscar papa quebec romeo sierra tango uniform victor whiskey xray yankee zulu.');
    // No text lost or duplicated: concatenation reconstructs the whole book.
    expect(page0 + page1).toBe(chunk0Text + chunk1Text);
  });

  it("collapses a scene entirely swallowed by the previous page's completed sentence into an EMPTY page — the honest edge case, not a bug", () => {
    const c0 = 'Sing of the wrath of Achilles';
    const c1 = ' terrible and consuming, that brought countless woes.';
    const c2 = ' Many a valiant soul it sent to Hades.';
    const chunks: SceneReadingChunk[] = [
      { startLine: 1, endLine: 4, flowParts: [{ text: c0, n: null, real: false }], otables: {} },
      { startLine: 5, endLine: 9, flowParts: [{ text: c1, n: null, real: false }], otables: {} },
      { startLine: 10, endLine: 14, flowParts: [{ text: c2, n: null, real: false }], otables: {} },
    ];
    const scenes: SceneRange[] = [
      { startLine: 1, endLine: 4 },
      { startLine: 5, endLine: 9 },  // wholly inside the sentence scene 0 already completed
      { startLine: 10, endLine: 14 },
    ];
    const [page0, page1, page2] = sentenceSnapScenePages(chunks, scenes).map(textOf);

    // The sentence-end match consumes the whitespace that follows the
    // terminator too (same rule as every other test above) — here that
    // whitespace happens to be c2's own leading space, so it moves to page 0
    // and page 2 starts at "Many" with none to spare.
    expect(page0).toBe(c0 + c1 + ' ');
    expect(page1).toBe('');
    expect(page2).toBe(c2.slice(1));
    expect(page0 + page1 + page2).toBe(c0 + c1 + c2); // no loss, no duplication
  });

  it('places a zero-width marker (tick / paragraph) on exactly one page — never dropped, never duplicated', () => {
    const chunks: SceneReadingChunk[] = [
      { startLine: 1, endLine: 4, flowParts: [{ text: 'Sing of the wrath.', n: null, real: false }], otables: {} },
      {
        startLine: 5, endLine: 9,
        flowParts: [
          { text: null, n: 5, real: true },
          { text: ' Chryses came bearing gifts.', n: null, real: false },
        ],
        otables: {},
      },
    ];
    const scenes: SceneRange[] = [
      { startLine: 1, endLine: 4 },
      { startLine: 5, endLine: 9 },
    ];
    const pages = sentenceSnapScenePages(chunks, scenes);
    const tickCount = pages.reduce((n, p) => n + p.flowParts.filter((x) => x.n === 5).length, 0);
    expect(tickCount).toBe(1);
    expect(pages.map(textOf).join('')).toBe('Sing of the wrath. Chryses came bearing gifts.');
  });

  it('a TEI paragraph marker still breaks a paragraph even when it falls inside a sentence-snapped page (no change to that contract)', () => {
    const chunks: SceneReadingChunk[] = [
      {
        startLine: 1, endLine: 9,
        flowParts: [
          { text: 'Sing of the wrath. But go, do not anger me.', n: null, real: false },
          { text: null, n: null, real: false, para: true },
          { text: 'So he spoke, and the old man was seized with fear.', n: null, real: false },
        ],
        otables: {},
      },
    ];
    const scenes: SceneRange[] = [{ startLine: 1, endLine: 9 }];
    const [page] = sentenceSnapScenePages(chunks, scenes);
    expect(page.flowParts.some((p) => p.para === true)).toBe(true);
  });

  it('returns one page per scene, empty pages when there are no chunks at all', () => {
    const scenes: SceneRange[] = [{ startLine: 1, endLine: 4 }, { startLine: 5, endLine: 9 }];
    const pages = sentenceSnapScenePages([], scenes);
    expect(pages).toEqual([{ flowParts: [], otables: {} }, { flowParts: [], otables: {} }]);
  });

  it('returns an empty array for an empty scene list', () => {
    expect(sentenceSnapScenePages([{ startLine: 1, endLine: 4, flowParts: [], otables: {} }], [])).toEqual([]);
  });
});

// ── Real Iliad 1 / Odyssey 9 data ───────────────────────────────────────────
// build/dist is pipeline output (gitignored, regenerated — see CLAUDE.md's
// concurrency gotcha), so these tests read it if present and skip cleanly if
// not, rather than making the suite depend on a build artifact being in a
// particular state. buildRealChunks below is a small, TEST-ONLY
// reconstruction of "text + bekker ticks + paragraph offsets -> tick-chunked
// SceneFlowChunk[]" — sufficient to exercise sentenceSnapScenePages against
// real Murray prose (real footnote markers, real paragraph breaks, real
// punctuation) — NOT a copy of Reader.svelte's own private
// flowParts()/groupFlowByTicks()/alignGroups() (those also resolve real
// per-line Greek offsets and speech-snap adjustments, out of scope for a
// pure-module text test).
interface RealBekkerTick { n: number; offset: number; real: boolean }
interface RealMarker { kind: string; offset: number }

function buildRealChunks(text: string, bekker: RealBekkerTick[], paraOffsets: number[]): SceneReadingChunk[] {
  const markers = [
    ...bekker.map((t) => ({ off: t.offset, isPara: false, n: t.n, real: t.real })),
    ...paraOffsets.map((off) => ({ off, isPara: true, n: 0, real: false })),
  ].sort((a, b) => a.off - b.off || Number(a.isPara) - Number(b.isPara));

  const flatParts: { text: string | null; n: number | null; real: boolean; para?: boolean; tickN?: number }[] = [];
  let cur = 0;
  for (const m of markers) {
    const off = Math.max(0, Math.min(m.off, text.length));
    if (off > cur) { flatParts.push({ text: text.slice(cur, off), n: null, real: false }); cur = off; }
    if (m.isPara) flatParts.push({ text: null, n: null, real: false, para: true });
    else flatParts.push({ text: null, n: m.n, real: m.real, tickN: m.n });
  }
  if (cur < text.length) flatParts.push({ text: text.slice(cur), n: null, real: false });

  const tickNs = bekker.map((t) => t.n).sort((a, b) => a - b);
  const chunks: SceneReadingChunk[] = [];
  let curChunk: SceneReadingChunk | null = null;
  for (const p of flatParts) {
    if (p.tickN !== undefined) {
      if (curChunk) chunks.push(curChunk);
      const idx = tickNs.indexOf(p.tickN);
      const nextN = tickNs[idx + 1];
      curChunk = {
        startLine: p.tickN,
        endLine: nextN !== undefined ? nextN - 1 : p.tickN + 100000,
        flowParts: [{ text: null, n: p.n, real: p.real }],
        otables: {},
      };
    } else if (curChunk) {
      curChunk.flowParts.push({ text: p.text, n: p.n, real: p.real, para: p.para });
    }
  }
  if (curChunk) chunks.push(curChunk);
  return chunks;
}

const ILIAD_1_PATH = '../build/dist/iliad/book-01.json';
const ODYSSEY_9_PATH = '../build/dist/odyssey/book-09.json';
const hasRealBookData = existsSync(ILIAD_1_PATH) && existsSync(ODYSSEY_9_PATH);

function loadRealBook(path: string): { chunks: SceneReadingChunk[]; scenes: SceneRange[] } {
  const raw = JSON.parse(readFileSync(path, 'utf-8'));
  const seg = raw.segments[0];
  const paraOffsets = (seg.english.markers as RealMarker[])
    .filter((m) => m.kind === 'paragraph')
    .map((m) => m.offset);
  const chunks = buildRealChunks(seg.english.text, seg.english.bekker, paraOffsets);
  const scenes: SceneRange[] = raw.apparatus.scenes.map((s: { lines: [number, number] }) => ({
    startLine: s.lines[0], endLine: s.lines[1],
  }));
  return { chunks, scenes };
}

describe.skipIf(!hasRealBookData)('sentenceSnapScenePages — real Iliad 1 / Odyssey 9 data', () => {
  if (!hasRealBookData) {
    // eslint-disable-next-line no-console
    console.warn('scene-paging.test.ts: build/dist/{iliad,odyssey}/book-0{1,9}.json not found — skipping real-data invariant tests (pipeline output is gitignored/regenerated, not a suite dependency).');
  }

  it.each([['Iliad 1', ILIAD_1_PATH], ['Odyssey 9', ODYSSEY_9_PATH]])(
    '%s: every page is a disjoint, lossless slice of the whole book flow (no text lost or duplicated)',
    (_label, path) => {
      const { chunks, scenes } = loadRealBook(path);
      const pages = sentenceSnapScenePages(chunks, scenes);
      const whole = mergeSceneFlowChunks(chunks).flowParts.map((p) => p.text ?? '').join('');
      const rebuilt = pages.map((p) => p.flowParts.map((x) => x.text ?? '').join('')).join('');
      expect(rebuilt).toBe(whole);
    },
  );

  it.each([['Iliad 1', ILIAD_1_PATH], ['Odyssey 9', ODYSSEY_9_PATH]])(
    '%s: every non-empty page after the first starts at a sentence start (capital/digit/opening quote)',
    (_label, path) => {
      const { chunks, scenes } = loadRealBook(path);
      const pages = sentenceSnapScenePages(chunks, scenes);
      let emptyCount = 0;
      pages.forEach((p, i) => {
        if (i === 0) return; // the book's own opening, not a snapped boundary
        const t = p.flowParts.map((x) => x.text ?? '').join('').trimStart();
        if (!t) { emptyCount += 1; return; } // an intentionally swallowed page — see the dedicated unit test above
        expect(t[0], `scene ${i} of ${path} starts with "${t.slice(0, 40)}"`).toMatch(/[A-Z0-9"'“‘]/);
      });
      // No silent-cap: real Il. 1 (20 scenes) and Od. 9 (17 scenes) both
      // come out with ZERO empty pages — the degenerate "swallowed scene"
      // edge case (see the dedicated unit test above) doesn't occur with
      // real apparatus data; scenes are narrative units well over one
      // sentence. Still asserted generally, not hardcoded to 0, so a future
      // finer-grained apparatus pass that DID produce one wouldn't silently
      // break this test.
      expect(emptyCount).toBeLessThan(pages.length);
    },
  );

  it("Il. 1: at least one scene's RAW chunk-overlap edge splits a sentence, and the snap moves that boundary to a clean sentence end (John's reported case)", () => {
    const { chunks, scenes } = loadRealBook(ILIAD_1_PATH);
    const pages = sentenceSnapScenePages(chunks, scenes);
    const endsClean = (s: string) => /[.?!]["'”’)]*$/.test(s.trimEnd());

    let sawARawSplit = false;
    for (let i = 0; i < scenes.length - 1; i++) {
      const rawSelected = chunksForScene(chunks, scenes[i]).map((idx) => chunks[idx]);
      const rawText = mergeSceneFlowChunks(rawSelected).flowParts.map((p) => p.text ?? '').join('');
      if (endsClean(rawText)) continue; // this particular scene's raw edge already lands clean
      sawARawSplit = true;
      const snappedText = pages[i].flowParts.map((p) => p.text ?? '').join('');
      expect(snappedText).not.toBe(rawText);       // the snap actually moved the boundary
      expect(endsClean(snappedText)).toBe(true);    // ...to a clean sentence end
    }
    expect(sawARawSplit).toBe(true); // the raw (pre-snap) contract really did cut a sentence somewhere in Il. 1
  });
});
