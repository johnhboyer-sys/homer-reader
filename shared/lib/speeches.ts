// DICES speech-span rendering logic (Phase 4, reader feature): pure
// classification + label helpers consumed by shared/components/Reader.svelte.
// No DOM, no fetch — see shared/lib/data.ts for fetchSpeeches/fetchCharacters
// and docs/APPARATUS-SCHEMAS.md for the speeches.json contract. Homer-only;
// no plato-reader counterpart (Plato's corpus carries no DICES apparatus).

import type { Speech, CharacterEntry } from './data';

export type SpeechRenderMode = 'rail' | 'degraded';

export interface SpeechClassification {
  mode: SpeechRenderMode;
  // Human-readable reason, present only when degraded (used as the flagged
  // marker's tooltip/aria-label).
  reason?: string;
}

// ── Confidence classification (the registry's CONFIDENCE DEGRADE RULE) ─────
//
// Full rendering (a rail) ONLY for high-confidence spans: level 0, and
// "clean" level 1 (fully inside a level-0 span in the SAME book). Everything
// else degrades to a marker at the span's opening line:
//   - crossBook (the two Apologoi frame speeches: Od. 9.2-11.332,
//     11.378-12.453) — never painted as a rail across the books they cross.
//   - level >= 2 (deeper narrative-within-speech nesting).
//   - a line landing on a real vulgate numbering gap in THIS book (e.g.
//     odyssey-931, "10.456" — the Od. 10.456 line this edition's Perseus
//     grc2 text omits; see the manifest's expected_line_gaps and
//     apparatus_speeches.py's `check_line`, which reports this at BUILD time
//     but does not annotate the emitted JSON, so the reader re-derives it
//     against the actually-rendered book's real line set).
//   - a level-1 speech with no clean level-0 container in its own book (see
//     `bookSpeeches` below — this also naturally degrades every level-1
//     speech whose *recorded* book differs from its narrative frame's book,
//     e.g. Od. 10 and Od. 12's speeches, whose containing frame is recorded
//     under book 9 / 11 respectively: a real, honest limitation of the
//     "same book" predicate, not a bug — see the classifySpeech docstring).
//   - an unresolvable speaker/addressee (empty array on either side; DICES
//     always resolves to at least a lowercase raw name in the data observed
//     2026-07-17, so this is a defensive floor, not an observed case).
//
// A speaker/addressee string with NO apparatus/characters.json entry (e.g.
// "chryses", "greeks", "companions of odysseus" — the majority of DICES
// names; see apparatus_speeches.py's join report) is NOT, by itself, a
// degrade trigger: it renders with a humanized label (humanizeSpeaker below),
// the same "never invents an identification, but never blocks display
// either" posture shared/lib/maps.ts's leaderDisplayName/humanizeId already
// establish for Catalogue leaders. Chryses's plea (Il. 1.17-21, speaker
// "chryses", unmatched) is the concrete case this decision is built to
// render as a full rail, per the reader's own verification script.

// `bookSpeeches`: every speech (any level) recorded under the SAME `book` as
// `speech` — used to find a containing level-0 parent for the "clean level
// 1" check. `realLines`: the vulgate line numbers actually printed for that
// book (from the fetched BookData's segments — see realLinesFromSegments).
export function classifySpeech(
  speech: Speech,
  bookSpeeches: Speech[],
  realLines: Set<number>,
): SpeechClassification {
  if (!speech.speaker.length || !speech.addressee.length) {
    return { mode: 'degraded', reason: 'speaker or addressee unresolved' };
  }
  if (speech.crossBook) {
    return { mode: 'degraded', reason: 'nested telling — a speech spanning multiple books' };
  }
  if (speech.level >= 2) {
    return { mode: 'degraded', reason: `nested speech (level ${speech.level})` };
  }
  if (!realLines.has(speech.lines[0]) || !realLines.has(speech.lines[1])) {
    return { mode: 'degraded', reason: 'a line in this span falls on a vulgate numbering gap' };
  }
  if (speech.level === 0) return { mode: 'rail' };
  // level === 1: clean only if fully inside a level-0 speech recorded under
  // the same book. A crossBook parent's lines[1] belongs to a LATER book (see
  // the Speech doc comment in data.ts), so it cannot cap containment within
  // THIS book — only the parent's opening line is checked for a crossBook
  // parent (the parent is known to extend to the book's end and beyond).
  const parent = bookSpeeches.find((p) =>
    p.level === 0 &&
    p.book === speech.book &&
    p.lines[0] <= speech.lines[0] &&
    (p.crossBook || p.lines[1] >= speech.lines[1]),
  );
  if (parent) return { mode: 'rail' };
  return { mode: 'degraded', reason: 'nested speech has no clean level-0 span in this book' };
}

// The real (emitted) vulgate line numbers for a book, from its fetched
// segments — loosely typed so this module never needs to import the
// (larger, Svelte-adjacent) Segment/GreekLine shapes from data.ts.
export function realLinesFromSegments(segments: { greek: { n: number }[] }[]): Set<number> {
  const s = new Set<number>();
  for (const seg of segments) for (const line of seg.greek) s.add(line.n);
  return s;
}

// Turn a raw, unjoined DICES name ("greek.3", "companions of odysseus") into
// a plain-text display label. A trailing ".N" disambiguator (DICES's own
// convention for anonymous same-named participants) becomes "(N)"; every
// other word is title-cased. Never invents an identification — this is
// formatting only, the same posture as shared/lib/maps.ts's humanizeId.
export function humanizeSpeaker(raw: string): string {
  const m = raw.match(/^(.*)\.(\d+)$/);
  const base = m ? m[1] : raw;
  const suffix = m ? ` (${m[2]})` : '';
  const titled = base.replace(/\b\p{L}/gu, (c) => c.toUpperCase());
  return titled + suffix;
}

// One speaker/addressee id's display name: the real apparatus/characters.json
// name when present, else the humanized raw string.
export function speakerDisplayName(
  id: string,
  charactersById: Map<string, CharacterEntry>,
): string {
  return charactersById.get(id)?.name ?? humanizeSpeaker(id);
}

// The margin label for a speech's opening line: "ACHILLES → AGAMEMNON" (the
// small-caps rendering is CSS — this returns plain text). Multiple speakers
// or addressees join with " & ".
export function speechLabel(speech: Speech, charactersById: Map<string, CharacterEntry>): string {
  const names = (ids: string[]) => ids.map((id) => speakerDisplayName(id, charactersById)).join(' & ');
  return `${names(speech.speaker)} → ${names(speech.addressee)}`;
}
