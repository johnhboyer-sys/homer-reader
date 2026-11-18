import type { CharacterEntry } from './data';
import type { SpeakerFilter } from './search';
import type { SpeechFilter } from './search-url';

export function speakerLinkToSpeech(
  speaker: SpeakerFilter | null,
  speech: SpeechFilter | null,
  cast: ReadonlyMap<string, CharacterEntry>,
): SpeechFilter | null {
  if (speech) return speech;
  if (speaker?.mode !== 'only' || speaker.names.length !== 1) return null;
  const name = speaker.names[0].toLowerCase();
  const matches = [...cast.values()].filter(character =>
    character.id.toLowerCase() === name || character.name.toLowerCase() === name);
  return matches.length === 1 ? { kind: 'speaker', id: matches[0].id } : null;
}
