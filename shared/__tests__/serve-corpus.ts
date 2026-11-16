// Serve the real corpus (app/public/data, the build/dist symlink) to the page
// under test through a fetch spy, so a mounted search page counts what a
// reader would see. Without the data (a fresh worktree) HAVE_CORPUS is false
// and callers skip, loudly. `edit` may rewrite one file's JSON on the way out.
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { vi } from 'vitest';

export const CORPUS = path.resolve(process.cwd(), '../app/public/data');
export const HAVE_CORPUS = existsSync(path.join(CORPUS, 'iliad/search/meta.json'))
  && existsSync(path.join(CORPUS, 'iliad/search/eng-chapters.json'));

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function serveCorpus(edit: Record<string, (json: any) => unknown> = {}) {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (url) => {
    const rel = decodeURIComponent(String(url)).replace(/^.*?\/data\//, '');
    const file = path.join(CORPUS, rel);
    if (!rel || rel.includes('..') || !existsSync(file)) {
      return { ok: false, status: 404, json: async () => ({}), text: async () => '' } as Response;
    }
    const buf = readFileSync(file);
    const text = () => (edit[rel] ? JSON.stringify(edit[rel](JSON.parse(buf.toString('utf8')))) : buf.toString('utf8'));
    return {
      ok: true, status: 200,
      json: async () => JSON.parse(text()),
      text: async () => text(),
      arrayBuffer: async () => buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength),
    } as Response;
  });
}
