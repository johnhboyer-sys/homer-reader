<script lang="ts">
  import { fetchRepetitions, type Repetition } from '@shared/lib/data';
  import { filterRepetitions, isCrossEpic } from '@shared/lib/repetitions';

  export let initialEntries: Repetition[];
  export let base = '';

  let query = '';
  let crossEpicOnly = false;
  let fullEntries: Repetition[] | null = null;
  let loading = false;
  let failed = false;

  async function loadFullIndex() {
    if (fullEntries || loading) return;
    loading = true;
    failed = false;
    try {
      fullEntries = await fetchRepetitions();
    } catch {
      failed = true;
    } finally {
      loading = false;
    }
  }

  function readerHref(work: 'iliad' | 'odyssey', book: number, line: number): string {
    return `${base}/${work}/book/${book}/?loc=${book}.${line}`;
  }

  $: entries = fullEntries ?? initialEntries;
  $: visibleEntries = filterRepetitions(entries, query, crossEpicOnly);
  $: showingFullIndex = fullEntries !== null;
  $: refLimit = showingFullIndex ? 5 : 1;
</script>

<section class="repetition-index" aria-label="Repeated lines and phrases">
  <div class="pg-bar filters">
    <label class="filter-field" for="repetition-filter">
      <span class="filter-label">Find a Greek phrase</span>
      <input
        id="repetition-filter"
        type="search"
        bind:value={query}
        on:input={loadFullIndex}
        placeholder="Type Greek text"
        autocomplete="off"
      />
    </label>
    <label class="cross-filter">
      <input type="checkbox" bind:checked={crossEpicOnly} />
      <span>Cross-epic only</span>
    </label>
  </div>

  <p class="result-note" aria-live="polite">
    {#if loading}
      Loading the full index…
    {:else if failed}
      The full index could not load; showing the leading 300 entries.
    {:else if showingFullIndex}
      {visibleEntries.length} matching {visibleEntries.length === 1 ? 'entry' : 'entries'} in the full index.
    {:else}
      Showing the 300 most frequent entries. Start typing to search all 4,390.
    {/if}
  </p>

  {#if visibleEntries.length}
    <div class="rep-scroll" tabindex="0" role="group" aria-label="Repeated lines and phrases, scrollable on narrow screens">
      <ol class="repetition-list">
        {#each visibleEntries as entry (entry.key)}
          <li class="repetition-row">
            <div class="repetition-main">
              <span class="repetition-text" lang="grc">{entry.text}</span>
              <span class="repetition-count">{entry.count}×</span>
              {#if isCrossEpic(entry)}<span class="cross-chip">Il+Od</span>{/if}
            </div>
            <div class="references" aria-label={`Occurrences of ${entry.text}`}>
              {#each entry.refs.slice(0, refLimit) as ref}
                <a href={readerHref(ref.work, ref.book, ref.line)}>{ref.work === 'iliad' ? 'Il.' : 'Od.'} {ref.book}.{ref.line}</a>
              {/each}
              {#if entry.count > refLimit}<span class="more-refs">+{entry.count - refLimit} more</span>{/if}
            </div>
          </li>
        {/each}
      </ol>
    </div>
  {:else}
    <p class="empty-state">No repeated phrase matches those filters.</p>
  {/if}
</section>

<style>
  /* The filter row is the shared sticky bar (.pg-bar, edition-pages.css);
     these rules set what sits in it and the rows under it. */
  .repetition-index { margin-top: 0; }
  .filters { flex-wrap: wrap; }
  .filter-field { display: flex; align-items: center; gap: 0.75rem; flex: 1 1 24rem; max-width: 34rem; min-width: 0; }
  .filter-label { flex: none; font: 600 var(--step--1)/1 var(--font-ui); color: var(--text-mid); }
  .filter-field input { flex: 1 1 auto; min-width: 0; height: 2.5rem; padding: 0 1rem; border: 1px solid var(--edge-ui); border-radius: var(--radius-pill); background: var(--input-bg); color: var(--text); font-family: var(--font-greek); font-size: 1.125rem; }
  .filter-field input::placeholder { font: 500 0.9375rem/1 var(--font-ui); color: var(--text-light); opacity: 1; }
  .filter-field input:focus-visible { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 18%, transparent); }
  .cross-filter input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .cross-filter { display: inline-flex; align-items: center; gap: 0.5rem; min-height: 2.5rem; padding: 0 0.875rem; border: 1px solid var(--border); border-radius: var(--radius-pill); background: var(--col-bg); font: 600 var(--step--1)/1 var(--font-ui); color: var(--text); cursor: pointer; white-space: nowrap; }
  .cross-filter:hover { border-color: var(--accent); }
  .cross-filter input { width: 1rem; height: 1rem; margin: 0; accent-color: var(--accent); }
  .result-note { margin: var(--space-4) 0 var(--space-3); font: 500 var(--step--1)/1.4 var(--font-ui); color: var(--text-mid); }
  .rep-scroll { min-width: 0; }
  .rep-scroll:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .repetition-list { list-style: none; margin: 0; padding: 0; border-top: 2px solid var(--text); }
  .repetition-row { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr); gap: 0.375rem var(--space-6); align-items: baseline; padding: 0.875rem 0; border-bottom: 1px solid var(--border); }
  .repetition-main { display: flex; align-items: baseline; flex-wrap: wrap; gap: 0.25rem 0.75rem; min-width: 0; }
  .repetition-text { font-family: var(--font-greek); font-size: 1.3125rem; line-height: 1.4; color: var(--text); overflow-wrap: anywhere; }
  .repetition-count { font: 600 var(--step--1)/1 var(--font-ui); font-variant-numeric: tabular-nums; color: var(--text-mid); white-space: nowrap; }
  .cross-chip { padding: 0.1875rem 0.5rem; border: 1px solid var(--accent); border-radius: var(--radius-pill); font: 600 var(--step--2)/1 var(--font-ui); letter-spacing: 0.02em; color: var(--accent); white-space: nowrap; }
  .references { display: flex; align-content: start; align-items: baseline; flex-wrap: wrap; gap: 0.25rem 0.875rem; font: 600 var(--step--1)/1.5 var(--font-ui); font-variant-numeric: tabular-nums; }
  .references a { color: var(--accent); text-decoration: none; white-space: nowrap; }
  .references a:hover { text-decoration: underline; text-underline-offset: 0.2em; }
  .references a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .more-refs { font-weight: 500; color: var(--text-mid); white-space: nowrap; }
  .empty-state { padding: var(--space-6) 0; border-top: 2px solid var(--text); font-size: 1.0625rem; color: var(--text-mid); }
  @media (max-width: 760px) {
    /* On a phone the field's placeholder stands in for its label, which stays
       in the tree for assistive tech; the row then fits on one line. */
    .filter-field { flex: 1 1 0; max-width: none; }
    .filter-label { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
    .filters { flex-wrap: nowrap; gap: var(--space-2); }
    .cross-filter { padding: 0 0.75rem; }
    /* A phone row is the phrase, then one line of its count and places: the
       count no longer drops to a line of its own when the phrase fills the
       measure, and every row has the same two-part shape. */
    .repetition-row { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.375rem 0.75rem; }
    .repetition-main, .references { display: contents; }
    .repetition-text { flex: 1 1 100%; }
    .repetition-text { font-size: 1.25rem; }
  }
</style>
