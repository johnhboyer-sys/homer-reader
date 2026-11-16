// The reader's scene pages as character spans of each translation's own text
// (app/scripts/scene-pages.ts), pinned on hand-made books. The spans feed
// pipeline/homer_pipeline/search_scenes.py, which counts the words in them.
import { describe, expect, it } from 'vitest';
import { decoratedToRaw, translationPages, type PagedTranslationRef } from '../../scripts/scene-pages.ts';
import { decoratePiece } from '../../../shared/lib/kosmos.ts';

const NO_OVERRIDES = { _source: '', _semantics: '', overrides: [] };
const LINES = Array.from({ length: 10 }, (_, i) => ({ n: i + 1, text: '', tokens: [] }));
const SCENES = [{ startLine: 1, endLine: 4 }, { startLine: 5, endLine: 10 }];
const MURRAY: PagedTranslationRef = { id: 'murray', slot: 'english' };
const KOSMOS: PagedTranslationRef = { id: 'kosmos', slot: 'overlay', verseGroups: true };

// "Then" (offset 37) opens line 5's group.
const TEXT = 'Sing goddess. The wrath of Achilles. Then Zeus spoke. And all was done.';

function pages(seg: object, translation: PagedTranslationRef, overrides: object = NO_OVERRIDES) {
  return translationPages({
    seg: { id: '1:1', book: 1, column: '1', greek: LINES, ...seg } as never,
    translation, scenes: SCENES, speechStarts: [], overrides: overrides as never, work: 'iliad', book: 1,
  });
}

describe('translationPages', () => {
  it('gives each scene the spans of the text its page shows', () => {
    const got = pages({ english: { text: TEXT, bekker: [{ n: 1, offset: 0, real: true }, { n: 5, offset: 37, real: true }] } }, MURRAY);
    expect(got).toMatchObject({ slot: 'english', anchored: true, offPage: 0, onTwoPages: 0 });
    expect(got!.pages).toEqual([[[0, 37]], [[37, TEXT.length]]]);
  });

  it('cuts at a sentence end, not at the line mark', () => {
    // The mark for line 5 falls mid-sentence; the page runs on to the full stop.
    const text = 'Sing goddess of the wrath. It came. Then Zeus spoke at length. And all was done.';
    const mid = text.indexOf('spoke');
    const got = pages({ english: { text, bekker: [{ n: 1, offset: 0, real: true }, { n: 5, offset: mid, real: true }] } }, MURRAY);
    const end = text.indexOf('And');
    expect(got!.pages).toEqual([[[0, end]], [[end, text.length]]]);
  });

  it('reports spans in the piece’s own offsets, past Kosmos’s sentinels', () => {
    const text = 'Anger [mēnis], goddess, sing it. Then speech came.';
    const piece = {
      chapter: '1', cont: false, text,
      bekker: [{ n: 1, offset: 0, real: true }, { n: 5, offset: 33, real: true }],
      spans: [[6, 13, 'tr']] as [number, number, 'tr'][],
      marks: [{ n: 3, offset: 20, label: '3', reason: 'repeat' }],
    };
    const got = pages({ overlays: { kosmos: [piece] } }, KOSMOS);
    expect(got).toMatchObject({ slot: 'overlay-kosmos', anchored: true, offPage: 0, onTwoPages: 0 });
    expect(got!.pages).toEqual([[[0, 33]], [[33, text.length]]]);
  });

  it('does not page a text with one line mark', () => {
    const got = pages({ english: { text: TEXT, bekker: [{ n: 1, offset: 0, real: true }] } }, MURRAY);
    expect(got).toEqual({ slot: 'english', anchored: false, pages: null, offPage: 0, onTwoPages: 0 });
  });

  it('is null for a translation the book does not carry', () => {
    expect(pages({}, KOSMOS)).toBeNull();
  });

  it('follows a boundary override, and records one that does not resolve', () => {
    const bekker = [{ n: 1, offset: 0, real: true }, { n: 5, offset: 37, real: true }];
    const pinned = { _source: '', _semantics: '', overrides: [{ work: 'iliad', book: 1, translation: 'murray', sceneNumber: 2, startAnchor: 'And all' }] };
    const and = TEXT.indexOf('And all');
    expect(pages({ english: { text: TEXT, bekker } }, MURRAY, pinned)!.pages).toEqual([[[0, and]], [[and, TEXT.length]]]);
    const lost = { ...pinned, overrides: [{ ...pinned.overrides[0], startAnchor: 'not in the text' }] };
    const got = pages({ english: { text: TEXT, bekker } }, MURRAY, lost);
    expect(got!.pages).toEqual([[[0, 37]], [[37, TEXT.length]]]);
    expect(got!.overrideError).toMatch(/not found/);
  });
});

describe('decoratedToRaw', () => {
  it('maps every character decoratePiece keeps back to the piece', () => {
    const piece = { chapter: '1', cont: false, text: 'ab [cd] ef\ngh', spans: [[3, 7, 'tr'], [8, 10, 'em']] as [number, number, 'tr' | 'em'][], marks: [{ n: 2, offset: 11, label: '12', reason: 'repeat' }], bekker: [{ n: 1, offset: 0, real: true }] };
    const d = decoratePiece(piece);
    const map = decoratedToRaw(d.text, piece.text);
    const kept = [...map].filter(r => r >= 0);
    expect(kept).toEqual([...piece.text].map((_, i) => i));
    for (let i = 0; i < map.length; i++) if (map[i] >= 0) expect(d.text[i]).toBe(piece.text[map[i]]);
  });

  it('refuses a decorated text that is not the piece', () => {
    expect(() => decoratedToRaw('abX', 'abc')).toThrow();
  });
});
