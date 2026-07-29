# The Iliad's own topography: every passage that fixes a place relative to another

**Date:** 2026-07-29
**Consumed by:** the *schematic* plate (`trojan-plain-schematic`) and the 38 conjectural
`plateAnchors` of `TROY-MAPS-HANDOFF-2.md` §4.
**Register:** this dossier is the authority for the **schematic** sheet only. Nothing in it
licenses a coordinate. Where a claim below fixes A relative to B, it fixes an *ordering* or
an *adjacency* on the poem's own mental map — never a latitude.

**What this is not.** It is not site copy, and it is not a geographic gazetteer. Survey and
archaeology are handled by `TROAD-SOURCES.md`, `RESEARCH-PALEOGEOGRAPHY.md` and
`RESEARCH-BASEMAP-DATA.md`. Where this dossier names Strabo or Leaf on a *location*, that is
an `identification` claim about a tradition, tagged as such, and it belongs to the
`traditional` tier with the tradition named.

**Copyright.** Per CLAUDE.md, in-copyright scholarship is a legitimate SOURCE: cited
precisely, quoted briefly, never republished. Everything quoted at length below is public
domain in the US (Leaf 1902, Leaf 1912, Jones's Strabo as served by LacusCurtius). The
Cambridge commentaries could **not** be consulted — see §8.

---

## 1. How to read an entry

Every claim carries five things:

- **claim** — one sentence, stating what is fixed relative to what.
- **Homer** — book.line, with the Greek that carries the claim.
- **scholarship** — Chicago for books and articles; a hyperlink for web resources.
- **authority** — `geometry` (the claim constrains shape, order or distance) ·
  `identification` (the claim attaches a name to ground) · `prose` (the claim is a reading,
  useful for a note but not for a drawing).
- **verified how** — the actual check performed.

`geometry` claims may drive the anchor layout. `identification` claims may drive the tier
and the note. `prose` claims may drive the note only. **A drawing lane must not promote a
`prose` claim into a position.**

---

## 2. Method, and what "verified against the corpus" means here

Every Greek line quoted below was read out of the built corpus at
`app/public/data/iliad/book-NN.json` (a symlink to `build/dist`), which carries the patched
TLG vulgate text and is the project's authority on lineation. Two scripts were used, both in
this session's scratchpad and both trivial to re-derive:

- a line printer (`book.line` or `book.a-b` → the Greek lines);
- an accent- and case-insensitive grepper over all 24 books (NFD-strip, `ς`→`σ`), used for
  the exhaustive lemma sweeps reported in §7 (`Σκαι-`, `Δαρδανι-`, `φηγ-`, `ἐρινε-`,
  `σκοπι-`, `κρουν-`, `πλυν-`, `ἀμαξ-`, `θρωσμ-`, `περγαμ-`, `θυμβρ-`, `ἑλλησπ-`, `λιμεν-`,
  `ροιτ-`, `σιγει-`).

Where a secondary source gave a line number, that number was re-checked against the corpus
and **corrected where it drifted** — one such correction is recorded in §5.2 (Porter's
`νεῶν ὕπερ` at VII 448 is at **7.449**).

**Coverage is complete for the 38.** All 38 ids in handoff §4 are treated. Twelve have no
Homeric anchor of any kind; they are listed as such in §7.4, not silently dropped. Coverage
of the *poem* is not claimed complete: the sweeps above are exhaustive for the named lemmata,
but a topographic detail carried by no such lemma (e.g. an unnamed `ὄχθος`) could have been
missed. No sampling was done — every hit of every sweep was read.

---

## 3. The load-bearing frame

Six claims fix the whole sheet. Everything in §5–§6 hangs off them. If a drawing lane gets
only these right, the plate is honest.

### 3.1 Orientation: right and left are fixed, and they are the camp's right and left

- **claim** — The poem's `left`/`right` are constant throughout, and they are the left and
  right of an observer standing in the middle of the Achaean camp facing the Trojan plain.
  Every "left of the ships" therefore means the same end of the line every time.
- **Homer** — 12.118–19, where Asius drives at the ships' left because that is where the
  Achaeans came back off the plain with their teams:
  `εἴσατο γὰρ νηῶν ἐπ' ἀριστερά, τῇ περ Ἀχαιοὶ / ἐκ πεδίου νίσοντο σὺν ἵπποισιν καὶ ὄχεσφι`
  (12.118–19). The poem has **two** such formulas and they must be kept apart:
  `νηῶν ἐπ' ἀριστερά`, the ships' left (12.118, 13.675), and `μάχης ἐπ' ἀριστερά`, the
  battle's left (5.355, 11.498, 13.765, 17.116, 17.682). Hector's own question at 13.309,
  `ἦ ἐπ' ἀριστερόφιν;`, and Idomeneus's `νῶϊν δ' ὧδ' ἐπ' ἀριστέρ' ἔχε στρατοῦ` (13.326) show
  the army itself using the axis as a working direction. Complete sweep in §7.1.
- **scholarship** — Jenny Strauss Clay, *Homer's Trojan Theater: Space, Vision, and Memory in
  the Iliad* (Cambridge: Cambridge University Press, 2011). Consulted at second hand through
  J. Marks's review, [BMCR 2011.08.23](https://bmcr.brynmawr.edu/2011/2011.08.23), which
  states her thesis: the orientation of right and left "remains constant throughout and is
  always seen from the perspective of a narrator situated in the center of the Greek camp
  facing the Trojan plain." Clay's companion project put this on a drawn sheet: the
  now-defunct site says it provides "a schematic map in accordance with the *Iliad*'s
  orientation" with landmarks and the positions of the leading characters in Books 12, 13,
  15, 16 and 17 —
  [Wayback capture, 2011-07-17](https://web.archive.org/web/20110717014937/http://www.homerstrojantheater.org/).
- **authority** — `geometry` (and it is the single most consequential geometry claim in the
  dossier: it converts every `ἀριστερά` in the battle books into a position on our sheet).
- **verified how** — Greek checked against local corpus books 12 and 13; Clay's thesis
  consulted via the BMCR review (the monograph itself is in copyright and was not consulted —
  see §8); the companion site's own self-description read off the Wayback capture.
- **caution** — Clay's book, not the review, is the place where the thesis is argued from the
  text. Our plate may rely on the thesis and cite Clay; it must not attribute to Clay any
  *particular* placement we have not read in her.

### 3.2 The camp is a beach between two headlands, and it has depth

- **claim** — The ships fill a long shore-mouth closed at both ends by headlands; they stand
  in rows one behind another, not in a single line; the first-hauled ships were dragged
  *furthest inland*, and the wall was built at their **sterns**. The camp is therefore a
  block with front-to-back depth, not a ribbon.
- **Homer** — 14.30–36:
  `πολλὸν γάρ ῥ' ἀπάνευθε μάχης εἰρύατο νῆες / θῖν' ἔφ' ἁλὸς πολιῆς· τὰς γὰρ πρώτας πεδίον δὲ
  / εἴρυσαν, αὐτὰρ τεῖχος ἐπὶ πρύμνῃσιν ἔδειμαν` (14.30–32);
  `οὐδὲ γὰρ οὐδ' εὐρύς περ ἐὼν ἐδυνήσατο πάσας / αἰγιαλὸς νῆας χαδέειν` (14.33–34);
  `τώ ῥα προκρόσσας ἔρυσαν, καὶ πλῆσαν ἁπάσης / ἠϊόνος στόμα μακρόν, ὅσον συνεέργαθον ἄκραι`
  (14.35–36). Hauling method at 1.485–86:
  `νῆα μὲν οἵ γε μέλαιναν ἐπ' ἠπείροιο ἔρυσσαν / ὑψοῦ ἐπὶ ψαμάθοις, ὑπὸ δ' ἕρματα μακρὰ
  τάνυσσαν`.
- **scholarship** — Walter Leaf, ed., *The Iliad*, 2nd ed., 2 vols. (London: Macmillan,
  1900–1902), note on 14.35 (`προκρόσσας`): the word means "in rows or ranks, one behind
  another"; Aristarchus explained it as the ships hauled up the curving beach in tiers
  "ὥστε θεατροειδὲς φαίνεσθαι τὸ νεώλκιον" (so that the slipway looks like a theatre);
  Herodotus 7.188 uses `πρόκροσσαι` of ships moored in ranks eight deep. Leaf's note on
  15.409 adds that the huts are behind the first line of ships and that huts and ships most
  likely **alternate in rows**, each man's hut by his own ship.
  [archive.org, `iliadhom02home`](https://archive.org/details/iliadhom02home).
- **authority** — `geometry`.
- **verified how** — Greek checked against local corpus book 14 and book 1; Leaf's notes read
  in the full text of the 1902 scan (public domain).
- **note for the drawing lane** — 14.36 gives the schematic its frame: a shore-mouth closed
  at both ends. The Iliad does not name the headlands. Sigeion and Rhoiteion are Strabonic
  (§6), and a sweep of all 24 books for `σιγει-` and `ροιτ-` returns **zero** Homeric hits.

### 3.3 The order along the line: Ajax — … — Odysseus + agora + altars — … — Achilles

- **claim** — Odysseus's ship is in the middle of the line, so a shout from it carries both
  ways; Ajax son of Telamon and Achilles hold the two extremities. The assembly-ground and
  the place of judgement, with the gods' altars, are at Odysseus's ships — i.e. in the
  middle. **The poem does not say which extremity is left and which is right.**
- **Homer** — 8.222–26 = 11.5–9, verbatim:
  `στῆ δ' ἐπ' Ὀδυσσῆος μεγακήτεϊ νηῒ μελαίνῃ, / ἥ ῥ' ἐν μεσσάτῳ ἔσκε γεγωνέμεν ἀμφοτέρωσε, /
  ἠμὲν ἐπ' Αἴαντος κλισίας Τελαμωνιάδαο / ἠδ' ἐπ' Ἀχιλλῆος, τοί ῥ' ἔσχατα νῆας ἐΐσας /
  εἴρυσαν`. Agora and altars: 11.806–8,
  `ἀλλ' ὅτε δὴ κατὰ νῆας Ὀδυσσῆος θείοιο / ἷξε θέων Πάτροκλος, ἵνά σφ' ἀγορή τε θέμις τε /
  ἤην, τῇ δὴ καί σφι θεῶν ἐτετεύχατο βωμοί`.
- **scholarship** — Leaf, *Iliad* (1902), prints **8.224–26 in square brackets** — he
  athetizes the camp-order lines at Θ as borrowed from Λ — and on 11.1–55 notes that nearly
  half the opening consists of lines that appear elsewhere, so that "5–9 = Θ 222–6 (but here
  the lines are at home in Λ)." At 13.681 he calls the introduction to Λ "so late a passage."
  So Leaf accepts the order as the text's, while holding the passage that states it to be
  late. Our lineation never moves; recording the athetesis is apparatus, not renumbering.
- **authority** — `geometry` for the order; `prose` for Leaf's athetesis.
- **verified how** — Greek checked against local corpus books 8 and 11 (the two passages are
  character-identical apart from punctuation at 11.9); Leaf's brackets and notes read in the
  1900 and 1902 scans.
- **open, and John's alone if we ever want to state it** — which end is "left." A widely
  repeated reconstruction puts Ajax at the left (north-east, toward Rhoiteion) and Achilles
  at the right (south-west, toward Sigeion), on the ground that the right is the post of
  honour; it goes back to Jean Cuillandre, *La droite et la gauche dans les poèmes homériques*
  (Paris, 1943). **Not consulted — see §9.** The poem itself is silent, and the plate should
  keep it silent: label the ends `one extremity (Ajax)` and `the other extremity (Achilles)`
  and let the tier filter carry the honesty.

### 3.4 The wall, the ditch, and the gap between them

- **claim** — The Achaeans raise a single common tumulus over the dead out of the plain, and
  build the wall **against it**, with high towers, gates wide enough for a chariot road, and
  a broad deep ditch *outside* the wall, palisaded. There is a space between ditch and wall
  large enough for seven companies of a hundred men to camp and light fires. The ditch is
  steep-sided on both faces and impassable to a chariot.
- **Homer** — plan and execution, 7.336–43 and 7.435–41:
  `τύμβον δ' ἀμφ' αὐτὴν ἕνα ποίεον ἐξαγαγόντες / ἄκριτον ἐκ πεδίου, ποτὶ δ' αὐτὸν τεῖχος
  ἔδειμαν / πύργους θ' ὑψηλούς, εἶλαρ νηῶν τε καὶ αὐτῶν` (7.435–37);
  `ὄφρα δι' αὐτάων ἱππηλασίη ὁδὸς εἴη` (7.439);
  `ἔκτοσθεν δὲ βαθεῖαν ἐπ' αὐτῷ τάφρον ὄρυξαν / εὐρεῖαν μεγάλην, ἐν δὲ σκόλοπας κατέπηξαν`
  (7.440–41). Landward of the ships: `τεῖχος ἐτειχίσσαντο νεῶν ὕπερ, ἀμφὶ δὲ τάφρον / ἤλασαν`
  (7.449–50); repeated 12.5–6. The gap: `κὰδ δὲ μέσον τάφρου καὶ τείχεος ἷζον ἰόντες· / ἔνθα
  δὲ πῦρ κήαντο` (9.87–88). Ditch profile: `κρημνοὶ γὰρ ἐπηρεφέες περὶ πᾶσαν / ἕστασαν
  ἀμφοτέρωθεν, ὕπερθεν δὲ σκολόπεσσιν / ὀξέσιν ἠρήρει` (12.54–56), and
  `ἔνθ' οὔ κεν ῥέα ἵππος ἐΰτροχον ἅρμα τιταίνων / ἐσβαίη` (12.58–59). Apollo's causeway across
  it: `γεφύρωσεν δὲ κέλευθον / μακρὴν ἠδ' εὐρεῖαν, ὅσον τ' ἐπὶ δουρὸς ἐρωὴ / γίγνεται`
  (15.357–59) — a spear-cast wide.
- **scholarship** — James Porter, "Making and Unmaking: The Achaean Wall and the Limits of
  Fictionality in Homeric Criticism," *Classics@* 3, no. 1 (Center for Hellenic Studies),
  [open access](https://classics-at.chs.harvard.edu/classics3-james-porter-making-and-unmaking-the-achaean-wall-and-the-limits-of-fictionality-in-homeric-criticism/):
  collects the ancient criticism, including Aristotle fr. 162 Rose *apud* Strabo 13.1.36 —
  the poet who made the wall up (`ὁ πλάσας`) also made it vanish (`ἠφάνισεν`) — the athetesis
  of 7.443–64 by Aristarchus, Zenodotus and Aristophanes, and the point that some Aristarchean
  material in the scholia may derive from his treatise *On the Naval Station*
  (Περὶ τοῦ ναυστάθμου) rather than from his lemmatic commentaries. Leaf, *Iliad* (1900), note
  on 8.213, lays out the two possible geometries and refuses to choose (see §7.6, C-6).
- **authority** — `geometry` for the Homeric measurements and relations; `prose` for
  Aristotle/Aristarchus.
- **verified how** — every Greek line above checked against the local corpus (books 7, 9, 12,
  15); Porter's article read in full via the CHS open-access URL; his `νεῶν ὕπερ` line number
  (VII 448) corrected to **7.449** against the corpus.
- **note** — the wall stands on a barrow of Achaean dead. That is content for the schematic:
  the wall and the mass grave are the same feature.

### 3.5 The road: camp → ford → tomb of Ilos → mid-plain → gate

The poem walks this road three times in full, and it always has the same waypoints in the
same order. This is the spine of the schematic.

- **outbound (Priam, Book 24)** — out of Troy, past the great tomb of Ilos, halt at the river
  to water the animals, on to the ford, then the towers of the ships and the ditch, then
  Achilles' hut:
  `Οἳ δ' ἐπεὶ οὖν μέγα σῆμα παρὲξ Ἴλοιο ἔλασσαν, / στῆσαν ἄρ' ἡμιόνους τε καὶ ἵππους ὄφρα
  πίοιεν / ἐν ποταμῷ` (24.349–51); `ἀλλ' ὅτε δὴ πύργους τε νεῶν καὶ τάφρον ἵκοντο` (24.443);
  `ἀλλ' ὅτε δὴ κλισίην Πηληϊάδεω ἀφίκοντο` (24.448). Return: the ford again at 24.692–93.
- **inbound (the rout of Book 11)** — past the tomb of Ilos, through the middle of the plain,
  past the fig tree, up to the Scaean gates and the oak:
  `οἳ δὲ παρ' Ἴλου σῆμα παλαιοῦ Δαρδανίδαο / μέσσον κὰπ πεδίον παρ' ἐρινεὸν ἐσσεύοντο /
  ἱέμενοι πόλιος` (11.166–68); `ἀλλ' ὅτε δὴ Σκαιάς τε πύλας καὶ φηγὸν ἵκοντο` (11.170).
- **the wounded Hector (Book 14)** — carried toward the city, halted at the ford:
  `οἳ τόν γε προτὶ ἄστυ φέρον βαρέα στενάχοντα. / Ἀλλ' ὅτε δὴ πόρον ἷξον ἐϋρρεῖος ποταμοῖο /
  Ξάνθου δινήεντος` (14.432–34).
- **scholarship** — Leaf, *Troy: A Study in Homeric Geography* (London: Macmillan, 1912),
  35–40 (index s.v. "Ford of Scamander"), makes the observation that matters most for a
  drawing: in **none** of the three `πόρος` passages is the ford said to be *crossed*. Each
  time there is another reason for the halt — water for Hector, water for the animals. Leaf's
  reading: "The ford led across the river, from the plain to the ridge of hills by Sigeum: the
  road to the camp passed close by it, but did not actually cross it."
  [archive.org, `troyastudyinhom00leafgoog`](https://archive.org/details/troyastudyinhom00leafgoog).
- **authority** — `geometry` for the waypoint order; `identification` for Leaf's placement of
  the ford relative to a real ridge.
- **verified how** — Greek checked against local corpus books 11, 14, 24; Leaf 1912 read in
  the full public-domain scan, page range confirmed from the book's own index.

### 3.6 The divine grandstands are a matched pair, one on each side

- **claim** — When the gods take sides they sit in two facing places: the pro-Achaean gods on
  the heaped wall of Heracles, on the camp side, between the shore and the plain; the
  pro-Trojan gods on the brows of Callicolone, on the city side, by the Simoeis.
- **Homer** — 20.144–52:
  `τεῖχος ἐς ἀμφίχυτον Ἡρακλῆος θείοιο / ὑψηλόν, τό ῥά οἱ Τρῶες καὶ Παλλὰς Ἀθήνη / ποίεον,
  ὄφρα τὸ κῆτος ὑπεκπροφυγὼν ἀλέαιτο, / ὁππότε μιν σεύαιτο ἀπ' ἠϊόνος πεδίον δέ` (20.145–48);
  `οἳ δ' ἑτέρωσε καθῖζον ἐπ' ὀφρύσι Καλλικολώνης` (20.151). Callicolone by the Simoeis also at
  20.53, `ἄλλοτε πὰρ Σιμόεντι θέων ἐπὶ Καλλικολώνῃ`.
- **scholarship** — Leaf, *Troy* (1912), 43–44: the Wall of Heracles must be a genuinely
  *neutral* vantage between the armies, which is why Dörpfeld's placement of it on the point
  of Sigeion will not do — that would put it "to all intents and purposes in the Greek camp,
  from which the gods retire"; and Callicolone must answer it "in a corresponding position on
  the other or eastern side of the plain," on a hill with "brows," for which Leaf proposes the
  browy hills that gave Ophrynion its name. Strabo 13.1.35 puts Callicolone forty stades from
  Ilium and, quoting Demetrius of Scepsis, five stades from the Simoeis.
- **authority** — `geometry` for the pairing (the poem itself makes them a matched pair,
  `ἑκάτερθε`, 20.153); `identification` for Leaf's and Strabo's placements.
- **verified how** — Greek checked against local corpus book 20; Leaf read in the scan;
  Strabo's section number confirmed by anchor-mapping the LacusCurtius HTML of Jones's
  translation (see §6).
- **register note** — `wall-of-heracles` is tiered `mythical`. Per CLAUDE.md that is a
  category, not a warning: the poem states flatly that the Trojans and Athena built it, and it
  goes on the schematic with confidence, on the camp side, between shore and plain.

---

## 4. The plain's own coordinate system, in the poem's words

Four expressions do most of the work, and a drawing lane should know all four:

| expression | sense | Homer | note |
|---|---|---|---|
| `θῖν' ἔφ' ἁλὸς πολιῆς` / `ἠϊών` / `ἀκτή` / `αἰγιαλός` | the shore-line the camp sits on | 14.31, 14.36, 23.125, 14.34 | `αἰγιαλός` is the beach proper; `ἠϊόνος στόμα` its long mouth |
| `πεδίον` / `μέσσον πεδίον` | the plain, and its middle | 11.167, 11.172, 23.359 | the mid-plain is where the tomb of Ilos and the (first) fig tree stand |
| `θρωσμὸς πεδίοιο` | the rise of the plain — the Trojan bivouac | 10.160, 11.56, 20.3 | three times, always the Trojan position; 10.161 adds `ἄγχι νεῶν` |
| `ὑπὸ πτόλιν` / `τεῖχος ὕπο` / `προπάροιθε πόλιος` | the ground immediately under the walls | 11.181, 22.144, 2.811 | where the chase-route furniture sits: `σκοπιή`, `ἐρινεός`, `ἀμαξιτός`, the springs |

`θρωσμὸς πεδίοιο` is the most useful of the four and is absent from the gazetteer's
`trojan-camp` mentions. It should be added: three attestations, all positional, all Trojan.

Verified how: `θρωσμ-` swept across all 24 books of the local corpus — exactly three hits,
10.160, 11.56, 20.3. Leaf 1912, 41 (index s.v. "Throsmos") renders it "spring of the plain"
in the sense of a *rise*, and places it, following Dörpfeld, at the low rise where the huts
of Kum Köi stand.

---

## 5. The catalogue: the 38, in the order of handoff §4

Each entry gives the anchoring passages, the relation they fix, and what remains unfixed.
Where an entry says **NO HOMERIC ANCHOR**, the poem gives nothing positional and the anchor
must come from tradition (tier `traditional`, tradition named) or must not be placed at all.

### 5.1 `batieia`

- **claim** — A steep isolated mound in the plain, in front of the city, free-standing so that
  one can run right round it; it is the Trojan mustering-ground where the contingents separate.
- **Homer** — 2.811–15: `Ἔστι δέ τις προπάροιθε πόλιος αἰπεῖα κολώνη / ἐν πεδίῳ ἀπάνευθε
  περίδρομος ἔνθα καὶ ἔνθα, / τὴν ἤτοι ἄνδρες Βατίειαν κικλήσκουσιν, / ἀθάνατοι δέ τε σῆμα
  πολυσκάρθμοιο Μυρίνης· / ἔνθα τότε Τρῶές τε διέκριθεν ἠδ' ἐπίκουροι.`
- **fixes** — in the plain (`ἐν πεδίῳ`), in front of the city (`προπάροιθε πόλιος`), *away*
  from something (`ἀπάνευθε`), and isolated (`περίδρομος ἔνθα καὶ ἔνθα`). Not the mid-plain,
  not the wall: between them, on the city side.
- **scholarship** — Strabo 13.1.34 lists Batieia among the places "pointed out" on the Trojan
  plain in his own day, alongside Erineus, the tomb of Aesyetes and the monument of Ilus.
  Leaf 1912 does not give it a separate index entry.
- **authority** — `geometry` (Homer) · `identification` (Strabo, as a tradition of the guides).
- **verified how** — Greek checked against local corpus book 2; Strabo section number
  anchor-mapped in the LacusCurtius text.
- **unfixed** — which side of the road; distance from the wall.

### 5.2 `washing-troughs` and 5.3 `two-springs-of-scamander`

These are one place in the poem and must be anchored as one.

- **claim** — Two springs of the Scamander rise at the same spot, one steaming hot, one
  ice-cold; broad handsome stone washing-troughs stand beside them; the pair lies **on the
  chase-circuit round the city**, reached on the wagon-road out from under the wall, and
  passed a fourth time as the chase completes its laps.
- **Homer** — 22.147–56: `κρουνὼ δ' ἵκανον καλλιρρόω· ἔνθα δὲ πηγαὶ / δοιαὶ ἀναΐσσουσι
  Σκαμάνδρου δινήεντος. / ἣ μὲν γάρ θ' ὕδατι λιαρῷ ῥέει, ἀμφὶ δὲ καπνὸς / γίγνεται ἐξ αὐτῆς
  ὡς εἰ πυρὸς αἰθομένοιο· / ἣ δ' ἑτέρη θέρεϊ προρέει ἐϊκυῖα χαλάζῃ, / ἢ χιόνι ψυχρῇ ἢ ἐξ
  ὕδατος κρυστάλλῳ. / ἔνθα δ' ἐπ' αὐτάων πλυνοὶ εὐρέες ἐγγὺς ἔασι / καλοὶ λαΐνεοι, ὅθι
  εἵματα σιγαλόεντα / πλύνεσκον Τρώων ἄλοχοι καλαί τε θύγατρες / τὸ πρὶν ἐπ' εἰρήνης πρὶν
  ἐλθεῖν υἷας Ἀχαιῶν.` The circuit: `ὣς τὼ τρὶς Πριάμοιο πόλιν πέρι δινηθήτην` (22.165) and
  `ἀλλ' ὅτε δὴ τὸ τέταρτον ἐπὶ κρουνοὺς ἀφίκοντο` (22.208).
- **fixes** — this is the sharpest geometric constraint in the whole dossier, and the one most
  reconstructions quietly drop. The springs are **on a route that circles the walls**, not out
  in the plain: the runners reach them once per lap. Any anchor that puts them a mile off is
  contradicting 22.208.
- **scholarship** — Leaf, *Iliad* (1902), note on 22.147: `πηγαὶ Σκαμάνδρου` "must mean
  *sources* of Skamandros, not merely 'springs flowing into Skamandros'," and the only real
  pair of notably differing temperature is the source-pair under the summit of Ida, some
  twenty miles SE — measured at 34°/69° F by Clarke in 1801, 43°/70° by Parker Webb in 1819,
  8.4°/15.8° C by Virchow in 1879. Leaf, *Troy* (1912), 46–52: Lechevalier's Bunarbashi
  springs are not two but some thirty or forty ("the Forty Eyes"), and "thermometers are not
  enthusiastic" — all the same temperature; the warmest in the plain are in the Düden marsh by
  the Thymbra farm, with the nearest cold spring a mile away; Leaf's conclusion is that "the
  poet purposely introduced into his landscape a feature which did not exist." Strabo 13.1.43
  had already said it: "no hot waters are now to be found at the site," and the Scamander has
  one source, in the mountain, not two. Modern confirmation:
  [Wolkersdorfer, Stadler, et al., "Hydrochemical investigations to locate Homer's hot and
  cold springs of Troia (Troy)/Turkey," *Geochemistry* 80 (2020)](https://www.sciencedirect.com/science/article/abs/pii/S0341816220306202)
  (already in the gazetteer).
- **authority** — `geometry` (Homer: on the circuit) · `prose` (Leaf, Strabo, Wolkersdorfer:
  the feature is not on the ground).
- **verified how** — Greek checked against local corpus book 22; `κρουν-` and `πλυν-` swept
  across all 24 books (22.147, 22.208; 22.153, 22.155, plus the unrelated simile at 4.454);
  Leaf's commentary note and *Troy* pages read in the public-domain scans; Strabo 13.1.43
  anchor-mapped.
- **register** — put them on the schematic, on the circuit, and let the absence be content: a
  labelled feature with `speculative` and a note saying the ground has been searched for two
  millennia and does not have them. Never a coordinate.

### 5.4 `scaean-gate`

- **claim** — The gate the Achaean-facing traffic uses. Chariots drive out through it to the
  plain; the oak stands beside it; the great tower stands over it; the elders sit "at the
  Scaean gates," which the poem treats as the same thing as sitting "on the tower."
- **Homer** — full sweep of `Σκαι-` over 24 books gives 3.145, 3.149, 3.263, 6.237, 6.307,
  6.393, 9.354, 11.170, 16.712, 18.453, 22.6, 22.360. The load-bearing ones:
  `ἥατο δημογέροντες ἐπὶ Σκαιῇσι πύλῃσι` (3.149) with `τοῖοι ἄρα Τρώων ἡγήτορες ἧντ' ἐπὶ
  πύργῳ` (3.153); `τὼ δὲ διὰ Σκαιῶν πεδίον δ' ἔχον ὠκέας ἵππους` (3.263);
  `Σκαιάς, τῇ ἄρ' ἔμελλε διεξίμεναι πεδίον δέ` (6.393);
  `Ἕκτωρ δ' ὡς Σκαιάς τε πύλας καὶ φηγὸν ἵκανεν` (6.237), same pairing at 9.354 and 11.170.
- **fixes** — gate + oak + great tower are one complex, on the side that faces the plain and
  the ships.
- **scholarship** — Leaf, *Troy* (1912), 151–58 (index s.v.): the Scaean Gate "was flanked by
  a tower, the greatest in the fortress, for it is called 'the great tower of Ilios' (vi. 386).
  Both are regarded as a single work, for to sit 'at the Skaian gates' is equivalent to sitting
  'on the tower' (iii. 149, 153)." He adds that the etymology settles nothing — whether "the
  gate on the left" is left from the Trojan or the Achaean side cannot be decided, and Strabo
  cites the name among those suggesting a Thraco-Trojan link. Leaf also records Aristarchus's
  minority view that Homer's Troy had **one** gate, called either Scaean or Dardanian, and
  that 2.809 means "the gate was opened wide," not "all the gates were opened" — a reading
  Leaf rejects, holding for at least three gates.
- **authority** — `geometry` (the gate–oak–tower complex, and the plain-facing orientation) ·
  `prose` (Aristarchus's one-gate theory).
- **verified how** — `Σκαι-` swept across all 24 books of the local corpus; 2.809
  (`πᾶσαι δ' ὠΐγνυντο πύλαι`) checked; Leaf 1912 pages located from the book's own index and
  read in the scan.
- **John's alone** — the Scaean/Dardanian pairing to excavated gates VI U / VI T stays a human
  gate (handoff §6). Nothing here settles it.

### 5.5 `dardanian-gates`

- **claim** — A second gate, on the far side of the fortress from the ships. Before Achilles
  withdrew, the Trojans did not dare come out even by *this* gate. In the chase Hector tries
  repeatedly to dart at it under the well-built towers so his people can shoot over him, and
  Achilles heads him off toward the plain each time. Priam's impulse in Book 22 is to rush out
  of *this* gate.
- **Homer** — the full `Δαρδανι-` gate sweep is exactly three: 5.789, 22.194, 22.413.
  `οὐδέ ποτε Τρῶες πρὸ πυλάων Δαρδανιάων / οἴχνεσκον` (5.789–90);
  `ὁσσάκι δ' ὁρμήσειε πυλάων Δαρδανιάων / ἀντίον ἀΐξασθαι ἐϋδμήτους ὑπὸ πύργους, / εἴ πως οἷ
  καθύπερθεν ἀλάλκοιεν βελέεσσι, / τοσσάκι μιν προπάροιθεν ἀποστρέψασκε παραφθὰς / πρὸς πεδίον`
  (22.194–98); `ἐξελθεῖν μεμαῶτα πυλάων Δαρδανιάων` (22.413).
- **fixes** — a second gate, distinct from the Scaean, with towers over it, positioned so that
  reaching it means turning *away from the plain*.
- **scholarship** — Leaf, *Troy* (1912), 158–62 (index s.v.): on Dörpfeld's view the Dardanian
  Gate lies "at the back of the fortress, farthest from the Achaian camp, and best protected
  from observation," which gives 5.789 its force; but Leaf then finds the other two passages
  hard to square with it and says so — why should Hector aim at the *back* gate, and why should
  Priam, standing on the tower by the Scaean gate with gatekeepers at hand (21.530–36), want
  to leave by a gate on the other side and facing away from the sea? "The question seems to me
  unanswerable."
- **authority** — `geometry` (two gates, and 22.198's `πρὸς πεδίον` vector) · `prose` (Leaf's
  unresolved difficulty, which must be recorded, not smoothed).
- **verified how** — `Δαρδανι-` swept across all 24 books; 21.526–37 checked; Leaf read in the
  scan.

### 5.6 `great-tower-of-ilios`

- **claim** — The greatest tower of the fortress, over the Scaean gate; it projects from the
  wall line; it is the watch-place from which the plain and the fighting are seen. Helen goes
  up to it; Andromache runs to it; Priam stands on it; Hector sets his shield against it.
- **Homer** — `ἀλλ' ἐπὶ πύργον ἔβη μέγαν Ἰλίου` (6.386); elders on it, 3.153–54; Helen,
  3.384 (`πύργῳ ἐφ' ὑψηλῷ`); Andromache, 6.373, 6.431, 22.462–63; Priam,
  `Ἑστήκει δ' ὃ γέρων Πρίαμος θείου ἐπὶ πύργου` (21.526); Hector,
  `πύργῳ ἔπι προὔχοντι φαεινὴν ἀσπίδ' ἐρείσας` (22.97).
- **fixes** — vertically above the Scaean gate; `προὔχοντι` says it stands proud of the curtain.
  22.463–65 fixes its sightline: from the wall Andromache sees Hector dragged `πρόσθεν πόλιος`
  toward `κοίλας ἐπὶ νῆας Ἀχαιῶν` — so the tower looks down the whole road to the camp.
- **scholarship** — Leaf, *Troy* (1912), 151–58, treats gate and tower as one work (quoted at
  §5.4); he further argues from the ground that the only point giving an uninterrupted view of
  the plain, and so the only point where Hector could stand "in front of Ilios and the Scaean
  gate" (22.6), must be near the north-west angle of the fort.
- **authority** — `geometry` (tower over gate, projecting, with a sightline down the road) ·
  `identification` (Leaf's north-west angle).
- **verified how** — `πυργ-` swept across all 24 books of the local corpus (the sweep also
  returns the Achaean towers at 7.338, 7.437, 12.36 ff., and the Ajax-as-tower similes at
  7.219, 11.485 — none of them this place); Leaf read in the scan.

### 5.7 `oak-of-zeus`

- **claim** — An oak beside the Scaean gate, three times paired with it in a single formula;
  it belongs to Zeus; gods sit under it and on it; it is the marker of how far outside the wall
  Hector used to venture.
- **Homer** — `φηγ-` sweep over 24 books gives, for this place: 5.693 (`εἷσαν ὑπ' αἰγιόχοιο
  Διὸς περικαλλέϊ φηγῷ`), 6.237, 7.22 (`ἀλλήλοισι δὲ τώ γε συναντέσθην παρὰ φηγῷ`), 7.60
  (`φηγῷ ἐφ' ὑψηλῇ πατρὸς Διὸς αἰγιόχοιο`), 9.354, 11.170, 21.549 (`φηγῷ κεκλιμένος`). Excluded
  by inspection: 5.11 and 5.15 (Φηγεύς, a man), 5.838 (`φήγινος ἄξων`, an oaken axle), 16.767
  (oaks in a simile).
- **fixes** — adjacent to the Scaean gate, outside the wall, close enough that "as far as the
  Scaean gates and the oak" (9.354) is one short distance.
- **scholarship** — Strabo 13.1.35, arguing for the old settlement against present Ilium:
  "a little below Erineus is Phegus," in reference to Achilles' words at 9.352–54. That makes
  the ancient tradition place the oak *below* the fig-place, on the slope up to the city.
- **authority** — `geometry` (Homer: beside the gate) · `identification` (Strabo/Demetrius:
  below Erineus).
- **verified how** — `φηγ-` swept across all 24 books; each hit read and classified; Strabo
  13.1.35 anchor-mapped in the LacusCurtius text.

### 5.8 `fig-tree`

- **claim** — **There are two fig-tree claims in the poem and they do not agree.** See §7.6,
  C-1. Both must reach the plate.
- **Homer** — `ἐρινε-` sweep over 24 books gives exactly four: 6.433, 11.167, 21.37, 22.145.
  (a) close under the wall, at the weak point: `λαὸν δὲ στῆσον παρ' ἐρινεόν, ἔνθα μάλιστα /
  ἀμβατός ἐστι πόλις καὶ ἐπίδρομον ἔπλετο τεῖχος` (6.433–34); and on the chase-circuit,
  `οἳ δὲ παρὰ σκοπιὴν καὶ ἐρινεὸν ἠνεμόεντα / τείχεος αἰὲν ὑπ' ἐκ` (22.145–46).
  (b) in the middle of the plain, next to the tomb of Ilos: `οἳ δὲ παρ' Ἴλου σῆμα … / μέσσον
  κὰπ πεδίον παρ' ἐρινεὸν ἐσσεύοντο` (11.166–67). A fourth, unrelated: 21.37, a wild fig by
  the river whose shoots Lycaon was cutting for chariot rails.
- **scholarship** — Leaf, *Troy* (1912), 42, resolves it by positing **two** trees: the
  mid-plain landmark is "different of course from the other wild fig-tree which … grew close to
  the Skaian gate, under the wall of Troy." Strabo 13.1.35 takes a third route: `Ἐρινεός` is a
  *place-name*, "a place that is rugged and full of wild fig trees," lying at the foot of the
  ancient site, which is why Andromache's line suits the old settlement and not present Ilium.
  Leaf, *Iliad* (1902), note on 22.145, simply records the cross-references (Ζ 433, Λ 167)
  without resolving them.
- **authority** — `geometry` (two incompatible positions in Homer) · `identification` (Leaf's
  two trees; Strabo's fig-district).
- **verified how** — `ἐρινε-` swept across all 24 books, all four hits read; Leaf 1912 and Leaf
  1902 read in the scans; Strabo 13.1.35 anchor-mapped.
- **for the plate** — anchor **two** fig features, labelled, with the contradiction stated. Do
  not average them.

### 5.9 `lookout-skopie`

- **claim** — A lookout on the chase-circuit, named once, immediately before the windy fig-tree
  and the wagon-road, all three "ever out from under the wall."
- **Homer** — `οἳ δὲ παρὰ σκοπιὴν καὶ ἐρινεὸν ἠνεμόεντα / τείχεος αἰὲν ὑπ' ἐκ κατ' ἀμαξιτὸν
  ἐσσεύοντο` (22.145–46). The `σκοπι-` sweep over 24 books returns nothing else on the Trojan
  plain: 4.275 and 8.557/16.299 are similes; 5.771 is a man on a headland in a simile; 20.137
  is Hera proposing the gods withdraw `ἐκ πάτου ἐς σκοπιήν`; the rest are `ἀλαοσκοπιή` and
  `διασκοπιᾶσθαι` idioms.
- **fixes** — on the circuit, under the wall, next to the fig-tree.
- **scholarship** — Leaf, *Iliad* (1902), note on 22.145, is blunt: "Where the σκοπιή was we
  cannot say. It can hardly be, as the scholia think, the tomb of Aisyetes where Polites is
  posted as σκοπός in Β 793, for that must have been far from the wall."
- **authority** — `geometry` (adjacency to the fig-tree and the road) · `prose` (Leaf's
  refusal, and his rejection of the scholiasts' identification with the tomb of Aesyetes).
- **verified how** — `σκοπι-` swept across all 24 books, every hit read and classified; Leaf's
  note read in the 1902 scan.
- **important** — the scholiastic identification `σκοπιή` = tomb of Aesyetes is a live
  tradition and Leaf rejects it. If the plate ever shows them as one feature, it must say
  whose reading that is. Default: keep them separate.

### 5.10 `wagon-road`

- **claim** — A wagon-track (`ἀμαξιτός`, once only in the poem) running round the town a short
  way out from the wall, carrying the chase past the lookout, the fig-tree and the springs.
- **Homer** — `τείχεος αἰὲν ὑπ' ἐκ κατ' ἀμαξιτὸν ἐσσεύοντο` (22.146). The `ἀμαξ-` sweep over
  24 books gives no other road: 7.426, 12.448, 18.487 (the Wain), 18.563, and the Book 24
  mule-wagon are all something else.
- **fixes** — a *ring* road at a short offset from the wall, not a radial highway to the camp.
  This is the single most misdrawn feature on existing plates.
- **scholarship** — Leaf, *Iliad* (1902), note on 22.146: "The idea seems to be that a
  wagon-track ran round the town at a short distance from the wall, and that both keep away
  from under the wall in order to secure the better going of this road." He notes `ἀμαξιτός`
  does not recur in Homer, comparing *Od.* 10.103.
- **authority** — `geometry`.
- **verified how** — `ἀμαξ-` swept across all 24 books; Leaf's note read in full in the 1902
  scan.
- **for the plate** — the road that Priam drives (§3.5) and the `ἀμαξιτός` of 22.146 are **not
  the same object** on the evidence. One is a ring under the walls; the other is the route to
  the camp. Drawing them as one line is a claim the poem does not make. If the plate draws a
  radial road, label it "the road to the ships (inferred from the Book 24 waypoints)" and keep
  `ἀμαξιτός` as the ring.

### 5.11 `tomb-of-ilos`

- **claim** — An artificial barrow with a standing stone (`στήλη`) on it, in the middle of the
  plain, roughly halfway between ships and city, on the road, and near the river; the Trojan
  leaders hold council beside it, away from the din.
- **Homer** — four passages, all positional. `βουλὰς βουλεύει θείου παρὰ σήματι Ἴλου / νόσφιν
  ἀπὸ φλοίσβου` (10.415–16); `οἳ δὲ παρ' Ἴλου σῆμα παλαιοῦ Δαρδανίδαο / μέσσον κὰπ πεδίον`
  (11.166–67); `στήλῃ κεκλιμένος ἀνδροκμήτῳ ἐπὶ τύμβῳ / Ἴλου Δαρδανίδαο` (11.371–72);
  `Οἳ δ' ἐπεὶ οὖν μέγα σῆμα παρὲξ Ἴλοιο ἔλασσαν, / στῆσαν ἄρ' ἡμιόνους τε καὶ ἵππους ὄφρα
  πίοιεν / ἐν ποταμῷ` (24.349–51).
- **fixes** — mid-plain; on the road out of Troy; near enough to the river that Priam waters at
  the river immediately after passing it. `ἀνδροκμήτῳ` says the mound is man-made — the poem
  itself insists it is not a natural hillock.
- **scholarship** — Leaf, *Troy* (1912), 42: "Close to it, perhaps on it, must have stood the
  'Tomb of Ilos,' which we have twice found mentioned as a landmark near the ford … So that all
  is here consistent" — "it" being the rise (`θρωσμός`) he places at Kum Köi. Strabo 13.1.34
  lists the monument of Ilus among the sights shown on the plain in his day. Rose and Körpe's
  survey is the modern deflation of every such mound (already in the gazetteer): several of the
  traditional hero-tombs are Neolithic-to-Bronze-Age settlement mounds, and the real tumuli are
  largely Hellenistic and Roman.
- **authority** — `geometry` (Homer) · `identification` (Leaf, Strabo) · `prose` (Rose & Körpe).
- **verified how** — Greek checked against local corpus books 10, 11, 24; Leaf 1912 read in the
  scan; Strabo 13.1.34 anchor-mapped.

### 5.12 `tomb-of-aesyetes`

- **claim** — A barrow used as the Trojan watch-post; Polites sits on its very top to see when
  the Achaeans push out from their ships.
- **Homer** — 2.792–94: `ὃς Τρώων σκοπὸς ἷζε ποδωκείῃσι πεποιθὼς / τύμβῳ ἐπ' ἀκροτάτῳ
  Αἰσυήταο γέροντος, / δέγμενος ὁππότε ναῦφιν ἀφορμηθεῖεν Ἀχαιοί.`
- **fixes** — line of sight to the ships; and the watchman is chosen for *speed of foot*
  (`ποδωκείῃσι πεποιθώς`), which implies the post is far enough from the city that the warning
  has to be run in. That is a soft distance constraint, and it is the only one the poem gives.
- **scholarship** — Leaf, *Troy* (1912), 43: "We can hardly suppose him placed anywhere but
  just here, half way between the armies. There is room enough for two tumuli in this debatable
  land" — i.e. Leaf puts it beside the tomb of Ilos in the mid-plain. Strabo 13.1.34 lists it
  among the shown sights. Leaf, *Iliad* (1902) on 22.145, rejects the scholiasts' equation of
  this tomb with the `σκοπιή` (see §5.9).
- **authority** — `geometry` (sightline and the speed-of-foot inference) · `identification`
  (Leaf, Strabo).
- **verified how** — Greek checked against local corpus book 2; Leaf 1912 and 1902 read in the
  scans; Strabo 13.1.34 anchor-mapped.

### 5.13 `scamander-simoeis-confluence`

- **claim** — The two rivers join, and the join is the standard place for a divine arrival:
  Hera unyokes there.
- **Homer** — 5.773–74: `ἀλλ' ὅτε δὴ Τροίην ἷξον ποταμώ τε ῥέοντε, / ἧχι ῥοὰς Σιμόεις
  συμβάλλετον ἠδὲ Σκάμανδρος`. Also 6.4, `μεσσηγὺς Σιμόεντος ἰδὲ Ξάνθοιο ῥοάων` — the battle
  ranges *between* the two rivers, which is a second, independent constraint: the fighting
  ground lies in the interfluve.
- **fixes** — a junction, and an interfluve battlefield.
- **scholarship** — Leaf, *Troy* (1912), 37, states the problem plainly: "in this one passage
  the poet clearly conceives the two rivers as meeting close under Troy, and so cutting the
  city off from the camp. He thus stands in direct conflict not merely with the opening of
  xxi. …" — see §7.6, C-2. Strabo 13.1.34 has the ancient version: the Scamander and Simoeis
  "meet a little in front of the present Ilium, and then issue towards Sigeium and form
  Stomalimnê." Leaf, *Troy*, Appendix A (384–89), is the fullest PD treatment of the ancient
  evidence for the Scamander's course.
- **authority** — `geometry` (Homer) · `identification` (Strabo/Demetrius on where).
- **verified how** — Greek checked against local corpus books 5 and 6; Leaf 1912 read in the
  scan (page located from the running head); Strabo 13.1.34 anchor-mapped.

### 5.14 `ford-of-the-scamander`

- **claim** — A named crossing (`πόρος`) of the Xanthus, on the road between city and camp; the
  formula that names it is identical three times.
- **Homer** — `Ἀλλ' ὅτε δὴ πόρον ἷξον ἐϋρρεῖος ποταμοῖο / Ξάνθου δινήεντος, ὃν ἀθάνατος τέκετο
  Ζεύς` — 14.433–34, 21.1–2, 24.692–93, verbatim each time. At 21.3–4 it is where Achilles
  splits the rout: `ἔνθα διατμήξας τοὺς μὲν πεδίον δὲ δίωκε / πρὸς πόλιν`.
- **fixes** — on the road, between the tomb of Ilos and the camp gate (from the Book 24
  sequence, §3.5); and a place where a body of men in flight naturally divides — half to the
  plain, half into the water.
- **scholarship** — Leaf, *Troy* (1912), 35–40: the ford is never said to be crossed in any of
  the three passages; on his reading the road to the camp passed close by it without crossing
  it, and it is possible to go from town to camp "without crossing a river at all."
- **authority** — `geometry` (position in the waypoint order) · `prose` (Leaf's
  never-actually-crossed observation, which is a real constraint on how the road is drawn).
- **verified how** — the three formulaic passages checked line-for-line against the local corpus
  (books 14, 21, 24) and confirmed character-identical; Leaf 1912 read in the scan.

### 5.15 `achaean-camp`

Covered at §3.2 and §3.3. Additional anchoring passages:

- **the camp is on the Hellespont shore** — `λεῖα δ' ἐποίησεν παρ' ἀγάρροον Ἐλλήσποντον, /
  αὖτις δ' ἠϊόνα μεγάλην ψαμάθοισι κάλυψε` (12.30–31; the corpus prints smooth-breathing
  `Ἐλλήσποντον` here, its only smooth-breathing Hellespont — every other occurrence has
  `Ἑλλησπ-`), Poseidon smoothing the ground after the
  war; and the standing pairing "the ships and the Hellespont" as the thing a rout runs for:
  15.233, 18.150, 23.2. `ἑλλησπ-` sweep over 24 books: 2.845, 7.86, 9.360, 12.30, 15.233,
  17.432, 18.150, 23.2, 24.346, 24.545.
- **the huts sit among the ships** — `αὐτοὶ δ' ἐσκίδναντο κατὰ κλισίας τε νέας τε` (1.487); the
  formula for moving through the camp is `παρά τε κλισίας καὶ νῆας Ἀχαιῶν` (8.220, 11.617).
- **no harbour is named** — the `λιμεν-` sweep over 24 books returns no Trojan harbour: 1.432
  is Chryse, 21.23 is a simile (fish crowding into the recesses of a good anchorage), 23.745 is
  Lemnos. **The Iliad gives the Achaeans a beach, not a port.** That is a labelled absence, and
  it matters, because the geoarchaeological literature is looking for harbours.
- **authority** — `geometry`.
- **verified how** — `ἑλλησπ-` and `λιμεν-` swept across all 24 books of the local corpus, every
  hit read and classified; the quoted lines checked in books 1, 8, 11, 12.

### 5.16 `achaean-wall-and-ditch`

Covered at §3.4. Additional:

- **the wagon gate is at the left** — 12.118–19 (quoted at §3.1). The gates are plural (7.438)
  and made for a chariot road (7.439).
- **the wall is lowest at one point** — `αὐτὰρ ὕπερθε / τεῖχος ἐδέδμητο χθαμαλώτατον, ἔνθα
  μάλιστα / ζαχρηεῖς γίγνοντο μάχῃ αὐτοί τε καὶ ἵπποι` (13.682–84) — the low point is where
  Ajax's and Protesilaus's ships are. See §7.6, C-3.
- **the poem provides for its own erasure** — 12.13–33: Poseidon and Apollo turn eight Idaean
  rivers against it for nine days, Zeus rains, and the shore is covered in sand again.
- **scholarship** — Porter (§3.4). Leaf, *Iliad* (1900), note on 12.175–81, records that the
  ancient critics unanimously rejected those lines as an addition meant to distinguish Asius's
  gate from Hector's, and that Aristarchus argued in *On the Naval Camp* for a single gate, on
  the left — "such an arrangement would be absurd," Leaf replies, since 13.312 and 13.679 show
  Hector attacking in the centre.
- **authority** — `geometry` · `prose` (the ancient criticism).
- **verified how** — Greek checked against local corpus books 7, 9, 12, 13, 15; Leaf's notes on
  12.112–24 and 12.175–81 read in the 1900 scan; Porter read via CHS.

### 5.17 `achaean-assembly-place`

- **claim** — Two independent anchors, and they agree. (a) The assembly-ground with the place of
  judgement and the gods' altars is at Odysseus's ships — the middle of the line. (b) The host
  walks from the ships and huts out **in front of the deep shore** to reach the assembly. The
  assembly is therefore on open ground on the landward side of the hut-and-ship block, at the
  centre.
- **Homer** — (a) 11.806–8 (quoted at §3.3). (b) `ὣς τῶν ἔθνεα πολλὰ νεῶν ἄπο καὶ κλισιάων /
  ἠϊόνος προπάροιθε βαθείης ἐστιχόωντο / ἰλαδὸν εἰς ἀγορήν` (2.91–93). A third term for the
  same ground: `νεῶν ἐν ἀγῶνι` (15.428, 16.239, 16.500, 19.42, 20.33), "the gathering-place of
  the ships."
- **fixes** — centre of the line, landward of the huts.
- **authority** — `geometry`.
- **verified how** — Greek checked against local corpus books 2, 11; `ἀγων-` swept across all
  24 books and every hit read (the Book 23 hits are the funeral-games ring, §5.29; 7.298 and
  18.376 are `θεῖος ἀγών`, unrelated).

### 5.18 `hut-of-odysseus`

- **claim** — In the middle of the line, at the ship from which a shout reaches both ends; the
  assembly and the altars are at it.
- **Homer** — 8.222–23 = 11.5–6; 11.806–8. Odysseus goes to his hut for his shield at 10.148.
- **authority** — `geometry`.
- **verified how** — Greek checked against local corpus books 8, 10, 11.

### 5.19 `hut-of-ajax`

- **claim** — At one extremity of the line (`ἔσχατα`), the ships hauled up there by men who
  trusted their own courage and strength of hand. **Which** extremity is not stated.
- **Homer** — 8.224–26 = 11.7–9. Also 13.681, where Ajax's ships and Protesilaus's are together
  at the point where the wall was lowest — which conflicts with `ἔσχατα` (§7.6, C-3).
- **authority** — `geometry`.
- **verified how** — Greek checked against local corpus books 8, 11, 13.

### 5.20 `hut-of-achilles`

- **claim** — At the other extremity. It is the largest structure named in the camp: high,
  built by the Myrmidons of hewn fir with a thatched roof, inside a great palisaded courtyard,
  with a door-bar three men were needed to shift. There is an inner recess (`μυχῷ κλισίης`).
  Priam's route reaches it directly after the camp gate — so it is close to the perimeter, not
  buried in the middle.
- **Homer** — 24.448–56: `ἀλλ' ὅτε δὴ κλισίην Πηληϊάδεω ἀφίκοντο / ὑψηλήν, τὴν Μυρμιδόνες
  ποίησαν ἄνακτι / δοῦρ' ἐλάτης κέρσαντες· ἀτὰρ καθύπερθεν ἔρεψαν / λαχνήεντ' ὄροφον
  λειμωνόθεν ἀμήσαντες· / ἀμφὶ δέ οἱ μεγάλην αὐλὴν ποίησαν ἄνακτι / σταυροῖσιν πυκινοῖσι`;
  the inner room, `Ἀχιλλεὺς εὗδε μυχῷ κλισίης εὐπήκτου` (9.663). The embassy walks to it along
  the shore: `Τὼ δὲ βάτην παρὰ θῖνα πολυφλοίσβοιο θαλάσσης … / Μυρμιδόνων δ' ἐπί τε κλισίας
  καὶ νῆας ἱκέσθην` (9.182–85).
- **fixes** — an extremity; a walled compound with a courtyard, drawable as a block rather than
  a dot; reached along the shore from Agamemnon's hut; and adjacent to the camp gate on Priam's
  route (24.443–48).
- **authority** — `geometry`.
- **verified how** — Greek checked against local corpus books 9 and 24.

### 5.21 `hut-of-agamemnon`

- **claim** — The command post: councils, embassies and reconciliations happen there, and the
  route from it to Achilles' hut runs along the shore. Its position in the line is **never
  stated**. Everything the poem gives is functional, not positional.
- **Homer** — 2.9 (`ἐλθὼν ἐς κλισίην Ἀγαμέμνονος Ἀτρεΐδαο`), 9.178, 9.669, 19.241, 23.38; the
  shore walk at 9.182. Note that the council of elders in Book 2 sits **at Nestor's ship**
  (2.53–54), not at Agamemnon's — so the two are close.
- **fixes** — adjacent to Nestor's ship; on the shore; nothing more.
- **authority** — `geometry` (the Nestor adjacency) · `prose` (the rest).
- **verified how** — Greek checked against local corpus books 2, 9, 19, 23.
- **honest position** — anchor it beside Nestor near the centre and say in the note that the
  poem does not place it. Do not invent a "flagship at the middle."

### 5.22 `hut-of-nestor`

- **claim** — Beside his own black ship; the council of elders sits at that ship; Machaon is
  brought there; Nestor is found lying by hut and ship with his gear beside him.
- **Homer** — `Βουλὴν δὲ πρῶτον μεγαθύμων ἷζε γερόντων / Νεστορέῃ παρὰ νηῒ Πυλοιγενέος
  βασιλῆος` (2.53–54); `τὸν δ' εὗρεν παρά τε κλισίῃ καὶ νηῒ μελαίνῃ` (10.74);
  `Οἳ δ' ὅτε δὴ κλισίην Νηληϊάδεω ἀφίκοντο` (11.618).
- **fixes** — hut beside ship (which is the general rule Leaf infers for the whole camp, §3.2);
  in the council quarter, near Agamemnon.
- **authority** — `geometry`.
- **verified how** — Greek checked against local corpus books 2, 10, 11.

### 5.23 `tomb-of-achilles-and-patroclus`

- **claim** — Planned by Achilles **on the shore**, at the spot where the timber for the pyre
  was stacked: one mound for Patroclus now, to be built up broad and high later, over both.
- **Homer** — `κὰδ δ' ἄρ' ἐπ' ἀκτῆς βάλλον ἐπισχερώ, ἔνθ' ἄρ' Ἀχιλλεὺς / φράσσατο Πατρόκλῳ
  μέγα ἠρίον ἠδὲ οἷ αὐτῷ` (23.125–26); `τύμβον δ' οὐ μάλα πολλὸν ἐγὼ πονέεσθαι ἄνωγα, / ἀλλ'
  ἐπιεικέα τοῖον· ἔπειτα δὲ καὶ τὸν Ἀχαιοὶ / εὐρύν θ' ὑψηλόν τε τιθήμεναι` (23.245–47);
  the mound made, `τορνώσαντο δὲ σῆμα θεμείλιά τε προβάλοντο / ἀμφὶ πυρήν· εἶθαρ δὲ χυτὴν ἐπὶ
  γαῖαν ἔχευαν` (23.255–56). Compare 7.86, Hector's offer of `σῆμά τέ οἱ χεύωσιν ἐπὶ πλατεῖ
  Ἑλλησπόντῳ` — the Homeric idiom puts hero-mounds on the Hellespont shore.
- **fixes** — on the shore (`ἀκτή`), at the Myrmidon end of the line — i.e. adjacent to
  `hut-of-achilles`, at one extremity. The mound is circled out (`τορνώσαντο`) with a founded
  kerb: a ring, drawable as such.
- **scholarship** — Strabo 13.1.32: a temple and monument of Achilles near Sigeium, with
  monuments of Patroclus and Antilochus, all receiving Ilian sacrifice. `TROAD-SOURCES.md`
  §B has the modern deflation: every "tomb of Achilles" on the Troad is a cult identification,
  not a burial; Kesik Tepe near Sigeion is the mound that was *regarded* as his in the 4th
  century.
- **authority** — `geometry` (Homer) · `identification` (Strabo, and it is a cult tradition,
  never `certain`).
- **verified how** — Greek checked against local corpus books 7 and 23; Strabo 13.1.32
  anchor-mapped.

### 5.24 `tomb-of-hector`

- **claim** — A grave dug, roofed with big close-set stones, and a mound heaped over it —
  **with lookouts posted all round in case the Achaeans attacked before the rite was done.**
  The guard implies the tomb is outside the walls, within reach of a sally.
- **Homer** — 24.797–801: `αἶψα δ' ἄρ' ἐς κοίλην κάπετον θέσαν, αὐτὰρ ὕπερθε / πυκνοῖσιν
  λάεσσι κατεστόρεσαν μεγάλοισι· / ῥίμφα δὲ σῆμ' ἔχεαν, περὶ δὲ σκοποὶ ἥατο πάντῃ, / μὴ πρὶν
  ἐφορμηθεῖεν ἐϋκνήμιδες Ἀχαιοί.` The pyre: wood brought into the town (`ἄξετε νῦν Τρῶες ξύλα
  ἄστυ δέ`, 24.778) but the people muster `πρὸ ἄστεος` (24.783), and after the burial they
  feast in Priam's house (24.802–3).
- **fixes** — outside the city but close to it, on the side a raid would come from — i.e.
  between the walls and the plain. **This is an inference from the guard, not a statement.**
  Mark it as an inference on the plate.
- **scholarship** — Strabo 13.1.29 records the cult site: near Ophrynium, "in a conspicuous
  place, is the sacred precinct of Hector." That is the Troad tradition and it is nowhere near
  the Homeric scene — a good example of a `traditional` identification that must name its
  tradition and must not be conflated with the poem's tomb.
- **authority** — `geometry` (weak — the guard inference) · `identification` (Strabo, the
  Ophrynium precinct, a separate place).
- **verified how** — Greek checked against local corpus book 24; Strabo 13.1.29 anchor-mapped.

### 5.25 `kesik-basin` — **NO HOMERIC ANCHOR**

The poem names no basin, no dockyard, no cut. `λιμεν-` sweep: nothing at Troy (§5.15). This is
a modern hypothesis about excavated ground (Zangger; Jablonka and Kayan) and belongs to the
geographic register with a coordinate, or to nothing. It must not receive a schematic anchor,
because there is no poem-logic position to give it. See `TROAD-SOURCES.md` §A, which already
flags it as contested and thinly evidenced.

### 5.26 `trojan-camp`

- **claim** — Three anchors, mutually consistent. (a) Hector holds the Trojan assembly away
  from the ships, by the river, in a clear space among the corpses. (b) The Trojans bivouac on
  the rise of the plain (`θρωσμὸς πεδίοιο`), *near the ships*, with only a little ground left
  between. (c) Their thousand fires burn on the plain **between the ships and the streams of
  Xanthus, in front of Ilios**.
- **Homer** — (a) `Τρώων αὖτ' ἀγορὴν ποιήσατο φαίδιμος Ἕκτωρ / νόσφι νεῶν ἀγαγὼν ποταμῷ ἔπι
  δινήεντι, / ἐν καθαρῷ ὅθι δὴ νεκύων διεφαίνετο χῶρος` (8.489–91). (b)
  `οὐκ ἀΐεις ὡς Τρῶες ἐπὶ θρωσμῷ πεδίοιο / εἵαται ἄγχι νεῶν, ὀλίγος δ' ἔτι χῶρος ἐρύκει;`
  (10.160–61); same phrase 11.56, 20.3. (c) `τόσσα μεσηγὺ νεῶν ἠδὲ Ξάνθοιο ῥοάων / Τρώων
  καιόντων πυρὰ φαίνετο Ἰλιόθι πρό. / χίλι' ἄρ' ἐν πεδίῳ πυρὰ καίετο, πὰρ δὲ ἑκάστῳ / εἴατο
  πεντήκοντα` (8.560–63). Also 8.553, `ἐπὶ πτολέμοιο γεφύρας`. Council beside the tomb of Ilos:
  10.415.
- **fixes** — a band on the plain between the Achaean ditch and the Scamander, on the rise, in
  front of Troy, with the command post at the tomb of Ilos. That is a *region*, not a dot, and
  should be anchored as one.
- **scholarship** — Leaf, *Troy* (1912), 41–42, places the `θρωσμός` at the low rise of Kum
  Köi, "just in the narrow space between" the streams, following Dörpfeld, and notes the drop
  there conceals a rider from anyone on Hisarlık.
- **authority** — `geometry` (Homer) · `identification` (Leaf/Dörpfeld).
- **verified how** — Greek checked against local corpus books 8, 10, 11, 20; `θρωσμ-` swept
  across all 24 books (three hits, all cited); Leaf 1912 read in the scan.
- **gazetteer fix** — `trojan-camp` currently cites only 8.489–565. Add 10.160–61, 11.56, 20.3.

### 5.27 `thracian-camp`

- **claim** — The Thracians are newcomers, camped **apart, at the outermost point of all**;
  their gear is laid out in three rows with paired horses beside each man, and Rhesus sleeps in
  the middle. Dolon's survey of the allied camps orders them: seafront (`πρὸς ἁλός`) — Carians,
  Paeonians, Leleges, Caucones, Pelasgi; toward Thymbre — Lycians, Mysians, Phrygians,
  Maeonians.
- **Homer** — `Θρήϊκες οἷδ' ἀπάνευθε νεήλυδες ἔσχατοι ἄλλων· / ἐν δέ σφιν Ῥῆσος βασιλεὺς`
  (10.434–35); `ἔντεα δέ σφιν / καλὰ παρ' αὐτοῖσι χθονὶ κέκλιτο εὖ κατὰ κόσμον / τριστοιχί·
  παρὰ δέ σφιν ἑκάστῳ δίζυγες ἵπποι. / Ῥῆσος δ' ἐν μέσῳ εὗδε` (10.471–74); the allied order,
  `πρὸς μὲν ἁλὸς Κᾶρες καὶ Παίονες ἀγκυλότοξοι / … / πρὸς Θύμβρης δ' ἔλαχον Λύκιοι Μυσοί τ'
  ἀγέρωχοι` (10.428–31). Odysseus's tamarisk marker on the way out:
  `θῆκεν ἀνὰ μυρίκην· δέελον δ' ἐπὶ σῆμά τ' ἔθηκε` (10.466).
- **fixes** — this is the richest camp geometry in the poem and it is almost entirely unused.
  It gives an **axis**: sea at one end, Thymbre at the other, with the allied contingents
  ordered along it and the Thracians beyond the far end. That is exactly a schematic diagram.
  Plus an internal plan for the Thracian bivouac: three rows, horses paired, king centred.
- **authority** — `geometry`.
- **verified how** — Greek checked against local corpus book 10; `θυμβρ-` swept across all 24
  books — two hits, 10.430 (the place) and 11.320 (Θυμβραῖος, a man).
- **for the plate** — draw the 10.428–31 axis as an ordered band of allied contingents. It
  converts a coordless region into a legible diagram, and it is entirely in the poem.

### 5.28 `pyre-of-patroclus`

- **claim** — A hundred feet square, on the shore, at the spot marked for the joint mound; the
  timber for it was cut on the spurs of Ida and hauled down.
- **Homer** — `ποίησαν δὲ πυρὴν ἑκατόμπεδον ἔνθα καὶ ἔνθα` (23.164); the shore siting,
  23.125–26 (quoted at §5.23); the timber, `ἀλλ' ὅτε δὴ κνημοὺς προσέβαν πολυπίδακος Ἴδης, /
  αὐτίκ' ἄρα δρῦς ὑψικόμους ταναήκεϊ χαλκῷ / τάμνον` (23.117–19).
- **fixes** — a **measured** square, on the shore, coincident with the tomb. `ἑκατόμπεδον ἔνθα
  καὶ ἔνθα` is one of only two numeric dimensions the poem gives for any structure on the plain
  (the other is 15.358's spear-cast causeway). Use it: the pyre itself can be drawn or
  annotated at its cited size — a dimension label on the one measured feature, NOT a sheet
  scale bar; the schematic carries no scale bar (§7.5, §10).
- **authority** — `geometry`.
- **verified how** — Greek checked against local corpus book 23.

### 5.29 `funeral-games-ground`

- **claim** — Achilles keeps the host **on the spot** — at the new mound — and seats them in a
  wide ring; the prizes are carried out of the ships. The chariot course runs out into the
  plain to a turn-post Achilles fixes far off, on level ground, with Phoenix stationed there as
  umpire; the turn-post is a dry stump about a fathom high with two white stones set either side
  of it at a road-junction, and the poem says it may be somebody's old grave-marker.
- **Homer** — `χεύαντες δὲ τὸ σῆμα πάλιν κίον. αὐτὰρ Ἀχιλλεὺς / αὐτοῦ λαὸν ἔρυκε καὶ ἵζανεν
  εὐρὺν ἀγῶνα, / νηῶν δ' ἔκφερ' ἄεθλα` (23.257–59); `στὰν δὲ μεταστοιχί, σήμηνε δὲ τέρματ'
  Ἀχιλλεὺς / τηλόθεν ἐν λείῳ πεδίῳ· παρὰ δὲ σκοπὸν εἷσεν / ἀντίθεον Φοίνικα` (23.358–60); the
  post, `ἕστηκε ξύλον αὖον ὅσον τ' ὄργυι' ὑπὲρ αἴης / ἢ δρυὸς ἢ πεύκης· … / λᾶε δὲ τοῦ
  ἑκάτερθεν ἐρηρέδαται δύο λευκὼ / ἐν ξυνοχῇσιν ὁδοῦ, λεῖος δ' ἱππόδρομος ἀμφὶς / ἤ τευ σῆμα
  βροτοῖο πάλαι κατατεθνηῶτος` (23.327–31).
- **fixes** — a ring at the mound on the shore; a **radial course** out into the level plain to
  a marked turn far off, at a road-junction. This is a second road on the plain, distinct from
  both the `ἀμαξιτός` and the camp road, and the poem says so (`ἐν ξυνοχῇσιν ὁδοῦ`).
- **authority** — `geometry`.
- **verified how** — Greek checked against local corpus book 23.

### 5.30 `thymbra`

- **claim** — Named once, as a direction: the Lycians, Mysians, Phrygians and Maeonians drew
  the lot "toward Thymbre." In the poem it is a bearing, not a settlement.
- **Homer** — `πρὸς Θύμβρης δ' ἔλαχον Λύκιοι Μυσοί τ' ἀγέρωχοι` (10.430). The `θυμβρ-` sweep
  over 24 books returns only this and 11.320 (a man's name).
- **scholarship** — Strabo 13.1.35: the plain of Thymbra is near the ancient settlement, as is
  the Thymbrius river, which flows through the plain and empties into the Scamander at the
  temple of Thymbraean Apollo; Thymbra is fifty stades from present Ilium. `TROAD-SOURCES.md`
  §E already recommends treating it as a district anchored to the Thymbrios–Scamander
  confluence, not a dot, given Pleiades 550927's own rough-rectangle caveat.
- **authority** — `geometry` (Homer: a bearing, paired against `πρὸς ἁλός`) ·
  `identification` (Strabo, and the tradition must be named).
- **verified how** — `θυμβρ-` swept across all 24 books; Strabo 13.1.35 anchor-mapped.
- **for the plate** — its Homeric anchor is not a point but the **far end of the 10.428–31
  axis**. Anchor it there and label it a direction.

### 5.31 `troy-lower-city` — **NO DIRECT HOMERIC ANCHOR**

The poem has no term for a lower city. What it has is a *distinction*: Pergamos and the
`πόλις ἄκρη` on the one hand, the `ἄστυ` on the other.

- **Homer** — `περγαμ-` sweep over 24 books: 4.508, 5.446, 5.460 (`ἐφέζετο Περγάμῳ ἄκρῃ`),
  6.512 (`κατὰ Περγάμου ἄκρης`), 7.21, 24.700. Paris's house `ἐγγύθι τε Πριάμοιο καὶ Ἕκτορος
  ἐν πόλει ἄκρῃ` (6.317) — the three principal houses are on the acropolis, which implies
  something that is not. Ares shouts `κατ' ἀκροτάτης πόλιος` (20.52). And the wall has a stretch
  that is scalable and run-alongside: `ἔνθα μάλιστα / ἀμβατός ἐστι πόλις καὶ ἐπίδρομον ἔπλετο
  τεῖχος` (6.433–34).
- **authority** — `prose`. This is an inference from a contrast, and it must not be promoted
  into an anchored area.
- **verified how** — `περγαμ-` and `ακροπολ-` swept across all 24 books; the quoted lines
  checked in books 6 and 20.
- **scholarship** — the lower city is an archaeological question, not a Homeric one: Kolb
  against Korfmann, with Jablonka and Rose replying, both AJA 2004 and both open access (links
  in `TROAD-SOURCES.md` §D). If the plate draws a lower-city circuit, the caption must say
  whose reconstruction it is.

### 5.32 `tomb-of-ajax-in-tepe` — **NO HOMERIC ANCHOR**

Ajax does not die in the *Iliad*. There is no Homeric tomb. Strabo 13.1.30 gives the tradition:
adjacent to Rhoeteium, on a low-lying shore, "a tomb and temple of Aias, and also a statue of
him," taken to Egypt by Antony and returned by Augustus. That is the whole basis, and it is a
cult site of the Roman period. Tier `traditional`, tradition named as Strabonic/Rhoeteian cult;
no schematic anchor, because the poem has no place for it. (`TROAD-SOURCES.md` also carries a
warning about the Vici.org point for this record.)

### 5.33 `thymbrios` — **NO HOMERIC ANCHOR**

The river is not in the *Iliad*: the `θυμβρ-` sweep gives only 10.430 (Θύμβρη) and 11.320 (a
man). Strabo 13.1.35 names the Thymbrius and states its confluence with the Scamander at the
temple of Thymbraean Apollo. Tier `traditional`, tradition named as Demetrian/Strabonic; it can
be drawn as a watercourse on the geographic sheet from real hydrology (Kemer Su), never as a
poem-logic anchor.

### 5.34 `scamandrian-plain`

- **claim** — The plain is named for the Scamander, twice in five lines, and it is where the
  Achaean host pours out from the ships and huts to muster; it is a flowery meadow.
- **Homer** — `ὣς τῶν ἔθνεα πολλὰ νεῶν ἄπο καὶ κλισιάων / ἐς πεδίον προχέοντο Σκαμάνδριον`
  (2.464–65); `ἔσταν δ' ἐν λειμῶνι Σκαμανδρίῳ ἀνθεμόεντι / μυρίοι` (2.467–68).
- **fixes** — everything between the camp and the city. It is the *ground*, not a place: the
  whole schematic sheet is the Scamandrian plain, which is exactly why it drives 125 Chart Room
  scenes and why a pin for it is meaningless.
- **scholarship** — Strabo 13.1.34, quoting Demetrius: the spurs enclose both the Simoeisian
  Plain and the Scamandrian Plain, "and this is called the Trojan Plain in the special sense of
  the term; and here it is that the poet represents most of the fights as taking place, for it
  is wider."
- **authority** — `geometry` (Homer) · `identification` (Strabo/Demetrius).
- **verified how** — Greek checked against local corpus book 2; Strabo 13.1.34 anchor-mapped.
- **for the Chart Room** — `scamandrian-plain` should resolve to **the whole schematic sheet
  unzoomed**, not to an anchor. That is the honest camera for it, and it is not a defect.

### 5.35 `bay-of-troy` — **NO HOMERIC ANCHOR**

The poem gives the Achaeans a beach on the Hellespont and no harbour (§5.15). "Bay of Troy" is
a geoarchaeological term (Kayan's "Troian Bay"), not a Homeric one. Geographic register only,
with a coordinate or a polygon from `RESEARCH-PALEOGEOGRAPHY.md`. It is currently tiered
`certain` with no coords, which is the §3.8 gap: it wants geometry, not an anchor.

### 5.36 `uvecik-tepe` — **NO HOMERIC ANCHOR**

A surveyed Roman tumulus (the tomb of Festus, per `TROAD-SOURCES.md` §B). Coordinates, not an
anchor. Same §3.8 gap.

### 5.37 `besik-bay` — **NO HOMERIC ANCHOR**

Excavated Bronze Age site (Korfmann 1982–87). Coordinates, not an anchor. Same §3.8 gap.

### 5.38 `wall-of-heracles`

Covered at §3.6. Tier `mythical`, drawn with confidence on the camp side, between the shore and
the plain, facing Callicolone.

---

## 6. The ancient tradition, in one place

Every `traditional` tier on this plate traces to Demetrius of Scepsis as transmitted by Strabo
13.1. Section numbers below were established by mapping the section anchors in the HTML of
Bill Thayer's LacusCurtius edition of H. L. Jones's translation and reading the mapped text —
so each is a verified section number, not a remembered one.
[LacusCurtius, Strabo 13.1.28–45](https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Strabo/13A2*.html).

| § | what it says | which of our records it bears on |
|---|---|---|
| 13.1.29 | Ophrynium, and near it, in a conspicuous place, the sacred precinct of Hector | `tomb-of-hector` (a *separate*, later cult site) |
| 13.1.30 | Rhoeteium, and on the low shore beside it a tomb and temple of Aias with his statue | `tomb-of-ajax-in-tepe` |
| 13.1.31 | Coastwise order: Rhoeteium → Sigeium → the Naval Station → the Harbour of the Achaeans → the Achaean Camp → Stomalimnê → the outlets of the Scamander; the two rivers meet in the plain and silt the coast into a blind mouth, lagoons and marshes | `achaean-camp`, `bay-of-troy`, `scamander-simoeis-confluence` |
| 13.1.32 | Rhoeteium to Sigeium 60 stades; Harbour of the Achaeans about 12 stades from present Ilium; earlier Ilium 30 stades further inland toward Ida; temple and monument of Achilles near Sigeium, with monuments of Patroclus and Antilochus, all receiving Ilian sacrifice | `tomb-of-achilles-and-patroclus` |
| 13.1.34 | The spurs enclose the Simoeisian and Scamandrian plains; the Trojan Plain proper is the wider one where most of the fighting is set; the places "pointed out" on it are **Erineus, the tomb of Aesyetes, Batieia, and the monument of Ilus**; the rivers meet a little in front of present Ilium and issue toward Sigeium forming Stomalimnê | `scamandrian-plain`, `fig-tree`, `tomb-of-aesyetes`, `batieia`, `tomb-of-ilos`, `scamander-simoeis-confluence` |
| 13.1.35 | Callicolone 40 stades from present Ilium, 5 from the Simoeis; Thymbra 50 stades, with the Thymbrius flowing to the Scamander at the temple of Thymbraean Apollo; **Erineus** "a place that is rugged and full of wild fig trees" at the foot of the ancient site; **a little below Erineus is Phegus** | `callicolone`, `thymbra`, `thymbrios`, `fig-tree`, `oak-of-zeus` |
| 13.1.36 | The Naval Station is so near present Ilium as to make both sides look foolish; Homer says the wall was built only recently, "or else it was not built at all, but fabricated and then abolished by the poet, as Aristotle says"; Naval Station near Sigeium, Scamander emptying near it, 20 stades from Ilium | `achaean-wall-and-ditch`, `achaean-camp` |
| 13.1.43 | On 22.147–52: "no hot waters are now to be found at the site," and the Scamander has one source, in the mountain, not two; the hot spring may have given out | `two-springs-of-scamander`, `washing-troughs` |

Two things follow that the plate must respect. First, **Erineos in the tradition is a place,
not a tree** — a fig-covered rough slope with the oak below it. Second, the tradition's whole
argument (Demetrius's) is that these places fit the *old* settlement and not Hisarlık; we are
not adopting that argument, and any note that cites Strabo must not smuggle it in.

**Sigeion and Rhoiteion are not Homeric.** Sweeps for `σιγει-` and `ροιτ-` across all 24 books
return zero relevant hits (all `ροιτ-` hits are Προῖτος, ἄροιτο, φέροιτο and the like). They
are Strabonic reference points and must be labelled as such if they appear at all.

---

## 7. Sweeps, absences, and contradictions

### 7.1 What the exhaustive lemma sweeps returned

| lemma swept | hits relevant to the plain | note |
|---|---|---|
| `Σκαι-` | 12 | plus 1.501, 16.734, 21.490 (`σκαιῇ`, "with the left hand"), 5.387/10.495/10.561 (`τρισκαι-`), 18.572 (`σκαίροντες`) |
| `Δαρδανι-` (gates) | 3 | 5.789, 22.194, 22.413 — the complete set |
| `φηγ-` | 7 | plus 3 excluded (personal name, axle, simile) |
| `ἐρινε-` | 4 | 6.433, 11.167, 21.37, 22.145 — the complete set |
| `σκοπι-` | 1 on the plain | 22.145; all others similes or idioms |
| `ἀμαξ-` | 1 | 22.146 — the only road so named |
| `κρουν-` | 2 | 22.147, 22.208; 4.454 is a simile |
| `πλυν-` | 2 | 22.153, 22.155 — the complete set |
| `θρωσμ-` | 3 | 10.160, 11.56, 20.3 — the complete set |
| `περγαμ-` | 6 | 4.508, 5.446, 5.460, 6.512, 7.21, 24.700 |
| `θυμβρ-` | 1 | 10.430; 11.320 is a man |
| `ἑλλησπ-` | 10 | all listed at §5.15 |
| `λιμεν-` | 0 at Troy | 1.432 Chryse, 21.23 simile, 23.745 Lemnos |
| `σιγει-` | **0** | not a Homeric name |
| `ροιτ-` | **0** | not a Homeric name |
| `ἀριστερ-` | 21 total | positional: 12.118, 13.675 (*ships'* left); 5.355, 11.498, 13.765, 17.116, 17.682 (*battle's* left); 13.309, 13.326 (army's own usage); 2.526, 12.240 (contingent/omen); 12.201, 12.219 (the eagle omen); the rest are wounds and Ajax's shield-work (5.16, 5.660, 11.321, 16.106, 16.478, 7.238) or the chariot race (23.336, 23.338) |

### 7.2 Absences that are content

These should be *labelled* on the schematic, per the register rule:

- **No harbour at Troy.** The Achaeans have a beach.
- **No named headlands.** 14.36 says `ἄκραι` and stops.
- **No left/right assignment for Ajax and Achilles.** The poem says `ἔσχατα` twice and never
  which end.
- **No temperature-differentiated spring pair on the ground**, from Demetrius (Strabo 13.1.43)
  through Virchow and Leaf to the 2020 hydrochemistry.
- **No trace of the Achaean wall, by design.** The poem erases it (12.13–33) and antiquity
  noticed (Aristotle *ap.* Strabo 13.1.36).

### 7.3 Places whose Homeric anchor is a *region* or a *bearing*, not a point

`scamandrian-plain` (the whole sheet) · `trojan-camp` (a band between ditch and river) ·
`thymbra` (a bearing at the far end of the 10.428–31 axis) · `achaean-camp` (a block with
depth) · `troy-lower-city` (an inference, no anchor).

Anchoring these as pins is the mistake that produced "these are all at Troy." Anchor them as
extents.

### 7.4 The twelve with no Homeric anchor at all

`kesik-basin` · `tomb-of-ajax-in-tepe` · `thymbrios` · `bay-of-troy` · `uvecik-tepe` ·
`besik-bay` · `troy-lower-city` (inference only) — seven with nothing positional in the poem.
A further five have exactly **one** Homeric mention and no relational statement beyond it, so
their anchor rests on a single line: `lookout-skopie` (22.145), `wagon-road` (22.146),
`thymbra` (10.430), `achaean-assembly-place` (11.806–8, though 2.91–93 corroborates),
`batieia` (2.811–15). Twelve in total that a drawing lane must handle with care.

Three of the seven — `uvecik-tepe`, `besik-bay`, `bay-of-troy` — are the handoff §3.8 gap:
they are `certain` with no coordinate, and they want **coordinates**, not anchors. Do not let
the anchor mechanism paper over a missing coordinate on a surveyed site.

### 7.5 Two numeric dimensions the poem does give

Worth recording because the schematic has no scale otherwise, and because a plate that claims
a scale it cannot support is the §3.4 defect:

- `πυρὴν ἑκατόμπεδον ἔνθα καὶ ἔνθα` (23.164) — the pyre, a hundred feet each way.
- `γεφύρωσεν δὲ κέλευθον / μακρὴν ἠδ' εὐρεῖαν, ὅσον τ' ἐπὶ δουρὸς ἐρωὴ / γίγνεται` (15.357–59)
  — Apollo's causeway over the ditch, a spear-cast wide.

Nothing else in the plain is measured. A schematic scale bar is therefore not available, and
the plate should not carry one.

### 7.6 Contradictions — **recorded, not resolved**

These are the reason this dossier exists. A drawing lane must see both readings of each and
must not average them.

**C-1. The fig tree is in two places.**
`μέσσον κὰπ πεδίον παρ' ἐρινεόν` (11.167), beside the tomb of Ilos, mid-plain — against
`παρὰ σκοπιὴν καὶ ἐρινεὸν ἠνεμόεντα / τείχεος αἰὲν ὑπ' ἐκ` (22.145–46) and
`στῆσον παρ' ἐρινεόν, ἔνθα μάλιστα / ἀμβατός ἐστι πόλις` (6.433–34), close under the wall.
Readings on offer: two trees (Leaf 1912, 42); one fig-*district* on the slope below the city
(Strabo 13.1.35 / Demetrius); a formulaic landmark used loosely (the position taken by the
dissenting tradition, `TROAD-SOURCES.md` §C). *Verified how:* all four `ἐρινε-` hits read in
the corpus; Leaf and Strabo read in the sources cited.

**C-2. The rivers join under the city — and they do not.**
`ἧχι ῥοὰς Σιμόεις συμβάλλετον ἠδὲ Σκάμανδρος` (5.774), with the arrival framed as *reaching
Troy*, puts the confluence close under the city and so between city and camp — which is
incompatible with Book 21, where Achilles drives half the Trojans across the plain toward the
city and half into the river, and with 6.4's interfluve battlefield. Leaf, *Troy* (1912), 37:
"in this one passage the poet clearly conceives the two rivers as meeting close under Troy, and
so cutting the city off from the camp. He thus stands in direct conflict not merely with the
opening of xxi." *Verified how:* Greek checked in corpus books 5, 6, 21; Leaf read in the scan.

**C-3. Protesilaus's ship is at the low point of the wall, at the extremity, and — on one
reading — in the middle.**
- 13.681–83: `ἔνθ' ἔσαν Αἴαντός τε νέες καὶ Πρωτεσιλάου / θῖν' ἔφ' ἁλὸς πολιῆς εἰρυμέναι·
  αὐτὰρ ὕπερθε / τεῖχος ἐδέδμητο χθαμαλώτατον` — Ajax's and Protesilaus's ships together,
  where the wall is lowest.
- 8.225 = 11.8: Ajax is at an extremity (`ἔσχατα`).
- 16.285–86: `ἀντικρὺ κατὰ μέσσον, ὅθι πλεῖστοι κλονέοντο, / νηῒ πάρα πρυμνῇ μεγαθύμου
  Πρωτεσιλάου` — strictly, what is `κατὰ μέσσον` is **Patroclus's throw** into the thickest
  press, which lands beside Protesilaus's stern; that the *ship itself* is central is a
  reading (Clay's, per Marks's BMCR notice — authority: prose until Clay or Hainsworth is
  read), not the bare Greek. The same-book pair below carries the contradiction on its own.
- 13.312–13, independently: `νηυσὶ μὲν ἐν μέσσῃσιν ἀμύνειν εἰσὶ καὶ ἄλλοι / Αἴαντές τε δύω` —
  Idomeneus puts **both** Ajaxes at the middle of the ships, in the same book as 13.681. This
  is the sharpest form of the contradiction and it needs no cross-book argument.
- 15.704–6: Hector grips the stern of the ship that brought Protesilaus, and 15.707–8 makes it
  the focus of the whole fight; 15.415–18 has Hector and Ajax struggling over one single ship.

Readings on offer: Leaf, *Iliad* (1902) on 13.681 — "Αἴαντος without an adj. must mean the
Telamonian; though acc. to Λ 8–9 his ships were at the extremity of the line, and in Λ 5 the
centre is occupied by those of Odysseus. But we need not trouble ourselves about the discrepancy
with so late a passage as the introduction to Λ — certainly not to the extent of supposing with
Ar. that the Oilean Aias is meant." So: (i) Aristarchus took the Ajax of 13.681 to be the Locrian
(and Leaf rejects it); (ii) Leaf sets the camp-order passage aside as late; (iii) the fight
moved, and Ajax with it, which is what 15.415–18 and 16.102–24 describe. *Verified how:* Greek
checked in corpus books 8, 11, 13, 15, 16; Leaf's note read in the 1902 scan.
**For the plate:** anchor Protesilaus's ship **once**, at the low point of the wall, and put the
16.286 "centre" reading in the note as a recorded conflict. Do not anchor it twice.

**C-4. Aristarchus: one gate, on the left.**
Aristarchus argued in *On the Naval Camp* (Περὶ τοῦ ναυστάθμου) that the Achaean wall had a
single gate, on the left (from 12.118). Leaf, *Iliad* (1900) on 12.175–81, records that the
ancient critics unanimously rejected 12.175–81 as an addition intended to distinguish Asius's
gate from Hector's, and answers Aristarchus from 13.312 and 13.679, which put Hector's assault
in the centre. Our text has plural gates at 7.438 and 12.120. *Verified how:* Greek checked in
corpus books 7, 12, 13; Leaf's notes read in the 1900 scan; the existence and title of
Aristarchus's treatise corroborated by Porter, *Classics@* 3.1.

**C-5. Troy: one gate or three?**
Aristarchus read 2.809 `πᾶσαι δ' ὠΐγνυντο πύλαι` as "the gate was opened wide," giving Homer's
Troy a single gate called either Scaean or Dardanian. Leaf, *Troy* (1912), 151–53, records the
view, calls the Greek doubtful, and holds for at least three gates. *Verified how:* 2.809
checked in the corpus; Leaf read in the scan.

**C-6. Is the ditch close to the wall or far from it?**
8.213, `τῶν δ' ὅσον ἐκ νηῶν ἀπὸ πύργου τάφρος ἔεργε`, admits both. Leaf, *Iliad* (1900) on
8.213, sets out the two options — (1) ships and wall together with the trench at a considerable
distance off, the Greeks driven behind the trench but not inside the wall; (2) wall and trench
together, the Greeks driven inside both and filling the space up to the ships — and says option
(2) "is by far the most natural, and is what we should like to get; but (1) in one form or
another is what the words seem to imply," because `ἀπό` implies *far from*. Against that,
9.87–88 has 700 watchmen camping and cooking in the gap, which requires a real interval.
*Verified how:* 8.213 and 9.87–88 checked in the corpus; Leaf's note read in the 1900 scan.
**For the plate:** draw a stated interval and cite 9.87; note the ambiguity of 8.213.

**C-7. The `ἀμαξιτός` ring versus the road to the ships.**
See §5.10. The poem names one road under the walls (a ring) and describes another by its
waypoints (a radial route to the camp). It never joins them. Drawing a single continuous road
from the Scaean gate to the camp gate through the springs is a synthesis, not a text.

**C-8. Leaf's athetesis of the camp order.**
Leaf brackets 8.224–26 and calls 11.1–55 late (§3.3). Our lineation never moves and the lines
stand; but a plate that treats the camp order as bedrock should note that the fullest PD
commentary on the poem treats the passage that states it as an addition.

---

## 8. Needs paywalled access

Named precisely, with the claim each would settle. Nothing below was consulted; nothing below
may be cited as if it were.

1. **G. S. Kirk, *The Iliad: A Commentary*, vol. I, Books 1–4** (Cambridge, 1985) —
   [lending scan, `iliadcommentary0000kirk`](https://archive.org/details/iliadcommentary0000kirk).
   Wanted: the notes on **2.792–94** (tomb of Aesyetes: does Kirk accept the mid-plain
   placement or the scholiasts' equation with the 22.145 `σκοπιή`?) and **2.811–15** (Batieia:
   what does he make of `ἀπάνευθε` and `περίδρομος`?). *Would settle:* whether §5.1 and §5.12
   can state an offset from the wall.
2. **G. S. Kirk, vol. II, Books 5–8** (Cambridge, 1990) —
   [`iliadcommentary0002kirk`](https://archive.org/details/iliadcommentary0002kirk).
   Wanted: notes on **5.774** (the confluence — does Kirk accept Leaf's "direct conflict"?),
   **7.336–43 / 7.435–41** (wall geometry), **8.213** (the ditch interval, C-6), and
   **8.222–26** (whether he keeps or brackets the camp order, C-8). *Would settle:* C-2, C-6,
   C-8 with a modern authority rather than Leaf alone.
3. **Bryan Hainsworth, vol. III, Books 9–12** (Cambridge, 1993) —
   [`iliadthecommenta0003unse`](https://archive.org/details/iliadthecommenta0003unse).
   Wanted: notes on **9.87** (the ditch/wall gap), **11.166–70** (the fig tree in the
   mid-plain, C-1), **11.806–8** (the agora and altars), and **12.118–19** (the left of the
   ships — this is the note that either confirms or breaks §3.1). Also the general remark on
   Troad geography as "a poetical construction" that `TROAD-SOURCES.md` §C attributes to
   Hainsworth *at second hand and flags as unverified* — **that attribution is still
   unverified and must not be quoted on the site until someone reads the page.**
   *Would settle:* C-1, C-4, and §3.1's strongest single claim.
4. **Richard Janko, vol. IV, Books 13–16** (Cambridge, 1992) — **no archive.org record found**
   in this lane's searches; needs a library. Wanted: notes on **13.681–84** and **16.285–86**
   (the Protesilaus contradiction, C-3 — Janko is the standard modern treatment) and
   **14.30–36** (`προκρόσσας` and the camp's depth). Also: **what the single map in this volume
   actually depicts** — the open question already logged in `TROAD-CARTOGRAPHY.md`.
   *Would settle:* C-3, and the map question.
5. **Mark Edwards, vol. V, Books 17–20** (Cambridge, 1991) —
   [`iliadcommentary0005unse`](https://archive.org/details/iliadcommentary0005unse).
   Wanted: note on **20.144–52** (the wall of Heracles and Callicolone as a matched pair —
   does Edwards endorse Leaf's neutrality argument?). *Would settle:* §3.6's geometry.
6. **Nicholas Richardson, vol. VI, Books 21–24** (Cambridge, 1993) —
   [`iliadcommentaryv0006unse`](https://archive.org/details/iliadcommentaryv0006unse).
   Wanted: notes on **22.145–56** (the whole chase-route complex — the most consequential note
   in the whole dossier), **22.165 / 22.208** (does Richardson accept that the springs lie on
   the circuit?), **23.125–26 / 23.164 / 23.255–57** (pyre, mound and ring), **23.327–33**
   (the turn-post), and **24.349–51 / 24.443 / 24.692** (Priam's route). *Would settle:* §3.5,
   §5.2, §5.28, §5.29.
   *Access note:* all five located scans are **lending-only**; both archive.org search-inside
   endpoints return nothing without an authenticated borrow, so page numbers cannot be
   established remotely. A borrow session or a library visit is required.
7. **J. V. Luce, *Celebrating Homer's Landscapes: Troy and Ithaca Revisited*** (New Haven:
   Yale University Press, 1998). Not on archive.org. Wanted: his reconstruction of the Book 22
   chase and of the camp, and specifically whether he charts the fighting scene by scene (the
   open question in `TROAD-CARTOGRAPHY.md`). *Would settle:* whether the schematic can cite a
   modern scene-by-scene reconstruction rather than deriving one.
8. **J. V. Luce, "The Homeric Topography of the Trojan Plain Reconsidered," *Oxford Journal of
   Archaeology* 3, no. 1 (1984)** — already cited in the `fig-tree` record. Wanted: his
   treatment of the fig tree and the two-fig problem (C-1). *Would settle:* whether the
   gazetteer's existing citation actually supports what that record says. **It should be
   checked: the record cites Luce 1984 for a claim nobody in this lane has read.**
9. **Jenny Strauss Clay, *Homer's Trojan Theater*** (Cambridge, 2011). Wanted: the argument
   for constant left/right orientation from the camp's centre (§3.1) in her own words, with the
   passages she rests it on; and her Books 12/13/15/16/17 stage layout. *Would settle:* §3.1,
   which currently rests on a review. **The companion website is dead** (host no longer
   resolves); the 2011 Wayback capture is the only record, and it describes the maps without
   showing them.
10. **Alexandra Trachsel, *La Troade: un paysage et son héritage littéraire. Les commentaires
    antiques sur la Troade, leur genèse et leur influence*, Bibliotheca Helvetica Romana 28
    (Basel: Schwabe, 2007).** Wanted: her treatment of the Achaean camp, the divine viewpoints,
    and the subdivisions of the city as the ancient commentators construed them; and **what her
    four maps depict**. Consulted only through Andrea Primo's review,
    [BMCR 2009.05.02](https://bmcr.brynmawr.edu/2009/2009.05.02/), which confirms she treats
    "the city of Troy in its divisions, the Achaean encampment, the observation points of the
    gods, and the other geographical places of the Troad" but names none of our individual
    features. *Would settle:* the provenance of every `traditional` tier on this plate, at the
    level of the individual commentator (Demetrius, Polemon, Hestiaea) rather than Strabo.
11. **Christos Tsagalis, *From Listeners to Viewers: Space in the Iliad*, Hellenic Studies 53
    (Washington, DC: Center for Hellenic Studies, 2012).** Nominally open access at
    [chs.harvard.edu](https://chs.harvard.edu/book/tsagalis-christos-from-listeners-to-viewers-space-in-the-iliad/),
    but the chapter pages returned empty to every fetch attempted in this lane (the site blocks
    the fetchers). Wanted: his chapter on the Achaean camp — the four areas he distinguishes
    (Agamemnon's and Achilles' headquarters, the seashore, the wall, the ships) and the passages
    behind them. *Would settle:* §3.2, §3.3, §5.21 with a modern narratological treatment. This
    is the **cheapest** item on this list to close — it is free, it just needs a browser.
12. **Oscar Mey, *Das Schlachtfeld vor Troja: eine Untersuchung*** (Berlin and Leipzig: de
    Gruyter, 1926), and whatever 1928 publication carries **Walter Andrae's fold-out drawing of
    the Teichomachie vor Troja** (see §9.3). Reviewed in *Classical Review* (Cambridge,
    paywalled). *Would settle:* the single most directly relevant prior reconstruction of the
    Achaean wall-and-ditch as a drawn plate, and — if the drawing was published in 1928 — a
    **US public-domain** precedent for exactly our schematic register.
13. **Jean Cuillandre, *La droite et la gauche dans les poèmes homériques*** (Paris: Les Belles
    Lettres, 1943). Wanted: the argument that assigns Ajax to the left and Achilles to the
    right of the line. *Would settle:* §3.3's open question — but note that even if Cuillandre
    is persuasive, the *poem* is silent, so the plate should still label the ends
    non-committally.

---

## 9. Unverified — do not claim publicly

1. **Which end of the Achaean line is left.** Every version of "Ajax at the north-east /
   Achilles at the south-west" traced in this lane came from tertiary web summaries that
   attribute it to Cuillandre 1943 without a page. Not consulted. **Do not put a compass
   bearing on the camp's ends.**
2. **What Clay's schematic map actually shows.** The Wayback capture of her project describes
   "a schematic map in accordance with the *Iliad*'s orientation" and lists Books 12, 13, 15,
   16, 17, but no map image from the interface was retrieved and read in this lane. We may cite
   that the map exists and what the site says about it; we may not describe its content.
3. **The Andrae drawing's publication.** An image titled `BattlefieldH.jpg` was hosted by
   Clay's UVa project and **was retrieved and looked at** in this lane (3785×2653 JPEG, Adobe
   Photoshop CS metadata dated 2006-11-30). What it depicts, described from looking: a
   pen-and-ink bird's-eye reconstruction of the Teichomachia, monogrammed and dated **1928** —
   the Achaean ships and huts massed along the Hellespont behind a timber palisade with berm
   and ditch swung in a **wide arc**, three gates, Trojans assaulting in several groups, one
   gate already burst, and in the foreground chariots coming to grief in the ditch. The German
   caption beneath it credits the drawing to **Prof. Walter Andrae** and is written in the first
   person by someone calling it an illustration of "our findings" and of "my whole text"; it
   cites *Il.* 12.445 ff. for the great pointed stone standing at the middle gate — and that
   citation checks out against the corpus: `Ἕκτωρ δ' ἁρπάξας λᾶαν φέρεν, ὅς ῥα πυλάων /
   ἑστήκει πρόσθε πρυμνὸς παχύς, αὐτὰρ ὕπερθεν / ὀξὺς ἔην` (12.445–47), a stone standing
   before the Achaean gate, thick at the base and pointed above. So a pointed standing stone
   at a camp gate is a **Homeric** feature our own schematic can draw, on 12.445–47, without
   going anywhere near Andrae's plate.
   **What is unverified:** the publication. Oscar Mey's *Das Schlachtfeld vor Troja* is 1926,
   the drawing is dated 1928, and no bibliographic record for a 1928 Mey volume containing an
   Andrae fold-out was confirmed in this lane. **Do not attribute the plate to Mey 1926, and do
   not assert it is public domain, until the publication is established.** Do not trace it under
   any circumstances before that.
4. **Hainsworth on Troad geography as "a poetical construction."** Already flagged as
   second-hand and unverified in `TROAD-SOURCES.md` §C. Still unverified. Still must not be
   quoted.
5. **What the gazetteer's Luce 1984 citation on `fig-tree` actually supports.** The record
   cites the article; nobody in this lane has read it. Either read it or soften the record.
6. **Page numbers in Leaf 1912.** Page ranges quoted above (35–40 ford, 41 Throsmos, 42 tomb of
   Ilos, 43 tomb of Aesyetes and the wall of Heracles, 44 Callicolone, 46–52 and 165–66 springs,
   151–58 Scaean Gate, 158–62 Dardanian Gate, 384–89 Appendix A) come from **the book's own
   index** as OCR'd, cross-checked against the running heads embedded in the scanned text where
   possible. Two index digits were visibly OCR-corrupted ("85-40" for 35–40; "48" for 43) and
   were corrected by inference. Treat every Leaf 1912 page number as ±1 until someone opens the
   scan to the page. The *quotations* are verbatim from the scan and are safe; the *page
   numbers* are not yet citation-grade.
7. **Scholiastic citations at second hand.** The scholia references in §7.6 (Aristarchus on
   2.809 and on the camp's single gate; the unanimous ancient rejection of 12.175–81; the
   athetesis of 7.443–64) are reported from Leaf 1900/1902 and from Porter's *Classics@*
   article. No scholia edition (Erbse) was opened. Cite Leaf and Porter, not the scholia.
8. **Aristotle fr. 162 Rose.** The fragment number comes from Porter's article, not from a Rose
   edition. Cite it as "Aristotle *apud* Strabo 13.1.36 (fr. 162 Rose, per Porter)."

---

## 10. What a drawing lane should take from this

Six things, in order of leverage:

1. **Build the sheet on §3.1's orientation.** One fixed left and right, from the camp's centre
   facing the plain. It converts every `ἀριστερά` into a position.
2. **Draw the camp as a block with depth** (§3.2), not a line of ship glyphs: shore, ships in
   ranks with huts alternating, sterns, then the wall, then the interval where the watch camps,
   then the ditch with its palisade.
3. **Anchor the order, not the ends** (§3.3): extremity — … — Odysseus + agora + altars — … —
   extremity, with the ends labelled by name and *not* by compass.
4. **Draw the ring road and the camp road as two different things** (§5.10, C-7), and put the
   springs, the lookout and the windy fig-tree on the ring, because 22.208 puts them there.
5. **Use the 10.428–31 axis** (§5.27) for the allied camps. It is the poem handing us a
   diagram, and it is currently unused.
6. **Anchor extents, not pins, for the five regions** in §7.3 — above all
   `scamandrian-plain`, which should resolve to the unzoomed sheet. That single decision fixes
   125 Chart Room scenes honestly instead of pretending to frame them.

And two prohibitions:

- **No scale bar on the schematic** (§7.5). The poem measures two things and neither is a
  distance across the plain.
- **No anchor for the seven places with no Homeric position** (§7.4). Three of them want
  coordinates instead; four want nothing.
