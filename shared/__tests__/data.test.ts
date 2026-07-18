import { afterEach, describe, expect, it, vi } from 'vitest';
import { activeSceneIndex, cunliffeShard, fetchBook, fetchCunliffeShard, fetchFootnotes, fetchLsjShard, fetchRepetitions, invalidateBookCache, lookupWord, lsjShard, normalizeBookData, parseBekker, parseLocation, resolveBekker, stripBookForClient, type Scene } from '../lib/data';

function mockFetch(map: Record<string, unknown>) {
  vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
    const key = Object.keys(map).find((part) => String(url).includes(part));
    if (!key) return Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as Response);
    return Promise.resolve({ ok: true, json: async () => map[key] } as Response);
  });
}

afterEach(() => {
  vi.restoreAllMocks();
  delete (globalThis as { __ARISTOTLE_BOOK_HOOK__?: unknown }).__ARISTOTLE_BOOK_HOOK__;
});

describe('parseBekker and resolveBekker', () => {
  it.each([
    ['1097a15', { column: '1097a', line: 15 }],
    ['1097a 15', { column: '1097a', line: 15 }],
    ['1097A.15', { column: '1097a', line: 15 }],
    ['  1000b2  ', { column: '1000b', line: 2 }],
    ['not a citation', null],
    // The citation-scheme contract's column grammar is shared a-e across
    // schemes (pipeline/homer_pipeline/scheme.py's `_COLUMN_RE`/`_REF_RE`),
    // so parseBekker — now a thin wrapper over the bekker scheme — accepts
    // c/d/e too; real column membership is still gated by resolveBekker
    // against columns.json, not by this grammar.
    ['1097c15', { column: '1097c', line: 15 }],
    ['1097f15', null], // outside a-e: still rejected
    ['1097a', null],   // bare column, no line: not a *Bekker* citation
  ])('parses %s', (raw, expected) => {
    expect(parseBekker(raw)).toEqual(expected);
  });

  it('resolves columns and snaps shared-column gaps to the nearest book', () => {
    const columns = {
      '1097a': [{ book: 1, lo: 1, hi: 20 }],
      '1100b': [{ book: 1, lo: 1, hi: 8 }, { book: 2, lo: 14, hi: 20 }],
    };
    expect(resolveBekker(columns, '1097a', 10)).toBe(1);
    expect(resolveBekker(columns, '1100b', 4)).toBe(1);
    expect(resolveBekker(columns, '1100b', 12)).toBe(2);
    expect(resolveBekker(columns, '999a', 1)).toBeNull();
  });
});

describe('parseLocation (per-work scheme dispatch)', () => {
  it('parses a bekker work\'s bare column and column:line forms', () => {
    expect(parseLocation('EN', '1097a')).toEqual({ column: '1097a', line: null });
    expect(parseLocation('EN', '1097a:15')).toEqual({ column: '1097a', line: 15 });
    expect(parseLocation('EN', '1097a15')).toEqual({ column: '1097a', line: 15 });
  });

  it('parses a busse-scheme work the same way — it has user-facing lines '
    + '(no busse work is in the registry right now, so this exercises the '
    + 'unknown-work bekker default, which shares busse\'s hasUserFacingLines)', () => {
    expect(parseLocation('NoSuchWork', '1a')).toEqual({ column: '1a', line: null });
    expect(parseLocation('NoSuchWork', '1a:5')).toEqual({ column: '1a', line: 5 });
  });

  it('falls back to bekker for an unknown work id', () => {
    expect(parseLocation('NoSuchWork', '1097a:15')).toEqual({ column: '1097a', line: 15 });
  });
});

describe('activeSceneIndex (scene-rail current-scene mapping)', () => {
  const scenes: Scene[] = [
    { summary: 'a', startLine: 1 },
    { summary: 'b', startLine: 8 },
    { summary: 'c', startLine: 53 },
  ];
  it.each([
    [1, 0],     // first line of the first scene
    [7, 0],     // still inside the first scene's span
    [8, 1],     // opening line of the second scene
    [52, 1],    // inside the second scene
    [53, 2],    // opening line of the third
    [900, 2],   // past the last opening → last scene
    [0, 0],     // before every scene → first scene
  ])('line %i → scene %i', (line, expected) => {
    expect(activeSceneIndex(scenes, line)).toBe(expected);
  });
  it('returns -1 when there are no scenes', () => {
    expect(activeSceneIndex([], 5)).toBe(-1);
  });
  it('is order-independent (unsorted scene list)', () => {
    const unsorted: Scene[] = [
      { summary: 'c', startLine: 53 },
      { summary: 'a', startLine: 1 },
      { summary: 'b', startLine: 8 },
    ];
    expect(activeSceneIndex(unsorted, 52)).toBe(2); // the startLine:8 scene
    expect(activeSceneIndex(unsorted, 53)).toBe(0); // the startLine:53 scene
  });
});

describe('fetch and lookup helpers', () => {
  it('fetchRepetitions loads the corpus-wide index once and retries failures', async () => {
    mockFetch({
      'repetitions.json': [{ key: 'x', text: 'ἄνδρα', count: 2, refs: [] }],
    });
    await expect(fetchRepetitions()).resolves.toEqual([
      { key: 'x', text: 'ἄνδρα', count: 2, refs: [] },
    ]);
  });
  it('fetchBook normalizes emitted apparatus.scenes into top-level Scene[]', async () => {
    mockFetch({
      'ScenesWork/book-01.json': {
        book: 1,
        segments: [],
        apparatus: {
          argument: 'The quarrel.',
          draft: true,
          scenes: [
            { lines: [1, 7], summary: 'Invocation.', location: 'Achaean camp', dayNumber: 1 },
            { lines: [8, 52], summary: 'Chryses is refused.', location: 'Achaean camp', dayNumber: 1 },
          ],
        },
      },
    });
    const d = await fetchBook('ScenesWork', 1);
    expect(d.scenes).toEqual([
      { summary: 'Invocation.', startLine: 1, endLine: 7, place: 'Achaean camp', day: 1 },
      { summary: 'Chryses is refused.', startLine: 8, endLine: 52, place: 'Achaean camp', day: 1 },
    ]);
  });

  it('normalizeBookData carries the scene day (dayNumber → day), null included', () => {
    const raw = {
      book: 1,
      segments: [],
      apparatus: {
        scenes: [
          { lines: [1, 7] as [number, number], summary: 'Proem.', location: 'proem', dayNumber: null },
          { lines: [8, 52] as [number, number], summary: 'Chryses.', location: 'camp', dayNumber: 2 },
        ],
      },
    };
    const d = normalizeBookData(raw);
    expect(d.scenes).toEqual([
      { summary: 'Proem.', startLine: 1, endLine: 7, place: 'proem', day: null },
      { summary: 'Chryses.', startLine: 8, endLine: 52, place: 'camp', day: 2 },
    ]);
  });

  it('fetchBook leaves scenes absent when the payload has no apparatus', async () => {
    mockFetch({ 'NoScenesWork/book-01.json': { book: 1, segments: [] } });
    const d = await fetchBook('NoScenesWork', 1);
    expect(d.scenes).toBeUndefined();
  });

  // The SSR path (ReaderShell.astro's readFileSync + JSON.parse) calls the same
  // normalization the fetch path does, so a static page's bookData.scenes has the
  // reader's Scene shape — not the raw apparatus.scenes the old raw-parse left it.
  it('normalizeBookData is the shared SSR-path normalizer (apparatus.scenes → Scene[])', () => {
    const raw = {
      book: 1,
      segments: [],
      apparatus: {
        draft: true,
        scenes: [{ lines: [1, 7] as [number, number], summary: 'Invocation.', location: 'proem' }],
      },
    };
    const d = normalizeBookData(raw);
    expect(d.scenes).toEqual([{ summary: 'Invocation.', startLine: 1, endLine: 7, place: 'proem' }]);
    // The raw apparatus (the cartouche's draft flag + sibling fields) is preserved.
    expect((d as typeof raw).apparatus.draft).toBe(true);
  });

  it('normalizeBookData leaves an already-normalized book untouched', () => {
    const scenes = [{ summary: 'x', startLine: 1 }];
    const d = normalizeBookData({ book: 1, segments: [], scenes });
    expect(d.scenes).toBe(scenes);
  });

  it('stripBookForClient drops Greek tokens + non-default translations, keeps the rest', () => {
    const full = {
      book: 1,
      scenes: [{ summary: 'Invocation.', startLine: 1 }],
      segments: [{
        id: '1:1', column: '1',
        greek: [{ n: 1, text: 'μῆνιν ἄειδε', tokens: [
          { t: 'μῆνιν', o: 0, k: 'mh=nin' }, { t: 'ἄειδε', o: 6, k: 'a)/eide' },
        ] }],
        english: { text: 'The wrath sing', notes: [], markers: [] },
        ross: [{ chapter: '1', text: 'Butler', cont: false }],
        third: [{ chapter: '1', text: 'Pope', cont: false }],
      }],
    };
    const client = stripBookForClient(full);
    // Tokens emptied on the copy; text/english/scenes preserved.
    expect(client.segments[0].greek[0].tokens).toEqual([]);
    expect(client.segments[0].greek[0].text).toBe('μῆνιν ἄειδε');
    expect(client.segments[0].english).toEqual(full.segments[0].english);
    expect(client.scenes).toEqual(full.scenes);
    expect(client.tokensStripped).toBe(true);
    // Non-default translations dropped (fetched on demand).
    expect(client.segments[0].ross).toBeUndefined();
    expect(client.segments[0].third).toBeUndefined();
    // Input is left intact (the server render still uses the full book).
    expect(full.segments[0].greek[0].tokens).toHaveLength(2);
    expect(full.segments[0].ross).toBeDefined();
  });

  it('fetchBook returns JSON data and applies the runtime hook', async () => {
    mockFetch({
      'HookWork/book-01.json': { book: 1, segments: [] },
    });
    (globalThis as { __ARISTOTLE_BOOK_HOOK__?: unknown }).__ARISTOTLE_BOOK_HOOK__ = vi.fn((_work, _n, data) => ({
      ...data,
      segments: [{ id: 'hooked', column: '1a', greek: [], english: null }],
    }));

    await expect(fetchBook('HookWork', 1)).resolves.toMatchObject({
      book: 1,
      segments: [{ id: 'hooked' }],
    });
  });

  it('invalidateBookCache forces a re-fetch that re-runs the book hook', async () => {
    // Two fetches of the same book normally hit the promise cache once — the
    // hook runs a single time. This is the desktop import staleness bug: a
    // re-import updates the hook's overlay data, but the open book keeps its
    // first (pre-import) hook result until the cache is dropped.
    mockFetch({ 'EvictWork/book-01.json': { book: 1, segments: [] } });
    const hook = vi.fn((_work, _n, data) => data);
    (globalThis as { __ARISTOTLE_BOOK_HOOK__?: unknown }).__ARISTOTLE_BOOK_HOOK__ = hook;

    await fetchBook('EvictWork', 1);
    await fetchBook('EvictWork', 1);
    expect(hook).toHaveBeenCalledTimes(1);           // cached: hook ran once

    invalidateBookCache('EvictWork');
    await fetchBook('EvictWork', 1);
    expect(hook).toHaveBeenCalledTimes(2);           // evicted: re-fetch re-ran the hook

    // A different work's cache is untouched by the eviction.
    invalidateBookCache('OtherWork');
    await fetchBook('EvictWork', 1);
    expect(hook).toHaveBeenCalledTimes(2);           // still cached — no spurious re-fetch
  });

  it('fetchFootnotes linkifies glossary references for EN only', async () => {
    mockFetch({
      'EN/footnotes.json': { '1': 'See Glossary, <em>hexis</em>.' },
      'DA/footnotes.json': { '1': 'See Glossary, <em>hexis</em>.' },
    });

    await expect(fetchFootnotes('EN')).resolves.toMatchObject({
      '1': expect.stringContaining('class="gloss-ref"'),
    });
    await expect(fetchFootnotes('DA')).resolves.toMatchObject({
      '1': 'See Glossary, <em>hexis</em>.',
    });
  });

  it('selects LSJ shards and de-duplicates lookupWord dictionary entries', async () => {
    mockFetch({
      'LookupWork/analyses.json': {
        logos: [
          { lemma: 'lo/gos', gloss: 'word', parse: 'noun', lsj: ['lo/gos', '*a)rxh/'], cunliffe: ['lo/gos'] },
          { lemma: 'lo/gos', gloss: 'speech', parse: 'noun', lsj: ['lo/gos'], cunliffe: ['lo/gos'] },
        ],
      },
      '/lsj/l.json': { 'lo/gos': { key: 'lo/gos', head: 'λόγος', html: '<p>word</p>' } },
      '/lsj/a.json': { '*a)rxh/': { key: '*a)rxh/', head: 'ἀρχή', html: '<p>beginning</p>' } },
      '/cunliffe/l.json': { 'lo/gos': { key: 'lo/gos', head: 'λόγος', html: '<p>word, tale</p>', src: 'lex' } },
    });

    expect(lsjShard('*a)rxh/')).toBe('a');
    expect(lsjShard('123')).toBe('_');
    const result = await lookupWord('LookupWork', 'logos');
    expect(result.analyses).toHaveLength(2);
    expect(result.lsj.map((e) => e.key)).toEqual(['lo/gos', '*a)rxh/']);
    // Same key referenced by both parses de-duplicates to one Cunliffe entry.
    expect(result.cunliffe.map((e) => e.key)).toEqual(['lo/gos']);
    await expect(fetchLsjShard('missing')).resolves.toEqual({});
    await expect(fetchCunliffeShard('missing')).resolves.toEqual({});
  });

  it('cunliffeShard mirrors lsjShard\'s letter rule exactly (same fixture, both dictionaries)', () => {
    // Parity fixture: identical to the one in
    // pipeline/tests/test_stage5_cunliffe.py's SHARD_FIXTURE and asserted
    // against Python's front_end_shard there — this is the TS half of that
    // cross-language parity check.
    const fixture: Array<[string, string]> = [
      ['mh=nis', 'm'],
      ['a)ga/qwn', 'a'],
      ['*mastori/dhs', 'm'],
      ['e(/ktwr', 'e'],
      ['*(/ektwr', 'e'],
      ['999', '_'],
    ];
    for (const [key, expected] of fixture) {
      expect(cunliffeShard(key)).toBe(expected);
      expect(lsjShard(key)).toBe(expected);
    }
  });
});
