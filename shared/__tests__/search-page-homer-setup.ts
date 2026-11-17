// Shared by search-page-homer.test.ts and search-page-homer-pages.test.ts:
// the page on the real corpus, served from app/public/data by a fetch spy.
// The suite is two files so each runs in one worker's default heap.
import { render, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, expect, vi } from 'vitest';
import Search from '../components/Search.svelte';
import { CORPUS, HAVE_CORPUS, serveCorpus } from './serve-corpus';

// Iliad 1's scenes are marked as a draft here (the shipped data has every
// book reviewed), so the heading's badge can be seen; the Odyssey stays as shipped.
const serve = () => serveCorpus({
  'iliad/book-01.json': b => ({ ...b, apparatus: { ...b.apparatus, draft: true } }),
});

export const open = (query: string) => {
  window.history.replaceState(null, '', `/search/?${query}`);
  return render(Search);
};
export const status = () => document.querySelector('[role="status"]')?.textContent?.replace(/\s+/g, ' ').trim() ?? '';
export const counted = async () => {
  await waitFor(() => expect(status()).toMatch(/\d+ scenes?|No scenes found/), { timeout: 30000 });
  return status();
};
export const refs = () => [...document.querySelectorAll('.inst-ref')].map(a => a.textContent?.trim() ?? '');
export const scenesIn = (bar: string) => Number(bar.match(/^(\d+) scenes?/)?.[1] ?? 0);

export function pageSetup(name: string) {
  // The first search in a file reads the corpus cold.
  vi.setConfig({ testTimeout: 60000 });
  beforeEach((ctx) => {
    if (!HAVE_CORPUS) { console.warn(`${name}: no corpus at ${CORPUS}; skipping`); ctx.skip(); }
    serve();
  });
  afterEach(() => window.history.replaceState(null, '', '/'));
}
