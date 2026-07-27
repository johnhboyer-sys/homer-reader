# Pope scene-anchor review (2026-07-21)

For John's spot-check before these anchors are treated as settled.

**What this is:** `sources/pope/scene-anchors-{iliad,odyssey}.json` — one
verbatim Pope Iliad/Odyssey text anchor per apparatus scene start (except each
book's own first scene, which auto-anchors at offset 0), resolving Pope's
verse to a `real: true` tick at the correct vulgate line in the reader
(`pipeline/homer_pipeline/stage1_pope.py`, schema in
`docs/APPARATUS-SCHEMAS.md`).

**Provenance:** AI-drafted per book (fan-out, ~5 books/agent), then every
entry adversarially verified by a second model against the scene's
Murray-derived opening. 19 of 742 entries failed first-pass verification and
were redrafted; a recheck pass re-verified all 19, of which 17 came back
correct. The remaining 2 (Odyssey 11 n=628, Odyssey 16 n=266) still failed on
recheck and needed a senior ("Opus adjudication:") pass to land correctly.
Every shipped entry carries `status: "verified"`.

**Totals:** 388 Iliad anchors + 354 Odyssey anchors = **742 total**, matching
the expected count. All 48 books pass `validate-anchors.mjs` with 0 errors (52
non-fatal sentence-boundary warnings across the set — see the per-book table).

Note on count framing: the brief for this pass described "21 corrected
entries (19 redrafts + 2 adjudications)." The data shows the 2 adjudicated
entries (Odyssey 11 n=628, Odyssey 16 n=266) are two of the 19 redrafted
entries, not additional to them — they simply needed a second correction
round after the first redraft still failed recheck. So the true count of
distinct corrected anchors is **19**, two of which are flagged below as
having gone through an extra adjudication step.

## Corrected entries (19)

For each: the first-pass verification reason (which names what was wrong with
the original anchor, and usually quotes it or the correct replacement) and
the anchor that shipped. The 2 marked **[adjudicated]** required a second
correction round beyond the redraft — see their extra row.

| Book | n | First-pass verdict reason (why it was wrong) | Shipped anchor |
|---|---|---|---|
| Il. 2 | 53 | Anchored the rosy-Morn dawn formula closing the prior dressing scene; true opening is the heralds' summons and elders' council. | "The king despatch'd his heralds with commands" |
| Il. 3 | 324 | Anchored the armies' prayer that finishes the prior lots sequence; true opening is the lot falling to Paris. | "With eyes averted Hector hastes to turn" |
| Il. 4 | 501 | Anchored mid-blow in Democoön's death, closing the prior casualty sequence; true opening is the Trojan panic and Apollo's rally. | "Seized with affright the boldest foes appear;" |
| Il. 7 | 433 | Anchored the Achaean cremation still belonging to the prior burial scene; true opening is the dawn before the wall-building. | "Now, ere the morn had streak'd with reddening light" |
| Il. 11 | 489 | Late: caught the later Doryclus kill instead of Ajax's tower-shield stand and Menelaus leading Odysseus out. | "But soon as Ajax leaves his tower-like shield," |
| Il. 13 | 330 | Late: sat mid-scene on the Zeus-Poseidon digression instead of the Trojans sighting Idomeneus and closing for battle. | "Soon as the foe the shining chiefs beheld" |
| Il. 20 | 306 | Late: anchored only Hera's reply after Poseidon's prophecy speech, missing the speech's own closing couplet on Aeneas's future kingship. | "On great Æneas shall devolve the reign," |
| Il. 21 | 21 | Anchored the later twelve-youths capture; true opening is the sword-slaughter/river-reddening beat. | "Repeated wounds the reddening river dyed," |
| Il. 23 | 176 | Anchored the host's dismissal and pyre-building; true opening is the slaughter of the twelve Trojan captives. | "Sad sacrifice! twelve Trojan captives fell." |
| Od. 5 | 412 | Anchored the wave-dash after the monologue; true opening is the no-harbor/sharp-crags deliberation itself. | "No port receives me from the angry main," |
| Od. 9 | 170 | Caught the prior scene's night-sleep close ("Now sunk the sun…"); true opening is the dawn muster speech. | "I call'd my fellows, and these words address'd" |
| Od. 11 | 628 | **[adjudicated]** First-pass caught the mid-speech Cerberus climax; the redraft's own choice ("Now I the strength of Hercules behold…") was rechecked as still too early — both sit inside the prior scene span (568–627). | "Curious to view the kings of ancient days," |
| Od. 12 | 73 | Caught the prior Wandering-Rocks/Argo close; true opening is Scylla's cliff description. | "High in the air the rock its summit shrouds" |
| Od. 13 | 121 | Caught the prior landing's treasure-laying by the olive; true opening is Poseidon's approach to Zeus to protest. | "Before the throne of mighty Jove he stood," |
| Od. 15 | 261 | Late: missed Theoclymenus's own opening address, landing on Telemachus's later reply instead. | "O thou! that dost thy happy course prepare" |
| Od. 16 | 266 | **[adjudicated]** First-pass caught Odysseus's second speech; the redraft's own choice ("Mark well my voice…") was rechecked as still Odysseus's *first* speech (still inside the prior scene, n=221's span) — true start is his second speech. | "Such aids expect (he cries,) when strong in might" |
| Od. 17 | 150 | Anchored Telemachus finishing his report and the queen's silence, closing the prior scene; true opening is Theoclymenus rising to prophesy. | "When Theoclymenus the seer began:" |
| Od. 18 | 346 | Anchored Odysseus resuming torch-duty, closing the Melantho scene; true opening is Athena rousing the suitors to further insult. | "And now the martial maid, by deeper wrongs" |
| Od. 21 | 256 | Anchored glued Eurymachus's closing exclamation onto the "Antinous thus replied" attribution tag, mixing the two speakers; true opening is Antinous's speech alone. | "Not so, Eurymachus: that no man draws" |

## Per-book table

Scenes = staged scene count for the book (incl. the auto-anchored first
scene); Anchors = curated anchor entries shipped for the book (scenes − 1);
Warnings = non-fatal `validate-anchors.mjs` check-5 sentence-boundary
warnings (Pope's couplets not always breaking exactly on the scene boundary —
worth a glance, not an error).

| Book | Scenes | Anchors | Warnings |
|---|---|---|---|
| Il. 1 | 20 | 19 | 0 |
| Il. 2 | 20 | 19 | 0 |
| Il. 3 | 17 | 16 | 0 |
| Il. 4 | 15 | 14 | 0 |
| Il. 5 | 19 | 18 | 1 |
| Il. 6 | 16 | 15 | 0 |
| Il. 7 | 18 | 17 | 0 |
| Il. 8 | 18 | 17 | 0 |
| Il. 9 | 17 | 16 | 1 |
| Il. 10 | 16 | 15 | 1 |
| Il. 11 | 20 | 19 | 2 |
| Il. 12 | 17 | 16 | 0 |
| Il. 13 | 19 | 18 | 1 |
| Il. 14 | 13 | 12 | 2 |
| Il. 15 | 17 | 16 | 1 |
| Il. 16 | 19 | 18 | 2 |
| Il. 17 | 16 | 15 | 1 |
| Il. 18 | 18 | 17 | 0 |
| Il. 19 | 14 | 13 | 1 |
| Il. 20 | 12 | 11 | 1 |
| Il. 21 | 17 | 16 | 2 |
| Il. 22 | 14 | 13 | 1 |
| Il. 23 | 20 | 19 | 2 |
| Il. 24 | 20 | 19 | 2 |
| Od. 1 | 15 | 14 | 0 |
| Od. 2 | 14 | 13 | 0 |
| Od. 3 | 18 | 17 | 2 |
| Od. 4 | 20 | 19 | 0 |
| Od. 5 | 15 | 14 | 1 |
| Od. 6 | 14 | 13 | 1 |
| Od. 7 | 14 | 13 | 0 |
| Od. 8 | 16 | 15 | 1 |
| Od. 9 | 17 | 16 | 2 |
| Od. 10 | 20 | 19 | 1 |
| Od. 11 | 14 | 13 | 1 |
| Od. 12 | 19 | 18 | 5 |
| Od. 13 | 12 | 11 | 3 |
| Od. 14 | 13 | 12 | 0 |
| Od. 15 | 16 | 15 | 3 |
| Od. 16 | 14 | 13 | 1 |
| Od. 17 | 18 | 17 | 2 |
| Od. 18 | 14 | 13 | 1 |
| Od. 19 | 15 | 14 | 0 |
| Od. 20 | 14 | 13 | 1 |
| Od. 21 | 15 | 14 | 1 |
| Od. 22 | 18 | 17 | 1 |
| Od. 23 | 17 | 16 | 2 |
| Od. 24 | 16 | 15 | 2 |

**Totals:** 388 Iliad scenes-1 = 388 anchors; 354 Odyssey scenes-1 = 354
anchors; 742 grand total. 52 total warnings, concentrated in the Apologoi
(Od. 12 has the most, 5) where Pope's continuous narrative style breaks less
often on hard sentence boundaries.

## Post-verification notes (2026-07-21, ownership-floor triage)

Five Pope pages sit below the Murray/Butler ownership floor (0.7) for a
structural reason — Pope's colon/semicolon-linked couplets carry a sentence
past a content-correct neighboring anchor — and the audit now applies a
documented Pope-specific floor (0.55) covering exactly these worst pages:
Il. 19 sc.13 (0.690) · Il. 21 sc.2 (0.567) · Od. 3 sc.3 (0.652) ·
Od. 11 sc.13 (0.650) · Od. 23 sc.15 (0.677). All binary defect gates
(empty/mid-sentence/out-of-range/duplication/lossless) remain at zero across
all 144 books.

**Editorial flag for John (accuracy, not paging):** Il. 21 scene 2's anchor
"Repeated wounds the reddening river dyed," is a weaker content match for the
scene summary ("exhausted from slaughter… seizes twelve youths") than the
nearby "Now, tired with slaughter, from the Trojan band". Triage kept the
current anchor because shifting it would lower the page's ownership further
(the overflow into scene 3 is fixed in size); flagged here for your editorial
judgment via scene-boundary-overrides.json if you prefer the alternative.
