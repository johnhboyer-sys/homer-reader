// Pure line -> speech-span membership logic for the search page's speaker /
// "speeches only" result filters (Homer-only; no plato-reader counterpart —
// Plato's corpus carries no DICES speech apparatus). No DOM, no fetch — see
// shared/lib/data.ts's fetchSpeeches/fetchCharacters for loading the data
// this operates on, and shared/components/Search.svelte for the caller.
//
// A search hit is (work, book, line). A speech span is "in this book" when
// speech.book === book, with membership `lines[0] <= line <= lines[1]` for an
// ordinary (non-crossBook) speech.
//
// crossBook spans (only the two Apologoi frame speeches in this corpus, e.g.
// Od. 9.2-11.332: `book: 9, lines: [2, 332]`) record their OPENING book in
// `book` and their CLOSING line in a LATER book — there is no `endBook` field
// (see shared/lib/data.ts's Speech doc comment). We do not know where the
// opening book itself ends, nor which interior/closing books the span also
// covers, so we never guess: a crossBook speech only ever matches lines in
// its own recorded `book`, from `lines[0]` onward with NO upper bound (safe,
// because the true close is in a later book, so every line from `lines[0]` to
// the book's end is genuinely inside the speech). It contributes no match in
// any other book. This under-matches the true span rather than over-claiming
// one — the same "never invent" posture shared/lib/speeches.ts's
// classifySpeech already applies (crossBook spans degrade there too, for the
// identical reason: the boundary past this book isn't known here).

import type { Speech } from './data';
import type { SearchResult } from './search';
import { cutPositions } from './result-views';
import type { SpeechFilter } from './search-url';

// Per-book index: speech.book -> the speeches recorded under that book.
// Built once per work per search session; lookups are O(speeches in that
// book) — a few dozen at most, fine for even large result sets.
export type SpanIndex = Map<number, Speech[]>;

export function buildSpanIndex(speeches: Speech[]): SpanIndex {
  const idx: SpanIndex = new Map();
  for (const s of speeches) {
    const arr = idx.get(s.book);
    if (arr) arr.push(s);
    else idx.set(s.book, [s]);
  }
  return idx;
}

function lineInSpeech(speech: Speech, line: number): boolean {
  if (speech.crossBook) return line >= speech.lines[0];
  return line >= speech.lines[0] && line <= speech.lines[1];
}

// Every speech (in `book`) whose span contains `line`.
export function speechesAtLine(index: SpanIndex, book: number, line: number): Speech[] {
  const candidates = index.get(book);
  if (!candidates) return [];
  return candidates.filter((s) => lineInSpeech(s, line));
}

// "Speeches only" predicate: is this line inside ANY speech span, any speaker?
export function lineInAnySpeech(index: SpanIndex, book: number, line: number): boolean {
  const candidates = index.get(book);
  if (!candidates) return false;
  return candidates.some((s) => lineInSpeech(s, line));
}

// Speaker filter predicate: is this line inside a span whose speaker list
// includes `speakerId`? A line inside no span never matches (even if
// `speakerId` is otherwise valid) — the speaker filter always implies span
// membership.
export function lineMatchesSpeaker(index: SpanIndex, book: number, line: number, speakerId: string): boolean {
  const candidates = index.get(book);
  if (!candidates) return false;
  return candidates.some((s) => s.speaker.includes(speakerId) && lineInSpeech(s, line));
}

// Where a hit's words stand: the Greek line of token `pos` of r's section (from
// offsets.json), and the line a translation's word `word` is read at (from the
// book's ticks, lib/english-place englishLines). Null: not known.
export interface SpeechPlace {
  grkLine(r: SearchResult, pos: number): number | null;
  engLine(r: SearchResult, translation: string, word: number): number | null;
}

// The results held to the speech filter (the new search page's spk / spo):
// each Greek word, and each English word, kept when its line passes. A match
// of several words (a window, a phrase) stands or falls by its first word,
// where it is cited. A word whose line is not known is not kept. A result left
// with no hit in either language goes.
export function speechCut(
  results: SearchResult[],
  filter: SpeechFilter,
  spans: Record<string, SpanIndex | undefined>,
  place: SpeechPlace,
): SearchResult[] {
  const passes = (work: string, book: number, line: number | null) => {
    const idx = spans[work];
    if (!idx || line === null) return false;
    return filter.kind === 'speaker'
      ? lineMatchesSpeaker(idx, book, line, filter.id)
      : lineInAnySpeech(idx, book, line);
  };
  return results.flatMap(r => {
    const book = r.meta.book;
    let out = r;
    if (r.grkMatch) {
      const ok = new Map(r.grkPositions.map(p => [p, passes(r.work, book, place.grkLine(r, p))]));
      for (const w of r.windows ?? []) for (const p of w) ok.set(p, ok.get(w[0]) ?? false);
      out = cutPositions(r, r.grkPositions.map(p => ok.get(p) ?? false));
    }
    const engHits = (r.engHits ?? []).flatMap(h => {
      const keep = (w: number) => passes(r.work, book, place.engLine(r, h.translation, w));
      if (h.matches) {
        const heads = h.matches.filter(keep);
        if (!heads.length) return [];
        // A phrase's words go with the head they follow.
        const positions = h.positions.filter(p => {
          const head = h.matches!.filter(m => m <= p).at(-1);
          return head === undefined ? keep(p) : heads.includes(head);
        });
        return [{ ...h, positions, matches: heads }];
      }
      const positions = h.positions.filter(keep);
      return positions.length ? [{ ...h, positions }] : [];
    });
    const grkMatch = r.grkMatch && out.grkPositions.length > 0;
    const engMatch = engHits.length > 0;
    if (!grkMatch && !engMatch) return [];
    return [{ ...out, grkMatch, engMatch, ...(r.engHits ? { engHits } : {}) }];
  });
}
