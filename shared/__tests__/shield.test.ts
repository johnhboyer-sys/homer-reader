import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  renderShield,
  type ShieldBand,
  type ShieldPlate,
} from '../lib/shield';

const PLATE_PATH = '../apparatus/plates/shield-of-achilles.json';
const plate = JSON.parse(readFileSync(PLATE_PATH, 'utf-8')) as ShieldPlate;

describe('Shield of Achilles plate data', () => {
  it('keeps every band line range inside Iliad 18.478–608', () => {
    for (const band of plate.bands) {
      const [from, to] = band.lines;
      expect(from).toBeGreaterThanOrEqual(478);
      expect(to).toBeLessThanOrEqual(608);
      expect(from).toBeLessThanOrEqual(to);
    }
  });

  it('has strictly ascending rings and non-overlapping ascending line ranges', () => {
    const ordered = [...plate.bands].sort((a, b) => a.ring - b.ring);
    const rendered = renderShield(plate).bands;
    for (let index = 1; index < ordered.length; index++) {
      expect(ordered[index].ring).toBeGreaterThan(ordered[index - 1].ring);
      expect(ordered[index].lines[0]).toBeGreaterThan(ordered[index - 1].lines[1]);
      expect(rendered[index].innerRadius).toBe(rendered[index - 1].outerRadius);
    }
  });
});

describe('renderShield', () => {
  it('is byte-identical for identical input', () => {
    expect(renderShield(plate).svg).toBe(renderShield(plate).svg);
  });

  it('emits only CSS custom-property references for fills and strokes', () => {
    const { svg } = renderShield(plate);
    expect(svg).not.toMatch(/#[0-9a-fA-F]{3,8}/);
    expect(svg).not.toMatch(/\brgb\(/i);
    expect(svg).not.toMatch(/\bhsl\(/i);
    expect(svg).not.toMatch(/\b(?:black|white|red|green|blue|gray|grey|yellow|orange|purple|pink|brown|cyan|magenta|aqua|maroon|navy|lime|olive|silver|gold|teal|transparent)\b/i);

    const paintValues = [...svg.matchAll(/\b(?:fill|stroke)="([^"]+)"/g)].map(
      (match) => match[1],
    );
    expect(paintValues.length).toBeGreaterThan(0);
    for (const value of paintValues) {
      expect(value).toMatch(/^var\(--[a-z0-9-]+\)$/);
    }
  });

  it('escapes hostile band titles instead of emitting executable markup', () => {
    const hostileTitle = '<script>alert(1)</script> "quoted"';
    const hostileBand: ShieldBand = { ...plate.bands[0], title: hostileTitle };
    const hostilePlate: ShieldPlate = {
      ...plate,
      bands: [hostileBand, ...plate.bands.slice(1)],
    };
    const { svg } = renderShield(hostilePlate);

    expect(svg).not.toContain(hostileTitle);
    expect(svg).not.toContain('<script>');
    expect(svg).toContain('&lt;script&gt;alert(1)&lt;/script&gt;');
    expect(svg).toContain('&quot;quoted&quot;');
  });

  it('emits one matching data-band-id for every band', () => {
    const { svg } = renderShield(plate);
    for (const band of plate.bands) {
      expect(svg.match(new RegExp(`data-band-id="${band.id}"`, 'g'))).toHaveLength(1);
    }
  });
});
