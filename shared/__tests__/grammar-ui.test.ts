import { fireEvent, render, screen, within } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Search from '../components/Search.svelte';
import type { BookData, ColumnRef, Speech } from '../lib/data';
import type { GrammarDict } from '../lib/search';

// The four tests in grammar-search.test.ts exercise `searchGrammar` alone, and
// would all still pass with the "Grammar, scoped to one book" panel deleted.
// These are about the PANEL: what the header claims, what the URL records, and
// what the scope selects are allowed to do to a result set that is DEFINED by
// its scope.
//
// Corpus shape the fixture reproduces: one segment per book, so a book-scoped
// grammar search returns a SINGLE SearchResult carrying every hit as a
// position — 4 words standing in 1 passage.
//
//   Iliad book 1   (3 tokens): 1 certain dual, 1 possible -> 2 words, 1 certain
//   Iliad book 9   (4 tokens): 2 certain dual, 2 possible -> 4 words, 2 certain
//   Iliad, whole   (7 tokens):                            -> 6 words, 3 certain
//   Odyssey book 3 (2 tokens): 1 certain dual, 1 possible -> 2 words, 1 certain
//
// The whole-work figure is what the single-book gate exists to keep off the
// screen, so "6 words" appearing anywhere is a failure this file watches for.

const SIGS: GrammarDict['sigs'] = [
  [],                                                   // 0 reserved: unkeyed
  [],                                                   // 1 reserved: unanalysed
  [{ number: ['dual'], tense: ['aor'] }],               // 2 certain dual
  [{ number: ['dual'] }, { number: ['pl'] }],           // 3 dual or plural
  [{ number: ['pl'] }],                                 // 4 never dual
  // 5 is sig 3 with a hostile alternative spelling. Reading values are corpus
  // data, not typed by a reader, but they are interpolated into an HTML title
  // attribute, so a quote in one must not be able to close the attribute.
  [{ number: ['dual'] }, { number: ['pl<"x'] }],
];

const iliadDict: GrammarDict = {
  token_count: 7,
  width: 2,
  categories: ['number', 'tense'],
  reserved: { unkeyed: 0, unanalysed: 1 },
  sigs: SIGS,
};
const odysseyDict: GrammarDict = { ...iliadDict, token_count: 2 };

const iliadColumn = Uint16Array.from([2, 3, 4, /* book 9: */ 2, 2, 3, 5]);
const odysseyColumn = Uint16Array.from([2, 3]);

const segMeta = (id: string, book: number, column: string) => ({
  id, book, column, greek_head: '', greek_tokens: '', english_head: '',
});
const iliadMeta = [segMeta('1:1', 1, '1'), segMeta('9:1', 9, '9')];
const odysseyMeta = [segMeta('3:1', 3, '3')];

const iliadOffsets = {
  token_count: 7,
  seg_base_offset: [0, 3],
  segments: [
    { book: 1, column: '1', line_runs: [[1, 3]] },
    { book: 9, column: '9', line_runs: [[1, 2], [2, 2]] },
  ],
  book_bounds: [{ book: 1, start: 0 }, { book: 9, start: 3 }],
  chapter_bounds: [],
};
const odysseyOffsets = {
  token_count: 2,
  seg_base_offset: [0],
  segments: [{ book: 3, column: '3', line_runs: [[1, 2]] }],
  book_bounds: [{ book: 3, start: 0 }],
  chapter_bounds: [],
};

// `alpha` stands at book 9, position 1 — beside the duals, so a combo of "this
// spelling near a dual" matches and its results carry r.grammar exactly as a
// solo grammar search does. That is the case the ambiguity marker must not
// pick up.
const iliadForm: Record<string, [number, number][]> = { alpha: [[1, 1]] };

const line = (n: number, ...toks: string[]) => ({
  n, text: toks.join(' '), tokens: toks.map((t, i) => ({ t, o: i, k: t })),
});
const books: Record<string, BookData> = {
  'iliad:1': { book: 1, segments: [{ id: '1:1', column: '1', greek: [line(1, 'μῆνιν', 'ἄειδε', 'θεά')], english: null }] },
  'iliad:9': {
    book: 9,
    segments: [{
      id: '9:1', column: '9',
      greek: [line(1, 'δύω', 'alpha'), line(2, 'ἄμφω', 'ἵππω')],
      english: null,
    }],
  },
  'odyssey:3': { book: 3, segments: [{ id: '3:1', column: '3', greek: [line(1, 'ἄνδρα', 'μοι')], english: null }] },
};
const columns: Record<string, Record<string, ColumnRef[]>> = {
  iliad: { '1': [{ book: 1, lo: 1, hi: 1 }], '9': [{ book: 9, lo: 1, hi: 2 }] },
  odyssey: { '3': [{ book: 3, lo: 1, hi: 1 }] },
};

// One speech, covering Iliad 9 line 2 only — which holds the two POSSIBLE
// duals and neither certain one. A certain count computed before this filter
// runs claims 2 certain over rows where none is.
const achillesSpeech: Speech = {
  id: 'iliad-9-1', book: 9, lines: [2, 2],
  speaker: ['achilles'], addressee: ['agamemnon'],
  level: 0, cluster: 1, part: 1, type: 'G',
};

// data.ts caches every fetched book/column for the module's lifetime, so the
// second test in this file would otherwise see no request at all. Mock the data
// module — never vi.resetModules(), which gives a second Svelte runtime and
// kills the component with effect_orphan (docs/advanced-search-phrases-
// addendum.md §4).
vi.mock('../lib/data', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/data')>();
  return {
    ...actual,
    fetchBook: vi.fn(async (work: string, n: number) => {
      const b = books[`${work}:${n}`];
      if (!b) throw new Error(`no fixture book ${work}:${n}`);
      return b;
    }),
    fetchColumns: vi.fn(async (work: string) => columns[work] ?? {}),
    fetchSpeeches: vi.fn(async (work: string) => (work === 'iliad' ? [achillesSpeech] : [])),
    fetchCharacters: vi.fn(async () => ({})),
  };
});

// The search indexes go through raw fetch (lib/search.ts keeps its own per-file
// cache), so they are served by a fetch spy keyed on the work in the path.
let deferOdysseyColumn: { promise: Promise<void>; release: () => void } | null = null;

function json(data: unknown) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(data) } as Response);
}

function mockFetch() {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (url) => {
    const path = String(url);
    const iliad = path.includes('/iliad/');
    if (path.endsWith('/meta.json')) return json(iliad ? iliadMeta : odysseyMeta);
    if (path.endsWith('/offsets.json')) return json(iliad ? iliadOffsets : odysseyOffsets);
    if (path.endsWith('/grammar-dict.json')) return json(iliad ? iliadDict : odysseyDict);
    if (path.endsWith('/greek_form.json')) return json(iliad ? iliadForm : {});
    if (path.endsWith('/grammar-col.bin')) {
      if (!iliad && deferOdysseyColumn) await deferOdysseyColumn.promise;
      const col = iliad ? iliadColumn : odysseyColumn;
      const buf = col.buffer.slice(col.byteOffset, col.byteOffset + col.byteLength);
      return { ok: true, arrayBuffer: () => Promise.resolve(buf) } as Response;
    }
    return { ok: false, status: 404, json: async () => ({}) } as Response;
  });
}

// -- Reading the page ------------------------------------------------------
// Both panels sit inside a closed <details>, so buttons are reached by class
// rather than by role (role queries filter on accessibility visibility).

const panel = () => document.querySelector('.grammar-solo-panel') as HTMLElement;
const comboPanel = () => document.querySelector('.combo-slots') as HTMLElement;
const filtersRow = () => document.querySelector('.filters-row') as HTMLElement | null;
const sel = (root: HTMLElement, label: string) => within(root).getByLabelText(label) as HTMLSelectElement;
const grammarBtn = () => panel().querySelector('button.search-btn') as HTMLButtonElement;
const headline = () => document.querySelector('.result-count')?.textContent?.replace(/\s+/g, ' ').trim() ?? '';
const params = () => new URLSearchParams(window.location.search);
const settle = () => new Promise((r) => setTimeout(r, 0));

// Steering a BOUND select under happy-dom. Svelte reads the chosen option with
// `select.querySelector(':checked')`, and happy-dom implements no `:checked` at
// all — neither `select.value =` nor `option.selected =` moves that query, so
// every change event on a `bind:value` select would read Svelte's fallback,
// "the first option that is not disabled", and silently reset the state. The
// one lever that fallback does answer to is `disabled`, so the other options
// are hidden behind it for the length of the event and restored after.
// (Handler-driven selects, like the combo panel's, read `currentTarget.value`
// and work either way; this helper drives both.)
const choose = async (select: HTMLSelectElement, value: string) => {
  const opts = Array.from(select.options);
  const wanted = opts.find((o) => o.value === value);
  const was = opts.map((o) => o.disabled);
  for (const o of opts) o.disabled = o !== wanted;
  select.value = value;
  if (wanted) wanted.selected = true;
  await fireEvent.change(select);
  opts.forEach((o, i) => { o.disabled = was[i]; });
};

/** Fill the panel's scope + shape and press "Search this book". */
async function runGrammarSearch(work: string, book: string, category = 'Number', value = 'dual') {
  await choose(sel(panel(), 'Work'), work);
  await choose(sel(panel(), 'Book'), book);
  await choose(sel(panel(), category), value);
  await fireEvent.click(grammarBtn());
}

async function expectHeadline(re: RegExp) {
  await vi.waitFor(() => expect(headline()).toMatch(re));
}

async function chooseSpeaker(id: string) {
  await fireEvent.click(filtersRow()!.querySelector('.filter-activate') as HTMLElement);
  await vi.waitFor(() => expect(sel(filtersRow()!, 'Speaker').options.length).toBeGreaterThan(1));
  await choose(sel(filtersRow()!, 'Speaker'), id);
}

async function expandAll() {
  for (const head of Array.from(document.querySelectorAll('.group-head'))) {
    if (head.getAttribute('aria-expanded') !== 'true') await fireEvent.click(head);
  }
}

beforeEach(mockFetch);
afterEach(() => {
  // Release even on a failed assertion: a still-pending column promise stays in
  // lib/search's file cache and hangs every later search of that work.
  deferOdysseyColumn?.release();
  deferOdysseyColumn = null;
  window.history.replaceState(null, '', '/');
  vi.restoreAllMocks();
  try { localStorage.clear(); } catch { /* happy-dom */ }
});

describe('a grammar result set is labelled with the scope it was searched under', () => {
  // FIRST odyssey search in the file, deliberately: lib/search caches each
  // index file's promise for the module's lifetime, so a later test would find
  // the column already resolved and this deferral would be inert.
  it('keeps the searched scope when the selects move while the request is in flight', async () => {
    let release!: () => void;
    deferOdysseyColumn = { promise: new Promise<void>((r) => { release = () => r(); }), release: () => release() };

    render(Search);
    await runGrammarSearch('odyssey', '3');
    await vi.waitFor(() => expect(grammarBtn().textContent?.trim()).toBe('Searching…'));

    // The scope controls are shut while the request is out. The change below is
    // a direct dispatch, which a disabled control still receives under
    // happy-dom — so the snapshot has to hold even if the state does move.
    expect(sel(panel(), 'Work')).toBeDisabled();
    expect(sel(panel(), 'Book')).toBeDisabled();
    await choose(sel(panel(), 'Work'), 'iliad');

    deferOdysseyColumn.release();
    await expectHeadline(/certainly dual/);
    expect(headline()).toBe('2 words, 1 of them certainly dual.');
    expect(params().get('w')).toBe('odyssey');
    expect(params().get('b')).toBe('3');
    expect(sel(panel(), 'Work').value).toBe('odyssey');
  });

  it('runs a ?gr= link on mount and renders its results', async () => {
    window.history.replaceState(null, '', '/search?gr=number:dual&w=iliad&b=9');
    render(Search);
    await expectHeadline(/certainly dual/);
    expect(headline()).toBe('4 words, 2 of them certainly dual.');
  });

  it('describes the results with the submitted query, not the one now in the selects', async () => {
    render(Search);
    await runGrammarSearch('iliad', '9');
    await expectHeadline(/4 words/);

    // Edit the shape WITHOUT searching again. The rows on screen are still the
    // duals, so the sentence over them must still say dual — and the URL must
    // still be the link that reproduces them.
    await choose(sel(panel(), 'Number'), 'pl');
    await settle();
    expect(headline()).toBe('4 words, 2 of them certainly dual.');
    expect(params().get('gr')).toBe('number:dual');
  });

  it('never widens past one book when the book filter is cleared', async () => {
    render(Search);
    await runGrammarSearch('iliad', '9');
    await expectHeadline(/4 words/);

    // "Any" is reachable in the results filter row. Post-filtering the
    // already-fetched whole-work set would answer with the 6 words the gate
    // exists to refuse.
    await choose(sel(filtersRow()!, 'Book'), '');
    await settle();
    expect(headline()).not.toMatch(/6 words/);
    expect(document.body.textContent).toContain('only runs scoped to a single book');
    expect(params().has('gr')).toBe(false);
  });

  it('re-runs under the new book rather than re-filtering the old answer', async () => {
    render(Search);
    await runGrammarSearch('iliad', '9');
    await expectHeadline(/4 words/);
    await choose(sel(filtersRow()!, 'Book'), '1');
    await expectHeadline(/2 words/);
    expect(headline()).toBe('2 words, 1 of them certainly dual.');
    expect(params().get('b')).toBe('1');
  });
});

describe('the certain count is counted over the rows actually rendered', () => {
  it('follows a speaker filter down', async () => {
    render(Search);
    await runGrammarSearch('iliad', '9');
    await expectHeadline(/4 words, 2 of them certainly dual/);

    await chooseSpeaker('achilles');

    // Achilles' span holds line 2 — the two POSSIBLE duals, neither certain.
    await expectHeadline(/2 words/);
    expect(headline()).toBe('2 words, 0 of them certainly dual.');
  });

  it('reads as English when a single word matches', async () => {
    render(Search);
    // Only the certain-dual signature carries an aorist reading, and book 1
    // holds one of it.
    await runGrammarSearch('iliad', '1', 'Tense', 'aor');
    await expectHeadline(/word/);
    expect(headline()).toBe('1 word, certainly aor.');
  });
});

describe('the ambiguity marker', () => {
  it('marks the undetermined hits, escapes its title, and leaves the certain ones plain', async () => {
    render(Search);
    await runGrammarSearch('iliad', '9');
    await expectHeadline(/4 words/);
    await expandAll();

    const marks = Array.from(document.querySelectorAll('.inst-snippet mark'));
    const ambiguous = marks.filter((m) => m.classList.contains('ambiguous'));
    expect(marks).toHaveLength(4);
    expect(ambiguous).toHaveLength(2);
    // The quote in the hostile reading value survives as data rather than
    // closing the attribute early.
    const titles = ambiguous.map((m) => m.getAttribute('title'));
    expect(titles).toContain('one of several readings: dual, pl');
    expect(titles).toContain('one of several readings: dual, pl<"x');
  });

  it('is never applied to a combo result, which carries r.grammar too', async () => {
    render(Search);
    await choose(sel(comboPanel(), 'Kind for term 1'), 'grammatical');
    await choose(sel(comboPanel(), 'Number for term 1'), 'dual');
    await fireEvent.input(within(comboPanel()).getByLabelText('Spelling'), { target: { value: 'alpha' } });
    await fireEvent.click(document.querySelector('.combo-search-btn') as HTMLElement);

    await expectHeadline(/instances?/);
    await expandAll();
    expect(document.querySelectorAll('.inst-snippet mark').length).toBeGreaterThan(0);
    expect(document.querySelector('.inst-snippet mark.ambiguous')).toBeNull();
  });
});
