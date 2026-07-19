// Day-strip data derivation for /timeline/ — pure functions over the emitted
// scenes apparatus (build/dist/{work}/book-NN.json's apparatus.scenes), which
// carry a `dayNumber` (or null for undated/transitional scenes) per Book.
//
// The vulgate day-count is DERIVED, not hand-maintained: a book's dayNumbers
// are read off the emitted scenes, so a re-emit that shifts the calendar
// (a pipeline gotcha this repo has hit before — see CLAUDE.md) reflows the
// strip automatically rather than silently drifting from a hardcoded table.
//
// A day strip is a flat, reading-order sequence of two entry kinds:
//   - 'day': a single dramatized day, anchored at the first scene carrying
//     that dayNumber.
//   - 'span': a summarized/compressed interval between two dated scenes (or
//     trailing past the last one, per the book's own day RANGE) where the
//     poem narrates several days in a handful of lines — Il. 1's nine-day
//     plague, its twelve-day divine absence, and so on. `spanDays` is the
//     count of calendar days the span covers; a null `fromDay`/`toDay` marks
//     an open end (the poem doesn't narrate to a stated terminus — see Il.
//     24's truce, which the poem sets up rhetorically but never finishes
//     narrating: docs/research/chronology-iliad.md).
//
// Both epics' compressed spans (Il.'s four framing intervals, Od. Book 5's
// raft/sailing/adrift trio) fall out of this one algorithm — no per-epic
// special-casing lives here. Curated overlay content (the Od. Day-34 telling
// inset, bibliography quotes) is the Astro page's job, not this module's.

export interface SceneInput {
  lines: number[];
  dayNumber: number | null;
  summary?: string;
}

export interface BookInput {
  book: number;
  // Book-level day range, e.g. apparatus.day "40-51" parsed to [40, 51].
  // Used only to close a trailing span past the last dated scene (Il. 24's
  // truce, narrated rhetorically to day 51 but not scened that far) — null
  // when the book carries no day field.
  dayRange: [number, number] | null;
  scenes: SceneInput[];
}

export interface DayEntry {
  kind: 'day';
  dayNumber: number;
  book: number;
  line: number;
}

export interface SpanEntry {
  kind: 'span';
  fromDay: number | null;
  toDay: number | null;
  spanDays: number;
  book: number;
  line: number;
  summary?: string;
}

export type DayStripEntry = DayEntry | SpanEntry;

export interface BookRange {
  book: number;
  // Index range into `entries`, inclusive-exclusive, of entries anchored in
  // this book (a trailing span anchored in book N's own final scene belongs
  // to N even though it may extend past N's stated day range).
  startIndex: number;
  endIndex: number;
}

export interface DayStrip {
  entries: DayStripEntry[];
  bookRanges: BookRange[];
}

// Walk a work's books in order, collapsing same-day scenes into one 'day'
// entry (first occurrence anchors it) and turning any jump between two
// dated scenes — or a book's stated day range extending past its last dated
// scene — into a 'span'. Scenes whose dayNumber matches the running day, or
// sits between two adjacent (diff-by-1) dated scenes, are connective
// narration folded into the surrounding day rather than surfaced.
export function buildDayStrip(books: BookInput[]): DayStrip {
  const entries: DayStripEntry[] = [];
  const bookRanges: BookRange[] = [];
  let lastDay: number | null = null;
  // The most recent scene seen with dayNumber === null since the last dated
  // scene — the natural anchor/summary source for a span that turns out to
  // bridge a gap.
  let pendingNull: { book: number; line: number; summary?: string } | null = null;

  for (const b of books) {
    const startIndex = entries.length;
    for (const scene of b.scenes) {
      const line = scene.lines[0];
      if (scene.dayNumber == null) {
        pendingNull = { book: b.book, line, summary: scene.summary };
        continue;
      }
      const d = scene.dayNumber;
      if (lastDay == null) {
        entries.push({ kind: 'day', dayNumber: d, book: b.book, line });
      } else if (d !== lastDay) {
        // A gap only ever means something moving FORWARD (d > lastDay + 1);
        // a decreasing dayNumber is an out-of-order/analepsis case this
        // module doesn't interpret further — it's recorded as its own day
        // entry with no fabricated backward span, and left to the caller.
        if (d > lastDay + 1) {
          const anchor = pendingNull ?? { book: b.book, line };
          entries.push({
            kind: 'span',
            fromDay: lastDay,
            toDay: d,
            spanDays: d - lastDay - 1,
            book: anchor.book,
            line: anchor.line,
            summary: anchor.summary,
          });
        }
        entries.push({ kind: 'day', dayNumber: d, book: b.book, line });
      }
      lastDay = d;
      pendingNull = null;
    }

    // Close a trailing span implied by this book's own day range (Il. 24:
    // last dated scene is day 41, but the book's range runs to 51 — the
    // poem's nine-days-wood-then-cremation close, told but not day-scened).
    if (b.dayRange && lastDay != null && b.dayRange[1] > lastDay) {
      const anchor = pendingNull ?? { book: b.book, line: b.scenes.at(-1)?.lines[0] ?? 0 };
      entries.push({
        kind: 'span',
        fromDay: lastDay,
        toDay: null,
        spanDays: b.dayRange[1] - lastDay,
        book: anchor.book,
        line: anchor.line,
        summary: anchor.summary,
      });
      lastDay = b.dayRange[1];
      pendingNull = null;
    }

    bookRanges.push({ book: b.book, startIndex, endIndex: entries.length });
  }

  return { entries, bookRanges };
}

// Parse an apparatus.day field ("1-21", "22", or absent) into a [min, max]
// range, or null. Mirrors the pipeline's own day-field grammar; a malformed
// or missing field degrades to null rather than throwing, since the day
// strip is best-effort apparatus, not a hard data contract.
export function parseDayRange(day: string | null | undefined): [number, number] | null {
  if (!day) return null;
  const m = /^(\d+)(?:-(\d+))?$/.exec(day.trim());
  if (!m) return null;
  const lo = Number(m[1]);
  const hi = m[2] != null ? Number(m[2]) : lo;
  return [lo, hi];
}

// Total calendar-day span covered by a strip, for a simple "N days" header
// stat: the last 'day' entry's dayNumber, or an open span's toDay-less
// spanDays folded onto its fromDay.
export function totalDays(strip: DayStrip): number {
  let max = 0;
  for (const e of strip.entries) {
    if (e.kind === 'day') max = Math.max(max, e.dayNumber);
    else if (e.toDay != null) max = Math.max(max, e.toDay);
    else if (e.fromDay != null) max = Math.max(max, e.fromDay + e.spanDays);
  }
  return max;
}

// ── Voyage strip (Troy -> Ithaca, the ten wandering years) ─────────────────
// A second, year-scale strip layered onto apparatus/voyage-chronology.json's
// ordered stations (see that file's header for sourcing). Unlike the day
// strip, this one has no calendar to derive from -- the poem states some
// intervals in round numbers (ἐννῆμαρ, μῆνα, ἐνιαυτός, ἑπτάετες...) and is
// silent on the rest. buildVoyageStrip turns that curated station list into
// a flat, ordered sequence of 'stated' (sized to a real duration) and
// 'unstated' (the poem gives no number; rendered as a narrow hatched gap by
// the caller, not sized to any invented length) entries -- structurally the
// same 'known span' / 'honest gap' split as the day strip's day/span split,
// just at year scale instead of day scale.

export type VoyageUnit = 'day' | 'days' | 'night' | 'month' | 'months' | 'year' | 'years';

export interface VoyageDuration {
  value: number;
  unit: VoyageUnit;
  // The Greek anchor word/phrase for a stated duration (e.g. "ἐννῆμαρ"), or
  // null when the duration is inferred from narrative framing rather than a
  // counted numeral in the text (e.g. the Scheria -> Ithaca "one night").
  greek: string | null;
  cite: string;
  // True when the duration is read off narrative framing (sunset-to-dawn)
  // rather than an explicit counting word.
  approximate?: boolean;
  label?: string;
}

export interface VoyageRef {
  work: string;
  book: number;
  lines: [number, number];
}

export interface VoyageStationInput {
  id: string;
  placeId: string | null;
  label: string;
  kind: 'start' | 'stop' | 'digression' | 'end';
  unlocatable?: boolean;
  refs: VoyageRef[];
  // The duration associated with reaching/leaving this station (travel time
  // or a hospitality/captivity stay -- whichever the poem actually states).
  duration: VoyageDuration | null;
  // A second stated duration for the rare station that carries both (Ogygia:
  // nine days adrift arriving, then seven years kept).
  stayDuration?: VoyageDuration | null;
  note?: string;
}

export interface VoyageStripEntry {
  kind: 'stated' | 'unstated';
  stationId: string;
  label: string;
  // Day-equivalent length for width sizing (0 for 'unstated' -- the caller
  // draws a fixed narrow hatched gap, never a fabricated width).
  days: number;
  duration: VoyageDuration | null;
  refs: VoyageRef[];
  note?: string;
  unlocatable: boolean;
}

export interface VoyageStrip {
  entries: VoyageStripEntry[];
  totalStatedDays: number;
}

const VOYAGE_DAYS_PER_UNIT: Record<VoyageUnit, number> = {
  day: 1,
  days: 1,
  night: 1,
  month: 30,
  months: 30,
  year: 365,
  years: 365,
};

// A stated voyage duration's length in days, for proportional width sizing.
// Months and years are approximated (30 / 365) -- display-scale conversion,
// not a calendrical claim.
export function voyageDurationDays(d: VoyageDuration): number {
  return d.value * VOYAGE_DAYS_PER_UNIT[d.unit];
}

// Walk the curated station list in order and emit one entry per stated
// duration, or one 'unstated' placeholder per station with none. The 'start'
// station (Troy) has no incoming interval and contributes no entry. A
// station carrying both `duration` and `stayDuration` (Ogygia) contributes
// two consecutive 'stated' entries, in that order.
export function buildVoyageStrip(stations: VoyageStationInput[]): VoyageStrip {
  const entries: VoyageStripEntry[] = [];
  let totalStatedDays = 0;

  for (const s of stations) {
    if (s.kind === 'start') continue;

    if (s.duration) {
      const days = voyageDurationDays(s.duration);
      totalStatedDays += days;
      entries.push({
        kind: 'stated',
        stationId: s.id,
        label: s.label,
        days,
        duration: s.duration,
        refs: s.refs,
        note: s.note,
        unlocatable: !!s.unlocatable,
      });
    } else {
      entries.push({
        kind: 'unstated',
        stationId: s.id,
        label: s.label,
        days: 0,
        duration: null,
        refs: s.refs,
        note: s.note,
        unlocatable: !!s.unlocatable,
      });
    }

    if (s.stayDuration) {
      const days = voyageDurationDays(s.stayDuration);
      totalStatedDays += days;
      entries.push({
        kind: 'stated',
        stationId: s.id,
        label: s.stayDuration.label ?? s.label,
        days,
        duration: s.stayDuration,
        refs: s.refs,
        note: s.note,
        unlocatable: !!s.unlocatable,
      });
    }
  }

  return { entries, totalStatedDays };
}
