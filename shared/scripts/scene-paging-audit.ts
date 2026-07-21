// Scene-paging corpus audit (measurement only — John, 2026-07-21).
//
// Runs sentenceSnapScenePages against every book in the real corpus (both
// Murray and Butler translations) and reports how often the sentence-snap
// partition produces a page outside the safety properties John's brief for
// this module states: never mid-sentence, never empty (after the first
// page), never spilling text a scene doesn't own, never duplicating text
// across the guardrail. This is a PRE-FIX baseline — it does not assert
// anything and does not modify shared/lib/scene-paging.ts or its test. A
// later vitest gate is what turns these numbers into a pass/fail suite.
//
// Run from shared/:
//   source ~/.nvm/nvm.sh && nvm use 22 && node --experimental-strip-types scripts/scene-paging-audit.ts
//
// (Node 22's --experimental-strip-types requires explicit .ts extensions on
// relative imports — the "bundler" moduleResolution the rest of this package
// uses for tsc/vite is not in play when node runs this file directly.)

import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  chunksForScene,
  HOLLOW_MAX_CHARS,
  mergeSceneFlowChunks,
  pageCharLength,
  sentenceEndOffsets,
  sentenceSnapScenePages,
  type SceneFlowChunk,
} from '../lib/scene-paging.ts';
import { loadRealBoundaryOverrides, loadRealBook, type RealTranslation } from '../__tests__/real-book-loader.ts';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const EPICS = ['iliad', 'odyssey'] as const;
type Epic = (typeof EPICS)[number];
const BOOK_COUNT = 24;
const TRANSLATIONS: RealTranslation[] = ['murray', 'butler'];

// A non-empty page's END OFFSET (in the whole-book flattened text) must be a
// real sentence boundary — reusing sentenceEndOffsets' own membership is more
// faithful than re-testing the page's trailing text against a standalone
// regex: sentenceEndOffsets already knows about Murray's inline footnote
// markers (`...for itself.[^2.4.2]`, where the sentence truly ends BEFORE the
// marker) and abbreviation/quote guards, so reusing it here can't drift out of
// sync with what sentenceSnapScenePages itself considers a valid cut. The
// book's true final offset (whole.length) is also always a valid terminator —
// a page that runs to the very end of the book's flow is not a mid-sentence
// CUT even when the source text itself ends without terminal punctuation
// (e.g. Butler Od. 3's final tick, a documented pipeline extraction quirk,
// not a paging defect).
// "Shares a common substring of >= 40 chars with an adjacent page" per the
// audit brief — sufficient window size to catch real duplicated prose
// without false-positiving on short common phrases.
const DUP_WINDOW = 40;

// A page whose share of its own scene's owned Greek range falls below 0.5 —
// less than half the page's text is text that scene actually owns. Surfaced
// per book (not just the book-level worst) so every candidate becomes a
// concrete manual-review item for John: which scene, how bad, and the Greek
// line range in play (Codex new-finding 1, 2026-07-21).
export interface LowOwnershipPage {
  sceneIndex: number; // 1-indexed, matching this module's other scene-number reporting
  fraction: number; // fraction of the page's text actually inside its scene's owned tick union
  greekRange: [number, number];
}

export interface BookRow {
  epic: Epic;
  book: number;
  translation: RealTranslation;
  present: boolean;
  sceneCount: number;
  tickCount: number;
  hollowGuardrailFirings: number;
  emptyPagesPureSnap: number;
  midSentenceEndsPureSnap: number;
  outOfOwnedRangePages: number;
  duplicatedTextPages: number;
  partitionLossless: boolean;
  // WELL-FORMED tick-chunk INPUT flag (Codex review F1 diagnosis, 2026-07-21;
  // broadened Codex re-review 2026-07-21 — see chunkGeometryValid below). A
  // book failing this cannot fairly test scene-paging's own logic, so the
  // gate excludes it (its raw defect counts stay in this row + totals — the
  // corruption is surfaced, never hidden — and is reported to the pipeline lane).
  chunkGeometryValid: boolean;
  // Informational (Codex review F2, 2026-07-21): guardrail-ON pages holding the
  // COMPLETE prose of a short owned share (0 < len < HOLLOW_MAX_CHARS). These
  // are legitimate short-but-complete pages, NOT padded and NOT gated — counted
  // so they are visible in the report rather than silently short.
  shortPagesBelowHollowThreshold: number;
  // Informational (Codex review F3, 2026-07-21): worst per-page fraction of a
  // page's own text that falls OUTSIDE its scene's owned tick range (0 = fully
  // owned, 1 = wholly overflow). Surfaces gross overflow that the binary
  // zero-intersection `outOfOwnedRangePages` gate cannot see.
  worstOwnershipFraction: number;
  // Manual-review candidates (Codex new-finding 1, 2026-07-21): every page
  // whose OWNED share (1 - the fractionOutside above) is below 0.5. See
  // LowOwnershipPage; also rolled into AuditTotals.lowOwnershipPages as a count.
  lowOwnershipPages: LowOwnershipPage[];
  // Manual scene-boundary overrides (John, 2026-07-21): true when this book/
  // translation carries no override, or every override resolved cleanly.
  // false ⇒ resolveBoundaryOverrides threw (anchor not found or scene number
  // out of range) — a HARD gate failure, never silently ignored (see
  // scene-boundary-overrides.json's mechanism doc).
  overridesResolved: boolean;
  overrideErrors: string[];
  // 1-based scene numbers excluded from this row's ownership-fraction metric
  // because an override touches their page — see the exclusion comment at
  // the computation site in auditOneBook.
  overrideAffectedScenePages: number[];
}

export interface AuditTotals {
  hollowGuardrailFirings: number;
  emptyPagesPureSnap: number;
  midSentenceEndsPureSnap: number;
  outOfOwnedRangePages: number;
  duplicatedTextPages: number;
  // F3: partition-lossless failures are now a first-class total AND gate input.
  partitionLosslessFailures: number;
  // F2/F3 informational rollups.
  shortPagesBelowHollowThreshold: number;
  worstOwnershipFraction: number;
  // Codex new-finding 1 (2026-07-21): total count of LowOwnershipPage entries
  // across every book — see BookRow.lowOwnershipPages for the per-book list.
  lowOwnershipPages: number;
  // Manual scene-boundary overrides (John, 2026-07-21): books whose override
  // anchor(s) failed to resolve — see BookRow.overridesResolved.
  booksWithOverrideErrors: number;
  overrideErrors: string[];
  // Upstream tick-chunk corruption (see BookRow.chunkGeometryValid) —
  // surfaced loudly: how many books, and which. Excluded from gate correctness.
  booksWithCorruptChunks: number;
  corruptChunkBooks: string[];
  booksAudited: number;
  booksMissing: number;
}

export interface AuditGate {
  maxOutOfOwnedRange: 0;
  maxMidSentence: 0;
  maxEmptyPureSnap: 0;
  maxDuplicatedTextPages: 0;
  maxPartitionLosslessFailures: 0;
  // Regression floor (Codex new-finding 1, 2026-07-21): the minimum per-page
  // OWNED fraction (1 - fractionOutside) any well-formed book's page may drop
  // to before the gate fails. Set from the post-Od.10-fix corpus baseline,
  // rounded DOWN to a clean value — see the literal assignment below in
  // auditScenePaging for the observed worst page's identity and why a
  // legitimate straddle can land this low without being a defect.
  minOwnershipFraction: number;
  // Correctness sums over WELL-FORMED books only (chunkGeometryValid) —
  // an upstream-corrupt book (BookRow.chunkGeometryValid false) is not a
  // scene-paging defect and is excluded here; its raw numbers remain in
  // `totals`. `wellFormedBooks`/`excludedCorruptBooks` make the split explicit.
  wellFormedBooks: number;
  excludedCorruptBooks: number;
  emptyPagesPureSnap: number;
  midSentenceEndsPureSnap: number;
  outOfOwnedRangePages: number;
  duplicatedTextPages: number;
  partitionLosslessFailures: number;
  // Count of well-formed books whose WORST page falls below
  // minOwnershipFraction — a real gate input (unlike lowOwnershipPages/
  // shortPagesBelowHollowThreshold above, which stay informational). A lower
  // bound on the true violating-PAGE count (see the computation site).
  belowMinOwnershipPages: number;
  // Manual scene-boundary overrides (John, 2026-07-21): a real gate input —
  // any anchor-resolution failure fails the gate outright.
  overrideResolutionFailures: number;
  pass: boolean;
}

export interface AuditReport {
  buildDistPresent: true;
  books: BookRow[];
  totals: AuditTotals;
  gate: AuditGate;
}

export type AuditResult = AuditReport | { buildDistPresent: false };

function pageText(page: SceneFlowChunk): string {
  return page.flowParts.map((p) => p.text ?? '').join('');
}

function emptyRow(epic: Epic, book: number, translation: RealTranslation): BookRow {
  return {
    epic,
    book,
    translation,
    present: false,
    sceneCount: 0,
    tickCount: 0,
    hollowGuardrailFirings: 0,
    emptyPagesPureSnap: 0,
    midSentenceEndsPureSnap: 0,
    outOfOwnedRangePages: 0,
    duplicatedTextPages: 0,
    partitionLossless: false,
    chunkGeometryValid: true,
    shortPagesBelowHollowThreshold: 0,
    worstOwnershipFraction: 0,
    lowOwnershipPages: [],
    overridesResolved: true,
    overrideErrors: [],
    overrideAffectedScenePages: [],
  };
}

// A Set of every DUP_WINDOW-length substring of `text` (empty if too short).
function windowSet(text: string): Set<string> {
  const out = new Set<string>();
  for (let i = 0; i + DUP_WINDOW <= text.length; i++) out.add(text.slice(i, i + DUP_WINDOW));
  return out;
}

function auditOneBook(distRoot: string, epic: Epic, book: number, translation: RealTranslation): BookRow {
  const bookNum = String(book).padStart(2, '0');
  const filePath = path.join(distRoot, epic, `book-${bookNum}.json`);
  const loaded = loadRealBook(filePath, translation);
  if (!loaded) return emptyRow(epic, book, translation);

  const { chunks, scenes } = loaded;

  // Manual scene-boundary overrides (John, 2026-07-21): resolved the SAME way
  // Reader.svelte does (loadRealBoundaryOverrides → selectBoundaryOverrideEntries
  // + resolveBoundaryOverrides, shared/lib/scene-paging.ts), so this audit
  // measures the geometry actually shown to readers, not the pre-override one.
  // A resolution failure (missing anchor / bad scene number) is a HARD gate
  // failure — surfaced via overridesResolved/overrideErrors below, never
  // silently ignored — and the book falls back to computing its OTHER metrics
  // with no overrides applied (so the rest of the row still reports honestly).
  let boundaryOverrides: ReturnType<typeof loadRealBoundaryOverrides> = [];
  let overridesResolved = true;
  const overrideErrors: string[] = [];
  try {
    boundaryOverrides = loadRealBoundaryOverrides(epic, book, translation, chunks, scenes);
  } catch (err) {
    overridesResolved = false;
    overrideErrors.push(err instanceof Error ? err.message : String(err));
  }

  // Every scene index (0-based) whose PAGE TEXT an override touches: the
  // pinned scene itself, and the scene immediately before it (whose end moved
  // to the same offset). The ownership-fraction metric below measures
  // conformance to the Greek-tick alignment scene-paging derives automatically
  // — exactly what a manual override deliberately overrules (that's the whole
  // point of John's correction), so these pages are excluded from that metric
  // specifically, WITH attribution (overrideAffectedScenePages), not silently.
  // Every OTHER invariant (mid-sentence, empty, lossless, duplication) still
  // applies to these pages with no exception — see the corpus audit gate test.
  const overrideAffectedSceneIndices = new Set<number>();
  for (const o of boundaryOverrides) {
    overrideAffectedSceneIndices.add(o.sceneIndex);
    if (o.sceneIndex > 0) overrideAffectedSceneIndices.add(o.sceneIndex - 1);
  }

  const pureOff = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: false, boundaryOverrides });
  const guardOn = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: true, boundaryOverrides });

  // ── partitionLossless: pureOff pages concatenated === mergeSceneFlowChunks(chunks) text ──
  const whole = mergeSceneFlowChunks(chunks).flowParts.map((p) => p.text ?? '').join('');
  const rebuilt = pureOff.map(pageText).join('');
  const partitionLossless = rebuilt === whole;

  // ── hollowGuardrailFirings: guardrail-ON page text differs from guardrail-OFF at same index ──
  let hollowGuardrailFirings = 0;
  for (let i = 0; i < guardOn.length; i++) {
    if (pageText(guardOn[i]) !== pageText(pureOff[i])) hollowGuardrailFirings++;
  }

  // Real sentence-end offsets in the SAME flattened whole-book text pureOff's
  // pages slice from (identical join rule, so identical string — see the
  // module's own buildBookFlow comment) — membership in this set (or landing
  // exactly at the book's true end) is what "ends cleanly" means.
  const sentenceEnds = sentenceEndOffsets(whole);
  const sentenceEndSet = new Set(sentenceEnds);

  // Cumulative [from, to) offset each pureOff page occupies in `whole` —
  // needed both for the mid-sentence offset check below and for
  // outOfOwnedRangePages further down.
  const pageFrom: number[] = [];
  const pageTo: number[] = [];
  {
    let cursor = 0;
    for (const p of pureOff) {
      pageFrom.push(cursor);
      cursor += pageCharLength(p);
      pageTo.push(cursor);
    }
  }

  // ── emptyPagesPureSnap (non-first pages) / midSentenceEndsPureSnap (ALL pages) ──
  // Empty check: pages after the first (page 0 is the book's own opening).
  // Mid-sentence check: EVERY page incl. index 0 (Codex review F3 — the opening
  // page can end mid-sentence too and must not be exempt). The true-end
  // exemption applies ONLY to the final page: a NON-final page that happens to
  // reach whole.length still ends mid-sentence if it doesn't land on a real
  // sentence boundary (F3 — was previously exempting any page reaching the end).
  let emptyPagesPureSnap = 0;
  let midSentenceEndsPureSnap = 0;
  const lastIdx = pureOff.length - 1;
  for (let i = 0; i < pureOff.length; i++) {
    const t = pageText(pureOff[i]).trim();
    if (t === '') {
      if (i >= 1) emptyPagesPureSnap++;
      continue;
    }
    const endsAtTrueEnd = i === lastIdx && pageTo[i] >= whole.length;
    const endsAtRealSentence = sentenceEndSet.has(pageTo[i]);
    if (!endsAtTrueEnd && !endsAtRealSentence) midSentenceEndsPureSnap++;
  }

  // ── outOfOwnedRangePages (guardrail OFF) ──
  // Map each chunk's own contribution onto the same cumulative-offset space
  // pureOff's pages occupy in `whole`: mergeSceneFlowChunks processes chunks
  // left-to-right via the identical join rule buildBookFlow uses internally
  // (see scene-paging.ts's own comment on joinChunkFlow being shared), so
  // pageCharLength(mergeSceneFlowChunks(chunks.slice(0, i + 1))) reproduces
  // buildBookFlow's private chunkTextEnd[i] without needing that internal.
  const chunkEnd: number[] = [];
  for (let i = 0; i < chunks.length; i++) {
    chunkEnd.push(pageCharLength(mergeSceneFlowChunks(chunks.slice(0, i + 1))));
  }
  const chunkStart = (i: number) => (i === 0 ? 0 : chunkEnd[i - 1]);

  // Gate: pages with ZERO intersection with their scene's owned tick union
  // (unchanged). Informational: the WORST per-page fraction of page text that
  // falls OUTSIDE that union — a page can touch its owned range by a single
  // char and pass the binary gate while being mostly overflow, so this measures
  // how much (Codex review F3).
  let outOfOwnedRangePages = 0;
  let worstOwnershipFraction = 0;
  const lowOwnershipPages: LowOwnershipPage[] = [];
  for (let i = 0; i < pureOff.length; i++) {
    if (pageText(pureOff[i]).trim() === '') continue;
    const selected = chunksForScene(chunks, scenes[i]);
    const from = pageFrom[i];
    const to = pageTo[i];
    if (to <= from) continue;
    const greekRange: [number, number] = [scenes[i].startLine, scenes[i].endLine ?? scenes[i].startLine];
    let overlaps = false;
    for (const idx of selected) {
      const cs = chunkStart(idx);
      const ce = chunkEnd[idx];
      if (cs < to && ce > from) {
        overlaps = true;
        break;
      }
    }
    if (!overlaps) {
      outOfOwnedRangePages++;
      worstOwnershipFraction = 1; // no owned text at all on this page
      lowOwnershipPages.push({ sceneIndex: i + 1, fraction: 0, greekRange });
      continue;
    }
    // Override-affected pages (John's editorial boundary pins + their
    // predecessors) intentionally defy the tick alignment, so they are exempt
    // from the FRACTION accounting below — but the binary zero-overlap gate
    // above still applies to them in full (Codex verify finding 1: the
    // exclusion must not widen beyond the fraction/floor metrics).
    if (overrideAffectedSceneIndices.has(i)) continue;
    // Fraction of [from, to) outside the union [unionStart, unionEnd) of the
    // scene's owned chunks.
    const unionStart = Math.min(...selected.map((idx) => chunkStart(idx)));
    const unionEnd = Math.max(...selected.map((idx) => chunkEnd[idx]));
    const inside = Math.max(0, Math.min(to, unionEnd) - Math.max(from, unionStart));
    const fractionOutside = ((to - from) - inside) / (to - from);
    if (fractionOutside > worstOwnershipFraction) worstOwnershipFraction = fractionOutside;
    // Codex new-finding 1: surface every page under half-owned as a manual-
    // review candidate — not just the book's single worst.
    const ownershipFraction = 1 - fractionOutside;
    if (ownershipFraction < 0.5) {
      lowOwnershipPages.push({ sceneIndex: i + 1, fraction: ownershipFraction, greekRange });
    }
  }

  // ── duplicatedTextPages: guardrail-caused duplication only ──
  // Measurement honesty (John, 2026-07-21): the corpus is full of genuine
  // Homeric formulaic repetition (near-verbatim repeated lines across
  // adjacent pages), which a plain "shares a 40-char run with the previous
  // page" scan can't tell apart from actual guardrail duplication — and the
  // guardrail-OFF partition is provably disjoint (partitionLossless), so any
  // such formulaic overlap there is not this module's doing. Count a page
  // ONLY when (a) the guardrail actually fired on it (its guardrail-ON text
  // differs from the guardrail-OFF text at the same index — a page the
  // guardrail left untouched can't be blamed for duplication) AND (b) the
  // fired page shares a >=40-char run with an ADJACENT page (previous or
  // next — the bounded fallback in scene-paging.ts can only ever straddle
  // into a neighbor, never duplicate anything further away).
  let duplicatedTextPages = 0;
  for (let i = 0; i < guardOn.length; i++) {
    const cur = pageText(guardOn[i]);
    if (cur === pageText(pureOff[i])) continue; // guardrail did not fire here
    if (cur.trim() === '' || cur.length < DUP_WINDOW) continue;
    const curWindows = windowSet(cur);
    let dup = false;
    for (const j of [i - 1, i + 1]) {
      if (j < 0 || j >= guardOn.length) continue;
      const neighbor = pageText(guardOn[j]);
      if (neighbor.trim() === '' || neighbor.length < DUP_WINDOW) continue;
      for (let w = 0; w + DUP_WINDOW <= neighbor.length; w++) {
        if (curWindows.has(neighbor.slice(w, w + DUP_WINDOW))) {
          dup = true;
          break;
        }
      }
      if (dup) break;
    }
    if (dup) duplicatedTextPages++;
  }

  // ── shortPagesBelowHollowThreshold (guardrail ON) ──
  // Legitimately short-but-complete pages (0 < len < HOLLOW_MAX_CHARS) the
  // guardrail left in place — surfaced, not gated (Codex review F2).
  let shortPagesBelowHollowThreshold = 0;
  for (const p of guardOn) {
    const len = pageCharLength(p);
    if (len > 0 && len < HOLLOW_MAX_CHARS) shortPagesBelowHollowThreshold++;
  }

  // ── chunkGeometryValid: well-formed tick-chunk INPUT? ──
  // A backward OR EQUAL jump in chunk startLine, an overlap between adjacent
  // chunks' [startLine, endLine] spans, or an inverted chunk (endLine <
  // startLine) is the signature of alignGroups' `lineIndex.get(n) ?? 0`
  // fallback firing on a snap target absent from the Greek (upstream dropped
  // vulgate line — Od. 10.456, pre-fix). Broadened beyond strictly-backward
  // startLine (Codex re-review, 2026-07-21): a repeated startLine (two chunks
  // both restarting at the same collapsed index) or an overlap is the same
  // corruption signature and was previously invisible to this check. After the
  // tick-chunks.ts speech-snap hardening (nearest-extant-line resolution),
  // Odyssey 10 (Murray) no longer trips this — see scene-paging.test.ts.
  let chunkGeometryValid = true;
  for (let i = 0; i < chunks.length; i++) {
    if (chunks[i].endLine < chunks[i].startLine) { chunkGeometryValid = false; break; }
    if (i > 0 && chunks[i].startLine <= chunks[i - 1].startLine) { chunkGeometryValid = false; break; }
    if (i > 0 && chunks[i].startLine <= chunks[i - 1].endLine) { chunkGeometryValid = false; break; }
  }

  return {
    epic,
    book,
    translation,
    present: true,
    sceneCount: scenes.length,
    tickCount: chunks.length,
    hollowGuardrailFirings,
    emptyPagesPureSnap,
    midSentenceEndsPureSnap,
    outOfOwnedRangePages,
    duplicatedTextPages,
    partitionLossless,
    chunkGeometryValid,
    shortPagesBelowHollowThreshold,
    worstOwnershipFraction,
    lowOwnershipPages,
    overridesResolved,
    overrideErrors,
    overrideAffectedScenePages: [...overrideAffectedSceneIndices].sort((a, b) => a - b).map((i) => i + 1),
  };
}

export function auditScenePaging(distRoot: string): AuditResult {
  if (!existsSync(distRoot)) return { buildDistPresent: false };

  const books: BookRow[] = [];
  for (const epic of EPICS) {
    for (let book = 1; book <= BOOK_COUNT; book++) {
      for (const translation of TRANSLATIONS) {
        books.push(auditOneBook(distRoot, epic, book, translation));
      }
    }
  }

  // totals: RAW sums over every present book — the honest, nothing-hidden view
  // (a corrupt book's defect counts are included here so the corruption shows).
  const totals: AuditTotals = {
    hollowGuardrailFirings: 0,
    emptyPagesPureSnap: 0,
    midSentenceEndsPureSnap: 0,
    outOfOwnedRangePages: 0,
    duplicatedTextPages: 0,
    partitionLosslessFailures: 0,
    shortPagesBelowHollowThreshold: 0,
    worstOwnershipFraction: 0,
    lowOwnershipPages: 0,
    booksWithCorruptChunks: 0,
    corruptChunkBooks: [],
    booksAudited: 0,
    booksMissing: 0,
    booksWithOverrideErrors: 0,
    overrideErrors: [],
  };
  for (const row of books) {
    if (row.present) totals.booksAudited++;
    else totals.booksMissing++;
    totals.hollowGuardrailFirings += row.hollowGuardrailFirings;
    totals.emptyPagesPureSnap += row.emptyPagesPureSnap;
    totals.midSentenceEndsPureSnap += row.midSentenceEndsPureSnap;
    totals.outOfOwnedRangePages += row.outOfOwnedRangePages;
    totals.duplicatedTextPages += row.duplicatedTextPages;
    totals.shortPagesBelowHollowThreshold += row.shortPagesBelowHollowThreshold;
    totals.lowOwnershipPages += row.lowOwnershipPages.length;
    if (row.present && !row.partitionLossless) totals.partitionLosslessFailures++;
    if (row.worstOwnershipFraction > totals.worstOwnershipFraction) totals.worstOwnershipFraction = row.worstOwnershipFraction;
    if (row.present && !row.chunkGeometryValid) {
      totals.booksWithCorruptChunks++;
      totals.corruptChunkBooks.push(`${row.epic} ${row.book} ${row.translation}`);
    }
    if (row.present && !row.overridesResolved) {
      totals.booksWithOverrideErrors++;
      totals.overrideErrors.push(`${row.epic} ${row.book} ${row.translation}: ${row.overrideErrors.join('; ')}`);
    }
  }

  // gate: correctness sums over WELL-FORMED present books only. A book with
  // corrupt tick-chunk INPUT (chunkGeometryValid false — an UPSTREAM dropped
  // vulgate line, see BookRow doc) cannot fairly test scene-paging and is
  // excluded; it is surfaced via totals.corruptChunkBooks and reported to
  // the pipeline lane, never silently zeroed. partitionLossless is folded in
  // (any failure ⇒ fail) per Codex review F3.
  const wellFormed = books.filter((b) => b.present && b.chunkGeometryValid);
  const sum = (pick: (b: BookRow) => number) => wellFormed.reduce((a, b) => a + pick(b), 0);
  const gateEmpty = sum((b) => b.emptyPagesPureSnap);
  const gateMid = sum((b) => b.midSentenceEndsPureSnap);
  const gateOut = sum((b) => b.outOfOwnedRangePages);
  const gateDup = sum((b) => b.duplicatedTextPages);
  const gateLosslessFailures = wellFormed.filter((b) => !b.partitionLossless).length;
  // Regression floor (Codex new-finding 1, 2026-07-21): the worst per-page
  // OWNED fraction (1 - worstOwnershipFraction) observed across the WHOLE
  // well-formed corpus, post the tick-chunks.ts speech-snap fix (Od. 10
  // Murray no longer corrupt — see scene-paging.test.ts), was 0.7160 on
  // Odyssey 21 (Butler) scene 2 (Greek 42-67) — a scene whose owned Greek
  // range sits mostly inside one coarse tick that straddles ~28% of its page
  // into the neighboring scene; John-approved design (bounded straddle
  // duplication on coarse ticks is deliberate, not a defect). Gated at 0.7,
  // rounded down from that observed worst, so this is a REGRESSION floor
  // catching future degradation, not a design constraint on today's corpus.
  //
  // Computed from the per-book worstOwnershipFraction (not from
  // lowOwnershipPages, which is a fixed <0.5 informational cutoff decoupled
  // from this floor — see BookRow.lowOwnershipPages) so the floor works
  // correctly regardless of where 0.7 sits relative to 0.5. A book's WORST
  // page failing the floor is what's counted; if several pages in the same
  // book are all under the floor, this is a lower bound on the true page
  // count (the per-page detail lives in a fresh corpus run's lowOwnershipPages
  // once the floor is ever lowered near 0.5).
  const MIN_OWNERSHIP_FRACTION = 0.7;
  const belowMinOwnershipPages = wellFormed.filter(
    (b) => (1 - b.worstOwnershipFraction) < MIN_OWNERSHIP_FRACTION,
  ).length;
  const gate: AuditGate = {
    maxOutOfOwnedRange: 0,
    maxMidSentence: 0,
    maxEmptyPureSnap: 0,
    maxDuplicatedTextPages: 0,
    maxPartitionLosslessFailures: 0,
    minOwnershipFraction: MIN_OWNERSHIP_FRACTION,
    wellFormedBooks: wellFormed.length,
    excludedCorruptBooks: totals.booksWithCorruptChunks,
    emptyPagesPureSnap: gateEmpty,
    midSentenceEndsPureSnap: gateMid,
    outOfOwnedRangePages: gateOut,
    duplicatedTextPages: gateDup,
    partitionLosslessFailures: gateLosslessFailures,
    belowMinOwnershipPages,
    overrideResolutionFailures: totals.booksWithOverrideErrors,
    pass: gateOut <= 0
      && gateMid <= 0
      && gateEmpty <= 0
      && gateDup <= 0
      && gateLosslessFailures <= 0
      && belowMinOwnershipPages <= 0
      && totals.booksWithOverrideErrors <= 0,
  };

  return { buildDistPresent: true, books, totals, gate };
}

// ── CLI entry ────────────────────────────────────────────────────────────
function isMainModule(): boolean {
  const invoked = process.argv[1] ? path.resolve(process.argv[1]) : '';
  return invoked === fileURLToPath(import.meta.url);
}

if (isMainModule()) {
  const distRoot = path.resolve(__dirname, '../../build/dist');
  const report = auditScenePaging(distRoot);
  // eslint-disable-next-line no-console
  console.log(JSON.stringify(report, null, 2));
  process.exit(0);
}
