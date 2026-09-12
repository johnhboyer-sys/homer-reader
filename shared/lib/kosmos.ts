// The Kosmos Society revision of Butler (works.ts `verseGroups` translation):
// its pipeline piece carries standoff `spans` (transliteration brackets `tr`,
// editorial brackets `ed`, italics `em`) and `marks` (printed line numbers
// that do not cut a group — see pipeline/homer_pipeline/stage1_kosmos.py).
//
// The reader's flow model (tick-chunks.ts flowParts) slices a piece's plain
// text at its ticks and paragraph breaks, and each slice is rendered through
// esc() into its own {@html} run. To carry the standoff through that, this
// module writes private-use sentinel characters into the text (rebasing the
// ticks to match) and turns them into tags after escaping. Two rules keep
// every run's tags balanced: every open span is closed before a tick or a
// '\n' and reopened after it, and a span that must close while an inner one
// is still open closes the inner one first and reopens it.

import type { RossPiece } from './data';

const TR_OPEN = '\uE000';
const TR_CLOSE = '\uE001';
const EM_OPEN = '\uE002';
const EM_CLOSE = '\uE003';
const MARK_OPEN = '\uE004';
const MARK_CLOSE = '\uE005';

type Kind = 'tr' | 'em';
const OPEN: Record<Kind, string> = { tr: TR_OPEN, em: EM_OPEN };
const CLOSE: Record<Kind, string> = { tr: TR_CLOSE, em: EM_CLOSE };

// Reason codes travel as one character after MARK_OPEN.
const REASON_CODE: Record<string, string> = { repeat: 'r', 'out-of-sequence': 'o', 'not-in-greek': 'g' };
const REASON_TITLE: Record<string, string> = {
  r: 'Kosmos prints this line number again here; the groups do not break at it.',
  o: 'Kosmos prints this line number out of sequence (a misprint); the groups do not break at it.',
  g: 'Kosmos numbers a line that this Greek text does not carry; the groups do not break at it.',
};

export interface DecoratedPiece {
  text: string;
  ticks: { n: number; real: boolean; off: number }[];
}

type Event =
  | { pos: number; order: number; type: 'close'; id: number }
  | { pos: number; order: number; type: 'open'; id: number }
  | { pos: number; order: number; type: 'break' }
  | { pos: number; order: number; type: 'tick'; n: number; real: boolean }
  | { pos: number; order: number; type: 'mark'; label: string; code: string };

// Text + ticks with the piece's standoff written in as sentinels. A piece
// without spans or marks comes back unchanged (same text, same offsets).
export function decoratePiece(p: RossPiece): DecoratedPiece {
  const text = p.text;
  const baseTicks = (p.bekker ?? []).map(t => ({ n: t.n, real: t.real, off: t.offset }));
  const spans = (p.spans ?? []).filter(s => s[2] === 'tr' || s[2] === 'em');
  const marks = p.marks ?? [];
  if (!spans.length && !marks.length) return { text, ticks: baseTicks };

  const kinds: Kind[] = [];
  const events: Event[] = [];
  spans.forEach(([s, e, k], id) => {
    kinds[id] = k as Kind;
    // A hidden transliteration takes the space before it with it, so hiding
    // "Anger [mēnis], goddess" leaves "Anger, goddess".
    const start = k === 'tr' && s > 0 && text[s - 1] === ' ' ? s - 1 : s;
    // Longer spans open first and close last at a shared position.
    events.push({ pos: start, order: 3, type: 'open', id });
    events.push({ pos: e, order: 0, type: 'close', id });
  });
  for (let i = 0; i < text.length; i++) if (text[i] === '\n') events.push({ pos: i, order: 1, type: 'break' });
  for (const t of baseTicks) events.push({ pos: t.off, order: 2, type: 'tick', n: t.n, real: t.real });
  for (const m of marks) events.push({ pos: m.offset, order: 4, type: 'mark', label: m.label, code: REASON_CODE[m.reason] ?? 'o' });
  const len = (id: number) => spans[id][1] - spans[id][0];
  events.sort((a, b) => a.pos - b.pos || a.order - b.order
    || (a.type === 'open' && b.type === 'open' ? len(b.id) - len(a.id) : 0)
    || (a.type === 'close' && b.type === 'close' ? len(a.id) - len(b.id) : 0));

  let out = '';
  let cur = 0;
  const stack: number[] = [];
  const ticks: DecoratedPiece['ticks'] = [];
  const closeAll = () => { for (let i = stack.length - 1; i >= 0; i--) out += CLOSE[kinds[stack[i]]]; };
  const openAll = () => { for (const id of stack) out += OPEN[kinds[id]]; };
  for (const ev of events) {
    if (ev.pos > cur) { out += text.slice(cur, ev.pos); cur = ev.pos; }
    if (ev.type === 'open') { out += OPEN[kinds[ev.id]]; stack.push(ev.id); }
    else if (ev.type === 'close') {
      const at = stack.lastIndexOf(ev.id);
      if (at < 0) continue;
      const above = stack.splice(at);
      for (let i = above.length - 1; i >= 0; i--) out += CLOSE[kinds[above[i]]];
      for (const id of above.slice(1)) { out += OPEN[kinds[id]]; stack.push(id); }
    } else if (ev.type === 'break') {
      closeAll(); out += '\n'; cur = ev.pos + 1; openAll();
    } else if (ev.type === 'tick') {
      closeAll(); ticks.push({ n: ev.n, real: ev.real, off: out.length }); openAll();
    } else {
      out += MARK_OPEN + ev.code + ev.label + MARK_CLOSE;
    }
  }
  out += text.slice(cur);
  closeAll();
  return { text: out, ticks };
}

// Sentinels -> markup, AFTER the run has been escaped. Safe to run on any
// string: text without sentinels is returned unchanged.
export function sentinelsToHtml(escaped: string): string {
  if (!/[\uE000-\uE005]/.test(escaped)) return escaped;
  return escaped
    .replace(/\uE004([rog])([^\uE005]*)\uE005/g, (_m, code: string, label: string) =>
      `<span class="k-mark" title="${REASON_TITLE[code]}">${label}</span>`)
    .replace(/\uE000/g, '<span class="k-tr">')
    .replace(/\uE001/g, '</span>')
    .replace(/\uE002/g, '<em>')
    .replace(/\uE003/g, '</em>');
}

// Plain text of a decorated string (sentinels and mark labels removed) — for
// tests and anything that needs the words alone.
export function stripSentinels(s: string): string {
  return s.replace(/\uE004[rog][^\uE005]*\uE005/g, '').replace(/[\uE000-\uE005]/g, '');
}
