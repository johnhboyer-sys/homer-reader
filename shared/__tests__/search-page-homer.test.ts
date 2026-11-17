// The search page after the port (lane C): Aristotle's page carrying Homer's
// features. These run the page on the real corpus, served from
// app/public/data by a fetch spy, so the counts are the ones a reader sees.
// Without the data (a fresh worktree) every test skips, loudly.
import { fireEvent, render, screen, waitFor, within } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Search from '../components/Search.svelte';
import { CORPUS, HAVE_CORPUS, serveCorpus } from './serve-corpus';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { chapterPlaces, eachHit } from '../lib/chapter-pages';
import { formKey, ownGrammar } from '../lib/result-views';
import { greekFold, greekHitForms, greekHitGrammar, loadEngChapters, loadOffsets, search, type Reading } from '../lib/search';

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
  // The switch reads and | and/or | or (John's ruling in aristotle-reader,
  // 16 Nov); "or" is one language, not both, in a scene.
  it('offers "and/or" by default once both boxes hold a query, with "and" and "or" on offer', async () => {
    const page = open('');
    const grk = page.container.querySelector('#grk-input') as HTMLTextAreaElement;
    const eng = page.container.querySelector('#eng-input') as HTMLTextAreaElement;
    grk.value = 'θάλασσα'; await fireEvent.input(grk);
    eng.value = 'sea'; await fireEvent.input(eng);
    expect(page.container.querySelector('.join summary')?.textContent).toMatch(/^Hits match\s*and\/or/);
    const radios = [...page.container.querySelectorAll<HTMLInputElement>('.join input[name="op"]')];
    expect(radios.map(r => [r.value, r.checked])).toEqual([['and', false], ['or', true], ['xor', false]]);
  });

  it('a link that says op=or reads as and/or and counts either language', async () => {
    open('g=θάλασσα&e=sea&op=or');
    expect(await counted()).toMatch(/^298 scenes/);
  });

  // Codex review of the fold (lane F): the rows under the count were
  // measured before "All words" held each language's terms to one scene, so
  // they summed to 615 under a bar of 377.
  it('measures the rows under the count after "All words", as the bar is', async () => {
    open('g=ἄναξ ἀνδρῶν&e=sea&op=or');
    const bar = await counted();
    const rows = await waitFor(() => {
      const r = [...document.querySelectorAll('.sx-split li')].map(li => [li.querySelector('.i-t')?.textContent, Number(li.querySelector('small')?.textContent)]);
      expect(r).toHaveLength(3);
      return r;
    });
    expect(rows).toEqual([['Greek and English', 61], ['Greek only', 79], ['English only', 237]]);
    expect(scenesIn(bar)).toBe(61 + 79 + 237);
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

// Codex review of e03973358: "bed-but" begins in Il. 1 scene 8-32 and runs
// into 33-42, where "go" is; the page counted 33-42 for both terms.
describe('"All words" places a term of several words by its first word', () => {
  it('does not count "bed-but go" in the scene "but" runs into', async () => {
    open('e=bed-but%20go&ef=0&t=murray&w=iliad&b=1');
    expect(await counted()).toMatch(/^No scenes found/);
    expect([...document.querySelectorAll('.sx-chap-n')].map(h => h.textContent)).not.toContain('Lines 33–42');
  });

  // Codex review of the fold (lane F): word 339, the second word of
  // "bed-but", is also a "but"; it is not a second start of "bed-but".
  it('does not take another term\'s word for a second start ("bed-but but")', async () => {
    open('e=bed-but%20but&ef=0&w=iliad&b=1&t=murray');
    expect(await counted()).toMatch(/^1 scene · 4 hits/);
  });
});

// The English phrase list (aristotle-reader PR #202) on Homer's four
// translations: each run holds the word searched, which it would not if the
// words read for the list were out of step with the index; and setting the
// top run aside takes its hits from the count.
describe('the phrase list, in each translation', () => {
  const rows = () => [...document.querySelectorAll('.sx-phr label.fx')].map(l => ({
    phrase: l.querySelector('.ph-t')?.textContent?.trim() ?? '',
    n: Number(l.querySelector('small')?.textContent ?? 0),
    box: l.querySelector('input') as HTMLInputElement,
  }));
  const hits = () => Number(status().match(/· (\d+) hits?/)?.[1] ?? NaN);
  it.each(['murray', 'butler', 'pope', 'kosmos'])('%s: "ships" in the Iliad', async t => {
    open(`e=ships&ef=0&t=${t}&w=iliad`);
    await counted();
    const listed = await waitFor(() => { const r = rows(); expect(r.length).toBeGreaterThan(0); return r; }, { timeout: 60000 });
    for (const r of listed) expect(r.phrase.split(' '), `${t}: ${r.phrase}`).toContain('ships');
    const before = hits();
    await fireEvent.click(listed[0].box);
    await waitFor(() => expect(hits()).toBe(before - listed[0].n), { timeout: 30000 });
    expect(new URLSearchParams(window.location.search).get('xp')).toBe(listed[0].phrase);
  }, 120000);
});

// Codex review of the fold (lane F): the sheet's "Show n scenes" counted
// the forms ticked without the phrases set aside, so it promised 31 scenes
// where Apply drew 29.
describe('the sheet counts what Apply draws', () => {
  it('a form unticked with a phrase set aside: "Show n scenes" is the bar after', async () => {
    open('g=θάλασσα&e=sea&op=and&w=iliad&xp=of%20the%20sea');
    await counted();
    await fireEvent.click(screen.getByRole('button', { name: /^Filter/ }));
    const sheet = await screen.findByRole('dialog', { name: 'Filter' });
    await fireEvent.click(await waitFor(() => within(sheet).getByRole('button', { name: /^Forms/ }), { timeout: 30000 }));
    const forms = await screen.findByRole('group', { name: 'Greek forms found' });
    // The form θάλασσα, spelled or (before its spellings load) folded.
    const bare = (t: string) => t.normalize('NFD').replace(/\p{M}/gu, '');
    const box = [...forms.querySelectorAll('label.fx')].find(l => bare(l.querySelector('span')?.textContent ?? '').split(' · ').includes('θαλασσα'))!.querySelector('input')!;
    await fireEvent.click(box);
    const show = await waitFor(() => { const b = within(forms).getByRole('button', { name: /^Show \d+ scenes?$/ }); expect(b).not.toBeDisabled(); return b; });
    const promised = Number(show.textContent!.match(/\d+/)![0]);
    await fireEvent.click(show);
    await waitFor(() => expect(scenesIn(status())).toBe(promised), { timeout: 30000 });
    expect(status()).toMatch(/^29 scenes · 33 hits/);
  }, 120000);
});

// Pages are rows (aristotle-reader PR #201): exactly N a page, and the 100
// page lists each row as its book.line and the words around its first hit,
// opened in place to the passage.
describe('pages by rows, and the 100 page', () => {
  it('draws exactly 20 rows on a full page of θάλασσα', async () => {
    open('g=θάλασσα&ps=20');
    await counted();
    await waitFor(() => expect(document.querySelectorAll('li.instance')).toHaveLength(20));
  });

  it('lists θάλασσα on the 100 page as citations with a summary, each opening in place', async () => {
    open('g=θάλασσα&ps=100');
    expect(await counted()).toMatch(/^94 scenes · 119 hits/);
    // The page count shows once every book is laid out.
    await waitFor(() => expect(status()).toMatch(/^94 scenes · 119 hits · page 1 of 2$/), { timeout: 30000 });
    const rows = await waitFor(() => { const r = [...document.querySelectorAll('button.cmp-row')]; expect(r).toHaveLength(100); return r; });
    for (const row of rows) {
      expect(row.querySelector('.cmp-ref')?.textContent).toMatch(/^\d+\.\d+/);
      expect(row.querySelector('.cmp-sum mark')?.textContent).toMatch(/θαλάσσ|θάλασσ/);
    }
    await fireEvent.click(rows[0]);
    await waitFor(() => expect(document.querySelector('.cmp-head a.cmp-ref')?.getAttribute('href')).toMatch(/loc=/));
    expect(document.querySelector('li.cmp-open .inst-snippet.greek mark')).not.toBeNull();
  });
});

// Codex review of the fold (lane F): below 961px the citation's width gave
// way to its text, so the link heading an opened row ("1.34") was narrower
// than a 44px target.
// Codex review of the fold (lane F): by form, an instance holding hits of
// several forms is drawn once under each, so a page laid out by instances
// drew 47 rows where it promised 20. (The review's "ὁ καί", any word, is
// offered By work only; one word, ὁ, is offered By form.)
describe('pages by rows, grouped by form', () => {
  const pagesOf = () => Number(status().match(/page \d+ of (\d+)/)?.[1] ?? 1);
  // Every page of the search in view: the rows each page draws (every
  // grouping opened, as a reader would open them), each row's reader link,
  // the scene heading over it (By work), and its marked Greek forms. `parts`:
  // each row's marked words split by form, a part to a form, each named by
  // its form and its words (work:segment:position, as the page's word
  // buttons carry them). By work that is every (instance, form) pair the
  // data gives; By form, each row is one part.
  async function walkRows(perPage: number) {
    await waitFor(() => expect(status()).toMatch(/page \d+ of \d+$/), { timeout: 60000 });
    const pages = pagesOf();
    const sizes: number[] = [];
    const links: string[] = [];
    const scenes = new Set<string>();
    const parts: { form: string; toks: string[] }[] = [];
    let forms = 0;
    for (let p = 1; p <= pages; p++) {
      if (p > 1) {
        await fireEvent.click(document.querySelector<HTMLButtonElement>('button.pager-next')!);
        await waitFor(() => expect(document.querySelector('.pager-status')?.textContent).toBe(`Page ${p} of ${pages}`), { timeout: 30000 });
      }
      // By grammar the paradigm rows start shut: open them, then count.
      await waitFor(() => expect(document.querySelectorAll('li.instance, .group-head[aria-expanded="false"]').length).toBeGreaterThan(0), { timeout: 30000 });
      for (let shut; (shut = [...document.querySelectorAll<HTMLButtonElement>('.group-head[aria-expanded="false"]')]).length;) {
        for (const b of shut) await fireEvent.click(b);
      }
      await waitFor(() => expect(document.querySelectorAll('li.instance').length).toBeGreaterThan(0), { timeout: 30000 });
      let scene = '';
      let n = 0;
      for (const el of document.querySelectorAll('.sx-chap-n, li.instance')) {
        if (el.matches('.sx-chap-n')) { scene = el.textContent?.trim() ?? ''; continue; }
        n++;
        const href = el.querySelector('.inst-ref')?.getAttribute('href') ?? '';
        links.push(href);
        if (scene) scenes.add(`${new URL(href, 'http://x').pathname}|${scene}`);
        const byForm = new Map<string, Set<string>>();
        for (const m of el.querySelectorAll('.inst-snippet.greek mark')) {
          const w = m.closest<HTMLElement>('button.gw');
          expect(w, `${href}: a marked word with no place`).not.toBeNull();
          const f = formKey(m.textContent ?? '');
          (byForm.get(f) ?? byForm.set(f, new Set()).get(f)!).add(`${w!.dataset.w}:${w!.dataset.s}:${w!.dataset.i}`);
        }
        forms += byForm.size;
        for (const [form, toks] of byForm) parts.push({ form, toks: [...toks].sort() });
      }
      sizes.push(n);
    }
    expect(sizes.slice(0, -1).every(k => k === perPage), `rows a page: ${sizes}`).toBe(true);
    expect(sizes.at(-1)!).toBeGreaterThan(0);
    expect(sizes.at(-1)!).toBeLessThanOrEqual(perPage);
    return { pages, sizes, links, scenes, forms, parts, rows: sizes.reduce((a, b) => a + b, 0) };
  }
  // The same search By work: its rows, the scenes they are drawn under (all
  // the bar counts), and the forms they hold, which By form draws a row each.
  async function byWork(query: string) {
    open(query);
    const bar = await counted();
    const w = await walkRows(20);
    expect(w.scenes.size, `${query}: scenes drawn`).toBe(scenesIn(bar));
    document.body.innerHTML = '';
    return w;
  }

  it('ὁ, Il. 1: every row By work drawn once for each of its forms, 20 a page', async () => {
    const work = await byWork('g=ὁ&w=iliad&b=1&ps=20');
    open('g=ὁ&w=iliad&b=1&ps=20&v=form');
    await counted();
    const form = await walkRows(20);
    console.info(`ὁ, Il. 1: by work ${work.rows} rows holding ${work.forms} forms; by form ${form.rows} rows on ${form.pages} pages`);
    expect(form.rows).toBe(work.forms);
    expect([...new Set(form.links)].sort()).toEqual([...new Set(work.links)].sort());
    // Each (instance, form) pair drawn once, and no pair drawn in another's
    // place: counts and links alone pass a page that draws one form twice.
    const ids = (parts: { form: string; toks: string[] }[]) => parts.map(p => `${p.form}|${p.toks.join(',')}`).sort();
    expect(ids(form.parts)).toEqual(ids(work.parts));
  }, 300000);

  it('lays the pages out again when the grouping turns to By form', async () => {
    open('g=ὁ&w=iliad&b=1&ps=20');
    await counted();
    await waitFor(() => expect(status()).toMatch(/page \d+ of \d+$/), { timeout: 60000 });
    const byWorkPages = pagesOf();
    const radio = [...document.querySelectorAll<HTMLInputElement>('input[name="sx-view"]')].find(r => r.value === 'form')!;
    await fireEvent.click(radio);
    await waitFor(() => expect(document.querySelectorAll('li.instance')).toHaveLength(20), { timeout: 30000 });
    await waitFor(() => expect(pagesOf()).toBeGreaterThan(byWorkPages), { timeout: 30000 });
  }, 120000);

  // The rows By grammar, worked out from the data: each part (an instance's
  // hits of one form) is drawn once under each headword it is filed under.
  // Filed as paradigmOf files it, from the same inputs the page reads (the
  // readings of the words it holds, narrowed to the headwords searched, and
  // the headwords its form belongs to), but by the rule written out here, not
  // by calling paradigmHeads: the headwords its readings name, else those its
  // form belongs to, else the first searched.
  async function grammarRows(parts: { toks: string[] }[], lemmas: string[], work: string, book: number) {
    const { results } = await search(lemmas.join(' '), '', 'any', 'all', 'or', [work], 'headword');
    const inBook = results.filter(r => r.meta.book === book);
    const heads = [...new Set(lemmas.map(greekFold))];
    const grammar = ownGrammar(await greekHitGrammar(inBook), new Set(heads));
    const forms = await greekHitForms(inBook, lemmas.join(' '), 'headword');
    const readings = new Map<string, Reading[]>();
    const formHeads = new Map<string, string[] | undefined>();
    for (const r of inBook) {
      const seg = `${r.work}:${r.meta.id}`;
      r.grkPositions.forEach((pos, i) => {
        readings.set(`${seg}:${pos}`, grammar.byResult.get(seg)?.[i] ?? []);
        formHeads.set(`${seg}:${pos}`, forms.headwords.get(forms.byResult.get(seg)?.[i] ?? ''));
      });
    }
    let rows = 0;
    for (const { toks } of parts) {
      for (const t of toks) expect(readings.has(t), `${t}: a hit of the search`).toBe(true);
      const held = toks.flatMap(t => readings.get(t)!);
      const named = heads.filter(h => held.some(r => Object.hasOwn(r, 'lemma') && r.lemma.includes(h)));
      const mapped = heads.filter(h => formHeads.get(toks[0])?.includes(h));
      rows += named.length || mapped.length || 1;
    }
    return rows;
  }

  // Codex check of 09cee472c: by grammar with two headwords, a form both
  // own is drawn under each, and the pages counted it once (rows 25, 27, …).
  it('two headwords by grammar: a form under both is two rows, 20 a page', async () => {
    const work = await byWork('l=o,os&w=iliad&b=1&ps=20');
    open('l=o,os&v=grammar&w=iliad&b=1&ps=20');
    await counted();
    // The readings load after the first page; the pages are laid out again then.
    await waitFor(() => expect(document.querySelector('.sx-para')).not.toBeNull(), { timeout: 60000 });
    const grammar = await walkRows(20);
    const want = await grammarRows(work.parts, ['o', 'os'], 'iliad', 1);
    console.info(`ὁ, ὅς, Il. 1: by work ${work.rows} rows; by grammar ${grammar.rows} rows on ${grammar.pages} pages (from the data: ${want} rows)`);
    expect(grammar.rows).toBe(want);
    expect(grammar.pages).toBe(Math.ceil(want / 20));
    expect([...new Set(grammar.links)].sort()).toEqual([...new Set(work.links)].sort());
  }, 600000);
});

describe('the 100 page on a narrow screen', () => {
  it('keeps every citation at least 44px wide', () => {
    const css = readFileSync(path.resolve(process.cwd(), 'styles/b-search.css'), 'utf8');
    const narrow = css.slice(css.indexOf('@media not all and (min-width: 961px) {\n  @media not all and (max-height: 500px) {\n    .search-page .cmp-row'));
    const rule = narrow.slice(narrow.indexOf('.search-page .cmp-ref {')).split('}')[0];
    expect(rule).toMatch(/min-width: 44px/);
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

describe('the guide (app/src/pages/advanced.astro)', () => {
  const guide = readFileSync(path.resolve(process.cwd(), '../app/src/pages/advanced.astro'), 'utf8');
  const page = readFileSync(path.resolve(process.cwd(), 'components/Search.svelte'), 'utf8');

  it('has every section the search page links to', () => {
    const ids = new Set([...guide.matchAll(/<section id="([^"]+)"/g)].map(m => m[1]));
    const wanted = [...page.matchAll(/\/advanced#([\w-]+)/g)].map(m => m[1]);
    expect(wanted.length).toBeGreaterThan(0);
    for (const id of wanted) expect(ids, `#${id}`).toContain(id);
    for (const [, id] of guide.matchAll(/href="#([\w-]+)"/g)) expect(ids, `#${id}`).toContain(id);
  });

  it('runs every search it links to, each finding something', async () => {
    const links = [...guide.matchAll(/\$\{base\}\/search\/\?([^`]+)`/g)].map(m => m[1]);
    expect(links.length).toBeGreaterThanOrEqual(5);
    for (const query of links) {
      document.body.innerHTML = '';
      open(query);
      expect(await counted(), query).toMatch(/^\d+ scenes?/);
    }
  }, 120000);
});

describe('hostile input', () => {
  it('renders markup typed into the address as text', async () => {
    const page = open('g=%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E&e=%3Cscript%3Ex%3C%2Fscript%3E');
    await counted();
    expect(page.container.querySelector('img[src="x"], script')).toBeNull();
  });
});
