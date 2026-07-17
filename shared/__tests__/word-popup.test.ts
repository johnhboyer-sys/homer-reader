import { cleanup, fireEvent, render, screen } from '@testing-library/svelte';
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

  it('renders a modal dialog with a backdrop when NOT docked', async () => {
    lookupWordMock.mockResolvedValue(analysis);
    const { container } = renderPopup({ docked: false });

    const sidebar = container.querySelector('.word-sidebar');
    expect(sidebar).not.toHaveClass('docked');
    expect(sidebar).toHaveAttribute('role', 'dialog');
    expect(sidebar).toHaveAttribute('aria-modal', 'true');
    expect(container.querySelector('.popup-backdrop')).not.toBeNull();
  });
});
