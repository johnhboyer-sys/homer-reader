// Citation-scheme contract — the frontend twin of the pipeline's
// pipeline/homer_pipeline/scheme.py. A *citation scheme* is the reference
// system a work is cited by: Bekker pages for Aristotle ("1094a15"), Busse/CAG
// pages for Porphyry's Isagoge ("1a5" — synthetic single-side pages), or
// Stephanus pages for Plato ("17a"). Every scheme-conditional in the reader
// should dispatch on the `CitationScheme` returned by `schemeFor(work)`
// instead of scattering `=== 'busse'` / `=== 'stephanus'` string tests.
//
// Two distinct grammars matter, and this module deliberately keeps them
// separate:
//
//   * a CITATION string — the form a scholar writes/copies: column and line
//     run together with no separator ("1097a15"), or just the column when the
//     scheme has no user-facing lines ("17a"). `formatCitation` produces this;
//     it's what the scroll-spy hash, copy-citation, and resume storage show.
//   * a LOCATION string — the `?loc=` query grammar: a column, optionally
//     followed by `:` and a line ("1097a:15" or "17a:12"). This is a routing
//     detail, not something a reader is meant to read as a citation, so it
//     keeps the line internally (DOM anchors still need it to scroll to an
//     exact Greek line) even for a lineless scheme. `parseLocation` reads
//     this grammar; nothing in this module composes it with a line for a
//     lineless scheme, because nothing upstream can ever hand one a line for
//     one (see `hasUserFacingLines` below).
//
// The known reader bug this replaces: splitting `?loc=` on ':' unconditionally
// produced `L17a-undefined` for a column-only value. `parseLocation` always
// returns a `line` of `null` rather than `NaN`/`undefined` when none is given,
// so a caller can branch on `line == null` to target the column-level anchor
// instead of a garbled line-level one.

import { getWork, WORKS } from './works';

export type SchemeId = 'bekker' | 'busse' | 'stephanus' | 'verse-line';

export interface ParsedLocation {
  column: string;
  line: number | null;
}

export interface CitationScheme {
  readonly id: SchemeId;
  // Bare-column token grammar shared by every scheme (mirrors scheme.py's
  // `_COLUMN_RE` — Bekker's real sides are a/b and Busse's is a-only, but the
  // grammar itself accepts a-e for all three so one regex serves them all;
  // real membership is enforced by the columns.json lookup, not this regex).
  readonly columnRegex: RegExp;
  // Whether individual line numbers within a column are meaningful,
  // user-facing citation targets. False only for stephanus — Plato is cited
  // page+letter only; lines exist in the underlying TEI but are editorial.
  readonly hasUserFacingLines: boolean;
  // Placeholder text for a citation-jump input box.
  readonly jumpPlaceholder: string;
  // Human label for the jump box / error copy ("Bekker citation", "Stephanus page").
  readonly label: string;
  // Parse + normalize a bare column token ("34b", "1097A" -> "1097a"). Returns
  // null if it doesn't match this scheme's column grammar.
  parseColumnToken(raw: string): string | null;
  // Parse a `?loc=` value: a bare column, or column + line joined by ':' or
  // (for backward compatibility with hand-typed Bekker citations) run
  // together with an optional space/dot separator ("1097a15", "1097a.15").
  // A line component on a scheme with no user-facing lines is invalid input
  // (there is no such thing as "line 12 of Stephanus page 34b"), not a value
  // to silently drop — this rejects rather than truncates it.
  parseLocation(raw: string): ParsedLocation | null;
  // Render the citation string a reader sees: "1097a15" (line given, scheme
  // has lines), "1097a" (no line, or a lineless scheme where `line` is
  // ignored regardless of what's passed).
  formatCitation(column: string, line?: number | null): string;
}

// Shared column/ref grammar (mirrors scheme.py's `_COLUMN_RE` / `_REF_RE`):
// digits + a single letter a-e, optionally followed by a line number.
const COLUMN_RE = /^(\d+)([a-e])$/;
const REF_RE = /^(\d+)([a-e])\.?(\d+)$/;

function normalize(raw: string): string {
  return raw.trim().toLowerCase().replace(/\s+/g, '');
}

function makeScheme(
  id: SchemeId,
  hasUserFacingLines: boolean,
  jumpPlaceholder: string,
  label: string,
): CitationScheme {
  function parseColumnToken(raw: string): string | null {
    const norm = normalize(raw);
    return COLUMN_RE.test(norm) ? norm : null;
  }

  function parseLocation(raw: string): ParsedLocation | null {
    const norm = normalize(raw);
    if (!norm) return null;

    // Bare column, e.g. "17a" or "1097a" — valid for every scheme.
    if (COLUMN_RE.test(norm)) return { column: norm, line: null };

    // "{column}:{line}" — the `?loc=` query grammar.
    const colon = norm.indexOf(':');
    if (colon !== -1) {
      const colPart = norm.slice(0, colon);
      const linePart = norm.slice(colon + 1);
      if (!COLUMN_RE.test(colPart) || !/^\d+$/.test(linePart)) return null;
      if (!hasUserFacingLines) return null; // no such thing as a lineless-scheme line
      return { column: colPart, line: Number(linePart) };
    }

    // Legacy concatenated citation form, e.g. "1097a15" / "1097a.15" — only
    // meaningful for a scheme with user-facing lines. For a lineless scheme
    // this is exactly the malformed "34b12" input that must be rejected, not
    // reinterpreted.
    if (!hasUserFacingLines) return null;
    const m = REF_RE.exec(norm);
    if (!m) return null;
    return { column: m[1] + m[2], line: Number(m[3]) };
  }

  function formatCitation(column: string, line?: number | null): string {
    if (hasUserFacingLines && line != null) return `${column}${line}`;
    return column;
  }

  return { id, columnRegex: COLUMN_RE, hasUserFacingLines, jumpPlaceholder, label, parseColumnToken, parseLocation, formatCitation };
}

// Verse-line (Homer) grammar. The container is a bare book number ("9"), a full
// citation joins book and line with a DOT ("9.366") — the vulgate lineation is
// sacred, so a line is a first-class, user-facing citation target. This differs
// from bekker's letter-bearing, separator-less column/line ("1097a15"), so the
// scheme carries its own factory rather than reusing makeScheme.
const BOOK_RE = /^(\d+)$/;
// A full ref: book + line joined by a dot (copy-citation "9.366") or a colon
// (the ?loc= query grammar "9:366"). No range grammar — the inherited citation
// machinery parses single locations only.
const VERSE_REF_RE = /^(\d+)[.:](\d+)$/;

function makeVerseScheme(id: SchemeId, jumpPlaceholder: string, label: string): CitationScheme {
  function parseColumnToken(raw: string): string | null {
    const norm = normalize(raw);
    return BOOK_RE.test(norm) ? norm : null;
  }
  function parseLocation(raw: string): ParsedLocation | null {
    const norm = normalize(raw);
    if (!norm) return null;
    if (BOOK_RE.test(norm)) return { column: norm, line: null }; // bare book
    const m = VERSE_REF_RE.exec(norm);
    return m ? { column: m[1], line: Number(m[2]) } : null;
  }
  function formatCitation(column: string, line?: number | null): string {
    return line != null ? `${column}.${line}` : column;
  }
  return { id, columnRegex: BOOK_RE, hasUserFacingLines: true, jumpPlaceholder, label, parseColumnToken, parseLocation, formatCitation };
}

const SCHEMES: Record<SchemeId, CitationScheme> = {
  bekker: makeScheme('bekker', true, 'e.g. 1097a15', 'Bekker citation'),
  busse: makeScheme('busse', true, 'e.g. 1a5', 'CAG citation'),
  stephanus: makeScheme('stephanus', false, 'e.g. 34b', 'Stephanus page'),
  'verse-line': makeVerseScheme('verse-line', 'e.g. Od. 9.366', 'verse citation'),
};

// The scheme for a scheme id; unknown/omitted defaults to bekker (matching
// scheme.py's `get(name)`).
export function scheme(id: SchemeId | string | null | undefined): CitationScheme {
  return (id && id in SCHEMES ? SCHEMES[id as SchemeId] : SCHEMES.bekker);
}

// The scheme a work is cited by — reads works.ts's `citation?.scheme`
// (default bekker), the same default the pipeline's `for_manifest` applies.
export function schemeFor(work: string): CitationScheme {
  return scheme(getWork(work)?.citation?.scheme);
}

// ── Convenience composers ──────────────────────────────────────────────────
// These aren't part of the per-scheme contract itself, but wrap it for the
// call sites that compose a citation/location string for a specific work
// (the scroll-spy hash, resume storage, copy-citation, and Search jump URLs).
// Reader.svelte and Search.svelte don't call these yet (that wiring is a
// later task) — they're here, exported and tested, for that task to use.

// The scroll-spy/resume/copy-citation string for a work's column (+ line):
// "1097a15" (bekker), "17a" (stephanus — line, if given, is dropped).
export function formatCite(work: string, column: string, line?: number | null): string {
  return schemeFor(work).formatCitation(column, line);
}

// The `#`-prefixed hash for `history.replaceState` / a shareable link.
export function formatHash(work: string, column: string, line?: number | null): string {
  return `#${formatCite(work, column, line)}`;
}

// The `loc=` query VALUE (not URL-encoded) for a jump-in link: "1097a:15" when
// the scheme has user-facing lines and a line is given, otherwise the bare
// column — so a stephanus Search-result link reads as a clean "?loc=17a"
// rather than a line-level citation a Plato reader never sees elsewhere.
export function formatLocValue(work: string, column: string, line?: number | null): string {
  const s = schemeFor(work);
  return s.hasUserFacingLines && line != null ? `${column}:${line}` : column;
}

// ── Verse-line (Homer) work-aware helpers ───────────────────────────────────
// The jump box and copy-citation for a verse work resolve/name the WORK itself
// (a "Od."/"Iliad" prefix, an author prefix in a copied citation), so they need
// the registry and live here rather than in the work-agnostic per-scheme
// contract above. The per-scheme parseLocation/formatCitation still handle the
// bare book.line grammar; these compose the work around it.

export interface VerseCitation {
  work: string;        // resolved work id
  book: number;
  line: number | null; // null ⇒ a whole-book reference
}

// Parse a verse jump-box query into {work, book, line}. Accepts an optional
// leading work reference — the work's abbr ("Od.", trailing dot optional) or its
// full title ("Iliad"), case-insensitive — then book and (optionally) line
// separated by a dot or whitespace: "Od. 9.366", "od 9 366", "Iliad 2.494", or
// a bare "9.366"/"9" read in `currentWork`'s context. The book is range-checked
// against the work's book count. Returns null on anything it can't resolve to a
// real verse-line work + valid book. Ranges ("1.1-7") are NOT parsed — the
// inherited citation machinery has no range grammar (parseLocation parses a
// single location), so a range falls through to null, matching bekker/stephanus.
export function parseVerseCitation(raw: string, currentWork?: string): VerseCitation | null {
  const s = raw.trim().toLowerCase();
  if (!s) return null;

  // Longest-token-first so a full title ("iliad") wins over a shorter abbr
  // ("il") that prefixes it. Tokens are registry strings (letters/dot only), so
  // plain startsWith matching avoids any dynamic-regex injection.
  const prefixes: { token: string; id: string }[] = [];
  for (const w of WORKS) {
    if (w.citation?.scheme !== 'verse-line') continue;
    prefixes.push({ token: w.abbr.toLowerCase().replace(/[.\s]+$/, ''), id: w.id });
    prefixes.push({ token: w.title.toLowerCase(), id: w.id });
  }
  prefixes.sort((a, b) => b.token.length - a.token.length);

  let workId = currentWork;
  let rest = s;
  for (const { token, id } of prefixes) {
    if (!s.startsWith(token)) continue;
    let i = token.length;
    if (s[i] === '.') i++;                       // "Od." — the abbr's own dot
    while (i < s.length && (s[i] === ' ' || s[i] === '.' || s[i] === '\t')) i++;
    if (i < s.length && s[i] >= '0' && s[i] <= '9') { workId = id; rest = s.slice(i); break; }
  }

  if (!workId) return null;
  const w = getWork(workId);
  if (!w || w.citation?.scheme !== 'verse-line') return null;

  const m = /^(\d+)(?:[.\s]+(\d+))?$/.exec(rest.trim());
  if (!m) return null;
  const book = Number(m[1]);
  if (book < 1 || book > w.books) return null;
  return { work: workId, book, line: m[2] != null ? Number(m[2]) : null };
}

// The reader-facing verse citation for a work: "Il. 1.1" / "Od. 9.366" (or a
// whole-book "Od. 9" when no line). This is the inverse of parseVerseCitation.
export function formatVerseCitation(work: string, book: number, line?: number | null): string {
  const abbr = getWork(work)?.abbr ?? '';
  const bl = line != null ? `${book}.${line}` : String(book);
  return abbr ? `${abbr} ${bl}` : bl;
}

// The Copy-Citation string: author abbr + work + book.line, with the active
// translator appended when an English translation is showing. Greek-only view
// passes no translationName → "Hom. Il. 1.1"; bilingual passes it →
// "Hom. Il. 1.1, trans. Murray".
export function formatCopyCitation(
  work: string,
  book: number,
  line: number | null,
  translationName?: string | null,
): string {
  const author = getWork(work)?.authorAbbr;
  const base = `${author ? `${author} ` : ''}${formatVerseCitation(work, book, line)}`;
  return translationName ? `${base}, trans. ${translationName}` : base;
}
