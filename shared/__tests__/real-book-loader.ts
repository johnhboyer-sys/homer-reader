// Shared real-data loader for scene-paging tests and the corpus audit script.
//
// Reconstructs "text + bekker ticks + paragraph offsets -> tick-chunked
// SceneReadingChunk[]" from a build/dist book JSON — sufficient to exercise
// sentenceSnapScenePages against real translation prose. NOT a copy of
// Reader.svelte's private flowParts()/alignGroups() (those also resolve real
// per-line Greek offsets and speech-snap adjustments, out of scope for a
// pure-module text test).
//
// Translations:
//   'murray' — seg.english: text + bekker + paragraph markers.
//   'butler' — seg.ross[0]: text + bekker, NO paragraph markers — faithful to
//     production, where Reader.svelte's flowOf(RossPiece) passes no paragraph
//     offsets either (Reader.svelte flowOf; ross pieces carry no `markers`).
import { existsSync, readFileSync } from 'node:fs';
import type { SceneRange, SceneReadingChunk } from '../lib/scene-paging';

export type RealTranslation = 'murray' | 'butler';

export interface RealBekkerTick { n: number; offset: number; real: boolean }
export interface RealMarker { kind: string; offset: number }

export function buildRealChunks(text: string, bekker: RealBekkerTick[], paraOffsets: number[]): SceneReadingChunk[] {
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

// Loads one translation's flow + the book's scenes from a build/dist book
// JSON. Returns null when the file is missing (pipeline output is gitignored,
// not a suite dependency) or the requested translation slot is absent.
export function loadRealBook(path: string, translation: RealTranslation): { chunks: SceneReadingChunk[]; scenes: SceneRange[] } | null {
  if (!existsSync(path)) return null;
  const raw = JSON.parse(readFileSync(path, 'utf-8'));
  const seg = raw.segments[0];
  let chunks: SceneReadingChunk[];
  if (translation === 'murray') {
    if (!seg.english?.text) return null;
    const paraOffsets = ((seg.english.markers ?? []) as RealMarker[])
      .filter((m) => m.kind === 'paragraph')
      .map((m) => m.offset);
    chunks = buildRealChunks(seg.english.text, seg.english.bekker ?? [], paraOffsets);
  } else {
    // Homer verse-line books carry exactly one ross piece per segment.
    const piece = seg.ross?.[0];
    if (!piece?.text) return null;
    chunks = buildRealChunks(piece.text, piece.bekker ?? [], []);
  }
  const scenes: SceneRange[] = raw.apparatus.scenes.map((s: { lines: [number, number] }) => ({
    startLine: s.lines[0], endLine: s.lines[1],
  }));
  return { chunks, scenes };
}
