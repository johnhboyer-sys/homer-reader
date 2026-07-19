// FIX 1 (John's directive, phone review 2026-07-18): pure boundary-snapping
// for the mobile "Both" view's alignment groups (see Reader.svelte's
// alignGroups, which is also reused by Reading Mode's scene chunker,
// readingChunks). Murray's English milestone ticks occasionally drift 1-2
// lines ahead of where their content actually starts translating — usually
// invisible (prose bleeding a half-line past an arbitrary 5-line milestone is
// unremarkable) but glaring right at a speech opening: the tick anchors its
// Greek run one or two lines INTO the speech, so the speech's own opening
// line renders in the group AFTER the "SPEAKER → ADDRESSEE" label while its
// English translation already sits in the group BEFORE it. Concrete case:
// Il. 1.25/26 — the tick anchored at Greek 25 actually leads English
// translating line 26 ("Let me not find you, old man…"); line 25's own
// English ("…and laid upon him a stern command:") is the TRAILING text of
// the PREVIOUS (line-20-anchored) group. See speech-snap.test.ts.
//
// THE RULE (John's design, implement exactly): for a tick anchored at Greek
// line n, if a speech starts at line s with n < s <= n+2, snap this tick's
// group to start at s instead of n — Greek lines n..s-1 join the PREVIOUS
// group; the new group opens exactly at the speech's own first line, pairing
// speech-Greek with speech-English. Forward-only (a tick already at or past a
// speech start is untouched); capped at 2 lines; never snapped to or past
// the NEXT tick's own anchor line (would leave the next group empty/inverted).
// Multiple speech starts inside the window: snap to the earliest.
//
// Level-agnostic by design: the caller passes every speech's opening line
// (all nesting levels — see Reader.svelte's `bookSpeeches`), not just the
// high-confidence ones that render as a rail. A tick may snap to a NESTED
// speech's opening exactly like any level-0 span start.
export function snapTicksToSpeechStarts(tickLines: number[], speechStarts: number[]): number[] {
  const starts = [...new Set(speechStarts)].sort((a, b) => a - b);
  return tickLines.map((n, i) => {
    const nextN = tickLines[i + 1];
    for (const s of starts) {
      if (s <= n) continue;                          // not forward
      if (s > n + 2) break;                           // outside the window (starts is sorted)
      if (nextN !== undefined && s >= nextN) break;    // would cross/empty the next group
      return s;                                        // earliest valid snap wins
    }
    return n;
  });
}
