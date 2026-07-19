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

  // --- spouse pairing, tree "dynasty": one father, two wives (one a known
  // character, one external/unknown, the second flagged nonHomeric) ---
  { id: 'patriarch', name: 'Patriarch', greek: 'Πα', role: 'king', genealogy: { tree: 'dynasty' } },
  { id: 'matriarch', name: 'Matriarch', greek: 'Μη', role: 'queen' }, // known character, no genealogy of her own
  { id: 'kid-a', name: 'Kid A', greek: 'Κ1', genealogy: { tree: 'dynasty', father: 'patriarch', mother: 'matriarch' } },
  { id: 'kid-b', name: 'Kid B', greek: 'Κ2', genealogy: { tree: 'dynasty', father: 'patriarch', mother: 'matriarch' } },
  { id: 'kid-c', name: 'Kid C', greek: 'Κ3', genealogy: { tree: 'dynasty', father: 'patriarch', mother: 'second-wife', nonHomeric: ['mother'] } },
  { id: 'kid-childless', name: 'Kid Childless', greek: 'Κ4', genealogy: { tree: 'dynasty', father: 'patriarch' } },
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

// Mobile "indented descent chart" (see /genealogies/) pairs a parent with a
// spouse card drawn from its children's mother links, instead of laying out
// pixel coordinates. These tests cover that pure-data transform: generation
// nesting is unaffected by the new field, spouses dedup rather than overlap
// (one card per distinct mother, not one per child), and multiple wives
// produce distinct, order-preserved "couples".
describe('buildGenealogyTree spouses', () => {
  it('dedupes a single shared mother across multiple children into one spouse, not a duplicate per child', () => {
    const roots = buildGenealogyTree(fixture, 'dynasty');
    const patriarch = roots[0];
    expect(patriarch.id).toBe('patriarch');
    // kid-a and kid-b share "matriarch" -- must appear exactly once.
    const matriarchEntries = patriarch.spouses.filter((s) => s.id === 'matriarch');
    expect(matriarchEntries).toHaveLength(1);
    expect(matriarchEntries[0]).toEqual({
      key: 'mother',
      id: 'matriarch',
      name: 'Matriarch',
      greek: 'Μη',
      known: true,
      nonHomeric: false,
    });
  });

  it('keeps multiple distinct wives as separate, order-preserved couples and flags the nonHomeric one', () => {
    const roots = buildGenealogyTree(fixture, 'dynasty');
    const patriarch = roots[0];
    // Discovery order follows children order: matriarch (kid-a) before the
    // external second-wife (kid-c); kid-childless contributes nothing.
    expect(patriarch.spouses.map((s) => s.id)).toEqual(['matriarch', 'second-wife']);
    const secondWife = patriarch.spouses.find((s) => s.id === 'second-wife')!;
    expect(secondWife).toEqual({
      key: 'mother',
      id: 'second-wife',
      name: 'Second-wife',
      greek: undefined,
      known: false,
      nonHomeric: true,
    });
  });

  it('leaves spouses empty for a leaf (no children) and for children with no recorded mother', () => {
    const roots = buildGenealogyTree(fixture, 'dynasty');
    const kidA = roots[0].children.find((c) => c.id === 'kid-a')!;
    const kidChildless = roots[0].children.find((c) => c.id === 'kid-childless')!;
    expect(kidA.spouses).toEqual([]);
    expect(kidChildless.spouses).toEqual([]);
  });

  it('does not regress the existing single-mother "house" chain (no couple to pair)', () => {
    const roots = buildGenealogyTree(fixture, 'house');
    // mid1's only child (leaf1) has mother "outsider" (external, unflagged).
    const mid1 = roots[0].children[0];
    expect(mid1.spouses).toEqual([
      { key: 'mother', id: 'outsider', name: 'Outsider', greek: undefined, known: false, nonHomeric: false },
    ]);
    // root1's only child (mid1) has no mother link at all -> no spouse.
    expect(roots[0].spouses).toEqual([]);
  });
});
