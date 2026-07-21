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
  mergeSceneFlowChunks,
  pageCharLength,
  sentenceEndOffsets,
  sentenceSnapScenePages,
  type SceneFlowChunk,
} from '../lib/scene-paging.ts';
import { loadRealBook, type RealTranslation } from '../__tests__/real-book-loader.ts';

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
}

export interface AuditTotals {
  hollowGuardrailFirings: number;
  emptyPagesPureSnap: number;
  midSentenceEndsPureSnap: number;
  outOfOwnedRangePages: number;
  duplicatedTextPages: number;
  booksAudited: number;
  booksMissing: number;
}

export interface AuditGate {
  maxOutOfOwnedRange: 0;
  maxMidSentence: 0;
  maxEmptyPureSnap: 0;
  maxDuplicatedTextPages: 0;
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

  const pureOff = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: false });
  const guardOn = sentenceSnapScenePages(chunks, scenes, { applyHollowGuardrail: true });

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

  // ── emptyPagesPureSnap / midSentenceEndsPureSnap (non-first pages, guardrail OFF) ──
  let emptyPagesPureSnap = 0;
  let midSentenceEndsPureSnap = 0;
  for (let i = 1; i < pureOff.length; i++) {
    const t = pageText(pureOff[i]).trim();
    if (t === '') {
      emptyPagesPureSnap++;
      continue;
    }
    const endsAtTrueEnd = pageTo[i] >= whole.length;
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

  let outOfOwnedRangePages = 0;
  for (let i = 0; i < pureOff.length; i++) {
    if (pageText(pureOff[i]).trim() === '') continue;
    const selected = chunksForScene(chunks, scenes[i]);
    const from = pageFrom[i];
    const to = pageTo[i];
    let overlaps = false;
    for (const idx of selected) {
      const cs = chunkStart(idx);
      const ce = chunkEnd[idx];
      if (cs < to && ce > from) {
        overlaps = true;
        break;
      }
    }
    if (!overlaps) outOfOwnedRangePages++;
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

  const totals: AuditTotals = {
    hollowGuardrailFirings: 0,
    emptyPagesPureSnap: 0,
    midSentenceEndsPureSnap: 0,
    outOfOwnedRangePages: 0,
    duplicatedTextPages: 0,
    booksAudited: 0,
    booksMissing: 0,
  };
  for (const row of books) {
    if (row.present) totals.booksAudited++;
    else totals.booksMissing++;
    totals.hollowGuardrailFirings += row.hollowGuardrailFirings;
    totals.emptyPagesPureSnap += row.emptyPagesPureSnap;
    totals.midSentenceEndsPureSnap += row.midSentenceEndsPureSnap;
    totals.outOfOwnedRangePages += row.outOfOwnedRangePages;
    totals.duplicatedTextPages += row.duplicatedTextPages;
  }

  const gate: AuditGate = {
    maxOutOfOwnedRange: 0,
    maxMidSentence: 0,
    maxEmptyPureSnap: 0,
    maxDuplicatedTextPages: 0,
    pass: totals.outOfOwnedRangePages <= 0
      && totals.midSentenceEndsPureSnap <= 0
      && totals.emptyPagesPureSnap <= 0
      && totals.duplicatedTextPages <= 0,
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
