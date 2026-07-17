// Genealogy-tree builder for the four Landmark-style family trees (House of
// Atreus, House of Aeacus, House of Troy, the Olympians) drawn from
// apparatus/characters.json's `genealogy: {tree, father, mother, nonHomeric?}`
// field. Pure data transform — flat character list -> nested parent/child
// forest — so it's independently testable and reused by the build-time
// /genealogies/ page (never fetched at runtime; the page reads the JSON once
// at build time and calls this).
//
// Apparatus honesty (CLAUDE.md): a parent id that isn't itself a character in
// the file is an "external" reference (rendered as a muted terminal node by
// the page, never invented data). `nonHomeric` on a parent key flags that
// specific link as later tradition, not Homer — carried through per-parent so
// the page can render it dashed with an accessible annotation.

export interface CharacterRecord {
  id: string;
  name: string;
  greek: string;
  role?: string;
  genealogy?: {
    tree: string;
    father?: string;
    mother?: string;
    nonHomeric?: ('father' | 'mother')[];
  };
}

export interface ParentRef {
  key: 'father' | 'mother';
  id: string;
  name: string;
  greek?: string;
  known: boolean; // true iff `id` is a character in the file (any tree)
  nonHomeric: boolean;
}

export interface GenealogyNode {
  id: string;
  name: string;
  greek: string;
  role?: string;
  parents: ParentRef[];
  children: GenealogyNode[];
}

function humanize(id: string): string {
  return id.length === 0 ? id : id.charAt(0).toUpperCase() + id.slice(1);
}

/**
 * Build the forest of GenealogyNode roots for one tree id ("atreus" |
 * "aeacus" | "troy" | "olympians"), from the flat characters array.
 *
 * A member is any character whose `genealogy.tree` equals `tree`. A member is
 * a ROOT of the forest unless its father is ITSELF a member of the same tree
 * (in which case it nests under that father — every tree in the current data
 * is patrilineal: mother links never drive nesting, only father does).
 * `olympians` has four roots (zeus/hera/poseidon/hades, siblings with no
 * in-tree father); every other tree has exactly one.
 */
export function buildGenealogyTree(characters: CharacterRecord[], tree: string): GenealogyNode[] {
  const byId = new Map(characters.map((c) => [c.id, c]));
  const members = characters.filter((c) => c.genealogy?.tree === tree);
  const memberIds = new Set(members.map((m) => m.id));

  function resolveParent(
    key: 'father' | 'mother',
    id: string,
    nonHomericFlags: ('father' | 'mother')[] | undefined,
  ): ParentRef {
    const known = byId.get(id);
    return {
      key,
      id,
      name: known ? known.name : humanize(id),
      greek: known?.greek,
      known: Boolean(known),
      nonHomeric: Boolean(nonHomericFlags?.includes(key)),
    };
  }

  function buildNode(c: CharacterRecord, seen: Set<string>): GenealogyNode {
    const g = c.genealogy!;
    const parents: ParentRef[] = [];
    if (g.father) parents.push(resolveParent('father', g.father, g.nonHomeric));
    if (g.mother) parents.push(resolveParent('mother', g.mother, g.nonHomeric));
    // Guard against a malformed cycle in future data (father chain looping
    // back on itself) rather than recursing forever.
    const nextSeen = new Set(seen).add(c.id);
    const children = members
      .filter((m) => m.genealogy!.father === c.id && !seen.has(m.id))
      .map((m) => buildNode(m, nextSeen));
    return { id: c.id, name: c.name, greek: c.greek, role: c.role, parents, children };
  }

  const roots = members.filter((m) => {
    const fatherId = m.genealogy!.father;
    return !fatherId || !memberIds.has(fatherId);
  });

  return roots.map((r) => buildNode(r, new Set()));
}

/** Flatten a forest back to a flat node list (depth-first), for counting/testing. */
export function flattenGenealogy(roots: GenealogyNode[]): GenealogyNode[] {
  const out: GenealogyNode[] = [];
  const visit = (n: GenealogyNode) => {
    out.push(n);
    n.children.forEach(visit);
  };
  roots.forEach(visit);
  return out;
}
