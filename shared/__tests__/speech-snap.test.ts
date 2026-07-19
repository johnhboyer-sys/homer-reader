import { describe, expect, it } from 'vitest';
import { snapTicksToSpeechStarts } from '../lib/speech-snap';

describe('snapTicksToSpeechStarts', () => {
  it('Il. 1.25/26 real-data case: snaps the tick anchored at 25 to the Agamemnon→Chryses speech start at 26', () => {
    // Real Murray tick anchors around Il. 1 (5-line milestones) and real
    // DICES speech starts for book 1 (iliad-1 at 17, iliad-2 at 26 — see
    // apparatus/speeches/iliad.json).
    const tickLines = [15, 20, 25, 30];
    const speechStarts = [17, 26];
    expect(snapTicksToSpeechStarts(tickLines, speechStarts)).toEqual([17, 20, 26, 30]);
  });

  it('a book with no speeches leaves every tick unchanged', () => {
    const tickLines = [1, 5, 10, 15, 20, 25, 30];
    expect(snapTicksToSpeechStarts(tickLines, [])).toEqual(tickLines);
  });

  it('a tick exactly AT a speech start is unchanged (not forward)', () => {
    const tickLines = [10, 15, 20];
    expect(snapTicksToSpeechStarts(tickLines, [15])).toEqual([10, 15, 20]);
  });

  it('window-of-2 edge: s = n+2 snaps, s = n+3 does not', () => {
    expect(snapTicksToSpeechStarts([15], [17])).toEqual([17]);
    expect(snapTicksToSpeechStarts([15], [18])).toEqual([15]);
  });

  it('nested speech: snaps to whichever start is in-window, regardless of nesting level (level-agnostic — the caller resolves which speeches to include)', () => {
    // A level-0 frame speech starting exactly at the tick (no snap there) and
    // a nested level-1 speech opening 2 lines later, inside the frame.
    const tickLines = [100, 103, 110];
    const speechStarts = [100, 105]; // frame start (100), nested start (105)
    expect(snapTicksToSpeechStarts(tickLines, speechStarts)).toEqual([100, 105, 110]);
  });

  it('never snaps to or past the NEXT tick\'s own anchor line (no empty/inverted group)', () => {
    // tick0(10)'s window reaches 12, but tick1 already anchors at 11 — snapping
    // tick0 to 12 would leave tick1's group empty/inverted, so it's blocked.
    // tick1(11)'s own window also reaches 12, and its next tick (20) is far
    // enough away, so ITS snap is allowed.
    const tickLines = [10, 11, 20];
    const speechStarts = [12];
    expect(snapTicksToSpeechStarts(tickLines, speechStarts)).toEqual([10, 12, 20]);
  });

  it('multiple speech starts in the window snap to the earliest', () => {
    const tickLines = [40];
    const speechStarts = [42, 41];
    expect(snapTicksToSpeechStarts(tickLines, speechStarts)).toEqual([41]);
  });

  it('never snaps backward past a start already at or before the tick', () => {
    const tickLines = [50];
    const speechStarts = [48, 49, 50];
    expect(snapTicksToSpeechStarts(tickLines, speechStarts)).toEqual([50]);
  });
});
