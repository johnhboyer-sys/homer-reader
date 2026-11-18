import { describe, expect, it } from 'vitest';
import { speakerLinkToSpeech } from '../lib/speaker-link-to-speech';
import type { SpeechFilter } from '../lib/search-url';

const cast = new Map([
  ['achilles', { id: 'achilles', name: 'Achilles' }],
  ['athena', { id: 'athena', name: 'Athena' }],
  ['ajax', { id: 'ajax', name: 'Ajax the Greater' }],
]);

describe('speakerLinkToSpeech', () => {
  it.each(['Achilles', 'achilles', 'ACHILLES'])('maps only + %s to Achilles', name => {
    expect(speakerLinkToSpeech({ mode: 'only', names: [name] }, null, cast))
      .toEqual({ kind: 'speaker', id: 'achilles' });
  });

  it.each(['AJAX', 'ajax THE greater'])('matches a distinct cast id or name case-insensitively: %s', name => {
    expect(speakerLinkToSpeech({ mode: 'only', names: [name] }, null, cast))
      .toEqual({ kind: 'speaker', id: 'ajax' });
  });

  it('does not map except + Achilles', () => {
    expect(speakerLinkToSpeech({ mode: 'except', names: ['Achilles'] }, null, cast)).toBeNull();
  });
  it('does not map only + two names', () => {
    expect(speakerLinkToSpeech({ mode: 'only', names: ['Achilles', 'Athena'] }, null, cast)).toBeNull();
  });
  it('does not map only + an unknown name', () => {
    expect(speakerLinkToSpeech({ mode: 'only', names: ['Nobody'] }, null, cast)).toBeNull();
  });
  it('does not map an empty cast', () => {
    expect(speakerLinkToSpeech({ mode: 'only', names: ['Achilles'] }, null, new Map())).toBeNull();
  });
  it.each<SpeechFilter>([{ kind: 'speeches' }, { kind: 'speaker', id: 'athena' }])('keeps existing speech filter %j', speech => {
    expect(speakerLinkToSpeech({ mode: 'only', names: ['Achilles'] }, speech, cast)).toBe(speech);
  });
  it('leaves an absent speaker filter alone', () => {
    expect(speakerLinkToSpeech(null, null, cast)).toBeNull();
  });
});
