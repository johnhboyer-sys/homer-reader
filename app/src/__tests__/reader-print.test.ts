// Review finding (round 5): the book's end (previous / next and the grid of
// every book) is styled only on screen, so on paper it printed as a bare list
// after the poem. It is reader chrome; print hides it as it hides the rest.
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const css = readFileSync(path.resolve(process.cwd(), '../shared/styles/global.css'), 'utf8')
  .replace(/\/\*[\s\S]*?\*\//g, '');

/** Bodies of the rules directly inside an `@media print` block whose selector list names `sel`. */
function printRules(sel: string): string[] {
  const out: string[] = [];
  const stack: string[] = [];
  let chunk = '';
  for (let i = 0; i < css.length; i++) {
    const ch = css[i];
    if (ch === '{') {
      const prelude = chunk.trim();
      chunk = '';
      if (prelude.startsWith('@')) { stack.push(prelude); continue; }
      const end = css.indexOf('}', i);
      const inPrint = stack.some((s) => /^@media\s+print\b/.test(s));
      if (inPrint && prelude.split(',').some((s) => s.trim() === sel)) out.push(css.slice(i + 1, end));
      i = end;
    } else if (ch === '}') { stack.pop(); chunk = ''; }
    else chunk += ch;
  }
  return out;
}

describe('the reader in print', () => {
  it('hides the book-end navigation', () => {
    expect(printRules('.book-end').some((b) => /display\s*:\s*none/.test(b))).toBe(true);
  });
});
