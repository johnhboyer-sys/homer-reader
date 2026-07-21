import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  chunksForScene,
  endAnchorChunkIndex,
  isHollowScenePage,
  mergeSceneFlowChunks,
  naturalEndOffset,
  pageCharLength,
  resolveBoundaryOverrides,
  selectBoundaryOverrideEntries,
  sentenceEndOffsets,
  sentenceSnapScenePages,
  type SceneBoundaryOverrideFile,
  type SceneFlowChunk,
  type SceneFlowPart,
  type SceneReadingChunk,
  type SceneRange,
  type TickChunkRange,
} from '../lib/scene-paging';
import { alignGroups } from '../lib/tick-chunks';
import { buildRealChunks, loadRealBoundaryOverrides, loadRealBook, type RealMarker, type RealTranslation } from './real-book-loader';
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

// ── alignGroups speech-snap line resolution hardening (Codex re-review, ────
// 2026-07-21). tick-chunks.ts's alignGroups resolves a (possibly speech-
// snapped) tick's target Greek line NUMBER to an array INDEX via `lineIndex`.
// The line it replaces defaulted a missing line straight to `?? 0`/`??
// lines.length` — for a declared vulgate gap (manifests/*.yaml
// expected_line_gaps; real case: Od. 10.456, where Circe's speech honestly
// opens on the dropped line) that restarted the chunk at the TOP of the book,
// collapsing every scene after it (the live Odyssey 10 Reader bug this fixes).
// alignGroups now resolves forward to the nearest EXTANT line, falling back
// to the tick's own pre-snap anchor when even that fails (target past the
// end of the book).
describe('alignGroups — speech-snap line resolution hardening (Codex re-review, 2026-07-21)', () => {
  const tick = (n: number): SceneFlowPart => ({ text: null, n, real: true });
  const text = (s: string): SceneFlowPart => ({ text: s, n: null, real: false });

  it('Od. 10 shape: a speech start snapped onto the declared vulgate-gap line (456) resolves forward to 457, never restarting at index 0', () => {
    // Lines 450-460 with 456 missing — mirrors Od. 10 (has 455 and 457, not
    // 456). A tick anchored at 455 is within the snap window of speech start
    // 456 (Circe's speech), so it snaps there even though 456 doesn't exist.
    const lines = [450, 451, 452, 453, 454, 455, 457, 458, 459, 460].map((n) => ({ n }));
    const flow: SceneFlowPart[] = [
      tick(450), text('A'),
      tick(455), text('B'),
      tick(460), text('C'),
    ];
    const groups = alignGroups(lines, flow, [456]);
    const nonEmpty = groups.filter((g) => g.lines.length > 0);
    const startLines = nonEmpty.map((g) => g.lines[0].n);
    // No index-0 restart: the snapped group starts at 457 (nearest extant
    // line >= 456), so every group's own start line strictly increases.
    expect(startLines).toEqual([450, 457, 460]);
    for (let i = 1; i < startLines.length; i++) {
      expect(startLines[i]).toBeGreaterThan(startLines[i - 1]);
    }
  });

  it("Codex's synthetic case: ticks [1,5,10] with Greek line 6 absent and a speech start at 6 produce no equal-start or overlapping chunks", () => {
    const lines = [1, 2, 3, 4, 5, 7, 8, 9, 10].map((n) => ({ n }));
    const flow: SceneFlowPart[] = [
      tick(1), text('A'),
      tick(5), text('B'),
      tick(10), text('C'),
    ];
    const groups = alignGroups(lines, flow, [6]);
    const nonEmpty = groups.filter((g) => g.lines.length > 0);
    expect(nonEmpty.map((g) => g.lines[0].n)).toEqual([1, 7, 10]);
    for (let i = 1; i < nonEmpty.length; i++) {
      const prevEnd = nonEmpty[i - 1].lines.at(-1)!.n;
      const curStart = nonEmpty[i].lines[0].n;
      // Strictly past the previous chunk's own last line — neither an equal
      // start (a restart-to-the-same-index duplicate) nor an overlap.
      expect(curStart).toBeGreaterThan(prevEnd);
    }
  });

  it('a snap target past the end of the book skips the snap for that tick, falling back to its own pre-snap anchor rather than index 0', () => {
    // Tick at line 9 is within the snap window of speech start 11 (9 < 11 <=
    // 11), but this book's Greek ends at line 10 — no line exists at or past
    // 11, so the snap is skipped in favor of the tick's own anchor (9).
    const lines = Array.from({ length: 10 }, (_, i) => ({ n: i + 1 }));
    const flow: SceneFlowPart[] = [
      tick(1), text('A'),
      tick(9), text('B'),
    ];
    const groups = alignGroups(lines, flow, [11]);
    expect(groups).toHaveLength(2);
    // Contiguous at line 9 (the pre-snap anchor), not restarted at index 0
    // and not the whole book swallowed into one group via `?? lines.length`.
    expect(groups[0].lines.at(-1)!.n).toBe(8);
    expect(groups[1].lines[0].n).toBe(9);
    expect(groups.reduce((a, g) => a + g.lines.length, 0)).toBe(lines.length);
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

  // Codex review F2a, 2026-07-21: a page holding the COMPLETE prose of a short
  // owned share is short-but-complete, NOT hollow — the guardrail must leave it
  // exactly as sentence-snap cut it, never padded with a neighbor's prose. Here
  // scene 2 owns only a tiny share of a wide straddling tick, so its snapped
  // page ("Bee. ") is far shorter than the whole-tick backup (would flag hollow
  // by the ratio), yet it already contains its entire owned sentence — the
  // guardrail's bounded backup equals the page, so replacement is skipped.
  it('guardrail leaves a short-but-complete page unpadded (bounded backup == page ⇒ skip)', () => {
    const chunks: SceneReadingChunk[] = [
      { startLine: 1, endLine: 5, flowParts: [{ text: 'Alpha alpha alpha alpha alpha alpha alpha alpha alpha alpha alpha alpha.', n: null, real: false }], otables: {} },
      { startLine: 6, endLine: 60, flowParts: [{ text: ' Bee. Charlie charlie charlie charlie charlie charlie charlie charlie charlie charlie charlie charlie charlie charlie charlie charlie.', n: null, real: false }], otables: {} },
    ];
    const scenes: SceneRange[] = [
      { startLine: 1, endLine: 5 },
      { startLine: 6, endLine: 8 },   // tiny owned share of the wide tick
      { startLine: 9, endLine: 60 },
    ];
    const off = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: false }).map(textOf);
    const on = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: true }).map(textOf);
    // Scene 2's snapped page is its complete owned sentence, kept verbatim — the
    // guardrail did NOT pad it with chunk 1's "Charlie…" run.
    expect(off[1]).toBe('Bee. ');
    expect(on[1]).toBe('Bee. ');
    expect(on[1]).not.toContain('Charlie');
  });

  // Codex review F2c, 2026-07-21: John approved bounded guardrail duplication as
  // the honest floor for a scene sentence-snap swallowed empty. This pins that
  // (a) the fill duplicates ONLY the ADJACENT page (its own overlapping tick can
  // straddle a neighbor, never reach further), and (b) the audit's
  // duplicatedTextPages window logic catches exactly the filled page.
  it('guardrail duplication is bounded to an adjacent page, and the audit dup metric catches it', () => {
    const c0 = 'Aaaa aaaa aaaa aaaa aaaa aaaa aaaa aaaa aaaa aaaa aaaa aaaa aaaa.';
    const c1 = ' Short one here now. ' + 'w'.repeat(120) + ' finally ends here at last today.';
    const chunks: SceneReadingChunk[] = [
      { startLine: 1, endLine: 5, flowParts: [{ text: c0, n: null, real: false }], otables: {} },
      { startLine: 6, endLine: 60, flowParts: [{ text: c1, n: null, real: false }], otables: {} },
    ];
    const scenes: SceneRange[] = [
      { startLine: 1, endLine: 5 },
      { startLine: 6, endLine: 9 },    // short owned share
      { startLine: 10, endLine: 60 },  // its long sentence is completed onto scene 2, leaving scene 3 empty
    ];
    const off = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: false }).map(textOf);
    const on = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: true }).map(textOf);

    // Scene 3 is empty under pure snap (its share was completed onto scene 2)…
    expect(off[2].trim()).toBe('');
    // …and the guardrail fills it rather than showing a blank card.
    expect(on[2].trim()).not.toBe('');

    // The fill duplicates the ADJACENT page (scene 2) — a >=40-char shared run —
    // but shares NOTHING with the non-adjacent page 0: the duplication is bounded.
    const has40Overlap = (a: string, b: string) => {
      for (let i = 0; i + 40 <= a.length; i++) if (b.includes(a.slice(i, i + 40))) return true;
      return false;
    };
    expect(has40Overlap(on[2], on[1])).toBe(true);   // duplicates the neighbor
    expect(has40Overlap(on[2], on[0])).toBe(false);  // never the non-adjacent page

    // The audit's duplicatedTextPages logic (guardrail fired here AND a >=40-char
    // run is shared with an adjacent page) flags exactly this page.
    const auditFlags = (i: number) => {
      if (on[i] === off[i] || on[i].trim() === '' || on[i].length < 40) return false;
      return [i - 1, i + 1].some((j) => j >= 0 && j < on.length && on[j].length >= 40 && has40Overlap(on[i], on[j]));
    };
    expect(auditFlags(2)).toBe(true);
    expect(auditFlags(0)).toBe(false); // untouched page is never blamed
  });

  // Codex review F4 decision, 2026-07-21: naturalEndOffset's dangling-sentence
  // branch correctly gates on `after > cursor` (the code was right; only its
  // comment was fixed). When `floor` (the owned share's lower bound, here 100 >
  // cursor 50) is ITSELF a clean sentence end — a fully-owned tick ended exactly
  // there — the natural end is `floor`, NOT the next sentence end past it: the
  // scene must STOP at its clean owned boundary, never over-extend into the
  // straddling tick's later-scene share. Synthetic: chunk 0 fully owned
  // (chunkTextEnd 100, a terminator AT 100 ⇒ floor 100), chunk 1 straddles with
  // its next terminator only at 160. A hypothetical `after > floor` would return
  // 160 (swallowing the neighbor); the correct `after > cursor` returns 100.
  it('naturalEndOffset: when `floor` (> cursor) is itself a clean sentence end, the scene stops there, not at the next end', () => {
    const chunks: TickChunkRange[] = [
      { startLine: 1, endLine: 5 },
      { startLine: 6, endLine: 10 }, // straddles scene (endLine 10 > scene.endLine 8)
    ];
    const scene: SceneRange = { startLine: 3, endLine: 8 };
    expect(naturalEndOffset(chunks, scene, [100, 200], [100, 160], 50)).toBe(100);
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
// concurrency gotcha), so these tests read it if present. The loader
// (buildRealChunks/loadRealBook) lives in ./real-book-loader, shared with the
// corpus audit script, and since Codex review F1 (2026-07-21) it builds chunks
// through the SAME extracted production path Reader.svelte renders —
// flowParts → alignGroups(seg.greek, flow, bookSpeechStarts) from
// shared/lib/tick-chunks.ts — so the tested geometry IS the rendered geometry.
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
// Odyssey 10 (Murray) — the book whose Circe speech honestly opens on the
// declared vulgate-gap line 456 (see tick-chunks.ts's alignGroups). Added to
// the real-data combo matrix so its 12 recovered scenes are directly
// exercised by every invariant below, post the speech-snap hardening fix.
const ODYSSEY_10_PATH = '../build/dist/odyssey/book-10.json';
const FIXTURE_PATH = './__tests__/fixtures/scene-paging-books.json';

interface FixtureBook {
  segments: [{
    greek: { n: number }[];
    english: { text: string; bekker: { n: number; offset: number; real: boolean }[]; markers: RealMarker[] };
    ross: [{ text: string; bekker: { n: number; offset: number; real: boolean }[] }];
    // Pope (curated scene-boundary ticks) — present on iliad1/odyssey9 only;
    // optional so any future fixture entry without it still type-checks.
    third?: [{ text: string; bekker: { n: number; offset: number; real: boolean }[] }];
  }];
  // Speech-opening lines in this book (the fixture's own bookSpeechStarts) —
  // fed to buildRealChunks so the fixture runs the SAME production
  // flowParts→alignGroups→snapTicksToSpeechStarts path as real build/dist data
  // (Codex review F1/F5, 2026-07-21). See the fixture's `_provenance`.
  speechStarts: number[];
  apparatus: { scenes: { lines: [number, number] }[] };
}

// The fixture carries a top-level `_provenance` (see F5) alongside the book
// entries — keep it out of the book-keyed lookup.
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
    chunks = buildRealChunks(seg.english.text, seg.english.bekker, paraOffsets, seg.greek, raw.speechStarts);
  } else if (translation === 'butler') {
    const piece = seg.ross[0];
    chunks = buildRealChunks(piece.text, piece.bekker, [], seg.greek, raw.speechStarts);
  } else {
    // pope: curated ticks are exact anchors — [] speechStarts, same as
    // loadRealBook's pope branch (see real-book-loader.ts).
    const piece = seg.third?.[0];
    if (!piece) return null;
    chunks = buildRealChunks(piece.text, piece.bekker, [], seg.greek, []);
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
  // Odyssey 10 (Murray) — post-fix, its 12 scenes must pass every invariant
  // below exactly like any other book (see ODYSSEY_10_PATH comment above).
  { label: 'Odyssey 10 (Murray)', translation: 'murray', load: () => loadRealBook(ODYSSEY_10_PATH, 'murray') },
  // Pope (curated scene-boundary ticks — T3, 2026-07-21): same trigger books
  // as the Butler/Murray combos above, skip-if-absent like every other
  // REAL_COMBOS entry (build/dist's Pope carries one book-level tick until
  // the pipeline lane re-emits — see this lane's report).
  { label: 'Iliad 1 (Pope)', translation: 'pope', load: () => loadRealBook(ILIAD_1_PATH, 'pope') },
  { label: 'Iliad 12 (Pope)', translation: 'pope', load: () => loadRealBook(ILIAD_12_PATH, 'pope') },
  { label: 'Odyssey 9 (Pope)', translation: 'pope', load: () => loadRealBook(ODYSSEY_9_PATH, 'pope') },
  { label: 'Odyssey 11 (Pope)', translation: 'pope', load: () => loadRealBook(ODYSSEY_11_PATH, 'pope') },
];
const FIXTURE_COMBOS: BookCombo[] = [
  { label: 'Iliad 1 fixture (Murray)', translation: 'murray', load: () => loadFixtureBook('iliad1', 'murray') },
  { label: 'Odyssey 9 fixture (Murray)', translation: 'murray', load: () => loadFixtureBook('odyssey9', 'murray') },
  { label: 'Iliad 1 fixture (Butler)', translation: 'butler', load: () => loadFixtureBook('iliad1', 'butler') },
  { label: 'Odyssey 9 fixture (Butler)', translation: 'butler', load: () => loadFixtureBook('odyssey9', 'butler') },
  { label: 'Iliad 1 fixture (Pope)', translation: 'pope', load: () => loadFixtureBook('iliad1', 'pope') },
  { label: 'Odyssey 9 fixture (Pope)', translation: 'pope', load: () => loadFixtureBook('odyssey9', 'pope') },
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

    // Default options (hollow guardrail ON) — same call shape as Reader.svelte,
    // INCLUDING the speech-snapped tick geometry (Codex review F1, 2026-07-21):
    // this loader now runs the SAME flowParts→alignGroups→snapTicksToSpeechStarts
    // path the component renders (Il. 1 speeches at 17/26/37 snap ticks 15→17,
    // 25→26, 35→37), so these assertions pin the TRUE live-reader boundary. The
    // pre-F1 audit geometry (no speech-snap) ended scene 2 one line later, at
    // "…return the safer." — that contradicted production and is what F1 fixed.
    const pages = sentenceSnapScenePages(chunks, scenes);
    const s2 = pages[1].flowParts.map((p) => p.text ?? '').join('');
    const s3 = pages[2].flowParts.map((p) => p.text ?? '').join('');
    const s4 = pages[3].flowParts.map((p) => p.text ?? '').join('');
    const endsClean = (s: string) => !s.trim() || /[.?!]["'”’)]*$/.test(s.trimEnd());

    // Scene 2 ends with Agamemnon's refusal to release the girl ("…serves my
    // bed.", ~line 31), not the prayer or the descent.
    expect(s2).toMatch(/serves my bed\.\s*$/);
    expect(s2).not.toMatch(/silver bow/);
    expect(s2).not.toMatch(/Down from the peaks of Olympus/);
    expect(endsClean(s2)).toBe(true);

    // Scene 3 owns Chryses' reaction + prayer to Apollo; not the descent.
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
// The full 144-book (24 books x 2 epics x 3 translations) corpus audit
// (auditScenePaging, shared/scripts/scene-paging-audit.ts) is what turns the
// manual audit run into an actual vitest gate. Skips (like every other
// real-data suite above) when build/dist isn't present locally — it's
// gitignored pipeline output, not a suite dependency (see CLAUDE.md's
// concurrency gotcha). Computed ONCE at describe-body eval time and reused
// across every assertion below, rather than re-running the 144-book sweep per
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

  it.skipIf(!hasAuditDistRoot)('gate passes over well-formed books: zero empty, zero mid-sentence, zero out-of-owned-range, zero partition-loss', () => {
    if (!result?.buildDistPresent) return;
    // Gate sums are over WELL-FORMED books only (see below) — scene-paging's own
    // contract, not upstream data corruption.
    expect(result.gate.emptyPagesPureSnap).toBe(0);
    expect(result.gate.midSentenceEndsPureSnap).toBe(0);
    expect(result.gate.outOfOwnedRangePages).toBe(0);
    expect(result.gate.partitionLosslessFailures).toBe(0);
  });

  it.skipIf(!hasAuditDistRoot)('gate passes: guardrail-caused duplication stays within the gate max', () => {
    if (!result?.buildDistPresent) return;
    expect(result.gate.duplicatedTextPages).toBeLessThanOrEqual(result.gate.maxDuplicatedTextPages);
  });

  // The known Odyssey 10 (Murray) upstream tick-chunk corruption (Codex review
  // F1 diagnosis, 2026-07-21: a real Circe speech opens on the declared
  // vulgate-gap line 456, which snapTicksToSpeechStarts legitimately hands
  // back, and alignGroups' pre-fix `?? 0` fallback restarted the chunk at
  // line 1) is now FIXED at the source (tick-chunks.ts's alignGroups resolves
  // forward to the nearest extant line — see the "alignGroups — speech-snap
  // line resolution hardening" describe block above). This is asserted as an
  // EMPTY set, not removed, so the mechanism itself stays a live tripwire: if
  // any book's tick-chunk geometry ever corrupts again (backward/duplicate
  // startLine, an overlap, or an inverted chunk — see
  // scene-paging-audit.ts's chunkGeometryValid), this assertion is what fails
  // and forces a fresh diagnosis.
  it.skipIf(!hasAuditDistRoot)('no book has corrupt tick-chunk geometry (Odyssey 10 Murray fixed by the speech-snap hardening)', () => {
    if (!result?.buildDistPresent) return;
    expect(result.totals.corruptChunkBooks).toEqual([]);
    expect(result.gate.excludedCorruptBooks).toBe(0);
    expect(result.totals.booksAudited).toBe(144);
  });

  it.skipIf(!hasAuditDistRoot)('ownership floor: no well-formed book page falls below the minOwnershipFraction regression floor', () => {
    if (!result?.buildDistPresent) return;
    expect(result.gate.belowMinOwnershipPages).toBe(0);
    expect(result.gate.minOwnershipFraction).toBeGreaterThan(0);
  });

  it.skipIf(!hasAuditDistRoot)('overall gate.pass is true', () => {
    if (!result?.buildDistPresent) return;
    expect(result.gate.pass).toBe(true);
  });

  it.skipIf(!hasAuditDistRoot)('manual scene-boundary overrides all resolve cleanly (no anchor-resolution gate failures)', () => {
    if (!result?.buildDistPresent) return;
    expect(result.totals.overrideErrors).toEqual([]);
    expect(result.gate.overrideResolutionFailures).toBe(0);
  });
});

// ── Manual scene-boundary overrides (John, 2026-07-21 review) ──────────────
// John's editorial corrections to the algorithmic boundaries — see
// shared/lib/scene-boundary-overrides.json's `_source`/`_semantics` header and
// shared/lib/scene-paging.ts's resolveBoundaryOverrides doc. Every case below
// asserts (a) the overridden scene's page starts with its startAnchor
// verbatim, and (b) the preceding pages' text ends EXACTLY there (no gap, no
// overlap) — i.e. the override actually moved the cut, not just added text.
const ILIAD_8_PATH = '../build/dist/iliad/book-08.json';
const ODYSSEY_21_PATH = '../build/dist/odyssey/book-21.json';
const OVERRIDES_JSON_PATH = './lib/scene-boundary-overrides.json';
const overridesFileRaw: SceneBoundaryOverrideFile | null = existsSync(OVERRIDES_JSON_PATH)
  ? JSON.parse(readFileSync(OVERRIDES_JSON_PATH, 'utf-8'))
  : null;

function pageTextOf(page: SceneFlowChunk): string {
  return page.flowParts.map((p) => p.text ?? '').join('');
}

interface OverrideCase {
  label: string;
  path: string;
  translation: RealTranslation;
  work: string;
  book: number;
  sceneNumber: number; // 1-based
}

const OVERRIDE_CASES: OverrideCase[] = [
  { label: 'Iliad 8 (Murray) scene 17', path: ILIAD_8_PATH, translation: 'murray', work: 'iliad', book: 8, sceneNumber: 17 },
  { label: 'Odyssey 11 (Murray) scene 13', path: ODYSSEY_11_PATH, translation: 'murray', work: 'odyssey', book: 11, sceneNumber: 13 },
  { label: 'Odyssey 11 (Murray) scene 14', path: ODYSSEY_11_PATH, translation: 'murray', work: 'odyssey', book: 11, sceneNumber: 14 },
  { label: 'Odyssey 11 (Butler) scene 13', path: ODYSSEY_11_PATH, translation: 'butler', work: 'odyssey', book: 11, sceneNumber: 13 },
  { label: 'Odyssey 11 (Butler) scene 14', path: ODYSSEY_11_PATH, translation: 'butler', work: 'odyssey', book: 11, sceneNumber: 14 },
  { label: 'Odyssey 21 (Butler) scene 3', path: ODYSSEY_21_PATH, translation: 'butler', work: 'odyssey', book: 21, sceneNumber: 3 },
  { label: 'Odyssey 21 (Butler) scene 10', path: ODYSSEY_21_PATH, translation: 'butler', work: 'odyssey', book: 21, sceneNumber: 10 },
  { label: 'Odyssey 21 (Murray) scene 10', path: ODYSSEY_21_PATH, translation: 'murray', work: 'odyssey', book: 21, sceneNumber: 10 },
];

describe('manual scene-boundary overrides (John, 2026-07-21)', () => {
  it('scene-boundary-overrides.json carries exactly these 8 entries, one per case above', () => {
    if (!overridesFileRaw) return; // file always exists in-repo, but honor the skip-if-absent convention
    expect(overridesFileRaw.overrides).toHaveLength(8);
    for (const c of OVERRIDE_CASES) {
      const entries = selectBoundaryOverrideEntries(overridesFileRaw, c.work, c.book, c.translation);
      expect(entries.map((e) => e.sceneNumber), c.label).toContain(c.sceneNumber);
    }
  });

  it.each(OVERRIDE_CASES.map((c) => [c.label, c] as const))(
    '%s: overridden page starts with its startAnchor, and the preceding text ends exactly there',
    (_label, c) => {
      const loaded = loadRealBook(c.path, c.translation);
      if (!loaded) return; // real book source absent locally — not a suite dependency
      const { chunks, scenes } = loaded;
      const boundaryOverrides = loadRealBoundaryOverrides(c.work, c.book, c.translation, chunks, scenes);
      expect(boundaryOverrides.length, c.label).toBeGreaterThan(0);
      const pages = sentenceSnapScenePages(chunks, scenes, { boundaryOverrides });
      const whole = mergeSceneFlowChunks(chunks).flowParts.map((p) => p.text ?? '').join('');

      const sceneIndex = c.sceneNumber - 1;
      const cumBefore = pages.slice(0, sceneIndex).reduce((n, p) => n + pageCharLength(p), 0);
      const anchorEntry = selectBoundaryOverrideEntries(overridesFileRaw!, c.work, c.book, c.translation)
        .find((e) => e.sceneNumber === c.sceneNumber)!;

      // Previous pages, concatenated, stop EXACTLY where the anchor begins.
      expect(whole.slice(cumBefore, cumBefore + anchorEntry.startAnchor.length), c.label).toBe(anchorEntry.startAnchor);
      // The overridden page itself opens with the anchor, verbatim.
      expect(pageTextOf(pages[sceneIndex]).startsWith(anchorEntry.startAnchor), c.label).toBe(true);
    },
  );

  it('Iliad 8 (Murray) scene 16 is sunset-sentence-only (no longer includes "Then did glorious Hector…")', () => {
    const loaded = loadRealBook(ILIAD_8_PATH, 'murray');
    if (!loaded) return;
    const { chunks, scenes } = loaded;
    const boundaryOverrides = loadRealBoundaryOverrides('iliad', 8, 'murray', chunks, scenes);
    const pages = sentenceSnapScenePages(chunks, scenes, { boundaryOverrides });
    const scene16Text = pageTextOf(pages[15]).trim(); // scene 16 is index 15
    expect(scene16Text).toBe(
      'Then into Oceanus fell the bright light of the sun drawing black night over the face of the earth, '
      + 'the giver of grain. Sorely against the will of the Trojans sank the daylight, but over the Achaeans '
      + 'welcome, aye, thrice-prayed-for, came the darkness of night.',
    );
    expect(scene16Text).not.toContain('Then did glorious Hector');
  });

  it('Odyssey 21 (Butler) scene 2 ends at the bearing-posts sentence (not the suitors’ speech)', () => {
    const loaded = loadRealBook(ODYSSEY_21_PATH, 'butler');
    if (!loaded) return;
    const { chunks, scenes } = loaded;
    const boundaryOverrides = loadRealBoundaryOverrides('odyssey', 21, 'butler', chunks, scenes);
    const pages = sentenceSnapScenePages(chunks, scenes, { boundaryOverrides });
    const scene2Text = pageTextOf(pages[1]).trim(); // scene 2 is index 1
    expect(scene2Text.endsWith(
      'When she reached the suitors, she stood by one of the bearing-posts supporting the roof of the room, '
      + 'holding a veil before her face, and with a maid on either side of her.',
    )).toBe(true);
    expect(scene2Text).not.toContain('Then she said');
  });

  it.each([
    ['murray' as RealTranslation, 'This is a reproach for men that are yet to be to hear of.'],
    ['butler' as RealTranslation, 'This will disgrace us in the eyes of those who are yet unborn.'],
  ])(
    'Odyssey 21 (%s): Eurymachus’ lament closer appears on scene 9’s page only, never scene 10’s',
    (translation, lamentCloser) => {
      const loaded = loadRealBook(ODYSSEY_21_PATH, translation);
      if (!loaded) return;
      const { chunks, scenes } = loaded;
      const boundaryOverrides = loadRealBoundaryOverrides('odyssey', 21, translation, chunks, scenes);
      const pages = sentenceSnapScenePages(chunks, scenes, { boundaryOverrides });
      expect(pageTextOf(pages[8])).toContain(lamentCloser); // scene 9, index 8
      expect(pageTextOf(pages[9])).not.toContain(lamentCloser); // scene 10, index 9
    },
  );
});
