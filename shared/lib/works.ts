// The corpus registry — the single source of truth for which works the site
// carries. Adding a work is one entry here (plus its pipeline data under
// build/dist/<id>/). Everything else — routing, the home index, the reader's
// work switcher, unified search — is driven off this list.
//
// `id` is the URL slug AND the data directory name; it is a readable
// CamelCase slug matching the manifest filename (Euthyphro, Alcibiades1),
// established by the Euthyphro pilot rather than a Bekker-style abbreviation.
//
// `translations[].slot` says which emitted segment field the reader renders for
// that translation: 'english' is the primary parallel chunk, 'ross' a
// secondary chapter-anchored overlay, 'third' an optional third overlay, and
// 'overlay' any further overlay (4th onward) read from seg.overlays[id] — so a
// work can carry any number of translations. The picker lists them in
// registry order. Every Plato work in this rollout carries exactly one
// (primary/'english') translation; the slot machinery is inherited generic
// infrastructure, not Plato-specific.

export interface TranslationRef {
  id: string;
  name: string;     // full citation, for the picker + attribution
  short: string;    // chip label
  slot: 'english' | 'ross' | 'third' | 'overlay';
  // Carries inline `[^N]` footnote markers + a footnotes.json popup map.
  // Independent of slot — the reader renders the markers for whichever
  // translation sets this.
  footnotes?: boolean;
  // Copyright-encumbered translations carried only in the local/full build.
  // The public deploy sets PUBLIC_HIDE_PRIVATE=1 to drop them from the registry
  // (and is built from the work's -public manifest, so their text is absent too).
  private?: boolean;
}

// A gap in a work's book sequence worth annotating in the reader (e.g. the
// Aristotelian Eudemian Ethics' "common books", shared with the Nicomachean
// Ethics and not reprinted). No work in this rollout uses it — every Plato
// work here is bookless (books: 1) — but the field/type stay as generic
// multi-book infrastructure for the Republic/Laws/Letters follow-up.
export interface MissingBooks {
  after: number;      // render the note after this (contiguous) book index
  label: string;      // the missing books' labels, e.g. 'IV–VI'
  note: string;       // one line explaining the gap
  linkWork: string;   // id of the work that carries the text (e.g. 'EN')
  linkBook: number;   // book to jump to in that work
  linkLabel: string;  // link text, e.g. 'Nicomachean Ethics V–VII'
}

export interface Work {
  id: string;       // slug + data dir, e.g. 'Euthyphro'
  title: string;
  greekTitle?: string;  // polytonic Greek title, shown in the print masthead
  abbr: string;     // display abbreviation (may differ from id styling)
  author: string;
  // Standard scholarly abbreviation of the author, for a copy-able citation
  // that names the author ("Hom. Il. 1.1"). Omitted ⇒ the citation carries no
  // author prefix (the pre-Homer convention, where the work context is implicit).
  authorAbbr?: string;
  books: number;
  bookLabels: string[];   // per-book display labels (Arabic for a bookless work)
  missingBooks?: MissingBooks;  // annotate a gap in the book sequence
  greekEdition: string;
  // The print edition the TLG text was digitised from, in two lengths: `short`
  // for the reader's bilingual strip, `full` for the Greek-only strip and the
  // Texts & Licences page (both driven off this one field so they can't drift).
  greekSource: { short: string; full: string };
  translations: TranslationRef[];
  // Which translation the reader shows by default (a translations[].id). When
  // omitted the reader falls back to the primary 'english'-slot translation.
  defaultTranslation?: string;
  blurb: string;    // one line for the home index
  // Most works are cited by Bekker (column:line). Plato is cited by Stephanus
  // page + section only — no user-facing line numbers at all (see
  // shared/lib/citation.ts). Default (omitted) = bekker.
  citation?: { scheme: 'bekker' | 'busse' | 'stephanus' | 'verse-line'; hideLineNumbers?: boolean };
  // Cross-links to closely related works, shown on the landing page. Each
  // `id` must be a built work.
  related?: { id: string; label: string }[];
  // Ancient commentaries/introductions hosted on the site that comment on THIS
  // work (ids of built works), surfaced in a "Commentary" section on the
  // landing page.
  commentaries?: string[];
  /** Authorship status. Absent ⇒ genuine. Drives the homepage/landing badge. */
  authenticity?: 'genuine' | 'dubious' | 'spurious';
  // Traditional stylometric/dramatic dating (early/middle/late Plato), shown
  // as a single hedged line on the work's landing page. Omitted for the
  // disputed corpus (works without a settled place in the traditional
  // chronology) and the Letters — see docs/registry-draft.md and John's call
  // 2026-07-11. Not shown anywhere on the home page.
  period?: 'early' | 'middle' | 'late';
}

export const AUTHENTICITY_LABEL: Record<'dubious' | 'spurious', string> = {
  dubious: 'Dubious',
  spurious: 'Spurious',
};

// Copyright-encumbered translations are carried ONLY when a build explicitly
// opts in via PUBLIC_SHOW_PRIVATE=1 — the `npm run dev` script sets it, so they
// show locally. Every production build (plain `npm run build` AND the public
// deploy, which forces it off) leaves it unset, so private entries — and their
// citations — are dropped from the bundle. This is fail-SAFE: a forgotten flag
// hides private content rather than leaking text we can't host. No work in
// this rollout carries a private translation yet, but `visibleTranslations`
// below still gates on this flag for when one does.
const SHOW_PRIVATE = import.meta.env.PUBLIC_SHOW_PRIVATE === '1';

// The site's house author. Works BY this author show a bare title everywhere a
// label is composed (work switcher, breadcrumbs); a work by anyone else (a
// future commentator/introduction, as aristotle-reader carries Porphyry) keeps
// the "(Author)" parenthetical. Single named constant so the default is never a
// scattered string comparison.
export const HOUSE_AUTHOR = 'Homer';

// The two Homeric epics, in traditional (Iliad-before-Odyssey) order. Both are
// cited by the verse-line scheme (book.line — the sacred vulgate lineation; see
// shared/lib/citation.ts). Book labels are Arabic numerals 1–24, matching the
// citation display ("Il. 1.1"); the Greek-letter book convention (Α–Ω) is not
// used for navigation labels. The digital Greek text is Perseus' PerseusDL
// canonical-greekLit (CC BY-SA 4.0); each work's `greekEdition` names the print
// edition that text was keyed from. Translations are public-domain only, judged
// by US copyright rules: Murray (Loeb, primary), Butler (prose), Pope (verse).
const BOOK_LABELS_24 = Array.from({ length: 24 }, (_, i) => String(i + 1));
const PERSEUS_GREEK_SOURCE = {
  short: 'Perseus',
  full: 'Digital Greek text from the Perseus Digital Library (PerseusDL, '
    + 'canonical-greekLit), licensed CC BY-SA 4.0.',
};
const TLG_ALLEN_GREEK_SOURCE = {
  short: 'Allen 1931',
  full: 'Greek text of T. W. Allen’s editio maior (Oxford, 1931), from a '
    + 'licensed TLG export; Il. 8.548, 550–552, omitted by Allen, are '
    + 'supplied from the vulgate (Perseus) and rendered as athetized.',
};

export const WORKS: Work[] = [
  {
    id: 'iliad',
    title: 'Iliad',
    greekTitle: 'Ἰλιάς',
    abbr: 'Il.',
    author: 'Homer',
    authorAbbr: 'Hom.',
    books: 24,
    bookLabels: BOOK_LABELS_24,
    greekEdition: 'T. W. Allen, editio maior (Oxford, 1931)',
    greekSource: TLG_ALLEN_GREEK_SOURCE,
    translations: [
      { id: 'murray', name: 'A. T. Murray (Loeb, 1924–25)', short: 'Murray', slot: 'english', footnotes: true },
      { id: 'butler', name: 'Samuel Butler (1898)', short: 'Butler', slot: 'ross' },
      { id: 'pope', name: 'Alexander Pope (literary translation — alignment approximate), 1715–20', short: 'Pope', slot: 'third' },
    ],
    blurb: 'The wrath of Achilles and the war at Troy.',
    citation: { scheme: 'verse-line' },
    related: [{ id: 'odyssey', label: 'Odyssey' }],
  },
  {
    id: 'odyssey',
    title: 'Odyssey',
    greekTitle: 'Ὀδύσσεια',
    abbr: 'Od.',
    author: 'Homer',
    authorAbbr: 'Hom.',
    books: 24,
    bookLabels: BOOK_LABELS_24,
    greekEdition: 'Greek text of the Loeb edition (1919)',
    greekSource: PERSEUS_GREEK_SOURCE,
    translations: [
      { id: 'murray', name: 'A. T. Murray (Loeb, 1919)', short: 'Murray', slot: 'english', footnotes: true },
      { id: 'butler', name: 'Samuel Butler (1900)', short: 'Butler', slot: 'ross' },
      { id: 'pope', name: 'Alexander Pope (literary translation — alignment approximate), 1725–26', short: 'Pope', slot: 'third' },
    ],
    blurb: 'The long homecoming of Odysseus from Troy to Ithaca.',
    citation: { scheme: 'verse-line' },
    related: [{ id: 'iliad', label: 'Iliad' }],
  },
];

const BY_ID = new Map(WORKS.map((w) => [w.id, w]));

export function getWork(id: string): Work | undefined {
  return BY_ID.get(id);
}

export function bookLabel(work: Work, n: number): string {
  return work.bookLabels[n - 1] ?? String(n);
}

// A single-book work (every Plato work carried so far) is a single treatise
// with no book level, so it lives at /<work> with no /book/<n> subfolder, and
// the reader hides all book-level navigation.
export function isBookless(work: Work): boolean {
  return work.books === 1;
}

// The base-relative path to a work's READER (caller prepends BASE_URL). Every
// work — bookless or not — reads at /<work>/book/<n>; bookless works only ever
// have book 1. The bare /<work> slug is the work's landing page (workLanding).
// The single source of truth for reader URLs — used by the home index, work
// switcher, Bekker/Stephanus jump, search jumps, and cross-book outline links.
export function workPath(workId: string, book = 1): string {
  // Clamp to the work's real book range so a stale/overflow value (e.g. a
  // remembered book number for a work that is now bookless) can't 404.
  const w = BY_ID.get(workId);
  const max = w ? w.books : book;
  const b = Math.min(Math.max(1, book || 1), max);
  return `/${workId}/book/${b}`;
}

// The base-relative path to a work's LANDING page (caller prepends BASE_URL):
// the bare /<work> slug, an overview of the work that funnels into the reader.
export function workLanding(workId: string): string {
  return `/${workId}`;
}

// Translations visible in the current build. Private (copyright-encumbered)
// entries are already dropped from WORKS at compile time unless the build opted
// in (see SHOW_PRIVATE above); this filter is a runtime backstop.
// A non-Astro host (e.g. a future desktop app) can append runtime-registered
// translations — user imports, loaded from local files — via
// globalThis.__ARISTOTLE_EXTRA_TRANSLATIONS__ ({workId: TranslationRef[]});
// the site never sets it, so the static registry is unchanged there.
export function visibleTranslations(work: Work): TranslationRef[] {
  const extra = (globalThis as {
    __ARISTOTLE_EXTRA_TRANSLATIONS__?: Record<string, TranslationRef[]>;
  }).__ARISTOTLE_EXTRA_TRANSLATIONS__?.[work.id] ?? [];
  return work.translations.filter(t => !t.private || SHOW_PRIVATE).concat(extra);
}

// ---------------------------------------------------------------------------
// "In print" — copyright-encumbered modern translations and commentaries we
// can't host but want to point readers to, shown on each work's landing page.
// This is curated, additive metadata: a work with no entry simply omits the
// section. Each item is a citation plus an optional direct `url`; when `url` is
// absent the landing renders a Google Books search for the citation, so a link
// always resolves and we never fabricate a product page.
//
// Empty for this rollout — no modern Plato translations/commentaries have
// been curated yet (the Aristotle-specific catalogue this replaced is gone
// along with those works). Populate per-work as John curates them.

export interface FurtherReadingItem {
  // 'translation'/'commentary' = modern, copyright-protected works we can't host.
  // 'collection' = an in-print physical edition that CONTAINS the translation we
  // do host (e.g. a Loeb volume), for readers who want a paper copy of what
  // they're reading here.
  kind: 'translation' | 'commentary' | 'collection';
  cite: string;     // full citation, e.g. "Christopher Rowe (Penguin, 2005)"
  url?: string;     // optional direct purchase/publisher link; else Books search
}

// Citations may use <em>…</em> around the work's title (rendered as italics on
// the landing; stripped for the Google Books search link in inPrintHref).
const FURTHER_READING: Record<string, FurtherReadingItem[]> = {};

export function furtherReading(workId: string): FurtherReadingItem[] {
  return FURTHER_READING[workId] ?? [];
}

// A link that always resolves to where the cited edition can be found/bought.
// The cite may carry <em> title markup, so strip tags before building the query.
export function inPrintHref(item: FurtherReadingItem): string {
  const plain = item.cite.replace(/<[^>]+>/g, '');
  return item.url ?? `https://www.google.com/search?tbm=bks&q=${encodeURIComponent(plain)}`;
}

// ---------------------------------------------------------------------------
// "Resources" — external study aids relevant to a specific work, shown on the
// landing page. Curated, additive metadata like FURTHER_READING: a work with
// no entry simply omits the section. Empty for this rollout (the Aristotle
// logic-exercise catalogue this replaced doesn't apply to Plato).

export interface ResourceItem {
  label: string;         // resource name
  url: string;
  blurb: string;         // one line describing the resource
  authorName: string;
  authorUrl: string;
  exercises?: string;    // exercise set(s) within the resource keyed to this work
}

const RESOURCES: Record<string, ResourceItem[]> = {};

export function resourcesFor(workId: string): ResourceItem[] {
  return RESOURCES[workId] ?? [];
}

// ---------------------------------------------------------------------------
// Home-page taxonomy. The nine Thrasyllan tetralogies grouped the corpus by
// original publication set — accurate ancient history, but "too inside
// baseball" for a first-time reader (John's call 2026-07-11): nobody browsing
// for something to read thinks in tetralogies. SHELVES replaces that grouping
// with six thematic "reading paths" a newcomer would recognise (the trial and
// death of Socrates, the search for definitions, and so on). WITHIN each
// shelf, works stay in Thrasyllan (TLG-number) order — scholars will notice
// that continuity; nobody else has to. A `ShelfWork` is either an existing
// work (`id`, resolved against WORKS) or a not-yet-added work shown as a
// "coming soon" placeholder (`title` only) — unused so far; the works missing
// from this rollout are called out with a TODO comment instead (see WORKS
// above), since none of them are meant to display as a placeholder card yet.
// Every one of the 36 WORKS entries appears in exactly one shelf — verified in
// shared/__tests__/works.test.ts.

export interface ShelfWork {
  id?: string;      // an existing work (in WORKS) — clickable
  title?: string;   // a planned work — greyed-out placeholder
}

export interface Shelf {
  numeral: string;  // '1'–'6', a plain ordinal — the shelf TITLE is what should read prominently
  title: string;    // 'The Trial and Death of Socrates'
  works: ShelfWork[];
}

export const SHELVES: Shelf[] = [
  { numeral: '1', title: 'The Epics', works: [{ id: 'iliad' }, { id: 'odyssey' }] },
];

// "Start here" — a curated front-table strip of six approachable works for
// newcomers, rendered as a featured band ABOVE the SHELVES on the home page
// (John's call 2026-07-11, Option 3). These six also keep their normal place
// in their thematic shelf below: this is an additive pointer, not a seventh
// division, so the "every work exactly once" invariant is checked against
// SHELVES only. Every id here must resolve to a real WORKS entry — verified
// in shared/__tests__/works.test.ts.
export const START_HERE: string[] = ['iliad', 'odyssey'];

// A named group of works for the search "works to include" selector: one entry
// per home-page shelf, in home-page order, holding only the existing works
// (placeholders dropped).
export interface WorkGroup {
  ref: string;    // '1'–'6' (the shelf numeral)
  label: string;  // the shelf's title
  ids: string[];  // existing work ids in this group, in order
}

export const WORK_GROUPS: WorkGroup[] = (() => {
  const groups: WorkGroup[] = [];
  const ids = (ws: ShelfWork[]) => ws.filter(w => w.id && BY_ID.has(w.id)).map(w => w.id!);
  for (const shelf of SHELVES) {
    const g = ids(shelf.works);
    if (g.length) groups.push({ ref: shelf.numeral, label: shelf.title, ids: g });
  }
  return groups;
})();

// Cross-work ordering for search results, matching the home page's SHELVES
// flatten order (which differs from the raw WORKS/corpus order). Any real work
// not referenced by SHELVES is appended in WORKS order so every searchable
// work has a defined index.
export const WORK_ORDER: Map<string, number> = (() => {
  const order: string[] = [];
  for (const g of WORK_GROUPS) for (const id of g.ids) order.push(id);
  for (const w of WORKS) if (!order.includes(w.id)) order.push(w.id);
  return new Map(order.map((id, i) => [id, i]));
})();
