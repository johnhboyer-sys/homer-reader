import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/svelte';
import { escapeRe, highlightPrefixMatches } from '../lib/text';
import Search from '../components/Search.svelte';
import type { BookData } from '../lib/data';

describe('regex helpers', () => {
  it.each(['(', '[', '*?', '\\', 'λόγος'])('escapes %s for direct RegExp use', (term) => {
    expect(() => new RegExp(escapeRe(term), 'u')).not.toThrow();
  });

  it.each([
    ['(', 'alpha ( beta', 'alpha <mark>(</mark> beta'],
    ['[', 'alpha [ beta', 'alpha <mark>[</mark> beta'],
    ['*?', 'alpha *? beta', 'alpha <mark>*?</mark> beta'],
    ['\\', 'alpha \\ beta', 'alpha <mark>\\</mark> beta'],
    ['λόγος', 'ὁ λόγος καλός', 'ὁ <mark>λόγος</mark> καλός'],
  ])('highlights %s without corrupting escaped text', (term, text, expected) => {
    expect(() => highlightPrefixMatches(text, [term])).not.toThrow();
    expect(highlightPrefixMatches(text, [term])).toBe(expected);
  });
});

// -- Search.svelte's new panels ("Every form of one word", "Two things near
// each other") must render their result snippets through the SAME sanitizer
// as the rest of the page (greekKwic's local `esc` / englishKwicAt's
// highlightPrefixMatches) — no new {@html} sink. These drive each panel
// end-to-end with a malicious Greek token and English phrase and assert the
// payload lands as escaped text, never as a parsed <script>/<img> element.
const { fixtureBook } = vi.hoisted(() => ({
  fixtureBook: {
    book: 1,
    segments: [
      {
        id: 'seg1',
        column: '1',
        greek: [
          {
            n: 1,
            text: '<script>xss</script> λόγος',
            tokens: [
              { t: '<script>xss</script>', o: 0, k: 'xss' },
              { t: 'λόγος', o: 22, k: 'logos' },
            ],
          },
        ],
        english: {
          text: 'Virtue <img src=x onerror=alert(1)> and honor.',
          notes: [],
          markers: [],
          bekker: [{ n: 1, offset: 0, real: true }],
        },
        chapterStarts: [],
        third: [],
      },
    ],
  } satisfies BookData,
}));

vi.mock('../lib/search', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/search')>();
  return {
    ...actual,
    search: vi.fn(async () => ({
      results: [
        {
          work: 'iliad',
          meta: {
            id: 'seg1', book: 1, column: '1',
            greek_head: '<script>xss</script> λόγος',
            greek_tokens: 'xss logos',
            english_head: 'Virtue <img src=x onerror=alert(1)> and honor.',
          },
          grkMatch: true, engMatch: true, grkPositions: [0], engPositions: [0],
        },
      ],
      failedWorks: [],
    })),
    searchCombo: vi.fn(async () => ({
      results: [
        {
          work: 'iliad',
          meta: {
            id: 'seg1', book: 1, column: '1',
            greek_head: '<script>xss</script> λόγος',
            greek_tokens: 'xss logos',
            english_head: 'Virtue and honor.',
          },
          grkMatch: true, engMatch: false, grkPositions: [0, 1], engPositions: [],
        },
      ],
      failedWorks: [],
    })),
  };
});

vi.mock('../lib/data', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/data')>();
  return {
    ...actual,
    fetchBook: vi.fn(async () => fixtureBook),
    fetchColumns: vi.fn(async () => ({ '1': [{ book: 1, lo: 1, hi: 1 }] })),
  };
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  window.history.replaceState(null, '', '/');
});

describe('Search.svelte new panels route snippets through the shared sanitizer', () => {
  it('"Every form of one word" panel renders a malicious token as escaped text, not markup', async () => {
    render(Search);

    await fireEvent.input(screen.getByLabelText('One word'), { target: { value: 'logos' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Find every form' }));

    // Two matches (Greek + English) land in the same chapter group, so it is
    // NOT auto-expanded (only single-instance groups are) — expand it.
    await fireEvent.click(await screen.findByRole('button', { name: /Whole book/ }));

    await screen.findByText(/xss/);
    const main = document.querySelector('.search-page') as HTMLElement;
    expect(main.querySelector('script')).toBeNull();
    expect(main.querySelector('img')).toBeNull();
    expect(main.innerHTML).toContain('&lt;script&gt;xss&lt;/script&gt;');
    // The two checks above would also hold for a sanitizer that STRIPS the
    // markup instead of escaping it — no <script>/<img> element is created
    // either way. `textContent` decodes HTML entities back to literal
    // characters, so this only passes when the tag survives as text the
    // reader can actually see, proving escape rather than strip.
    expect(main.textContent).toContain('<script>xss</script>');
    expect(main.textContent).toContain('<img src=x onerror=alert(1)>');
  });

  it('"Two things near each other" panel renders a malicious token as escaped text, not markup', async () => {
    render(Search);

    // Term 1 defaults to "Any form of this word" (a lemma slot, which would
    // hit the lemma-map fetch); switch both slots to a plain spelling match so
    // this test exercises only searchCombo + the render path.
    await fireEvent.change(screen.getByRole('combobox', { name: 'Kind for term 1' }), { target: { value: 'form' } });
    const [word1, word2] = screen.getAllByLabelText('Spelling');
    await fireEvent.input(word1, { target: { value: 'xss' } });
    await fireEvent.input(word2, { target: { value: 'logos' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Search these terms' }));

    // Two matched token positions land in one chapter group — expand it.
    await fireEvent.click(await screen.findByRole('button', { name: /Whole book/ }));
    // Two positions matched, so this asserts on ALL of them (findByText throws
    // on an ambiguous match; findAllByText does not).
    await screen.findAllByText(/xss/);
    const main = document.querySelector('.search-page') as HTMLElement;
    expect(main.querySelector('script')).toBeNull();
    expect(main.querySelector('img')).toBeNull();
    expect(main.innerHTML).toContain('&lt;script&gt;xss&lt;/script&gt;');
    // Same distinction as the panel above: a stripping sanitizer would also
    // leave no <script> element, so prove the payload is literally visible.
    expect(main.textContent).toContain('<script>xss</script>');
  });
});
