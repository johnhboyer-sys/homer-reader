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

  it('shows off-canvas places as a list distinct from unlocated ones (renderPlate\'s three buckets)', async () => {
    mockFetchPlate.mockResolvedValue({
      id: 'test-plate',
      title: 'Test Plate',
      kind: 'geographic',
      status: 'reviewed',
      bbox: [0, 0, 1, 1],
      size: [100, 80],
      layers: [],
    });

    const places = [
      // Projects to [50, 40] -- inside the 100x80 canvas.
      { id: 'located', name: 'Located Place', coords: [0.5, 0.5] as [number, number], certainty: 'certain' as const },
      // Projects to [410, 40] -- a real, defensible position, but off this
      // plate's own frame (renderPlate's `offCanvas` bucket).
      { id: 'off-canvas-place', name: 'Off-Canvas Place', coords: [0.5, 5] as [number, number], certainty: 'traditional' as const },
      // No coords at all -- no defensible position on any sheet.
      { id: 'no-position', name: 'No Position Place', certainty: 'speculative' as const },
    ];

    const { container, getByText } = render(PlatePanel, {
      props: { plateId: 'test-plate', places, title: 'Test Plate' },
    });

    await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());

    // Located: a pin, not in either honesty list.
    expect(container.querySelector('[data-place-id="located"]')).toBeTruthy();

    // Off-canvas: its own list, worded as "look elsewhere," not "unknown."
    const offCanvasSection = container.querySelector('.pp-offcanvas');
    expect(offCanvasSection).toBeTruthy();
    expect(offCanvasSection?.querySelector('h3')?.textContent).toMatch(/Off this sheet \(1\)/);
    expect(getByText('Off-Canvas Place')).toBeTruthy();
    expect(offCanvasSection?.textContent).not.toMatch(/no defensible position/i);

    // Unlocated: the pre-existing "named, not drawn" list, captioned as
    // genuinely unknown -- and it must NOT contain the off-canvas place.
    const unlocatedSections = container.querySelectorAll('.pp-unlocated');
    const namedNotDrawn = Array.from(unlocatedSections).find((el) => /Named, not drawn/.test(el.querySelector('h3')?.textContent ?? ''));
    expect(namedNotDrawn).toBeTruthy();
    expect(namedNotDrawn?.textContent).toMatch(/no defensible position/i);
    expect(getByText('No Position Place')).toBeTruthy();
    expect(namedNotDrawn?.textContent).not.toMatch(/Off-Canvas Place/);
  });

  it('tolerates a hostile layer id (validator-accepted, selector-breaking) in the layer toggle', async () => {
    // A validator-accepted plate/layer id is not a trusted literal: `x"]`
    // interpolated straight into `[data-feature-id="x"]"]` breaks the
    // attribute-value quoting and used to throw a DOMException on toggle
    // (finding 8, 2026-07-28). This id is otherwise a completely ordinary
    // layer -- the fix must not just avoid a crash, it must still actually
    // toggle the right element.
    const hostileId = 'x"]';
    mockFetchPlate.mockResolvedValue({
      id: 'hostile-plate',
      title: 'Hostile Plate',
      kind: 'geographic',
      status: 'reviewed',
      bbox: [0, 0, 1, 1],
      size: [100, 80],
      layers: [
        {
          id: hostileId,
          kind: 'coast',
          default: 'on',
          rings: [[[0, 0], [1, 1]]],
        },
      ],
    });

    const { container, getByRole } = render(PlatePanel, {
      props: { plateId: 'hostile-plate', places: [], title: 'Hostile Plate' },
    });

    await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());

    const targetEl = container.querySelector(`[data-feature-id]`) as SVGElement;
    expect(targetEl.dataset.featureId).toBe(hostileId);
    expect(targetEl.style.display).not.toBe('none');

    const toggle = getByRole('checkbox') as HTMLInputElement;
    expect(() => toggle.click()).not.toThrow();
    await waitFor(() => expect(targetEl.style.display).toBe('none'));

    toggle.click();
    await waitFor(() => expect(targetEl.style.display).not.toBe('none'));
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
