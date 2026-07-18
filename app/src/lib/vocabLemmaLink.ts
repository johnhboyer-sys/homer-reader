// Joins a /vocabulary/ page's raw vocab.json lemma to a /lemma/<slug>/ page.
//
// vocab.json's `lemma` field is `analyses[k][0].lemma` (see
// pipeline/homer_pipeline/apparatus_vocab.py) -- the Morpheus/analyses Beta
// Code lemma, straight off the token. public/data/lemmata/_index.json's
// `key`, by contrast, is build-lemmata.mjs's concordance bucket key:
// `(analyses[k][0].lsj && analyses[k][0].lsj[0]) || analyses[k][0].lemma`
// (see app/scripts/build-lemmata.mjs "Accumulate the concordance"). The two
// diverge whenever a lemma has an LSJ headword: the LSJ key can carry vowel-
// quantity marks the raw lemma doesn't (`basileu/s` -> `ba^si^leu/s`) and/or
// a homograph digit suffix the raw lemma doesn't share (`ce/nos1` -> the
// index key is `ce/nos`; `a(/ls` -> the index key is `a(/ls1`). A raw
// string-equality join therefore misses every lemma with an LSJ headword
// that differs from its morphological lemma -- most of the "inert span"
// defect found in review.
//
// The fix: rebuild the SAME key build-lemmata.mjs computes, from the same
// source (this work's analyses.json), and join through that instead of the
// raw lemma string.

interface AnalysisEntry {
  lemma?: string;
  lsj?: string[];
}

/**
 * Scans a work's analyses.json (the same file build-lemmata.mjs reads) and
 * returns raw-lemma -> concordance-bucket-key, mirroring build-lemmata.mjs's
 * `key = (a0.lsj && a0.lsj[0]) || a0.lemma` exactly.
 *
 * Across the live corpus every raw lemma resolves to exactly one bucket key
 * (checked: 0 counterexamples in either work as of 2026-07-18), but this is
 * verified rather than assumed here: a lemma that resolves to more than one
 * distinct key in this work's analyses is dropped from the map entirely, so
 * callers fall back to a plain lookup for it (honesty over a guessed link).
 */
export function buildLemmaKeyMap(analyses: Record<string, AnalysisEntry[]>): Map<string, string> {
  const candidates = new Map<string, Set<string>>();
  for (const entries of Object.values(analyses)) {
    const a0 = entries?.[0];
    const lemma = a0?.lemma;
    if (!lemma) continue;
    const key = (a0.lsj && a0.lsj[0]) || lemma;
    let keys = candidates.get(lemma);
    if (!keys) { keys = new Set(); candidates.set(lemma, keys); }
    keys.add(key);
  }
  const out = new Map<string, string>();
  for (const [lemma, keys] of candidates) {
    if (keys.size === 1) out.set(lemma, [...keys][0]);
  }
  return out;
}

/**
 * Resolves a vocab.json lemma to its /lemma/<slug>/ page, joining through
 * the bucket-key map above. Falls back to a raw match (covers lemmata that
 * are already their own bucket key, and any wired-through edge case) then
 * gives up honestly -- undefined for a lemma with no page (below
 * build-lemmata.mjs's MIN_COUNT) or one left ambiguous by
 * buildLemmaKeyMap.
 */
export function resolveLemmaSlug(
  lemma: string,
  lemmaKeyMap: Map<string, string>,
  lemmaSlugs: Map<string, string>,
): string | undefined {
  const key = lemmaKeyMap.get(lemma) ?? lemma;
  return lemmaSlugs.get(key) ?? lemmaSlugs.get(lemma);
}
