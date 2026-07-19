import { describe, expect, it } from 'vitest';
import {
  formatCite,
  formatCopyCitation,
  formatVerseCitation,
  parseVerseCitation,
  scheme,
  schemeFor,
} from '../lib/citation';

// The verse-line scheme + its work-aware jump/citation helpers, exercised
// against the REAL registry (iliad/odyssey) — no mocks. The vulgate lineation
// is sacred: a line is a user-facing citation target, joined to the book with a
// dot ("Il. 1.1", "Od. 9.366").

describe('verse-line per-scheme contract', () => {
  const s = scheme('verse-line');

  it('is registered with user-facing lines', () => {
    expect(s.id).toBe('verse-line');
    expect(s.hasUserFacingLines).toBe(true);
    expect(schemeFor('iliad').id).toBe('verse-line');
    expect(schemeFor('odyssey').id).toBe('verse-line');
  });

  it('parses a bare book and a book.line, rejecting letter tokens and ranges', () => {
    expect(s.parseColumnToken('9')).toBe('9');
    expect(s.parseColumnToken('9a')).toBeNull();
    expect(s.parseLocation('9')).toEqual({ column: '9', line: null });
    expect(s.parseLocation('9.366')).toEqual({ column: '9', line: 366 }); // citation dot form
    expect(s.parseLocation('9:366')).toEqual({ column: '9', line: 366 }); // ?loc= colon form
    expect(s.parseLocation('9a')).toBeNull();
    expect(s.parseLocation('1.1-7')).toBeNull();  // no range grammar (matches inherited)
    expect(s.parseLocation('')).toBeNull();
  });

  it('formats book.line with a dot, or the bare book with no line', () => {
    expect(s.formatCitation('9', 366)).toBe('9.366');
    expect(s.formatCitation('9', null)).toBe('9');
    expect(s.formatCitation('9')).toBe('9');
    // The work-agnostic composer follows the scheme (within-work, no abbr).
    expect(formatCite('odyssey', '9', 366)).toBe('9.366');
  });
});

describe('parseVerseCitation — jump box grammar', () => {
  it('accepts an abbr prefix with dot/space separators', () => {
    expect(parseVerseCitation('Od. 9.366')).toEqual({ work: 'odyssey', book: 9, line: 366 });
    expect(parseVerseCitation('od 9 366')).toEqual({ work: 'odyssey', book: 9, line: 366 });
    expect(parseVerseCitation('il 2.494')).toEqual({ work: 'iliad', book: 2, line: 494 });
  });

  it('accepts a full-title prefix (longest match wins over a shorter abbr)', () => {
    expect(parseVerseCitation('Iliad 2.494')).toEqual({ work: 'iliad', book: 2, line: 494 });
    expect(parseVerseCitation('Odyssey 9.366')).toEqual({ work: 'odyssey', book: 9, line: 366 });
  });

  it('reads a bare book.line in the current work context', () => {
    expect(parseVerseCitation('9.366', 'odyssey')).toEqual({ work: 'odyssey', book: 9, line: 366 });
    expect(parseVerseCitation('2.494', 'iliad')).toEqual({ work: 'iliad', book: 2, line: 494 });
    expect(parseVerseCitation('9', 'odyssey')).toEqual({ work: 'odyssey', book: 9, line: null });
  });

  it('range-checks the book against the work and rejects invalid input', () => {
    expect(parseVerseCitation('25.1', 'iliad')).toBeNull();  // Iliad has 24 books
    expect(parseVerseCitation('0.1', 'iliad')).toBeNull();
    expect(parseVerseCitation('9.366')).toBeNull();          // no current work, no prefix
    expect(parseVerseCitation('banana', 'iliad')).toBeNull();
    expect(parseVerseCitation('', 'iliad')).toBeNull();
    expect(parseVerseCitation('1.1-7', 'iliad')).toBeNull(); // range: no grammar for it
  });
});

describe('verse citation round-trips (parse → format)', () => {
  it('"od 9 366" -> {odyssey, 9, 366} -> "Od. 9.366"', () => {
    const p = parseVerseCitation('od 9 366');
    expect(p).toEqual({ work: 'odyssey', book: 9, line: 366 });
    expect(formatVerseCitation(p!.work, p!.book, p!.line)).toBe('Od. 9.366');
  });

  it('"Iliad 2.494" -> {iliad, 2, 494} -> "Il. 2.494"', () => {
    const p = parseVerseCitation('Iliad 2.494');
    expect(formatVerseCitation(p!.work, p!.book, p!.line)).toBe('Il. 2.494');
  });

  it('"9.366" in current-work context -> "Od. 9.366"', () => {
    const p = parseVerseCitation('9.366', 'odyssey');
    expect(formatVerseCitation(p!.work, p!.book, p!.line)).toBe('Od. 9.366');
  });

  it('formats a whole-book reference without a line', () => {
    expect(formatVerseCitation('iliad', 1)).toBe('Il. 1');
  });
});

describe('formatCopyCitation — author-prefixed, translator-suffixed', () => {
  it('bilingual view names the active translator', () => {
    expect(formatCopyCitation('iliad', 1, 1, 'Murray')).toBe('Hom. Il. 1.1, trans. Murray');
    expect(formatCopyCitation('odyssey', 9, 366, 'Murray')).toBe('Hom. Od. 9.366, trans. Murray');
  });

  it('Greek-only view drops the translator suffix', () => {
    expect(formatCopyCitation('iliad', 1, 1)).toBe('Hom. Il. 1.1');
    expect(formatCopyCitation('odyssey', 9, 366, null)).toBe('Hom. Od. 9.366');
  });
});
