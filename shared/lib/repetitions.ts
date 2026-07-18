import { greekFold } from './search';
import type { Repetition } from './data';

// Search the surface form without making readers reproduce accents, breathing
// marks, or case. `crossEpicOnly` is intentionally derived from refs rather
// than emitted as a second, denormalized data field.
export function isCrossEpic(repetition: Repetition): boolean {
  return repetition.crossEpic ?? new Set(repetition.refs.map(ref => ref.work)).size > 1;
}

export function filterRepetitions(
  repetitions: Repetition[],
  query: string,
  crossEpicOnly: boolean,
): Repetition[] {
  const foldedQuery = greekFold(query.trim());
  return repetitions.filter(repetition =>
    (!foldedQuery || greekFold(repetition.text).includes(foldedQuery)) &&
    (!crossEpicOnly || isCrossEpic(repetition)),
  );
}
