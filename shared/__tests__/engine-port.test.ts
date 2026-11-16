// The Homer-side pieces the ported search engine needs from works, citation,
// data and text, and the two search.ts exports Phrases.svelte imports.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AUTHENTIC_IDS, HAS_SPEAKERS, SEARCH_GROUPS, WORKS, getWork, searchableTranslations } from '../lib/works';
import { formatCite } from '../lib/citation';
import { fetchLemmaGlosses, fetchLemmaPickerShard } from '../lib/data';
import { esc } from '../lib/text';
import { lineStarts, unitRange } from '../lib/search';

describe('works registry, as the search engine reads it', () => {
  it('lists every translation of each epic, in registry order, by slot', () => {
    for (const id of ['iliad', 'odyssey']) {
      expect(searchableTranslations(getWork(id)!).map((t) => [t.id, t.slot]))
        .toEqual([['murray', 'english'], ['butler', 'ross'], ['pope', 'third'], ['kosmos', 'overlay']]);
    }
  });
  it('names both epics authentic, one search group, and no speaker panel', () => {
    expect(AUTHENTIC_IDS).toEqual(WORKS.map((w) => w.id));
    expect(SEARCH_GROUPS.flatMap((g) => g.ids)).toEqual(['iliad', 'odyssey']);
    expect(HAS_SPEAKERS).toBe(false);
  });
});

describe('formatCite', () => {
  it('cites book.line, and ignores a lettered-line suffix Homer never has', () => {
    expect(formatCite('iliad', '9', 366)).toBe('9.366');
    expect(formatCite('iliad', '9', 366, 'a')).toBe('9.366a');
    expect(formatCite('iliad', '9')).toBe('9');
  });
});

describe('text.esc', () => {
  it('escapes markup', () => expect(esc('<b>&')).toBe('&lt;b&gt;&amp;'));
});

describe('search.ts exports Phrases.svelte imports', () => {
  const offsets = {
    token_count: 8, seg_base_offset: [0],
    segments: [{ book: 1, column: '1', line_runs: [[1, 3], [2, 5]] as [number, number][] }],
    book_bounds: [{ book: 1, start: 0 }],
  };
  it('finds line starts and the line a token is on', () => {
    expect(lineStarts(offsets)).toEqual([0, 3]);
    expect(unitRange([0, 3], 4, 8)).toEqual([3, 8]);
    expect(unitRange([0, 3], 1, 8)).toEqual([0, 3]);
  });
});

describe('lemma picker and glosses', () => {
  afterEach(() => vi.restoreAllMocks());
  it('reads a picker shard, and refuses a stale one', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const u = String(url);
      const body = u.endsWith('/lemma-picker/a.json') ? { a: { n: 2, c: [{ h: 'ἀ', k: 'a' }] } }
        : u.endsWith('/lemma-picker/b.json') ? { b: { n: 2 } } : { glosses: ['wrath'] };
      return Promise.resolve({ ok: true, json: async () => body } as Response);
    });
    expect((await fetchLemmaPickerShard('a')).a.n).toBe(2);
    await expect(fetchLemmaPickerShard('b')).rejects.toThrow(/stale/);
    expect(await fetchLemmaGlosses('menis')).toEqual(['wrath']);
  });
});
