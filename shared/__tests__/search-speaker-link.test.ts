import { cleanup, render, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Search from '../components/Search.svelte';
import { fetchCharacters, fetchSpeeches } from '../lib/data';
import { search } from '../lib/search';

vi.mock('../lib/data', async original => ({
  ...await original<typeof import('../lib/data')>(),
  fetchCharacters: vi.fn(),
  fetchSpeeches: vi.fn(),
}));
vi.mock('../lib/search', async original => ({
  ...await original<typeof import('../lib/search')>(),
  search: vi.fn(),
  speakerRoster: vi.fn(async () => []),
}));

beforeEach(() => {
  vi.mocked(fetchCharacters).mockReset().mockResolvedValue({ achilles: { id: 'achilles', name: 'Achilles' } });
  vi.mocked(fetchSpeeches).mockReset().mockResolvedValue([]);
  vi.mocked(search).mockReset().mockResolvedValue({ results: [], failedWorks: [] });
});
afterEach(() => {
  cleanup();
  window.history.replaceState(null, '', '/');
});

async function open(query: string) {
  window.history.replaceState(null, '', `/search/?g=κλέος&${query}#results`);
  const replace = vi.spyOn(window.history, 'replaceState');
  const page = render(Search);
  await waitFor(() => expect(search).toHaveBeenCalled());
  await waitFor(() => expect(page.container.textContent).toContain('No scenes found'));
  return { params: new URLSearchParams(window.location.search), replace };
}

describe('Homer speaker links', () => {
  it('replaces a single speaker alias with spk before running the search', async () => {
    vi.mocked(search).mockImplementation(async () => {
      expect(new URLSearchParams(window.location.search).get('spk')).toBe('achilles');
      return { results: [], failedWorks: [] };
    });
    const { params, replace } = await open('sp=only&sn=Achilles');
    expect(params.get('spk')).toBe('achilles');
    expect(params.has('sp')).toBe(false);
    expect(params.has('sn')).toBe(false);
    expect(window.location.pathname).toBe('/search/');
    expect(window.location.hash).toBe('#results');
    expect(replace).toHaveBeenCalledTimes(1);
    expect(fetchCharacters).toHaveBeenCalledTimes(1);
  });

  it.each(['sp=except&sn=Achilles', 'sp=only&sn=Achilles,Athena', 'sp=only&sn=Nobody'])(
    'removes an unsupported speaker filter: %s', async query => {
      const { params } = await open(query);
      expect(params.has('sp')).toBe(false);
      expect(params.has('sn')).toBe(false);
      expect(params.has('spk')).toBe(false);
      expect(params.get('g')).toBe('κλέος');
    },
  );

  it('keeps spo=1 and removes the speaker alias', async () => {
    const { params } = await open('sp=only&sn=Achilles&spo=1');
    expect(params.get('spo')).toBe('1');
    expect(params.has('spk')).toBe(false);
    expect(params.has('sp')).toBe(false);
    expect(params.has('sn')).toBe(false);
  });

  it.each(['cast', 'speeches'])('removes the alias when %s data fails to load', async data => {
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    if (data === 'cast') vi.mocked(fetchCharacters).mockRejectedValue(new Error('offline'));
    else vi.mocked(fetchSpeeches).mockRejectedValue(new Error('offline'));
    const { params } = await open('sp=only&sn=Achilles');
    expect(params.has('sp')).toBe(false);
    expect(params.has('sn')).toBe(false);
    expect(params.has('spk')).toBe(false);
  });

  it('does not fetch speech data or rewrite an ordinary search', async () => {
    const { replace } = await open('');
    expect(fetchCharacters).not.toHaveBeenCalled();
    expect(fetchSpeeches).not.toHaveBeenCalled();
    expect(replace).not.toHaveBeenCalled();
  });
});
