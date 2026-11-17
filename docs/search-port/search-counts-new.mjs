// The baseline searches of search-counts.mjs, run on the NEW search page (the
// port of aristotle-reader's, lane C). The new page keeps its whole search in
// the address, so every query is a URL; the old form steps are written as the
// parameters the new page reads (lib/search-url.ts). It records the bar: the
// scenes (the unit since the port), the hits where the bar counts them, and
// the pages, beside the old total from counts-base-2026-11-16.json.
//
// Usage: node docs/search-port/search-counts-new.mjs --base http://localhost:PORT --out FILE.json [--pages]
// --pages (ported from aristotle-reader PR #208): walk every page by the
// pager's Next and record each page's rows in order, each as its scene and
// citation (with its reader link), so two builds can be compared row for row
// with search-counts-compare.mjs.
// Serve a build of app/dist first (`npx astro preview` in app/, reading the
// bound port from the log).
import { createRequire } from 'node:module';
import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
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
const flag = name => args[args.indexOf(name) + 1];
if (!args.includes('--base') || !args.includes('--out')) throw new Error('Usage: --base URL --out FILE.json');
const base = JSON.parse(readFileSync(join(dirname(fileURLToPath(import.meta.url)), 'counts-base-2026-11-16.json'), 'utf8'));
const oldTotal = name => base.find(r => r.name === name)?.shown;
const walk = args.includes('--pages');

// [name as in the baseline, the new page's parameters]. A row whose name the
// baseline lacks is new (the old page searched Murray alone; the new searches
// every translation, so both readings are listed).
const queries = [
  ['Greek lemma, μῆνις', { g: 'μῆνις' }],
  ['Greek lemma, θάλασσα', { g: 'θάλασσα' }],
  ['Greek exact form, θαλάσσης', { g: 'θαλάσσης', m: 'form' }],
  ['Greek exact phrase, οἴνοπα πόντον', { g: 'οἴνοπα πόντον', gm: 'phrase', m: 'form' }],
  ['Greek any word, ἄναξ ἀνδρῶν', { g: 'ἄναξ ἀνδρῶν', gm: 'any' }],
  ['Greek accents exactly, θεά', { g: 'θεά', m: 'form', acc: '1' }],
  ['English word, sea', { e: 'sea' }],
  ['English word, sea (Murray, exact form)', { e: 'sea', t: 'murray', ef: '0' }],
  ['English phrase, rosy-fingered dawn', { e: 'rosy-fingered dawn', em: 'phrase' }],
  ['English phrase, rosy fingered dawn (no hyphen)', { e: 'rosy fingered dawn', em: 'phrase' }],
  ['English word, fingered', { e: 'fingered' }],
  ['Both, and: θάλασσα + sea', { g: 'θάλασσα', e: 'sea', op: 'and' }],
  ['Both, and: θάλασσα + sea (Murray, exact form)', { g: 'θάλασσα', e: 'sea', op: 'and', t: 'murray', ef: '0' }],
  ['Both, or: θάλασσα + sea', { g: 'θάλασσα', e: 'sea', op: 'or' }],
  // The switch reads and | and/or | or (aristotle-reader 47444b1f5c): a link
  // from before it with no op still means "and"; a search typed into a blank
  // page with the switch untouched is "and/or"; op=xor is one language, not both.
  ['Both, a link with no op (and): θάλασσα + sea', { g: 'θάλασσα', e: 'sea' }],
  ['Both, typed into a blank page (and/or): θάλασσα + sea', { typed: { g: 'θάλασσα', e: 'sea' } }],
  ['Both, xor (or: one language, not both): θάλασσα + sea', { g: 'θάλασσα', e: 'sea', op: 'xor' }],
  ['Work and book: Ὀδυσσεύς, Od. 9', { g: 'Ὀδυσσεύς', w: 'odyssey', b: '9' }],
  ['Speaker: θεός spoken by Achilles', { g: 'θεός', spk: 'achilles' }],
  ['Speeches only: θεός', { g: 'θεός', so: '1' }],
  ['Speeches only: θεός (spo=1)', { g: 'θεός', spo: '1' }],
  ['Every form of one word: ἔπεα', { l: 'epos' }],
  ['Near: πούς near ὠκύς, 3 words', { c: ['l:pous', 'l:wkus'], cw: '3' }],
  ['Grammar in one book: optatives, Il. 1', { w: 'iliad', b: '1', gr: 'mood:opt' }],
  // The two views whose rows split an instance (Search.svelte rowsIn): by
  // form, one row per form; by grammar, one per headword it is filed under.
  ['By form: ὁ, Il. 1, 20 a page', { g: 'ὁ', w: 'iliad', b: '1', ps: '20', v: 'form' }],
  ['By grammar: ὁ and ὅς, Il. 1, 20 a page', { l: 'o,os', v: 'grammar', w: 'iliad', b: '1', ps: '20' }],
];

// Every page's rows, from the first to the last, by the pager's Next. A row
// is its scene (the heading above it), the group it is filed under by form or
// by grammar, its citation and its reader link. By grammar each headword's
// spellings open first: their rows are drawn only when open.
async function pageRows(page) {
  const rows = [];
  for (let i = 1; ; i++) {
    await page.waitForFunction(n => {
      const status = document.querySelector('.pager-status')?.textContent ?? '';
      const drawn = document.querySelectorAll('li.instance, button.sx-para').length > 0;
      return drawn && !/Loading/.test(status) && (n === 1 ? !status || !/…/.test(status) : status.startsWith(`Page ${n} `));
    }, i, { timeout: 120000 });
    for (let k = 0; k < 50; k++) {
      const shut = page.locator('button.sx-para[aria-expanded="false"]');
      if (!(await shut.count())) break;
      await shut.first().click();
    }
    rows.push(await page.evaluate(() => {
      const t = el => el?.textContent?.replace(/\s+/g, ' ').trim() ?? '';
      let group = '';
      let para = '';
      let scene = '';
      const out = [];
      for (const el of document.querySelectorAll('.sx-results h2 .group-head, button.sx-para, .sx-book, .sx-chap-n, li.instance')) {
        if (el.matches('h2 .group-head')) { group = t(el.querySelector('.group-label, .work-name')); para = ''; scene = ''; continue; }
        if (el.matches('button.sx-para')) { para = t(el.querySelector('.group-label')) + ' ' + t(el.querySelector('.sx-para-sp')); scene = ''; continue; }
        if (el.matches('.sx-book')) { scene = ''; continue; }
        if (el.matches('.sx-chap-n')) { scene = t(el); continue; }
        const a = el.querySelector('a.inst-ref, a.cmp-ref, .cmp-ref');
        const href = a?.getAttribute?.('href') ?? '';
        out.push(`${group}${para ? ` / ${para.trim()}` : ''} | ${scene} | ${t(a)} | ${href.replace(/^https?:\/\/[^/]+/, '')}`);
      }
      return out;
    }));
    const next = page.locator('button.pager-next').first();
    if (!(await next.count()) || await next.isDisabled()) break;
    await next.click();
  }
  return rows;
}

const COUNT = /^(?:(\d[\d,]*) scenes?(?: (\d[\d,]*) hits?)?|No scenes found)/;
const PARTIAL = /couldn['’]t load|didn['’]t load|did not load|failed to load/;
const { chromium } = resolvePlaywright();
const browser = await chromium.launch({ headless: true })
  .catch(() => chromium.launch({ headless: true, channel: 'chrome' }));
const results = [];
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  for (const [name, params] of queries) {
    try {
      const qs = new URLSearchParams();
      if (!params.typed) for (const [k, v] of Object.entries(params)) for (const x of [v].flat()) qs.append(k, x);
      let url = new URL(`/search/?${qs}`, flag('--base')).href;
      await page.goto(url);
      if (params.typed) {
        await page.fill('#grk-input', params.typed.g);
        await page.fill('#eng-input', params.typed.e);
        await page.click('button.search-btn');
        await page.waitForURL(u => u.search.includes('e='));
        url = page.url();
      }
      await page.waitForFunction(() => {
        const err = document.querySelector('.search-error');
        if (err?.textContent?.trim()) throw new Error(err.textContent.trim());
        // Pages are rows, counted as the books load: "page 1 of …" until they have.
        const status = document.querySelector('[role="status"]')?.textContent?.trim() ?? '';
        return /scenes? ·|scenes?$|No scenes found/.test(status) && !/of …/.test(status);
      }, null, { timeout: 120000 });
      await page.waitForLoadState('networkidle', { timeout: 120000 });
      // Settled: the same bar on four reads 500 ms apart.
      let last = '';
      let same = 0;
      for (let i = 0; i < 40 && same < 3; i++) {
        await page.waitForTimeout(500);
        const t = (await page.locator('[role="status"]').first().textContent())?.trim() ?? '';
        same = t === last ? same + 1 : 0;
        last = t;
      }
      if (same < 3) throw new Error(`the bar never settled (last read: ${last})`);
      const warning = await page.evaluate((re) => document.querySelector('.sx-notes, .search-note')?.textContent?.match(new RegExp(re, 'i'))?.[0], PARTIAL.source);
      if (warning) throw new Error(`partial results ("${warning}"); re-run`);
      const shown = last.replace(/\s+/g, ' ');
      const m = shown.replace(' · ', ' ').match(COUNT);
      const pages = shown.match(/page \d+ of (\d+)/i);
      const scenes = m?.[1] ? Number(m[1].replaceAll(',', '')) : 0;
      const hits = m?.[2] ? Number(m[2].replaceAll(',', '')) : null;
      const counts = { name, url, scenes, hits, pages: pages ? Number(pages[1]) : scenes ? 1 : 0, shown, before: oldTotal(name) ?? null };
      if (walk) counts.rows = await pageRows(page);
      results.push(counts);
      console.log(`${name} → ${shown}${oldTotal(name) ? `   (old page: ${oldTotal(name)})` : ''}${walk ? `; ${counts.rows.flat().length} rows on ${counts.rows.length} pages` : ''}`);
    } catch (error) { throw new Error(`${name}: ${error.message}`, { cause: error }); }
  }
  writeFileSync(flag('--out'), JSON.stringify(results, null, 2) + '\n');
} finally { await browser.close(); }
