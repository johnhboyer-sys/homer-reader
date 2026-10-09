// The Maps page's Trojan Plain tab (John, 2026-09-15): the geographic sheet
// is retired and the tab mounts the schematic sheet, with its "Later
// tradition and survey" layer off until the reader switches it on. Real
// apparatus/places.json and the real plate JSON; only the fetch is mocked.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, waitFor } from '@testing-library/svelte';
import MapsPage from '../components/MapsPage.svelte';

const mockFetchPlate = vi.fn();
vi.mock('@shared/lib/data', () => ({
  fetchPlate: (id: string) => mockFetchPlate(id),
}));

const readJson = (rel: string) => JSON.parse(readFileSync(path.resolve(process.cwd(), rel), 'utf-8'));

describe('MapsPage: the Trojan Plain tab', () => {
  afterEach(() => {
    document.body.innerHTML = '';
    window.history.replaceState(null, '', '/');
  });

  it('mounts the schematic sheet, framed on ?focus=, with the tradition layer off until switched on', async () => {
    const schematic = readJson('../apparatus/plates/trojan-plain-schematic.json');
    mockFetchPlate.mockImplementation(async (id: string) => (id === 'trojan-plain-schematic' ? schematic : null));
    window.history.replaceState(null, '', '/maps/?map=plain&focus=hut-of-odysseus');

    const { container, getByRole } = render(MapsPage, {
      props: { base: '', places: readJson('../apparatus/places.json').places, achaean: [], trojan: [], characters: [] },
    });
    await waitFor(() => expect(container.querySelector('#mp-panel-plain svg')).toBeTruthy(), { timeout: 20000 });

    expect(mockFetchPlate).toHaveBeenCalledWith('trojan-plain-schematic');
    expect(mockFetchPlate).not.toHaveBeenCalledWith('trojan-plain');
    const svg = container.querySelector('#mp-panel-plain svg')!;
    expect(svg.getAttribute('aria-label')).toBe(schematic.title);
    // Framed on the focused place, not the whole sheet.
    expect(container.querySelector('#mp-panel-plain .pp-camera')?.getAttribute('transform')).not.toBe('translate(0 0) scale(1)');

    const toggle = getByRole('checkbox', { name: 'Show later tradition and survey' }) as HTMLInputElement;
    expect(toggle.checked).toBe(false);
    expect(svg.querySelector('[data-layer-group]')).toBeNull();

    toggle.click();
    await waitFor(() => expect(container.querySelector('#mp-panel-plain [data-place-id="kum-tepe"]')).toBeTruthy(), {
      timeout: 20000,
    });
    const kum = container.querySelector('#mp-panel-plain [data-place-id="kum-tepe"]')!;
    expect(kum.getAttribute('aria-label')).toContain('Kum Tepe');
    // A traditional site carries its tradition into the accessible name.
    const kesik = container.querySelector('#mp-panel-plain [data-place-id="kesik-tepe"]')!;
    expect(kesik.getAttribute('aria-label')).toContain('Antilochus');
  }, 60000);

  // John, 2026-10-09: the "Kesik cut (contested)" label came off the sheet, but
  // the gazetteer record `kesik-basin` still carries `troad-plain`, so it fell
  // into "Named, not drawn" on every load. It belongs behind the same switch as
  // the other later-tradition sites.
  it('lists the Kesik basin under "Named, not drawn" only once the tradition layer is on', async () => {
    const schematic = readJson('../apparatus/plates/trojan-plain-schematic.json');
    mockFetchPlate.mockImplementation(async (id: string) => (id === 'trojan-plain-schematic' ? schematic : null));
    window.history.replaceState(null, '', '/maps/?map=plain');

    const { container, getByRole } = render(MapsPage, {
      props: { base: '', places: readJson('../apparatus/places.json').places, achaean: [], trojan: [], characters: [] },
    });
    await waitFor(() => expect(container.querySelector('#mp-panel-plain svg')).toBeTruthy(), { timeout: 20000 });
    const panel = container.querySelector('#mp-panel-plain') as HTMLElement;

    const toggle = getByRole('checkbox', { name: 'Show later tradition and survey' }) as HTMLInputElement;
    expect(toggle.checked).toBe(false);
    expect(panel.textContent).not.toContain('Kesik basin');

    toggle.click();
    await waitFor(() => expect(panel.querySelector('[data-place-id="kum-tepe"]')).toBeTruthy(), { timeout: 20000 });
    const section = Array.from(panel.querySelectorAll('.pp-unlocated')).find((el) =>
      /Named, not drawn/.test(el.querySelector('h3')?.textContent ?? ''),
    );
    expect(section?.textContent).toContain('Kesik basin');

    toggle.click();
    await waitFor(() => expect(panel.querySelector('[data-place-id="kum-tepe"]')).toBeNull(), { timeout: 20000 });
    expect(panel.textContent).not.toContain('Kesik basin');
  }, 60000);
});
