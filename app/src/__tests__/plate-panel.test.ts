// PlatePanel.svelte (P4): fetches a plate by id through @shared/lib/data's
// fetchPlate (mocked here) and renders it via the REAL shared/lib/plate.ts /
// shared/lib/shield.ts renderers -- only the network boundary is mocked, so
// these tests exercise the actual rendering + layer-toggle + honesty-list
// wiring the component is responsible for.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, waitFor } from '@testing-library/svelte';
import PlatePanel from '../components/maps/PlatePanel.svelte';

const mockFetchPlate = vi.fn();
vi.mock('@shared/lib/data', () => ({
  fetchPlate: (id: string) => mockFetchPlate(id),
}));

describe('PlatePanel', () => {
  beforeEach(() => {
    mockFetchPlate.mockReset();
  });
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('renders a geographic plate, its draft badge, an on/off layer toggle, and the unlocated list', async () => {
    mockFetchPlate.mockResolvedValue({
      id: 'test-plate',
      title: 'Test Plate',
      kind: 'geographic',
      status: 'draft',
      seed: 1,
      bbox: [0, 0, 1, 1],
      size: [100, 80],
      layers: [
        {
          id: 'coast-a',
          kind: 'coast',
          default: 'on',
          rings: [[[0, 0], [1, 1]]],
        },
      ],
    });

    const places = [
      { id: 'located', name: 'Located Place', coords: [0.5, 0.5] as [number, number], certainty: 'certain' as const },
      { id: 'not-located', name: 'Unlocated Place', certainty: 'speculative' as const },
    ];

    const { container, getByText, getByRole } = render(PlatePanel, {
      props: { plateId: 'test-plate', places, title: 'Test Plate' },
    });

    await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());

    expect(mockFetchPlate).toHaveBeenCalledWith('test-plate');
    expect(container.querySelector('svg')?.getAttribute('aria-label')).toBe('Test Plate');
    expect(container.querySelector('.draft-badge')?.getAttribute('title')).toMatch(/AI-drafted apparatus/i);
    expect(getByText('Unlocated Place')).toBeTruthy();
    expect(container.querySelector('[data-place-id="located"]')).toBeTruthy();

    const toggle = getByRole('checkbox', { name: /show coast a/i }) as HTMLInputElement;
    expect(toggle.checked).toBe(true);
    const coastEl = container.querySelector('[data-feature-id="coast-a"]') as SVGElement;
    expect(coastEl.style.display).not.toBe('none');

    toggle.click();
    await waitFor(() => expect(coastEl.style.display).toBe('none'));
  });

  it('renders the Shield of Achilles (schematic bands) via the real apparatus file, all 10 bands', async () => {
    // import.meta.url resolves relative URLs against Vite's HTTP base under
    // vitest, not the filesystem (see CLAUDE.md's shared/ vitest gotcha,
    // 2026-07-27) -- process.cwd() is this package's own dir (app/) when run
    // via `npx vitest run` here, same fix as that gotcha describes.
    const shieldRaw = JSON.parse(
      readFileSync(path.resolve(process.cwd(), '../apparatus/plates/shield-of-achilles.json'), 'utf-8'),
    );
    mockFetchPlate.mockResolvedValue(shieldRaw);

    const { container } = render(PlatePanel, {
      props: { plateId: 'shield-of-achilles', title: 'The Shield of Achilles' },
    });

    await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());

    expect(container.querySelectorAll('[data-band-id]').length).toBe(10);
    expect(container.querySelector('svg')?.getAttribute('aria-label')).toBe('The Shield of Achilles');
    // The shield renderer takes no places -- no layer toggles, no unlocated list.
    expect(container.querySelector('.pp-toggles')).toBeNull();
    expect(container.querySelector('.pp-unlocated')).toBeNull();
  });

  it('degrades gracefully, not a crash or an empty box, when the plate file does not exist yet', async () => {
    mockFetchPlate.mockResolvedValue(null);

    const { getByText, container } = render(PlatePanel, {
      props: { plateId: 'troy-citadel', title: 'The Troy Citadel' },
    });

    await waitFor(() => expect(getByText(/hasn't been drawn yet/i)).toBeTruthy());
    expect(container.querySelector('svg')).toBeNull();
  });
});
