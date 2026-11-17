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

// 9–16: aristotle-reader's cases from 47444b1f5c (PRs #198, #200), on Homer's
// scenes. 9–11. The switch: and | and/or | or (John, 16 Nov). Scene 1-10 has
// Greek (token 3) and English (word 0); scene 11-22 has Greek alone (token 15).
const splitOf = (c: Element) => [...c.querySelectorAll('.sx-split .i')]
  .map(i => `${text(i.querySelector('.i-t'))} ${text(i.querySelector('small'))}${i.classList.contains('off') ? ' off' : ''}`);
async function openSplit(op: string) {
  const { loadOffsets, loadEngChapters } = await import('../lib/search');
  vi.mocked(loadOffsets).mockResolvedValue(offsetsOf(10));
  vi.mocked(loadEngChapters).mockResolvedValue({ english: { '0': [[0, '1-10'], [2, '11-22']] } });
  const r: SearchResult = { ...base, grkMatch: true, engMatch: true, grkPositions: [3, 15],
    engHits: [{ translation: 'murray', positions: [0] }] };
  return open(book(Array.from({ length: 22 }, (_, i) => line(i + 1, 'α')), 'Virtue one. Two.'), [r], `g=α&e=virtue${op}`);
}
it('"and" counts the scenes with both, and lights only that row', async () => {
  const c = await openSplit('');
  await vi.waitFor(() => expect(splitOf(c)).toEqual(['Greek and English 1', 'Greek only 1 off', 'English only 0 off']));
  expect(text(c.querySelector('.result-count'))).toMatch(/^1 scene\s*1 hit\b/);
  expect(text(c.querySelector('details.opt.join summary b'))).toBe('and');
});
it('"and/or" (op=or) counts every scene with a hit', async () => {
  const c = await openSplit('&op=or');
  await vi.waitFor(() => expect(splitOf(c)).toEqual(['Greek and English 1', 'Greek only 1', 'English only 0']));
  expect(text(c.querySelector('.result-count'))).toMatch(/^2 scenes\s*2 hits\b/);
  expect(text(c.querySelector('details.opt.join summary b'))).toBe('and/or');
});
it('"or" (op=xor) counts the scenes with one language, not both', async () => {
  const c = await openSplit('&op=xor');
  await vi.waitFor(() => expect(splitOf(c)).toEqual(['Greek and English 1 off', 'Greek only 1', 'English only 0']));
  expect(text(c.querySelector('.result-count'))).toMatch(/^1 scene\s*1 hit\b/);
  expect(text(c.querySelector('details.opt.join summary b'))).toBe('or');
  expect(headings(c)).toEqual(['Lines 11–22']);
});

// 12. A new search opens on "and/or" (John, 16 Nov): typed into a blank page
// and run with the switch untouched, it counts every scene with a hit, and
// its link names the op.
it('runs a new Greek and English search as "and/or" by default', async () => {
  const { loadOffsets, loadEngChapters, search } = await import('../lib/search');
  const { fetchBook, fetchChapters } = await import('../lib/data');
  vi.mocked(loadOffsets).mockResolvedValue(offsetsOf(10));
  vi.mocked(loadEngChapters).mockResolvedValue({ english: { '0': [[0, '1-10'], [2, '11-22']] } });
  vi.mocked(fetchBook).mockResolvedValue(book(Array.from({ length: 22 }, (_, i) => line(i + 1, 'α')), 'Virtue one. Two.'));
  vi.mocked(fetchChapters).mockResolvedValue({});
  vi.mocked(search).mockResolvedValue({ results: [{ ...base, grkMatch: true, engMatch: true, grkPositions: [3, 15],
    engHits: [{ translation: 'murray', positions: [0] }] }], failedWorks: [] });
  window.history.replaceState(null, '', '/search/?w=iliad');
  const { container: c } = render(Search);
  await fireEvent.input(c.querySelector('#grk-input')!, { target: { value: 'α' } });
  await fireEvent.input(c.querySelector('#eng-input')!, { target: { value: 'virtue' } });
  await vi.waitFor(() => expect(text(c.querySelector('details.opt.join summary b'))).toBe('and/or'));
  await fireEvent.click(c.querySelector('button.search-btn')!);
  await vi.waitFor(() => expect(text(c.querySelector('.result-count'))).toMatch(/^2 scenes\s*2 hits\b/));
  expect(new URLSearchParams(window.location.search).get('op')).toBe('or');
});

// 13. "and" with no scene holding both languages finds nothing, and the
// split still says where the hits are (Codex review, 16 Nov).
it('keeps the split rows when "and" finds no scene with both', async () => {
  const { loadOffsets, loadEngChapters, search } = await import('../lib/search');
  const { fetchBook, fetchChapters } = await import('../lib/data');
  vi.mocked(loadOffsets).mockResolvedValue(offsetsOf(10));
  vi.mocked(loadEngChapters).mockResolvedValue({ english: { '0': [[0, '1-10'], [2, '11-22']] } });
  vi.mocked(fetchBook).mockResolvedValue(book(Array.from({ length: 22 }, (_, i) => line(i + 1, 'α')), 'Virtue one. Two.'));
  vi.mocked(fetchChapters).mockResolvedValue({});
  // Greek in scene 2 only; English in scene 1 only.
  vi.mocked(search).mockResolvedValue({ results: [{ ...base, grkMatch: true, engMatch: true, grkPositions: [15],
    engHits: [{ translation: 'murray', positions: [0] }] }], failedWorks: [] });
  window.history.replaceState(null, '', '/search/?w=iliad&g=α&e=virtue&op=and');
  const { container: c } = render(Search);
  await vi.waitFor(() => expect(c.textContent).toMatch(/No scenes found/));
  await vi.waitFor(() => expect(splitOf(c)).toEqual(['Greek and English 0', 'Greek only 1 off', 'English only 1 off']));
});

// 14–15. English searched: one list, a work with its scenes, under it each
// translation with its hits there (John, 16 Nov). Scene 1 has Murray's
// word 0; scene 2 Butler's two words (Butler's slot has no scene starts, so
// its words fall in the scene the section's Greek opens in: scene 1).
const nestOf = (c: Element) => [...c.querySelectorAll('.sx-nest .i:not(.i-all)')]
  .map(i => `${i.classList.contains('sub') ? '  ' : ''}${text(i.querySelector('.i-t'))} ${text(i.querySelector('small'))}`);
async function openNest() {
  const { loadOffsets, loadEngChapters } = await import('../lib/search');
  vi.mocked(loadOffsets).mockResolvedValue(offsetsOf(10));
  vi.mocked(loadEngChapters).mockResolvedValue({ english: { '0': [[0, '1-10'], [2, '11-22']] } });
  const r: SearchResult = { ...base, grkMatch: false, engMatch: true, grkPositions: [],
    engHits: [{ translation: 'murray', positions: [0, 2] }, { translation: 'butler', positions: [1, 4, 6] }] };
  return open(book(Array.from({ length: 22 }, (_, i) => line(i + 1, 'α')), 'Virtue one. Virtue two.'), [r], 'e=virtue');
}
it('lists each work with its scenes, and its translations with their hits', async () => {
  const c = await openNest();
  await vi.waitFor(() => expect(nestOf(c)).toEqual(['Iliad 2 scenes', '  Butler 3', '  Murray 2']));
  expect(c.querySelector('.sx-trans')).toBeNull();
});
it('narrows to a translation in its work, and lifts it when chosen again', async () => {
  const c = await openNest();
  await vi.waitFor(() => expect(nestOf(c)).toHaveLength(3));
  const butler = () => [...c.querySelectorAll<HTMLElement>('.sx-nest .i.sub')].find(i => /Butler/.test(i.textContent ?? ''))!;
  await fireEvent.click(butler());
  await vi.waitFor(() => expect(new URLSearchParams(window.location.search).get('t')).toBe('butler'));
  expect(new URLSearchParams(window.location.search).get('wf')).toBe('iliad');
  await vi.waitFor(() => expect(text(c.querySelector('.result-count'))).toMatch(/^1 scene\s*3 hits\b/));
  expect(butler()).toHaveAttribute('aria-pressed', 'true');
  expect(nestOf(c)).toEqual(['Iliad 2 scenes', '  Butler 3', '  Murray 2']);
  await fireEvent.click(butler());
  await vi.waitFor(() => expect(new URLSearchParams(window.location.search).get('t')).toBeNull());
  expect(new URLSearchParams(window.location.search).get('wf')).toBeNull();
});

// 16. A translation chosen in no one work (an old link's t=): its row is on
// in its work, and choosing it lifts the filter (Codex review, 16 Nov).
it('marks a translation chosen across works, and lifts it when chosen', async () => {
  const { loadOffsets, loadEngChapters } = await import('../lib/search');
  vi.mocked(loadOffsets).mockResolvedValue(offsetsOf(10));
  vi.mocked(loadEngChapters).mockResolvedValue({ english: { '0': [[0, '1-10'], [2, '11-22']] } });
  const r: SearchResult = { ...base, grkMatch: false, engMatch: true, grkPositions: [],
    engHits: [{ translation: 'murray', positions: [0, 2] }, { translation: 'butler', positions: [1, 4, 6] }] };
  const c = await open(book(Array.from({ length: 22 }, (_, i) => line(i + 1, 'α')), 'Virtue one. Virtue two.'), [r], 'e=virtue&t=butler');
  const butler = () => [...c.querySelectorAll<HTMLElement>('.sx-nest .i.sub')].find(i => /Butler/.test(i.textContent ?? ''))!;
  await vi.waitFor(() => expect(butler()).toHaveAttribute('aria-pressed', 'true'));
  await fireEvent.click(butler());
  await vi.waitFor(() => expect(new URLSearchParams(window.location.search).get('t')).toBeNull());
  expect(new URLSearchParams(window.location.search).get('wf')).toBeNull();
});
