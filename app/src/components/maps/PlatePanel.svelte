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
  import {
    parsePlate,
    renderPlate,
    scaleBarMarkup,
    computeCamera,
    type PlatePlace,
    type PlateLayer,
    type Certainty,
    type Viewport,
    type Plate,
    type LabelBox,
  } from '@shared/lib/plate';
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
  // Frame the camera on these ids (place or layer, per computeCamera) rather
  // than showing the whole sheet at load -- the Chart Room postcard's
  // click-through (Reader.svelte links here with `?focus=<ids>`). Empty
  // (the default) leaves the identity camera, exactly the old behaviour.
  // Only ever consulted for a plate.ts `layers` plate -- the shield takes no
  // camera at all.
  export let focusIds: string[] = [];

  type Status = 'loading' | 'ready' | 'missing' | 'error';
  let status: Status = 'loading';
  let errorMessage = '';

  let svgMarkup = '';
  let plateTitle = '';
  let isDraft = false;
  let plateSize: [number, number] = [4, 3];
  // The plate's own projection, as returned by renderPlate -- kept only so
  // the camera can re-derive an honest scale bar at the current zoom (see
  // updateScaleBar): `{ ...plateViewport, scale: plateViewport.scale * camK }`
  // is the same viewport plate.ts's scaleBarMarkup was given at zoom 1,
  // scaled the same way the camera's own transform scales the geometry.
  // Undefined for a schematic plate (no scale bar) and for the shield (not a
  // plate.ts plate at all).
  let plateViewport: Viewport | undefined;
  let unlocated: PlatePlace[] = [];
  // Places with a real, defensible position that simply falls outside this
  // plate's own frame (renderPlate's `offCanvas` bucket, 2026-07-28, finding
  // 1) -- a different claim from `unlocated` ("no defensible position at
  // all") and kept as a visibly distinct list, never merged into it.
  let offCanvas: PlatePlace[] = [];
  // Places with no pin position but visibly drawn anyway via a layer's own
  // geometry (renderPlate's `drawnByLayer` bucket, 2026-07-28, Problem 2 --
  // e.g. `wall-of-troy` carried by the citadel's wall-circuit layers,
  // `pergamos` carried by the summit region) -- a third distinct claim from
  // both `unlocated` and `offCanvas`, listed separately so "is X on this
  // map?" always has an honest answer.
  let drawnByLayer: PlatePlace[] = [];
  // Only ever true for a schematic plate.ts plate that resolved at least one
  // place via `plateAnchors` + `positionBasis: "conjectural"` (see plate.ts's
  // resolvePlacePosition) -- the shield itself takes no places, so this stays
  // false there.
  let hasConjectural = false;

  // ── Layer toggles: relief / rivers / shoreline ─────────────────────────
  // Replaces the old one-checkbox-per-layer debug panel (up to 28 boxes on
  // troad.json) with exactly three, grouped by `PlateLayer.kind` -- the
  // honest, renderer-defined category, not a guess from the id string (real
  // plates don't consistently prefix ids by kind: trojan-plain.json's own
  // river layers are just `scamander` / `simoeis`, no `river-` prefix).
  type LayerCategory = 'relief' | 'river' | 'coast';
  const CATEGORY_LABEL: Record<LayerCategory, string> = { relief: 'relief', river: 'rivers', coast: 'shoreline' };
  const CATEGORY_ORDER: LayerCategory[] = ['relief', 'river', 'coast'];
  function layerCategory(layer: PlateLayer): LayerCategory | null {
    if (layer.kind === 'relief') return 'relief';
    if (layer.kind === 'river') return 'river';
    if (layer.kind === 'coast') return 'coast';
    return null;
  }
  let plateLayers: PlateLayer[] = [];
  let layerCategories: LayerCategory[] = [];
  let categoryVisible: Record<LayerCategory, boolean> = { relief: true, river: true, coast: true };

  function applyLayerVisibility() {
    if (!mapEl) return;
    const categoryById = new Map(plateLayers.map((l) => [l.id, layerCategory(l)]));
    // Finding 8 (2026-07-28): a layer id is validator-accepted apparatus
    // data, not a trusted literal -- an id like `x"]` interpolated straight
    // into a `[data-layer-id="..."]` selector breaks the attribute-value
    // quoting and throws a DOMException. Select every data-layer-id element
    // and compare the dataset value in JS instead of building a selector
    // string from the id at all.
    //
    // Match on data-layer-id, NOT data-feature-id (2026-07-29, two lanes'
    // bug report): several plate.ts registers emit auxiliary elements with
    // SUFFIXED feature ids for one logical layer -- `<id>-band` (the
    // reconstructed shore's blurred halo), `<id>-body` (filled coasts),
    // `<id>-waterline-N`. An exact data-feature-id match missed those, so
    // toggling the layer off left its auxiliaries on the sheet. data-layer-id
    // is plate.ts stamping the relationship explicitly on every element a
    // layer draws (see renderLayer's own comment) -- this component never
    // has to know the renderer's suffix vocabulary.
    mapEl.querySelectorAll<SVGElement>('[data-layer-id]').forEach((el) => {
      const category = categoryById.get(el.dataset.layerId ?? '');
      // A layer outside the three toggle categories (wall/route/region/
      // shipRow/tumulus/band) has no checkbox and stays visible -- same as
      // before this change, when it never had a `default` field either.
      if (!category) return;
      el.style.display = categoryVisible[category] === false ? 'none' : '';
    });
  }

  function toggleCategory(category: LayerCategory, on: boolean) {
    categoryVisible = { ...categoryVisible, [category]: on };
    applyLayerVisibility();
    applyCertaintyVisibility();
  }

  // ── Certainty filter ────────────────────────────────────────────────────
  // Replaces the per-layer debug boxes' other half of the job: filtering by
  // the gazetteer's own certainty tier, read straight from the `places` prop
  // (every place already carries `.certainty`) rather than from anything
  // scraped off the rendered SVG.
  const CERTAINTY_TIERS: Certainty[] = ['certain', 'traditional', 'speculative', 'mythical'];
  let certaintyVisible: Record<Certainty, boolean> = {
    certain: true,
    traditional: true,
    speculative: true,
    mythical: true,
  };
  let currentPlaces: PlatePlace[] = [];

  function applyCertaintyVisibility() {
    if (!mapEl) return;
    const hidden = new Set(
      currentPlaces.filter((p) => certaintyVisible[p.certainty ?? 'certain'] === false).map((p) => p.id),
    );
    mapEl.querySelectorAll<SVGElement>('[data-place-id]').forEach((el) => {
      const id = el.dataset.placeId;
      el.style.display = id && hidden.has(id) ? 'none' : '';
    });
    // Layers carry their gazetteer place as `placeId` on the plate object,
    // not as `data-place-id` on the SVG (that attribute is pins/dots only).
    // Match `[data-layer-id]` via dataset — never interpolate an id into a
    // selector (plate.ts, data-layer-id stamp). This pass owns both
    // directions for layers with a placeId: hide when the tier is off;
    // otherwise leave applyLayerVisibility's decision on categorized
    // layers (a category that's off stays off) and restore uncategorized
    // ones (region/wall/route/shipRow/tumulus/band have no category pass).
    const hiddenLayers = new Set(
      plateLayers.filter((l) => l.placeId && hidden.has(l.placeId)).map((l) => l.id),
    );
    mapEl.querySelectorAll<SVGElement>('[data-layer-id]').forEach((el) => {
      const id = el.dataset.layerId;
      if (!id) return;
      const layer = plateLayers.find((l) => l.id === id);
      if (!layer?.placeId) return;
      if (hiddenLayers.has(id)) el.style.display = 'none';
      else if (!layerCategory(layer)) el.style.display = '';
    });
    // A label carries `data-label-for` naming the place OR layer id it
    // letters (plate.ts, 2026-07-30) -- hide a place's name together with
    // its pin, and a layer's name together with its linework.
    mapEl.querySelectorAll<SVGElement>('[data-label-for]').forEach((el) => {
      const id = el.dataset.labelFor;
      el.style.display = id && (hidden.has(id) || hiddenLayers.has(id)) ? 'none' : '';
    });
    // Numbered feature key (stage 5c): a badge already matches the
    // `[data-place-id]`/`[data-layer-id]` passes above (it carries exactly
    // one of those two attributes, same as a pin or a layer), so hiding a
    // tier already hides the badge itself. The key ROW is separate DOM (the
    // right-margin text list) named only by data-key-n -- find it by
    // matching that badge's own data-key-n, so the key never keeps
    // numbering a feature the certainty filter just hid.
    const hiddenKeyNs = new Set<string>();
    mapEl.querySelectorAll<SVGElement>('.plate-key-badge').forEach((badge) => {
      const pid = badge.dataset.placeId;
      const lid = badge.dataset.layerId;
      const isHidden = (pid && hidden.has(pid)) || (lid && hiddenLayers.has(lid));
      if (isHidden && badge.dataset.keyN) hiddenKeyNs.add(badge.dataset.keyN);
    });
    mapEl.querySelectorAll<SVGElement>('.plate-key-row').forEach((row) => {
      const n = row.dataset.keyN;
      row.style.display = n && hiddenKeyNs.has(n) ? 'none' : '';
    });
  }

  function toggleCertainty(tier: Certainty, on: boolean) {
    certaintyVisible = { ...certaintyVisible, [tier]: on };
    applyLayerVisibility();
    applyCertaintyVisibility();
  }

  // ── Camera: pan/zoom ─────────────────────────────────────────────────────
  // A pure CSS-style transform (`translate(tx,ty) scale(k)`) on a `<g>`
  // wrapped around the rendered content, INSIDE the sheet's own clip-path
  // group but not carrying the clip-path itself -- clip-path and transform
  // on the SAME element would scale the clip window along with the content
  // (clip-path's userSpaceOnUse geometry is resolved in the element's own,
  // already-transformed, local space), which would defeat cropping to the
  // panel's frame entirely. Legend, scale bar, hypsometric key and neatline
  // stay OUTSIDE this group (scale bar/key/neatline already were, by
  // plate.ts's own paint order; the legend is pulled out here) so they read
  // as fixed chrome rather than panning away with the map.
  const CAM_MIN_K = 1;
  const CAM_MAX_K = 8;
  // How far past the content's own edge a pan may go before it clamps --
  // enough slack to bring an edge feature to the panel's centre, not so much
  // that the map can be panned entirely out of view and "lost."
  const CAM_OVERPAN_FRACTION = 0.4;
  const ZOOM_STEP = 1.25;
  const PAN_STEP_SCREEN_PX = 60;

  let svgEl: SVGSVGElement | undefined;
  let clipG: SVGGElement | undefined;
  let cameraG: SVGGElement | undefined;
  let labelWrappers: { el: SVGGElement; x: number; y: number }[] = [];
  let camK = 1;
  let camTx = 0;
  let camTy = 0;
  let dragPointerId: number | null = null;
  let dragStart = { x: 0, y: 0, tx: 0, ty: 0 };

  // ── Numbered feature key (stage 5c): badge <-> key-row hover/focus ──────
  // A `.plate-key-badge` (plate.ts's numeral disc) is a hover/focus target
  // the same as a Greek token elsewhere in the reader; the matching
  // `.plate-key-row` (the right-margin text list) lights up with it, and
  // the reverse (hovering the row lights the badge and its pin). Always
  // matched via `dataset.keyN`/`dataset.placeId`/`dataset.layerId`
  // comparisons, never a selector built from plate data (Finding 8,
  // 2026-07-28's rule applies to badges' ids exactly as it does to layer
  // ids).
  let mapFrameEl: HTMLDivElement | undefined;
  let tipVisible = false;
  let tipText = '';
  let tipLeft = 0;
  let tipTop = 0;
  let activeBadgeEl: SVGGElement | null = null;
  let activeRowEls: SVGElement[] = [];
  let activePinEl: SVGGElement | null = null;

  function badgeCertainty(el: SVGGElement): Certainty | undefined {
    const placeId = el.dataset.placeId;
    if (placeId) return currentPlaces.find((p) => p.id === placeId)?.certainty;
    const layerId = el.dataset.layerId;
    if (layerId) {
      const layer = plateLayers.find((l) => l.id === layerId);
      if (layer?.placeId) return currentPlaces.find((p) => p.id === layer.placeId)?.certainty;
    }
    return undefined;
  }

  // The pin/dot a badge stands in for -- a separate element (dotMarkup)
  // carrying the SAME data-place-id/data-layer-id, but never the
  // plate-key-badge class, so `:not(.plate-key-badge)` alone tells the two
  // apart without re-deriving a selector from the id itself.
  function findPin(el: SVGGElement): SVGGElement | null {
    if (!mapEl) return null;
    const placeId = el.dataset.placeId;
    const layerId = el.dataset.layerId;
    let found: SVGGElement | null = null;
    mapEl.querySelectorAll<SVGGElement>('[data-place-id], [data-layer-id]').forEach((candidate) => {
      if (found || candidate.classList.contains('plate-key-badge')) return;
      if (placeId && candidate.dataset.placeId === placeId) found = candidate;
      else if (layerId && candidate.dataset.layerId === layerId) found = candidate;
    });
    return found;
  }

  function showTooltip(el: SVGGElement) {
    const label = el.getAttribute('aria-label') ?? '';
    const tier = badgeCertainty(el);
    tipText = tier ? `${label} (${tier})` : label;
    const frameRect = mapFrameEl?.getBoundingClientRect();
    const badgeRect = el.getBoundingClientRect();
    if (frameRect) {
      tipLeft = badgeRect.left - frameRect.left + badgeRect.width / 2;
      tipTop = badgeRect.top - frameRect.top;
    }
    tipVisible = true;
  }

  function hideTooltip() {
    tipVisible = false;
  }

  function setActiveBadge(el: SVGGElement | null) {
    activeBadgeEl?.classList.remove('plate-key-active');
    for (const row of activeRowEls) row.classList.remove('plate-key-active');
    activePinEl?.classList.remove('plate-key-active');
    activeBadgeEl = el;
    activeRowEls = [];
    activePinEl = null;
    if (!el || !mapEl) return;
    el.classList.add('plate-key-active');
    const n = el.dataset.keyN;
    if (n) {
      mapEl.querySelectorAll<SVGElement>('.plate-key-row').forEach((row) => {
        if (row.dataset.keyN === n) {
          row.classList.add('plate-key-active');
          activeRowEls.push(row);
        }
      });
    }
    activePinEl = findPin(el);
    activePinEl?.classList.add('plate-key-active');
  }

  function activateBadge(el: SVGGElement) {
    setActiveBadge(el);
    showTooltip(el);
  }

  function deactivateBadge() {
    setActiveBadge(null);
    hideTooltip();
  }

  function findBadgeByKeyN(n: string): SVGGElement | null {
    if (!mapEl) return null;
    let found: SVGGElement | null = null;
    mapEl.querySelectorAll<SVGGElement>('.plate-key-badge').forEach((b) => {
      if (!found && b.dataset.keyN === n) found = b;
    });
    return found;
  }

  // Bound directly in setupCamera (imperative addEventListener, same as
  // every other camera wiring here) rather than Svelte `on:` -- these
  // elements live inside the {@html}-injected SVG, recreated wholesale on
  // every load(), so there is nothing stale to clean up between loads.
  function wireFeatureKey() {
    if (!mapEl) return;
    mapEl.querySelectorAll<SVGGElement>('.plate-key-badge').forEach((badge) => {
      badge.setAttribute('tabindex', '0');
      badge.addEventListener('mouseenter', () => activateBadge(badge));
      badge.addEventListener('mouseleave', () => deactivateBadge());
      badge.addEventListener('focusin', () => activateBadge(badge));
      badge.addEventListener('focusout', () => deactivateBadge());
    });
    mapEl.querySelectorAll<SVGElement>('.plate-key-row').forEach((row) => {
      row.addEventListener('mouseenter', () => {
        const n = row.dataset.keyN;
        const badge = n ? findBadgeByKeyN(n) : null;
        if (badge) activateBadge(badge);
      });
      row.addEventListener('mouseleave', () => deactivateBadge());
    });
  }

  function svgFragmentFromMarkup(markup: string): Element | null {
    // Same trick Svelte's own {@html} relies on to parse a raw SVG string:
    // the HTML parser only promotes `<g>`/`<path>`/etc. into the SVG
    // namespace inside an `<svg>` integration point, so the wrapper is
    // required even though only its first child is kept. Built via
    // innerHTML on a same-document, unattached <div> -- appending the result
    // elsewhere in the SAME document needs no adoptNode.
    const scratch = document.createElement('div');
    scratch.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg">${markup}</svg>`;
    return scratch.firstElementChild?.firstElementChild ?? null;
  }

  function teardownCamera() {
    svgEl = undefined;
    clipG = undefined;
    cameraG = undefined;
    labelWrappers = [];
    camK = 1;
    camTx = 0;
    camTy = 0;
    dragPointerId = null;
    activeBadgeEl = null;
    activeRowEls = [];
    activePinEl = null;
    tipVisible = false;
  }

  // Wraps the clip-path group's children in a new inner `<g class="pp-
  // camera">` (see the doc comment above for why it can't just be the
  // clip-path element's own transform), pulls the legend out as a sibling
  // so it stays fixed, and wraps every `.plate-label` text node in its own
  // counter-scale group so labels never magnify under zoom (part 3: ships,
  // waterlines and every other drawn feature DO magnify; only text does
  // not). Re-run after every load() -- {@html} recreates the whole SVG
  // subtree on each reactive re-render, so any previous wrapping is gone.
  function setupCamera() {
    teardownCamera();
    if (!mapEl) return;
    const svg = mapEl.querySelector('svg');
    if (!svg) return;
    svgEl = svg;
    const outerG = svg.querySelector(':scope > g[clip-path]') as SVGGElement | null;
    if (!outerG) return;
    clipG = outerG;

    const legendEl = outerG.querySelector(':scope > g.plate-legend');
    const camera = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    camera.setAttribute('class', 'pp-camera');
    const children = Array.from(outerG.children);
    for (const child of children) {
      if (child === legendEl) continue;
      camera.appendChild(child);
    }
    outerG.appendChild(camera);
    if (legendEl) outerG.appendChild(legendEl);
    cameraG = camera;

    // A label's own x/y attribute is its exact anchor point (text-anchor
    // positions the glyphs relative to it); a textPath label (a river name
    // set along its channel) has no x/y at all, so its rendered bounding-box
    // centre is the next best pivot -- getBBox() is defined in the
    // element's own user space regardless of any ancestor transform, so
    // it's safe to read before or after the camera group exists.
    const wrappers: { el: SVGGElement; x: number; y: number }[] = [];
    camera.querySelectorAll<SVGTextElement>('.plate-label').forEach((textEl) => {
      const xAttr = textEl.getAttribute('x');
      const yAttr = textEl.getAttribute('y');
      let x: number;
      let y: number;
      if (xAttr !== null && yAttr !== null) {
        x = parseFloat(xAttr);
        y = parseFloat(yAttr);
      } else {
        const bbox = textEl.getBBox();
        x = bbox.x + bbox.width / 2;
        y = bbox.y + bbox.height / 2;
      }
      const wrapper = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      wrapper.setAttribute('class', 'pp-label-descale');
      textEl.parentNode?.insertBefore(wrapper, textEl);
      wrapper.appendChild(textEl);
      wrappers.push({ el: wrapper, x, y });
    });
    labelWrappers = wrappers;

    wireFeatureKey();
    applyCamera();
  }

  function updateLabelDescale() {
    const inv = 1 / camK;
    for (const { el, x, y } of labelWrappers) {
      el.setAttribute('transform', camK === 1 ? '' : `translate(${x} ${y}) scale(${inv}) translate(${-x} ${-y})`);
    }
  }

  function updateScaleBar() {
    if (!svgEl || !plateViewport) return;
    const existing = svgEl.querySelector(':scope > g.plate-scale');
    if (!existing) return;
    const markup = scaleBarMarkup({ ...plateViewport, scale: plateViewport.scale * camK }, plateSize[0], plateSize[1]);
    const fresh = markup ? svgFragmentFromMarkup(markup) : null;
    if (fresh) existing.replaceWith(fresh);
    else existing.remove();
  }

  function applyCamera() {
    if (!cameraG) return;
    cameraG.setAttribute('transform', `translate(${camTx} ${camTy}) scale(${camK})`);
    updateLabelDescale();
    updateScaleBar();
    // Tier-2 labels hidden below a zoom threshold (stage 5a, 2026-09-02):
    // minor names (Plate/PlatePlace.labelTier 2) are clutter at this
    // panel's default view — shown only once the reader is actually
    // zoomed in close. `.plate-zoomed` on the SVG ROOT (not cameraG) gates
    // a CSS rule below; 2.5 matches Reader.svelte's Chart Room postcard
    // threshold, so the two surfaces read as one behaviour.
    svgEl?.classList.toggle('plate-zoomed', camK >= 2.5);
  }

  function clampCamera(k: number, tx: number, ty: number): { k: number; tx: number; ty: number } {
    const [w, h] = plateSize;
    const kk = Math.min(CAM_MAX_K, Math.max(CAM_MIN_K, k));
    const overpanX = w * CAM_OVERPAN_FRACTION;
    const overpanY = h * CAM_OVERPAN_FRACTION;
    const minTx = w - kk * w - overpanX;
    const minTy = h - kk * h - overpanY;
    return {
      k: kk,
      tx: Math.min(overpanX, Math.max(minTx, tx)),
      ty: Math.min(overpanY, Math.max(minTy, ty)),
    };
  }

  function setCamera(k: number, tx: number, ty: number) {
    const clamped = clampCamera(k, tx, ty);
    camK = clamped.k;
    camTx = clamped.tx;
    camTy = clamped.ty;
    applyCamera();
  }

  function resetCamera() {
    setCamera(1, 0, 0);
  }

  // Client (screen) point -> the clip-path group's own local coordinate
  // space -- the space the camera's `translate/scale` is defined in, since
  // the clip-path group itself carries no transform of its own.
  function screenToWorld(clientX: number, clientY: number): { x: number; y: number } | null {
    if (!clipG || !svgEl) return null;
    const ctm = clipG.getScreenCTM();
    if (!ctm) return null;
    const pt = svgEl.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    const local = pt.matrixTransform(ctm.inverse());
    return { x: local.x, y: local.y };
  }

  // Cursor-anchored zoom: the world point under (clientX, clientY) stays
  // under the cursor after the zoom, rather than the view re-centring on the
  // plate's own centre.
  function zoomBy(factor: number, clientX?: number, clientY?: number) {
    if (!cameraG) return;
    const newK = Math.min(CAM_MAX_K, Math.max(CAM_MIN_K, camK * factor));
    let cx = clientX;
    let cy = clientY;
    if (cx === undefined || cy === undefined) {
      const rect = mapEl?.getBoundingClientRect();
      cx = rect ? rect.left + rect.width / 2 : 0;
      cy = rect ? rect.top + rect.height / 2 : 0;
    }
    const world = screenToWorld(cx, cy);
    if (!world) {
      setCamera(newK, camTx, camTy);
      return;
    }
    const localX = (world.x - camTx) / camK;
    const localY = (world.y - camTy) / camK;
    setCamera(newK, world.x - newK * localX, world.y - newK * localY);
  }

  function onWheel(e: WheelEvent) {
    if (!cameraG) return;
    e.preventDefault();
    zoomBy(Math.exp(-e.deltaY * 0.0015), e.clientX, e.clientY);
  }

  function onPointerDown(e: PointerEvent) {
    if (!cameraG || e.button !== 0) return;
    dragPointerId = e.pointerId;
    (e.currentTarget as Element).setPointerCapture(e.pointerId);
    dragStart = { x: e.clientX, y: e.clientY, tx: camTx, ty: camTy };
  }

  function onPointerMove(e: PointerEvent) {
    if (dragPointerId === null || e.pointerId !== dragPointerId || !clipG) return;
    const ctm = clipG.getScreenCTM();
    if (!ctm) return;
    const dx = (e.clientX - dragStart.x) / ctm.a;
    const dy = (e.clientY - dragStart.y) / ctm.d;
    setCamera(camK, dragStart.tx + dx, dragStart.ty + dy);
  }

  function onPointerUp(e: PointerEvent) {
    if (dragPointerId !== e.pointerId) return;
    dragPointerId = null;
  }

  function onMapKeydown(e: KeyboardEvent) {
    if (!cameraG) return;
    const step = PAN_STEP_SCREEN_PX / camK;
    switch (e.key) {
      case 'Escape':
        // Clears the numbered-key tooltip/highlight only -- never
        // preventDefault/stopPropagation, so Escape still does whatever a
        // browser or an ancestor widget expects of it (the panel's own pan/
        // zoom keys below are unaffected either way, since they're other
        // cases in this same switch).
        if (activeBadgeEl) deactivateBadge();
        break;
      case '+':
      case '=':
        e.preventDefault();
        zoomBy(ZOOM_STEP);
        break;
      case '-':
      case '_':
        e.preventDefault();
        zoomBy(1 / ZOOM_STEP);
        break;
      case '0':
      case 'Home':
        e.preventDefault();
        resetCamera();
        break;
      case 'ArrowUp':
        e.preventDefault();
        setCamera(camK, camTx, camTy + step);
        break;
      case 'ArrowDown':
        e.preventDefault();
        setCamera(camK, camTx, camTy - step);
        break;
      case 'ArrowLeft':
        e.preventDefault();
        setCamera(camK, camTx + step, camTy);
        break;
      case 'ArrowRight':
        e.preventDefault();
        setCamera(camK, camTx - step, camTy);
        break;
    }
  }

  let mapEl: HTMLDivElement | undefined;

  $: aspectRatio = `${plateSize[0]} / ${plateSize[1]}`;

  // Set only in the plate.ts (non-shield) branch of load() -- inputs
  // computeCamera needs to frame `focusIds` once the camera is set up.
  let focusPlate: Plate | undefined;
  let focusViewport: Viewport | undefined;
  let focusLabelBoxes: Record<string, LabelBox> = {};

  // 2026-09-03, stage 6 review (F3): `load` has no sequence check, so a
  // slower earlier fetch (kicked off before `plateId` changed) can resolve
  // AFTER the newer one and paint the wrong plate/camera. Not a current click
  // path (MapsPage mounts one instance per tab) but a trap for any future
  // caller that flips `plateId` on a live instance. Bump on every call;
  // ignore a completion whose generation has gone stale.
  let loadGeneration = 0;
  async function load(id: string, placesForPlate: PlatePlace[], focusIdsForPlate: string[]) {
    const generation = ++loadGeneration;
    status = 'loading';
    errorMessage = '';
    svgMarkup = '';
    unlocated = [];
    offCanvas = [];
    drawnByLayer = [];
    plateLayers = [];
    layerCategories = [];
    hasConjectural = false;
    plateViewport = undefined;
    currentPlaces = placesForPlate;
    focusPlate = undefined;
    focusViewport = undefined;
    focusLabelBoxes = {};

    try {
      const raw = await fetchPlate(id);
      // Stale completion: `plateId` moved on again while this fetch was in
      // flight, and a newer `load()` call already claimed the generation.
      // Drop this result rather than let it paint over the newer one.
      if (generation !== loadGeneration) return;
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
        plateViewport = plate.kind === 'geographic' ? result.viewport : undefined;
        unlocated = result.unlocated;
        offCanvas = result.offCanvas;
        drawnByLayer = result.drawnByLayer;
        plateLayers = plate.layers;
        const present = new Set(plate.layers.map((l) => layerCategory(l)).filter((c): c is LayerCategory => c !== null));
        layerCategories = CATEGORY_ORDER.filter((c) => present.has(c));
        categoryVisible = { relief: true, river: true, coast: true };
        // Pinned/located count only -- `drawnByLayer` places are visibly
        // drawn but never pinned, so they must not inflate this the way
        // they would if only unlocated/offCanvas were subtracted.
        const locatedCount =
          placesForPlate.length - result.unlocated.length - result.offCanvas.length - result.drawnByLayer.length;
        hasConjectural = plate.kind === 'schematic' && locatedCount > 0;
        focusPlate = plate;
        focusViewport = result.viewport;
        focusLabelBoxes = result.labelBoxes;
      }

      status = 'ready';
      await tick();
      if (generation !== loadGeneration) return;
      applyLayerVisibility();
      applyCertaintyVisibility();
      setupCamera();
      if (focusIdsForPlate.length && focusPlate && focusViewport) {
        const cam = computeCamera(focusPlate, focusViewport, focusIdsForPlate, {
          places: placesForPlate,
          labelBoxes: focusLabelBoxes,
          maxScale: CAM_MAX_K,
        });
        setCamera(cam.scale, cam.tx, cam.ty);
      }
    } catch (e) {
      // 2026-09-03, stage 6 verification: a stale REJECTION must be dropped
      // too, or an old fetch failing late paints an error over the newer load.
      if (generation !== loadGeneration) return;
      status = 'error';
      errorMessage = e instanceof Error ? e.message : String(e);
    }
  }

  // Re-fetches whenever the id, places, or focusIds changes (a mounted
  // instance switching plates, or MapsPage picking up a new `?focus=`) as
  // well as on first mount.
  $: load(plateId, places, focusIds);
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
        <div class="pp-map-frame" bind:this={mapFrameEl}>
          <!-- svelte-ignore a11y_no_noninteractive_tabindex -- role="application" is not in
               svelte's built-in "interactive roles" list (its ARIA superclass is `structure`,
               not `widget`), but this IS a custom keyboard-driven widget by design: drag to
               pan, wheel/+/- to zoom, arrow keys to pan, 0/Home to reset (see the camera
               section in the script). -->
          <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
          <div
            class="pp-map"
            style="aspect-ratio: {aspectRatio};"
            bind:this={mapEl}
            tabindex="0"
            role="application"
            aria-roledescription="Pannable, zoomable map"
            aria-label="{plateTitle || title || 'Plate'} map. Drag or use the arrow keys to pan; + and - (or the buttons below) to zoom; 0 to reset."
            on:wheel={onWheel}
            on:pointerdown={onPointerDown}
            on:pointermove={onPointerMove}
            on:pointerup={onPointerUp}
            on:pointercancel={onPointerUp}
            on:keydown={onMapKeydown}
          >
            <!-- eslint-disable-next-line svelte/no-at-html-tags -->
            {@html svgMarkup}
          </div>
          <div class="pp-cam-controls" role="group" aria-label="Zoom controls">
            <button type="button" class="pp-cam-btn" on:click={() => zoomBy(1 / ZOOM_STEP)} aria-label="Zoom out">&minus;</button>
            <button type="button" class="pp-cam-btn" on:click={resetCamera} aria-label="Reset map view">Reset</button>
            <button type="button" class="pp-cam-btn" on:click={() => zoomBy(ZOOM_STEP)} aria-label="Zoom in">+</button>
          </div>
          {#if tipVisible}
            <div class="pp-tip" role="tooltip" style="left: {tipLeft}px; top: {tipTop}px;">{tipText}</div>
          {/if}
        </div>

        {#if layerCategories.length}
          <div class="pp-toggles" role="group" aria-label="Plate layers">
            {#each layerCategories as category (category)}
              <label class="pp-toggle">
                <input
                  type="checkbox"
                  checked={categoryVisible[category] !== false}
                  on:change={(e) => toggleCategory(category, (e.currentTarget as HTMLInputElement).checked)}
                />
                Show {CATEGORY_LABEL[category]}
              </label>
            {/each}
          </div>
        {/if}

        {#if currentPlaces.length}
          <div class="pp-toggles pp-certainty-filter" role="group" aria-label="Filter by certainty">
            {#each CERTAINTY_TIERS as tier (tier)}
              <label class="pp-toggle">
                <input
                  type="checkbox"
                  checked={certaintyVisible[tier] !== false}
                  on:change={(e) => toggleCertainty(tier, (e.currentTarget as HTMLInputElement).checked)}
                />
                {tier}
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

      {#if unlocated.length || offCanvas.length || drawnByLayer.length}
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

          {#if drawnByLayer.length}
            <div class="pp-unlocated pp-drawn-by-layer">
              <h3>Drawn as part of the map ({drawnByLayer.length})</h3>
              <p class="pp-unlocated-caption">
                Carried by the map's own linework — a wall, a region — rather than by its own pin.
              </p>
              <ul>
                {#each drawnByLayer as p (p.id)}
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
  .pp-map-frame { position: relative; }
  .pp-map {
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 7px;
    background: var(--page-bg);
    /* Pan/zoom target: wheel to zoom, drag to pan, arrow keys to pan,
       +/-/0 to zoom/reset (see the camera section in the script). touch-
       action: none stops the browser's own touch-scroll/pinch from
       fighting the pointer handlers that implement panning here. */
    touch-action: none;
    cursor: grab;
  }
  .pp-map:active { cursor: grabbing; }
  .pp-map:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
  .pp-map :global(svg) { display: block; width: 100%; height: 100%; }
  /* The camera group's own contents (ships, waterlines, relief, pins) are
     meant to magnify under zoom -- only .pp-label-descale (wrapped around
     every .plate-label by setupCamera) is ever given a counter-transform. */
  .pp-map :global(.pp-camera) { will-change: transform; }
  /* Tier-2 labels (stage 5a, 2026-09-02): hidden until the panel is
     actually zoomed in (`.plate-zoomed`, toggled on the svg root by
     applyCamera at camK >= 2.5) -- a tier-2 label's own leader (plate.ts's
     leaderElement) hides with it, never left dangling. */
  .pp-map :global(svg .plate-label-tier2),
  .pp-map :global(svg .plate-leader-tier2) { display: none; }
  .pp-map :global(svg.plate-zoomed .plate-label-tier2),
  .pp-map :global(svg.plate-zoomed .plate-leader-tier2) { display: inline; }

  .pp-cam-controls {
    position: absolute;
    right: 0.5rem;
    bottom: 0.5rem;
    display: flex;
    gap: 0.3rem;
  }
  .pp-cam-btn {
    min-width: 1.9rem;
    padding: 0.25rem 0.5rem;
    font-family: var(--font-ui);
    font-size: 0.8rem;
    font-weight: 600;
    line-height: 1;
    background: var(--col-bg);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 5px;
    cursor: pointer;
  }
  .pp-cam-btn:hover { border-color: var(--accent); color: var(--accent); }
  .pp-cam-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

  /* Numbered feature key (stage 5c): tooltip is an HTML element positioned
     from the badge's own getBoundingClientRect() (see showTooltip) --
     never SVG <text>, so font/AA/tokens are the same as the rest of the
     chrome, not the map's own halo-stroked lettering. */
  .pp-tip {
    position: absolute;
    transform: translate(-50%, calc(-100% - 8px));
    max-width: 220px;
    padding: 0.3rem 0.5rem;
    font-family: var(--font-ui);
    font-size: 0.78rem;
    line-height: 1.3;
    color: var(--text);
    background: var(--col-bg);
    border: 1px solid var(--border);
    border-radius: 5px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.18);
    pointer-events: none;
    z-index: 1;
    white-space: normal;
  }
  /* Badge <-> key-row hover/focus (wireFeatureKey): a badge's own circle
     gets the accent stroke a Greek token's hover state already uses
     elsewhere in the reader; the matching key row and pin get the same
     accent, so all three read as one highlighted feature. */
  .pp-map :global(.plate-key-badge.plate-key-active circle) {
    stroke: var(--accent);
    stroke-width: 1.6;
  }
  .pp-map :global(.plate-key-badge:focus-visible) { outline: 2px solid var(--accent); outline-offset: 1px; }
  .pp-map :global(.plate-key-row.plate-key-active) { fill: var(--accent); font-weight: 600; }
  .pp-map :global([data-place-id].plate-key-active:not(.plate-key-badge) circle),
  .pp-map :global([data-layer-id].plate-key-active:not(.plate-key-badge) circle) {
    stroke: var(--accent);
    stroke-width: 2;
  }

  .pp-toggles { display: flex; flex-wrap: wrap; gap: 0.8rem; font-family: var(--font-ui); font-size: 0.8rem; color: var(--text); }
  .pp-toggle { display: flex; align-items: center; gap: 0.4rem; cursor: pointer; }
  .pp-toggle input { cursor: pointer; }
  .pp-toggle input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .pp-certainty-filter { text-transform: capitalize; }

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
