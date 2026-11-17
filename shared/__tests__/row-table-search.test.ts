// The row table (lib/row-table) against the rows the page draws: each case
// runs a search through Search.svelte with the table in force, and the page
// compares every book it reads with the table's count of it (bookRows), and
// says so on the console where they differ. Ported from aristotle-reader's
// row-table-search.test.ts (PR #208) onto Homer's books: a book is one
// section, its units the stretches between Murray's line marks (here lines
// 1–4, 5–8, 9–12), each translation placed by its own marks, and each book
// cut into two scenes (1–6, 7–12) whose edge falls inside the unit 5–8, so
// one unit's English is two rows, one in each scene.
import { cleanup, fireEvent, render, within } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import Search from '../components/Search.svelte';
import type { BookData, GreekLine } from '../lib/data';
import { chapterPlaces } from '../lib/chapter-pages';
import { countRows, encodeRowBook, type RowTable } from '../lib/row-table';
import { englishQueryUnits, englishWords, type EngChapters, type Offsets, type SearchResult } from '../lib/search';
import { getWork, searchableTranslations } from '../lib/works';
import { CORPUS, HAVE_CORPUS, serveCorpus } from './serve-corpus';
import { walk } from './walk-pages';

const { books, state, offsets, engChapters, texts } = vi.hoisted(() => {
  const line = (n: number): GreekLine => {
    const text = `${n}α ${n}β ${n}γ`;
    return { n, text, tokens: text.split(' ').map((t, i) => ({ t, o: i * (String(n).length + 2), k: t })) };
  };
  // Murray: one sentence a unit, marked at lines 1, 5 and 9.
  const m = ['The sea was dark and wide. ', 'Men sailed the sea at dawn and the sea was calm. ', 'They came home from the sea.'];
  const texts = {
    murray: m.join(''),
    butler: 'Over the wine-dark sea they went, and the sea took them home again at last.',
    pope: 'Along the sea the ships, along the shore the sea.',
    kosmos: 'Sing of the sea. The sea is wide. The sea is grey.',
  };
  const tick = (n: number, offset: number) => ({ n, offset, real: true });
  const bookOf = (n: number): BookData => ({ book: n, segments: [{
    id: `${n}:${n}`, column: `${n}`,
    greek: Array.from({ length: 12 }, (_, i) => line(i + 1)),
    english: { text: texts.murray, notes: [], markers: [], bekker: [tick(1, 0), tick(5, m[0].length), tick(9, m[0].length + m[1].length)] },
    ross: [{ chapter: `${n}`, text: texts.butler, cont: false, bekker: [tick(1, 0), tick(7, texts.butler.indexOf('and'))] }],
    third: [{ chapter: `${n}`, text: texts.pope, cont: false, bekker: [tick(1, 0)] }],
    overlays: { kosmos: [{ chapter: `${n}`, text: texts.kosmos, cont: false, bekker: [tick(1, 0), tick(5, texts.kosmos.indexOf('The')), tick(10, texts.kosmos.lastIndexOf('The'))] }] },
  }] } as BookData);
  // Scenes 1–6 and 7–12 of each book; each translation's 7–12 starts at
  // its fifth word.
  const offsets = {
    token_count: 72, seg_base_offset: [0, 36],
    segments: [{ book: 1, column: '1', line_runs: [] }, { book: 2, column: '2', line_runs: [] }],
    book_bounds: [{ book: 1, start: 0 }, { book: 2, start: 36 }],
    chapter_bounds: [1, 2].flatMap(b => [
      { book: b, chapter: '1-6', start: (b - 1) * 36, accuracy: 'exact' },
      { book: b, chapter: '7-12', start: (b - 1) * 36 + 18, accuracy: 'exact' },
    ]),
  };
  const scenes = { 0: [[0, '1-6'], [9, '7-12']], 1: [[0, '1-6'], [9, '7-12']] };
  const engChapters = { english: scenes, ross: scenes, third: scenes, 'overlay-kosmos': scenes };
  return { books: { 1: bookOf(1), 2: bookOf(2) } as Record<number, BookData>, texts, offsets, engChapters,
    state: { table: null as RowTable | null, corpus: false, fail: 0 } };
});

vi.mock('../lib/search', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/search')>();
  return {
    ...actual,
    search: vi.fn(async (...a: Parameters<typeof actual.search>) => (state.corpus ? actual.search(...a) : { results: [], failedWorks: [] })),
    loadOffsets: vi.fn(async (w: string) => (state.corpus ? actual.loadOffsets(w) : offsets as unknown as Offsets)),
    loadEngChapters: vi.fn(async (w: string) => (state.corpus ? actual.loadEngChapters(w) : engChapters as unknown as EngChapters)),
    greekHitForms: vi.fn(async () => ({ byResult: new Map(), headwords: new Map(), failedWorks: [] })),
    speakerRoster: vi.fn(async () => []),
  };
});

vi.mock('../lib/data', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/data')>();
  return {
    ...actual,
    fetchBook: vi.fn(async (w: string, n: number) => {
      if (n === state.fail) throw new Error(`book ${n}: 503`);
      return state.corpus ? actual.fetchBook(w, n) : books[n];
    }),
    // Homer's chapters.json lists no book: its scenes come with the places.
    fetchChapters: vi.fn(async (w: string) => (state.corpus ? actual.fetchChapters(w) : {})),
    loadRowTable: vi.fn(async (w: string) => {
      if (state.corpus) return actual.loadRowTable(w);
      if (!state.table) throw new Error('no table');
      return state.table;
    }),
  };
});

const translations = searchableTranslations(getWork('iliad')!);
const tableOf = (): RowTable => ({ v: 1, books: { 1: encodeRowBook(books[1], translations), 2: encodeRowBook(books[2], translations) } });
let warn: ReturnType<typeof vi.spyOn>;
beforeEach(() => { warn = vi.spyOn(console, 'warn').mockImplementation(() => {}); });
afterEach(() => {
  warn.mockRestore();
  vi.clearAllMocks();
  state.corpus = false;
  state.fail = 0;
  window.history.replaceState(null, '', '/');
});

const at = (book: number, r: Partial<SearchResult>): SearchResult => ({
  work: 'iliad', meta: { id: `${book}:${book}`, book, column: `${book}` },
  grkMatch: false, engMatch: false, grkPositions: [], ...r,
});
// Where "sea" stands in each translation's words: the index's places.
const sea = (id: keyof typeof texts) => englishWords(texts[id]).flatMap((w, i) => (w.word.toLowerCase() === 'sea' ? [i] : []));
const allSea = () => (['murray', 'butler', 'pope', 'kosmos'] as const).map(id => ({ translation: id, positions: sea(id) }));
const text = (el: Element | null) => (el?.textContent ?? '').replace(/\s+/g, ' ').trim();
const status = () => text(document.querySelector('[role="status"]'));
const mismatches = () => warn.mock.calls.filter((c: unknown[]) => /the row table counts/.test(String(c[0])));

// Runs the search with the table in force; the rows drawn, once the page has
// read its books.
async function rows(url: string, results: SearchResult[], table: RowTable | null = tableOf(), asked = true) {
  const { search } = await import('../lib/search');
  const { fetchBook, loadRowTable } = await import('../lib/data');
  state.table = table;
  vi.mocked(search).mockResolvedValueOnce({ results, failedWorks: [] });
  window.history.replaceState(null, '', url);
  const { container } = render(Search);
  await vi.waitFor(() => expect(fetchBook).toHaveBeenCalled());
  await vi.waitFor(() => expect(container.querySelectorAll('li.instance').length).toBeGreaterThan(0));
  await vi.waitFor(() => expect(status()).not.toMatch(/of …/));
  // The table was asked for and answered: a case where it was not would pass
  // without comparing anything.
  if (asked) expect(loadRowTable).toHaveBeenCalled();
  return container.querySelectorAll('li.instance').length;
}

const greekWord = 'g=' + encodeURIComponent('α');
const cases: [string, string, SearchResult[]][] = [
  ['Greek words on lines 1, 2 and 7 (two scenes)', greekWord, [at(1, { grkMatch: true, grkPositions: [0, 4, 19] })]],
  ['Greek words two lines apart, in one scene', greekWord, [at(1, { grkMatch: true, grkPositions: [0, 7] })]],
  ['Murray joining the Greek of its unit, and alone in the others', `${greekWord}&e=sea&op=or`, [
    at(1, { grkMatch: true, engMatch: true, grkPositions: [1], engHits: [{ translation: 'murray', positions: sea('murray') }] })]],
  ['four translations, each placed by its own marks', 'e=sea', [at(1, { engMatch: true, engHits: allSea() })]],
  ['Greek in the unit a scene starts in, English both sides of the edge', `${greekWord}&e=sea&op=or`, [
    at(1, { grkMatch: true, engMatch: true, grkPositions: [15, 18], engHits: allSea() })]],
  ['a run of several words', `${greekWord}&gm=phrase`, [
    at(1, { grkMatch: true, grkPositions: [3, 4, 18, 19], windows: [[3, 4], [18, 19]] })]],
  ['two books', `${greekWord}&e=sea&op=or`, [
    at(1, { grkMatch: true, grkPositions: [0, 4, 30] }),
    at(2, { engMatch: true, engHits: allSea() })]],
];

describe('the row table counts the rows the page draws', () => {
  for (const [name, query, results] of cases) {
    // Homer's page offers 1 and 3 lines (an address asking for the whole
    // section reads as 3); countRows is checked at the section too.
    for (const ctx of ['1', '3'] as const) {
      it(`${name}, context ${ctx}`, async () => {
        const drawn = await rows(`/search/?${query}&ctx=${ctx}`, results);
        expect(drawn).toBeGreaterThan(0);
        expect(mismatches()).toEqual([]);
        // And the count itself, as the page asked for it, book by book.
        const eng = new URLSearchParams(query).get('e') ?? '';
        const places = chapterPlaces(new Map([['iliad', offsets as unknown as Offsets]]), new Map([['iliad', engChapters as unknown as EngChapters]]));
        const table = tableOf();
        const counted = [1, 2].reduce((n, b) => {
          const own = results.filter(r => r.meta.book === b);
          return n + (own.length ? countRows(own, table.books[String(b)], {
            context: ctx, places, translations, chapterSection: false,
            lookup: () => ({ chapter: '—' }), engUnits: englishQueryUnits(eng), engPhrase: false,
          })! : 0);
        }, 0);
        expect(counted).toBe(drawn);
      });
    }
  }

  // Book 1: every Greek word a match of its own (a row each, 36), and Murray's
  // first "sea", which joins the Greek of its unit; book 2: one row more. At
  // 20 a page, page 1 is book 1's.
  const words = (book: number, english = false): SearchResult => at(book, {
    grkMatch: true, engMatch: english, grkPositions: Array.from({ length: 36 }, (_, i) => i),
    windows: Array.from({ length: 36 }, (_, i) => [i]), ...(english ? { engHits: [{ translation: 'murray', positions: [1] }] } : {}),
  });
  const two = [words(1, true), { ...words(2), grkPositions: [0], windows: [[0]] }];
  const url = `/search/?${greekWord}&e=sea&op=or&ps=20`;
  const booksRead = async () => {
    const { fetchBook } = await import('../lib/data');
    return [...new Set(vi.mocked(fetchBook).mock.calls.map(c => c[1]))].sort();
  };

  it('reads only the books its page draws, the page count from the table', async () => {
    await rows(url, two);
    await vi.waitFor(() => expect(text(document.querySelector('.pager-status'))).toBe('Page 1 of 2'));
    expect(document.querySelectorAll('li.instance')).toHaveLength(20);
    expect(await booksRead()).toEqual([1]);
    expect(mismatches()).toEqual([]);
  });

  it('reads every book where there is no table, as before it', async () => {
    await rows(url, two, null);
    await vi.waitFor(async () => expect(await booksRead()).toEqual([1, 2]));
    await vi.waitFor(() => expect(text(document.querySelector('.pager-status'))).toBe('Page 1 of 2'));
    expect(document.querySelectorAll('li.instance')).toHaveLength(20);
  });

  // Greek alone, which is offered the by-form view.
  const greekOnly = [words(1), two[1]];
  const urlG = `/search/?${greekWord}&ps=20`;
  // Pages count passages in every view (John, 17 Nov): by form a page holds
  // By work's passages, regrouped, so the table counts its pages too.
  it('by form, reads only the books its page draws, the page count from the table', async () => {
    await rows(`${urlG}&v=form`, greekOnly);
    await vi.waitFor(() => expect(text(document.querySelector('.pager-status'))).toBe('Page 1 of 2'));
    expect(await booksRead()).toEqual([1]);
    expect(mismatches()).toEqual([]);
  });

  it('moving to the by-form view keeps the pages and reads no other book', async () => {
    await rows(urlG, greekOnly);
    await vi.waitFor(() => expect(text(document.querySelector('.pager-status'))).toBe('Page 1 of 2'));
    expect(await booksRead()).toEqual([1]);
    const form = document.querySelector<HTMLInputElement>('input[name="sx-view"][value="form"]');
    expect(form).toBeTruthy();
    await fireEvent.click(form!);
    await new Promise(r => setTimeout(r, 50));
    expect(await booksRead()).toEqual([1]);
    expect(text(document.querySelector('.pager-status'))).toBe('Page 1 of 2');
  });

  it('keeps the next book on its own page where a book the table counted fails to load', async () => {
    const { search } = await import('../lib/search');
    const { fetchBook } = await import('../lib/data');
    state.table = tableOf();
    state.fail = 1;
    vi.mocked(search).mockResolvedValueOnce({ results: two, failedWorks: [] });
    window.history.replaceState(null, '', url);
    const { container } = render(Search);
    await vi.waitFor(() => expect(text(container.querySelector('.pager-status'))).toBe('Page 1 of 2'));
    await vi.waitFor(() => expect(vi.mocked(fetchBook).mock.calls.some(c => c[1] === 1)).toBe(true));
    await new Promise(r => setTimeout(r, 50));
    // Page 1 is book 1's rows, which did not load: book 2's row is not drawn there.
    expect(container.querySelectorAll('li.instance')).toHaveLength(0);
    expect(vi.mocked(fetchBook).mock.calls.some(c => c[1] === 2)).toBe(false);
  });

  it('stays on a later page whose book failed to load', async () => {
    const { search } = await import('../lib/search');
    const { fetchBook } = await import('../lib/data');
    state.table = tableOf();
    state.fail = 1;
    // Book 1 alone: its 36 rows are pages 1 and 2.
    vi.mocked(search).mockResolvedValueOnce({ results: two.slice(0, 1), failedWorks: [] });
    window.history.replaceState(null, '', url);
    const { container } = render(Search);
    await vi.waitFor(() => expect(text(container.querySelector('.pager-status'))).toBe('Page 1 of 2'));
    await fireEvent.click(within(container.querySelector('.pager')! as HTMLElement).getByRole('button', { name: /Next/ }));
    await vi.waitFor(() => expect(text(container.querySelector('.pager-status'))).toBe('Page 2 of 2'));
    await new Promise(r => setTimeout(r, 50));
    expect(text(container.querySelector('.pager-status'))).toBe('Page 2 of 2');
    expect(container.querySelectorAll('li.instance')).toHaveLength(0);
  });

  it('reads every book, and draws the same rows, where the table disagrees with a book', async () => {
    // Every Murray word in a unit of its own: it no longer joins the Greek,
    // so the table counts a row more in book 1 than the book draws.
    const wrong = tableOf();
    const seg = wrong.books['1'].s[0];
    seg.e = { ...seg.e, murray: [999, 1000, 999] };
    wrong.books['1'].u[999] = 0;
    await rows(url, two, wrong);
    await vi.waitFor(() => expect(mismatches()).toHaveLength(1));
    await vi.waitFor(async () => expect(await booksRead()).toEqual([1, 2]));
    await vi.waitFor(() => expect(text(document.querySelector('.pager-status'))).toBe('Page 1 of 2'));
    expect(document.querySelectorAll('li.instance')).toHaveLength(20);
  });
});

// On the real corpus: θάλασσα + sea (and/or), the table made from the built
// books as the site build makes it (the build's own word check aside), and
// every page walked, so every book the search reaches is read and compared
// with the table's count. Without the data it skips, loudly.
describe('on the corpus, the table agrees with every book θάλασσα + sea reads', () => {
  beforeEach((ctx) => {
    if (!HAVE_CORPUS) { console.warn(`row-table-search: no corpus at ${CORPUS}; skipping`); ctx.skip(); }
  });
  // The tables, made from the built books as the site build makes them.
  function serveTables() {
    const tables = new Map<string, RowTable>();
    for (const w of ['iliad', 'odyssey']) {
      const dir = path.join(CORPUS, w);
      const table: RowTable = { v: 1, books: {} };
      for (const file of readdirSync(dir).filter(f => /^book-\d+\.json$/.test(f))) {
        table.books[String(Number(file.slice(5, -5)))] = encodeRowBook(JSON.parse(readFileSync(path.join(dir, file), 'utf8')), searchableTranslations(getWork(w)!), false);
      }
      tables.set(w, table);
    }
    serveCorpus({}, Object.fromEntries([...tables].map(([w, t]) => [`${w}/rows.json`, () => t])));
    state.corpus = true;
  }
  it('θάλασσα + sea, and/or', async () => {
    serveTables();
    const { fetchBook, loadRowTable } = await import('../lib/data');
    // The table is in force: the page total shows at once, and page 1 has
    // read only the books it draws (Il. 1-2), not the 47 the search reaches.
    // A page that fell back to reading every book would pass the walk below.
    window.history.replaceState(null, '', `/search/?g=${encodeURIComponent('θάλασσα')}&e=sea&op=or`);
    render(Search);
    await vi.waitFor(() => expect(status()).toMatch(/page 1 of \d+/), { timeout: 60000 });
    await vi.waitFor(() => expect(document.querySelectorAll('li.instance').length).toBe(40), { timeout: 60000 });
    const read = new Set(vi.mocked(fetchBook).mock.calls.map(c => `${c[0]} ${c[1]}`));
    expect([...read].sort()).toEqual(['iliad 1', 'iliad 2']);
    cleanup();
    window.history.replaceState(null, '', '/');
    const { bar, scenes, pages, drawn } = await walk('g=θάλασσα&e=sea&op=or');
    console.info(`θάλασσα + sea with the table: ${bar} → ${drawn} scenes over ${pages} pages`);
    expect(loadRowTable).toHaveBeenCalled();
    expect(mismatches()).toEqual([]);
    expect(drawn).toBe(scenes);
  }, 600000);

  // Pages count passages in every view (John, 17 Nov): by form and by grammar
  // page 1 reads the books By work's page 1 does, and no other.
  for (const [view, query] of [
    ['by form', `g=${encodeURIComponent('θάλασσα')}&e=sea&op=or&v=form`],
    ['by grammar', 'l=qalassa&e=sea&op=or&v=grammar'],
  ] as const) {
    it(`${view}, θάλασσα + sea: page 1 reads Il. 1-2 alone`, async () => {
      serveTables();
      const { fetchBook } = await import('../lib/data');
      window.history.replaceState(null, '', `/search/?${query}`);
      render(Search);
      await vi.waitFor(() => expect(status()).toMatch(/page 1 of \d+$/), { timeout: 60000 });
      // By grammar the paradigm rows start shut: their headings show the page drawn.
      await vi.waitFor(() => expect(document.querySelectorAll('li.instance, .group-head').length).toBeGreaterThan(0), { timeout: 60000 });
      // Long enough for a page that reads every book to start them.
      await new Promise(r => setTimeout(r, 200));
      const read = new Set(vi.mocked(fetchBook).mock.calls.map(c => `${c[0]} ${c[1]}`));
      expect([...read].sort()).toEqual(['iliad 1', 'iliad 2']);
      expect(mismatches()).toEqual([]);
      cleanup();
    }, 300000);
  }
});
