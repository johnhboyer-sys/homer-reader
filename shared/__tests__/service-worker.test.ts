import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

// The service worker's contract is "anything you have read is available
// offline", which only holds if each cache write outlives the response. A
// write started and then abandoned (`cache.put(...)` with nothing holding the
// event open) may be killed when the browser terminates the worker after the
// response is delivered, so every write must be handed to event.waitUntil().
//
// sw.js is a plain browser script, not a module: run it inside a fake
// ServiceWorkerGlobalScope and collect the listeners it registers.
// process.cwd() is shared/ under vitest; see CLAUDE.md on import.meta.url.
const SW_SRC = readFileSync(path.resolve(process.cwd(), '../app/public/sw.js'), 'utf8');

const ORIGIN = 'https://example.test';
const SCOPE = ORIGIN + '/homer-reader/';

type Deferred<T> = { promise: Promise<T>; resolve: (v: T) => void };

function defer<T>(): Deferred<T> {
  let resolve!: (v: T) => void;
  const promise = new Promise<T>((r) => { resolve = r; });
  return { promise, resolve };
}

/** Let every queued microtask and timer callback run. */
const flush = () => new Promise((r) => setTimeout(r, 0));

/** Does this promise still have nothing to say once the queue has drained? */
async function pending(p: Promise<unknown>): Promise<boolean> {
  let settled = false;
  p.then(() => { settled = true; }, () => { settled = true; });
  await flush();
  return !settled;
}

interface Harness {
  fetchEvent(url: string, init?: { mode?: string }): {
    response: Promise<Response> | null;
    waits: Promise<unknown>[];
  };
  /** Resolves the one in-flight cache.put, if any. */
  put: Deferred<void>;
  puts: string[];
}

function loadSw(
  { responseOk = true, type = 'basic' }: { responseOk?: boolean; type?: string } = {},
): Harness {
  const listeners = new Map<string, (event: unknown) => void>();
  const put = defer<void>();
  const puts: string[] = [];

  const cache = {
    addAll: async () => {},
    match: async () => undefined,
    put: (request: { url: string }) => {
      puts.push(request.url);
      return put.promise;
    },
  };

  const self = {
    registration: { scope: SCOPE },
    skipWaiting: async () => {},
    clients: { claim: async () => {} },
    addEventListener: (type: string, fn: (event: unknown) => void) => { listeners.set(type, fn); },
  };
  const caches = { open: async () => cache, keys: async () => [], delete: async () => true };
  const fetchImpl = async () => ({
    ok: responseOk,
    type,
    marker: 'network',
    clone: () => ({ marker: 'clone' }),
  });

  // eslint-disable-next-line no-new-func
  new Function('self', 'caches', 'fetch', 'location', SW_SRC)(
    self, caches, fetchImpl, { origin: ORIGIN },
  );

  return {
    put,
    puts,
    fetchEvent(url, init = {}) {
      const waits: Promise<unknown>[] = [];
      let response: Promise<Response> | null = null;
      const event = {
        request: { url, method: 'GET', mode: init.mode ?? 'no-cors' },
        waitUntil: (p: Promise<unknown>) => { waits.push(p); },
        respondWith: (p: Promise<Response>) => { response = p; },
      };
      listeners.get('fetch')!(event);
      return { get response() { return response; }, waits };
    },
  };
}

describe('service worker cache writes are tied to the event lifetime', () => {
  it('network-first: keeps the event alive until the write settles, without delaying the response', async () => {
    const sw = loadSw();
    const event = sw.fetchEvent(SCOPE + 'iliad/1/', { mode: 'navigate' });

    // The reader gets the network response immediately — the write must not
    // sit in front of it.
    await expect(event.response).resolves.toMatchObject({ marker: 'network' });
    expect(sw.puts).toEqual([SCOPE + 'iliad/1/']);

    // ...but the worker must not be allowed to die yet.
    expect(event.waits).toHaveLength(1);
    expect(await pending(event.waits[0])).toBe(true);

    sw.put.resolve();
    expect(await pending(event.waits[0])).toBe(false);
  });

  it('cache-first: keeps the event alive until the write settles, without delaying the response', async () => {
    const sw = loadSw();
    const event = sw.fetchEvent(SCOPE + '_astro/Reader.abc123.css');

    await expect(event.response).resolves.toMatchObject({ marker: 'network' });
    expect(sw.puts).toEqual([SCOPE + '_astro/Reader.abc123.css']);

    expect(event.waits).toHaveLength(1);
    expect(await pending(event.waits[0])).toBe(true);

    sw.put.resolve();
    expect(await pending(event.waits[0])).toBe(false);
  });

  it('holds the event open for font writes too', async () => {
    const sw = loadSw();
    const url = 'https://fonts.gstatic.com/s/gfsdidot/v1/font.woff2';
    const event = sw.fetchEvent(url);

    await expect(event.response).resolves.toMatchObject({ marker: 'network' });
    expect(sw.puts).toEqual([url]);

    expect(event.waits).toHaveLength(1);
    expect(await pending(event.waits[0])).toBe(true);

    sw.put.resolve();
    expect(await pending(event.waits[0])).toBe(false);
  });

  // A cross-origin font arrives as an opaque response: ok is false, and
  // cacheFirst caches it on the `type === 'opaque'` arm instead. That arm needs
  // its own case — with a 'basic' response the first condition short-circuits
  // and the arm is never reached.
  it('holds the event open for an opaque cross-origin response', async () => {
    const sw = loadSw({ responseOk: false, type: 'opaque' });
    const url = 'https://fonts.gstatic.com/s/gfsdidot/v1/font.woff2';
    const event = sw.fetchEvent(url);

    await expect(event.response).resolves.toMatchObject({ type: 'opaque' });
    expect(sw.puts).toEqual([url]);

    expect(event.waits).toHaveLength(1);
    expect(await pending(event.waits[0])).toBe(true);

    sw.put.resolve();
    expect(await pending(event.waits[0])).toBe(false);
  });

  it('does not write, or extend the event, for a failed response', async () => {
    const sw = loadSw({ responseOk: false });
    const event = sw.fetchEvent(SCOPE + 'data/iliad/1.json');

    await expect(event.response).resolves.toMatchObject({ ok: false });
    expect(sw.puts).toEqual([]);
    expect(event.waits).toEqual([]);
  });
});
