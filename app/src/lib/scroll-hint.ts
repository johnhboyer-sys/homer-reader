// A row that scrolls sideways says so. Each scroller gets `data-more`:
// "end" when there is more to its right, "start" when there is more to its
// left, "both", or "" when it all fits. The stylesheet fades the edge that has
// more (edition-pages.css), so a row cut by the screen edge reads as a row
// that goes on, and stops doing so when the reader reaches its end.
//
// Without script there is no attribute and no fade: the row still scrolls.

export type More = '' | 'start' | 'end' | 'both';

/** Which edges of a sideways scroller have content beyond them. */
export function scrollEdges(el: Pick<HTMLElement, 'scrollLeft' | 'scrollWidth' | 'clientWidth'>): More {
  // A pixel of slack: fractional widths leave scrollWidth one over clientWidth
  // on rows that do not scroll at all.
  const start = el.scrollLeft > 1;
  const end = el.scrollLeft + el.clientWidth < el.scrollWidth - 1;
  return start && end ? 'both' : start ? 'start' : end ? 'end' : '';
}

/** Keep `data-more` current on each scroller. Returns the teardown. */
export function initScrollHints(els: Iterable<HTMLElement>): () => void {
  const off: (() => void)[] = [];
  const list = Array.from(els);
  const update = (el: HTMLElement) => {
    const more = scrollEdges(el);
    if (el.dataset.more !== more) el.dataset.more = more;
  };
  const all = () => list.forEach(update);
  for (const el of list) {
    const onScroll = () => update(el);
    el.addEventListener('scroll', onScroll, { passive: true });
    off.push(() => el.removeEventListener('scroll', onScroll));
  }
  // A row's width changes with the window, with fonts arriving, and with
  // filters that hide its items.
  if (typeof ResizeObserver === 'function') {
    const ro = new ResizeObserver(all);
    list.forEach((el) => { ro.observe(el); if (el.firstElementChild) ro.observe(el.firstElementChild); });
    off.push(() => ro.disconnect());
  }
  window.addEventListener('resize', all, { passive: true });
  off.push(() => window.removeEventListener('resize', all));
  all();
  return () => off.forEach((fn) => fn());
}

/** The site's sideways scrollers: jump rows, the timeline strips, the two charts. */
export const SCROLLERS = '.pg-jump, .day-strip-scroll, .voyage-strip-scroll, .cn-scroll, .gen-scroll';
