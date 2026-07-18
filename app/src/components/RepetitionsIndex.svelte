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
  <div class="filters">
    <label class="filter-field" for="repetition-filter">
      <span>Find a Greek phrase</span>
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
  .repetition-index { margin-top: 1.4rem; }
  .filters { display: flex; align-items: end; flex-wrap: wrap; gap: .85rem 1.35rem; padding: .8rem 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
  .filter-field { display: grid; gap: .28rem; min-width: min(100%, 22rem); font-family: var(--font-ui); font-size: .68rem; font-variant-caps: small-caps; letter-spacing: .07em; color: var(--text-mid); }
  .filter-field input { width: 100%; min-height: 2.2rem; padding: .35rem .5rem; border: 1px solid var(--rule-strong); border-radius: 0; background: var(--input-bg); color: var(--text); font-family: var(--font-greek); font-size: 1rem; }
  .filter-field input:focus-visible, .cross-filter input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .cross-filter { display: inline-flex; align-items: center; gap: .45rem; min-height: 2.2rem; font-family: var(--font-ui); font-size: .72rem; color: var(--text); cursor: pointer; }
  .cross-filter input { accent-color: var(--accent); }
  .result-note { margin: .8rem 0; font-family: var(--font-ui); font-size: .7rem; color: var(--text-mid); }
  .rep-scroll { overflow-x: auto; padding-bottom: .45rem; }
  .rep-scroll:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .repetition-list { min-width: 34rem; list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--border); }
  .repetition-row { display: grid; grid-template-columns: minmax(17rem, 1.15fr) minmax(16rem, .85fr); gap: .55rem 1.15rem; padding: .65rem .1rem; border-bottom: 1px solid var(--border); }
  .repetition-main { display: flex; align-items: baseline; flex-wrap: wrap; gap: .38rem .55rem; min-width: 0; }
  .repetition-text { font-family: var(--font-greek); font-size: 1.08rem; line-height: 1.4; overflow-wrap: anywhere; }
  .repetition-count { font-family: var(--font-ui); font-size: .67rem; color: var(--text-mid); white-space: nowrap; }
  .cross-chip { border: 1px solid var(--accent); padding: .03rem .33rem; color: var(--accent); font-family: var(--font-ui); font-size: .61rem; font-variant-caps: small-caps; letter-spacing: .06em; white-space: nowrap; }
  .references { display: flex; align-content: start; flex-wrap: wrap; gap: .2rem .55rem; font-family: var(--font-ui); font-size: .68rem; line-height: 1.5; }
  .references a { color: var(--accent); text-decoration: none; border-bottom: 1px solid transparent; white-space: nowrap; }
  .references a:hover { border-bottom-color: var(--accent); }
  .references a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .more-refs { color: var(--text-mid); white-space: nowrap; }
  .empty-state { padding: 1.3rem 0; border-top: 1px solid var(--border); color: var(--text-mid); }
  @media (max-width: 480px) { .filters { align-items: start; } .filter-field { min-width: 100%; } }
</style>
