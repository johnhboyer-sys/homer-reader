// The site header's Atlas / People / Language menus as real disclosures.
//
// Without script the menus still open on :hover and :focus-within (plain CSS in
// SiteHeader.astro), so every link stays reachable. With script, this module
// takes over: it marks the header `sh-js` (which switches the CSS from
// focus-within to an explicit `is-open` class) and gives each trigger the
// behaviour its `aria-haspopup` promises: click / Enter / Space toggle,
// `aria-expanded` kept true to the state, Escape closes and returns focus to
// the trigger, and a click or focus move outside closes.
//
// A pointer still opens a menu by hovering. A click on a menu opened that way
// keeps it open (pins it) rather than closing it under the pointer; a second
// click closes it.

export function initSiteMenus(header: HTMLElement): () => void {
  const groups = Array.from(header.querySelectorAll<HTMLElement>('.sh-group'));
  const pinned = new WeakSet<HTMLElement>();
  const off: (() => void)[] = [];
  const on = <K extends keyof HTMLElementEventMap>(
    el: HTMLElement | Document,
    type: K,
    fn: (e: HTMLElementEventMap[K]) => void,
  ) => {
    el.addEventListener(type, fn as EventListener);
    off.push(() => el.removeEventListener(type, fn as EventListener));
  };

  const trigger = (g: HTMLElement) => g.querySelector<HTMLElement>('.sh-group-btn');
  const isOpen = (g: HTMLElement) => g.classList.contains('is-open');
  const close = (g: HTMLElement) => {
    g.classList.remove('is-open');
    pinned.delete(g);
    trigger(g)?.setAttribute('aria-expanded', 'false');
  };
  const open = (g: HTMLElement) => {
    groups.forEach((other) => { if (other !== g) close(other); });
    g.classList.add('is-open');
    trigger(g)?.setAttribute('aria-expanded', 'true');
  };

  header.classList.add('sh-js');
  groups.forEach((g) => {
    const btn = trigger(g);
    if (!btn) return;
    btn.setAttribute('aria-expanded', 'false');
    on(btn, 'click', () => {
      if (isOpen(g) && pinned.has(g)) close(g);
      else { open(g); pinned.add(g); }
    });
    on(g, 'mouseenter', () => { if (!isOpen(g)) open(g); });
    // The pointer leaving closes a menu it opened by hovering, but not while
    // keyboard focus is on one of its links: the link would go on holding
    // focus, hidden. Focus leaving the group (focusout, below) closes it then.
    on(g, 'mouseleave', () => { if (!pinned.has(g) && !g.contains(document.activeElement)) close(g); });
    on(g, 'focusout', (e) => {
      const next = e.relatedTarget;
      if (!(next instanceof Node) || !g.contains(next)) close(g);
    });
    on(g, 'keydown', (e) => {
      if (e.key !== 'Escape' || !isOpen(g)) return;
      e.stopPropagation();
      // Focus first: closing on the trigger's own focusout would be a no-op
      // here, but moving focus out of the menu before it hides is the order
      // that never strands it on an invisible link.
      btn.focus();
      close(g);
    });
  });
  on(document, 'click', (e) => {
    const t = e.target;
    groups.forEach((g) => { if (!(t instanceof Node) || !g.contains(t)) close(g); });
  });

  return () => {
    off.forEach((fn) => fn());
    groups.forEach(close);
    header.classList.remove('sh-js');
  };
}

/** Opening the palette from inside the phone sheet closes the sheet under it.
 * A Go-to inside the sheet hands focus to the sheet's Menu summary first: the
 * palette saves the focused element to return to on close, and the link it
 * was opened from is hidden once the sheet shuts. */
export function closeSheetOnGoto(sheet: HTMLDetailsElement | null, triggers: Iterable<HTMLElement>): () => void {
  const off: (() => void)[] = [];
  for (const t of triggers) {
    const fn = () => {
      if (!sheet?.open) return;
      if (sheet.contains(t)) sheet.querySelector<HTMLElement>('summary')?.focus();
      sheet.open = false;
    };
    t.addEventListener('click', fn);
    off.push(() => t.removeEventListener('click', fn));
  }
  return () => off.forEach((f) => f());
}
