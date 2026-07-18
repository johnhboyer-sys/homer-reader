// Reading Mode pagination (John's directive, 2026-07-18): a book's prose is
// too long as one scroll, so Reading Mode shows ONE apparatus scene
// (Scene — see data.ts) at a time. But the English translation itself is
// chunked by ~5-line Murray milestone ticks (Segment.english.bekker), not by
// scene — a scene's [startLine, endLine] range only rarely lands exactly on a
// tick boundary (measured across Il. 1 + Od. 9: the large majority of scenes
// have at least one edge that doesn't land on a tick — see the Reading Mode
// PR notes). This module is the pure, framework-free core of that
// reconciliation, so it's testable without mounting Reader.svelte.
//
// ALIGNMENT HONESTY (CLAUDE.md): a tick's prose is never split mid-chunk.
// Every tick-chunk that OVERLAPS a scene's line range renders in full on that
// scene's page — which means a little text right at a scene boundary can
// appear on both the previous and the next scene's page. That's the honest
// tradeoff: the apparatus (scene ranges, drafted from the Greek) and the
// translation flow (chunked by the translator's own milestone ticks) are two
// independently-anchored things with no guaranteed exact join.

// One tick-anchored chunk of a book's English flow, in reading order.
// `startLine`/`endLine` are real Greek vulgate line numbers (never a computed
// array index), so a numbering gap inside or at the edge of a chunk is
// carried faithfully — see CLAUDE.md's "vulgate lineation is sacred".
export interface TickChunkRange {
  startLine: number;
  endLine: number;
}

// The line range a scene covers. `endLine` omitted ⇒ open-ended (treated as
// a single-line scene for overlap purposes) — mirrors data.ts's `Scene`.
export interface SceneRange {
  startLine: number;
  endLine?: number;
}

// Indices into `chunks` (same order) of every chunk that overlaps `scene`'s
// line range. `chunks` is assumed sorted in reading order and to cover the
// book contiguously (each chunk's endLine is the line immediately before the
// next chunk's startLine, gaps aside) — true of every chunk list Reader.svelte
// derives from a segment's ticks, so the result is always a contiguous run of
// indices for a well-formed scene.
//
// Degenerate case: if `scene`'s range falls entirely inside a gap between
// chunks (no chunk overlaps it at all — not expected from real apparatus
// data, since scene lines are drawn from the text itself, but a pipeline
// anomaly shouldn't blank the page), fall back to the single nearest chunk by
// line distance so the scene still shows some prose.
export function chunksForScene(chunks: TickChunkRange[], scene: SceneRange): number[] {
  const lo = scene.startLine;
  const hi = scene.endLine ?? scene.startLine;
  const out: number[] = [];
  for (let i = 0; i < chunks.length; i++) {
    if (chunks[i].endLine >= lo && chunks[i].startLine <= hi) out.push(i);
  }
  if (out.length || !chunks.length) return out;
  let best = 0;
  let bestDist = Infinity;
  for (let i = 0; i < chunks.length; i++) {
    const d = lo > chunks[i].endLine ? lo - chunks[i].endLine : chunks[i].startLine - hi;
    if (d < bestDist) { bestDist = d; best = i; }
  }
  return [best];
}
