// Review finding (round 5): the reader bar's work picker and Help button were
// moved to client:idle. Both are controls a reader can reach in the first
// second; a change to the picker or a click on Help before idle hydration
// fired into markup with no handler and was lost. They hydrate on load again.
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const shell = readFileSync(path.resolve(process.cwd(), 'src/components/ReaderShell.astro'), 'utf8');

/** The client:* directive on each use of a component in the shell. */
const directives = (name: string) =>
  Array.from(shell.matchAll(new RegExp(`<${name}\\b[^>]*?\\b(client:[a-z]+)`, 'g')), (m) => m[1]);

describe('reader bar islands an early action reaches', () => {
  for (const name of ['WorkSwitcher', 'HelpButton', 'BekkerJump']) {
    it(`${name} hydrates on load, not on idle`, () => {
      const found = directives(name);
      expect(found.length).toBeGreaterThan(0);
      expect(found.every((d) => d === 'client:load')).toBe(true);
    });
  }
});
