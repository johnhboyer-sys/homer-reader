import { cleanup, render, waitFor } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import WordPopup from '../components/WordPopup.svelte';

// One card per DICTIONARY ENTRY (John, 2026-08-30). An analysis can name
// several LSJ keys — 2,335 of them across this corpus — and only lsj[0] used to
// reach the screen. Keying on the entry means no card names more than one
// entry, and every card opens the entry it is actually about.
//
// The earlier rule folded homonyms unless each carried its own short
// definition, because two boxes with one gloss added no information. That
// reasoning expired when the entry began opening under the card tapped: ὅς's
// two cards now open LSJ's ὅς (A) and ὅς (B) separately, so the split is the
// information.

const { lookupWordMock, headsMock } = vi.hoisted(() => ({
  lookupWordMock: vi.fn(),
  headsMock: vi.fn(),
}));

vi.mock('../lib/data', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/data')>();
  return {
    ...actual,
    fetchLemmata: vi.fn(async () => ({})),
    fetchLsjHeads: headsMock,
    lookupWord: lookupWordMock,
  };
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderPopup(token = { t: 'ἔχων', k: 'e)/xwn' }) {
  return render(WordPopup, {
    props: { work: 'iliad', token, anchor: { x: 0, y: 0 }, onClose: vi.fn() },
  });
}

const cards = (container: HTMLElement) =>
  Array.from(container.querySelectorAll('.analysis-card')).map(el => ({
    head: el.querySelector('.lemma')?.textContent?.trim() ?? '',
    gloss: el.querySelector('.gloss')?.textContent?.trim() ?? '',
    parse: el.querySelector('.parse')?.textContent?.replace(/\s+/g, ' ').trim() ?? '',
  }));

describe('one card per dictionary entry', () => {
  it('gives every named entry its own card, each with its own definition', async () => {
    headsMock.mockResolvedValue({
      'e)/xw1': { head: 'ἔχω', short: 'have, hold' },
      'e)/xw2': { head: 'ἔχω', short: 'bear, carry, bring' },
    });
    lookupWordMock.mockResolvedValue({
      analyses: [{
        lemma: 'e)/xw', gloss: 'have, hold',
        parse: 'pres part act masc nom sg',
        lsj: ['e)/xw1', 'e)/xw2'], cunliffe: [],
      }],
      lsj: [], cunliffe: [],
    });
    const { container } = renderPopup();
    await waitFor(() => expect(cards(container)).toHaveLength(2));
    expect(cards(container).map(c => c.gloss))
      .toEqual(['have, hold', 'bear, carry, bring']);
  });

  it('splits even when the two entries share one gloss, because each opens its own entry', async () => {
    // ὅς: LSJ derives no short definition for either homonym. The old rule
    // folded these; now each card opens a different LSJ entry, so folding them
    // would hide one of the two entries entirely.
    headsMock.mockResolvedValue({
      'o(/s1': { head: 'ὅς' },
      'o(/s2': { head: 'ὅς' },
    });
    lookupWordMock.mockResolvedValue({
      analyses: [{
        lemma: 'o(/s', gloss: 'the; who; he, she, it',
        parse: 'masc nom sg', lsj: ['o(/s1', 'o(/s2'], cunliffe: ['o(/s'],
      }],
      lsj: [], cunliffe: [],
    });
    const { container } = renderPopup({ t: 'ὅς', k: 'o(/s' });
    await waitFor(() => expect(cards(container)).toHaveLength(2));
  });

  it('still renders distinct lemmata as separate cards', async () => {
    headsMock.mockResolvedValue({ a1: { head: 'ἀλφά' }, b1: { head: 'βῆτα' } });
    lookupWordMock.mockResolvedValue({
      analyses: [
        { lemma: 'a', gloss: 'first', parse: 'fem nom sg', lsj: ['a1'], cunliffe: [] },
        { lemma: 'b', gloss: 'second', parse: 'fem nom sg', lsj: ['b1'], cunliffe: [] },
      ],
      lsj: [], cunliffe: [],
    });
    const { container } = renderPopup();
    await waitFor(() => expect(cards(container)).toHaveLength(2));
    expect(cards(container).map(c => c.head)).toEqual(['ἀλφά', 'βῆτα']);
  });

  it('joins two analyses of the same entry into ONE card, keeping both parses', async () => {
    headsMock.mockResolvedValue({ 'mh=nis': { head: 'μῆνις' } });
    lookupWordMock.mockResolvedValue({
      analyses: [
        { lemma: 'mh=nis', gloss: 'wrath', parse: 'fem nom sg', lsj: ['mh=nis'], cunliffe: [] },
        { lemma: 'mh=nis', gloss: 'wrath', parse: 'fem voc sg', lsj: ['mh=nis'], cunliffe: [] },
      ],
      lsj: [], cunliffe: [],
    });
    const { container } = renderPopup();
    await waitFor(() => expect(cards(container)).toHaveLength(1));
    expect(container.querySelectorAll('.analysis-card .parse')).toHaveLength(2);
  });
});

describe("the homograph letter is LSJ's own, never the key's digit", () => {
  it("prints LSJ's letter even when it contradicts the digit", async () => {
    // κάρ's key is ka/r2 and LSJ's own letter is (A). Five keys in this corpus
    // disagree that way; deriving the mark from the digit prints a lie.
    headsMock.mockResolvedValue({ 'ka/r2': { head: 'κάρ', hom: 'A' } });
    lookupWordMock.mockResolvedValue({
      analyses: [{ lemma: 'ka/r', gloss: 'hair', parse: 'neut nom sg', lsj: ['ka/r2'], cunliffe: [] }],
      lsj: [], cunliffe: [],
    });
    const { container } = renderPopup({ t: 'κάρ', k: 'ka/r' });
    await waitFor(() => expect(cards(container)).toHaveLength(1));
    expect(container.querySelector('.lemma sup.homonym')?.textContent).toBe('(A)');
  });

  it('prints no mark at all when LSJ printed none, though the key is numbered', async () => {
    // 191 of 627 numbered keys here carry no letter — 30%. They must show
    // nothing rather than a numeral LSJ never wrote.
    headsMock.mockResolvedValue({ 'a)/llos1': { head: 'ἄλλος' } });
    lookupWordMock.mockResolvedValue({
      analyses: [{ lemma: 'a)/llos', gloss: 'other', parse: 'masc nom sg', lsj: ['a)/llos1'], cunliffe: [] }],
      lsj: [], cunliffe: [],
    });
    const { container } = renderPopup({ t: 'ἄλλος', k: 'a)/llos' });
    await waitFor(() => expect(cards(container)).toHaveLength(1));
    expect(container.querySelector('.lemma sup.homonym')).toBeNull();
  });
});

describe('which definition a card shows', () => {
  const oneCard = async (analyses: unknown[], heads: Record<string, unknown>) => {
    headsMock.mockResolvedValue(heads);
    lookupWordMock.mockResolvedValue({ analyses, lsj: [], cunliffe: [] });
    const { container } = renderPopup();
    await waitFor(() => expect(cards(container).length).toBeGreaterThan(0));
    return cards(container).map(c => c.gloss);
  };

  it('prefers a real gloss over an empty one from the same entry', async () => {
    // Two analyses of one entry, the first glossed "". First-exact-wins would
    // leave the card blank.
    expect(await oneCard(
      [
        { lemma: 'x', gloss: '', parse: 'masc gen sg', lsj: ['x1'], cunliffe: [] },
        { lemma: 'x', gloss: 'builder, architect', parse: 'masc gen sg', lsj: ['x1'], cunliffe: [] },
      ],
      { x1: { head: 'ξ' } },
    )).toEqual(['builder, architect']);
  });

  it("does not let one entry's gloss stand in for a sibling that has none", async () => {
    // A fan-out stamps its gloss onto every entry it names. Where the sibling's
    // OWN analysis has no gloss, blank is honest and "two" is another word's
    // meaning.
    expect(await oneCard(
      [
        { lemma: 'du/w', gloss: 'two', parse: 'card', lsj: ['du/w1', 'du/w2'], cunliffe: [] },
        { lemma: 'du/w', gloss: '', parse: 'pres', lsj: ['du/w2'], cunliffe: [] },
      ],
      { 'du/w1': { head: 'δύω' }, 'du/w2': { head: 'δύω' } },
    )).toEqual(['two', '']);
  });

  it("takes LSJ's own sense over a gloss fanned out from a sibling entry", async () => {
    // νέω: one unresolved analysis names all three entries and glosses them
    // "swim", so νέω (B) would read "swim" while opening the entry for "spin".
    expect(await oneCard(
      [{ lemma: 'ne/w', gloss: 'swim', parse: 'pres', lsj: ['ne/w1', 'ne/w2'], cunliffe: [] }],
      {
        'ne/w1': { head: 'νέω', short: 'swim' },
        'ne/w2': { head: 'νέω', short: 'spin' },
      },
    )).toEqual(['swim', 'spin']);
  });

  it('keeps an exact gloss even when the entry carries a short definition', async () => {
    // An exact gloss is already about this entry, and is usually the crisper
    // of the two.
    expect(await oneCard(
      [{ lemma: 'mh=nis', gloss: 'wrath', parse: 'fem nom sg', lsj: ['mh=nis'], cunliffe: [] }],
      { 'mh=nis': { head: 'μῆνις', short: 'wrath, anger, esp. of the gods' } },
    )).toEqual(['wrath']);
  });
});

describe('the dialect label', () => {
  const parseOf = async (parse: string) => {
    headsMock.mockResolvedValue({ k1: { head: 'κ' } });
    lookupWordMock.mockResolvedValue({
      analyses: [{ lemma: 'k', gloss: 'g', parse, lsj: ['k1'], cunliffe: [] }],
      lsj: [], cunliffe: [],
    });
    const { container } = renderPopup();
    await waitFor(() => expect(cards(container).length).toBeGreaterThan(0));
    return container.querySelector('.analysis-card .parse')!;
  };

  it('prints the dialect, because Homer is Epic and LSJ is not', async () => {
    const el = await parseOf('pres ind act 3rd sg (epic ionic)');
    expect(el.querySelector('.parse-dialect')?.textContent).toBe('epic ionic');
    expect(el.textContent).toContain('pres ind act 3rd sg');
  });

  it('prints a label naming attic too, which aristotle would have suppressed', async () => {
    // 7,443 analyses here name attic; 3,303 of them are "attic epic ionic".
    // Suppressing on attic's presence would hide exactly those.
    const el = await parseOf('pres ind act 3rd sg (attic epic ionic)');
    expect(el.querySelector('.parse-dialect')?.textContent).toBe('attic epic ionic');
  });

  it('shows no chip when the trailing parenthesis names no dialect', async () => {
    const el = await parseOf('indeclform (particle)');
    expect(el.querySelector('.parse-dialect')).toBeNull();
    expect(el.textContent?.trim()).toBe('indeclform (particle)');
  });
});

describe('against the built corpus', () => {
  const DATA = path.resolve(process.cwd(), '../app/public/data');

  it('reads κάρ\'s letter from the shipped manifest, and it is not the digit', (ctx) => {
    const f = path.join(DATA, 'lsj-heads.json');
    if (!fs.existsSync(f)) {
      ctx.skip();
      return;
    }
    const heads = JSON.parse(fs.readFileSync(f, 'utf8'));
    expect(heads['ka/r2']).toBeDefined();
    expect(heads['ka/r2'].hom).toBe('A');
    expect(heads['ka/r2'].head).toBe('κάρ');
  });

  it('carries a headword for every key the analyses name', (ctx) => {
    const f = path.join(DATA, 'lsj-heads.json');
    if (!fs.existsSync(f) || !fs.existsSync(path.join(DATA, 'iliad', 'analyses.json'))) {
      ctx.skip();
      return;
    }
    const heads = JSON.parse(fs.readFileSync(f, 'utf8'));
    const analyses = JSON.parse(fs.readFileSync(path.join(DATA, 'iliad', 'analyses.json'), 'utf8'));
    const missing = new Set<string>();
    for (const list of Object.values(analyses) as { lsj?: string[] }[][]) {
      for (const a of list) for (const k of a.lsj ?? []) if (!heads[k]) missing.add(k);
    }
    expect([...missing]).toEqual([]);
  });
});
