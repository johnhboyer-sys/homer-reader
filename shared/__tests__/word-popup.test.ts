import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { tick } from 'svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import WordPopup from '../components/WordPopup.svelte';

const { lookupWordMock } = vi.hoisted(() => ({ lookupWordMock: vi.fn() }));

vi.mock('../lib/data', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/data')>();
  return {
    ...actual,
    fetchLemmata: vi.fn(async () => ({})),
    lookupWord: lookupWordMock,
  };
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderPopup(props: Record<string, unknown> = {}) {
  return render(WordPopup, {
    props: {
      work: 'iliad',
      token: { t: 'μῆνις', k: 'mhnis' },
      anchor: { x: 0, y: 0 },
      onClose: vi.fn(),
      ...props,
    },
  });
}

// The full dictionary entry (tabs + HTML) now lives behind an EXPAND disclosure
// (DESIGN.md 2026-07-17): the panel shows the short gloss first. Reveal it.
async function expand() {
  const btn = await screen.findByRole('button', { name: /dictionary entry/i });
  await fireEvent.click(btn);
  return btn;
}

describe('WordPopup.svelte — gloss + EXPAND disclosure', () => {
  it('shows the short gloss first and reveals the full entry only after EXPAND', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{ lemma: 'mh=nis', gloss: 'wrath', parse: 'noun', lsj: ['mh=nis'], cunliffe: ['mh=nis'] }],
      lsj: [{ key: 'mh=nis', head: 'μῆνις', html: '<p>wrath, ire</p>' }],
      cunliffe: [{ key: 'mh=nis', head: 'μῆνις', html: '<div class="cunliffe-sense">Wrath, ire.</div>', src: 'lex' }],
    });
    renderPopup();

    // The gloss shows immediately; the tab row does NOT until expanded.
    expect(await screen.findByText('wrath')).toBeInTheDocument();
    const expandBtn = await screen.findByRole('button', { name: /dictionary entry/i });
    expect(expandBtn).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByRole('tab', { name: 'LSJ' })).toBeNull();

    await fireEvent.click(expandBtn);
    expect(expandBtn).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('tab', { name: 'LSJ' })).toBeInTheDocument();
    expect(screen.getByText('wrath, ire')).toBeVisible();
  });

  it('shows the LSJ · Cunliffe · Logeion tab row (LSJ default) once expanded', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{ lemma: 'mh=nis', gloss: 'wrath', parse: 'noun', lsj: ['mh=nis'], cunliffe: ['mh=nis'] }],
      lsj: [{ key: 'mh=nis', head: 'μῆνις', html: '<p>wrath, ire</p>' }],
      cunliffe: [{ key: 'mh=nis', head: 'μῆνις', html: '<div class="cunliffe-sense">Wrath, ire.</div>', src: 'lex' }],
    });
    renderPopup();
    await expand();

    const lsjTab = screen.getByRole('tab', { name: 'LSJ' });
    const cunliffeTab = screen.getByRole('tab', { name: 'Cunliffe' });
    const logeionLink = screen.getByRole('link', { name: /Logeion/ });

    expect(lsjTab).toHaveAttribute('aria-selected', 'true');
    expect(cunliffeTab).toHaveAttribute('aria-selected', 'false');
    expect(logeionLink).toHaveAttribute('target', '_blank');
    expect(logeionLink).toHaveAttribute('rel', 'noopener');
    expect(logeionLink.getAttribute('href')).toContain('logeion.uchicago.edu/');
    expect(logeionLink.getAttribute('href')).toContain(encodeURIComponent('μῆνις'));

    expect(screen.getByText('wrath, ire')).toBeVisible();
    expect(screen.getByText('Wrath, ire.').closest('[role="tabpanel"]')).toHaveAttribute('hidden');

    await fireEvent.click(cunliffeTab);
    expect(cunliffeTab).toHaveAttribute('aria-selected', 'true');
    expect(lsjTab).toHaveAttribute('aria-selected', 'false');
    expect(screen.getByText('Wrath, ire.').closest('[role="tabpanel"]')).not.toHaveAttribute('hidden');
  });

  it('Logeion is the ONLY link that opens a new tab in the rendered popup', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{ lemma: 'mh=nis', gloss: 'wrath', parse: 'noun', lsj: ['mh=nis'], cunliffe: ['mh=nis'] }],
      lsj: [{ key: 'mh=nis', head: 'μῆνις', html: '<p>wrath, ire</p>' }],
      cunliffe: [{ key: 'mh=nis', head: 'μῆνις', html: '<div class="cunliffe-sense">Wrath.</div>', src: 'lex' }],
    });
    const { container } = renderPopup();
    await expand();

    const blankTargets = container.querySelectorAll('[target="_blank"]');
    expect(blankTargets).toHaveLength(1);
    expect(blankTargets[0]).toHaveTextContent(/Logeion/);
    expect(blankTargets[0]).toHaveAttribute('rel', 'noopener');
  });

  it('shows a quiet "not in Cunliffe" empty state when no entry matched', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{ lemma: 'a)/gnwstos', gloss: 'unknown', parse: 'adj', lsj: ['a)/gnwstos'], cunliffe: [] }],
      lsj: [{ key: 'a)/gnwstos', head: 'ἄγνωστος', html: '<p>unknown</p>' }],
      cunliffe: [],
    });
    renderPopup();
    await expand();

    const cunliffeTab = screen.getByRole('tab', { name: 'Cunliffe' });
    await fireEvent.click(cunliffeTab);

    expect(screen.getByText('Not in Cunliffe.')).toBeInTheDocument();
  });

  it('arrow-key navigation moves focus and selection between LSJ and Cunliffe tabs', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{ lemma: 'mh=nis', gloss: 'wrath', parse: 'noun', lsj: ['mh=nis'], cunliffe: ['mh=nis'] }],
      lsj: [{ key: 'mh=nis', head: 'μῆνις', html: '<p>wrath</p>' }],
      cunliffe: [{ key: 'mh=nis', head: 'μῆνις', html: '<div class="cunliffe-sense">Wrath.</div>', src: 'lex' }],
    });
    renderPopup();
    await expand();

    const lsjTab = screen.getByRole('tab', { name: 'LSJ' });
    const cunliffeTab = screen.getByRole('tab', { name: 'Cunliffe' });

    lsjTab.focus();
    await fireEvent.keyDown(lsjTab, { key: 'ArrowRight' });
    expect(cunliffeTab).toHaveAttribute('aria-selected', 'true');
    expect(document.activeElement).toBe(cunliffeTab);

    await fireEvent.keyDown(cunliffeTab, { key: 'ArrowLeft' });
    expect(lsjTab).toHaveAttribute('aria-selected', 'true');
    expect(document.activeElement).toBe(lsjTab);
  });
});

describe('WordPopup.svelte — docked vs modal presentation', () => {
  const analysis = {
    analyses: [{ lemma: 'mh=nis', gloss: 'wrath', parse: 'noun', lsj: ['mh=nis'], cunliffe: [] }],
    lsj: [{ key: 'mh=nis', head: 'μῆνις', html: '<p>wrath</p>' }],
    cunliffe: [],
  };

  it('renders a NON-modal region with no backdrop when docked', async () => {
    lookupWordMock.mockResolvedValue(analysis);
    const { container } = renderPopup({ docked: true });

    const sidebar = container.querySelector('.word-sidebar');
    expect(sidebar).toHaveClass('docked');
    expect(sidebar).toHaveAttribute('role', 'region');
    expect(sidebar).not.toHaveAttribute('aria-modal');
    expect(container.querySelector('.popup-backdrop')).toBeNull();
  });

  it('renders a NON-modal dialog with no backdrop when NOT docked', async () => {
    lookupWordMock.mockResolvedValue(analysis);
    const { container } = renderPopup({ docked: false });

    const sidebar = container.querySelector('.word-sidebar');
    expect(sidebar).not.toHaveClass('docked');
    expect(sidebar).toHaveAttribute('role', 'dialog');
    // Honest non-modality (Sol adversarial-review fix, 2026-07-29): outside
    // clicks land on their targets and other tokens swap the panel, so the
    // dialog must NOT claim aria-modal.
    expect(sidebar).not.toHaveAttribute('aria-modal');
    // No blocking backdrop — see "pointerdown outside" describe block below
    // for the 2026-07-29 fix (a full-page backdrop swallowed clicks meant for
    // another Greek token, forcing close-then-reopen with two page snaps).
    expect(container.querySelector('.popup-backdrop')).toBeNull();
  });
});

// Regression tests for the 2026-07-29 fix: with the (non-docked) word popup
// open, clicking another Greek word must swap the analysis in place — the old
// full-page `.popup-backdrop` swallowed that click and forced close/reopen.
// Closing must also not snap the page's scroll position.
describe('WordPopup.svelte — click outside (replaces the backdrop)', () => {
  const analysis = {
    analyses: [{ lemma: 'mh=nis', gloss: 'wrath', parse: 'noun', lsj: ['mh=nis'], cunliffe: [] }],
    lsj: [{ key: 'mh=nis', head: 'μῆνις', html: '<p>wrath</p>' }],
    cunliffe: [],
  };

  it('renders no click-blocking backdrop element at all', async () => {
    lookupWordMock.mockResolvedValue(analysis);
    renderPopup();
    await screen.findByText('wrath');
    expect(document.querySelector('.popup-backdrop')).toBeNull();
  });

  it('closes on click outside, but not on the panel or on a Greek token', async () => {
    lookupWordMock.mockResolvedValue(analysis);
    const tok = document.createElement('span');
    tok.className = 'tok';
    document.body.appendChild(tok);

    const onClose = vi.fn();
    renderPopup({ onClose });
    await screen.findByText('wrath');

    // On a Greek token: the token's own click handler swaps the word — no close.
    tok.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    await tick();
    expect(onClose).not.toHaveBeenCalled();

    // Inside the panel: no close.
    document.querySelector('.word-sidebar')!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    await tick();
    expect(onClose).not.toHaveBeenCalled();

    // A press alone must NOT close — a touch pan or a text-selection drag
    // starts with one, and dismissing mid-gesture fought the Reader's
    // open-time scroll pin (Sol adversarial-review fix, 2026-07-29).
    document.body.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
    await tick();
    expect(onClose).not.toHaveBeenCalled();

    // A right-button press must NOT close either.
    document.body.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, button: 2 }));
    await tick();
    expect(onClose).not.toHaveBeenCalled();

    // A completed click anywhere else: close.
    document.body.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    await tick();
    expect(onClose).toHaveBeenCalledTimes(1);

    tok.remove();
  });

  it('is non-modal: no Tab focus trap on the dialog', async () => {
    lookupWordMock.mockResolvedValue(analysis);
    renderPopup();
    await screen.findByText('wrath');

    // The old trap intercepted Tab only at the focus BOUNDARIES (last
    // focusable forward, first backward) — so exercise exactly that spot:
    // focus the last focusable, press Tab, and require the event to pass
    // through unhindered instead of being wrapped back to the first.
    const dialog = document.querySelector('.word-sidebar')!;
    const els = dialog.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
    );
    expect(els.length).toBeGreaterThan(0);
    const last = els[els.length - 1];
    last.focus();
    const ev = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true });
    last.dispatchEvent(ev);
    expect(ev.defaultPrevented).toBe(false);
    // And the trap must not have rewired focus back into the panel.
    expect(document.activeElement).toBe(last);
  });

  // Preserved-behavior coverage: docked never had outside-close, and the
  // 2026-07-29 pointerdown handler must not introduce it by accident.
  it('invariant: does not close on outside click when docked (rail stays persistent)', async () => {
    lookupWordMock.mockResolvedValue(analysis);
    const onClose = vi.fn();
    renderPopup({ onClose, docked: true });
    // docked opens the LSJ entry expanded by default, so "wrath" appears both
    // as the gloss and inside the LSJ html — target the unique gloss element.
    await screen.findByText('wrath', { selector: '.gloss' });

    document.body.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    await tick();
    expect(onClose).not.toHaveBeenCalled();
  });
});

describe('WordPopup.svelte — focus restore preserves scroll position', () => {
  const analysis = {
    analyses: [{ lemma: 'mh=nis', gloss: 'wrath', parse: 'noun', lsj: ['mh=nis'], cunliffe: [] }],
    lsj: [{ key: 'mh=nis', head: 'μῆνις', html: '<p>wrath</p>' }],
    cunliffe: [],
  };

  it('restores focus with preventScroll when NOT docked', async () => {
    lookupWordMock.mockResolvedValue(analysis);
    const opener = document.createElement('button');
    document.body.appendChild(opener);
    opener.focus();
    const focusSpy = vi.spyOn(opener, 'focus');

    const { unmount } = renderPopup();
    await screen.findByText('wrath');

    unmount();
    expect(focusSpy).toHaveBeenCalledWith({ preventScroll: true });
    opener.remove();
  });

  it('moves focus INTO the panel on mount with preventScroll when NOT docked', async () => {
    lookupWordMock.mockResolvedValue(analysis);
    const { container } = renderPopup();
    // The mount-time focus() call runs off a setTimeout(0) inside onMount, so
    // the spy must be attached to the panel before that timer fires (safe
    // here — nothing yields control between render() and the spyOn call
    // below) and the assertion flushed via waitFor.
    const panel = container.querySelector('.word-sidebar') as HTMLDivElement;
    const focusSpy = vi.spyOn(panel, 'focus');

    await waitFor(() => expect(focusSpy).toHaveBeenCalled());
    expect(focusSpy).toHaveBeenCalledWith({ preventScroll: true });
  });

  // Preserved-behavior coverage: docked never restored focus on teardown, and
  // the 2026-07-29 pointerdown/focus changes must not disturb that.
  it('invariant: skips focus restore entirely when docked', async () => {
    lookupWordMock.mockResolvedValue(analysis);
    const opener = document.createElement('button');
    document.body.appendChild(opener);
    opener.focus();
    const focusSpy = vi.spyOn(opener, 'focus');

    const { unmount } = renderPopup({ docked: true });
    // docked opens the LSJ entry expanded by default, so "wrath" appears both
    // as the gloss and inside the LSJ html — target the unique gloss element.
    await screen.findByText('wrath', { selector: '.gloss' });

    unmount();
    expect(focusSpy).not.toHaveBeenCalled();
    opener.remove();
  });
});

describe('WordPopup.svelte — token switch while open', () => {
  it('re-fetches parse + definition when token changes without closing', async () => {
    lookupWordMock
      .mockResolvedValueOnce({
        analyses: [{ lemma: 'mh=nis', gloss: 'wrath', parse: 'fem acc sg', lsj: ['mh=nis'], cunliffe: [] }],
        lsj: [{ key: 'mh=nis', head: 'μῆνις', html: '<p>wrath entry</p>' }],
        cunliffe: [],
      })
      .mockResolvedValueOnce({
        analyses: [{ lemma: 'a)ei/dw', gloss: 'sing', parse: 'pres imperat act 2nd sg', lsj: ['a)ei/dw'], cunliffe: [] }],
        lsj: [{ key: 'a)ei/dw', head: 'ἀείδω', html: '<p>sing entry</p>' }],
        cunliffe: [],
      });

    const { rerender } = renderPopup({
      docked: true,
      token: { t: 'μῆνιν', k: 'mh=nin' },
    });

    expect(await screen.findByText('wrath')).toBeInTheDocument();
    expect(screen.getByText('fem acc sg')).toBeInTheDocument();
    expect(lookupWordMock).toHaveBeenCalledWith('iliad', 'mh=nin');

    // Same instance stays mounted (Reader keeps {#if popup}); only the token
    // prop changes — this is the sitewide second-click path. Svelte 5: use
    // testing-library rerender rather than the removed component.$set.
    await rerender({
      work: 'iliad',
      token: { t: 'ἄειδε', k: 'a)ei/de' },
      anchor: { x: 0, y: 0 },
      onClose: vi.fn(),
      docked: true,
    });

    expect(await screen.findByText('sing')).toBeInTheDocument();
    expect(screen.getByText('pres imperat act 2nd sg')).toBeInTheDocument();
    expect(screen.queryByText('wrath')).toBeNull();
    expect(lookupWordMock).toHaveBeenCalledWith('iliad', 'a)ei/de');
    expect(lookupWordMock).toHaveBeenCalledTimes(2);
  });
});
