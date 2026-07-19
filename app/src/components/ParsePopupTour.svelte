<script lang="ts">
  // A 5-step dismissible walkthrough for readers arriving via the /start
  // funnel's "Reading along in Greek" door (see app/src/pages/start/index.astro
  // and app/src/pages/index.astro's Greek door, both of which append
  // `&tour=parse` to the destination URL). Mounted once, globally, in
  // ReaderShell.astro — it only ever renders when that query param is present
  // AND the tour hasn't already been dismissed, so it never intrudes on a
  // normal reading session or a bookmarked link visited a second time.
  //
  // Deliberately independent of HelpButton.svelte's existing "first reader
  // visit" tip (a different, generic one-shot toast keyed by `ar-help-seen`
  // that fires for ANY new visitor on ANY door): this component is gated on
  // the funnel referral itself, not on visit recency, and covers five points
  // instead of one. No external library — plain Svelte state, same modal/
  // focus-trap pattern as HelpButton's help modal.
  //
  // With JavaScript disabled this component never hydrates, so nothing
  // renders and the reading surface (already fully server-rendered) is
  // unaffected — the tour is a pure enhancement.
  import { onMount, onDestroy, tick } from 'svelte';

  const DISMISSED_KEY = 'homer-parse-tour-dismissed';

  const STEPS: { title: string; body: string }[] = [
    {
      title: 'Reading the Greek, side by side',
      body: 'You’re looking at the original Greek with an English translation alongside it. A few things here aren’t obvious — this is a 30-second tour.',
    },
    {
      title: 'Click any Greek word',
      body: 'Click (or tap) a word in the Greek column and a popup opens with its dictionary form, grammatical parse, and full LSJ and Cunliffe entries — without leaving the page.',
    },
    {
      title: 'Choose your view',
      body: 'The view buttons (or ⚙ Settings on a phone) switch between Greek only, English only, or both side by side, and pick which translation fills the English column.',
    },
    {
      title: 'Cite a line, jump to a line',
      body: 'Every line keeps its traditional vulgate number, like Il. 1.1 — copy the address bar to link straight to it, or press ⌘K (Ctrl-K) to jump to any citation.',
    },
    {
      title: 'Look around',
      body: 'The ☰ Contents drawer lists every book. Maps, Genealogies, and Search are in the header above. Enjoy the poem.',
    },
  ];

  let open = false;
  let step = 0;
  let modalEl: HTMLDivElement;
  let triggerFocus: HTMLElement | null = null;

  function dismiss() {
    open = false;
    try { localStorage.setItem(DISMISSED_KEY, '1'); } catch {}
    triggerFocus?.focus();
  }
  function next() {
    if (step < STEPS.length - 1) step += 1;
    else dismiss();
  }
  function back() {
    if (step > 0) step -= 1;
  }

  function onKeydown(e: KeyboardEvent) {
    if (!open) return;
    if (e.key === 'Escape') { dismiss(); return; }
    if (e.key === 'ArrowRight') { next(); return; }
    if (e.key === 'ArrowLeft') { back(); return; }
    if (e.key !== 'Tab') return;
    const els = modalEl
      ? Array.from(modalEl.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
        )).filter((el) => !el.hasAttribute('disabled') && el.tabIndex !== -1)
      : [];
    if (els.length === 0) { e.preventDefault(); modalEl?.focus(); return; }
    const first = els[0];
    const last = els[els.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  onMount(async () => {
    let dismissed = false;
    try { dismissed = !!localStorage.getItem(DISMISSED_KEY); } catch {}
    if (dismissed) return;
    const params = new URLSearchParams(window.location.search);
    if (params.get('tour') !== 'parse') return;
    triggerFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    open = true;
    window.addEventListener('keydown', onKeydown);
    await tick();
    modalEl?.focus();
  });
  onDestroy(() => {
    if (typeof window !== 'undefined') window.removeEventListener('keydown', onKeydown);
  });
</script>

{#if open}
  <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
  <div class="tour-backdrop" on:click={dismiss}>
    <div
      class="tour-modal"
      bind:this={modalEl}
      role="dialog"
      aria-modal="true"
      aria-label="Reading the Greek: a quick tour"
      tabindex="-1"
      on:click|stopPropagation
    >
      <div class="tour-head">
        <span class="tour-step-count">Step {step + 1} of {STEPS.length}</span>
        <button type="button" class="tour-close" on:click={dismiss} aria-label="Skip tour">×</button>
      </div>
      <h2 class="tour-title">{STEPS[step].title}</h2>
      <p class="tour-body">{STEPS[step].body}</p>
      <div class="tour-dots" aria-hidden="true">
        {#each STEPS as _, i}
          <span class="tour-dot" class:active={i === step}></span>
        {/each}
      </div>
      <div class="tour-actions">
        <button type="button" class="tour-skip" on:click={dismiss}>Skip tour</button>
        <span class="tour-nav">
          {#if step > 0}
            <button type="button" class="tour-back" on:click={back}>Back</button>
          {/if}
          <button type="button" class="tour-next" on:click={next}>
            {step < STEPS.length - 1 ? 'Next' : 'Done'}
          </button>
        </span>
      </div>
    </div>
  </div>
{/if}

<style>
  .tour-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: flex-end;
    justify-content: center;
    padding: 1.25rem;
    z-index: 70;
    animation: tour-backdrop-in 0.18s ease-out;
  }
  @media (min-width: 640px) {
    .tour-backdrop { align-items: center; }
  }
  .tour-modal {
    background: var(--popup-bg);
    border-radius: 8px;
    max-width: 26rem;
    width: 100%;
    padding: 1.1rem 1.3rem 1.3rem;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.25);
    font-family: var(--font-ui);
    color: var(--text);
    animation: tour-modal-in 0.2s cubic-bezier(0.2, 0, 0, 1);
  }
  @keyframes tour-backdrop-in { from { opacity: 0; } to { opacity: 1; } }
  @keyframes tour-modal-in {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @media (prefers-reduced-motion: reduce) {
    .tour-backdrop, .tour-modal { animation: none; }
  }
  .tour-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }
  .tour-step-count {
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--accent);
    font-weight: 600;
  }
  .tour-close {
    background: none;
    border: none;
    font-size: 1.4rem;
    line-height: 1;
    color: var(--text-light);
    cursor: pointer;
    padding: 0 0.2rem;
  }
  .tour-close:hover { color: var(--text); }
  .tour-title {
    font-family: var(--font-display);
    font-weight: 400;
    font-size: 1.25rem;
    margin: 0 0 0.5rem;
    color: var(--text);
  }
  .tour-body {
    font-size: 0.9rem;
    line-height: 1.55;
    color: var(--text-mid);
    margin: 0 0 1rem;
  }
  .tour-dots {
    display: flex;
    gap: 0.35rem;
    margin-bottom: 1.1rem;
  }
  .tour-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--border);
  }
  .tour-dot.active { background: var(--accent); }
  .tour-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
  }
  .tour-skip {
    background: none;
    border: none;
    font: inherit;
    font-size: 0.82rem;
    color: var(--text-light);
    cursor: pointer;
    padding: 0.3rem 0;
  }
  .tour-skip:hover { color: var(--text-mid); text-decoration: underline; }
  .tour-nav { display: flex; gap: 0.5rem; }
  .tour-back {
    font: inherit;
    font-size: 0.85rem;
    cursor: pointer;
    padding: 0.35rem 0.8rem;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--col-bg);
    color: var(--text-mid);
  }
  .tour-back:hover { border-color: var(--text-mid); }
  .tour-next {
    font: inherit;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    padding: 0.35rem 0.9rem;
    border: 1px solid var(--accent);
    border-radius: 4px;
    background: var(--accent);
    color: var(--on-accent);
  }
  .tour-next:hover { filter: brightness(1.08); }
</style>
