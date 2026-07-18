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

// The Reader's inline prose representation. `para: true` is a real TEI <p>
// boundary; ordinary tick markers have `text: null` and a numeric `n`.
export interface SceneFlowPart {
  text: string | null;
  n: number | null;
  real: boolean;
  para?: boolean;
}

export interface SceneOTable {
  n: number;
  rows: string[][];
}

export interface SceneFlowChunk {
  flowParts: SceneFlowPart[];
  otables: Record<string, SceneOTable[]>;
}

const DASH_CHARS = '-–—';

function needsJoinSpace(previous: string, next: string): boolean {
  return !!previous
    && !!next
    && !/\s$/.test(previous)
    && !/^\s/.test(next)
    && !DASH_CHARS.includes(previous.at(-1) ?? '')
    && !DASH_CHARS.includes(next[0]);
}

function hasParagraphStart(parts: SceneFlowPart[]): boolean {
  for (const part of parts) {
    if (part.para || part.text === '\n') return true;
    if (part.text !== null) return false;
  }
  return false;
}

function isTextRun(part: SceneFlowPart | undefined): part is SceneFlowPart & { text: string } {
  return !!part && part.text !== null && part.text !== '\n';
}

// Combine every whole tick-chunk selected for a scene into one inline prose
// flow. Chunk borders are alignment implementation details, not paragraph
// boundaries: only the explicit TEI paragraph part gets to introduce a break.
// Tables are carried forward from every source block; the same table object is
// shared by a block's tick chunks, so retain it once to avoid duplicate output.
export function mergeSceneFlowChunks(chunks: SceneFlowChunk[]): SceneFlowChunk {
  const flowParts: SceneFlowPart[] = [];
  const otables: Record<string, SceneOTable[]> = {};
  const seenTables = new Set<SceneOTable>();

  for (const chunk of chunks) {
    for (const [transId, tables] of Object.entries(chunk.otables)) {
      const out = otables[transId] ??= [];
      for (const table of tables) {
        if (!seenTables.has(table)) {
          seenTables.add(table);
          out.push(table);
        }
      }
    }

    const incoming = chunk.flowParts.map((part) => ({ ...part }));
    if (flowParts.length && incoming.length && !hasParagraphStart(incoming)) {
      let previousIndex = flowParts.length - 1;
      while (previousIndex >= 0 && flowParts[previousIndex].text === null) previousIndex -= 1;
      const nextIndex = incoming.findIndex(isTextRun);
      const previous = flowParts[previousIndex];
      const next = incoming[nextIndex];
      if (isTextRun(previous) && isTextRun(next)) {
        const joiner = needsJoinSpace(previous.text, next.text) ? ' ' : '';
        if (previousIndex === flowParts.length - 1 && nextIndex === 0) {
          // No tick/paragraph marker lies between these runs, so coalesce them.
          previous.text += joiner + next.text;
          incoming.shift();
        } else if (joiner) {
          // Keep a tick at its exact text offset, but supply the same visible
          // separator when it split what is logically one prose run.
          previous.text += joiner;
        }
      }
    }
    flowParts.push(...incoming);
  }

  return { flowParts, otables };
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
