import { fireEvent, render, screen, within } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Phrases from '../components/Phrases.svelte';
import type { NgramRow } from '../lib/data';
import type { Offsets } from '../lib/search';

// τὸν δ' ἀπαμειβόμενος προσέφη is stored in the dictionary-form index as
// ὁ δέ ἀπαμείβομαι πρόσφημι, so the phrase a reader has in front of them matches
// nothing typed literally. ἦν is genuinely ambiguous — the corpus map reads it
// as ἐάν, εἰμί, ἠμί, ἤν and ὅς — so not every reading of a typed phrase is a
// phrase that recurs. Every entry below is the built corpus's own
// lemma-map/<letter>.json, trimmed to the words these tests type.
const lemmaMap: Record<string, Record<string, string[]>> = {
  t: { ton: ['o'], ti: ['tis'] },
  d: { "d'": ['de'] },
  a: { apameibomenos: ['apameibomai'] },
  h: { hn: ['ean', 'eimi', 'hmi', 'hn', 'os'], h: ['eimi', 'h', 'hmi', 'ihmi', 'o', 'os'] },
  o: { o: ['o', 'os'] },
};

const shards: Record<string, Record<string, NgramRow>> = {
  'lemma/o': {
    'o de apameibomai': [3, 111, 1034.9, 2],
    'o de apameibomai prosfhmi': [4, 106, 2046.3, 2],
    'os de': [2, 5, 3.0, 2],
  },
  // Trimmed: the corpus also files ἐάν τις and ὅς τις here, and they are left
  // out so that two of ἦν's five readings are dead ends, as most readings of an
  // ambiguous word are in practice.
  'lemma/e': { 'eimi tis': [2, 12, 3.1, 2] },
  'lemma/h': { 'hn te': [2, 9, 4.5, 2], 'hmi tis': [2, 19, 25.7, 2] },
  'form/t': {
    "ton d' apameibomenos": [3, 55, 1179.2, 2],
    'te kai': [2, 526, 1494.3, 2],
    // Only one poem: the cross-epic toggle's discriminating case. Every other
    // fixture row above is in both, which would make the toggle a no-op test.
    'te monon': [2, 8, 12.0, 1],
  },
  'english/o': {
    'odysseus of many wiles': [4, 92, 2044.8, 2],
    'odysseus of ithaca': [3, 6, 9.4, 1],
  },
};

// One book of three five-token verses. `te kai` stands at offset 3 (inside verse
// 1) and at offset 9 (the last token of verse 2, so its second word falls into
// verse 3) — the enjambed case the within-verse toggle exists for.
const OFFSETS: Offsets = {
  token_count: 15,
  seg_base_offset: [0],
  segments: [{ book: 1, column: '1', line_runs: [[1, 5], [2, 5], [3, 5]] }],
  book_bounds: [{ book: 1, start: 0 }],
  chapter_bounds: [],
};

const occurrences: Record<string, Record<string, Record<string, number[]>>> = {
  'lemma/o-3': { 'o de apameibomai': { iliad: [40] } },
  'form/t-2': { 'te kai': { iliad: [3, 6] } },     // delta-encoded: 3, then 9
  'english/o-4': { 'odysseus of many wiles': { odyssey: [0] } },
};

// The shard, occurrence and offset fetchers cache for the life of the module,
// which is right in a browser and useless in a test: the second test would see
// no request at all. Mock the data module and record what each render asked for.
const { shardCalls, occCalls } = vi.hoisted(() => ({
  shardCalls: [] as string[],
  occCalls: [] as string[],
}));

vi.mock('../lib/data', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/data')>();
  return {
    ...actual,
    fetchNgramShard: vi.fn(async (stream: string, letter: string) => {
      shardCalls.push(`${stream}/${letter}`);
      return shards[`${stream}/${letter}`] ?? {};
    }),
    fetchNgramOccurrences: vi.fn(async (stream: string, letter: string, n: number) => {
      const key = `${stream}/${letter}-${n}`;
      occCalls.push(key);
      return occurrences[key] ?? {};
    }),
    fetchOffsets: vi.fn(async () => OFFSETS),
    fetchEnglishSegments: vi.fn(async () => ({
      odyssey: [{ book: 1, column: '1', base: 0, words: 100 }],
    })),
  };
});

function json(data: unknown) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(data) } as Response);
}

// The Greek the page prints is the fold turned back into letters, so it carries
// no accents — ὁ δέ ἀπαμείβομαι appears as ο δε απαμειβομαι. Asserting on the
// accented spelling would be asserting on a phrase the page never shows.
const GREEK = {
  oDeApameibomai: 'ο δε απαμειβομαι',
  eimiTis: 'ειμι τις',
  hmiTis: 'ημι τις',
  eanTis: 'εαν τις',
  hnTe: 'ην τε',
  surface: "τον δ' απαμειβομενος",
  teKai: 'τε και',
  teMonon: 'τε μονον',
};

// A phrase can appear twice on the page — once as a row, once named in the note
// under the box — so a row is looked up by its own class.
function findRow(greek: string) {
  return screen.findByText(greek, { selector: '.phrase-greek' });
}

async function type(text: string) {
  await fireEvent.input(screen.getByRole('searchbox'), { target: { value: text } });
  await vi.waitFor(() => expect(shardCalls.length).toBeGreaterThan(0));
}

// Pick the dictionary-form stream, then type, so the widening runs against a
// settled query.
async function typeInLemmaMode(text: string) {
  const view = render(Phrases);
  await fireEvent.click(screen.getByRole('radio', { name: 'Word in any of its forms' }));
  await type(text);
  return view;
}

describe('Phrases: the dictionary-form index takes the form standing in the verse', () => {
  beforeEach(() => {
    shardCalls.length = 0;
    occCalls.length = 0;
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      const path = String(url);
      const map = path.match(/lemma-map\/([a-z_])\.json$/);
      if (map) return json(lemmaMap[map[1]] ?? {});
      return Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as Response);
    });
  });
  afterEach(() => vi.restoreAllMocks());

  // The defect: the index is keyed on headwords, so the phrase a reader has in
  // front of them matched nothing typed literally — τόν is not a headword, ὁ is.
  it('finds the phrase typed as it stands in the verse', async () => {
    await typeInLemmaMode("ton d' apameibomenos");
    expect(await findRow(GREEK.oDeApameibomai)).toBeInTheDocument();
  });

  it('reads the shard a reading lives in, not the typed letter', async () => {
    await typeInLemmaMode("ton d' apameibomenos");
    await findRow(GREEK.oDeApameibomai);
    // τόν resolves to ὁ, so the row is in the O shard — and the T shard is never
    // fetched, because τόν is no headword and reading it literally would cost a
    // whole shard with nothing in it.
    expect(shardCalls).toContain('lemma/o');
    expect(shardCalls).not.toContain('lemma/t');
  });

  // Half-typed words are the common case while a reader is still typing, and the
  // map records none of them.
  it('matches a word the map does not record as typed', async () => {
    await typeInLemmaMode('o de apameib');
    expect(await findRow(GREEK.oDeApameibomai)).toBeInTheDocument();
  });

  // Which shards are wanted turns on the FIRST word: ἦν is the surface of εἰμί,
  // ἠμί, ἐάν and ὅς, whose phrases are filed under different letters.
  it('reads every shard when the first word is ambiguous', async () => {
    await typeInLemmaMode('hn ti');
    expect(await findRow(GREEK.eimiTis)).toBeInTheDocument();
    expect(shardCalls).toContain('lemma/e');
    expect(shardCalls).toContain('lemma/h');
    expect(shardCalls).toContain('lemma/o');
  });

  it('names the readings that matched, and only those', async () => {
    await typeInLemmaMode('hn ti');
    const note = await screen.findByText(/Reading these words as/);
    expect(note.textContent).toContain(GREEK.eimiTis);
    expect(note.textContent).toContain(GREEK.hmiTis);
    // ἦν read as ἐάν is a real reading, but it produced no row here, and a note
    // that named it would be claiming a match the page never made.
    expect(note.textContent).not.toContain(GREEK.eanTis);
  });

  it('still matches a dictionary form typed as one', async () => {
    await typeInLemmaMode('o de apameibomai');
    expect(await findRow(GREEK.oDeApameibomai)).toBeInTheDocument();
    // The row alone does not prove the widen ran: "o de apameibomai" typed
    // literally is ALSO the exact shard key, so a broken widen that fell
    // back to matching the raw typed string (e.g. because it treated any
    // one unrecorded word — here "de" and "apameibomai" are both unrecorded
    // in the fixture map, only "d'" and "apameibomenos" are — as reason to
    // give up on widening the whole phrase) would find the same row by
    // coincidence. The "Reading these words as" note only renders when a
    // real Plan with tried readings exists, which only happens on the
    // genuine per-word widen path.
    const note = await screen.findByText(/Reading these words as/);
    expect(note.textContent).toContain(GREEK.oDeApameibomai);
  });

  // The letter buttons type into the same box. η is a form of εἰμί, ἵημι and ὁ,
  // so widening one letter would silently move the browse to another shard.
  it('does not widen a single letter', async () => {
    await typeInLemmaMode('h');
    expect(await findRow(GREEK.hnTe)).toBeInTheDocument();
    expect(shardCalls).toEqual(['lemma/h']);
  });

  it("fetches a row's occurrences from the shard that holds it", async () => {
    await typeInLemmaMode("ton d' apameibomenos");
    await fireEvent.click(await findRow(GREEK.oDeApameibomai));
    // Not lemma/t by luck of the typed letter: t is what was typed, o is where
    // the row lives.
    await vi.waitFor(() => expect(occCalls).toContain('lemma/o-3'));
    expect(occCalls).not.toContain('lemma/t-3');
  });

  it('leaves the surface stream matching what was typed', async () => {
    render(Phrases);
    await type("ton d' apameibomenos");
    expect(await findRow(GREEK.surface)).toBeInTheDocument();
    expect(shardCalls).toEqual(['form/t']);
  });
});

describe('Phrases: the within-one-verse toggle', () => {
  beforeEach(() => {
    shardCalls.length = 0;
    occCalls.length = 0;
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as Response));
  });
  afterEach(() => vi.restoreAllMocks());

  // The panel and the results list are landmark regions too, so the citations
  // are reached by the one the work's own heading names.
  async function expandTeKai() {
    render(Phrases);
    await type('te kai');
    await fireEvent.click(await findRow(GREEK.teKai));
    return screen.findByRole('region', { name: 'Iliad' });
  }

  function toggle() {
    return screen.getByRole('checkbox', { name: /inside a single verse/ });
  }

  // τε καί stands 526 times in the built corpus and 15 of those run over a verse
  // end; the fixture keeps one of each. The toggle is a query-time filter — the
  // index deliberately retains the straddling occurrences so it can exist.
  it('counts only the occurrences inside one verse, and is on by default', async () => {
    const region = await expandTeKai();
    expect(toggle()).toBeChecked();
    await vi.waitFor(() => expect(within(region).getAllByRole('link')).toHaveLength(1));
    expect(within(region).getByRole('link')).toHaveTextContent('1.1');
    expect(within(region).getByText(/runs over a verse end/)).toBeInTheDocument();
  });

  it('counts the straddling occurrence too when it is cleared', async () => {
    const region = await expandTeKai();
    await vi.waitFor(() => expect(within(region).getAllByRole('link')).toHaveLength(1));
    await fireEvent.click(toggle());
    const links = within(region).getAllByRole('link');
    expect(links).toHaveLength(2);
    expect(links.map((a) => a.textContent?.trim())).toEqual(['1.1', '1.2']);
  });

  // Never `${column}:${line}` — the Homeric convention is dotted, and it is the
  // citation module's job to know that.
  it('cites book.line, and jumps to the same', async () => {
    const region = await expandTeKai();
    const link = await within(region).findByRole('link');
    expect(link).toHaveTextContent('1.1');
    expect(link.getAttribute('href')).toContain('/iliad/book/1?loc=1.1');
  });

  it('has no verse toggle for the English stream, whose citation is the book', async () => {
    render(Phrases);
    await fireEvent.click(screen.getByRole('radio', { name: 'English translation' }));
    expect(screen.queryByRole('checkbox', { name: /inside a single verse/ })).toBeNull();
    await type('odysseus of many');
    const row = await screen.findByText('odysseus of many wiles', { selector: '.phrase-english' });
    await fireEvent.click(row);
    const region = await screen.findByRole('region', { name: 'Odyssey' });
    const link = await within(region).findByRole('link');
    // The book, with no verse: '1', not '1.1'.
    expect(link).toHaveTextContent(/^1$/);
    expect(link.getAttribute('href')).toContain('/odyssey/book/1?loc=1');
  });
});

describe('Phrases: the cross-epic toggle', () => {
  beforeEach(() => {
    shardCalls.length = 0;
    occCalls.length = 0;
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as Response));
  });
  afterEach(() => vi.restoreAllMocks());

  function toggle() {
    return screen.getByRole('checkbox', { name: /both poems/ });
  }

  // τε και stands in both poems; τε μόνον is the fixture's one-poem row —
  // the case the toggle exists to remove.
  it('is off by default, and removes the one-poem row when ticked', async () => {
    render(Phrases);
    await type('te');
    expect(toggle()).not.toBeChecked();
    expect(await findRow(GREEK.teKai)).toBeInTheDocument();
    expect(await findRow(GREEK.teMonon)).toBeInTheDocument();
    const countBefore = await screen.findByText(/of 2 matching phrases/);
    expect(countBefore).toBeInTheDocument();

    await fireEvent.click(toggle());
    expect(screen.queryByText(GREEK.teMonon, { selector: '.phrase-greek' })).toBeNull();
    expect(await findRow(GREEK.teKai)).toBeInTheDocument();
    expect(await screen.findByText(/of 1 matching phrases/)).toBeInTheDocument();
  });

  // The toggle reads a work count the shard row already carries, so ticking it
  // asks for no further shard or occurrence fetch.
  it('fetches nothing extra when ticked', async () => {
    render(Phrases);
    await type('te');
    await findRow(GREEK.teKai);
    const callsBefore = shardCalls.length;
    await fireEvent.click(toggle());
    await screen.findByText(/of 1 matching phrases/);
    expect(shardCalls).toHaveLength(callsBefore);
    expect(occCalls).toHaveLength(0);
  });

  // The stream this toggle exists for is Greek, but it applies to English too.
  it('also narrows the English stream', async () => {
    render(Phrases);
    await fireEvent.click(screen.getByRole('radio', { name: 'English translation' }));
    await type('odysseus of');
    await screen.findByText('odysseus of ithaca', { selector: '.phrase-english' });
    await screen.findByText(/of 2 matching phrases/);

    await fireEvent.click(toggle());
    expect(screen.queryByText('odysseus of ithaca', { selector: '.phrase-english' })).toBeNull();
    expect(
      await screen.findByText('odysseus of many wiles', { selector: '.phrase-english' }),
    ).toBeInTheDocument();
    await screen.findByText(/of 1 matching phrases/);
  });
});
