// Grammar on the search page (the port of aristotle-reader's page). Grammar
// alone runs on one book of one poem (?w= and ?b= beside ?gr=): a whole
// poem's genitive plurals are the corpus, not an answer. These replace the
// old page's grammar-panel tests with the same behaviours on the new page,
// run on the real corpus (serve-corpus.ts).
import { fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Search from '../components/Search.svelte';
import { CORPUS, HAVE_CORPUS, serveCorpus } from './serve-corpus';

// The first search in a file reads the corpus cold.
vi.setConfig({ testTimeout: 60000 });

const open = (query: string) => {
  window.history.replaceState(null, '', `/search/?${query}`);
  return render(Search);
};
const status = () => document.querySelector('[role="status"]')?.textContent?.replace(/\s+/g, ' ').trim() ?? '';
const counted = async () => {
  await waitFor(() => expect(status()).toMatch(/\d+ scenes?|No scenes found/), { timeout: 30000 });
  return status();
};
const hits = (s: string) => Number(s.match(/· (\d+) hits?/)?.[1] ?? NaN);
const refs = () => [...document.querySelectorAll('.inst-ref')].map(a => a.textContent?.trim() ?? '');
const params = () => new URLSearchParams(window.location.search);

beforeEach((ctx) => {
  if (!HAVE_CORPUS) { console.warn(`grammar-ui: no corpus at ${CORPUS}; skipping`); ctx.skip(); }
  serveCorpus();
});
afterEach(() => window.history.replaceState(null, '', '/'));

describe('grammar alone, held to one book', () => {
  it('runs a ?gr= link on mount and renders its book’s results', async () => {
    open('w=iliad&b=1&gr=case:gen,number:pl');
    expect(await counted()).toMatch(/^19 scenes · 122 hits/);
    expect(refs().length).toBeGreaterThan(0);
    expect(refs().every(r => r.startsWith('1.'))).toBe(true);
    expect(params().get('w')).toBe('iliad');
    expect(params().get('b')).toBe('1');
  });

  it('never widens past one book: without b it asks for a book and counts nothing', async () => {
    open('w=iliad&gr=case:gen,number:pl');
    await waitFor(() => expect(document.querySelector('.narrow-prompt')?.textContent).toMatch(/Choose a book/), { timeout: 30000 });
    expect(status()).not.toMatch(/\d+ scenes?/);
    expect(document.querySelector('.inst-ref')).toBeNull();
  });

  it('asks for a poem and a book when neither is given', async () => {
    open('gr=case:gen,number:pl');
    await waitFor(() => expect(document.querySelector('.narrow-prompt')?.textContent).toMatch(/Choose a poem and a book/), { timeout: 30000 });
    expect(status()).not.toMatch(/\d+ scenes?/);
  });

  it('re-runs under a new book rather than re-filtering the old answer', async () => {
    const page = open('w=iliad&b=1&gr=case:gen,number:pl');
    await counted();
    const sel = document.querySelector('#book-select') as HTMLSelectElement;
    sel.value = '2';
    await fireEvent.change(sel);
    await fireEvent.click(page.getByRole('button', { name: 'Search' }));
    await waitFor(() => expect(params().get('b')).toBe('2'), { timeout: 30000 });
    await waitFor(() => expect(refs()[0]).toMatch(/^2\./), { timeout: 30000 });
    expect(refs().every(r => r.startsWith('2.'))).toBe(true);
    expect(status()).not.toMatch(/^19 scenes · 122 hits/);
  }, 60000);
});

describe('what the rows say', () => {
  it('a speaker filter cuts the grammar hits to that speaker’s lines', async () => {
    open('w=iliad&b=1&gr=case:gen,number:pl&spk=achilles');
    const n = hits(await counted());
    expect(n).toBeGreaterThan(0);
    expect(n).toBeLessThan(122);
  });

  it('marks a word whose analysis allows more than one reading, in words', async () => {
    open('w=iliad&b=1&gr=number:dual');
    await counted();
    const notes = [...document.querySelectorAll('.inst-oneof')].map(n => n.textContent ?? '');
    // Il. 1 holds 176 words that may be dual; the analysis is sure of few.
    expect(status()).toMatch(/^19 scenes · 176 hits/);
    expect(notes).toContain('dual or plural');
    expect(notes.every(n => /\bdual\b/.test(n) && / or /.test(n))).toBe(true);
  });
});
