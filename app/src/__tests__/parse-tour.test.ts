// Round 4: the parse tour is fetched only for a reader URL with ?tour=parse,
// and still opens there on the first visit (the real component, mounted on
// demand).
import { describe, it, expect, afterEach, vi } from 'vitest';
import { waitFor } from '@testing-library/svelte';
import { initParseTour } from '../lib/parse-tour';

describe('parse tour, loaded on demand', () => {
  afterEach(() => {
    document.body.innerHTML = '';
    try { localStorage.clear(); } catch { /* none here */ }
    window.history.replaceState(null, '', '/');
  });

  it('loads nothing on an ordinary reader URL', () => {
    const load = vi.fn(async () => {});
    expect(initParseTour('', load)).toBeNull();
    expect(initParseTour('?loc=1.1', load)).toBeNull();
    expect(load).not.toHaveBeenCalled();
  });

  it('opens the tour on a ?tour=parse URL', async () => {
    window.history.replaceState(null, '', '/iliad/book/1/?tour=parse');
    await initParseTour(window.location.search);
    await waitFor(() => expect(document.querySelector('[role="dialog"][aria-label="Reading the Greek: a quick tour"]')).not.toBeNull());
  });
});
