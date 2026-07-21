// Shared real-data loader for scene-paging tests and the corpus audit script.
//
// Reconstructs the EXACT production Reading-Mode chunk geometry from a
// build/dist book JSON, so the audit/tests measure what the reader renders
// (Codex review F1, 2026-07-21). Reader.svelte's readingChunks are:
//
//   flowParts(text, bekker, paraOffsets)                     (shared/lib/tick-chunks.ts)
//     → alignGroups(seg.greek, flow, bookSpeechStarts)       (shared/lib/tick-chunks.ts)
//       → one chunk per group: startLine/endLine = the group's first/last
//         real Greek line (the vulgate-gap carrier), flowParts = the group's
//         tick-anchored English run.
//
// This module calls that SAME extracted path — NOT a private re-derivation.
// `bookSpeechStarts` (every speech's opening line in the book) feeds
// snapTicksToSpeechStarts inside alignGroups exactly as the component does;
// in Reader they come from fetchSpeeches(work); here from the book's sibling
// speeches.json in the same build/dist work directory.
//
// Translations:
//   'murray' — seg.english: text + bekker + paragraph markers.
//   'butler' — seg.ross[0]: text + bekker, NO paragraph markers — faithful to
//     production, where Reader.svelte's flowOf(RossPiece) passes no paragraph
//     offsets either (Reader.svelte flowOf; ross pieces carry no `markers`).
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
// `.ts` extension so `node --experimental-strip-types` (the audit CLI) resolves
// this runtime import; vitest's bundler resolution accepts it too. (The
// scene-paging import below is type-only — erased before resolution.)
import { alignGroups, flowParts } from '../lib/tick-chunks.ts';
import type { SceneRange, SceneReadingChunk } from '../lib/scene-paging';

export type RealTranslation = 'murray' | 'butler';

export interface RealBekkerTick { n: number; offset: number; real: boolean }
export interface RealMarker { kind: string; offset: number }

// Build production Reading-Mode chunks from one translation's raw text +
// ticks + paragraph offsets, the book's real Greek line list, and the book's
// speech-opening lines — via the identical flowParts → alignGroups path
// Reader.svelte's readingChunks uses. A group with no Greek lines is dropped
// (matches readingChunks' `if (!g.lines.length) continue`).
export function buildRealChunks(
  text: string,
  bekker: RealBekkerTick[],
  paraOffsets: number[],
  greekLines: { n: number }[],
  speechStarts: number[],
): SceneReadingChunk[] {
  const flow = flowParts(text, bekker.map((t) => ({ n: t.n, real: t.real, off: t.offset })), paraOffsets);
  const chunks: SceneReadingChunk[] = [];
  for (const g of alignGroups(greekLines, flow, speechStarts)) {
    if (!g.lines.length) continue;
    chunks.push({
      startLine: g.lines[0].n,
      endLine: g.lines[g.lines.length - 1].n,
      flowParts: g.flowParts,
      otables: {},
    });
  }
  return chunks;
}

// Every speech-opening line in `bookNum`, read from the book's sibling
// speeches.json (build/dist/<work>/speeches.json) — the on-disk source of
// Reader.svelte's bookSpeechStarts. Missing/unreadable ⇒ no snapping (empty),
// same as Reader before its async speeches fetch resolves.
export function loadSpeechStarts(bookPath: string, bookNum: number): number[] {
  const speechesPath = path.join(path.dirname(bookPath), 'speeches.json');
  if (!existsSync(speechesPath)) return [];
  try {
    const raw = JSON.parse(readFileSync(speechesPath, 'utf-8')) as {
      speeches?: { book: number; lines: [number, number] }[];
    };
    return (raw.speeches ?? []).filter((s) => s.book === bookNum).map((s) => s.lines[0]);
  } catch {
    return [];
  }
}

// Loads one translation's flow + the book's scenes from a build/dist book
// JSON. Returns null when the file is missing (pipeline output is gitignored,
// not a suite dependency) or the requested translation slot is absent.
export function loadRealBook(bookPath: string, translation: RealTranslation): { chunks: SceneReadingChunk[]; scenes: SceneRange[] } | null {
  if (!existsSync(bookPath)) return null;
  const raw = JSON.parse(readFileSync(bookPath, 'utf-8'));
  const seg = raw.segments[0];
  // block.lines for a Homer book (no chapter starts) is exactly seg.greek —
  // the real vulgate line list, gaps and all. alignGroups reads only `.n`.
  const greekLines: { n: number }[] = (seg.greek ?? []).map((l: { n: number }) => ({ n: l.n }));
  const speechStarts = loadSpeechStarts(bookPath, raw.book);
  let chunks: SceneReadingChunk[];
  if (translation === 'murray') {
    if (!seg.english?.text) return null;
    const paraOffsets = ((seg.english.markers ?? []) as RealMarker[])
      .filter((m) => m.kind === 'paragraph')
      .map((m) => m.offset);
    chunks = buildRealChunks(seg.english.text, seg.english.bekker ?? [], paraOffsets, greekLines, speechStarts);
  } else {
    // Homer verse-line books carry exactly one ross piece per segment.
    const piece = seg.ross?.[0];
    if (!piece?.text) return null;
    chunks = buildRealChunks(piece.text, piece.bekker ?? [], [], greekLines, speechStarts);
  }
  const scenes: SceneRange[] = raw.apparatus.scenes.map((s: { lines: [number, number] }) => ({
    startLine: s.lines[0], endLine: s.lines[1],
  }));
  return { chunks, scenes };
}
