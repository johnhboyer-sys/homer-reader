import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  chunksForScene,
  endAnchorChunkIndex,
  isHollowScenePage,
  mergeSceneFlowChunks,
  pageCharLength,
  sentenceEndOffsets,
  sentenceSnapScenePages,
  type SceneFlowChunk,
  type SceneFlowPart,
  type SceneReadingChunk,
  type SceneRange,
  type TickChunkRange,
} from '../lib/scene-paging';
import { buildRealChunks, loadRealBook, type RealMarker, type RealTranslation } from './real-book-loader';
import { auditScenePaging } from '../scripts/scene-paging-audit';

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

describe('endAnchorChunkIndex', () => {
  it('prefers the last fully-contained tick, not the last overlapping straddler', () => {
    // Scene ends at 32; tick 30–34 straddles into 33–34. Old snap used index 6
    // (the straddler); accurate end-anchor is the last fully inside (25–29 = 5).
    expect(endAnchorChunkIndex(chunks, { startLine: 8, endLine: 32 })).toBe(5);
    expect(chunksForScene(chunks, { startLine: 8, endLine: 32 }).at(-1)).toBe(6);
  });

  it('falls back to last overlapping when no tick is fully contained', () => {
    expect(endAnchorChunkIndex(chunks, { startLine: 11, endLine: 13 })).toBe(2);
  });
});

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

  it('hollow-page guardrail: a scene swallowed empty by the previous page falls back to raw tick-overlap prose', () => {
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

    // Scene 0 still extends to finish its sentence (may include c1 + leading space of c2).
    expect(page0).toBe(c0 + c1 + ' ');
    // Guardrail: scene 1 is no longer left empty — raw tick-overlap restores c1.
    // (Duplication with page0 is the known guardrail-only tradeoff.)
    expect(page1).toBe(c1);
    expect(page2).toBe(c2.slice(1));
  });

  it('isHollowScenePage: empty vs short-vs-raw ratio', () => {
    expect(isHollowScenePage(0, 400)).toBe(true);
    expect(isHollowScenePage(113, 500)).toBe(true); // Il. 1.3-shaped
    expect(isHollowScenePage(180, 200)).toBe(false); // snap ≈ raw, legitimately short
    expect(isHollowScenePage(500, 600)).toBe(false);
    expect(isHollowScenePage(0, 0)).toBe(false);
  });

  it('never ends a page mid-sentence when the only terminator is past the straddling tick', () => {
    // Scene A owns only the first half of a 5-line tick; English has no period
    // until the NEXT tick. Hard-capping at the tick edge would end on
    // "pause " — forbidden. Overflow to the real sentence end instead.
    const chunks: SceneReadingChunk[] = [
      {
        startLine: 1, endLine: 5,
        flowParts: [{ text: 'He walked along the shore without a pause ', n: null, real: false }],
        otables: {},
      },
      {
        startLine: 6, endLine: 10,
        flowParts: [{ text: 'until he reached the temple and stopped. ', n: null, real: false }],
        otables: {},
      },
      {
        startLine: 11, endLine: 15,
        flowParts: [{ text: 'Then Apollo answered him.', n: null, real: false }],
        otables: {},
      },
    ];
    const scenes: SceneRange[] = [
      { startLine: 1, endLine: 3 },
      { startLine: 4, endLine: 10 },
      { startLine: 11, endLine: 15 },
    ];
    const pages = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: false }).map(textOf);
    const endsClean = (s: string) => !s.trim() || /[.?!]["'”’)]*$/.test(s.trimEnd());

    expect(pages[0]).toMatch(/stopped\.\s*$/);
    expect(pages[0]).not.toMatch(/pause\s*$/);
    expect(endsClean(pages[0])).toBe(true);
    expect(endsClean(pages[1])).toBe(true);
    // Partition: no loss, no duplication.
    expect(pages.join('')).toBe(
      'He walked along the shore without a pause until he reached the temple and stopped. Then Apollo answered him.',
    );
  });

  // Regression (Codex Issue 1 / John 2026-07-21 audit): a short scene wholly
  // inside a single wide straddling tick, whose OWN cursor happens to land
  // exactly on the sentence end the PRECEDING scene chose (the common case —
  // every scene after the first starts exactly where sentence-snap left
  // off). Reproduces the real corpus defect (Od. 11 Butler scene 14, empty)
  // in miniature: the tick has three sentences (Beta, Gamma, Delta); the
  // preceding scene's correct natural end is Gamma (the nearest terminator
  // after its own start), but the pre-fix `lastInTick` fallback kept
  // overwriting through every candidate in range and returned the FARTHEST
  // one (Delta) instead of the nearest, swallowing the next scene's entire
  // 4-line share whole.
  it('a scene landing exactly on the previous cursor picks the NEAREST sentence end in its tick, not the farthest — the next (4-line) scene is not swallowed empty', () => {
    const chunk0Text = 'Prologue done.';
    const chunk1Text = ' Beta continues right after. Gamma marks a natural pause here. Delta wraps up far beyond.';
    const chunks: SceneReadingChunk[] = [
      { startLine: 1, endLine: 5, flowParts: [{ text: chunk0Text, n: null, real: false }], otables: {} },
      { startLine: 6, endLine: 60, flowParts: [{ text: chunk1Text, n: null, real: false }], otables: {} },
    ];
    const scenes: SceneRange[] = [
      { startLine: 1, endLine: 5 },   // wholly chunk0 — clean natural end at "Prologue done.".
      { startLine: 6, endLine: 8 },   // wholly inside chunk1, no fully-contained tick, and its
                                       // OWN cursor (15) lands exactly on chunk0's sentence end
                                       // — the "preceding scene" whose correct end is "Beta...".
      { startLine: 9, endLine: 12 },  // the 4-line scene — wholly inside the SAME tick, last
                                       // scene in the array (own end bypassed to book end).
    ];
    const [page1, page2, page3] = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: false }).map(textOf);

    expect(page1).toBe('Prologue done. ');
    expect(page2).toBe('Beta continues right after. ');
    expect(page2).not.toContain('Gamma');
    expect(page2).not.toContain('Delta');
    // The 4-line scene must not be swallowed empty by the preceding scene's
    // over-extension (the pre-fix `lastInTick` loop kept overwriting to the
    // FARTHEST sentence end in the tick — "Delta..." — instead of the
    // nearest, consuming Gamma AND Delta into scene 2 and leaving scene 3
    // with nothing), and must not carry a duplicate of the preceding
    // scene's own trailing sentence ("Beta...").
    expect(page3.trim()).not.toBe('');
    expect(page3).not.toContain('Beta continues right after.');
    expect(page3).toBe('Gamma marks a natural pause here. Delta wraps up far beyond.');
    // Partition: no loss, no duplication across all three pages.
    expect(page1 + page2 + page3).toBe(chunk0Text + chunk1Text);
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

// ── Real Iliad 1 / Odyssey {1,9} data ───────────────────────────────────────
// build/dist is pipeline output (gitignored, regenerated — see CLAUDE.md's
// concurrency gotcha), so these tests read it if present. The loader itself
// (buildRealChunks/loadRealBook — "text + bekker ticks + paragraph offsets ->
// tick-chunked SceneReadingChunk[]", NOT a copy of Reader.svelte's private
// flowParts()/groupFlowByTicks()/alignGroups()) lives in ./real-book-loader,
// shared with the corpus audit script.
//
// Because build/dist is gitignored, a committed fixture
// (./fixtures/scene-paging-books.json — trimmed, book-JSON-shaped, public-
// domain Murray/Butler excerpts) gives the invariant tests below something to
// run against even when the pipeline hasn't been built locally (e.g. CI).
// loadFixtureBook adapts a fixture entry into the same {chunks, scenes} shape
// loadRealBook returns, by calling buildRealChunks directly on the fixture's
// already-JSON-shaped english/ross/scenes fields.
const ILIAD_1_PATH = '../build/dist/iliad/book-01.json';
const ODYSSEY_1_PATH = '../build/dist/odyssey/book-01.json';
const ODYSSEY_9_PATH = '../build/dist/odyssey/book-09.json';
// Trigger books (John, 2026-07-21 audit): the exact "scene wholly inside one
// straddling tick, no fully-contained tick" condition the naturalEndOffset
// floor fix targets occurs (Butler only, in this corpus) at Il. 12 scene 16,
// Od. 17 scene 5, Od. 23 scene 9, and Od. 11 scenes 13-14 (1-indexed; the
// original Codex/Opus brief cited these 0-indexed). Added here so the real-
// data invariant suite below actually exercises the fixed code paths.
const ILIAD_12_PATH = '../build/dist/iliad/book-12.json';
const ODYSSEY_11_PATH = '../build/dist/odyssey/book-11.json';
const ODYSSEY_17_PATH = '../build/dist/odyssey/book-17.json';
const ODYSSEY_23_PATH = '../build/dist/odyssey/book-23.json';
const FIXTURE_PATH = './__tests__/fixtures/scene-paging-books.json';

interface FixtureBook {
  segments: [{
    english: { text: string; bekker: { n: number; offset: number; real: boolean }[]; markers: RealMarker[] };
    ross: [{ text: string; bekker: { n: number; offset: number; real: boolean }[] }];
  }];
  apparatus: { scenes: { lines: [number, number] }[] };
}

const fixtureRaw: Record<string, FixtureBook> | null = existsSync(FIXTURE_PATH)
  ? JSON.parse(readFileSync(FIXTURE_PATH, 'utf-8'))
  : null;

function loadFixtureBook(entry: string, translation: RealTranslation): { chunks: SceneReadingChunk[]; scenes: SceneRange[] } | null {
  const raw = fixtureRaw?.[entry];
  if (!raw) return null;
  const seg = raw.segments[0];
  let chunks: SceneReadingChunk[];
  if (translation === 'murray') {
    const paraOffsets = seg.english.markers.filter((m) => m.kind === 'paragraph').map((m) => m.offset);
    chunks = buildRealChunks(seg.english.text, seg.english.bekker, paraOffsets);
  } else {
    const piece = seg.ross[0];
    chunks = buildRealChunks(piece.text, piece.bekker, []);
  }
  const scenes: SceneRange[] = raw.apparatus.scenes.map((s) => ({ startLine: s.lines[0], endLine: s.lines[1] }));
  return { chunks, scenes };
}

// Every (label, translation, loader) combo the invariant tests below run
// against: real build/dist books (skipped individually if that file is
// absent) plus the two always-available fixture entries.
type BookCombo = { label: string; translation: RealTranslation; load: () => { chunks: SceneReadingChunk[]; scenes: SceneRange[] } | null };
const REAL_COMBOS: BookCombo[] = [
  { label: 'Iliad 1 (Murray)', translation: 'murray', load: () => loadRealBook(ILIAD_1_PATH, 'murray') },
  { label: 'Odyssey 9 (Murray)', translation: 'murray', load: () => loadRealBook(ODYSSEY_9_PATH, 'murray') },
  { label: 'Iliad 1 (Butler)', translation: 'butler', load: () => loadRealBook(ILIAD_1_PATH, 'butler') },
  { label: 'Odyssey 1 (Butler)', translation: 'butler', load: () => loadRealBook(ODYSSEY_1_PATH, 'butler') },
  { label: 'Odyssey 9 (Butler)', translation: 'butler', load: () => loadRealBook(ODYSSEY_9_PATH, 'butler') },
  // Trigger books (see ILIAD_12_PATH comment above) — real-data combos, both
  // translations each, skip-if-absent like every other REAL_COMBOS entry.
  { label: 'Iliad 12 (Murray)', translation: 'murray', load: () => loadRealBook(ILIAD_12_PATH, 'murray') },
  { label: 'Iliad 12 (Butler)', translation: 'butler', load: () => loadRealBook(ILIAD_12_PATH, 'butler') },
  { label: 'Odyssey 11 (Murray)', translation: 'murray', load: () => loadRealBook(ODYSSEY_11_PATH, 'murray') },
  { label: 'Odyssey 11 (Butler)', translation: 'butler', load: () => loadRealBook(ODYSSEY_11_PATH, 'butler') },
  { label: 'Odyssey 17 (Murray)', translation: 'murray', load: () => loadRealBook(ODYSSEY_17_PATH, 'murray') },
  { label: 'Odyssey 17 (Butler)', translation: 'butler', load: () => loadRealBook(ODYSSEY_17_PATH, 'butler') },
  { label: 'Odyssey 23 (Murray)', translation: 'murray', load: () => loadRealBook(ODYSSEY_23_PATH, 'murray') },
  { label: 'Odyssey 23 (Butler)', translation: 'butler', load: () => loadRealBook(ODYSSEY_23_PATH, 'butler') },
];
const FIXTURE_COMBOS: BookCombo[] = [
  { label: 'Iliad 1 fixture (Murray)', translation: 'murray', load: () => loadFixtureBook('iliad1', 'murray') },
  { label: 'Odyssey 9 fixture (Murray)', translation: 'murray', load: () => loadFixtureBook('odyssey9', 'murray') },
  { label: 'Iliad 1 fixture (Butler)', translation: 'butler', load: () => loadFixtureBook('iliad1', 'butler') },
  { label: 'Odyssey 9 fixture (Butler)', translation: 'butler', load: () => loadFixtureBook('odyssey9', 'butler') },
];
const ALL_COMBOS = [...REAL_COMBOS, ...FIXTURE_COMBOS];

const hasRealBookData = existsSync(ILIAD_1_PATH) && existsSync(ODYSSEY_9_PATH);

describe('sentenceSnapScenePages — real Iliad 1 / Odyssey 9 data', () => {
  it.each(ALL_COMBOS.map((c) => [c.label, c] as const))(
    '%s: pure snap (no guardrail) is a disjoint, lossless slice of the whole book flow',
    (_label, combo) => {
      const loaded = combo.load();
      if (!loaded) return; // real book source absent locally — not a suite dependency
      const { chunks, scenes } = loaded;
      const pages = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: false });
      const whole = mergeSceneFlowChunks(chunks).flowParts.map((p) => p.text ?? '').join('');
      const rebuilt = pages.map((p) => p.flowParts.map((x) => x.text ?? '').join('')).join('');
      expect(rebuilt).toBe(whole);
    },
  );

  it.each(ALL_COMBOS.map((c) => [c.label, c] as const))(
    '%s: pure snap non-empty pages after the first start at a sentence start',
    (_label, combo) => {
      const loaded = combo.load();
      if (!loaded) return;
      const { chunks, scenes } = loaded;
      const pages = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: false });
      let emptyCount = 0;
      pages.forEach((p, i) => {
        if (i === 0) return; // the book's own opening, not a snapped boundary
        const t = p.flowParts.map((x) => x.text ?? '').join('').trimStart();
        if (!t) { emptyCount += 1; return; }
        expect(t[0], `scene ${i} of ${_label} starts with "${t.slice(0, 40)}"`).toMatch(/[A-Z0-9"'“‘]/);
      });
      expect(emptyCount).toBeLessThan(pages.length);
    },
  );

  // Strict empty-page invariant (John, 2026-07-21): the naturalEndOffset
  // floor fix (see scene-paging.ts) exists precisely so a page never comes
  // out empty because an earlier scene's dangling-sentence search stole a
  // sentence end that belonged to a LATER scene, or overran past it. Unlike
  // the "starts at a sentence start" test above (which tolerates some empty
  // pages as an honest degenerate case per this module's own header comment),
  // this asserts STRICT ZERO empty non-first pages, guardrail off, across
  // every real-data combo — including the four trigger books added above.
  it.each(ALL_COMBOS.map((c) => [c.label, c] as const))(
    '%s: pure snap (no guardrail) never leaves a non-first page empty',
    (_label, combo) => {
      const loaded = combo.load();
      if (!loaded) return;
      const { chunks, scenes } = loaded;
      const pages = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: false });
      const emptyScenes: number[] = [];
      pages.forEach((p, i) => {
        if (i === 0) return; // the book's own opening, not a snapped boundary
        const t = p.flowParts.map((x) => x.text ?? '').join('').trim();
        if (!t) emptyScenes.push(i + 1);
      });
      expect(emptyScenes, `${_label}: empty page(s) at scene(s) ${emptyScenes.join(', ')}`).toEqual([]);
    },
  );

  it.each(ALL_COMBOS.map((c) => [c.label, c] as const))(
    '%s: pure snap (no guardrail) never ends a non-empty page mid-sentence',
    (_label, combo) => {
      const loaded = combo.load();
      if (!loaded) return;
      const { chunks, scenes } = loaded;
      const pages = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: false });
      const endsClean = (s: string) => !s.trim() || /[.?!]["'”’)]*$/.test(s.trimEnd());
      for (let i = 0; i < pages.length; i++) {
        const t = pages[i].flowParts.map((p) => p.text ?? '').join('');
        expect(endsClean(t), `${_label} scene ${i + 1} ends mid-sentence: "…${t.slice(-40)}"`).toBe(true);
      }
    },
  );

  it.each(ALL_COMBOS.map((c) => [c.label, c] as const))(
    '%s: every page\'s text overlaps its scene\'s owned tick range',
    (_label, combo) => {
      const loaded = combo.load();
      if (!loaded) return;
      const { chunks, scenes } = loaded;
      const pages = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: false });

      // Cumulative [start, end) interval each chunk contributes to the
      // concatenated whole-book flow, computed from each chunk's OWN
      // flowParts text length (the brief's "cumulative flowParts text
      // lengths" — a coarser, join-space-agnostic approximation of the
      // module's internal buildBookFlow, sufficient for an overlap check).
      const chunkStart: number[] = [];
      const chunkEnd: number[] = [];
      let cCursor = 0;
      for (const c of chunks) {
        chunkStart.push(cCursor);
        cCursor += pageCharLength({ flowParts: c.flowParts, otables: {} });
        chunkEnd.push(cCursor);
      }

      // Same cumulative-interval bookkeeping for the output pages, in the
      // same (pure-snap, guardrail-off) coordinate space.
      const pageStart: number[] = [];
      const pageEnd: number[] = [];
      let pCursor = 0;
      for (const p of pages) {
        pageStart.push(pCursor);
        pCursor += pageCharLength(p);
        pageEnd.push(pCursor);
      }

      const violations: string[] = [];
      for (let i = 0; i < pages.length; i++) {
        if (pageCharLength(pages[i]) <= 0) continue; // empty pages have no interval to check
        const selected = chunksForScene(chunks, scenes[i]);
        if (!selected.length) continue;
        const unionStart = Math.min(...selected.map((idx) => chunkStart[idx]));
        const unionEnd = Math.max(...selected.map((idx) => chunkEnd[idx]));
        const overlaps = pageStart[i] < unionEnd && pageEnd[i] > unionStart;
        if (!overlaps) {
          violations.push(`scene ${i + 1}: page [${pageStart[i]}, ${pageEnd[i]}) vs owned tick union [${unionStart}, ${unionEnd})`);
        }
      }
      expect(violations, `${_label}: ${violations.join('; ')}`).toEqual([]);
    },
  );

  it("Il. 1: at least one scene's RAW chunk-overlap edge splits a sentence, and pure snap moves that boundary to a clean sentence end", () => {
    const loaded = loadRealBook(ILIAD_1_PATH, 'murray');
    if (!loaded) return;
    const { chunks, scenes } = loaded;
    const pages = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: false });
    const endsClean = (s: string) => /[.?!]["'”’)]*$/.test(s.trimEnd());

    let sawARawSplit = false;
    for (let i = 0; i < scenes.length - 1; i++) {
      const rawSelected = chunksForScene(chunks, scenes[i]).map((idx) => chunks[idx]);
      const rawText = mergeSceneFlowChunks(rawSelected).flowParts.map((p) => p.text ?? '').join('');
      if (endsClean(rawText)) continue;
      sawARawSplit = true;
      const snappedText = pages[i].flowParts.map((p) => p.text ?? '').join('');
      expect(snappedText).not.toBe(rawText);
      expect(endsClean(snappedText)).toBe(true);
    }
    expect(sawARawSplit).toBe(true);
  });

  it.skipIf(!hasRealBookData)('Il. 1 scenes 2–4 (default path = what the live reader uses): prayer on scene 3', () => {
    const { chunks, scenes } = loadRealBook(ILIAD_1_PATH, 'murray')!;
    expect(scenes[1]?.endLine).toBe(32);
    expect(scenes[2]?.startLine).toBe(33);
    expect(scenes[2]?.endLine).toBe(42);

    // Default options (hollow guardrail ON) — same call shape as Reader.svelte.
    const pages = sentenceSnapScenePages(chunks, scenes);
    const s2 = pages[1].flowParts.map((p) => p.text ?? '').join('');
    const s3 = pages[2].flowParts.map((p) => p.text ?? '').join('');
    const s4 = pages[3].flowParts.map((p) => p.text ?? '').join('');
    const endsClean = (s: string) => !s.trim() || /[.?!]["'”’)]*$/.test(s.trimEnd());

    // Scene 2 ends with Agamemnon's dismissal, not the prayer.
    expect(s2).toMatch(/return the safer\./);
    expect(s2).not.toMatch(/silver bow/);
    expect(s2).not.toMatch(/Down from the peaks of Olympus/);
    expect(endsClean(s2)).toBe(true);

    // Scene 3 owns Chryses' reaction + prayer; not the Agamemnon lead-in, not descent.
    expect(s3).toMatch(/So he spoke, and the old man was seized with fear/);
    expect(s3).toMatch(/silver bow/);
    expect(s3).toMatch(/Phoebus Apollo heard him/);
    expect(s3).not.toMatch(/as she walks to and fro before the loom/);
    expect(s3).not.toMatch(/Down from the peaks of Olympus/);
    expect(endsClean(s3)).toBe(true);

    // Scene 4 starts the descent.
    expect(s4).toMatch(/Down from the peaks of Olympus|arrows rattled/i);
    expect(endsClean(s4)).toBe(true);
  });

  it.skipIf(!hasRealBookData)('Il. 1 default path: every non-empty page ends on a sentence boundary', () => {
    const { chunks, scenes } = loadRealBook(ILIAD_1_PATH, 'murray')!;
    const pages = sentenceSnapScenePages(chunks, scenes);
    const endsClean = (s: string) => !s.trim() || /[.?!]["'”’)]*$/.test(s.trimEnd());
    for (let i = 0; i < pages.length; i++) {
      const t = pages[i].flowParts.map((p) => p.text ?? '').join('');
      expect(endsClean(t), `scene ${i + 1} ends mid-sentence: "…${t.slice(-40)}"`).toBe(true);
    }
  });
});

// ── Corpus audit gate (John, 2026-07-21) ────────────────────────────────────
// The full 96-book (24 books x 2 epics x 2 translations) corpus audit
// (auditScenePaging, shared/scripts/scene-paging-audit.ts) is what turns the
// manual audit run into an actual vitest gate. Skips (like every other
// real-data suite above) when build/dist isn't present locally — it's
// gitignored pipeline output, not a suite dependency (see CLAUDE.md's
// concurrency gotcha). Computed ONCE at describe-body eval time and reused
// across every assertion below, rather than re-running the 96-book sweep per
// `it` — auditScenePaging is not cheap enough to call repeatedly.
const AUDIT_DIST_ROOT = '../build/dist';
const hasAuditDistRoot = existsSync(AUDIT_DIST_ROOT);

describe('scene-paging corpus audit gate (real build/dist data)', () => {
  const result = hasAuditDistRoot ? auditScenePaging(AUDIT_DIST_ROOT) : null;

  it.skipIf(!hasAuditDistRoot)('build/dist audit report is present and covers the full corpus', () => {
    expect(result?.buildDistPresent).toBe(true);
    if (result?.buildDistPresent) {
      expect(result.totals.booksMissing).toBe(0);
    }
  });

  it.skipIf(!hasAuditDistRoot)('gate passes: zero empty, zero mid-sentence, zero out-of-owned-range pages', () => {
    if (!result?.buildDistPresent) return;
    expect(result.totals.emptyPagesPureSnap).toBe(0);
    expect(result.totals.midSentenceEndsPureSnap).toBe(0);
    expect(result.totals.outOfOwnedRangePages).toBe(0);
  });

  it.skipIf(!hasAuditDistRoot)('gate passes: guardrail-caused duplication stays within the gate max', () => {
    if (!result?.buildDistPresent) return;
    expect(result.totals.duplicatedTextPages).toBeLessThanOrEqual(result.gate.maxDuplicatedTextPages);
  });

  it.skipIf(!hasAuditDistRoot)('overall gate.pass is true', () => {
    if (!result?.buildDistPresent) return;
    expect(result.gate.pass).toBe(true);
  });
});
