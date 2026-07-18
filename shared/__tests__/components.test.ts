import { fireEvent, render, screen, within } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Reader from '../components/Reader.svelte';
import Search from '../components/Search.svelte';
import type { BookData } from '../lib/data';
import type { Work } from '../lib/works';

// These Reader tests need a real Work shape (translations, citation scheme)
// for the 'EN'/'Isa' fixture ids they render — a bekker-scheme work with a
// Rackham-style primary translation, and a busse-scheme work with lineless
// citations. Neither id is in the real registry (Plato-only now), so fixture
// metas stand in rather than depending on a real registry entry.
vi.mock('../lib/works', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/works')>();
  const fixtures: Record<string, Work> = {
    EN: {
      id: 'EN', title: 'Fixture Bekker Work', abbr: 'EN', author: 'Test',
      books: 1, bookLabels: ['1'],
      greekEdition: 'Test edition',
      greekSource: { short: 'Test', full: 'Test edition, full citation.', licence: 'Test licence' },
      translations: [{ id: 'rackham', name: 'Test Translator (Test, 1900)', short: 'Rackham', slot: 'english' }],
      blurb: 'Fixture work for Reader.svelte tests (bekker scheme, the default).',
    },
    Isa: {
      id: 'Isa', title: 'Fixture Busse Work', abbr: 'Isa', author: 'Test',
      books: 1, bookLabels: ['1'],
      greekEdition: 'Test edition',
      greekSource: { short: 'Test', full: 'Test edition, full citation.', licence: 'Test licence' },
      translations: [{ id: 'owen', name: 'Test Translator (Test, 1900)', short: 'Owen', slot: 'english', footnotes: true }],
      citation: { scheme: 'busse', hideLineNumbers: true },
      blurb: 'Fixture work for Reader.svelte tests (busse scheme, lineless).',
    },
  };
  return { ...actual, getWork: (id: string) => fixtures[id] ?? actual.getWork(id) };
});

const { fixtureBook } = vi.hoisted(() => ({
  fixtureBook: {
    book: 1,
    segments: [
      {
        id: 'seg1',
        column: '1094a',
        greek: [
          { n: 1, text: 'λόγος ἀρετή', tokens: [{ t: 'λόγος', o: 0, k: 'logos' }, { t: 'ἀρετή', o: 6, k: 'areth' }] },
        ],
        english: {
          text: 'Virtue (test) and κόσμος are discussed here.',
          notes: [],
          markers: [],
          bekker: [{ n: 1, offset: 0, real: true }],
        },
        chapterStarts: [{ chapter: '1', beforeLine: 1, wordIndex: 0, engOffset: 0, bekker: '1094a' }],
        third: [
          {
            chapter: '1',
            cont: false,
            text: 'Ostwald says virtue (test) beside κόσμος.',
            bekker: [{ n: 1, offset: 0, real: true }],
          },
        ],
      },
    ],
  } satisfies BookData,
}));

vi.mock('../lib/search', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/search')>();
  return {
    ...actual,
    search: vi.fn(async () => [
      {
        work: 'EN',
        meta: { id: 'seg1', book: 1, column: '1094a', greek_head: 'λόγος', greek_tokens: 'logos', english_head: 'Virtue (test) and κόσμος' },
        grkMatch: true,
        engMatch: true,
        grkPositions: [0],
        engPositions: [0],
      },
    ]),
  };
});

vi.mock('../lib/data', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/data')>();
  return {
    ...actual,
    fetchBook: vi.fn(async () => fixtureBook),
    fetchChapters: vi.fn(async () => ({
      '1': [{ chapter: '1', column: '1094a', line: '1', bekker: '1094a' }],
    })),
    // WordPopup → LexiconPanel resolves an entry on token click; stub it so the
    // lookup presentation renders without a network fetch.
    lookupWord: vi.fn(async () => ({ analyses: [], lsj: [], cunliffe: [] })),
    fetchLemmata: vi.fn(async () => ({})),
  };
});

afterEach(() => {
  vi.clearAllMocks();
  window.history.replaceState(null, '', '/');
  // Posture/view/translation choices persist in localStorage; clear so one
  // test's saved posture can't leak into the next render.
  try { localStorage.clear(); } catch { /* jsdom */ }
});

describe('Search.svelte', () => {
  // Smoke test: mounts, accepts Greek + English queries (including a
  // parenthesis metacharacter and a Unicode Greek term), and runs a search
  // without throwing. Asserting exact result-card markup would couple this to
  // the grouping internals; the value here is that mount + input + submit +
  // the (mocked) search call all wire together and nothing crashes.
  it('mounts and runs a search with metacharacter + Unicode input without throwing', async () => {
    const { search } = await import('../lib/search');
    render(Search);

    await fireEvent.input(screen.getByLabelText('Greek'), { target: { value: 'λόγ*' } });
    await fireEvent.input(screen.getByLabelText('English'), { target: { value: 'virtue (test) κόσμος' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    // The wired search path was invoked with the typed queries.
    expect(search).toHaveBeenCalled();
    // The form is still mounted (no crash / unhandled render error): the Greek
    // searchbox persists after the search runs.
    expect(screen.getByLabelText('Greek')).toBeInTheDocument();
  });
});

describe('Reader.svelte', () => {
  // Smoke test: mounts with fixture book data plus highlight URL params
  // (Greek wildcard + English phrase containing a metacharacter) and renders
  // the fixture prose without throwing in the highlight code paths.
  it('renders fixture book data with highlight params applied', async () => {
    window.history.replaceState(null, '', '/EN/book/1?hlg=λόγ*&hle=virtue%20(test)%20κόσμος&loc=1094a:1');

    render(Reader, { props: { work: 'EN', bookNum: 1, bookData: fixtureBook } });

    // Bekker column from the fixture renders.
    expect(await screen.findByText('1094a')).toBeInTheDocument();
    // Greek token from the fixture renders as a token span.
    expect(screen.getByText('λόγος')).toHaveClass('tok');
    // The English column renders the fixture prose (the highlight code path ran
    // over a phrase containing a parenthesis metacharacter without throwing).
    const main = screen.getByRole('main');
    expect(within(main).getAllByText(/virtue/i).length).toBeGreaterThan(0);
  });

  it('renders sidecar English paragraph markers as paragraph breaks', async () => {
    window.history.replaceState(null, '', '/EN/book/1?trans=rackham');
    const book: BookData = structuredClone(fixtureBook);
    book.segments[0].english = {
      text: 'First paragraph. Second paragraph.',
      notes: [],
      markers: [{ kind: 'paragraph', n: '', offset: 'First paragraph.'.length }],
      bekker: [{ n: 1, offset: 0, real: true }],
    };

    const { container } = render(Reader, { props: { work: 'EN', bookNum: 1, bookData: book } });

    expect(await screen.findByText('First paragraph.')).toBeInTheDocument();
    expect(container.querySelectorAll('.english-col .para-br')).toHaveLength(1);
    expect(screen.getByText(/Second paragraph/)).toBeInTheDocument();
  });

  it('keeps English prose without paragraph markers on the existing flat path', async () => {
    window.history.replaceState(null, '', '/EN/book/1?trans=rackham');
    const book: BookData = structuredClone(fixtureBook);
    book.segments[0].english = {
      text: 'First paragraph. Second paragraph.',
      notes: [],
      markers: [],
      bekker: [{ n: 1, offset: 0, real: true }],
    };

    const { container } = render(Reader, { props: { work: 'EN', bookNum: 1, bookData: book } });

    expect(await screen.findByText(/First paragraph\. Second paragraph\./)).toBeInTheDocument();
    expect(container.querySelectorAll('.english-col .para-br')).toHaveLength(0);
  });

  it('keeps existing sidenote and figure inline markers out of rendered prose', async () => {
    window.history.replaceState(null, '', '/Isa/book/1');
    const book: BookData = structuredClone(fixtureBook);
    book.segments[0].english = {
      text: 'Alpha [[s1]] beta [[fig2]] gamma.',
      notes: [],
      markers: [],
      bekker: [{ n: 1, offset: 0, real: true }],
    };

    const { container } = render(Reader, { props: { work: 'Isa', bookNum: 1, bookData: book } });

    expect(await screen.findByText(/Alpha/)).toBeInTheDocument();
    expect(container.textContent).toContain('Alpha beta gamma.');
    expect(container.textContent).not.toContain('[[s1]]');
    expect(container.textContent).not.toContain('[[fig2]]');
  });
});

describe('Reader.svelte — Reading Mode posture', () => {
  it('toggles Reading Mode with the `r` key and persists the posture', async () => {
    window.history.replaceState(null, '', '/EN/book/1');
    const { container } = render(Reader, { props: { work: 'EN', bookNum: 1, bookData: fixtureBook } });
    await screen.findByText('1094a');

    const body = container.querySelector('.reader-body')!;
    expect(body).not.toHaveClass('reading-mode');

    await fireEvent.keyDown(window, { key: 'r' });
    expect(body).toHaveClass('reading-mode');
    expect(localStorage.getItem('reader-posture')).toBe('reading');

    await fireEvent.keyDown(window, { key: 'r' });
    expect(body).not.toHaveClass('reading-mode');
    expect(localStorage.getItem('reader-posture')).toBe('scholar');
  });

  it('ignores the `r` key while focus is in a text field', async () => {
    window.history.replaceState(null, '', '/EN/book/1');
    const { container } = render(Reader, { props: { work: 'EN', bookNum: 1, bookData: fixtureBook } });
    await screen.findByText('1094a');

    const input = document.createElement('input');
    document.body.appendChild(input);
    input.focus();
    await fireEvent.keyDown(window, { key: 'r' });
    expect(container.querySelector('.reader-body')).not.toHaveClass('reading-mode');
    input.remove();
  });

  it('the posture button toggles Reading Mode and reflects aria-pressed', async () => {
    window.history.replaceState(null, '', '/EN/book/1');
    const { container } = render(Reader, { props: { work: 'EN', bookNum: 1, bookData: fixtureBook } });
    const btn = await screen.findByRole('button', { name: /Reading Mode/i });
    expect(btn).toHaveAttribute('aria-pressed', 'false');

    await fireEvent.click(btn);
    expect(container.querySelector('.reader-body')).toHaveClass('reading-mode');
    const scholarBtn = screen.getByRole('button', { name: /Scholar view/i });
    expect(scholarBtn).toHaveAttribute('aria-pressed', 'true');
  });

  it('opens in Reading Mode from ?mode=reading', async () => {
    window.history.replaceState(null, '', '/EN/book/1?mode=reading');
    const { container } = render(Reader, { props: { work: 'EN', bookNum: 1, bookData: fixtureBook } });
    await screen.findByText(/Virtue/i);
    expect(container.querySelector('.reader-body')).toHaveClass('reading-mode');
    // Single reading column present; no parallel Greek column in the reading body.
    expect(container.querySelector('.reading-col')).not.toBeNull();
  });
});

describe('Reader.svelte — lexicon presentation breakpoint', () => {
  const defaultMatchMedia = () =>
    vi.fn().mockImplementation((query: string) => ({
      matches: false, media: query, onchange: null,
      addListener: vi.fn(), removeListener: vi.fn(),
      addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn(),
    }));

  function setMatchMedia(matcher: (q: string) => boolean) {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: matcher(query), media: query, onchange: null,
      addListener: vi.fn(), removeListener: vi.fn(),
      addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn(),
    })) as unknown as typeof window.matchMedia;
  }

  afterEach(() => {
    // Restore the setup's matches:false default so this describe can't leak a
    // custom matchMedia into other suites.
    window.matchMedia = defaultMatchMedia() as unknown as typeof window.matchMedia;
  });

  it('opens a DOCKED, non-modal lexicon rail at ≥1100px', async () => {
    setMatchMedia((q) => q.includes('min-width: 1100px'));
    window.history.replaceState(null, '', '/EN/book/1');
    render(Reader, { props: { work: 'EN', bookNum: 1, bookData: fixtureBook } });

    const tok = await screen.findByText('λόγος');
    await fireEvent.click(tok);

    const sidebar = document.querySelector('.word-sidebar');
    expect(sidebar).toHaveClass('docked');
    expect(sidebar).toHaveAttribute('role', 'region');
    expect(document.querySelector('.popup-backdrop')).toBeNull();
  });

  it('opens the anchored MODAL popup below 1100px', async () => {
    setMatchMedia(() => false);
    window.history.replaceState(null, '', '/EN/book/1');
    render(Reader, { props: { work: 'EN', bookNum: 1, bookData: fixtureBook } });

    const tok = await screen.findByText('λόγος');
    await fireEvent.click(tok);

    const sidebar = document.querySelector('.word-sidebar');
    expect(sidebar).not.toHaveClass('docked');
    expect(sidebar).toHaveAttribute('role', 'dialog');
    expect(document.querySelector('.popup-backdrop')).not.toBeNull();
  });
});

describe('Reader.svelte — verse-line (epic) rendering', () => {
  // 'iliad' is the real registry work (citation.scheme: 'verse-line'), not a
  // fixture — no mock needed for epicVerse to derive true off schemeFor. Lines
  // n=1..5,7 (a real vulgate gap: 6 is missing) exercise gutter-tick logic
  // (1 and every multiple of 5) against the line's OWN n, never a computed
  // index; n=7 is bracketed (athetized/bracketed in the editorial tradition).
  const verseBook = (bracketLine7: boolean): BookData => ({
    book: 1,
    segments: [
      {
        id: 'seg1',
        column: '1',
        greek: [1, 2, 3, 4, 5, 7].map((n) => ({
          n,
          text: `Greek line ${n}`,
          tokens: [{ t: `tok${n}`, o: 0, k: `key${n}` }],
          ...(n === 7 && bracketLine7 ? { bracketed: true } : {}),
        })),
        english: { text: 'English filler.', notes: [], markers: [] },
      },
    ],
  });

  it('renders one block per Greek line with gutter ticks on 1 and 5 only (n=7 gap keeps its own id)', async () => {
    window.history.replaceState(null, '', '/iliad/book/1');
    const { container } = render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: verseBook(true) } });

    const lines = container.querySelectorAll('.greek-line');
    expect(lines).toHaveLength(6);

    const nums = Array.from(container.querySelectorAll('.line-num')).map((el) => el.textContent);
    expect(nums).toEqual(['1', '', '', '', '5', '']);

    // The scheme-derived epicVerse flag scopes the verse-line class.
    expect(container.querySelector('.reader-body')).toHaveClass('verse-line');
    // Line 7's DOM id carries its real vulgate number (the gap is data, not a
    // bug) — a computed index would have produced "L1-6".
    expect(container.querySelector('#L1-7')).not.toBeNull();
    // Token interactivity flows through unchanged even inside a verse line.
    expect(container.querySelector('#L1-7 .tok')).not.toBeNull();
  });

  it('marks a bracketed line with the bracket class/tooltip/glyphs and shows the legend once', async () => {
    window.history.replaceState(null, '', '/iliad/book/1');
    const { container } = render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: verseBook(true) } });

    const bracketedLine = container.querySelector('#L1-7');
    expect(bracketedLine).toHaveClass('bracketed');
    expect(bracketedLine?.getAttribute('title')).toBe('athetized/bracketed in the editorial tradition');
    expect(container.querySelectorAll('.line-bracket')).toHaveLength(2);
    expect(container.querySelectorAll('.verse-bracket-legend')).toHaveLength(1);

    // No other line is affected.
    expect(container.querySelector('#L1-5')).not.toHaveClass('bracketed');
  });

  it('is inert (no bracket class, no legend) when the book carries no bracketed lines', async () => {
    window.history.replaceState(null, '', '/iliad/book/1');
    const { container } = render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: verseBook(false) } });

    expect(container.querySelectorAll('.bracketed')).toHaveLength(0);
    expect(container.querySelectorAll('.line-bracket')).toHaveLength(0);
    expect(container.querySelectorAll('.verse-bracket-legend')).toHaveLength(0);
  });
});
