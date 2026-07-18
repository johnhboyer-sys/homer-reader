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
