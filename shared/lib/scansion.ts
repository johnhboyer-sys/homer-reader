// Meter-overlay rendering logic (feature #19, reader half): pure glyph +
// confidence-honesty helpers consumed by shared/components/Reader.svelte. No
// DOM, no fetch — see shared/lib/data.ts's fetchScansion for the
// scansion-<NN>.json contract and pipeline/homer_pipeline/apparatus_scansion.py
// for how a line's scan is computed. Homer-only; no plato-reader counterpart
// (Plato's corpus is prose, not hexameter).

import type { ScansionEntry } from './data';

// A line's honesty tier for display, derived from the data's actual
// confidence + notes (the pipeline never emits a third "unresolved"
// confidence value — see apparatus_scansion.py's scan_line: an unresolved
// line is `confidence: "ambiguous"` PLUS a `notes` entry of "unresolved").
//   - "normal": one unambiguous scan — render the feet plainly.
//   - "ambiguous": more than one minimal-relaxation derivation ties — a REAL
//     pattern (the solver's best answer), just philologically disputed.
//     Rendered visibly qualified, never presented as certain.
//   - "unresolved": no parse was found at any relaxation level; `feet` is a
//     best-effort placeholder with no evidentiary weight. NEVER rendered as
//     a pattern — a quiet placeholder only.
export type ScansionTier = 'normal' | 'ambiguous' | 'unresolved';

export function scansionTier(entry: Pick<ScansionEntry, 'confidence' | 'notes'>): ScansionTier {
  if (entry.confidence !== 'ambiguous') return 'normal';
  return entry.notes.includes('unresolved') ? 'unresolved' : 'ambiguous';
}

// Traditional scansion glyphs: dactyl (long-short-short), spondee
// (long-long), and the verse-final anceps (a long-counted final syllable,
// occasionally admitting a naturally short one — "brevis in longo", flagged
// separately in notes). "—" = long (macron), "◡" = short (breve), "×" =
// anceps (either).
const FOOT_GLYPHS: Record<string, string> = {
  D: '—◡◡',
  S: '——',
  X: '—×',
};

// A plain space between feet reads as a clean, thin break at this glyph
// weight without needing a visible separator character; letter-spacing on
// the containing element (see the Reader.svelte meter-tag styles) opens it
// further for legibility.
const FOOT_SEPARATOR = ' ';

// The 6-char feet string ("DDSDDX") -> its glyph rendering
// ("—◡◡ —◡◡ —— —◡◡ —◡◡ —×"). An unrecognized character (never emitted by the
// pipeline, but this is a display function, not a validator) passes through
// literally rather than throwing.
export function renderFeet(feet: string): string {
  return feet.split('').map((ch) => FOOT_GLYPHS[ch] ?? ch).join(FOOT_SEPARATOR);
}

const NOTE_LABELS: Record<string, string> = {
  synizesis: 'synizesis',
  correption: 'correption',
  'digamma-assumed': 'digamma assumed',
  'muta-cum-liquida': 'muta cum liquida',
  hiatus: 'hiatus',
  'brevis-in-longo': 'brevis in longo',
  unresolved: 'unresolved',
};

// notes[] -> a plain, comma-joined tooltip string ("synizesis, hiatus").
// Unknown flags pass through as-is (forward-compatible with a future note
// the solver adds).
export function formatNotes(notes: string[]): string {
  return notes.map((n) => NOTE_LABELS[n] ?? n).join(', ');
}

export interface ScansionDisplay {
  tier: ScansionTier;
  // The visible meter text: rendered feet (normal/ambiguous) or the honest
  // "—" placeholder (unresolved). Ambiguous lines are prefixed "≈" so the
  // qualification survives even where CSS dimming doesn't (copy/paste,
  // print, forced-colors mode).
  text: string;
  // Tooltip (title attribute) text, or undefined when there is nothing to
  // say (a high-confidence line with no philological notes).
  title: string | undefined;
}

// One scansion entry -> what the reader should actually show. The single
// point of truth for the honesty rules in the task brief: unresolved lines
// NEVER show a fake pattern; ambiguous lines are visibly qualified with the
// real (disputed) pattern; high-confidence lines render plainly, with any
// notes still surfaced as a tooltip (e.g. Il. 1.1: confidence "high" but
// notes ["brevis-in-longo","hiatus","synizesis"] — a clean scan can still be
// worth annotating).
export function scansionDisplay(entry: ScansionEntry): ScansionDisplay {
  const tier = scansionTier(entry);
  if (tier === 'unresolved') {
    return { tier, text: '—', title: 'no confident scan' };
  }
  const glyphs = renderFeet(entry.feet);
  const noteText = entry.notes.length ? formatNotes(entry.notes) : '';
  if (tier === 'ambiguous') {
    const title = noteText
      ? `ambiguous scan (more than one reading fits) — ${noteText}`
      : 'ambiguous scan (more than one reading fits)';
    return { tier, text: `≈ ${glyphs}`, title };
  }
  return { tier, text: glyphs, title: noteText || undefined };
}

// "<book>.<line>" key builder — matches apparatus_scansion.py's `f"{book}.{line}"`
// exactly (no zero-padding on either side).
export function scansionKey(book: number, line: number): string {
  return `${book}.${line}`;
}
