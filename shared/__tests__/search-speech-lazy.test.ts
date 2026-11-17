// The speech data (speeches.json for each poem and characters.json, ~350 KB)
// loads only when a speech filter needs it: a speech link (spo, spk), the
// "Speeches only" button, or the reader reaching for the Spoken-by menu. Not
// after every search. In a file of its own: lib/data caches the fetches for
// the life of the module, so an earlier test would hide them.
import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Search from '../components/Search.svelte';
import { CORPUS, HAVE_CORPUS, serveCorpus } from './serve-corpus';

vi.setConfig({ testTimeout: 60000 });

const open = (query: string) => {
  window.history.replaceState(null, '', `/search/?${query}`);
  return render(Search);
};
const status = () => document.querySelector('[role="status"]')?.textContent?.replace(/\s+/g, ' ').trim() ?? '';
const counted = () => waitFor(() => expect(status()).toMatch(/\d+ scenes?|No scenes found/), { timeout: 30000 });
const fetched = () => vi.mocked(fetch).mock.calls.map(([url]) => decodeURIComponent(String(url)));
const speechFetches = () => fetched().filter(u => /speeches\.json|characters\.json/.test(u));

beforeEach((ctx) => {
  if (!HAVE_CORPUS) { console.warn(`search-speech-lazy: no corpus at ${CORPUS}; skipping`); ctx.skip(); }
  serveCorpus();
});
afterEach(() => window.history.replaceState(null, '', '/'));

describe('the speech data loads only for a speech filter', () => {
  // These run in order: the first leaves the data unfetched for the second.
  it('a plain search fetches neither speeches.json nor characters.json', async () => {
    const page = open('g=θάλασσα&e=sea');
    await counted();
    // Past the first page's drawing, and anything queued after it.
    await new Promise(r => setTimeout(r, 500));
    expect(fetched().some(u => u.includes('/search/'))).toBe(true);
    expect(speechFetches()).toEqual([]);
    expect((page.getByLabelText('Spoken by') as HTMLSelectElement).options).toHaveLength(1);
  });

  it('reaching for the Spoken-by menu fetches them, and fills it', async () => {
    const page = open('g=θάλασσα');
    await counted();
    expect(speechFetches()).toEqual([]);
    const select = page.getByLabelText('Spoken by') as HTMLSelectElement;
    await fireEvent.pointerEnter(select.closest('label')!);
    await waitFor(() => expect(select.options.length).toBeGreaterThan(10));
    expect(speechFetches().length).toBeGreaterThan(0);
  });

  it('a speech link applies its filter (the data now cached)', async () => {
    open('g=θάλασσα&spo=1');
    await counted();
    expect(status()).toMatch(/^45 scenes · 60 hits/);
  });
});
