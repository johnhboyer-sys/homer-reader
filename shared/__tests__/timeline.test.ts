import { describe, expect, it } from 'vitest';
import { buildDayStrip, parseDayRange, totalDays, type BookInput } from '../lib/timeline';

describe('parseDayRange', () => {
  it('parses a range, a single day, and absent/malformed input', () => {
    expect(parseDayRange('40-51')).toEqual([40, 51]);
    expect(parseDayRange('22')).toEqual([22, 22]);
    expect(parseDayRange(null)).toBeNull();
    expect(parseDayRange(undefined)).toBeNull();
    expect(parseDayRange('')).toBeNull();
    expect(parseDayRange('bogus')).toBeNull();
  });
});

describe('buildDayStrip', () => {
  it('folds same-day and connective-null scenes into one day entry', () => {
    const books: BookInput[] = [
      {
        book: 1,
        dayRange: [1, 1],
        scenes: [
          { lines: [1, 7], dayNumber: null, summary: 'proem' },
          { lines: [43, 52], dayNumber: 1, summary: 'Apollo shoots' },
          { lines: [53, 60], dayNumber: 1, summary: 'plague continues' },
        ],
      },
    ];
    const strip = buildDayStrip(books);
    expect(strip.entries).toEqual([{ kind: 'day', dayNumber: 1, book: 1, line: 43 }]);
    expect(strip.bookRanges).toEqual([{ book: 1, startIndex: 0, endIndex: 1 }]);
  });

  it('turns a gap between dated scenes into a span, anchored at the intervening null scene', () => {
    // Il. 1's 9-day plague (day 1 -> day 10) then 12-day divine absence
    // (day 10 -> day 21), matching build/dist/iliad/book-01.json.
    const books: BookInput[] = [
      {
        book: 1,
        dayRange: [1, 21],
        scenes: [
          { lines: [43, 52], dayNumber: 1, summary: 'Apollo shoots' },
          { lines: [53, 100], dayNumber: 10, summary: 'nine days the plague rages' },
          { lines: [488, 492], dayNumber: null, summary: 'Achilles nurses his anger' },
          { lines: [493, 530], dayNumber: 21, summary: 'twelfth dawn, gods return' },
        ],
      },
    ];
    const strip = buildDayStrip(books);
    expect(strip.entries).toEqual([
      { kind: 'day', dayNumber: 1, book: 1, line: 43 },
      // No null scene sits between day 1 and day 10 in this fixture, so the
      // gap anchors at the day-10 scene itself (no summary carried).
      {
        kind: 'span', fromDay: 1, toDay: 10, spanDays: 8,
        book: 1, line: 53, summary: undefined,
      },
      { kind: 'day', dayNumber: 10, book: 1, line: 53 },
      {
        kind: 'span', fromDay: 10, toDay: 21, spanDays: 10,
        book: 1, line: 488, summary: 'Achilles nurses his anger',
      },
      { kind: 'day', dayNumber: 21, book: 1, line: 493 },
    ]);
  });

  it('closes a trailing span from the book day range when the poem never narrates the terminus', () => {
    // Il. 24: last dated scene day 41, book range runs to 51 (the truce's
    // nine-days-wood-then-cremation close, told but not day-scened).
    const books: BookInput[] = [
      {
        book: 24,
        dayRange: [40, 51],
        scenes: [
          { lines: [31, 54], dayNumber: 40, summary: 'twelfth day, Apollo protests' },
          { lines: [695, 717], dayNumber: 41, summary: 'dawn, Priam nears Troy' },
          { lines: [777, 804], dayNumber: null, summary: 'nine days wood, tenth cremation' },
        ],
      },
    ];
    const strip = buildDayStrip(books);
    expect(strip.entries).toEqual([
      { kind: 'day', dayNumber: 40, book: 24, line: 31 },
      { kind: 'day', dayNumber: 41, book: 24, line: 695 },
      {
        kind: 'span', fromDay: 41, toDay: null, spanDays: 10,
        book: 24, line: 777, summary: 'nine days wood, tenth cremation',
      },
    ]);
    expect(totalDays(strip)).toBe(51);
  });

  it('spans a book boundary (Il. 23 day 28 -> Il. 24 day 40, the twelve-day maltreatment)', () => {
    const books: BookInput[] = [
      { book: 23, dayRange: [26, 28], scenes: [{ lines: [1, 10], dayNumber: 28, summary: 'funeral games end' }] },
      { book: 24, dayRange: [40, 40], scenes: [
        { lines: [1, 30], dayNumber: null, summary: 'each night Achilles drags the body' },
        { lines: [31, 54], dayNumber: 40, summary: 'twelfth day, Apollo protests' },
      ] },
    ];
    const strip = buildDayStrip(books);
    expect(strip.entries).toEqual([
      { kind: 'day', dayNumber: 28, book: 23, line: 1 },
      {
        kind: 'span', fromDay: 28, toDay: 40, spanDays: 11,
        book: 24, line: 1, summary: 'each night Achilles drags the body',
      },
      { kind: 'day', dayNumber: 40, book: 24, line: 31 },
    ]);
    // The span is anchored in book 24 (where the connective scene lives),
    // so it belongs to book 24's range, not book 23's.
    expect(strip.bookRanges).toEqual([
      { book: 23, startIndex: 0, endIndex: 1 },
      { book: 24, startIndex: 1, endIndex: 3 },
    ]);
  });

  it('keeps a flat run of same-day scenes across several books as one day (Od. Day 34 Apologoi)', () => {
    const books: BookInput[] = [
      { book: 8, dayRange: [34, 34], scenes: [{ lines: [1, 5], dayNumber: 34, summary: 'games' }] },
      { book: 9, dayRange: [34, 34], scenes: [{ lines: [1, 14], dayNumber: 34, summary: 'Odysseus names himself' }] },
      { book: 12, dayRange: [34, 34], scenes: [{ lines: [447, 453], dayNumber: 34, summary: 'reaches Ogygia' }] },
    ];
    const strip = buildDayStrip(books);
    expect(strip.entries).toEqual([{ kind: 'day', dayNumber: 34, book: 8, line: 1 }]);
  });

  it('does not run a day number backward for an out-of-order dayNumber', () => {
    const books: BookInput[] = [
      {
        book: 1,
        dayRange: null,
        scenes: [
          { lines: [1, 5], dayNumber: 5, summary: 'later day first' },
          { lines: [6, 10], dayNumber: 3, summary: 'earlier day number' },
        ],
      },
    ];
    const strip = buildDayStrip(books);
    // No span/backward day is fabricated; the second scene is recorded as
    // its own day entry (the caller is responsible for treating a decreasing
    // sequence as analepsis, not this module).
    expect(strip.entries).toEqual([
      { kind: 'day', dayNumber: 5, book: 1, line: 1 },
      { kind: 'day', dayNumber: 3, book: 1, line: 6 },
    ]);
  });
});
