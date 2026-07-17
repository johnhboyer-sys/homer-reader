<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { fly } from 'svelte/transition';
  import { lookupWord, fetchLemmata, type Analysis, type LsjEntry, type CunliffeEntry, type LemmaRef } from '../lib/data';
  import { betaToGreek } from '../lib/betacode';
  import { workPath } from '../lib/works';
  import { formatLocValue } from '../lib/citation';

  export let work: string = 'EN';
  export let token: { t: string; k: string };
  export const anchor: { x: number; y: number } = { x: 0, y: 0 };
  export let onClose: () => void;
  // Compare mode packs three columns into the reading measure; on a tablet the
  // right-margin reserve would crush them, so there the panel drops to a bottom
  // sheet (like the phone layout) and the text keeps full width. See the
  // .word-sidebar.as-sheet block in global.css.
  export let asSheet: boolean = false;

  let dialogEl: HTMLDivElement;
  let previousFocus: HTMLElement | null = null;
  let analyses: Analysis[] = [];
  let lsj: LsjEntry[] = [];
  let cunliffe: CunliffeEntry[] = [];
  let loading = true;
  let error = '';
  // LSJ default; Cunliffe is the second native lexicon pane; Logeion (a plain
  // link, not a real panel) lives in the same tab row — see the markup below.
  let activeTab: 'lsj' | 'cunliffe' = 'lsj';
  // Resolved synchronously at instantiation (this component only ever mounts
  // client-side, on a word click) so the intro transition picks the right
  // direction: mobile rises from the bottom, desktop slides in from the right.
  // Reading it in onMount would be too late — Svelte evaluates transition
  // params when the element mounts, before onMount runs.
  const isMobile = typeof window !== 'undefined'
    && window.matchMedia('(max-width: 680px)').matches;
  // Whether we render as a bottom sheet: always on phones, and on tablets when
  // the caller is in compare mode (asSheet) — matches the CSS in global.css.
  const asSheetHere = typeof window !== 'undefined'
    && (isMobile || (asSheet && window.matchMedia('(min-width: 681px) and (max-width: 1100px)').matches));
  // Honour the OS "reduce motion" setting: the fly-in is decorative, so collapse
  // it to an instant appearance. (The CSS @media query can't reach Svelte's JS
  // transitions, so it's gated here too.)
  const reduceMotion = typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  lookupWord(work, token.k)
    .then(r => { analyses = r.analyses; lsj = r.lsj; cunliffe = r.cunliffe; })
    .catch(e => { error = String(e); })
    .finally(() => { loading = false; });

  // The lemma-page manifest (loaded once, cached): lets each analysis card offer
  // a "see all N occurrences" link into /lemma/<slug>, but only for lemmata that
  // actually have a page. Absent manifest = no links, popup unchanged.
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  let lemmata: Record<string, LemmaRef> = {};
  fetchLemmata().then(m => { lemmata = m; }).catch(() => {});
  // A card's lemma page keys off its primary LSJ key (matching the concordance).
  const lemmaRef = (a: Analysis): LemmaRef | null =>
    (a.lsj[0] && lemmata[a.lsj[0]]) || null;

  // Logeion (logeion.uchicago.edu) looks up by headword, not by inflected
  // surface form — use the primary analysis's resolved LSJ head (matching the
  // first analysis card's own lemma display), falling back to the raw lemma
  // transliteration, or the clicked surface form if nothing resolved yet.
  $: primaryHead = analyses[0]
    ? (analyses[0].lsj[0]
        ? lsj.find(e => e.key === analyses[0].lsj[0])?.head ?? betaToGreek(analyses[0].lemma)
        : betaToGreek(analyses[0].lemma))
    : token.t;
  $: logeionHref = `https://logeion.uchicago.edu/${encodeURIComponent(primaryHead)}`;

  function onKey(e: KeyboardEvent) {
    if (e.key === 'Escape') onClose();
  }

  // A Cunliffe entry's HTML embeds internal citation links as
  // <a class="cunliffe-cite" data-work data-book data-line> markers rather
  // than baked hrefs (the reader's BASE_URL is only known client-side — see
  // pipeline/homer_pipeline/stage5_cunliffe.py's linkify_definition
  // docstring). Resolve the real destination here, the same way
  // BekkerJump.svelte and CommandPalette.svelte do for their own jump links.
  function onCunliffeClick(e: MouseEvent) {
    const target = (e.target as HTMLElement).closest('a.cunliffe-cite') as HTMLElement | null;
    if (!target) return;
    e.preventDefault();
    const w = target.dataset.work;
    const book = Number(target.dataset.book);
    const line = Number(target.dataset.line);
    if (!w || !book || !line) return;
    window.location.href = `${base}${workPath(w, book)}?loc=${formatLocValue(w, String(book), line)}`;
  }

  // Minimal ARIA-tabs keyboard support: left/right arrow moves both selection
  // and focus between the two real tabs (LSJ, Cunliffe). The Logeion item is
  // a plain external link, not a tab panel, so it isn't part of this cycle —
  // it's still reachable in sequence via the popup's own Tab-key focus trap
  // (onDialogKey below), which already treats it as a normal `a[href]`.
  const TAB_ORDER: Array<'lsj' | 'cunliffe'> = ['lsj', 'cunliffe'];
  function onTabRowKey(e: KeyboardEvent) {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    e.preventDefault();
    const i = TAB_ORDER.indexOf(activeTab);
    const next = e.key === 'ArrowRight'
      ? TAB_ORDER[(i + 1) % TAB_ORDER.length]
      : TAB_ORDER[(i - 1 + TAB_ORDER.length) % TAB_ORDER.length];
    activeTab = next;
    dialogEl?.querySelector<HTMLElement>(`#dict-tab-${next}`)?.focus();
  }

  function focusableEls(): HTMLElement[] {
    return dialogEl
      ? Array.from(dialogEl.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        )).filter((el) => !el.hasAttribute('disabled') && el.tabIndex !== -1)
      : [];
  }

  function onDialogKey(e: KeyboardEvent) {
    if (e.key !== 'Tab') return;
    const els = focusableEls();
    if (els.length === 0) {
      e.preventDefault();
      dialogEl?.focus();
      return;
    }
    const first = els[0];
    const last = els[els.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  onMount(() => {
    previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setTimeout(() => dialogEl?.focus(), 0);
  });

  onDestroy(() => {
    previousFocus?.focus();
  });
</script>

<svelte:window on:keydown={onKey} />

<div class="popup-backdrop" on:click={onClose} on:keydown={() => {}} role="presentation"></div>

<!-- Desktop: slide-in sidebar. Mobile / tablet-compare: bottom sheet. Both via CSS. -->
<div
  class="word-sidebar"
  class:as-sheet={asSheet}
  bind:this={dialogEl}
  transition:fly={reduceMotion ? { duration: 0 } : asSheetHere ? { y: 600, duration: 260, opacity: 1 } : { x: 420, duration: 220, opacity: 1 }}
  role="dialog"
  aria-label="Word analysis"
  aria-modal="true"
  tabindex="-1"
  on:keydown={onDialogKey}
>
  <div class="word-sidebar-head">
    <span class="popup-surface" lang="grc">{token.t}</span>
    <button class="settings-close" on:click={onClose} aria-label="Close">×</button>
  </div>
  <div class="word-sidebar-body">
    {#if loading}
      <div class="popup-loading">Looking up…</div>
    {:else if error}
      <div class="popup-loading">Error: {error}</div>
    {:else if analyses.length === 0}
      <div class="popup-loading">No analysis found for this form.</div>
    {:else}
      {#each analyses as a}
        <div class="analysis-card">
          <div class="lemma" lang="grc">{a.lsj[0] ? lsj.find(e => e.key === a.lsj[0])?.head ?? betaToGreek(a.lemma) : betaToGreek(a.lemma)}</div>
          <div class="gloss">{a.gloss}</div>
          <div class="parse">{a.parse}</div>
          {#if lemmaRef(a)}
            <a class="lemma-link" href={`${base}/lemma/${lemmaRef(a)!.slug}/`}>
              Appears {lemmaRef(a)!.count.toLocaleString()}× across Plato
              <span class="lemma-link-arr" aria-hidden="true">→</span>
            </a>
          {/if}
        </div>
      {/each}
      <div class="dict-section">
        <div class="dict-tabs">
          <div class="dict-tablist" role="tablist" aria-label="Dictionary" tabindex="-1" on:keydown={onTabRowKey}>
            <button
              type="button"
              role="tab"
              id="dict-tab-lsj"
              aria-selected={activeTab === 'lsj'}
              aria-controls="dict-panel-lsj"
              tabindex={activeTab === 'lsj' ? 0 : -1}
              class="dict-tab"
              on:click={() => (activeTab = 'lsj')}
            >LSJ</button>
            <button
              type="button"
              role="tab"
              id="dict-tab-cunliffe"
              aria-selected={activeTab === 'cunliffe'}
              aria-controls="dict-panel-cunliffe"
              tabindex={activeTab === 'cunliffe' ? 0 : -1}
              class="dict-tab"
              on:click={() => (activeTab = 'cunliffe')}
            >Cunliffe</button>
          </div>
          <!-- Not part of the tablist: role="tablist" only permits role="tab"
               children, and this is a real external navigation, not a panel
               switch. It stays reachable via the popup's normal Tab-key
               focus order (see focusableEls' a[href] selector). -->
          <a
            class="dict-tab dict-tab-link"
            href={logeionHref}
            target="_blank"
            rel="noopener"
          >Logeion <span aria-hidden="true">↗</span></a>
        </div>
        <div id="dict-panel-lsj" role="tabpanel" aria-labelledby="dict-tab-lsj" tabindex="0" hidden={activeTab !== 'lsj'}>
          {#if lsj.length > 0}
            {#each lsj as entry}
              <div class="lsj-entry">
                <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                {@html entry.html}
              </div>
            {/each}
          {:else}
            <div class="popup-loading">Not in LSJ.</div>
          {/if}
        </div>
        <div id="dict-panel-cunliffe" role="tabpanel" aria-labelledby="dict-tab-cunliffe" tabindex="0" hidden={activeTab !== 'cunliffe'} on:click={onCunliffeClick} on:keydown={() => {}}>
          {#if cunliffe.length > 0}
            {#each cunliffe as entry}
              <div class="cunliffe-entry">
                <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                {@html entry.html}
              </div>
            {/each}
          {:else}
            <div class="popup-loading">Not in Cunliffe.</div>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  /* "See all occurrences" link into the lemma page — the popup's one bridge to
     the deeper reference view. Sits at the foot of each analysis card. */
  .lemma-link {
    display: inline-flex; align-items: center; gap: 0.35em;
    margin-top: 0.5rem; font-family: var(--font-ui); font-size: 0.8rem;
    font-weight: 600; color: var(--accent); text-decoration: none;
  }
  .lemma-link:hover { text-decoration: underline; }
  .lemma-link-arr { transition: transform .1s ease; }
  .lemma-link:hover .lemma-link-arr { transform: translateX(2px); }
</style>
