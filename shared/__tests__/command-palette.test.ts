import { cleanup, fireEvent, render, screen } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import CommandPalette from '../components/CommandPalette.svelte';

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
