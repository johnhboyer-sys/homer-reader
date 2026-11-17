import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { englishQueryUnits, englishWords, greekFold, search, searchPhraseVariants } from '../lib/search';

const meta = [
  { id: 's1', book: 1, column: '1094a' },
  { id: 's2', book: 1, column: '1094b' },
  { id: 's3', book: 2, column: '1100a' },
];

const greekIndex = {
  logos: [[0, 0], [1, 1]],
  areth: [[0, 1]],
  yuxh: [[1, 0]],
  texnh: [[2, 0]],
} satisfies Record<string, [number, number][]>;

// The index shape since the port: {word: [[seg_idx, word_pos], ...]}.
// s1 "virtue is a habit of choice", s2 "happiness and virtue together",
// s3 "craft concerns making".
const englishIndex = {
  virtue: [[0, 0], [1, 2]],
  habit: [[0, 3]],
  choice: [[0, 5]],
  happiness: [[1, 0]],
  and: [[1, 1]],
  craft: [[2, 0]],
  making: [[2, 2]],
} satisfies Record<string, [number, number][]>;

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

  it('lists each term\'s words for "all words" of several terms, for the scene join', async () => {
    const [grk] = (await search('logos areth', '', 'all', 'all', 'and', ['TAllTerms'])).results;
    expect(grk.grkTerms).toEqual([[0], [1]]);
    const [eng] = (await search('', 'virtue habit', 'all', 'all', 'and', ['TAllUnits'])).results;
    expect(eng.engHits?.[0].units).toEqual([[0], [3]]);
    // One term, or any word, or a phrase: nothing to join. Each finds
    // something, or every() would pass on nothing (Codex review of e03973358).
    const one = (await search('logos', 'virtue', 'all', 'all', 'or', ['TAllOne'])).results;
    expect(one.length).toBeGreaterThan(0);
    expect(one.every(r => !r.grkTerms && !r.engHits?.some(h => h.units))).toBe(true);
    const any = (await search('logos areth', 'virtue habit', 'any', 'any', 'or', ['TAnyNone'])).results;
    expect(any.length).toBeGreaterThan(0);
    expect(any.every(r => !r.grkTerms && !r.engHits?.some(h => h.units))).toBe(true);
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
    expect(hits[0].engHits).toEqual([{ translation: 'english', positions: [0, 1, 2], matches: [0] }]);
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
  const partialMeta = [{ id: 'p1', book: 1, column: '1', }];
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

describe('English words and positions', () => {
  const longText = `${'filler word '.repeat(60)}the crux is that one shall avail nothing`;
  const words = englishWords(longText).map(w => w.word);
  const at = words.indexOf('shall');
  const engMeta = [{ id: 's1', book: 1, column: '406a' }];
  const engIndex = {
    filler: words.flatMap((w, i) => (w === 'filler' ? [[0, i]] : [])),
    word: words.flatMap((w, i) => (w === 'word' ? [[0, i]] : [])),
    shall: [[0, at]], avail: [[0, at + 1]],
  };
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

  it('finds a phrase far past the old 500-character cap', async () => {
    expect(longText.indexOf('shall avail')).toBeGreaterThan(500);
    const { results } = await search('', 'shall avail', 'all', 'phrase', 'and', ['TEng500']);
    expect(results).toHaveLength(1);
    expect(results[0].engHits?.[0].matches).toEqual([at]);
  });

  it('counts every repeat of a word in a segment', async () => {
    const { results } = await search('', 'word', 'all', 'all', 'and', ['TEngCount']);
    expect(results).toHaveLength(1);
    expect(results[0].engHits?.[0].positions).toHaveLength(60);
  });
});

// A hyphenated query used to find nothing: the old englishFold stripped the
// hyphen, so "rosy-fingered" was looked up as the one word "rosyfingered",
// which the index never holds. The index splits at the hyphen (englishWords),
// and a typed term splits the same way, its parts standing in a row.
describe('a hyphenated English query', () => {
  const text = 'Dawn came, rosy-fingered Dawn, and the sea was wine-dark.';
  const words = englishWords(text).map(w => w.word);
  const idx: Record<string, [number, number][]> = {};
  words.forEach((w, i) => (idx[w] ??= []).push([0, i]));

  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const path = String(url);
      if (path.endsWith('/meta.json')) return json([{ id: 'h1', book: 1, column: '1' }]);
      if (path.endsWith('/english.json')) return json(idx);
      if (path.endsWith('/greek_lemma.json') || path.endsWith('/greek_form.json')) return json({});
      return Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as Response);
    });
  });
  afterEach(() => vi.restoreAllMocks());

  it('splits at the hyphen, as the index does', () => {
    expect(words).toContain('rosy');
    expect(words).toContain('fingered');
    expect(words).not.toContain('rosyfingered');
    expect(englishQueryUnits('rosy-fingered dawn')).toEqual([['rosy', 'fingered'], ['dawn']]);
  });

  it('finds "rosy-fingered dawn" as the words "rosy-fingered Dawn"', async () => {
    const { results } = await search('', 'rosy-fingered dawn', 'all', 'phrase', 'and', ['THyphen']);
    expect(results.map(r => r.meta.id)).toEqual(['h1']);
    expect(results[0].engHits?.[0].matches).toEqual([words.indexOf('rosy')]);
  });

  it('finds a hyphenated term alone, and a term whose parts are not in a row finds nothing', async () => {
    expect((await search('', 'wine-dark', 'all', 'all', 'and', ['THyphen2'])).results).toHaveLength(1);
    expect((await search('', 'dark-wine', 'all', 'all', 'and', ['THyphen3'])).results).toHaveLength(0);
  });
});
