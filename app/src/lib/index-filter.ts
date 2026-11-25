// Client-side filter for the alphabetical reference lists (/places/,
// /characters/): a name field plus one group of toggle chips. Progressive
// enhancement only — the server renders every row and the field is hidden by a
// <noscript> rule on the page, so with no script the page is the full list.
//
// Rows carry data-name, data-letter and data-<chipKey>; letter headings carry
// data-letter and hide when none of their rows is showing.

interface Options {
  /** id of the list element holding .pg-entry rows and .pg-letter headings. */
  list: string;
  /** id of the <input type="search">. */
  input: string;
  /** id of the live "N of M" counter. */
  count?: string;
  /** id of the "nothing matches" line. */
  empty?: string;
  /** Selector for the toggle chips (buttons with aria-pressed). */
  chips?: string;
  /** dataset key shared by a chip and the rows it selects (e.g. "tier"). */
  chipKey?: string;
  /** Called with the ids of the rows showing, or null when nothing is filtered. */
  onChange?: (visible: Set<string> | null) => void;
}

/** Lower-case, strip accents and punctuation: "Üvecik Tepe" matches "uvecik". */
export const foldName = (s: string): string =>
  s.normalize('NFD').replace(/\p{Mn}/gu, '').toLowerCase().replace(/[^a-z0-9 ]/g, '');

export function wireIndexFilter(opts: Options): void {
  const list = document.getElementById(opts.list);
  const input = document.getElementById(opts.input) as HTMLInputElement | null;
  if (!list || !input) return;
  const rows = Array.from(list.querySelectorAll<HTMLElement>('.pg-entry'));
  const letters = Array.from(list.querySelectorAll<HTMLElement>('.pg-letter'));
  const jumps = Array.from(document.querySelectorAll<HTMLAnchorElement>('.pg-jump a[data-letter]'));
  const countEl = opts.count ? document.getElementById(opts.count) : null;
  const emptyEl = opts.empty ? document.getElementById(opts.empty) : null;
  const chips = opts.chips ? Array.from(document.querySelectorAll<HTMLButtonElement>(opts.chips)) : [];
  const key = opts.chipKey ?? '';
  const folded = rows.map((r) => foldName(r.dataset.name ?? ''));

  const apply = () => {
    const q = foldName(input.value.trim());
    const on = new Set(chips.filter((c) => c.getAttribute('aria-pressed') === 'true').map((c) => c.dataset[key] ?? ''));
    const live = new Set<string>();
    const ids = new Set<string>();
    let shown = 0;
    rows.forEach((row, i) => {
      const hit = (!q || folded[i].includes(q)) && (on.size === 0 || on.has(row.dataset[key] ?? ''));
      row.hidden = !hit;
      if (hit) {
        shown++;
        live.add(row.dataset.letter ?? '');
        if (row.dataset.id) ids.add(row.dataset.id);
      }
    });
    for (const l of letters) l.hidden = !live.has(l.dataset.letter ?? '');
    for (const j of jumps) j.classList.toggle('is-empty', !live.has(j.dataset.letter ?? ''));
    const filtering = Boolean(q) || on.size > 0;
    if (countEl) countEl.textContent = filtering ? `${shown} of ${rows.length}` : '';
    if (emptyEl) emptyEl.hidden = shown !== 0;
    opts.onChange?.(filtering ? ids : null);
  };

  input.addEventListener('input', apply);
  for (const chip of chips) {
    chip.addEventListener('click', () => {
      chip.setAttribute('aria-pressed', String(chip.getAttribute('aria-pressed') !== 'true'));
      apply();
    });
  }
}
