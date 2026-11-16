// Baseline of Homer's search before the port of aristotle-reader's new search.
// Adapted from aristotle-reader app/scripts/search-counts.mjs (origin/main).
// Homer's search keeps its modes in the form, not the URL (only g, e, w, b, spk,
// so and gr are URL parameters), so each query either opens a URL or fills the
// form and submits it. It records the bar's text, the total and the page count.
//
// Usage: node docs/search-port/search-counts.mjs --base http://localhost:PORT --out FILE.json
// Serve a build of app/dist first (e.g. `npx astro preview` in app/, reading the
// bound port from the log).
import { createRequire } from 'node:module';
import { existsSync, readdirSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
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

// Each query: URL parameters, then optional form steps. With steps, the script
// fills the form and presses the step named `run`; without, the URL runs it.
const greek = (text, opts = {}) => [
  ['fill', '#grk-input', text],
  ...(opts.mode ? [['check', `input[name="grkmode"][value="${opts.mode}"]`]] : []),
  ...(opts.form ? [['check', 'input[name="matchmode"][value="form"]']] : []),
  ...(opts.accents ? [['check', '.mode-group input[type="checkbox"]']] : []),
];
const queries = [
  ['Greek lemma, μῆνις', { g: 'μῆνις' }],
  ['Greek lemma, θάλασσα', { g: 'θάλασσα' }],
  ['Greek exact form, θαλάσσης', {}, [...greek('θαλάσσης', { form: true }), ['run', 'form.search-form button[type="submit"]']]],
  ['Greek exact phrase, οἴνοπα πόντον', {}, [...greek('οἴνοπα πόντον', { mode: 'phrase', form: true }), ['run', 'form.search-form button[type="submit"]']]],
  ['Greek any word, ἄναξ ἀνδρῶν', {}, [...greek('ἄναξ ἀνδρῶν', { mode: 'any' }), ['run', 'form.search-form button[type="submit"]']]],
  ['Greek accents exactly, θεά', {}, [...greek('θεά', { form: true, accents: true }), ['run', 'form.search-form button[type="submit"]']]],
  ['English word, sea', { e: 'sea' }],
  ['English phrase, rosy-fingered dawn', {}, [['fill', '#eng-input', 'rosy-fingered dawn'], ['check', 'input[name="engmode"][value="phrase"]'], ['run', 'form.search-form button[type="submit"]']]],
  // The hyphenated query above finds nothing today (pre-port defect); the same
  // phrase without the hyphen finds the formula.
  ['English phrase, rosy fingered dawn (no hyphen)', {}, [['fill', '#eng-input', 'rosy fingered dawn'], ['check', 'input[name="engmode"][value="phrase"]'], ['run', 'form.search-form button[type="submit"]']]],
  ['English word, fingered', { e: 'fingered' }],
  ['Both, and: θάλασσα + sea', { g: 'θάλασσα', e: 'sea' }],
  ['Both, or: θάλασσα + sea', {}, [['fill', '#grk-input', 'θάλασσα'], ['fill', '#eng-input', 'sea'], ['check', 'input[name="op"][value="or"]'], ['run', 'form.search-form button[type="submit"]']]],
  ['Work and book: Ὀδυσσεύς, Od. 9', { g: 'Ὀδυσσεύς', w: 'odyssey', b: '9' }],
  ['Speaker: θεός spoken by Achilles', { g: 'θεός', spk: 'achilles' }],
  ['Speeches only: θεός', { g: 'θεός', so: '1' }],
  ['Every form of one word: ἔπεα', {}, [['open', 'details.lemma-panel'], ['fill', '#solo-word-input', 'ἔπεα'], ['run', 'details.lemma-panel button.search-btn']]],
  ['Near: πούς near ὠκύς, 3 words', {}, [
    ['open', 'details.combo-panel'],
    ['select', 'details.combo-panel .combo-slot:nth-of-type(1) select', 'lemma'],
    ['fill', 'details.combo-panel .combo-slot:nth-of-type(1) input[type="text"]', 'πούς'],
    ['select', 'details.combo-panel .combo-slot:nth-of-type(2) select', 'lemma'],
    ['fill', 'details.combo-panel .combo-slot:nth-of-type(2) input[type="text"]', 'ὠκύς'],
    ['fill', 'details.combo-panel .combo-window input', '3'],
    ['run', 'details.combo-panel button.combo-search-btn'],
  ]],
  ['Grammar in one book: optatives, Il. 1', { w: 'iliad', b: '1', gr: 'mood:opt' }],
];

const COUNT = /^(?:([\d,]+) (?:instances?|words?)|No passages found)/;
// The site's warnings for an index, a book's text or the speech data that failed to load.
const PARTIAL = /Incomplete results|couldn['’]t load|didn['’]t load|did not load|failed to load/;
// Playwright's own browser build may be missing from the cache (versions drift);
// fall back to the installed Google Chrome.
const { chromium } = resolvePlaywright();
const browser = await chromium.launch({ headless: true })
  .catch(() => chromium.launch({ headless: true, channel: 'chrome' }));
const results = [];
try {
  const page = await browser.newPage();
  for (const [name, params, steps = []] of queries) {
    try {
      const qs = new URLSearchParams(params).toString();
      const url = new URL(`/search/${qs ? `?${qs}` : ''}`, flag('--base')).href;
      await page.goto(url);
      await page.evaluate(() => document.fonts.ready);
      for (const [op, sel, value] of steps) {
        const el = page.locator(sel).first();
        if (op === 'open') await el.evaluate(d => { d.open = true; });
        else if (op === 'fill') await el.fill(value);
        else if (op === 'check') await el.check();
        else if (op === 'select') await el.selectOption(value);
        else if (op === 'run') await el.click();
      }
      // The bar settles when its text reads as a count and stops changing
      // (the speaker and speeches filters re-filter after speech data loads).
      let last = '';
      await page.waitForFunction((re) => {
        const err = document.querySelector('.search-error');
        if (err?.textContent?.trim()) throw new Error(err.textContent.trim());
        if ([...document.querySelectorAll('.filter-note')].some(n => /Loading/.test(n.textContent))) return false;
        const t = document.querySelector('.result-count')?.textContent?.trim();
        return t && new RegExp(re).test(t);
      }, COUNT.source, { timeout: 120000 });
      // A speaker or speeches filter first shows the unfiltered (or empty) bar,
      // then re-filters once speech data arrives: wait for the fetches to end.
      if (params.spk || params.so) await page.waitForLoadState('networkidle', { timeout: 120000 });
      // Settled = the same text on four reads 500 ms apart.
      let same = 0;
      for (let i = 0; i < 40 && same < 3; i++) {
        await page.waitForTimeout(500);
        const t = await page.locator('.result-count').first().textContent();
        same = t === last ? same + 1 : 0;
        last = t;
      }
      if (same < 3) throw new Error(`the bar never settled (last read: ${last})`);
      const shown = last.trim().replace(/\s+/g, ' ');
      const m = shown.match(COUNT);
      // The total is set before page 1's books load: wait for its groups.
      if (m[1] && !/ words?\b/.test(shown)) {
        await page.waitForFunction(() => document.querySelectorAll('.group-count').length > 0, null, { timeout: 120000 });
        await page.waitForLoadState('networkidle');
      }
      // A failed index, book or speech file leaves a short count on screen with
      // a warning beside it. Never record that as the baseline.
      const warning = await page.evaluate((re) => document.body.innerText.match(new RegExp(re, 'i'))?.[0], PARTIAL.source);
      if (warning) throw new Error(`partial results ("${warning}"); re-run`);
      const pages = shown.match(/page \d+ of (\d+)/i);
      const total = m[1] ? Number(m[1].replaceAll(',', '')) : 0;
      const groups = await page.locator('.group-count').count();
      results.push({ name, url, steps: steps.length ? steps : undefined, total, pages: pages ? Number(pages[1]) : total ? 1 : 0, groupsOnPage1: groups, shown });
      console.log(name, '→', shown);
    } catch (error) { throw new Error(`${name}: ${error.message}`, { cause: error }); }
  }
  writeFileSync(flag('--out'), JSON.stringify(results, null, 2) + '\n');
} finally { await browser.close(); }
