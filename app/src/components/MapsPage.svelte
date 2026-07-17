<script lang="ts">
  // Top-level /maps/ island: four Landmark-style maps (Ships/Catalogue
  // explorer, Troad, Wanderings, Greece) behind a tablist, so Leaflet loads
  // exactly once per page visit and the four views share one legend/draft
  // badge/source note. Mounted client:only="svelte" by app/src/pages/maps/
  // index.astro — Leaflet needs `window`, so this island never runs during
  // SSR (see LandmarkMap.svelte).
  import {
    placesForMap,
    splitByCoords,
    shipCircleRadius,
    principalPlace,
    placesById as buildPlacesById,
    wanderingsRoute,
    type Place,
    type Contingent,
    type CharacterRef,
    type CatalogueSort,
  } from '@shared/lib/maps';
  import LandmarkMap from './maps/LandmarkMap.svelte';
  import ContingentPanel from './maps/ContingentPanel.svelte';

  export let base: string;
  export let places: Place[];
  export let achaean: Contingent[];
  export let trojan: Contingent[];
  export let characters: CharacterRef[];
  export let placesDraft = false;
  export let catalogueDraft = false;

  const pById = buildPlacesById(places);
  const charsById = new Map(characters.map((c) => [c.id, c]));

  const TABS = [
    { id: 'ships', label: 'Ships (Catalogue)' },
    { id: 'troad', label: 'Troad' },
    { id: 'wanderings', label: 'Wanderings' },
    { id: 'greece', label: 'Greece' },
  ] as const;
  type TabId = (typeof TABS)[number]['id'];
  let activeTab: TabId = 'ships';

  const SHIP_SUBTABS = [
    { id: 'achaean', label: 'Achaeans' },
    { id: 'trojan', label: 'Trojans & allies' },
  ] as const;
  type ShipSubtab = (typeof SHIP_SUBTABS)[number]['id'];
  let shipSubtab: ShipSubtab = 'achaean';

  let sort: CatalogueSort = 'catalogue';
  let selectedAchaean: string | null = null;
  let selectedTrojan: string | null = null;

  function onTabKeydown(e: KeyboardEvent, order: readonly string[], get: () => string, set: (v: any) => void) {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    e.preventDefault();
    const i = order.indexOf(get());
    const next = e.key === 'ArrowRight' ? order[(i + 1) % order.length] : order[(i - 1 + order.length) % order.length];
    set(next);
    (e.currentTarget as HTMLElement)?.querySelector<HTMLElement>(`[data-tabid="${next}"]`)?.focus();
  }

  const maxAchaeanShips = Math.max(...achaean.map((c) => c.ships ?? 0), 1);

  function contingentItems(list: Contingent[], withShips: boolean) {
    return list
      .map((c) => {
        const place = principalPlace(c, pById);
        if (!place) return null;
        const radius = withShips && c.ships != null ? shipCircleRadius(c.ships, maxAchaeanShips) : undefined;
        const extra = c.ships != null
          ? [{ label: 'Ships', value: String(c.ships) }]
          : [{ label: 'Ships', value: 'none counted' }];
        return { id: c.id, place, radius, extra };
      })
      .filter((x): x is { id: string; place: Place; radius: number | undefined; extra: { label: string; value: string }[] } => x !== null);
  }
  $: achaeanItems = contingentItems(achaean, true);
  $: trojanItems = contingentItems(trojan, false);

  // Places without a fixed coordinate (any of the 274) — never force-pinned;
  // listed per map instead (CLAUDE.md apparatus honesty).
  function unlocatedFor(tag: string) {
    return splitByCoords(placesForMap(places, tag)).unlocated;
  }
  const troadPlaces = splitByCoords(placesForMap(places, 'troad'));
  const wanderingsPlaces = splitByCoords(placesForMap(places, 'wanderings'));
  const greecePlaces = splitByCoords(placesForMap(places, 'greece'));
  const wanderingsRouteStations = wanderingsRoute(places);

  // Ships-map "not locatable" is every place referenced by ANY contingent's
  // toponym list that itself has no coords (not just the 29+16 principal
  // pins) — the full honesty accounting for the Catalogue's ~230 named towns.
  const shipsUnlocated = unlocatedFor('ships');

  const isDraft = placesDraft || catalogueDraft;
</script>

<div class="mp-root">
  {#if isDraft}
    <span class="draft-badge" title="AI-drafted apparatus, pending review">Draft</span>
  {/if}

  <p class="mp-source-note">
    Identifications follow the recorded traditions (Strabo, Barrington Atlas,
    Simpson &amp; Lazenby's Catalogue survey); certainty is marked per pin, not
    asserted for the map as a whole.
  </p>

  <div class="mp-legend" aria-label="Certainty legend">
    <span class="mp-legend-item"><span class="mp-mark certain" aria-hidden="true"></span>certain</span>
    <span class="mp-legend-item"><span class="mp-mark traditional" aria-hidden="true"></span>traditional</span>
    <span class="mp-legend-item"><span class="mp-mark speculative" aria-hidden="true"></span>speculative</span>
    <span class="mp-legend-item"><span class="mp-mark mythical" aria-hidden="true"></span>mythical</span>
  </div>

  <div
    class="mp-tabs"
    role="tablist"
    aria-label="Maps"
    on:keydown={(e) => onTabKeydown(e, TABS.map((t) => t.id), () => activeTab, (v) => (activeTab = v))}
  >
    {#each TABS as t}
      <button
        type="button"
        role="tab"
        data-tabid={t.id}
        id="mp-tab-{t.id}"
        aria-selected={activeTab === t.id}
        aria-controls="mp-panel-{t.id}"
        tabindex={activeTab === t.id ? 0 : -1}
        class="mp-tab"
        on:click={() => (activeTab = t.id)}
      >{t.label}</button>
    {/each}
  </div>

  {#if activeTab === 'ships'}
    <div id="mp-panel-ships" role="tabpanel" aria-labelledby="mp-tab-ships" tabindex="0" class="mp-panel">
      <div
        class="mp-subtabs"
        role="tablist"
        aria-label="Catalogue side"
        on:keydown={(e) => onTabKeydown(e, SHIP_SUBTABS.map((t) => t.id), () => shipSubtab, (v) => (shipSubtab = v))}
      >
        {#each SHIP_SUBTABS as t}
          <button
            type="button"
            role="tab"
            data-tabid={t.id}
            id="mp-subtab-{t.id}"
            aria-selected={shipSubtab === t.id}
            aria-controls="mp-subpanel-{t.id}"
            tabindex={shipSubtab === t.id ? 0 : -1}
            class="mp-subtab"
            on:click={() => (shipSubtab = t.id)}
          >{t.label}</button>
        {/each}
      </div>

      {#if shipSubtab === 'achaean'}
        <div id="mp-subpanel-achaean" role="tabpanel" aria-labelledby="mp-subtab-achaean" tabindex="0" class="mp-explorer">
          <LandmarkMap
            {base}
            ariaLabel="Map of the Achaean Catalogue of Ships: one circle per contingent, sized by ship count"
            items={achaeanItems}
            selectedId={selectedAchaean}
            onSelect={(id) => (selectedAchaean = id)}
          />
          <ContingentPanel
            {base}
            contingents={achaean}
            placesById={pById}
            charactersById={charsById}
            selectedId={selectedAchaean}
            {sort}
            showShips={true}
            readerWork="iliad"
            readerBook={2}
            onSelect={(id) => (selectedAchaean = id)}
            onSortChange={(m) => (sort = m)}
          />
        </div>
      {:else}
        <div id="mp-subpanel-trojan" role="tabpanel" aria-labelledby="mp-subtab-trojan" tabindex="0" class="mp-explorer">
          <LandmarkMap
            {base}
            ariaLabel="Map of the Trojan Catalogue: regions of Troy's allies (Homer gives no ship count for them)"
            items={trojanItems}
            selectedId={selectedTrojan}
            onSelect={(id) => (selectedTrojan = id)}
          />
          <ContingentPanel
            {base}
            contingents={trojan}
            placesById={pById}
            charactersById={charsById}
            selectedId={selectedTrojan}
            {sort}
            showShips={false}
            readerWork="iliad"
            readerBook={2}
            onSelect={(id) => (selectedTrojan = id)}
            onSortChange={(m) => (sort = m)}
          />
        </div>
      {/if}

      <details class="mp-unlocated">
        <summary>Not locatable ({shipsUnlocated.length} named places with no fixed site)</summary>
        <ul>
          {#each shipsUnlocated as p}
            <li><span lang="grc">{p.greek}</span> {p.name} <span class="mp-tier-word">({p.certainty})</span></li>
          {/each}
        </ul>
      </details>
    </div>
  {:else if activeTab === 'troad'}
    <div id="mp-panel-troad" role="tabpanel" aria-labelledby="mp-tab-troad" tabindex="0" class="mp-panel">
      <LandmarkMap
        {base}
        ariaLabel="Map of the Troad: places near Troy"
        items={troadPlaces.located.map((p) => ({ id: p.id, place: p }))}
      />
      <details class="mp-unlocated" open={troadPlaces.unlocated.length > 0}>
        <summary>Not locatable ({troadPlaces.unlocated.length})</summary>
        <ul>
          {#each troadPlaces.unlocated as p}
            <li><span lang="grc">{p.greek}</span> {p.name} <span class="mp-tier-word">({p.certainty})</span></li>
          {/each}
        </ul>
      </details>
    </div>
  {:else if activeTab === 'wanderings'}
    <div id="mp-panel-wanderings" role="tabpanel" aria-labelledby="mp-tab-wanderings" tabindex="0" class="mp-panel">
      <LandmarkMap
        {base}
        ariaLabel="Map of Odysseus's wanderings: stations of the Apologoi (Od. 9-12) connected by a dashed route, plus other travel/homecoming places named in the poem"
        items={wanderingsPlaces.located.map((p) => ({ id: p.id, place: p }))}
        polyline={wanderingsRouteStations}
      />
      <p class="mp-route-note">
        The dashed line traces Odysseus's own sea voyage as he narrates it
        (Od. 9&ndash;12, Ismarus to Thrinacia); the other pins here are places
        named elsewhere in the poem's travel geography, not stops on that route.
      </p>
      <details class="mp-unlocated" open={wanderingsPlaces.unlocated.length > 0}>
        <summary>Not locatable ({wanderingsPlaces.unlocated.length})</summary>
        <ul>
          {#each wanderingsPlaces.unlocated as p}
            <li><span lang="grc">{p.greek}</span> {p.name} <span class="mp-tier-word">({p.certainty})</span></li>
          {/each}
        </ul>
      </details>
    </div>
  {:else}
    <div id="mp-panel-greece" role="tabpanel" aria-labelledby="mp-tab-greece" tabindex="0" class="mp-panel">
      <LandmarkMap
        {base}
        ariaLabel="Map of Greece: homes and homecomings named in the poems"
        items={greecePlaces.located.map((p) => ({ id: p.id, place: p }))}
      />
      <details class="mp-unlocated" open={greecePlaces.unlocated.length > 0}>
        <summary>Not locatable ({greecePlaces.unlocated.length})</summary>
        <ul>
          {#each greecePlaces.unlocated as p}
            <li><span lang="grc">{p.greek}</span> {p.name} <span class="mp-tier-word">({p.certainty})</span></li>
          {/each}
        </ul>
      </details>
    </div>
  {/if}
</div>

<style>
  .mp-root { display: flex; flex-direction: column; gap: 0.9rem; }

  .mp-source-note { margin: 0; font-size: 0.82rem; color: var(--text-mid); font-style: italic; max-width: 62ch; }

  .mp-legend { display: flex; flex-wrap: wrap; gap: 0.9rem; font-family: var(--font-ui); font-size: 0.78rem; color: var(--text-mid); }
  .mp-legend-item { display: flex; align-items: center; gap: 0.35rem; }
  .mp-mark { width: 10px; height: 10px; flex: none; display: inline-block; }
  .mp-mark.certain { border-radius: 50%; background: var(--accent); }
  .mp-mark.traditional { border-radius: 50%; border: 1.4px solid var(--accent); background: transparent; }
  .mp-mark.speculative { border-radius: 50%; border: 1.4px dashed var(--text-mid); background: transparent; }
  .mp-mark.mythical { border: 1.4px solid var(--text-mid); transform: rotate(45deg); width: 8px; height: 8px; }

  .mp-tabs, .mp-subtabs { display: flex; gap: 0.3rem; border-bottom: 1px solid var(--border); flex-wrap: wrap; }
  .mp-tab, .mp-subtab {
    padding: 0.45rem 0.9rem;
    font-family: var(--font-ui);
    font-size: 0.86rem;
    font-weight: 600;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--text-mid);
    cursor: pointer;
  }
  .mp-tab[aria-selected="true"], .mp-subtab[aria-selected="true"] { color: var(--accent); border-bottom-color: var(--accent); }
  .mp-tab:hover, .mp-subtab:hover { color: var(--accent); }
  .mp-tab:focus-visible, .mp-subtab:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

  .mp-panel { display: flex; flex-direction: column; gap: 0.8rem; }
  .mp-explorer { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(260px, 1fr); gap: 1rem; align-items: start; }
  @media (max-width: 860px) { .mp-explorer { grid-template-columns: 1fr; } }

  .mp-route-note { margin: 0; font-size: 0.8rem; color: var(--text-mid); max-width: 68ch; }

  .mp-unlocated { font-family: var(--font-ui); font-size: 0.82rem; color: var(--text-mid); }
  .mp-unlocated summary { cursor: pointer; font-weight: 600; color: var(--text); }
  .mp-unlocated ul { margin: 0.5rem 0 0; padding-left: 1.2rem; columns: 2; column-gap: 1.5rem; }
  @media (max-width: 640px) { .mp-unlocated ul { columns: 1; } }
  .mp-unlocated li { margin-bottom: 0.15rem; break-inside: avoid; }
  .mp-tier-word { color: var(--text-light); }
</style>
