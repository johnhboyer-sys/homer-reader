# LAUNCH-CHECKLIST — The Homer Reader

Everything below is John-gated unless marked done. Nothing here runs
without your explicit go-ahead. Written for a human at deploy time.

## 0. Decisions that must precede deploy (see docs/OVERNIGHT.md queue)

- [ ] **Domain / site name.** `astro.config.mjs` `site:` and
  `app/src/pages/robots.txt.ts` still carry the deliberate placeholder
  `https://example.invalid`. Fill with the real origin; robots.txt and
  the sitemap URLs derive from it. (OG cards are already Homer-branded;
  only the URL is pending.)
- [ ] **Merge to main.** PR #1 (claude/build → main) is yours to review
  and merge; the ledger (DEPLOY-STATUS.md) is the review companion.
- [ ] Review-queue calls that affect rendering: Il. 8.538–541 sigil,
  Apologoi containment (0a), Odyssey credit wording, Pope picker
  wording, Lyceum About wording.
- [ ] Any `draft → reviewed` apparatus flips you want pre-launch (all
  content currently ships with the draft badge, which is honest and
  fine to launch with).

## 1. Preflight gate (hard, machine-checked — run before ANY deploy)

```sh
cd ~/Developer/homer-reader
nvm use 22                       # engines >=22.12 <24; system node is 24
npm run build:public             # clean → pipeline --public → preflight
                                 # → astro build → check-links
```

`build:public` refuses to ship if preflight reports any error. Manual
equivalents if you need pieces:

```sh
cd pipeline && .venv/bin/python -m pytest            # 336+ tests
.venv/bin/python -m homer_pipeline.preflight ../build/dist ../manifests
cd ../shared && npx vitest run                       # 369+
cd ../app && npx vitest run && npm run build         # 4,711 pages
```

Verification invariants preflight enforces: vulgate lineation monotonic
with recorded gaps; apparatus presence (scenes 48/48, epithets,
speeches, characters, repetitions, scansion per book, vocab); audio
manifest copy consistency; alignment tick floors.

## 2. GitHub Pages deploy (aristotle-reader incremental recipe)

One-off static hosting at the domain root — no Cloudflare/R2 (John,
2026-07-17). Free tier throughout; site is ~static HTML + JSON, audio
is hotlinked from archive.org (nothing heavy in the repo).

1. `nvm use 22 && npm run build:public` (gate above must pass).
2. Clone/refresh the `gh-pages` worktree (first deploy: create orphan
   branch; later deploys: reuse — never re-init git at size).
3. `rsync -a --delete app/dist/ <gh-pages-worktree>/` then commit with
   a dated message and push.
4. Enable Pages on the repo (first time only): branch `gh-pages`, root.
   Custom domain per decision #0; enforce HTTPS.
5. Smoke: `curl -sI https://<domain>/` 200; spot-check a deep link
   (`/odyssey/book/9?loc=9.366`), a places citation, sitemap.xml.

## 3. Post-deploy verification (the FINAL GATE, live)

Od. 9.366 (Οὖτις): jump box → parse popup → three translations →
Wanderings map pin → nested speech span → draft-badged scene summary.
Then: OG card renders in a social-card debugger; Lighthouse mobile ≥90;
both themes AA spot-check; ⌘K palette; meter + audio toggles on Il. 1.

## 4. Promo (docs/PROMO.md is the plan of record)

- Mollick reply fires immediately on deploy, any day.
- Launch thread the following **Sunday**, pinned. No movie branding.
- OG cards per SEO lander: bespoke cards are a nice-to-have before the
  launch thread; generic Homer card is acceptable for the Mollick reply.

## 5. Rollback

Pages serves the `gh-pages` branch head; `git revert` (or reset to the
prior deploy commit) on `gh-pages` and push restores the previous site
in one step. Corpus/data problems: fix on claude/build, re-run the
gate, re-deploy — never hand-edit `gh-pages`.
