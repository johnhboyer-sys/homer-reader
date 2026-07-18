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
  import {
    captionSummary,
    arcPoints,
    curvedRoute,
    fadeStub,
    primaryDuration,
    chipLabel,
    durationLine,
    durationExtras,
    journeyLegNote,
    wanderingsPlaybackLegs,
    WANDERINGS_STEP_MS,
    type Place,
    type StoryStation,
    type ResolvedLeg,
    type LatLon,
    type VoyageStation,
    type TravelerNote,
  } from '@shared/lib/maps';

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

  // Wanderings tab only: the Odysseus-return journey's legs from Thrinacia
  // onward (Thrinacia -> Ogygia -> Scheria -> Ithaca), pre-resolved by
  // MapsPage against the places gazetteer. Drawn as an extension of the same
  // route -- broken/faded through the Ogygia gap (Ogygia has no coordinates
  // in the gazetteer; never a confident line to fake them), solid again
  // Scheria->Ithaca (John's explicit call, 2026-07-17: the route must end at
  // Ithaca). Empty on every tab but Wanderings.
  export let wanderingsTail: ResolvedLeg[] = [];

  // The Journeys tab only: the four nostoi, each its own color+dash route
  // (MapsPage assigns colorClass/dashArray -- see that file's JOURNEY_STYLE
  // -- so this component stays a pure rendering shell). `arrivalLegIndex`
  // marks the one leg (Odysseus's Scheria->Ithaca) that gets the heavier
  // "arriving home" glow treatment; undefined for routes with no such leg.
  export let journeyRoutes: {
    id: string;
    colorClass: string;
    dashArray: string | undefined;
    arrivalLegIndex: number | undefined;
    legs: ResolvedLeg[];
  }[] = [];

  // John's directive (2026-07-18): apparatus/voyage-chronology.json's
  // per-station poem-stated durations, pre-resolved by place id (see
  // shared/lib/maps voyageDurationByPlaceId) -- Wanderings + Journeys tabs
  // only, an empty Map elsewhere. This component only reads it, to add a
  // duration line/chip wherever a station has one; never invents one where
  // it's absent.
  export let durationsByPlaceId: Map<string, VoyageStation> = new Map();

  // Story-mode Play control (Wanderings tab only; John's directive,
  // 2026-07-18): the 1-based telling-order station number the playthrough
  // has reached, or null when the player has never been engaged this
  // Story-mode session -- in which case the map shows the ordinary,
  // fully-drawn static Story route (unchanged default behavior). MapsPage
  // owns the timer/play-pause/step state; this component only reacts to the
  // number, in the dedicated playback block below render().
  export let playbackStep: number | null = null;

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
  let tailLayers: any[] = [];
  let journeyLayers: any[] = [];
  let resizeObserver: ResizeObserver | null = null;

  // ── Story-mode Play control (John's directive, 2026-07-18) ────────────────
  // Kept entirely separate from render()'s own bookkeeping (`layers`,
  // `routeLayer`, `tailLayers`) so a single playback step never triggers a
  // full render() rebuild -- see the dedicated reactive block below `render`.
  // `playbackLastStep` null means "not engaged this Story-mode session" (the
  // ordinary, fully-drawn static route is showing). The one place the two
  // systems touch: the moment the player first engages, the static
  // routeLayer/tailLayers are hidden; the moment it disengages, a plain
  // render() call restores them (idempotent -- the same props render the
  // same thing).
  let playbackLegLayers: any[] = [];
  let playbackAnimTimers: number[] = [];
  let playbackAnimRaf: number | null = null;
  let playbackLastStep: number | null = null;
  let reducedMotionMql: MediaQueryList | null = null;
  let prefersReducedMotion = false;
  function onReducedMotionChange() { prefersReducedMotion = reducedMotionMql?.matches ?? false; }

  $: playbackLegs = wanderingsPlaybackLegs(storyStations);

  // ── Marker clustering (Wave B #7: the Ships map's Argolid clump) ──────────
  // Non-story mode only — story mode already has its own dedicated collision
  // system (captions, below). Computed ONCE per render() at the "default
  // framing" zoom fitBounds lands on, not continuously on every zoom tick
  // (simplicity: the illegible-at-default-view problem this fixes doesn't
  // require live re-clustering while the user free-zooms — scroll/zoom
  // controls keep working normally on whatever's already unclustered, and a
  // cluster badge, once clicked, expands and stays expanded for that
  // render()). A click expands the badge into its real, individually
  // certainty-styled markers (never invents a merged place) and zooms in one
  // step so they visually separate. `expandGroup` is also called from the
  // selectedId pan-to effect below, so selecting a clustered place from
  // ContingentPanel (the keyboard-operable equivalent for the Ships map)
  // reveals it rather than silently failing to pan/pop.
  interface ClusterGroup { ids: string[]; badge: any; centroid: [number, number] }
  let clusterGroups: ClusterGroup[] = [];
  // A fixed CENTER-to-center threshold, not a radius-sum ("edges touch")
  // threshold: the Ships tab's area-scaled circles run up to 26px radius
  // (see shipCircleRadius), and their edges are MEANT to brush neighbors —
  // that's the point of the area encoding, and it's still legible. A
  // radius-sum threshold chains through those large circles and swallows
  // half the map into one uninformative badge (confirmed against the
  // Argolid: it absorbed 24 of 29 Achaean places into a single "24" the
  // first time this was tried). A small fixed distance instead singles out
  // only genuinely near-coincident points — Argos/Tiryns/Mycenae's centers
  // sit within a few px of each other at default framing — without chaining
  // across the ordinary, expected overlap of differently-sized circles.
  const CLUSTER_CENTER_PX = 15;

  function unionFind(n: number) {
    const parent = Array.from({ length: n }, (_, i) => i);
    function find(i: number): number {
      while (parent[i] !== i) { parent[i] = parent[parent[i]]; i = parent[i]; }
      return i;
    }
    return { find, union: (a: number, b: number) => { const ra = find(a), rb = find(b); if (ra !== rb) parent[ra] = rb; } };
  }

  function centroidOf(coordsList: [number, number][]): [number, number] {
    const lat = coordsList.reduce((s, c) => s + c[0], 0) / coordsList.length;
    const lon = coordsList.reduce((s, c) => s + c[1], 0) / coordsList.length;
    return [lat, lon];
  }

  function expandGroup(g: ClusterGroup) {
    // The badge is about to be removed from the map (and its DOM element
    // destroyed) — if it currently holds keyboard focus (a Tab+Enter/Space
    // expansion, see below), that focus would otherwise silently fall back
    // to <body>. Move it to the map region instead so a keyboard user never
    // loses their place. `el` carries tabindex="-1" for exactly this: a
    // legitimate programmatic focus target that isn't in the normal Tab
    // order.
    const hadFocus = typeof document !== 'undefined' && document.activeElement === g.badge?.getElement?.();
    for (const id of g.ids) {
      const layer = layers.get(id);
      if (layer && !map.hasLayer(layer)) layer.addTo(map);
    }
    if (g.badge && map.hasLayer(g.badge)) map.removeLayer(g.badge);
    clusterGroups = clusterGroups.filter((x) => x !== g);
    if (hadFocus) el?.focus();
  }

  function computeClusters() {
    if (!map) return;
    for (const g of clusterGroups) { if (map.hasLayer(g.badge)) map.removeLayer(g.badge); }
    clusterGroups = [];
    if (storyMode) return;

    const entries: { id: string; pt: any; coords: [number, number] }[] = [];
    for (const item of items) {
      const p = item.place;
      const layer = p.coords ? layers.get(item.id) : null;
      if (!layer) continue;
      entries.push({ id: item.id, pt: map.latLngToContainerPoint(p.coords as [number, number]), coords: p.coords as [number, number] });
    }
    const n = entries.length;
    if (n < 2) return;
    const { find, union } = unionFind(n);
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const dx = entries[i].pt.x - entries[j].pt.x;
        const dy = entries[i].pt.y - entries[j].pt.y;
        if (Math.sqrt(dx * dx + dy * dy) < CLUSTER_CENTER_PX) union(i, j);
      }
    }
    const groups = new Map<number, number[]>();
    for (let i = 0; i < n; i++) {
      const root = find(i);
      if (!groups.has(root)) groups.set(root, []);
      groups.get(root)!.push(i);
    }
    for (const idxs of groups.values()) {
      if (idxs.length < 2) continue;
      const ids = idxs.map((i) => entries[i].id);
      const centroid = centroidOf(idxs.map((i) => entries[i].coords));
      for (const id of ids) {
        const layer = layers.get(id);
        if (layer && map.hasLayer(layer)) map.removeLayer(layer);
      }
      const group: ClusterGroup = { ids, badge: null, centroid };
      // Unlike the other markers in this file (all `keyboard: false` — see
      // the onMount comment: those are mouse-first by design, with
      // ContingentPanel as the keyboard-operable equivalent), a cluster
      // badge is itself an interactive control that ACTIVELY HIDES the
      // markers it collapses, so it has no equivalent standing control
      // elsewhere. It gets real keyboard access: `keyboard: true` makes
      // Leaflet mark the icon focusable (tabindex + role="button"), and
      // the keydown listener below supplies the Enter/Space activation
      // Leaflet's marker keyboard option doesn't wire up on its own.
      const anchorName = items.find((it) => it.id === ids[0])?.place.name ?? 'this area';
      const expandLabel = `Expand ${ids.length} places near ${anchorName}`;
      const badge = L.marker(centroid, {
        icon: L.divIcon({
          className: 'lm-cluster',
          html: `<span class="lm-cluster-num" aria-hidden="true">${ids.length}</span>`,
          iconSize: [26, 26],
          iconAnchor: [13, 13],
        }),
        keyboard: true,
      });
      badge.on('click', () => {
        expandGroup(group);
        map.setZoomAround(L.latLng(centroid), Math.min(map.getZoom() + 2, 12));
      });
      badge.addTo(map);
      const badgeEl = badge.getElement?.();
      if (badgeEl) {
        badgeEl.setAttribute('aria-label', expandLabel);
        badgeEl.addEventListener('keydown', (e: KeyboardEvent) => {
          if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
            e.preventDefault();
            badge.fire('click');
          }
        });
      }
      group.badge = badge;
      clusterGroups.push(group);
    }
  }

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
    // Compact duration chip (John, 2026-07-18): the station's poem-stated
    // duration, glance-only text ("9 days"); null when the poem states none
    // (never invented — no chip, not a guess). `durationTitle` is the fuller
    // cited line (Greek + citation) for the chip's title/aria description.
    durationChip: string | null;
    durationTitle: string | null;
    durationDetails: string[];
    // Unlocated story stations borrow the end of their faded stub as an
    // affordance position, never as a claim about where the place was.
    unplaced: boolean;
    citation: string | null;
    // Play control (John, 2026-07-18): true for the station the playthrough
    // has currently reached, when the player is engaged.
    active: boolean;
  }
  interface ArrowPos { left: number; top: number; angle: number }

  let captions: CaptionPos[] = [];
  let arrows: ArrowPos[] = [];

  const CARD_W = 168;
  // Safety margin above the CSS card's real rendered height, as collision-math
  // headroom — ~52px plain, ~68px with a duration chip (John, 2026-07-18)
  // wrapping to its own line; sized for the taller case since every card
  // shares one collision box regardless of whether ITS station has a chip.
  const CARD_H = 124;
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
    // Play control (John, 2026-07-18): once the player is engaged
    // (playbackStep non-null), only stations the playthrough has actually
    // reached get a caption card — the route "unfolds", so a caption never
    // appears ahead of the leg that reaches it. Unengaged (the ordinary
    // static Story view) shows every located station's caption, unchanged.
    const located = storyStations
      .map((s) => ({ station: s, point: s.place.coords ?? storyGapPoint(s) }))
      .filter((entry): entry is { station: StoryStation; point: LatLon } => !!entry.point)
      .filter(({ station }) => playbackStep == null || station.number <= playbackStep);
    const size = map.getSize();

    // Reserve a no-card zone around every badge (not just each card's own)
    // so a neighbor's caption never sits on top of a pin.
    const reserved: Rect[] = located.map(({ point }) => {
      const pt = map.latLngToContainerPoint(point);
      return { x0: pt.x - BADGE_HALF, y0: pt.y - BADGE_HALF, x1: pt.x + BADGE_HALF, y1: pt.y + BADGE_HALF };
    });

    const placed: Rect[] = [...reserved];
    const next: CaptionPos[] = [];
    for (const { station: s, point } of located) {
      const pt = map.latLngToContainerPoint(point);
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
      const stationDuration = s.place.id ? durationsByPlaceId.get(s.place.id) : undefined;
      const d = stationDuration ? primaryDuration(stationDuration) : null;
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
        durationChip: d ? chipLabel(d) : null,
        durationTitle: d ? durationLine(d) : null,
        durationDetails: stationDuration ? durationExtras(stationDuration).map((x) => `${x.label}: ${x.value}`) : [],
        unplaced: !s.place.coords,
        citation: stationCitation(s.place),
        active: playbackStep != null && s.number === playbackStep,
      });
    }
    captions = next;
    updateStoryBadgeState();

    // One direction arrow per hero-route segment (screen-space rotation).
    // Suppressed while the Play control is engaged — the animated leg
    // stroke itself carries direction, and drawing arrows for legs the
    // playthrough hasn't reached yet would show the route ahead of where
    // it has "unfolded" to.
    const pts = playbackStep != null
      ? []
      : polyline.filter((p) => p.coords).map((p) => map.latLngToContainerPoint(p.coords as [number, number]));
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
    // Poem-stated duration(s) for this station (John, 2026-07-18) — never
    // invented: only present when apparatus/voyage-chronology.json actually
    // records one for this place.
    const durStation = durationsByPlaceId.get(p.id);
    if (durStation) for (const x of durationExtras(durStation)) row('lm-popup-duration', `${x.label}: ${x.value}`);
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

  function stationCitation(p: Place): string | null {
    const m = p.mentions[0];
    if (!m) return null;
    const lines = m.lines[0] === m.lines[1] ? `${m.lines[0]}` : `${m.lines[0]}–${m.lines[1]}`;
    return `${WORK_ABBR[m.work] ?? m.work} ${m.book}.${lines}`;
  }

  // The fixed-geography sentence is deliberately about Homer's evidence,
  // rather than about the open-water badge, which is only an affordance.
  function storyGapPopupNode(s: StoryStation): HTMLElement {
    const wrap = document.createElement('div');
    wrap.className = 'lm-popup';
    const row = (cls: string, text: string) => {
      const d = document.createElement('div');
      d.className = cls;
      d.textContent = text;
      wrap.appendChild(d);
    };
    row('lm-popup-name', `${s.number}. ${s.place.name}`);
    row('lm-popup-note', 'Homer gives this station no fixed geography; this badge marks the route’s deliberate break, not a location.');
    const cite = stationCitation(s.place);
    if (cite) row('lm-popup-mentions', cite);
    const durStation = durationsByPlaceId.get(s.place.id);
    if (durStation) for (const x of durationExtras(durStation)) row('lm-popup-duration', `${x.label}: ${x.value}`);
    return wrap;
  }

  function tierClass(certainty: Place['certainty']): string {
    return `lm-pin tier-${certainty}`;
  }

  // ── Route curvature / gap rendering (journeyRoutes + wanderingsTail) ──────
  // Per-leg curvature ("bow", see maps.ts curvedRoute/arcPoints) and, for
  // broken legs, fade-stub bearing/length -- rendering-layer tuning tables,
  // never sourced from apparatus data (CLAUDE.md: journeys.json/places.json
  // are data only, no display hints belong there). Keyed by "from-to"
  // place-id pairs; a leg not listed falls back to a default that still
  // reads as "gentle curve, not a rigid straight line" (John, 2026-07-17)
  // even for a future journeys.json addition this table hasn't been tuned
  // for yet. Signs/magnitudes below were chosen by eye against the CAWM
  // basemap at each map's default framing, favoring a small bow through
  // tight island clusters (Scylla/Charybdis/Thrinacia; the Aeaea/
  // Laestrygonia stretch off the Italian coast) and a larger one across open
  // water or a multi-leg fan-out from a single hub (Menelaus's five Egypt
  // departures; Cape Malea, shared by two travelers).
  const DEFAULT_BOW = 0.08;
  const BOW_HINTS: Record<string, number> = {
    'ismarus-cape-malea': 0.09,
    'cape-malea-cythera': -0.1,
    'cythera-lotus-eaters-land': 0.07,
    'lotus-eaters-land-cyclopes-land': -0.06,
    'cyclopes-land-aeolia': 0.08,
    'aeolia-laestrygonia': -0.05,
    'laestrygonia-aeaea': 0.05,
    'aeaea-sirens-island': -0.06,
    'sirens-island-scylla': 0.05,
    'scylla-charybdis': -0.04,
    'charybdis-thrinacia': 0.06,
    'scheria-ithaca': -0.09,
    'troy-sounion': 0.07,
    'sounion-cape-malea': -0.08,
    'cape-malea-crete-knossos': 0.11,
    'cape-malea-egypt': -0.09,
    'egypt-pharos': 0.06,
    'pharos-sparta': -0.05,
    'egypt-cyprus': 0.1,
    'egypt-sidon-phoenicia': 0.17,
    'egypt-libya': -0.15,
    'troy-tenedos': -0.07,
    'tenedos-lesbos': 0.06,
    'lesbos-geraistos': -0.09,
    'geraistos-pylos': 0.08,
    'ithaca-pylos': 0.09,
    'pylos-pherae-messenia': -0.07,
    'pherae-messenia-sparta': 0.06,
    'sparta-ithaca': -0.1,
  };
  function bowFor(fromId: string, toId: string, legIndex: number): number {
    const hint = BOW_HINTS[`${fromId}-${toId}`];
    if (hint != null) return hint;
    return legIndex % 2 === 0 ? DEFAULT_BOW : -DEFAULT_BOW;
  }

  // Every currently-unlocatable leg in the corpus is listed explicitly (no
  // silent numeric default for these -- an unlisted unlocatable leg falls
  // back to a generic bearing AND logs a console.warn, so a future
  // journeys.json addition doesn't go unnoticed).
  const FADE_HINTS: Record<string, { bearing: number; length: number }> = {
    'thrinacia-ogygia': { bearing: 235, length: 2.6 }, // "the navel of the sea" -- southwest into open water
    'ogygia-scheria': { bearing: 235, length: 2.0 }, // mirrored: arriving at Scheria from the same unknown quarter
    'egypt-ethiopians-land': { bearing: 165, length: 3.2 }, // Homer's Ethiopians, "sundered in two" at the ends of the earth -- south
    'egypt-erembi': { bearing: 95, length: 3.0 }, // unresolved ancient crux (Strabo); fanned east of the Cyprus/Sidon legs, no identification implied
    'aeaea-cimmerians-underworld': { bearing: 300, length: 2.8 }, // Circe sends Odysseus "across Ocean" for the nekyia -- northwest, away from the Apologoi's Sicily/Italy cluster
    'cimmerians-underworld-aeaea': { bearing: 300, length: 2.2 }, // mirrored: the return from the house of Hades
    // Story-mode playback only (John, 2026-07-18): wanderingsPlaybackLegs
    // draws the 17-station telling order leg by leg, and Story order does
    // not repeat Aeaea as its own numbered stop between the Nekyia and the
    // Sirens (see maps.ts wanderingsPlaybackLegs doc) -- so the one step
    // between those two stations is this single honest gap-to-known
    // transition, standing in for Circe's actual two-hop directions
    // (Cimmerians -> Aeaea -> Sirens, Od. 12.1-40). Bearing continues the
    // voyage's own southeastward drift back toward the Sicily/Italy cluster.
    'cimmerians-underworld-sirens-island': { bearing: 120, length: 2.4 },
  };

  function drawableLeg(leg: ResolvedLeg): boolean {
    return !leg.unlocatable && !!leg.fromPlace?.coords && !!leg.toPlace?.coords;
  }

  // An unlocatable station gets one Story badge at the far end of the
  // incoming faded stub. That open-water point is a rendering affordance,
  // not a geographic identification or a coordinate for the station.
  function storyGapPoint(station: StoryStation): LatLon | null {
    const index = storyStations.findIndex((s) => s.number === station.number);
    const previous = index > 0 ? storyStations[index - 1]?.place : undefined;
    if (!previous?.coords || station.place.coords) return null;
    const hint = FADE_HINTS[`${previous.id}-${station.place.id}`];
    const pts = fadeStub(previous.coords, hint?.bearing ?? 200, hint?.length ?? 2.2, 4);
    return pts[pts.length - 1] ?? null;
  }

  const storyGapBadges = new Map<number, any>();
  function updateStoryBadgeState() {
    for (const s of storyStations) {
      if (!s.place.coords) continue;
      const el = layers.get(s.place.id)?.getElement?.();
      el?.classList.toggle('lm-active', playbackStep != null && s.number === playbackStep);
    }
    for (const [number, marker] of storyGapBadges) {
      const el = marker.getElement?.();
      el?.classList.toggle('lm-active', playbackStep != null && number === playbackStep);
    }
  }

  function drawStoryGapBadges(): void {
    storyGapBadges.clear();
    if (!storyMode) return;
    for (const s of storyStations) {
      if (s.place.coords) continue;
      const point = storyGapPoint(s);
      if (!point) continue;
      const icon = L.divIcon({
        className: `lm-gap-badge${playbackStep != null && s.number === playbackStep ? ' lm-active' : ''}`,
        html: `<span class="lm-gap-badge-num" aria-hidden="true"><span>${s.number}</span></span>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });
      const marker = L.marker(point, {
        icon,
        keyboard: false,
        alt: `${s.number}. ${s.place.name}; position not fixed`,
      });
      marker.bindPopup(storyGapPopupNode(s));
      marker.addTo(map);
      storyGapBadges.set(s.number, marker);
      layers.set(`story-gap-${s.place.id}`, marker);
    }
  }

  // Draws one leg's honesty "gap" treatment: a short fading stub from
  // whichever endpoint IS locatable, plus a small gap marker (with the leg's
  // own note in its popup) at the fading tip. Never draws anything AT the
  // unlocatable place itself -- see maps.ts fadeStub doc.
  function drawBrokenLeg(leg: ResolvedLeg, colorClass: string, showGapMarker = true): any[] {
    const out: any[] = [];
    const fromCoords = leg.fromPlace?.coords as LatLon | undefined;
    const toCoords = leg.toPlace?.coords as LatLon | undefined;
    const outbound = !!fromCoords;
    const known = outbound ? fromCoords : toCoords;
    if (!known) return out; // both endpoints unlocatable -- nothing to anchor a stub to (not in the current corpus)

    const key = `${leg.from}-${leg.to}`;
    const hint = FADE_HINTS[key];
    if (!hint) {
      console.warn(`[LandmarkMap] no FADE_HINTS entry for unlocatable leg "${key}" -- using a generic bearing`);
    }
    const bearing = hint?.bearing ?? 200;
    const length = hint?.length ?? 2.2;
    let pts = fadeStub(known, bearing, length, 4);
    if (!outbound) pts = pts.slice().reverse(); // arriving FROM the unknown: fade IN toward `known`

    // Several progressively fainter CHUNKS (not one segment per fadeStub
    // point -- at this zoom a single point-to-point segment is only ~10px
    // long, too short for a dash pattern to read as anything but a solid
    // sliver; each chunk here spans multiple points instead, long enough for
    // its own dash pattern to actually show 2-3 dashes). Leaflet has no
    // gradient stroke, so the "fade" is this per-chunk opacity step, not a
    // continuous gradient.
    const CHUNK = 2; // points per chunk (>= 2, so >=1 segment per chunk)
    for (let start = 0; start < pts.length - 1; start += CHUNK) {
      const end = Math.min(start + CHUNK, pts.length - 1);
      const chunkPts = pts.slice(start, end + 1);
      const t = outbound ? start / (pts.length - 1) : 1 - end / (pts.length - 1);
      out.push(
        L.polyline(chunkPts, {
          className: `lm-journey-route lm-journey-broken ${colorClass}`,
          weight: 2.5,
          dashArray: '4,4',
          opacity: Math.max(0.2, 0.75 * (1 - t)),
        }).addTo(map),
      );
    }

    const farPoint = outbound ? pts[pts.length - 1]! : pts[0]!;
    const unknownName = (outbound ? leg.to : leg.from).replace(/-/g, ' ');
    if (!showGapMarker) return out;
    const gapIcon = L.divIcon({
      className: 'lm-gap-marker',
      html: '<span class="lm-gap-dot" aria-hidden="true"></span>',
      iconSize: [12, 12],
      iconAnchor: [6, 6],
    });
    const gapMarker = L.marker(farPoint, { icon: gapIcon, keyboard: false, alt: `Position not fixed: ${unknownName}` });
    const popup = document.createElement('div');
    popup.className = 'lm-popup';
    const title = document.createElement('div');
    title.className = 'lm-popup-name';
    title.textContent = 'Position not fixed';
    popup.appendChild(title);
    const noteEl = document.createElement('div');
    noteEl.className = 'lm-popup-note';
    noteEl.textContent = leg.note;
    popup.appendChild(noteEl);
    // Poem-stated duration(s) for the unlocatable place itself (John,
    // 2026-07-18) — e.g. Ogygia: "kept by Calypso: 7 years — ἑπτάετες, Od.
    // 7.259" belongs on THIS gap marker (the only map presence Ogygia has —
    // it carries no coordinate of its own, see maps.ts). Never invented:
    // only present when voyage-chronology.json actually records one.
    const unknownId = outbound ? leg.to : leg.from;
    const durStation = durationsByPlaceId.get(unknownId);
    if (durStation) {
      for (const x of durationExtras(durStation)) {
        const d = document.createElement('div');
        d.className = 'lm-popup-duration';
        d.textContent = `${x.label}: ${x.value}`;
        popup.appendChild(d);
      }
    }
    gapMarker.bindPopup(popup);
    gapMarker.addTo(map);
    out.push(gapMarker);
    return out;
  }

  // A verified, hand-citation duration/timing note for one leg (Menelaus's
  // "eighth year", Nestor's sailing rhythm, Telemachus's calendar line —
  // see maps.ts JOURNEY_LEG_NOTES) rendered into a small dedicated marker's
  // popup, DOM-built the same no-innerHTML way as every other popup here.
  function noteMarkerPopupNode(note: TravelerNote): HTMLElement {
    const wrap = document.createElement('div');
    wrap.className = 'lm-popup';
    const title = document.createElement('div');
    title.className = 'lm-popup-name';
    title.textContent = note.travelerId[0]!.toUpperCase() + note.travelerId.slice(1);
    wrap.appendChild(title);
    const gloss = document.createElement('div');
    gloss.className = 'lm-popup-note';
    gloss.textContent = note.gloss;
    wrap.appendChild(gloss);
    if (note.greek) {
      const g = document.createElement('div');
      g.className = 'lm-popup-greek';
      g.lang = 'grc';
      g.textContent = note.greek;
      wrap.appendChild(g);
    }
    if (note.cite) {
      const c = document.createElement('div');
      c.className = 'lm-popup-tier';
      c.textContent = note.cite;
      wrap.appendChild(c);
    }
    return wrap;
  }

  // Draws a full leg list (a journey, or the Wanderings tail): a gently-
  // curved solid arc per drawable leg, the broken/faded gap treatment
  // otherwise. `isArrival` marks the one leg (if any) that gets the heavier
  // "arriving home" glow. A drawable leg with a verified JOURNEY_LEG_NOTES
  // entry (John, 2026-07-18: Menelaus's eighth year, Nestor's sailing
  // rhythm, Telemachus's calendar line) also gets a small note marker at
  // its midpoint, so the citation is discoverable without hunting for the
  // exact pixel of a thin curved line.
  function drawJourneyLegs(
    legs: ResolvedLeg[],
    colorClass: string,
    dashArray: string | undefined,
    weight: number,
    isArrival?: (leg: ResolvedLeg, i: number) => boolean,
    showGapMarkers = true,
  ): any[] {
    const out: any[] = [];
    legs.forEach((leg, i) => {
      if (drawableLeg(leg)) {
        const from = leg.fromPlace!.coords as LatLon;
        const to = leg.toPlace!.coords as LatLon;
        const pts = arcPoints(from, to, bowFor(leg.from, leg.to, i), 16);
        const arrival = isArrival?.(leg, i) ?? false;
        out.push(
          L.polyline(pts, {
            className: `lm-journey-route ${colorClass}${arrival ? ' lm-journey-arrival' : ''}`,
            weight,
            dashArray,
          }).addTo(map),
        );
        const note = journeyLegNote(leg.from, leg.to);
        if (note) {
          const mid = pts[Math.floor(pts.length / 2)]!;
          const icon = L.divIcon({
            className: 'lm-note-marker',
            html: '<span class="lm-note-dot" aria-hidden="true"></span>',
            iconSize: [12, 12],
            iconAnchor: [6, 6],
          });
          const marker = L.marker(mid, {
            icon,
            keyboard: false,
            alt: `Verified duration note: ${note.travelerId}`,
          });
          marker.bindPopup(noteMarkerPopupNode(note));
          marker.addTo(map);
          out.push(marker);
        }
      } else {
        out.push(...drawBrokenLeg(leg, colorClass, showGapMarkers));
      }
    });
    return out;
  }

  // ── Story-mode Play control: leg-by-leg playback ───────────────────────────
  // John's directive (2026-07-18). Deliberately NOT folded into render()'s
  // clear-and-redraw cycle: render() is retriggered by many unrelated prop
  // changes (see its own `$:` line below) and a step's animation must run
  // exactly once, only when playbackStep itself advances. These functions
  // manage their OWN small set of layers/timers (playbackLegLayers,
  // playbackAnimTimers) entirely separately from render()'s `layers` /
  // `routeLayer` / `tailLayers` bookkeeping.

  // A PlaybackLeg (maps.ts) reshaped into the same ResolvedLeg shape
  // drawableLeg()/drawBrokenLeg() already know how to draw, so playback
  // reuses the exact honesty logic (a leg is drawn broken whenever either
  // endpoint lacks coordinates) rather than a second copy of it.
  function toResolvedLeg(leg: { from: Place; to: Place }): ResolvedLeg {
    return {
      from: leg.from.id,
      to: leg.to.id,
      fromPlace: leg.from,
      toPlace: leg.to,
      certainty: leg.to.certainty,
      note: leg.to.note ?? `${leg.from.name} to ${leg.to.name}.`,
      unlocatable: !leg.from.coords || !leg.to.coords,
    };
  }

  function clearPlaybackAnimTimers() {
    for (const t of playbackAnimTimers) clearTimeout(t);
    playbackAnimTimers = [];
    if (playbackAnimRaf != null) { cancelAnimationFrame(playbackAnimRaf); playbackAnimRaf = null; }
  }

  function clearPlaybackLayers() {
    for (const l of playbackLegLayers) map?.removeLayer(l);
    playbackLegLayers = [];
  }

  // Removes the ordinary static route/tail from the map (kept, not nulled —
  // render() always removes-then-recreates them itself, so the next
  // render() call restores everything with no special-casing here).
  function hideStaticRoute() {
    if (routeLayer && map.hasLayer(routeLayer)) map.removeLayer(routeLayer);
    for (const l of tailLayers) if (map.hasLayer(l)) map.removeLayer(l);
  }

  // One completed leg's final (non-animating) appearance — a solid curved
  // arc for a drawable leg, the honest broken/faded gap treatment otherwise
  // ("Broken/unlocatable legs animate as their honest faded-stub treatment —
  // never a confident stroke to a guessed point", John's brief).
  function drawCompletedLeg(leg: { from: Place; to: Place }, legIndex: number): any[] {
    const resolved = toResolvedLeg(leg);
    if (drawableLeg(resolved)) {
      const pts = arcPoints(leg.from.coords as LatLon, leg.to.coords as LatLon, bowFor(leg.from.id, leg.to.id, legIndex), 16);
      return [
        L.polyline(pts, { className: 'lm-journey-route lm-journey-odysseus lm-route-story', weight: 4.5 }).addTo(map),
      ];
    }
    return drawBrokenLeg(resolved, 'lm-journey-odysseus', false);
  }

  // Camera follow for one step. Unlocatable stations (Cimmerians'
  // underworld, Ogygia) hold the camera where it is rather than flying to a
  // guessed point — same honesty posture as never drawing a confident line
  // to one. `animate=false` (a jump/rebuild, or prefers-reduced-motion) is
  // an instant cut; `animate=true` is a Leaflet flyTo glide.
  function flyToStation(station: StoryStation | undefined, animate: boolean) {
    if (!map || !station?.place.coords) return;
    const zoom = Math.max(map.getZoom(), 7);
    if (animate && !prefersReducedMotion) {
      map.flyTo(station.place.coords, zoom, { duration: (WANDERINGS_STEP_MS / 1000) * 0.8 });
    } else {
      map.setView(station.place.coords, zoom);
    }
  }

  // The classic SVG "draw a line" technique: a dash covering the path's
  // whole length, offset to fully hide it, then transitioned to zero. Only
  // ever called for a drawable (non-broken) leg, never under
  // prefers-reduced-motion (see the caller) — so this is the one place an
  // actual line-drawing animation happens, matching John's brief exactly.
  function animateLegStroke(layer: any, durationMs: number, onDone: () => void) {
    const path: SVGPathElement | undefined = layer?.getElement?.();
    if (!path || typeof path.getTotalLength !== 'function') { onDone(); return; }
    const len = path.getTotalLength();
    path.style.transition = 'none';
    path.style.strokeDasharray = `${len}`;
    path.style.strokeDashoffset = `${len}`;
    void path.getBoundingClientRect(); // force reflow so the transition below actually animates
    path.style.transition = `stroke-dashoffset ${durationMs}ms linear`;
    playbackAnimRaf = requestAnimationFrame(() => { path.style.strokeDashoffset = '0'; });
    const t = window.setTimeout(() => {
      path.style.transition = '';
      path.style.strokeDasharray = '';
      path.style.strokeDashoffset = '';
      onDone();
    }, durationMs + 30);
    playbackAnimTimers.push(t);
  }

  // Jump/rebuild: used on first engagement, on any step-back (Prev), and as
  // the safe fallback for any non-adjacent step change. Redraws every leg
  // up to (not including) `step` instantly (no animation — this is a jump,
  // not a step), then cuts the camera to `step`'s station.
  function rebuildPlaybackTo(step: number) {
    clearPlaybackAnimTimers();
    clearPlaybackLayers();
    const newLayers: any[] = [];
    for (let i = 0; i < step - 1; i++) {
      const leg = playbackLegs[i];
      if (leg) newLayers.push(...drawCompletedLeg(leg, i));
    }
    playbackLegLayers = newLayers;
    playbackLastStep = step;
    flyToStation(storyStations.find((s) => s.number === step), false);
    updateOverlays();
  }

  // Advance exactly one step forward (autoplay tick or a Next click): the
  // only path that actually animates — camera glide + stroke-draw for a
  // drawable leg, or (broken leg / prefers-reduced-motion) an instant
  // completed-leg draw, same treatment as rebuildPlaybackTo's per-leg draw.
  function stepForwardAnimated(toStep: number) {
    flyToStation(storyStations.find((s) => s.number === toStep), true);
    const leg = playbackLegs[toStep - 2];
    if (!leg) { playbackLastStep = toStep; updateOverlays(); return; }
    const resolved = toResolvedLeg(leg);
    if (drawableLeg(resolved) && !prefersReducedMotion) {
      const pts = arcPoints(leg.from.coords as LatLon, leg.to.coords as LatLon, bowFor(leg.from.id, leg.to.id, toStep - 2), 16);
      const layer = L.polyline(pts, { className: 'lm-journey-route lm-journey-odysseus lm-route-story', weight: 4.5 }).addTo(map);
      playbackLegLayers = [...playbackLegLayers, layer];
      animateLegStroke(layer, Math.round(WANDERINGS_STEP_MS * 0.75), () => { playbackLastStep = toStep; });
    } else {
      playbackLegLayers = [...playbackLegLayers, ...drawCompletedLeg(leg, toStep - 2)];
      playbackLastStep = toStep;
    }
    updateOverlays();
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

    // Render one station-owned badge per coordless Story station, separate
    // from broken-leg drawing so an incoming/outgoing pair cannot duplicate
    // a number (and a station can never silently disappear from the count).
    drawStoryGapBadges();

    if (polyline.length > 1) {
      // Gently curved, not a rigid straight polyline (John, 2026-07-17) --
      // see maps.ts curvedRoute/arcPoints and this file's BOW_HINTS above.
      const routePlaces = polyline.filter((p) => p.coords);
      const coords: LatLon[] = routePlaces.map((p) => p.coords as LatLon);
      const curved = curvedRoute(coords, (i) => bowFor(routePlaces[i]!.id, routePlaces[i + 1]!.id, i), 16);
      routeLayer = L.polyline(curved, {
        className: storyMode ? 'lm-route lm-route-story' : 'lm-route',
        weight: storyMode ? 4.5 : 2,
        dashArray: storyMode ? undefined : '6,6',
      }).addTo(map);
    }

    // Wanderings-tab-only extension: Thrinacia -> Ogygia (broken) -> Scheria
    // -> Ithaca, in the SAME color/dash treatment as the route above so it
    // reads as one continuous line -- see this file's drawJourneyLegs.
    for (const l of tailLayers) map.removeLayer(l);
    tailLayers = wanderingsTail.length
      ? drawJourneyLegs(
          wanderingsTail,
          'lm-journey-odysseus',
          storyMode ? undefined : '6,6',
          storyMode ? 4.5 : 2,
          (_leg, i) => i === wanderingsTail.length - 1,
          !storyMode,
        )
      : [];

    // The ordinary Story polyline intentionally omits coordless stations,
    // so give those legs their honest faded stubs too. Ogygia's matching
    // return-tail legs were already drawn immediately above; excluding those
    // keys avoids doubling their stubs while keeping this data-derived for
    // any other unlocated Story station (the Nekyia today).
    if (storyMode) {
      const tailBrokenKeys = new Set(
        wanderingsTail
          .filter((leg) => !drawableLeg(leg))
          .map((leg) => `${leg.from}-${leg.to}`),
      );
      for (const leg of playbackLegs) {
        const resolved = toResolvedLeg(leg);
        if (!drawableLeg(resolved) && !tailBrokenKeys.has(`${resolved.from}-${resolved.to}`)) {
          tailLayers.push(...drawBrokenLeg(resolved, 'lm-journey-odysseus', false));
        }
      }
    }

    // Journeys-tab-only: the four nostoi, each its own color+dash route.
    for (const l of journeyLayers) map.removeLayer(l);
    journeyLayers = journeyRoutes.flatMap((route) =>
      drawJourneyLegs(
        route.legs,
        route.colorClass,
        route.dashArray,
        2.5,
        route.arrivalLegIndex != null ? (_leg, i) => i === route.arrivalLegIndex : undefined,
      ),
    );

    if (bounds.length) {
      map.fitBounds(bounds, { padding: [28, 28], maxZoom: 8 });
      // Clamp pan/zoom-out to this map's own data extent (Wave B #6): CAWM's
      // tile mosaic thins out well beyond the Mediterranean/Aegean core, and
      // without a clamp, panning or zooming out from a tight cluster (e.g.
      // the Troad) reaches genuinely blank tiles — the container's own
      // background shows through as a grey void. `pad(0.5)` (at least
      // MIN_BOX_DEG in each direction, for a single-point or very tight
      // map) gives comfortable browsing room around the data while keeping
      // the view inside well-covered territory. Recomputed every render()
      // (tab switch), so each of the four maps gets its own box sized to its
      // own places, not one shared global one.
      const MIN_BOX_DEG = 0.75;
      const b = L.latLngBounds(bounds);
      const ne = b.getNorthEast();
      const sw = b.getSouthWest();
      const latPad = Math.max(MIN_BOX_DEG, (ne.lat - sw.lat) * 0.5);
      const lngPad = Math.max(MIN_BOX_DEG, (ne.lng - sw.lng) * 0.5);
      const padded = L.latLngBounds(
        [sw.lat - latPad, sw.lng - lngPad],
        [ne.lat + latPad, ne.lng + lngPad],
      );
      map.setMaxBounds(padded);
      map.setMinZoom(Math.max(2, map.getBoundsZoom(padded, false)));
    } else {
      map.setMaxBounds(null);
      map.setMinZoom(0);
    }

    updateOverlays();
    computeClusters();
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
      computeClusters();
    });
    resizeObserver.observe(el);

    // prefers-reduced-motion (John's brief): no line-drawing or
    // camera-glide animation — instant step transitions, same controls.
    // Read live (not just once) so a Playwright emulateMedia() toggle
    // mid-session — or a user's OS-level toggle — takes effect immediately.
    if (typeof window !== 'undefined' && window.matchMedia) {
      reducedMotionMql = window.matchMedia('(prefers-reduced-motion: reduce)');
      onReducedMotionChange();
      reducedMotionMql.addEventListener('change', onReducedMotionChange);
    }
  });

  onDestroy(() => {
    resizeObserver?.disconnect();
    map?.off('move zoom', updateOverlays);
    reducedMotionMql?.removeEventListener('change', onReducedMotionChange);
    clearPlaybackAnimTimers();
    map?.remove();
    map = null;
  });

  // Re-draw whenever the caller swaps in a new item set (tab switch), moves
  // the selection (panel click), or toggles story mode — Leaflet is
  // imperative, so this is a full layer rebuild rather than a Svelte-reactive
  // DOM diff; the corpus is 274 places / 45 contingents, so a rebuild is
  // inexpensive.
  $: if (map && (items || polyline || selectedId !== undefined || storyMode || storyStations || wanderingsTail || journeyRoutes)) render();

  // Pan to (but don't re-zoom past) a newly selected item and open its popup,
  // mirroring the panel's aria-selected state. If the selection is currently
  // hidden inside a cluster badge (Wave B #7), expand that badge first —
  // ContingentPanel is the keyboard-operable equivalent of the map, so a
  // place selected there must always become reachable, not silently fail to
  // pan/pop because it's bundled under a "3" badge.
  $: if (map && selectedId) {
    const layer = layers.get(selectedId);
    if (layer && !map.hasLayer(layer)) {
      const g = clusterGroups.find((cg) => cg.ids.includes(selectedId as string));
      if (g) expandGroup(g);
    }
    if (layer?.getLatLng) {
      map.panTo(layer.getLatLng());
      layer.openPopup?.();
    }
  }

  // ── Story-mode Play control: engage / step / disengage ────────────────────
  // Deliberately its OWN reactive block, not folded into the render() one
  // above — see the "Story-mode Play control" comment further up. Only
  // depends on `playbackStep` (MapsPage's single source of truth for the
  // player's position) plus `map`/`storyMode` guards.
  $: if (map && storyMode && playbackStep != null) {
    const target = playbackStep;
    if (playbackLastStep == null) {
      // First engagement this Story-mode session: hide the ordinary static
      // route once, then jump-render up to `target` (normally 1 — Play/Next/
      // Prev all engage at the current step, no legs played yet).
      hideStaticRoute();
      rebuildPlaybackTo(target);
    } else if (target === playbackLastStep + 1) {
      stepForwardAnimated(target);
    } else if (target !== playbackLastStep) {
      // Any non-adjacent change (Prev, or a jump) — always correct, just
      // without a per-leg animation, matching this component's own
      // "jump vs. step" distinction above.
      rebuildPlaybackTo(target);
    }
  }

  // Disengage: storyMode turned off, or MapsPage stopped passing a step
  // (both count as "exiting Story mode or switching tabs", John's brief) —
  // tear down every playback-only layer/timer and let a plain render() call
  // restore the ordinary static route, unchanged from before the player was
  // ever touched.
  $: if (map && playbackLastStep != null && (!storyMode || playbackStep == null)) {
    clearPlaybackAnimTimers();
    clearPlaybackLayers();
    playbackLastStep = null;
    render();
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
       keyboard users is the panel/list beside or below it. Cluster badges
       are the one exception (they're real keyboard-focusable controls —
       see computeClusters), so this region also carries tabindex="-1": a
       legitimate focus target (not in the Tab order) that expandGroup
       moves focus to when a badge it just removed held it. -->
  <div bind:this={el} class="lm-map" role="region" aria-label={ariaLabel} tabindex="-1"></div>
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
          class:active={c.active}
          style="left:{c.left}px; top:{c.top}px;"
          href={c.href ?? undefined}
          tabindex={c.href ? undefined : 0}
          aria-label={`${c.number}. ${c.place.name}, certainty: ${c.place.certainty}. ${captionSummary(c.place.note, 120)}${c.durationTitle ? '. Duration: ' + c.durationTitle : ''}`}
        >
          <span class="lm-caption-num" aria-hidden="true">{c.number}</span>
          <span class="lm-caption-body">
            <span class="lm-caption-name">{c.place.name}</span>
            {#if c.unplaced}
              <span class="lm-caption-note lm-caption-note-unplaced">Homer gives no fixed geography; route break, not location.</span>
              {#if c.citation}<span class="lm-caption-citation">{c.citation}</span>{/if}
              {#each c.durationDetails as detail}
                <span class="lm-caption-duration">{detail}</span>
              {/each}
            {:else}
              <span class="lm-caption-note">{captionSummary(c.place.note)}</span>
            {/if}
            {#if c.durationChip}
              <span class="lm-caption-chip" title={c.durationTitle ?? undefined}>{c.durationChip}</span>
            {/if}
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
    /* Fallback "ground" shown through any gap in the CAWM tile mosaic (a
       failed/slow tile fetch, or a residual gap the bounds clamp above
       doesn't fully reach) — tinted to sit inside the duotone treatment
       below rather than reading as a raw UI-grey void (Wave B #6). */
    background: #cdd2c6;
  }
  :global(:root[data-theme="dark"] .lm-map) { background: #171224; }

  /* CAWM's tile basemap ships in stock atlas green/blue — a per-theme CSS
     filter on Leaflet's tile pane (not the pins/popups/chrome, which live in
     separate panes) mutes it into the site's own parchment (light) / plum
     (dark) family (Wave B #6). Sepia+hue-rotate for light keeps the terrain
     legible under a warm, desaturated cast; the dark treatment is the
     standard invert+hue-rotate "negative" trick (recovers original hue
     relationships at inverted lightness) then desaturated/dimmed and
     re-tinted toward the Wine-dark plum so coastlines/labels stay readable
     against the dark UI instead of glaring at full basemap brightness. */
  :global(.lm-map .leaflet-tile-pane) {
    filter: sepia(0.3) saturate(0.55) hue-rotate(-8deg) brightness(1.04) contrast(0.96);
  }
  :global(:root[data-theme="dark"] .lm-map .leaflet-tile-pane) {
    filter: invert(1) hue-rotate(185deg) saturate(0.5) brightness(0.6) contrast(1.1);
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

  /* Journey routes (John, 2026-07-17): the Wanderings-tail extension and the
     Journeys tab's four nostoi. Colors are CSS custom properties MapsPage
     defines on its own .mp-root wrapper (an ancestor of this component's
     .lm-map, so ordinary CSS inheritance carries them down to these Leaflet
     SVG paths) -- see that file for the derivation-from-tokens formula. The
     var()-with-fallback here is defensive only: MapsPage always sets these,
     but a bare --accent/etc. keeps a broken/faded route legible even if it
     didn't. */
  :global(.lm-journey-route) { fill: none; }
  :global(.lm-journey-odysseus) { stroke: var(--journey-odysseus, var(--accent)); }
  :global(.lm-journey-menelaus) { stroke: var(--journey-menelaus, var(--accent-light)); }
  :global(.lm-journey-nestor) { stroke: var(--journey-nestor, var(--rule-strong)); }
  :global(.lm-journey-telemachus) { stroke: var(--journey-telemachus, var(--text-mid)); }
  /* The one leg that gets the heavier "arriving home" glow (Odysseus's
     Scheria->Ithaca, on both the Wanderings tail and the Journeys tab). */
  :global(.lm-journey-arrival) { filter: drop-shadow(0 0 3px var(--journey-odysseus, var(--accent))); }
  /* Broken/faded "gap" leg treatment (an unlocatable endpoint -- Ogygia; the
     Ethiopians; the Erembi): several progressively fainter mini-segments
     (opacity set inline per-segment in the script, Leaflet has no gradient
     stroke) in a fine dotted pattern distinct from every traveler's own dash,
     so a gap reads as "gap", not as that traveler's ordinary route. */
  :global(.lm-journey-broken) { stroke-linecap: round; }

  :global(.lm-gap-marker) { background: none; border: none; }
  .lm-gap-dot {
    display: block;
    width: 8px; height: 8px;
    margin: 2px;
    border-radius: 50%;
    border: 1.4px dashed var(--text-mid);
    background: var(--popup-bg);
  }

  /* Story's unplaced stations retain their number, but the dashed diamond
     uses the map's mythical-tier language to distinguish an affordance point
     from a solid, geographically identified station pin. */
  :global(.lm-gap-badge) { background: none; border: none; }
  :global(.lm-gap-badge-num) {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    margin: 3px;
    box-sizing: border-box;
    transform: rotate(45deg);
    border: 1.5px dashed var(--text-mid);
    background: var(--popup-bg);
    color: var(--text);
    font-family: var(--font-ui);
    font-size: 0.68rem;
    font-weight: 700;
    line-height: 1;
  }
  :global(.lm-gap-badge-num > span) { transform: rotate(-45deg); }
  :global(.lm-gap-badge.lm-active .lm-gap-badge-num) {
    border-color: var(--accent);
    border-width: 2.2px;
    background: var(--greek-hover);
    color: var(--accent);
  }

  /* Verified traveler-timing note marker (John, 2026-07-18: Menelaus's
     eighth year, Nestor's sailing rhythm, Telemachus's calendar line) — a
     small SOLID dot (unlike the dashed lm-gap-dot honesty marker above) so
     it reads as "here's a citation", not as a gap in the record. */
  :global(.lm-note-marker) { background: none; border: none; cursor: pointer; }
  .lm-note-dot {
    display: block;
    width: 8px; height: 8px;
    margin: 2px;
    border-radius: 50%;
    border: 1.4px solid var(--accent);
    background: var(--accent);
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
  :global(.lm-badge.lm-active .lm-badge-num) { border-color: var(--rule-strong); border-width: 2.4px; box-shadow: 0 0 0 2px var(--greek-hover); }
  :global(.lm-pin.lm-quiet) { opacity: 0.45; }
  :global(.lm-mythical-icon.lm-quiet .lm-diamond) { opacity: 0.45; }

  /* Cluster badges (Wave B #7): a neutral count marker standing in for
     several places whose real pins overlap at the current zoom (the
     Argolid clump on the Ships map, chiefly) — deliberately NOT tier-styled
     (--accent fill like a certain-tier pin, or a ring like traditional)
     since a badge represents a MIX of places whose certainty may differ;
     asserting one tier for the group would misrepresent the others. Click
     expands it into its real, individually tier-styled markers. */
  :global(.lm-cluster) { background: none; border: none; cursor: pointer; }
  :global(.lm-cluster-num) {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: var(--popup-bg);
    color: var(--text);
    border: 1.8px solid var(--accent);
    box-shadow: var(--popup-shadow);
    font-family: var(--font-ui);
    font-weight: 700;
    font-size: 0.74rem;
    line-height: 1;
    box-sizing: border-box;
  }
  :global(.lm-cluster:hover .lm-cluster-num) { border-color: var(--rule-strong); border-width: 2.2px; }
  :global(.lm-cluster:focus-visible) { outline: 2px solid var(--accent); outline-offset: 2px; }
  :global(.lm-cluster:focus-visible .lm-cluster-num) { border-color: var(--rule-strong); border-width: 2.2px; }

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
  /* Play control (John, 2026-07-18): the station the playthrough has
     currently reached — a stronger fill than .selected's border-only
     treatment, since during playback there's no separate click-to-select
     interaction competing for the same visual language. */
  .lm-caption.active { border-color: var(--accent); border-width: 1.6px; background: var(--greek-hover); }

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
  .lm-caption-note-unplaced { white-space: normal; overflow: visible; text-overflow: clip; line-height: 1.25; }
  .lm-caption-citation { display: block; margin-top: 0.08rem; font-size: 0.62rem; color: var(--text-mid); }
  .lm-caption-duration { display: block; margin-top: 0.08rem; font-size: 0.62rem; color: var(--text-mid); line-height: 1.25; }
  .lm-caption-tier-mark {
    flex: none;
    width: 8px;
    height: 8px;
    margin-top: 0.2rem;
    border-radius: 50%;
    background: var(--accent);
  }
  /* Compact duration chip (John, 2026-07-18): glance-only text ("9 days");
     the full cited line (Greek + citation) is the chip's title attribute,
     not shown here — the caption card is already tight on space. */
  .lm-caption-chip {
    display: inline-block;
    margin-top: 0.15rem;
    padding: 0.04rem 0.3rem;
    border-radius: 999px;
    border: 1px solid var(--accent);
    color: var(--accent);
    font-size: 0.6rem;
    font-weight: 600;
    line-height: 1.3;
    white-space: nowrap;
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
  /* Poem-stated duration line(s) (John, 2026-07-18) — "Duration: 9 days —
     ἐννῆμαρ, Od. 9.82" and the like. Distinguished from the plain
     lm-popup-extra rows (ship counts etc.) by weight + accent color, since a
     verified citation carries more evidential weight than a display fact. */
  :global(.lm-popup-duration) { font-size: 0.8rem; margin-top: 0.3rem; font-weight: 600; color: var(--accent); }
  :global(.lm-popup-mentions) { margin-top: 0.4rem; font-size: 0.78rem; }
  :global(.lm-popup-mentions a) { color: var(--accent); margin-right: 0.4rem; }
</style>
