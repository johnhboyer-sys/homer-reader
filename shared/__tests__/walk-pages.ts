// Walk every page of a search on the real corpus (search-chapter-draw-homer
// and its -heavy twin): each page must draw rows, each scene on one page
// only. Returns the bar and the scenes drawn.
import { cleanup, fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, expect } from 'vitest';
import Search from '../components/Search.svelte';
import { CORPUS, HAVE_CORPUS, serveCorpus } from './serve-corpus';

const status = () => document.querySelector('[role="status"]')?.textContent?.replace(/\s+/g, ' ').trim() ?? '';

export function walkSetup(name: string) {
  beforeEach((ctx) => {
    if (!HAVE_CORPUS) { console.warn(`${name}: no corpus at ${CORPUS}; skipping`); ctx.skip(); }
    serveCorpus();
  });
  afterEach(() => { cleanup(); window.history.replaceState(null, '', '/'); });
}

// Each row with the scene it is drawn under: the poem and book from its
// reader link, the scene from the heading above it.
function rowsOnPage(): string[] {
  let scene = '';
  const out: string[] = [];
  for (const el of document.querySelectorAll('.sx-chap-n, li.instance')) {
    if (el.matches('.sx-chap-n')) { scene = el.textContent?.trim() ?? ''; continue; }
    const href = el.querySelector('.inst-ref')?.getAttribute('href') ?? '';
    out.push(`${new URL(href, 'http://x').pathname}|${scene}`);
  }
  return out;
}

// Pages are rows (aristotle-reader PR #201, John, 16 Nov: "n results = n rows
// per page"): every page but the last draws exactly `perPage` rows, and a
// scene whose rows run past a page's end heads its part on the next page too,
// and on no other.
export async function walk(query: string, perPage = 40) {
  window.history.replaceState(null, '', `/search/?${query}`);
  render(Search);
  await waitFor(() => expect(status()).toMatch(/^\d+ scenes?/), { timeout: 60000 });
  // The page count shows once every book is laid out ("page 1 of …" until then).
  await waitFor(() => expect(status()).not.toMatch(/…/), { timeout: 120000 });
  const bar = status();
  const scenes = Number(bar.match(/^(\d+) scenes?/)![1]);
  const pages = Number(bar.match(/page \d+ of (\d+)/)?.[1] ?? 1);
  const seen = new Map<string, number[]>();   // scene -> the pages it was drawn on
  let rowsDrawn = 0;
  for (let p = 1; p <= pages; p++) {
    if (p > 1) {
      await fireEvent.click(document.querySelector<HTMLButtonElement>('button.pager-next')!);
      await waitFor(() => expect(document.querySelector('.pager-status')?.textContent).toBe(`Page ${p} of ${pages}`), { timeout: 30000 });
    }
    const rows = await waitFor(() => {
      const r = rowsOnPage();
      expect(r.length, `${query}: page ${p} of ${pages} drew no rows`).toBeGreaterThan(0);
      return r;
    }, { timeout: 30000 });
    if (p < pages) expect(rows.length, `${query}: page ${p} of ${pages}`).toBe(perPage);
    else expect(rows.length, `${query}: last page`).toBeLessThanOrEqual(perPage);
    rowsDrawn += rows.length;
    const keys = [...new Set(rows)];
    keys.forEach((key, j) => {
      const before = seen.get(key);
      // Only the page's first scene may have begun on the page before.
      if (before) expect([j, before.at(-1)], `${query}: ${key} on pages ${before} and ${p}`).toEqual([0, p - 1]);
      seen.set(key, [...(before ?? []), p]);
    });
  }
  return { bar, scenes, pages, drawn: seen.size, rowsDrawn };
}
