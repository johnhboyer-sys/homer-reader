// Screenshots of a search page at phone, sideways and desktop widths, in both
// themes, for John's ruling on the look of Homer's search after the port.
// Both readers keep the theme in localStorage 'ne-theme' ('dark' | 'light').
//
// Usage: node docs/search-port/shots.mjs --base URL --path '/search/?g=…' --prefix NAME --out DIR [--open SELECTOR]
// --open clicks the first element matching SELECTOR before the shot (Homer folds
// a book's hits under a closed header; '.group-head[aria-expanded="false"]' opens it).
import { createRequire } from 'node:module';
import { existsSync, mkdirSync, readdirSync } from 'node:fs';
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
const flag = name => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
for (const f of ['--base', '--path', '--prefix', '--out']) if (!flag(f)) throw new Error(`Missing ${f}`);
mkdirSync(flag('--out'), { recursive: true });

// width, height of the viewport, and how much of the page to keep.
const SIZES = [
  ['phone', 390, 844, 2600],
  ['sideways', 844, 390, 1700],
  ['desktop', 1440, 900, 1800],
];
// The bar reads as a count once the search has run (Homer: .result-count;
// Aristotle: [role="status"]).
const READY = () => {
  const t = (document.querySelector('[role="status"]')?.textContent || '')
    + ' ' + (document.querySelector('.result-count')?.textContent || '');
  return /\d[\d,]* (instances?|passages?|hits?|chapters?)|No passages found/.test(t);
};

const { chromium } = resolvePlaywright();
const browser = await chromium.launch({ headless: true })
  .catch(() => chromium.launch({ headless: true, channel: 'chrome' }));
try {
  for (const theme of ['light', 'dark']) {
    for (const [label, width, height, keep] of SIZES) {
      const context = await browser.newContext({
        viewport: { width, height }, deviceScaleFactor: 2, colorScheme: theme,
        isMobile: width < 768, hasTouch: width < 768,
      });
      await context.addInitScript(t => { try { localStorage.setItem('ne-theme', t); } catch {} }, theme);
      const page = await context.newPage();
      // A slow local server can make an index miss the page's load window, and
      // the page then shows a "did not load" warning and a short count. Retry.
      for (let attempt = 1; ; attempt++) {
        await page.goto(new URL(flag('--path'), flag('--base')).href);
        await page.evaluate(() => document.fonts.ready);
        await page.waitForFunction(READY, null, { timeout: 120000 });
        await page.waitForLoadState('networkidle');
        if (!(await page.evaluate(() => /did not load/i.test(document.body.innerText)))) break;
        if (attempt === 3) throw new Error(`${label} ${theme}: an index did not load, three times`);
        console.warn(`${label} ${theme}: an index did not load; retrying`);
      }
      if (flag('--open')) {
        await page.locator(flag('--open')).first().click();
        await page.waitForLoadState('networkidle');
        await page.evaluate(() => window.scrollTo(0, 0)); // else a sticky header lands mid-shot
      }
      await page.waitForTimeout(800);
      const full = await page.evaluate(() => document.documentElement.scrollHeight);
      const file = join(flag('--out'), `${flag('--prefix')}-${label}-${theme}.jpg`);
      await page.screenshot({ path: file, type: 'jpeg', quality: 72, fullPage: true,
        clip: { x: 0, y: 0, width, height: Math.min(full, keep) } });
      console.log(file);
      await context.close();
    }
  }
} finally { await browser.close(); }
