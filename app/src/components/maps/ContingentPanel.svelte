<script lang="ts">
  // The Ships/Catalogue explorer's side panel: sort toggles + a fully
  // keyboard-operable list of contingents, plus the detail block for whichever
  // contingent is selected (leaders, ship count, toponyms, reader deep link).
  // Independent of the map — every control here is a real <button>, so Tab +
  // Enter/Space (and ArrowUp/ArrowDown as a roving-focus convenience) work
  // with no mouse, satisfying "the contingent PANEL must be fully
  // keyboard-operable even if map pins are mouse-first" (CLAUDE.md brief).
  import {
    sortContingents,
    leaderDisplayName,
    contingentLocValue,
    type Contingent,
    type Place,
    type CharacterRef,
    type CatalogueSort,
  } from '@shared/lib/maps';
  import { workPath } from '@shared/lib/works';
  import { formatLocValue } from '@shared/lib/citation';

  export let base: string;
  export let contingents: Contingent[];
  export let placesById: Map<string, Place>;
  export let charactersById: Map<string, CharacterRef>;
  export let selectedId: string | null;
  export let sort: CatalogueSort;
  export let showShips = true;
  export let readerWork = 'iliad';
  export let readerBook = 2;
  export let onSelect: (id: string) => void;
  export let onSortChange: (mode: CatalogueSort) => void;

  const SORTS: { id: CatalogueSort; label: string }[] = [
    { id: 'catalogue', label: 'Catalogue order' },
    { id: 'ships-desc', label: 'Ships ↓' },
    { id: 'alpha', label: 'A–Z' },
  ];

  $: sorted = sortContingents(contingents, sort);
  $: selected = sorted.find((c) => c.id === selectedId) ?? null;
  $: readerHref = selected
    ? `${base}${workPath(readerWork, readerBook)}?loc=${formatLocValue(readerWork, String(readerBook), selected.lines[0])}`
    : null;

  let listEl: HTMLDivElement;
  function moveFocus(delta: number) {
    const buttons = Array.from(listEl.querySelectorAll<HTMLButtonElement>('button[role="option"]'));
    const i = buttons.findIndex((b) => b === document.activeElement);
    const next = buttons[Math.min(Math.max(i + delta, 0), buttons.length - 1)];
    next?.focus();
  }
  function onListKeydown(e: KeyboardEvent) {
    if (e.key === 'ArrowDown') { e.preventDefault(); moveFocus(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); moveFocus(-1); }
    else if (e.key === 'Home') { e.preventDefault(); moveFocus(-Infinity); }
    else if (e.key === 'End') { e.preventDefault(); moveFocus(Infinity); }
  }
</script>

<div class="cp-panel">
  <div class="cp-sort" role="group" aria-label="Sort contingents">
    {#each SORTS as s}
      <button
        type="button"
        class="cp-sort-btn"
        aria-pressed={sort === s.id}
        on:click={() => onSortChange(s.id)}
      >{s.label}</button>
    {/each}
  </div>

  <div
    class="cp-list"
    role="listbox"
    aria-label="Contingents"
    bind:this={listEl}
    on:keydown={onListKeydown}
  >
    {#each sorted as c (c.id)}
      <button
        type="button"
        role="option"
        aria-selected={c.id === selectedId}
        class="cp-row"
        class:selected={c.id === selectedId}
        on:click={() => onSelect(c.id)}
      >
        <span class="cp-row-name">{c.name}</span>
        <span class="cp-row-ships">{showShips && c.ships != null ? `${c.ships} ships` : '—'}</span>
      </button>
    {/each}
  </div>

  <div class="cp-detail" aria-live="polite">
    {#if selected}
      <h3 class="cp-detail-name">{selected.name}</h3>
      <dl class="cp-detail-facts">
        <dt>Ships</dt>
        <dd>{selected.ships != null ? selected.ships : 'None counted (Homer gives no ship tally for this contingent)'}</dd>
        <dt>Leaders</dt>
        <dd>
          {#each selected.leaders as id, i}
            {@const ld = leaderDisplayName(id, charactersById)}<span class="cp-leader" class:unknown={!ld.known}>{ld.name}</span>{i < selected.leaders.length - 1 ? ', ' : ''}
          {/each}
        </dd>
        <dt>Toponyms</dt>
        <dd class="cp-toponyms">
          {#each selected.places as id, i}
            {@const p = placesById.get(id)}<span class="cp-toponym" class:no-coords={!p?.coords}>{p?.name ?? id}</span>{i < selected.places.length - 1 ? ', ' : ''}
          {/each}
        </dd>
      </dl>
      {#if selected.note}<p class="cp-detail-note">{selected.note}</p>{/if}
      {#if readerHref}
        <a class="cp-detail-link" href={readerHref}>Read this entry in the Catalogue &rarr;</a>
      {/if}
    {:else}
      <p class="cp-detail-empty">Select a contingent to see its leaders, ship count, and toponyms.</p>
    {/if}
  </div>
</div>

<style>
  .cp-panel {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    font-family: var(--font-ui);
    color: var(--text);
  }

  .cp-sort { display: flex; flex-wrap: wrap; gap: 0.35rem; }
  .cp-sort-btn {
    padding: 0.3rem 0.6rem;
    font-family: var(--font-ui);
    font-size: 0.76rem;
    font-weight: 600;
    background: var(--col-bg);
    color: var(--text-mid);
    border: 1px solid var(--border);
    border-radius: 999px;
    cursor: pointer;
  }
  .cp-sort-btn[aria-pressed="true"] { background: var(--accent); color: var(--on-accent); border-color: var(--accent); }
  .cp-sort-btn:hover:not([aria-pressed="true"]) { border-color: var(--accent); color: var(--accent); }
  .cp-sort-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

  .cp-list {
    max-height: 260px;
    overflow-y: auto;
    border: 1px solid var(--border);
    border-radius: 6px;
  }
  .cp-row {
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    width: 100%;
    padding: 0.4rem 0.6rem;
    background: var(--col-bg);
    color: var(--text);
    border: none;
    border-bottom: 1px solid var(--border);
    font-family: var(--font-ui);
    font-size: 0.84rem;
    text-align: left;
    cursor: pointer;
  }
  .cp-list .cp-row:last-child { border-bottom: none; }
  .cp-row:hover { background: var(--greek-hover); }
  .cp-row.selected { background: var(--accent); color: var(--on-accent); }
  .cp-row:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
  .cp-row-ships { color: var(--text-mid); white-space: nowrap; }
  .cp-row.selected .cp-row-ships { color: var(--on-accent); opacity: 0.85; }

  .cp-detail {
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.7rem 0.8rem;
    background: var(--col-bg);
    min-height: 4rem;
  }
  .cp-detail-name { margin: 0 0 0.4rem; font-family: var(--font-display); font-size: 1.05rem; }
  .cp-detail-facts { margin: 0; font-size: 0.82rem; }
  .cp-detail-facts dt { color: var(--text-mid); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.5rem; }
  .cp-detail-facts dd { margin: 0.1rem 0 0; }
  .cp-leader.unknown { color: var(--text-mid); font-style: italic; }
  .cp-toponym.no-coords { color: var(--text-mid); }
  .cp-detail-note { margin: 0.6rem 0 0; font-size: 0.8rem; color: var(--text-mid); font-style: italic; }
  .cp-detail-link {
    display: inline-block;
    margin-top: 0.6rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--accent);
    text-decoration: none;
  }
  .cp-detail-link:hover { text-decoration: underline; }
  .cp-detail-empty { margin: 0; font-size: 0.82rem; color: var(--text-mid); }
</style>
