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

function renderPopup() {
  return render(WordPopup, {
    props: {
      work: 'iliad',
      token: { t: 'μῆνις', k: 'mhnis' },
      anchor: { x: 0, y: 0 },
      onClose: vi.fn(),
    },
  });
}

describe('WordPopup.svelte — dictionary tabs', () => {
  it('shows the LSJ · Cunliffe · Logeion tab row, LSJ selected by default', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{ lemma: 'mh=nis', gloss: 'wrath', parse: 'noun', lsj: ['mh=nis'], cunliffe: ['mh=nis'] }],
      lsj: [{ key: 'mh=nis', head: 'μῆνις', html: '<p>wrath, ire</p>' }],
      cunliffe: [{ key: 'mh=nis', head: 'μῆνις', html: '<div class="cunliffe-sense">Wrath, ire.</div>', src: 'lex' }],
    });
    renderPopup();

    const lsjTab = await screen.findByRole('tab', { name: 'LSJ' });
    const cunliffeTab = screen.getByRole('tab', { name: 'Cunliffe' });
    const logeionLink = screen.getByRole('link', { name: /Logeion/ });

    expect(lsjTab).toHaveAttribute('aria-selected', 'true');
    expect(cunliffeTab).toHaveAttribute('aria-selected', 'false');
    expect(logeionLink).toHaveAttribute('target', '_blank');
    expect(logeionLink).toHaveAttribute('rel', 'noopener');
    expect(logeionLink.getAttribute('href')).toContain('logeion.uchicago.edu/');
    expect(logeionLink.getAttribute('href')).toContain(encodeURIComponent('μῆνις'));

    // LSJ panel visible, Cunliffe panel hidden, until the tab is switched.
    expect(screen.getByText('wrath, ire')).toBeVisible();
    expect(screen.getByText('Wrath, ire.').closest('[role="tabpanel"]')).toHaveAttribute('hidden');

    await fireEvent.click(cunliffeTab);
    expect(cunliffeTab).toHaveAttribute('aria-selected', 'true');
    expect(lsjTab).toHaveAttribute('aria-selected', 'false');
    expect(screen.getByText('Wrath, ire.').closest('[role="tabpanel"]')).not.toHaveAttribute('hidden');
  });

  it('shows a quiet "not in Cunliffe" empty state when no entry matched', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{ lemma: 'a)/gnwstos', gloss: 'unknown', parse: 'adj', lsj: ['a)/gnwstos'], cunliffe: [] }],
      lsj: [{ key: 'a)/gnwstos', head: 'ἄγνωστος', html: '<p>unknown</p>' }],
      cunliffe: [],
    });
    renderPopup();

    const cunliffeTab = await screen.findByRole('tab', { name: 'Cunliffe' });
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

    const lsjTab = await screen.findByRole('tab', { name: 'LSJ' });
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
