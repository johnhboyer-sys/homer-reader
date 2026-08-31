<script lang="ts">
  import { tick } from 'svelte';
  import {
    lookupWord, fetchLemmata, fetchLsjHeads, fetchCunliffeShard, cunliffeShard,
    type Analysis, type CunliffeEntry, type LemmaRef, type LsjHead,
  } from '../lib/data';
  import { betaToGreek } from '../lib/betacode';
  import { workPath } from '../lib/works';
  import { formatLocValue } from '../lib/citation';

  // The shared BODY of the word lookup, rendered identically inside the docked
  // desktop lexicon rail AND the anchored mobile popup (WordPopup). It owns the
  // single analyses-fetch and the dictionary presentation.
  //
  // One card per DICTIONARY ENTRY, each carrying its own LSJ · Cunliffe tabs;
  // the entry opens under the card tapped (John, 2026-08-30). Nothing is
  // fetched for a reader who only wanted the parse.
  export let work: string = 'EN';
  export let token: { t: string; k: string };
  // Whether this body is rendered inside the DESKTOP docked lexicon rail (true)
  // vs the anchored mobile popup (false). Both now show the same thing: the tab
  // row is surfaced on every card (punch-list #12's intent), closed until asked.
  export let docked: boolean = false;

  let panelEl: HTMLDivElement;
  let analyses: Analysis[] = [];
  let loading = true;
  let error = '';
  let lookupSeq = 0;

  // Re-fetch whenever the clicked token (or work) changes. A one-shot top-level
  // lookupWord only ran on mount, so switching Greek words while the docked
  // rail/popup stayed open updated the header surface form but left parse +
  // dictionary stuck on the first word (sitewide; reported Safari + Chrome).
  $: {
    const w = work;
    const k = token.k;
    const seq = ++lookupSeq;
    loading = true;
    error = '';
    analyses = [];
    // Everything the previous word opened belongs to the previous word.
    open = {};
    cunliffeText = {};
    entryError = {};
    // entries:false — no dictionary shard is fetched for a lookup any more.
    // The cards come from the analyses plus the heads manifest; an entry's text
    // is fetched only when its tab is tapped.
    lookupWord(w, k, { entries: false })
      .then(r => { if (seq === lookupSeq) analyses = r.analyses; })
      .catch(e => { if (seq === lookupSeq) error = String(e); })
      .finally(() => { if (seq === lookupSeq) loading = false; });
  }

  const base = import.meta.env.BASE_URL.replace(/\/$/, '');

  // The lemma-page manifest (loaded once, cached): lets each card offer a "see
  // all N occurrences" link into /lemma/<slug>, but only for lemmata that
  // actually have a page. Absent manifest = no links, panel unchanged.
  let lemmata: Record<string, LemmaRef> = {};
  fetchLemmata().then(m => { lemmata = m; }).catch(() => {});

  // The headword manifest: head, LSJ's own homograph letter, and LSJ's one-line
  // sense, for every key an analysis names. Absent manifest = the betaToGreek
  // fallback below, which is why nothing here throws.
  let heads: Record<string, LsjHead> = {};
  fetchLsjHeads().then(m => { heads = m; }).catch(() => {});

  // ── Cards are keyed by DICTIONARY ENTRY, not by Morpheus lemma ────────────
  // An analysis can name several LSJ entries (2,335 across this corpus: ὅς's
  // single analysis points at both o(/s1 and o(/s2). Keying on the entry means
  // its parses join each of those entries' cards, no card ever names more than
  // one entry, and there is no unresolved parent card that opens nothing.
  const DIALECTS = ['attic', 'epic', 'doric', 'ionic', 'aeolic', 'homeric'];

  // HOMER IS EPIC, and prints every dialect label it is given (John,
  // 2026-08-30). Aristotle suppresses "attic" because LSJ's baseline dialect
  // and its corpus are the same, so the label says nothing. That equivalence
  // does not hold here: LSJ still writes from an Attic baseline whatever text
  // you are reading, so "epic" and "ionic" are the informative labels — the
  // ones a Homer reader opens the entry to see. Suppressing on Attic's
  // presence would additionally have hidden 7,443 analyses here, 3,303 of them
  // "attic epic ionic". 48% of analyses carry a label; the rest carry none and
  // show no chip.
  function splitParse(parse: string): { text: string; dialect: string } {
    const m = /\(([^)]*)\)\s*$/.exec(parse ?? '');
    if (!m) return { text: (parse ?? '').trim(), dialect: '' };
    // The trailing parenthesis is not always dialect — "indeclform (particle)",
    // "(conj)", "(prep)". Only the dialect words become a chip.
    const named = m[1].split(/\s+/).filter(w => DIALECTS.includes(w));
    if (named.length === 0) return { text: (parse ?? '').trim(), dialect: '' };
    return { text: parse.slice(0, m.index).trim(), dialect: named.join(' ') };
  }

  interface EntryCard {
    id: string;
    lsjKey: string;          // '' when this analysis names no LSJ entry
    head: string;
    hom: string;             // LSJ's own homograph letter, '' when unmarked
    gloss: string;
    // Whether `gloss` came from an analysis naming this entry ALONE. An
    // analysis can fan out across several entries carrying the gloss of only
    // one of them, and first-wins then mislabels the rest.
    glossExact: boolean;
    /** Settled after grouping — see the precedence note below. */
    definition: string;
    rows: { text: string; dialect: string }[];
    cunliffeKeys: string[];
    ref: LemmaRef | null;
  }

  $: cards = (() => {
    const out: EntryCard[] = [];
    const byId = new Map<string, EntryCard>();
    for (const a of analyses) {
      const keys = a.lsj && a.lsj.length ? a.lsj : [''];
      // An analysis naming exactly one entry describes THAT entry; one naming
      // several is unresolved and its gloss belongs to none in particular.
      const exact = keys.length === 1;
      for (const k of keys) {
        const id = k || `lemma:${a.lemma}`;
        let card = byId.get(id);
        if (!card) {
          const meta = k ? heads[k] : undefined;
          card = {
            id,
            lsjKey: k,
            head: meta?.head || betaToGreek(a.lemma),
            hom: meta?.hom ?? '',
            gloss: a.gloss,
            glossExact: exact,
            definition: '',
            rows: [],
            cunliffeKeys: [],
            ref: (k && lemmata[k]) || null,
          };
          byId.set(id, card);
          out.push(card);
        }
        // Precedence, in order:
        //  - a non-empty exact gloss always wins, even over an earlier exact:
        //    two analyses of one lemma where the first is glossed "" must not
        //    leave the card blank.
        //  - an empty exact still marks the card exact, and CLEARS a gloss that
        //    came from a fan-out, because a fan-out gloss may be a sibling
        //    entry's meaning and blank is honest where borrowed is not.
        //  - a fan-out gloss only ever fills a hole, and never overwrites.
        if (exact) {
          if (a.gloss) card.gloss = a.gloss;
          else if (!card.glossExact) card.gloss = '';
          card.glossExact = true;
        } else if (!card.glossExact && !card.gloss && a.gloss) {
          card.gloss = a.gloss;
        }
        const row = splitParse(a.parse);
        // Drop rows this card already carries: an analysis naming several
        // entries repeats its parse into each of them.
        if (!card.rows.some(r => r.text === row.text && r.dialect === row.dialect)) {
          card.rows.push(row);
        }
        // Cunliffe keys ride on the ANALYSIS, not on the LSJ entry, so a
        // fan-out hands the same Cunliffe entry to each of its cards. That is
        // not a fudge: Cunliffe simply does not make LSJ's homonym split — ὅς
        // is one Cunliffe entry against LSJ's o(/s1 and o(/s2 — so one entry
        // genuinely covers both cards.
        for (const c of a.cunliffe ?? []) {
          if (!card.cunliffeKeys.includes(c)) card.cunliffeKeys.push(c);
        }
      }
    }
    // Each card's definition, settled here rather than in the template so it is
    // computed once per card and reads in one place. LSJ's own one-line sense
    // outranks a gloss fanned out across several entries — "swim" stamped onto
    // the entry for "spin" is a card lying about what it is about to open — but
    // not an exact gloss, which is already about this entry and is usually the
    // crisper of the two.
    for (const c of out) {
      c.definition = (c.glossExact && c.gloss)
        || (c.lsjKey ? heads[c.lsjKey]?.short ?? '' : '')
        || c.gloss || '';
    }
    return out;
  })();

  // ── the entry, opened under the card that asked for it ────────────────────
  // Served by grammata (grammar-site's deploy), not rendered here: one grammata
  // deploy updates every reader site. Architecture decided 2026-08-29. Do not
  // vendor, proxy, pin or cache-bust this URL — its deploys ARE the update
  // mechanism — and do not style anything inside the container: the widget's
  // CSS is generated from grammata's design system and changes with it.
  const GRAMMATA_LOOKUP = 'https://grammata.pages.dev/t8/lookup.js';
  type LookupFn = (
    word: string,
    el: HTMLElement,
    opts?: { lang?: string; key?: string },
  ) => Promise<void>;
  let _grammata: Promise<LookupFn> | null = null;
  function grammata(): Promise<LookupFn> {
    // @vite-ignore is REQUIRED: Vite cannot resolve an https: import at build
    // time and the build fails without it.
    if (!_grammata) {
      const p = import(/* @vite-ignore */ GRAMMATA_LOOKUP).then(m => m.lookup as LookupFn);
      p.catch(() => { if (_grammata === p) _grammata = null; });
      _grammata = p;
    }
    return _grammata;
  }

  // Which lexicon each card has open, by card id. Absent = closed, and closed
  // is the default everywhere: nothing is fetched for a reader who wanted only
  // the parse.
  let open: Record<string, 'lsj' | 'cunliffe'> = {};
  let cunliffeText: Record<string, CunliffeEntry[]> = {};
  let entryError: Record<string, string> = {};

  async function toggle(card: EntryCard, i: number, which: 'lsj' | 'cunliffe') {
    if (open[card.id] === which) {
      const { [card.id]: _drop, ...rest } = open;
      open = rest;
      return;
    }
    open = { ...open, [card.id]: which };
    entryError = { ...entryError, [card.id]: '' };
    await tick();   // the mount point only exists once the panel has rendered
    if (which === 'lsj') await openLsj(card, i);
    else await openCunliffe(card);
  }

  async function openLsj(card: EntryCard, i: number) {
    const el = panelEl?.querySelector<HTMLElement>(`#lex-panel-${i} .grammata-mount`);
    if (!el) return;
    try {
      const lookup = await grammata();
      // PASS THE KEY, NEVER THE SURFACE FORM. A surface form makes the widget
      // re-analyse from scratch and discard the disambiguation this reader has
      // already done — εἰσὶ comes back as ἵημι, εἰμί and εἶμι with ἵημι first,
      // so the entry under a card reading "εἰμί" would be a different verb.
      // Their pack keys are Perseus betacode, the same key space as ours, so
      // the key passes verbatim, homograph digits included.
      // logeion:false — this card's own tab row already carries a Logeion link
      // for this headword, and grammata's entry header prints one too, so the
      // reader saw the same link twice a few lines apart. Their option, shipped
      // in grammar-site#32 at John's request; it defaults on, so aristotle
      // keeps its link untouched.
      const opts = { lang: 'grc', logeion: false };
      if (card.lsjKey) await lookup('', el, { ...opts, key: card.lsjKey });
      else await lookup(card.head, el, opts);
    } catch {
      // The widget renders its own loading, not-found and network-failure
      // states; this catch is only for the module itself failing to load.
      entryError = { ...entryError, [card.id]: 'The dictionary could not be loaded.' };
    }
  }

  async function openCunliffe(card: EntryCard) {
    if (cunliffeText[card.id]) return;
    try {
      const found: CunliffeEntry[] = [];
      for (const key of card.cunliffeKeys) {
        const shard = await fetchCunliffeShard(cunliffeShard(key));
        if (shard[key]) found.push(shard[key]);
      }
      cunliffeText = { ...cunliffeText, [card.id]: found };
    } catch {
      entryError = { ...entryError, [card.id]: 'Cunliffe could not be loaded.' };
    }
  }

  // A Cunliffe entry's HTML embeds internal citation links as
  // <a class="cunliffe-cite" data-work data-book data-line> markers rather than
  // baked hrefs (BASE_URL is only known client-side). Resolve the destination
  // here, in-place navigation (same tab), the way BekkerJump/CommandPalette do.
  function onCunliffeClick(e: MouseEvent) {
    const target = (e.target as HTMLElement).closest('a.cunliffe-cite') as HTMLElement | null;
    if (!target) return;
    e.preventDefault();
    const w = target.dataset.work;
    const book = Number(target.dataset.book);
    const line = Number(target.dataset.line);
    if (!w || !book || !line) return;
    window.location.href = `${base}${workPath(w, book)}?loc=${formatLocValue(w, String(book), line)}`;
  }

  // Logeion looks up by headword, not inflected surface form — and now each
  // card HAS its own headword, so the link is per card rather than one link
  // built from the first analysis for the whole panel.
  const logeionHref = (c: EntryCard) =>
    `https://logeion.uchicago.edu/${encodeURIComponent(c.head)}`;
</script>

<div class="lexicon-panel" class:docked bind:this={panelEl}>
  {#if loading}
    <div class="popup-loading">Looking up…</div>
  {:else if error}
    <div class="popup-loading">Error: {error}</div>
  {:else if cards.length === 0}
    <div class="popup-loading">No analysis found for this form.</div>
  {:else}
    {#each cards as c, i}
      <div class="analysis-card">
        <div class="lemma" lang="grc">{c.head}{#if c.hom}<sup class="homonym">({c.hom})</sup>{/if}</div>
        {#if c.definition}<div class="gloss">{c.definition}</div>{/if}
        {#each c.rows as row}
          <div class="parse">
            {row.text}{#if row.dialect}<span class="parse-dialect">{row.dialect}</span>{/if}
          </div>
        {/each}
        {#if c.ref}
          <a class="lemma-link" href={`${base}/lemma/${c.ref.slug}/`}>
            Appears {c.ref.count.toLocaleString()}× across Homer
            <span class="lemma-link-arr" aria-hidden="true">→</span>
          </a>
        {/if}

        <div class="card-lex">
          <button
            type="button"
            class="lex-tab"
            class:active={open[c.id] === 'lsj'}
            aria-expanded={open[c.id] === 'lsj'}
            on:click={() => toggle(c, i, 'lsj')}
          >LSJ</button>
          {#if c.cunliffeKeys.length}
            <button
              type="button"
              class="lex-tab"
              class:active={open[c.id] === 'cunliffe'}
              aria-expanded={open[c.id] === 'cunliffe'}
              on:click={() => toggle(c, i, 'cunliffe')}
            >Cunliffe</button>
          {/if}
          <!-- A real external navigation, not a panel switch: the ONE control
               here that opens a new tab. -->
          <a class="lex-tab lex-tab-link" href={logeionHref(c)} target="_blank" rel="noopener"
            >Logeion <span aria-hidden="true">↗</span></a>
        </div>

        {#if open[c.id]}
          <div class="card-entry" id={`lex-panel-${i}`}>
            {#if entryError[c.id]}
              <div class="popup-loading">{entryError[c.id]}</div>
            {:else if open[c.id] === 'lsj'}
              <!-- grammata fills this; it renders its own loading, not-found
                   and failure states, so there is nothing to add here. -->
              <div class="grammata-mount"></div>
            {:else}
              <div class="cunliffe-body" on:click={onCunliffeClick} on:keydown={() => {}}>
                {#if cunliffeText[c.id] === undefined}
                  <div class="popup-loading">Looking up…</div>
                {:else if cunliffeText[c.id].length === 0}
                  <div class="popup-loading">Not in Cunliffe.</div>
                {:else}
                  {#each cunliffeText[c.id] as entry}
                    <div class="cunliffe-entry">
                      <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                      {@html entry.html}
                    </div>
                  {/each}
                {/if}
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {/each}
  {/if}
</div>
