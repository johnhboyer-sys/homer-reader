# Grok session fixes — 2026-07-20

Handoff for Claude / next orchestrator. Work done by Grok (Grok Build / xAI) while Claude usage was on cooldown. John (johnhboyer-sys) reviewed on local dev, merged PRs, and redeployed.

**Live site:** https://johnhboyer-sys.github.io/homer-reader/  
**Source branch with merges:** `claude/build` (tip includes merge commits for PRs #1–#3)  
**Deploy commit (`gh-pages`):** `a00dd596` — *Deploy: lexicon switch, sticky cartouche, Reading Mode scene paging*  
**Working style:** one coherent unit per PR into `claude/build`; no merge to `main` / deploy without John’s go-ahead (this session: John merged PRs + deployed himself).

---

## Summary table

| PR | Title | Branch | Status | Files |
|---|---|---|---|---|
| [#1](https://github.com/johnhboyer-sys/homer-reader/pull/1) | Lexicon re-fetch on token switch | `fix/lexicon-token-switch` | **MERGED** → `claude/build` (`325b7cd8`) | `shared/components/LexiconPanel.svelte`, `shared/__tests__/word-popup.test.ts` |
| [#2](https://github.com/johnhboyer-sys/homer-reader/pull/2) | Sticky controls cover band vs cartouche | `fix/sticky-controls-cover-band` | **MERGED** → `claude/build` (`145a8a7c`) | `shared/styles/global.css` |
| [#3](https://github.com/johnhboyer-sys/homer-reader/pull/3) | Reading Mode scene paging ownership | `fix/reading-mode-hollow-guardrail` | **MERGED** → `claude/build` (`4179377d`) | `shared/lib/scene-paging.ts`, `shared/__tests__/scene-paging.test.ts` |

Fix commits (pre-merge):

- `73c23e46` — lexicon reactive re-fetch  
- `ca37d89b` — sticky cover band `3rem` → `4px`  
- `f1f9d765` — Reading Mode `naturalEndOffset` + hollow guardrail + tests  

---

## PR #1 — Lexicon: second word does not update

### Symptom (user report + friend on X)

With the parse/define panel open (docked desktop rail or popup), clicking a **second** Greek word updated only the **surface form in the header**. Lemma, gloss, parse, and dictionary stayed on the first word. Reproduced Safari + Chrome, Iliad + Odyssey (sitewide). User had to close the panel and reopen.

### Root cause

`LexiconPanel.svelte` ran `lookupWord(work, token.k)` as a **one-shot top-level statement** (runs once on component create).  
`Reader.svelte` keeps `{#if popup}` mounted while switching tokens (`popup = { token, … }`), so `WordPopup` / `LexiconPanel` **do not remount**. Header bound to `token.t` (reactive); body state (`analyses` / `lsj` / `cunliffe`) filled only once.

### Fix

In `shared/components/LexiconPanel.svelte`:

- Reactive `$:` block on `work` + `token.k` re-runs `lookupWord`.
- Clear analyses/lsj/cunliffe while loading so stale gloss never lingers.
- `lookupSeq` guard: ignore out-of-order responses when clicking quickly.

### Tests

`shared/__tests__/word-popup.test.ts` — “token switch while open”: open word A, `rerender` with token B (Svelte 5; no `$set`), assert `lookupWord` called twice and new gloss appears.

### Codex review

**ship** — no issues.

---

## PR #2 — Sticky chrome covers book-plate cartouche

### Symptom

Large empty / “blocked” band between cartouche (argument, cast, day) and the sticky translation / Reading Mode / Greek·Both·English strip. Looked like a layer over the in-page header.

### Root cause

`.reader-controls::before` in `shared/styles/global.css`: opaque `page-bg` band **above** the sticky strip, meant to plug Safari sub-pixel/rubber-band gaps between sticky header and sticky controls. Height was **`3rem` (48px)** — far larger than a hairline gap — painting over the bottom of `.book-plate` (cast/day + bottom hairline).

### Fix

Height `3rem` → **`4px`**, with comment explaining why it must stay tiny. Still plugs the gap; does not erase the cartouche.

### Codex review

**ship** — no issues.

---

## PR #3 — Reading Mode scene paging (intermediate)

### Symptom

Reading Mode, **Iliad 1 scene 3** (apparatus lines **33–42**, “Chryses withdraws… prays”):

- Header correct (scene 3 · lines 33–42).  
- Body was **one leftover sentence**: “Down from the peaks of Olympus…” (start of scene 4 / Apollo descent).  
- The prayer English that belongs on scene 3 sat at the **end of scene 2**.

Scholar view / scene rail were fine — **Reading Mode only**.

### Root cause

`sentenceSnapScenePages` (`shared/lib/scene-paging.ts`):

1. Natural end of a scene = end of **last overlapping** Murray ~5-line tick.  
2. Scene 2 ends Greek **32**; tick **30–34** straddles into scene 3.  
3. Free `firstSentenceEndAtOrAfter` then ran to the next real period — through the whole prayer to “…Phoebus Apollo heard him.”  
4. Scene 3’s page started after that → only the Olympus sentence.

Same class of tension: **English sentence integrity** vs **Greek apparatus scene ranges**. Murray ticks are not line-aligned.

### Fix (intermediate — not a full pager overhaul)

John: ship intermediate fix; leave full overhaul for Claude later if needed.

1. **`naturalEndOffset` / owned-share cut**  
   For a straddling last tick, map `scene.endLine` into the tick (midpoint of last owned Greek line), prefer last sentence end in that owned share. Soft preference for a sentence end still inside the straddling tick; if none, **overflow past the tick** rather than hard-cut mid-sentence.

2. **Never end a page mid-sentence** (John + Codex).  
   Cap must not force `end = tick boundary` mid-phrase.

3. **Hollow-page safety net** (`isHollowScenePage`, default ON)  
   Plain English: if a scene card would be empty or almost empty (previous card ate its prose), fill from coarser backup (`chunksForScene` + `mergeSceneFlowChunks`). Mild **duplication** with previous page possible; better than a blank/wrong scrap. Healthy pages untouched. After ownership fix, corpus hollow count ≈ 0; net is last-resort.

4. **Tests** (`shared/__tests__/scene-paging.test.ts`, 39 tests at ship)  
   - Il. 1 scenes 2–4 on **default** path (what Reader uses).  
   - Synthetic: terminator only past straddling tick → page must not end mid-sentence.  
   - Hollow guardrail unit cases.  
   - Pure partition tests still use `{ applyHollowGuardrail: false }`.

### Verified correct after fix (Il. 1)

| Scene | Expected |
|---|---|
| 2 (8–32) | Ends at “…return the safer.” — not the prayer |
| 3 (33–42) | “So he spoke, and the old man was seized…” through “…heard him.” — not Olympus, not Agamemnon loom lead-in |
| 4 (43–52) | Starts “Down from the peaks of Olympus…” |
| 5 / 6 | After hard-refresh: scene 5 ends Calchas; scene 6 opens Agamemnon rising |

### Codex review (on PR #3)

**ship-with-fixes** — residual edge case:

- Short scene **wholly inside one tick** with no fully-contained tick: `naturalEndOffset` can pick a sentence end **before** `scene.startLine` in that tick.  

**Corpus check (push back on theory):** among **790** scenes (Murray ticks, both epics), scenes wholly inside **one** tick: **1**

- **Iliad 8 scene 16**, lines **485–488** (“The sun sets, ending the day's fighting.”), inside tick 485–489.

Not merge-blocking; optional follow-up.

### Explicitly out of scope for this PR

- Perfect classicist alignment of every scene boundary corpus-wide.  
- Speech-aware page cuts.  
- Replacing hollow guardrail with full re-partition of neighbors.  
- Checked-in Il. 1 fixture independent of `build/dist` (real-data tests still skip if artifacts missing).

---

## Deploy notes (John executed)

1. Merged PRs #1–#3 into `claude/build` on GitHub.  
2. `git checkout claude/build && git pull`.  
3. `source ~/.nvm/nvm.sh && nvm use 22 && npm run build:public`.  
4. Gotcha: **`ENOTEMPTY` on `rmdir build/dist`** if Astro **dev server** still has that directory open. Kill preview (`:4321`), `rm -rf build/dist app/dist`, rebuild.  
5. Worktree / folder `~/Developer/homer-reader-site` on branch `gh-pages`.  
6. `rsync -a --delete --exclude .git app/dist/ →` site folder; `touch .nojekyll`.  
7. Commit + `git push origin gh-pages` → live project Pages.  

**Live base:** `/homer-reader/` (see `app/astro.config.mjs` `base`).  
**URL:** https://johnhboyer-sys.github.io/homer-reader/  

Harmless noise in deploy commit: `.DS_Store` files slipped in; optional `.gitignore` on `gh-pages` later.

**Merge alone does not make fixes live** — only `gh-pages` push does. Source: private `origin` (`homer-reader`). Pages also configured for project URL under that repo.

---

## Process / multi-agent notes (John)

- Preferred **PRs into `claude/build`**, one concern per PR; no force-push; no deploy without explicit ask (this session: John redeployed).  
- Dev server shows **only the checked-out branch** — testing PR #3 alone does **not** include #1/#2 until merged into the same branch.  
- Codex CLI used for adversarial PR reviews (gpt-5.6-terra); notes under `.claude/review-pr-*.md` (local; may not be committed).

---

## Suggested follow-ups for Claude

1. **Optional:** fix `naturalEndOffset` for the single one-tick scene (Il. 8.16) — enforce owned interval using `scene.startLine` as well as end.  
2. **Optional:** hollow guardrail → re-slice partition instead of raw tick paste if it ever fires again.  
3. **Larger overhaul (John deferred):** Reading Mode pager that systematically balances sentence integrity vs apparatus ownership (speech openings, next-scene preference, checked-in fixtures).  
4. Keep deploy recipe handholding-friendly in `LAUNCH-CHECKLIST.md` if not already (ENOTEMPTY + dev server gotcha is new).  
5. Strip `.DS_Store` from `gh-pages` history or ignore going forward.

---

## Quick file map

```
shared/components/LexiconPanel.svelte   # reactive lookup + seq guard
shared/__tests__/word-popup.test.ts     # token-switch regression
shared/styles/global.css                # .reader-controls::before height 4px
shared/lib/scene-paging.ts              # naturalEndOffset, hollow guardrail, snap
shared/__tests__/scene-paging.test.ts   # Il.1 + mid-sentence + hollow tests
docs/grok-fixes.md                      # this file
```

---

*Written 2026-07-20 for Claude Code resume. Prefer this file over chat archaeology when continuing apparatus/reader work.*
