// Build-time SSR channel between ReaderShell.astro and the Reader island.
//
// The reading text is server-rendered into the static HTML by the Reader island,
// but the island's props are ALSO serialized into the page (Astro hydration), so
// passing the full book both ways double-ships it — and the Greek token arrays
// (~half the book) merely duplicate the token spans the server render already
// emitted. To avoid that, ReaderShell stashes the FULL book here (with tokens)
// just before rendering the island, then passes the island a token-stripped copy
// (stripBookForClient) as its serialized props. During the server render the
// island pulls the full book out of this channel so the static markup still
// carries every token span; on the client it rebuilds tokens from those spans.
//
// Server-only: the value is set during SSG frontmatter and read once by the
// island's server render (takeSsrBook clears it, so it never leaks to the next
// page). In the browser the module value is always null — the client uses the
// stripped prop and the DOM instead.
import type { BookData } from './data';

let _ssrBook: BookData | null = null;

export function setSsrBook(b: BookData | null): void {
  _ssrBook = b;
}

// Read and clear the stashed book. Returns null on the client (never set there)
// and after the first read on the server, so a stale book can't bleed across
// pages during a static build.
export function takeSsrBook(): BookData | null {
  const b = _ssrBook;
  _ssrBook = null;
  return b;
}
