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

// Append one chunk's flowParts onto a running merged array, joining a
// mid-sentence chunk seam into one continuous prose run — only an explicit
// TEI paragraph part is allowed to introduce a break. Extracted from
// mergeSceneFlowChunks so buildBookFlow (below, the sentence-snapping path)
// shares the IDENTICAL join/space rule: two separate implementations of "how
// do two adjacent chunks' prose join" would drift and produce different text
// between plain scene paging and the sentence-snapped path.
function joinChunkFlow(flowParts: SceneFlowPart[], incomingRaw: SceneFlowPart[]): void {
  const incoming = incomingRaw.map((part) => ({ ...part }));
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

// Fold `incoming`'s otables into `otables`, skipping any table object already
// seen (the same table object is shared by a block's tick chunks, so retain
// it once to avoid duplicate output). Shared by mergeSceneFlowChunks and
// slicePage (below).
function mergeTablesInto(
  otables: Record<string, SceneOTable[]>,
  seenTables: Set<SceneOTable>,
  incoming: Record<string, SceneOTable[]>,
): void {
  for (const [transId, tables] of Object.entries(incoming)) {
    const out = otables[transId] ??= [];
    for (const table of tables) {
      if (!seenTables.has(table)) {
        seenTables.add(table);
        out.push(table);
      }
    }
  }
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
    mergeTablesInto(otables, seenTables, chunk.otables);
    joinChunkFlow(flowParts, chunk.flowParts);
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

// ── Sentence-snapped page boundaries (John, 2026-07-19) ─────────────────────
// "SCENES SHOULD NOT BREAK UP SENTENCES... BECAUSE IT'S ENGLISH ONLY, THERE
// IS NO REASON TO SPLIT ACCORDING TO GREEK IF ENGLISH DOESN'T FOLLOW IT
// NEATLY." chunksForScene/mergeSceneFlowChunks above are honest about
// alignment, but two consequences follow directly from "every overlapping
// chunk renders WHOLE": (1) a chunk straddling a scene boundary is included
// by BOTH neighboring scenes, so its text is literally duplicated across two
// pages; (2) a page still opens or closes mid-sentence whenever a tick's
// ~5-line span doesn't happen to land on an English sentence boundary (the
// common case, per this file's header comment).
//
// sentenceSnapScenePages fixes both by repartitioning the WHOLE BOOK's prose
// into scene pages with ONE forward pass over a single flattened "book flow"
// (every chunk merged once, in order): a running cursor marks where the
// previous page ended, and each page runs from the cursor to whichever
// sentence-end offset sits at or after that scene's natural (chunk-based)
// end — extending past the natural end into as many further chunks as it
// takes to complete a dangling sentence, never short of it. The NEXT page
// then starts exactly at that same offset. Because every page's [from, to)
// range is a slice of the SAME flattened string, and each page's `to` becomes
// the next page's `from`, the pages are a disjoint partition of the whole
// book's text by construction — no separate "drop my leading fragment" step
// is needed on the follow-on page; starting at the previous page's exact end
// already IS starting at a clean sentence boundary. (A sentence spanning a
// raw boundary therefore always lands wholly on the page where it begins,
// per John's rule, as a consequence of the construction rather than a
// second, separately-verified rule.)
//
// Degenerate case: if a scene's own natural end has already been passed by
// the cursor (a scene short enough to be entirely swallowed by the PREVIOUS
// page's completed sentence — not expected of real apparatus scenes, which
// are narrative units well over one sentence, but not excluded by the data
// model either), that scene's page comes out empty. This is the honest
// result of "the sentence belongs to the page where it begins" pushed to its
// edge case, not a bug — see the dedicated test below.

// Sentence terminators: only . ? ! end a sentence — never a colon. John's
// worked example (Il. 1): "…and laid upon him a stern command:" must NOT
// start a new page right after the colon; the colon introduces what follows
// (the priest's own speech) as part of the SAME sentence/page.
const SENTENCE_TRAILERS = `"'”’)`;
// Murray's inline footnote convention embeds `[^label]` directly in the
// prose text (see Reader.svelte's fn-marker regex) and it commonly sits
// right at a sentence's end — e.g. real Il. 1 text: "than his father.[^1.9.1]
// He sat down…". Allow zero or more such markers between the terminator
// (+ optional closing quote/paren) and the whitespace that starts the next
// sentence, so a footnote reference never masks a real sentence boundary.
const FOOTNOTE_MARKER = String.raw`(?:\[\^[^\]]*\])*`;
// A short, defensive guard list — John's brief: "Mr./St. are essentially
// absent in Murray" — kept intentionally small rather than a general
// abbreviation dictionary (Karpathy: no speculative generality). The single-
// capital-letter guard below (an initial like "T.") covers the case the
// brief actually asks to protect.
const ABBREV_GUARD = new Set(['Mr', 'Mrs', 'Ms', 'Dr', 'St']);
const SENTENCE_END_RE = new RegExp(
  `[.?!]+([${SENTENCE_TRAILERS}]*)${FOOTNOTE_MARKER}(\\s+|$)`,
  'g',
);

// Character offsets in `text` at which one sentence ends and the next
// begins (right after the terminator + optional trailing quote/footnote +
// whitespace, or at text.length for a terminator at the very end). Exported
// for direct testing against synthetic Murray/Butler-shaped prose;
// sentenceSnapScenePages (below) is what real pages call.
export function sentenceEndOffsets(text: string): number[] {
  const offsets: number[] = [];
  SENTENCE_END_RE.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = SENTENCE_END_RE.exec(text))) {
    const matchEnd = m.index + m[0].length;
    // Guard: a single capital letter or a short known abbreviation
    // immediately before the terminator is not a real sentence end (e.g.
    // "T. E. Lawrence", "St. Nicholas") — the "sentence" continues past it.
    const word = /([A-Za-z]+)$/.exec(text.slice(0, m.index))?.[1] ?? '';
    const isAbbrev = (word.length === 1 && /[A-Z]/.test(word)) || ABBREV_GUARD.has(word);
    // Guard: what follows must actually look like a fresh sentence (a
    // capital, a digit, or an opening quote) or the end of the text —
    // otherwise this is a lowercase continuation (e.g. dialogue trailing off
    // mid-attribution), not a real boundary.
    const nextChar = text[matchEnd] ?? '';
    const looksLikeNewSentence = !nextChar || /[A-Z0-9"'“‘]/.test(nextChar);
    if (!isAbbrev && looksLikeNewSentence) offsets.push(matchEnd);
  }
  return offsets;
}

// A tick-anchored chunk carrying its own inline prose, as Reader.svelte's
// readingChunks derives it (TickChunkRange + SceneFlowChunk in one object).
export interface SceneReadingChunk extends TickChunkRange, SceneFlowChunk {}

interface BookFlow {
  flowParts: SceneFlowPart[];
  text: string;
  // partStart[k]: the character offset in `text` at which flowParts[k]
  // begins (zero-width — i.e. equal to the offset right after it — for a
  // non-text marker part).
  partStart: number[];
  // chunkTextEnd[i]: the cumulative length of `text` once chunks[0..i] have
  // all been folded in — i.e. the offset marking the end of chunk i's own
  // contribution to the flattened book text.
  chunkTextEnd: number[];
}

// Merge every chunk (the WHOLE book's tick list, not one scene's selection)
// into a single flattened prose flow, once, via the same join rule
// mergeSceneFlowChunks uses — plus the offset bookkeeping sentence-snapping
// needs to find sentence boundaries and slice pages back out again.
function buildBookFlow(chunks: SceneReadingChunk[]): BookFlow {
  const flowParts: SceneFlowPart[] = [];
  const chunkTextEnd: number[] = [];
  for (const chunk of chunks) {
    joinChunkFlow(flowParts, chunk.flowParts);
    let len = 0;
    for (const p of flowParts) if (typeof p.text === 'string') len += p.text.length;
    chunkTextEnd.push(len);
  }
  const partStart: number[] = [];
  let text = '';
  for (const p of flowParts) {
    partStart.push(text.length);
    if (typeof p.text === 'string') text += p.text;
  }
  return { flowParts, text, partStart, chunkTextEnd };
}

// The index of the original chunk whose own contribution contains character
// `offset` (clamped to the last chunk for offset === text.length).
function chunkAtOffset(chunkTextEnd: number[], offset: number): number {
  for (let i = 0; i < chunkTextEnd.length; i++) if (chunkTextEnd[i] > offset) return i;
  return Math.max(0, chunkTextEnd.length - 1);
}

// Slice [from, to) of a whole-book flow into one page. A text part straddling
// either edge is SPLIT, never duplicated (John's brief: "splitting a text
// part mid-part at a sentence boundary is fine — split into two parts
// between pages"). A zero-width marker (tick/paragraph) exactly at `from`
// stays with the page it opens; one exactly at `to` moves to the next page it
// introduces — "footnote/tick markers travel with the text they're embedded
// in".
function slicePage(book: BookFlow, chunks: SceneReadingChunk[], from: number, to: number): SceneFlowChunk {
  const flowParts: SceneFlowPart[] = [];
  for (let k = 0; k < book.flowParts.length; k++) {
    const part = book.flowParts[k];
    const start = book.partStart[k];
    if (typeof part.text !== 'string') {
      if (start >= from && start < to) flowParts.push({ ...part });
      continue;
    }
    const end = start + part.text.length;
    if (end <= from || start >= to) continue;
    const sliceStart = Math.max(0, from - start);
    const sliceEnd = Math.min(part.text.length, to - start);
    if (sliceEnd > sliceStart) flowParts.push({ ...part, text: part.text.slice(sliceStart, sliceEnd) });
  }
  const otables: Record<string, SceneOTable[]> = {};
  if (to > from) {
    const seenTables = new Set<SceneOTable>();
    const lo = chunkAtOffset(book.chunkTextEnd, from);
    const hi = chunkAtOffset(book.chunkTextEnd, Math.max(from, to - 1));
    for (let ci = lo; ci <= hi && ci < chunks.length; ci++) mergeTablesInto(otables, seenTables, chunks[ci].otables);
  }
  return { flowParts, otables };
}

// One sentence-snapped Reading Mode page per scene, covering the currently
// selected translation's own chunk list end to end with no gap and no
// overlap (see the file-section comment above for the algorithm). Call once
// per (chunks, scenes) change and index the result by the current scene,
// rather than recomputing per scene — a single forward pass is what
// guarantees the partition.
export function sentenceSnapScenePages(chunks: SceneReadingChunk[], scenes: SceneRange[]): SceneFlowChunk[] {
  if (!scenes.length) return [];
  if (!chunks.length) return scenes.map(() => ({ flowParts: [], otables: {} }));

  const book = buildBookFlow(chunks);
  const sentenceEnds = sentenceEndOffsets(book.text);
  const firstSentenceEndAtOrAfter = (threshold: number): number => {
    for (const e of sentenceEnds) if (e >= threshold) return e;
    return book.text.length;
  };

  const pages: SceneFlowChunk[] = [];
  let cursor = 0;
  for (let si = 0; si < scenes.length; si++) {
    let end: number;
    if (si === scenes.length - 1) {
      end = book.text.length; // the last scene always runs to the true end — no trailing dangle
    } else {
      const selected = chunksForScene(chunks, scenes[si]);
      const naturalChunkIdx = selected.length ? selected[selected.length - 1] : chunks.length - 1;
      const naturalBoundary = Math.max(cursor, book.chunkTextEnd[naturalChunkIdx] ?? book.text.length);
      end = firstSentenceEndAtOrAfter(naturalBoundary);
    }
    pages.push(slicePage(book, chunks, cursor, end));
    cursor = end;
  }
  return pages;
}
