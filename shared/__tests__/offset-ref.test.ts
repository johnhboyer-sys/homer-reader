// offsetRef: global token offset -> a citable book.line.
//
// The seven edge cases the resolver has to survive (docs/advanced-search-client-plan.md §3).
// Cases 1, 2, 4 and 6 are asserted against the REAL built corpus; cases 3, 5
// and 7 need a corpus property the current build does not have (a zero-token
// line, a keyless token) or a second work in one file, so they use a synthetic
// fixture. Both matter: the fixture proves the algorithm, the real data proves
// the build agrees with it.

import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { offsetRef, type Offsets } from '../lib/search';

const DATA = path.resolve(process.cwd(), '../app/public/data');

function loadOffsets(work: string): Offsets | null {
  const file = path.join(DATA, work, 'search', 'offsets.json');
  if (!fs.existsSync(file)) return null;
  return JSON.parse(fs.readFileSync(file, 'utf8')) as Offsets;
}

// Global offset of the first token of a given emitted line, by walking the runs.
function startOfLine(offsets: Offsets, book: number, line: number): number {
  const si = offsets.segments.findIndex(s => s.book === book);
  if (si < 0) throw new Error(`no segment for book ${book}`);
  let at = offsets.seg_base_offset[si];
  for (const [n, count] of offsets.segments[si].line_runs) {
    if (n === line) return at;
    at += count;
  }
  throw new Error(`book ${book} has no line ${line}`);
}

// -- Synthetic fixture -------------------------------------------------------
// Two segments. Book 1 holds a numbering gap (3 -> 5), an athetized line kept
// under its own number (5), a zero-token line (6) and a keyless token; book 2
// starts exactly where book 1 ends.
//   book 1: line 1 = offsets 0-1, line 3 = 2-4, line 5 = 5-6, line 6 = (none)
//   book 2: line 1 = offsets 7-8
const fixture: Offsets = {
  token_count: 9,
  seg_base_offset: [0, 7],
  segments: [
    { book: 1, column: '1', line_runs: [[1, 2], [3, 3], [5, 2], [6, 0]] },
    { book: 2, column: '2', line_runs: [[1, 2]] },
  ],
  book_bounds: [{ book: 1, start: 0 }, { book: 2, start: 7 }],
  chapter_bounds: [],
};

describe('offsetRef (synthetic fixture)', () => {
  it('case 1 — a numbering gap resolves to the emitted number, not a count', () => {
    // Line 3 owns offsets 2-4; the line before it is 1, not 2.
    expect(offsetRef(fixture, 2)).toMatchObject({ book: 1, line: 3 });
    expect(offsetRef(fixture, 4)).toMatchObject({ book: 1, line: 3 });
  });

  it('case 2 — an athetized line keeps its own bracketed number', () => {
    // Line 5 is the athetized one: it carries its own n and its own tokens.
    expect(offsetRef(fixture, 5)).toMatchObject({ book: 1, line: 5 });
    expect(offsetRef(fixture, 6)).toMatchObject({ book: 1, line: 5 });
  });

  it('case 3 — a zero-token line can never own an offset', () => {
    // Line 6 has count 0 and sits last in book 1, so nothing resolves to it —
    // but `.not.toContain(6)` alone would also pass if offsetRef returned
    // undefined for every offset (undefined is not 6 either), so pin the
    // exact mapping: offsets 0-1 belong to line 1, 2-4 to line 3, 5-6 to
    // line 5, and none is undefined or 6.
    const lines = [...Array(7).keys()].map(g => offsetRef(fixture, g)?.line);
    expect(lines).toEqual([1, 1, 3, 3, 3, 5, 5]);
  });

  it('case 4 — a segment boundary belongs to the following segment', () => {
    expect(offsetRef(fixture, 6)).toMatchObject({ seg_idx: 0, book: 1, line: 5, pos: 6 });
    expect(offsetRef(fixture, 7)).toMatchObject({ seg_idx: 1, book: 2, line: 1, pos: 0 });
  });

  it('case 5 — a keyless token still occupies its offset', () => {
    // The offset space counts EVERY stage-3 token, so line 3's three offsets
    // include the unanalysable one at 3. If line_runs had counted only keyed
    // tokens, offset 4 would have drifted into line 5.
    expect(offsetRef(fixture, 3)).toMatchObject({ book: 1, line: 3 });
    expect(offsetRef(fixture, 4)).toMatchObject({ book: 1, line: 3 });
  });

  it('case 6 — the fingerprint: token_count equals the sum of the run counts', () => {
    const sum = fixture.segments
      .flatMap(s => s.line_runs)
      .reduce((total, [, count]) => total + count, 0);
    expect(sum).toBe(fixture.token_count);
  });

  it('rejects an offset outside the work rather than clamping it', () => {
    expect(offsetRef(fixture, -1)).toBeNull();
    expect(offsetRef(fixture, 9)).toBeNull();
    expect(offsetRef(fixture, 8)).toMatchObject({ book: 2, line: 1 });
  });

  it('returns null rather than guess when the runs are short of the segment', () => {
    // A build defect: the segment spans 3 offsets but its runs cover 2.
    const broken: Offsets = {
      token_count: 3,
      seg_base_offset: [0],
      segments: [{ book: 1, column: '1', line_runs: [[1, 2]] }],
      book_bounds: [{ book: 1, start: 0 }],
      chapter_bounds: [],
    };
    expect(offsetRef(broken, 2)).toBeNull();
  });

  it('column always agrees with book, so a citation composes without a fork', () => {
    for (let g = 0; g < fixture.token_count; g++) {
      const ref = offsetRef(fixture, g)!;
      expect(ref.column).toBe(String(ref.book));
    }
  });
});

describe('offsetRef (real built corpus)', () => {
  it('case 7 — offsets never mix works: each file stands alone', (ctx) => {
    const iliad = loadOffsets('iliad');
    const odyssey = loadOffsets('odyssey');
    if (!iliad || !odyssey) {
      ctx.skip();
      return;
    }
    // The last Iliad offset is a valid Iliad citation and out of range for the
    // Odyssey, which is only true because the two offset spaces are separate.
    const last = iliad.token_count - 1;
    expect(offsetRef(iliad, last)).toMatchObject({ book: 24 });
    expect(offsetRef(odyssey, last)).toBeNull();
    expect(iliad.token_count).not.toBe(odyssey.token_count);
  });

  it('case 1 (real) — Od. 10 past the 455/457 gap resolves to 457, never 456', (ctx) => {
    const odyssey = loadOffsets('odyssey');
    if (!odyssey) {
      ctx.skip();
      return;
    }
    const at457 = startOfLine(odyssey, 10, 457);
    // The gap is real in the current build: 456 exists nowhere in book 10.
    const book10 = odyssey.segments.find(s => s.book === 10)!;
    const numbers = book10.line_runs.map(([n]) => n);
    expect(numbers).toContain(455);
    expect(numbers).toContain(457);
    expect(numbers).not.toContain(456);

    expect(offsetRef(odyssey, at457)).toMatchObject({ book: 10, line: 457 });
    expect(offsetRef(odyssey, at457 - 1)).toMatchObject({ book: 10, line: 455 });
  });

  it('case 1 (real) — the other two Odyssey gaps resolve the same way', (ctx) => {
    const odyssey = loadOffsets('odyssey');
    if (!odyssey) {
      ctx.skip();
      return;
    }
    for (const [book, before, after] of [[16, 100, 102], [23, 48, 50]] as const) {
      const at = startOfLine(odyssey, book, after);
      expect(offsetRef(odyssey, at)).toMatchObject({ book, line: after });
      expect(offsetRef(odyssey, at - 1)).toMatchObject({ book, line: before });
    }
  });

  it('case 4 (real) — both edges of a book land in the right book', (ctx) => {
    const iliad = loadOffsets('iliad');
    if (!iliad) {
      ctx.skip();
      return;
    }
    iliad.segments.forEach((seg, si) => {
      const base = iliad.seg_base_offset[si];
      const end = si + 1 < iliad.seg_base_offset.length
        ? iliad.seg_base_offset[si + 1]
        : iliad.token_count;
      expect(offsetRef(iliad, base)).toMatchObject({
        seg_idx: si, book: seg.book, line: seg.line_runs[0][0], pos: 0,
      });
      expect(offsetRef(iliad, end - 1)).toMatchObject({
        seg_idx: si, book: seg.book, line: seg.line_runs[seg.line_runs.length - 1][0],
      });
    });
  });

  it('case 6 (real) — every offset resolves, in both works', (ctx) => {
    const works = ['iliad', 'odyssey'].map(w => [w, loadOffsets(w)] as const);
    if (works.some(([, o]) => !o)) {
      ctx.skip();
      return;
    }
    for (const [work, offsets] of works) {
      const o = offsets!;
      const sum = o.segments
        .flatMap(s => s.line_runs)
        .reduce((total, [, count]) => total + count, 0);
      expect(sum, `${work}: sum of line_runs`).toBe(o.token_count);
      // Walking every offset is ~200k resolutions per work; cheap enough, and
      // it is the only check that proves no offset falls in a hole.
      let previous = -1;
      for (let g = 0; g < o.token_count; g++) {
        const ref = offsetRef(o, g);
        expect(ref, `${work}: offset ${g}`).not.toBeNull();
        // Citations advance monotonically through the work.
        const rank = ref!.seg_idx * 100000 + ref!.line;
        expect(rank, `${work}: offset ${g} went backwards`).toBeGreaterThanOrEqual(previous);
        previous = rank;
      }
    }
  });
});
