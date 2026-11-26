import { describe, expect, it } from 'vitest';
import { hasGreek, rankBooks, rankLemmata, rankWorks } from '../lib/palette';
import type { LemmaRef } from '../lib/data';

// Note: citation parsing for the palette is delegated to the work's own
// citation scheme (shared/lib/citation.ts, tested in citation.test.ts) rather
// than duplicated here — the palette library owns only the Greek/work/lemma
// ranking below.

describe('hasGreek', () => {
  it('detects polytonic and monotonic Greek', () => {
    expect(hasGreek('λόγος')).toBe(true);
    expect(hasGreek('ἀρετή')).toBe(true);
    expect(hasGreek('justice')).toBe(false);
    expect(hasGreek('34b')).toBe(false);
  });
});

describe('rankWorks', () => {
  it('ranks a title-prefix match first', () => {
    const r = rankWorks('ili');
    expect(r[0]?.id).toBe('iliad');
  });
  it('matches a Homer abbreviation, ignoring its trailing dot', () => {
    // "Il." → "il"; "Od." → "od"; both are exact-abbr (top-tier) hits.
    expect(rankWorks('il')[0]?.id).toBe('iliad');
    expect(rankWorks('od')[0]?.id).toBe('odyssey');
  });
  it('matches on the id', () => {
    expect(rankWorks('odyssey').some((w) => w.id === 'odyssey')).toBe(true);
  });
  it('returns nothing for an empty query', () => {
    expect(rankWorks('  ')).toEqual([]);
  });
  it('caps the result count', () => {
    expect(rankWorks('a', undefined, 3).length).toBeLessThanOrEqual(3);
  });
});

describe('rankBooks', () => {
  it('keeps the canonical Iliad-then-Odyssey order and offers eight books on open', () => {
    expect(rankBooks('', undefined, 8).map((x) => x.label)).toEqual([
      'Iliad · Book 1 (Α)', 'Iliad · Book 2 (Β)', 'Iliad · Book 3 (Γ)', 'Iliad · Book 4 (Δ)',
      'Iliad · Book 5 (Ε)', 'Iliad · Book 6 (Ζ)', 'Iliad · Book 7 (Η)', 'Iliad · Book 8 (Θ)',
    ]);
  });
  it('matches work names, book numerals, and the epic Greek-letter convention', () => {
    expect(rankBooks('od').every((x) => x.work.id === 'odyssey')).toBe(true);
    expect(rankBooks('9').map((x) => `${x.work.id}:${x.book}`)).toEqual([
      'iliad:9', 'iliad:19', 'odyssey:9', 'odyssey:19',
    ]);
    expect(rankBooks('ι').map((x) => `${x.work.id}:${x.book}`)).toEqual(['iliad:9', 'odyssey:9']);
    expect(rankBooks('ω').map((x) => `${x.work.id}:${x.book}`)).toEqual(['iliad:24', 'odyssey:24']);
  });
});

describe('rankLemmata', () => {
  const lemmata: Record<string, LemmaRef> = {
    'lo/gos': { slug: 'logos', head: 'λόγος', count: 100 },
    'le/gw': { slug: 'lego', head: 'λέγω', count: 500 },
    'lu/w': { slug: 'luo', head: 'λύω', count: 5 },
    'a)reth/': { slug: 'arete', head: 'ἀρετή', count: 300 },
  };
  it('prefix-matches on the folded headword, frequency-ranked', () => {
    const r = rankLemmata('λ', lemmata);
    expect(r.map((x) => x.slug)).toEqual(['lego', 'logos', 'luo']);
  });
  it('accent-insensitive matching', () => {
    expect(rankLemmata('λογο', lemmata).map((x) => x.slug)).toEqual(['logos']);
  });
  it('respects the limit', () => {
    expect(rankLemmata('λ', lemmata, 1).map((x) => x.slug)).toEqual(['lego']);
  });
  it('empty for non-matching input', () => {
    expect(rankLemmata('ζζζ', lemmata)).toEqual([]);
  });
});

// ── Round 3: the site-wide Go-to ────────────────────────────────────────────
import { SITE_PAGES, nameEntries, rankLemmaSlugs, rankNames, searchPath, verseCitations } from '../lib/palette';

import { ALL_NAV_PATHS } from '../../app/src/lib/site-nav';

describe('SITE_PAGES', () => {
  it('offers only pages the site header links, at the same paths', () => {
    for (const page of SITE_PAGES) expect(ALL_NAV_PATHS, page.label).toContain(page.path);
  });
});

describe('verseCitations', () => {
  it('reads a bare citation in both poems where no poem is open, Iliad first', () => {
    expect(verseCitations('6.237')).toEqual([
      { work: 'iliad', book: 6, line: 237 },
      { work: 'odyssey', book: 6, line: 237 },
    ]);
  });
  it('reads a bare citation in the open poem first, then the other', () => {
    expect(verseCitations('9.105', 'odyssey').map((c) => c.work)).toEqual(['odyssey', 'iliad']);
  });
  it('a work prefix names one poem, whatever is open', () => {
    expect(verseCitations('Od 9.105')).toEqual([{ work: 'odyssey', book: 9, line: 105 }]);
    expect(verseCitations('Il. 6.237', 'odyssey')).toEqual([{ work: 'iliad', book: 6, line: 237 }]);
    expect(verseCitations('odyssey 23')).toEqual([{ work: 'odyssey', book: 23, line: null }]);
  });
  it('offers nothing for a book neither poem has, or for words', () => {
    expect(verseCitations('25.1')).toEqual([]);
    expect(verseCitations('Il. 99.1', 'odyssey')).toEqual([]);
    expect(verseCitations('ithaca')).toEqual([]);
    expect(verseCitations('')).toEqual([]);
  });
});

describe('rankNames', () => {
  const entries = [
    ...SITE_PAGES,
    ...nameEntries(
      [{ id: 'ithaca', name: 'Ithaca', greek: 'Ἰθάκη' }, { id: 'tomb-hector', name: 'The tomb of Hector', greek: 'σῆμα Ἕκτορος' }, { id: 'troy', name: 'Troy', greek: 'Τροίη' }],
      [{ id: 'hector', name: 'Hector', greek: 'Ἕκτωρ' }, { id: 'odysseus', name: 'Odysseus', greek: 'Ὀδυσσεύς' }],
    ),
  ];
  it('finds a place and links the anchor its page renders', () => {
    const [hit] = rankNames('ithaca', entries);
    expect(hit).toMatchObject({ kind: 'Place', label: 'Ithaca', path: '/places/#place-ithaca' });
  });
  it('puts the name itself before a longer name that holds it', () => {
    expect(rankNames('hector', entries).map((e) => e.path)).toEqual(['/characters/#roster-hector', '/places/#place-tomb-hector']);
  });
  it('finds a page by its name or what readers call it', () => {
    expect(rankNames('timeline', entries)[0]?.path).toBe('/timeline/');
    expect(rankNames('family trees', entries)[0]?.path).toBe('/genealogies/');
    expect(rankNames('map', entries)[0]?.path).toBe('/maps/');
  });
  it('needs three letters unless the name is spelled in full', () => {
    expect(rankNames('od', entries)).toEqual([]);
    expect(rankNames('tr', entries)).toEqual([]);
    expect(rankNames('tro', entries).map((e) => e.label)).toEqual(['Troy']);
  });
  it('matches a Greek name with its accents and breathing left off', () => {
    expect(rankNames('ιθακη', entries)[0]?.label).toBe('Ithaca');
    expect(rankNames('Ἕκτωρ', entries)[0]?.label).toBe('Hector');
  });
  it('ignores an empty query and caps the list', () => {
    expect(rankNames('  ', entries)).toEqual([]);
    expect(rankNames('the', entries, 1).length).toBeLessThanOrEqual(1);
  });
});

describe('rankLemmaSlugs', () => {
  const lemmata: Record<string, LemmaRef> = {
    'mh=nis': { slug: 'menis', head: 'μῆνις', count: 18 },
    'mhni/w': { slug: 'menio', head: 'μηνίω', count: 14 },
    'me/nos': { slug: 'menos', head: 'μένος', count: 300 },
  };
  it('finds a word by the Latin spelling its page is served at', () => {
    expect(rankLemmaSlugs('menis', lemmata)[0]?.head).toBe('μῆνις');
  });
  it('puts the exact slug before more frequent words that only start with it', () => {
    const ranked = rankLemmaSlugs('men', lemmata).map((l) => l.slug);
    expect(ranked).toEqual(['menos', 'menis', 'menio']);
    expect(rankLemmaSlugs('menos', lemmata)[0]?.slug).toBe('menos');
  });
  it('wants three plain letters', () => {
    expect(rankLemmaSlugs('me', lemmata)).toEqual([]);
    expect(rankLemmaSlugs('6.237', lemmata)).toEqual([]);
  });
});

describe('searchPath', () => {
  it('hands the query to the search page, encoded', () => {
    expect(searchPath(' wine-dark sea ')).toBe('/search?q=wine-dark%20sea');
    expect(searchPath('μῆνις')).toBe(`/search?q=${encodeURIComponent('μῆνις')}`);
    expect(searchPath('  ')).toBe('/search');
  });
});
