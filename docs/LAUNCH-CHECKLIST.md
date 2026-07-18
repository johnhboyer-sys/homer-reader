# Launch checklist — 2026-07-18 (John: "Let's launch tonight")

Decisions locked: user-site rename (`johnhboyer-sys.github.io`, domain
root, custom domain may layer on later); Flaxman art ships IN the launch.

## Pre-deploy gates (all must be green on the final commit)

- [ ] Flaxman asset factory landed; assets + `apparatus/art.json`
      committed after orchestrator review of the contact sheets.
- [ ] Flaxman UI integration landed (header plate sized to the header
      band beside the wavy rule, desktop; hero plates with the Iliad
      image raised; dark ink = candidate A, bone at 0.67); verified in
      browser both themes.
- [ ] **John's render verdict on the integrated art. (John)**
- [ ] `npm run build:public` on the final commit: preflight 0 errors,
      0 broken links, 48/48 books carry `apparatus.scenes`.
- [ ] Spot-check built canonicals/sitemap carry
      `https://johnhboyer-sys.github.io` (config committed at 320411a).
- [ ] DEPLOY-STATUS.md launch entry written.
- [ ] **PR #1 (claude/build → main) merged. (John)**

## Deploy steps (orchestrator, in order, after the gates)

1. `gh repo rename johnhboyer-sys.github.io` (old URLs redirect).
2. Update local remote URL; verify `git remote -v`.
3. Build once more from `main` post-merge (the deployed artifact comes
   from main, per git flow).
4. Publish: orphan `gh-pages` branch = `app/dist` contents +
   `.nojekyll` (REQUIRED — `_astro/` is Jekyll-blocked otherwise);
   commit; push.
5. Enable Pages: source = `gh-pages` branch, root (`gh api`). Repo
   visibility: Pages on a private repo requires public repo or paid
   plan — **flip repo to public at this step (it's a launch)**; confirm
   with John if not already implied.
6. Wait for the Pages build; fetch `https://johnhboyer-sys.github.io/`
   until 200.

## Post-deploy verification (live URL)

- [ ] Home renders, both themes; hero English-first titles.
- [ ] /iliad/book/1 and /odyssey/book/9: Greek + Murray render; word
      popup parses; footnote opens; Reading Mode pages by scene.
- [ ] Maps: Wanderings story mode plays; gap badges 10/15 present.
- [ ] /timeline/, /places/pylos prose citation, Οὖτις 404.
- [ ] Sitemap + robots resolve; a sampled canonical matches the live
      origin.
- [ ] John's phone pass (the sheet-pin check rides along).

## Rollback

Pages source can be flipped off (or gh-pages reset to a prior commit)
in one step; the repo rename is reversible. Nothing destructive in the
path.
