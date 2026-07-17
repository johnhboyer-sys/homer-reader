<script lang="ts">
  // Generic Leaflet canvas shared by all four /maps/ pages (Ships/Catalogue,
  // Troad, Wanderings, Greece). Pure rendering shell: callers hand it a flat
  // list of pinnable items (each wrapping a Place for the honesty fields) plus
  // an optional ordered polyline; it owns the Leaflet lifecycle, marker
  // styling by certainty tier, popups, and selection highlight/pan-to. All
  // sorting/scaling/route-membership decisions live in @shared/lib/maps (pure,
  // tested) — this component only draws what it's given.
  //
  // The ONLY external network requests this component makes are the CAWM
  // tile fetches (CLAUDE.md: "the ONLY external requests the maps may make").
  // If tiles are unreachable, Leaflet's tile <img>s simply fail to paint and
  // the container's own background (--page-bg, set in <style> below) shows
  // through as a plain ground — pins still render normally over it.
  import { onMount, onDestroy } from 'svelte';
  import 'leaflet/dist/leaflet.css';
  import L from 'leaflet';
  import { workPath } from '@shared/lib/works';
  import { formatLocValue } from '@shared/lib/citation';
  import type { Place } from '@shared/lib/maps';

  export let base: string;
  export let ariaLabel: string;
  // Every locatable pin/circle to draw. `radius` overrides the default pin
  // radius (the Ships tab's area-scaled circles); `extra` adds labelled rows
  // to the popup ABOVE the place's own honesty block (e.g. a contingent's
  // ship count) without altering the place data itself.
  export let items: { id: string; place: Place; radius?: number; extra?: { label: string; value: string }[] }[] = [];
  // Ordered, coord-bearing stations to connect with a dashed route line (the
  // Wanderings map only). Empty elsewhere.
  export let polyline: Place[] = [];
  export let selectedId: string | null = null;
  export let onSelect: ((id: string) => void) | null = null;

  const DEFAULT_RADIUS = 7;
  const CAWM_ATTRIBUTION =
    'Tiles &copy; <a href="https://cawm.lib.uiowa.edu/" target="_blank" rel="noopener">' +
    'Consortium of Ancient World Mappers (CAWM)</a>, CC BY 4.0';

  // Leaflet ships no bundled types (see app/src/types/leaflet.d.ts) — every
  // Leaflet-shaped value below is intentionally `any`.
  let el: HTMLDivElement;
  let map: any = null;
  const layers = new Map<string, any>();
  let routeLayer: any = null;

  const WORK_ABBR: Record<string, string> = { iliad: 'Il.', odyssey: 'Od.' };

  function mentionHref(work: string, book: number, line: number): string {
    return `${base}${workPath(work, book)}?loc=${formatLocValue(work, String(book), line)}`;
  }

  // Built entirely with createElement/textContent (never innerHTML) — the
  // apparatus JSON is build-time, repo-committed content, not user input, but
  // this keeps popup construction to the same no-injection posture as the
  // rest of the reader (CLAUDE.md: sanitize/escape anything rendered as
  // markup) with no escaping logic to get wrong.
  function popupNode(item: (typeof items)[number]): HTMLElement {
    const p = item.place;
    const wrap = document.createElement('div');
    wrap.className = 'lm-popup';

    const row = (cls: string, text: string, lang?: string) => {
      const d = document.createElement('div');
      d.className = cls;
      d.textContent = text;
      if (lang) d.lang = lang;
      wrap.appendChild(d);
    };

    row('lm-popup-name', p.name);
    if (p.greek) row('lm-popup-greek', p.greek, 'grc');
    if (item.extra) for (const x of item.extra) row('lm-popup-extra', `${x.label}: ${x.value}`);
    row('lm-popup-tier', `Certainty: ${p.certainty}`);
    if (p.tradition) row('lm-popup-tradition', p.tradition);
    if (p.note) row('lm-popup-note', p.note);

    if (p.mentions.length) {
      const ml = document.createElement('div');
      ml.className = 'lm-popup-mentions';
      for (const m of p.mentions) {
        const a = document.createElement('a');
        a.href = mentionHref(m.work, m.book, m.lines[0]);
        const abbr = WORK_ABBR[m.work] ?? m.work;
        const span = m.lines[1] !== m.lines[0] ? `${m.lines[0]}–${m.lines[1]}` : String(m.lines[0]);
        a.textContent = `${abbr} ${m.book}.${span}`;
        ml.appendChild(a);
        ml.appendChild(document.createTextNode(' '));
      }
      wrap.appendChild(ml);
    }
    return wrap;
  }

  function tierClass(certainty: Place['certainty']): string {
    return `lm-pin tier-${certainty}`;
  }

  function render() {
    if (!map) return;
    for (const l of layers.values()) map.removeLayer(l);
    layers.clear();
    if (routeLayer) { map.removeLayer(routeLayer); routeLayer = null; }

    const bounds: [number, number][] = [];

    for (const item of items) {
      const p = item.place;
      if (!p.coords) continue;
      bounds.push(p.coords);

      let layer: any;
      if (p.certainty === 'mythical') {
        const icon = L.divIcon({
          className: `lm-mythical-icon${item.id === selectedId ? ' lm-selected' : ''}`,
          html: '<span class="lm-diamond" aria-hidden="true"></span>',
          iconSize: [16, 16],
          iconAnchor: [8, 8],
        });
        layer = L.marker(p.coords, { icon, keyboard: false, alt: p.name });
      } else {
        const dashArray = p.certainty === 'speculative' ? '3,2' : undefined;
        layer = L.circleMarker(p.coords, {
          radius: item.radius ?? DEFAULT_RADIUS,
          weight: 2,
          dashArray,
          className: tierClass(p.certainty) + (item.id === selectedId ? ' lm-selected' : ''),
          keyboard: false,
        });
      }
      layer.bindPopup(popupNode(item));
      layer.on('click', () => onSelect?.(item.id));
      layer.addTo(map);
      layers.set(item.id, layer);
    }

    if (polyline.length > 1) {
      const coords = polyline.filter((p) => p.coords).map((p) => p.coords);
      routeLayer = L.polyline(coords, {
        className: 'lm-route',
        weight: 2,
        dashArray: '6,6',
      }).addTo(map);
    }

    if (bounds.length) {
      map.fitBounds(bounds, { padding: [28, 28], maxZoom: 8 });
    }
  }

  onMount(() => {
    // `keyboard: false` — Leaflet's own built-in map-panning keyboard handler
    // makes the container itself focusable (tabindex="0"), which combined
    // with its focusable descendants (zoom buttons, attribution links) and
    // this container's `role="img"` trips axe's nested-interactive/ARIA
    // rules. Pins are mouse-first by design here (CLAUDE.md): the
    // accessible equivalent is the fully keyboard-operable ContingentPanel/
    // not-locatable list beside/below the map, not the canvas itself.
    map = L.map(el, { scrollWheelZoom: true, worldCopyJump: false, keyboard: false }).setView([37, 24], 6);
    L.tileLayer('https://cawm.lib.uiowa.edu/tiles/{z}/{x}/{y}.png', {
      maxZoom: 12,
      attribution: CAWM_ATTRIBUTION,
    }).addTo(map);
    render();
  });

  onDestroy(() => {
    map?.remove();
    map = null;
  });

  // Re-draw whenever the caller swaps in a new item set (tab switch) or moves
  // the selection (panel click) — Leaflet is imperative, so this is a full
  // layer rebuild rather than a Svelte-reactive DOM diff; the corpus is 274
  // places / 45 contingents, so a rebuild is inexpensive.
  $: if (map && (items || polyline || selectedId !== undefined)) render();

  // Pan to (but don't re-zoom past) a newly selected item and open its popup,
  // mirroring the panel's aria-selected state.
  $: if (map && selectedId) {
    const layer = layers.get(selectedId);
    if (layer?.getLatLng) {
      map.panTo(layer.getLatLng());
      layer.openPopup?.();
    }
  }
</script>

<div class="lm-wrap">
  <!-- role="region" (not "img"): Leaflet injects real interactive controls
       (zoom buttons, the attribution link) as children of this container,
       and the ARIA "img" role's content model forbids interactive
       descendants (that's what axe's nested-interactive rule catches). A
       labelled region is the correct landmark for a widget that legitimately
       contains focusable children — the map itself stays mouse-first
       (see `keyboard: false` above); the accessible equivalent for
       keyboard users is the panel/list beside or below it. -->
  <div bind:this={el} class="lm-map" role="region" aria-label={ariaLabel}></div>
</div>

<style>
  .lm-wrap { position: relative; }
  .lm-map {
    width: 100%;
    height: min(60vh, 560px);
    min-height: 320px;
    border: 1px solid var(--border);
    border-radius: 6px;
    /* Plain "ground" shown through if CAWM tiles can't be reached. */
    background: var(--page-bg);
  }

  /* Certainty-tier marker styling (mirrors the homepage mini-tier-legend:
     certain = solid fill, traditional = ringed, speculative = dashed ring,
     mythical = rotated-square outline via the divIcon below). CSS class
     selectors beat the SVG presentation attributes Leaflet's defaults set, so
     no inline color options are passed from the script. */
  :global(.lm-pin) { cursor: pointer; }
  :global(.lm-pin.tier-certain) { stroke: var(--accent); fill: var(--accent); fill-opacity: 0.88; }
  :global(.lm-pin.tier-traditional) { stroke: var(--accent); fill: var(--accent); fill-opacity: 0.14; }
  :global(.lm-pin.tier-speculative) { stroke: var(--text-mid); fill: none; fill-opacity: 0; }
  :global(.lm-pin.lm-selected) { stroke: var(--rule-strong); stroke-width: 3.5; }

  :global(.lm-mythical-icon) { background: none; border: none; }
  :global(.lm-diamond) {
    display: block;
    width: 10px; height: 10px;
    margin: 3px;
    border: 1.6px solid var(--text-mid);
    background: var(--popup-bg);
    transform: rotate(45deg);
  }
  :global(.lm-mythical-icon.lm-selected .lm-diamond) { border-color: var(--rule-strong); border-width: 2.4px; }

  :global(.lm-route) { stroke: var(--accent-light); fill: none; }

  /* Popup content + Leaflet chrome recolored to the wine-dark tokens. */
  :global(.leaflet-popup-content-wrapper) {
    background: var(--popup-bg);
    color: var(--text);
    border-radius: 6px;
    box-shadow: var(--popup-shadow);
  }
  :global(.leaflet-popup-tip) { background: var(--popup-bg); }
  :global(.leaflet-container a.leaflet-popup-close-button) { color: var(--text-mid); }
  :global(.leaflet-control-attribution) {
    background: var(--col-bg);
    color: var(--text-mid);
    font-family: var(--font-ui);
  }
  :global(.leaflet-control-attribution a) { color: var(--accent); }
  :global(.leaflet-control-zoom a) {
    background: var(--col-bg);
    color: var(--text);
    border-color: var(--border) !important;
  }
  :global(.leaflet-control-zoom a:hover) { background: var(--accent); color: var(--on-accent); }

  :global(.lm-popup) { font-family: var(--font-ui); max-width: 240px; }
  :global(.lm-popup-name) { font-weight: 700; font-size: 0.92rem; }
  :global(.lm-popup-greek) { font-family: var(--font-greek); font-size: 0.95rem; margin-top: 0.15rem; }
  :global(.lm-popup-extra) { font-size: 0.8rem; margin-top: 0.3rem; color: var(--text-mid); }
  :global(.lm-popup-tier) {
    display: inline-block;
    margin-top: 0.35rem;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--accent);
  }
  :global(.lm-popup-tradition),
  :global(.lm-popup-note) { font-size: 0.8rem; margin-top: 0.3rem; color: var(--text-mid); }
  :global(.lm-popup-mentions) { margin-top: 0.4rem; font-size: 0.78rem; }
  :global(.lm-popup-mentions a) { color: var(--accent); margin-right: 0.4rem; }
</style>
