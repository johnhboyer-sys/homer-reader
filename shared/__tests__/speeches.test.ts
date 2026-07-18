import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  classifySpeech,
  realLinesFromSegments,
  humanizeSpeaker,
  speakerDisplayName,
  speechLabel,
} from '../lib/speeches';
import type { Speech, CharacterEntry } from '../lib/data';

// A synthetic book-9-shaped line set (real Od. 9 has no numbering gap, so a
// plain contiguous range is representative for the non-gap fixtures below).
function contiguousLines(lo: number, hi: number): Set<number> {
  const s = new Set<number>();
  for (let n = lo; n <= hi; n++) s.add(n);
  return s;
}

// Real Od. 10's line set MINUS line 456 — the one confirmed vulgate gap this
// module's docstring cites (manifests/Odyssey.yaml's expected_line_gaps:
// {book: 10, after: 455, next: 457}).
function od10LinesWithGap(): Set<number> {
  const s = contiguousLines(1, 574);
  s.delete(456);
  return s;
}

describe('classifySpeech — confidence degrade rule', () => {
  it('level 0, non-crossBook, real lines: renders a rail', () => {
    const chryses: Speech = {
      id: 'iliad-1', book: 1, lines: [17, 21],
      speaker: ['chryses'], addressee: ['agamemnon', 'greeks'],
      level: 0, cluster: 1001, part: 1, type: 'G',
    };
    const result = classifySpeech(chryses, [chryses], contiguousLines(1, 611));
    expect(result).toEqual({ mode: 'rail' });
  });

  it('the two Apologoi crossBook frames degrade at their opening line, never a whole-book rail', () => {
    // Od. 9.2-11.332 (odyssey-890) and Od. 11.378-12.453 (odyssey-957) — see
    // apparatus/speeches/odyssey.json and apparatus_speeches.py's docstring.
    const frame1: Speech = {
      id: 'odyssey-890', book: 9, lines: [2, 332],
      speaker: ['odysseus'], addressee: ['alcinous'],
      level: 0, cluster: 2077, part: 2, type: 'G', crossBook: true,
    };
    const frame2: Speech = {
      id: 'odyssey-957', book: 11, lines: [378, 453],
      speaker: ['odysseus'], addressee: ['alcinous'],
      level: 0, cluster: 2105, part: 6, type: 'G', crossBook: true,
    };
    const r1 = classifySpeech(frame1, [frame1], contiguousLines(1, 566));
    const r2 = classifySpeech(frame2, [frame2], contiguousLines(1, 640));
    expect(r1.mode).toBe('degraded');
    expect(r2.mode).toBe('degraded');
    expect(r1.reason).toMatch(/nested telling/i);
    expect(r2.reason).toMatch(/nested telling/i);
  });

  it('a clean level-1 fully inside a same-book (even crossBook) level-0 parent renders a rail', () => {
    // odyssey-890 is the book-9 frame; Polyphemus's exchange with Odysseus
    // (odyssey-892..895, lines well past the frame's literal lines[1]=332,
    // which belongs to book 11 — see the crossBook doc comment) must still
    // nest cleanly, since it never leaves book 9.
    const frame: Speech = {
      id: 'odyssey-890', book: 9, lines: [2, 332],
      speaker: ['odysseus'], addressee: ['alcinous'],
      level: 0, cluster: 2077, part: 2, type: 'G', crossBook: true,
    };
    const polyphemus: Speech = {
      id: 'odyssey-892', book: 9, lines: [447, 460],
      speaker: ['polyphemus'], addressee: ['ram'],
      level: 1, cluster: 2082, part: 1, type: 'M',
    };
    const bookSpeeches = [frame, polyphemus];
    const result = classifySpeech(polyphemus, bookSpeeches, contiguousLines(1, 566));
    expect(result).toEqual({ mode: 'rail' });
  });

  it('a level-1 speech recorded in a DIFFERENT book than its narrative frame degrades (honest "same book" limit)', () => {
    // Book 10 (entirely inside the Apologoi) has no level-0 speech of its own
    // — the enclosing frame is recorded under book 9 — so a book-10 level-1
    // speech has no same-book parent and correctly degrades.
    const circe: Speech = {
      id: 'odyssey-940', book: 10, lines: [15, 20],
      speaker: ['circe'], addressee: ['odysseus'],
      level: 1, cluster: 2090, part: 1, type: 'G',
    };
    const result = classifySpeech(circe, [circe], contiguousLines(1, 574));
    expect(result.mode).toBe('degraded');
    expect(result.reason).toMatch(/no clean level-0 span/i);
  });

  it('level >= 2 always degrades', () => {
    const parent: Speech = {
      id: 'x-1', book: 5, lines: [1, 50], speaker: ['a'], addressee: ['b'],
      level: 0, cluster: 1, part: 1, type: 'G',
    };
    const grandchild: Speech = {
      id: 'x-2', book: 5, lines: [10, 12], speaker: ['c'], addressee: ['d'],
      level: 2, cluster: 2, part: 1, type: 'G',
    };
    const result = classifySpeech(grandchild, [parent, grandchild], contiguousLines(1, 50));
    expect(result).toEqual({ mode: 'degraded', reason: 'nested speech (level 2)' });
  });

  it('a span whose line falls on a real vulgate gap degrades with a gap reason (odyssey-931, Od. 10.456)', () => {
    const circesWarning: Speech = {
      id: 'odyssey-931', book: 10, lines: [456, 465],
      speaker: ['circe'], addressee: ['odysseus'],
      level: 1, cluster: 2096, part: 1, type: 'M',
    };
    const result = classifySpeech(circesWarning, [circesWarning], od10LinesWithGap());
    expect(result.mode).toBe('degraded');
    expect(result.reason).toMatch(/vulgate numbering gap/i);
  });

  it('an unresolved (empty) speaker or addressee degrades defensively', () => {
    const broken: Speech = {
      id: 'x-3', book: 1, lines: [1, 2], speaker: [], addressee: ['a'],
      level: 0, cluster: 1, part: 1, type: 'G',
    };
    expect(classifySpeech(broken, [broken], contiguousLines(1, 10)).mode).toBe('degraded');
  });
});

describe('humanizeSpeaker / speakerDisplayName / speechLabel', () => {
  const chars = new Map<string, CharacterEntry>([
    ['achilles', { id: 'achilles', name: 'Achilles', greek: 'Ἀχιλλεύς' }],
    ['agamemnon', { id: 'agamemnon', name: 'Agamemnon' }],
  ]);

  it('title-cases a raw multi-word DICES name', () => {
    expect(humanizeSpeaker('companions of odysseus')).toBe('Companions Of Odysseus');
  });

  it('turns a trailing ".N" disambiguator into "(N)"', () => {
    expect(humanizeSpeaker('greek.3')).toBe('Greek (3)');
  });

  it('never invents a characters.json identification — falls back to humanized text', () => {
    // "chryses" has no apparatus/characters.json entry (only "chryseis", his
    // daughter, does), yet Chryses's plea (Il. 1.17-21) must still label.
    expect(speakerDisplayName('chryses', chars)).toBe('Chryses');
  });

  it('uses the real characters.json name when present', () => {
    expect(speakerDisplayName('achilles', chars)).toBe('Achilles');
  });

  it('builds a "SPEAKER → ADDRESSEE" label, joining multiple names with " & "', () => {
    const s: Speech = {
      id: 'iliad-1', book: 1, lines: [17, 21], speaker: ['chryses'],
      addressee: ['agamemnon', 'greeks'], level: 0, cluster: 1, part: 1, type: 'G',
    };
    expect(speechLabel(s, chars)).toBe('Chryses → Agamemnon & Greeks');
  });
});

describe('realLinesFromSegments', () => {
  it('collects every greek line n across all segments', () => {
    const segs = [{ greek: [{ n: 1 }, { n: 2 }] }, { greek: [{ n: 3 }] }];
    expect(realLinesFromSegments(segs)).toEqual(new Set([1, 2, 3]));
  });
});

// ── Real-corpus regression: the exact fixtures cited above actually exist in
// the committed apparatus data, so the doc comments/tests can't silently
// drift from the DICES import (mirrors maps.test.ts's real-apparatus checks).
describe('speeches.json / characters.json — real apparatus regression', () => {
  it('the two Apologoi frame speeches are crossBook, level 0, and match the cited spans', () => {
    const raw = JSON.parse(readFileSync('../apparatus/speeches/odyssey.json', 'utf-8'));
    const byId = new Map(raw.speeches.map((s: Speech) => [s.id, s]));
    const frame1 = byId.get('odyssey-890') as Speech;
    const frame2 = byId.get('odyssey-957') as Speech;
    expect(frame1).toMatchObject({ book: 9, lines: [2, 332], level: 0, crossBook: true });
    expect(frame2).toMatchObject({ book: 11, lines: [378, 453], level: 0, crossBook: true });
  });

  it('odyssey-931 sits on the confirmed Od. 10.456 vulgate gap', () => {
    const raw = JSON.parse(readFileSync('../apparatus/speeches/odyssey.json', 'utf-8'));
    const gap = raw.speeches.find((s: Speech) => s.id === 'odyssey-931');
    expect(gap).toMatchObject({ book: 10, lines: [456, 465] });
  });

  it('"chryses" has no apparatus/characters.json entry (the unmatched-but-legible case)', () => {
    const raw = JSON.parse(readFileSync('../apparatus/characters.json', 'utf-8'));
    const ids = new Set(raw.characters.map((c: CharacterEntry) => c.id));
    expect(ids.has('chryses')).toBe(false);
    expect(humanizeSpeaker('chryses')).toBe('Chryses');
  });

  it('counts: iliad has 0 crossBook speeches; odyssey has exactly 2', () => {
    const iliad = JSON.parse(readFileSync('../apparatus/speeches/iliad.json', 'utf-8'));
    const odyssey = JSON.parse(readFileSync('../apparatus/speeches/odyssey.json', 'utf-8'));
    expect(iliad.speeches.filter((s: Speech) => s.crossBook).length).toBe(0);
    expect(odyssey.speeches.filter((s: Speech) => s.crossBook).length).toBe(2);
  });
});
