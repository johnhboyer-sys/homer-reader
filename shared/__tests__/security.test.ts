import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render } from '@testing-library/svelte';
import { escapeRe, highlightPrefixMatches } from '../lib/text';
import Search from '../components/Search.svelte';
import { CORPUS, HAVE_CORPUS, serveCorpus } from './serve-corpus';

// The first search in a file reads the corpus cold.
vi.setConfig({ testTimeout: 60000 });

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

// -- The search page (the port of aristotle-reader's) must draw corpus text and
// whatever arrives in the address as text, never as markup. The real corpus is
// served with a payload planted at Il. 1.34, where θαλάσσης and Murray's "sea"
// are hits: the Greek word becomes a <script>, the English word a <u> (the
// same length, so the translation's line marks still fall where they did).
const plant = () => serveCorpus({
  'iliad/book-01.json': (b) => {
    const seg = b.segments[0];
    const line = seg.greek.find((l: { n: number }) => l.n === 34);
    for (const t of line.tokens) if (t.t === 'θαλάσσης') t.t = '<script>xss</script>';
    line.text = line.text.replace('θαλάσσης', '<script>xss</script>');
    seg.english.text = seg.english.text.replace('loud-resounding sea', 'loud-resounding <u>');
    return b;
  },
});

afterEach(() => {
  cleanup();
  window.history.replaceState(null, '', '/');
});

describe('the search page draws corpus text and the address as text', () => {
  // textContent decodes entities, so the payload being visible there proves it
  // was escaped; a sanitizer that STRIPPED it would leave no element either,
  // and would fail these.
  const results = () => document.querySelector('.sx-results') as HTMLElement;
  const settled = () => vi.waitFor(() => expect(document.querySelector('[role="status"]')?.textContent).toMatch(/\d+ scenes?|No scenes/), { timeout: 30000 });
  beforeEach((ctx) => {
    if (!HAVE_CORPUS) { console.warn(`security: no corpus at ${CORPUS}; skipping`); ctx.skip(); }
    plant();
  });

  it('a Greek and an English hit whose words are markup', async () => {
    window.history.replaceState(null, '', '/search/?g=θάλασσα&e=sea&t=murray&w=iliad&b=1&op=or');
    render(Search);
    await settled();
    await vi.waitFor(() => expect(results().textContent).toContain('<script>xss</script>'));
    expect(results().textContent).toContain('loud-resounding <u>');
    expect(results().querySelector('script, u')).toBeNull();
  });

  it('two words near each other, one of them markup', async () => {
    window.history.replaceState(null, '', '/search/?c=l:qalassa&c=l:qis&cw=3&w=iliad&b=1');
    render(Search);
    await settled();
    await vi.waitFor(() => expect(results().textContent).toContain('<script>xss</script>'));
    expect(results().querySelector('script')).toBeNull();
  });

  it('a hostile query and speaker in the address', async () => {
    const bad = '<img src=x onerror=alert(1)>';
    window.history.replaceState(null, '', `/search/?g=${encodeURIComponent(bad)}&e=${encodeURIComponent('<script>y</script>')}&spk=${encodeURIComponent(bad)}`);
    render(Search);
    await settled();
    const page = document.querySelector('.search-page') as HTMLElement;
    expect(page.querySelector('img, script')).toBeNull();
    expect((page.querySelector('#grk-input') as HTMLTextAreaElement).value).toBe(bad);
    expect((page.querySelector('#eng-input') as HTMLTextAreaElement).value).toBe('<script>y</script>');
  });
});
