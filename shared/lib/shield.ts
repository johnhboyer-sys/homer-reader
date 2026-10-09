// Pure library for a build-time SVG rendering of Achilles' shield. The
// shield is a schematic plate, not a geographic map: each Homeric scene is
// an annular band in unit-like concentric order, from the cosmos at the
// centre to Ocean at the rim.
//
// No DOM, no file I/O, no randomness/clock reads — pure data-in, string-out
// transforms. Band labels follow their rings when they fit; longer labels
// move to a deterministic leader-line column outside the shield.
//
// Colors are ALWAYS emitted as `var(--...)` custom-property references,
// never literals, so a caller can define an accessible palette for every
// site theme. This module references --shield-ring-cosmos,
// --shield-ring-peace, --shield-ring-war, --shield-ring-field,
// --shield-ring-harvest, --shield-ring-vineyard, --shield-ring-cattle,
// --shield-ring-pasture, --shield-ring-dance, --shield-ring-ocean,
// --shield-outline, --shield-label, --shield-label-halo, and
// --shield-leader, plus the existing --font-ui typography token.

export interface ShieldBand {
  id: string;
  title: string;
  greek: string;
  lines: [number, number];
  summary: string;
  /** Concentric position: zero is the centre, increasing outward. */
  ring: number;
}

export interface ShieldPlate {
  id: string;
  title: string;
  kind: 'schematic';
  status: 'draft' | 'reviewed';
  seed: number;
  size: [number, number];
  bands: ShieldBand[];
}

export interface ShieldOptions {
  width?: number;
  height?: number;
  padding?: number;
  fontSizePx?: number;
  /** Prefix for internal text-path ids when more than one shield is inlined. */
  idPrefix?: string;
}

export interface RenderedBand {
  id: string;
  ring: number;
  innerRadius: number;
  outerRadius: number;
  labelPlacement: 'ring' | 'leader';
  labelX: number;
  labelY: number;
}

export interface ShieldResult {
  svg: string;
  bands: RenderedBand[];
}

interface BandLayout {
  band: ShieldBand;
  sourceIndex: number;
  innerRadius: number;
  outerRadius: number;
  middleRadius: number;
  labelPlacement: 'ring' | 'leader';
  labelX: number;
  labelY: number;
}

const RING_FILL_TOKENS = [
  'var(--shield-ring-cosmos)',
  'var(--shield-ring-peace)',
  'var(--shield-ring-war)',
  'var(--shield-ring-field)',
  'var(--shield-ring-harvest)',
  'var(--shield-ring-vineyard)',
  'var(--shield-ring-cattle)',
  'var(--shield-ring-pasture)',
  'var(--shield-ring-dance)',
  'var(--shield-ring-ocean)',
] as const;

function escapeXml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function round1(n: number): number {
  return Math.round(n * 10) / 10;
}

// Average glyph-width heuristic for the site's UI font stack. SVG text
// measurement would require the DOM, so this deliberately errs a little wide.
function estimateTextWidth(text: string, fontSizePx: number): number {
  return Array.from(text).length * fontSizePx * 0.58;
}

function safeIdFragment(s: string): string {
  const safe = s.replace(/[^a-zA-Z0-9_-]/g, '-');
  return safe || 'shield';
}

function annulusPath(cx: number, cy: number, innerRadius: number, outerRadius: number): string {
  const outerRight = round1(cx + outerRadius);
  const outerLeft = round1(cx - outerRadius);
  const innerRight = round1(cx + innerRadius);
  const innerLeft = round1(cx - innerRadius);
  const y = round1(cy);
  const outer = round1(outerRadius);
  const inner = round1(innerRadius);
  return (
    `M ${outerRight} ${y} A ${outer} ${outer} 0 1 0 ${outerLeft} ${y} ` +
    `A ${outer} ${outer} 0 1 0 ${outerRight} ${y} Z ` +
    `M ${innerRight} ${y} A ${inner} ${inner} 0 1 1 ${innerLeft} ${y} ` +
    `A ${inner} ${inner} 0 1 1 ${innerRight} ${y} Z`
  );
}

function upperArcPath(cx: number, cy: number, radius: number): string {
  const insetRadius = radius * 0.88;
  return (
    `M ${round1(cx - insetRadius)} ${round1(cy)} ` +
    `A ${round1(insetRadius)} ${round1(insetRadius)} 0 0 1 ${round1(cx + insetRadius)} ${round1(cy)}`
  );
}

function positiveFinite(value: number, name: string): number {
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(`shield: ${name} must be a positive finite number`);
  }
  return value;
}

// Assembles the plate's ordered bands into one self-contained SVG string.
// Pure and deterministic: identical inputs always produce byte-identical
// `svg` output and equivalent rendered-band geometry.
export function renderShield(
  plate: ShieldPlate,
  options: ShieldOptions = {},
): ShieldResult {
  if (plate.bands.length === 0) {
    throw new Error('shield: plate must contain at least one band');
  }

  const width = positiveFinite(options.width ?? plate.size[0], 'width');
  const height = positiveFinite(options.height ?? plate.size[1], 'height');
  const padding = positiveFinite(options.padding ?? 28, 'padding');
  const fontSizePx = positiveFinite(options.fontSizePx ?? 13, 'fontSizePx');
  const idPrefix = safeIdFragment(options.idPrefix ?? `shield-${plate.id}`);

  const ordered = plate.bands
    .map((band, sourceIndex) => ({ band, sourceIndex }))
    .sort((a, b) => a.band.ring - b.band.ring || a.sourceIndex - b.sourceIndex);

  const seenRings = new Set<number>();
  for (const { band } of ordered) {
    if (!Number.isInteger(band.ring) || band.ring < 0 || seenRings.has(band.ring)) {
      throw new Error('shield: band rings must be distinct non-negative integers');
    }
    seenRings.add(band.ring);
  }

  // Reserve the rightmost third for labels that cannot fit their ring.
  const diagramWidth = width * 0.68;
  const cx = diagramWidth / 2;
  const cy = height / 2;
  const outerRadius = positiveFinite(
    Math.min(diagramWidth / 2 - padding, height / 2 - padding),
    'available radius',
  );
  const slotCount = ordered[ordered.length - 1].band.ring + 1;
  const ringWidth = outerRadius / slotCount;
  const leaderLabelX = diagramWidth + 18;

  const layouts: BandLayout[] = ordered.map(({ band, sourceIndex }) => {
    const innerRadius = band.ring * ringWidth;
    const bandOuterRadius = (band.ring + 1) * ringWidth;
    const middleRadius = (innerRadius + bandOuterRadius) / 2;
    const label = `${band.title} — ${band.greek}`;
    const availableArc = Math.PI * middleRadius * 0.78;
    const fitsRing =
      ringWidth >= fontSizePx * 1.55 &&
      estimateTextWidth(label, fontSizePx) <= availableArc;

    return {
      band,
      sourceIndex,
      innerRadius,
      outerRadius: bandOuterRadius,
      middleRadius,
      labelPlacement: fitsRing ? 'ring' : 'leader',
      labelX: fitsRing ? cx : leaderLabelX,
      labelY: cy,
    };
  });

  const leaders = layouts.filter((layout) => layout.labelPlacement === 'leader');
  const leaderSpacing = fontSizePx * 3.35;
  leaders.forEach((layout, index) => {
    layout.labelY = cy + (index - (leaders.length - 1) / 2) * leaderSpacing;
  });

  const textPathDefs = layouts
    .filter((layout) => layout.labelPlacement === 'ring')
    .map((layout) => {
      const pathId = `${idPrefix}-label-${layout.sourceIndex}`;
      return `<path id="${pathId}" d="${upperArcPath(cx, cy, layout.middleRadius)}"/>`;
    })
    .join('');

  const bandMarkup = layouts
    .map((layout) => {
      const { band } = layout;
      const fill = RING_FILL_TOKENS[band.ring % RING_FILL_TOKENS.length];
      const titleText = `${band.title} — ${band.greek}. ${band.summary}`;
      const ariaLabel = `${band.title}, lines ${band.lines[0]}–${band.lines[1]}: ${band.summary}`;
      const shape =
        layout.innerRadius === 0
          ? `<circle cx="${round1(cx)}" cy="${round1(cy)}" r="${round1(layout.outerRadius)}" fill="${fill}" stroke="var(--shield-outline)" stroke-width="1"/>`
          : `<path d="${annulusPath(cx, cy, layout.innerRadius, layout.outerRadius)}" fill="${fill}" fill-rule="evenodd" stroke="var(--shield-outline)" stroke-width="1"/>`;

      let labelMarkup: string;
      if (layout.labelPlacement === 'ring') {
        const pathId = `${idPrefix}-label-${layout.sourceIndex}`;
        labelMarkup =
          `<text font-size="${fontSizePx}" font-family="var(--font-ui)" fill="var(--shield-label)" ` +
          `paint-order="stroke" stroke="var(--shield-label-halo)" stroke-width="2.5" stroke-linejoin="round">` +
          `<textPath href="#${pathId}" startOffset="50%" text-anchor="middle">` +
          `${escapeXml(band.title)} — ${escapeXml(band.greek)}` +
          `</textPath></text>`;
      } else {
        const lineStartX = cx + layout.middleRadius;
        const elbowX = cx + outerRadius + 9;
        const lineEndX = layout.labelX - 8;
        const lineEndY = layout.labelY - fontSizePx * 0.35;
        labelMarkup =
          `<line x1="${round1(lineStartX)}" y1="${round1(cy)}" x2="${round1(elbowX)}" y2="${round1(lineEndY)}" stroke="var(--shield-leader)" stroke-width="1"/>` +
          `<line x1="${round1(elbowX)}" y1="${round1(lineEndY)}" x2="${round1(lineEndX)}" y2="${round1(lineEndY)}" stroke="var(--shield-leader)" stroke-width="1"/>` +
          `<text x="${round1(layout.labelX)}" y="${round1(layout.labelY)}" text-anchor="start" font-size="${fontSizePx}" font-family="var(--font-ui)" fill="var(--shield-label)" paint-order="stroke" stroke="var(--shield-label-halo)" stroke-width="2.5" stroke-linejoin="round">` +
          `<tspan x="${round1(layout.labelX)}">${escapeXml(band.title)}</tspan>` +
          `<tspan x="${round1(layout.labelX)}" dy="${round1(fontSizePx * 1.2)}">${escapeXml(band.greek)}</tspan>` +
          `</text>`;
      }

      return (
        `<g data-band-id="${escapeXml(band.id)}" role="group" aria-label="${escapeXml(ariaLabel)}">` +
        `<title>${escapeXml(titleText)}</title>` +
        shape +
        labelMarkup +
        `</g>`
      );
    })
    .join('');

  const svg =
    `<svg viewBox="0 0 ${round1(width)} ${round1(height)}" width="100%" height="100%" role="img" ` +
    `aria-label="${escapeXml(plate.title)}" data-plate-id="${escapeXml(plate.id)}" xmlns="http://www.w3.org/2000/svg">` +
    (textPathDefs ? `<defs>${textPathDefs}</defs>` : '') +
    bandMarkup +
    `</svg>`;

  const bands: RenderedBand[] = layouts.map((layout) => ({
    id: layout.band.id,
    ring: layout.band.ring,
    innerRadius: round1(layout.innerRadius),
    outerRadius: round1(layout.outerRadius),
    labelPlacement: layout.labelPlacement,
    labelX: round1(layout.labelX),
    labelY: round1(layout.labelY),
  }));

  return { svg, bands };
}
