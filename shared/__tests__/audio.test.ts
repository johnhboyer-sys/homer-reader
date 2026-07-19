import { describe, expect, it } from 'vitest';
import {
  isRevisionChunk,
  bookAudio,
  hasAudio,
  lineInGap,
  chunkForLine,
  effectiveChunks,
  licenseLabel,
  chunkAriaLabel,
  itemPageUrl,
  type AudioBookEntry,
  type AudioManifest,
} from '../lib/audio';

// A synthetic manifest shaped like apparatus/audio/manifest.json, with an
// Iliad 1-shaped contiguous book, an Iliad 6-shaped book carrying an
// overlapping revision set, an Iliad 8-shaped book with a recorded gap, and
// no Odyssey coverage past book 7 (real coverage posture: Od. 1-7 only).
function fixtureManifest(): AudioManifest {
  return {
    status: 'draft',
    source: {
      creator: 'David Chamberlain',
      statement_url: 'https://hypotactic.com/my-reading-of-homer-work-in-progress/',
      license_note: 'CC BY 3.0 or 4.0 per item; see licenseurl per book',
    },
    works: {
      iliad: {
        '1': {
          item: 'Iliad1458611',
          licenseurl: 'http://creativecommons.org/licenses/by/4.0/',
          chunks: [
            { file: 'Iliad1_1-100.mp3', format: 'mp3', url: 'https://archive.org/download/Iliad1458611/Iliad1_1-100.mp3', lines: [1, 100] },
            { file: 'Iliad1_101-222.mp3', format: 'mp3', url: 'https://archive.org/download/Iliad1458611/Iliad1_101-222.mp3', lines: [101, 222] },
          ],
          gaps: [],
        },
        '6': {
          item: 'daybird66_gmail_136R',
          licenseurl: 'http://creativecommons.org/licenses/by/4.0/',
          chunks: [
            { file: 'Iliad6_1-36.mp3', format: 'mp3', url: 'https://archive.org/download/x/Iliad6_1-36.mp3', lines: [1, 36] },
            { file: 'Iliad6_R1-36.mp3', format: 'mp3', url: 'https://archive.org/download/x/Iliad6_R1-36.mp3', lines: [1, 36] },
            { file: 'Iliad6_37-65.mp3', format: 'mp3', url: 'https://archive.org/download/x/Iliad6_37-65.mp3', lines: [37, 65] },
            { file: 'Iliad6_R37-118.mp3', format: 'mp3', url: 'https://archive.org/download/x/Iliad6_R37-118.mp3', lines: [37, 118] },
            { file: 'Iliad6_66-118.mp3', format: 'mp3', url: 'https://archive.org/download/x/Iliad6_66-118.mp3', lines: [66, 118] },
          ],
          gaps: [],
        },
        '8': {
          item: 'Iliad8Fixture',
          licenseurl: 'http://creativecommons.org/licenses/by/3.0/',
          chunks: [
            { file: '1-561.mp3', format: 'mp3', url: 'https://archive.org/download/x/1-561.mp3', lines: [1, 561] },
            { file: '566-565.mp3', format: 'mp3', url: 'https://archive.org/download/x/566-end.mp3', lines: [566, 600] },
          ],
          gaps: [[562, 565]],
        },
      },
      odyssey: {
        '1': {
          item: 'Odyssey1Fixture',
          licenseurl: 'http://creativecommons.org/licenses/by/3.0/',
          chunks: [{ file: '1-100.mp3', format: 'mp3', url: 'https://archive.org/download/x/1-100.mp3', lines: [1, 100] }],
          gaps: [],
        },
      },
    },
  };
}

describe('isRevisionChunk', () => {
  it('flags an "_R<digit>" filename as a revision', () => {
    expect(isRevisionChunk('Iliad6_R37-118.mp3')).toBe(true);
    expect(isRevisionChunk('Iliad6_R1-36.mp3')).toBe(true);
  });
  it('does not flag an ordinary base-set filename', () => {
    expect(isRevisionChunk('Iliad6_37-65.mp3')).toBe(false);
    expect(isRevisionChunk('Iliad1_1-100.mp3')).toBe(false);
    expect(isRevisionChunk('1-561.mp3')).toBe(false);
  });
});

describe('bookAudio / hasAudio — honest coverage', () => {
  const manifest = fixtureManifest();
  it('finds a covered work/book', () => {
    expect(hasAudio(manifest, 'iliad', 1)).toBe(true);
  });
  it('reports no coverage for an Odyssey book past the manifest range (e.g. Od. 12)', () => {
    expect(hasAudio(manifest, 'odyssey', 12)).toBe(false);
    expect(bookAudio(manifest, 'odyssey', 12)).toBeUndefined();
  });
  it('reports no coverage for an unknown work', () => {
    expect(hasAudio(manifest, 'nonexistent', 1)).toBe(false);
  });
  it('reports no coverage for a null/undefined manifest (not-yet-loaded state)', () => {
    expect(hasAudio(null, 'iliad', 1)).toBe(false);
    expect(hasAudio(undefined, 'iliad', 1)).toBe(false);
  });
});

describe('lineInGap', () => {
  const entry = fixtureManifest().works.iliad['8'];
  it('flags a line inside the recorded gap', () => {
    expect(lineInGap(entry, 562)).toBe(true);
    expect(lineInGap(entry, 565)).toBe(true);
    expect(lineInGap(entry, 563)).toBe(true);
  });
  it('does not flag a line outside the gap', () => {
    expect(lineInGap(entry, 561)).toBe(false);
    expect(lineInGap(entry, 566)).toBe(false);
  });
  it('is false for an entry with no gaps', () => {
    expect(lineInGap(fixtureManifest().works.iliad['1'], 50)).toBe(false);
  });
});

describe('chunkForLine — line-honest lookup', () => {
  const iliad1 = fixtureManifest().works.iliad['1'];
  it('finds the chunk covering an ordinary line', () => {
    const c = chunkForLine(iliad1, 150);
    expect(c?.file).toBe('Iliad1_101-222.mp3');
  });
  it('finds the chunk at a range boundary (inclusive)', () => {
    expect(chunkForLine(iliad1, 100)?.file).toBe('Iliad1_1-100.mp3');
    expect(chunkForLine(iliad1, 101)?.file).toBe('Iliad1_101-222.mp3');
  });
  it('returns null beyond the book\'s recorded coverage', () => {
    expect(chunkForLine(iliad1, 9999)).toBeNull();
  });
  it('returns null for an undefined entry (uncovered work/book)', () => {
    expect(chunkForLine(undefined, 5)).toBeNull();
  });
  it('returns null for a line inside a recorded gap even though a nearby chunk exists', () => {
    const iliad8 = fixtureManifest().works.iliad['8'];
    expect(chunkForLine(iliad8, 563)).toBeNull();
    expect(chunkForLine(iliad8, 561)?.file).toBe('1-561.mp3');
  });

  describe('R-set (revision) preference — Iliad 6', () => {
    const iliad6 = fixtureManifest().works.iliad['6'];
    it('prefers the revision chunk when both a base and revision chunk cover the line', () => {
      // line 1 is covered by both Iliad6_1-36.mp3 (base) and Iliad6_R1-36.mp3 (revision)
      expect(chunkForLine(iliad6, 1)?.file).toBe('Iliad6_R1-36.mp3');
      expect(chunkForLine(iliad6, 36)?.file).toBe('Iliad6_R1-36.mp3');
    });
    it('prefers the revision even when the base set re-chunks the same span differently', () => {
      // line 50 falls in base Iliad6_37-65.mp3 AND revision Iliad6_R37-118.mp3
      expect(chunkForLine(iliad6, 50)?.file).toBe('Iliad6_R37-118.mp3');
      // line 90 falls only in base Iliad6_66-118.mp3, but the revision
      // Iliad6_R37-118.mp3 also covers it — revision still wins.
      expect(chunkForLine(iliad6, 90)?.file).toBe('Iliad6_R37-118.mp3');
    });
  });
});

describe('effectiveChunks — the play-affordance set', () => {
  it('returns the whole chunk list, sorted, for a book with no revisions', () => {
    const chunks = effectiveChunks(fixtureManifest().works.iliad['1']);
    expect(chunks.map((c) => c.file)).toEqual(['Iliad1_1-100.mp3', 'Iliad1_101-222.mp3']);
  });
  it('drops base chunks fully superseded by a revision, keeps the revisions', () => {
    const chunks = effectiveChunks(fixtureManifest().works.iliad['6']);
    const files = chunks.map((c) => c.file);
    expect(files).toContain('Iliad6_R1-36.mp3');
    expect(files).toContain('Iliad6_R37-118.mp3');
    // Iliad6_1-36.mp3, Iliad6_37-65.mp3, Iliad6_66-118.mp3 are each fully
    // covered by a revision chunk and must not surface their own affordance.
    expect(files).not.toContain('Iliad6_1-36.mp3');
    expect(files).not.toContain('Iliad6_37-65.mp3');
    expect(files).not.toContain('Iliad6_66-118.mp3');
  });
  it('is sorted by start line', () => {
    const chunks = effectiveChunks(fixtureManifest().works.iliad['8']);
    expect(chunks.map((c) => c.lines[0])).toEqual([1, 566]);
  });
  it('returns an empty array for an undefined entry', () => {
    expect(effectiveChunks(undefined)).toEqual([]);
  });
});

describe('licenseLabel', () => {
  it('labels a 4.0 license', () => {
    expect(licenseLabel('http://creativecommons.org/licenses/by/4.0/')).toBe('CC BY 4.0');
  });
  it('labels a 3.0 license', () => {
    expect(licenseLabel('http://creativecommons.org/licenses/by/3.0/')).toBe('CC BY 3.0');
  });
  it('falls back honestly on an unrecognized URL shape', () => {
    expect(licenseLabel('https://example.com/not-a-license')).toBe('CC license');
  });
});

describe('chunkAriaLabel', () => {
  it('formats an accessible play-button label', () => {
    const chunk = fixtureManifest().works.iliad['1'].chunks[0];
    expect(chunkAriaLabel(chunk, 'David Chamberlain')).toBe(
      'Play lines 1–100, read by David Chamberlain',
    );
  });
});

describe('itemPageUrl', () => {
  it('builds the archive.org item page URL', () => {
    expect(itemPageUrl('Iliad1458611')).toBe('https://archive.org/details/Iliad1458611');
  });
});
