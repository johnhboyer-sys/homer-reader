import { describe, expect, it } from 'vitest';
import { decoratePiece, sentinelsToHtml, stripSentinels } from '../lib/kosmos';
import { flowParts, alignGroups } from '../lib/tick-chunks';
import type { RossPiece } from '../lib/data';

// Il. 1.1–2 as the pipeline emits it (stage1_kosmos): brackets and italics
// as standoff, ticks at Kosmos's printed numbers.
const TEXT = 'Anger [mēnis], goddess, sing it, of Achilles, son of Peleus— disastrous [oulomenē] anger, [= Apollo] and [Agamemnon] too.';
const piece = (extra: Partial<RossPiece> = {}): RossPiece => ({
  chapter: '1', cont: false, text: TEXT,
  bekker: [{ n: 1, offset: 0, real: true }, { n: 2, offset: TEXT.indexOf('disastrous'), real: true }],
  spans: [
    [6, 13, 'tr'], [7, 12, 'em'],
    [TEXT.indexOf('[oulo'), TEXT.indexOf('] anger') + 1, 'tr'], [TEXT.indexOf('oulo'), TEXT.indexOf('] anger'), 'em'],
    [TEXT.indexOf('[= A'), TEXT.indexOf('] and') + 1, 'ed'],
    [TEXT.indexOf('[Aga'), TEXT.indexOf('] too') + 1, 'ed'],
  ],
  ...extra,
});

function renderRuns(p: RossPiece): string[] {
  const d = decoratePiece(p);
  return flowParts(d.text, d.ticks)
    .filter(x => x.text !== null)
    .map(x => sentinelsToHtml(x.text!));
}

describe('decoratePiece', () => {
  it('leaves the words verbatim and moves ticks onto the same words', () => {
    const d = decoratePiece(piece());
    expect(stripSentinels(d.text)).toBe(TEXT);
    const plain = stripSentinels(d.text.slice(d.ticks[1].off));
    expect(plain.startsWith('disastrous')).toBe(true);
  });

  it('marks transliteration brackets (with the space before them) and italics, not editorial brackets', () => {
    const html = renderRuns(piece()).join('');
    expect(html).toContain('Anger<span class="k-tr"> [<em>mēnis</em>]</span>, goddess');
    expect(html).toContain('[= Apollo]');
    expect(html).not.toMatch(/k-tr">[^<]*\[= Apollo/);
    expect(html).toContain('[Agamemnon]');
  });

  it('keeps every rendered run balanced when a span crosses a tick', () => {
    // A tick inside a transliteration: the span is closed before it and
    // reopened after it, so each {@html} run is well formed on its own.
    const p = piece({ bekker: [{ n: 1, offset: 0, real: true }, { n: 2, offset: 9, real: true }] });
    for (const run of renderRuns(p)) {
      const opens = (run.match(/<(span|em)\b/g) ?? []).length;
      const closes = (run.match(/<\/(span|em)>/g) ?? []).length;
      expect(opens).toBe(closes);
    }
  });

  it('renders a non-break mark inline without cutting a group', () => {
    const p = piece({ marks: [{ n: 460, offset: TEXT.indexOf('goddess'), label: '460', reason: 'not-in-greek' }] });
    const d = decoratePiece(p);
    expect(d.ticks.map(t => t.n)).toEqual([1, 2]);
    const html = renderRuns(p).join('');
    expect(html).toMatch(/<span class="k-mark" title="[^"]+">460<\/span>goddess/);
  });

  it('is a no-op for a piece without standoff', () => {
    const plain: RossPiece = { chapter: '1', cont: false, text: 'Sing, O goddess', bekker: [{ n: 1, offset: 0, real: true }] };
    expect(decoratePiece(plain)).toEqual({ text: 'Sing, O goddess', ticks: [{ n: 1, real: true, off: 0, label: undefined }] });
    expect(sentinelsToHtml('a &amp; b')).toBe('a &amp; b');
  });

  // A character in kosmos.ts's own private-use sentinel range (TR_OPEN..
  // MARK_CLOSE) is written into the string via String.fromCharCode rather
  // than a \u escape literal, so this test file never itself contains the
  // code point kosmos.ts reserves for its generated markup.
  const FORGED_SENTINEL = String.fromCharCode(0xe000); // == kosmos.ts's TR_OPEN

  it('never lets a literal source character forge markup (no standoff — the fast path)', () => {
    // stage1_kosmos.py now refuses a source character in this range, but
    // decoratePiece must not trust that: a piece with no spans/marks takes
    // the early-return path, which used to hand the raw text straight to
    // sentinelsToHtml unexamined.
    const text = `Anger ${FORGED_SENTINEL}goddess, sing it.`;
    const p: RossPiece = { chapter: '1', cont: false, text, bekker: [{ n: 1, offset: 0, real: true }] };
    const d = decoratePiece(p);
    expect(d.text).not.toContain(FORGED_SENTINEL);
    expect(sentinelsToHtml(d.text)).not.toContain('<span class="k-tr">');
  });

  it('never lets a literal source character forge markup (a real span forces the full processing path)', () => {
    // An 'ed' span alone would be filtered out (decoratePiece only tracks
    // 'tr'/'em'), which would silently retake the no-standoff fast path
    // above -- use a real 'tr' span so this genuinely exercises the
    // open/close event machinery alongside the forged character. Because
    // FORGED_SENTINEL is the same code point decoratePiece legitimately
    // writes to open a 'tr' span, "d.text doesn't contain it" is the wrong
    // assertion here (the real span's own opener does contain it) -- the
    // real symptom is an extra, unmatched opener: before the fix, the forged
    // character contributes a SECOND <span class="k-tr"> with no closing
    // </span> of its own, unbalancing the rendered run.
    const text = `Anger ${FORGED_SENTINEL}goddess, [mēnis] sing it.`;
    const p = piece({ text, bekker: [{ n: 1, offset: 0, real: true }], spans: [[text.indexOf('[m'), text.indexOf('] sing') + 1, 'tr']] });
    const d = decoratePiece(p);
    const html = sentinelsToHtml(d.text);
    const opens = (html.match(/<(span|em)\b/g) ?? []).length;
    const closes = (html.match(/<\/(span|em)>/g) ?? []).length;
    expect(opens).toBe(closes);
    expect(opens).toBe(1); // exactly the real 'tr' span -- not a forged second one
  });

  it('carries a tick\'s printed label through, keeping n for alignment (Kosmos "321–322")', () => {
    const p = piece({ bekker: [{ n: 1, offset: 0, real: true }, { n: 2, offset: TEXT.indexOf('disastrous'), real: true, label: '321–322' }] });
    const d = decoratePiece(p);
    expect(d.ticks[0].label).toBeUndefined();
    expect(d.ticks[1]).toMatchObject({ n: 2, label: '321–322' });

    const flow = flowParts(d.text, d.ticks);
    const tickPart = flow.find(part => part.n === 2);
    expect(tickPart?.label).toBe('321–322');
  });
});

describe('verse groups', () => {
  it('break exactly at each printed number, each beside its own Greek span', () => {
    const lines = [1, 2, 3, 4, 5].map(n => ({ n }));
    const d = decoratePiece(piece());
    const groups = alignGroups(lines, flowParts(d.text, d.ticks), []);
    expect(groups.map(g => g.lines.map(l => l.n))).toEqual([[1], [2, 3, 4, 5]]);
    const firstText = groups[0].flowParts.filter(x => x.text).map(x => stripSentinels(x.text!)).join('');
    expect(firstText.trim().endsWith('Peleus—')).toBe(true);
  });
});
