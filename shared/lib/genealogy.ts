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

/** A person placed in 2-D for the chart (center-x, top-y of the node card). */
export interface PlacedPerson {
  id: string;
  name: string;
  greek: string;
  role?: string;
  parents: ParentRef[];
  /** Horizontal center of the node card, in layout pixels. */
  x: number;
  /** Top edge of the node card, in layout pixels. */
  y: number;
  depth: number;
}

/**
 * Orthogonal parent→child connector. Style mirrors the father-link honesty
 * flags: solid = attested in Homer, dashed = later tradition (`nonHomeric`).
 * External (named-but-not-in-edition) parents are not tree edges — they only
 * appear on node cards / the accessible list.
 */
export interface TreeConnector {
  fromId: string;
  toId: string;
  /** Parent bottom-center. */
  x1: number;
  y1: number;
  /** Child top-center. */
  x2: number;
  y2: number;
  /** Y of the horizontal sibling bar between parent and children. */
  barY: number;
  style: 'solid' | 'dashed';
}

export interface GenealogyLayout {
  nodes: PlacedPerson[];
  connectors: TreeConnector[];
  width: number;
  height: number;
  /** Card box used for placement (page uses the same for CSS). */
  nodeWidth: number;
  nodeHeight: number;
}

export interface LayoutOptions {
  nodeWidth?: number;
  nodeHeight?: number;
  /** Horizontal gap between sibling subtrees. */
  hGap?: number;
  /** Vertical gap between generations (edge clearance between cards). */
  vGap?: number;
  padX?: number;
  padY?: number;
}

const DEFAULT_LAYOUT: Required<LayoutOptions> = {
  nodeWidth: 132,
  nodeHeight: 52,
  hGap: 18,
  vGap: 40,
  padX: 16,
  padY: 12,
};

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

/**
 * Tidy-tree layout: leaves pack left-to-right, parents center over their
 * children, multi-root forests sit side-by-side. Pure geometry — no DOM.
 * Connectors use classic family-tree orthogonal routing (stem + sibling bar
 * + drop).
 */
export function layoutGenealogyTree(
  roots: GenealogyNode[],
  opts: LayoutOptions = {},
): GenealogyLayout {
  const cfg = { ...DEFAULT_LAYOUT, ...opts };
  const { nodeWidth, nodeHeight, hGap, vGap, padX, padY } = cfg;

  if (roots.length === 0) {
    return {
      nodes: [],
      connectors: [],
      width: padX * 2,
      height: padY * 2,
      nodeWidth,
      nodeHeight,
    };
  }

  const subtreeW = new Map<string, number>();

  function measure(node: GenealogyNode): number {
    if (subtreeW.has(node.id)) return subtreeW.get(node.id)!;
    let w: number;
    if (node.children.length === 0) {
      w = nodeWidth;
    } else {
      const kids =
        node.children.reduce((sum, c) => sum + measure(c), 0) +
        hGap * (node.children.length - 1);
      w = Math.max(nodeWidth, kids);
    }
    subtreeW.set(node.id, w);
    return w;
  }

  roots.forEach(measure);

  const placed = new Map<string, PlacedPerson>();
  let maxDepth = 0;

  function place(node: GenealogyNode, left: number, depth: number): void {
    maxDepth = Math.max(maxDepth, depth);
    const w = measure(node);
    const y = padY + depth * (nodeHeight + vGap);
    let x: number;

    if (node.children.length === 0) {
      x = left + w / 2;
    } else {
      let cursor = left + (w - measureChildrenSpan(node)) / 2;
      for (const child of node.children) {
        const cw = measure(child);
        place(child, cursor, depth + 1);
        cursor += cw + hGap;
      }
      const first = placed.get(node.children[0].id)!;
      const last = placed.get(node.children[node.children.length - 1].id)!;
      x = (first.x + last.x) / 2;
    }

    placed.set(node.id, {
      id: node.id,
      name: node.name,
      greek: node.greek,
      role: node.role,
      parents: node.parents,
      x,
      y,
      depth,
    });
  }

  function measureChildrenSpan(node: GenealogyNode): number {
    if (node.children.length === 0) return 0;
    return (
      node.children.reduce((sum, c) => sum + measure(c), 0) +
      hGap * (node.children.length - 1)
    );
  }

  // Multi-root forest: pack roots left-to-right with an extra root gap.
  const rootGap = hGap * 2;
  let forestLeft = padX;
  for (const root of roots) {
    const w = measure(root);
    place(root, forestLeft, 0);
    forestLeft += w + rootGap;
  }

  // Re-center each root over its children after place() (already done inside
  // place for non-leaves). Leaves and multi-root roots are correct as packed.

  const nodes = Array.from(placed.values());
  const connectors: TreeConnector[] = [];

  function walkEdges(node: GenealogyNode): void {
    const parent = placed.get(node.id)!;
    if (node.children.length > 0) {
      const parentBottomY = parent.y + nodeHeight;
      const barY = parentBottomY + vGap / 2;
      for (const child of node.children) {
        const c = placed.get(child.id)!;
        const father = child.parents.find((p) => p.key === 'father');
        const style: 'solid' | 'dashed' =
          father?.nonHomeric === true ? 'dashed' : 'solid';
        connectors.push({
          fromId: node.id,
          toId: child.id,
          x1: parent.x,
          y1: parentBottomY,
          x2: c.x,
          y2: c.y,
          barY,
          style,
        });
        walkEdges(child);
      }
    }
  }
  roots.forEach(walkEdges);

  // Width: rightmost card right-edge + pad. Height: deepest card bottom + pad.
  let maxRight = padX;
  for (const n of nodes) {
    maxRight = Math.max(maxRight, n.x + nodeWidth / 2);
  }
  const width = Math.ceil(maxRight + padX);
  const height = Math.ceil(padY + (maxDepth + 1) * nodeHeight + maxDepth * vGap + padY);

  return { nodes, connectors, width, height, nodeWidth, nodeHeight };
}
