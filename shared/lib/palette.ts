// Matching logic for the ⌘K command palette — pure functions so the ranking
// is unit-testable without mounting the component. The palette accepts three
// kinds of input: a Stephanus citation (jump within the current work — parsed
// by the work's own citation scheme, see ./citation), a work name/abbreviation
// (open that work, resuming its saved position), or Greek (lemma lookup).
// Everything else falls through to corpus search.

import { GREEK_BOOK_LETTERS, WORKS, type Work } from './works';
import { greekFold } from './greek-fold';
import type { LemmaRef } from './data';
import { parseVerseCitation, type VerseCitation } from './citation';

export function hasGreek(q: string): boolean {
  return /[Ͱ-Ͽἀ-῿]/.test(q);
}

// Rank works for a query: exact abbr/id first, then title-prefix, word-start,
// abbr/id-prefix, and finally any substring; alphabetical within a tier. Abbr
// and id match case-insensitively ("rep" → Republic via id, "phdr" → Phaedrus
// via abbr). Plato abbreviations carry a trailing dot ("Ap.", "Phd."), so the
// abbr is compared with any trailing punctuation stripped.
export function rankWorks(q: string, works: readonly Work[] = WORKS, limit = 6): Work[] {
  const needle = q.trim().toLowerCase();
  if (!needle) return [];
  const tier = (w: Work): number => {
    const title = w.title.toLowerCase();
    const abbr = w.abbr.toLowerCase().replace(/[.\s]+$/, '');
    const id = w.id.toLowerCase();
    if (abbr === needle || id === needle) return 0;
    if (title.startsWith(needle)) return 1;
    // Word-start match inside the title ("laws" → the Laws; "sophist" → Sophist).
    if (title.includes(` ${needle}`)) return 2;
    if (abbr.startsWith(needle) || id.startsWith(needle)) return 3;
    if (title.includes(needle)) return 4;
    return -1;
  };
  return works
    .map((w) => ({ w, t: tier(w) }))
    .filter((x) => x.t >= 0)
    .sort((a, b) => a.t - b.t || a.w.title.localeCompare(b.w.title))
    .slice(0, limit)
    .map((x) => x.w);
}

export interface BookResult {
  work: Work;
  book: number;
  greekLetter: string;
  label: string;
  hay: string;
}

// The approved reader palette indexes every book, rather than just a work's
// landing page. Its deliberately simple substring ranking mirrors the mock:
// citation first (in the component), then book matches in canonical epic order.
export function rankBooks(q: string, works: readonly Work[] = WORKS, limit = 12): BookResult[] {
  const needle = q.trim().toLowerCase();
  const index: BookResult[] = [];
  for (const work of works) {
    for (let book = 1; book <= work.books; book++) {
      const letter = (GREEK_BOOK_LETTERS[book - 1] ?? String(book));
      const greekLetter = work.id === 'odyssey' ? letter.toLowerCase() : letter;
      const label = `${work.title} · Book ${work.bookLabels[book - 1] ?? book} (${greekLetter})`;
      index.push({
        work,
        book,
        greekLetter,
        label,
        hay: `${work.id} ${work.title} book ${book} ${greekLetter}`.toLowerCase(),
      });
    }
  }
  return (needle ? index.filter((item) => item.hay.includes(needle)) : index).slice(0, limit);
}

// Rank lemmata for a Greek query: fold-prefix matches on the headword,
// most frequent first.
export function rankLemmata(
  q: string,
  lemmata: Record<string, LemmaRef>,
  limit = 5,
): LemmaRef[] {
  const needle = greekFold(q.trim());
  if (!needle) return [];
  const out: LemmaRef[] = [];
  for (const ref of Object.values(lemmata)) {
    if (greekFold(ref.head).startsWith(needle)) out.push(ref);
  }
  return out.sort((a, b) => b.count - a.count).slice(0, limit);
}

// ── Site-wide Go-to (round 3) ───────────────────────────────────────────────
// The palette is the one finder on every page: a citation, a book, a page of
// the site, a place, a character, or a Greek word. Everything below is pure,
// so the ranking is tested without mounting the component.


/** Every reading of a typed citation, best first. A work prefix ("Il. 6.237")
 * names one poem. A bare "6.237" reads in the poem that is open, then in the
 * other; with no poem open (the home page, a reference page) it reads in each
 * poem in canonical order. The grammar is parseVerseCitation's own: this only
 * decides which poems to ask it about. */
export function verseCitations(raw: string, currentWork?: string | null): VerseCitation[] {
  const out: VerseCitation[] = [];
  const add = (c: VerseCitation | null) => {
    if (c && !out.some((o) => o.work === c.work && o.book === c.book && o.line === c.line)) out.push(c);
  };
  add(parseVerseCitation(raw, currentWork ?? undefined));
  for (const w of WORKS) {
    if (w.citation?.scheme === 'verse-line') add(parseVerseCitation(raw, w.id));
  }
  return out;
}

export type SiteEntryKind = 'Page' | 'Place' | 'Character' | 'Word';
export interface SiteEntry {
  kind: SiteEntryKind;
  /** What the row shows: an English name, or a Greek headword. */
  label: string;
  /** A second, quieter name beside it (the Greek of a place or person). */
  greek?: string;
  /** Path under the site base, with its anchor: "/places/#place-ithaca". */
  path: string;
  /** Extra words the entry answers to, lowercase. */
  also?: string[];
  /** How often the name occurs in the poems (see withMentions): the tiebreak
   * between two names a query matches equally well. */
  mentions?: number;
}

/** The pages of the site a reader may want by name. Paths are the header's. */
export const SITE_PAGES: SiteEntry[] = [
  { kind: 'Page', label: 'Maps', path: '/maps/', also: ['atlas', 'map'] },
  { kind: 'Page', label: 'Places', path: '/places/', also: ['gazetteer'] },
  { kind: 'Page', label: 'Timeline', path: '/timeline/', also: ['calendar', 'days'] },
  { kind: 'Page', label: 'Characters', path: '/characters/', also: ['people', 'roster'] },
  { kind: 'Page', label: 'Genealogies', path: '/genealogies/', also: ['family trees', 'houses'] },
  { kind: 'Page', label: 'Vocabulary', path: '/vocabulary/', also: ['words'] },
  { kind: 'Page', label: 'Formulas', path: '/formulas/', also: ['epithets'] },
  { kind: 'Page', label: 'Repetitions', path: '/repetitions/', also: ['repeated lines'] },
  { kind: 'Page', label: 'Phrases', path: '/phrases/' },
  { kind: 'Page', label: 'Lexicon', path: '/lemma/', also: ['dictionary', 'greek words'] },
  { kind: 'Page', label: 'Search', path: '/search' },
  { kind: 'Page', label: 'Advanced search', path: '/advanced' },
  { kind: 'Page', label: 'About', path: '/about' },
];

interface NamedPlace { id: string; name: string; greek?: string; mentions?: readonly unknown[] }
interface NamedCharacter { id: string; name: string; greek?: string }

/** Places and characters as palette entries. The anchors are the ones their
 * pages render: /places/ gives every entry id="place-<id>", /characters/
 * id="roster-<id>". */
export function nameEntries(places: readonly NamedPlace[], characters: readonly NamedCharacter[]): SiteEntry[] {
  return [
    ...characters.map((c): SiteEntry => ({ kind: 'Character', label: c.name, greek: c.greek, path: `/characters/#roster-${c.id}` })),
    ...places.map((p): SiteEntry => ({
      kind: 'Place', label: p.name, greek: p.greek, path: `/places/#place-${p.id}`,
      ...(p.mentions?.length ? { mentions: p.mentions.length } : {}),
    })),
  ];
}

/** The lexicon's occurrence counts by folded headword (Ἕκτωρ: 454). */
export function headwordCounts(lemmata: Record<string, LemmaRef>): Map<string, number> {
  const out = new Map<string, number>();
  for (const ref of Object.values(lemmata)) {
    const key = greekFold(ref.head);
    if (key && ref.count > (out.get(key) ?? 0)) out.set(key, ref.count);
  }
  return out;
}

/** Give each character the count of its Greek name as a headword. Only a
 * one-word name is looked up (Αἴας Τελαμώνιος is not Αἴας alone), and only a
 * character's: a place called τεῖχος is not every wall in the poems, and
 * keeps its own list of mentions. */
export function withMentions(entries: readonly SiteEntry[], counts: ReadonlyMap<string, number>): SiteEntry[] {
  return entries.map((e) => {
    const g = e.kind === 'Character' ? e.greek?.trim() : undefined;
    const n = g && !/\s/.test(g) ? counts.get(greekFold(g)) : undefined;
    return n ? { ...e, mentions: n } : e;
  });
}

const plain = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

/** Rank named entries for a query: the whole name, then a name that starts
 * with it, then a word inside the name (or an alias) that does. Two letters
 * match too many of 270 places to mean anything, so a query under three
 * letters only finds a name it spells in full. A Greek query matches the
 * Greek name, accents and breathings ignored. Within a tier a page of the
 * site comes first, then the name the poems use more often (Hector before
 * Hecuba for "hec"), then the order given (characters, then places). */
export function rankNames(q: string, entries: readonly SiteEntry[], limit = 6): SiteEntry[] {
  const greek = hasGreek(q);
  const needle = greek ? greekFold(q.trim()) : plain(q.trim());
  if (!needle) return [];
  const tier = (e: SiteEntry): number => {
    if (greek) {
      const g = e.greek ? greekFold(e.greek) : '';
      if (!g) return -1;
      return g === needle ? 0 : g.startsWith(needle) ? 1 : -1;
    }
    const name = plain(e.label);
    if (name === needle || e.also?.includes(needle)) return 0;
    if (needle.length < 3) return -1;
    if (name.startsWith(needle)) return 1;
    if (name.includes(` ${needle}`) || e.also?.some((a) => a.startsWith(needle) || a.includes(` ${needle}`))) return 2;
    return -1;
  };
  return entries
    .map((e, i) => ({ e, i, t: tier(e) }))
    .filter((x) => x.t >= 0)
    .sort((a, b) => a.t - b.t
      || Number(b.e.kind === 'Page') - Number(a.e.kind === 'Page')
      || (b.e.mentions ?? 0) - (a.e.mentions ?? 0)
      || a.i - b.i)
    .slice(0, limit)
    .map((x) => x.e);
}

/** Lemmata for a query typed in Latin letters, by the transliterated slug a
 * lemma page is served at ("menis" finds μῆνις): the slug itself first, then
 * slugs that start with it, most frequent first. Three letters at least. */
export function rankLemmaSlugs(q: string, lemmata: Record<string, LemmaRef>, limit = 3): LemmaRef[] {
  const needle = plain(q.trim());
  if (needle.length < 3 || !/^[a-z]+$/.test(needle)) return [];
  const out: LemmaRef[] = [];
  for (const ref of Object.values(lemmata)) if (ref.slug.startsWith(needle)) out.push(ref);
  return out
    .sort((a, b) => Number(b.slug === needle) - Number(a.slug === needle) || b.count - a.count)
    .slice(0, limit);
}

/** Where the full-text search opens for a query the palette could not place:
 * search.astro reads ?q= and sends Greek script to the Greek box, anything
 * else to the English one. */
export function searchPath(q: string): string {
  const t = q.trim();
  return t ? `/search?q=${encodeURIComponent(t)}` : '/search';
}
