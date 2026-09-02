import { fireEvent, render, screen, waitFor, within } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Reader from '../components/Reader.svelte';
import Search from '../components/Search.svelte';
import { fetchPlaces, fetchJourneys, fetchCoastline, fetchPlate, type BookData, type RawBookData } from '../lib/data';
import type { Work } from '../lib/works';
import { parsePlate, renderPlate } from '../lib/plate';

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
    // Two translations (unlike 'EN' above) — needed for the nav-bar bridge's
    // set-trans/trans-state test below, which switches between them.
    ENM: {
      id: 'ENM', title: 'Fixture Multi-Translation Work', abbr: 'ENM', author: 'Test',
      books: 1, bookLabels: ['1'],
      greekEdition: 'Test edition',
      greekSource: { short: 'Test', full: 'Test edition, full citation.', licence: 'Test licence' },
      translations: [
        { id: 'rackham', name: 'Test Translator (Test, 1900)', short: 'Rackham', slot: 'english' },
        { id: 'ross', name: 'Second Translator (Test, 1910)', short: 'Ross', slot: 'ross' },
      ],
      blurb: 'Fixture work for Reader.svelte tests (bekker scheme, two translations).',
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
    // Reading Mode's figure-plate payload (Reader.svelte's ensurePlateData) —
    // default to empty/absent so the pre-existing scene-paging tests above,
    // which never assert on the plate map, see it degrade to "no map"
    // exactly as the real fetch would on a build with no gazetteer copied in
    // yet. The Reader.svelte scene-map gating test below overrides these
    // per-call via vi.mocked(...).mockResolvedValueOnce.
    fetchPlaces: vi.fn(async () => ({ places: [] })),
    fetchJourneys: vi.fn(async () => ({ journeys: [] })),
    fetchCoastline: vi.fn(async () => null),
    // Chart Room per-scene plates (Reader.svelte's ensureIliadPlate) — default
    // to "no plate on the server" so every pre-existing Iliad/reading test
    // above degrades to the old renderSceneMap path exactly as it did before
    // this fetch existed (Reader.svelte's own fallback rule). The Iliad plate
    // describe block below overrides this per-call via
    // vi.mocked(fetchPlate).mockResolvedValueOnce.
    fetchPlate: vi.fn(async () => null),
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

  // NOT replaced (see final report): the brief flagged this assertion as
  // broken by the nav-bar merge, but pass/fail #6 requires the reader-
  // controls strip (this component's own posture-btn, used below 1100px) to
  // stay BYTE-IDENTICAL to before the merge — so its text stays "Reading
  // Mode"/"Scholar view", the wide-screen nav bar's differently-worded
  // posture control lives entirely in ReaderShell.astro (not rendered by
  // this component-only suite), and this assertion is unaffected either way.
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

// Nav-bar bridge (John's nav-bar merge brief, 2026-07-24): ReaderShell.astro
// now server-renders the translation/view/posture/Chart Room controls in
// .nav-panel and drives Reader.svelte via window CustomEvents (set-trans,
// set-view, toggle-reading, toggle-chart-room), which Reader.svelte answers
// with matching *-state broadcasts (trans-state, view-state, reading-state,
// chart-room-state) so the server-rendered markup can sync its selected
// option / active button / aria-pressed after hydration — the same shape as
// the pre-existing toggle-settings/settings-state pair (see the "closes the
// docked lexicon when Settings opens" test above). These tests exercise the
// Reader.svelte side of that contract in isolation (ReaderShell.astro's own
// listeners are plain DOM script, not covered by this Svelte component suite).
describe('Reader.svelte — nav-bar bridge events (John, 2026-07-24)', () => {
  it('toggle-reading flips posture and dispatches reading-state', async () => {
    window.history.replaceState(null, '', '/EN/book/1');
    const { container } = render(Reader, { props: { work: 'EN', bookNum: 1, bookData: fixtureBook } });
    await screen.findByText('1094a');
    const states: boolean[] = [];
    const onState = (e: Event) => states.push((e as CustomEvent<{ reading: boolean }>).detail.reading);
    window.addEventListener('reading-state', onState);

    await fireEvent(window, new CustomEvent('toggle-reading'));
    expect(container.querySelector('.reader-body')).toHaveClass('reading-mode');
    expect(states.at(-1)).toBe(true);

    window.removeEventListener('reading-state', onState);
  });

  it('set-view switches the reading view and dispatches view-state', async () => {
    window.history.replaceState(null, '', '/EN/book/1');
    const { container } = render(Reader, { props: { work: 'EN', bookNum: 1, bookData: fixtureBook } });
    await screen.findByText('1094a');
    const states: string[] = [];
    const onState = (e: Event) => states.push((e as CustomEvent<{ view: string }>).detail.view);
    window.addEventListener('view-state', onState);

    await fireEvent(window, new CustomEvent('set-view', { detail: { view: 'greek' } }));
    expect(container.querySelector('.reader-body')).toHaveClass('view-greek');
    expect(states.at(-1)).toBe('greek');

    window.removeEventListener('view-state', onState);
  });

  it('set-trans switches the selected translation and dispatches trans-state', async () => {
    window.history.replaceState(null, '', '/ENM/book/1');
    const { container } = render(Reader, { props: { work: 'ENM', bookNum: 1, bookData: fixtureBook } });
    await screen.findByText('1094a');
    const states: string[] = [];
    const onState = (e: Event) => states.push((e as CustomEvent<{ id: string }>).detail.id);
    window.addEventListener('trans-state', onState);

    await fireEvent(window, new CustomEvent('set-trans', { detail: { id: 'ross' } }));
    expect(container.querySelector('.reader-body')).toHaveClass('trans-ross');
    expect(states.at(-1)).toBe('ross');

    window.removeEventListener('trans-state', onState);
  });

  it('toggle-chart-room flips the Chart Room state and dispatches chart-room-state', async () => {
    window.history.replaceState(null, '', '/EN/book/1');
    render(Reader, { props: { work: 'EN', bookNum: 1, bookData: fixtureBook } });
    await screen.findByText('1094a');
    const states: boolean[] = [];
    const onState = (e: Event) => states.push((e as CustomEvent<{ open: boolean }>).detail.open);
    window.addEventListener('chart-room-state', onState);

    await fireEvent(window, new CustomEvent('toggle-chart-room'));
    expect(states.at(-1)).toBe(true);
    expect(localStorage.getItem('reader-chart-room')).toBe('true');

    window.removeEventListener('chart-room-state', onState);
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
    // No blocking backdrop for either presentation — see word-popup.test.ts
    // for the 2026-07-29 fix (a full-page backdrop swallowed clicks meant for
    // another Greek token).
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
    expect(document.querySelector('.popup-backdrop')).toBeNull();
  });

  // Settings and the docked lexicon rail are both right-docked, fixed
  // full-height panels (.settings-sidebar / .word-sidebar) — open together
  // they stack, and the lexicon's higher z-index intercepts clicks meant for
  // Settings (reported: the Settings checkbox is unclickable until the
  // lexicon is closed). Mutually exclusive: opening either closes the other.
  it('closes the docked lexicon when Settings opens, and vice versa', async () => {
    setMatchMedia((q) => q.includes('min-width: 1100px'));
    window.history.replaceState(null, '', '/EN/book/1');
    render(Reader, { props: { work: 'EN', bookNum: 1, bookData: fixtureBook } });

    const tok = await screen.findByText('λόγος');
    await fireEvent.click(tok);
    expect(document.querySelector('.word-sidebar:not([inert])')).not.toBeNull();

    // Opening Settings (the header toggle dispatches this CustomEvent — see
    // ReaderShell.astro's settings-toggle wiring) closes the open lexicon: the
    // component state (`popup`) goes back to null immediately. The lexicon's
    // outro is a Svelte transition (WordPopup's `transition:fly`) that may
    // still be animating the node out of the DOM, but Svelte marks an
    // outroing node `inert` right away — it can no longer receive focus or
    // intercept clicks, which is exactly what the reported bug (the Settings
    // checkbox being unclickable) depended on. So the real assertion is "no
    // non-inert .word-sidebar remains", not "the node is gone".
    await fireEvent(window, new CustomEvent('toggle-settings'));
    expect(document.querySelector('.settings-sidebar')).toHaveClass('open');
    expect(document.querySelector('.word-sidebar:not([inert])')).toBeNull();

    // Re-opening a word lookup while Settings is open closes Settings back.
    await fireEvent.click(tok);
    expect(document.querySelector('.word-sidebar:not([inert])')).not.toBeNull();
    expect(document.querySelector('.settings-sidebar')).not.toHaveClass('open');
  });

  // Regression test for the DOM round-trip half of the sigla-inside-a-word fix.
  // Token spans print the VERBATIM slice, so a word carrying an editorial
  // siglum renders as "ἔπει<τα>" — but this repo rebuilds Tokens by reading
  // that surface back out of the DOM (tokenFromEl / rebuildTokensFromDom), so
  // the popup header, its Logeion fallback and the aria-label would all inherit
  // the brackets. They must see the bare word the pipeline emitted. Latent: no
  // line in the corpus carries sigla today.
  it('shows the bare word in the popup for a token printed with sigla inside it', async () => {
    setMatchMedia(() => false);
    window.history.replaceState(null, '', '/EN/book/1');
    const bracketedBook = {
      ...fixtureBook,
      segments: [{
        ...fixtureBook.segments[0],
        greek: [{
          n: 1,
          text: 'ἔπει<τα> ἀρετή',
          tokens: [{ t: 'ἔπειτα', o: 0, k: 'e)/peita' }, { t: 'ἀρετή', o: 9, k: 'areth' }],
        }],
      }],
    } as BookData;
    const { container } = render(Reader, { props: { work: 'EN', bookNum: 1, bookData: bracketedBook } });

    // The line prints byte-identically to its source, the word once.
    const lineText = container.querySelector('.line-text');
    expect(lineText?.textContent).toBe('ἔπει<τα> ἀρετή');
    const toks = Array.from(container.querySelectorAll('.tok'));
    expect(toks.map((t) => t.textContent)).toEqual(['ἔπει<τα>', 'ἀρετή']);
    // The click target keeps its verbatim form, but names the bare word.
    expect(toks[0].getAttribute('aria-label')).toBe('Analyse ἔπειτα');

    // Clicking it resolves the bare word, not the bracketed surface.
    await fireEvent.click(toks[0]);
    expect(await screen.findByText('ἔπειτα', { selector: '.popup-surface' })).toBeInTheDocument();
    expect(screen.queryByText('ἔπει<τα>', { selector: '.popup-surface' })).toBeNull();
  });

  // Integration-level regression test for the 2026-07-29 fix (see
  // word-popup.test.ts "pointerdown outside" describe block): a real click
  // through Reader's delegated `.tok` handler on a SECOND token, while the
  // popup is already open, must swap the panel to the new word in place — the
  // old full-page `.popup-backdrop` swallowed that click. Below 1100px so the
  // anchored modal popup (the one guarded by the pointerdown-outside handler)
  // is what opens.
  it('clicking a second Greek token while the popup is open swaps to that word without closing', async () => {
    setMatchMedia(() => false);
    window.history.replaceState(null, '', '/EN/book/1');
    render(Reader, { props: { work: 'EN', bookNum: 1, bookData: fixtureBook } });

    const first = await screen.findByText('λόγος');
    await fireEvent.click(first);
    expect(await screen.findByText('λόγος', { selector: '.popup-surface' })).toBeInTheDocument();

    const second = screen.getByText('ἀρετή');
    await fireEvent.click(second);

    // Still open, now showing the second token's word — not closed/reopened.
    expect(await screen.findByText('ἀρετή', { selector: '.popup-surface' })).toBeInTheDocument();
    expect(screen.queryByText('λόγος', { selector: '.popup-surface' })).toBeNull();
    expect(document.querySelectorAll('.word-sidebar')).toHaveLength(1);
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
          // The token surface must actually occur in the line text at `o`, as
          // the pipeline always emits it — lineRenderParts locates each token
          // by its surface and emits nothing for one that isn't there.
          tokens: [{ t: 'Greek', o: 0, k: `key${n}` }],
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

describe('Reader.svelte — Reading Mode scene paging (John, 2026-07-18)', () => {
  // A verse book (real 'iliad' registry work, epicVerse) with:
  //  - a REAL vulgate gap (13-14 missing, like Il. 9.457→462) so chunk
  //    derivation is exercised against real line numbers, not array index
  //    arithmetic;
  //  - 5 English ticks (n=1,5,10,15,20) chunking the prose into 5 labelled
  //    SENTENCES ("ChunkX text." each ends in a period), so which sentences a
  //    scene page shows is directly readable from which "ChunkX text." runs
  //    appear;
  //  - 3 scenes whose edges deliberately DON'T land on tick boundaries
  //    (scene2 additionally spans the gap), exercising sentence-snapped
  //    paging (John, 2026-07-19; shared/lib/scene-paging.ts's
  //    sentenceSnapScenePages) under the straddle-ownership rule (John,
  //    2026-07-20): a sentence inside a tick that straddles a scene boundary
  //    belongs to whichever scene's owned line-share it ends within (the
  //    owned-share midpoint target in naturalEndOffset), not to every scene
  //    whose Greek range the raw tick happens to overlap. Each tick chunk
  //    here is exactly one whole sentence, so which "ChunkX text." sentence
  //    lands on which scene's page is a direct, readable trace of that rule
  //    — scene 1 (ends at line 7) owns only 3 of chunk B's 5 lines (5-9), too
  //    small a share to pull chunk B's sentence onto scene 1's page, so it
  //    lands on scene 2's page instead; chunk D (15-19) similarly lands on
  //    scene 3's page rather than scene 2's. Every chunk appears on exactly
  //    one page, never duplicated, never dropped.
  const TICK_TEXT =
    'ChunkA text. ChunkB text. ChunkC text. ChunkD text. ChunkE text.';
  const sceneBook = (draft = false): RawBookData => ({
    book: 1,
    apparatus: draft ? { draft: true } : undefined,
    scenes: [
      { summary: 'Scene one summary.', startLine: 1, endLine: 7 },
      { summary: 'Scene two summary.', startLine: 8, endLine: 16, place: 'Ithaca', day: 3 },
      { summary: 'Scene three summary.', startLine: 17, endLine: 24 },
    ],
    segments: [
      {
        id: 'seg1',
        column: '1',
        greek: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, /* 13, 14 gap */ 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
          .map((n) => ({ n, text: `g${n}`, tokens: [{ t: `g${n}`, o: 0, k: `g${n}` }] })),
        english: {
          text: TICK_TEXT,
          notes: [],
          markers: [],
          bekker: [
            { n: 1, offset: 0, real: true },
            { n: 5, offset: 13, real: true },
            { n: 10, offset: 26, real: true },
            { n: 15, offset: 39, real: true },
            { n: 20, offset: 52, real: true },
          ],
        },
      },
    ],
  });

  it('opens Reading Mode on the scene containing the top-visible line, and pages by scene', async () => {
    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: sceneBook() } });

    // Scene 1 (lines 1-7) claims chunk A (1-4) only — chunk B (5-9) straddles
    // the boundary, and scene 1 owns just 3 of its 5 lines (5-7), too small
    // a share to pull "ChunkB text." onto scene 1's page (owned-share
    // midpoint rule, naturalEndOffset); chunk B's sentence lands on scene 2
    // instead (below).
    await screen.findByText(/Scene 1 of 3/);
    expect(container.querySelector('.reading-scene-pos')?.textContent).toContain('lines 1–7');
    expect(container.textContent).toContain('ChunkA text.');
    expect(container.textContent).not.toContain('ChunkB text.');
    expect(container.textContent).not.toContain('ChunkC text.');
    // Full presence/absence matrix (Codex new-finding 3, 2026-07-21): scene 1
    // owns ONLY chunk A — D and E (which land on scene 3, far downstream)
    // must be just as absent here as the already-checked B and C.
    expect(container.textContent).not.toContain('ChunkD text.');
    expect(container.textContent).not.toContain('ChunkE text.');
    expect(container.querySelector('.reading-scene-prev')).toHaveProperty('disabled', true);

    // No scene chips anywhere — the header replaces them.
    expect(container.querySelectorAll('.scene-chip')).toHaveLength(0);

    // Next scene → scene 2 (lines 8-16), which SPANS the vulgate gap
    // (13-14 missing): its page shows chunks B (5-9) and C (10-14) — chunk B
    // was not fully owned by scene 1 above, so its sentence lands here
    // instead (no duplication); chunk D (15-19) similarly isn't pulled onto
    // scene 2's page (scene 2 ends at line 16, only 2 of chunk D's 5 lines),
    // so it lands on scene 3's page instead (below).
    await fireEvent.click(screen.getByRole('button', { name: /Next scene/i }));
    await screen.findByText(/Scene 2 of 3/);
    expect(container.querySelector('.reading-scene-pos')?.textContent).toContain('lines 8–16');
    expect(container.textContent).toContain('ChunkB text.');
    expect(container.textContent).toContain('ChunkC text.');
    expect(container.textContent).not.toContain('ChunkA text.');
    expect(container.textContent).not.toContain('ChunkD text.');
    expect(container.textContent).not.toContain('ChunkE text.');
    // Day + place meta render; scene 1 (no day/place) showed neither.
    expect(container.textContent).toContain('Day 3');
    expect(container.textContent).toContain('Ithaca');
    // The URL reflects position (1-based) for refresh/share.
    expect(new URL(window.location.href).searchParams.get('scene')).toBe('2');

    // Previous scene → back to scene 1.
    await fireEvent.click(screen.getByRole('button', { name: /Previous scene/i }));
    await screen.findByText(/Scene 1 of 3/);

    // Keyboard: → advances, ← retreats, matching the buttons.
    await fireEvent.keyDown(window, { key: 'ArrowRight' });
    await screen.findByText(/Scene 2 of 3/);
    await fireEvent.keyDown(window, { key: 'ArrowLeft' });
    await screen.findByText(/Scene 1 of 3/);

    // Next scene is disabled only at the last scene.
    await fireEvent.click(screen.getByRole('button', { name: /Next scene/i }));
    await fireEvent.click(screen.getByRole('button', { name: /Next scene/i }));
    await screen.findByText(/Scene 3 of 3/);
    expect(container.querySelector('.reading-scene-next')).toHaveProperty('disabled', true);

    // Scene 3 (lines 17-24) shows chunk D (15-19, not fully owned by scene 2)
    // and chunk E (20-24) — pinning every one of the five chunk-sentences to
    // exactly ONE scene page across the three scenes (Codex review F6,
    // 2026-07-21): A→scene 1, B+C→scene 2, D+E→scene 3, none duplicated.
    expect(container.querySelector('.reading-scene-pos')?.textContent).toContain('lines 17–24');
    expect(container.textContent).toContain('ChunkD text.');
    expect(container.textContent).toContain('ChunkE text.');
    expect(container.textContent).not.toContain('ChunkA text.');
    expect(container.textContent).not.toContain('ChunkB text.');
    expect(container.textContent).not.toContain('ChunkC text.');
  });

  it('ignores arrow-key scene paging while focus is in a text field', async () => {
    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: sceneBook() } });
    await screen.findByText(/Scene 1 of 3/);

    const input = document.createElement('input');
    document.body.appendChild(input);
    input.focus();
    await fireEvent.keyDown(window, { key: 'ArrowRight' });
    expect(screen.queryByText(/Scene 2 of 3/)).toBeNull();
    input.remove();
  });

  it('shows the draft badge on the scene header only when the apparatus is drafted', async () => {
    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: sceneBook(true) } });
    await screen.findByText(/Scene 1 of 3/);
    expect(container.querySelector('.reading-scene-head .draft-badge')).not.toBeNull();
  });

  it('?scene= deep-links to that scene on load (1-based, share/refresh position)', async () => {
    window.history.replaceState(null, '', '/iliad/book/1?mode=reading&scene=3');
    render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: sceneBook() } });
    await screen.findByText(/Scene 3 of 3/);
  });

  it('?loc= while opening in Reading Mode lands on the scene CONTAINING that line', async () => {
    // Line 9 falls in scene 2's range (8-16), not scene 1 (1-7) or 3 (17-24).
    window.history.replaceState(null, '', '/iliad/book/1?mode=reading&loc=1.9');
    render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: sceneBook() } });
    await screen.findByText(/Scene 2 of 3/);
  });

  it('degrades silently to the whole-book flow when the book carries no scene apparatus', async () => {
    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const noScenes: BookData = {
      book: 1,
      segments: [
        {
          id: 'seg1', column: '1',
          greek: [1, 2, 3].map((n) => ({ n, text: `g${n}`, tokens: [{ t: `g${n}`, o: 0, k: `g${n}` }] })),
          english: { text: 'English filler.', notes: [], markers: [] },
        },
      ],
    };
    const { container } = render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: noScenes } });
    await screen.findByText(/English filler/i);
    expect(container.querySelector('.reading-scene-head')).toBeNull();
    expect(container.querySelector('.reading-scene-nav')).toBeNull();
    expect(container.querySelectorAll('.scene-chip')).toHaveLength(0);
  });
});

describe('Reader.svelte — Chart Room scene map gates on ANY resolved place (2026-07-28, finding 4)', () => {
  // Reproduces the reported latent bug: a scene authored with
  // `places: [unlocatedId, locatedId]` resolves `place` (shared/lib/
  // scene-place.ts's ScenePlaceResolution) to the FIRST id — the unlocated
  // one — while `places` (every resolved, coords-bearing id) still carries
  // the second, mappable one. Before the fix, Reader.svelte's
  // `currentPlateMap` gated on `place.coords` alone and rendered no map at
  // all despite a perfectly mappable place; the fix gates on `places`
  // instead. This test only exercises Reader.svelte's own gating — the
  // `place`/`places` split itself is shared/lib/scene-place.ts's job and is
  // covered in shared/__tests__/scene-place.test.ts.
  const bookData: RawBookData = {
    book: 1,
    scenes: [
      {
        summary: 'A scene naming an unlocated place first, a located one second.',
        startLine: 1,
        endLine: 3,
        places: ['no-coords-place', 'has-coords-place'],
      },
    ],
    segments: [
      {
        id: 'seg1',
        column: '1',
        greek: [1, 2, 3].map((n) => ({ n, text: `g${n}`, tokens: [{ t: `g${n}`, o: 0, k: `g${n}` }] })),
        // Reading Mode only pages by scene when the translation carries real
        // (>1) bekker ticks (Reader.svelte's readingHasSceneAnchors) — a
        // markerless translation falls back to its own "aligned at book
        // level only" notice, with no scene head/plate at all, which would
        // make this test vacuous. Two real ticks are enough to satisfy the
        // gate; same posture as the scene-paging describe block above.
        english: {
          text: 'Scene text.',
          notes: [],
          markers: [],
          bekker: [
            { n: 1, offset: 0, real: true },
            { n: 2, offset: 6, real: true },
          ],
        },
      },
    ],
  };

  afterEach(() => {
    vi.mocked(fetchPlaces).mockReset();
    vi.mocked(fetchJourneys).mockReset();
    vi.mocked(fetchCoastline).mockReset();
    // Restore the file-level defaults (empty gazetteer/journeys, no
    // coastline) other describe blocks rely on.
    vi.mocked(fetchPlaces).mockResolvedValue({ places: [] });
    vi.mocked(fetchJourneys).mockResolvedValue({ journeys: [] });
    vi.mocked(fetchCoastline).mockResolvedValue(null);
  });

  it('renders the scene map when `place` is coordless but `places` has a mappable entry', async () => {
    vi.mocked(fetchPlaces).mockResolvedValueOnce({
      places: [
        { id: 'no-coords-place', name: 'No Coords Place', certainty: 'mythical' }, // no coords: place.coords is undefined
        { id: 'has-coords-place', name: 'Has Coords Place', coords: [10, 20], certainty: 'certain' },
      ],
    });
    vi.mocked(fetchJourneys).mockResolvedValueOnce({ journeys: [] });
    vi.mocked(fetchCoastline).mockResolvedValueOnce({ bbox: [0, 0, 1, 1], rings: [] });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, { props: { work: 'iliad', bookNum: 1, bookData } });
    // The reading-mode translation's real bekker ticks split "Scene text."
    // across two `.bk-seg` spans (at the tick boundary) — wait on the scene
    // head itself (proof `readingHasSceneAnchors` passed and paging is
    // live) rather than a text match that would miss the split.
    await screen.findByText(/Scene 1 of 1/i);

    // The map slot renders an actual map (not the "collapsed, no map" state)
    // once plate data resolves, even though `place` itself is coordless.
    await waitFor(() => expect(container.querySelector('.reading-plate-map svg')).toBeTruthy());
    expect(container.querySelector('.reading-plate')).not.toHaveClass('reading-plate-nomap');

    const svg = container.querySelector('.reading-plate-map svg');
    expect(svg?.getAttribute('aria-label')).toContain('Has Coords Place');
    expect(svg?.getAttribute('aria-label')).not.toContain('No Coords Place');
  });

  it('still shows no map when every resolved place for the scene is coordless (unchanged honest-null behavior)', async () => {
    vi.mocked(fetchPlaces).mockResolvedValueOnce({
      places: [
        { id: 'no-coords-place', name: 'No Coords Place', certainty: 'mythical' },
        { id: 'also-no-coords', name: 'Also No Coords', certainty: 'speculative' },
      ],
    });
    vi.mocked(fetchJourneys).mockResolvedValueOnce({ journeys: [] });
    vi.mocked(fetchCoastline).mockResolvedValueOnce({ bbox: [0, 0, 1, 1], rings: [] });

    const allCoordless: RawBookData = {
      ...bookData,
      scenes: [{ ...bookData.scenes![0], places: ['no-coords-place', 'also-no-coords'] }],
    };

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: allCoordless } });
    // The reading-mode translation's real bekker ticks split "Scene text."
    // across two `.bk-seg` spans (at the tick boundary) — wait on the scene
    // head itself (proof `readingHasSceneAnchors` passed and paging is
    // live) rather than a text match that would miss the split.
    await screen.findByText(/Scene 1 of 1/i);

    await waitFor(() => expect(container.querySelector('.reading-plate')).toHaveClass('reading-plate-nomap'));
    expect(container.querySelector('.reading-plate-map')).toBeNull();
  });
});

describe('Reader.svelte — Chart Room plate path stays off while CHART_ROOM_PLATE_ENABLED is false (John, 2026-07-29)', () => {
  // Reader.svelte's CHART_ROOM_PLATE_ENABLED const gates BOTH the
  // ensureIliadPlate() fetch reactive and useIliadPlate — while it's false
  // (current state, pending the research-first rebuild — see
  // docs/TROY-MAPS-HANDOFF-2.md §1), an Iliad scene must fall back to the
  // same renderSceneMap path Odyssey scenes use, even when fetchPlate WOULD
  // resolve a ready plate. Ready-plate mock cribbed from the skipped
  // describe block below (:812-); the point of this test is that mock is
  // never touched while the flag is off.
  const trojanPlainFixture = {
    id: 'trojan-plain',
    title: 'The Trojan Plain',
    kind: 'geographic',
    status: 'draft',
    bbox: [0, 0, 10, 10],
    size: [400, 300],
    layers: [],
  };

  const bookData: RawBookData = {
    book: 1,
    scenes: [
      {
        summary: 'A scene naming a located place.',
        startLine: 1,
        endLine: 3,
        places: ['has-coords-place'],
      },
    ],
    segments: [
      {
        id: 'seg1',
        column: '1',
        greek: [1, 2, 3].map((n) => ({ n, text: `g${n}`, tokens: [{ t: `g${n}`, o: 0, k: `g${n}` }] })),
        english: {
          text: 'Scene text.',
          notes: [],
          markers: [],
          bekker: [
            { n: 1, offset: 0, real: true },
            { n: 2, offset: 6, real: true },
          ],
        },
      },
    ],
  };

  afterEach(() => {
    vi.mocked(fetchPlaces).mockReset();
    vi.mocked(fetchJourneys).mockReset();
    vi.mocked(fetchCoastline).mockReset();
    vi.mocked(fetchPlate).mockReset();
    vi.mocked(fetchPlaces).mockResolvedValue({ places: [] });
    vi.mocked(fetchJourneys).mockResolvedValue({ journeys: [] });
    vi.mocked(fetchCoastline).mockResolvedValue(null);
    vi.mocked(fetchPlate).mockResolvedValue(null);
  });

  it('chart-room plate path stays off while CHART_ROOM_PLATE_ENABLED is false (falls back to scene map even with a ready plate)', async () => {
    vi.mocked(fetchPlate).mockResolvedValueOnce(trojanPlainFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({
      places: [{ id: 'has-coords-place', name: 'Has Coords Place', coords: [3, 3], certainty: 'certain' }],
    });
    vi.mocked(fetchJourneys).mockResolvedValueOnce({ journeys: [] });
    vi.mocked(fetchCoastline).mockResolvedValueOnce({ bbox: [0, 0, 1, 1], rings: [] });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, { props: { work: 'iliad', bookNum: 1, bookData } });
    await screen.findByText(/Scene 1 of 1/i);

    // The fallback renderSceneMap path renders — same as an Odyssey scene
    // would — proving the plate path never took over.
    await waitFor(() => expect(container.querySelector('.reading-plate-map svg')).toBeTruthy());
    expect(container.querySelector('.chart-plate')).toBeNull();

    // The gate is on the FETCH itself, not just the render: ensureIliadPlate
    // must never even run while the flag is off (Reader.svelte's fetch-
    // gating reactive), so fetchPlate('trojan-plain') — the illustrated
    // GEOGRAPHIC plate — is never called despite a ready plate waiting in
    // the mock. fetchPlate('trojan-plain-schematic') is a SEPARATE,
    // unflagged fetch (queue item 3b, 2026-07-30's schematic-only routing —
    // see shared/components/Reader.svelte's ensureSchematicPlate) and is
    // expected to fire regardless; this scene resolves to a coords-bearing
    // place, so its resolution carries no `schematic` field and the
    // schematic plate never activates either — the fallback renderSceneMap
    // assertion above already proves that.
    expect(fetchPlate).not.toHaveBeenCalledWith('trojan-plain');
  });
});

// The postcard camera/focus/label machinery lives on the SCHEMATIC path
// (live today — CHART_ROOM_PLATE_ENABLED gates only the geographic
// trojan-plain plate, see the two describe blocks above and below). The
// skipped geographic block below covers the same camera/no-rerender shape
// for the flag-gated path; this block is its live counterpart, plus the new
// postcard assertions (focus/ghost/omit, label descale wrapper, locator
// inset) that block does not yet exercise (it predates the postcard design).
describe('Reader.svelte — Chart Room SCHEMATIC plate postcard (live path, 2026-09-02)', () => {
  const schematicFixture = {
    id: 'trojan-plain-schematic',
    title: 'The Troad, schematic',
    kind: 'schematic',
    status: 'draft',
    size: [400, 300],
    layers: [],
  };

  const anchorA = {
    id: 'anchor-a', name: 'Anchor Alpha', certainty: 'certain' as const,
    plateAnchors: { 'trojan-plain-schematic': [0.3, 0.4] as [number, number] }, positionBasis: 'conjectural' as const,
  };
  const anchorB = {
    id: 'anchor-b', name: 'Anchor Beta', certainty: 'certain' as const,
    plateAnchors: { 'trojan-plain-schematic': [0.7, 0.6] as [number, number] }, positionBasis: 'conjectural' as const,
  };

  const oneSceneBook = (placeIds: string[]): RawBookData => ({
    book: 1,
    scenes: [{ summary: 'A scene naming a schematic-only place.', startLine: 1, endLine: 3, places: placeIds }],
    segments: [
      {
        id: 'seg1',
        column: '1',
        greek: [1, 2, 3].map((n) => ({ n, text: `g${n}`, tokens: [{ t: `g${n}`, o: 0, k: `g${n}` }] })),
        english: {
          text: 'Scene text.',
          notes: [],
          markers: [],
          bekker: [
            { n: 1, offset: 0, real: true },
            { n: 2, offset: 6, real: true },
          ],
        },
      },
    ],
  });

  afterEach(() => {
    vi.mocked(fetchPlaces).mockReset();
    vi.mocked(fetchJourneys).mockReset();
    vi.mocked(fetchCoastline).mockReset();
    vi.mocked(fetchPlate).mockReset();
    vi.mocked(fetchPlaces).mockResolvedValue({ places: [] });
    vi.mocked(fetchJourneys).mockResolvedValue({ journeys: [] });
    vi.mocked(fetchCoastline).mockResolvedValue(null);
    vi.mocked(fetchPlate).mockResolvedValue(null);
  });

  it("frames the camera on the scene's focus place; only the focus pin stays undimmed and only its label stays shown", async () => {
    vi.mocked(fetchPlate).mockResolvedValueOnce(schematicFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({ places: [anchorA, anchorB] });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, {
      props: { work: 'iliad', bookNum: 1, bookData: oneSceneBook(['anchor-a']) },
    });
    await screen.findByText(/Scene 1 of 1/i);

    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());
    const svg = container.querySelector('.chart-plate svg')!;
    expect(svg.getAttribute('aria-label')).toContain('Anchor Alpha');

    const cameraG = container.querySelector('.plate-camera') as HTMLElement;
    expect(cameraG).toBeTruthy();
    expect(cameraG.style.transform).not.toBe('translate(0px, 0px) scale(1)');

    // The focus pin is undimmed; every other place's pin is ghosted.
    expect(container.querySelector('[data-place-id="anchor-a"]')).not.toHaveClass('plate-dimmed');
    expect(container.querySelector('[data-place-id="anchor-b"]')).toHaveClass('plate-dimmed');

    // Postcard design part C: a non-focus LABEL is OMITTED (`.plate-hidden`,
    // display:none) — a stricter treatment than the ghosted pin above.
    expect(container.querySelector('[data-label-for="anchor-a"]')).not.toHaveClass('plate-hidden');
    expect(container.querySelector('[data-label-for="anchor-b"]')).toHaveClass('plate-hidden');
  });

  it('wraps every .plate-label in a descale group (part D)', async () => {
    vi.mocked(fetchPlate).mockResolvedValueOnce(schematicFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({ places: [anchorA, anchorB] });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, {
      props: { work: 'iliad', bookNum: 1, bookData: oneSceneBook(['anchor-a']) },
    });
    await screen.findByText(/Scene 1 of 1/i);
    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());

    const labels = container.querySelectorAll('.plate-label');
    expect(labels.length).toBeGreaterThan(0);
    labels.forEach((label) => {
      expect(label.parentElement).toHaveClass('chart-label-descale');
    });
  });

  it('renders exactly one locator frame rect, and no click-through link on the schematic path (part E/F: no /maps/ tab exists for this plate)', async () => {
    vi.mocked(fetchPlate).mockResolvedValueOnce(schematicFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({ places: [anchorA] });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, {
      props: { work: 'iliad', bookNum: 1, bookData: oneSceneBook(['anchor-a']) },
    });
    await screen.findByText(/Scene 1 of 1/i);
    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());

    expect(container.querySelectorAll('rect.chart-locator-frame').length).toBe(1);
    expect(container.querySelector('.chart-plate-postcard')?.tagName).toBe('DIV');

    // Finding (2026-09-02, Codex review): a single --accent stroke measured
    // under the 3:1 AA floor against the lean locator's own coast/river
    // strokes where the frame crosses them. Fixed with a wider halo rect
    // (--scene-map-label-halo) drawn UNDERNEATH the accent frame — both
    // must be present, halo first in document order (so the accent stroke
    // paints on top of it, not the other way around).
    const overlay = container.querySelector('.chart-locator-overlay');
    const children = overlay ? Array.from(overlay.children) : [];
    // Svelte appends its own scoped-style hash class, so match on the
    // authored class only rather than the full attribute value.
    expect(children.map((el) => el.classList[0])).toEqual(['chart-locator-frame-halo', 'chart-locator-frame']);
  });

  it('does not re-render the plate SVG when paging between scenes, only the camera/focus (mirrors the skipped geographic test below)', async () => {
    vi.mocked(fetchPlate).mockResolvedValueOnce(schematicFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({ places: [anchorA, anchorB] });

    const twoSceneBook: RawBookData = {
      book: 1,
      scenes: [
        { summary: 'Scene one summary.', startLine: 1, endLine: 3, places: ['anchor-a'] },
        { summary: 'Scene two summary.', startLine: 4, endLine: 6, places: ['anchor-b'] },
      ],
      segments: [
        {
          id: 'seg1',
          column: '1',
          greek: [1, 2, 3, 4, 5, 6].map((n) => ({ n, text: `g${n}`, tokens: [{ t: `g${n}`, o: 0, k: `g${n}` }] })),
          english: {
            text: 'Scene one text. Scene two text.',
            notes: [],
            markers: [],
            bekker: [
              { n: 1, offset: 0, real: true },
              { n: 4, offset: 'Scene one text. '.length, real: true },
            ],
          },
        },
      ],
    };

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: twoSceneBook } });
    await screen.findByText(/Scene 1 of 2/i);

    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());
    const svgBefore = container.querySelector('.chart-plate svg');
    const cameraG = container.querySelector('.plate-camera') as HTMLElement;
    const transformBefore = cameraG.style.transform;
    expect(container.querySelector('svg')?.getAttribute('aria-label')).toContain('Anchor Alpha');

    await fireEvent.click(screen.getByRole('button', { name: /Next scene/i }));
    await screen.findByText(/Scene 2 of 2/i);

    // Same SVG element — the base markup was never reassigned via {@html}.
    expect(container.querySelector('.chart-plate svg')).toBe(svgBefore);
    expect(cameraG.style.transform).not.toBe(transformBefore);
    expect(container.querySelector('svg')?.getAttribute('aria-label')).toContain('Anchor Beta');
    expect(container.querySelector('svg')?.getAttribute('aria-label')).not.toContain('Anchor Alpha');
  });

  // Defect A (2026-09-02, orchestrator screenshot review): the schematic
  // sheet's title cartouche and named side panels are `style: 'inset'`
  // LAYERS drawn inside `.plate-camera` -- without this fix they pan and
  // crop with the map ("S IT OUT" fragment at the postcard's bottom-left).
  // The legend/scale bar/north arrow/hypsometric key are sheet chrome drawn
  // OUTSIDE the camera group at full-sheet size -- left alone they sit at
  // the slot's corner, where the locator inset then overlaps them. A
  // postcard shows one subject and a locator, never any of this.
  it('hides every sheet-furniture element in the postcard: an inset layer, and the legend/scale/north/hypsometric-key chrome', async () => {
    const furnitureFixture = {
      id: 'trojan-plain-schematic',
      title: 'The Troad, schematic',
      kind: 'schematic',
      status: 'draft',
      size: [400, 300],
      // A caption is what draws the north arrow at all (see plate.ts's own
      // comment on Plate.north).
      north: 'Approximate, after the survey grid',
      // A schematic plate draws a scale bar only when it declares a scale.
      pxPerMetre: 0.5,
      layers: [
        {
          id: 'title-block', kind: 'region', style: 'inset',
          polygon: [[0.02, 0.02], [0.3, 0.02], [0.3, 0.12], [0.02, 0.12]],
          label: 'THE TROAD',
        },
        // A river layer earns a legend row (derivedLegendEntry).
        { id: 'river-1', kind: 'river', path: [[0.1, 0.5], [0.9, 0.5]], width: 2 },
        // Two DIFFERENT elevations are what makes hypsometricLevels (and so
        // the hypsometric key) non-empty.
        { id: 'relief-1', kind: 'relief', elevation: 100, polygon: [[0.6, 0.6], [0.7, 0.6], [0.7, 0.7], [0.6, 0.7]] },
        { id: 'relief-2', kind: 'relief', elevation: 200, polygon: [[0.75, 0.6], [0.85, 0.6], [0.85, 0.7], [0.75, 0.7]] },
      ],
    };

    vi.mocked(fetchPlate).mockResolvedValueOnce(furnitureFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({ places: [anchorA] });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, {
      props: { work: 'iliad', bookNum: 1, bookData: oneSceneBook(['anchor-a']) },
    });
    await screen.findByText(/Scene 1 of 1/i);
    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());

    // Precondition: every furniture element actually rendered onto the
    // sheet (this fixture is deliberately crafted to draw all four chrome
    // registers plus one inset layer) — a selector matching nothing would
    // make the assertions below pass vacuously.
    const inset = container.querySelector('[data-layer-style="inset"]');
    const legend = container.querySelector('.plate-legend');
    const scale = container.querySelector('.plate-scale');
    const north = container.querySelector('.plate-north');
    const hypsometricKey = container.querySelector('.plate-hypsometric-key');
    for (const el of [inset, legend, scale, north, hypsometricKey]) expect(el).toBeTruthy();

    for (const el of [inset, legend, scale, north, hypsometricKey]) {
      expect(el).toHaveClass('plate-hidden');
    }
    // The neatline is the one piece of furniture a postcard keeps.
    expect(container.querySelector('.plate-neatline')).not.toHaveClass('plate-hidden');

    // The locator inset is its OWN renderPlate() call (chartLocatorInset,
    // a static {@html} sibling of `.chart-plate`, not itself `use:`d) — its
    // coast/river layers still earn a legend row the same way the main
    // sheet's do, found leaking a tiny illegible swatch into the locator's
    // own corner during this lane's browser smoke pass. ensureLabelWrappers
    // reaches into the sibling `.chart-locator` and stamps the same
    // `.plate-hidden` class its main-sheet furniture pass uses.
    const locatorLegend = container.querySelector('.chart-locator .plate-legend');
    expect(locatorLegend).toBeTruthy();
    expect(locatorLegend).toHaveClass('plate-hidden');
  });

  // Defect B (2026-09-02, orchestrator screenshot review): "Assembly and
  // law-place" reads "ssembly and law-place" in the ~220px desktop Reading
  // Mode inline slot. Reproduced with the REAL schematic layer/place data
  // (apparatus/plates/trojan-plain-schematic.json's achaean-assembly-place
  // layer, apparatus/places.json's matching entry) inlined as literals, not
  // read from the corpus files, so this test stays independent of apparatus
  // edits — see shared/__tests__/plate.test.ts's own SEED_PLATE_PATH tests
  // for the corpus-reading style this deliberately does NOT use.
  const assemblyLayer = {
    id: 'achaean-assembly-place',
    kind: 'region',
    placeId: 'achaean-assembly-place',
    polygon: [[0.458, 0.73], [0.582, 0.728], [0.582, 0.766], [0.458, 0.768]],
  };
  const assemblyPlace = {
    id: 'achaean-assembly-place',
    name: "The assembly and law-place, with the gods' altars",
    certainty: 'certain' as const,
    plateAnchors: { 'trojan-plain-schematic': [0.52, 0.748] as [number, number] },
    positionBasis: 'conjectural' as const,
  };
  const narrowFixture = {
    id: 'trojan-plain-schematic',
    title: 'The Troad, schematic',
    kind: 'schematic',
    status: 'draft',
    size: [960, 780],
    layers: [assemblyLayer],
  };
  const twoAssemblySceneBook: RawBookData = {
    book: 1,
    scenes: [
      { summary: 'Scene one summary.', startLine: 1, endLine: 3, places: ['achaean-assembly-place'] },
      { summary: 'Scene two summary.', startLine: 4, endLine: 6, places: ['achaean-assembly-place'] },
    ],
    segments: [
      {
        id: 'seg1',
        column: '1',
        greek: [1, 2, 3, 4, 5, 6].map((n) => ({ n, text: `g${n}`, tokens: [{ t: `g${n}`, o: 0, k: `g${n}` }] })),
        english: {
          text: 'Scene one text. Scene two text.',
          notes: [],
          markers: [],
          bekker: [
            { n: 1, offset: 0, real: true },
            { n: 4, offset: 'Scene one text. '.length, real: true },
          ],
        },
      },
    ],
  };

  it("keeps the focus label's on-screen extent inside a narrow 220px slot (the reported clip)", async () => {
    vi.mocked(fetchPlate).mockResolvedValueOnce(narrowFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({ places: [assemblyPlace] });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: twoAssemblySceneBook } });
    await screen.findByText(/Scene 1 of 2/i);
    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());

    const slotWidth = 220;
    const chartPlateEl = container.querySelector('.chart-plate') as HTMLElement;
    // The same mechanism the descale code reads (node.clientWidth) -- happy-
    // dom lays out nothing, so this is stubbed directly on the element.
    Object.defineProperty(chartPlateEl, 'clientWidth', { value: slotWidth, configurable: true });

    // Force the action's `update()` to re-run (camera/focus are recomputed
    // reactively on scene paging; a fresh scene produces a fresh Camera
    // object even though this fixture names the same place both times) so
    // it runs with the stub above already in place — mirrors the "does not
    // re-render" test's own two-scene technique.
    await fireEvent.click(screen.getByRole('button', { name: /Next scene/i }));
    await screen.findByText(/Scene 2 of 2/i);

    const cameraG = container.querySelector('.plate-camera') as SVGGElement;
    const camMatch = cameraG.style.transform.match(/translate\(([-\d.]+)px, ([-\d.]+)px\) scale\(([-\d.]+)\)/);
    expect(camMatch).not.toBeNull();
    const [, txStr, , scaleStr] = camMatch!;
    const camK = parseFloat(scaleStr);
    const tx = parseFloat(txStr);

    const labelText = container.querySelector('[data-label-for="achaean-assembly-place"]') as SVGTextElement;
    const descaleWrapper = labelText.parentElement as SVGGElement;
    expect(descaleWrapper).toHaveClass('chart-label-descale');
    const wrapMatch = descaleWrapper
      .getAttribute('transform')!
      .match(/translate\(([-\d.]+) ([-\d.]+)\) scale\(([-\d.]+)\)/);
    expect(wrapMatch).not.toBeNull();
    const [, pivotXStr, , fStr] = wrapMatch!;
    const pivotX = parseFloat(pivotXStr);
    const f = parseFloat(fStr);

    // The label's own box (plate units) -- computed independently via
    // renderPlate/parsePlate on the same fixture, exactly as
    // Reader.svelte's labelBoxes prop does, rather than trusting the fix
    // under test to have reported it correctly.
    const plate = parsePlate(narrowFixture);
    const rendered = renderPlate(plate, [assemblyPlace], { idPrefix: 'test-extent' });
    const box = rendered.labelBoxes['achaean-assembly-place'];
    expect(box).toBeTruthy();

    const S = slotWidth / plate.size[0];
    const screenOf = (plateX: number) => S * (camK * (pivotX + f * (plateX - pivotX)) + tx);
    const left = Math.min(screenOf(box[0]), screenOf(box[2]));
    const right = Math.max(screenOf(box[0]), screenOf(box[2]));

    expect(left).toBeGreaterThanOrEqual(0);
    expect(right).toBeLessThanOrEqual(slotWidth);
  });

  it('does not throw or write a non-finite transform when the slot is hidden (clientWidth 0)', async () => {
    vi.mocked(fetchPlate).mockResolvedValueOnce(narrowFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({ places: [assemblyPlace] });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: twoAssemblySceneBook } });
    await screen.findByText(/Scene 1 of 2/i);
    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());

    const chartPlateEl = container.querySelector('.chart-plate') as HTMLElement;
    Object.defineProperty(chartPlateEl, 'clientWidth', { value: 0, configurable: true });

    await expect(
      (async () => {
        await fireEvent.click(screen.getByRole('button', { name: /Next scene/i }));
        await screen.findByText(/Scene 2 of 2/i);
      })(),
    ).resolves.not.toThrow();

    const cameraG = container.querySelector('.plate-camera') as SVGGElement;
    expect(cameraG.style.transform).not.toContain('NaN');
    expect(cameraG.style.transform).not.toContain('Infinity');
    const camMatch = cameraG.style.transform.match(/translate\(([-\d.]+)px, ([-\d.]+)px\) scale\(([-\d.]+)\)/);
    expect(camMatch).not.toBeNull();
    expect(camMatch!.slice(1).every((n) => Number.isFinite(parseFloat(n)))).toBe(true);

    const descaleWrapper = container.querySelector('.chart-label-descale');
    if (descaleWrapper) {
      const t = descaleWrapper.getAttribute('transform') ?? '';
      expect(t).not.toContain('NaN');
      expect(t).not.toContain('Infinity');
    }
  });

  // Codex finding (2026-09-02): the omit pass hides a non-focus label's
  // `<text>` but plate.ts's leader path used to carry no id at all, leaving
  // a dangling dashed line pointing at nothing once the name it explained
  // was gone. Fixed by stamping `data-label-for` on the leader too (see
  // plate.ts's leaderElement) — Reader.svelte's existing `[data-label-for]`
  // omit pass then already catches it, unchanged.
  it('hides a non-focus label\'s leader line along with its name', async () => {
    const crowdedFixture = {
      id: 'trojan-plain-schematic',
      title: 'The Troad, schematic',
      kind: 'schematic',
      status: 'draft',
      size: [400, 300],
      layers: [],
    };
    // Nine places packed into a ~1% square: dense enough that plate.ts's
    // label solver detaches several names from their own pins and draws a
    // leader back to the mark (measured with a throwaway script against
    // this exact fixture shape before writing this test).
    const crowd = Array.from({ length: 9 }, (_, i) => ({
      id: `crowd-${i}`,
      name: `Crowd ${i}`,
      certainty: 'certain' as const,
      plateAnchors: {
        'trojan-plain-schematic': [0.3 + (i % 4) * 0.01, 0.4 + Math.floor(i / 4) * 0.01] as [number, number],
      },
      positionBasis: 'conjectural' as const,
    }));

    vi.mocked(fetchPlate).mockResolvedValueOnce(crowdedFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({ places: crowd });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, {
      props: { work: 'iliad', bookNum: 1, bookData: oneSceneBook(['crowd-0']) },
    });
    await screen.findByText(/Scene 1 of 1/i);
    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());

    const leaders = container.querySelectorAll('path.plate-leader');
    expect(leaders.length).toBeGreaterThan(0);
    // A non-focus id that actually drew a leader (not every crowd member
    // necessarily does — pick whichever one did, rather than assume a
    // specific id, so this test isn't coupled to the label solver's exact
    // placement choices).
    const leaderId = leaders[0].getAttribute('data-label-for');
    expect(leaderId).toBeTruthy();
    expect(leaderId).not.toBe('crowd-0'); // the focus id stays visible

    const matches = container.querySelectorAll(`[data-label-for="${leaderId}"]`);
    // The name's own <text> and its leader <path> both carry the id.
    expect(matches.length).toBe(2);
    matches.forEach((el) => expect(el).toHaveClass('plate-hidden'));
  });
});

// Chart Room plate path disabled (John, 2026-07-29 — see Reader.svelte's
// CHART_ROOM_PLATE_ENABLED and docs/TROY-MAPS-HANDOFF-2.md §1): useIliadPlate
// is forced false and the fetch-gating reactive above it never even calls
// ensureIliadPlate, so `.chart-plate` never renders and every Iliad scene
// falls to the `currentPlateMap`/nomap fallback exactly like Odyssey — the
// fetch/camera/dimming/no-rerender/reduced-motion internals this block's 6
// tests exercise are all unreachable while the flag is off (see the active
// guard test above, which pins that behavior). Skipped rather than rewritten
// so the coverage comes back verbatim when the flag flips to true.
describe.skip('Reader.svelte — Chart Room per-scene plates (Iliad only, 2026-07-28)', () => {
  // A minimal, geographically valid plate.ts fixture (shared/lib/plate.ts's
  // parsePlate/renderPlate) standing in for apparatus/plates/trojan-plain.json
  // — no layers needed (this suite is about the CAMERA/FOCUS/DIMMING wiring
  // in Reader.svelte, not plate.ts's own rendering, which is
  // shared/__tests__/plate.test.ts's job).
  const trojanPlainFixture = {
    id: 'trojan-plain',
    title: 'The Trojan Plain',
    kind: 'geographic',
    status: 'draft',
    bbox: [0, 0, 10, 10],
    size: [400, 300],
    layers: [],
  };

  const oneSceneBook = (placeIds: string[]): RawBookData => ({
    book: 1,
    scenes: [{ summary: 'A scene naming places.', startLine: 1, endLine: 3, places: placeIds }],
    segments: [
      {
        id: 'seg1',
        column: '1',
        greek: [1, 2, 3].map((n) => ({ n, text: `g${n}`, tokens: [{ t: `g${n}`, o: 0, k: `g${n}` }] })),
        // Two real bekker ticks — same posture as the describe block above:
        // Reading Mode only pages by scene (readingHasSceneAnchors) with a
        // real per-line alignment signal.
        english: {
          text: 'Scene text.',
          notes: [],
          markers: [],
          bekker: [
            { n: 1, offset: 0, real: true },
            { n: 2, offset: 6, real: true },
          ],
        },
      },
    ],
  });

  afterEach(() => {
    vi.mocked(fetchPlaces).mockReset();
    vi.mocked(fetchJourneys).mockReset();
    vi.mocked(fetchCoastline).mockReset();
    vi.mocked(fetchPlate).mockReset();
    vi.mocked(fetchPlaces).mockResolvedValue({ places: [] });
    vi.mocked(fetchJourneys).mockResolvedValue({ journeys: [] });
    vi.mocked(fetchCoastline).mockResolvedValue(null);
    vi.mocked(fetchPlate).mockResolvedValue(null);
  });

  it("frames the camera on an Iliad scene's multiple resolved places, undimmed", async () => {
    vi.mocked(fetchPlate).mockResolvedValueOnce(trojanPlainFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({
      places: [
        { id: 'place-a', name: 'Place A', coords: [3, 3], certainty: 'certain' },
        { id: 'place-b', name: 'Place B', coords: [7, 7], certainty: 'certain' },
      ],
    });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, {
      props: { work: 'iliad', bookNum: 1, bookData: oneSceneBook(['place-a', 'place-b']) },
    });
    await screen.findByText(/Scene 1 of 1/i);

    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());
    const svg = container.querySelector('.chart-plate svg')!;
    expect(svg.getAttribute('role')).toBe('img');
    expect(svg.getAttribute('aria-label')).toContain('Place A');
    expect(svg.getAttribute('aria-label')).toContain('Place B');

    // A real camera move away from the identity (whole-plate) transform —
    // proof the frame is actually keyed to the two resolved places, not just
    // showing the whole sheet.
    const cameraG = container.querySelector('.plate-camera') as HTMLElement;
    expect(cameraG).toBeTruthy();
    expect(cameraG.style.transform).not.toBe('translate(0px, 0px) scale(1)');

    // Both focused places are drawn and neither is dimmed (the "rest of the
    // plate dims" rule only applies to places OUTSIDE the current focus set).
    expect(container.querySelector('[data-place-id="place-a"]')).not.toHaveClass('plate-dimmed');
    expect(container.querySelector('[data-place-id="place-b"]')).not.toHaveClass('plate-dimmed');
  });

  it("still renders the base plate, unframed, with an honest caption when the scene's named place has no fixed position", async () => {
    vi.mocked(fetchPlate).mockResolvedValueOnce(trojanPlainFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({
      places: [{ id: 'no-coords-place', name: 'No Coords Place', certainty: 'mythical' }],
    });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, {
      props: { work: 'iliad', bookNum: 1, bookData: oneSceneBook(['no-coords-place']) },
    });
    await screen.findByText(/Scene 1 of 1/i);

    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());
    expect(container.querySelector('.chart-plate-caption')?.textContent).toBe(
      "This scene's named places have no fixed position on this plate.",
    );
    // computeCamera's own identity camera (plate.ts: "if NO id resolves to
    // any geometry, this returns {scale:1,tx:0,ty:0}") — the whole plate,
    // never a fabricated frame.
    const cameraG = container.querySelector('.plate-camera') as HTMLElement;
    expect(cameraG.style.transform).toBe('translate(0px, 0px) scale(1)');
  });

  it('gives the same honest caption when the resolved place has real coordinates but falls outside this plate\'s own frame', async () => {
    // A real, located place (mirrors Olympus/Chryse/Lemnos — real Iliad
    // scene-dictionary targets nowhere near the Troad) whose coordinates
    // simply aren't on THIS 0..10/0..10 sheet: renderPlate buckets it as
    // off-canvas, never drawing a pin for it, so it must not count as a
    // focusable id either — otherwise computeCamera would zoom the whole
    // plate in on empty parchment trying to frame a point off the canvas.
    vi.mocked(fetchPlate).mockResolvedValueOnce(trojanPlainFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({
      places: [{ id: 'far-place', name: 'Far Place', coords: [500, 500], certainty: 'certain' }],
    });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, {
      props: { work: 'iliad', bookNum: 1, bookData: oneSceneBook(['far-place']) },
    });
    await screen.findByText(/Scene 1 of 1/i);

    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());
    expect(container.querySelector('.chart-plate-caption')?.textContent).toBe(
      "This scene's named places have no fixed position on this plate.",
    );
    const cameraG = container.querySelector('.plate-camera') as HTMLElement;
    expect(cameraG.style.transform).toBe('translate(0px, 0px) scale(1)');
  });

  it('leaves Odyssey scenes on the existing renderSceneMap path, and never fetches the plate', async () => {
    vi.mocked(fetchPlaces).mockResolvedValueOnce({
      places: [{ id: 'has-coords-place', name: 'Has Coords Place', coords: [10, 20], certainty: 'certain' }],
    });
    vi.mocked(fetchCoastline).mockResolvedValueOnce({ bbox: [0, 0, 1, 1], rings: [] });

    window.history.replaceState(null, '', '/odyssey/book/1?mode=reading');
    const { container } = render(Reader, {
      props: { work: 'odyssey', bookNum: 1, bookData: oneSceneBook(['has-coords-place']) },
    });
    await screen.findByText(/Scene 1 of 1/i);

    await waitFor(() => expect(container.querySelector('.reading-plate-map svg')).toBeTruthy());
    expect(container.querySelector('.chart-plate')).toBeNull();
    expect(fetchPlate).not.toHaveBeenCalled();
  });

  it('does not re-render the plate SVG when paging between scenes, only the camera/focus', async () => {
    vi.mocked(fetchPlate).mockResolvedValueOnce(trojanPlainFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({
      places: [
        { id: 'place-a', name: 'Place A', coords: [3, 3], certainty: 'certain' },
        { id: 'place-b', name: 'Place B', coords: [7, 7], certainty: 'certain' },
      ],
    });

    const twoSceneBook: RawBookData = {
      book: 1,
      scenes: [
        { summary: 'Scene one summary.', startLine: 1, endLine: 3, places: ['place-a'] },
        { summary: 'Scene two summary.', startLine: 4, endLine: 6, places: ['place-b'] },
      ],
      segments: [
        {
          id: 'seg1',
          column: '1',
          greek: [1, 2, 3, 4, 5, 6].map((n) => ({ n, text: `g${n}`, tokens: [{ t: `g${n}`, o: 0, k: `g${n}` }] })),
          english: {
            text: 'Scene one text. Scene two text.',
            notes: [],
            markers: [],
            bekker: [
              { n: 1, offset: 0, real: true },
              { n: 4, offset: 'Scene one text. '.length, real: true },
            ],
          },
        },
      ],
    };

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, { props: { work: 'iliad', bookNum: 1, bookData: twoSceneBook } });
    await screen.findByText(/Scene 1 of 2/i);

    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());
    const svgBefore = container.querySelector('.chart-plate svg');
    const cameraG = container.querySelector('.plate-camera') as HTMLElement;
    const transformBefore = cameraG.style.transform;
    expect(container.querySelector('svg')?.getAttribute('aria-label')).toContain('Place A');

    await fireEvent.click(screen.getByRole('button', { name: /Next scene/i }));
    await screen.findByText(/Scene 2 of 2/i);

    // Same SVG element — the base markup was never reassigned via {@html}.
    expect(container.querySelector('.chart-plate svg')).toBe(svgBefore);
    // The camera itself DID move, and the aria-label now names the other
    // scene's place — proof the per-scene update ran, imperatively, on the
    // very same DOM node.
    expect(cameraG.style.transform).not.toBe(transformBefore);
    expect(container.querySelector('svg')?.getAttribute('aria-label')).toContain('Place B');
    expect(container.querySelector('svg')?.getAttribute('aria-label')).not.toContain('Place A');
  });

  it('snaps the camera instead of animating it under prefers-reduced-motion', async () => {
    vi.spyOn(window, 'matchMedia').mockImplementation((query: string) => ({
      matches: query.includes('prefers-reduced-motion'),
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }) as MediaQueryList);

    vi.mocked(fetchPlate).mockResolvedValueOnce(trojanPlainFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({
      places: [{ id: 'place-a', name: 'Place A', coords: [3, 3], certainty: 'certain' }],
    });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, {
      props: { work: 'iliad', bookNum: 1, bookData: oneSceneBook(['place-a']) },
    });
    await screen.findByText(/Scene 1 of 1/i);

    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());
    const cameraG = container.querySelector('.plate-camera') as HTMLElement;
    expect(cameraG.style.transition).toBe('none');
  });

  // Postcard part F (2026-09-02): the geographic path's click-through to
  // /maps/, framed on the scene. Belongs in THIS skipped block, not a live
  // one — there is no way to exercise `useIliadPlate` without either
  // flipping CHART_ROOM_PLATE_ENABLED in source (forbidden — John's
  // research-gated call) or a test-only override this codebase has never
  // had; every other test of this path is skipped for the identical reason.
  // Activates verbatim, with its siblings, when the flag flips to true.
  it('the postcard link is keyboard-reachable and named for its destination (John\'s click-through, part F)', async () => {
    vi.mocked(fetchPlate).mockResolvedValueOnce(trojanPlainFixture as never);
    vi.mocked(fetchPlaces).mockResolvedValueOnce({
      places: [{ id: 'place-a', name: 'Place A', coords: [3, 3], certainty: 'certain' }],
    });

    window.history.replaceState(null, '', '/iliad/book/1?mode=reading');
    const { container } = render(Reader, {
      props: { work: 'iliad', bookNum: 1, bookData: oneSceneBook(['place-a']) },
    });
    await screen.findByText(/Scene 1 of 1/i);
    await waitFor(() => expect(container.querySelector('.chart-plate svg')).toBeTruthy());

    const link = screen.getByRole('link', { name: 'Open the Trojan Plain plate framed on this scene' });
    expect(link).toBeInTheDocument();
    link.focus();
    expect(document.activeElement).toBe(link);
    expect(link.getAttribute('href')).toContain('/maps/?map=plain');
    expect(link.getAttribute('href')).toContain('focus=place-a');
  });
});
