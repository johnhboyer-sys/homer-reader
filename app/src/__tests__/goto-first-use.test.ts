// Round 4: the palette is never in a page's first load, the reader's included.
// These run the REAL loader (no injected `load`), so they prove the first
// press of Cmd/Ctrl+K, or the first click on a Go-to control, fetches the
// palette and opens it, and that the reader's book and scenes reach it.
import { describe, it, expect, afterEach, vi } from 'vitest';
import { waitFor } from '@testing-library/svelte';
import { initGoto } from '../lib/goto';

// Only the network boundary is mocked (as plate-panel.test.ts does): data.ts
// pulls the glossary markdown, which this suite's Vite root may not read.
vi.mock('@shared/lib/data', () => ({
  fetchPlaces: async () => ({ places: [] }),
  fetchCharacters: async () => ({}),
  fetchColumns: async () => ({}),
  fetchLemmata: async () => ({}),
  parseLocation: () => null,
}));

const dialog = () => document.querySelector<HTMLElement>('[role="dialog"][aria-modal="true"]');

describe('Go-to on first use (real palette, loaded on demand)', () => {
  let teardown: (() => void) | undefined;
  afterEach(() => { teardown?.(); teardown = undefined; document.body.innerHTML = ''; });

  it('the first Cmd/Ctrl+K opens the palette with focus in its field', async () => {
    document.body.innerHTML = '<a id="go" href="/search" data-goto>Go to</a>';
    teardown = initGoto({ triggers: [document.getElementById('go')!] });
    expect(dialog()).toBeNull();
    const key = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true, cancelable: true });
    window.dispatchEvent(key);
    expect(key.defaultPrevented).toBe(true);
    await waitFor(() => expect(dialog()).not.toBeNull());
    await waitFor(() => expect(document.activeElement).toHaveClass('cp-input'));
  });

  it('the first click on the header Go to field opens it, not /search', async () => {
    document.body.innerHTML = '<a id="go" href="/search" data-goto>Go to</a>';
    const go = document.getElementById('go') as HTMLAnchorElement;
    teardown = initGoto({ triggers: [go] });
    const click = new MouseEvent('click', { bubbles: true, cancelable: true });
    go.dispatchEvent(click);
    expect(click.defaultPrevented).toBe(true);
    await waitFor(() => expect(dialog()).not.toBeNull());
  });

  it("the reader's Go to button opens it on first press, with the book's scenes", async () => {
    document.body.innerHTML = '<button type="button" class="command-palette-trigger">Go to</button>';
    const btn = document.querySelector<HTMLElement>('.command-palette-trigger')!;
    teardown = initGoto({
      triggers: [btn],
      work: 'iliad',
      book: { bookNum: 1, scenes: [{ summary: 'Chryses begs for his daughter', startLine: 12, endLine: 42 }] },
    });
    btn.click();
    await waitFor(() => expect(dialog()).not.toBeNull());
    const input = document.querySelector<HTMLInputElement>('.cp-input')!;
    input.value = 'Chryses';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    await waitFor(() => expect(dialog()!.textContent).toContain('Chryses begs for his daughter'));
  });

  // The palette's styles ride in its chunk (<svelte:options css="injected">),
  // since no page links its stylesheet any more: they must arrive with it.
  it('brings its own styles when it mounts', async () => {
    document.body.innerHTML = '<a id="go" href="/search" data-goto>Go to</a>';
    teardown = initGoto({ triggers: [document.getElementById('go')!] });
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true, cancelable: true }));
    await waitFor(() => expect(dialog()).not.toBeNull());
    const css = [...document.querySelectorAll('style')].map((s) => s.textContent).join('');
    expect(css).toContain('.cp-backdrop');
  });
});
