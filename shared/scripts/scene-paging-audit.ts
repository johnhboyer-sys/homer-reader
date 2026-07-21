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
  sentenceSnapScenePages,
  type SceneFlowChunk,
} from '../lib/scene-paging.ts';
import { loadRealBook, type RealTranslation } from '../__tests__/real-book-loader.ts';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const EPICS = ['iliad', 'odyssey'] as const;
type Epic = (typeof EPICS)[number];
const BOOK_COUNT = 24;
const TRANSLATIONS: RealTranslation[] = ['murray', 'butler'];

// Non-empty page text (guardrail off) must end in a real sentence terminator
// (with optional trailing quote/paren/bracket) — mirrors John's "never end a
// page mid-sentence" rule from scene-paging.ts's own header comment.
const SENTENCE_END_TRAIL_RE = /[.?!]["'”’)\]]*$/;
// "Shares a common substring of >= 40 chars with the previous page" per the
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

  // ── emptyPagesPureSnap / midSentenceEndsPureSnap (non-first pages, guardrail OFF) ──
  let emptyPagesPureSnap = 0;
  let midSentenceEndsPureSnap = 0;
  for (let i = 1; i < pureOff.length; i++) {
    const t = pageText(pureOff[i]).trim();
    if (t === '') {
      emptyPagesPureSnap++;
      continue;
    }
    if (!SENTENCE_END_TRAIL_RE.test(t)) midSentenceEndsPureSnap++;
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

  // ── duplicatedTextPages (guardrail ON): page i shares a >=40-char window with page i-1 ──
  let duplicatedTextPages = 0;
  for (let i = 1; i < guardOn.length; i++) {
    const cur = pageText(guardOn[i]);
    const prev = pageText(guardOn[i - 1]);
    if (cur.trim() === '' || prev.trim() === '') continue;
    if (cur.length < DUP_WINDOW || prev.length < DUP_WINDOW) continue;
    const prevWindows = windowSet(prev);
    let dup = false;
    for (let w = 0; w + DUP_WINDOW <= cur.length; w++) {
      if (prevWindows.has(cur.slice(w, w + DUP_WINDOW))) {
        dup = true;
        break;
      }
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
    pass: totals.outOfOwnedRangePages <= 0 && totals.midSentenceEndsPureSnap <= 0 && totals.emptyPagesPureSnap <= 0,
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
