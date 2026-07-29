<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { fly } from 'svelte/transition';
  import LexiconPanel from './LexiconPanel.svelte';

  // The PRESENTATION shell for a word lookup. Two presentations, one shared body
  // (LexiconPanel):
  //   • docked=false (default) — the anchored MOBILE / narrow popup: a
  //     NON-modal bottom-sheet (phone / tablet-compare) or right slide-in,
  //     closed by a window click listener (not a blocking backdrop — that
  //     swallowed clicks meant for another Greek token). Non-modal for real:
  //     outside clicks land on their targets and other tokens swap the panel,
  //     so it claims no aria-modal and installs no focus trap.
  //   • docked=true — the DESKTOP (≥1100px) lexicon rail: an in-layout
  //     panel — no outside-click close, part of the page tab order. Focus
  //     management (move-in on keyboard open, return-on-Escape) is owned by
  //     the Reader, which knows whether the token was opened by keyboard
  //     (DESIGN.md 2026-07-17).
  export let work: string = 'EN';
  export let token: { t: string; k: string };
  export const anchor: { x: number; y: number } = { x: 0, y: 0 };
  export let onClose: () => void;
  // Compare mode packs three columns into the reading measure; on a tablet the
  // right-margin reserve would crush them, so there the panel drops to a bottom
  // sheet (like the phone layout) and the text keeps full width. See the
  // .word-sidebar.as-sheet block in global.css.
  export let asSheet: boolean = false;
  export let docked: boolean = false;
  // Move focus into the panel on open only when asked — keyboard activation of a
  // Greek token. A docked panel opened by MOUSE must not steal focus from the
  // reading flow; the anchored popup always takes focus.
  export let autofocus: boolean = false;

  let dialogEl: HTMLDivElement;
  let previousFocus: HTMLElement | null = null;
  // Resolved synchronously at instantiation (this component only ever mounts
  // client-side, on a word click) so the intro transition picks the right
  // direction: mobile rises from the bottom, desktop slides in from the right.
  const isMobile = typeof window !== 'undefined'
    && window.matchMedia('(max-width: 680px)').matches;
  // Whether we render as a bottom sheet: always on phones, and on tablets when
  // the caller is in compare mode (asSheet) — matches the CSS in global.css.
  const asSheetHere = typeof window !== 'undefined'
    && (isMobile || (asSheet && window.matchMedia('(min-width: 681px) and (max-width: 1100px)').matches));
  // Honour the OS "reduce motion" setting: the fly-in is decorative, so collapse
  // it to an instant appearance.
  const reduceMotion = typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function onKey(e: KeyboardEvent) {
    if (e.key === 'Escape') onClose();
  }

  // Close on any CLICK outside the panel — EXCEPT on a Greek token, whose
  // own click handler swaps the popup to the new word. (A blocking backdrop
  // here would swallow that click and force close-then-reopen, with two page
  // reflows.) Click, not pointerdown: a click only fires after press+release
  // on the same target, so a touch pan, a text-selection drag, or a
  // right-click never dismisses the panel — the same tap-not-pan semantics
  // the old backdrop had (Sol adversarial-review catch, 2026-07-29). The
  // docked rail was never dismissed by outside clicks (no backdrop ever
  // rendered for it) — preserve that by no-op'ing here while docked.
  function onOutsideClick(e: MouseEvent) {
    if (docked) return;
    const t = e.target as HTMLElement | null;
    if (!t || t.closest('.word-sidebar') || t.closest('.tok')) return;
    onClose();
  }

  onMount(() => {
    previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    // The anchored popup always takes focus; the docked rail only when the
    // reader signals a keyboard open (autofocus).
    if (!docked || autofocus) setTimeout(() => dialogEl?.focus({ preventScroll: true }), 0);
  });

  onDestroy(() => {
    // The anchored popup restores focus to the opener on teardown. The docked rail
    // leaves focus to the reader (it returns focus to the token on Escape), so a
    // mouse-driven close never yanks the caret around the page.
    // preventScroll: the reader pins its own scroll position across the close
    // reflow; letting focus() scroll to the old word snaps the page around.
    if (!docked) previousFocus?.focus({ preventScroll: true });
  });
</script>

<svelte:window on:keydown={onKey} on:click={onOutsideClick} />

<!-- Desktop docked rail OR the anchored popup/sheet (both non-modal). Both via CSS. -->
<div
  class="word-sidebar"
  class:as-sheet={asSheet}
  class:docked
  bind:this={dialogEl}
  transition:fly={reduceMotion ? { duration: 0 } : asSheetHere ? { y: 600, duration: 260, opacity: 1 } : { x: 420, duration: 220, opacity: 1 }}
  role={docked ? 'region' : 'dialog'}
  aria-label="Word analysis"
  tabindex="-1"
>
  <div class="word-sidebar-head">
    <span class="popup-surface" lang="grc">{token.t}</span>
    <button class="settings-close" on:click={onClose} aria-label="Close">×</button>
  </div>
  <div class="word-sidebar-body">
    <LexiconPanel {work} {token} {docked} />
  </div>
</div>
