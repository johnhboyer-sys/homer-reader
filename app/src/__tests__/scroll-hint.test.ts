// Round-2 review finding M4: rows that scroll sideways on a phone were cut at
// the screen edge with nothing to say they scroll. lib/scroll-hint.ts marks
// the edges that have more beyond them; the stylesheet fades those edges.
import { describe, it, expect, afterEach } from 'vitest';
import { initScrollHints, scrollEdges, SCROLLERS } from '../lib/scroll-hint';

function scroller(scrollWidth: number, clientWidth: number, scrollLeft = 0) {
  const el = document.createElement('div');
  el.className = 'pg-jump';
  let left = scrollLeft;
  Object.defineProperty(el, 'scrollWidth', { get: () => scrollWidth, configurable: true });
  Object.defineProperty(el, 'clientWidth', { get: () => clientWidth, configurable: true });
  Object.defineProperty(el, 'scrollLeft', { get: () => left, set: (v: number) => { left = v; }, configurable: true });
  document.body.appendChild(el);
  return el;
}

describe('sideways-scroll hints', () => {
  let teardown: (() => void) | undefined;
  afterEach(() => { teardown?.(); teardown = undefined; document.body.innerHTML = ''; });

  it('reports the edges that have more beyond them', () => {
    expect(scrollEdges({ scrollLeft: 0, scrollWidth: 900, clientWidth: 358 })).toBe('end');
    expect(scrollEdges({ scrollLeft: 200, scrollWidth: 900, clientWidth: 358 })).toBe('both');
    expect(scrollEdges({ scrollLeft: 542, scrollWidth: 900, clientWidth: 358 })).toBe('start');
    expect(scrollEdges({ scrollLeft: 0, scrollWidth: 358, clientWidth: 358 })).toBe('');
  });

  it('does not call a row scrollable over a rounding pixel', () => {
    expect(scrollEdges({ scrollLeft: 0, scrollWidth: 359, clientWidth: 358 })).toBe('');
    expect(scrollEdges({ scrollLeft: 0.5, scrollWidth: 900, clientWidth: 358 })).toBe('end');
  });

  it('marks a cut row on load and follows it as the reader scrolls', () => {
    const row = scroller(900, 358);
    const fits = scroller(300, 358);
    teardown = initScrollHints(document.querySelectorAll<HTMLElement>(SCROLLERS));
    expect(row.dataset.more).toBe('end');
    expect(fits.dataset.more).toBe('');
    row.scrollLeft = 300;
    row.dispatchEvent(new Event('scroll'));
    expect(row.dataset.more).toBe('both');
    row.scrollLeft = 542;
    row.dispatchEvent(new Event('scroll'));
    expect(row.dataset.more).toBe('start');
  });

  it('re-reads every row when the window changes size', () => {
    let width = 358;
    const row = scroller(900, 358);
    Object.defineProperty(row, 'clientWidth', { get: () => width, configurable: true });
    teardown = initScrollHints([row]);
    expect(row.dataset.more).toBe('end');
    width = 1200;
    window.dispatchEvent(new Event('resize'));
    expect(row.dataset.more).toBe('');
  });

  it('stops listening after teardown', () => {
    const row = scroller(900, 358);
    initScrollHints([row])();
    row.scrollLeft = 542;
    row.dispatchEvent(new Event('scroll'));
    expect(row.dataset.more).toBe('end');
  });
});
