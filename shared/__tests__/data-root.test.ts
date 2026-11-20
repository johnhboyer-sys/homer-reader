import { afterEach, describe, expect, it, vi } from 'vitest';

// PUBLIC_DATA_ROOT (the Cloudflare build, data on R2; docs/cloudflare.md) is
// read into a top-level const at build time, so each case stubs the env and
// imports a fresh copy of the module. Ported from aristotle-reader (PR #222).
describe('PUBLIC_DATA_ROOT build-time root', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
    vi.resetModules();
    delete (globalThis as { __ARISTOTLE_DATA_ROOT__?: string }).__ARISTOTLE_DATA_ROOT__;
  });

  const okJson = (body: unknown) => vi.spyOn(globalThis, 'fetch')
    .mockResolvedValue({ ok: true, json: async () => body } as Response);

  it('falls back to BASE_URL/data when it is unset', async () => {
    vi.resetModules();
    const fresh = await import('../lib/data');
    const fetchMock = okJson({ speeches: [] });
    await fresh.fetchSpeeches('Iliad');
    expect(String(fetchMock.mock.calls[0][0])).toMatch(/^\/data\/Iliad\/speeches\.json$/);
  });

  it('roots data.ts fetches there, without a trailing slash', async () => {
    vi.stubEnv('PUBLIC_DATA_ROOT', 'https://data.example.com/');
    vi.resetModules();
    const fresh = await import('../lib/data');
    const fetchMock = okJson({ speeches: [] });
    await fresh.fetchSpeeches('Iliad');
    expect(fetchMock).toHaveBeenCalledWith('https://data.example.com/Iliad/speeches.json');
  });

  it('roots search.ts fetches there too', async () => {
    vi.stubEnv('PUBLIC_DATA_ROOT', 'https://data.example.com');
    vi.resetModules();
    const fresh = await import('../lib/search');
    const fetchMock = okJson({});
    await fresh.loadEngChapters('Iliad');
    expect(String(fetchMock.mock.calls[0][0])).toBe('https://data.example.com/Iliad/search/eng-chapters.json');
  });

  it('still loses to the desktop override', async () => {
    vi.stubEnv('PUBLIC_DATA_ROOT', 'https://data.example.com');
    vi.resetModules();
    const fresh = await import('../lib/data');
    (globalThis as { __ARISTOTLE_DATA_ROOT__?: string }).__ARISTOTLE_DATA_ROOT__ = 'asset://localhost/corpus';
    const fetchMock = okJson({ speeches: [] });
    await fresh.fetchSpeeches('Odyssey');
    expect(fetchMock).toHaveBeenCalledWith('asset://localhost/corpus/Odyssey/speeches.json');
  });
});
