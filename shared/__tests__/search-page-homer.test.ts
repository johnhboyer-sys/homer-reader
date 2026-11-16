// The search page after the port (lane C): Aristotle's page carrying Homer's
// features. These run the page on the real corpus, served from
// app/public/data by a fetch spy, so the counts are the ones a reader sees.
// Without the data (a fresh worktree) every test skips, loudly.
import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Search from '../components/Search.svelte';
import { CORPUS, HAVE_CORPUS, serveCorpus } from './serve-corpus';
import { chapterPlaces, eachHit } from '../lib/chapter-pages';
import { loadEngChapters, loadOffsets, search } from '../lib/search';

// The first search in a file reads the corpus cold.
vi.setConfig({ testTimeout: 60000 });

// Iliad 1's scenes are marked as a draft here (the shipped data has every
// book reviewed), so the heading's badge can be seen; the Odyssey stays as shipped.
const serve = () => serveCorpus({
  'iliad/book-01.json': b => ({ ...b, apparatus: { ...b.apparatus, draft: true } }),
});

const open = (query: string) => {
  window.history.replaceState(null, '', `/search/?${query}`);
  return render(Search);
};
const status = () => document.querySelector('[role="status"]')?.textContent?.replace(/\s+/g, ' ').trim() ?? '';
const counted = async () => {
  await waitFor(() => expect(status()).toMatch(/\d+ scenes?|No scenes found/), { timeout: 30000 });
  return status();
};
const refs = () => [...document.querySelectorAll('.inst-ref')].map(a => a.textContent?.trim() ?? '');

beforeEach((ctx) => {
  if (!HAVE_CORPUS) { console.warn(`search-page-homer: no corpus at ${CORPUS}; skipping`); ctx.skip(); }
  serve();
});
afterEach(() => window.history.replaceState(null, '', '/'));

describe('the count is by scene', () => {
  it('θάλασσα stands in 94 scenes', async () => {
    open('g=θάλασσα');
    expect(await counted()).toMatch(/^94 scenes · 119 hits/);
  });

  it('heads each scene with its line range and summary, as the reader labels it', async () => {
    open('g=θάλασσα&w=iliad&b=1');
    await counted();
    const head = document.querySelector('.sx-chap');
    expect(head?.querySelector('.sx-chap-n')?.textContent).toBe('Lines 33–42');
    expect(head?.querySelector('.sx-chap-t')?.textContent).toMatch(/Chryses/);
  });

  it('shows the reader’s draft badge on a draft scene, and none on a reviewed one', async () => {
    open('g=θάλασσα&w=iliad&b=1');
    await counted();
    expect(document.querySelector('.sx-chap .draft-badge')?.textContent).toBe('Draft');
    document.body.innerHTML = '';
    open('g=θάλασσα&w=odyssey&b=5');
    await counted();
    expect(document.querySelectorAll('.sx-chap').length).toBeGreaterThan(0);
    expect(document.querySelector('.sx-chap .draft-badge')).toBeNull();
  }, 60000);
});

describe('citations and jump links', () => {
  it('cites Greek by book.line and links into the reader at that line', async () => {
    open('g=θάλασσα&w=iliad&b=1');
    await counted();
    expect(refs()[0]).toBe('1.34');
    const a = document.querySelector('.inst-ref') as HTMLAnchorElement;
    const href = new URL(a.getAttribute('href')!, 'http://x');
    expect(href.pathname).toBe('/iliad/book/1');
    expect(href.searchParams.get('loc')).toBe('1.34');
  });

  it('cites an English row by a line or a line range, with no raw footnote marks', async () => {
    open('e=sea&t=murray&w=iliad&b=1');
    await counted();
    const english = [...document.querySelectorAll('li.instance')].filter(li => li.querySelector('.inst-en, [lang="en"]'));
    expect(english.length).toBeGreaterThan(0);
    for (const li of english) expect(li.querySelector('.inst-ref')?.textContent?.trim()).toMatch(/^1\.\d+(–\d+)?$/);
    expect(document.querySelector('.sx-results, main')?.textContent ?? '').not.toMatch(/\[\^/);
  });
});

describe('the book filter (b)', () => {
  it('keeps one book of one poem, and the Book select shows it', async () => {
    open('g=θάλασσα&w=iliad&b=1');
    expect(await counted()).toMatch(/^4 scenes/);
    expect((document.querySelector('#book-select') as HTMLSelectElement).value).toBe('1');
    expect(refs().every(r => r.startsWith('1.'))).toBe(true);
  });

  it('applies a book chosen beside In at the next search, and writes b to the address', async () => {
    const page = open('g=θάλασσα&w=iliad');
    expect(await counted()).toMatch(/^36 scenes/);
    const sel = document.querySelector('#book-select') as HTMLSelectElement;
    sel.value = '1';
    await fireEvent.change(sel);
    await fireEvent.click(page.getByRole('button', { name: 'Search' }));
    await waitFor(() => expect(status()).toMatch(/^4 scenes/), { timeout: 30000 });
    expect(new URLSearchParams(window.location.search).get('b')).toBe('1');
  }, 60000);
});

describe('the speech filters (spo, so, spk)', () => {
  it('spo=1 keeps lines inside a speech', async () => {
    open('g=θάλασσα&spo=1');
    expect(await counted()).toMatch(/^45 scenes · 60 hits/);
  });

  it('reads the old so=1 link the same way', async () => {
    open('g=θάλασσα&so=1');
    expect(await counted()).toMatch(/^45 scenes · 60 hits/);
  });

  it('spk keeps one speaker’s lines', async () => {
    open('g=θάλασσα&spk=achilles');
    expect(await counted()).toMatch(/^3 scenes/);
  });
});

describe('grammar, which needs one book', () => {
  it('runs a gr link scoped by w and b', async () => {
    open('w=iliad&b=1&gr=mood:opt');
    expect(await counted()).toMatch(/^18 scenes · 54 hits/);
  });

  it('asks for a poem and a book before running grammar alone', async () => {
    open('c=g:mood.opt');
    await waitFor(() => expect(document.querySelector('.narrow-prompt')?.textContent).toMatch(/Choose a poem and a book/), { timeout: 30000 });
  });
});

describe('joining the Greek and the English', () => {
  it('offers "and/or" by default once both boxes hold a query, with "and" on offer', async () => {
    const page = open('');
    const grk = page.container.querySelector('#grk-input') as HTMLTextAreaElement;
    const eng = page.container.querySelector('#eng-input') as HTMLTextAreaElement;
    grk.value = 'θάλασσα'; await fireEvent.input(grk);
    eng.value = 'sea'; await fireEvent.input(eng);
    expect(page.container.querySelector('.join summary')?.textContent).toMatch(/^Hits match\s*and\/or/);
    const radios = [...page.container.querySelectorAll<HTMLInputElement>('.join input[name="op"]')];
    expect(radios.map(r => [r.value, r.checked])).toEqual([['or', true], ['and', false]]);
  });

  it('a link that says op=or reads as and/or and counts either language', async () => {
    open('g=θάλασσα&e=sea&op=or');
    expect(await counted()).toMatch(/^298 scenes/);
  });

  it('op=and keeps the scenes that hold both', async () => {
    open('g=θάλασσα&e=sea&t=murray&op=and');
    const n = Number((await counted()).match(/^(\d+) scenes/)![1]);
    expect(n).toBeGreaterThan(80);
    expect(n).toBeLessThan(94);
  });
});

// The scenes that hold every one of `terms`, each searched alone and placed
// by scene: what "All words" must count, worked out without the join.
async function scenesHolding(lang: 'grk' | 'eng', terms: string[], translation?: string): Promise<number> {
  const works = ['iliad', 'odyssey'];
  const places = chapterPlaces(
    new Map(await Promise.all(works.map(async w => [w, await loadOffsets(w)] as const))),
    new Map(await Promise.all(works.map(async w => [w, await loadEngChapters(w)] as const))),
  );
  const each: Set<string>[] = [];
  for (const t of terms) {
    const { results } = await search(lang === 'grk' ? t : '', lang === 'eng' ? t : '', 'all', 'all', 'or', works, 'lemma', true);
    const mine = new Set<string>();
    for (const r of results) eachHit(r, places, (at, _l, tr) => { if (!translation || tr === translation) mine.add(at.key); });
    each.push(mine);
  }
  return [...each[0]].filter(k => each.every(keys => keys.has(k))).length;
}
const scenesIn = (bar: string) => Number(bar.match(/^(\d+) scenes?/)?.[1] ?? 0);

describe('"All words" means every word in one scene', () => {
  it('ἄναξ ἀνδρῶν: counts only the scenes holding both, not the books', async () => {
    open('g=ἄναξ ἀνδρῶν&gm=all');
    const shown = scenesIn(await counted());
    const want = await scenesHolding('grk', ['ἄναξ', 'ἀνδρῶν']);
    console.info(`ἄναξ ἀνδρῶν, all words: ${shown} scenes (by scene: ${want})`);
    expect(shown).toBe(want);
  });

  it('English all words in Murray: counts only the scenes holding both', async () => {
    open('e=swift ships&em=all&t=murray');
    const shown = scenesIn(await counted());
    const want = await scenesHolding('eng', ['swift', 'ships'], 'murray');
    console.info(`swift ships (Murray), all words: ${shown} scenes (by scene: ${want})`);
    expect(shown).toBe(want);
  });
});

describe('"Show the whole scene"', () => {
  it('opens the hit\'s whole scene, Greek and English, with the hit marked', async () => {
    open('g=θάλασσα&e=sea&w=iliad&b=1');
    await counted();
    const btn = await waitFor(() => {
      const b = [...document.querySelectorAll<HTMLButtonElement>('button.inst-more')][0];
      expect(b?.textContent).toBe('Show the whole scene');
      return b;
    });
    expect(document.body.textContent).not.toMatch(/whole section/);
    await fireEvent.click(btn);
    const li = btn.closest('li.instance')!;
    const greek = li.querySelector('.inst-snippet.greek')!;
    // Il. 1.33-42 (Chryses at the shore), and not the lines either side.
    expect(greek.textContent).toMatch(/ἔδεισεν/);
    expect(greek.textContent).toMatch(/δάκρυα/);
    expect(greek.textContent).not.toMatch(/ἐρέθιζε|εὐχόμενος/);
    expect(greek.querySelector('mark')?.textContent).toMatch(/θαλάσσης/);
    const english = li.querySelector('.inst-en')!;
    expect(english.textContent).toMatch(/loud-resounding sea/);
    expect(english.textContent).toMatch(/tears/);
    // The English is the words the count puts in the scene (eng-chapters),
    // whose edges are estimated within a translator's chunk: a line either
    // side may come with it, but not the scenes beyond.
    expect(english.textContent).not.toMatch(/old age come upon her|Down from the peaks/);
    expect(english.querySelector('mark')?.textContent).toMatch(/sea/i);
    expect(li.querySelector('button.inst-less')?.textContent).toBe('Show less');
  });
});

describe('hostile input', () => {
  it('renders markup typed into the address as text', async () => {
    const page = open('g=%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E&e=%3Cscript%3Ex%3C%2Fscript%3E');
    await counted();
    expect(page.container.querySelector('img[src="x"], script')).toBeNull();
  });
});
