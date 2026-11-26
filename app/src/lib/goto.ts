// The site-wide Go-to: one palette on every page, loaded on first use.
//
// Every page has it through its header: the site header's Go-to control (or
// the reader bar's Go to button) and Cmd/Ctrl+K open it; the reader passes its
// book and scenes as well. The palette is the reader's own component
// (shared/components/CommandPalette.svelte), so there is one citation parser
// and one set of results. It is not in the page's first load: this module
// fetches it when the reader reaches for the control (pointer over it, focus
// on it) or presses the shortcut, so a reference page still ships no script
// to speak of, and the reader's first load leaves it out too.
//
// Without script the control is a plain link to /search, which is where the
// palette's own last row leads.

export interface GotoHandle {
  open: () => void;
}

import type { Scene } from '@shared/lib/data';

/** What the reader adds to the palette: its book, and the scenes it finds. */
export interface GotoBook {
  bookNum: number;
  scenes: Scene[];
}

export interface GotoOptions {
  /** The controls that open the palette. */
  triggers: Iterable<HTMLElement>;
  /** The poem a bare citation ("6.237") reads in first: set on a poem's index. */
  work?: string | null;
  /** The book open in the reader, if any. */
  book?: GotoBook | null;
  /** Mounts the palette. Injected so the wiring is testable without Svelte. */
  load?: (work: string | null) => Promise<GotoHandle>;
}

const defaultLoad = async (work: string | null, book: GotoBook | null = null): Promise<GotoHandle> => {
  const [{ mount }, { default: CommandPalette }] = await Promise.all([
    import('svelte'),
    import('@shared/components/CommandPalette.svelte'),
  ]);
  const palette = mount(CommandPalette, { target: document.body, props: { work, ...book } }) as unknown as {
    openPalette: () => void;
  };
  return { open: () => palette.openPalette() };
};

const isShortcut = (e: KeyboardEvent) => (e.metaKey || e.ctrlKey) && !e.altKey && e.key.toLowerCase() === 'k';

export function initGoto({ triggers, work = null, book = null, load = (w) => defaultLoad(w, book) }: GotoOptions): () => void {
  let handle: Promise<GotoHandle> | null = null;
  let mounted = false;
  const off: (() => void)[] = [];
  const on = (el: EventTarget, type: string, fn: (e: Event) => void, opts?: AddEventListenerOptions) => {
    el.addEventListener(type, fn, opts);
    off.push(() => el.removeEventListener(type, fn, opts));
  };

  // One load, however many times it is asked for. A failed load is forgotten
  // so the next press tries again.
  const ensure = () => {
    if (!handle) {
      handle = load(work).then((h) => { mounted = true; return h; });
      handle.catch(() => { handle = null; });
    }
    return handle;
  };
  const open = () => ensure().then((h) => h.open());

  for (const el of triggers) {
    on(el, 'click', (e) => {
      const m = e as MouseEvent;
      // A modified click on the link keeps its meaning (open /search in a tab).
      if (m.metaKey || m.ctrlKey || m.shiftKey || m.button > 0) return;
      e.preventDefault();
      // Not caught: the trigger is still a link to /search if the load fails.
      open().catch(() => { window.location.href = (el as HTMLAnchorElement).href || '/search'; });
    });
    // Warm the module while the pointer or focus is on its way.
    on(el, 'pointerenter', () => { ensure().catch(() => {}); }, { passive: true });
    on(el, 'focus', () => { ensure().catch(() => {}); });
  }

  // Until the palette is mounted the shortcut is ours; once it is, the
  // palette's own window listener toggles it and this one stands down, so one
  // press never opens and closes in the same breath.
  on(window, 'keydown', (e) => {
    const k = e as KeyboardEvent;
    if (mounted || !isShortcut(k)) return;
    k.preventDefault();
    open().catch(() => {});
  });

  return () => off.forEach((fn) => fn());
}
