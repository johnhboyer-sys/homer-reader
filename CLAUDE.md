# The Homer Reader — CLAUDE.md

Static Astro + Svelte site: parallel Greek/English digital edition of the Iliad and
Odyssey with Landmark-style apparatus (maps, marginal summaries, timelines,
genealogies, epithet/formula indexes) — the digital Landmark Homer, which never
existed in print. Repo lives at `~/Developer/homer-reader`. Forked from
`~/Developer/plato-reader`; verse machinery borrowed from
`~/Developer/classical-philosophy-reader`. Sister repos (also
`~/Developer/aristotle-reader`): consult their CLAUDE.md/docs for shared-machinery
background; **never edit them from here — read-only**. Node 22; pipeline via
Python (`homer_pipeline/`). Plan of record: `homer-reader-plan-2026-07-17.md`
(background; where it conflicts with `PROMPT.md` or this file, those win).
**Build trigger: when John says GO, read `PROMPT.md` and execute it end-to-end.**
Act as a classicist PhD (Homerist) + senior web engineer; Homeric Greek accuracy is
non-negotiable.

## Hard rules

- Greek source is TLG (licensed, local, Diogenes-readable, patched `-y` verse
  export). **Corpus source text is never committed.** Same posture as the siblings.
- Website translations: free/public-domain only, judged by **US** copyright rules
  (pre-1931 as of 2026). In: Murray (1919/1924–25), Butler (1898/1900), Pope
  (1715–26), Autenrieth, LSJ, Cunliffe (1924). NEVER: Lattimore, Fitzgerald,
  Fagles, Lombardo, Wilson, M. L. West's editorial text, anything from the print
  Landmark series. archive.org "NOT_IN_COPYRIGHT" can be Canada-only — verify US.
- **Vulgate lineation is sacred.** Never renumber. Numbering gaps and
  bracketed/athetized lines are preserved verbatim; a verifier asserts monotonic
  numbering with recorded, expected gaps per book.
- **Apparatus sourcing (John, 2026-07-18):** apparatus features may draw on
  copyrighted scholarship as SOURCES — cited precisely, attributed quotes
  welcome, never republished wholesale. Site translations remain PD-only
  (rule above unchanged). Print Landmark series stays excluded entirely.
  Every sourced claim carries its citation in the data, not just the prose.
  Citation format (John, 2026-07-18): **Chicago** for books and articles;
  everything else (web resources, databases, blogs) hyperlinks to the
  source within the citation.
- **Apparatus honesty:** AI-drafted apparatus carries `status: "draft"` until John
  flips it; the UI shows a discreet draft badge. Every place has a certainty tier
  (`certain | traditional | speculative | mythical`); traditional identifications
  name their tradition. Never invent an identification.
- **Map registers (John, 2026-07-28): "it's an editorial and artistic decision
  to let Homer's descriptions determine the map."** Two registers, never mixed.
  A *geographic* plate carries only what survey and archaeology support. A
  *schematic* plate carries the poem's own spatial logic — the camp order (Il.
  8.222-26, 11.806-8), the road and its waypoints — labelled as such. Most
  Homeric topography has NO defensible coordinate (Scaean Gate, oak, fig tree,
  ford, tomb of Ilos, the two springs, the Achaean wall); putting those at
  guessed coordinates on the geographic plate is the failure mode. Absences are
  content: label them. Sources: `docs/TROAD-SOURCES.md`.
- **Rich, not hedging (John, 2026-07-28): "the gods aren't real, but they are
  present in the text. No need to be pedantic just because a historian might
  well-actually us about where Ajax had a tent."** The certainty tier does the
  honesty work; the note must not re-apologise for it. State what the poem
  states as fact (Il. 8.222-26 on the camp order; 11.806-8 on the assembly and
  altars). The `mythical` tier is a CATEGORY, not a warning label — divine
  places (Callicolone, the wall of Heracles, Gargaron, Poseidon's seat on
  Samothrace) go on the map with confidence. Hedging is a defect, the same as
  overclaiming. What stays absolute: tiers, `tradition` naming its tradition,
  citations, and **never a fabricated coordinate**.
- **Dates are BC/AD, never BCE/CE (John, 2026-07-30).** Site prose, apparatus
  notes, captions, dossiers — all of it. Exception: verbatim quotation keeps
  the source's own unit (a geologist's "3300 BP" stays BP).
- **No movie branding.** No stills, no title treatment, no "Nolan". The tie-in is
  structural (Start Here funnel + SEO pages), not visual.
- Deploying is John's call — never deploy without explicit go-ahead. Hosting:
  **GitHub Pages, one-off build — no Cloudflare/R2 on this project (John,
  2026-07-17).** Reuse aristotle-reader's incremental gh-pages deploy recipe.
  Creating the GitHub remote and the first push are also John-gated. Stay in free
  tier; surface anything that would incur cost **before** doing it.
- Git flow (John, 2026-07-17; two-remote split 2026-07-18; CORRECTED
  2026-07-21 after a deploy push bounced): `github.com/johnhboyer-sys/
  homer-reader` (remote `origin`) is now PUBLIC and serves the site itself —
  Pages from its own `gh-pages` branch at /homer-reader/. Deploys push
  `gh-pages` to **origin** (worktree `~/Developer/homer-reader-site`). The
  `johnhboyer-sys.github.io` repo (remote `deploy`) holds ONLY the root
  redirect to /homer-reader/ — never push site deploys there.
  Commit as we go, **push promptly after every commit** (backup). PR bundling at the orchestrator's judgment
  (John): PR #1 = claude/build → main umbrella (phases 0–3 + scenes);
  subsequent coherent units get branches off claude/build with stacked PRs
  into claude/build. Review gate applies at PR time; merging `main` is
  John's. Never enable GH Pages / deploy without explicit go-ahead.
- Verify functionally, not with screenshots.
- All data fetches go through the `data.ts` data-root override — never bypass it.
- Accessibility: WCAG AA contrast in BOTH themes; keyboard access on Greek tokens
  never regresses. The Aegean skin is a token layer (CSS custom properties) —
  revertible by variable swap.
- **Colour is free (John, 2026-07-28): "we want blue for sea. this is digital,
  not print. color is free. in print, it's expensive."** Do NOT import print
  cartography's one-spot-colour discipline — the Landmark series and the
  19th-century plates used a single pale ink because press runs charged per
  ink, which does not constrain SVG in a browser. Sea reads as sea; land stays
  warm against it. Borrow print's *linework* conventions (waterlines, hachures,
  neatline, letterspaced caps) freely — those are craft. Its palette
  austerity is an artifact of cost. Contrast rules still bind: colour being
  free does not make WCAG AA optional.
- Maintain `DRIFT.md`: one line per shared-core file diverged from plato-reader.

## Build & verify (add facts here as agents discover them)

- Inherited sibling gotcha (verify on first build): system node may be v24, out of
  the `>=22.12 <24` engines range — `nvm use 22` before any npm/vitest/astro
  command.
- Verification matrix: `npx vitest run` in `shared/` and `app/`; pipeline tests via
  pytest; `npm run build` in `app/`. Adopt the classical repo's preflight-gated
  `build:public` pattern as a hard gate before anything ships. data-preflight
  must report 0 errors before any deploy.
- Codex gotcha (machine-level, inherited): after a ChatGPT account switch, the
  codex plugin's per-repo thread state
  (`~/.claude/plugins/data/codex-openai-codex/state/<repo-hash>/`) holds threads
  bound to the old account and every run fails with "token could not be
  refreshed" — clear that state dir and start a `--fresh` thread. `codex login
  status` saying "Logged in" is not sufficient evidence the plugin runtime works.

- Pipeline gotcha (2026-07-21, cost an Iliad re-emit): `build/stage1` is a
  per-run working dir — running `stage1` then `stage7` alone against a stale
  working dir (last full run was the other work) crashes stage7 (KeyError on
  the token map) AFTER it has wiped the work's dist dir. A re-emit is only
  valid as `all --work <W>` (then apparatus, per the rule below).
- Pipeline gotcha (2026-07-17, caught by Gate 4): any stage7 re-emit
  (incl. `all` and full re-runs) must be FOLLOWED by `apparatus
  --work <W>` for both works — stage7 rewrites book JSONs without the
  apparatus merge and silently wipes scenes. Until preflight asserts
  apparatus presence (Phase 6 hardening), every pipeline re-run brief
  must end with the apparatus re-merge + a 48/48 scenes check.
- Concurrency gotcha (2026-07-17, bit two agents the same day): an app
  build/verification that runs while a pipeline lane is regenerating
  build/dist sees TRANSIENT states (books without scenes, off page
  counts). Never "fix" what such a build shows — re-verify after the
  pipeline lane lands. Orchestrator: avoid scheduling app verification
  concurrent with pipeline re-emits.
- Browser-verification gotcha (2026-07-17, caught by the /places/ verify
  lane): the Playwright MCP browser session is SHARED across concurrent
  agents — a tab can be hijacked to another agent's URL between tool
  calls. Any browser-verifying agent must open its own dedicated tab,
  navigate immediately before every screenshot/assert with no intervening
  calls, and visually confirm each screenshot shows ITS page before
  trusting it.
- Build-output gotcha (2026-07-18): app/dist is also a shared mutable —
  two lanes running `astro build` in the same checkout clobber each
  other's dist mid-verification. Lanes verifying against dist must
  build+verify without another build lane running, or verify via dev
  server instead.
- Test-harness gotcha (2026-07-28, found by the grammar-search fix lane):
  under happy-dom, `bind:value` on a `<select>` cannot be driven by
  `fireEvent.change`. Svelte 5 reads the chosen option with
  `select.querySelector(':checked')`, happy-dom implements no `:checked`, so
  it falls back to "the first option that is not `disabled`" — every bound
  select snaps back to its first option and component state never moves. The
  test passes vacuously. Workaround in `shared/__tests__/grammar-ui.test.ts`
  (`choose()`): disable the other options for the duration of the event.
  Selects driven by a handler (`on:change` reading `currentTarget.value`, as
  the combo panel does) are unaffected, which is why nobody hit this before.
- Codex model-flag gotcha (2026-07-18): `--model gpt-5.6-terra-high` is
  REJECTED on this ChatGPT-account setup ("model is not supported…"); runs
  fall back to the account's default Codex model at `--effort high`. Label
  lanes accordingly; the routing table's Terra/Sol names describe intent,
  not a selectable flag here.
- Browser-tooling gotcha (2026-07-18): the Chrome-MCP `resize_window` can
  silently lock at ~800px wide mid-session — for mobile-viewport captures
  use the Playwright MCP's `browser_resize` (dedicated tab, as ever).
- Verification gotcha (2026-07-17, cost a full Opus diagnostic lane):
  John often has the sibling classical-philosophy-reader dev server
  holding port 4321, so Homer's `astro preview` silently bumps to
  another port — a browser pointed at the conventional :4321 tests the
  WRONG SITE (symptom: SSR fine via curl, "empty" DOM in the browser).
  Any browser-based verification must read the actual bound port from
  the server log first, and hard-reload past service workers.
- Rebuild gotcha (2026-07-27, measured — CORRECTS a belief several briefs
  have repeated): **pytest is NOT a rebuild.** `test_stephanus.py:272`
  monkeypatches `stage7_emit.BUILD_DIR` to a tmp dir, so a full `pytest -q`
  leaves `build/` mtimes untouched and finishes in ~2s. The real rebuild is
  `python -m homer_pipeline all --work <Iliad|Odyssey>` (~6 min for both),
  still followed by `apparatus --work <W>` for both works + a 48/48 scenes
  check. What IS true: `app/public/data` is a symlink to `build/dist`, so a
  rebuild instantly changes what the site serves.
- Worktree bootstrap (2026-07-27): a fresh worktree has no `.venv`,
  `node_modules` or `build/`. `uv sync` in `pipeline/` does NOT install
  pytest (it is declared nowhere) — add it with
  `uv pip install --python .venv/bin/python pytest`. `npm install` is needed
  separately in `app/` and `shared/` (no workspaces). The Iliad TLG export
  subprocess fails in-sandbox with exit 25 (`stage1_greek.py:42-56`,
  `docs/PHASE0-FINDINGS.md:33-38`); copy the cached
  `build/export/Diogenes-Resources/xml/tlg/tlg0012001.xml` from the main
  checkout.
- Test gotcha (2026-07-27): in `shared/` vitest (jsdom), `import.meta.url`
  resolves relative URLs against Vite's HTTP base, NOT the filesystem — so
  `fs.existsSync(new URL('../../x', import.meta.url))` is always false and a
  corpus-reading test passes vacuously. Use
  `path.resolve(process.cwd(), '../app/public/data')`, and skip loudly
  (`ctx.skip()`) rather than returning early.
- Rebuild gotcha (2026-07-28, cost a false scene-paging regression hunt): a raw
  CLI rebuild (`all --work <W>`) is NOT equivalent to `npm run build:public`.
  stage7 recreates `build/dist/<work>/`, wiping the per-work apparatus copies
  that only `scripts/build-public.mjs:91-95` restores — `speeches.json` above
  all. Top-level copies (characters/places/journeys/coastline/audio) survive
  because they sit above the wiped directory, so the gap is easy to miss.
  Symptom: `shared/__tests__/scene-paging.test.ts` fails on scene boundaries and
  on the ownership gate, because `real-book-loader.ts` has no speech starts to
  snap to — it looks exactly like a scene-paging regression and is not one.
  After ANY CLI rebuild, either run `build:public` or re-copy
  `apparatus/speeches/<work>.json` into `build/dist/<work>/` and then run
  `.venv/bin/python -m homer_pipeline.preflight ../build/dist ../manifests`,
  which asserts the file is present.

- Deploy-from-main recipe (2026-08-05, seventh deploy): `npm run build:public`
  runs fully isolated in a fresh worktree off main — copy `build/export`
  (1.6M) into the worktree, symlink `pipeline/.venv` to the main checkout's,
  `npm install` in app/ and shared/, nvm 22. build:public WIPES AND REBUILDS
  `build/dist` under its own root, so never run it in the main checkout while
  another session holds build/dist. Deploy = rsync app/dist →
  ~/Developer/homer-reader-site (exclude .git/.DS_Store), commit, push
  origin gh-pages.

## Orchestration

You (Fable) are the **orchestrator**. Your job is planning, decomposition,
delegation, integration, review, and commits — not bulk reading or bulk writing.
The main thread's context is the scarcest resource in this project; spend it on
decisions, not on file contents.

### Fleet rules (John's standing orders, 2026-07-17)

- **Concurrency cap: 5 agents maximum, simultaneously.** Queue the rest. Absolute,
  regardless of tooling defaults.
- **Subagent models: Opus, Sonnet, Codex, Grok.** (Grok off probation — John,
  2026-07-17 — full implementer status; ~85% of trial balance available as of
  2026-07-17, use liberally.)
- **Fable never spawns fable subagents unless John explicitly says to.**
- **Grok-4.5 is available again (John, 2026-07-17: upgraded, free trial).**
  Content-verification gates route to Grok per the routing table below.
- **Usage rebalance (John, 2026-07-17 ~17:00): conserve Claude; lean on
  Codex + Grok.** Claude 7d at 57%, Codex has two resets banked, Grok at
  24% used. Well-specified implementation defaults to GPT-5.6-Terra-High
  (Codex) or Grok; Sonnet/Opus reserved for reader-core subtleties,
  philological judgment, and integration-heavy work. Judgment allowed.
  **LIFTED (John, 2026-07-21): weekly usage reset — normal routing table
  applies (Sonnet default; Opus on genuine difficulty; Codex/Grok per
  their table roles). Codex effort lowered to medium the same day.
  **RAISED BACK to `--effort high` for both Sol and Terra (John,
  2026-07-28).**
  **Escalation rule (John, same day, refined): minor stumbles stay in
  the Codex/Grok lane — nudge, clarify the brief, retry once. Escalate
  to Claude (Sonnet; Opus on difficulty) only on a BAD fuckup: badly
  wrong output, a failed verification gate traceable to the agent's
  sloppiness, or a second failure on the same brief. Claude is the
  trust anchor; economy never outranks correctness.**
  **Cross-model brief discipline (John, same day): Codex/Grok briefs
  must be tighter than Claude briefs — zero implicit context. Spell
  out: exact file paths, exact commands (venv, nvm), the output schema,
  what NOT to touch, every known gotcha from this file, and the
  machine-checkable pass/fail criteria. Assume the model has never seen
  this repo and will not infer conventions. If a brief leans on "follow
  existing conventions," name the file that exemplifies them.**
  **Codex output verification (John, same day: "it can be sloppy"):
  every Codex implementation lane gets a quick Claude (Sonnet)
  verification pass — tests re-run, functional smoke, diff review
  against the brief's blast radius — BEFORE the orchestrator commits.
  Not a full adversarial gate; a competence check. Grok content gates
  are unchanged. For UI work, the pass ALSO reviews design fidelity
  against the approved mock (John: "I don't trust its taste") and
  captures both-theme screenshots for John before commit.**
  **Cross-model review runs BOTH WAYS (John, 2026-07-28): "have each
  claude agent's work (including your own) reviewed by gpt or grok."
  Every Claude implementation lane — and the orchestrator's own hand
  edits — gets a Sol (code) or Grok (content/data) pass before the work
  is considered done.
  **ROSTER CHANGE (John, 2026-07-29): Codex OFF on login failures.
  LIFTED (John, 2026-07-30 11:52): Codex is back — regular rotation
  applies (Sol adversarial/code review, Terra cross-model implementer,
  Grok content gates). The lesson stands: never silently downgrade a
  cross-family gate to an in-family one — an Opus review of Sonnet's
  work shares its blind spots, which is exactly how the black Shield
  and the dropped `places[]` field both got past green suites.**
  Not only at PR gates: a fleet of Claude agents
  checking each other shares a model's blind spots, which is how the
  Shield shipped rendering solid black past a colour test that only
  checked for `var()` and never that the token existed. Sol reviews
  code and contracts; Grok verifies content against the corpus with raw
  evidence. Findings-only briefs — reviewers do not edit tracked files.**

### Context discipline

- **Delegate any task that requires reading more than a couple of files or
  producing bulk output.** Agents read; you receive conclusions. Never pull large
  files, build logs, or corpus data into the main thread when an agent can return
  a verdict with `file:line` citations.
- Every delegation brief states: the goal, **machine-verifiable success criteria**,
  the files/areas in scope, what is explicitly out of scope, and the **shape of
  the return** (bounded: a verdict, a diff summary, a list of findings — never a
  file dump).
- Fan out independent work in parallel (within the 5-agent cap); never serialize
  what doesn't depend on prior results. Use worktree isolation whenever parallel
  agents mutate files.
- Don't redo delegated work yourself. If an agent fails twice on the same brief,
  stop retrying: either read the minimal context yourself and rewrite the brief,
  or escalate the model tier. Never loop a failing agent.
- Keep this file lean. When a durable convention or gotcha is discovered, add one
  line here (or to the relevant doc) — a rule that isn't written down will be
  violated by the next agent.

### Model routing

| Model | Role | Use for |
|---|---|---|
| **Fable** (main thread) | Orchestrator | Planning, decomposition, briefs, integration, review of agent returns, commits/pushes, all conversation with John. No fable subagents without John's say-so. |
| **Opus** | Heavy reasoner | Architecture decisions, subtle pipeline/alignment bugs, Homeric philological judgment calls (vulgate lineation and athetized lines, formula/epithet boundaries, morphology disputes, speech-span nesting), judgment-heavy apparatus drafting, final verification of high-stakes work |
| **Sonnet** | Workhorse (default subagent) | Well-specified implementation, tests, mechanical multi-file edits, exploration/search sweeps, doc updates, data-build babysitting, per-book apparatus batches (~5 books/agent) |
| **GPT-5.6-Sol-High** (back on roster, John 2026-07-30) | Adversarial reviewer | Red-team review of finished work before John's review gates and before any deploy; cross-model second opinion on designs. Precedent: the plato-reader 14th-deploy whole-site adversarial review (15 confirmed findings). |
| **GPT-5.6-Terra-High** (back on roster, John 2026-07-30) | Cross-model implementer | Independent implementation of isolated, well-specified tasks; independent bug reproduction; second implementation when comparing approaches |
| **Grok-4.5** (Grok CLI, `grok-cc:grok-rescue`) | Full implementer + content verifier (off probation, John 2026-07-17; free trial) | Content/extraction verification gates (its specialty — twice found defect classes Sol/Opus/Claude all missed, with raw-line evidence), additional adversarial passes, mechanical coding tasks. Forwarder quirk (BOTH grok-rescue and codex-rescue): the runner may background the CLI task and end its turn with no result — nudge via SendMessage ("wait for the run and return the findings"). Gotcha: read-only task mode gets Cancelled by the runtime — use write-capable with a no-tracked-file-edits constraint. |

Routing principles: default subagent is Sonnet; escalate to Opus on genuine
difficulty, not on volume. **The Agent tool inherits the orchestrator's model
(Fable) whenever the `model` parameter is omitted — the prompt text saying "you
are a Sonnet subagent" does nothing. Every spawn must pass `model:` explicitly,
matching the label** (caught by John 2026-07-16). CLI forwarders run a Claude
wrapper around the external CLI — label them "<wrapper>→<worker>: …" (e.g.
"Sonnet→GPT-5.6-Sol-High: review X") so the status line tells the whole story.
**Every agent label/description starts with its model** (John, 2026-07-17):
"Sonnet: fix alignment defects", "Opus: verse-line scheme" — no unlabeled
spawns.
**Resuming a completed agent (SendMessage) does NOT re-apply its model override —
the resumed turn runs on the session model (Fable). For tier-sensitive
follow-ups, launch a FRESH agent with `model:` set and hand it the needed
context — or accept and label the Fable fallback** (caught by John 2026-07-16).
**Implementation and verification are never the same agent** — and for anything
gating a deploy or a PR to main, the verifier should be a *different model
family* (Sol reviewing Claude-written code, or Opus reviewing Codex-written
code). Codex sandbox caveat: **Codex agents cannot write `.git` metadata — Codex
implements, the orchestrator commits and pushes.** Tune these assignments from
observed results and record changes here.

### Fan-out guidance (Homer-specific)

- Fan-out-appropriate: per-book apparatus drafting (48 books of `scenes.json`,
  character mentions, book arguments — batches of ~5 books so a sweep runs in
  clean waves under the cap); alignment QA sweeps (agents report mismatches, never
  fix inline); adversarial verification of finder passes.
- Single-threaded only: citation scheme, works registry, pipeline stages, reader
  components, design tokens, anything touching `DRIFT.md`-tracked files.
- Every fan-out defines its output schema BEFORE spawning; agents return data, not
  prose. Reject and re-run non-conforming outputs — do not hand-patch them.
- Apparatus drafting briefs paste in the persona header (classicist PhD, Homerist)
  and the certainty-tier + draft-status rules — subagents do not inherit this file
  automatically.
- No silent caps: if a sweep samples rather than covers, say so in the report.
- The agent that drafted a book's apparatus never signs off on that book.
- Phase gates are checked in the main loop, never inside a subagent.

### Human gates (orchestration must route through John, never around him)

Main-branch commits (summary first) · deploys · anything costing money · copyright
judgment on any translation or edition · naming/domains · apparatus sign-off
(`draft → reviewed` flips are John's alone) · contested place identifications and
canon/scope calls (Hymns, Batrachomyomachia — log the decision in the plan doc).

## Coding rules (Karpathy's, adopted — they bind every agent, and every brief you write)

The four core rules, from Karpathy's CLAUDE.md:

1. **Think before coding.** Don't assume; don't hide confusion; surface tradeoffs.
   State assumptions explicitly; when uncertain, present interpretations and ask
   rather than guess. *(Orchestration corollary: a brief that forces an agent to
   guess is a defective brief — ambiguity gets resolved in the main thread, before
   delegation.)*
2. **Simplicity first.** Minimum code that solves the stated problem; nothing
   speculative, no unrequested features, no single-use abstractions. Cut
   ruthlessly.
3. **Surgical changes.** Touch only what the task requires; preserve existing
   style; don't refactor unbroken code; clean up only your own orphans. Every
   changed line must trace to the ask. *(Corollary: briefs declare their blast
   radius, and diffs outside it are rejected at review.)*
4. **Goal-driven execution.** Define success criteria a machine can verify before
   starting; loop until verified. *(Corollary: this is what makes delegation
   possible at all — agents get outcomes to satisfy, not steps to follow.)*

And from his expanded set, the ones this project adopts:

5. **Verification.** Before fixing a bug, write a test that reproduces it; fix;
   run the test. (Inherited discipline: the plato Laws turn-flow fix *replaced the
   test that had locked in the bug* — tests are claims, and wrong tests get
   replaced, not appeased.)
6. **Debugging.** Read the full error and stack trace; reproduce before fixing;
   change one variable at a time.
7. **Dependencies.** Every added package is permanent, uncontrolled code. Standard
   library first; justify anything beyond it in the commit message.
8. **Communication.** Report actionable information; when uncertainty is the
   accurate answer, say so — no confident-sounding guesses. (For agents: your
   return value is a report to the orchestrator; a wrong confident summary poisons
   decisions downstream.)
9. **Stop the failure modes.** Kitchen Sink (scope creep), Wrong Abstraction
   (premature generality), Optimistic Path (untested happy path), Runaway Refactor
   (touching the world). Any agent that catches itself in one stops and reports
   rather than continuing.

## Failure-mode registry (append dated lessons — a lesson not written down will be repeated)

- **Plan-mode Explore/Plan spawns ran on Fable** (2026-07-21, caught by John):
  the plan-mode workflow's built-in Explore/Plan agent types count as spawns —
  omitting `model:` inherits Fable there too. No explicit `model:`, no launch.

- **`git add -A` while agents are in flight** (2026-07-17, twice): sweeps
  concurrent agents' uncommitted work into unrelated commits. Orchestrator
  commits must stage explicit paths whenever any agent is running.
  UPDATE (2026-07-18, orchestrator self-caught): DIRECTORY adds count —
  `git add shared/__tests__/` swept an in-flight lane's test edits into an
  unrelated commit. Stage explicit FILES, never directories, while any
  agent runs.

- **Two Claude Code sessions in one checkout** (2026-07-28, caught by the
  orchestrator before any commit): a second session was working this repo on
  `claude/build` (a places/geo apparatus lane) while this one started. A
  checkout holds ONE branch, so `git checkout -b` here silently moved the other
  session's tree onto a branch it knew nothing about, and its uncommitted work
  landed there. Nothing was lost — uncommitted changes survive a branch switch,
  and both branches sat on the same commit — but the next commit from either
  side would have swept the other's files in.
  Symptoms: files dirty outside every lane's blast radius; an agent reporting a
  file "already modified on disk" that `git status` showed clean at session
  start; transient vitest failures from a half-written module (here
  `scenemap.ts`, mid-refactor, breaking 11 unrelated files through the vite
  cache). Diagnosis: `lsof -t +D <repo>` and look for more than one `claude`.
  **Rule: before `git checkout -b` here, diff `git status` against the
  session-start snapshot. If files you do not own are dirty, STOP and ask John
  — do not branch, do not commit.** The fix is a worktree per session
  (`git worktree add ../homer-reader-<lane> <base>`), which is where this lane
  moved; symlink `build/` to the main checkout so the corpus is readable
  without a 6-minute rebuild, and treat it as read-only.

- **An accurate drawing of the wrong thing** (2026-07-30, John: "an
  archeological picture of troy is useless"): Plate A first shipped as a
  faithful trace of Dörpfeld's excavation record — rectified, validated,
  LOOK-gated, and wrong, because the reader-facing plate must show the
  poem's standing city, with research as accuracy source and excavation
  apparatus demoted to notes. Every gate passed; none asked "what does the
  reader of Homer see?" **Drawing briefs must state the reader-facing
  register explicitly** — a lane handed survey sources will draw the survey.
  Standing rule recorded the same day: "this is a HOMER reader, not an
  archeology site"; the research was to get the details right, never the
  subject.

- **A map with no map under it** (2026-07-28, John: "it's just shapes. no
  geography at all. my 5 year old could draw this"): the Troy plates shipped to a
  PR with hand-authored coordinate arrays — 5-17 vertices per coastline — as
  their base. **Geography cannot be hand-authored.** Ten times the vertices is a
  smoother blob, not a coast. Real basemaps come from real vector data: AWMC's
  ancient-world GeoJSON (ODbL), Natural Earth 10m, OSM, a DEM for relief. The
  drawing primitives (hachure, waterlines, ship glyphs) are the FINISH, not the
  foundation; a whole day went into them over nothing.
  **And every gate was green.** 893 tests, preflight clean, 4705 pages, five
  plates validating — none of it could see that the output was unreadable.
  "Verify functionally, not with screenshots" means do not accept a screenshot as
  proof of CORRECTNESS; it does not mean never look at a visual artefact. **For
  anything whose output is an image, rendering it and LOOKING is a required gate,
  and the agent that made it must look before reporting done.**

- **Fork drift** (aristotle→plato: ~20 files diverged in 4 days): this repo is the
  fourth fork. `DRIFT.md` is the mitigation; keep it current.
- **Renumbering corruption:** sequential renumbering corrupts every citation.
  Numbering gaps are data, not bugs.
- **Paragraph flattening** (aristotle pipeline): English paragraph breaks silently
  flattened corpus-wide; fix required a full rebuild. Preserve paragraph structure
  from stage 1; verify with a round-trip test.
- **XSS + regex injection** (aristotle PR #17): user-reachable strings (search
  input, jump box, imported text) are hostile. Sanitize at render; escape regex
  metacharacters in queries; test both.
- **Base-path pain** (GH Pages era): serve at domain root; never hardcode a base
  path; data root comes from the `data.ts` override only.
- **Nested speeches:** the Apologoi (Od. 9–12) are narrative-within-speech. Logic
  that paints four books as one Odysseus speech is wrong; flag nesting; degrade to
  plain rendering below the confidence bar. Speech spans crossing book boundaries
  are flagged, never silently split.

## Working with John

Philosophy professor, competent Greek, Thomist. Explain architecture decisions;
check in at milestones, not every step. He reads the diffs and the DEPLOY-STATUS
ledger — write both for a human.
