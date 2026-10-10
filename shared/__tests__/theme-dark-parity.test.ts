// A reader whose OS is dark but whose page carries no data-theme attribute
// (ThemeInit could not run or could not read storage) must get the SAME dark
// declarations as an explicit data-theme="dark". The two lists live in
// shared/styles/global.css as separate rules, so this test parses the real
// file and fails the moment they drift apart. Explicit data-theme="light" and
// data-theme="dark" must keep winning over the OS.
import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const css = fs
  .readFileSync(path.resolve(process.cwd(), 'styles/global.css'), 'utf-8')
  .replace(/\/\*[\s\S]*?\*\//g, '');

/** The brace-balanced body of every `{` that follows a top-level prelude. */
function topLevel(text: string): { prelude: string; body: string }[] {
  const out: { prelude: string; body: string }[] = [];
  let i = 0;
  while (i < text.length) {
    const open = text.indexOf('{', i);
    if (open === -1) break;
    let depth = 0;
    let j = open;
    for (; j < text.length; j++) {
      if (text[j] === '{') depth++;
      else if (text[j] === '}' && --depth === 0) break;
    }
    out.push({ prelude: text.slice(i, open).trim(), body: text.slice(open + 1, j) });
    i = j + 1;
  }
  return out;
}

/** property -> value, splitting on `;` outside parentheses and quotes. */
function declarations(body: string): Map<string, string> {
  const map = new Map<string, string>();
  let depth = 0;
  let quote = '';
  let start = 0;
  const flush = (end: number) => {
    const d = body.slice(start, end).trim();
    const c = d.indexOf(':');
    if (c > 0) map.set(d.slice(0, c).trim(), d.slice(c + 1).replace(/\s+/g, ' ').trim());
    start = end + 1;
  };
  for (let k = 0; k < body.length; k++) {
    const ch = body[k];
    if (quote) {
      if (ch === quote) quote = '';
    } else if (ch === '"' || ch === "'") quote = ch;
    else if (ch === '(') depth++;
    else if (ch === ')') depth--;
    else if (ch === ';' && depth === 0) flush(k);
  }
  flush(body.length);
  return map;
}

function merged(rules: { body: string }[]): Map<string, string> {
  const all = new Map<string, string>();
  for (const r of rules) for (const [k, v] of declarations(r.body)) all.set(k, v);
  return all;
}

const rules = topLevel(css);
const darkRules = rules.filter((r) => r.prelude === ':root[data-theme="dark"]');
const mediaRules = rules
  .filter((r) => r.prelude === '@media (prefers-color-scheme: dark)')
  .flatMap((r) => topLevel(r.body))
  .filter((r) => r.prelude === ':root:not([data-theme])');

describe('dark theme: explicit data-theme="dark" vs. dark OS with no data-theme', () => {
  const dark = merged(darkRules);
  const media = merged(mediaRules);

  it('finds both lists in global.css', () => {
    expect(dark.size).toBeGreaterThan(40);
    expect(media.size).toBeGreaterThan(0);
  });

  it('the no-data-theme block declares every property the data-theme="dark" blocks declare', () => {
    const missing = [...dark.keys()].filter((k) => !media.has(k));
    expect(missing).toEqual([]);
  });

  it('every shared property has the same value', () => {
    const differ = [...dark.keys()]
      .filter((k) => media.has(k) && media.get(k) !== dark.get(k))
      .map((k) => `${k}: dark=${dark.get(k)} media=${media.get(k)}`);
    expect(differ).toEqual([]);
  });

  it('the no-data-theme block adds nothing the dark theme lacks', () => {
    const extra = [...media.keys()].filter((k) => !dark.has(k));
    expect(extra).toEqual([]);
  });

  it('the no-data-theme block only applies when data-theme is absent, so an explicit choice wins', () => {
    expect(mediaRules.length).toBeGreaterThan(0);
    expect(css).toContain(':root[data-theme="light"] {');
  });
});
