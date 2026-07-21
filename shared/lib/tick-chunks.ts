// Tick-chunking core, extracted VERBATIM from Reader.svelte (John, 2026-07-21,
// Codex review F1) so the Reading Mode scene-paging AUDIT and TESTS measure the
// SAME geometry the component renders — not a parallel re-derivation. The
// production render path is:
//
//   splitSegment → block.flow (via flowParts) → alignGroups(block.lines, flow,
//   bookSpeechStarts) → readingChunks (startLine/endLine from each group's
//   Greek lines).
//
// Reader.svelte imports flowParts + alignGroups (and the helpers/types below)
// from here; real-book-loader.ts builds its chunks through the identical
// path. Any change to how ticks chunk a book's prose belongs HERE, once.
//
// Nothing in this module is Svelte-specific — it is the pure, framework-free
// tick geometry. `snapTicksToSpeechStarts` already lives in speech-snap.ts and
// is re-used (not re-copied) here.
// `.ts` extension so `node --experimental-strip-types` (the scene-paging audit
// CLI, which imports this transitively) resolves this runtime import; vitest's
// bundler resolution accepts it too. The scene-paging import is type-only.
import { snapTicksToSpeechStarts } from './speech-snap.ts';
import type { SceneFlowPart } from './scene-paging';

// A flowing-prose part: either a text run (n null) or a Bekker margin marker
// (text null) placed at an exact mid-sentence offset — no row break.
export type FlowPart = SceneFlowPart;

// Flowing prose with Bekker numbers floated into the margin at their EXACT
// offsets (no row break, no in-text number, no sentence-boundary snapping).
// Used for precisely-placed translations like the gloss-aligned Ross.
export function flowParts(text: string, ticks: { n: number; real: boolean; off: number }[], paraOffsets: number[] = []): FlowPart[] {
  const ts = [
    ...ticks.map(t => ({ ...t, para: false })),
    ...paraOffsets.map(off => ({ n: 0, real: false, off, para: true })),
  ].sort((a, b) => a.off - b.off || Number(a.para) - Number(b.para));
  const parts: FlowPart[] = [];
  let cur = 0;
  const addText = (s: string) => {
    const segs = s.split('\n');
    for (let i = 0; i < segs.length; i++) {
      if (i > 0) parts.push({ text: '\n', n: null, real: false });
      if (segs[i]) parts.push({ text: segs[i], n: null, real: false });
    }
  };
  for (const t of ts) {
    const off = Math.max(0, Math.min(t.off, text.length));
    if (off > cur) { addText(text.slice(cur, off)); cur = off; }
    if (t.para) {
      parts.push({ text: null, n: null, real: false, para: true });
    } else {
      parts.push({ text: null, n: t.n, real: t.real });
    }
  }
  if (cur < text.length) addText(text.slice(cur));
  return parts;
}

// ── Both view on a phone: stack per ALIGNMENT GROUP, not per verse ─────────
// John's ruling (2026-07-18): the parallel Greek/English columns are
// unusable at phone width (Greek wraps to 1–2 words/line); the fix is to
// interleave Greek and English on narrow screens instead of squeezing two
// columns. HONESTY CONSTRAINT: Murray's English is aligned to the Greek per
// ~5-line milestone tick (`seg.english.bekker`), NOT per verse — there is no
// real per-line English pairing to display. So the stacking unit here is the
// ALIGNMENT GROUP: a run of Greek verse lines followed by the English chunk
// aligned to that same tick span — never a fabricated per-verse split.
// A tick-shaped FlowPart, as embedded inline in block.flow by flowParts()
// (text: null, n: the Greek line it anchors, real: milestone vs interpolated).
export type TickFlowPart = FlowPart & { text: null; n: number; para?: false | undefined };
export const isTickPart = (p: FlowPart): p is TickFlowPart => p.text === null && p.n !== null && !p.para;
// Split a block's full English flow into one run per tick, each run LED by
// its own tick marker (so flowProse's existing attachTicks/bk-num rendering
// works unmodified on a slice exactly as it does on the whole flow). Any
// text preceding the very first tick (not seen in practice — every book's
// first tick is at n=1/offset=0 — but not guaranteed by the type) is folded
// into the first tick's run rather than silently dropped.
export function groupFlowByTicks(flow: FlowPart[]): FlowPart[][] {
  const groups: FlowPart[][] = [];
  let cur: FlowPart[] = [];
  for (const part of flow) {
    if (isTickPart(part)) {
      if (cur.length) groups.push(cur);
      cur = [part];
    } else {
      cur.push(part);
    }
  }
  if (cur.length) groups.push(cur);
  if (groups.length > 1 && !isTickPart(groups[0][0])) {
    groups[1].unshift(...groups.shift()!);
  }
  return groups;
}

// A run of Greek verse lines paired with the tick-anchored English aligned to
// that same span. Generic over the line type so a caller keeps its own richer
// line shape (Reader.svelte's RLine) through the return — the derivation itself
// needs only a vulgate line number `n` and the `cont` (partial-tail) flag.
export interface AlignGroup<L> { lines: L[]; flowParts: FlowPart[] }

// Pair each tick-anchored English run with the Greek lines it aligns to —
// from this tick's line up to (excluding) the next tick's line, or the end
// of the block for the last group. Greek lines are matched by vulgate
// number (not array position), so a declared expected_line_gaps skip (e.g.
// Il. 9.457→462) never miscounts a group's span — the tick itself always
// anchors to a line number actually present in `lines`.
// `speechStarts` (FIX 1, John's phone report 2026-07-18): every speech's
// opening line in this book (bookSpeechStarts) — snapped via
// shared/lib/speech-snap.ts's snapTicksToSpeechStarts BEFORE the tick lines
// are resolved to Greek-line indices, so a tick 1-2 lines ahead of a
// speech's own start moves that speech's opening Greek line into the SAME
// group as its opening English instead of the group before it. Reader.svelte's
// callers pass `bookSpeechStarts` EXPLICITLY (not as a default) so Svelte's
// reactivity tracks it — a default reading the outer variable wouldn't appear
// in either call site's own dependency scan.
export function alignGroups<L extends { n: number; cont?: boolean }>(
  lines: L[],
  flow: FlowPart[],
  speechStarts: number[] = [],
): AlignGroup<L>[] {
  const flowGroups = groupFlowByTicks(flow);
  const ticks = flowGroups.map(g => g[0]).filter(isTickPart);
  const tickLines = snapTicksToSpeechStarts(ticks.map((t) => t.n), speechStarts);
  const lineIndex = new Map<number, number>();
  lines.forEach((l, i) => { if (!l.cont && !lineIndex.has(l.n)) lineIndex.set(l.n, i); });
  return flowGroups.map((parts, i) => {
    const n = tickLines[i];
    const startIdx = n !== undefined ? (lineIndex.get(n) ?? 0) : 0;
    const nextN = tickLines[i + 1];
    const endIdx = nextN !== undefined ? (lineIndex.get(nextN) ?? lines.length) : lines.length;
    return { lines: lines.slice(startIdx, endIdx), flowParts: parts };
  });
}
