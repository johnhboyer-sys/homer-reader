import { cleanup, render, screen, waitFor } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import WordPopup from '../components/WordPopup.svelte';

// Dictionary-level homonyms get their own box. Distinct LEMMATA already did —
// they arrive as separate `analyses` entries — but a single analysis can carry
// several LSJ keys, and only lsj[0] used to reach the screen. These pin both the
// split and the cases where splitting would ADD a box without adding meaning.

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
      token: { t: 'ἔχων', k: 'e)/xwn' },
      anchor: { x: 0, y: 0 },
      onClose: vi.fn(),
    },
  });
}

const cards = (container: HTMLElement) =>
  Array.from(container.querySelectorAll('.analysis-card')).map(el => ({
    head: el.querySelector('.lemma')?.textContent?.trim() ?? '',
    gloss: el.querySelector('.gloss')?.textContent?.trim() ?? '',
    parse: el.querySelector('.parse')?.textContent?.trim() ?? '',
  }));

describe('LexiconPanel — one box per dictionary-level homonym', () => {
  it('splits an analysis whose LSJ homonyms each carry their own definition', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{
        lemma: 'e)/xw', gloss: 'have, hold',
        parse: 'pres part act masc nom sg',
        lsj: ['e)/xw1', 'e)/xw2'], cunliffe: [],
      }],
      lsj: [
        { key: 'e)/xw1', head: 'ἔχω', html: '<p>x</p>', short: 'have, hold' },
        { key: 'e)/xw2', head: 'ἔχω', html: '<p>y</p>', short: 'bear, carry, bring' },
      ],
      cunliffe: [],
    });
    const { container } = renderPopup();

    await waitFor(() => expect(cards(container)).toHaveLength(2));
    expect(cards(container)).toEqual([
      { head: 'ἔχω1', gloss: 'have, hold', parse: 'pres part act masc nom sg' },
      { head: 'ἔχω2', gloss: 'bear, carry, bring', parse: 'pres part act masc nom sg' },
    ]);
    // The homonym index is the ONLY thing distinguishing two identical
    // headwords, so it must actually render as a marked-up superscript.
    expect(container.querySelectorAll('.lemma sup.homonym')).toHaveLength(2);
  });

  it('gives the Homeric sense of ἄναλτος its own box beside the non-Homeric one', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{
        lemma: 'a)/naltos', gloss: 'insatiate', parse: 'masc nom sg',
        lsj: ['a)/naltos1', 'a)/naltos2'], cunliffe: [],
      }],
      lsj: [
        { key: 'a)/naltos1', head: 'ἄναλτος', html: '<p>x</p>', short: 'not to be filled, insatiate' },
        { key: 'a)/naltos2', head: 'ἄναλτος', html: '<p>y</p>', short: 'not salted' },
      ],
      cunliffe: [],
    });
    const { container } = renderPopup();

    await waitFor(() => expect(cards(container)).toHaveLength(2));
    expect(cards(container).map(c => c.gloss))
      .toEqual(['not to be filled, insatiate', 'not salted']);
  });

  it('does NOT split when LSJ derives no definition for either homonym (ὅς)', async () => {
    // ὅς¹/ὅς² have no derived short def. Splitting would print the shared
    // Morpheus gloss twice under the same headword — two boxes, no new
    // information. One box is the honest rendering.
    lookupWordMock.mockResolvedValue({
      analyses: [{
        lemma: 'o(/s', gloss: 'the; who; he, she, it',
        parse: 'masc acc pl (doric)', lsj: ['o(/s1', 'o(/s2'], cunliffe: [],
      }],
      lsj: [
        { key: 'o(/s1', head: 'ὅς', html: '<p>x</p>' },
        { key: 'o(/s2', head: 'ὅς', html: '<p>y</p>' },
      ],
      cunliffe: [],
    });
    const { container } = renderPopup();

    await waitFor(() => expect(screen.getByText('the; who; he, she, it')).toBeInTheDocument());
    expect(cards(container)).toEqual([
      { head: 'ὅς', gloss: 'the; who; he, she, it', parse: 'masc acc pl (doric)' },
    ]);
    expect(container.querySelector('sup.homonym')).toBeNull();
  });

  it('does not invent a second box when only one homonym has a definition', async () => {
    // Borrowing the sibling's definition would be a guess; the analysis keeps
    // its single Morpheus gloss instead.
    lookupWordMock.mockResolvedValue({
      analyses: [{
        lemma: 'kata/', gloss: 'downwards', parse: 'indeclform (prep)',
        lsj: ['kata/1', 'kata/2'], cunliffe: [],
      }],
      lsj: [
        { key: 'kata/1', head: 'κατά', html: '<p>x</p>', short: 'downwards' },
        { key: 'kata/2', head: 'κατά', html: '<p>y</p>' },
      ],
      cunliffe: [],
    });
    const { container } = renderPopup();

    await waitFor(() => expect(screen.getByText('downwards')).toBeInTheDocument());
    expect(cards(container)).toHaveLength(1);
    expect(cards(container)[0].gloss).toBe('downwards');
  });

  it('collapses two keys that resolve to the same definition', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{
        lemma: 'x', gloss: 'raw gloss', parse: 'noun',
        lsj: ['x1', 'x2'], cunliffe: [],
      }],
      lsj: [
        { key: 'x1', head: 'ξ', html: '<p>x</p>', short: 'same sense' },
        { key: 'x2', head: 'ξ', html: '<p>y</p>', short: 'same sense' },
      ],
      cunliffe: [],
    });
    const { container } = renderPopup();

    await waitFor(() => expect(cards(container).length).toBeGreaterThan(0));
    expect(cards(container)).toHaveLength(1);
  });

  it('omits the homonym index when the headwords already differ', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{
        lemma: 'q', gloss: 'raw', parse: 'noun',
        lsj: ['q1', 'q2'], cunliffe: [],
      }],
      lsj: [
        { key: 'q1', head: 'ἀλφά', html: '<p>x</p>', short: 'first sense' },
        { key: 'q2', head: 'βῆτα', html: '<p>y</p>', short: 'second sense' },
      ],
      cunliffe: [],
    });
    const { container } = renderPopup();

    await waitFor(() => expect(cards(container)).toHaveLength(2));
    expect(cards(container).map(c => c.head)).toEqual(['ἀλφά', 'βῆτα']);
    expect(container.querySelector('sup.homonym')).toBeNull();
  });

  it('leaves a single-key analysis exactly as it was — the ~94% case', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [{
        lemma: 'mh=nis', gloss: 'wrath', parse: 'fem nom sg',
        lsj: ['mh=nis'], cunliffe: [],
      }],
      // A short def exists, but a lone entry keeps the Morpheus gloss: this
      // change must not rewrite the text of the cards it doesn't split.
      lsj: [{ key: 'mh=nis', head: 'μῆνις', html: '<p>x</p>', short: 'wrath, ire' }],
      cunliffe: [],
    });
    const { container } = renderPopup();

    await waitFor(() => expect(cards(container)).toHaveLength(1));
    expect(cards(container)[0]).toEqual({ head: 'μῆνις', gloss: 'wrath', parse: 'fem nom sg' });
  });

  it('still renders distinct lemmata as separate boxes', async () => {
    lookupWordMock.mockResolvedValue({
      analyses: [
        { lemma: 'a', gloss: 'first', parse: 'noun', lsj: ['a1'], cunliffe: [] },
        { lemma: 'b', gloss: 'second', parse: 'verb', lsj: ['b1'], cunliffe: [] },
      ],
      lsj: [
        { key: 'a1', head: 'α', html: '<p>x</p>' },
        { key: 'b1', head: 'β', html: '<p>y</p>' },
      ],
      cunliffe: [],
    });
    const { container } = renderPopup();

    await waitFor(() => expect(cards(container)).toHaveLength(2));
    expect(cards(container).map(c => c.gloss)).toEqual(['first', 'second']);
  });
});

// The mocked cases above pin the rule; this one pins the DATA CONTRACT — that
// the corpus actually ships what the rule needs (LsjEntry.short), so the split
// happens for real tokens and not just for fixtures.
describe('LexiconPanel — against the built corpus', () => {
  // NOT import.meta.url: under jsdom it resolves relatives against Vite's HTTP
  // base, so every existsSync came back false and the check passed vacuously.
  const root = path.resolve(process.cwd(), '../app/public/data');
  const load = (p: string) => {
    const f = path.join(root, p);
    return fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf-8')) : null;
  };

  it('splits ἔχων into ἔχω¹ and ἔχω² using real shipped data', async (ctx) => {
    const analyses = load('iliad/analyses.json');
    const shard = load('lsj/e.json');
    // Skip loudly rather than pass quietly: a green result here must mean the
    // corpus was actually checked.
    if (!analyses || !shard) return ctx.skip();

    const entry = analyses['e)/xwn'];
    expect(entry, 'e)/xwn missing from the built analyses').toBeTruthy();
    const multi = entry.find((a: { lsj: string[] }) => a.lsj.length > 1);
    expect(multi, 'e)/xwn no longer carries a multi-homonym analysis').toBeTruthy();

    lookupWordMock.mockResolvedValue({
      analyses: [multi],
      lsj: multi.lsj.map((k: string) => shard[k]).filter(Boolean),
      cunliffe: [],
    });
    const { container } = renderPopup();

    await waitFor(() => expect(cards(container).length).toBeGreaterThan(1));
    const rendered = cards(container);
    expect(rendered.map(c => c.gloss).sort())
      .toEqual(['bear, carry, bring', 'have, hold']);
    // Same headword on both, so the index has to be there to tell them apart.
    expect(new Set(rendered.map(c => c.head)).size).toBe(rendered.length);
  });
});
