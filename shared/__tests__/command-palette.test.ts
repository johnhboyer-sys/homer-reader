import { cleanup, fireEvent, render, screen } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import CommandPalette from '../components/CommandPalette.svelte';

// The palette asks for the name and word indexes when it opens. There is no
// server here; it must work without them, as it does offline.
beforeEach(() => { vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('no network in tests')))); });
afterEach(() => { vi.unstubAllGlobals(); });
afterEach(cleanup);

async function openFrom(trigger: HTMLButtonElement) {
  trigger.focus();
  await fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
  return screen.findByRole<HTMLInputElement>('combobox');
}

describe('CommandPalette', () => {
  it('opens from Ctrl+K, ranks books/scenes/citations, navigates, and restores focus', async () => {
    const trigger = document.body.appendChild(document.createElement('button'));
    const onNavigate = vi.fn();
    render(CommandPalette, {
      props: {
        work: 'iliad',
        bookNum: 1,
        onNavigate,
        scenes: [{ summary: 'Chryses seeks ransom from Agamemnon.', startLine: 8, endLine: 32, place: 'Achaean camp' }],
      },
    });

    const input = await openFrom(trigger);
    expect(document.activeElement).toBe(input);

    await fireEvent.input(input, { target: { value: 'od' } });
    expect(screen.getAllByRole('option').every((item) => item.textContent?.includes('Odyssey'))).toBe(true);

    await fireEvent.input(input, { target: { value: 'ransom' } });
    expect(screen.getByText(/Chryses seeks ransom/)).toBeInTheDocument();

    await fireEvent.input(input, { target: { value: '1.200' } });
    expect(screen.getByText('Iliad · Book 1, line 200')).toBeInTheDocument();
    await fireEvent.keyDown(input, { key: 'Enter' });
    expect(onNavigate).toHaveBeenCalledWith('/iliad/book/1?loc=1.200');

    const reopened = await openFrom(trigger);
    await fireEvent.keyDown(reopened, { key: 'Escape' });
    expect(document.activeElement).toBe(trigger);
    trigger.remove();
  });

  it('uses the current Odyssey book scenes and parses citations in its work context', async () => {
    const trigger = document.body.appendChild(document.createElement('button'));
    const onNavigate = vi.fn();
    render(CommandPalette, {
      props: {
        work: 'odyssey',
        bookNum: 9,
        onNavigate,
        scenes: [{ summary: 'Odysseus and his companions enter the Cyclops cave.', startLine: 181, endLine: 192 }],
      },
    });

    const input = await openFrom(trigger);
    await fireEvent.input(input, { target: { value: 'Cyclops' } });
    expect(screen.getByText(/Cyclops cave/)).toBeInTheDocument();

    await fireEvent.input(input, { target: { value: '9.366' } });
    expect(screen.getByText('Odyssey · Book 9, line 366')).toBeInTheDocument();
    await fireEvent.keyDown(input, { key: 'Enter' });
    expect(onNavigate).toHaveBeenCalledWith('/odyssey/book/9?loc=9.366');
    trigger.remove();
  });

  it('accepts the work-prefixed citation its own placeholder advertises, and cross-work jumps', async () => {
    const trigger = document.body.appendChild(document.createElement('button'));
    const onNavigate = vi.fn();
    render(CommandPalette, {
      props: { work: 'odyssey', bookNum: 9, onNavigate, scenes: [] },
    });

    let input = await openFrom(trigger);

    // The prefixed form the "Go to verse citation" placeholder advertises
    // ("e.g. Od. 9.366") must resolve here too — same grammar, not "No matches."
    await fireEvent.input(input, { target: { value: 'Od. 9.366' } });
    expect(screen.getByText('Odyssey · Book 9, line 366')).toBeInTheDocument();
    await fireEvent.keyDown(input, { key: 'Enter' });
    expect(onNavigate).toHaveBeenCalledWith('/odyssey/book/9?loc=9.366');

    // Enter navigates AND closes the palette — reopen for the next query.
    input = await openFrom(trigger);

    // A prefix naming the OTHER work resolves a cross-work jump, even though
    // this palette instance is mounted for the Odyssey.
    await fireEvent.input(input, { target: { value: 'Il. 1.1' } });
    expect(screen.getByText('Iliad · Book 1, line 1')).toBeInTheDocument();
    await fireEvent.keyDown(input, { key: 'Enter' });
    expect(onNavigate).toHaveBeenCalledWith('/iliad/book/1?loc=1.1');

    trigger.remove();
  });

  it('rejects an invalid book/line in a prefixed citation', async () => {
    const trigger = document.body.appendChild(document.createElement('button'));
    render(CommandPalette, {
      props: { work: 'odyssey', bookNum: 9, onNavigate: vi.fn(), scenes: [] },
    });

    const input = await openFrom(trigger);
    await fireEvent.input(input, { target: { value: 'Il. 99.1' } });
    expect(screen.queryByText(/Iliad · Book 99/)).not.toBeInTheDocument();
    trigger.remove();
  });
});

// ── Round 3: the same palette on every page ────────────────────────────────
describe('CommandPalette, with no poem open', () => {
  it('reads a bare citation in both poems and opens the Iliad on Enter', async () => {
    const trigger = document.body.appendChild(document.createElement('button'));
    const onNavigate = vi.fn();
    render(CommandPalette, { props: { onNavigate } });

    const input = await openFrom(trigger);
    await fireEvent.input(input, { target: { value: '6.237' } });
    const options = screen.getAllByRole('option').map((o) => o.textContent);
    expect(options[0]).toContain('Iliad · Book 6, line 237');
    expect(options[1]).toContain('Odyssey · Book 6, line 237');
    await fireEvent.keyDown(input, { key: 'Enter' });
    expect(onNavigate).toHaveBeenCalledWith('/iliad/book/6?loc=6.237');
    trigger.remove();
  });

  it('shows every book of both poems before anything is typed, one link each', async () => {
    const trigger = document.body.appendChild(document.createElement('button'));
    const onNavigate = vi.fn();
    render(CommandPalette, { props: { onNavigate } });

    await openFrom(trigger);
    const books = screen.getByRole('navigation', { name: 'Every book' });
    expect(books.querySelectorAll('ol a').length).toBe(48);
    const od23 = screen.getByRole('link', { name: 'Odyssey, Book 23' });
    expect(od23.getAttribute('href')).toBe('/odyssey/book/23');
    await fireEvent.click(od23);
    expect(onNavigate).toHaveBeenCalledWith('/odyssey/book/23');
    trigger.remove();
  });

  it('marks the open book in the grid when the reader mounts it', async () => {
    const trigger = document.body.appendChild(document.createElement('button'));
    render(CommandPalette, { props: { work: 'iliad', bookNum: 6, onNavigate: vi.fn() } });
    await openFrom(trigger);
    expect(screen.getByRole('link', { name: 'Iliad, Book 6' }).getAttribute('aria-current')).toBe('page');
    expect(screen.getByRole('link', { name: 'Odyssey, Book 6' }).hasAttribute('aria-current')).toBe(false);
    trigger.remove();
  });

  it('finds a page of the site by name', async () => {
    const trigger = document.body.appendChild(document.createElement('button'));
    const onNavigate = vi.fn();
    render(CommandPalette, { props: { onNavigate } });
    const input = await openFrom(trigger);
    await fireEvent.input(input, { target: { value: 'genealog' } });
    expect(screen.getByRole('option', { name: /Genealogies/ })).toBeInTheDocument();
    await fireEvent.keyDown(input, { key: 'Enter' });
    expect(onNavigate).toHaveBeenCalledWith('/genealogies/');
    trigger.remove();
  });

  it('hands what it cannot place to the full-text search, by Enter or by its link', async () => {
    const trigger = document.body.appendChild(document.createElement('button'));
    const onNavigate = vi.fn();
    render(CommandPalette, { props: { onNavigate } });

    let input = await openFrom(trigger);
    await fireEvent.input(input, { target: { value: 'rosy-fingered' } });
    expect(screen.queryAllByRole('option').length).toBe(0);
    const link = screen.getByRole('link', { name: /Search the poems for “rosy-fingered”/ });
    expect(link.getAttribute('href')).toBe('/search?q=rosy-fingered');
    await fireEvent.keyDown(input, { key: 'Enter' });
    expect(onNavigate).toHaveBeenCalledWith('/search?q=rosy-fingered');

    input = await openFrom(trigger);
    await fireEvent.input(input, { target: { value: 'od' } });
    await fireEvent.click(screen.getByRole('link', { name: /Search the poems for “od”/ }));
    expect(onNavigate).toHaveBeenLastCalledWith('/search?q=od');
    trigger.remove();
  });

  it('keeps Tab inside the dialog, its links included', async () => {
    const trigger = document.body.appendChild(document.createElement('button'));
    render(CommandPalette, { props: { onNavigate: vi.fn() } });
    const input = await openFrom(trigger);
    const dialog = screen.getByRole('dialog');
    const focusables = dialog.querySelectorAll<HTMLElement>('input, button, a[href]');
    const last = focusables[focusables.length - 1];
    last.focus();
    await fireEvent.keyDown(last, { key: 'Tab' });
    expect(document.activeElement).toBe(input);
    trigger.remove();
  });
});
