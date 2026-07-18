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
  import { captionSummary, type Place, type StoryStation } from '@shared/lib/maps';

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

  // Story mode (the Wanderings map only): promotes `polyline` to a heavier
  // hero route with direction arrows, swaps the coord-bearing story
  // stations' tier pins for numbered badges, and draws an always-visible
  // caption card per badge. `storyStations` is the FULL curated telling
  // order (@shared/lib/maps wanderingsStory) — both located and unlocated;
  // this component only ever draws the located subset (unlocated stations
  // are MapsPage's "beyond the map's edge" strip, not this canvas).
  export let storyMode = false;
  export let storyStations: StoryStation[] = [];

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
  let resizeObserver: ResizeObserver | null = null;

  const WORK_ABBR: Record<string, string> = { iliad: 'Il.', odyssey: 'Od.' };

  function mentionHref(work: string, book: number, line: number): string {
    return `${base}${workPath(work, book)}?loc=${formatLocValue(work, String(book), line)}`;
  }

  // ── Story mode: caption cards + direction arrows ──────────────────────────
  // Both are plain positioned DOM (not Leaflet layers): captions need
  // free-form pixel offsets and greedy collision avoidance that Leaflet's
  // marker/tooltip anchoring doesn't give us; arrows need screen-space
  // rotation (computed from projected pixel points, not raw lat/lng, so they
  // point correctly under Leaflet's projection at any zoom). Recomputed on
  // every 'move'/'zoom' event so they track pans and zooms live.
  interface CaptionPos {
    id: string;
    number: number;
    place: Place;
    href: string | null;
    left: number;
    top: number;
    // Thin leader line from the badge (pinX/pinY) to the nearest point on
    // the card's own edge (leadX/leadY) — collision avoidance sometimes
    // pushes a card well clear of its pin, and without the line it reads as
    // disconnected from the badge sharing its number.
    pinX: number;
    pinY: number;
    leadX: number;
    leadY: number;
  }
  interface ArrowPos { left: number; top: number; angle: number }

  let captions: CaptionPos[] = [];
  let arrows: ArrowPos[] = [];

  const CARD_W = 168;
  const CARD_H = 60; // safety margin above the CSS card's real rendered height (~52px), as collision-math headroom
  const CARD_GAP = 14;
  const BADGE_HALF = 12; // reserved no-card zone around every badge, incl. neighbors'

  type Rect = { x0: number; y0: number; x1: number; y1: number };

  function overlaps(a: Rect, b: Rect): boolean {
    return a.x0 < b.x1 && a.x1 > b.x0 && a.y0 < b.y1 && a.y1 > b.y0;
  }

  // Closest point ON `rect`'s boundary to an external point (px,py) —
  // clamping to the rect's bounds always lands on the boundary here because
  // the pin is never inside its own card's rect (BADGE_HALF is reserved).
  // The leader line's anchor on the card side.
  function nearestPointOnRect(px: number, py: number, rect: Rect): { x: number; y: number } {
    return {
      x: Math.max(rect.x0, Math.min(px, rect.x1)),
      y: Math.max(rect.y0, Math.min(py, rect.y1)),
    };
  }

  // Candidate card placement on a ring of radius `r` around pin pixel
  // (px,py) at angle `angle` (radians, screen space) — the card is CENTERED
  // at that ring point. A continuous angle (rather than 8 fixed compass
  // slots) is what makes the search below actually escape a tight real-world
  // cluster (Scylla/Charybdis/Thrinacia sit within ~1 degree of each other):
  // fixed compass directions run out of room fast; a growing ring with fine
  // angular steps always finds clear space eventually.
  function candidateRect(px: number, py: number, r: number, angle: number): Rect {
    const cx = px + r * Math.cos(angle);
    const cy = py + r * Math.sin(angle);
    return { x0: cx - CARD_W / 2, y0: cy - CARD_H / 2, x1: cx + CARD_W / 2, y1: cy + CARD_H / 2 };
  }

  const RING_START = CARD_GAP + Math.max(CARD_W, CARD_H) / 2;
  const RING_STEP = 10;
  const RING_COUNT = 90; // start..start+RING_STEP*90 covers any realistic map container, even a dense cluster
  const ANGLE_STEPS = 24; // 15 degree resolution per ring

  function firstMentionHref(p: Place): string | null {
    const m = p.mentions[0];
    return m ? mentionHref(m.work, m.book, m.lines[0]) : null;
  }

  // "Always visible" (VERIFY: at default zoom, no interaction) means a
  // card clipped off the map's own edge doesn't count — so a candidate
  // must also fit inside the map container, not just avoid other cards.
  function withinBounds(r: Rect, w: number, h: number): boolean {
    return r.x0 >= 0 && r.y0 >= 0 && r.x1 <= w && r.y1 <= h;
  }

  function updateOverlays() {
    if (!map || !storyMode) {
      if (captions.length || arrows.length) { captions = []; arrows = []; }
      return;
    }
    const located = storyStations.filter((s) => s.place.coords);
    const size = map.getSize();

    // Reserve a no-card zone around every badge (not just each card's own)
    // so a neighbor's caption never sits on top of a pin.
    const reserved: Rect[] = located.map((s) => {
      const pt = map.latLngToContainerPoint(s.place.coords as [number, number]);
      return { x0: pt.x - BADGE_HALF, y0: pt.y - BADGE_HALF, x1: pt.x + BADGE_HALF, y1: pt.y + BADGE_HALF };
    });

    const placed: Rect[] = [...reserved];
    const next: CaptionPos[] = [];
    for (const s of located) {
      const pt = map.latLngToContainerPoint(s.place.coords as [number, number]);
      // Preferred start angle: straight up, tried first so the common case
      // (an isolated pin) gets a tidy card directly above it; each failed
      // ring grows outward until a collision-free, in-bounds spot is found.
      // Two-pass: prefer collision-free AND fully on-screen; if the whole
      // sweep can't find that (a pin hard against the container edge), fall
      // back to the first merely collision-free spot found.
      let chosen = candidateRect(pt.x, pt.y, RING_START, -Math.PI / 2);
      let placedOk = false;
      let fallback: Rect | null = null;
      search:
      for (let ring = 0; ring < RING_COUNT; ring++) {
        const r = RING_START + ring * RING_STEP;
        for (let a = 0; a < ANGLE_STEPS; a++) {
          const angle = -Math.PI / 2 + (a * 2 * Math.PI) / ANGLE_STEPS;
          const rect = candidateRect(pt.x, pt.y, r, angle);
          if (placed.some((p) => overlaps(rect, p))) continue;
          if (!fallback) fallback = rect;
          if (withinBounds(rect, size.x, size.y)) {
            chosen = rect;
            placedOk = true;
            break search;
          }
        }
      }
      if (!placedOk && fallback) {
        chosen = fallback;
        placedOk = true;
      }
      if (!placedOk) {
        // Should not happen at any realistic map size/zoom given the ring
        // search radius (see RING_COUNT/RING_STEP above); surfaced loudly
        // rather than silently rendering an overlapping card.
        console.warn(`[LandmarkMap story mode] no collision-free caption spot found for station ${s.number} (${s.place.id})`);
      }
      placed.push(chosen);
      const lead = nearestPointOnRect(pt.x, pt.y, chosen);
      next.push({
        id: s.place.id,
        number: s.number,
        place: s.place,
        href: firstMentionHref(s.place),
        left: chosen.x0,
        top: chosen.y0,
        pinX: pt.x,
        pinY: pt.y,
        leadX: lead.x,
        leadY: lead.y,
      });
    }
    captions = next;

    // One direction arrow per hero-route segment (screen-space rotation).
    const pts = polyline.filter((p) => p.coords).map((p) => map.latLngToContainerPoint(p.coords as [number, number]));
    const nextArrows: ArrowPos[] = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const a = pts[i];
      const b = pts[i + 1];
      nextArrows.push({
        left: (a.x + b.x) / 2,
        top: (a.y + b.y) / 2,
        // +90deg: the CSS triangle glyph points "up" at rotate(0); this
        // rotates it to point along the segment's actual screen direction.
        angle: Math.atan2(b.y - a.y, b.x - a.x) * (180 / Math.PI) + 90,
      });
    }
    arrows = nextArrows;
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
    const storyNumberById = new Map(storyStations.map((s) => [s.place.id, s.number]));

    for (const item of items) {
      const p = item.place;
      if (!p.coords) continue;
      bounds.push(p.coords);

      const storyNumber = storyMode ? storyNumberById.get(item.id) : undefined;

      let layer: any;
      if (storyNumber != null) {
        // Story mode: a numbered badge replaces the tier pin for this
        // coord-bearing station (still keeps its popup — click/tap still
        // gets the full note, same as the tier pin it replaces).
        const icon = L.divIcon({
          className: `lm-badge${item.id === selectedId ? ' lm-selected' : ''}`,
          html: `<span class="lm-badge-num" aria-hidden="true">${storyNumber}</span>`,
          iconSize: [22, 22],
          iconAnchor: [11, 11],
        });
        layer = L.marker(p.coords, { icon, keyboard: false, alt: `${storyNumber}. ${p.name}` });
      } else if (p.certainty === 'mythical') {
        const icon = L.divIcon({
          className: `lm-mythical-icon${item.id === selectedId ? ' lm-selected' : ''}${storyMode ? ' lm-quiet' : ''}`,
          html: '<span class="lm-diamond" aria-hidden="true"></span>',
          iconSize: [16, 16],
          iconAnchor: [8, 8],
        });
        layer = L.marker(p.coords, { icon, keyboard: false, alt: p.name });
      } else {
        const dashArray = p.certainty === 'speculative' ? '3,2' : undefined;
        // Story mode dims/shrinks non-station wanderings pins ("quiet
        // dots") so the 17 telling-order stations read as the map's story.
        const quiet = storyMode && item.radius == null;
        layer = L.circleMarker(p.coords, {
          radius: quiet ? Math.max(4, (item.radius ?? DEFAULT_RADIUS) - 2) : item.radius ?? DEFAULT_RADIUS,
          weight: 2,
          dashArray,
          className: tierClass(p.certainty) + (item.id === selectedId ? ' lm-selected' : '') + (quiet ? ' lm-quiet' : ''),
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
        className: storyMode ? 'lm-route lm-route-story' : 'lm-route',
        weight: storyMode ? 4.5 : 2,
        dashArray: storyMode ? undefined : '6,6',
      }).addTo(map);
    }

    if (bounds.length) {
      map.fitBounds(bounds, { padding: [28, 28], maxZoom: 8 });
    }

    updateOverlays();
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
    // Keep story-mode caption cards + route arrows (plain DOM, not Leaflet
    // layers) in pixel sync through pans/zooms, including the animated
    // fitBounds pan below ('move' fires every frame of that animation).
    map.on('move zoom', updateOverlays);
    render();
    // Leaflet does not detect container resizes on its own (a responsive
    // CSS grid can change `.lm-map`'s width after mount, e.g. the tab panel
    // settling into its final layout, or a window/viewport resize) — without
    // this, latLngToContainerPoint stays keyed to a stale size and the
    // collision math above computes against the wrong pixel positions.
    resizeObserver = new ResizeObserver(() => {
      map?.invalidateSize();
      updateOverlays();
    });
    resizeObserver.observe(el);
  });

  onDestroy(() => {
    resizeObserver?.disconnect();
    map?.off('move zoom', updateOverlays);
    map?.remove();
    map = null;
  });

  // Re-draw whenever the caller swaps in a new item set (tab switch), moves
  // the selection (panel click), or toggles story mode — Leaflet is
  // imperative, so this is a full layer rebuild rather than a Svelte-reactive
  // DOM diff; the corpus is 274 places / 45 contingents, so a rebuild is
  // inexpensive.
  $: if (map && (items || polyline || selectedId !== undefined || storyMode || storyStations)) render();

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
  {#if storyMode}
    <!-- Story mode overlay: always-visible caption cards + route direction
         arrows. Plain positioned DOM (not Leaflet layers) so cards are real,
         keyboard-focusable links (`pointer-events: none` on the wrapper,
         `auto` on each card, so empty overlay areas still let the map drag).
         Hidden below 480px (see CSS): the mobile fallback is the tappable
         station list MapsPage renders under the map. -->
    <div class="lm-overlay">
      <svg class="lm-leaders" aria-hidden="true">
        {#each captions as c (c.id)}
          <line x1={c.pinX} y1={c.pinY} x2={c.leadX} y2={c.leadY} />
        {/each}
      </svg>
      {#each arrows as a, i (i)}
        <span
          class="lm-arrow"
          style="left:{a.left}px; top:{a.top}px; transform: translate(-50%, -50%) rotate({a.angle}deg);"
          aria-hidden="true"
        ></span>
      {/each}
      {#each captions as c (c.id)}
        <a
          class="lm-caption tier-{c.place.certainty}"
          class:selected={c.id === selectedId}
          style="left:{c.left}px; top:{c.top}px;"
          href={c.href ?? undefined}
          tabindex={c.href ? undefined : 0}
          aria-label={`${c.number}. ${c.place.name}, certainty: ${c.place.certainty}. ${captionSummary(c.place.note, 120)}`}
        >
          <span class="lm-caption-num" aria-hidden="true">{c.number}</span>
          <span class="lm-caption-body">
            <span class="lm-caption-name">{c.place.name}</span>
            <span class="lm-caption-note">{captionSummary(c.place.note)}</span>
          </span>
          <span class="lm-caption-tier-mark" aria-hidden="true"></span>
        </a>
      {/each}
    </div>
  {/if}
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
  /* Story mode: the route is promoted to hero — heavier weight (set via
     `weight` in the script), full --accent (not --accent-light), and a
     static glow (drop-shadow, not an animation, so it needs no
     reduced-motion guard). */
  :global(.lm-route-story) {
    stroke: var(--accent);
    filter: drop-shadow(0 0 3px var(--accent));
  }

  /* Story mode numbered station badges (replace tier pins for coord-bearing
     telling-order stations) and the "quiet dots" the other wanderings pins
     become while story mode is on. */
  :global(.lm-badge) { background: none; border: none; }
  :global(.lm-badge-num) {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--accent);
    color: var(--on-accent);
    border: 1.5px solid var(--popup-bg);
    font-family: var(--font-ui);
    font-weight: 700;
    font-size: 0.72rem;
    line-height: 1;
    box-sizing: border-box;
  }
  :global(.lm-badge.lm-selected .lm-badge-num) { border-color: var(--rule-strong); border-width: 2.4px; }
  :global(.lm-pin.lm-quiet) { opacity: 0.45; }
  :global(.lm-mythical-icon.lm-quiet .lm-diamond) { opacity: 0.45; }

  /* Story-mode overlay: caption cards + route direction arrows. Plain
     positioned DOM, not Leaflet layers (see script comment) — sits above
     Leaflet's own panes but below its popups. */
  .lm-overlay { position: absolute; inset: 0; pointer-events: none; z-index: 450; overflow: hidden; }

  .lm-leaders { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }
  .lm-leaders line { stroke: var(--text-mid); stroke-width: 1; opacity: 0.55; }
  @media (max-width: 480px) { .lm-leaders { display: none; } }

  .lm-arrow {
    position: absolute;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 8px solid var(--accent);
    opacity: 0.85;
  }

  .lm-caption {
    position: absolute;
    display: flex;
    align-items: flex-start;
    gap: 0.35rem;
    width: 168px;
    padding: 0.3rem 0.4rem;
    pointer-events: auto;
    background: var(--popup-bg);
    border: 1px solid var(--border);
    border-radius: 5px;
    box-shadow: var(--popup-shadow);
    font-family: var(--font-ui);
    text-decoration: none;
    color: var(--text);
    box-sizing: border-box;
  }
  .lm-caption:hover { border-color: var(--accent); }
  .lm-caption:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .lm-caption.selected { border-color: var(--rule-strong); border-width: 1.6px; }

  .lm-caption-num {
    flex: none;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--accent);
    color: var(--on-accent);
    font-size: 0.62rem;
    font-weight: 700;
    line-height: 1;
    margin-top: 0.05rem;
  }
  .lm-caption-body { min-width: 0; flex: 1; }
  .lm-caption-name {
    display: block;
    font-weight: 700;
    font-size: 0.74rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .lm-caption-note {
    display: block;
    margin-top: 0.1rem;
    font-size: 0.68rem;
    color: var(--text-mid);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .lm-caption-tier-mark {
    flex: none;
    width: 8px;
    height: 8px;
    margin-top: 0.2rem;
    border-radius: 50%;
    background: var(--accent);
  }
  .lm-caption.tier-certain .lm-caption-tier-mark { background: var(--accent); }
  .lm-caption.tier-traditional .lm-caption-tier-mark { background: transparent; border: 1.4px solid var(--accent); }
  .lm-caption.tier-speculative .lm-caption-tier-mark { background: transparent; border: 1.4px dashed var(--text-mid); }
  .lm-caption.tier-mythical .lm-caption-tier-mark { border: 1.4px solid var(--text-mid); border-radius: 0; transform: rotate(45deg); width: 7px; height: 7px; }

  /* Mobile: captions collide too readily to stagger sanely on a 390px
     screen — collapse to numbered badges only; MapsPage renders a tappable
     station list below the map instead. */
  @media (max-width: 480px) {
    .lm-caption { display: none; }
  }

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
