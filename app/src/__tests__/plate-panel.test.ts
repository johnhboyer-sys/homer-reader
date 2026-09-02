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

  it('renders a geographic plate, its draft badge, a category layer toggle, and the unlocated list', async () => {
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

    // A `coast` layer is toggled by the "Show shoreline" category checkbox,
    // not by its own id -- the debug per-layer boxes (up to 28 on troad.json)
    // are gone, replaced by exactly three category toggles (relief, rivers,
    // shoreline; see layerCategory in the component).
    const toggle = getByRole('checkbox', { name: /show shoreline/i }) as HTMLInputElement;
    expect(toggle.checked).toBe(true);
    const coastEl = container.querySelector('[data-feature-id="coast-a"]') as SVGElement;
    expect(coastEl.style.display).not.toBe('none');

    toggle.click();
    await waitFor(() => expect(coastEl.style.display).toBe('none'));

    // Only the shoreline category exists on this plate -- no relief/rivers
    // checkboxes are rendered for layers that were never authored.
    expect(container.querySelectorAll('.pp-toggles .pp-toggle').length).toBe(1 + 4); // shoreline + 4 certainty tiers
  });

  it('filters pins (and their labels) by certainty tier, and leaves the certainty filter off a plate with no places', async () => {
    mockFetchPlate.mockResolvedValue({
      id: 'certainty-plate',
      title: 'Certainty Plate',
      kind: 'geographic',
      status: 'reviewed',
      bbox: [0, 0, 1, 1],
      size: [100, 80],
      layers: [],
    });

    const places = [
      { id: 'sure-thing', name: 'Sure Thing', coords: [0.2, 0.2] as [number, number], certainty: 'certain' as const },
      { id: 'iffy-thing', name: 'Iffy Thing', coords: [0.8, 0.8] as [number, number], certainty: 'speculative' as const },
    ];

    const { container, getByRole } = render(PlatePanel, {
      props: { plateId: 'certainty-plate', places, title: 'Certainty Plate' },
    });

    await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());

    const surePin = container.querySelector('[data-place-id="sure-thing"]') as SVGElement;
    const iffyPin = container.querySelector('[data-place-id="iffy-thing"]') as SVGElement;
    const iffyLabel = container.querySelector('[data-label-for="iffy-thing"]') as SVGElement;
    expect(surePin).toBeTruthy();
    expect(iffyPin).toBeTruthy();
    expect(iffyLabel).toBeTruthy();
    expect(iffyPin.style.display).not.toBe('none');

    const speculativeToggle = getByRole('checkbox', { name: 'speculative' }) as HTMLInputElement;
    expect(speculativeToggle.checked).toBe(true);
    speculativeToggle.click();

    await waitFor(() => expect(iffyPin.style.display).toBe('none'));
    // The label goes with its pin -- never left floating with nothing to
    // point to.
    expect(iffyLabel.style.display).toBe('none');
    // A tier that's still checked is untouched.
    expect(surePin.style.display).not.toBe('none');
  });

  it('filters layers (and their labels) by the placeId certainty, the same way pins are filtered', async () => {
    // A layer carries its place as `placeId` on the plate object, not as
    // `data-place-id` on the SVG (that attribute is pins/dots only). Unticking
    // the place's certainty tier must hide the layer group and its label the
    // same way it hides pins today (`style.display = 'none'`).
    mockFetchPlate.mockResolvedValue({
      id: 'layer-certainty-plate',
      title: 'Layer Certainty Plate',
      kind: 'geographic',
      status: 'reviewed',
      bbox: [0, 0, 1, 1],
      size: [100, 80],
      layers: [
        {
          id: 'river-satnioeis',
          kind: 'river',
          placeId: 'satnioeis',
          label: 'Satnioeis',
          path: [
            [0.2, 0.2],
            [0.8, 0.8],
          ],
        },
      ],
    });

    const places = [
      { id: 'satnioeis', name: 'Satnioeis', certainty: 'traditional' as const },
      { id: 'sure-thing', name: 'Sure Thing', coords: [0.5, 0.5] as [number, number], certainty: 'certain' as const },
    ];

    const { container, getByRole } = render(PlatePanel, {
      props: { plateId: 'layer-certainty-plate', places, title: 'Layer Certainty Plate' },
    });

    await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());

    const layerEl = container.querySelector('[data-layer-id="river-satnioeis"]') as SVGElement;
    const layerLabel = container.querySelector('[data-label-for="river-satnioeis"]') as SVGElement;
    const surePin = container.querySelector('[data-place-id="sure-thing"]') as SVGElement;
    expect(layerEl).toBeTruthy();
    expect(layerLabel).toBeTruthy();
    expect(layerEl.style.display).not.toBe('none');
    expect(layerLabel.style.display).not.toBe('none');

    const traditionalToggle = getByRole('checkbox', { name: 'traditional' }) as HTMLInputElement;
    expect(traditionalToggle.checked).toBe(true);
    traditionalToggle.click();

    await waitFor(() => expect(layerEl.style.display).toBe('none'));
    expect(layerLabel.style.display).toBe('none');
    expect(surePin.style.display).not.toBe('none');
  });

  it('shows no certainty filter for the Shield of Achilles (it takes no places at all)', async () => {
    const shieldRaw = JSON.parse(
      readFileSync(path.resolve(process.cwd(), '../apparatus/plates/shield-of-achilles.json'), 'utf-8'),
    );
    mockFetchPlate.mockResolvedValue(shieldRaw);

    const { container } = render(PlatePanel, {
      props: { plateId: 'shield-of-achilles', title: 'The Shield of Achilles' },
    });

    await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());
    expect(container.querySelector('.pp-certainty-filter')).toBeNull();
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

  it('shows a place carried only by a layer\'s geometry as "drawn as part of the map," not "named, not drawn" (Problem 2)', async () => {
    mockFetchPlate.mockResolvedValue({
      id: 'citadel-like-plate',
      title: 'Citadel-Like Plate',
      kind: 'geographic',
      status: 'reviewed',
      bbox: [0, 0, 1, 1],
      size: [100, 80],
      layers: [
        {
          id: 'wall-circuit',
          kind: 'wall',
          placeId: 'wall-of-troy',
          trace: [[0.1, 0.1], [0.2, 0.2]],
        },
      ],
    });

    const places = [
      // No coords/plateAnchors of its own -- its only defensible position on
      // this plate is the wall-circuit layer's own geometry.
      { id: 'wall-of-troy', name: 'The wall of Troy', certainty: 'certain' as const },
      // No coords, and no layer names it either -- genuinely unlocated.
      { id: 'no-position', name: 'No Position Place', certainty: 'speculative' as const },
    ];

    const { container, getByText } = render(PlatePanel, {
      props: { plateId: 'citadel-like-plate', places, title: 'Citadel-Like Plate' },
    });

    await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());

    // Never pinned.
    expect(container.querySelector('[data-place-id="wall-of-troy"]')).toBeNull();
    // Its own list, distinct from "named, not drawn."
    const drawnByLayerSection = container.querySelector('.pp-drawn-by-layer');
    expect(drawnByLayerSection).toBeTruthy();
    expect(drawnByLayerSection?.querySelector('h3')?.textContent).toMatch(/Drawn as part of the map \(1\)/);
    expect(getByText('The wall of Troy')).toBeTruthy();

    // "Named, not drawn" keeps only the genuinely unlocated place.
    const unlocatedSections = container.querySelectorAll('.pp-unlocated');
    const namedNotDrawn = Array.from(unlocatedSections).find((el) => /Named, not drawn/.test(el.querySelector('h3')?.textContent ?? ''));
    expect(namedNotDrawn).toBeTruthy();
    expect(getByText('No Position Place')).toBeTruthy();
    expect(namedNotDrawn?.textContent).not.toMatch(/wall of Troy/);
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

  it('the "Show shoreline" category toggle hides a layer\'s auxiliaries too (real trojan-plain.json: shore-bronze -> shore-bronze-band)', async () => {
    // shore-bronze is a `coast` layer drawn `style: "approximate"` -- besides
    // its own `data-feature-id="shore-bronze"` line, plate.ts also emits a
    // separate `data-feature-id="shore-bronze-band"` element (the reconstructed
    // shore's blurred halo). Both must carry `data-layer-id="shore-bronze"`
    // (plate.ts, renderLayer) so the category toggle below -- which matches
    // on data-layer-id, not data-feature-id -- hides both together. Before
    // that fix (2026-07-28), an exact data-feature-id match left the band lit
    // on the sheet after its own layer was switched off; the debug per-layer
    // checkbox this test used to drive is gone (2026-07-30, replaced by
    // exactly three category toggles), but the underlying data-layer-id
    // matching this guards is unchanged and still worth pinning down.
    const raw = JSON.parse(
      readFileSync(path.resolve(process.cwd(), '../apparatus/plates/trojan-plain.json'), 'utf-8'),
    );
    mockFetchPlate.mockResolvedValue(raw);

    const { container, getByRole } = render(PlatePanel, {
      props: { plateId: 'trojan-plain', title: 'The Trojan Plain' },
    });

    await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());

    const baseEl = container.querySelector('[data-feature-id="shore-bronze"]') as SVGElement;
    const bandEl = container.querySelector('[data-feature-id="shore-bronze-band"]') as SVGElement;
    expect(baseEl).toBeTruthy();
    expect(bandEl).toBeTruthy();
    expect(baseEl.style.display).not.toBe('none');
    expect(bandEl.style.display).not.toBe('none');

    const toggle = getByRole('checkbox', { name: /show shoreline/i }) as HTMLInputElement;
    expect(toggle.checked).toBe(true);
    toggle.click();

    await waitFor(() => expect(baseEl.style.display).toBe('none'));
    expect(bandEl.style.display).toBe('none');
  });

  it('the "Show relief" category toggle hides every relief layer together (real troad.json), including ids that collide by prefix, and leaves rivers alone', async () => {
    // troad.json's own layer ids collide by prefix: "relief-ida" is a prefix
    // of "relief-ida-north-spurs", "relief-ida-800" and "relief-ida-1200" --
    // four DISTINCT authored layers, all `kind: "relief"`. Under the new
    // three-category toggle (2026-07-30) they share ONE checkbox and are
    // meant to hide together; what must NOT happen is a broken match (e.g. a
    // startsWith on the id, or a selector built from the raw id string)
    // catching some and missing others, or bleeding into a different
    // category (river-scamander, `kind: "river"`) that was never asked for.
    const raw = JSON.parse(readFileSync(path.resolve(process.cwd(), '../apparatus/plates/troad.json'), 'utf-8'));
    mockFetchPlate.mockResolvedValue(raw);

    const { container, getByRole } = render(PlatePanel, {
      props: { plateId: 'troad', title: 'The Troad' },
    });

    await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());

    const idaEl = container.querySelector('[data-feature-id="relief-ida"]') as SVGElement;
    const northSpursEl = container.querySelector('[data-feature-id="relief-ida-north-spurs"]') as SVGElement;
    const el800 = container.querySelector('[data-feature-id="relief-ida-800"]') as SVGElement;
    const el1200 = container.querySelector('[data-feature-id="relief-ida-1200"]') as SVGElement;
    const riverEl = container.querySelector('[data-feature-id="river-scamander"]') as SVGElement;
    expect(idaEl).toBeTruthy();
    expect(northSpursEl).toBeTruthy();
    expect(el800).toBeTruthy();
    expect(el1200).toBeTruthy();
    expect(riverEl).toBeTruthy();

    const toggle = getByRole('checkbox', { name: /show relief/i }) as HTMLInputElement;
    expect(toggle.checked).toBe(true);
    toggle.click();

    await waitFor(() => expect(idaEl.style.display).toBe('none'));
    expect(northSpursEl.style.display).toBe('none');
    expect(el800.style.display).toBe('none');
    expect(el1200.style.display).toBe('none');
    // A different category (rivers) is untouched by the relief toggle.
    expect(riverEl.style.display).not.toBe('none');
  });

  it('a layer outside the three toggle categories (region/wall) has no checkbox and is never hidden by one', async () => {
    // A synthetic fixture, not a real apparatus/plates/*.json file: the
    // citadel sheet this scenario originally exercised (troy-citadel.json)
    // is a live drawing target of a concurrent session as of this writing
    // (2026-07-30, CLAUDE.md's "two sessions, one checkout" gotcha -- its
    // layer set is being rewritten in place) and is unsafe ground for a test
    // to depend on. `region` and `wall` are neither relief, river, nor coast,
    // so neither gets a checkbox under the new three-category scheme; the
    // old debug panel's `default: "on"|"off"` field no longer drives
    // visibility at all.
    mockFetchPlate.mockResolvedValue({
      id: 'category-scope-plate',
      title: 'Category Scope Plate',
      kind: 'geographic',
      status: 'reviewed',
      bbox: [0, 0, 1, 1],
      size: [100, 80],
      layers: [
        { id: 'lower-city', kind: 'region', default: 'on', polygon: [[0.1, 0.1], [0.4, 0.1], [0.4, 0.4], [0.1, 0.4]] },
        { id: 'lower-city-ditch', kind: 'wall', default: 'on', trace: [[0.1, 0.1], [0.4, 0.4]] },
        { id: 'a-relief-layer', kind: 'relief', default: 'on', polygon: [[0.5, 0.5], [0.9, 0.5], [0.9, 0.9]] },
      ],
    });

    const { container, getByRole, queryByRole } = render(PlatePanel, {
      props: { plateId: 'category-scope-plate', title: 'Category Scope Plate' },
    });

    await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());

    const cityEl = container.querySelector('[data-layer-id="lower-city"]') as SVGElement;
    const ditchEl = container.querySelector('[data-layer-id="lower-city-ditch"]') as SVGElement;
    expect(cityEl).toBeTruthy();
    expect(ditchEl).toBeTruthy();

    // No per-layer checkbox for either -- and no "rivers" or "shoreline"
    // checkbox at all, since this plate authors neither kind.
    expect(queryByRole('checkbox', { name: /lower city/i })).toBeNull();
    expect(queryByRole('checkbox', { name: /show rivers/i })).toBeNull();
    expect(queryByRole('checkbox', { name: /show shoreline/i })).toBeNull();

    const reliefEl = container.querySelector('[data-layer-id="a-relief-layer"]') as SVGElement;
    expect(reliefEl).toBeTruthy();
    expect(reliefEl.style.display).not.toBe('none');

    const reliefToggle = getByRole('checkbox', { name: /show relief/i }) as HTMLInputElement;
    reliefToggle.click();

    await waitFor(() => expect(reliefEl.style.display).toBe('none'));
    expect(cityEl.style.display).not.toBe('none');
    expect(ditchEl.style.display).not.toBe('none');
  });

  it('focusIds (Chart Room postcard click-through, part F) frames the camera on a place, producing a non-identity transform clamped within the component\'s own CAM_MIN_K/CAM_MAX_K bounds', async () => {
    mockFetchPlate.mockResolvedValue({
      id: 'focus-plate',
      title: 'Focus Plate',
      kind: 'geographic',
      status: 'reviewed',
      bbox: [39.86, 26.12, 40.02, 26.36],
      size: [400, 300],
      layers: [],
    });

    const places = [
      { id: 'a', name: 'Place A', coords: [39.9, 26.15] as [number, number], certainty: 'certain' as const },
      { id: 'b', name: 'Place B', coords: [39.98, 26.33] as [number, number], certainty: 'certain' as const },
    ];

    const { container } = render(PlatePanel, {
      props: { plateId: 'focus-plate', places, title: 'Focus Plate', focusIds: ['a'] },
    });

    await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());
    const cameraG = container.querySelector('.pp-camera') as SVGGElement;
    expect(cameraG).toBeTruthy();
    const transform = cameraG.getAttribute('transform') ?? '';
    expect(transform).not.toBe('translate(0 0) scale(1)');
    const match = transform.match(/translate\(([-\d.]+) ([-\d.]+)\) scale\(([\d.]+)\)/);
    expect(match).not.toBeNull();
    const k = Number(match![3]);
    // clampCamera's own bounds (PlatePanel.svelte: CAM_MIN_K..CAM_MAX_K, 1..8).
    expect(k).toBeGreaterThanOrEqual(1);
    expect(k).toBeLessThanOrEqual(8);
  });

  it('an empty focusIds (the default) leaves the identity camera', async () => {
    mockFetchPlate.mockResolvedValue({
      id: 'focus-plate-2',
      title: 'Focus Plate 2',
      kind: 'geographic',
      status: 'reviewed',
      bbox: [0, 0, 1, 1],
      size: [100, 80],
      layers: [],
    });

    const places = [{ id: 'a', name: 'Place A', coords: [0.5, 0.5] as [number, number], certainty: 'certain' as const }];

    const { container } = render(PlatePanel, {
      // focusIds omitted -- exercises the `export let focusIds: string[] = []` default.
      props: { plateId: 'focus-plate-2', places, title: 'Focus Plate 2' },
    });

    await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());
    const cameraG = container.querySelector('.pp-camera') as SVGGElement;
    expect(cameraG.getAttribute('transform')).toBe('translate(0 0) scale(1)');
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
