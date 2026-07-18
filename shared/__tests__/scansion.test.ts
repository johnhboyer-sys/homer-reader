import { describe, expect, it } from 'vitest';
import {
  scansionTier,
  renderFeet,
  formatNotes,
  scansionDisplay,
  scansionKey,
} from '../lib/scansion';
import type { ScansionEntry } from '../lib/data';

describe('scansionTier', () => {
  it('a high-confidence entry is "normal"', () => {
    expect(scansionTier({ confidence: 'high', notes: [] })).toBe('normal');
  });

  it('an ambiguous entry WITHOUT an "unresolved" note is "ambiguous" (a real, disputed pattern)', () => {
    expect(scansionTier({ confidence: 'ambiguous', notes: ['synizesis'] })).toBe('ambiguous');
  });

  it('an ambiguous entry WITH an "unresolved" note is "unresolved" (no confident scan at all)', () => {
    expect(scansionTier({ confidence: 'ambiguous', notes: ['unresolved'] })).toBe('unresolved');
  });
});

describe('renderFeet — glyph mapping', () => {
  it('maps D/S/X to the traditional dactyl/spondee/anceps glyphs', () => {
    expect(renderFeet('DDSDDX')).toBe('—◡◡ —◡◡ —— —◡◡ —◡◡ —×');
  });

  it('renders Il. 1.1 exactly as the verified fixture line', () => {
    // build/dist/iliad/scansion-01.json: {"feet":"DDSDDX","confidence":"high",...}
    expect(renderFeet('DDSDDX')).toBe('—◡◡ —◡◡ —— —◡◡ —◡◡ —×');
  });

  it('an all-spondee line renders six long-long feet', () => {
    expect(renderFeet('SSSSSS')).toBe('—— —— —— —— —— ——');
  });
});

describe('formatNotes', () => {
  it('joins known flags with their display labels', () => {
    expect(formatNotes(['synizesis', 'hiatus'])).toBe('synizesis, hiatus');
    expect(formatNotes(['digamma-assumed'])).toBe('digamma assumed');
    expect(formatNotes(['brevis-in-longo'])).toBe('brevis in longo');
  });

  it('passes an unrecognized flag through unchanged', () => {
    expect(formatNotes(['some-future-flag'])).toBe('some-future-flag');
  });

  it('empty notes join to an empty string', () => {
    expect(formatNotes([])).toBe('');
  });
});

describe('scansionDisplay — the honesty contract', () => {
  it('a high-confidence line with notes renders plainly, notes as the tooltip', () => {
    const entry: ScansionEntry = {
      feet: 'DDSDDX',
      confidence: 'high',
      notes: ['brevis-in-longo', 'hiatus', 'synizesis'],
    };
    const d = scansionDisplay(entry);
    expect(d.tier).toBe('normal');
    expect(d.text).toBe('—◡◡ —◡◡ —— —◡◡ —◡◡ —×');
    expect(d.text.startsWith('≈')).toBe(false);
    expect(d.title).toBe('brevis in longo, hiatus, synizesis');
  });

  it('a high-confidence line with no notes has no tooltip', () => {
    const d = scansionDisplay({ feet: 'DDDDDS', confidence: 'high', notes: [] });
    expect(d.title).toBeUndefined();
  });

  it('an ambiguous (but real) line is visibly qualified with a ≈ prefix and an explanatory title', () => {
    const d = scansionDisplay({ feet: 'SSSSDS', confidence: 'ambiguous', notes: ['correption'] });
    expect(d.tier).toBe('ambiguous');
    expect(d.text).toBe('≈ —— —— —— —— —◡◡ ——');
    expect(d.title).toContain('ambiguous scan');
    expect(d.title).toContain('correption');
  });

  it('an ambiguous line with no other notes still gets an explanatory title', () => {
    const d = scansionDisplay({ feet: 'SSSSDS', confidence: 'ambiguous', notes: [] });
    expect(d.title).toBe('ambiguous scan (more than one reading fits)');
  });

  it('NEVER renders a fake pattern for an unresolved line — honest placeholder only', () => {
    // Il. 1.15 in the real corpus: confidence "ambiguous", notes ["unresolved"].
    const entry: ScansionEntry = { feet: 'DDDDSS', confidence: 'ambiguous', notes: ['unresolved'] };
    const d = scansionDisplay(entry);
    expect(d.tier).toBe('unresolved');
    expect(d.text).toBe('—');
    expect(d.text).not.toContain('D');
    expect(d.text).not.toContain('S');
    expect(d.title).toBe('no confident scan');
  });
});

describe('scansionKey', () => {
  it('builds the "<book>.<line>" key with no zero-padding', () => {
    expect(scansionKey(1, 1)).toBe('1.1');
    expect(scansionKey(9, 45)).toBe('9.45');
  });
});
