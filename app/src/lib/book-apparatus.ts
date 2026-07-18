// Build-time projection of the book-level apparatus used by reader chrome.
// ReaderShell renders once for every book in a work, so memoize the small
// whole-work index rather than reopening all of its book JSON files per page.
// This deliberately reads the same emitted public/data files as ReaderShell's
// current-book SSR loader; it is not a second apparatus source or pipeline API.
import { readFileSync } from 'node:fs';

export interface BookArgument {
  argument?: string;
  draft?: boolean;
  /** Number of emitted Greek verse lines, when the book has verse data. */
  lines?: number;
}

const cache = new Map<string, BookArgument[]>();

export function bookArguments(workId: string, books: number): BookArgument[] {
  const hit = cache.get(workId);
  if (hit) return hit;

  const argumentsByBook: BookArgument[] = [];
  for (let book = 1; book <= books; book++) {
    try {
      const raw = JSON.parse(
        readFileSync(`public/data/${workId}/book-${String(book).padStart(2, '0')}.json`, 'utf-8'),
      ) as {
        apparatus?: { argument?: unknown; draft?: unknown };
        segments?: Array<{ greek?: Array<{ n?: unknown; text?: unknown }> }>;
      };
      const apparatus = raw.apparatus;
      // A verse book's emitted text is split into segments, each carrying its
      // Greek line array. Count only actual numbered, non-empty text lines;
      // this excludes any structural/empty entries in a partial data file.
      const lines = raw.segments?.reduce(
        (total, segment) => total + (segment.greek?.filter(
          (line) => typeof line.n === 'number' && typeof line.text === 'string' && line.text.trim().length > 0,
        ).length ?? 0),
        0,
      );
      argumentsByBook.push({
        argument: typeof apparatus?.argument === 'string' ? apparatus.argument : undefined,
        draft: apparatus?.draft === true,
        lines,
      });
    } catch {
      // A partial build may not have emitted every book yet. Its link remains
      // usable, exactly as it was before this optional summary was added.
      argumentsByBook.push({});
    }
  }

  cache.set(workId, argumentsByBook);
  return argumentsByBook;
}
