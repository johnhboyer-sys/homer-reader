// The baseline searches of search-counts.mjs, run on the NEW search page (the
// port of aristotle-reader's, lane C). The new page keeps its whole search in
// the address, so every query is a URL; the old form steps are written as the
// parameters the new page reads (lib/search-url.ts). It records the bar: the
// scenes (the unit since the port), the hits where the bar counts them, and
// the pages, beside the old total from counts-base-2026-11-16.json.
//
// Usage: node docs/search-port/search-counts-new.mjs --base http://localhost:PORT --out FILE.json
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
  ['Work and book: Ὀδυσσεύς, Od. 9', { g: 'Ὀδυσσεύς', w: 'odyssey', b: '9' }],
  ['Speaker: θεός spoken by Achilles', { g: 'θεός', spk: 'achilles' }],
  ['Speeches only: θεός', { g: 'θεός', so: '1' }],
  ['Speeches only: θεός (spo=1)', { g: 'θεός', spo: '1' }],
  ['Every form of one word: ἔπεα', { l: 'epos' }],
  ['Near: πούς near ὠκύς, 3 words', { c: ['l:pous', 'l:wkus'], cw: '3' }],
  ['Grammar in one book: optatives, Il. 1', { w: 'iliad', b: '1', gr: 'mood:opt' }],
];

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
      for (const [k, v] of Object.entries(params)) for (const x of [v].flat()) qs.append(k, x);
      const url = new URL(`/search/?${qs}`, flag('--base')).href;
      await page.goto(url);
      await page.waitForFunction(() => {
        const err = document.querySelector('.search-error');
        if (err?.textContent?.trim()) throw new Error(err.textContent.trim());
        return /scenes? ·|scenes?$|No scenes found/.test(document.querySelector('[role="status"]')?.textContent?.trim() ?? '');
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
      results.push({ name, url, scenes, hits, pages: pages ? Number(pages[1]) : scenes ? 1 : 0, shown, before: oldTotal(name) ?? null });
      console.log(`${name} → ${shown}${oldTotal(name) ? `   (old page: ${oldTotal(name)})` : ''}`);
    } catch (error) { throw new Error(`${name}: ${error.message}`, { cause: error }); }
  }
  writeFileSync(flag('--out'), JSON.stringify(results, null, 2) + '\n');
} finally { await browser.close(); }
