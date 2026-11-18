// The search page after the port, continued from search-page-homer.test.ts:
// pages by rows, the views by form and by grammar, the 100 page, "Show the
// whole scene", the guide and hostile input, on the real corpus. Without the
// data (a fresh worktree) every test skips, loudly.
import { fireEvent, screen, waitFor, within } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { formKey, ownGrammar } from '../lib/result-views';
import { greekFold, greekHitForms, greekHitGrammar, search, type MatchMode, type Reading, type SearchMode } from '../lib/search';
import { counted, open, pageSetup, scenesIn, status } from './search-page-homer-setup';

pageSetup('search-page-homer-pages');
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
// Pages count passages in every view (John, 17 Nov: "Pages count passages in
// every view; By form regroups the same passages, so its pages may draw more
// than N; no per-form counting, no reading every book in those views"). By
// form and By grammar each page holds By work's passages for that page,
// regrouped: a passage with hits of several forms (or filed under several
// headwords) is drawn once under each, so the page draws more rows than N.
describe('pages by rows, grouped by form', () => {
  const pagesOf = () => Number(status().match(/page \d+ of (\d+)/)?.[1] ?? 1);
  // Every page of the search in view: the rows each page draws (every
  // grouping opened, as a reader would open them), each row's reader link,
  // the scene heading over it (By work), and its marked Greek forms. `parts`:
  // each row's marked words split by form, a part to a form, each named by
  // its form and its words (work:segment:position, as the page's word
  // buttons carry them), and `head` the folded label of the heading it is
  // drawn under (By grammar, its headword). By work that is every (instance,
  // form) pair drawn; By form and By grammar, each row is one part. With
  // `perPage`, every page but the last draws exactly that many rows (By
  // work); `passages`: each page's reader links, once each.
  async function walkRows(perPage: number | null) {
    await waitFor(() => expect(status()).toMatch(/page \d+ of \d+$/), { timeout: 60000 });
    const pages = pagesOf();
    const sizes: number[] = [];
    const links: string[] = [];
    const scenes = new Set<string>();
    const parts: { form: string; toks: string[]; head: string }[] = [];
    const passages: string[][] = [];
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
        const head = greekFold(el.closest('section.book-section')?.querySelector('h2 .group-label')?.textContent ?? '');
        const byForm = new Map<string, Set<string>>();
        for (const m of el.querySelectorAll('.inst-snippet.greek mark')) {
          const w = m.closest<HTMLElement>('button.gw');
          expect(w, `${href}: a marked word with no place`).not.toBeNull();
          const f = formKey(m.textContent ?? '');
          (byForm.get(f) ?? byForm.set(f, new Set()).get(f)!).add(`${w!.dataset.w}:${w!.dataset.s}:${w!.dataset.i}`);
        }
        forms += byForm.size;
        for (const [form, toks] of byForm) parts.push({ form, toks: [...toks].sort(), head });
      }
      sizes.push(n);
      passages.push([...new Set(links.slice(links.length - n))].sort());
    }
    expect(sizes.every(k => k > 0), `rows a page: ${sizes}`).toBe(true);
    if (perPage !== null) {
      expect(sizes.slice(0, -1).every(k => k === perPage), `rows a page: ${sizes}`).toBe(true);
      expect(sizes.at(-1)!).toBeLessThanOrEqual(perPage);
    }
    return { pages, sizes, links, passages, scenes, forms, parts, rows: sizes.reduce((a, b) => a + b, 0) };
  }
  // The same search By work: its rows, the scenes they are drawn under (all
  // the bar counts), and the forms they hold, which By form draws a row each.
  // Every page but the last holds 20 passages.
  async function byWork(query: string) {
    open(query);
    const bar = await counted();
    const w = await walkRows(20);
    expect(w.scenes.size, `${query}: scenes drawn`).toBe(scenesIn(bar));
    document.body.innerHTML = '';
    return w;
  }

  it('ὁ, Il. 1, by form: By work\'s pages, each with its own passages, regrouped', async () => {
    const data = await dataHits('ὁ', 'all', 'lemma', 'iliad', 1);
    const work = await byWork('g=ὁ&w=iliad&b=1&ps=20');
    // Every Greek hit the search finds is drawn once By work.
    expect(drawnHits(work.parts)).toEqual(data.hits);
    open('g=ὁ&w=iliad&b=1&ps=20&v=form');
    await counted();
    const form = await walkRows(null);
    console.info(`ὁ, Il. 1: by work ${work.rows} rows on ${work.pages} pages; by form ${form.rows} rows on ${form.pages} pages, ${form.sizes.join(', ')}`);
    expect(form.pages).toBe(work.pages);
    expect(form.passages).toEqual(work.passages);
    // A passage with hits of several forms is drawn under each: page 1 draws more than 20.
    expect(form.sizes[0]).toBeGreaterThan(20);
    // Each (instance, form) pair drawn once, and no pair drawn in another's
    // place: counts and links alone pass a page that draws one form twice.
    expect(ids(form.parts)).toEqual(ids(work.parts));
    // And every hit the search finds is drawn once By form, under its own form.
    expect(drawnHits(form.parts)).toEqual(data.hits);
  }, 300000);

  it('turning to By form keeps the pages and page 1\'s passages', async () => {
    open('g=ὁ&w=iliad&b=1&ps=20');
    await counted();
    await waitFor(() => expect(status()).toMatch(/page \d+ of \d+$/), { timeout: 60000 });
    const byWorkPages = pagesOf();
    const links = () => [...new Set([...document.querySelectorAll('li.instance .inst-ref')].map(a => a.getAttribute('href')))].sort();
    await waitFor(() => expect(document.querySelectorAll('li.instance')).toHaveLength(20), { timeout: 30000 });
    const page1 = links();
    const radio = [...document.querySelectorAll<HTMLInputElement>('input[name="sx-view"]')].find(r => r.value === 'form')!;
    await fireEvent.click(radio);
    await waitFor(() => expect(document.querySelectorAll('li.instance').length).toBeGreaterThan(20), { timeout: 30000 });
    // Long enough for a page count laid out again to show.
    await new Promise(r => setTimeout(r, 500));
    expect(status()).toMatch(/page \d+ of \d+$/);
    expect(pagesOf()).toBe(byWorkPages);
    expect(links()).toEqual(page1);
  }, 120000);

  // The Greek hits a search finds in one book, from its results (the
  // search the page runs), each as `${work}:${segment}:${position}|${fold}`:
  // where the hit stands and its form, folded.
  async function dataHits(grk: string, mode: SearchMode, matchMode: MatchMode, work: string, book: number) {
    const { results } = await search(grk, '', mode, 'all', 'or', [work], matchMode);
    const inBook = results.filter(r => r.meta.book === book);
    const forms = await greekHitForms(inBook, grk, matchMode);
    const hits = inBook.flatMap(r => r.grkPositions.map((pos, i) =>
      `${r.work}:${r.meta.id}:${pos}|${forms.byResult.get(`${r.work}:${r.meta.id}`)?.[i] ?? ''}`)).sort();
    return { inBook, forms, hits };
  }
  // The hits a walk drew, the same way: one for each row a word is marked in.
  const drawnHits = (parts: { form: string; toks: string[] }[]) => parts.flatMap(p => p.toks.map(t => `${t}|${greekFold(p.form)}`)).sort();
  const ids = (parts: { form: string; toks: string[] }[]) => parts.map(p => `${p.form}|${p.toks.join(',')}`).sort();

  // The rows By grammar, worked out from the data: each part (an instance's
  // hits of one form) is drawn once under each headword it is filed under,
  // as `${part}|${headword}`. Filed as paradigmOf files it, from the same
  // inputs the page reads (the readings of the words it holds, narrowed to
  // the headwords searched, and the headwords its form belongs to), but by
  // the rule written out here, not by calling paradigmOf: the headwords
  // its readings name, else those its form belongs to, else the first searched.
  async function grammarRows(parts: { form: string; toks: string[] }[], lemmas: string[], data: Awaited<ReturnType<typeof dataHits>>) {
    const heads = [...new Set(lemmas.map(greekFold))];
    const grammar = ownGrammar(await greekHitGrammar(data.inBook), new Set(heads));
    const readings = new Map<string, Reading[]>();
    const formHeads = new Map<string, string[] | undefined>();
    for (const r of data.inBook) {
      const seg = `${r.work}:${r.meta.id}`;
      r.grkPositions.forEach((pos, i) => {
        readings.set(`${seg}:${pos}`, grammar.byResult.get(seg)?.[i] ?? []);
        formHeads.set(`${seg}:${pos}`, data.forms.headwords.get(data.forms.byResult.get(seg)?.[i] ?? ''));
      });
    }
    const rows: string[] = [];
    for (const part of parts) {
      const { toks } = part;
      for (const t of toks) expect(readings.has(t), `${t}: a hit of the search`).toBe(true);
      const held = toks.flatMap(t => readings.get(t)!);
      const named = heads.filter(h => held.some(r => Object.hasOwn(r, 'lemma') && r.lemma.includes(h)));
      const mapped = heads.filter(h => formHeads.get(toks[0])?.includes(h));
      for (const h of named.length ? named : mapped.length ? mapped : heads.slice(0, 1)) rows.push(`${ids([part])[0]}|${h}`);
    }
    return rows.sort();
  }

  // By grammar with two headwords, a form both own is drawn under each (Codex
  // check of 09cee472c); the pages stay By work's.
  it('two headwords by grammar: By work\'s pages, a form under both drawn twice', async () => {
    const data = await dataHits('o os', 'any', 'headword', 'iliad', 1);
    const work = await byWork('l=o,os&w=iliad&b=1&ps=20');
    // Every Greek hit the search finds is drawn once By work, so the parts
    // below are the data's.
    expect(drawnHits(work.parts)).toEqual(data.hits);
    open('l=o,os&v=grammar&w=iliad&b=1&ps=20');
    await counted();
    // The readings load after the first page; the rows are filed again then.
    await waitFor(() => expect(document.querySelector('.sx-para')).not.toBeNull(), { timeout: 60000 });
    const grammar = await walkRows(null);
    const want = await grammarRows(work.parts, ['o', 'os'], data);
    console.info(`ὁ, ὅς, Il. 1: by work ${work.rows} rows on ${work.pages} pages; by grammar ${grammar.rows} rows on ${grammar.pages} pages (from the data: ${want.length} rows)`);
    expect(grammar.pages).toBe(work.pages);
    expect(grammar.passages).toEqual(work.passages);
    expect(grammar.rows).toBe(want.length);
    // Each row under the headword the filing gives it, read from the heading
    // it is drawn under.
    expect(grammar.parts.map(p => `${ids([p])[0]}|${p.head}`).sort()).toEqual(want);
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
