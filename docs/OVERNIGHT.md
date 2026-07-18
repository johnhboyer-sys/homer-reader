# Overnight build orders (John, 2026-07-17 ~23:00)

John: "I'm going to let you build overnight. Note all decisions I need to
make and hold them til later. UNLESS they are absolutely necessary for
proceeding, just set to the side and build. And if you get to the QA
phase and I'm not up yet, do a thorough review of the site and make it
better."

Interpretation: full build autonomy through the greenlit scope + Phase 6
QA + a whole-site improvement pass. Hard gates UNCHANGED regardless:
**no deploy, no GH Pages enablement, no domain/naming, no merge to main,
nothing that costs money.** Commits to claude/build + prompt pushes are
standing-authorized. Every decision that would normally go to John gets
LOGGED below and worked around, not waited on.

## Decisions held for John (accumulate here overnight)

1. Domain / site naming (og:url + astro.config `site` stay
   `example.invalid` until named).
2. Il. 8.538–541: should the %11 bullet-sigil lines render as athetized?
   (DEPLOY-STATUS review item 0.)
3. Apologoi containment-inference call (review item 0a).
4. Odyssey credit wording approval; Lyceum About wording.
5. Apparatus draft→reviewed flips (all remain draft; badges shown).
6. PR review + merge of claude/build → main.
7. Deploy + GH Pages + Mollick reply timing (PROMO.md sequence).

## Overnight sequence (orchestrator works down this list as lanes free)

1. Wave A design fixes (in flight) → verify → commit; both-theme
   screenshots saved to scratchpad design-board/wave-a/ for the morning.
2. /places/ gazetteer (Codex, in flight) → MANDATORY Sonnet verify+taste
   pass → commit.
3. Scansion pipeline stage (in flight) → commit → then reader-UI half:
   scansion overlay toggle + Chamberlain audio (CC-BY, Iliad full +
   Od. 1–7, attributed, graceful degrade).
4. /characters/ page + character network (dispatching now).
5. Wave B design punch (after Wave A lands; header unification and
   spacing tokens are cross-surface — single-threaded lane, not fan-out).
6. When pipeline is free: per-book vocab lists + ἐπ' αἶαν epithets fix
   (#16). ANY stage re-emit ends with `apparatus --work <W>` both works
   + 48/48 scenes check (standing gotcha).
7. Phase 6: full verification matrix; GPT-5.6-Sol-High adversarial
   whole-site review; thorough orchestrated QA + improvement pass
   ("make it better" is explicitly authorized); handoff docs
   (DEPLOY-STATUS, LAUNCH-CHECKLIST); FINAL GATE Od. 9.366 (Οὖτις):
   jump box, parse, 3 translations, Wanderings pin, nested speech span,
   draft-badged summary.
8. Morning brief: wake-up summary for John — what landed, what's held,
   screenshots/board links, the decision queue above.

Fleet rules bind as in CLAUDE.md (cap 5, explicit model on every spawn,
implementation ≠ verification, cross-family verify on deploy-gating work,
explicit-path staging while agents run, push after every commit).
