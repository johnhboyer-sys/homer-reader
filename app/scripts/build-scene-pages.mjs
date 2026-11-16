// Writes build/scene-pages/<work>.json: for every book and translation, the
// spans of the translation's text each scene's Reading Mode page shows
// (scene-pages.ts). pipeline/homer_pipeline/search_scenes.py reads it to
// write search/eng-chapters.json. Run by scripts/build-public.mjs after the
// pipeline and the speeches copy:
//
//   node --experimental-strip-types app/scripts/build-scene-pages.mjs [build/dist] [build/scene-pages]
//
// shared/lib imports its siblings without a file extension, which Vite
// resolves and Node does not; the hook below tries `<specifier>.ts` when Node
// cannot find one. works.ts reads import.meta.env (Vite's), which Node does not
// define; the hook gives that module an empty one, so SHOW_PRIVATE is off, as
// in the public build.
import { mkdirSync, readFileSync, readdirSync, existsSync, writeFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

registerHooks({
  resolve(specifier, context, next) {
    try {
      return next(specifier, context);
    } catch (err) {
      if (err?.code === 'ERR_MODULE_NOT_FOUND' && /^\.\.?\//.test(specifier) && !/\.[cm]?[jt]s$/.test(specifier)) {
        return next(`${specifier}.ts`, context);
      }
      throw err;
    }
  },
  load(url, context, next) {
    const result = next(url, context);
    if (url.endsWith('/shared/lib/works.ts')) {
      result.source = `import.meta.env ??= {};\n${String(result.source)}`;
    }
    return result;
  },
});

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const DIST = resolve(process.argv[2] ?? join(ROOT, 'build', 'dist'));
const OUT = resolve(process.argv[3] ?? join(ROOT, 'build', 'scene-pages'));

const { translationPages } = await import('./scene-pages.ts');
const { getWork, visibleTranslations } = await import('../../shared/lib/works.ts');
const overrides = JSON.parse(readFileSync(join(ROOT, 'shared', 'lib', 'scene-boundary-overrides.json'), 'utf-8'));

mkdirSync(OUT, { recursive: true });
const works = readdirSync(DIST).filter((w) => getWork(w) && existsSync(join(DIST, w, 'book-01.json'))).sort();
if (!works.length) {
  console.error(`no works in ${DIST}`);
  process.exit(1);
}
for (const work of works) {
  const translations = visibleTranslations(getWork(work));
  const speeches = existsSync(join(DIST, work, 'speeches.json'))
    ? JSON.parse(readFileSync(join(DIST, work, 'speeches.json'), 'utf-8')).speeches ?? []
    : [];
  const books = {};
  const tally = {};
  for (const file of readdirSync(join(DIST, work)).filter((f) => /^book-\d+\.json$/.test(f)).sort()) {
    const doc = JSON.parse(readFileSync(join(DIST, work, file), 'utf-8'));
    if (doc.segments.length !== 1) throw new Error(`${work} ${file}: expected one segment per book`);
    const seg = doc.segments[0];
    const sceneList = doc.apparatus?.scenes ?? [];
    const scenes = sceneList.map((s) => ({ startLine: s.lines[0], endLine: s.lines[1] }));
    const speechStarts = speeches.filter((s) => s.book === doc.book).map((s) => s.lines[0]);
    const out = {};
    for (const t of translations) {
      const paged = translationPages({ seg, translation: t, scenes, speechStarts, overrides, work, book: doc.book });
      if (!paged) continue;
      out[t.id] = paged;
      const n = (tally[t.id] ??= { books: 0, unpaged: [], offPage: 0, onTwoPages: 0, overrideErrors: 0 });
      n.books++;
      if (!paged.anchored) n.unpaged.push(doc.book);
      n.offPage += paged.offPage;
      n.onTwoPages += paged.onTwoPages;
      if (paged.overrideError) {
        n.overrideErrors++;
        console.warn(`${work} ${doc.book} ${t.id}: ${paged.overrideError}`);
      }
    }
    books[doc.book] = { scenes: sceneList.map((s) => `${s.lines[0]}-${s.lines[1]}`), translations: out };
  }
  writeFileSync(join(OUT, `${work}.json`), JSON.stringify({ work, books }));
  for (const [id, n] of Object.entries(tally)) {
    console.log(`scene pages ${work} ${id}: books=${n.books} unpaged=${JSON.stringify(n.unpaged)} `
      + `off_page_chars=${n.offPage} on_two_pages_chars=${n.onTwoPages} override_errors=${n.overrideErrors}`);
  }
}
