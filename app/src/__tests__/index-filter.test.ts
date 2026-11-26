// The filter chips on /characters/ and /places/.
//
// Round-3 review findings, each reproduced here before it was fixed:
//   - /characters/ handed wireIndexFilter the selector `.chars-key [data-poem]`,
//     which matches the chip button AND the colour mark inside it (both carry
//     data-poem). A click on the mark pressed both; a click on the label then
//     released only the button, so the roster stayed filtered with no chip
//     showing as pressed.
//   - a pressed certainty chip on /places/ set its label in the chip's own
//     background colour (1:1 contrast): the label's span names its own colour.
//
// The selectors and the stylesheet are read from the pages themselves, so the
// test fails if a page goes back to the wide selector.
import { describe, it, expect, beforeEach } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { wireIndexFilter } from '../lib/index-filter';

const src = (rel: string) => readFileSync(path.resolve(process.cwd(), rel), 'utf-8');
const chipsSelector = (page: string): string => {
  const m = src(page).match(/chips:\s*'([^']+)'/);
  if (!m) throw new Error(`no chips selector in ${page}`);
  return m[1];
};

describe('character chips: the mark inside a chip is not a second chip', () => {
  const selector = chipsSelector('src/pages/characters/index.astro');
  const iliad = () => document.querySelector<HTMLButtonElement>('button[data-poem="iliad"]')!;
  const hidden = () => document.querySelectorAll('.pg-entry[hidden]').length;

  beforeEach(() => {
    // The page's own markup for the group and two roster rows.
    document.body.innerHTML = `
      <input type="search" id="chars-find" />
      <div class="chars-key" role="group">
        <ul class="pg-chips">
          <li><button type="button" class="pg-chip" data-poem="iliad" aria-pressed="false"><span class="poem-mark" data-poem="iliad" aria-hidden="true"></span>Iliad</button></li>
          <li><button type="button" class="pg-chip" data-poem="odyssey" aria-pressed="false"><span class="poem-mark" data-poem="odyssey" aria-hidden="true"></span>Odyssey</button></li>
        </ul>
      </div>
      <span id="chars-count"></span>
      <ol id="roster-list">
        <li class="pg-entry" data-id="hector" data-name="Hector" data-poem="iliad" data-letter="H"></li>
        <li class="pg-entry" data-id="circe" data-name="Circe" data-poem="odyssey" data-letter="C"></li>
      </ol>`;
    wireIndexFilter({ list: 'roster-list', input: 'chars-find', count: 'chars-count', chips: selector, chipKey: 'poem' });
  });

  it('binds one control per chip', () => {
    expect(document.querySelectorAll(selector)).toHaveLength(2);
  });

  it('a click on the mark, then on the label, leaves nothing filtered', () => {
    iliad().querySelector<HTMLElement>('.poem-mark')!.click();
    expect(iliad().getAttribute('aria-pressed')).toBe('true');
    expect(hidden()).toBe(1);
    iliad().click();
    expect(iliad().getAttribute('aria-pressed')).toBe('false');
    expect(hidden()).toBe(0);
    expect(document.getElementById('chars-count')!.textContent).toBe('');
  });

  it('no element but a chip button ever carries the pressed state', () => {
    iliad().querySelector<HTMLElement>('.poem-mark')!.click();
    expect(document.querySelectorAll('[aria-pressed]:not(button)')).toHaveLength(0);
  });
});

describe('place chips', () => {
  it('binds the four tier buttons only', () => {
    const selector = chipsSelector('src/pages/places/index.astro');
    document.body.innerHTML = `<div class="places-legend"><ul class="pg-chips">${['certain', 'traditional', 'speculative', 'mythical']
      .map((t) => `<li><button type="button" class="pg-chip" data-tier="${t}" aria-pressed="false"><span class="pg-tier certainty-label" data-certainty="${t}">${t}</span></button></li>`)
      .join('')}</ul></div>`;
    const hit = Array.from(document.querySelectorAll(selector));
    expect(hit).toHaveLength(4);
    expect(hit.every((el) => el.tagName === 'BUTTON')).toBe(true);
  });
});

// A pressed chip is filled with the text colour. Anything inside it that
// names its own colour has to be told to take the chip's instead, or it is
// set in the fill. The check reads the stylesheet: every class that sits
// inside a chip on these pages and declares `color` needs a pressed rule.
describe('pressed chip: the label is not set in the fill colour', () => {
  const css = src('src/styles/edition-pages.css').replace(/\/\*[\s\S]*?\*\//g, '');
  const rules = Array.from(css.matchAll(/([^{}]+)\{([^{}]*)\}/g)).map((m) => ({ sel: m[1].trim(), body: m[2] }));
  const decl = (body: string, prop: string) => body.match(new RegExp(`(?:^|;)\\s*${prop}\\s*:\\s*([^;]+)`))?.[1].trim();

  it('the pressed chip fills with --text and sets its own text in --page-bg', () => {
    const pressed = rules.find((r) => r.sel === '.pg-chip[aria-pressed="true"]');
    expect(pressed).toBeDefined();
    expect(decl(pressed!.body, 'background')).toBe('var(--text)');
    expect(decl(pressed!.body, 'color')).toBe('var(--page-bg)');
  });

  it('.pg-tier names its own colour, so a pressed chip overrides it', () => {
    const tier = rules.find((r) => r.sel === '.pg-tier');
    expect(decl(tier!.body, 'color')).toBe('var(--text)');
    const fix = rules.find((r) => r.sel.split(',').map((s) => s.trim()).includes('.pg-chip[aria-pressed="true"] .pg-tier'));
    expect(fix, 'no rule for .pg-chip[aria-pressed="true"] .pg-tier').toBeDefined();
    expect(decl(fix!.body, 'color')).toBe('inherit');
  });
});
