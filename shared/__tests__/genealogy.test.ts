import { describe, expect, it } from 'vitest';
import { buildGenealogyTree, flattenGenealogy, type CharacterRecord } from '../lib/genealogy';

// A small fixture mirroring the shapes actually found in
// apparatus/characters.json: a single-root patrilineal chain (atreus-like), a
// multi-root sibling tree with shared external parents (olympians-like), a
// nonHomeric-flagged link, an external-string parent (not a character id in
// the file), and a cross-tree known parent (an id that exists but belongs to
// a different tree / has no genealogy of its own).
const fixture: CharacterRecord[] = [
  // --- single-root chain, tree "house" ---
  { id: 'root1', name: 'Root One', greek: 'Ῥίζα', role: 'founder', genealogy: { tree: 'house' } },
  { id: 'mid1', name: 'Mid One', greek: 'Μέσος', role: 'heir', genealogy: { tree: 'house', father: 'root1', nonHomeric: ['father'] } },
  { id: 'leaf1', name: 'Leaf One', greek: 'Φύλλον', role: 'child', genealogy: { tree: 'house', father: 'mid1', mother: 'outsider' } },
  // known-but-different-tree spouse, no genealogy of her own
  { id: 'spouse1', name: 'Spouse One', greek: 'Σύζυγος', role: 'consort' },

  // --- multi-root sibling tree, tree "pantheon", shared external parents ---
  { id: 'sib1', name: 'Sib One', greek: 'Α', role: 'god', genealogy: { tree: 'pantheon', father: 'elder', mother: 'elderess' } },
  { id: 'sib2', name: 'Sib Two', greek: 'Β', role: 'god', genealogy: { tree: 'pantheon', father: 'elder', mother: 'elderess' } },
  { id: 'child-of-sib1', name: 'Child Of Sib1', greek: 'Γ', role: 'demigod', genealogy: { tree: 'pantheon', father: 'sib1' } },
];

describe('buildGenealogyTree', () => {
  it('builds a single-root patrilineal chain and nests every member exactly once', () => {
    const roots = buildGenealogyTree(fixture, 'house');
    expect(roots).toHaveLength(1);
    expect(roots[0].id).toBe('root1');
    expect(roots[0].children).toHaveLength(1);
    expect(roots[0].children[0].id).toBe('mid1');
    expect(roots[0].children[0].children[0].id).toBe('leaf1');

    const flat = flattenGenealogy(roots);
    expect(flat.map((n) => n.id).sort()).toEqual(['leaf1', 'mid1', 'root1']);
  });

  it('flags a nonHomeric parent link and leaves unflagged links alone', () => {
    const roots = buildGenealogyTree(fixture, 'house');
    const mid = roots[0].children[0];
    expect(mid.parents).toEqual([
      { key: 'father', id: 'root1', name: 'Root One', greek: 'Ῥίζα', known: true, nonHomeric: true },
    ]);
  });

  it('resolves a known cross-tree parent by its real name/greek without inventing data', () => {
    const roots = buildGenealogyTree(fixture, 'house');
    const leaf = roots[0].children[0].children[0];
    const father = leaf.parents.find((p) => p.key === 'father')!;
    const mother = leaf.parents.find((p) => p.key === 'mother')!;
    expect(father).toEqual({ key: 'father', id: 'mid1', name: 'Mid One', greek: 'Μέσος', known: true, nonHomeric: false });
    // "outsider" is not a character id in the file at all -> external, humanized, not marked known.
    expect(mother).toEqual({ key: 'mother', id: 'outsider', name: 'Outsider', greek: undefined, known: false, nonHomeric: false });
  });

  it('produces multiple roots for a sibling tree with no in-tree father', () => {
    const roots = buildGenealogyTree(fixture, 'pantheon');
    expect(roots.map((r) => r.id).sort()).toEqual(['sib1', 'sib2']);
    const sib1 = roots.find((r) => r.id === 'sib1')!;
    expect(sib1.children.map((c) => c.id)).toEqual(['child-of-sib1']);
    // Each root still carries its own (external, shared) parentage.
    expect(sib1.parents).toEqual([
      { key: 'father', id: 'elder', name: 'Elder', greek: undefined, known: false, nonHomeric: false },
      { key: 'mother', id: 'elderess', name: 'Elderess', greek: undefined, known: false, nonHomeric: false },
    ]);
    expect(flattenGenealogy(roots)).toHaveLength(3);
  });

  it('returns an empty forest for a tree id with no members', () => {
    expect(buildGenealogyTree(fixture, 'nonexistent-tree')).toEqual([]);
  });
});
