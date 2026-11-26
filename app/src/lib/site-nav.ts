// The site's map, in one place: the header bar and phone sheet
// (SiteHeader.astro) and the "you are here" line on reference pages
// (Crumbs.astro) both read it, so a page cannot be in one and not the other.
// Paths are under the site base and written the way the header links them.

export interface NavItem { label: string; path: string; /** Path prefix that marks this item current. */ prefix: string; }
export interface NavGroup { label: string; items: NavItem[]; }

const item = (label: string, path: string, prefix = path.replace(/\/$/, '')): NavItem => ({ label, path, prefix });

export const POEMS: NavItem[] = [item('Iliad', '/iliad'), item('Odyssey', '/odyssey')];
export const GROUPS: NavGroup[] = [
  { label: 'Atlas', items: [item('Maps', '/maps/'), item('Places', '/places/'), item('Timeline', '/timeline/')] },
  { label: 'People', items: [item('Characters', '/characters/'), item('Genealogies', '/genealogies/')] },
  {
    label: 'Language',
    items: [
      item('Vocabulary', '/vocabulary/'),
      item('Formulas', '/formulas/'),
      item('Repetitions', '/repetitions/'),
      item('Phrases', '/phrases/'),
      item('Lexicon', '/lemma/'),
      item('Advanced search', '/advanced'),
    ],
  },
];
export const ABOUT = item('About', '/about');
export const SEARCH = item('Search', '/search');

/** Whether `pathname` (site base already stripped) is this item or under it. */
export const isCurrent = (pathname: string, i: NavItem): boolean =>
  pathname === i.prefix || pathname.startsWith(`${i.prefix}/`);

/** The group a page belongs to, and its item there; null for a page outside the groups. */
export function locate(pathname: string): { group: NavGroup; item: NavItem } | null {
  for (const group of GROUPS) {
    const found = group.items.find((i) => isCurrent(pathname, i));
    if (found) return { group, item: found };
  }
  return null;
}

/** Every page the header links, for the checks that keep the palette's list honest. */
export const ALL_NAV_PATHS: string[] = [...POEMS, ...GROUPS.flatMap((g) => g.items), ABOUT, SEARCH].map((i) => i.path);
