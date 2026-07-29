<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { fly } from 'svelte/transition';
  import LexiconPanel from './LexiconPanel.svelte';

  // The PRESENTATION shell for a word lookup. Two presentations, one shared body
  // (LexiconPanel):
  //   • docked=false (default) — the anchored MOBILE / narrow popup: a modal
  //     bottom-sheet (phone / tablet-compare) or right slide-in, closed by a
  //     window pointerdown listener (not a blocking backdrop — that swallowed
  //     clicks meant for another Greek token) and a Tab focus-trap.
  //   • docked=true — the DESKTOP (≥1100px) lexicon rail: a NON-modal, in-layout
  //     panel — no outside-click close, no aria-modal, no focus-trap, part of
  //     the page tab order. Focus management (move-in on keyboard open,
  //     return-on-Escape) is owned by the Reader, which knows whether the
  //     token was opened by keyboard (DESIGN.md 2026-07-17).
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
  // reading flow; the modal popup always takes focus.
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

  // Close on any pointer-down outside the panel — EXCEPT on a Greek token,
  // whose own click handler swaps the popup to the new word. (A blocking
  // backdrop here would swallow that click and force close-then-reopen, with
  // two page reflows.) The docked rail is non-modal and was never dismissed by
  // outside clicks (no backdrop ever rendered for it) — preserve that by
  // no-op'ing here while docked.
  function onOutsidePointer(e: PointerEvent) {
    if (docked) return;
    const t = e.target as HTMLElement | null;
    if (!t || t.closest('.word-sidebar') || t.closest('.tok')) return;
    onClose();
  }

  function focusableEls(): HTMLElement[] {
    return dialogEl
      ? Array.from(dialogEl.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        )).filter((el) => !el.hasAttribute('disabled') && el.tabIndex !== -1)
      : [];
  }

  // Tab focus-trap — modal presentation only. The docked rail is non-modal and
  // stays in the natural page tab order, so it installs no trap.
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
    // Modal popup always takes focus; the docked rail only when the reader
    // signals a keyboard open (autofocus).
    if (!docked || autofocus) setTimeout(() => dialogEl?.focus({ preventScroll: true }), 0);
  });

  onDestroy(() => {
    // The modal popup restores focus to the opener on teardown. The docked rail
    // leaves focus to the reader (it returns focus to the token on Escape), so a
    // mouse-driven close never yanks the caret around the page.
    // preventScroll: the reader pins its own scroll position across the close
    // reflow; letting focus() scroll to the old word snaps the page around.
    if (!docked) previousFocus?.focus({ preventScroll: true });
  });
</script>

<svelte:window on:keydown={onKey} on:pointerdown={onOutsidePointer} />

<!-- Desktop docked rail (non-modal) OR the anchored modal popup/sheet. Both via CSS. -->
<div
  class="word-sidebar"
  class:as-sheet={asSheet}
  class:docked
  bind:this={dialogEl}
  transition:fly={reduceMotion ? { duration: 0 } : asSheetHere ? { y: 600, duration: 260, opacity: 1 } : { x: 420, duration: 220, opacity: 1 }}
  role={docked ? 'region' : 'dialog'}
  aria-label="Word analysis"
  aria-modal={docked ? undefined : 'true'}
  tabindex="-1"
  on:keydown={docked ? undefined : onDialogKey}
>
  <div class="word-sidebar-head">
    <span class="popup-surface" lang="grc">{token.t}</span>
    <button class="settings-close" on:click={onClose} aria-label="Close">×</button>
  </div>
  <div class="word-sidebar-body">
    <LexiconPanel {work} {token} {docked} />
  </div>
</div>
