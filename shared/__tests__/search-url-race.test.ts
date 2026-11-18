import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Search from '../components/Search.svelte';
import { fetchCharacters, fetchSpeeches, fetchLemmaPickerShard } from '../lib/data';
import { search, lemmaOptions } from '../lib/search';

// Keep Svelte's module instance: resetting modules breaks component mounting.
vi.mock('../lib/data', async original => ({
  ...await original<typeof import('../lib/data')>(),
  fetchLemmaPickerShard: vi.fn(async () => ({})),
  fetchCharacters: vi.fn(),
  fetchSpeeches: vi.fn(),
}));
vi.mock('../lib/search', async original => ({
  ...await original<typeof import('../lib/search')>(),
  lemmaOptions: vi.fn(async () => [['noos']]),
  search: vi.fn(),
  speakerRoster: vi.fn(async () => []),
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>(done => { resolve = done; });
  return { promise, resolve };
}

beforeEach(() => {
  vi.mocked(fetchLemmaPickerShard).mockReset().mockResolvedValue({});
  vi.mocked(lemmaOptions).mockClear();
  vi.mocked(fetchCharacters).mockReset();
  vi.mocked(fetchSpeeches).mockReset().mockResolvedValue([]);
  vi.mocked(search).mockReset().mockResolvedValue({ results: [], failedWorks: [] });
});
afterEach(() => {
  cleanup();
  window.history.replaceState(null, '', '/');
});

async function openSlowA() {
  const lookup = deferred<Awaited<ReturnType<typeof fetchCharacters>>>();
  vi.mocked(fetchCharacters).mockReturnValue(lookup.promise);
  window.history.replaceState(null, '', '/search/?g=κλέος&sp=only&sn=Achilles');
  const page = render(Search);
  await waitFor(() => {
    expect(fetchCharacters).toHaveBeenCalledTimes(1);
    expect(fetchSpeeches).toHaveBeenCalled();
  });
  expect(search).not.toHaveBeenCalled();
  return {
    page,
    async finishA() {
      // act drains the lookup, searchFromUrl's continuation and Svelte updates
      // before the final assertions (including the negative search assertion).
      await act(async () => {
        lookup.resolve({ achilles: { id: 'achilles', name: 'Achilles' } });
        await lookup.promise;
      });
    },
  };
}

async function expectEnglishOnly(page: ReturnType<typeof render>, query: string) {
  await waitFor(() => expect(page.getByRole('status').textContent).toBe('No scenes found.'));
  expect((page.container.querySelector('#grk-input') as HTMLTextAreaElement).value).toBe('');
  expect((page.container.querySelector('#eng-input') as HTMLTextAreaElement).value).toBe(query);
  expect(page.getByLabelText('Spoken by')).toHaveValue('');
  expect(search).toHaveBeenCalledTimes(1);
  expect(vi.mocked(search).mock.calls.map(args => args.slice(0, 2))).toEqual([['', query]]);
  const params = new URLSearchParams(window.location.search);
  expect(params.get('e')).toBe(query);
  for (const key of ['g', 'sp', 'sn', 'spk', 'spo']) expect(params.has(key)).toBe(false);
  expect(page.container.querySelectorAll('li.instance')).toHaveLength(0);
}

describe('search URL load races', () => {
  it('keeps URL B controls and results when URL A finishes its speech lookup later', async () => {
    const { page, finishA } = await openSlowA();
    window.history.replaceState(null, '', '/search/?e=glory');
    await fireEvent(window, new PopStateEvent('popstate'));
    await expectEnglishOnly(page, 'glory');

    await finishA();

    await expectEnglishOnly(page, 'glory');
  });

  it('keeps a manual search when URL A finishes its speech lookup later', async () => {
    const { page, finishA } = await openSlowA();
    const english = page.container.querySelector('#eng-input') as HTMLTextAreaElement;
    await fireEvent.input(english, { target: { value: 'honour' } });
    await fireEvent.click(page.getByRole('button', { name: 'Search', exact: true }));
    await expectEnglishOnly(page, 'honour');

    await finishA();

    await expectEnglishOnly(page, 'honour');
  });
});

// Unlike speech-data races above, these loads wait on dictionary headwords.
async function openSlowLemma() {
  const lookup = deferred<Awaited<ReturnType<typeof fetchLemmaPickerShard>>>();
  vi.mocked(fetchLemmaPickerShard).mockReturnValue(lookup.promise);
  window.history.replaceState(null, '', `/search/?l=${encodeURIComponent('νοῦς')}`);
  const page = render(Search);
  await waitFor(() => expect(fetchLemmaPickerShard).toHaveBeenCalledWith('n'));
  expect(search).not.toHaveBeenCalled();
  return {
    page,
    async finish() {
      await act(async () => {
        lookup.resolve({ noos: { n: 1, c: [{ h: 'νοῦς', k: 'noos' }] } });
        await lookup.promise;
      });
      await waitFor(() => expect(lemmaOptions).toHaveBeenCalledWith(['nous']));
      expect(vi.mocked(fetchLemmaPickerShard).mock.calls.length).toBeGreaterThanOrEqual(2);
    },
  };
}

describe('search URL headword lookup races', () => {
  it('keeps URL B after URL A’s headword lookup resolves', async () => {
    const { page, finish } = await openSlowLemma();
    window.history.replaceState(null, '', '/search/?e=glory');
    await fireEvent(window, new PopStateEvent('popstate'));
    await expectEnglishOnly(page, 'glory');
    await finish();
    await expectEnglishOnly(page, 'glory');
  });

  it('keeps a manual search started while URL A’s headword lookup is pending', async () => {
    const { page, finish } = await openSlowLemma();
    const english = page.container.querySelector('#eng-input') as HTMLTextAreaElement;
    await fireEvent.input(english, { target: { value: 'honour' } });
    await fireEvent.click(page.getByRole('button', { name: 'Search', exact: true }));
    await expectEnglishOnly(page, 'honour');
    await finish();
    await expectEnglishOnly(page, 'honour');
  });
});
