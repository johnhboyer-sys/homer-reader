<!-- The palette is mounted on first use (app/src/lib/goto.ts), so its styles
     ride in its own chunk and are injected when it mounts, rather than linked
     from every page's head. -->
<svelte:options css="injected" />

<script lang="ts">
  import { onDestroy, onMount, tick } from 'svelte';
  import { fetchCharacters, fetchColumns, fetchLemmata, fetchPlaces, parseLocation, type ColumnRef, type LemmaRef, type Scene } from '../lib/data';
  import { formatLocValue } from '../lib/citation';
  import { WORKS, getWork, workPath } from '../lib/works';
  import {
    SITE_PAGES, hasGreek, headwordCounts, nameEntries, rankBooks, rankLemmaSlugs, rankLemmata, rankNames, searchPath, verseCitations, withMentions,
    type SiteEntry,
  } from '../lib/palette';

  // The one Go-to of the site (round 3): the reader mounts it with its book's
  // scenes; every other page mounts it lazily from the site header
  // (app/src/lib/goto.ts) with no work, or with the poem whose index is open.
  // This deliberately stays outside Reader.svelte so the token-stripped
  // hydration path is untouched.
  export let work: string | null = null;
  export let bookNum = 0;
  export let scenes: Scene[] = [];
  export let onNavigate: ((href: string) => void) | null = null;

  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  const VERSE_WORKS = WORKS.filter((w) => w.citation?.scheme === 'verse-line');
  const bookNumbers = (n: number) => Array.from({ length: n }, (_, i) => i + 1);

  interface Item {
    kind: 'Citation' | 'Book' | 'Scene' | SiteEntry['kind'];
    label: string;
    greek?: string;
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

  // Names the palette answers to, fetched once on first open through the
  // data.ts helpers (the same files /places/ and /characters/ are built from)
  // and the lexicon's headword list on the first query that could be a word.
  // Any of them failing leaves the palette what it was: books and citations.
  let names: SiteEntry[] = SITE_PAGES;
  let namesAsked = false;
  let lemmata: Record<string, LemmaRef> | null = null;
  let lemmataAsked = false;
  const columns: Record<string, Record<string, ColumnRef[]>> = {};

  function loadNames() {
    if (namesAsked) return;
    namesAsked = true;
    try {
      Promise.all([fetchPlaces(), fetchCharacters()])
        .then(([p, c]) => {
          names = [...SITE_PAGES, ...nameEntries(p.places ?? [], Object.values(c))];
          if (lemmata) names = withMentions(names, headwordCounts(lemmata));
          if (open) compute(query, true);
        })
        .catch(() => { /* names stay the site's pages */ });
      for (const w of VERSE_WORKS) {
        fetchColumns(w.id)
          .then((c) => { columns[w.id] = c; if (open) compute(query, true); })
          .catch(() => { /* a citation is then offered unchecked, as before */ });
      }
    } catch { /* no fetch here (a test, a file:// page) */ }
  }
  function loadLemmata() {
    if (lemmataAsked) return;
    lemmataAsked = true;
    try {
      fetchLemmata()
        .then((l) => {
          lemmata = l;
          // The lexicon's counts order two names a query matches equally
          // well: "hec" is Hector (454) before Hecuba (8).
          names = withMentions(names, headwordCounts(l));
          if (open) compute(query, true);
        })
        .catch(() => { /* no word rows */ });
    } catch { /* as above */ }
  }

  // A line the book does not have is not offered, once the poem's line counts
  // are in (columns.json: book -> its first and last line). Until then, and
  // for a whole-book citation, the citation stands.
  function lineExists(workId: string, book: number, line: number | null): boolean {
    if (line == null) return true;
    const ranges = columns[workId]?.[String(book)];
    if (!ranges) return true;
    return ranges.some((r) => line >= r.lo && line <= r.hi);
  }

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
    loadNames();
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

  const KIND_LABEL: Record<SiteEntry['kind'], string> = { Page: 'Page', Place: 'Place', Character: 'Character', Word: 'Word' };

  function compute(raw: string, keepSelection = false) {
    const trimmed = raw.trim();
    const out: Item[] = [];
    const currentWork = work ? getWork(work) : undefined;

    // Citations resolve two ways. Verse-line works (Homer) accept an optional
    // work prefix ("Od. 9.366", "Il. 1.1") that can name a DIFFERENT work
    // than the one currently open; a bare "9.366" reads in the open poem
    // first and then in the other, or in both where no poem is open
    // (verseCitations, shared/lib/palette.ts, over parseVerseCitation's
    // grammar). Any other scheme (inherited siblings: bekker/busse/stephanus)
    // has no work-prefix grammar, so it falls back to the plain per-work
    // parseLocation.
    const cited = verseCitations(trimmed, work);
    if (cited.length) {
      for (const c of cited) {
        const targetWork = getWork(c.work);
        if (!targetWork || !lineExists(c.work, c.book, c.line)) continue;
        out.push({
          kind: 'Citation',
          label: c.line != null
            ? `${targetWork.title} · Book ${c.book}, line ${c.line}`
            : `${targetWork.title} · Book ${c.book}`,
          detail: 'Citation',
          href: `${base}${workPath(c.work, c.book)}?loc=${formatLocValue(c.work, String(c.book), c.line)}`,
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

    // With nothing typed the palette shows every book of both poems as a grid
    // (below), not a list. Typed: the citation, then book matches in canonical
    // order (twelve at most, six when a name also matches), then pages,
    // people, and places by name, Greek words, and the scenes of THIS book.
    if (trimmed) {
      if (hasGreek(trimmed) || trimmed.length >= 3) loadLemmata();
      const named = rankNames(trimmed, names, 6);
      const words = lemmata
        ? (hasGreek(trimmed) ? rankLemmata(trimmed, lemmata, 6) : rankLemmaSlugs(trimmed, lemmata, 3))
        : [];
      for (const book of rankBooks(trimmed, undefined, named.length || words.length ? 6 : 12)) {
        out.push({
          kind: 'Book',
          label: book.label,
          detail: 'Book',
          href: `${base}${workPath(book.work.id, book.book)}`,
        });
      }
      for (const e of named) {
        out.push({ kind: e.kind, label: e.label, greek: e.greek, detail: KIND_LABEL[e.kind], href: `${base}${e.path}` });
      }
      for (const w of words) {
        out.push({ kind: 'Word', label: w.head, detail: `Word · ${w.count}×`, href: `${base}/lemma/${w.slug}/` });
      }
      for (const scene of sceneMatches(trimmed)) {
        if (out.length >= 16) break;
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
    }

    // A late answer (names, line counts) must not move the reader off the item
    // they are on, even when it re-ranks the rows (Hector above Hecuba).
    const prev = keepSelection ? items[selected] : undefined;
    const kept = prev ? out.findIndex((it) => it.href === prev.href && it.label === prev.label) : -1;
    items = out;
    selected = kept >= 0 ? kept : keepSelection ? Math.min(selected, Math.max(out.length - 1, 0)) : 0;
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
  // input, result buttons, and links.
  function onBoxKey(e: KeyboardEvent) {
    if (e.key !== 'Tab' || !boxEl) return;
    const focusables = boxEl.querySelectorAll<HTMLElement>('input, button, a[href]');
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
      // Nothing the palette can place: Enter runs the full-text search.
      else if (query.trim()) navigate(`${base}${searchPath(query)}`);
    }
  }

  // A link inside the palette (a book of the grid, a page, the search
  // hand-off) navigates the way a result does, so a host that routes for
  // itself (onNavigate) still does.
  function onLink(e: MouseEvent, href: string) {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    navigate(href);
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
    <div class="cp-box" role="dialog" aria-modal="true" aria-label="Go to a passage, book, place, person, or word" tabindex="-1"
         bind:this={boxEl} on:keydown={onBoxKey}>
      <div class="cp-field">
        <svg class="cp-glass" width="18" height="18" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="6.8" cy="6.8" r="4.6"/><line x1="10.4" y1="10.4" x2="14" y2="14"/></svg>
        <input
          class="cp-input"
          type="text"
          bind:this={inputEl}
          bind:value={query}
          on:input={(e) => compute(e.currentTarget.value)}
          on:keydown={onInputKey}
          placeholder="6.237, Od. 9.105, Ithaca, μῆνις"
          aria-label="Go to a line, book, place, person, or Greek word"
          role="combobox"
          aria-expanded={items.length > 0}
          aria-controls="cp-list"
          aria-activedescendant={items.length ? `cp-item-${selected}` : undefined}
          spellcheck="false"
          autocapitalize="off"
          autocomplete="off"
          enterkeyhint="go"
        />
        <button type="button" class="cp-close" on:click={close} aria-label="Close">esc</button>
      </div>
      {#if items.length}
        <ul class="cp-list" id="cp-list" role="listbox">
          {#each items as item, i}
            <li role="presentation">
              <button id={`cp-item-${i}`} type="button" role="option" aria-selected={i === selected}
                      class:active={i === selected} on:click={() => navigate(item.href)} on:mousemove={() => (selected = i)}>
                <span class="cp-label">{item.label}{#if item.greek}<span class="cp-greek" lang="grc">{item.greek}</span>{/if}</span>
                <span class="cp-kind">{item.detail}</span>
              </button>
            </li>
          {/each}
        </ul>
      {:else if query.trim()}
        <p class="cp-empty">No matches.</p>
      {:else}
        <nav class="cp-books" aria-label="Every book">
          {#each VERSE_WORKS as w}
            <div class="cp-work" data-work={w.id}>
              <a class="cp-work-name" href={`${base}/${w.id}`} on:click={(e) => onLink(e, `${base}/${w.id}`)}>{w.title}</a>
              <ol class="cp-grid">
                {#each bookNumbers(w.books) as b}
                  <li><a href={`${base}${workPath(w.id, b)}`} aria-label={`${w.title}, Book ${b}`}
                         aria-current={w.id === work && b === bookNum ? 'page' : undefined}
                         on:click={(e) => onLink(e, `${base}${workPath(w.id, b)}`)}>{b}</a></li>
                {/each}
              </ol>
            </div>
          {/each}
        </nav>
        <nav class="cp-pages" aria-label="Pages of the site">
          {#each SITE_PAGES as pg}
            <a href={`${base}${pg.path}`} on:click={(e) => onLink(e, `${base}${pg.path}`)}>{pg.label}</a>
          {/each}
        </nav>
      {/if}
      <div class="cp-foot">
        {#if query.trim()}
          <a class="cp-search" href={`${base}${searchPath(query)}`} on:click={(e) => onLink(e, `${base}${searchPath(query)}`)}>Search the poems for “{query.trim()}” <span aria-hidden="true">→</span></a>
        {:else}
          <span class="cp-hint">Type a line (6.237), a name, or a Greek word</span>
        {/if}
        <p class="cp-status" aria-live="polite"><kbd>↑↓</kbd> select · <kbd>⏎</kbd> open · <kbd>esc</kbd> close</p>
      </div>
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
    width: min(92%, 38rem);
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--popup-bg, var(--page-bg));
    border: 1px solid var(--rule-strong);
    border-radius: 12px;
    box-shadow: var(--popup-shadow);
    font-family: var(--font-ui);
    text-align: left;
  }
  .cp-field {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    padding: 0 0.75rem 0 1rem;
    border-bottom: 1px solid var(--border);
    color: var(--text-mid);
  }
  .cp-glass { flex: none; }
  .cp-input {
    box-sizing: border-box;
    flex: 1 1 auto;
    min-width: 0;
    border: 0;
    background: transparent;
    color: var(--text);
    font: inherit;
    font-size: 1.0625rem;
    padding: 1rem 0;
  }
  .cp-input::placeholder { color: var(--text-mid); opacity: 1; }
  .cp-input:focus-visible { outline: none; }
  .cp-field:focus-within { box-shadow: inset 0 -2px 0 var(--accent); }
  .cp-close {
    flex: none;
    min-width: 2.75rem;
    height: 1.75rem;
    padding: 0 0.5rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--col-bg);
    color: var(--text-mid);
    font: 500 0.75rem/1 var(--font-ui);
    cursor: pointer;
  }
  .cp-close:hover { color: var(--accent); border-color: var(--accent); }

  .cp-list { list-style: none; margin: 0; padding: 0.375rem; overflow-y: auto; }
  .cp-list li { border-radius: 6px; }
  .cp-list button {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.75rem;
    width: 100%;
    min-height: 2.5rem;
    border: 0;
    border-radius: 6px;
    background: transparent;
    color: var(--text);
    cursor: pointer;
    font: inherit;
    font-size: 0.9375rem;
    line-height: 1.3;
    padding: 0.5625rem 0.75rem;
    text-align: left;
  }
  .cp-list button.active { background: var(--accent); color: var(--on-accent); }
  .cp-label { min-width: 0; }
  .cp-greek { font-family: var(--font-greek); margin-left: 0.625rem; color: var(--text-mid); }
  .cp-list button.active .cp-greek { color: var(--on-accent); }
  .cp-kind { flex: 0 0 auto; color: var(--text-mid); font-size: 0.75rem; font-weight: 500; letter-spacing: 0.02em; }
  .cp-list button.active .cp-kind { color: var(--on-accent); }
  .cp-empty { color: var(--text-mid); font-size: 0.9375rem; margin: 0; padding: 1rem; }

  /* Nothing typed: every book of both poems, one tap each. */
  .cp-books { display: grid; gap: 0.875rem; padding: 0.875rem 1rem 0.75rem; overflow-y: auto; }
  .cp-work-name {
    display: inline-block;
    font: 600 0.75rem/1 var(--font-ui);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-mid);
    text-decoration: none;
    padding: 0.25rem 0;
    margin-bottom: 0.25rem;
  }
  .cp-work[data-work="iliad"] .cp-work-name { color: var(--iliad, var(--accent)); }
  .cp-work[data-work="odyssey"] .cp-work-name { color: var(--odyssey, var(--accent)); }
  .cp-work-name:hover { text-decoration: underline; }
  .cp-grid { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 0.25rem; }
  .cp-grid a {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 2.25rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--col-bg);
    color: var(--text);
    font: 500 0.875rem/1 var(--font-ui);
    font-variant-numeric: lining-nums tabular-nums;
    text-decoration: none;
  }
  .cp-grid a:hover { border-color: var(--accent); color: var(--accent); }
  .cp-grid a[aria-current="page"] { background: var(--accent); border-color: var(--accent); color: var(--on-accent); }
  .cp-pages { display: flex; flex-wrap: wrap; gap: 0.125rem 0.25rem; padding: 0.5rem 0.625rem 0.625rem; border-top: 1px solid var(--border); }
  .cp-pages a {
    display: inline-flex;
    align-items: center;
    min-height: 2rem;
    padding: 0 0.5rem;
    border-radius: 6px;
    color: var(--text);
    font: 500 0.875rem/1 var(--font-ui);
    text-decoration: none;
  }
  .cp-pages a:hover { color: var(--accent); background: color-mix(in srgb, var(--accent) 9%, transparent); }

  .cp-foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    border-top: 1px solid var(--border);
    padding: 0.5rem 0.75rem 0.5rem 1rem;
    min-height: 2.75rem;
    box-sizing: border-box;
    background: var(--col-bg);
  }
  .cp-search { color: var(--accent); font: 600 0.875rem/1.3 var(--font-ui); text-decoration: none; min-width: 0; overflow-wrap: anywhere; padding: 0.375rem 0; }
  .cp-search:hover { text-decoration: underline; }
  .cp-hint { color: var(--text-mid); font-size: 0.8125rem; }
  .cp-status { flex: none; color: var(--text-mid); font-size: 0.75rem; margin: 0; white-space: nowrap; }
  .cp-status kbd { background: var(--popup-bg, var(--page-bg)); border: 1px solid var(--border); border-radius: 4px; color: var(--text-mid); font: inherit; padding: 0 0.3rem; }
  .cp-box a:focus-visible, .cp-close:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

  /* Phone: the box sits at the top so the book grid stays above the keyboard;
     eight books to a row keeps every number a 40px target. */
  @media (max-width: 680px) {
    .cp-backdrop { padding-top: 0.5rem; }
    .cp-box { width: calc(100% - 1rem); max-height: calc(100dvh - 1rem); }
    .cp-input { font-size: 1rem; padding: 0.875rem 0; }
    .cp-grid { grid-template-columns: repeat(8, minmax(0, 1fr)); gap: 0.25rem; }
    .cp-grid a { height: 2.5rem; font-size: 0.9375rem; }
    .cp-books { gap: 0.625rem; padding: 0.625rem 0.75rem 0.5rem; }
    .cp-pages a { min-height: 2.5rem; padding: 0 0.625rem; }
    .cp-status { display: none; }
    .cp-list button { min-height: 2.75rem; }
  }
  @media (prefers-reduced-motion: reduce) { .cp-list { scroll-behavior: auto; } }
</style>
