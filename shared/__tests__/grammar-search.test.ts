import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { searchGrammar, type GrammarDict } from '../lib/search';

// A tiny GrammarDict + column, built by hand — no fixture like this exists
// in the repo yet. One segment, six tokens, one signature id per token:
//
//   pos 0 -> sig 0  reserved.unkeyed   — no readings, never matches
//   pos 1 -> sig 1  reserved.unanalysed — no readings, never matches
//   pos 2 -> sig 2  sole reading: dual                       (certain dual)
//   pos 3 -> sig 3  two readings: dual, pl                   (possible dual)
//   pos 4 -> sig 4  sole reading, syncretic case nom/voc      (not certain for case)
//   pos 5 -> sig 5  two readings, masc-nom-sg / fem-acc-pl    (whole-reading test)
const dict: GrammarDict = {
  token_count: 6,
  width: 2,
  categories: ['case', 'number', 'gender'],
  reserved: { unkeyed: 0, unanalysed: 1 },
  sigs: [
    [],
    [],
    [{ number: ['dual'] }],
    [{ number: ['dual'] }, { number: ['pl'] }],
    [{ case: ['nom', 'voc'], number: ['sg'] }],
    [{ gender: ['masc'], case: ['nom'], number: ['sg'] }, { gender: ['fem'], case: ['acc'], number: ['pl'] }],
  ],
};
const column = Uint16Array.from([0, 1, 2, 3, 4, 5]);

const meta = [{ id: '1:1', book: 1, column: '1', greek_head: '', greek_tokens: '', english_head: '' }];
const offsets = {
  token_count: 6,
  seg_base_offset: [0],
  segments: [{ book: 1, column: '1', line_runs: [[1, 6]] }],
  book_bounds: [{ book: 1, start: 0 }],
  chapter_bounds: [],
};

function json(data: unknown) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(data) } as Response);
}
function binary(col: Uint16Array) {
  const buf = col.buffer.slice(col.byteOffset, col.byteOffset + col.byteLength);
  return Promise.resolve({ ok: true, arrayBuffer: () => Promise.resolve(buf) } as Response);
}

// loadIndex/loadBinary cache per (work, file) for the module's lifetime, so —
// same discipline as combo.test.ts — every test that hits the network mock
// uses its own work id to avoid reading another test's cached response.
function mockFetch() {
  vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
    const path = String(url);
    if (path.endsWith('/meta.json')) return json(meta);
    if (path.endsWith('/offsets.json')) return json(offsets);
    if (path.endsWith('/grammar-dict.json')) return json(dict);
    if (path.endsWith('/grammar-col.bin')) return binary(column);
    return Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as Response);
  });
}

describe('searchGrammar', () => {
  beforeEach(mockFetch);
  afterEach(() => vi.restoreAllMocks());

  it('matches a token whose sole reading satisfies the query, and one where it is only possible', async () => {
    const { results } = await searchGrammar({ number: 'dual' }, ['GDUAL']);
    expect(results).toHaveLength(1);
    const r = results[0];
    // Position <-> certainty alignment: grkPositions[i] and grammar[i] must
    // describe the SAME token. Read them together rather than trusting index
    // order alone to still line up after some future edit — this is exactly
    // what Search.svelte's explicit position->certainty map (built at the
    // point of use, not assumed from array order) also guards against.
    const byPos = new Map(r.grkPositions.map((p, i) => [p, r.grammar![i]]));
    expect(byPos.get(2)).toEqual({ values: { number: ['dual'] }, certain: true });
    expect(byPos.get(3)).toEqual({ values: { number: ['dual', 'pl'] }, certain: false });
    // Nothing else in the fixture licenses a dual reading.
    expect([...byPos.keys()].sort((a, b) => a - b)).toEqual([2, 3]);
  });

  it('is certain only when every reading satisfies AND the category has exactly one licensed value', async () => {
    // pos 4's sole analysis is "case nom/voc sg" — one analysis record, two
    // possible cases, so a query for the nominative alone is not certain.
    const { results } = await searchGrammar({ case: 'nom' }, ['GCASE']);
    const r = results[0];
    const byPos = new Map(r.grkPositions.map((p, i) => [p, r.grammar![i]]));
    const hit = byPos.get(4)!;
    expect(hit.certain).toBe(false);
    expect(hit.values.case).toEqual(['nom', 'voc']);
  });

  it('requires one reading to satisfy every queried category at once (whole-reading semantics)', async () => {
    // pos 5 has two readings: masc/nom/sg and fem/acc/pl. Neither reading is
    // both masc AND acc, so a query asking for both together must not match
    // it — even though "masc" and "acc" are each individually licensed by
    // SOME reading of the token.
    const { results } = await searchGrammar({ gender: 'masc', case: 'acc' }, ['GWHOLE']);
    expect(results).toHaveLength(0);
  });

  it('never reports a signature with no readings (reserved ids)', async () => {
    // sig 0/1 (unkeyed/unanalysed) have zero readings; no query can match them.
    const { results } = await searchGrammar({ number: 'sg' }, ['GRESERVED']);
    const positions = results.flatMap((r) => r.grkPositions);
    expect(positions).not.toContain(0);
    expect(positions).not.toContain(1);
  });
});
