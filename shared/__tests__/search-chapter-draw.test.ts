// Where a hit is drawn is where it is counted, scene by scene: the cases of
// aristotle-reader's search-chapter-draw.test.ts (7ddd67b7ef) that apply to
// Homer, adapted. A Homer section is a whole book, and a scene is named by
// its lines ("1-10"), headed "Lines 1–10". Not ported: the two whole-section
// cases (ctx=s), which Homer does not offer ("Show the whole scene" stands in
// its place, tested in search-page-homer.test.ts).
import { fireEvent, render, screen } from '@testing-library/svelte';
import { afterEach, expect, it, vi } from 'vitest';
import Search from '../components/Search.svelte';
import type { BookData, GreekLine } from '../lib/data';
import type { SearchResult } from '../lib/search';

vi.mock('../lib/search', async original => ({
  ...await original<typeof import('../lib/search')>(),
  search: vi.fn(), searchPhraseVariants: vi.fn(), loadOffsets: vi.fn(async () => null),
  loadEngChapters: vi.fn(async () => { throw new Error('none'); }),
  greekHitForms: vi.fn(async () => ({ byResult: new Map(), headwords: new Map(), failedWorks: [] })),
  speakerRoster: vi.fn(async () => []),
}));
vi.mock('../lib/data', async original => ({
  ...await original<typeof import('../lib/data')>(),
  fetchBook: vi.fn(), fetchChapters: vi.fn(),
}));
afterEach(() => { vi.resetAllMocks(); window.history.replaceState(null, '', '/'); });

const line = (n: number, text: string): GreekLine => ({ n, text,
  tokens: [...text.matchAll(/\S+/g)].map(m => ({ t: m[0], o: m.index!, k: m[0] })) });
const text = (el: Element | null) => el?.textContent?.replace(/\s+/g, ' ').trim();
const book = (greek: GreekLine[], english: string): BookData => ({ book: 1, segments: [{
  id: '1', column: '1', greek,
  english: { text: english, notes: [], markers: [], bekker: [{ n: greek[0].n, offset: 0, real: true }] },
}] });
// Book 1 of 22 one-word lines; the second scene starts at line (token) `second` + 1.
const offsetsOf = (second: number) => ({ token_count: 22, seg_base_offset: [0],
  segments: [{ book: 1, column: '1', line_runs: [[1, 22]] }],
  book_bounds: [{ book: 1, start: 0 }], chapter_bounds: [
    { book: 1, chapter: `1-${second}`, start: 0, accuracy: 'exact' },
    { book: 1, chapter: `${second + 1}-22`, start: second, accuracy: 'exact' },
  ] }) as never;
const base = { work: 'iliad', meta: { id: '1', book: 1, column: '1' } };
const lines = (words: string[]) => words.map((w, i) => line(i + 1, w));

async function open(b: BookData, results: SearchResult[], query: string) {
  const { fetchBook, fetchChapters } = await import('../lib/data');
  const { search } = await import('../lib/search');
  vi.mocked(fetchBook).mockResolvedValue(b);
  vi.mocked(fetchChapters).mockResolvedValue({});
  vi.mocked(search).mockResolvedValue({ results, failedWorks: [] });
  window.history.replaceState(null, '', `/search/?w=iliad&${query}`);
  const page = render(Search);
  await vi.waitFor(() => expect(page.container.querySelector('li.instance')).not.toBeNull());
  return page.container;
}
const headings = (c: Element) => [...c.querySelectorAll('.sx-chap-n')].map(text);
const engMarks = (c: Element) => [...c.querySelectorAll('li.instance')]
  .map(i => [...i.querySelectorAll('.inst-en mark')].map(m => m.textContent).join(' ').trim().toLowerCase());

// 1. A Both phrase search, then "any inflection": the widened results are
// Greek alone, and the scene join must not drop them for want of English.
it('shows the widened results of a Both search, not an empty page', async () => {
  const { loadOffsets, searchPhraseVariants } = await import('../lib/search');
  vi.mocked(loadOffsets).mockResolvedValue(offsetsOf(20));
  vi.mocked(searchPhraseVariants).mockResolvedValue({
    results: [{ ...base, grkMatch: true, engMatch: false, grkPositions: [1] }],
    readings: [['logos', 'areth']], productive: [['logos', 'areth']], cappedFrom: 0, failedWorks: [],
  } as Awaited<ReturnType<typeof searchPhraseVariants>>);
  const both = { ...base, grkMatch: true, engMatch: true, grkPositions: [0],
    engHits: [{ translation: 'murray', positions: [0] }] };
  const c = await open(book([line(1, 'λόγος ἀρετή')], 'Virtue here.'), [both as SearchResult],
    `g=${encodeURIComponent('λόγος ἀρετή')}&gm=phrase&e=virtue&op=and`);
  await fireEvent.click(await screen.findByRole('button', { name: 'Find this phrase in any inflection' }));
  await vi.waitFor(() => expect(searchPhraseVariants).toHaveBeenCalled());
  const marks = () => [...c.querySelectorAll('li.instance mark')].map(m => m.textContent);
  await vi.waitFor(() => expect(marks().includes('ἀρετή') || /No scenes found/.test(c.textContent ?? '')).toBe(true));
  expect(c.textContent).not.toMatch(/No scenes found/);
  expect(marks()).toContain('ἀρετή');
});

// 2. A translator's chunk a scene starts in is one row under each scene, and
// each row marks only the word it counts.
it('marks only its own word in each half of a chunk split by a scene start', async () => {
  const { loadOffsets, loadEngChapters } = await import('../lib/search');
  vi.mocked(loadOffsets).mockResolvedValue(offsetsOf(20));
  vi.mocked(loadEngChapters).mockResolvedValue({ english: { '0': [[0, '1-20'], [2, '21-22']] } });
  const r: SearchResult = { ...base, grkMatch: false, engMatch: true, grkPositions: [],
    engHits: [{ translation: 'murray', positions: [0, 2] }] };
  const c = await open(book(lines(Array(22).fill('α')), 'Virtue here. Virtue there.'), [r], 'e=virtue&t=murray');
  await vi.waitFor(() => expect(c.querySelectorAll('li.instance')).toHaveLength(2));
  expect(headings(c)).toEqual(['Lines 1–20', 'Lines 21–22']);
  expect(engMarks(c)).toEqual(['virtue', 'virtue']);
});

// 3. An English phrase is counted at its first word and drawn there: one
// scene, though its second word stands in the next.
it('draws an English phrase under the scene it counts in', async () => {
  const { loadOffsets, loadEngChapters } = await import('../lib/search');
  vi.mocked(loadOffsets).mockResolvedValue(offsetsOf(20));
  vi.mocked(loadEngChapters).mockResolvedValue({ english: { '0': [[0, '1-20'], [1, '21-22']] } });
  const r: SearchResult = { ...base, grkMatch: false, engMatch: true, grkPositions: [],
    engHits: [{ translation: 'murray', positions: [0, 1], matches: [0] }] };
  const c = await open(book(lines(Array(22).fill('α')), 'One two three.'), [r], 'e=%22one%20two%22&em=phrase&t=murray');
  await vi.waitFor(() => expect(headings(c).length).toBeGreaterThan(0));
  expect(headings(c)).toEqual(['Lines 1–20']);
  expect(text(document.body)).toMatch(/1 scene\b/);
});

// 4. A work whose scene data did not load is counted by book, and the page
// says so.
it('warns when a poem\'s scenes did not load', async () => {
  const { loadOffsets } = await import('../lib/search');
  vi.mocked(loadOffsets).mockRejectedValue(new Error('no offsets.json'));
  const r: SearchResult = { ...base, grkMatch: true, engMatch: false, grkPositions: [0] };
  const c = await open(book([line(1, 'λόγος ἀρετή')], 'Virtue here.'), [r], 'g=λόγος');
  await vi.waitFor(() => expect(c.textContent).toMatch(/The scenes of Iliad did not load/));
});

// 5. Two runs of a phrase overlap across a scene start: the shared word is
// marked in both rows.
it('marks a word two overlapping phrase runs share in each run\'s row', async () => {
  const { loadOffsets, loadEngChapters } = await import('../lib/search');
  vi.mocked(loadOffsets).mockResolvedValue(offsetsOf(20));
  vi.mocked(loadEngChapters).mockResolvedValue({ english: { '0': [[0, '1-20'], [1, '21-22']] } });
  const r: SearchResult = { ...base, grkMatch: false, engMatch: true, grkPositions: [],
    engHits: [{ translation: 'murray', positions: [0, 1, 2], matches: [0, 1] }] };
  const c = await open(book(lines(Array(22).fill('α')), 'Ha ha ha.'), [r], 'e=%22ha%20ha%22&em=phrase&t=murray');
  await vi.waitFor(() => expect(headings(c)).toEqual(['Lines 1–20', 'Lines 21–22']));
  expect(engMarks(c)).toEqual(['ha ha', 'ha ha']);
});

// 6. Two terms, one a word and one two words, side by side across a scene
// start: the second term's words are not marked in the first's row.
it('does not stretch a one-word term over the next term\'s words', async () => {
  const { loadOffsets, loadEngChapters } = await import('../lib/search');
  vi.mocked(loadOffsets).mockResolvedValue(offsetsOf(20));
  vi.mocked(loadEngChapters).mockResolvedValue({ english: { '0': [[0, '1-20'], [1, '21-22']] } });
  const r: SearchResult = { ...base, grkMatch: false, engMatch: true, grkPositions: [],
    engHits: [{ translation: 'murray', positions: [0, 1, 2], matches: [0, 1] }] };
  const c = await open(book(lines(Array(22).fill('α')), 'Rosy well-being.'), [r], `e=${encodeURIComponent('rosy well-being')}&em=any&t=murray`);
  await vi.waitFor(() => expect(headings(c)).toEqual(['Lines 1–20', 'Lines 21–22']));
  expect(engMarks(c)).toEqual(['rosy', 'well being']);
});
