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
- **Apparatus honesty:** AI-drafted apparatus carries `status: "draft"` until John
  flips it; the UI shows a discreet draft badge. Every place has a certainty tier
  (`certain | traditional | speculative | mythical`); traditional identifications
  name their tradition. Never invent an identification.
- **No movie branding.** No stills, no title treatment, no "Nolan". The tie-in is
  structural (Start Here funnel + SEO pages), not visual.
- Deploying is John's call — never deploy without explicit go-ahead. Hosting:
  **GitHub Pages, one-off build — no Cloudflare/R2 on this project (John,
  2026-07-17).** Reuse aristotle-reader's incremental gh-pages deploy recipe.
  Creating the GitHub remote and the first push are also John-gated. Stay in free
  tier; surface anything that would incur cost **before** doing it.
- Git flow (John, 2026-07-17): private repo
  `github.com/johnhboyer-sys/homer-reader`; commit as we go, **push promptly
  after every commit** (backup). PR bundling at the orchestrator's judgment
  (John): PR #1 = claude/build → main umbrella (phases 0–3 + scenes);
  subsequent coherent units get branches off claude/build with stacked PRs
  into claude/build. Review gate applies at PR time; merging `main` is
  John's. Never enable GH Pages / deploy without explicit go-ahead.
- Verify functionally, not with screenshots.
- All data fetches go through the `data.ts` data-root override — never bypass it.
- Accessibility: WCAG AA contrast in BOTH themes; keyboard access on Greek tokens
  never regresses. The Aegean skin is a token layer (CSS custom properties) —
  revertible by variable swap.
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
| **GPT-5.6-Sol-High** (Codex CLI, `--effort high`) | Adversarial reviewer | Red-team review of finished work before John's review gates and before any deploy; cross-model second opinion on designs. Precedent: the plato-reader 14th-deploy whole-site adversarial review (15 confirmed findings). |
| **GPT-5.6-Terra-High** (Codex CLI, `--effort high`) | Cross-model implementer | Independent implementation of isolated, well-specified tasks; independent bug reproduction; second implementation when comparing approaches |
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

- **`git add -A` while agents are in flight** (2026-07-17, twice): sweeps
  concurrent agents' uncommitted work into unrelated commits. Orchestrator
  commits must stage explicit paths whenever any agent is running.

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
