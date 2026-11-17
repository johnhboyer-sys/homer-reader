// The reader's scene pages, as character spans of each translation's text.
//
// The ported search counts English hits by scene (docs/search-port/PLAN.md),
// and an English word must count in the scene whose page shows it. Reading
// Mode cuts each translation into scene pages with shared/lib/scene-paging.ts;
// this module runs that same code — the same flow, the same line groups, the
// same boundary overrides — and reports, per scene, which characters of the
// translation's own text (the text the search index counts words in) the page
// shows. pipeline/homer_pipeline/search_scenes.py turns those spans into word
// numbers with the index's own word split.
//
// What is copied from Reader.svelte rather than imported (it lives inside the
// component): picking a translation's piece (piecesFor/pieceCont), the tick
// and paragraph filters of flowFor, and the choice of speech-snapping
// (readingTransCuratedTicks). Each is marked below with its Reader.svelte
// source.
import { alignGroups, flowParts, type FlowPart } from '../../shared/lib/tick-chunks.ts';
import {
  mergeSceneFlowChunks,
  resolveBoundaryOverrides,
  selectBoundaryOverrideEntries,
  sentenceSnapScenePages,
  type BoundaryOverride,
  type SceneBoundaryOverrideFile,
  type SceneFlowChunk,
  type SceneRange,
  type SceneReadingChunk,
} from '../../shared/lib/scene-paging.ts';
import { decoratePiece } from '../../shared/lib/kosmos.ts';
import type { RossPiece, Segment } from '../../shared/lib/data.ts';

export interface PagedTranslationRef {
  id: string;
  slot: 'english' | 'ross' | 'third' | 'overlay';
  curatedTicks?: true;
  verseGroups?: true;
}

export interface TranslationPages {
  /** The slot as the search names its index (englishIndexSlot). */
  slot: string;
  /** False when the reader shows the whole book at once (fewer than two line
   * groups): there are no scene pages to follow. */
  anchored: boolean;
  /** Per scene, the [start, end) spans of the translation's text its page
   * shows, in that text's own character offsets. Null when not anchored. */
  pages: [number, number][][] | null;
  /** Non-space characters of the text on no page (line groups the reader
   * drops). */
  offPage: number;
  /** Characters shown on more than one page (the hollow-page backstop). */
  onTwoPages: number;
  /** Set when a boundary override did not resolve; the reader then pages
   * without overrides for this book, and so does this. */
  overrideError?: string;
}

/** englishIndexSlot from Aristotle's shared/lib/search.ts (7ddd67b7ef). */
export function indexSlot(t: PagedTranslationRef): string {
  return t.slot === 'overlay' ? `overlay-${t.id}` : t.slot;
}

/** The translation's prose flow as Reading Mode builds it, and for each
 * character of the flow's text the character of the piece's own text it
 * shows (-1 for a character the reader adds: Kosmos's span sentinels and
 * mark labels). Null when the segment has no text in this translation. */
export function readerFlow(seg: Segment, t: PagedTranslationRef): { flow: FlowPart[]; toRaw: Int32Array } | null {
  if (t.slot === 'english') {
    const text = seg.english?.text ?? '';
    if (!text) return null;
    // Reader.svelte splitSegment → flowFor(0, text.length) (no chapter starts).
    const ticks = (seg.english?.bekker ?? [])
      .filter(k => k.offset >= 0 && k.offset < text.length)
      .map(k => ({ n: k.n, real: k.real, off: k.offset }))
      .sort((x, y) => x.off - y.off);
    const paras = (seg.english?.markers ?? [])
      .filter(m => m.kind === 'paragraph')
      .map(m => m.offset)
      .filter(off => off > 0 && off < text.length);
    const toRaw = new Int32Array(text.length);
    for (let i = 0; i < text.length; i++) toRaw[i] = i;
    return { flow: flowParts(text, ticks, paras), toRaw };
  }
  // Reader.svelte piecesFor + pieceCont + flowOf.
  const pieces: RossPiece[] = t.slot === 'ross' ? (seg.ross ?? [])
    : t.slot === 'third' ? (seg.third ?? [])
    : (seg.overlays?.[t.id] ?? []);
  const p = pieces.find(x => x.cont) ?? pieces[0];
  if (!p || !p.text) return null;
  const d = decoratePiece(p);
  return { flow: flowParts(d.text, d.ticks), toRaw: decoratedToRaw(d.text, p.text) };
}

const SENTINEL = /[-]/;
const MARK_OPEN = '';
const MARK_CLOSE = '';

/** decoratePiece (lib/kosmos.ts) only inserts: span sentinels, and a mark's
 * code and label between MARK_OPEN and MARK_CLOSE. Every other character is
 * the piece's own, in order. Checked, not assumed. */
export function decoratedToRaw(decorated: string, raw: string): Int32Array {
  const out = new Int32Array(decorated.length);
  let r = 0;
  let inMark = false;
  for (let i = 0; i < decorated.length; i++) {
    const ch = decorated[i];
    if (ch === MARK_OPEN) { inMark = true; out[i] = -1; continue; }
    if (inMark) { if (ch === MARK_CLOSE) inMark = false; out[i] = -1; continue; }
    if (SENTINEL.test(ch)) { out[i] = -1; continue; }
    // decoratePiece replaces a sentinel-range character already in the
    // source with U+FFFD, one for one.
    if (ch !== raw[r] && !(ch === '�' && /[-]/.test(raw[r] ?? ''))) {
      throw new Error(`decorated text departs from the piece at ${i} (piece offset ${r})`);
    }
    out[i] = r++;
  }
  if (r !== raw.length) throw new Error(`decorated text drops ${raw.length - r} characters of the piece`);
  return out;
}

const textOf = (parts: FlowPart[]) => parts.map(p => (typeof p.text === 'string' ? p.text : '')).join('');

export interface PageInput {
  seg: Segment;
  translation: PagedTranslationRef;
  scenes: SceneRange[];
  /** Every speech's opening line in the book (Reader.svelte bookSpeechStarts). */
  speechStarts: number[];
  overrides: SceneBoundaryOverrideFile;
  work: string;
  book: number;
}

export function translationPages(input: PageInput): TranslationPages | null {
  const { seg, translation: t, scenes } = input;
  const built = readerFlow(seg, t);
  if (!built) return null;
  const { flow, toRaw } = built;
  const slot = indexSlot(t);

  // Where each flow part starts in the flow's text.
  const partStart = new Map<FlowPart, number>();
  let at = 0;
  for (const part of flow) {
    partStart.set(part, at);
    if (typeof part.text === 'string') at += part.text.length;
  }

  // Reader.svelte readingChunks; readingTransCuratedTicks decides snapping.
  const snap = !(t.curatedTicks || t.verseGroups);
  const lines = (seg.greek ?? []).map(l => ({ n: l.n, cont: (l as { cont?: boolean }).cont }));
  const chunks: SceneReadingChunk[] = [];
  const chunkFrom: number[] = [];
  for (const g of alignGroups(lines, flow, snap ? input.speechStarts : [])) {
    if (!g.lines.length) continue;
    chunks.push({ startLine: g.lines[0].n, endLine: g.lines[g.lines.length - 1].n, flowParts: g.flowParts, otables: {} });
    chunkFrom.push(g.flowParts.length ? partStart.get(g.flowParts[0])! : at);
  }
  if (chunks.length <= 1) return { slot, anchored: false, pages: null, offPage: 0, onTwoPages: 0 };

  // Reader.svelte sceneBoundaryOverrides: a failure pages without overrides.
  let boundaryOverrides: BoundaryOverride[] = [];
  let overrideError: string | undefined;
  const entries = selectBoundaryOverrideEntries(input.overrides, input.work, input.book, t.id);
  if (entries.length) {
    try {
      boundaryOverrides = resolveBoundaryOverrides(chunks, scenes, entries);
    } catch (err) {
      overrideError = String(err);
    }
  }
  const pages = sentenceSnapScenePages(chunks, scenes, { boundaryOverrides });
  const pure = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: false, boundaryOverrides });

  // The book's flow as the pager joins it: each chunk's text in order, with a
  // space the join may add between two chunks. Map each of its characters to
  // the flow's text, and from there to the piece's own text.
  const book = textOf(mergeSceneFlowChunks(chunks).flowParts);
  if (pure.map(p => textOf(p.flowParts)).join('') !== book) {
    throw new Error(`${input.work} ${input.book} ${t.id}: the pages are not a partition of the book's flow`);
  }
  const bookToRaw = new Int32Array(book.length).fill(-1);
  let ptr = 0;
  chunks.forEach((chunk, k) => {
    const text = textOf(chunk.flowParts);
    let start = ptr;
    if (!book.startsWith(text, ptr)) {
      if (book[ptr] === ' ' && book.startsWith(text, ptr + 1)) start = ptr + 1;
      else throw new Error(`${input.work} ${input.book} ${t.id}: chunk ${k} is not where the join puts it`);
    }
    for (let i = 0; i < text.length; i++) bookToRaw[start + i] = toRaw[chunkFrom[k] + i];
    ptr = start + text.length;
  });
  if (ptr !== book.length) throw new Error(`${input.work} ${input.book} ${t.id}: the joined flow has ${book.length - ptr} characters no chunk accounts for`);

  // Each page is a stretch of the joined flow: the pure cut's, or, where the
  // hollow-page backstop replaced a page, the stretch its text is found at
  // nearest the pure cut.
  const raw = t.slot === 'english' ? seg.english!.text : textOfPiece(seg, t);
  const cover = new Uint8Array(raw.length);
  let from = 0;
  const spans = pages.map((page: SceneFlowChunk, j: number) => {
    const text = textOf(page.flowParts);
    const pureFrom = from;
    from += textOf(pure[j].flowParts).length;
    let a = book.startsWith(text, pureFrom) ? pureFrom : -1;
    if (a < 0) {
      for (let i = book.indexOf(text); i !== -1; i = book.indexOf(text, i + 1)) {
        if (a < 0 || Math.abs(i - pureFrom) < Math.abs(a - pureFrom)) a = i;
      }
      if (a < 0) throw new Error(`${input.work} ${input.book} ${t.id}: page ${j + 1} is not in the book's flow`);
    }
    const out: [number, number][] = [];
    for (let i = a; i < a + text.length; i++) {
      const r = bookToRaw[i];
      if (r < 0) continue;
      const last = out[out.length - 1];
      if (last && last[1] === r) last[1] = r + 1;
      else out.push([r, r + 1]);
    }
    for (const [s, e] of out) for (let r = s; r < e; r++) cover[r] = Math.min(2, cover[r] + 1);
    return out;
  });

  let offPage = 0;
  let onTwoPages = 0;
  for (let r = 0; r < raw.length; r++) {
    if (cover[r] === 0 && !/\s/.test(raw[r])) offPage++;
    if (cover[r] === 2) onTwoPages++;
  }
  return { slot, anchored: true, pages: spans, offPage, onTwoPages, ...(overrideError ? { overrideError } : {}) };
}

function textOfPiece(seg: Segment, t: PagedTranslationRef): string {
  const pieces: RossPiece[] = t.slot === 'ross' ? (seg.ross ?? [])
    : t.slot === 'third' ? (seg.third ?? [])
    : (seg.overlays?.[t.id] ?? []);
  return (pieces.find(x => x.cont) ?? pieces[0])?.text ?? '';
}
