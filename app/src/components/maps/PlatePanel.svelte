<script lang="ts">
  // Renders one illustrated "plate" (shared/lib/plate.ts's build-time SVG
  // renderer, or shared/lib/shield.ts for the one schematic exception) by id,
  // fetched at runtime through @shared/lib/data's fetchPlate (the data-root
  // override — CLAUDE.md "all data fetches go through the data.ts data-root
  // override"). Pure SVG: this file must never import Leaflet, directly or
  // transitively, so it can sit inside a tab (MapsPage.svelte's Troad/Plain/
  // Citadel/Shield tabs) without pulling the tile-map machinery along.
  //
  // Plate JSON has two shapes: a `layers` array is a plate.ts geographic/
  // schematic plate (parsePlate + renderPlate); a `bands` array is the one
  // schematic exception, shield.ts's Shield of Achilles (renderShield) --
  // see that module's own doc comment for why the shield gets a separate
  // renderer. `fetchPlate`'s declared PlateFile type assumes the `layers`
  // shape; the `bands` check below happens on the raw fetched value before
  // any PlateFile-typed field is touched, so the shield's actually-different
  // shape is never forced through the wrong type.
  //
  // A plate id with no apparatus/plates/<id>.json yet (the Troy citadel, as
  // of this writing) is NOT an error -- fetchPlate resolves to null on a 404
  // and this component shows an honest "not yet drawn" state instead of a
  // crash or an empty box.
  import { tick } from 'svelte';
  import { fetchPlate } from '@shared/lib/data';
  import { parsePlate, renderPlate, type PlatePlace, type PlateLayer } from '@shared/lib/plate';
  import { renderShield, type ShieldPlate } from '@shared/lib/shield';

  // Which apparatus/plates/<id>.json to fetch.
  export let plateId: string;
  // Gazetteer places to overlay (ignored for a schematic `bands` plate --
  // renderShield takes no places at all, see shared/lib/shield.ts). Honesty
  // resolution (which places get a pin vs land in the unlocated list) is
  // entirely renderPlate's job -- this component never decides placement.
  export let places: PlatePlace[] = [];
  // Human label used only in the "not yet drawn" message for a plate id with
  // no file -- never invented from the plate data (there isn't any yet).
  export let title = '';

  type Status = 'loading' | 'ready' | 'missing' | 'error';
  let status: Status = 'loading';
  let errorMessage = '';

  let svgMarkup = '';
  let plateTitle = '';
  let isDraft = false;
  let plateSize: [number, number] = [4, 3];
  let unlocated: PlatePlace[] = [];
  // Places with a real, defensible position that simply falls outside this
  // plate's own frame (renderPlate's `offCanvas` bucket, 2026-07-28, finding
  // 1) -- a different claim from `unlocated` ("no defensible position at
  // all") and kept as a visibly distinct list, never merged into it.
  let offCanvas: PlatePlace[] = [];
  let togglableLayers: PlateLayer[] = [];
  let layerVisible: Record<string, boolean> = {};
  // Only ever true for a schematic plate.ts plate that resolved at least one
  // place via `plateAnchors` + `positionBasis: "conjectural"` (see plate.ts's
  // resolvePlacePosition) -- the shield itself takes no places, so this stays
  // false there.
  let hasConjectural = false;

  let mapEl: HTMLDivElement | undefined;

  $: aspectRatio = `${plateSize[0]} / ${plateSize[1]}`;

  // PlateLayer carries no display label (see shared/lib/plate.ts's schema) --
  // this is a mechanical id -> plain-text fallback, not authored copy. A
  // future `label` field on the layer would let content override this
  // directly.
  function humanizeLayerId(id: string): string {
    const spaced = id.replace(/[-_]+/g, ' ').trim();
    return spaced ? spaced[0].toUpperCase() + spaced.slice(1) : id;
  }

  function applyLayerVisibility() {
    if (!mapEl) return;
    for (const layer of togglableLayers) {
      const visible = layerVisible[layer.id] !== false;
      // Finding 8 (2026-07-28): a layer id is validator-accepted apparatus
      // data, not a trusted literal -- an id like `x"]` interpolated
      // straight into a `[data-feature-id="..."]` selector breaks the
      // attribute-value quoting and throws a DOMException. Select every
      // data-feature-id element and compare the dataset value in JS
      // instead of building a selector string from the id at all.
      mapEl.querySelectorAll<SVGElement>('[data-feature-id]').forEach((el) => {
        if (el.dataset.featureId !== layer.id) return;
        el.style.display = visible ? '' : 'none';
      });
    }
  }

  function toggleLayer(id: string, on: boolean) {
    layerVisible = { ...layerVisible, [id]: on };
    applyLayerVisibility();
  }

  async function load(id: string, placesForPlate: PlatePlace[]) {
    status = 'loading';
    errorMessage = '';
    svgMarkup = '';
    unlocated = [];
    offCanvas = [];
    togglableLayers = [];
    layerVisible = {};
    hasConjectural = false;

    try {
      const raw = await fetchPlate(id);
      if (!raw) {
        status = 'missing';
        return;
      }

      // Route on the raw shape (see module doc comment) before touching any
      // PlateFile-typed field.
      const rawRecord = raw as unknown as Record<string, unknown>;
      if (Array.isArray(rawRecord.bands)) {
        const shield = raw as unknown as ShieldPlate;
        const result = renderShield(shield);
        svgMarkup = result.svg;
        plateTitle = shield.title;
        isDraft = shield.status === 'draft';
        plateSize = shield.size;
      } else {
        const plate = parsePlate(raw);
        const result = renderPlate(plate, placesForPlate);
        svgMarkup = result.svg;
        plateTitle = plate.title;
        isDraft = plate.status === 'draft';
        plateSize = plate.size;
        unlocated = result.unlocated;
        offCanvas = result.offCanvas;
        togglableLayers = plate.layers.filter((l) => l.default === 'on' || l.default === 'off');
        layerVisible = Object.fromEntries(togglableLayers.map((l) => [l.id, l.default === 'on']));
        const locatedCount = placesForPlate.length - result.unlocated.length - result.offCanvas.length;
        hasConjectural = plate.kind === 'schematic' && locatedCount > 0;
      }

      status = 'ready';
      await tick();
      applyLayerVisibility();
    } catch (e) {
      status = 'error';
      errorMessage = e instanceof Error ? e.message : String(e);
    }
  }

  // Re-fetches whenever the id changes (a mounted instance switching plates)
  // as well as on first mount.
  $: load(plateId, places);
</script>

<div class="pp-root">
  {#if status === 'ready' && isDraft}
    <span class="draft-badge" title="AI-drafted apparatus, pending review">Draft</span>
  {/if}

  {#if status === 'loading'}
    <p class="pp-status">Loading the plate…</p>
  {:else if status === 'missing'}
    <p class="pp-status pp-missing">{title ? `${title} hasn't` : "This plate hasn't"} been drawn yet.</p>
  {:else if status === 'error'}
    <p class="pp-status pp-error">Couldn't load this plate{errorMessage ? `: ${errorMessage}` : '.'}</p>
  {:else}
    <div class="pp-body">
      <div class="pp-map-col">
        <div class="pp-map" style="aspect-ratio: {aspectRatio};" bind:this={mapEl}>
          <!-- eslint-disable-next-line svelte/no-at-html-tags -->
          {@html svgMarkup}
        </div>

        {#if togglableLayers.length}
          <div class="pp-toggles" role="group" aria-label="Plate layers">
            {#each togglableLayers as layer (layer.id)}
              <label class="pp-toggle">
                <input
                  type="checkbox"
                  checked={layerVisible[layer.id] !== false}
                  on:change={(e) => toggleLayer(layer.id, (e.currentTarget as HTMLInputElement).checked)}
                />
                Show {humanizeLayerId(layer.id).toLowerCase()}
              </label>
            {/each}
          </div>
        {/if}

        <div class="pp-legend" aria-label="Certainty legend">
          <span class="pp-legend-item"><span class="pp-mark certain" aria-hidden="true"></span>certain</span>
          <span class="pp-legend-item"><span class="pp-mark traditional" aria-hidden="true"></span>traditional</span>
          <span class="pp-legend-item"><span class="pp-mark speculative" aria-hidden="true"></span>speculative</span>
          <span class="pp-legend-item"><span class="pp-mark mythical" aria-hidden="true"></span>mythical</span>
          {#if hasConjectural}
            <span class="pp-legend-item"><span class="pp-mark conjectural" aria-hidden="true"></span>conjectural position</span>
          {/if}
        </div>
      </div>

      {#if unlocated.length || offCanvas.length}
        <div class="pp-honesty-lists">
          {#if offCanvas.length}
            <div class="pp-unlocated pp-offcanvas">
              <h3>Off this sheet ({offCanvas.length})</h3>
              <p class="pp-unlocated-caption">
                A known place — just outside this sheet's frame. See another map for it.
              </p>
              <ul>
                {#each offCanvas as p (p.id)}
                  <li>{p.name}{#if p.certainty} <span class="pp-tier-word">({p.certainty})</span>{/if}</li>
                {/each}
              </ul>
            </div>
          {/if}

          {#if unlocated.length}
            <div class="pp-unlocated">
              <h3>Named, not drawn ({unlocated.length})</h3>
              <p class="pp-unlocated-caption">
                Named in the poem, but with no defensible position for this plate to draw.
              </p>
              <ul>
                {#each unlocated as p (p.id)}
                  <li>{p.name}{#if p.certainty} <span class="pp-tier-word">({p.certainty})</span>{/if}</li>
                {/each}
              </ul>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .pp-root { display: flex; flex-direction: column; gap: 0.6rem; }
  .pp-root > .draft-badge { align-self: flex-start; }

  .pp-status { margin: 0; font-family: var(--font-ui); font-size: 0.85rem; color: var(--text-mid); }
  .pp-status.pp-missing { font-style: italic; }
  .pp-status.pp-error { color: var(--error); }

  .pp-body { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(200px, 1fr); gap: 1rem; align-items: start; }
  @media (max-width: 860px) { .pp-body { grid-template-columns: 1fr; } }

  .pp-map-col { display: flex; flex-direction: column; gap: 0.6rem; min-width: 0; }
  .pp-map {
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 7px;
    background: var(--page-bg);
  }
  .pp-map :global(svg) { display: block; width: 100%; height: 100%; }

  .pp-toggles { display: flex; flex-wrap: wrap; gap: 0.8rem; font-family: var(--font-ui); font-size: 0.8rem; color: var(--text); }
  .pp-toggle { display: flex; align-items: center; gap: 0.4rem; cursor: pointer; }
  .pp-toggle input { cursor: pointer; }

  .pp-legend { display: flex; flex-wrap: wrap; gap: 0.9rem; font-family: var(--font-ui); font-size: 0.78rem; color: var(--text-mid); }
  .pp-legend-item { display: flex; align-items: center; gap: 0.35rem; }
  .pp-mark { width: 10px; height: 10px; flex: none; display: inline-block; }
  .pp-mark.certain { border-radius: 50%; background: var(--accent); }
  .pp-mark.traditional { border-radius: 50%; border: 1.4px solid var(--accent); background: transparent; }
  .pp-mark.speculative { border-radius: 50%; border: 1.4px dashed var(--text-mid); background: transparent; }
  .pp-mark.mythical { border: 1.4px solid var(--text-mid); transform: rotate(45deg); width: 8px; height: 8px; }
  .pp-mark.conjectural { border-radius: 50%; border: 1.4px dotted var(--accent); background: transparent; }

  .pp-honesty-lists { display: flex; flex-direction: column; gap: 0.9rem; }

  .pp-unlocated { font-family: var(--font-ui); font-size: 0.82rem; color: var(--text-mid); }
  .pp-unlocated h3 { margin: 0 0 0.2rem; font-size: 0.86rem; font-family: var(--font-display); font-weight: 600; color: var(--text); }
  .pp-unlocated-caption { margin: 0 0 0.5rem; font-style: italic; }
  .pp-unlocated ul { margin: 0; padding-left: 1.2rem; }
  .pp-unlocated li { margin-bottom: 0.15rem; }
  .pp-tier-word { color: var(--text-light); }
</style>
