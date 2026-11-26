// Review finding (round 5): the lexicon's counts arrive after the names and
// re-rank them ("hec": Hecuba, Hector becomes Hector, Hecuba). The selection
// kept its row number, so a reader who had arrowed down to Hector and pressed
// Enter opened Hecuba. The selection must follow the item, not the row.
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';

let resolveLemmata: (l: Record<string, { slug: string; head: string; count: number }>) => void = () => {};

vi.mock('../lib/data', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../lib/data')>()),
  fetchPlaces: async () => ({ places: [] }),
  // Hecuba listed first, so before the counts land she ranks first.
  fetchCharacters: async () => ({
    hecuba: { id: 'hecuba', name: 'Hecuba', greek: 'Ἑκάβη' },
    hector: { id: 'hector', name: 'Hector', greek: 'Ἕκτωρ' },
  }),
  fetchColumns: () => new Promise(() => {}),
  fetchLemmata: () => new Promise((r) => { resolveLemmata = r; }),
}));

import CommandPalette from '../components/CommandPalette.svelte';

afterEach(cleanup);

describe('CommandPalette, when late counts re-rank the results', () => {
  it('keeps the selected item, not its row number', async () => {
    const trigger = document.body.appendChild(document.createElement('button'));
    const onNavigate = vi.fn();
    render(CommandPalette, { props: { onNavigate } });
    trigger.focus();
    await fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
    const input = await screen.findByRole<HTMLInputElement>('combobox');

    await fireEvent.input(input, { target: { value: 'hec' } });
    await waitFor(() => expect(screen.getAllByRole('option').map((o) => o.textContent)).toEqual(
      [expect.stringContaining('Hecuba'), expect.stringContaining('Hector')],
    ));
    await fireEvent.keyDown(input, { key: 'ArrowDown' });
    expect(screen.getByRole('option', { selected: true }).textContent).toContain('Hector');

    resolveLemmata({
      hektor: { slug: 'hektor', head: 'Ἕκτωρ', count: 454 },
      hekabe: { slug: 'hekabe', head: 'Ἑκάβη', count: 8 },
    });
    await waitFor(() => expect(screen.getAllByRole('option')[0].textContent).toContain('Hector'));
    expect(screen.getByRole('option', { selected: true }).textContent).toContain('Hector');

    await fireEvent.keyDown(input, { key: 'Enter' });
    expect(onNavigate).toHaveBeenCalledWith('/characters/#roster-hector');
    trigger.remove();
  });
});
