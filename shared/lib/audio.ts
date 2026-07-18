// David Chamberlain's public-domain recitation audio (apparatus/audio/manifest.json,
// see shared/lib/data.ts's fetchAudioManifest) — hotlinked archive.org MP3 chunks,
// NEVER vendored into the corpus (CLAUDE.md's hard rules). Pure functions only:
// chunk lookup for a given line (honoring the Iliad 6 revision-set preference and
// recorded gaps) and license-label formatting. No DOM, no fetch.
//
// Coverage is honest and partial: Iliad 1-24 (with a handful of small recorded
// gaps per book), Odyssey 1-7 only. A work/book absent from `works` (e.g. every
// Odyssey book past 7) simply has no audio — callers must treat "no entry" the
// same as "no chunks", never as an error.

export interface AudioChunk {
  file: string;
  format: string;
  url: string;
  lines: [number, number];
}

export interface AudioBookEntry {
  item: string;
  licenseurl: string;
  chunks: AudioChunk[];
  gaps?: [number, number][];
}

export interface AudioManifest {
  status: string;
  source: { creator: string; statement_url: string; license_note: string };
  works: Record<string, Record<string, AudioBookEntry>>;
}

// A chunk whose filename marks it as a REVISION recording of the same lines
// (observed today only on Iliad 6 — "Iliad6_R37-118.mp3" beside
// "Iliad6_37-65.mp3"/"Iliad6_66-118.mp3": two overlapping recording passes.
// John's call: always prefer the revision). Detected by filename pattern, not
// hardcoded to book 6, so any future book with a revision pass degrades the
// same honest way.
export function isRevisionChunk(file: string): boolean {
  return /_R\d/.test(file);
}

// A book/work entry from the manifest, or undefined if the work or book isn't
// covered at all.
export function bookAudio(
  manifest: AudioManifest | null | undefined,
  work: string,
  book: number,
): AudioBookEntry | undefined {
  return manifest?.works?.[work]?.[String(book)];
}

// Whether a work/book has ANY audio coverage — gates the Settings "Audio"
// toggle's visibility (hidden entirely for e.g. Od. 8-24, which the manifest
// simply doesn't mention).
export function hasAudio(
  manifest: AudioManifest | null | undefined,
  work: string,
  book: number,
): boolean {
  const entry = bookAudio(manifest, work, book);
  return !!entry && entry.chunks.length > 0;
}

// Whether a line falls inside a recorded gap (a real hole in an otherwise-
// covered book — a skipped/omitted span; see the manifest's `gaps`).
export function lineInGap(entry: AudioBookEntry | undefined, line: number): boolean {
  if (!entry?.gaps) return false;
  return entry.gaps.some(([lo, hi]) => line >= lo && line <= hi);
}

// The chunk that plays a given line, honoring the revision preference and gap
// exclusion. Returns null when the line has no audio: beyond the book's
// recorded coverage, inside a gap, or the book/work isn't in the manifest at
// all. NEVER guesses — an honest absence, never an implied one.
export function chunkForLine(entry: AudioBookEntry | undefined, line: number): AudioChunk | null {
  if (!entry || lineInGap(entry, line)) return null;
  const candidates = entry.chunks.filter((c) => line >= c.lines[0] && line <= c.lines[1]);
  if (!candidates.length) return null;
  const revisions = candidates.filter((c) => isRevisionChunk(c.file));
  const pool = revisions.length ? revisions : candidates;
  // Prefer the narrowest (most specific) matching range; ties keep manifest order.
  return pool.reduce((best, c) => {
    const width = c.lines[1] - c.lines[0];
    const bestWidth = best.lines[1] - best.lines[0];
    return width < bestWidth ? c : best;
  });
}

// Every chunk that actually plays within a book, in reading order, after the
// revision preference is applied — the set the reader paints a play
// affordance for at each chunk's start line. A base-set chunk is dropped only
// when its ENTIRE range is covered by some revision chunk; a revision that
// only partly overlaps still lets the uncovered part of the base chunk keep
// its own affordance (built on chunkForLine's line-honest lookup, so the
// affordance list can't silently claim coverage a click-through wouldn't
// back up — not observed in the current manifest, where Iliad 6's revision
// set fully re-covers 1-529, but the logic doesn't assume that).
export function effectiveChunks(entry: AudioBookEntry | undefined): AudioChunk[] {
  if (!entry) return [];
  const revisions = entry.chunks.filter((c) => isRevisionChunk(c.file));
  const base = entry.chunks.filter((c) => !isRevisionChunk(c.file));
  if (!revisions.length) return [...base].sort((a, b) => a.lines[0] - b.lines[0]);
  const keptBase = base.filter(
    (b) => !revisions.some((r) => r.lines[0] <= b.lines[0] && r.lines[1] >= b.lines[1]),
  );
  return [...revisions, ...keptBase].sort((a, b) => a.lines[0] - b.lines[0]);
}

// CC BY 3.0 vs 4.0 label from a chunk's item licenseurl
// ("http://creativecommons.org/licenses/by/4.0/" -> "CC BY 4.0"). Falls back
// to a plain "CC license" if the URL doesn't match the expected CC shape —
// never silently mislabels a license.
export function licenseLabel(licenseurl: string): string {
  const m = licenseurl.match(/\/licenses\/([a-z-]+)\/([\d.]+)\/?$/i);
  if (!m) return 'CC license';
  const [, family, version] = m;
  return `CC ${family.toUpperCase()} ${version}`;
}

// "Play lines 1-100, read by David Chamberlain" — the accessible label for a
// chunk's play affordance.
export function chunkAriaLabel(chunk: AudioChunk, creator: string): string {
  return `Play lines ${chunk.lines[0]}–${chunk.lines[1]}, read by ${creator}`;
}

// The archive.org item page URL for a book entry's `item` id.
export function itemPageUrl(item: string): string {
  return `https://archive.org/details/${item}`;
}
