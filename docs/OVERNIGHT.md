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
8. Chamberlain audio granularity (decided-for-now overnight, revisit):
   his corpus has NO per-line timing — audio exists per ~80–130-line
   chunk. Shipping "hear this passage" at honest chunk granularity,
   hotlinked from archive.org (his own embed pattern; CC BY 3.0 for 10
   early Iliad books, CC BY 4.0 for the rest — attribution says both).
   True per-line audio would need a forced-alignment build (real,
   unscoped work) — John to decide if that's wanted as a follow-up.
   Also open: optionally vendoring a marquee book (Il. 1, ~40MB) into
   the site for resilience vs. keeping the repo audio-free (current
   choice: audio-free, hotlink everything).

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

## Morning decisions (John, 2026-07-18)

- **Reading Mode stays prose** ("Murray did prose so keep it prose") —
  no prose label, no Pope alternative. CLOSED.
- **Priority order:** text quality + reader navigation first;
  maps/supplementary surfaces deferred until those are solid.
- Queue add (2026-07-18 morning): **Iliad day-calendar convention** —
  ours ends Day 38 (summarized end-spans compressed: the nine days of
  wood-gathering, twelve-day truce); traditional chronologies expand
  them to ~51-52 days. John to choose; one-pass recalibration if the
  classic scheme is preferred.
- Queue add: zero-flash stacked-Both on returning phone users needs the
  data-rview pre-hydration bridge (one visible reflow today; cosmetic).
- DECIDED (John, 2026-07-18): **Iliad calendar → traditional ~51-day
  numbering** (citable: Leaf/Whitman/tradition), recalibrated from our
  compressed 38; the timeline feature will visually compress the
  summarized spans instead. Odyssey stays Day 1–41 (Monro-corroborated).
- Queue add (2026-07-18): **Ogygia identification** — audit found the
  ancient Gozo/Gaudos tradition (Euhemerus, Callimachus; rebutted by
  ps.-Aristotle). Current tier 'mythical' is defensible; John to rule
  whether the rival tradition earns a note or a tier change.
