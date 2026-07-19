<script lang="ts">
  import { lookupWord, fetchLemmata, type Analysis, type LsjEntry, type CunliffeEntry, type LemmaRef } from '../lib/data';
  import { betaToGreek } from '../lib/betacode';
  import { workPath } from '../lib/works';
  import { formatLocValue } from '../lib/citation';

  // The shared BODY of the word lookup, rendered identically inside the docked
  // desktop lexicon rail AND the anchored mobile popup (WordPopup). It owns the
  // single entry-fetch (lookupWord) and the dictionary presentation — headword,
  // short gloss, the EXPAND disclosure to the full LSJ/Cunliffe entry, and the
  // LSJ · Cunliffe · Logeion tab row — so neither presentation duplicates it
  // (DESIGN.md 2026-07-17: "one source of truth for the entry-fetch logic").
  export let work: string = 'EN';
  export let token: { t: string; k: string };
  // Whether this body is rendered inside the DESKTOP docked lexicon rail (true)
  // vs the anchored mobile popup (false). The docked rail has room to surface the
  // LSJ · Cunliffe · Logeion tab row upfront, so the gloss is anchored to the
  // dictionary structure instead of floating in an empty rail (punch-list #12,
  // 2026-07-18). The compact mobile popup stays collapsed for scannability.
  export let docked: boolean = false;

  let panelEl: HTMLDivElement;
  let analyses: Analysis[] = [];
  let lsj: LsjEntry[] = [];
  let cunliffe: CunliffeEntry[] = [];
  let loading = true;
  let error = '';
  // LSJ default; Cunliffe is the second native lexicon pane; Logeion (a plain
  // external link, not a real panel) rides the same tab row — see below.
  let activeTab: 'lsj' | 'cunliffe' = 'lsj';
  // The definition shows the short gloss first; the full dictionary entry
  // (LSJ/Cunliffe HTML) is revealed IN PLACE behind an EXPAND control, and is
  // collapsible (DESIGN.md 2026-07-17). In the docked desktop rail it opens
  // expanded so the LSJ · Cunliffe · Logeion tabs are surfaced upfront (#12);
  // the mobile popup opens closed so it stays scannable. Nothing here opens a
  // new tab except the Logeion link.
  let expanded = docked;

  lookupWord(work, token.k)
    .then(r => { analyses = r.analyses; lsj = r.lsj; cunliffe = r.cunliffe; })
    .catch(e => { error = String(e); })
    .finally(() => { loading = false; });

  // The lemma-page manifest (loaded once, cached): lets each analysis card offer
  // a "see all N occurrences" link into /lemma/<slug>, but only for lemmata that
  // actually have a page. Absent manifest = no links, panel unchanged.
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  let lemmata: Record<string, LemmaRef> = {};
  fetchLemmata().then(m => { lemmata = m; }).catch(() => {});
  const lemmaRef = (a: Analysis): LemmaRef | null =>
    (a.lsj[0] && lemmata[a.lsj[0]]) || null;

  // Logeion (logeion.uchicago.edu) looks up by headword, not inflected surface
  // form — use the primary analysis's resolved LSJ head (matching the first
  // card's lemma display), falling back to the raw lemma transliteration, or the
  // clicked surface form if nothing resolved yet.
  $: primaryHead = analyses[0]
    ? (analyses[0].lsj[0]
        ? lsj.find(e => e.key === analyses[0].lsj[0])?.head ?? betaToGreek(analyses[0].lemma)
        : betaToGreek(analyses[0].lemma))
    : token.t;
  $: logeionHref = `https://logeion.uchicago.edu/${encodeURIComponent(primaryHead)}`;

  // A Cunliffe entry's HTML embeds internal citation links as
  // <a class="cunliffe-cite" data-work data-book data-line> markers rather than
  // baked hrefs (BASE_URL is only known client-side). Resolve the destination
  // here, in-place navigation (same tab), the way BekkerJump/CommandPalette do.
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

  // Minimal ARIA-tabs keyboard support: left/right moves selection AND focus
  // between the two real tabs (LSJ, Cunliffe). The Logeion item is a plain
  // external link, not a tab panel, so it isn't in this cycle — it stays
  // reachable via normal Tab order.
  const TAB_ORDER: Array<'lsj' | 'cunliffe'> = ['lsj', 'cunliffe'];
  function onTabRowKey(e: KeyboardEvent) {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    e.preventDefault();
    const i = TAB_ORDER.indexOf(activeTab);
    const next = e.key === 'ArrowRight'
      ? TAB_ORDER[(i + 1) % TAB_ORDER.length]
      : TAB_ORDER[(i - 1 + TAB_ORDER.length) % TAB_ORDER.length];
    activeTab = next;
    panelEl?.querySelector<HTMLElement>(`#dict-tab-${next}`)?.focus();
  }
</script>

<div class="lexicon-panel" bind:this={panelEl}>
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
            Appears {lemmaRef(a)!.count.toLocaleString()}× across Homer
            <span class="lemma-link-arr" aria-hidden="true">→</span>
          </a>
        {/if}
      </div>
    {/each}

    <button
      type="button"
      class="lex-expand"
      aria-expanded={expanded}
      aria-controls="dict-section"
      on:click={() => (expanded = !expanded)}
    >
      <span class="lex-expand-caret" class:open={expanded} aria-hidden="true">▸</span>
      {expanded ? 'Hide full dictionary entry' : 'Expand full dictionary entry'}
    </button>

    {#if expanded}
      <div class="dict-section" id="dict-section">
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
               switch. It stays reachable via normal Tab order (a[href]) and is
               the ONE control here that opens a new tab. -->
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
  {/if}
</div>

<style>
  .lexicon-panel { display: flex; flex-direction: column; gap: 0.75rem; }

  /* EXPAND disclosure to the full dictionary entry — a quiet, full-width control
     between the short gloss and the (revealed) tabbed entry. Uses the Aegean
     bronze accent, like the other reader labels; AA in both themes. */
  .lex-expand {
    display: inline-flex; align-items: center; gap: 0.4em;
    align-self: flex-start;
    padding: 0.3rem 0.1rem;
    background: none; border: none; cursor: pointer;
    font-family: var(--font-ui); font-size: 0.82rem; font-weight: 600;
    color: var(--accent);
  }
  .lex-expand:hover { color: var(--accent-light); text-decoration: underline; }
  .lex-expand:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 3px; }
  .lex-expand-caret { transition: transform .12s ease; font-size: 0.72em; }
  .lex-expand-caret.open { transform: rotate(90deg); }

  /* "See all occurrences" link into the lemma page — the panel's one bridge to
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
