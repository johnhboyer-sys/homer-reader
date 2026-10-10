// Theme policy (app/src/components/ThemeInit.astro): the page is LIGHT unless
// the reader chooses dark. The OS colour scheme is never followed, and a page
// that carries no data-theme (no script, or storage blocked) is light too
// (John, 2026-10-10). So no `prefers-color-scheme: dark` rule may restyle the
// page: such a rule would give a dark OS a dark page whenever data-theme is
// absent. Dark styling hangs on :root[data-theme="dark"] only.
import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const ROOTS = [path.resolve(process.cwd(), 'styles'), path.resolve(process.cwd(), 'components'), path.resolve(process.cwd(), '../app/src')];
const EXT = /\.(css|astro|svelte)$/;
const SKIP = new Set(['node_modules', 'dist', '.astro']);

function walk(dir: string): string[] {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    if (SKIP.has(e.name)) return [];
    const p = path.join(dir, e.name);
    return e.isDirectory() ? walk(p) : EXT.test(e.name) ? [p] : [];
  });
}

const stripComments = (s: string) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/<!--[\s\S]*?-->/g, '');
const DARK_OS = /prefers-color-scheme\s*:\s*dark/;

describe('theme policy: the OS dark preference never styles the page', () => {
  const files = ROOTS.flatMap(walk);

  it('scans global.css and the app sources', () => {
    expect(files.some((f) => f.endsWith(path.join('styles', 'global.css')))).toBe(true);
    expect(files.some((f) => f.endsWith('index.astro'))).toBe(true);
  });

  it('no `prefers-color-scheme: dark` rule exists in any .css, .astro or .svelte file', () => {
    const hits = files
      .filter((f) => DARK_OS.test(stripComments(fs.readFileSync(f, 'utf-8'))))
      .map((f) => path.relative(process.cwd(), f));
    expect(hits).toEqual([]);
  });

  it('global.css sets no tokens on an unstamped root (:root:not([data-theme]))', () => {
    const css = stripComments(fs.readFileSync(path.resolve(process.cwd(), 'styles/global.css'), 'utf-8'));
    expect(css).not.toMatch(/:root:not\(\[data-theme\]\)/);
  });
});
