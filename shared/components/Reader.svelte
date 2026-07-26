<script lang="ts">
  import { onMount, onDestroy, afterUpdate, tick } from 'svelte';
  import { fade } from 'svelte/transition';
  import { fetchBook, parseBekker, parseLocation, fetchSidenotes, fetchFigures, fetchSpeeches, fetchCharacters, fetchScansion, fetchAudioManifest, fetchPlaces, fetchJourneys, fetchCoastline, activeSceneIndex, type Segment, type GreekLine, type Token, type BookData, type RawBookData, type RossPiece, type Scene, type Speech, type CharacterEntry, type ScansionEntry } from '../lib/data';
  import { joinScenesToPlaces, type PlacesFile, type JourneysFile } from '../lib/scene-place';
  import { renderSceneMap, type Coastline } from '../lib/scenemap';
  import { takeSsrBook } from '../lib/ssr-book';
  import { schemeFor, formatCite } from '../lib/citation';
  import { lineRenderParts, buildFlowRows, buildEnglishTurnBlocks, labelSuppression, type SpeakerEvent, type LineRenderPart, type FlowRow, type EnglishTurnBlock } from '../lib/speakers';
  import { assignSpeakerSlots, collectDisplayOrder } from '../lib/speaker-colors';
  import { classifySpeech, realLinesFromSegments, speechLabel } from '../lib/speeches';
  import { flowParts, alignGroups } from '../lib/tick-chunks';
  import { bookAudio, hasAudio, effectiveChunks, licenseLabel, chunkAriaLabel, itemPageUrl, type AudioManifest, type AudioChunk, type AudioBookEntry } from '../lib/audio';
  import { scansionDisplay, scansionKey } from '../lib/scansion';
  import { greekFold } from '../lib/search';
  import { highlightPrefixMatches } from '../lib/text';
  import { getWork, visibleTranslations, bookLabel as workBookLabel, HOUSE_AUTHOR, type TranslationRef } from '../lib/works';
  import { touchRecent } from '../lib/resume';
  import { mergeSceneFlowChunks, resolveBoundaryOverrides, selectBoundaryOverrideEntries, sentenceSnapScenePages, type BoundaryOverride, type SceneBoundaryOverrideFile, type SceneFlowChunk, type SceneFlowPart, type TickChunkRange } from '../lib/scene-paging';
  import sceneBoundaryOverridesFile from '../lib/scene-boundary-overrides.json';
  import WordPopup from './WordPopup.svelte';
  import FootnotePopup from './FootnotePopup.svelte';

  export let work: string = 'EN';
  export let bookNum: number = 1;
  // The book's segments, read at build time and passed by ReaderShell.astro so
  // the reading text is server-rendered into the static HTML (crawlable, instant
  // paint) and the island hydrates over it. When absent (e.g. a future dynamic
  // mount), the reader falls back to fetching the JSON in onMount as before.
  export let bookData: BookData | null = null;
  // Optional per-chapter section titles {chapter: title} for this book, passed
  // by ReaderShell from chapter-titles.json. Shown in the chapter heading in
  // place of "Chapter N" (used by non-Bekker works like the Isagoge).
  export let chapterTitles: Record<string, string> = {};
  // The whole-work speaker-display roster (all books), passed by ReaderShell so
  // speaker-name colours are stable across books and match the landing cast
  // list. Null on hosts that mount a single book without it (desktop).
  export let speakerRoster: string[] | null = null;

  const workMeta = getWork(work);
  // The citation scheme this work is cited by (bekker / busse / stephanus) — the
  // single dispatch point for every scheme-conditional below, in place of
  // scattered string tests. See shared/lib/citation.ts.
  const cscheme = schemeFor(work);
  // Non-Bekker works (e.g. Porphyry's Isagoge) are cited by Busse page, not a
  // Bekker column:line. For them the reader relabels the column reference (p. N),
  // hides the per-line Greek numbers and the interpolated English gutter, and
  // titles each section from chapterTitles instead of "Chapter N".
  const busse = cscheme.id === 'busse';
  // Stephanus works (Plato) are cited by page+letter only (17a); there are no
  // user-facing Greek line numbers, and each segment shows its section token in
  // the gutter. Speaker turns are rendered as inline lead-ins (see speakers.ts).
  const stephanus = cscheme.id === 'stephanus';
  // Verse-line (Homer) works: real per-line vulgate numbers laid out as
  // genuine hexameter verse, not prose flow — scopes the hanging-indent wrap
  // CSS below (mirrors classical-philosophy-reader's dk-verse pilot, minus the
  // dk-specific fragment machinery Homer doesn't have).
  const epicVerse = cscheme.id === 'verse-line';
  // Suppress the per-line Greek numerals whenever the scheme has no user-facing
  // lines (stephanus), or a busse work that opts in via hideLineNumbers.
  const hideLineNums = !cscheme.hasUserFacingLines
    || (busse && workMeta?.citation?.hideLineNumbers === true);
  // Analytical sidenotes ({N: text}) for a busse work, floated into a right rail.
  let sidenotesData: Record<string, string> = {};
  if (busse) fetchSidenotes(work).then(d => { sidenotesData = d; }).catch(() => {});
  // Diagrams ({N: html}) rendered inline at [[figN]] markers (Tree of Porphyry).
  let figuresData: Record<string, string> = {};
  if (busse) fetchFigures(work).then(d => { figuresData = d; }).catch(() => {});
  const translations = workMeta ? visibleTranslations(workMeta) : [];
  // The reader can render any number of translations. The primary parallel
  // chunk is the 'english' slot; every other translation is a chapter-anchored
  // overlay read from its segment field (ross / third / overlays[id]).
  // `secondaries` is the ordered list of non-primary translations.
  const engSlot = translations.find(t => t.slot === 'english');
  const thirdSlot = translations.find(t => t.slot === 'third');  // bears footnotes/tables
  // The translation(s) whose prose carries [^label] footnote markers
  // (Ostwald's third slot, a primary like the Isagoge's Owen, or — Phase 4B —
  // any imported overlay whose file carried a footnotes block, flagged via
  // the same TranslationRef.footnotes bit by desktop/src/lib/imports.ts's
  // installHooks). Every such id's column renders the markers and opens the
  // footnote popup. thirdSlot is ALWAYS included (not just as a fallback when
  // nothing is explicitly flagged) so an import gaining footnotes:true never
  // silently un-flags Ostwald — this generalizes the old single-id
  // `fnTransId` without changing behavior for any existing work (today,
  // across the whole corpus, this set never has more than one member: either
  // the one explicitly-flagged translation, or thirdSlot — never both, since
  // no work currently combines them).
  const fnTransIds = new Set([
    ...translations.filter(t => t.footnotes).map(t => t.id),
    ...(thirdSlot ? [thirdSlot.id] : []),
  ]);
  const secondaries = translations.filter(t => t.slot !== 'english');
  const canCompare = translations.length >= 2;
  // Overlay pieces for a translation in a segment, selected by its slot.
  const piecesFor = (seg: Segment, t: TranslationRef | undefined | null): RossPiece[] => {
    if (!t) return [];
    if (t.slot === 'ross') return seg.ross ?? [];
    if (t.slot === 'third') return seg.third ?? [];
    if (t.slot === 'overlay') return seg.overlays?.[t.id] ?? [];
    return [];
  };
  const transById = (id: string | null | undefined): TranslationRef | null =>
    id ? (translations.find(t => t.id === id) ?? null) : null;

  // §Phase-4B-revised (John's call 2026-07-06): an imported translation's own
  // converter-derived chapter title is this edition's editorial paratext, not
  // work-level chrome — it renders as a small unaligned heading INSIDE that
  // import's own overlay column (see transFlow below), never merged into the
  // shared chapterTitles heading map above. Resolved through a window-level
  // hook installed by desktop/src/lib/imports.ts's installHooks(), the same
  // site-shared pattern __ARISTOTLE_IMPORT_FOOTNOTE_HOOK__ uses (see
  // FootnotePopup.svelte) — this component is SHARED with the static site
  // build, which never installs the hook, so the lazy read below is always
  // undefined there: inert, byte-identical rendering. Render-only: sourced
  // from ImportRecord.titles, never written into any offset-bearing text
  // stream, so no anchor ever shifts.
  function importChapterTitle(transId: string, chapter: string | null): string {
    if (!chapter) return '';
    const hook = (globalThis as {
      __ARISTOTLE_IMPORT_TITLE_HOOK__?: (work: string, id: string, book: number, chapter: string) => string | null;
    }).__ARISTOTLE_IMPORT_TITLE_HOOK__;
    return (hook ? hook(work, transId, bookNum, chapter) : null) ?? '';
  }

  // Compare mode shows two translations side by side; which two is chosen in the
  // settings sidebar. Defaults: primary + first secondary. Persisted per work.
  let compareLeft: string = engSlot?.id ?? translations[0]?.id ?? 'english';
  let compareRight: string = secondaries[0]?.id ?? translations[1]?.id ?? compareLeft;
  const CMPL_KEY = `reader-cmpl-${work}`;
  const CMPR_KEY = `reader-cmpr-${work}`;
  function saveCompare() {
    try { localStorage.setItem(CMPL_KEY, compareLeft); localStorage.setItem(CMPR_KEY, compareRight); } catch {}
  }
  // The two columns must differ — two identical translations is never useful.
  // Pick the first other translation to fill the freed side.
  function otherTrans(exclude: string): string {
    return translations.find(t => t.id !== exclude)?.id ?? exclude;
  }
  function pickCompareLeft() {
    if (compareLeft === compareRight) compareRight = otherTrans(compareLeft);
    saveCompare(); setTrans('compare');
  }
  function pickCompareRight() {
    if (compareRight === compareLeft) compareLeft = otherTrans(compareRight);
    saveCompare(); setTrans('compare');
  }

  // Client-hydrate helper: refill each Greek line's stripped `tokens` array from
  // the server-rendered token spans (`<span class="tok" data-k data-o>surface</span>`)
  // already in the DOM, keyed by the line's DOM id (`L{column}-{n}`, the template's
  // formula). This runs in component init — BEFORE the first hydration render — so
  // lineRenderParts reproduces the exact same parts and Svelte claims the existing
  // spans instead of wiping them. Only the token markup is stripped from the props
  // (stripBookForClient); everything the renderer needs is either kept in the prop
  // or recovered here. Mutates `d` in place.
  function rebuildTokensFromDom(d: BookData): void {
    if (typeof document === 'undefined') return;
    for (const seg of d.segments) {
      for (const line of seg.greek) {
        if (line.tokens.length) continue;
        const el = document.getElementById(`L${seg.column}-${line.n}`);
        const spans = el?.querySelectorAll<HTMLElement>('.line-text .tok');
        if (!spans || !spans.length) continue;
        line.tokens = Array.from(spans, (s) => ({
          t: s.textContent ?? '',
          o: Number(s.dataset.o ?? '0'),
          k: s.dataset.k ?? '',
        }));
      }
    }
  }

  // Resolve the book this render consumes. On the SERVER, ReaderShell stashed the
  // FULL book (with Greek tokens) in the SSR channel so the static render emits the
  // token spans; the island's serialized props instead carry the token-stripped
  // copy. On the CLIENT we take that stripped prop and rebuild its tokens from the
  // SSR DOM before the first render (no wipe). The non-default translations were
  // stripped too — ensureFullBook fetches them lazily on the first switch/compare.
  const ssrFull = typeof window === 'undefined' ? takeSsrBook() : null;
  if (!ssrFull && bookData?.tokensStripped) rebuildTokensFromDom(bookData);
  const activeBook = ssrFull ?? bookData;

  // Seeded from the build-time prop so SSR renders the text; stays empty (and
  // `loading` true) only in the fetch-fallback path.
  let segments: Segment[] = activeBook?.segments ?? [];
  // Global turn flow of a dialogue book (stephanus): drives the turn-row
  // rendering; null keeps the section-segment rendering.
  let turnFlow = activeBook?.turnFlow ?? null;
  let loading = !activeBook;
  // Whether the reader already holds the FULL book (Greek tokens + every
  // translation). False only on the client after a token-stripped prop: the
  // default (English-slot) view renders from the stripped prop, but switching to
  // a non-default translation or compare must first pull the full book in.
  let fullLoaded = !bookData?.tokensStripped;
  let fullBookLoading = false;
  let fullBookError = '';
  let fullBookRequest: Promise<void> | null = null;
  // Keep a URL-selected overlay pending until it can render, rather than
  // replacing the SSR-safe single translation with empty compare columns.
  let deferredQueryTrans = '';
  let mounted = false;
  async function ensureFullBook(): Promise<void> {
    if (fullLoaded) return;
    if (fullBookRequest) return fullBookRequest;
    fullBookLoading = true;
    fullBookError = '';
    const request = fetchBook(work, bookNum).then((data) => {
      segments = data.segments;
      turnFlow = data.turnFlow ?? null;
      scenes = data.scenes ?? scenes;
      scenesDraft = (data as RawBookData).apparatus?.draft === true || scenesDraft;
      fullLoaded = true;
      if (deferredQueryTrans) {
        const next = deferredQueryTrans;
        deferredQueryTrans = '';
        trans = next;
        if (next !== 'compare') lastSingle = next;
      }
    }).catch(() => {
      fullBookError = 'Unable to load this translation.';
    }).finally(() => {
      fullBookLoading = false;
      fullBookRequest = null;
    });
    fullBookRequest = request;
    return request;
  }
  function retryFullBook() { void ensureFullBook(); }
  let error = '';
  // OS "reduce motion" preference — gates the JS fade transitions below, which
  // the CSS @media (prefers-reduced-motion) query can't reach. Set in onMount.
  let reduceMotion = false;

  // Search jump-in: highlight query terms + scroll to a line (?hlg=&hle=&loc=).
  let hlGrkFolds: string[] = [];
  let hlEngTerms: string[] = [];
  let targetId: string | null = null;

  // Which translation fills the English column: a translation id from the
  // registry (its slot decides what renders) or 'compare' = both slots side by
  // side. Persisted per work (works carry different translations).
  // First-load translation: the work's preferred default if it names one (and
  // it's actually visible in this build), else the primary 'english' slot. A
  // saved choice or ?trans= query param overrides this in onMount.
  const defaultTrans = translations.find(t => t.id === workMeta?.defaultTranslation)?.id;
  let trans: string = defaultTrans ?? engSlot?.id ?? translations[0]?.id ?? 'english';
  // The translation ids currently on screen: the single selection, or the two
  // compare columns. Drives the gutter disclaimer and the citation strip.
  $: shownTransIds = trans === 'compare' ? [compareLeft, compareRight] : [trans];
  // Whether a translation carries any approximate (interpolated) Bekker ticks in
  // a segment — overlays whose gutter is fully anchored show none, so the note
  // is suppressed for them.
  const transApprox = (seg: Segment, id: string): boolean => {
    const t = transById(id);
    if (!t) return false;
    if (t.slot === 'english') return !!seg.english?.bekker?.some((x) => !x.real);
    return piecesFor(seg, t).some((p) => p.bekker?.some((x) => !x.real));
  };
  $: hasApproxTicks = view !== 'greek'
    && segments.some((seg) => shownTransIds.some((id) => transApprox(seg, id)));
  const TRANS_KEY = `reader-trans-${work}`;
  const CITE_KEY  = 'reader-cite-copy';
  // The "ℹ︎ Bekker numbers" popover (upright = fixed, italic = estimate).
  let bekkerInfoOpen = false;
  let citeCopy = true;
  function saveCiteCopy() { try { localStorage.setItem(CITE_KEY, String(citeCopy)); } catch {} }

  // ── Speaker-name colourisation ───────────────────────────────────────────
  // OFF by default. When on, each distinct speaker in the current dialogue gets
  // one of a small palette of complementary hues (--spk-* in global.css),
  // applied to the .speaker lead-in NAME only — never the speech text. Once the
  // slot is stamped on the span as data-spk, the whole effect is CSS, so the
  // toggle merely flips a container class (.spk-color) with no re-render.
  const SPK_KEY = 'reader-spkcolor';
  // On by default; a reader who turns it off has that choice remembered
  // (onMount reads SPK_KEY, which only exists once they've toggled it).
  let spkColor = true;
  function saveSpkColor() { try { localStorage.setItem(SPK_KEY, String(spkColor)); } catch {} }
  // display → palette slot for every NAMED speaker in this book's turn flow
  // (turns, embedded `et` speeches, folded `sub` speeches). Slot assignment is
  // shared with the landing-page cast list (shared/lib/speaker-colors) so a
  // speaker gets the same hue in both. Unattributed em-dash turns have no
  // display and are never coloured.
  // Prefer the whole-work roster (passed by ReaderShell.astro) so a speaker's
  // colour is stable across every book AND matches the landing cast list; fall
  // back to the current book alone when no roster is supplied (e.g. the desktop
  // shell, which mounts a single book).
  $: spkSlots = assignSpeakerSlots(
    speakerRoster && speakerRoster.length ? speakerRoster : collectDisplayOrder([turnFlow]),
  );
  // The last single-translation choice, remembered so leaving compare mode
  // returns to it (and so the picker has something to display in compare).
  let lastSingle: string = trans;
  function setTrans(t: string) {
    // A reader action supersedes an in-flight URL selection; otherwise a late
    // response could unexpectedly switch the column back to that URL value.
    deferredQueryTrans = '';
    fullBookError = '';
    trans = t;
    if (t !== 'compare') lastSingle = t;
    try { localStorage.setItem(TRANS_KEY, t); } catch {}
  }
  // The dropdowns select WHICH translation; mode (single vs compare) is chosen
  // in the settings sidebar. Picking a translation always means "show me this
  // one" — including from compare mode, which it exits.
  $: pickValue = trans === 'compare' ? lastSingle : trans;
  function onPick(e: Event) {
    setTrans((e.currentTarget as HTMLSelectElement).value);
  }

  // ── Settings sidebar ──────────────────────────────────────────────────────
  let settingsOpen = false;
  const FS_KEY = `reader-fs-${work}`;
  const LH_KEY = `reader-lh-${work}`;
  const COLW_KEY = `reader-colw-${work}`;
  // Base CSS values from global.css; scale as multipliers (1.0 = default).
  const FS_GREEK_BASE = 1.05;
  const FS_ENG_BASE   = 1.08;
  const LH_GREEK_BASE = 1.7;
  const LH_ENG_BASE   = 1.72;
  let fsScale = 1.0;
  let lhScale = 1.0;
  // Column-width scale: multiplies the layout's width caps (reader measure,
  // mono-view column measure) via --colw-scale; 1.0 = the stock layout.
  let colScale = 1.0;
  $: fsGreek = (FS_GREEK_BASE * fsScale).toFixed(3);
  $: fsEng   = (FS_ENG_BASE   * fsScale).toFixed(3);
  $: lhGreek = (LH_GREEK_BASE * lhScale).toFixed(3);
  $: lhEng   = (LH_ENG_BASE   * lhScale).toFixed(3);
  // The settings drawer is `inert` when closed (see the <aside> below), so it's
  // out of the tab order there. When open it needs the modal dance: move focus
  // in, trap Tab, and restore focus to the opener on close.
  let settingsEl: HTMLElement | undefined;
  let settingsReturnFocus: HTMLElement | null = null;
  function settingsFocusables(): HTMLElement[] {
    return settingsEl
      ? Array.from(settingsEl.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        )).filter((el) => el.offsetParent !== null)
      : [];
  }
  function onSettingsKey(e: KeyboardEvent) {
    if (e.key !== 'Tab') return;
    const f = settingsFocusables();
    if (!f.length) { e.preventDefault(); settingsEl?.focus(); return; }
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }
  function closeSettings() {
    if (!settingsOpen) return;
    settingsOpen = false;
    window.dispatchEvent(new CustomEvent('settings-state', { detail: { open: false } }));
    // Restore focus to the header toggle that opened the drawer.
    (settingsReturnFocus ?? document.querySelector<HTMLElement>('.settings-toggle'))?.focus();
    settingsReturnFocus = null;
  }
  function openSettings() {
    if (settingsOpen) return;
    settingsReturnFocus = document.activeElement as HTMLElement | null;
    settingsOpen = true;
    window.dispatchEvent(new CustomEvent('settings-state', { detail: { open: true } }));
    // Settings and the word-lookup panel are both right-docked, fixed
    // full-height panels (.settings-sidebar / .word-sidebar in global.css);
    // open together they stack, and the lexicon's higher z-index (101 vs 50)
    // intercepts clicks meant for Settings. Mutually exclusive, like every
    // other drawer pair in this reader — opening one closes the other.
    if (popup) closePopup();
    // Wait for the drawer to un-inert, then focus its close button.
    tick().then(() => (settingsEl?.querySelector('.settings-close') as HTMLElement | null)?.focus());
  }
  function saveFs() { try { localStorage.setItem(FS_KEY, String(fsScale)); } catch {} }
  function saveLh() { try { localStorage.setItem(LH_KEY, String(lhScale)); } catch {} }
  function saveColw() { try { localStorage.setItem(COLW_KEY, String(colScale)); } catch {} }
  function resetSettings() {
    fsScale = 1.0; lhScale = 1.0; colScale = 1.0; citeCopy = true; spkColor = true;
    try {
      localStorage.removeItem(FS_KEY); localStorage.removeItem(LH_KEY);
      localStorage.removeItem(COLW_KEY); localStorage.removeItem(CITE_KEY);
      localStorage.removeItem(SPK_KEY);
    } catch {}
  }

  // ── Citation shown in the controls strip ─────────────────────────────────
  // The strip is filled with the bibliographic provenance so it reads as a
  // header, not a lone toggle. The Greek source comes from the registry; the
  // translation citation from the currently-selected translation. `short` forms
  // ("Ross (1908)") sit beside the controls in bilingual view; the full forms
  // fill the otherwise-empty bar in Greek-only / English-only.
  const greekSrc = workMeta?.greekSource;
  $: selectedTrans = trans === 'compare'
    ? null
    : (translations.find(t => t.id === trans) ?? null);
  const yearOf = (s: string) => { const m = s.match(/(\d{4})/); return m ? m[1] : ''; };
  const citeShort = (t: { short: string; name: string } | null | undefined) => {
    if (!t) return '';
    const y = yearOf(t.name);
    return y ? `${t.short} (${y})` : t.short;
  };
  // Bilingual strip: short Greek source · short translation (omit either if absent).
  $: pairText = [greekSrc?.short, citeShort(selectedTrans)].filter(Boolean).join(' · ');

  type View = 'both' | 'greek' | 'english';
  let view: View = 'both';
  async function setView(v: View) {
    view = v;
    try { localStorage.setItem('reader-view', v); } catch {}
    // The tracked anchors differ by view (Greek lines vs. whole columns), so
    // rebuild the scroll-spy once the DOM reflects the new view.
    await tick();
    if (spyArmed) setupScrollSpy();
  }

  // ── Reading Mode posture (Phase 3 flagship; scene-paged since 2026-07-18) ──
  // Two postures: Scholar (the parallel-column reader above, unchanged) and
  // Reading Mode — a single generous column of ONE translation, minimal
  // chrome, PAGED BY SCENE (John's directive, 2026-07-18: a whole book's prose
  // is too long as one scroll). Toggled by the `r` keystroke (guarded against
  // firing in form fields) or the header button. Persisted GLOBALLY (like
  // reader-view), and openable via ?mode=reading. Announced to screen readers
  // (aria-live).
  const POSTURE_KEY = 'reader-posture';
  let reading = false;
  let postureMsg = '';
  function savePosture() { try { localStorage.setItem(POSTURE_KEY, reading ? 'reading' : 'scholar'); } catch {} }
  // Whether focus currently sits in a field that should swallow a bare
  // keystroke shortcut (typing `r`, arrow-paging scenes) rather than let it
  // fire as a reader command. Shared by onGlobalKey's `r` and arrow-key branches.
  function focusInField(): boolean {
    const ae = document.activeElement as HTMLElement | null;
    const tag = ae?.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || !!ae?.isContentEditable;
  }
  // Entering Reading Mode opens on the scene containing whatever line Scholar
  // had at the top of the viewport (computeCurrentScene, called here BEFORE
  // `reading` flips so its own `reading` guard still lets it scan); exiting
  // scrolls Scholar back to that scene's opening line (jumpToScene, called
  // after `reading` is already false so it takes the Greek-anchor branch).
  // Both scroll adjustments wait a tick for the posture's DOM swap to land.
  function setReading(on: boolean) {
    if (reading === on) return;
    if (on && scenes.length) { computeCurrentScene(); readingSceneIndex = currentSceneIndex; }
    reading = on;
    // P3 fix (independent review, 2026-07-25): the scene-context rail only
    // renders while `!reading && chartRoomOpen` (see the template below), so
    // switching TO Reading with Chart Room open removed the rail out from
    // under `#nav-chart-room`'s aria-controls/aria-expanded without either
    // attribute being cleared (nothing here used to touch chartRoomOpen).
    // Closing it here — the same chartRoomOpen mutation + persist
    // toggleChartRoom itself uses — lets the existing chartRoomOpen reactive broadcast
    // (below) and ReaderShell's chart-room-state listener clear both
    // attributes through the one mechanism that already owns them, rather
    // than a second place learning to clear aria-controls.
    if (on && chartRoomOpen) { chartRoomOpen = false; saveChartRoom(); }
    postureMsg = on ? 'Reading mode' : 'Scholar view';
    savePosture();
    saveSceneParam();
    tick().then(() => {
      if (reading) scrollReadingToTop();
      else if (scenes.length) jumpToScene(readingSceneIndex);
    });
  }
  function toggleReading() { setReading(!reading); }

  // ── Nav-bar bridge broadcasts (John's nav-bar merge brief, 2026-07-24) ────
  // ReaderShell.astro server-renders the translation/view/posture/Chart Room
  // controls in .nav-panel (the parent Astro island can't know client-only
  // state — a restored localStorage choice, a `?trans=`/`?mode=` override —
  // at build time), so these reactive statements broadcast this component's
  // authoritative state on every change; ReaderShell's plain-script listeners
  // (mirroring its existing settings-state/scenes-state pattern) use them to
  // sync the server-rendered controls' selected option / active button /
  // aria-pressed after hydration. Gated on `mounted` (set once onMount's
  // restoration from localStorage/URL settles) so each also fires exactly
  // once at that point, correcting any SSR-default mismatch — no separate
  // "initial sync" dispatch is needed.
  $: if (mounted) window.dispatchEvent(new CustomEvent('trans-state', { detail: { id: pickValue } }));
  $: if (mounted) window.dispatchEvent(new CustomEvent('view-state', { detail: { view } }));
  $: if (mounted) window.dispatchEvent(new CustomEvent('reading-state', { detail: { reading } }));
  $: if (mounted) window.dispatchEvent(new CustomEvent('chart-room-state', { detail: { open: chartRoomOpen } }));

  // `r` toggles posture; ←/→ page Reading Mode's current scene. Neither fires
  // while focus is in a text field (a reader typing in the Bekker jump /
  // search box, or a future note input), nor as part of a modifier chord.
  function onGlobalKey(e: KeyboardEvent) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key === 'r' || e.key === 'R') {
      if (focusInField()) return;
      e.preventDefault();
      toggleReading();
      return;
    }
    if (reading && scenes.length && !e.shiftKey && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
      if (focusInField()) return;
      e.preventDefault();
      if (e.key === 'ArrowLeft') prevScene(); else nextScene();
    }
  }
  // The single translation Reading Mode shows: the current selection, or — in
  // compare mode — the last single choice (pickValue already resolves this).
  // Never 'compare'.
  $: readingTransId = pickValue;
  // Whether readingTransId's own bekker ticks are CURATED scene-boundary
  // anchors (works.ts's TranslationRef.curatedTicks — Pope, T3 lane
  // 2026-07-21) rather than dense milestone ticks. A curated tick is already
  // exact, so it must NOT be moved by speech-snapping (see the readingChunks
  // alignGroups call below) — snapping exists to correct MILESTONE-tick
  // drift near a speech's true opening line, and applying it to an anchor
  // that's already correct could only knock it off target.
  $: readingTransCuratedTicks = !!translations.find(t => t.id === readingTransId)?.curatedTicks;

  // ── Reading Mode scene paging ─────────────────────────────────────────────
  // The scene Reading Mode currently pages to (0-based into `scenes`),
  // clamped whenever `scenes` is shorter than a restored/URL index. Position
  // lives in the URL (?scene=, 1-based for a human-shareable link), never
  // localStorage — it's book-specific and share-worthy, not a durable
  // preference (unlike POSTURE_KEY above).
  let readingSceneIndex = 0;
  $: clampedSceneIndex = scenes.length ? Math.max(0, Math.min(readingSceneIndex, scenes.length - 1)) : 0;

  // Every tick-anchored chunk of the CURRENTLY SHOWN translation's flow, in
  // reading order, across every block of every segment (Homer books are one
  // segment/one block each, but this doesn't assume that). Reuses alignGroups
  // — the same tick-chunker the phone "Both" view already relies on — passed
  // THIS translation's own flow (not always block.flow/Murray) so paging a
  // non-primary translation (Butler/Pope) chunks by ITS OWN ticks.
  interface ReadingChunk extends TickChunkRange, SceneFlowChunk {}
  $: readingChunks = ((): ReadingChunk[] => {
    if (!reading || flowRows) return [];
    const out: ReadingChunk[] = [];
    for (const { blocks } of enrichedSegments) {
      for (const block of blocks) {
        const flow = readingTransId === engSlot?.id ? block.flow : (block.oflows[readingTransId] ?? []);
        if (!flow.length) continue;
        for (const g of alignGroups(block.lines, flow, readingTransCuratedTicks ? [] : bookSpeechStarts)) {
          if (!g.lines.length) continue;
          out.push({
            startLine: g.lines[0].n, endLine: g.lines[g.lines.length - 1].n,
            flowParts: g.flowParts, otables: block.otables,
          });
        }
      }
    }
    return out;
  })();
  // Whether the currently shown translation carries any REAL internal
  // paging signal beyond the whole book (John, 2026-07-19: "CAN WE HAVE ALL
  // THREE DIVIDED INTO SCENE CHUNKS?" — investigated: Murray/Butler carry
  // dozens of ~5-line milestone ticks per book; Pope's overlay carried
  // exactly ONE bekker anchor per book, at n=1/offset=0 — a book-level-only
  // alignment, confirmed across every Iliad/Odyssey book). Fewer than two
  // chunks means chunksForScene resolves to the same single whole-book chunk
  // for every scene, so there is no real per-scene boundary to page — see
  // readingWholeBookFlow below for the honest fallback. T3 lane (2026-07-21):
  // Pope now carries a `curatedTicks` translation (works.ts) — once the
  // pipeline lane re-emits its ~15 curated scene-boundary ticks per book,
  // Pope will have readingChunks.length > 1 like Murray/Butler and this
  // branch goes dormant for it automatically; no logic here changes.
  $: readingHasSceneAnchors = readingChunks.length > 1;
  // Sentence-snapped Reading Mode pages, one per scene, computed once for
  // the whole book (shared/lib/scene-paging.ts's sentenceSnapScenePages,
  // pure + unit-tested) — John, 2026-07-19: "SCENES SHOULD NOT BREAK UP
  // SENTENCES... EACH SCENE NEEDS TO BEGIN WITH A COMPLETE SENTENCE." A
  // single forward pass repartitions the whole book's prose so every page
  // starts and ends at an English sentence boundary and the book's text is
  // covered exactly once (no loss, no duplication) — replacing the previous
  // chunksForScene(scene)+mergeSceneFlowChunks(scene) per-scene merge, which
  // rendered whole tick-chunks that could straddle (and thus duplicate) a
  // scene boundary and still cut a page open/closed mid-sentence.
  // Manual editorial boundary pins (John, 2026-07-21 review) — see
  // shared/lib/scene-boundary-overrides.json's header + shared/lib/
  // scene-paging.ts's resolveBoundaryOverrides doc. A resolution failure
  // (anchor text drifted out of the corpus, or a stale scene number) must
  // never crash Reading Mode for a reader — surfaced via console.error and
  // the page falls back to the plain algorithmic boundary for that book; the
  // audit/test gate is what treats this as a hard failure during development.
  $: sceneBoundaryOverrides = ((): BoundaryOverride[] => {
    if (!scenes.length || !readingHasSceneAnchors) return [];
    const entries = selectBoundaryOverrideEntries(
      sceneBoundaryOverridesFile as SceneBoundaryOverrideFile, work, bookNum, readingTransId,
    );
    if (!entries.length) return [];
    try {
      return resolveBoundaryOverrides(readingChunks, scenes, entries);
    } catch (err) {
      console.error('scene-boundary override resolution failed', err);
      return [];
    }
  })();
  $: sentenceSnappedPages = scenes.length && readingHasSceneAnchors
    ? sentenceSnapScenePages(readingChunks, scenes, { boundaryOverrides: sceneBoundaryOverrides })
    : [];
  $: currentSceneFlow = sentenceSnappedPages[clampedSceneIndex] ?? { flowParts: [], otables: {} };
  // Honest degradation for a book-level-only translation (Pope — see
  // readingHasSceneAnchors above): rather than fabricate a per-scene split
  // with no real alignment signal (CLAUDE.md: never invent alignment),
  // Reading Mode shows the whole book once, with a notice; readingView below
  // hides the scene nav in this branch. This is the SAME whole-book merge
  // chunksForScene's own fallback used to produce once per scene (by
  // accident, since its one chunk overlaps every scene) — made intentional.
  $: readingWholeBookFlow = scenes.length && !readingHasSceneAnchors && readingChunks.length
    ? mergeSceneFlowChunks(readingChunks)
    : { flowParts: [], otables: {} };

  // Reads `readingSceneIndex` directly (clamping inline) rather than the
  // reactive `clampedSceneIndex` — a `$:` recompute is batched, so a caller
  // that just assigned `readingSceneIndex` and calls this synchronously
  // (gotoScene, setReading) would otherwise write the URL one step stale.
  function saveSceneParam() {
    try {
      const url = new URL(window.location.href);
      if (reading && scenes.length) {
        const idx = Math.max(0, Math.min(readingSceneIndex, scenes.length - 1));
        url.searchParams.set('scene', String(idx + 1));
      } else {
        url.searchParams.delete('scene');
      }
      history.replaceState(history.state, '', url);
    } catch {}
  }
  // Scroll the new scene's header to the top of the viewport — a "page turn"
  // reset, so a long previous scene doesn't leave the next one's start
  // scrolled off-screen. Suppressed like every other programmatic jump so it
  // doesn't fight the scroll-spy/citation-hash tracking.
  function scrollReadingToTop() {
    const head = readerBodyEl?.querySelector('.reading-scene-head');
    if (!head) return;
    suppressArmUntil = Date.now() + 900;
    head.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
  }
  function gotoScene(i: number) {
    if (!scenes.length) return;
    readingSceneIndex = Math.max(0, Math.min(i, scenes.length - 1));
    currentSceneIndex = readingSceneIndex; // keeps the scene-rail highlight in sync
    saveSceneParam();
    tick().then(scrollReadingToTop);
  }
  function prevScene() { gotoScene(clampedSceneIndex - 1); }
  function nextScene() { gotoScene(clampedSceneIndex + 1); }

  // Lazy full-book load: the token-stripped prop carries only the English-slot
  // translation, so the moment a NON-default translation becomes visible (single,
  // either compare column, or Reading Mode's chosen translation) we pull the full
  // book in (Greek tokens + every translation). No-op once loaded, and never fires
  // for the default English view — which renders entirely from the stripped prop.
  $: wantsNonDefaultTrans =
    shownTransIds.some((id) => !!id && id !== engSlot?.id) ||
    (reading && readingTransId !== engSlot?.id) ||
    (deferredQueryTrans !== '' && deferredQueryTrans !== engSlot?.id);
  $: if (mounted && !fullLoaded && wantsNonDefaultTrans && !fullBookLoading && !fullBookError) ensureFullBook();

  // Landmark-style scene apparatus for this book (see data.ts Scene). Absent on
  // every payload today, so `scenes` is empty and Reading Mode degrades to
  // plain single-column prose; scene paging (below) activates only when real
  // scene data lands.
  let scenes: Scene[] = activeBook?.scenes ?? [];
  // Whether this book's apparatus (scenes + cartouche fields) is AI-drafted and
  // still pending John's review. Drives the discreet DRAFT badge on the
  // Reading Mode scene header and the scene-rail — CLAUDE.md's
  // apparatus-honesty rule. Set from the same `apparatus.draft` the cartouche
  // reads; refreshed in the desktop fetch path below.
  let scenesDraft: boolean =
    (activeBook as RawBookData | null)?.apparatus?.draft === true;
  // Apologoi day-honesty cue (John, phone session 2026-07-18): a book whose
  // apparatus marks its book-level `where` "… (telling)" (the pipeline's
  // frame-scene marker — Odysseus narrating at Alcinous's palace — set on the
  // book aggregate, never on an individual scene's `location`/`place`; see
  // RawBookData in data.ts) is narrated in flashback: every scene in it shares
  // the FRAME's day number (all of Od. 9's "Day 34" is the evening of the
  // telling, not when the Cicones/Lotus-eaters/Cyclops events themselves
  // fell). Read once from the initial book payload (like scenesDraft above) —
  // no book-number hardcoding — so the day display can read "Day 34 ·
  // telling" instead of a bare, chronologically-misleading "Day 34". Known
  // gap: Od. 10 and 12 are equally part of the same told-in-flashback frame
  // but carry no "(telling)" marker of their own (the frame only opens in
  // Book 9 and closes in Book 11), so this display-only cue can't reach
  // them — that needs a data-side fix (apparatus/staging + re-merge), out of
  // scope here.
  const bookTellingDay: boolean =
    (activeBook as RawBookData | null)?.apparatus?.where?.includes('(telling)') === true;

  // ── Reading Mode figure plate (per-scene map, Variant B) ───────────────────
  // The gazetteer (places.json) + nostoi legs (journeys.json) needed to join a
  // scene to a real, mappable place (shared/lib/scene-place.ts) plus the
  // vendored coastline (shared/lib/scenemap.ts) the map itself is drawn
  // against — all three payload-disciplined like fetchSpeeches/fetchCharacters
  // above: nothing fetches until Reading Mode is entered or a Chart Room surface
  // explicitly requests it, so Scholar-only readers who leave the rail closed
  // never pay for the ~200KB combined. Guarded by `plateDataLoaded` the same
  // way `speechesLoaded` guards ensureSpeeches, including the reset-on-failure
  // retry.
  let plateDataLoaded = false;
  let platePlaces: PlacesFile = { places: [] };
  let plateJourneys: JourneysFile = { journeys: [] };
  let plateCoastline: Coastline | null = null;
  async function ensurePlateData(): Promise<void> {
    if (plateDataLoaded) return;
    plateDataLoaded = true;
    try {
      const [pl, jo, co] = await Promise.all([fetchPlaces(), fetchJourneys(), fetchCoastline()]);
      platePlaces = pl;
      plateJourneys = jo;
      plateCoastline = co;
    } catch {
      plateDataLoaded = false;
    }
  }
  // Chart Room context is deliberately lazy too: the desktop rail stays off by
  // default, and the mobile sheet only needs the gazetteer after it is expanded.
  // A persisted desktop-rail choice must not wake this payload on a phone, where
  // that rail is unavailable.
  const CHART_ROOM_KEY = 'reader-chart-room';
  let chartRoomOpen = false;
  let sceneSheetOpen = false;
  let scenePanelMobile = false;
  function saveChartRoom() { try { localStorage.setItem(CHART_ROOM_KEY, String(chartRoomOpen)); } catch {} }
  function toggleChartRoom() {
    chartRoomOpen = !chartRoomOpen;
    if (!chartRoomOpen && !sceneRailOpen && !sheetNeedsSceneTracking) {
      window.removeEventListener('scroll', onSceneScroll);
      sceneTrackingArmed = false;
    }
    saveChartRoom();
  }
  function toggleSceneSheet() { sceneSheetOpen = !sceneSheetOpen; }
  // FIX 2 (John's iPhone Safari report, 2026-07-18): Astro wraps every
  // hydrated island in `<astro-island>`, styled `display: contents` by
  // Astro's own runtime CSS (astro-island-styles.js) so the island is
  // transparent to layout. WebKit has a long-documented bug where a
  // `position: fixed` DESCENDANT of a `display: contents` ancestor can fail
  // to resolve the viewport as its containing block (Chromium is
  // unaffected — matches the reported Chromium-pinned / WebKit-floating
  // divergence exactly). `.scene-context-sheet` is the only fixed-position
  // element in this island, and the astro-island wrapper is its ONLY
  // display:contents ancestor (audited: neither <body> nor <html> — see
  // shared/styles/global.css's `html`/`body` rules — nor any ancestor
  // WITHIN this component, since the sheet is a top-level sibling of
  // `.reader-body`, not nested inside `.book-plate`/`.reading-plate`, carry
  // transform/filter/backdrop-filter/will-change/contain/perspective/
  // container-type). Astro's runtime CSS isn't ours to edit (vendored,
  // site-wide blast radius), so instead: teleport the sheet's DOM node to a
  // direct child of <body> on mount — no longer a descendant of ANY
  // display:contents element, on either engine. SSR-safe: this action only
  // runs client-side, so a no-JS load keeps the pre-existing in-place
  // render (same posture as every other JS-only enhancement here).
  function teleportToBody(node: HTMLElement) {
    if (typeof document === 'undefined') return {};
    document.body.appendChild(node);
    return {
      destroy() {
        node.parentNode?.removeChild(node);
      },
    };
  }
  function computeScenePanelViewport() {
    scenePanelMobile = typeof window !== 'undefined'
      && window.matchMedia('(max-width: 680px)').matches;
  }
  $: if (mounted && scenes.length && !plateDataLoaded
    && (reading || sceneSheetOpen || (chartRoomOpen && !scenePanelMobile))) ensurePlateData();

  // FIX 3 (John's phone report, 2026-07-18): the mobile sheet's COLLAPSED bar
  // already shows the current scene's title (scenePanelScene, below), so
  // tracking must arm on the sheet's mere presence — a scenes-bearing book,
  // mobile viewport, Scholar view (Reading Mode pages scenes itself via
  // clampedSceneIndex; scenePanelIndex already branches on `reading`, below)
  // — not on sceneSheetOpen (that only gates the lazy map-payload fetch
  // above, unchanged). Unlike the scene rail / Chart Room, this consumer has
  // no click to hook an explicit arm/disarm to, so both directions are
  // reactive: mirrors their idempotent-guarded armSceneTracking, and tears
  // down only once NO consumer (rail, Chart Room, or this) still needs it.
  $: sheetNeedsSceneTracking = !!(scenes.length && scenePanelMobile && !reading);
  $: if (mounted && sheetNeedsSceneTracking) armSceneTracking();
  $: if (mounted && sceneTrackingArmed && !sceneRailOpen && !chartRoomOpen && !sheetNeedsSceneTracking) {
    window.removeEventListener('scroll', onSceneScroll);
    sceneTrackingArmed = false;
  }

  // Every scene's resolved place/route (or null — no mappable place anywhere
  // in this book), recomputed whenever the book's scenes or the fetched
  // gazetteer/journeys change. Cheap pure joins (shared/lib/scene-place.ts),
  // so resolving the whole book at once (rather than just the current scene)
  // keeps Previous/Next scene paging in sync with zero recompute lag.
  $: scenePlaceResolutions = plateDataLoaded && scenes.length
    ? joinScenesToPlaces(work, bookNum, scenes, platePlaces, plateJourneys)
    : [];
  // The current scene page's resolved place/route and its rendered map SVG —
  // undefined/null before plateDataLoaded resolves, or when the current
  // scene's anchor place has no coords (mythical tier, or the book names
  // nothing mappable at all): the plate then renders title/metadata only,
  // never a fabricated or empty map box (CLAUDE.md apparatus honesty).
  // Scholar view already maintains currentSceneIndex for the scene rail. The
  // Chart Room reuses it rather than adding a second scroll tracker; Reading
  // Mode's scene pager continues to own the equivalent clampedSceneIndex.
  $: scenePanelIndex = reading ? clampedSceneIndex : currentSceneIndex;
  $: scenePanelScene = scenes[scenePanelIndex] ?? null;
  $: currentPlateResolution = scenePlaceResolutions[scenePanelIndex] ?? null;
  $: currentPlateMap = plateCoastline && currentPlateResolution?.place.coords
    ? renderSceneMap(
        [currentPlateResolution.place],
        plateCoastline,
        { idPrefix: `scene-map-${work}-${bookNum}-${scenePanelIndex}` },
        currentPlateResolution.route,
      )
    : null;
  $: scenePanelPlaceName = currentPlateResolution?.place.name ?? scenePanelScene?.place ?? 'Place not recorded';
  $: scenePanelCertainty = currentPlateResolution?.place.certainty ?? null;

  // ── DICES speech rails (Phase 4 flagship) ─────────────────────────────────
  // Off by default; a thin speaker rail in the Greek gutter for high-
  // confidence spans (see shared/lib/speeches.ts's classifySpeech) plus a
  // discreet flagged marker for everything degraded (nested/crossBook/gap
  // spans). Data is a computed import (status:"imported", not draft — see
  // docs/APPARATUS-SCHEMAS.md), so it gets a small "DICES" source chip in
  // Settings, not the apparatus-honesty draft badge. Lazy-fetched only once
  // the toggle is switched on (payload discipline: ~700 spans across both
  // epics is not worth shipping to every reader who never opens it).
  const SPEECH_KEY = 'reader-speeches';
  let speechesOn = false;
  function saveSpeeches() { try { localStorage.setItem(SPEECH_KEY, String(speechesOn)); } catch {} }
  let allSpeeches: Speech[] = [];
  let charactersById: Map<string, CharacterEntry> = new Map();
  let speechesLoaded = false;
  let speechStartsRequest: Promise<void> | null = null;
  let charactersLoaded = false;
  // Alignment needs only speech starts. The rails additionally fetch character
  // names, but both consumers share this one work-level speeches request.
  async function ensureSpeechStarts(): Promise<void> {
    if (speechesLoaded) return;
    if (speechStartsRequest) return speechStartsRequest;
    const request = fetchSpeeches(work).then((sp) => {
      allSpeeches = sp;
      speechesLoaded = true;
    }).catch(() => {
      // The data-layer promise cache clears failed requests, so a later mode
      // change can retry without leaving an unhandled rejection behind.
    }).finally(() => {
      speechStartsRequest = null;
    });
    speechStartsRequest = request;
    return request;
  }
  async function ensureSpeeches(): Promise<void> {
    if (charactersLoaded) return;
    try {
      const [, chars] = await Promise.all([ensureSpeechStarts(), fetchCharacters()]);
      charactersById = new Map(Object.entries(chars));
      charactersLoaded = true;
    } catch {
      // Keep usable alignment starts if only the optional display labels fail.
    }
  }
  function toggleSpeeches() { speechesOn = !speechesOn; saveSpeeches(); }
  // Fetch on first toggle-on, and again whenever a book switch (bookNum
  // prop change) happens while already on and the data hasn't loaded yet.
  $: if (mounted && speechesOn && (!speechesLoaded || !charactersLoaded)) ensureSpeeches();
  // Only the phone-stacked Both path and prose Reading Mode call alignGroups.
  // Do not fetch on desktop/single-column Scholar renders that never need a
  // snapped boundary; when either grouping path becomes active, starts arrive
  // through the same cached fetch as the optional rail data.
  $: speechAlignmentNeeded = mounted && (
    (reading && !flowRows) ||
    (phoneWidth && view === 'both' && trans !== 'compare' && epicVerse)
  );
  $: if (speechAlignmentNeeded && !speechesLoaded) ensureSpeechStarts();

  // This book's speeches (any level — classifySpeech needs the whole set to
  // find a level-1's containing level-0 parent) and its real vulgate line
  // set (for the numbering-gap check). These remain gated by the visible toggle.
  $: bookSpeeches = speechesOn ? allSpeeches.filter((s) => s.book === bookNum) : [];
  $: bookRealLines = speechesOn ? realLinesFromSegments(segments) : new Set<number>();
  // Every speech's OPENING line in this book, any nesting level (FIX 1,
  // John's phone report 2026-07-18 — see shared/lib/speech-snap.ts): fed to
  // alignGroups below so the mobile "Both" view snaps a tick 1-2 lines ahead
  // of a speech's own start forward to that start, instead of splitting the
  // speech's opening Greek line into the wrong alignment group. This compact
  // alignment input deliberately remains available when the rail is hidden.
  $: bookSpeechStarts = allSpeeches.filter((s) => s.book === bookNum).map((s) => s.lines[0]);
  $: speechRenders = bookSpeeches.map((s) => ({ speech: s, cls: classifySpeech(s, bookSpeeches, bookRealLines) }));
  // line n -> true for every line covered by a high-confidence span (draws
  // the hairline rail via a CSS class, no per-line listener).
  $: speechRailLines = (() => {
    const m = new Set<number>();
    for (const { speech, cls } of speechRenders) {
      if (cls.mode !== 'rail') continue;
      for (let n = speech.lines[0]; n <= speech.lines[1]; n++) m.add(n);
    }
    return m;
  })();
  // line n -> the small-caps "SPEAKER → ADDRESSEE" label shown at a rail's
  // opening line only.
  $: speechRailStarts = (() => {
    const m = new Map<number, string>();
    for (const { speech, cls } of speechRenders) {
      if (cls.mode === 'rail') m.set(speech.lines[0], speechLabel(speech, charactersById));
    }
    return m;
  })();
  // line n -> the degrade reason, shown as a discreet flagged marker at a
  // degraded span's opening line only.
  $: speechDegradedStarts = (() => {
    const m = new Map<number, string>();
    for (const { speech, cls } of speechRenders) {
      if (cls.mode === 'degraded') m.set(speech.lines[0], cls.reason ?? 'flagged');
    }
    return m;
  })();

  // ── Meter overlay (feature #19) ────────────────────────────────────────────
  // Off by default; a per-line hexameter scansion tag right-aligned in the
  // Greek gutter (see shared/lib/scansion.ts's scansionDisplay for the
  // honesty rules: high-confidence renders plainly, ambiguous is visibly
  // qualified, unresolved shows a quiet placeholder, NEVER a fake pattern).
  // Data is a computed emit (apparatus_scansion.py's clean-room prosody
  // solver, not a vendored library or AI apparatus draft), so no draft badge
  // applies — same posture as the DICES speech data above. Lazy-fetched
  // per BOOK, not whole-work (a whole-work file ran ~1.5MB for the Iliad —
  // too heavy for a reader toggle's lazy fetch, so the pipeline emit is
  // split the same way book-<NN>.json already is); re-fetched on every book
  // switch while the toggle stays on.
  const METER_KEY = 'reader-meter';
  let meterOn = false;
  function saveMeter() { try { localStorage.setItem(METER_KEY, String(meterOn)); } catch {} }
  let bookScansion: Record<string, ScansionEntry> = {};
  // The book number `bookScansion` currently holds (or is being fetched
  // for) — null once a fetch fails, so a later toggle/book-switch retries.
  let meterLoadedFor: number | null = null;
  async function ensureMeter(book: number): Promise<void> {
    if (meterLoadedFor === book) return;
    meterLoadedFor = book; // guard re-entry; reset below if the fetch fails
    try {
      bookScansion = await fetchScansion(work, book);
    } catch {
      if (meterLoadedFor === book) meterLoadedFor = null; // allow a later retry
    }
  }
  function toggleMeter() { meterOn = !meterOn; saveMeter(); }
  // Fetch on first toggle-on, and again whenever a book switch happens while
  // already on and this book's scansion hasn't loaded yet. epicVerse-gated:
  // the toggle only exists for Homer (verse-line) works.
  $: if (mounted && meterOn && epicVerse && meterLoadedFor !== bookNum) ensureMeter(bookNum);
  // line n -> this book's scansion entry, or undefined (a line the pipeline
  // has no scan for — e.g. a vulgate numbering gap). Empty (cheap no-op) while
  // the toggle is off or the fetch hasn't landed yet.
  $: meterEntries = meterOn && meterLoadedFor === bookNum ? bookScansion : ({} as Record<string, ScansionEntry>);

  // ── "Hear this passage" audio (feature #19) ───────────────────────────────
  // Off by default; a play affordance at each recorded chunk's start line
  // (see shared/lib/audio.ts), backed by David Chamberlain's public-domain
  // recitation — hotlinked archive.org MP3s, never vendored (CLAUDE.md's hard
  // rules). Coverage is honest and partial: Iliad 1-24, Odyssey 1-7 only — the
  // Settings row itself is hidden on any book the manifest doesn't cover, so
  // the small corpus-wide manifest (~55KB, same whole-corpus shape as
  // characters.json) is fetched EAGERLY on mount rather than gated behind the
  // toggle: the toggle's own visibility depends on it. The audio bytes
  // themselves are never fetched until a reader actually presses play
  // (<audio preload="none">, src set only on click).
  const AUDIO_KEY = 'reader-audio';
  let audioOn = false;
  function saveAudio() { try { localStorage.setItem(AUDIO_KEY, String(audioOn)); } catch {} }
  function toggleAudio() { audioOn = !audioOn; saveAudio(); }
  let audioManifest: AudioManifest | null = null;
  let audioManifestLoaded = false;
  async function ensureAudioManifest(): Promise<void> {
    if (audioManifestLoaded) return;
    audioManifestLoaded = true; // guard re-entry; reset below if the fetch fails
    try {
      audioManifest = await fetchAudioManifest();
    } catch {
      audioManifestLoaded = false; // allow a later retry
    }
  }
  $: if (mounted && !audioManifestLoaded) ensureAudioManifest();
  $: audioEntry = bookAudio(audioManifest, work, bookNum);
  $: audioAvailable = hasAudio(audioManifest, work, bookNum);
  // line n -> the chunk that starts there, for this book, revision-preferred
  // and gap-honest (see effectiveChunks). Empty while the toggle is off — the
  // reader never even computes this, let alone the affordances, when unused.
  $: audioChunkStarts = (() => {
    const m = new Map<number, AudioChunk>();
    if (!audioOn || !audioEntry) return m;
    for (const c of effectiveChunks(audioEntry)) m.set(c.lines[0], c);
    return m;
  })();
  $: audioCreator = audioManifest?.source.creator ?? 'David Chamberlain';

  // The one shared <audio> element (bound below in the docked player markup):
  // a single playback session at a time, whichever chunk was last pressed.
  let audioEl: HTMLAudioElement | undefined;
  interface NowPlaying { book: number; chunk: AudioChunk; licenseurl: string; item: string; }
  let nowPlaying: NowPlaying | null = null;
  function playChunk(book: number, chunk: AudioChunk, entry: AudioBookEntry) {
    nowPlaying = { book, chunk, licenseurl: entry.licenseurl, item: entry.item };
    tick().then(() => {
      if (!audioEl) return;
      audioEl.src = chunk.url;
      audioEl.play().catch(() => {});
    });
  }
  function closeAudioDock() {
    if (audioEl) { audioEl.pause(); audioEl.removeAttribute('src'); audioEl.load(); }
    nowPlaying = null;
  }
  // Turning the toggle off silently, mid-playback, would leave the dock
  // playing with no way to see what it is anymore — close it instead.
  $: if (!audioOn && nowPlaying) closeAudioDock();

  // ── Scene rail (in-book navigation flyout) ───────────────────────────────
  // A thin left drawer listing this book's scenes (line range · day · place +
  // summary), mirroring the Contents/Settings drawer pattern: the toggle lives
  // in the SSR header (ReaderShell.astro) and speaks to this island via window
  // CustomEvents; the island owns the panel markup, open state, and focus dance.
  // The current-scene highlight tracks the reading position live while the rail
  // is open (a rAF-throttled scroll scan, wired only while open so the closed —
  // common — case costs nothing and the perf/CLS gates hold).
  let sceneRailOpen = false;
  let currentSceneIndex = 0;
  let sceneRailEl: HTMLElement | undefined;
  let sceneRailReturnFocus: HTMLElement | null = null;
  let sceneRaf = 0;
  let sceneTrackingArmed = false;
  let _onToggleScenes: () => void;
  let _onCloseScenes: () => void;

  // The Greek line-id column that owns a given vulgate line (ids are `L{col}-{n}`).
  // Homer books are a single segment (column "1"), but resolve through segments
  // so a multi-segment work still targets the right column.
  function columnForLine(n: number): string {
    for (const seg of segments) {
      const g = seg.greek;
      if (g && g.length && n >= g[0].n && n <= g[g.length - 1].n) return String(seg.column);
    }
    return String(segments[0]?.column ?? '');
  }
  // Detection line just below the sticky chrome (header + controls strip): the
  // reading position is the last anchor at or above it. Same idiom as
  // updateChapterContext.
  function sceneBoundary(): number {
    const ctrl = document.querySelector('.reader-controls')?.getBoundingClientRect().bottom ?? 0;
    return ctrl + 12;
  }
  // Recompute the current scene from the reading position: the lowest on-screen
  // Greek line still above the detection line gives the vulgate line we're
  // reading; activeSceneIndex maps it to a scene. Hidden lines (the Greek column
  // in English-only view) are skipped so they can't pin the highlight to the last
  // line. Scholar view only: Reading Mode has no Greek-line anchors to scan (its
  // single English column pages by scene already) — setReading calls this
  // directly, BEFORE flipping `reading` on, to seed the scene Reading Mode opens
  // to from wherever Scholar was scrolled.
  function computeCurrentScene() {
    if (!scenes.length || reading) return;
    const boundary = sceneBoundary();
    let line: number | null = null;
    for (const el of document.querySelectorAll<HTMLElement>('.greek-line[id]')) {
      if (el.offsetParent === null) continue;
      if (el.getBoundingClientRect().top > boundary) continue;
      const m = el.id.match(/^L.+-(\d+)$/);
      if (m) line = Number(m[1]);
    }
    if (line != null) currentSceneIndex = activeSceneIndex(scenes, line);
  }
  function onSceneScroll() {
    if (sceneRaf) return;
    sceneRaf = requestAnimationFrame(() => { sceneRaf = 0; computeCurrentScene(); });
  }
  function armSceneTracking() {
    if (sceneTrackingArmed) return;
    sceneTrackingArmed = true;
    computeCurrentScene();
    window.addEventListener('scroll', onSceneScroll, { passive: true });
  }
  // The scene rail is the ONE jump list for both postures (no second list):
  // in Reading Mode it PAGES to the scene (gotoScene); in Scholar view it
  // scrolls to the scene's opening Greek line, eagerly setting the highlight
  // so the click feels instant — block:'start' lands the line at the
  // detection boundary (see .greek-line scroll-margin-top) so the live scan
  // agrees with the eager pick once the scroll settles.
  function jumpToScene(i: number) {
    const s = scenes[i];
    if (!s) return;
    if (reading) { gotoScene(i); closeSceneRail(); return; }
    currentSceneIndex = i;
    suppressArmUntil = Date.now() + 900;
    const greek = document.getElementById(`L${columnForLine(s.startLine)}-${s.startLine}`);
    greek?.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
  }

  function sceneItems(): HTMLElement[] {
    return sceneRailEl ? Array.from(sceneRailEl.querySelectorAll<HTMLElement>('.scene-item')) : [];
  }
  function sceneRailFocusables(): HTMLElement[] {
    return sceneRailEl
      ? Array.from(sceneRailEl.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
        )).filter((el) => el.offsetParent !== null)
      : [];
  }
  // Arrow keys rove the scene list; Home/End jump to ends; Tab is trapped inside
  // the open drawer; Escape closes and restores focus to the header toggle.
  function onSceneRailKey(e: KeyboardEvent) {
    if (e.key === 'Escape') { e.preventDefault(); closeSceneRail(); return; }
    if (e.key === 'Tab') {
      const f = sceneRailFocusables();
      if (!f.length) { e.preventDefault(); sceneRailEl?.focus(); return; }
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      return;
    }
    const items = sceneItems();
    if (!items.length) return;
    const i = items.indexOf(document.activeElement as HTMLElement);
    if (e.key === 'ArrowDown') { e.preventDefault(); items[i < 0 ? 0 : Math.min(items.length - 1, i + 1)].focus(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); items[i < 0 ? items.length - 1 : Math.max(0, i - 1)].focus(); }
    else if (e.key === 'Home') { e.preventDefault(); items[0].focus(); }
    else if (e.key === 'End') { e.preventDefault(); items[items.length - 1].focus(); }
  }
  function openSceneRail() {
    if (sceneRailOpen) return;
    sceneRailReturnFocus = document.activeElement as HTMLElement | null;
    sceneRailOpen = true;
    window.dispatchEvent(new CustomEvent('scenes-state', { detail: { open: true } }));
    armSceneTracking();
    tick().then(() => {
      const items = sceneItems();
      (items[currentSceneIndex] ?? items[0]
        ?? sceneRailEl?.querySelector<HTMLElement>('.scene-rail-close'))?.focus();
    });
  }
  function closeSceneRail() {
    if (!sceneRailOpen) return;
    sceneRailOpen = false;
    window.dispatchEvent(new CustomEvent('scenes-state', { detail: { open: false } }));
    if (!chartRoomOpen && !sheetNeedsSceneTracking) {
      window.removeEventListener('scroll', onSceneScroll);
      sceneTrackingArmed = false;
    }
    (sceneRailReturnFocus ?? document.querySelector<HTMLElement>('.scenes-toggle'))?.focus();
    sceneRailReturnFocus = null;
  }
  // Keep the highlighted item visible within the rail as the reading position
  // moves it (scoped to the rail's own scroll container — the drawer is fixed).
  $: if (mounted && sceneRailOpen) {
    const _i = currentSceneIndex;
    tick().then(() => { if (sceneRailOpen) sceneItems()[_i]?.scrollIntoView({ block: 'nearest' }); });
  }
  $: if (mounted && chartRoomOpen && !reading) armSceneTracking();

  // ── Lookup presentation: docked rail (≥1100px) vs anchored popup (<1100px) ──
  // DESIGN.md 2026-07-17: a docked, non-modal lexicon rail on desktop; the
  // anchored WordPopup below it. Recomputed on mount and resize so a viewport
  // crossing 1100px swaps presentation for the next lookup.
  let dockedLexicon = false;
  // Whether the OPEN popup was raised by keyboard (Enter/Space on a token). Drives
  // focus: a keyboard open moves focus into the docked rail and Escape returns it
  // to the token; a mouse open leaves focus in the reading flow.
  let popupViaKb = false;
  function computeDocked() {
    dockedLexicon = typeof window !== 'undefined'
      && window.matchMedia('(min-width: 1100px)').matches;
  }

  // Both view's phone-width alignment-group stacking (see alignGroups above):
  // client-only, mount+resize-computed like dockedLexicon above — the DOM
  // structure genuinely differs (interleaved groups vs. parallel columns, not
  // just a CSS reflow of the same nodes), so this can't be a CSS breakpoint;
  // it has to gate which branch of the template renders. Same <=680px family
  // used everywhere else in the reader for the phone breakpoint.
  let phoneWidth = false;
  function computePhoneWidth() {
    phoneWidth = typeof window !== 'undefined'
      && window.matchMedia('(max-width: 680px)').matches;
  }

  // Print / Save-as-PDF: hand the currently-rendered view to the browser's
  // native print engine. The @media print stylesheet (global.css) strips the
  // app chrome, sets page breaks, and reveals a print-only title. We print the
  // on-screen view as-is, so Both / Greek / English all work via existing CSS.
  function printReader() {
    if (typeof window === 'undefined') return;
    window.print();
  }

  // Print a single chapter by temporarily hiding all seg-rows and chapter heads
  // that don't belong to the selected chapter, then restoring after print.
  function printSingleChapter(ch: string) {
    if (typeof window === 'undefined') return;
    const toRestore: { el: HTMLElement; was: string }[] = [];
    const hide = (el: HTMLElement) => {
      toRestore.push({ el, was: el.style.display });
      el.style.display = 'none';
    };
    document.querySelectorAll<HTMLElement>('.seg-row[data-chapter]').forEach(el => {
      if (el.dataset.chapter !== ch) hide(el);
    });
    document.querySelectorAll<HTMLElement>('.chapter-head').forEach(el => {
      const m = el.id.match(/^ch-\d+-(.+)$/);
      if (!m || m[1] !== ch) hide(el);
    });
    // Hide segments where every row was hidden (so the lone seg-ref doesn't print).
    document.querySelectorAll<HTMLElement>('.segment').forEach(seg => {
      const rows = seg.querySelectorAll<HTMLElement>('.seg-row[data-chapter]');
      if (rows.length > 0 && Array.from(rows).every(r => r.style.display === 'none')) hide(seg);
    });
    window.addEventListener('afterprint', () => {
      toRestore.forEach(({ el, was }) => { el.style.display = was; });
    }, { once: true });
    window.print();
  }

  // Print-menu dropdown state (chapter selector shown when book has > 1 chapter).
  let printMenuOpen = false;
  function togglePrintMenu(e: MouseEvent) {
    e.stopPropagation();
    if (printMenuOpen) { printMenuOpen = false; return; }
    printMenuOpen = true;
    document.addEventListener('click', () => { printMenuOpen = false; }, { once: true });
  }

  // Book label for chapter headings, the live context strip, and print —
  // multi-book works only, using the work's own numbering (Roman for EN).
  $: bookLabel = workMeta && workMeta.books > 1 ? `Book ${workBookLabel(workMeta, bookNum)}` : '';
  $: bekRange = segments.length
    ? (segments.length > 1
        ? `${segments[0].column}–${segments[segments.length - 1].column}`
        : segments[0].column)
    : '';
  // Masthead pieces (critical-edition design): author eyebrow + work title;
  // the full source citation(s) adapted to the printed view live in the footer.
  $: printCite = view === 'greek'
    ? (greekSrc?.full ? `Greek text: ${greekSrc.full}` : '')
    : view === 'english'
      ? (selectedTrans?.name ? `Translation: ${selectedTrans.name}` : '')
      : [greekSrc?.full ? `Greek text: ${greekSrc.full}` : '',
         selectedTrans?.name ? `Translation: ${selectedTrans.name}` : '']
          .filter(Boolean).join('   ·   ');

  // Segments annotated with a running currentChapter so every block — including
  // continuation blocks that don't open a new chapter — knows which chapter it
  // belongs to. Used for per-chapter print filtering via data-chapter attributes.
  $: enrichedSegments = (() => {
    let runCh = '';
    return segments.map(seg => {
      const blocks = splitSegment(seg);
      return {
        seg,
        blocks: blocks.map(b => {
          if (b.chapter) runCh = b.chapter;
          return { ...b, currentChapter: runCh } as EnrichedBlock;
        }),
      };
    });
  })();

  // Ordered list of distinct chapter identifiers present in the loaded book.
  // Empty-string entries (no chapter assignment yet) are filtered out.
  $: chaptersInBook = [...new Set(
    enrichedSegments.flatMap(s => s.blocks.map(b => b.currentChapter)).filter(Boolean)
  )];

  // Whether this book's Greek carries at least one athetized/bracketed line —
  // drives the one-line legend shown once per book view (verse-line works
  // only; no pipeline data sets `bracketed` yet, so this is false everywhere
  // today). Reactive on `segments` so it recomputes after the fetch-fallback
  // path resolves.
  $: hasBracketedLines = epicVerse && segments.some(s => s.greek.some(l => l.bracketed));

  // ── Live URL tracking (aquinas.cc style) ─────────────────────────────────
  // As the reader scrolls, rewrite the location hash to the Bekker citation at
  // the top of the reading area, so any position is a citable link. Line-level
  // when the Greek column is visible (our lineation is canonical Bekker);
  // column-level in English-only view (its line numbers are interpolated
  // estimates). history.replaceState keeps this out of back-history and avoids
  // jumping the scroll. We arm the spy only on the first user scroll so an
  // opened #citation link isn't overwritten before the reader actually moves.
  let spyObserver: IntersectionObserver | null = null;
  let spyState = new Map<Element, number | null>();
  let spyArmed = false;
  let lastCite = '';
  let suppressArmUntil = 0;   // ignore scroll-events from our own programmatic scrolls
  let resizeTimer: ReturnType<typeof setTimeout> | undefined;

  function citeOf(el: Element): string | null {
    // Compose through the work's citation scheme so the hash reads as a real
    // citation: "1094a15" (bekker line), "17a" (stephanus — the line is dropped,
    // never "17a5"). formatCite is byte-identical to the old concatenation for
    // schemes with user-facing lines.
    const lm = el.id.match(/^L(.+)-(\d+)$/);   // greek line: L{col}-{n}
    if (lm) return formatCite(work, lm[1], Number(lm[2]));
    const cm = el.id.match(/^col-(.+)$/);       // segment/tick: col-{column} → {column}
    if (cm) return formatCite(work, cm[1]);
    // English-view row tick of the turn flow (no id — the Greek tick owns
    // col-{token}); the section token rides a data attribute instead.
    const dt = el.getAttribute('data-etick');
    return dt ? formatCite(work, dt) : null;
  }

  function updateHash(cite: string | null) {
    if (!cite || cite === lastCite) return;
    lastCite = cite;
    try { history.replaceState(history.state, '', `#${cite}`); } catch {}
    // Remember the last position per work so the work-switcher can resume here.
    try { localStorage.setItem(`reader-loc-${work}`, cite); } catch {}
  }

  // ── Live book/chapter context in the sticky controls strip ───────────────
  // Chapter heads scroll away with the text (they sit inside segments, so
  // CSS sticky can't carry them across segment boundaries); the strip shows
  // the label of the last chapter head above the reading line instead, so
  // the reader always knows where they are. Sampled on scroll, rAF-throttled.
  let liveChapter = '';
  let ctxRaf = 0;
  function updateChapterContext() {
    const strip = document.querySelector('.reader-controls');
    const boundary = (strip?.getBoundingClientRect().bottom ?? 100) + 12;
    let label = '';
    for (const h of document.querySelectorAll('.chapter-head .chapter-label')) {
      if (h.getBoundingClientRect().top <= boundary) label = h.textContent?.trim() ?? '';
      else break;
    }
    liveChapter = label;
  }
  function onCtxScroll() {
    if (ctxRaf) return;
    ctxRaf = requestAnimationFrame(() => { ctxRaf = 0; updateChapterContext(); });
  }

  function setupScrollSpy() {
    spyObserver?.disconnect();
    spyState = new Map();
    const greekVisible = view === 'greek' || view === 'both';
    // English-only view has no Greek lines to observe: section segments carry
    // ids in the segment layout; in the turn flow the row-level English ticks
    // ([data-etick]) stand in for them.
    const els = Array.from(document.querySelectorAll(
      greekVisible ? '.greek-line[id]' : '.segment[id], [data-etick]'));
    if (!els.length) return;
    const headerH = Math.round(document.querySelector('.page-header')?.getBoundingClientRect().height ?? 60);
    // The reading area starts below the sticky header AND the sticky controls
    // strip pinned beneath it, so the detection band begins at the strip's bottom.
    const ctrlBottom = document.querySelector('.reader-controls')?.getBoundingClientRect().bottom ?? 0;
    const topInset = Math.max(headerH, Math.round(ctrlBottom));
    // Detection band: a strip just below the sticky chrome. The intersecting
    // anchor highest on screen is the line currently at the top of the reading area.
    spyObserver = new IntersectionObserver((entries) => {
      for (const e of entries) spyState.set(e.target, e.isIntersecting ? e.boundingClientRect.top : null);
      let best: Element | null = null;
      let bestTop = Infinity;
      for (const [el, top] of spyState) {
        if (top != null && top < bestTop) { bestTop = top; best = el; }
      }
      if (best) updateHash(citeOf(best));
    }, { rootMargin: `-${topInset + 8}px 0px -82% 0px`, threshold: 0 });
    els.forEach((el) => spyObserver!.observe(el));
  }

  // Arm on the first genuine user scroll. Scroll events from our own
  // programmatic jumps (citation/search) fall inside the suppression window and
  // are ignored, so an opened #citation stays put until the reader moves.
  function onScrollArm() {
    if (Date.now() < suppressArmUntil) return;
    window.removeEventListener('scroll', onScrollArm);
    spyArmed = true;
    setupScrollSpy();
  }

  function onResize() {
    clearTimeout(resizeTimer);
    computeDocked();
    computePhoneWidth();
    computeScenePanelViewport();
    resizeTimer = setTimeout(() => { if (spyArmed) setupScrollSpy(); }, 200);
  }

  // Open at a Bekker citation from the URL hash: the exact Greek line if it's
  // present and visible, otherwise the owning column. Instant (no animation) so
  // it doesn't stream scroll-events, and suppressed so it doesn't self-arm.
  function scrollToCitation(column: string, line: number | null) {
    suppressArmUntil = Date.now() + 800;
    // A null line (a lineless-scheme citation like "17a", or any column-only
    // reference) targets the whole segment; otherwise the exact Greek line if
    // it's present and visible, else its owning column.
    const lineEl = line != null ? document.getElementById(`L${column}-${line}`) : null;
    if (lineEl && (lineEl as HTMLElement).offsetParent !== null) {
      lineEl.scrollIntoView({ behavior: 'auto', block: 'center' });
    } else {
      // col-{column} is the section segment (segment layout) or the section's
      // Greek gutter tick (turn flow). A hidden tick (English-only view hides
      // the Greek cells) falls back to the row-level English tick.
      const colEl = document.getElementById(`col-${column}`);
      const target = colEl && (colEl as HTMLElement).offsetParent !== null
        ? colEl
        : document.querySelector(`[data-etick="${column}"]`) ?? colEl;
      target?.scrollIntoView({ behavior: 'auto', block: 'start' });
    }
  }

  let _onToggleSettings: () => void;
  let _onCloseSettings: () => void;
  // Nav-bar bridge (ReaderShell.astro's server-rendered translation/view/
  // posture/Chart Room controls — John's nav-bar merge brief, 2026-07-24):
  // same window-CustomEvent pattern as toggle-settings/toggle-scenes above.
  let _onSetTrans: (e: Event) => void;
  let _onSetView: (e: Event) => void;
  let _onToggleReading: () => void;
  let _onToggleChartRoomNav: () => void;

  onDestroy(() => {
    spyObserver?.disconnect();
    if (typeof window !== 'undefined') {
      window.removeEventListener('scroll', onScrollArm);
      window.removeEventListener('scroll', onCtxScroll);
      window.removeEventListener('resize', onResize);
      if (_onToggleSettings) window.removeEventListener('toggle-settings', _onToggleSettings);
      if (_onCloseSettings)  window.removeEventListener('close-settings',  _onCloseSettings);
      if (_onToggleScenes) window.removeEventListener('toggle-scenes', _onToggleScenes);
      if (_onCloseScenes)  window.removeEventListener('close-scenes',  _onCloseScenes);
      if (_onSetTrans) window.removeEventListener('set-trans', _onSetTrans);
      if (_onSetView) window.removeEventListener('set-view', _onSetView);
      if (_onToggleReading) window.removeEventListener('toggle-reading', _onToggleReading);
      if (_onToggleChartRoomNav) window.removeEventListener('toggle-chart-room', _onToggleChartRoomNav);
      window.removeEventListener('scroll', onSceneScroll);
      readerBodyEl?.removeEventListener('click', onReaderClick);
      readerBodyEl?.removeEventListener('keydown', onReaderKeydown);
      document.removeEventListener('mouseup', checkCopyBtn);
      document.removeEventListener('selectionchange', onSelectionChange);
    }
  });

  function isHit(surface: string): boolean {
    if (!hlGrkFolds.length) return false;
    const f = greekFold(surface);
    return f.length > 0 && hlGrkFolds.some(q => f.startsWith(q));
  }
  function esc(s: string): string {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function highlightEng(text: string): string {
    // Sidenote [[sN]] and figure [[figN]] markers are rendered elsewhere (the
    // right rail / an inline figure), so strip them from the prose flow.
    text = text.replace(/\s*\[\[(?:s|fig)\d+\]\]\s*/g, ' ');
    if (!hlEngTerms.length) return esc(text);
    return highlightPrefixMatches(text, hlEngTerms);
  }
  // §Phase-3 B5: the printed number is stored as `display`; identity is the
  // (scope, number) pair encoded in the label — continuous scope's label IS
  // the display digits (label === display, zero-change case), while a scoped
  // label ("2.3.1") or a star/dagger glyph carries its display as the
  // trailing component. Pure function of the label alone, so both Reader
  // (button text) and FootnotePopup (popup header) can compute it locally
  // without threading an extra value through the marker string itself.
  function fnDisplay(label: string): string {
    if (label === '*' || label === '†') return label;
    const i = label.lastIndexOf('.');
    return i === -1 ? label : label.slice(i + 1);
  }
  // A footnote-bearing translation (Ostwald's third slot, the Isagoge's Owen,
  // or — Phase 4B — an imported overlay; see fnTransIds above) carries inline
  // `[^label]` footnote references; turn each into a clickable superscript.
  // §B4.2: the label is the full scope-qualified identity (continuous scope:
  // plain digits, unchanged from before); the button only ever displays the
  // printed number. `data-fn-trans` records which translation's footnote map
  // to resolve against (§B4.3/4.4) — needed once more than one translation on
  // the page can carry footnotes. A delegated click handler on the column
  // reads both data attributes and opens the footnote popup.
  function renderThird(text: string, transId: string): string {
    // The marker <button> is an atomic inline box, and engines may take a
    // line-break opportunity at its edge even with no space — WKWebView
    // orphans the superscript onto the next line ("pair, | ¹ one thing").
    // Glue it to the word it annotates with a nowrap wrapper. The capture
    // deliberately stops at whitespace, tag brackets, and entities so it can
    // never swallow a fragment of highlightEng's own markup; if a tag abuts
    // the marker the wrapper just holds the marker alone (no worse than
    // before).
    return highlightEng(text).replace(
      /([^\s<>&]*)\[\^([\w.*†]+)\]/g,
      (_m, lead: string, label: string) => {
        const display = fnDisplay(label);
        return `<span class="fn-anchor">${lead}<button type="button" class="fn-marker" data-fn="${label}" data-fn-trans="${transId}" aria-label="Footnote ${display}">${display}</button></span>`;
      },
    );
  }

  // A segment renders as one or more blocks split at chapter boundaries.
  // `chapter` is non-null on the block that begins a new chapter (heading shown).
  // Every English slot (primary / Ross / third) lays out as flowing prose with
  // its Bekker numbers floated into the margin at their exact offsets (see
  // flowParts). A GreekLine may be a partial slice of a real line (cont = its
  // tail half, after a mid-line chapter split): it suppresses the repeated id.
  type RLine = GreekLine & { cont?: boolean };
  type OTables = SceneFlowChunk['otables'];
  interface Block { chapter: string | null; bekker: string; lines: RLine[]; flow: FlowPart[]; oflows: Record<string, FlowPart[]>; otables: OTables; sidenotes: number[]; figs: number[]; }
  // EnrichedBlock annotates each block with the chapter it belongs to (tracking
  // across segments so continuation blocks know their chapter too).
  interface EnrichedBlock extends Block { currentChapter: string; }
  // A flowing-prose part: either a text run (n null) or a Bekker margin marker
  // (text null) placed at an exact mid-sentence offset — no row break.
  type FlowPart = SceneFlowPart;

  // The char position where token `w` begins in a line's text (0 at the start,
  // text.length at/after the end), so a cut preserves the verbatim
  // punctuation/sigla between words on the correct side.
  function tokenPos(line: GreekLine, w: number): number {
    if (w <= 0) return 0;
    if (w >= line.tokens.length) return line.text.length;
    let ptr = 0;
    for (let i = 0; i < w; i++) {
      const idx = line.text.indexOf(line.tokens[i].t, ptr);
      if (idx >= 0) ptr = idx + line.tokens[i].t.length;
    }
    const cut = line.text.indexOf(line.tokens[w].t, ptr);
    return cut >= 0 ? cut : ptr;
  }

  // The sub-line covering tokens [fromW, toW) — used to split a Greek line at a
  // chapter boundary that falls mid-line (most chapters start mid-line). A
  // partial tail (fromW>0) is marked `cont` so the line number/id isn't repeated.
  function lineSlice(line: GreekLine, fromW: number, toW: number): RLine {
    fromW = Math.max(0, fromW);
    toW = Math.min(line.tokens.length, toW);
    if (fromW === 0 && toW === line.tokens.length) return line;
    let text = line.text.slice(tokenPos(line, fromW), tokenPos(line, toW));
    if (fromW > 0) text = text.replace(/^\s+/, '');
    if (toW < line.tokens.length) text = text.replace(/\s+$/, '');
    return { n: line.n, text, tokens: line.tokens.slice(fromW, toW), cont: fromW > 0 };
  }

  // flowParts (Bekker-margin flowing prose) is now shared/lib/tick-chunks.ts —
  // see the import at the top of this component (Codex review F1, 2026-07-21).

  // A standalone tick span is absolutely positioned with no `top`, so its
  // static position decides which line it reads against — and a marker box
  // sitting BETWEEN two text runs attaches to the END of the previous
  // rendered line whenever the marked word starts a new one. The tick then
  // shows a full rendered line (visually a sentence) too early, at every
  // column width. Merging each tick into the FOLLOWING text run as its first
  // child pins its static position to the first line box of the text it
  // marks. (It also keeps `.para-br + .bk-seg` adjacency intact when a tick
  // lands exactly on a paragraph start.) Ticks with an attached table — or
  // with no following text run — keep the standalone rendering.
  type RenderPart = FlowPart & { tick?: { n: number; real: boolean } };
  function attachTicks(parts: FlowPart[], tableNs: Set<number> = new Set()): RenderPart[] {
    const isText = (p: FlowPart | undefined): p is FlowPart => !!p && p.text !== null && p.text !== '\n';
    const isBreak = (p: FlowPart | undefined): boolean => !!p && (p.text === '\n' || p.para === true);
    const out: RenderPart[] = [];
    for (let i = 0; i < parts.length; i += 1) {
      const part = parts[i];
      const isTick = part.text === null && part.n !== null && !part.para;
      if (isTick && part.n !== null && !tableNs.has(part.n)) {
        const next = parts[i + 1];
        if (isText(next)) {
          out.push({ ...next, tick: { n: part.n, real: part.real } });
          i += 1;
          continue;
        }
        // A tick coinciding with a paragraph boundary marks the paragraph's
        // OPENING word: emit the break first, then the opener carrying the
        // tick (leaving the tick standalone before the <br> re-creates the
        // previous-line attachment this helper exists to prevent).
        if (isBreak(next) && isText(parts[i + 2])) {
          out.push(next);
          out.push({ ...parts[i + 2], tick: { n: part.n, real: part.real } });
          i += 2;
          continue;
        }
      }
      out.push(part);
    }
    return out;
  }

  // Split a line into clickable words, the verbatim text between them, and (for
  // Stephanus dialogues) speaker lead-in labels spliced in at each turn offset.
  // The tokens hold bare words (for the popup lookup); the line `text` keeps the
  // original punctuation AND the OCT editorial sigla ( ) [ ] < > † " — so the
  // gaps render as plain, non-clickable text, preserving the critical edition.
  // The position math lives in shared/lib/speakers.ts (see lineRenderParts):
  // with no speaker events it is byte-identical to the old token/gap split.
  const speakerEvents = (seg: Segment, line: RLine): SpeakerEvent[] =>
    // Speaker offsets are char positions in the FULL line, so they only apply to
    // a whole (non-`cont`) line; stephanus never splits lines (no chapters), but
    // guard anyway so a sliced line can't attach an event at a shifted offset.
    line.cont ? [] : (seg.speakers ?? []).filter((s) => s.line === line.n);

  // Clickable parts for a table cell (same shape as a line: text + tokens;
  // tables carry no speaker turns).
  function cellParts(cell: { text: string; tokens: Token[] }): LineRenderPart[] {
    return lineRenderParts(cell.text, cell.tokens);
  }

  // Turn-flow rows for a dialogue book (the pipeline emitted turnFlow): the
  // whole book renders as one continuous flow of turn rows — each speaker's
  // statement level with its translation, Stephanus sections as gutter ticks
  // (see speakers.ts buildFlowRows). Null for narrated books / non-stephanus
  // works, which render the segment array exactly as before. Reactive because
  // a fetch-mounted reader receives segments + turnFlow after onMount.
  let flowRows: FlowRow[] | null = null;
  $: flowRows =
    stephanus && turnFlow?.turns?.length
      ? buildFlowRows(segments, turnFlow)
      : null;
  // A narrated work's paragraph-anchored flow (Republic, Apology, Charmides,
  // Letters, Lovers): the same flow renderer, but rows are paragraphs (no
  // speaker — the em-dash fallback lead-in is suppressed) with English
  // paragraph breaks (`ep`), optional embedded dialogue (`et`), and optional
  // one-sided sub-speeches (`sub`). See flowRowsView.
  $: paraFlow = turnFlow?.kind === 'para';

  // Redundant-label suppression. When a single speaker's speech is split into a
  // new row — a section-boundary split whose Greek runs on, or a folded
  // one-sided continuation (`sub`) — the pipeline re-emits the speaker name, so
  // the reader would print e.g. "Soc." twice in a row for an unbroken speech
  // (Meno 70b→c). Print convention drops the name when the same speaker
  // continues: walk the rows in render order tracking who holds the floor, and
  // flag a lead-in / sub label as redundant when it repeats the current
  // speaker's same printed label (see labelSuppression in shared/lib/speakers).
  // Dialogue flows only — narrated `et` blocks carry no canonical speaker.
  $: rowMeta = paraFlow || !flowRows ? [] : labelSuppression(flowRows);

  // English turn blocks for a narrated work's said-bearing chunk (no turnFlow):
  // each turn is its own paragraph block with its lead-in — how print editions
  // set unaligned speeches — never an inline splice, so a label can't glue to
  // the previous sentence (speakers.ts buildEnglishTurnBlocks, pure + tested).
  function englishTurnBlocks(seg: Segment): EnglishTurnBlock[] {
    return buildEnglishTurnBlocks(seg.english?.text ?? '', seg.english?.turns ?? []);
  }
  // Embedded-dialogue blocks for a paragraph-flow row carrying `et` (english.turns
  // nested inside a narrated paragraph). buildEnglishTurnBlocks gives the speaker
  // structure; we re-anchor each trimmed block inside the row's English (indexOf
  // from a moving pointer — trim only strips surrounding whitespace, so the block
  // is a genuine substring) so any paragraph breaks (`ep`) fall in the right block
  // as block-local offsets. Lets ep + et coexist without dropping either.
  type EtBlock = EnglishTurnBlock & { ep: number[] };
  function etBlocks(
    english: string,
    et: { o: number; s: string | null; d: string | null }[],
    ep: number[] | null | undefined,
  ): EtBlock[] {
    const blocks = buildEnglishTurnBlocks(
      english,
      et.map((e) => ({ offset: e.o, speaker: e.s, display: e.d })),
    );
    let ptr = 0;
    return blocks.map((b) => {
      const found = b.text ? english.indexOf(b.text, ptr) : -1;
      const rawStart = found < 0 ? ptr : found;
      ptr = rawStart + b.text.length;
      const bep = (ep ?? [])
        .map((o) => o - rawStart)
        .filter((o) => o > 0 && o < b.text.length);
      return { ...b, ep: bep };
    });
  }
  const isUnpairedDialogue = (seg: Segment): boolean =>
    stephanus && !!seg.english?.turns?.length;
  // Group a block's Greek lines into render items: runs of table rows (lines
  // carrying `cells`, e.g. the De Int 22a modal square) become one table; other
  // lines render individually.
  type GreekItem = { table: false; line: RLine } | { table: true; rows: RLine[] };
  function greekItems(lines: RLine[]): GreekItem[] {
    const items: GreekItem[] = [];
    let run: RLine[] = [];
    for (const l of lines) {
      if (l.cells && l.cells.length) { run.push(l); continue; }
      if (run.length) { items.push({ table: true, rows: run }); run = []; }
      items.push({ table: false, line: l });
    }
    if (run.length) items.push({ table: true, rows: run });
    return items;
  }

  function splitSegment(seg: Segment): Block[] {
    const greek = seg.greek;
    const text = seg.english?.text ?? '';
    const allTicks = seg.english?.bekker ?? [];
    const allParas = (seg.english?.markers ?? [])
      .filter(m => m.kind === 'paragraph')
      .map(m => m.offset);
    // The primary English slice [a, b) as flowing prose: its Bekker ticks
    // (rebased into the slice) are floated into the margin at their EXACT char
    // offsets — no sentence-snapping, no row break — so a mid-sentence Bekker
    // number renders where it actually falls instead of jumping to the next
    // sentence start (which the older snapped-row gutter did). The secondary
    // Ross slot uses the same flow model.
    const flowFor = (a: number, b: number): FlowPart[] => {
      const slice = text.slice(a, b);
      const ticks = allTicks
        .filter(t => t.offset >= a && t.offset < b)
        .map(t => ({ n: t.n, real: t.real, off: t.offset - a }))
        .sort((x, y) => x.off - y.off);
      const paras = allParas
        .filter(off => off > a && off < b)
        .map(off => off - a);
      return flowParts(slice, ticks, paras);
    };
    // Sidenote numbers ([[sN]] markers) falling in the primary English slice
    // [a, b) — the reader floats these into the right rail (busse works).
    const sidesIn = (a: number, b: number): number[] =>
      [...text.slice(a, b).matchAll(/\[\[s(\d+)\]\]/g)].map(m => Number(m[1]));
    // Diagram numbers ([[figN]] markers) in the slice — rendered inline as figures.
    const figsIn = (a: number, b: number): number[] =>
      [...text.slice(a, b).matchAll(/\[\[fig(\d+)\]\]/g)].map(m => Number(m[1]));
    // Overlay slices for each secondary translation, paired to blocks: the
    // continuation slice (a chapter begun in an earlier column) and one per
    // chapter that starts here. Each lays out as flowing prose with its Bekker
    // numbers floated into the margin at exact offsets. Keyed by translation id
    // so any number of overlays render (the 'third'/footnote-bearing one also
    // carries diagram tables).
    const secPieces = secondaries.map((t) => ({ t, pieces: piecesFor(seg, t) }));
    const flowOf = (p: RossPiece | undefined): FlowPart[] =>
      (!p || !p.text) ? [] : flowParts(p.text, (p.bekker ?? []).map(t => ({ n: t.n, real: t.real, off: t.offset })));
    const pieceCont = (pieces: RossPiece[]) => pieces.find(p => p.cont) ?? pieces[0];
    const pieceFor = (pieces: RossPiece[], chapter: string | null) =>
      pieces.find(p => !p.cont && p.chapter === chapter);
    // {transId: flow} + {transId: tables} for a block, picking each overlay's
    // continuation slice or the slice for `chapter` (null → continuation).
    const overlaysFor = (chapter: string | null): { oflows: Record<string, FlowPart[]>; otables: Record<string, { n: number; rows: string[][] }[]> } => {
      const oflows: Record<string, FlowPart[]> = {};
      const otables: Record<string, { n: number; rows: string[][] }[]> = {};
      for (const { t, pieces } of secPieces) {
        const p = chapter === null ? pieceCont(pieces) : pieceFor(pieces, chapter);
        oflows[t.id] = flowOf(p);
        if (p?.tables?.length) otables[t.id] = p.tables;
      }
      return { oflows, otables };
    };

    const starts = (seg.chapterStarts ?? []).slice()
      .sort((a, b) => a.beforeLine - b.beforeLine || (a.wordIndex || 0) - (b.wordIndex || 0));
    if (!starts.length) return [{ chapter: null, bekker: '', lines: greek, flow: flowFor(0, text.length), sidenotes: sidesIn(0, text.length), figs: figsIn(0, text.length), ...overlaysFor(null) }];

    const lineIdx = (beforeLine: number) => {
      const i = greek.findIndex(l => l.n >= beforeLine);
      return i === -1 ? greek.length : i;
    };
    // Each chapter boundary is a cut at (line index, word index within the line).
    const bounds = starts.map(s => ({
      chapter: s.chapter, bekker: s.bekker, engOffset: s.engOffset,
      idx: lineIdx(s.beforeLine), word: s.wordIndex || 0,
    }));

    // The Greek lines spanning a block from cut (idxA,wA) to cut (idxB,wB),
    // splitting the boundary lines mid-line where wA/wB > 0.
    const linesFor = (idxA: number, wA: number, idxB: number, wB: number): RLine[] => {
      if (idxA >= greek.length) return [];
      if (idxA === idxB) {                       // block lies within one line
        const sl = lineSlice(greek[idxA], wA, wB);
        return sl.tokens.length || sl.text.trim() ? [sl] : [];
      }
      const res: RLine[] = [];
      for (let i = idxA; i < idxB && i < greek.length; i++) {
        res.push(i === idxA && wA > 0 ? lineSlice(greek[i], wA, greek[i].tokens.length) : greek[i]);
      }
      if (wB > 0 && idxB < greek.length) res.push(lineSlice(greek[idxB], 0, wB));
      return res;
    };

    const blocks: Block[] = [];
    const first = bounds[0];
    // Lines/English before the first chapter start continue the previous chapter.
    if (first.idx > 0 || first.word > 0 || starts[0].engOffset > 0) {
      blocks.push({
        chapter: null, bekker: '',
        lines: linesFor(0, 0, first.idx, first.word),
        flow: flowFor(0, starts[0].engOffset), sidenotes: sidesIn(0, starts[0].engOffset), figs: figsIn(0, starts[0].engOffset), ...overlaysFor(null),
      });
    }
    for (let i = 0; i < bounds.length; i++) {
      const b = bounds[i];
      const next = bounds[i + 1];
      const engTo = next ? next.engOffset : text.length;
      blocks.push({
        chapter: b.chapter, bekker: b.bekker,
        lines: linesFor(b.idx, b.word, next ? next.idx : greek.length, next ? next.word : 0),
        flow: flowFor(b.engOffset, engTo), sidenotes: sidesIn(b.engOffset, engTo), figs: figsIn(b.engOffset, engTo), ...overlaysFor(b.chapter),
      });
    }
    return blocks;
  }

  // ── Both view on a phone: stack per ALIGNMENT GROUP, not per verse ─────────
  // John's ruling (2026-07-18): the parallel Greek/English columns are
  // unusable at phone width (Greek wraps to 1–2 words/line); the fix is to
  // interleave Greek and English on narrow screens instead of squeezing two
  // columns. HONESTY CONSTRAINT: Murray's English is aligned to the Greek per
  // ~5-line milestone tick (`seg.english.bekker`), NOT per verse — there is no
  // real per-line English pairing to display. So the stacking unit here is the
  // ALIGNMENT GROUP: a run of Greek verse lines followed by the English chunk
  // aligned to that same tick span — never a fabricated per-verse split.
  // groupFlowByTicks / alignGroups (with isTickPart, TickFlowPart, AlignGroup)
  // are now shared/lib/tick-chunks.ts — imported at the top of this component
  // (Codex review F1, 2026-07-21) so the scene-paging audit/tests measure the
  // SAME tick geometry this component renders. Both call sites below pass
  // `block.lines` and the flow EXPLICITLY (alignGroups no longer defaults its
  // flow to block.flow) so Svelte's reactivity tracks each call's own deps.

  // Active popup state
  let popup: { token: Token; anchor: { x: number; y: number } } | null = null;
  // Active footnote popup (footnote-bearing translations' `[^label]`
  // markers). Opens on hover, with a short close-delay so the cursor can
  // travel from the marker into the popup without it vanishing; click/Enter
  // also open it (touch + keyboard). §B4.3: carries `transId` (from the
  // marker's `data-fn-trans`) alongside the label, so FootnotePopup knows
  // WHICH translation's footnote map to resolve `n` against.
  let footnote: { n: string; transId: string; anchor: { x: number; y: number } } | null = null;
  // A click PINS the popup open (it stays until you dismiss it); hover opens it
  // transiently with a short close delay. Pinning makes click-to-read reliable.
  let fnPinned = false;
  let fnCloseTimer: ReturnType<typeof setTimeout> | null = null;
  function cancelFnClose() {
    if (fnCloseTimer) { clearTimeout(fnCloseTimer); fnCloseTimer = null; }
  }
  function scheduleFnClose() {
    if (fnPinned) return;            // a clicked (pinned) note ignores hover-out
    cancelFnClose();
    fnCloseTimer = setTimeout(() => { footnote = null; fnCloseTimer = null; }, 180);
  }
  function showFootnote(marker: Element, pin = false) {
    cancelFnClose();
    if (pin) fnPinned = true;
    const n = marker.getAttribute('data-fn') ?? '';
    const transId = marker.getAttribute('data-fn-trans') ?? '';
    if (footnote?.n === n && footnote?.transId === transId) return;
    const r = marker.getBoundingClientRect();
    footnote = { n, transId, anchor: { x: r.left, y: r.bottom } };
  }
  function onFootnoteOver(e: MouseEvent) {
    const marker = (e.target as HTMLElement | null)?.closest?.('.fn-marker');
    if (marker) showFootnote(marker);
  }
  function onFootnoteOut(e: MouseEvent) {
    if ((e.target as HTMLElement | null)?.closest?.('.fn-marker')) scheduleFnClose();
  }
  function onFootnoteFocus(e: FocusEvent) {
    const marker = (e.target as HTMLElement | null)?.closest?.('.fn-marker');
    if (marker) showFootnote(marker);
  }
  function onFootnoteBlur(e: FocusEvent) {
    if ((e.target as HTMLElement | null)?.closest?.('.fn-marker')) scheduleFnClose();
  }
  function onFootnoteClick(e: MouseEvent | KeyboardEvent) {
    const marker = (e.target as HTMLElement | null)?.closest?.('.fn-marker');
    if (!marker) return;
    if (e instanceof KeyboardEvent && e.key !== 'Enter' && e.key !== ' ') return;
    e.preventDefault();
    e.stopPropagation();
    showFootnote(marker, true);
  }
  function closeFootnote() { cancelFnClose(); fnPinned = false; footnote = null; }
  // Click anywhere outside the marker/popup dismisses a pinned note; same
  // for the Bekker-numbers info popover.
  function onDocPointerDown(e: MouseEvent) {
    const t = e.target as HTMLElement | null;
    if (bekkerInfoOpen && !t?.closest?.('.bekker-info')) bekkerInfoOpen = false;
    if (!fnPinned) return;
    if (t?.closest?.('.fn-marker') || t?.closest?.('.footnote-popup')) return;
    closeFootnote();
  }

  onMount(async () => {
    reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    // Remember which book of this work was last open, for the work switcher —
    // and stamp the work's recency so hosts can offer "continue reading".
    try { localStorage.setItem(`reader-book-${work}`, String(bookNum)); } catch {}
    touchRecent(work);

    // Pre-hydration nav-bar intent (3rd Codex adversarial review restructure,
    // 2026-07-25): a click on the translation/view/posture controls BEFORE
    // this island mounted records the ACTUAL VALUE chosen in
    // window.__navPrehydrated (see ReaderShell.astro's P1 comment) — read
    // once here, applied at a single choke point after all the URL/
    // localStorage restoration logic below (search "choke point"), not by
    // guarding every read site (three earlier rounds each found a fresh
    // snap-back from exactly that scattered-guard shape).
    const navPrehydrated = (typeof window !== 'undefined'
      && (window as unknown as { __navPrehydrated?: { view?: View; trans?: string; reading?: boolean } }).__navPrehydrated) || {};

    // Restore font-size / line-height prefs.
    const savedFs = (() => { try { return localStorage.getItem(FS_KEY); } catch { return null; } })();
    if (savedFs) { const v = parseFloat(savedFs); if (!isNaN(v)) fsScale = v; }
    const savedLh = (() => { try { return localStorage.getItem(LH_KEY); } catch { return null; } })();
    if (savedLh) { const v = parseFloat(savedLh); if (!isNaN(v)) lhScale = v; }
    const savedColw = (() => { try { return localStorage.getItem(COLW_KEY); } catch { return null; } })();
    if (savedColw) { const v = parseFloat(savedColw); if (!isNaN(v)) colScale = v; }
    const savedCite = (() => { try { return localStorage.getItem(CITE_KEY); } catch { return null; } })();
    if (savedCite !== null) citeCopy = savedCite === 'true';
    const savedSpk = (() => { try { return localStorage.getItem(SPK_KEY); } catch { return null; } })();
    if (savedSpk !== null) spkColor = savedSpk === 'true';
    const savedSpeeches = (() => { try { return localStorage.getItem(SPEECH_KEY); } catch { return null; } })();
    if (savedSpeeches !== null) speechesOn = savedSpeeches === 'true';
    const savedMeter = (() => { try { return localStorage.getItem(METER_KEY); } catch { return null; } })();
    if (savedMeter !== null) meterOn = savedMeter === 'true';
    const savedAudio = (() => { try { return localStorage.getItem(AUDIO_KEY); } catch { return null; } })();
    if (savedAudio !== null) audioOn = savedAudio === 'true';
    const savedChartRoom = (() => { try { return localStorage.getItem(CHART_ROOM_KEY); } catch { return null; } })();
    if (savedChartRoom !== null) chartRoomOpen = savedChartRoom === 'true';
    // Restore the reading/scholar posture (global, like reader-view).
    const savedPosture = (() => { try { return localStorage.getItem(POSTURE_KEY); } catch { return null; } })();
    if (savedPosture === 'reading') reading = true;
    // Pick the lookup presentation for this viewport (recomputed on resize below).
    computeDocked();
    computePhoneWidth();
    computeScenePanelViewport();

    // Settings sidebar events (dispatched by ReaderShell.astro and Escape handler).
    _onToggleSettings = () => { settingsOpen ? closeSettings() : openSettings(); };
    _onCloseSettings  = () => { if (settingsOpen) closeSettings(); };
    window.addEventListener('toggle-settings', _onToggleSettings);
    window.addEventListener('close-settings',  _onCloseSettings);
    // Scene rail events (dispatched by ReaderShell.astro's .scenes-toggle + Esc).
    _onToggleScenes = () => { sceneRailOpen ? closeSceneRail() : openSceneRail(); };
    _onCloseScenes  = () => { if (sceneRailOpen) closeSceneRail(); };
    window.addEventListener('toggle-scenes', _onToggleScenes);
    window.addEventListener('close-scenes',  _onCloseScenes);
    // Nav-bar bridge events (ReaderShell.astro's server-rendered translation/
    // view/posture/Chart Room controls in .nav-panel — same dispatch pattern
    // as toggle-settings/toggle-scenes above). The matching *-state broadcasts
    // (trans-state/view-state/reading-state/chart-room-state) are reactive
    // statements further down, gated on `mounted` so they also fire once
    // restoration (localStorage/URL) has settled, syncing the server-rendered
    // controls' initial visual state.
    _onSetTrans = (e: Event) => setTrans((e as CustomEvent<{ id: string }>).detail.id);
    _onSetView = (e: Event) => { void setView((e as CustomEvent<{ view: View }>).detail.view); };
    _onToggleReading = () => toggleReading();
    _onToggleChartRoomNav = () => toggleChartRoom();
    window.addEventListener('set-trans', _onSetTrans);
    window.addEventListener('set-view', _onSetView);
    window.addEventListener('toggle-reading', _onToggleReading);
    window.addEventListener('toggle-chart-room', _onToggleChartRoomNav);
    // Delegated token interaction: one click + one keydown for the whole book,
    // instead of a listener pair on each of ~7000 token spans (see greekToks).
    readerBodyEl?.addEventListener('click', onReaderClick);
    readerBodyEl?.addEventListener('keydown', onReaderKeydown);
    const params = new URLSearchParams(window.location.search);
    hlGrkFolds = (params.get('hlg') ?? '').trim().split(/\s+/).filter(Boolean)
      .map(t => greekFold(t.replace(/\*/g, ''))).filter(Boolean);
    hlEngTerms = (params.get('hle') ?? '').trim().split(/\s+/).filter(Boolean);
    const loc = params.get('loc');
    let locCol = '';
    let locLine: number | null = null;
    if (loc) {
      // Parse through the work's citation scheme, so a column-only value ("17a")
      // yields line === null and targets the segment — never the malformed
      // "L17a-undefined" the old unconditional split-on-':' produced.
      const parsed = parseLocation(work, loc);
      if (parsed) {
        locCol = parsed.column;
        locLine = parsed.line;
        targetId = locLine != null ? `L${locCol}-${locLine}` : `col-${locCol}`;
      }
    }
    // Restore saved view, but a jump-in (loc/highlight) forces bilingual so the
    // target Greek line is on screen. UNTOUCHED by the navPrehydrated fix
    // below (2026-07-25 restructure) — a pre-hydration click is applied at a
    // single choke point AFTER all of this, not by guarding every read site.
    if (loc || hlGrkFolds.length) {
      view = 'both';
    } else {
      const saved = (() => { try { return localStorage.getItem('reader-view'); } catch { return null; } })();
      if (saved === 'greek' || saved === 'english' || saved === 'both') view = saved;
      // No saved choice: a phone defaults to English only (the bilingual columns
      // are cramped on a narrow screen); desktop stays bilingual. The toggle —
      // and any saved choice — overrides this on either.
      else if (window.matchMedia('(max-width: 680px)').matches) view = 'english';
    }
    const validTrans = new Set([...translations.map(t => t.id), ...(canCompare ? ['compare'] : [])]);
    const savedTrans = (() => { try { return localStorage.getItem(TRANS_KEY); } catch { return null; } })();
    if (savedTrans && validTrans.has(savedTrans)) trans = savedTrans;
    // A restored single choice is also the one "leave compare" returns to.
    if (trans !== 'compare') lastSingle = trans;
    // Restore the chosen compare pair (set in the settings sidebar).
    const transIds = new Set(translations.map(t => t.id));
    const savedL = (() => { try { return localStorage.getItem(CMPL_KEY); } catch { return null; } })();
    const savedR = (() => { try { return localStorage.getItem(CMPR_KEY); } catch { return null; } })();
    if (savedL && transIds.has(savedL)) compareLeft = savedL;
    if (savedR && transIds.has(savedR)) compareRight = savedR;
    // A stale/duplicate persisted pair (or a one-translation default colliding)
    // must not yield two identical columns.
    if (compareLeft === compareRight) compareRight = otherTrans(compareLeft);
    // The home index links can preselect a view/translation via query params.
    // UNTOUCHED by the navPrehydrated fix (see the choke point after qMode
    // below) — this whole block, side effects included, runs exactly as it
    // did before nav-bar clicks existed.
    const qView = params.get('view');
    if (qView === 'greek' || qView === 'both' || qView === 'english') view = qView;
    const qTrans = params.get('trans');
    if (qTrans && validTrans.has(qTrans)) {
      if (!fullLoaded && qTrans !== engSlot?.id) {
        // The stripped SSR prop has only the primary translation. Leave that
        // current single-column render in place until the URL-selected payload
        // resolves, instead of briefly rendering absent overlay flows.
        deferredQueryTrans = qTrans;
        if (trans === 'compare' || trans !== engSlot?.id) trans = engSlot?.id ?? translations[0]?.id ?? trans;
      } else {
        trans = qTrans;
        if (qTrans !== 'compare') lastSingle = qTrans;
      }
      if (view === 'greek') view = 'both';
    }
    // All translation/compare restoration is settled: arm the lazy full-book
    // reactive so a restored NON-default translation pulls the full book in (the
    // default English view keeps rendering from the token-stripped prop).
    mounted = true;
    // The pre-paint view bridge (ReaderShell's data-rview) has served its purpose
    // now that Svelte's `view` state (and its view-* class) is authoritative;
    // drop it so a later manual toggle back to Both isn't overridden by the
    // bridge's single-language CSS. The class Svelte will render matches what the
    // bridge painted, so removing it here causes no layout shift.
    document.documentElement.removeAttribute('data-rview');
    // Same for the posture half of the bridge (P2 fix, adversarial review,
    // 2026-07-25): ReaderShell's head script and its posture-sync script
    // painted the correct Scholar/Reading state — Chart Room and the view
    // toggle included — from data-rposture before this component ever ran;
    // now that `reading`'s own reactive broadcast (further down) is
    // authoritative, drop the attribute so a later manual posture toggle
    // isn't shadowed by the bridge's CSS (`:root[data-rposture="reading"]
    // .nav-chart-room`/`.nav-view-toggle`, global.css).
    document.documentElement.removeAttribute('data-rposture');
    // A shareable ?mode=reading|scholar overrides the saved posture (matches the
    // read-on-load convention of ?view / ?trans; posture is not written back).
    // UNTOUCHED by the navPrehydrated fix — see the choke point right below.
    const qMode = params.get('mode');
    if (qMode === 'reading') reading = true;
    else if (qMode === 'scholar') reading = false;

    // ── Pre-hydration intent choke point (required restructure, 2026-07-25,
    //    after three rounds each found a fresh snap-back from a guard
    //    scattered at one URL-reading site) ─────────────────────────────────
    // Everything above — localStorage restore, then ?view=/?trans=/?mode=/
    // loc/hlg, side effects (the qTrans block's "force view back to both")
    // included — runs EXACTLY as it did before the nav bar's controls
    // existed; a no-interaction load is byte-identical. A click on those
    // controls before this island mounted recorded the ACTUAL VALUE the user
    // chose in window.__navPrehydrated (see ReaderShell.astro's P1 comment),
    // not merely "something happened" — this single choke point applies it
    // OVER whatever the logic above computed, last, so "the URL seeds the
    // initial state, an explicit user action overrides it" is true by
    // construction rather than by remembering a guard at every read site.
    // Order matters: trans (with its own view side effect, mirrored from the
    // qTrans branch above) first, then view — so it always wins regardless
    // of what the trans branch just did to it — then reading.
    if (navPrehydrated.trans && validTrans.has(navPrehydrated.trans)) {
      if (!fullLoaded && navPrehydrated.trans !== engSlot?.id) {
        // Same "don't flash absent overlay content" deferral qTrans uses.
        deferredQueryTrans = navPrehydrated.trans;
        if (trans === 'compare' || trans !== engSlot?.id) trans = engSlot?.id ?? translations[0]?.id ?? trans;
      } else {
        trans = navPrehydrated.trans;
        if (navPrehydrated.trans !== 'compare') lastSingle = navPrehydrated.trans;
      }
    }
    if (navPrehydrated.view) view = navPrehydrated.view;
    if (navPrehydrated.reading !== undefined) reading = navPrehydrated.reading;
    // Reading Mode's initial scene: an explicit ?scene=N (1-based, written by
    // saveSceneParam) wins; otherwise, opening directly in Reading Mode via a
    // ?loc= deep link lands on the scene CONTAINING that line (activeSceneIndex);
    // otherwise scene 0. Idempotent and re-run once scenes load in the
    // fetch-fallback path below, so a client-only mount (no SSR bookData) still
    // resolves correctly once its fetch completes.
    const qScene = params.get('scene');
    const resolveSceneIndex = () => {
      if (!scenes.length) return;
      if (qScene) {
        const n = parseInt(qScene, 10);
        if (Number.isFinite(n)) { readingSceneIndex = Math.max(0, Math.min(n - 1, scenes.length - 1)); return; }
      }
      if (reading && locLine != null) readingSceneIndex = activeSceneIndex(scenes, locLine);
    };
    resolveSceneIndex();
    try {
      // Already seeded from the build-time prop in the normal (SSR) path; only
      // fetch when the reader was mounted without it.
      if (!bookData) {
        const data = await fetchBook(work, bookNum);
        segments = data.segments;
        turnFlow = data.turnFlow ?? null;
        scenes = data.scenes ?? [];
        scenesDraft = (data as RawBookData).apparatus?.draft === true;
        resolveSceneIndex();
      }
    } catch (e) {
      error = String(e);
    } finally {
      loading = false;
      // After Svelte renders, scroll to the jumped-to line (loc), a Bekker
      // citation in the hash, or a plain element-id hash.
      const hash = window.location.hash.slice(1);
      setTimeout(() => {
        if (targetId) {
          let el = document.getElementById(targetId);
          // Snap to the nearest existing line in the column if the exact
          // citation line isn't a Greek line break (e.g. mid-line citations).
          // Queried by line-id prefix, not by segment nesting, so it works in
          // both the section-segment layout and the turn flow (where a
          // section's lines aren't nested under its col-{token} tick).
          if (!el && locCol && locLine != null) {
            let best: Element | null = null;
            let bestDist = Infinity;
            document.querySelectorAll(`.greek-line[id^="L${CSS.escape(locCol)}-"]`).forEach((node) => {
              const m = node.id.match(/-(\d+)$/);
              if (!m) return;
              const d = Math.abs(Number(m[1]) - locLine);
              if (d < bestDist) { bestDist = d; best = node; }
            });
            if (best) { el = best as HTMLElement; targetId = (best as HTMLElement).id; }
          }
          // Instant, like the hash-citation path below: a smooth animation
          // started during client:idle hydration can be delayed/interrupted by
          // layout churn (viewport resize, reactive re-renders settling) and
          // strand the reader before it reaches the target. Reduced-motion
          // users need instant regardless, so there's no behavior split here.
          if (el) { suppressArmUntil = Date.now() + 1500; el.scrollIntoView({ behavior: 'auto', block: 'center' }); }
        } else if (hash) {
          const ref = parseBekker(hash);
          if (ref) {
            scrollToCitation(ref.column, ref.line);
            lastCite = `${ref.column}${ref.line}`;
            // Tint the cited line so a shared link makes the passage obvious.
            targetId = `L${ref.column}-${ref.line}`;
          } else {
            // Column-level citations (the scroll-spy writes bare "#1107a" when
            // the Greek column is hidden) target the segment element col-<col>.
            // Instant, like scrollToCitation: a smooth animation started during
            // hydration gets canceled by layout churn and strands the reader at
            // the top.
            let el = document.getElementById(hash) ?? document.getElementById(`col-${hash}`);
            // A hidden target (the turn flow's Greek gutter tick in
            // English-only view) falls back to the row-level English tick.
            if (el && (el as HTMLElement).offsetParent === null) {
              el = (document.querySelector(`[data-etick="${CSS.escape(hash)}"]`) as HTMLElement) ?? el;
            }
            if (el) {
              suppressArmUntil = Date.now() + 1500;
              el.scrollIntoView({ behavior: 'auto', block: 'start' });
            }
          }
        }
        // Begin live URL tracking once the reader actually scrolls (programmatic
        // jumps above are suppressed), so an opened #citation isn't overwritten.
        window.addEventListener('scroll', onScrollArm, { passive: true });
        window.addEventListener('scroll', onCtxScroll, { passive: true });
        window.addEventListener('resize', onResize);
        document.addEventListener('mouseup', checkCopyBtn);
        document.addEventListener('selectionchange', onSelectionChange);
        updateChapterContext();
        // Paint search-hit tokens once the mount-time view/trans state settled
        // (a ?hlg deep-link set hlGrkFolds above; tokens carry no reactive
        // class:hit, so apply it here — a no-op when there are no folds).
        refreshTokenDecorations();
      }, 0);
    }
  });

  // Opening/closing the word sidebar changes the reader body's width (it gains
  // padding-right to clear the panel), which reflows the text and shifts every
  // line vertically — so the passage the reader was looking at jumps. Pin a
  // given element to its current screen position by compensating scroll on each
  // frame for the duration of the width transition. MUST be called BEFORE the
  // `popup` state change so startTop is captured in the pre-reflow layout.
  function pinAcrossReflow(el: HTMLElement | null) {
    if (!el || typeof window === 'undefined') return;
    const startTop = el.getBoundingClientRect().top;
    suppressArmUntil = Date.now() + 500;   // don't let our scrolls arm the spy
    const until = Date.now() + 360;        // padding-right transition is 0.22s
    const step = () => {
      const delta = el.getBoundingClientRect().top - startTop;
      if (Math.abs(delta) >= 0.5) window.scrollBy(0, delta);
      if (Date.now() < until) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  // The line currently at the top of the reading area — the fallback anchor to
  // keep fixed when the sidebar closes after the clicked word has scrolled away.
  function topAnchor(): HTMLElement | null {
    const ctrlBottom = document.querySelector('.reader-controls')?.getBoundingClientRect().bottom ?? 0;
    const inset = ctrlBottom + 8;
    const greekVisible = view === 'greek' || view === 'both';
    const els = document.querySelectorAll<HTMLElement>(
      greekVisible ? '.greek-line[id]' : '.segment[id], .turn-flow .seg-row');
    let best: HTMLElement | null = null, bestDiff = Infinity;
    for (const el of els) {
      const diff = Math.abs(el.getBoundingClientRect().top - inset);
      if (diff < bestDiff) { bestDiff = diff; best = el; }
    }
    return best;
  }

  function inViewport(el: HTMLElement): boolean {
    const r = el.getBoundingClientRect();
    return r.bottom > 0 && r.top < window.innerHeight;
  }

  // The word whose click opened the sidebar — pinned again on close so the
  // passage lands back exactly where it opened (symmetric), unless the reader
  // scrolled it out of view, in which case we keep the current top line fixed.
  let pinnedTok: HTMLElement | null = null;
  // The token span currently wearing the .active ring. Toggled imperatively (the
  // token markup carries no reactive class:active — see the greekToks snippet).
  let activeTokEl: HTMLElement | null = null;

  // Reconstruct a Token from a delegated target's data attributes. The surface
  // form is the span's text; the popup/lexicon only read `t` and `k`, and `o`
  // is preserved for completeness.
  function tokenFromEl(el: HTMLElement): Token {
    return { t: el.textContent ?? '', o: Number(el.dataset.o ?? '0'), k: el.dataset.k ?? '' };
  }

  function activateToken(el: HTMLElement, viaKeyboard = false) {
    const token = tokenFromEl(el);
    if (!token.k) return;
    const rect = el.getBoundingClientRect();
    // Settings and the word-lookup panel are mutually exclusive right-docked
    // panels (see the matching comment in openSettings) — opening a lookup
    // while Settings is open closes Settings first.
    if (settingsOpen) closeSettings();
    // Only the first open reflows the body (adds .word-open); switching words
    // while the sidebar is already open changes nothing about the layout.
    if (!popup) pinAcrossReflow(el);
    // Remember the token so a keyboard-opened docked rail can hand focus back to
    // it on Escape/close, and whether this open was keyboard-driven at all.
    pinnedTok = el;
    popupViaKb = viaKeyboard;
    if (activeTokEl && activeTokEl !== el) activeTokEl.classList.remove('active');
    activeTokEl = el;
    el.classList.add('active');
    popup = { token, anchor: { x: rect.left, y: rect.bottom } };
    // Keyboard activation moves focus INTO the docked rail (WAI-ARIA); a mouse
    // open leaves focus in the reading flow. The modal popup handles its own
    // focus (autofocus is irrelevant there).
    if (dockedLexicon && viaKeyboard) {
      tick().then(() => document.querySelector<HTMLElement>('.word-sidebar.docked')?.focus());
    }
  }

  // Delegated token interaction: one click + one keydown listener on the reader
  // body (wired in onMount) instead of a pair per token. `closest('.tok')`
  // resolves the token span; non-token clicks/keys fall through untouched.
  function onReaderClick(e: MouseEvent) {
    const el = (e.target as Element | null)?.closest?.('.tok') as HTMLElement | null;
    if (!el) return;
    e.stopPropagation();
    activateToken(el, false);
  }
  function onReaderKeydown(e: KeyboardEvent) {
    const el = (e.target as Element | null)?.closest?.('.tok') as HTMLElement | null;
    if (!el) return;
    onTokenKey(e, el);
  }

  function closePopup() {
    // A keyboard-opened docked rail returns focus to the originating token
    // (Escape restores context); the modal popup does its own focus restore.
    const returnTo = dockedLexicon && popupViaKb && pinnedTok && inViewport(pinnedTok) ? pinnedTok : null;
    if (popup) pinAcrossReflow(pinnedTok && inViewport(pinnedTok) ? pinnedTok : topAnchor());
    popup = null;
    if (activeTokEl) { activeTokEl.classList.remove('active'); activeTokEl = null; }
    pinnedTok = null;
    popupViaKb = false;
    returnTo?.focus();
  }

  // ── Keyboard access to Greek tokens ──────────────────────────────────────
  // Analysable tokens are a huge set (thousands per book), so putting every one
  // in the tab order would be hostile to keyboard and screen-reader users.
  // Instead we use a roving tabindex: exactly one token is tabbable; arrow keys
  // move focus token-to-token; Enter/Space opens its analysis. The reader body
  // is the scope so navigation can't wander into chrome.
  let readerBodyEl: HTMLElement | undefined;
  function ensureRovingTab() {
    if (!readerBodyEl) return;
    if (readerBodyEl.querySelector('.tok[tabindex="0"]')) return;
    const first = readerBodyEl.querySelector<HTMLElement>('.tok');
    first?.setAttribute('tabindex', '0');
  }
  // Re-apply the imperative token decorations after any Svelte re-render (which
  // rebuilds token spans and drops the classes we set by hand). ensureRovingTab
  // keeps exactly one token tabbable; the search-hit paint only runs when a
  // ?hlg deep-link actually set folds (the common case is a no-op); the active
  // ring is restored if its element survived the render.
  function refreshTokenDecorations() {
    if (!readerBodyEl) return;
    ensureRovingTab();
    if (hlGrkFolds.length) {
      readerBodyEl.querySelectorAll<HTMLElement>('.tok').forEach(el => {
        if (isHit(el.textContent ?? '')) el.classList.add('hit');
      });
    }
    if (activeTokEl && activeTokEl.isConnected) activeTokEl.classList.add('active');
  }
  afterUpdate(refreshTokenDecorations);

  function onTokenKey(e: KeyboardEvent, cur: HTMLElement) {
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
      e.preventDefault();
      activateToken(cur, true);
      return;
    }
    const step: Record<string, number | 'first' | 'last'> = {
      ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1, Home: 'first', End: 'last',
    };
    if (!(e.key in step)) return;
    e.preventDefault();
    const toks = Array.from(readerBodyEl?.querySelectorAll<HTMLElement>('.tok') ?? []);
    const i = toks.indexOf(cur);
    if (i < 0) return;
    const move = step[e.key];
    const j = move === 'first' ? 0
      : move === 'last' ? toks.length - 1
      : Math.min(toks.length - 1, Math.max(0, i + move));
    if (j === i) return;
    cur.setAttribute('tabindex', '-1');
    toks[j].setAttribute('tabindex', '0');
    toks[j].focus();
  }

  // Show line number only for multiples of 5 (and line 1). Suppressed entirely
  // for non-Bekker works whose synthetic line numbers aren't meaningful.
  function showLineNum(n: number): string {
    if (hideLineNums) return '';
    if (n === 1 || n % 5 === 0) return String(n);
    return '';
  }

  // ── Copy-with-citation helpers ────────────────────────────────────────────
  function nearestGreekLine(node: Node): HTMLElement | null {
    let n: Node | null = node;
    while (n && n !== document.body) {
      if (n instanceof HTMLElement && n.classList.contains('greek-line')) return n;
      n = n.parentNode;
    }
    return null;
  }
  // A Greek-line id → its citation string, composed through the work's scheme:
  // L1094a-3 / L1094a-3-c → "1094a3" (bekker), L17a-5 → "17a" (stephanus — the
  // line is dropped, so a same-section selection cites just the section token).
  function idToCite(id: string): string | null {
    const m = id.match(/^L(.+?)-(\d+)(?:-c)?$/);
    return m ? formatCite(work, m[1], Number(m[2])) : null;
  }

  function greekCiteForRange(range: Range): string | null {
    const startLine = nearestGreekLine(range.startContainer);
    const endLine   = nearestGreekLine(range.endContainer);
    if (!startLine && !endLine) return null;
    const s = startLine ? idToCite(startLine.id) : null;
    const f = endLine   ? idToCite(endLine.id)   : null;
    const abbr = workMeta?.abbr ?? '';
    return (s && f && s !== f) ? `(${abbr} ${s}–${f})` : `(${abbr} ${s ?? f})`;
  }

  function handleCopy(e: ClipboardEvent) {
    if (!citeCopy) return;
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || sel.rangeCount === 0) return;
    const text = sel.toString().trim();
    if (!text) return;
    const range = sel.getRangeAt(0);
    const cite = greekCiteForRange(range);
    if (!cite) return; // English-only selection; wait for alignment
    e.clipboardData?.setData('text/plain', text + '\n' + cite);
    e.preventDefault();
  }

  // ── Floating copy button (appears on Greek text selection) ────────────────
  let copyBtnPos: { x: number; y: number } | null = null;

  function checkCopyBtn() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || sel.rangeCount === 0) { copyBtnPos = null; return; }
    const range = sel.getRangeAt(0);
    if (!nearestGreekLine(range.startContainer) && !nearestGreekLine(range.endContainer)) {
      copyBtnPos = null; return;
    }
    const rect = range.getBoundingClientRect();
    if (!rect.width && !rect.height) { copyBtnPos = null; return; }
    copyBtnPos = { x: rect.right, y: rect.top };
  }

  function onSelectionChange() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) copyBtnPos = null;
  }

  function clickCopyBtn() {
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0) { copyBtnPos = null; return; }
    const text = sel.toString().trim();
    const cite = greekCiteForRange(sel.getRangeAt(0));
    const full = cite ? text + '\n' + cite : text;
    navigator.clipboard.writeText(full).catch(() => {});
    copyBtnPos = null;
  }
</script>

<!-- View toggle and Print control are rendered in the reader header on desktop
     and inside the ⚙ Settings sidebar on mobile (CSS scopes which is visible).
     Top-level snippets keep a single source of markup and one printMenuOpen. -->
{#snippet viewToggle()}
  <div class="view-toggle" role="group" aria-label="Reading view">
    <button class:active={view === 'greek'} aria-pressed={view === 'greek'} on:click={() => setView('greek')}>Greek</button>
    <button class:active={view === 'both'} aria-pressed={view === 'both'} on:click={() => setView('both')}>Both</button>
    <button class:active={view === 'english'} aria-pressed={view === 'english'} on:click={() => setView('english')}>English</button>
  </div>
{/snippet}

{#snippet printControl()}
  {#if chaptersInBook.length > 1}
    <div class="print-menu">
      <button class="print-btn" on:click={togglePrintMenu} title="Print or save as PDF" aria-label="Print or save as PDF">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M6 9V2h12v7" />
          <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
          <rect x="6" y="14" width="12" height="8" />
        </svg>
        <span class="print-btn-label">Print</span>
        <svg class="print-chevron" viewBox="0 0 10 6" width="8" height="5" fill="currentColor" aria-hidden="true"><path d="M0 0l5 6 5-6z"/></svg>
      </button>
      {#if printMenuOpen}
        <div class="print-dropdown">
          <button class="print-dd-item" on:click={() => { printMenuOpen = false; printReader(); }}>Full book</button>
          <div class="print-dd-sep" role="separator"></div>
          {#each chaptersInBook as ch}
            <button class="print-dd-item" on:click={() => { printMenuOpen = false; printSingleChapter(ch); }}>
              {#if bookLabel}{bookLabel}, {/if}Chapter {ch}
            </button>
          {/each}
        </div>
      {/if}
    </div>
  {:else}
    <button class="print-btn" on:click={printReader} title="Print or save as PDF" aria-label="Print or save as PDF">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M6 9V2h12v7" />
        <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
        <rect x="6" y="14" width="12" height="8" />
      </svg>
      <span class="print-btn-label">Print</span>
    </button>
  {/if}
{/snippet}

{#if loading}
  <p style="padding:2rem;font-family:system-ui;color:#888">Loading Book {bookNum}…</p>
{:else if error}
  <p style="padding:2rem;color:red">{error}</p>
{:else}
  <!-- Token markup is deliberately INERT: no per-token event listeners and no
       reactive `class:` bindings. A book is ~7000 tokens; giving each an on:click
       + on:keydown + a class:active effect subscribed to `popup` cost ~1s of
       hydration scripting and blocked the main thread. Instead the container
       (.reader-body) carries ONE delegated click + keydown handler (see onMount),
       resolving the token from data-k/data-o; the active-word ring and search-hit
       highlight are applied imperatively (activateToken / refreshTokenDecorations).
       The keyboard roving-tabindex model is unchanged. -->
  {#snippet greekToks(parts: LineRenderPart[])}{#each parts as part}{#if part.kind === 'token'}<span
        class="tok"
        role="button"
        tabindex="-1"
        aria-label="Analyse {part.text}"
        aria-haspopup="dialog"
        data-k={part.tok.k}
        data-o={part.tok.o}
      >{part.text}</span>{:else if part.kind === 'speaker'}<span class="speaker" class:speaker-dash={part.dash} lang="grc">{part.label}</span>{:else}{part.text}{/if}{/each}{/snippet}
  {#snippet chapterHead(block: Block)}
    <div class="chapter-head" id="ch-{bookNum}-{block.chapter}">
      <span class="chapter-label">{#if bookLabel}<span class="chapter-book">{bookLabel},&nbsp;</span>{/if}Chapter {block.chapter}{#if chapterTitles[block.chapter ?? '']}: {chapterTitles[block.chapter ?? '']}{/if}</span>
      {#if block.bekker && !busse}<span class="chapter-bekker">({block.bekker})</span>{/if}
    </div>
  {/snippet}

  <!-- Greek lines for a run of RLine — factored out of the desktop .greek-col
       loop so the Both-view phone stacking (alignGroups, above) can render
       the SAME per-line markup (tokens, speech rail, audio, meter, brackets)
       for a group's sliced lines, byte-identical to what the full block
       renders. `lines` is `block.lines` on desktop; a group's slice on the
       phone-stacked layout. -->
  {#snippet greekLinesRender(seg: Segment, lines: RLine[])}
    {#each greekItems(lines) as item}
      {#if item.table}
        <!-- Greek inline table (the TLG ⎪ column square, e.g. De Int 22a). -->
        <table class="greek-table"><tbody>
          {#each item.rows as row}
            <tr id={`L${seg.column}-${row.n}`} class:target={targetId === `L${seg.column}-${row.n}`}>
              <td class="line-num">{showLineNum(row.n)}</td>
              {#each (row.cells ?? []) as cell}
                <td class="line-text" lang="grc">{@render greekToks(cellParts(cell))}</td>
              {/each}
            </tr>
          {/each}
        </tbody></table>
      {:else}
        {#if speechesOn && !item.line.cont && speechRailStarts.has(item.line.n)}
          <!-- Speaker→addressee margin label: real text (not
               aria-hidden), CSS small-caps. Sits at the span's
               opening line only — never repeated down the rail. -->
          <p class="spk-rail-label">{speechRailStarts.get(item.line.n)}</p>
        {/if}
        <div class="greek-line" id={item.line.cont ? `L${seg.column}-${item.line.n}-c` : `L${seg.column}-${item.line.n}`} class:target={!item.line.cont && targetId === `L${seg.column}-${item.line.n}`} class:cont={item.line.cont} class:bracketed={!!item.line.bracketed} class:spk-rail={speechesOn && !item.line.cont && speechRailLines.has(item.line.n)} title={item.line.bracketed ? 'athetized/bracketed in the editorial tradition' : undefined}>
          {#if audioOn && !item.line.cont && audioChunkStarts.has(item.line.n)}
            {@const chunk = audioChunkStarts.get(item.line.n)}
            <!-- Play affordance at a recorded chunk's start line only
                 (chunk-level granularity — never a fake per-line
                 seek). Keyboard-focusable real <button>, same
                 gutter-marker idiom as .spk-flag above. -->
            <button
              type="button"
              class="audio-play"
              class:playing={nowPlaying?.chunk.file === chunk?.file}
              on:click={() => { if (chunk && audioEntry) playChunk(bookNum, chunk, audioEntry); }}
              title={chunk ? chunkAriaLabel(chunk, audioCreator) : ''}
              aria-label={chunk ? chunkAriaLabel(chunk, audioCreator) : ''}
            >{nowPlaying?.chunk.file === chunk?.file ? '♪' : '▶'}</button>
          {/if}
          {#if speechesOn && !item.line.cont && speechDegradedStarts.has(item.line.n)}
            <!-- Discreet flagged marker: a degraded span (nested,
                 crossBook, or a vulgate-gap line) gets no rail —
                 just this, at its opening line. -->
            <button type="button" class="spk-flag" title={speechDegradedStarts.get(item.line.n)} aria-label={`Speech flagged: ${speechDegradedStarts.get(item.line.n)}`}>†</button>
          {/if}
          <span class="line-num">{item.line.cont ? '' : showLineNum(item.line.n)}</span>
          <span class="line-text" lang="grc">{#if item.line.bracketed}<span class="line-bracket" aria-hidden="true">[</span>{/if}{@render greekToks(lineRenderParts(item.line.text, item.line.tokens, speakerEvents(seg, item.line)))}{#if item.line.bracketed}<span class="line-bracket" aria-hidden="true">]</span>{/if}</span>
          {#if meterOn && !item.line.cont}
            {@const sc = meterEntries[scansionKey(bookNum, item.line.n)]}
            {#if sc}
              <!-- Supplementary annotation, not primary content: aria-hidden
                   so per-line scansion doesn't interrupt a screen reader's
                   pass through ~700 lines a book — the feature is described
                   once, on the Settings toggle itself (aria-label below).
                   Greek token focus order is untouched (no tabindex here). -->
              {@const sd = scansionDisplay(sc)}
              <span
                class="meter-tag"
                class:meter-ambiguous={sd.tier === 'ambiguous'}
                class:meter-unresolved={sd.tier === 'unresolved'}
                title={sd.title}
                aria-hidden="true"
              >{sd.text}</span>
            {/if}
          {/if}
        </div>
      {/if}
    {/each}
  {/snippet}

  <!-- English flow prose for a run of FlowPart — factored out of transFlow so
       the Both-view phone stacking (alignGroups, above) can render a single
       alignment group's sliced parts through the SAME footnote/table/tick
       markup as the full block, byte-identical to what the full flow
       renders. `parts` is `block.flow`/`block.oflows[id]` on desktop; a
       group's tick-bounded slice on the phone-stacked layout. -->
  {#snippet flowProse(parts: FlowPart[], transId: string, otables: OTables)}
    {#if fnTransIds.has(transId)}
      <div
        class="ross-prose"
        on:mouseover={onFootnoteOver}
        on:mouseout={onFootnoteOut}
        on:focus={onFootnoteFocus}
        on:blur={onFootnoteBlur}
        on:focusin={onFootnoteFocus}
        on:focusout={onFootnoteBlur}
        on:click={onFootnoteClick}
        on:keydown={onFootnoteClick}
        role="presentation"
      >
        {#each attachTicks(parts, new Set((otables[transId] ?? []).map(t => t.n))) as part}
          {#if part.text === '\n'}
            <br class="para-br" />
          {:else if part.text !== null}
            <span class="bk-seg"
              >{#if part.tick}<span class="bk-num" class:approx={!part.tick.real}>{part.tick.n}</span
                >{/if}<!-- eslint-disable-next-line svelte/no-at-html-tags -->{@html renderThird(part.text, transId)}</span>
          {:else if part.para}
            <br class="para-br" />
          {:else}
            <span class="bk-num" class:approx={!part.real}>{part.n}</span>
            {#each (otables[transId] ?? []).filter(t => t.n === part.n) as tbl}
              <table class="eng-table"><tbody>
                {#each tbl.rows as trow}
                  <tr>{#each trow as cell}<td>{cell}</td>{/each}</tr>
                {/each}
              </tbody></table>
            {/each}
          {/if}
        {/each}
      </div>
    {:else}
      <div class="ross-prose">
        {#each attachTicks(parts) as part}
          {#if part.text === '\n'}
            <br class="para-br" />
          {:else if part.text !== null}
            <span class="bk-seg"
              >{#if part.tick}<span class="bk-num" class:approx={!part.tick.real}>{part.tick.n}</span
                >{/if}<!-- eslint-disable-next-line svelte/no-at-html-tags -->{@html highlightEng(part.text)}</span>
          {:else if part.para}
            <br class="para-br" />
          {:else}
            <span class="bk-num" class:approx={!part.real}>{part.n}</span>
          {/if}
        {/each}
      </div>
    {/if}
  {/snippet}

  {#snippet fullBookLoadState()}
    {#if !fullLoaded && fullBookLoading}
      <p class="translation-load-state" aria-live="polite">Loading {deferredQueryTrans ? (transById(deferredQueryTrans)?.short ?? 'translation') : 'translation'}…</p>
    {:else if !fullLoaded && fullBookError}
      <p class="translation-load-state translation-load-error" role="alert">{fullBookError} <button type="button" on:click={retryFullBook}>Retry</button></p>
    {/if}
  {/snippet}

  <!-- One English column for a translation: the primary's flow (block.flow) or
       an overlay's (block.oflows[id]), as flowing prose with margin-floated
       Bekker numbers. The footnote/table-bearing translation ('third' slot)
       uses renderThird + clickable `[^N]` markers + diagram tables; the rest
       use plain highlightEng. Works for any number of translations. -->
  {#snippet transFlow(block: Block, transId: string)}
    {@const flow = transId === engSlot?.id ? block.flow : (block.oflows[transId] ?? [])}
    {#if flow.length}
      {@const chTitle = importChapterTitle(transId, block.chapter)}
      <!-- An imported translation's chapter-opening title: a SIBLING before
           .ross-prose, not its first child — (a) inside .ross-prose it pushed
           the English prose one line below the Greek (John's review of
           631ff971); the Greek column gets a matching invisible spacer
           instead (see the .greek-col markup below), so Greek line 1 and
           English prose line 1 stay flush and the title takes its own space
           above; (b) the offset walkers (annotations.ts proseOffsetAt,
           emphasis-paint.ts proseText) root at col.querySelector('.ross-prose')
           and exclude only .bk-num/.eng-table, so title text INSIDE
           .ross-prose would leak into captured offsets — as a sibling they
           never see it, keeping the render-only/no-offset-shift guarantee
           structural. -->
      {#if chTitle}<div class="ross-chapter-title">{chTitle}</div>{/if}
      {@render flowProse(flow, transId, block.otables)}
    {:else if !fullLoaded && (fullBookLoading || fullBookError)}
      {@render fullBookLoadState()}
    {/if}
  {/snippet}

  <!-- The turn flow of a dialogue book: one row per speaker turn, the whole
       book long — each speaker's Greek statement level with its English
       translation (Tier-0 alignment). Stephanus sections are gutter TICKS, not
       layout containers: each section's first Greek line floats its token in
       the center gutter (Both view) / left gutter (Greek-only), and the tick
       element carries the col-{token} citation anchor (deep links, outline
       nav, scroll-spy, resume). In English-only view the Greek cells are
       hidden, so each row also carries no-id [data-etick] markers in the left
       gutter for the sections starting within it (row-level approximation —
       English tick precision is deferred Tier 1+). One-sided residual rows
       (unpaired turns) render in place with the other cell empty. -->
  <!-- Narrated paragraph prose: the row's English with `ep` paragraph breaks
       rendered as <br class="para-br"> (reusing flowParts/attachTicks — no
       Bekker ticks are passed here, so only the paragraph breaks and any hard
       newlines survive). flowParts clamps each break offset into the slice, so
       a break landing exactly on a turn/tick offset can't over-run the text. -->
  {#snippet paraProse(text: string, ep: number[] | null | undefined)}
    {#each attachTicks(flowParts(text, [], ep ?? [])) as part}
      {#if part.text === '\n'}
        <br class="para-br" />
      {:else if part.text !== null}
        <span class="bk-seg"><!-- eslint-disable-next-line svelte/no-at-html-tags -->{@html highlightEng(part.text)}</span>
      {:else if part.para}
        <br class="para-br" />
      {/if}
    {/each}
  {/snippet}

  <!-- One row's PRIMARY-translation English cell body (et embed / dialogue turn
       + folded subs). Factored out of the turn-flow english column so it can
       render in EITHER compare column when that column shows the primary. -->
  {#snippet primaryEng(row: FlowRow, ri: number)}
    {#if paraFlow && row.et && row.et.length}
      <div class="ross-prose turn-eng turn-stack">
        {#each etBlocks(row.english ?? '', row.et, row.ep) as b}
          <p class="turn-para">{#if !b.lead}{#if b.display}<span class="speaker" data-spk={spkSlots.get(b.display)}>{b.display}</span>{:else}<span class="speaker speaker-dash">—</span>{/if}{/if}{@render paraProse(b.text, b.ep)}</p>
        {/each}
      </div>
    {:else}
      {#if row.english}
        <div class="ross-prose turn-eng">
          {#if !paraFlow && !row.lead}{#if row.display}{#if !rowMeta[ri]?.hideLead}<span class="speaker" data-spk={spkSlots.get(row.display)}>{row.display}</span>{/if}{:else}<span class="speaker speaker-dash">—</span>{/if}{/if}{@render paraProse(row.english, row.ep)}{#each row.englishCont as c}<p class="turn-cont">{@render paraProse(c.text, c.ep)}</p>{/each}</div>
      {/if}
      {#if row.sub && row.sub.length}
        <div class="ross-prose turn-eng turn-stack">
          {#each row.sub as s, si}
            <p class="turn-para">{#if s.d}{#if !rowMeta[ri]?.hideSub[si]}<span class="speaker" data-spk={spkSlots.get(s.d)}>{s.d}</span>{:else}<span class="speaker speaker-dash">—</span>{/if}{/if}{@render paraProse(s.e, s.ep)}</p>
          {/each}
        </div>
      {:else if paraFlow && !row.english && !row.lead}
        <div class="ross-prose turn-eng"><span class="eng-missing" aria-hidden="true">—</span></div>
      {/if}
    {/if}
  {/snippet}

  <!-- One row's ALTERNATE-translation cell (turn-by-turn compare). The turn
       aligner gives each alternate one per-turn slice (alt[id] = {e, ep}), so
       this is just the row's speaker lead-in + that slice, or an em-dash where
       the alternate has no matching turn. No et/sub structure — alternates
       carry plain per-turn prose. Label suppression mirrors the primary (same
       speaker sequence) so the two columns stay visually parallel. -->
  {#snippet altEng(row: FlowRow, ri: number, id: string)}
    {@const a = row.alt?.[id]}
    <div class="ross-prose turn-eng">
      {#if !paraFlow && !row.lead}{#if row.display}{#if !rowMeta[ri]?.hideLead}<span class="speaker" data-spk={spkSlots.get(row.display)}>{row.display}</span>{/if}{:else}<span class="speaker speaker-dash">—</span>{/if}{/if}{#if a && a.e}{@render paraProse(a.e, a.ep)}{:else}<span class="eng-missing" title="No aligned passage in this translation"><span class="sr-only">No aligned passage in this translation.</span><span aria-hidden="true">—</span></span>{/if}</div>
  {/snippet}

  {#snippet flowRowsView(rows: FlowRow[])}
    <div class="turn-flow" class:para-flow={paraFlow} class:spk-color={spkColor}>
      {#each rows as row, ri}
        <!-- Which translation the (single / left) English column shows: the
             selected id, or the left compare id in compare mode. -->
        {@const leftId = trans === 'compare' ? compareLeft : trans}
        <div class="seg-row turn-row" class:turn-lead={row.lead} class:turn-residual={!row.lead && !row.paired}>
          <!-- Each turn row is a single speaker, so the Greek siglum (ΣΩ.) is
               coloured to match the row's English name via the column's data-spk
               (see .greek-col[data-spk] rules in global.css). -->
          <div class="greek-col" lang="grc" data-spk={row.display ? spkSlots.get(row.display) : undefined}>
            {#each row.greek as gl}
              <!-- Only the line's opening slice carries its id: a line split by
                   several turns (Parmenides' dash runs) yields multiple cont
                   slices, and repeating an -c id per slice would duplicate
                   ids. Cont slices aren't citation targets, so they get none. -->
              <div class="greek-line" id={gl.cont ? undefined : `L${gl.col}-${gl.n}`} class:target={!gl.cont && targetId === `L${gl.col}-${gl.n}`} class:cont={gl.cont}>
                {#if gl.tick}<span class="sect-tick" id="col-{gl.tick}">{gl.tick}</span>{/if}
                <span class="line-num">{gl.cont ? '' : showLineNum(gl.n)}</span>
                <span class="line-text" lang="grc">{@render greekToks(gl.parts)}</span>
              </div>
            {/each}
          </div>
          <div class="english-col" data-trans={leftId}>
            {#if trans === 'compare'}<div class="col-label">{transById(compareLeft)?.short ?? 'English'}</div>{/if}
            {#each row.ticks as t}<span class="sect-tick eng-tick" data-etick={t} aria-hidden="true">{t}</span>{/each}
            <!-- The (single / left) column shows the primary translation inline
                 (its full et/dialogue/sub structure) or, for an alternate id,
                 the aligner's per-turn slice via altEng. -->
            {#if leftId !== engSlot?.id}{@render altEng(row, ri, leftId)}{:else if paraFlow && row.et && row.et.length}
              <!-- Narrated embedded-dialogue row (para flow, `et`): the row's
                   English is english.turns nested inside a narrated paragraph —
                   set as a .turn-stack of labelled blocks (em-dash when the
                   lead-in is null), any `ep` breaks rebased per block. -->
              <div class="ross-prose turn-eng turn-stack">
                {#each etBlocks(row.english ?? '', row.et, row.ep) as b}
                  <p class="turn-para">{#if !b.lead}{#if b.display}<span class="speaker" data-spk={spkSlots.get(b.display)}>{b.display}</span>{:else}<span class="speaker speaker-dash">—</span>{/if}{/if}{@render paraProse(b.text, b.ep)}</p>
                {/each}
              </div>
            {:else}
              {#if row.english}
                <!-- The row's own English: dialogue rows keep their speaker
                     lead-in (em-dash for an unattributed turn); paragraph rows
                     (kind==='para') have no speaker, so the em-dash fallback is
                     suppressed. BOTH render `ep` paragraph breaks — pipeline B2
                     gives dialogue turns internal breaks too (Timaeus/Phaedo
                     long speeches), not just para flows. -->
                <div class="ross-prose turn-eng">
                  {#if !paraFlow && !row.lead}{#if row.display}{#if !rowMeta[ri]?.hideLead}<span class="speaker" data-spk={spkSlots.get(row.display)}>{row.display}</span>{/if}{:else}<span class="speaker speaker-dash">—</span>{/if}{/if}{@render paraProse(row.english, row.ep)}{#each row.englishCont as c}<p class="turn-cont">{@render paraProse(c.text, c.ep)}</p>{/each}</div>
              {/if}
              {#if row.sub && row.sub.length}
                <!-- One-sided English speeches folded under this row (pipeline
                     B4 residual redesign — dialogue flows AND para flows): a
                     stack of labelled blocks under the row's Greek. Usually the
                     row's `e` is null and this stack IS the English cell; when
                     the row also carries English (a narration lead, e.g. Lysis
                     203a) the stack follows it. Lead-in span when a printed
                     display exists; em-dash otherwise (genuine speaker turns —
                     Fowler's prose embeds the "he said" attributions). -->
                <div class="ross-prose turn-eng turn-stack">
                  {#each row.sub as s, si}
                    <p class="turn-para">{#if s.d}{#if !rowMeta[ri]?.hideSub[si]}<span class="speaker" data-spk={spkSlots.get(s.d)}>{s.d}</span>{/if}{:else}<span class="speaker speaker-dash">—</span>{/if}{@render paraProse(s.e, s.ep)}</p>
                  {/each}
                </div>
              {:else if paraFlow && !row.english && !row.lead}
                <!-- Defensive: a para-flow row with Greek but NO English content
                     (e null, sub null/empty) is malformed pipeline output — the
                     contract says every para row carries e or sub. Render an
                     intentional untranslated marker instead of a silently blank
                     cell (the blank-cell defect this round eliminates). Dialogue
                     flows are exempt: a Greek-only residual with a blank English
                     cell is their normal pre-B4 shape. -->
                <div class="ross-prose turn-eng"><span class="eng-missing" aria-hidden="true">—</span></div>
              {/if}
            {/if}
          </div>
          <!-- Right compare column: the second chosen translation, turn-by-turn
               beside the first (hidden in Greek-only). Either column may be the
               primary or an alternate — pick the renderer by id. -->
          {#if trans === 'compare' && view !== 'greek'}
            <div class="ross-col" data-trans={compareRight}>
              <div class="col-label">{transById(compareRight)?.short ?? ''}</div>
              {#if compareRight === engSlot?.id}{@render primaryEng(row, ri)}{:else}{@render altEng(row, ri, compareRight)}{/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/snippet}

  <!-- A scene page's figure plate (Variant B, approved mock:
       design-board/context-panel-mocks/variantB-*): a bordered cartouche
       composing the scene's map (shared/lib/scenemap.ts, joined via
       shared/lib/scene-place.ts — currentPlateMap, computed above) beside its
       title treatment — position indicator + draft badge + day/place labels +
       the one-line Landmark summary (the same fields the old plain header
       carried; no scene title/plate-number is invented, since the pipeline
       emits none). Replaces the old marginal scene chips now that Reading
       Mode pages one scene at a time — this header IS the scene's
       introduction, not a margin annotation.
       Map-slot presence: reserved (`!plateDataLoaded`) before the gazetteer
       fetch resolves, so the box's aspect-ratio is already in the layout
       and filling it in place causes no reflow on the (overwhelmingly
       common) case that this scene turns out to have one; collapsed only
       once resolution confirms no mappable place (never an empty box in the
       settled state) — see the ensurePlateData block above for the tradeoff
       this accepts on a session's very first scene view. -->
  {#snippet readingSceneHead(s: Scene, idx: number, total: number)}
    <header class="reading-scene-head">
      <div class="reading-plate" class:reading-plate-nomap={plateDataLoaded && !currentPlateMap}>
        {#if !plateDataLoaded || currentPlateMap}
          <div class="reading-plate-map">
            <!-- eslint-disable-next-line svelte/no-at-html-tags -->
            {#if currentPlateMap}{@html currentPlateMap.svg}{/if}
          </div>
        {/if}
        <div class="reading-plate-content">
          <p class="reading-scene-pos">Scene {idx + 1} of {total} · lines {s.startLine}{#if s.endLine && s.endLine !== s.startLine}–{s.endLine}{/if}</p>
          <div class="reading-scene-meta">
            {#if typeof s.day === 'number'}
              <span
                class="reading-scene-day"
                title={bookTellingDay ? 'The day of the telling at Alcinous’s palace; the events narrated here lie years earlier.' : undefined}
              >Day {s.day}{bookTellingDay ? ' · telling' : ''}</span>
            {/if}
            {#if s.place}<span class="reading-scene-place">{s.place}</span>{/if}
            {#if scenesDraft}<span class="draft-badge" title="AI-drafted apparatus, pending review">Draft</span>{/if}
          </div>
          <p class="reading-scene-summary">{s.summary}</p>
        </div>
      </div>
    </header>
  {/snippet}

  <!-- Reading Mode body: ONE translation in a single generous column, no
       parallel Greek, no gutters, PAGED BY SCENE (John's directive,
       2026-07-18). Reuses the existing prose snippets (transFlow's flowProse /
       primaryEng / altEng) so the wording, footnotes and paragraphing match
       Scholar view exactly. A book with no scene apparatus degrades silently
       to the old whole-book flow (the `:else` branch below). -->
  {#snippet readingView()}
    <div class="reading-col">
      {@render fullBookLoadState()}
      {#if flowRows}
        {#each flowRows as row, ri}
          <div class="reading-row">
            {#if readingTransId === engSlot?.id}{@render primaryEng(row, ri)}{:else}{@render altEng(row, ri, readingTransId)}{/if}
          </div>
        {/each}
      {:else if scenes.length && readingHasSceneAnchors}
        {@const s = scenes[clampedSceneIndex]}
        {@render readingSceneHead(s, clampedSceneIndex, scenes.length)}
        {#if readingTransCuratedTicks}
          <!-- T3 lane (2026-07-21): Pope's pages ARE scene-anchored (curated
               ticks, exact at the boundary) but the prose BETWEEN those
               boundaries has no line-level Greek alignment signal — unlike
               Murray/Butler's dense milestone ticks. Same discreet-notice
               treatment as the book-level fallback below, honest about the
               narrower (not absent) uncertainty. -->
          <p class="reading-anchor-notice">Pope’s pages are anchored at scene boundaries; alignment within a scene is approximate.</p>
        {/if}
        {@render flowProse(currentSceneFlow.flowParts, readingTransId, currentSceneFlow.otables)}
        <nav class="reading-scene-nav" aria-label="Scene navigation">
          <button type="button" class="reading-scene-prev" on:click={prevScene} disabled={clampedSceneIndex === 0}>← Previous scene</button>
          <button type="button" class="reading-scene-next" on:click={nextScene} disabled={clampedSceneIndex === scenes.length - 1}>Next scene →</button>
        </nav>
      {:else if scenes.length}
        <!-- Book-level-only translation (John, 2026-07-19 — see
             readingHasSceneAnchors above): no real per-scene alignment
             signal exists, so scene paging is honestly unavailable rather
             than fabricated — the whole book renders once, with no scene
             nav, and a discreet notice explains why. -->
        <p class="reading-anchor-notice">{(translations.find(t => t.id === readingTransId)?.name) ?? readingTransId}'s translation is aligned at book level only; scene paging unavailable.</p>
        {@render flowProse(readingWholeBookFlow.flowParts, readingTransId, readingWholeBookFlow.otables)}
      {:else}
        {#each enrichedSegments as { seg, blocks } (seg.id)}
          {#each blocks as block}
            {#if block.chapter}{@render chapterHead(block)}{/if}
            {@render transFlow(block, readingTransId)}
          {/each}
        {/each}
      {/if}
    </div>
  {/snippet}

  <div class="reader-body view-{view} trans-{trans}" role="main"
    bind:this={readerBodyEl}
    class:busse={busse}
    class:stephanus={stephanus}
    class:verse-line={epicVerse}
    class:reading-mode={reading}
    class:word-open={!!popup}
    class:speeches-on={speechesOn}
    class:audio-on={audioOn}
    style="--fs-greek:{fsGreek}rem;--fs-english:{fsEng}rem;--lh-greek:{lhGreek};--lh-english:{lhEng};--colw-scale:{colScale};--fs-scale:{fsScale}"
    on:copy={handleCopy}>
    <!-- Screen-reader announcement of a posture change (Scholar ⇄ Reading). -->
    <p class="sr-only" aria-live="polite">{postureMsg}</p>
    <div class="reader-controls">
      {#if liveChapter}
        <span class="rc-context">{liveChapter}</span>
      {/if}
      <div class="rc-cite">
        {#if view === 'greek'}
          {#if greekSrc}<span class="rc-greek">{greekSrc.full}</span>{/if}
        {:else if trans === 'compare'}
          {#if view === 'both'}<span class="rc-col-spacer" aria-hidden="true"></span>{/if}
          <span class="rc-col-name">{citeShort(transById(compareLeft))}</span>
          <span class="rc-col-name">{citeShort(transById(compareRight))}</span>
        {:else if view === 'both'}
          <span class="rc-pair">{pairText}</span>
        {:else if selectedTrans}
          <span class="rc-full">{selectedTrans.name}</span>
        {/if}
      </div>
      <div class="rc-controls">
        <!-- Posture toggle: Scholar ⇄ Reading Mode (keystroke `r`). UNCHANGED
             text/behaviour (John's nav-bar merge brief, 2026-07-24, pass/fail
             #6: below-1100px arrangement — including this button's copy —
             stays byte-identical to before the merge). At/above 1100px the
             nav bar (ReaderShell.astro) carries its OWN, differently-worded
             posture control instead — see global.css's `.reader-controls
             .posture-btn` width gate — so this copy is the ONLY carrier below
             1100px, same reachability rationale as before (phones/compact
             windows need it here, not buried in Settings). -->
        <button
          type="button"
          class="posture-btn"
          aria-pressed={reading}
          on:click={toggleReading}
          title={reading ? 'Return to Scholar view (r)' : 'Enter Reading Mode (r)'}
        >{reading ? 'Scholar view' : 'Reading Mode'}</button>
      </div>
    </div>
    {#if scenes.length && !reading && chartRoomOpen}
      <aside class="scene-context-rail" id="scene-context-rail" aria-label="Chart Room scene context">
        <div class="scene-context-rail-head">
          <span>Chart Room</span>
          <button type="button" on:click={toggleChartRoom} aria-label="Close Chart Room">×</button>
        </div>
        <p class="scene-context-title">{scenePanelScene?.summary ?? 'Scene context'}</p>
        {#if typeof scenePanelScene?.day === 'number'}
          <span class="scene-context-day">Day {scenePanelScene.day}{bookTellingDay ? ' · telling' : ''}</span>
        {/if}
        <div class="scene-context-place">
          <span class="scene-context-place-name">{scenePanelPlaceName}</span>
          {#if scenePanelCertainty}<span class="scene-context-certainty">{scenePanelCertainty}</span>{/if}
        </div>
        {#if !plateDataLoaded || currentPlateMap}
          <div class="scene-context-map" class:pending={!currentPlateMap}>
            <!-- eslint-disable-next-line svelte/no-at-html-tags -->
            {#if currentPlateMap}{@html currentPlateMap.svg}{/if}
          </div>
        {/if}
      </aside>
    {/if}
    <!-- Print-only masthead (hidden on screen): author eyebrow, work title with
         its Greek title alongside, and the source citation. -->
    <div class="print-head" aria-hidden="true">
      <div class="print-eyebrow">{workMeta?.author ?? HOUSE_AUTHOR}</div>
      <div class="print-titleline">
        <span class="print-title">{workMeta?.title ?? ''}</span>
        {#if workMeta?.greekTitle}<span class="print-title-gk">{workMeta.greekTitle}</span>{/if}
      </div>
      {#if printCite}<div class="print-cite">{printCite}</div>{/if}
    </div>
    {#if hasApproxTicks && !busse}
      <!-- The estimate disclaimer stays one click away, not a paragraph of
           front matter: the honesty lives in the ticks themselves (upright vs
           italic grey); this explains the convention on demand. -->
      <div class="bekker-info">
        <button
          type="button"
          class="bekker-info-btn"
          aria-expanded={bekkerInfoOpen}
          on:click|stopPropagation={() => (bekkerInfoOpen = !bekkerInfoOpen)}
        >ℹ︎ Bekker numbers</button>
        {#if bekkerInfoOpen}
          <div class="bekker-info-pop" role="note" transition:fade={{ duration: reduceMotion ? 0 : 120 }}>
            Greek line numbers are exact. The translations carry no Bekker
            numbers of their own, so those beside the English are aligned to
            the Greek: <span class="bk-fixed">upright</span> = fixed (anchored
            to this point in the text), <span class="bk-approx">italic grey</span>
            = approximate (interpolated estimate).
          </div>
        {/if}
      </div>
    {/if}
    {#if hasBracketedLines}
      <!-- Once per book view, only when this book actually carries a
           bracketed line (John's apparatus-honesty rule: the convention is
           explained where it's used, not as permanent front matter). -->
      <div class="verse-bracket-legend">
        <span class="bracket-sample" aria-hidden="true">[ ]</span> marks lines athetized/bracketed in the editorial tradition.
      </div>
    {/if}
    {#if meterOn && epicVerse && !reading}
      <!-- Discreet legend, same "explain the convention where it's used"
           posture as the bracket legend above. Guarded off in Reading Mode:
           that posture shows a single translation with no Greek gutter to
           annotate, so the meter tag never appears there — a legend with
           nothing to explain would just be clutter. -->
      <div class="meter-legend">
        <span class="meter-sample" aria-hidden="true">—◡◡</span> dactyl ·
        <span class="meter-sample" aria-hidden="true">——</span> spondee ·
        <span class="meter-sample" aria-hidden="true">—×</span> anceps —
        <span class="meter-amb-sample" aria-hidden="true">≈</span> ambiguous scan ·
        <span class="meter-unres-sample" aria-hidden="true">—</span> no confident scan
      </div>
    {/if}
    {#if reading}
      <!-- Reading Mode: single column, one translation, minimal chrome. -->
      {@render readingView()}
    {:else}
    {#if flowRows}
      <!-- Dialogue book: the continuous turn flow replaces the per-section
           segment blocks; Stephanus tokens float as gutter ticks. -->
      {@render flowRowsView(flowRows)}
    {:else}
    {#each enrichedSegments as {seg, blocks} (seg.id)}
      {@const leadChapter = blocks[0]?.chapter ? blocks[0] : null}
      <div class="segment" id="col-{seg.column}">
        <!-- A chapter that opens this column heads the segment, ABOVE the column
             reference (the column ref is a marker within the chapter, not a
             heading over it). Mid-column chapter starts render inline below. -->
        {#if leadChapter}{@render chapterHead(leadChapter)}{/if}
        {#if !busse}
          <div class="seg-ref">
            {seg.column}
          </div>
        {/if}

        {#each blocks as block, bi}
          <!-- If the on-screen primary translation (English cell of this row)
               opens this chapter with an imported title, the Greek column gets
               an invisible spacer of the same one-line height (see
               .ross-chapter-title-spacer in global.css) so both columns are
               pushed down equally: title above, Greek line 1 flush with
               English prose line 1. Same gates as the visible title in
               transFlow (chapter start + that import's flow present here);
               skipped in greek-only view (no title shown → no gap). Compare
               mode aligns Greek to the LEFT column; the right column's own
               title still renders in its cell via transFlow. -->
          {@const spacerTransId = trans === 'compare' ? compareLeft : trans}
          {@const spacerFlow = spacerTransId === engSlot?.id ? block.flow : (block.oflows[spacerTransId] ?? [])}
          {@const spacerTitle = view !== 'greek' && spacerFlow.length ? importChapterTitle(spacerTransId, block.chapter) : ''}
          {#if block.chapter && !(bi === 0 && leadChapter)}
            {@render chapterHead(block)}
          {/if}
          {#if phoneWidth && view === 'both' && trans !== 'compare' && epicVerse}
            <!-- Both view, phone width (John's ruling, 2026-07-18): interleaved
                 ALIGNMENT GROUPS instead of squeezed parallel columns — Greek
                 wrapped to 1–2 words/line otherwise. Each group is a run of
                 Greek verse lines followed by the English chunk aligned to
                 that same ~5-line milestone tick (see alignGroups above) —
                 never a fabricated per-verse pairing (Murray aligns per tick,
                 not per verse). Reuses greekLinesRender/flowProse, the exact
                 snippets the desktop columns below use, so tokens, brackets,
                 speech rail, audio, meter and footnotes behave identically.
                 Compare mode keeps its existing (pre-existing, out of scope)
                 phone stacking; busse/sidenotes/figs don't apply to epicVerse
                 works. -->
            <div class="seg-row stacked-both" data-chapter={block.currentChapter}>
              {#each alignGroups(block.lines, block.flow, bookSpeechStarts) as group, gi (gi)}
                <div class="align-group">
                  <div class="greek-col" lang="grc">
                    {@render greekLinesRender(seg, group.lines)}
                  </div>
                  <div class="english-col" data-trans={trans}>
                    {@render flowProse(group.flowParts, trans, block.otables)}
                    {#if gi === 0 && deferredQueryTrans}{@render fullBookLoadState()}{/if}
                  </div>
                </div>
              {/each}
            </div>
          {:else}
          <div class="seg-row" data-chapter={block.currentChapter}>
            <!-- Greek column -->
            <div class="greek-col" lang="grc">
              {#if spacerTitle}<div class="ross-chapter-title ross-chapter-title-spacer" aria-hidden="true">{spacerTitle}</div>{/if}
              {@render greekLinesRender(seg, block.lines)}
            </div>

            <!-- English column: the selected translation (single view), or the
                 left compare column. Prose laid out beside its Bekker-line
                 gutter — real anchors full weight, estimates lighter/italic. -->
            <div class="english-col" data-trans={trans === 'compare' ? compareLeft : trans}>
              {#if trans === 'compare'}<div class="col-label">{transById(compareLeft)?.short ?? 'English'}</div>{/if}
              {#if isUnpairedDialogue(seg)}
                <!-- A dialogue segment whose turns did not reconcile (and a
                     narrated work's said-bearing chunk): the English renders as
                     a STACK of turn paragraphs — each speech its own block with
                     its small-caps lead-in (em-dash for an unattributed turn),
                     the leading pre-turn continuation an unlabeled block. Block
                     boundaries, not inline splices, so a label can never butt
                     against the previous sentence. -->
                <div class="ross-prose turn-eng turn-stack">
                  {#each englishTurnBlocks(seg) as b}
                    <p class="turn-para">{#if !b.lead}{#if b.display}<span class="speaker">{b.display}</span>{:else}<span class="speaker speaker-dash">—</span>{/if}{/if}<!-- eslint-disable-next-line svelte/no-at-html-tags -->{@html highlightEng(b.text)}</p>
                  {/each}
                </div>
              {:else}
              {@render transFlow(block, trans === 'compare' ? compareLeft : trans)}
              {/if}
              {#if bi === 0 && deferredQueryTrans}{@render fullBookLoadState()}{/if}
              <!-- Inline diagrams ([[figN]] markers), e.g. the Tree of Porphyry. -->
              {#if busse && view !== 'greek' && block.figs.length}
                {#each block.figs as fig}
                  {#if figuresData[String(fig)]}<!-- eslint-disable-next-line svelte/no-at-html-tags -->{@html figuresData[String(fig)]}{/if}
                {/each}
              {/if}
            </div>

            <!-- Right compare column: the second chosen translation beside the
                 first (hidden in Greek-only). -->
            {#if trans === 'compare' && view !== 'greek'}
              <div class="ross-col" data-trans={compareRight}>
                <div class="col-label">{transById(compareRight)?.short ?? ''}</div>
                {@render transFlow(block, compareRight)}
              </div>
            {/if}

            <!-- Analytical sidenotes (Owen's marginal notes), floated into a
                 right rail on desktop; on mobile they fall inline below the
                 English (hidden in Greek-only view). -->
            {#if busse && view !== 'greek' && block.sidenotes.length}
              <aside class="sidenote-rail">
                {#each block.sidenotes as sn}
                  {#if sidenotesData[String(sn)]}<p class="sidenote">{sidenotesData[String(sn)]}</p>{/if}
                {/each}
              </aside>
            {/if}
          </div>
          {/if}
        {/each}
      </div>
    {/each}
    {/if}
    {/if}
  </div>
{/if}

<!-- Mobile Chart Room: its compact header is always present below the reader's
     established phone breakpoint; map payloads remain lazy until this expands. -->
{#if scenes.length}
  <aside class="scene-context-sheet" class:open={sceneSheetOpen} aria-label="Scene context" use:teleportToBody>
    <button
      type="button"
      class="scene-context-sheet-toggle"
      aria-expanded={sceneSheetOpen}
      aria-controls="scene-context-sheet-details"
      on:click={toggleSceneSheet}
    >
      <span class="scene-context-sheet-grab" aria-hidden="true"></span>
      <span class="scene-context-sheet-copy">
        <span class="scene-context-sheet-title">{scenePanelScene?.summary ?? 'Scene context'}</span>
        {#if typeof scenePanelScene?.day === 'number'}
          <span class="scene-context-sheet-day">Day {scenePanelScene.day}{bookTellingDay ? ' · telling' : ''}</span>
        {/if}
      </span>
      <span class="scene-context-sheet-chevron" aria-hidden="true">⌃</span>
    </button>
    <div class="scene-context-sheet-details" id="scene-context-sheet-details" aria-hidden={!sceneSheetOpen} inert={!sceneSheetOpen}>
      <div class="scene-context-sheet-label">Chart Room</div>
      {#if !plateDataLoaded || currentPlateMap}
        <div class="scene-context-map" class:pending={!currentPlateMap}>
          <!-- eslint-disable-next-line svelte/no-at-html-tags -->
          {#if currentPlateMap}{@html currentPlateMap.svg}{/if}
        </div>
      {/if}
      <div class="scene-context-place">
        <span class="scene-context-place-name">{scenePanelPlaceName}</span>
        {#if scenePanelCertainty}<span class="scene-context-certainty">{scenePanelCertainty}</span>{/if}
      </div>
    </div>
  </aside>
{/if}

<!-- Scene rail: a thin left drawer of this book's scenes (in-book navigation).
     Owned by the island (live scene data + scroll-tracked highlight); the header
     toggle lives in ReaderShell.astro and speaks via CustomEvents. Rendered only
     when the book carries scene apparatus. -->
{#if scenes.length}
<aside class="scene-rail" id="scene-rail" class:open={sceneRailOpen} aria-label="Scenes in this book" aria-hidden={!sceneRailOpen} inert={!sceneRailOpen} bind:this={sceneRailEl} on:keydown={onSceneRailKey}>
  <div class="scene-rail-head">
    <span class="scene-rail-title">Scenes</span>
    {#if scenesDraft}<span class="draft-badge" title="AI-drafted apparatus, pending review">Draft</span>{/if}
    <button type="button" class="scene-rail-close" on:click={closeSceneRail} aria-label="Close scenes">×</button>
  </div>
  <ul class="scene-list">
    {#each scenes as s, i}
      <li>
        <button
          type="button"
          class="scene-item"
          class:current={i === currentSceneIndex}
          aria-current={i === currentSceneIndex ? 'true' : undefined}
          on:click={() => jumpToScene(i)}
        >
          <span class="scene-item-meta">
            <span class="scene-item-lines">{s.startLine}{#if s.endLine && s.endLine !== s.startLine}–{s.endLine}{/if}</span>
            {#if typeof s.day === 'number'}
              <span
                class="scene-item-day"
                title={bookTellingDay ? 'The day of the telling at Alcinous’s palace; the events narrated here lie years earlier.' : undefined}
              >Day {s.day}{bookTellingDay ? ' · telling' : ''}</span>
            {/if}
            {#if s.place}<span class="scene-item-place">{s.place}</span>{/if}
          </span>
          <span class="scene-item-summary">{s.summary}</span>
        </button>
      </li>
    {/each}
  </ul>
</aside>
{#if sceneRailOpen}
  <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
  <div class="scenes-backdrop" on:click={closeSceneRail} transition:fade={{ duration: reduceMotion ? 0 : 180 }}></div>
{/if}
{/if}

<!-- Docked audio player: one shared <audio> element (feature #19). Sits
     collapsed off-screen until a chunk is pressed (nowPlaying set); the
     element itself never fetches anything until then — preload="none" and
     no src until playChunk sets one. The license link and item link are per
     BOOK (one archive.org item per book — see apparatus/audio/manifest.json),
     so they're always correct for whatever chunk is currently playing. -->
<div class="audio-dock" class:open={!!nowPlaying} aria-hidden={!nowPlaying} inert={!nowPlaying}>
  {#if nowPlaying}
    <div class="audio-dock-info">
      <span class="audio-dock-range">{workMeta?.title ?? work} {workMeta ? workBookLabel(workMeta, nowPlaying.book) : nowPlaying.book}.{nowPlaying.chunk.lines[0]}–{nowPlaying.chunk.lines[1]}</span>
      <span class="audio-dock-credit">read by {audioCreator}</span>
      <a class="audio-dock-license" href={nowPlaying.licenseurl} target="_blank" rel="noopener noreferrer">{licenseLabel(nowPlaying.licenseurl)}</a>
      <a class="audio-dock-item" href={itemPageUrl(nowPlaying.item)} target="_blank" rel="noopener noreferrer">archive.org ↗</a>
    </div>
  {/if}
  <audio bind:this={audioEl} controls preload="none" on:ended={closeAudioDock}></audio>
  {#if nowPlaying}
    <button type="button" class="audio-dock-close" on:click={closeAudioDock} aria-label="Close audio player">×</button>
  {/if}
</div>

<aside class="settings-sidebar" class:open={settingsOpen} aria-label="Reader settings" aria-hidden={!settingsOpen} inert={!settingsOpen} bind:this={settingsEl} on:keydown={onSettingsKey}>
  <div class="settings-head">
    <span class="settings-title">Settings</span>
    <button type="button" class="settings-close" on:click={closeSettings} aria-label="Close settings">×</button>
  </div>
  <div class="settings-body">
    <!-- Compact-only (below 1100px): at/above 1100px the view toggle lives in
         the nav bar instead (ReaderShell.astro's .nav-view-toggle — see
         .settings-compact-only in global.css). -->
    <div class="settings-section settings-compact-only">
      <div class="settings-section-label">View</div>
      {@render viewToggle()}
    </div>
    {#if translations.length > 1}
      <!-- Mobile-only: on desktop the picker sits beside the view toggle in the
           header (see .settings-trans in global.css). -->
      <div class="settings-section settings-trans">
        <div class="settings-section-label">Translation</div>
        <!-- svelte-ignore a11y-label-has-associated-control -->
        <label>
          <select class="settings-select" value={pickValue} on:change={onPick} aria-label="English translation">
            {#each translations as t}
              <option value={t.id}>{t.name}</option>
            {/each}
          </select>
        </label>
      </div>
    {/if}
    {#if canCompare}
      <!-- Mode lives HERE, not in the picker: the dropdowns choose WHICH
           translation, this chooses single vs side-by-side comparison. -->
      <div class="settings-section">
        <div class="settings-section-label">Translations</div>
        <label class="settings-mode-row">
          <input
            type="radio"
            name="trans-mode"
            checked={trans !== 'compare'}
            on:change={() => setTrans(lastSingle)}
          />
          <span>Single translation</span>
        </label>
        <label class="settings-mode-row">
          <input
            type="radio"
            name="trans-mode"
            checked={trans === 'compare'}
            on:change={() => setTrans('compare')}
          />
          <span>Compare two translations</span>
        </label>
      </div>
    {/if}
    {#if canCompare && trans === 'compare'}
      <!-- Compare pair: which two translations sit side by side. -->
      <div class="settings-section">
        <div class="settings-section-label">Compare</div>
        <!-- svelte-ignore a11y-label-has-associated-control -->
        <label class="settings-compare-row">
          <span class="settings-compare-side">Left</span>
          <select class="settings-select" bind:value={compareLeft} on:change={pickCompareLeft} aria-label="Compare left translation">
            {#each translations as t}
              <option value={t.id} disabled={t.id === compareRight}>{t.name}</option>
            {/each}
          </select>
        </label>
        <!-- svelte-ignore a11y-label-has-associated-control -->
        <label class="settings-compare-row">
          <span class="settings-compare-side">Right</span>
          <select class="settings-select" bind:value={compareRight} on:change={pickCompareRight} aria-label="Compare right translation">
            {#each translations as t}
              <option value={t.id} disabled={t.id === compareLeft}>{t.name}</option>
            {/each}
          </select>
        </label>
      </div>
    {/if}

    <!-- Print lives ONLY here, at every width (John's nav-bar merge brief,
         2026-07-24: dropped from the controls row entirely) — .settings-print
         (global.css) widens what was a mobile-only gate so this section shows
         on desktop too, unlike the compact-only sections above. -->
    <div class="settings-section settings-print">
      <div class="settings-section-label">Print</div>
      {@render printControl()}
    </div>

    <div class="settings-section">
      <div class="settings-section-label">Text size</div>
      <label class="settings-slider">
        <div class="settings-slider-row">
          <span class="settings-slider-name">Size</span>
          <span class="settings-slider-val">{Math.round(fsScale * 100)}%</span>
        </div>
        <input type="range" min="0.75" max="1.4" step="0.05" bind:value={fsScale} on:change={saveFs} aria-label="Text size" />
      </label>
    </div>

    <div class="settings-section">
      <div class="settings-section-label">Line spacing</div>
      <label class="settings-slider">
        <div class="settings-slider-row">
          <span class="settings-slider-name">Spacing</span>
          <span class="settings-slider-val">{Math.round(lhScale * 100)}%</span>
        </div>
        <input type="range" min="0.8" max="1.4" step="0.05" bind:value={lhScale} on:change={saveLh} aria-label="Line spacing" />
      </label>
    </div>

    <div class="settings-section">
      <div class="settings-section-label">Column width</div>
      <label class="settings-slider">
        <div class="settings-slider-row">
          <span class="settings-slider-name">Width</span>
          <span class="settings-slider-val">{Math.round(colScale * 100)}%</span>
        </div>
        <input type="range" min="0.75" max="1.3" step="0.05" bind:value={colScale} on:change={saveColw} aria-label="Column width" />
      </label>
    </div>

    {#if spkSlots.size > 1}
    <div class="settings-section">
      <div class="settings-section-label">Speakers</div>
      <label class="settings-check-row">
        <span class="settings-check-name">
          Color speaker names
          <span class="settings-check-hint">A distinct hue per speaker</span>
        </span>
        <span class="settings-pill">
          <input type="checkbox" bind:checked={spkColor} on:change={saveSpkColor} aria-label="Color speaker names by speaker" />
          <span class="settings-pill-track"></span>
          <span class="settings-pill-thumb"></span>
        </span>
      </label>
    </div>
    {/if}

    {#if epicVerse}
    <div class="settings-section">
      <div class="settings-section-label">Speeches</div>
      <label class="settings-check-row">
        <span class="settings-check-name">
          Show speaker rails
          <span class="settings-check-hint">
            Margin rail for who's speaking <span class="draft-badge dices-badge" title="Computed from DICES (Du Bois et al.), CC-BY 4.0">DICES</span>
          </span>
        </span>
        <span class="settings-pill">
          <input type="checkbox" bind:checked={speechesOn} on:change={saveSpeeches} aria-label="Show DICES speech rails in the Greek gutter" />
          <span class="settings-pill-track"></span>
          <span class="settings-pill-thumb"></span>
        </span>
      </label>
    </div>
    {/if}

    {#if epicVerse}
    <div class="settings-section">
      <div class="settings-section-label">Meter</div>
      <label class="settings-check-row">
        <span class="settings-check-name">
          Show hexameter scansion
          <span class="settings-check-hint">Computed dactyl/spondee pattern beside each Greek line; on small screens, shown in Greek view and in Both view's stacked layout, hidden when comparing two translations</span>
        </span>
        <span class="settings-pill">
          <input type="checkbox" bind:checked={meterOn} on:change={saveMeter} aria-label="Show computed hexameter scansion beside each Greek line, in Scholar view" />
          <span class="settings-pill-track"></span>
          <span class="settings-pill-thumb"></span>
        </span>
      </label>
    </div>
    {/if}

    {#if audioAvailable}
    <div class="settings-section">
      <div class="settings-section-label">Audio</div>
      <label class="settings-check-row">
        <span class="settings-check-name">
          Hear this passage
          <span class="settings-check-hint">Recitation by {audioCreator}, hotlinked from archive.org</span>
        </span>
        <span class="settings-pill">
          <input type="checkbox" bind:checked={audioOn} on:change={saveAudio} aria-label={`Show play buttons for ${audioCreator}'s recitation audio in the Greek gutter`} />
          <span class="settings-pill-track"></span>
          <span class="settings-pill-thumb"></span>
        </span>
      </label>
    </div>
    {/if}

    <div class="settings-section">
      <div class="settings-section-label">Copying</div>
      <label class="settings-check-row">
        <span class="settings-check-name">
          Append citation on copy
          <span class="settings-check-hint">Greek selections only</span>
        </span>
        <span class="settings-pill">
          <input type="checkbox" bind:checked={citeCopy} on:change={saveCiteCopy} aria-label="Append citation when copying text" />
          <span class="settings-pill-track"></span>
          <span class="settings-pill-thumb"></span>
        </span>
      </label>
    </div>

    <div class="settings-section">
      <button type="button" class="settings-reset" on:click={resetSettings}>Reset to defaults</button>
    </div>
  </div>
</aside>

{#if settingsOpen}
  <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
  <div class="settings-backdrop" on:click={closeSettings} transition:fade={{ duration: reduceMotion ? 0 : 180 }}></div>
{/if}

{#if popup}
  <WordPopup
    {work}
    token={popup.token}
    anchor={popup.anchor}
    asSheet={trans === 'compare'}
    docked={dockedLexicon}
    autofocus={popupViaKb}
    onClose={closePopup}
  />
{/if}

<svelte:window on:pointerdown={onDocPointerDown} on:keydown={onGlobalKey} />

{#if footnote}
  <FootnotePopup
    {work}
    n={footnote.n}
    transId={footnote.transId}
    anchor={footnote.anchor}
    onClose={closeFootnote}
    onHoverIn={cancelFnClose}
    onHoverOut={scheduleFnClose}
  />
{/if}

{#if copyBtnPos}
  <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
  <button
    class="copy-cite-btn"
    style="left:{copyBtnPos.x}px;top:{copyBtnPos.y}px"
    on:mousedown|preventDefault
    on:click={clickCopyBtn}
    aria-label="Copy with citation"
    title="Copy with citation"
  >
    <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V2z"/>
      <path d="M0 4a2 2 0 0 1 2-2v10a2 2 0 0 0 2 2h8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V4z"/>
    </svg>
    Copy
  </button>
{/if}

<!-- Meter overlay (feature #19): scoped, component-local styles rather than
     global.css (avoids widening the shared-core drift surface tracked in
     DRIFT.md for a Homer-only feature — see the module docstring above). -->
<style>
  /* Reading Mode's honest-degradation notice for a book-level-only
     translation (John, 2026-07-19 — see readingHasSceneAnchors in the
     script above: Pope carries one bekker anchor per book, no real
     per-scene signal). Same discreet one-line-legend tone as global.css's
     .verse-bracket-legend/.bekker-info-pop (this file only owns a handful of
     small component-scoped rules; the rest of the reader's chrome styling
     lives centrally in global.css). */
  .reading-anchor-notice {
    font-family: var(--font-ui);
    font-size: 0.78rem;
    font-style: italic;
    color: var(--text-light);
    margin: 0 0 1rem;
  }

  .translation-load-state {
    margin: 0.7rem 0 0;
    color: var(--text-light);
    font-family: var(--font-ui);
    font-size: 0.78rem;
    font-style: italic;
  }
  .translation-load-error { color: var(--text-mid); }
  .translation-load-state button {
    margin-left: 0.35rem;
    border: 1px solid var(--border);
    border-radius: 0.2rem;
    background: transparent;
    color: var(--accent);
    cursor: pointer;
    font: inherit;
    padding: 0.08rem 0.35rem;
  }
  .translation-load-state button:hover { border-color: var(--accent); }

  /* Right-aligned tag on the Greek line's flex row (.greek-line: line-num
     fixed-width, .line-text flex:1, this sits last) — no layout reservation
     when meterOn is false, since the element isn't rendered at all then
     (see Reader.svelte's {#if meterOn} guard), so toggling off leaves no
     residual gutter/CLS. */
  .meter-tag {
    flex-shrink: 0;
    margin-left: 0.5rem;
    font-family: var(--font-ui);
    font-size: 0.78em;
    color: var(--text-light);
    letter-spacing: 0.02em;
    cursor: help;
    -webkit-user-select: none;
    user-select: none;
  }
  /* Ambiguous (a real, minimal-relaxation scan — just philologically
     disputed): visibly qualified via the "≈" prefix already in the text
     (shared/lib/scansion.ts's scansionDisplay) plus italic + a light dim.
     0.88 opacity keeps text-light's contrast at ~4.9:1 (light) / ~6.6:1
     (dark) — still AA (>=4.5:1), never washed out to illegible. */
  .meter-tag.meter-ambiguous {
    font-style: italic;
    opacity: 0.88;
  }
  /* Unresolved: the honest "—" placeholder only (never a fabricated
     pattern — see scansionDisplay). Same AA-safe opacity as the ambiguous
     tier; the placeholder's sparseness (a single dash) plus its title "no
     confident scan" carry the signal, not a contrast trick. */
  .meter-tag.meter-unresolved {
    opacity: 0.88;
  }

  /* Squeezed Both view at phone width (John's phone screenshot, 2026-07-18):
     the parallel Greek/English columns compress hard here (see global.css's
     `@media (max-width: 680px) { .reader-body.view-both .greek-col {
     font-size: 0.9rem } … }` — same <=680px family used throughout the
     reader for this exact squeeze), wrapping Greek to 1–2 words a row, with
     no room for the meter-tag glyph strings (—◡◡ —◡◡ —— …). Still hidden
     there. The stacked-Both alignment-group layout (John's follow-up ruling,
     same day) gives Greek back its full single-column width, same as
     Greek-only — re-enabled there, one rule down, now that the wrap fix
     below makes it safe at any width. The element is already conditionally
     rendered (`{#if meterOn}`), so `display: none` adds no layout
     reservation of its own. */
  @media (max-width: 680px) {
    .reader-body.view-both .meter-tag { display: none; }
    /* Stacked-Both's Greek is full-width (not the squeezed two-column
       layout above) — re-enable the tag there, matching Greek-only. */
    .reader-body.view-both .stacked-both .meter-tag { display: inline; }
  }

  /* Greek-only meter overflow at phone width (flagged 2026-07-18, ~38px
     horizontal page overflow at 390px): `.greek-line` is a flex row with no
     wrap, `.line-text` flex:1, and `.meter-tag` flex-shrink:0 — a full
     hexameter's scan string (up to 6 feet, e.g. "—◡◡ —◡◡ —◡◡ —◡◡ —◡◡ ——")
     doesn't fit beside the Greek line at this width and the un-shrinkable
     tag forces the whole row past the viewport. Fix: let the row wrap and
     force the tag onto its own line below the Greek text (flex-basis:100% in
     a flex-wrap container is a reliable break, not just "if it happens to
     not fit") — legible, not truncated, never causes horizontal scroll.
     Applies at any width in this family: Greek-only (always shows the tag)
     and stacked-Both (re-enabled just above) both use this same .greek-line
     markup and both need the same guarantee. margin-left aligns the tag
     under the Greek text, not the line-number gutter: default `.line-num`
     min-width (1.8rem) + `.greek-line` gap (0.35rem) — the values both
     Greek-only and stacked-Both use at this width (see global.css's
     `.stacked-both .line-num`/`.greek-line` rules, which restore these same
     defaults after the two-column Both view's tighter squeeze). */
  @media (max-width: 680px) {
    .greek-line { flex-wrap: wrap; }
    .meter-tag {
      flex: 1 1 100%;
      margin-left: calc(1.8rem + 0.35rem);
      margin-top: 0.15rem;
    }
  }

  /* Discreet legend, shown only while the overlay is on (Scholar view) —
     same "explain the convention where it's used" posture as
     .verse-bracket-legend in global.css. */
  .meter-legend {
    font-family: var(--font-ui);
    font-size: 0.78rem;
    color: var(--text-light);
    margin: 0 0 0.75rem;
  }
  .meter-legend .meter-sample {
    font-family: var(--font-greek);
  }
  .meter-legend .meter-amb-sample {
    font-style: italic;
  }

  /* Chart Room shares the reader's material vocabulary: restrained rules,
     display-face place names, and the existing accent rather than a new map
     palette. It floats at the reading edge so the normal Scholar flow keeps
     its markup and token order intact. The toggle BUTTON itself moved to
     ReaderShell.astro's nav bar (`.nav-chart-room` in global.css, John's
     nav-bar merge brief, 2026-07-24); this scoped block now only styles the
     rail/sheet surface that button opens. */
  .scene-context-rail button:focus-visible,
  .scene-context-sheet-toggle:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }
  .scene-context-rail {
    float: right;
    position: sticky;
    top: calc(var(--header-h, 92px) + 3.5rem);
    z-index: 4;
    width: min(20rem, 32%);
    margin: 0 0 1.25rem 1.5rem;
    padding: 1rem;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--col-bg);
    box-shadow: 0 1px 2px var(--border);
  }
  .scene-context-rail-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    font-family: var(--font-display);
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
  }
  .scene-context-rail-head button {
    border: 0;
    padding: 0.1rem 0.3rem;
    background: transparent;
    color: var(--text-mid);
    cursor: pointer;
    font-family: var(--font-ui);
    font-size: 1.1rem;
    line-height: 1;
  }
  .scene-context-title {
    margin: 0.8rem 0 0;
    color: var(--text-mid);
    font-family: var(--font-ui);
    font-size: 0.82rem;
    font-style: italic;
    line-height: 1.45;
  }
  .scene-context-day {
    display: inline-block;
    margin-top: 0.75rem;
    padding: 0.16rem 0.5rem;
    border: 1px solid color-mix(in srgb, var(--accent) 40%, var(--border));
    border-radius: 999px;
    color: var(--accent);
    font-family: var(--font-ui);
    font-size: 0.72rem;
    font-weight: 600;
  }
  .scene-context-place {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.4rem;
    margin-top: 0.8rem;
  }
  .scene-context-place-name {
    color: var(--text);
    font-family: var(--font-display);
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.2;
  }
  .scene-context-certainty {
    padding: 0.05rem 0.35rem;
    border: 1px solid color-mix(in srgb, var(--text-mid) 45%, transparent);
    border-radius: 999px;
    color: var(--text-mid);
    font-family: var(--font-ui);
    font-size: 0.58rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }
  .scene-context-map {
    aspect-ratio: 320 / 220;
    margin-top: 0.85rem;
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 7px;
    background: var(--page-bg);
  }
  .scene-context-map.pending { min-height: 7rem; }
  .scene-context-map svg { display: block; width: 100%; height: 100%; }

  .scene-context-sheet { display: none; }

  @media (max-width: 680px) {
    .scene-context-rail { display: none; }
    /* The mobile sheet is the single map surface; the B-plate keeps its
       textual heading while yielding its duplicate map slot. */
    .reader-body.reading-mode .reading-plate-map { display: none; }
    .reader-body.reading-mode .reading-plate { grid-template-columns: 1fr; }

    .scene-context-sheet {
      position: fixed;
      right: 0;
      bottom: 0;
      left: 0;
      z-index: 40;
      display: block;
      border-top: 1px solid var(--accent);
      border-radius: 14px 14px 0 0;
      background: var(--col-bg);
      box-shadow: 0 -4px 18px var(--border);
    }
    .scene-context-sheet-toggle {
      display: grid;
      grid-template-columns: 1fr auto;
      width: 100%;
      padding: 0.35rem 0.9rem 0.65rem;
      border: 0;
      background: transparent;
      color: var(--text);
      cursor: pointer;
      text-align: left;
    }
    .scene-context-sheet-grab {
      grid-column: 1 / -1;
      width: 2.1rem;
      height: 0.25rem;
      margin: 0 auto 0.35rem;
      border-radius: 999px;
      background: var(--border);
    }
    .scene-context-sheet-copy { min-width: 0; }
    .scene-context-sheet-title,
    .scene-context-sheet-day { display: block; }
    .scene-context-sheet-title {
      overflow: hidden;
      color: var(--text);
      font-family: var(--font-display);
      font-size: 0.95rem;
      font-weight: 600;
      line-height: 1.15;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .scene-context-sheet-day {
      margin-top: 0.18rem;
      color: var(--text-mid);
      font-family: var(--font-ui);
      font-size: 0.72rem;
    }
    .scene-context-sheet-chevron {
      align-self: center;
      color: var(--text-mid);
      font-family: var(--font-ui);
      font-size: 1.1rem;
      line-height: 1;
      transition: transform 180ms ease;
    }
    .scene-context-sheet.open .scene-context-sheet-chevron { transform: rotate(180deg); }
    .scene-context-sheet-details {
      max-height: 0;
      overflow: hidden;
      padding: 0 1rem;
      opacity: 0;
      transform: translateY(0.75rem);
      transition: max-height 180ms ease, opacity 180ms ease, transform 180ms ease, padding 180ms ease;
    }
    .scene-context-sheet.open .scene-context-sheet-details {
      max-height: 62dvh;
      padding: 0 1rem calc(1rem + env(safe-area-inset-bottom));
      opacity: 1;
      overflow-y: auto;
      transform: translateY(0);
    }
    .scene-context-sheet-label {
      margin: 0 0 0.7rem;
      color: var(--text-mid);
      font-family: var(--font-display);
      font-size: 0.82rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }
    .scene-context-sheet-details .scene-context-map { margin-top: 0; }
    .scene-context-sheet-details .scene-context-place { margin: 0.75rem 0 0; }
  }

  @media (prefers-reduced-motion: reduce) {
    .scene-context-sheet-chevron,
    .scene-context-sheet-details { transition: none; }
  }
</style>
