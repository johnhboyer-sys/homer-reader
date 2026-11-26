// The Greek fold: Unicode Greek or Beta Code to the base Beta Code letters the
// search indexes are keyed on. Its own module so the reader and the Go-to
// palette can fold a word without loading the search engine (search.ts
// re-exports both names, so its importers are unchanged).
export const GREEK_BETA: Record<string, string> = {
  α:'a',β:'b',γ:'g',δ:'d',ε:'e',ζ:'z',η:'h',θ:'q',ι:'i',κ:'k',
  λ:'l',μ:'m',ν:'n',ξ:'c',ο:'o',π:'p',ρ:'r',σ:'s',ς:'s',τ:'t',
  υ:'u',φ:'f',χ:'x',ψ:'y',ω:'w',ϝ:'v',
};

export function greekFold(input: string): string {
  const out: string[] = [];
  for (const ch of input.normalize('NFD')) {
    const lower = ch.toLowerCase();
    const b = GREEK_BETA[lower];
    if (b) out.push(b);                          // Unicode Greek → fold letter
    else if (lower >= 'a' && lower <= 'z') out.push(lower); // Beta Code Latin input
    // Elision: the index keys δ' as d'. The page prints the mark as U+2019
    // (δ’), so a word copied from the text must fold to the same key as one
    // typed with a straight apostrophe. stage6 keys U+1FBD (᾽) the same way.
    else if (ch === "'" || ch === '\u2019' || ch === '\u02bc' || ch === '\u1fbd') out.push("'");
    // skip combining marks, punctuation, Beta Code diacritics ) ( / \ = | +,
    // asterisk (handled by caller), and sigma-variant digits
  }
  return out.join('');
}
