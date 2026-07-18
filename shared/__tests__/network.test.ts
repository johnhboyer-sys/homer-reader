import { describe, expect, it } from 'vitest';
import {
  aggregateSpeechEdges,
  buildKinshipEdges,
  computeKinshipDegree,
  computeSpeechParticipation,
  layoutNetwork,
  type NetworkCharacter,
  type SpeechJoin,
} from '../lib/network';

// Fixture mirroring the shapes actually found in apparatus/characters.json:
// a joined father link, a joined nonHomeric-flagged father link, and a
// mother pointing at a name that is NOT itself a character id (external,
// like Dardanus's mother "electra" in the real corpus).
const characters: NetworkCharacter[] = [
  { id: 'peleus' },
  { id: 'thetis' },
  { id: 'achilles', genealogy: { father: 'peleus', mother: 'thetis' } },
  { id: 'tantalus' },
  { id: 'pelops', genealogy: { father: 'tantalus', nonHomeric: ['father'] } },
  { id: 'dardanus', genealogy: { father: 'zeus', mother: 'electra', nonHomeric: ['mother'] } },
  { id: 'zeus' },
  { id: 'isolate' },
];

describe('buildKinshipEdges', () => {
  it('builds an edge for each parent link where both ends are known character ids', () => {
    const edges = buildKinshipEdges(characters);
    const achillesEdges = edges.filter((e) => e.target === 'achilles');
    expect(achillesEdges).toHaveLength(2);
    expect(achillesEdges).toEqual(
      expect.arrayContaining([
        { type: 'kinship', source: 'peleus', target: 'achilles', relation: 'father', nonHomeric: false },
        { type: 'kinship', source: 'thetis', target: 'achilles', relation: 'mother', nonHomeric: false },
      ]),
    );
  });

  it('never invents an edge to a parent id that is not itself a character (external reference)', () => {
    const edges = buildKinshipEdges(characters);
    // dardanus's mother "electra" is not in the fixture's character list.
    const dardanusEdges = edges.filter((e) => e.target === 'dardanus');
    expect(dardanusEdges).toHaveLength(1);
    expect(dardanusEdges[0]).toEqual({
      type: 'kinship',
      source: 'zeus',
      target: 'dardanus',
      relation: 'father',
      nonHomeric: false,
    });
  });

  it('preserves nonHomeric per edge and never conflates it with an attested link', () => {
    const edges = buildKinshipEdges(characters);
    const pelopsEdge = edges.find((e) => e.target === 'pelops')!;
    expect(pelopsEdge.nonHomeric).toBe(true);
    const achillesFatherEdge = edges.find((e) => e.target === 'achilles' && e.relation === 'father')!;
    expect(achillesFatherEdge.nonHomeric).toBe(false);
  });

  it('produces no edges for a character with no genealogy', () => {
    const edges = buildKinshipEdges(characters);
    expect(edges.some((e) => e.source === 'isolate' || e.target === 'isolate')).toBe(false);
  });
});

describe('aggregateSpeechEdges', () => {
  const ids = new Set(['achilles', 'agamemnon', 'thetis', 'greeks']);

  it('aggregates repeated speeches between the same pair into one weighted edge, order-independent', () => {
    const speeches: SpeechJoin[] = [
      { speaker: ['achilles'], addressee: ['agamemnon'] },
      { speaker: ['agamemnon'], addressee: ['achilles'] },
      { speaker: ['achilles'], addressee: ['agamemnon'] },
    ];
    const { edges, excludedUnjoined, excludedSelf } = aggregateSpeechEdges(speeches, ids);
    expect(edges).toHaveLength(1);
    expect(edges[0].count).toBe(3);
    expect([edges[0].a, edges[0].b].sort()).toEqual(['achilles', 'agamemnon']);
    expect(excludedUnjoined).toBe(0);
    expect(excludedSelf).toBe(0);
  });

  it('excludes and counts speeches with multiple speakers/addressees or an unjoined party, without dropping silently', () => {
    const speeches: SpeechJoin[] = [
      { speaker: ['achilles', 'agamemnon'], addressee: ['thetis'] }, // multi-speaker: excluded
      { speaker: ['achilles'], addressee: ['greeks'] }, // "greeks" IS a joined id here: valid single-single edge
      { speaker: ['achilles'], addressee: ['chryses'] }, // chryses not joined: excluded
      { speaker: ['achilles'], addressee: ['thetis'] }, // valid
    ];
    const { edges, excludedUnjoined, excludedSelf } = aggregateSpeechEdges(speeches, ids);
    expect(edges).toHaveLength(2); // achilles-greeks, achilles-thetis
    expect(edges.reduce((sum, e) => sum + e.count, 0)).toBe(2);
    expect(excludedUnjoined).toBe(2); // multi-speaker + unjoined chryses
    expect(excludedSelf).toBe(0);
  });

  it('excludes self-addressed speech separately from unjoined exclusions', () => {
    const speeches: SpeechJoin[] = [
      { speaker: ['achilles'], addressee: ['achilles'] },
      { speaker: ['achilles'], addressee: ['agamemnon'] },
    ];
    const { edges, excludedUnjoined, excludedSelf } = aggregateSpeechEdges(speeches, ids);
    expect(edges).toHaveLength(1);
    expect(excludedSelf).toBe(1);
    expect(excludedUnjoined).toBe(0);
  });

  it('accounts for every input speech across edges + both exclusion buckets', () => {
    const speeches: SpeechJoin[] = [
      { speaker: ['achilles'], addressee: ['agamemnon'] },
      { speaker: ['achilles'], addressee: ['achilles'] },
      { speaker: ['achilles'], addressee: ['unknown-person'] },
      { speaker: ['achilles', 'agamemnon'], addressee: ['thetis'] },
    ];
    const { edges, excludedUnjoined, excludedSelf } = aggregateSpeechEdges(speeches, ids);
    const totalEdgeCount = edges.reduce((sum, e) => sum + e.count, 0);
    expect(totalEdgeCount + excludedUnjoined + excludedSelf).toBe(speeches.length);
  });
});

describe('computeSpeechParticipation / computeKinshipDegree', () => {
  it('sums incident speech-edge counts per node', () => {
    const participation = computeSpeechParticipation([
      { type: 'speech', a: 'achilles', b: 'agamemnon', count: 5 },
      { type: 'speech', a: 'achilles', b: 'thetis', count: 2 },
    ]);
    expect(participation.get('achilles')).toBe(7);
    expect(participation.get('agamemnon')).toBe(5);
    expect(participation.get('thetis')).toBe(2);
  });

  it('counts kinship degree per node across father/mother edges', () => {
    const degree = computeKinshipDegree(buildKinshipEdges(characters));
    expect(degree.get('achilles')).toBe(2); // father + mother
    expect(degree.get('peleus')).toBe(1);
    expect(degree.get('isolate')).toBeUndefined();
  });
});

describe('layoutNetwork', () => {
  const nodeIds = ['a', 'b', 'c', 'd', 'e'];
  const edges = [
    { source: 'a', target: 'b', weight: 1 },
    { source: 'b', target: 'c', weight: 3 },
    { source: 'c', target: 'd', weight: 1 },
  ];

  it('is deterministic: identical input produces byte-identical output', () => {
    const first = layoutNetwork(nodeIds, edges, { iterations: 60 });
    const second = layoutNetwork(nodeIds, edges, { iterations: 60 });
    expect(second).toEqual(first);
  });

  it('produces one finite, in-bounds position per node id, in input order', () => {
    const width = 400;
    const height = 300;
    const positions = layoutNetwork(nodeIds, edges, { width, height, iterations: 60 });
    expect(positions.map((p) => p.id)).toEqual(nodeIds);
    for (const p of positions) {
      expect(Number.isFinite(p.x)).toBe(true);
      expect(Number.isFinite(p.y)).toBe(true);
      expect(p.x).toBeGreaterThanOrEqual(0);
      expect(p.x).toBeLessThanOrEqual(width);
      expect(p.y).toBeGreaterThanOrEqual(0);
      expect(p.y).toBeLessThanOrEqual(height);
    }
  });

  it('handles zero and one node without crashing', () => {
    expect(layoutNetwork([], [])).toEqual([]);
    const single = layoutNetwork(['solo'], [], { width: 200, height: 200 });
    expect(single).toEqual([{ id: 'solo', x: 100, y: 100 }]);
  });

  it('ignores edges referencing unknown node ids rather than throwing', () => {
    expect(() => layoutNetwork(['a', 'b'], [{ source: 'a', target: 'ghost' }], { iterations: 20 })).not.toThrow();
  });

  it('pulls a strongly-connected pair closer together than two disconnected nodes, on average', () => {
    // A chain graph where b-c has the heaviest weight should end with b/c
    // measurably closer than the disconnected-ish endpoints a/e.
    const positions = layoutNetwork(nodeIds, edges, { iterations: 400, width: 900, height: 700 });
    const byId = new Map(positions.map((p) => [p.id, p]));
    const dist = (x: string, y: string) => {
      const p1 = byId.get(x)!;
      const p2 = byId.get(y)!;
      return Math.hypot(p1.x - p2.x, p1.y - p2.y);
    };
    expect(dist('b', 'c')).toBeLessThan(dist('a', 'e'));
  });
});
