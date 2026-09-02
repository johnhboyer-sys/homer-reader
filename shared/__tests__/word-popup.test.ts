import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { tick } from 'svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import WordPopup from '../components/WordPopup.svelte';

const { lookupWordMock, headsMock, cunliffeShardMock } = vi.hoisted(() => ({
  lookupWordMock: vi.fn(),
  headsMock: vi.fn(async () => ({})),
  cunliffeShardMock: vi.fn(async () => ({})),
}));

vi.mock('../lib/data', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/data')>();
  return {
    ...actual,
    fetchLemmata: vi.fn(async () => ({})),
    fetchLsjHeads: headsMock,
    fetchCunliffeT8Shard: cunliffeShardMock,
    lookupWord: lookupWordMock,
  };
});

// The dictionary entry itself is served by grammata over the network. Stub the
// module so the popup's contract with it can be asserted without a fetch — above
// all that it is handed the KEY and never the surface form.
const grammataLookup = vi.fn(async () => {});
// renderEntry is what draws a Cunliffe record. Stubbed so the popup's contract
// with it can be asserted — which record, and which options — without a fetch.
const grammataRender = vi.fn((_rec: unknown, el: HTMLElement) => {
  el.innerHTML = '<article class="t8-entry">rendered</article>';
});
vi.mock('https://grammata.pages.dev/t8/lookup.js', () => ({
  lookup: (...args: unknown[]) => grammataLookup(...(args as [])),
  renderEntry: (...args: unknown[]) => grammataRender(...(args as [never, never])),
  T8_SCHEMA_VERSION: 1,
}));

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

// The dictionary is no longer behind one EXPAND control for the whole panel.
// Each CARD carries its own LSJ · Cunliffe tabs, and the entry opens under the
// card tapped (John, 2026-08-30) — so nothing is fetched for a reader who
// wanted only the parse.
const WRATH = {
  analyses: [{
    lemma: 'mh=nis', gloss: 'wrath', parse: 'fem nom sg',
    lsj: ['mh=nis'], cunliffe: ['mh=nis'],
  }],
  lsj: [], cunliffe: [],
};
const HEADS = { 'mh=nis': { head: 'μῆνις' } };

describe('WordPopup.svelte — the entry opens under the card tapped', () => {
  it('shows the gloss at once, and fetches no entry until a tab is tapped', async () => {
    lookupWordMock.mockResolvedValue(WRATH);
    headsMock.mockResolvedValue(HEADS);
    const { container } = renderPopup();

    expect(await screen.findByText('wrath')).toBeInTheDocument();
    const lsjTab = screen.getByRole('button', { name: 'LSJ' });
    expect(lsjTab).toHaveAttribute('aria-expanded', 'false');
    // Closed means CLOSED: no mount point, and grammata never called.
    expect(container.querySelector('.grammata-mount')).toBeNull();
    expect(grammataLookup).not.toHaveBeenCalled();
    // And the panel asked for no dictionary shards in the first place.
    expect(lookupWordMock).toHaveBeenCalledWith('iliad', 'mhnis', { entries: false });
  });

  it('hands grammata the KEY, never the surface form', async () => {
    // A surface form makes the widget re-analyse and discard this reader's
    // disambiguation: εἰσὶ comes back as ἵημι, εἰμί and εἶμι, ἵημι first.
    lookupWordMock.mockResolvedValue(WRATH);
    headsMock.mockResolvedValue(HEADS);
    const { container } = renderPopup();
    await screen.findByText('wrath');

    await fireEvent.click(screen.getByRole('button', { name: 'LSJ' }));
    await waitFor(() => expect(grammataLookup).toHaveBeenCalled());
    const [word, , opts] = grammataLookup.mock.calls[0] as [string, HTMLElement, Record<string, string>];
    expect(word).toBe('');
    // logeion:false — grammata suppresses its own header link, so the card's
    // tab row is the only one. Their option; it defaults on for other hosts.
    expect(opts).toEqual({ lang: 'grc', logeion: false, key: 'mh=nis' });
    expect(container.querySelector('.grammata-mount')).toBeInTheDocument();
  });

  it('opens Cunliffe under the same card, and closes on a second tap', async () => {
    lookupWordMock.mockResolvedValue(WRATH);
    headsMock.mockResolvedValue(HEADS);
    cunliffeShardMock.mockResolvedValue({
      'mh=nis': [{ key: 'mh=nis', head: 'μῆνις', i: 'ἡ.',
                   rows: [{ lv: 1, n: '1', z: 'Wrath, ire' }] }],
    });
    const { container } = renderPopup();
    await screen.findByText('wrath');

    const cunliffeTab = screen.getByRole('button', { name: 'Cunliffe' });
    await fireEvent.click(cunliffeTab);
    await waitFor(() => expect(grammataRender).toHaveBeenCalled());
    const [rec] = grammataRender.mock.calls[0] as [{ head: string }];
    expect(rec.head).toBe('μῆνις');
    // The entry sits INSIDE the card it belongs to, not below the whole stack.
    expect(container.querySelector('.analysis-card .card-entry')).toBeInTheDocument();

    await fireEvent.click(cunliffeTab);
    await waitFor(() =>
      expect(container.querySelector('.cunliffe-mount')).toBeNull());
    expect(cunliffeTab).toHaveAttribute('aria-expanded', 'false');
  });

  it('renders Cunliffe with our links and without LSJ abbreviations', async () => {
    lookupWordMock.mockResolvedValue(WRATH);
    headsMock.mockResolvedValue(HEADS);
    cunliffeShardMock.mockResolvedValue({
      'mh=nis': [{ key: 'mh=nis', head: 'μῆνις', rows: [{ lv: 1, n: '1', z: 'Wrath' }] }],
    });
    renderPopup();
    await screen.findByText('wrath');
    await fireEvent.click(screen.getByRole('button', { name: 'Cunliffe' }));
    await waitFor(() => expect(grammataRender).toHaveBeenCalled());

    const [, , opts] = grammataRender.mock.calls[0] as [unknown, unknown, {
      abbr: boolean; logeion: boolean; citation: (t: string) => string | null }];
    // abbr:false — grammata's table is LSJ-shaped and Cunliffe's conventions
    // are narrower; a wrong expansion is worse than none.
    expect(opts.abbr).toBe(false);
    // logeion:false — the card's own tab row already carries that link.
    expect(opts.logeion).toBe(false);
    // We supply the hrefs: grammata deliberately does not know our URL scheme.
    expect(opts.citation('Il. 1.75')).toContain('/iliad/');
    // A bare continuation has no book of its own and must stay plain rather
    // than become a link to the wrong line.
    expect(opts.citation('75')).toBeNull();
    // A line range Cunliffe prints in full ("Od. 6.177-8") is ONE reference,
    // and it opens on Od. 6.177. Leaving it unresolved would cost the link on
    // a reference he really does make; resolving it to the tail would point at
    // Od. 6.8, which is the defect the range token was folded to prevent.
    expect(opts.citation('Od. 6.177-8')).toContain('6.177');
    expect(opts.citation('Od. 6.177-8')).not.toContain('6.8');
    expect(opts.citation('Il. 2.671-673')).toContain('2.671');
  });

  it('offers no Cunliffe tab on a card no Cunliffe entry covers', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{
        lemma: 'a)/gnwstos', gloss: 'unknown', parse: 'adj',
        lsj: ['a)/gnwstos'], cunliffe: [],
      }],
      lsj: [], cunliffe: [],
    });
    headsMock.mockResolvedValue({ 'a)/gnwstos': { head: 'ἄγνωστος' } });
    renderPopup();
    await screen.findByText('unknown');

    expect(screen.getByRole('button', { name: 'LSJ' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Cunliffe' })).toBeNull();
  });

  it('says so quietly when Cunliffe is named but holds nothing', async () => {
    lookupWordMock.mockResolvedValue(WRATH);
    headsMock.mockResolvedValue(HEADS);
    cunliffeShardMock.mockResolvedValue({});
    renderPopup();
    await screen.findByText('wrath');

    await fireEvent.click(screen.getByRole('button', { name: 'Cunliffe' }));
    expect(await screen.findByText('Not in Cunliffe.')).toBeInTheDocument();
  });

  it('gives every card its own Logeion link, and it is the only new tab', async () => {
    lookupWordMock.mockResolvedValue(WRATH);
    headsMock.mockResolvedValue(HEADS);
    const { container } = renderPopup();
    await screen.findByText('wrath');

    const blankTargets = container.querySelectorAll('[target="_blank"]');
    expect(blankTargets).toHaveLength(1);
    expect(blankTargets[0]).toHaveTextContent(/Logeion/);
    expect(blankTargets[0]).toHaveAttribute('rel', 'noopener');
    // Keyed off THIS card's headword, not the first analysis in the panel.
    expect(blankTargets[0].getAttribute('href'))
      .toContain(encodeURIComponent('μῆνις'));
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
    expect(lookupWordMock).toHaveBeenCalledWith('iliad', 'mh=nin', { entries: false });

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
    expect(lookupWordMock).toHaveBeenCalledWith('iliad', 'a)ei/de', { entries: false });
    expect(lookupWordMock).toHaveBeenCalledTimes(2);
  });
});

describe('WordPopup.svelte — following a Cunliffe cross-reference', () => {
  // Cunliffe points from entry to entry constantly ("See πολλός."). stage5
  // marks the pointers whose target ships, inside the record's own `z`; the
  // panel follows them in place and can come back.
  const setup = async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{ lemma: 'p', gloss: 'much', parse: 'adj', lsj: ['p1'], cunliffe: ['polu/s'] }],
      lsj: [], cunliffe: [],
    });
    headsMock.mockResolvedValue({ p1: { head: 'πολύς' } });
    cunliffeShardMock.mockResolvedValue({
      'polu/s': [{ key: 'polu/s', head: 'πολύς', rows: [{ lv: 1, n: '',
        z: 'See <a class="cunliffe-xref" href="#" data-key="pollo/s">πολλός</a>.' }] }],
      'pollo/s': [{ key: 'pollo/s', head: 'πολλός', rows: [{ lv: 1, n: '', z: 'Much, many.' }] }],
    });
    // the stub paints the record's own markup, so the xref anchor is clickable
    grammataRender.mockImplementation((rec: any, el: HTMLElement) => {
      el.innerHTML = `<article class="t8-entry" data-head="${rec.head}">`
        + rec.rows.map((r: any) => r.z ?? '').join('') + '</article>';
    });
    const r = renderPopup();
    await screen.findByText('much');
    await fireEvent.click(screen.getByRole('button', { name: 'Cunliffe' }));
    await waitFor(() => expect(r.container.querySelector('a.cunliffe-xref')).toBeTruthy());
    return r;
  };

  it('opens the entry the pointer names, in place', async () => {
    const { container } = await setup();
    await fireEvent.click(container.querySelector('a.cunliffe-xref')!);
    await waitFor(() =>
      expect(container.querySelector('[data-head="πολλός"]')).toBeTruthy());
  });

  it('comes back to the entry it was called from', async () => {
    const { container } = await setup();
    await fireEvent.click(container.querySelector('a.cunliffe-xref')!);
    await waitFor(() => expect(container.querySelector('[data-head="πολλός"]')).toBeTruthy());

    await fireEvent.click(screen.getByRole('button', { name: /Back to πολύς/ }));
    await waitFor(() =>
      expect(container.querySelector('[data-head="πολύς"]')).toBeTruthy());
  });

  it('leaves the trail behind when the reader moves to another word', async () => {
    // A trail belongs to the word it was followed from; carrying it to the next
    // word would strand the reader inside a pointer chain they did not open.
    const { container, rerender } = await setup();
    await fireEvent.click(container.querySelector('a.cunliffe-xref')!);
    await waitFor(() => expect(container.querySelector('[data-head="πολλός"]')).toBeTruthy());

    await rerender({ token: { t: 'ἄλλο', k: 'a)/llo' } });
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: /Back to/ })).toBeNull());
  });
});
