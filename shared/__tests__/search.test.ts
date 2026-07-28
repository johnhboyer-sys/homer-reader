import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { englishOccurrences, greekFold, search, searchPhraseVariants } from '../lib/search';

const meta = [
  { id: 's1', book: 1, column: '1094a', greek_head: 'λόγος ἀρετή', greek_tokens: 'logos areth', english_head: 'virtue is a habit of choice' },
  { id: 's2', book: 1, column: '1094b', greek_head: 'ψυχή λόγος', greek_tokens: 'yuxh logos', english_head: 'happiness and virtue together' },
  { id: 's3', book: 2, column: '1100a', greek_head: 'τέχνη', greek_tokens: 'texnh', english_head: 'craft concerns making' },
];

const greekIndex = {
  logos: [[0, 0], [1, 1]],
  areth: [[0, 1]],
  yuxh: [[1, 0]],
  texnh: [[2, 0]],
} satisfies Record<string, [number, number][]>;

const englishIndex = {
  virtue: [0, 1],
  habit: [0],
  choice: [0],
  happiness: [1],
  and: [1],
  craft: [2],
  making: [2],
} satisfies Record<string, number[]>;

function json(data: unknown) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(data) } as Response);
}

describe('greekFold', () => {
  it.each([
    ['λόγος', 'logos'],
    ['lo/gos', 'logos'],
    ['*a)nqrwpos', 'anqrwpos'],
    ["ἀρετή'", "areth'"],
    ['ψυχή κόσμος', 'yuxhkosmos'],
  ])('folds %s', (input, expected) => {
    expect(greekFold(input)).toBe(expected);
  });
});

describe('search', () => {
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const path = String(url);
      if (path.endsWith('/meta.json')) return json(meta);
      if (path.endsWith('/greek_lemma.json') || path.endsWith('/greek_form.json')) return json(greekIndex);
      if (path.endsWith('/english.json')) return json(englishIndex);
      return Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as Response);
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns no results for empty queries or no works', async () => {
    await expect(search('', ' ', 'all', 'all', 'and', ['TEmpty'])).resolves.toEqual({ results: [], failedWorks: [] });
    await expect(search('logos', '', 'all', 'all', 'and', [])).resolves.toEqual({ results: [], failedWorks: [] });
  });

  it('supports all, any, and phrase modes', async () => {
    expect((await search('logos areth', '', 'all', 'all', 'and', ['TAll'])).results).toHaveLength(1);
    expect((await search('yuxh areth', '', 'any', 'all', 'and', ['TAny'])).results).toHaveLength(2);
    expect((await search('logos areth', '', 'phrase', 'all', 'and', ['TPhraseMiss'])).results).toHaveLength(1);
    expect((await search('areth logos', '', 'phrase', 'all', 'and', ['TPhraseHit'])).results).toHaveLength(0);
  });

  it('supports wildcards for Greek and English terms', async () => {
    const greek = (await search('tex*', '', 'all', 'all', 'and', ['TGreekWildcard'])).results;
    const english = (await search('', 'hap*', 'all', 'all', 'and', ['TEngWildcard'])).results;
    expect(greek.map((r) => r.meta.id)).toEqual(['s3']);
    expect(english.map((r) => r.meta.id)).toEqual(['s2']);
  });

  it('matches a mid-word Greek * without widening it to a prefix', async () => {
    const matching = (await search('l*s', '', 'all', 'all', 'and', ['TGreekMidStar'])).results;
    const missing = (await search('l*x', '', 'all', 'all', 'and', ['TGreekMidStarMiss'])).results;
    expect(matching.map((r) => r.meta.id)).toEqual(['s1', 's2']);
    expect(missing).toHaveLength(0);
  });

  it('makes Greek ? match exactly one fold character', async () => {
    const one = (await search('l?gos', '', 'all', 'all', 'and', ['TGreekQ1'])).results;
    const zero = (await search('l?ogos', '', 'all', 'all', 'and', ['TGreekQ2'])).results;
    const two = (await search('l?os', '', 'all', 'all', 'and', ['TGreekQ3'])).results;
    expect(one.map((r) => r.meta.id)).toEqual(['s1', 's2']);
    expect(zero).toHaveLength(0);
    expect(two).toHaveLength(0);
  });

  it('makes English ? match exactly one fold character', async () => {
    const one = (await search('', 'c?aft', 'all', 'all', 'and', ['TEngQ1'])).results;
    const zero = (await search('', 'c?raft', 'all', 'all', 'and', ['TEngQ2'])).results;
    expect(one.map((r) => r.meta.id)).toEqual(['s3']);
    expect(zero).toHaveLength(0);
  });

  it('allows a wildcard inside an English phrase', async () => {
    // The phrase check must keep the wildcard: folding it away would leave
    // `happ* and virtue` looking for the literal token "happ".
    const hits = (await search('', 'happ* and virtue', 'phrase', 'phrase', 'and', ['TEngPhraseWild'])).results;
    expect(hits.map((r) => r.meta.id)).toEqual(['s2']);
    expect(hits[0].engPositions).toEqual([0]);
  });

  it('combines Greek and English boxes with AND or OR', async () => {
    const andHits = (await search('logos', 'happiness', 'all', 'all', 'and', ['TAnd'])).results;
    const orHits = (await search('texnh', 'happiness', 'all', 'all', 'or', ['TOr'])).results;
    expect(andHits.map((r) => r.meta.id)).toEqual(['s2']);
    expect(orHits.map((r) => r.meta.id)).toEqual(['s2', 's3']);
  });

  it.each([
    ['whitespace only', '   ', '\t'],
    ['pure punctuation', '!!!', '...'],
    ['regex metacharacters', '.*+?^${}()|[]\\', '.*+?^${}()|[]\\'],
    ['Greek string', 'λόγος τέχνη', 'virtue'],
    ['very long string', `${'logos '.repeat(500)}texnh`, `${'virtue '.repeat(500)}craft`],
  ])('does not throw for adversarial input: %s', async (_label, grk, eng) => {
    await expect(search(grk, eng, 'any', 'any', 'or', [`TAdv-${_label}`])).resolves.toMatchObject({
      results: expect.any(Array),
      failedWorks: expect.any(Array),
    });
  });
});

// T4 / T1. grkPositions are token positions in the FLATTENED surface token list
// of the segment's Greek — every token counted, keyless ones included — because
// Search.svelte's accent post-filter and greekKwic index that list directly.
// The old phrase check walked meta.greek_tokens, which is built SKIPPING keyless
// tokens, so its positions were indices into a shorter list and drifted by one
// per keyless token before the match. Postings count every token, so posting
// adjacency fixes this by construction.
describe('Greek phrase positions index the full token list', () => {
  // Four surface tokens; the second ('ἄειδε') has no Beta Code key, so it is
  // absent from greek_tokens but still occupies token position 1.
  const gapMeta = [{
    id: 'g1', book: 1, column: '1',
    greek_head: 'μῆνιν ἄειδε θεά Πηληϊάδεω',
    greek_tokens: 'mhnin qea phlhiadew',
    english_head: '',
  }];
  const gapIndex = {
    mhnin: [[0, 0]],
    qea: [[0, 2]],
    phlhiadew: [[0, 3]],
  } satisfies Record<string, [number, number][]>;

  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const path = String(url);
      if (path.endsWith('/meta.json')) return json(gapMeta);
      if (path.endsWith('/greek_lemma.json') || path.endsWith('/greek_form.json')) return json(gapIndex);
      return Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as Response);
    });
  });
  afterEach(() => vi.restoreAllMocks());

  it('reports surface-token indices, not fold-stream indices', async () => {
    const { results } = await search('qea phlhiadew', '', 'phrase', 'all', 'and', ['TFullTok'], 'form');
    expect(results).toHaveLength(1);
    // Surface positions 2 and 3. The fold stream would have said 1 and 2.
    expect(results[0].grkPositions).toEqual([2, 3]);
  });

  it('will not join two words the keyless token separates', async () => {
    // mhnin@0 and qea@2 are adjacent in greek_tokens but not in the text.
    const { results } = await search('mhnin qea', '', 'phrase', 'all', 'and', ['TFullTokGap'], 'form');
    expect(results).toHaveLength(0);
  });
});

describe('lemma search resolves an inflected word to its headword', () => {
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const path = String(url);
      if (path.endsWith('/meta.json')) return json(meta);
      if (path.endsWith('/greek_lemma.json') || path.endsWith('/greek_form.json')) return json(greekIndex);
      if (path.endsWith('/english.json')) return json(englishIndex);
      // fold(surface) -> the headwords it can belong to
      if (path.endsWith('/lemma-map/l.json')) return json({ logou: ['logos'], logos: ['logos'] });
      return Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as Response);
    });
  });
  afterEach(() => vi.restoreAllMocks());

  it('finds the whole word from a form the reader met on the page', async () => {
    const { results } = await search('logou', '', 'all', 'all', 'and', ['TInflected'], 'lemma');
    expect(results.map((r) => r.meta.id)).toEqual(['s1', 's2']);
  });

  it('still finds it when the reader types the dictionary form', async () => {
    const { results } = await search('logos', '', 'all', 'all', 'and', ['TDictForm'], 'lemma');
    expect(results.map((r) => r.meta.id)).toEqual(['s1', 's2']);
  });

  it('does not resolve in form mode, where the typed spelling is the query', async () => {
    const { results } = await search('logou', '', 'all', 'all', 'and', ['TFormMode'], 'form');
    expect(results).toEqual([]);
  });
});

describe('searchPhraseVariants falls back to the typed word when the map does not record it', () => {
  // logos@0 and xyz@1 sit adjacent in one segment, so the phrase matches under
  // the one reading that pairs logos's headword with xyz exactly as typed.
  const partialMeta = [{ id: 'p1', book: 1, column: '1', greek_head: '', greek_tokens: '', english_head: '' }];
  const partialIndex = {
    logos: [[0, 0]],
    xyz: [[0, 1]],
  } satisfies Record<string, [number, number][]>;

  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const path = String(url);
      if (path.endsWith('/meta.json')) return json(partialMeta);
      if (path.endsWith('/greek_lemma.json')) return json(partialIndex);
      if (path.endsWith('/lemma-map/l.json')) return json({ logos: ['logos'] });
      // The shard for xyz's letter loads fine but does not record the word —
      // this is the "unrecorded word" case, not a missing-map failure.
      if (path.endsWith('/lemma-map/x.json')) return json({});
      return Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as Response);
    });
  });
  afterEach(() => vi.restoreAllMocks());

  it('widens the recorded word and keeps the unrecorded one as typed', async () => {
    const { readings, results } = await searchPhraseVariants('logos xyz', ['TPartial']);
    expect(readings).toEqual([['logos', 'xyz']]);
    expect(results.map((r) => r.meta.id)).toEqual(['p1']);
  });
});

describe('englishOccurrences', () => {
  it('returns one offset per matching token (repeats counted)', () => {
    // #11: "socrates" three times -> three offsets, not one.
    const text = 'Socrates asked; then Socrates replied, and Socrates smiled.';
    expect(englishOccurrences(text, ['socrates'], 'all')).toHaveLength(3);
  });

  it('finds a phrase whose occurrence is past the old 500-char cap', () => {
    // #5: the phrase sits well beyond character 500; token-based matching still finds it.
    const filler = 'word '.repeat(200);           // ~1000 chars
    const text = `${filler}you shall avail yourself of it`;
    const offs = englishOccurrences(text, ['shall', 'avail'], 'phrase');
    expect(offs).toHaveLength(1);
    expect(offs[0]).toBeGreaterThan(500);
  });

  it('matches whole tokens and prefix wildcards, not substrings', () => {
    const text = 'virtue and virtues and virtuous';
    expect(englishOccurrences(text, ['virtue'], 'all')).toHaveLength(1);   // not "virtues"/"virtuous"
    expect(englishOccurrences(text, ['virtu*'], 'all')).toHaveLength(3);   // prefix hits all three
  });

  it('accepts the same wildcards the index does', () => {
    const text = 'happiness and holiness';
    expect(englishOccurrences(text, ['hap*ness'], 'all')).toHaveLength(1);
    expect(englishOccurrences(text, ['h?liness'], 'all')).toHaveLength(1);
  });
});

describe('search English occurrences (index integration)', () => {
  const longText = `${'filler word '.repeat(60)}the crux is that one shall avail nothing`;
  const engMeta = [
    { id: 's1', book: 1, column: '406a', greek_head: '', greek_tokens: '', english_head: longText },
  ];
  const engIndex = { shall: [0], avail: [0], filler: [0], word: [0], the: [0] };
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const path = String(url);
      if (path.endsWith('/meta.json')) return json(engMeta);
      if (path.endsWith('/english.json')) return json(engIndex);
      if (path.endsWith('/greek_lemma.json') || path.endsWith('/greek_form.json')) return json({});
      return Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as Response);
    });
  });
  afterEach(() => vi.restoreAllMocks());

  it('phrase past char 500 is found (regression for the [:500] truncation)', async () => {
    const idx = longText.toLowerCase().indexOf('shall avail');
    expect(idx).toBeGreaterThan(500);
    const { results } = await search('', 'shall avail', 'all', 'phrase', 'and', ['TEng500']);
    expect(results).toHaveLength(1);
    expect(results[0].engPositions).toEqual([idx]);
  });

  it('counts repeated English occurrences per segment', async () => {
    const { results } = await search('', 'word', 'all', 'all', 'and', ['TEngCount']);
    expect(results).toHaveLength(1);
    // "word" appears 60 times in the filler.
    expect(results[0].engPositions).toHaveLength(60);
  });
});
