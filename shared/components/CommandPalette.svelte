<script lang="ts">
  import { onDestroy, onMount, tick } from 'svelte';
  import { parseLocation, type Scene } from '../lib/data';
  import { formatLocValue, parseVerseCitation } from '../lib/citation';
  import { getWork, workPath } from '../lib/works';
  import { rankBooks } from '../lib/palette';

  // The reader passes its already-normalized book apparatus. This deliberately
  // stays outside Reader.svelte so the token-stripped hydration path is untouched.
  export let work: string | null = null;
  export let bookNum = 1;
  export let scenes: Scene[] = [];
  export let onNavigate: ((href: string) => void) | null = null;

  const base = import.meta.env.BASE_URL.replace(/\/$/, '');

  interface Item {
    kind: 'Citation' | 'Book' | 'Scene';
    label: string;
    detail: string;
    href: string;
  }

  let open = false;
  let query = '';
  let items: Item[] = [];
  let selected = 0;
  let inputEl: HTMLInputElement | undefined;
  let boxEl: HTMLDivElement | undefined;
  let restoreEl: HTMLElement | null = null;

  function navigate(href: string) {
    close();
    if (onNavigate) onNavigate(href);
    else window.location.href = href;
  }

  export async function openPalette() {
    if (open) return;
    restoreEl = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    open = true;
    query = '';
    compute('');
    await tick();
    inputEl?.focus();
  }

  function close() {
    if (!open) return;
    open = false;
    query = '';
    items = [];
    restoreEl?.focus();
    restoreEl = null;
  }

  function sceneMatches(q: string): Scene[] {
    const needle = q.trim().toLowerCase();
    if (!needle) return [];
    return scenes.filter((scene) =>
      `${scene.summary} ${scene.place ?? ''} ${(scene.people ?? []).join(' ')}`.toLowerCase().includes(needle),
    );
  }

  function compute(raw: string) {
    const trimmed = raw.trim();
    const out: Item[] = [];
    const currentWork = work ? getWork(work) : undefined;

    // Citations resolve two ways. Verse-line works (Homer) accept an optional
    // work prefix — "Od. 9.366", "Il. 1.1" — that can name a DIFFERENT work
    // than the one currently open, enabling a cross-work jump straight from
    // the palette; a bare "9.366" still resolves in the current work's
    // context (parseVerseCitation, shared/lib/citation.ts). Any other scheme
    // (inherited siblings: bekker/busse/stephanus) has no work-prefix
    // grammar, so it falls back to the plain per-work parseLocation.
    const verseCitation = parseVerseCitation(trimmed, work ?? undefined);
    if (verseCitation) {
      const targetWork = getWork(verseCitation.work);
      if (targetWork) {
        out.push({
          kind: 'Citation',
          label: verseCitation.line != null
            ? `${targetWork.title} · Book ${verseCitation.book}, line ${verseCitation.line}`
            : `${targetWork.title} · Book ${verseCitation.book}`,
          detail: 'Citation',
          href: `${base}${workPath(verseCitation.work, verseCitation.book)}?loc=${formatLocValue(verseCitation.work, String(verseCitation.book), verseCitation.line)}`,
        });
      }
    } else if (work && currentWork) {
      const citation = parseLocation(work, trimmed);
      // Citation parsing belongs to data.ts/the work's citation scheme. For a
      // non-verse scheme, the parsed column is the book number; range-check
      // it before offering a URL.
      if (citation) {
        const targetBook = Number(citation.column);
        if (Number.isInteger(targetBook) && targetBook >= 1 && targetBook <= currentWork.books) {
          out.push({
            kind: 'Citation',
            label: citation.line != null
              ? `${currentWork.title} · Book ${targetBook}, line ${citation.line}`
              : `${currentWork.title} · Book ${targetBook}`,
            detail: 'Citation',
            href: `${base}${workPath(work, targetBook)}?loc=${formatLocValue(work, citation.column, citation.line)}`,
          });
        }
      }
    }

    // Treatment 3's ranked index is citation, then canonical book matches,
    // then scenes in THIS book. It opens on the first eight books and limits
    // typed matches to twelve, exactly as the approved mock does.
    for (const book of rankBooks(trimmed, undefined, trimmed ? 12 : 8)) {
      out.push({
        kind: 'Book',
        label: book.label,
        detail: 'Book',
        href: `${base}${workPath(book.work.id, book.book)}`,
      });
    }
    for (const scene of sceneMatches(trimmed)) {
      if (out.length >= (trimmed ? 13 : 8)) break;
      const range = scene.endLine != null ? `${scene.startLine}–${scene.endLine}` : String(scene.startLine);
      out.push({
        kind: 'Scene',
        label: `${range} — ${scene.summary}`,
        detail: `Scene · ${currentWork?.title ?? 'Current book'} ${bookNum}`,
        href: work
          ? `${base}${workPath(work, bookNum)}?loc=${formatLocValue(work, String(bookNum), scene.startLine)}`
          : '#',
      });
    }

    items = out;
    selected = 0;
  }

  function onWindowKey(e: KeyboardEvent) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (open) close();
      else openPalette();
      return;
    }
    if (open && e.key === 'Escape') { e.preventDefault(); close(); }
  }

  // aria-modal promises focus stays inside: wrap Tab within the dialog's
  // input and result buttons.
  function onBoxKey(e: KeyboardEvent) {
    if (e.key !== 'Tab' || !boxEl) return;
    const focusables = boxEl.querySelectorAll<HTMLElement>('input, button');
    if (!focusables.length) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  function onInputKey(e: KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selected = Math.min(selected + 1, items.length - 1);
      document.getElementById(`cp-item-${selected}`)?.scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selected = Math.max(selected - 1, 0);
      document.getElementById(`cp-item-${selected}`)?.scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const item = items[selected];
      if (item) navigate(item.href);
    }
  }

  function onOpenRequest() { openPalette(); }
  onMount(() => {
    window.addEventListener('open-command-palette', onOpenRequest);
    return () => window.removeEventListener('open-command-palette', onOpenRequest);
  });
  onDestroy(() => { restoreEl = null; });
</script>

<svelte:window on:keydown={onWindowKey} />

{#if open}
  <div class="cp-backdrop" on:click={(e) => { if (e.target === e.currentTarget) close(); }} role="presentation">
    <div class="cp-box" role="dialog" aria-modal="true" aria-label="Go to book, scene, or citation" tabindex="-1"
         bind:this={boxEl} on:keydown={onBoxKey}>
      <input
        class="cp-input"
        type="text"
        bind:this={inputEl}
        bind:value={query}
        on:input={(e) => compute(e.currentTarget.value)}
        on:keydown={onInputKey}
        placeholder="Book, scene, or citation (e.g. 5.239)"
        aria-label="Book, scene, or citation"
        role="combobox"
        aria-expanded={items.length > 0}
        aria-controls="cp-list"
        aria-activedescendant={items.length ? `cp-item-${selected}` : undefined}
        spellcheck="false"
        autocapitalize="off"
        autocomplete="off"
      />
      {#if items.length}
        <ul class="cp-list" id="cp-list" role="listbox">
          {#each items as item, i}
            <li role="presentation">
              <button id={`cp-item-${i}`} type="button" role="option" aria-selected={i === selected}
                      class:active={i === selected} on:click={() => navigate(item.href)} on:mousemove={() => (selected = i)}>
                <span class="cp-label">{item.label}</span>
                <span class="cp-kind">{item.detail}</span>
              </button>
            </li>
          {/each}
        </ul>
      {:else}
        <p class="cp-empty">No matches.</p>
      {/if}
      <p class="cp-status" aria-live="polite"><kbd>↑↓</kbd> select · <kbd>⏎</kbd> open · <kbd>esc</kbd> close</p>
    </div>
  </div>
{/if}

<style>
  .cp-backdrop {
    position: fixed;
    inset: 0;
    z-index: 1200;
    background: color-mix(in srgb, var(--text) 45%, transparent);
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 10vh;
  }
  .cp-box {
    width: min(92%, 34rem);
    overflow: hidden;
    background: var(--page-bg);
    border: 1px solid var(--rule-strong);
    border-radius: 10px;
    box-shadow: var(--popup-shadow);
    font-family: var(--font-ui);
  }
  .cp-input {
    box-sizing: border-box;
    width: 100%;
    border: 0;
    border-bottom: 1px solid var(--rule-strong);
    background: transparent;
    color: var(--text);
    font: inherit;
    font-size: 1rem;
    padding: 0.8rem 0.9rem;
  }
  .cp-input:focus-visible { outline-offset: -2px; }
  .cp-list { list-style: none; margin: 0; padding: 0.3rem; max-height: 20rem; overflow-y: auto; }
  .cp-list li { border-radius: 5px; }
  .cp-list button {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.6rem;
    width: 100%;
    border: 0;
    border-radius: 5px;
    background: transparent;
    color: var(--text);
    cursor: pointer;
    font: inherit;
    font-size: 0.88rem;
    padding: 0.45rem 0.6rem;
    text-align: left;
  }
  .cp-list button.active { background: var(--accent); color: var(--on-accent); }
  .cp-label { min-width: 0; }
  .cp-kind { flex: 0 0 auto; color: var(--text-mid); font-size: 0.64rem; font-variant: small-caps; letter-spacing: 0.05em; }
  .cp-list button.active .cp-kind { color: var(--on-accent); opacity: 0.8; }
  .cp-empty { color: var(--text-mid); font-family: var(--font-english); font-size: 0.82rem; font-style: italic; margin: 0; padding: 0.8rem 0.9rem; }
  .cp-status { border-top: 1px solid var(--rule-strong); color: var(--draft); font-family: var(--font-english); font-size: 0.76rem; margin: 0; min-height: 1.2em; padding: 0.5rem 0.9rem; }
  .cp-status kbd { background: var(--col-bg); border: 1px solid var(--rule-strong); border-radius: 4px; color: var(--text-mid); font: inherit; padding: 0 0.3rem; }
  @media (prefers-reduced-motion: reduce) { .cp-list { scroll-behavior: auto; } }
</style>
