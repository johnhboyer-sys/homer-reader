// Every address the Go-to palette can send a reader to is a page, or an
// anchor on a page, that the build emitted (round 3: "links point at existing
// pages and anchors only"). The palette makes these addresses at run time from
// the name and word indexes, so the built pages' own link checker
// (scripts/check-links.mjs) never sees them.
//
// Reads app/dist and the corpus from disk. Without a build there is nothing to
// check: the tests skip, loudly, and do not pass by default.
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { SITE_PAGES, nameEntries } from '../lib/palette';
import { WORKS } from '../lib/works';

const DIST = path.resolve(process.cwd(), '../app/dist');
const DATA = path.resolve(process.cwd(), '../app/public/data');
const built = existsSync(path.join(DIST, 'index.html')) && existsSync(path.join(DATA, 'places.json'));

const pageFile = (p: string): string | null => {
  const clean = p.replace(/[?#].*$/, '').replace(/^\/|\/$/g, '');
  for (const f of [path.join(DIST, clean, 'index.html'), path.join(DIST, `${clean}.html`)]) if (existsSync(f)) return f;
  return null;
};
const idsOf = (file: string) => new Set(Array.from(readFileSync(file, 'utf-8').matchAll(/\sid="([^"]+)"/g), (m) => m[1]));
const json = <T>(name: string): T => JSON.parse(readFileSync(path.join(DATA, name), 'utf-8')) as T;

describe.skipIf(!built)('Go-to palette addresses resolve in the built site', () => {
  it('every page it lists was built', () => {
    for (const page of SITE_PAGES) expect(pageFile(page.path), page.path).not.toBeNull();
  });

  it('every place and every character it can name has its anchor on the page', () => {
    const places = json<{ places: { id: string; name: string; greek?: string }[] }>('places.json').places;
    const characters = json<{ characters: { id: string; name: string; greek?: string }[] }>('characters.json').characters;
    const entries = nameEntries(places, characters);
    expect(entries.length).toBe(places.length + characters.length);
    const ids = new Map<string, Set<string>>();
    const missing: string[] = [];
    for (const e of entries) {
      const [page, anchor] = e.path.split('#');
      const file = pageFile(page);
      if (!file) { missing.push(e.path); continue; }
      if (!ids.has(file)) ids.set(file, idsOf(file));
      if (!ids.get(file)!.has(anchor)) missing.push(e.path);
    }
    expect(missing).toEqual([]);
  });

  it('every word it can offer has a lexicon page', () => {
    const lemmata = json<Record<string, { slug: string }>>('lemmata.json');
    const slugs = Object.values(lemmata).map((l) => l.slug);
    expect(slugs.length).toBeGreaterThan(1000);
    const missing = slugs.filter((s) => !existsSync(path.join(DIST, 'lemma', s, 'index.html')));
    expect(missing).toEqual([]);
  });

  it('every book in its grid, and each poem\'s own page, was built', () => {
    const missing: string[] = [];
    for (const work of WORKS.filter((w) => w.citation?.scheme === 'verse-line')) {
      if (!pageFile(`/${work.id}`)) missing.push(`/${work.id}`);
      for (let b = 1; b <= work.books; b++) if (!pageFile(`/${work.id}/book/${b}`)) missing.push(`/${work.id}/book/${b}`);
    }
    expect(missing).toEqual([]);
  });

  it('the family trees a character links to are sections of the genealogies page', () => {
    const ids = idsOf(pageFile('/genealogies/')!);
    const characters = json<{ characters: { genealogy?: { tree: string } }[] }>('characters.json').characters;
    const trees = new Set(characters.map((c) => c.genealogy?.tree).filter((t): t is string => !!t));
    expect(trees.size).toBeGreaterThan(0);
    for (const t of trees) expect(ids.has(t), `#${t}`).toBe(true);
  });
});
