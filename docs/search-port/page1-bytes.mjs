// What page 1 of a search reads (after aristotle-reader's gate R-S8, PR #208,
// which Homer has no check-redesign.mjs to hold): every /data/ response the
// page fetches until it has drawn page 1 and the network is idle, raw and
// gzipped (zlib's default level), the book files apart, and the books page 1
// draws (from its rows' reader links). Service workers are blocked, so each
// response is a fetch.
//
// Usage: node docs/search-port/page1-bytes.mjs --base URL [--path '/search/?…']
//          [--max-books N] [--max-book-gzip BYTES] [--out FILE.json]
// With --max-books or --max-book-gzip it is a check: it exits 1 when page 1
// reads a book it does not draw, more books than N, or more than BYTES of book
// data gzipped.
import { createRequire } from 'node:module';
import { existsSync, readdirSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { gzipSync } from 'node:zlib';
const require = createRequire(import.meta.url);
function resolvePlaywright() {
  try { return require('playwright'); } catch {}
  const root = join(homedir(), '.npm', '_npx');
  if (existsSync(root)) for (const hash of readdirSync(root)) {
    const p = join(root, hash, 'node_modules', 'playwright');
    if (existsSync(p)) return require(p);
  }
  throw new Error('Playwright not found in the project or npm cache');
}
if (!process.env.PLAYWRIGHT_BROWSERS_PATH) {
  const cache = join(homedir(), 'Library', 'Caches', 'ms-playwright');
  if (existsSync(cache)) process.env.PLAYWRIGHT_BROWSERS_PATH = cache;
}
const args = process.argv.slice(2);
const flag = name => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
if (!flag('--base')) throw new Error('Usage: --base URL [--path PATH] [--max-books N] [--max-book-gzip BYTES] [--out FILE]');
const path = flag('--path') ?? `/search/?g=${encodeURIComponent('θάλασσα')}&e=sea&op=or`;

const { chromium } = resolvePlaywright();
const browser = await chromium.launch({ headless: true })
  .catch(() => chromium.launch({ headless: true, channel: 'chrome' }));
let failed = false;
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, serviceWorkers: 'block' });
  const page = await context.newPage();
  const reads = [];
  const pending = [];
  page.on('response', r => {
    const at = new URL(r.url()).pathname;
    if (!at.includes('/data/')) return;
    pending.push(r.body().then(b => { reads.push({ path: at.replace(/^.*\/data\//, ''), raw: b.length, gzip: gzipSync(b).length }); }).catch(() => {}));
  });
  await page.goto(new URL(path, flag('--base')).href);
  await page.waitForFunction(() => {
    const status = document.querySelector('.pager-status')?.textContent ?? '';
    return document.querySelectorAll('li.instance').length > 0 && !/Loading/.test(status);
  }, null, { timeout: 120000 });
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  await page.waitForLoadState('networkidle');
  await Promise.all(pending);
  const drawn = [...new Set(await page.$$eval('li.instance a.inst-ref', as => as.map(a => {
    const m = new URL(a.href).pathname.match(/\/(iliad|odyssey)\/book\/(\d+)/);
    return m ? `${m[1]}/book-${m[2].padStart(2, '0')}.json` : '';
  })))].sort();
  const rows = await page.locator('li.instance').count();
  const status = (await page.locator('.pager-status').first().textContent().catch(() => ''))?.trim();
  const sum = (list, k) => list.reduce((n, r) => n + r[k], 0);
  const books = reads.filter(r => /\/book-\d+\.json$/.test(r.path)).sort((x, y) => x.path.localeCompare(y.path));
  const out = {
    path, rows, status, drawn,
    books: { count: books.length, raw: sum(books, 'raw'), gzip: sum(books, 'gzip'), files: books.map(r => r.path) },
    data: { count: reads.length, raw: sum(reads, 'raw'), gzip: sum(reads, 'gzip') },
    reads: reads.sort((x, y) => y.raw - x.raw),
  };
  console.log(`${path}: ${rows} rows (${status}) drawn from ${drawn.join(', ')}`);
  console.log(`  book files: ${out.books.count}, ${out.books.raw.toLocaleString('en')} bytes raw, ${out.books.gzip.toLocaleString('en')} gzip`);
  console.log(`  all /data/: ${out.data.count} files, ${out.data.raw.toLocaleString('en')} bytes raw, ${out.data.gzip.toLocaleString('en')} gzip`);
  for (const r of out.reads.slice(0, 12)) console.log(`    ${r.path} ${r.raw.toLocaleString('en')} / ${r.gzip.toLocaleString('en')}`);
  if (flag('--out')) writeFileSync(flag('--out'), JSON.stringify(out, null, 2) + '\n');
  const stray = books.map(r => r.path).filter(b => !drawn.includes(b));
  const maxBooks = flag('--max-books') && Number(flag('--max-books'));
  const maxGzip = flag('--max-book-gzip') && Number(flag('--max-book-gzip'));
  if (maxBooks !== undefined || maxGzip !== undefined) {
    const errors = [];
    if (!rows || !drawn.length) errors.push('page 1 drew no rows');
    if (stray.length) errors.push(`page 1 read ${stray.length} book${stray.length === 1 ? '' : 's'} it does not draw: ${stray.slice(0, 6).join(', ')}`);
    if (maxBooks && books.length > maxBooks) errors.push(`page 1 read ${books.length} books, at most ${maxBooks}`);
    if (maxGzip && out.books.gzip > maxGzip) errors.push(`page 1 read ${out.books.gzip.toLocaleString('en')} bytes of books gzipped, at most ${maxGzip.toLocaleString('en')}`);
    for (const e of errors) console.log(`FAIL ${e}`);
    if (!errors.length) console.log('PASS');
    failed = errors.length > 0;
  }
  await context.close();
} finally { await browser.close(); }
process.exit(failed ? 1 : 0);
