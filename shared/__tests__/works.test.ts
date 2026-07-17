import { describe, expect, it } from 'vitest';
import { SHELVES, START_HERE, WORKS, bookLabel, furtherReading, getWork, inPrintHref, isBookless, visibleTranslations, workLanding, workPath, type Work } from '../lib/works';

// A fixture multi-book Work exercises bookLabel/workPath's generic numbering
// logic without depending on a real registry entry — every Plato work carried
// so far is bookless (books: 1), so a fixture stands in for a multi-book work.
const multiBookFixture: Work = {
  id: 'FixtureMultiBook',
  title: 'Fixture Multi-Book Work',
  abbr: 'Fix.',
  author: 'Test',
  books: 10,
  bookLabels: ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'],
  greekEdition: 'Test edition',
  greekSource: { short: 'Test', full: 'Test edition, full citation.' },
  translations: [{ id: 'test', name: 'Test Translator (Test, 1900)', short: 'Test', slot: 'english' }],
  blurb: 'A fixture multi-book work for exercising bookLabel/workPath generic logic.',
};

describe('works registry helpers', () => {
  it('normalizes book labels using a fixture multi-book work', () => {
    expect(bookLabel(multiBookFixture, 1)).toBe('I');
    expect(bookLabel(multiBookFixture, 99)).toBe('99'); // out of range -> falls back to the raw number
  });

  it('clamps workPath to a real registry work\'s book range', () => {
    const iliad = getWork('iliad');
    expect(iliad?.books).toBe(24);
    expect(workPath('iliad', 99)).toBe('/iliad/book/24');  // over the top -> clamped to 24
    expect(workPath('iliad', -3)).toBe('/iliad/book/1');
    expect(workLanding('iliad')).toBe('/iliad');
  });

  it('reports non-bookless works and visible translations', () => {
    // Both Homeric epics are 24-book works — no Homer work is bookless.
    const iliad = getWork('iliad');
    expect(iliad && isBookless(iliad)).toBe(false);
    expect(iliad && visibleTranslations(iliad).every((t) => !t.private)).toBe(true);
    expect(WORKS.length).toBe(2);
  });

  it('adds runtime extra translations without mutating the registry entry', () => {
    const iliad = getWork('iliad')!;
    (globalThis as { __ARISTOTLE_EXTRA_TRANSLATIONS__?: unknown }).__ARISTOTLE_EXTRA_TRANSLATIONS__ = {
      iliad: [{ id: 'mine', name: 'Local Import', short: 'Local', slot: 'overlay' }],
    };
    expect(visibleTranslations(iliad).map((t) => t.id)).toContain('mine');
    delete (globalThis as { __ARISTOTLE_EXTRA_TRANSLATIONS__?: unknown }).__ARISTOTLE_EXTRA_TRANSLATIONS__;
  });

  it('creates stable in-print links from curated metadata (empty for this rollout)', () => {
    // No Homer work has curated FURTHER_READING metadata yet — the function
    // still resolves to an empty array rather than throwing.
    expect(furtherReading('iliad')).toEqual([]);
    expect(inPrintHref({ kind: 'translation', cite: 'A <em>Book</em> & commentary' })).toBe(
      'https://www.google.com/search?tbm=bks&q=A%20Book%20%26%20commentary',
    );
  });
});

describe('home-page thematic shelves (SHELVES)', () => {
  const shelfIds = SHELVES.flatMap((s) => s.works.map((w) => w.id).filter((id): id is string => Boolean(id)));

  it('carries every work in WORKS exactly once across the shelves', () => {
    // The two-work Homer rollout uses a single "The Epics" shelf.
    expect(SHELVES.length).toBe(1);
    // Every real work appears exactly once.
    for (const w of WORKS) {
      const count = shelfIds.filter((id) => id === w.id).length;
      expect(count, `${w.id} should appear in exactly one shelf, found ${count}`).toBe(1);
    }
    // No stray/unknown ids and no duplicates overall.
    expect(shelfIds.length).toBe(WORKS.length);
    expect(new Set(shelfIds).size).toBe(shelfIds.length);
    for (const id of shelfIds) expect(getWork(id)).toBeDefined();
  });

  it('never surfaces the retired "Tetralogy" grouping name in user-facing shelf/work data', () => {
    const haystacks = [
      ...SHELVES.map((s) => s.title),
      ...SHELVES.map((s) => s.numeral),
      ...WORKS.map((w) => w.title),
      ...WORKS.map((w) => w.blurb),
    ];
    for (const s of haystacks) expect(s).not.toMatch(/tetralogy/i);
  });
});

describe('"Start here" featured strip (START_HERE)', () => {
  it('lists both epics, in order, each resolving to a real work', () => {
    expect(START_HERE).toEqual(['iliad', 'odyssey']);
    for (const id of START_HERE) expect(getWork(id), `${id} should be a real WORKS entry`).toBeDefined();
  });
});

describe('traditional dating (Work.period)', () => {
  it('keeps period optional and valid; the Homeric epics carry no Platonic period', () => {
    for (const w of WORKS) {
      if (w.period) expect(['early', 'middle', 'late']).toContain(w.period);
    }
    // period is a Platonic-chronology concept — not applicable to Homer.
    expect(getWork('iliad')?.period).toBeUndefined();
    expect(getWork('odyssey')?.period).toBeUndefined();
  });
});
