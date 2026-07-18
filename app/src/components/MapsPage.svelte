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
    wanderingsStory,
    splitStoryByCoords,
    captionSummary,
    resolveLegs,
    resolveJourneyLegs,
    journeysPlaceSplit,
    wanderingsReturnTail,
    type Place,
    type Contingent,
    type CharacterRef,
    type CatalogueSort,
    type Journey,
  } from '@shared/lib/maps';
  import { workPath } from '@shared/lib/works';
  import { formatLocValue } from '@shared/lib/citation';
  import LandmarkMap from './maps/LandmarkMap.svelte';
  import ContingentPanel from './maps/ContingentPanel.svelte';
  // Vite/Astro JSON import (tsconfig resolveJsonModule: true) -- the same
  // "load the raw apparatus file at build time" posture as
  // places.json/catalogue.json/characters.json in
  // app/src/pages/maps/index.astro, just as a static import inside this
  // client:only island rather than an Astro-frontmatter prop, so the
  // journeys.json plumbing stays entirely within this file.
  import journeysFile from '../../../apparatus/journeys.json';

  export let base: string;
  export let places: Place[];
  export let achaean: Contingent[];
  export let trojan: Contingent[];
  export let characters: CharacterRef[];
  export let placesDraft = false;
  export let catalogueDraft = false;

  const journeys = (journeysFile as { status: string; journeys: Journey[] }).journeys;
  const journeysDraft = (journeysFile as { status: string }).status === 'draft';

  const pById = buildPlacesById(places);
  const charsById = new Map(characters.map((c) => [c.id, c]));

  const TABS = [
    { id: 'ships', label: 'Ships (Catalogue)' },
    { id: 'troad', label: 'Troad' },
    { id: 'wanderings', label: 'Wanderings' },
    { id: 'greece', label: 'Greece' },
    { id: 'journeys', label: 'Journeys' },
  ] as const;
  type TabId = (typeof TABS)[number]['id'];

  // Restore the active tab from `?map=<id>`, so a shared/reloaded link (e.g.
  // /maps/?map=wanderings) lands on the right panel instead of always the
  // Ships default. An invalid/unknown value falls back to the default tab
  // silently (no error UI — this is a soft deep-link, not a form).
  function readMapParam(): TabId {
    const raw = new URLSearchParams(window.location.search).get('map');
    return TABS.some((t) => t.id === raw) ? (raw as TabId) : 'ships';
  }
  let activeTab: TabId = readMapParam();

  // Persist the active tab to `?map=` on every switch — same replaceState
  // idiom as setStoryMode below — so the URL a reader copies/reloads always
  // reflects what's on screen.
  function setActiveTab(id: TabId) {
    activeTab = id;
    const url = new URL(window.location.href);
    url.searchParams.set('map', id);
    window.history.replaceState(window.history.state, '', url);
  }

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

  // Story mode: the ~17-station Troy-to-Ithaca telling order (see
  // shared/lib/maps wanderingsStory doc comment). `located` gets numbered
  // map badges + caption cards (LandmarkMap); `unlocated` is the "beyond the
  // map's edge" honesty strip below the map.
  const wanderingsStoryStations = wanderingsStory(places);
  const wanderingsStorySplit = splitStoryByCoords(wanderingsStoryStations);

  // The Wanderings route's extension past Thrinacia (John, 2026-07-17: the
  // drawn route must end at Ithaca) -- see shared/lib/maps
  // wanderingsReturnTail doc. Applies to BOTH Map and Story mode (the same
  // `wanderingsTail` prop below), since the badges for Ogygia/Scheria/Ithaca
  // already exist in Story mode's numbered stations; only the route LINE
  // reaching them was missing.
  const wanderingsTailLegs = resolveLegs(wanderingsReturnTail(journeys), pById);

  // ── Journeys tab: the four nostoi (Menelaus, Nestor, Telemachus, plus
  // Odysseus's own return again in its own color, for cross-reference) --
  // placement call (John's brief left this to the implementer): a dedicated
  // tab rather than toggle layers folded into Wanderings, so Wanderings /
  // Story mode stays Odysseus-focused and uncluttered, while this tab can be
  // as busy as four overlapping routes actually are. Each route is drawn as
  // several independent gently-curved LEG polylines (LandmarkMap
  // drawJourneyLegs), not one continuous path per journey, because several
  // legs fan out from a shared hub (Menelaus's five departures from Egypt)
  // rather than forming a simple chain.
  const JOURNEY_STYLE: Record<string, { colorClass: string; dashArray?: string }> = {
    'odysseus-return': { colorClass: 'lm-journey-odysseus' },
    'menelaus-nostos': { colorClass: 'lm-journey-menelaus', dashArray: '11,7' },
    'nestor-nostos': { colorClass: 'lm-journey-nestor', dashArray: '1,5' },
    'telemachus-journey': { colorClass: 'lm-journey-telemachus', dashArray: '10,4,2,4' },
  };
  const JOURNEY_LABELS: Record<string, string> = {
    odysseus: 'Odysseus',
    menelaus: 'Menelaus',
    nestor: 'Nestor',
    telemachus: 'Telemachus',
  };

  const allJourneyRoutes = journeys.map((j) => {
    const style = JOURNEY_STYLE[j.id] ?? { colorClass: 'lm-journey-odysseus' };
    return {
      id: j.id,
      traveler: j.traveler,
      colorClass: style.colorClass,
      dashArray: style.dashArray,
      arrivalLegIndex: j.id === 'odysseus-return' ? j.legs.length - 1 : undefined,
      legs: resolveJourneyLegs(j, pById),
    };
  });

  let journeysVisible: Record<string, boolean> = Object.fromEntries(journeys.map((j) => [j.id, true]));
  function toggleJourney(id: string, on: boolean) {
    journeysVisible = { ...journeysVisible, [id]: on };
  }
  $: visibleJourneyRoutes = allJourneyRoutes.filter((r) => journeysVisible[r.id]);

  const journeysSplit = journeysPlaceSplit(journeys, pById);
  const journeysItems = journeysSplit.located.map((p) => ({ id: p.id, place: p }));

  // "Story" / "Map" toggle on the Wanderings panel only. Persists via
  // `?story=1` so a shared/reloaded link keeps the mode (client:only island —
  // this always runs in the browser, never during SSR). Presence of the
  // param also opens the Wanderings tab directly, since that's the only
  // place the toggle has any effect.
  function readStoryParam(): boolean {
    return new URLSearchParams(window.location.search).get('story') === '1';
  }
  let storyMode = readStoryParam();
  if (storyMode) activeTab = 'wanderings';

  function setStoryMode(v: boolean) {
    storyMode = v;
    const url = new URL(window.location.href);
    if (v) url.searchParams.set('story', '1');
    else url.searchParams.delete('story');
    window.history.replaceState(window.history.state, '', url);
  }

  function mentionHref(work: string, book: number, line: number): string {
    return `${base}${workPath(work, book)}?loc=${formatLocValue(work, String(book), line)}`;
  }

  // Ships-map "not locatable" is every place referenced by ANY contingent's
  // toponym list that itself has no coords (not just the 29+16 principal
  // pins) — the full honesty accounting for the Catalogue's ~230 named towns.
  const shipsUnlocated = unlocatedFor('ships');

  const isDraft = placesDraft || catalogueDraft || journeysDraft;
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
    on:keydown={(e) => onTabKeydown(e, TABS.map((t) => t.id), () => activeTab, setActiveTab)}
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
        on:click={() => setActiveTab(t.id)}
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
      <div class="mp-story-toggle" role="group" aria-label="Wanderings view">
        <button
          type="button"
          class="mp-story-btn"
          aria-pressed={!storyMode}
          on:click={() => setStoryMode(false)}
        >Map</button>
        <button
          type="button"
          class="mp-story-btn"
          aria-pressed={storyMode}
          on:click={() => setStoryMode(true)}
        >Story</button>
      </div>

      <LandmarkMap
        {base}
        ariaLabel={storyMode
          ? "Map of Odysseus's wanderings in Story mode: the 17 numbered stations of his voyage, Troy to Ithaca, in telling order, with the sea-voyage route (Ismarus to Thrinacia) drawn as the hero route"
          : "Map of Odysseus's wanderings: stations of the Apologoi (Od. 9-12) connected by a dashed route, plus other travel/homecoming places named in the poem"}
        items={wanderingsPlaces.located.map((p) => ({ id: p.id, place: p }))}
        polyline={wanderingsRouteStations}
        wanderingsTail={wanderingsTailLegs}
        {storyMode}
        storyStations={wanderingsStoryStations}
      />

      {#if storyMode}
        <p class="mp-route-note">
          Numbered stations follow Odysseus's own telling, Troy to Ithaca; the
          heavier route line is his sea voyage proper (Od. 9&ndash;12, Ismarus
          to Thrinacia), continuing on to Ithaca &mdash; broken through the
          Ogygia gap, where Homer's own geography gives no fixed position,
          solid again from Scheria home.
        </p>
        <p class="mp-route-note mp-story-attribution">
          Route follows the traditional identifications recorded here;
          certainty marked per station.
        </p>

        <ol class="mp-story-mobile-list" aria-label="Wanderings stations">
          {#each wanderingsStorySplit.located as s}
            <li>
              <a href={s.place.mentions[0] ? mentionHref(s.place.mentions[0].work, s.place.mentions[0].book, s.place.mentions[0].lines[0]) : `#`}>
                <span class="mp-story-num" aria-hidden="true">{s.number}</span>
                <span class="mp-story-item-body">
                  <span class="mp-story-item-name"><span lang="grc">{s.place.greek}</span> {s.place.name}</span>
                  <span class="mp-story-item-note">{captionSummary(s.place.note)}</span>
                </span>
                <span class="mp-tier-word">({s.place.certainty})</span>
              </a>
            </li>
          {/each}
        </ol>

        <div class="mp-beyond-edge">
          <h2>Beyond the map's edge</h2>
          <p class="mp-beyond-edge-note">
            Stations Odysseus's own telling places in the voyage, but no
            tradition puts on a real map.
          </p>
          <ol>
            {#each wanderingsStorySplit.unlocated as s}
              <li>
                <a href={s.place.mentions[0] ? mentionHref(s.place.mentions[0].work, s.place.mentions[0].book, s.place.mentions[0].lines[0]) : `#`}>
                  <span class="mp-story-num" aria-hidden="true">{s.number}</span>
                  <span class="mp-beyond-edge-item">
                    <span lang="grc">{s.place.greek}</span> {s.place.name} &mdash; {captionSummary(s.place.note, 90)}
                  </span>
                </a>
              </li>
            {/each}
          </ol>
        </div>
      {:else}
        <p class="mp-route-note">
          The dashed line traces Odysseus's own sea voyage as he narrates it
          (Od. 9&ndash;12, Ismarus to Thrinacia), continuing on to Ithaca
          &mdash; broken through the Ogygia gap (no fixed position in this
          gazetteer), solid again from Scheria home; the other pins here are
          places named elsewhere in the poem's travel geography, not stops on
          that route.
        </p>
      {/if}

      <details class="mp-unlocated" open={wanderingsPlaces.unlocated.length > 0}>
        <summary>Not locatable ({wanderingsPlaces.unlocated.length})</summary>
        <ul>
          {#each wanderingsPlaces.unlocated as p}
            <li><span lang="grc">{p.greek}</span> {p.name} <span class="mp-tier-word">({p.certainty})</span></li>
          {/each}
        </ul>
      </details>
    </div>
  {:else if activeTab === 'greece'}
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
  {:else}
    <div id="mp-panel-journeys" role="tabpanel" aria-labelledby="mp-tab-journeys" tabindex="0" class="mp-panel">
      <p class="mp-route-note">
        The four homecomings (nostoi) Homer narrates. Odysseus's own route
        continues here from Thrinacia to Ithaca (see the Wanderings tab for
        his Apologoi voyage in full); Menelaus's, Nestor's, and Telemachus's
        are drawn for the first time, each its own color and dash pattern.
        Toggle a route off below to compare the others; a faded, finely
        dotted gap marks a leg whose far end has no fixed position in this
        gazetteer &mdash; a confident line was never drawn to a guessed spot
        &mdash; tap or click its small ringed marker for the note.
      </p>

      <div class="mp-journey-legend" role="group" aria-label="Journeys shown">
        {#each allJourneyRoutes as r (r.id)}
          <label class="mp-journey-legend-item">
            <input
              type="checkbox"
              checked={journeysVisible[r.id]}
              on:change={(e) => toggleJourney(r.id, (e.currentTarget as HTMLInputElement).checked)}
            />
            <svg class="mp-journey-swatch" viewBox="0 0 32 6" aria-hidden="true" focusable="false">
              <line
                x1="1" y1="3" x2="31" y2="3"
                class={r.colorClass}
                stroke-dasharray={r.dashArray ?? ''}
                stroke-width="3"
                stroke-linecap="round"
              />
            </svg>
            <span>{JOURNEY_LABELS[r.traveler] ?? r.traveler}</span>
          </label>
        {/each}
      </div>

      <LandmarkMap
        {base}
        ariaLabel="Map of the four nostoi: the homecomings of Odysseus, Menelaus, Nestor, and Telemachus, each a distinct colored and patterned route"
        items={journeysItems}
        journeyRoutes={visibleJourneyRoutes}
      />

      <details class="mp-unlocated" open={journeysSplit.unlocated.length > 0}>
        <summary>Not locatable ({journeysSplit.unlocated.length})</summary>
        <ul>
          {#each journeysSplit.unlocated as p}
            <li><span lang="grc">{p.greek}</span> {p.name} <span class="mp-tier-word">({p.certainty})</span></li>
          {/each}
        </ul>
      </details>
    </div>
  {/if}
</div>

<style>
  .mp-root {
    display: flex;
    flex-direction: column;
    gap: 0.9rem;
    /* Journey route colors (John, 2026-07-17: "distinct route color derived
       from the site palette... no arbitrary hex"). Odysseus keeps the
       site's own primary wayfinding accent unchanged (journeys.json
       color_role: "primary"); the other three are CSS relative-color hue
       rotations of that SAME token -- a formula, not a literal color -- by a
       fixed, evenly-spread amount chosen to land clear of --draft's reserved
       slate-blue (~206deg hue, wired to the draft badge ONLY per this
       project's one-red-flag-only rule) and --error's reserved red
       (~0-4deg). Defined here (not in LandmarkMap.svelte) so both the map's
       Leaflet paths (a descendant of .mp-root) and this file's own legend
       swatches read the same custom properties via ordinary CSS
       inheritance -- one source of truth for the palette-derivation
       formula. Dash pattern (set in JOURNEY_STYLE above) is the second,
       color-vision-independent channel distinguishing the four routes. */
    --journey-odysseus: var(--accent);
    --journey-menelaus: hsl(from var(--accent) calc(h + 80) s l);
    --journey-nestor: hsl(from var(--accent) calc(h + 170) s l);
    --journey-telemachus: hsl(from var(--accent) calc(h - 60) s l);
  }
  /* .draft-badge (global.css) is display:inline-block, sized to its text —
     but as a direct flex item of .mp-root's column flex it stretched to the
     full row width by the default align-items:stretch, painting as an empty
     bordered bar instead of the compact chip every other surface uses
     (Wave A #9, 2026-07-17). Opt this one item out of stretch; markup and
     the shared .draft-badge rule are unchanged. */
  .mp-root > .draft-badge { align-self: flex-start; }

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

  .mp-story-toggle { display: inline-flex; gap: 0.3rem; border: 1px solid var(--border); border-radius: 999px; padding: 0.2rem; width: fit-content; }
  .mp-story-btn {
    padding: 0.3rem 0.85rem;
    font-family: var(--font-ui);
    font-size: 0.78rem;
    font-weight: 600;
    background: none;
    color: var(--text-mid);
    border: none;
    border-radius: 999px;
    cursor: pointer;
  }
  .mp-story-btn[aria-pressed="true"] { background: var(--accent); color: var(--on-accent); }
  .mp-story-btn:hover:not([aria-pressed="true"]) { color: var(--accent); }
  .mp-story-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

  /* Mobile fallback for story-mode captions (LandmarkMap hides its
     always-visible caption cards below 480px — see that component's own
     media query) — a fully keyboard/tap-operable list of the same 15
     coord-bearing stations, in telling order. */
  .mp-story-mobile-list { display: none; list-style: none; margin: 0; padding: 0; font-family: var(--font-ui); }
  @media (max-width: 480px) {
    .mp-story-mobile-list { display: flex; flex-direction: column; gap: 0.4rem; }
  }
  .mp-story-mobile-list li { border: 1px solid var(--border); border-radius: 6px; }
  .mp-story-mobile-list a {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.6rem;
    text-decoration: none;
    color: var(--text);
  }
  .mp-story-mobile-list a:hover,
  .mp-story-mobile-list a:focus-visible { background: var(--greek-hover); }
  .mp-story-mobile-list a:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
  .mp-story-item-body { flex: 1; min-width: 0; }
  .mp-story-item-name { display: block; font-weight: 700; font-size: 0.85rem; }
  .mp-story-item-note { display: block; font-size: 0.76rem; color: var(--text-mid); }

  .mp-story-num {
    flex: none;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--accent);
    color: var(--on-accent);
    font-size: 0.68rem;
    font-weight: 700;
  }

  .mp-beyond-edge { border-top: 1px dashed var(--border); padding-top: 0.7rem; font-family: var(--font-ui); }
  .mp-beyond-edge h2 { margin: 0 0 0.2rem; font-size: 0.86rem; font-family: var(--font-display); font-weight: 600; color: var(--text); }
  .mp-beyond-edge-note { margin: 0 0 0.5rem; font-size: 0.78rem; color: var(--text-mid); font-style: italic; max-width: 60ch; }
  .mp-beyond-edge ol { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.35rem; }
  .mp-beyond-edge li { border: 1px solid var(--border); border-radius: 6px; }
  .mp-beyond-edge a {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.45rem 0.6rem;
    text-decoration: none;
    color: var(--text);
    font-size: 0.82rem;
  }
  .mp-beyond-edge a:hover,
  .mp-beyond-edge a:focus-visible { background: var(--greek-hover); }
  .mp-beyond-edge a:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
  .mp-beyond-edge-item { color: var(--text-mid); }

  .mp-journey-legend { display: flex; flex-wrap: wrap; gap: 1rem; font-family: var(--font-ui); font-size: 0.84rem; color: var(--text); }
  .mp-journey-legend-item { display: flex; align-items: center; gap: 0.4rem; cursor: pointer; }
  .mp-journey-legend-item input { cursor: pointer; }
  .mp-journey-swatch { width: 32px; height: 6px; flex: none; }
  .mp-journey-swatch line { fill: none; }

  .mp-unlocated { font-family: var(--font-ui); font-size: 0.82rem; color: var(--text-mid); }
  .mp-unlocated summary { cursor: pointer; font-weight: 600; color: var(--text); }
  .mp-unlocated ul { margin: 0.5rem 0 0; padding-left: 1.2rem; columns: 2; column-gap: 1.5rem; }
  @media (max-width: 640px) { .mp-unlocated ul { columns: 1; } }
  .mp-unlocated li { margin-bottom: 0.15rem; break-inside: avoid; }
  .mp-tier-word { color: var(--text-light); }
</style>
