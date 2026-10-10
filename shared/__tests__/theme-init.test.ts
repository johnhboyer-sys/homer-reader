// app/src/components/ThemeInit.astro stamps data-theme on <html> before paint.
// If localStorage throws (storage blocked) the script must still stamp it;
// leaving it absent puts the page in the half-themed no-data-theme state.
import fs from 'node:fs';
import path from 'node:path';
import { afterEach, describe, expect, it, vi } from 'vitest';

const src = fs.readFileSync(
  path.resolve(process.cwd(), '../app/src/components/ThemeInit.astro'),
  'utf-8',
);
const script = src.match(/<script is:inline>([\s\S]*?)<\/script>/)![1];

function run(opts: { stored?: string | 'throw' | null; osDark: boolean }) {
  document.documentElement.removeAttribute('data-theme');
  vi.stubGlobal(
    'matchMedia',
    (q: string) => ({ matches: opts.osDark && q.includes('dark'), media: q }),
  );
  const store = {
    getItem: () => {
      if (opts.stored === 'throw') throw new DOMException('blocked', 'SecurityError');
      return opts.stored ?? null;
    },
  };
  vi.stubGlobal('localStorage', store);
  // eslint-disable-next-line no-new-func
  new Function(script)();
  return document.documentElement.getAttribute('data-theme');
}

afterEach(() => vi.unstubAllGlobals());

describe('ThemeInit script', () => {
  it('stamps data-theme when storage throws, on a dark OS', () => {
    expect(run({ stored: 'throw', osDark: true })).toBe('light');
  });
  it('stamps data-theme when storage throws, on a light OS', () => {
    expect(run({ stored: 'throw', osDark: false })).toBe('light');
  });
  it('honours a saved dark choice', () => {
    expect(run({ stored: 'dark', osDark: false })).toBe('dark');
  });
  it('defaults to light with nothing saved, whatever the OS says', () => {
    expect(run({ stored: null, osDark: true })).toBe('light');
  });
});
