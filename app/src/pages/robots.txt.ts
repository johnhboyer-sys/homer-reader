// Dynamic robots.txt, derived from Astro's `site` config (astro.config.mjs)
// instead of a hardcoded origin. The previous static public/robots.txt
// hardcoded `https://johnhboyer-sys.github.io/homer-reader/sitemap-index.xml`
// — a real-looking GitHub Pages URL, but NOT what `site` is actually set to
// (currently `https://example.invalid`, an explicit TODO placeholder per
// astro.config.mjs; the real domain is John's call, per CLAUDE.md's
// naming/domains human gate). Publishing a Sitemap: line for either the
// placeholder or a guessed-but-unconfirmed domain would be dishonest, so:
// once `site` names a real (non-placeholder) host, this emits the Sitemap
// directive built from it; until then, robots.txt omits the directive
// entirely (still valid — search engines can be pointed at the sitemap via
// Search Console instead, per docs/LAUNCH-CHECKLIST.md).
import type { APIContext } from 'astro';

const PLACEHOLDER_HOSTS = new Set(['example.invalid']);

export function GET({ site }: APIContext): Response {
  const base = import.meta.env.BASE_URL;
  const lines = ['User-agent: *', 'Allow: /'];
  if (site && !PLACEHOLDER_HOSTS.has(site.hostname)) {
    lines.push('', `Sitemap: ${new URL(`${base}sitemap-index.xml`, site).href}`);
  }
  return new Response(lines.join('\n') + '\n', {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
