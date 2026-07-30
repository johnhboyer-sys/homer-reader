# RESEARCH-SHIELD — the Shield of Achilles, Iliad 18.478–608

**Consumed by:** the Shield plate rebuild (`apparatus/plates/shield-of-achilles.json`,
pulled from the reader per `docs/TROY-MAPS-HANDOFF-2.md` §3.7).
**Kind:** figuration brief. What must be depicted, where scholarship puts it on the
disc, and in what visual register. **Not** a palette brief.
**Drafted:** 2026-07-29. Status: draft; nothing here is signed off.
**Revised:** 2026-07-29 — Taplin 1980, Hardie 1985 and Revermann 1998 obtained as
PDFs (`research-cache/`), read in full, and folded in. Sections touched: 0, 1.1,
1.2, 1.3, 2.2, 3.1, 3.2, 3.3, 3.4, 4, 5.1, 5.3, 5.4, 7, 8. Three things a reader
should not miss: the **start page of Hardie is 11**; §3.1e's attribution was
**backwards** and is fixed; and §2.2 now carries a **FLAG FOR JOHN** on the
singer.

Every claim below carries an **authority kind** — `geometry` (compositional
structure: what goes where on the disc), `identification` (what a thing is), or
`prose` (interpretation, tone, framing) — and a `verified how` note. Per
CLAUDE.md, in-copyright scholarship is a legitimate *source*: cited precisely,
quoted briefly, never republished. Chicago for books and articles; hyperlinks for
web resources.

---

## 0. Method and sampling declaration

- **The text was covered, not sampled.** Every line of Il. 18.468–615 was read
  from the shipped corpus, and **every** occurrence of `Ἐν / ἐν / εἰν / ἔνθα` in
  478–608 was enumerated programmatically (31 lines carry one of those forms; 33
  counting `ἐνί` at 504 and 591). §1.3 lists
  the ones that are *not* scene boundaries — the trap.
- **Corpus of record.** `app/public/data` → `build/dist`;
  `build/dist/iliad/book-18.json` (617 lines, `n` 1–617, no gaps). Greek
  provenance is stated in the TLG export header
  (`build/export/Diogenes-Resources/xml/tlg/tlg0012001.xml`): *"Homeri Ilias,
  vols. 2 3", Ed. Allen, T.W. Oxford: Clarendon Press, 1931.* English is Murray's
  Loeb, per CLAUDE.md.
- **Scholarship: three of the five key items are now read in full** (updated
  2026-07-29). **Taplin 1980, Hardie 1985 and Revermann 1998** are on disk as
  JSTOR PDFs and were read cover to cover, notes included —
  `research-cache/taplin-1980-shield.pdf`,
  `research-cache/hardie-1985-imago-mundi.pdf`,
  `research-cache/revermann-1998-text-iliad.pdf`. Claims sourced to them now
  carry page numbers and a first-hand `verified how`, and where they correct
  what this dossier said second-hand the correction is marked in place.
  **Edwards vol. V and Fittschen 1973 remain unread**; everything resting on
  them is still second-hand and still listed in §7. Nothing was inferred from a
  title.
- I did not consult the print Landmark series (excluded by CLAUDE.md) and did not
  read any pirated scan of Edwards vol. V; the one such host I opened
  (`vdoc.pub`) stops inside Book 17 and gave nothing.

---

## 1. The text: scene inventory

### 1.1 The frame (478–482) — not a scene

```
478  Ποίει δὲ πρώτιστα σάκος μέγα τε στιβαρόν τε
479  πάντοσε δαιδάλλων, περὶ δ' ἄντυγα βάλλε φαεινὴν
480  τρίπλακα μαρμαρέην, ἐκ δ' ἀργύρεον τελαμῶνα.
481  πέντε δ' ἄρ' αὐτοῦ ἔσαν σάκεος πτύχες· αὐτὰρ ἐν αὐτῷ
482  ποίει δαίδαλα πολλὰ ἰδυίῃσι πραπίδεσσιν.
```

| # | Claim | Kind | Citation | Verified how |
|---|---|---|---|---|
| 1.1a | The shield is round, decorated `πάντοσε` ("all over", 479), with a **triple bright rim** (`ἄντυγα … τρίπλακα μαρμαρέην`, 479–80) and a **silver baldric** (480). The rim is the only structural feature the poet gives the *face*. | geometry | Il. 18.479–80 | Read in corpus, `book-18.json` |
| 1.1b | `πέντε … πτύχες` (481) are **structural layers, not decorated zones**. Cunliffe s.v. πτύξ: "One of the layers of hide or metal forming a shield Il. 7.247, Il. 18.481, Il. 20.269, 270." | identification | Richard John Cunliffe, *A Lexicon of the Homeric Dialect* (London: Blackie and Son, 1924), s.v. πτύξ | Queried the shipped Cunliffe slice, `build/dist/cunliffe/p.json` |
| 1.1c | The poem itself blocks the "five layers = five zones" inference: at Il. 20.269–72 the five πτύχες are **two of bronze, two of tin, and one of gold**, and the gold one is what stops Aeneas's spear (`χρυσὸς γὰρ ἐρύκακε`, 20.268; `τῇ ῥ' ἔσχετο μείλινον ἔγχος`, 20.272). That the gold sits *inside* is the standard reconstruction of the much-discussed layering, not an explicit gloss — 20.271's `ἔνδοθι` attaches to the tin. Either way, a layer that stops a spear from within is not a visible band. | geometry | Il. 20.268–72 | Read in corpus, `build/dist/iliad/book-20.json` lines 259–281 |
| 1.1d | **The "five layers = five zones" reading is nevertheless an ancient allegory, and Hardie shows exactly where it came from.** Heraclitus (*Homeric Problems*) and Eustathius make the four metals the four elements and the five πτύχες "the five zones into which the earth is divided"; Demo's variant makes them the five circles of *heaven*, which Hardie judges "probably the result of contamination from the allegorization of the Shield of Agamemnon." Eustathius further allegorises the triple `ἄντυξ` as the **zodiac** ("triple" = the breadth of the zodiac; "gleaming" because the sun moves within it) and the `τελαμών` as the axis of the universe. Aelius Aristides (*Panath.* 15) builds a five-ring shield out of the layers: Acropolis, polis, Attica, Hellas, the Earth. **The tradition is real and it is exegesis, not description** — which is why a plate may not cite it as the poem's own arrangement. | identification | P. R. Hardie, "*Imago Mundi*: Cosmological and Ideological Aspects of the Shield of Achilles," *Journal of Hellenic Studies* 105 (1985): 11–31, at 15, 15 n. 30, and 28 n. 114 | Read in full, `research-cache/hardie-1985-imago-mundi.pdf` |

### 1.2 The nine `Ἐν`-marked units (and the tenth scene inside one of them)

Allen's text capitalises the initial `Ἐν` at exactly nine places. Those nine are
the poem's own division of the field. The two cities are **one** `Ἐν δὲ` unit
containing two members, the second introduced by `Τὴν δ' ἑτέρην πόλιν` (509).

| # | Span | Lines | Greek incipit | Content a drawer must put on the disc |
|---|---|---|---|---|
| 1 | **483–489** | 7 | `Ἐν μὲν γαῖαν ἔτευξ', ἐν δ' οὐρανόν, ἐν δὲ θάλασσαν,` | Earth, sky, sea; tireless Sun and full Moon; **named** constellations — Pleiades, Hyades, the might of Orion, and the Bear "which they also call the Wain", which turns in place watching Orion and alone has no share in Ocean's baths (487–89). Four named star-groups, not a generic star-field. |
| 2a | **490–508** | 19 | `Ἐν δὲ δύω ποίησε πόλεις μερόπων ἀνθρώπων` / `ἐν τῇ μέν ῥα γάμοι` | City at peace, two simultaneous events: (i) **wedding**, 491–96 — brides led from their chambers under blazing torches, `πολὺς … ὑμέναιος`, whirling boy-dancers, pipes and lyres sounding, women standing in wonder each at her own porch-door (`ἐπὶ προθύροισιν ἑκάστη`); (ii) **lawsuit**, 497–508 — see §2.1. |
| 2b | **509–540** | 32 | `Τὴν δ' ἑτέρην πόλιν ἀμφὶ δύω στρατοὶ ἥατο λαῶν` | City at war — the **longest scene by far**. Besiegers in flashing armour, split in counsel (sack it, or halve the property); wives, small children and old men holding the **wall** (514–15); the sortie led by **Ares and Pallas Athene, both gold, in gold clothing, tall and beautiful and conspicuous, while the people were smaller** (516–19 — an explicit scale hierarchy, the one composition instruction the poem gives); **ambush at the river** where the watering-place is (520–22); two scouts apart, waiting for flocks and cattle (523–24); shepherds piping, foreseeing nothing (525–26); the raid, the killing of the herdsmen (527–29); the besieged mount and ride out (530–32); **battle along the river banks** (533–34); Strife, Tumult and deadly Fate among them, Fate dragging one dead man by the feet, her garment blood-red (535–38); "they mingled and fought like living mortals, and dragged away each other's dead" (539–40). |
| 3 | **541–549** | 9 | `Ἐν δ' ἐτίθει νειὸν μαλακὴν πίειραν ἄρουραν` | Ploughing. Wide, thrice-worked fallow; many ploughmen wheeling teams "this way and that"; at each headland (`τέλσον`) a man puts a cup of honey-sweet wine in their hands and they turn back down the furrows; **the ground darkens behind the plough and looks like ploughed earth although it is gold — `τὸ δὴ περὶ θαῦμα τέτυκτο`** (548–49). |
| 4 | **550–560** | 11 | `Ἐν δ' ἐτίθει τέμενος βασιλήϊον· ἔνθα δ' ἔριθοι` | The king's `τέμενος` at harvest. Hired reapers with sharp sickles; swathes falling in rows; three binders behind them; boys gathering armfuls and handing them up unceasingly; **the king standing among them in silence, sceptre in hand, at the swathe, glad at heart** (556–57); heralds apart under an **oak** preparing the meal, having sacrificed a great ox; women sprinkling much white barley for the reapers' dinner. |
| 5 | **561–572** | 12 | `Ἐν δ' ἐτίθει σταφυλῇσι μέγα βρίθουσαν ἀλωὴν` | Vineyard heavy with grapes, **beautiful and golden**; the clusters **dark** (`μέλανες … βότρυες`); it stood on **silver poles**; round it a **κυάνεος ditch** and a **fence of tin**; **one single path** for the carriers at vintage; girls and youths carrying the honey-sweet fruit in plaited baskets; **and in their midst a boy playing a clear-toned lyre and singing the Λίνος** in a delicate voice, the rest beating the ground in time, following with dance and shouting (569–72). |
| 6 | **573–586** | 14 | `Ἐν δ' ἀγέλην ποίησε βοῶν ὀρθοκραιράων·` | Herd of straight-horned cattle, **the cows wrought of gold and tin**, lowing as they hurry from the farmyard to pasture **beside a sounding river, beside the waving reed-bed** (576); **four golden herdsmen**, **nine swift-footed dogs**; **two terrible lions among the foremost cattle have seized a bellowing bull**, which is dragged away roaring; dogs and young men chase; the lions have ripped the great ox's hide open and are gulping entrails and dark blood; the herdsmen set the swift dogs on in vain — the dogs shrink from biting, stand very close, bark and dodge away (585–86). |
| 7 | **587–589** | 3 | `Ἐν δὲ νομὸν ποίησε περικλυτὸς ἀμφιγυήεις` | Sheep pasture — "in a beautiful glen, a great one, of white sheep — and steadings and roofed huts and pens." **Three lines. The thinnest scene on the shield.** |
| 8 | **590–606** | 17 | `Ἐν δὲ χορὸν ποίκιλλε περικλυτὸς ἀμφιγυήεις,` | Dancing floor, **like the one Daedalus once made in broad Knossos for fair-haired Ariadne** (591–92). Youths and marriageable girls dancing, holding each other **by the wrist** (594); the girls in fine linen, the youths in well-woven tunics **faintly glistening with oil**; the girls with beautiful garlands, the youths with **gold daggers on silver baldrics** (597–98); now they run round on skilled feet, lightly, **as a potter tries his wheel to see if it will run** (599–601); now they run in rows toward each other; a great crowd stands round the lovely dance, delighting in it; **two tumblers whirl through the middle as leaders of the song** (605–6 — see §2.2). |
| 9 | **607–608** | 2 | `Ἐν δ' ἐτίθει ποταμοῖο μέγα σθένος Ὠκεανοῖο` | The great strength of the river Ocean, **`ἄντυγα πὰρ πυμάτην σάκεος πύκα ποιητοῖο`** — along the outermost rim. |

Arithmetic check: 483–608 = 126 lines; 7+19+32+9+11+12+14+3+17+2 = 126. ✔

**Brief correction (small, load-bearing for the plate's `lines` field):** the
Ocean is **607–608**, not 606–7. The task brief said "606-7 Ocean at the rim";
606 is the last line of the dance (`μολπῆς ἐξάρχοντες ἐδίνευον κατὰ μέσσους`).
The existing plate JSON already has `[607, 608]` and is right.

**Where "606-7" came from — traced, 2026-07-29.** It is Taplin's own heading:
"V *The fifth (outmost) circle (606–7): Ocean*" (Taplin 11). It reflects a
lineation that collapses the 604/605 half-line fossil (§2.2) into whole verses;
Taplin is internally inconsistent about it, since on the same page he ends the
dance at 606. **Hardie, independently, gives the Ocean as "607 f."** (Hardie
11), agreeing with Allen and with our corpus. `[607, 608]` stands, and CLAUDE.md's
sacred-lineation rule settles it anyway: we print Allen's numbers.

**Two spans other scholars have bracketed** (recorded, not adopted — both are in
our corpus and both are therefore drawn as printed):

- **535–40**, the personifications and the mêlée. Solmsen condemned them as
  plus-verses drawn from the *Shield of Heracles* (four of 535–8 recur at
  *Aspis* 156–9); Lynn-George added further points against 535–8 while defending
  539–40 as Homeric. Taplin reports both and finds the defence made "unconvincingly to
  my mind"; his own reason for suspicion is that "this primitive conception of
  battle is not typical of the *Iliad*." *Kind:* identification. *Citation:*
  Taplin, "Shield of Achilles within the *Iliad*," 7 and 19 n. 20, citing F.
  Solmsen, *Hermes* 93 (1965): 1–6, and J. M. Lynn-George, *Hermes* 106 (1978):
  396–405. *Verified how:* read in full, `research-cache/taplin-1980-shield.pdf`.
- **587–9**, the sheep pasture. "I must confess that I am not clear how the last
  three lines, 587–9, fit in. The scene is different from all the others, not
  only because much briefer, but also because **it contains no human figures**.
  Yet it is clearly marked off from the scene of the winter herding and the
  lions. The lines may be interpolated: see Leaf ad loc." (Taplin 9). Our table
  already calls it the thinnest scene; Taplin names *why* it is odd — it is the
  one scene on the shield with nobody in it. A drawer should treat that as
  content, not as a gap to populate.

**One further textual fluctuation a drawer should know about:** the same 'wild'
papyrus that expands the dance (§2.2a) also adds, **after line 608**, four verses
describing a harbour full of fish, "almost the same as *Shield of Heracles*,
207–13" (Taplin 7, citing S. West, *The Ptolemaic Papyri of Homer* (Cologne,
1967), 132–6). Some ancient copies, in other words, put a **fishing harbour**
outside the Ocean rim. It is not in our text; it is not to be drawn; it is worth
a caption if the plate discusses the rim.

### 1.3 The `ἐν` occurrences that are NOT boundaries (the trap)

A parser or a drawer that treats every `ἐν δὲ` as a new zone will invent zones.
Enumerated in full: **485** (`ἐν δὲ τὰ τείρεα πάντα` — inside the cosmos),
**491** (`ἐν τῇ μέν` — the first city), **494** (`ἐν δ' ἄρα τοῖσιν` — pipes among
the dancers), **497** (`εἰν ἀγορῇ`, `ἔνθα δὲ νεῖκος`), **505**, **507**
(`ἐν μέσσοισι` — the talents), **521** (`ἐν ποταμῷ`), **535**
(`ἐν δ' Ἔρις ἐν δὲ Κυδοιμὸς … ἐν δ' ὀλοὴ Κήρ` — **three** `ἐν δ'` in one line,
all inside the battle), **542**, **543**, **545**, **550b** (`ἔνθα δ' ἔριθοι`),
**551**, **553**, **555**, **556**, **568**, **569** (`ἐν μέσσοισι` — the boy
with the lyre), **579**, **588**, **593**, **600**.

- **Claim:** the personifications at 535 (Ἔρις, Κυδοιμός, ὀλοὴ Κήρ) belong **inside
  the river battle**, not on a ring of their own.
  **Kind:** geometry. **Citation:** Il. 18.535–38.
  **Verified how:** regex enumeration over `book-18.json`; 535 is lower-case
  `ἐν δ'` in Allen, mid-sentence, and 539–40 continues the same battle.
  **Corroborated first-hand:** Taplin's own scheme makes 535–40 a sub-scene of
  the war city, "(iii) 535–40: *the ensuing mêlée*" (Taplin 7) — not a band. And
  Revermann, arguing about a different line, states the boundary rule this
  dossier derived independently: on the Shield `ἐν` at verse-opening "introduces
  a new topic rather than concluding one" (Revermann 33). Both read in full from
  `research-cache/`.

---

## 2. The two cruces a drawer must know

### 2.1 The lawsuit: the two talents and the disputed δίκη (18.497–508)

```
497  λαοὶ δ' εἰν ἀγορῇ ἔσαν ἀθρόοι· ἔνθα δὲ νεῖκος
498  ὠρώρει, δύο δ' ἄνδρες ἐνείκεον εἵνεκα ποινῆς
499  ἀνδρὸς ἀποφθιμένου· ὃ μὲν εὔχετο πάντ' ἀποδοῦναι
500  δήμῳ πιφαύσκων, ὃ δ' ἀναίνετο μηδὲν ἑλέσθαι·
501  ἄμφω δ' ἱέσθην ἐπὶ ἴστορι πεῖραρ ἑλέσθαι.
…
504  εἵατ' ἐπὶ ξεστοῖσι λίθοις ἱερῷ ἐνὶ κύκλῳ,
…
507  κεῖτο δ' ἄρ' ἐν μέσσοισι δύω χρυσοῖο τάλαντα,
508  τῷ δόμεν ὃς μετὰ τοῖσι δίκην ἰθύντατα εἴποι.
```

**What is not in dispute, and must be drawn:** a `νεῖκος` in the assembly over
the `ποινή` for a dead man; two litigants; the **people taking sides and shouting
support for both** (502, `λαοὶ δ' ἀμφοτέροισιν ἐπήπυον ἀμφὶς ἀρωγοί`); heralds
holding the crowd back; **the elders seated on polished stones in a sacred
circle** (504, `ἐπὶ ξεστοῖσι λίθοις ἱερῷ ἐνὶ κύκλῳ`), each **holding a herald's
staff** (505) and giving judgement **in turn** (`ἀμοιβηδὶς δὲ δίκαζον`, 506); and
**two talents of gold lying in the middle** (507).

| # | Claim | Kind | Citation | Verified how |
|---|---|---|---|---|
| 2.1a | The elders sit in a **sacred circle** on **dressed stone** — a real, drawable furnishing, not a metaphor. | geometry | Il. 18.504 | Corpus |
| 2.1b | The talents lie **`ἐν μέσσοισι`** — in the middle of the elders' circle, not between the litigants. | geometry | Il. 18.507 | Corpus |
| 2.1c | **Crux, open.** What the two talents *are*: the prevailing reading is a **prize for whichever elder speaks the straightest judgement** (taking 508 `τῷ δόμεν ὃς … δίκην ἰθύντατα εἴποι` of the elders); the competing reading makes them the sum at issue / a deposit by the litigants, in which case they are the *stake*, not a *fee*. | identification | Nicholas Swift, "The Shield of Achilles: Iliad 18.478–608," [Aoidoi.org](http://www.aoidoi.org/poets/homer/il/shield.pdf), October 2005 (CC BY-SA 2.0) — reports the prize reading and lists three candidate referents for `ἴστωρ` | Fetched the document's content and its licence statement; the PDF host's TLS chain fails, so read via the mirrored copy at [yumpu](https://www.yumpu.com/en/document/view/4005917/the-shield-of-achilles-iliad-18478-608-aoidoiorg) |
| 2.1d | **Crux, open.** What the case is *about*: (i) a question of **fact** — has the blood-price been paid or not (`ὃ μὲν εὔχετο πάντ' ἀποδοῦναι … ὃ δ' ἀναίνετο μηδὲν ἑλέσθαι`); or (ii) a question of **law** — whether a feud may be commuted to compensation at all. The choice changes who the two men are and how they stand. | identification | The controversy and both alternatives are stated in the abstract of the open-access paper "Blood-money in Homer — role of *istor* in the trial scene on the shield of Achilles (Il. 18, 497–508)" ([ResearchGate record](https://www.researchgate.net/publication/321920687_Blood-money_in_homer_-_role_of_istor_in_the_trial_scene_on_the_shield_of_Achilles_Il_18_497-508)) | Read the abstract via web search result summary; **full text not read** — see §7 |
| 2.1e | **Crux, open.** Who decides: the assembled people, the elders collectively, or the single `ἴστωρ` of 501. Cunliffe's own gloss cannot arbitrate — see the data gap in §6. | identification | as 2.1d | as 2.1d |
| 2.1f | `δίκη` at 18.508 is Cunliffe's sense 3, **"a judgement or doom"** — not "justice" in the abstract and not "lawsuit". `δικάζω` at 506 is "to pronounce judgment, give a decision". | identification | Cunliffe, *Lexicon*, s.vv. δίκη (sense 3, citing Il. 18.508), δικάζω (sense 1, citing Il. 18.506) | Queried `build/dist/cunliffe/d.json` |
| 2.1g | **Taplin, read in full, does not settle 2.1c–2.1e** — he sets the legal crux aside deliberately: "There has been much discussion of the precise legal problem and procedure here. What matters for present purposes is that we have the stable justice of a civilized city." So the two talents and the `ἴστωρ` stay open, and the plate's caption still carries them. What he *does* add is drawable: `δίκη` at 508 is used "in a sense similar to that in the famous 'Hesiodic' simile at 16.384 ff. **Here is no vendetta** or the perilous exile which Homer and his audience associated with a murderer in the age of heroes. We have, rather, **arbitrators, speeches on both sides, and considered judgements**." The sceptre at 505 is "the symbol of a well-ordered hierarchy". And the `ξεστοὶ λίθοι` of 504 carry Homeric comparanda that fix what they look like: the epithet describes the masonry of Priam's palace (Il. 6.242ff.) and the palace of Zeus (Il. 20.11), and above all the council-stones of Pylos where Nestor sits — "white stones, with a shine on them that glistened" (Od. 3.406–8; cf. Od. 8.6f.). **Draw them as dressed, polished, light-coloured seats**, not field boulders. | identification | Taplin, "Shield of Achilles within the *Iliad*," 6 | **Read in full**, `research-cache/taplin-1980-shield.pdf`; the Homeric parallels re-read in corpus |

**Drawing consequence.** The scene is drawable at full confidence except for one
object's *meaning*: the two talents. Draw them where the text puts them (in the
middle of the circle) and let the caption carry the crux. Do **not** resolve it by
placing them in a litigant's hand or in a herald's.

### 2.2 The singer among the dancers (18.603–606) — and why our own line numbers are ragged

**What our text prints.** Allen's OCT, and therefore our corpus:

```
603  πολλὸς δ' ἱμερόεντα χορὸν περιίσταθ' ὅμιλος
604  τερπόμενοι·
605  δοιὼ δὲ κυβιστητῆρε κατ' αὐτοὺς
606  μολπῆς ἐξάρχοντες ἐδίνευον κατὰ μέσσους.
```

604 is a **half-line**; the TLG XML marks 605 as `n="605*"` — a continuation, not a
whole verse. The words that would fill them are absent:
`μετὰ δέ σφιν ἐμέλπετο θεῖος ἀοιδὸς / φορμίζων·`. **The ragged numbering is the
fossil of the crux.** Line numbers 604–605 exist because an expanded text once
occupied them.

**The parallel, verified in our own Odyssey.** Od. 4.17–19 reads
`τερπόμενοι· μετὰ δέ σφιν ἐμέλπετο θεῖος ἀοιδὸς / φορμίζων, δοιὼ δὲ κυβιστητῆρε
κατ' αὐτούς, / μολπῆς ἐξάρχοντος, ἐδίνευον κατὰ μέσσους.` — the same three lines
**with** the singer, and with the participle in the **genitive singular**
`ἐξάρχοντος` (the singer leads). Our Iliad has the **nominative plural**
`ἐξάρχοντες` (the tumblers lead). The grammar tracks the presence or absence of
the bard exactly.

| # | Claim | Kind | Citation | Verified how |
|---|---|---|---|---|
| 2.2a | **The "sole carrier" hedge is settled, and partly corrected.** Revermann's opening sentence gives the witnesses to the **short** text: "unanimously by our manuscript tradition, five Vulgate papyri from the first to the sixth century A.D., our scholia, and in a quotation in Dionysius of Halicarnassus" (29 — note Dionysius, whom this dossier did not have). But the expanded tradition is **not Athenaeus alone**. A second, independent witness expands the passage: the 'wild' Ptolemaic papyrus **P. Berol. 9774 (Allen's 𝔓51, first century BC)**, which after the tumblers adds a plus-verse of *instruments*, no singer — `ἐν δ' ἔσαν σ]ύριγγε[ς, ἔσαν κίθαρίς τ[ε] καὶ α[ὐλοί` (606a, as restored by S. West). Revermann rejects it: `ἔσαν` "is unmetrical" (and the alternative `ἔσσαν` "unhomeric"), the `ἐν` is used against the Shield's own usage, and an `ὀβελός` stands against the line in the papyrus's own margin — "it can confidently be stated that it is not fit to fill the *lacuna*." | identification | Martin Revermann, "The Text of *Iliad* 18.603–6 and the Presence of an ΑΟΙΔΟΣ on the Shield of Achilles," *Classical Quarterly* 48, no. 1 (1998): 29–38, [doi:10.1093/cq/48.1.29](https://doi.org/10.1093/cq/48.1.29), at 29, 33–34 | **Read in full**, `research-cache/revermann-1998-text-iliad.pdf` |
| 2.2a′ | Nagy's Athenaeus loci and the `ἐξάρχοντος`/`ἐξάρχοντες` split stand; Revermann cites the passage as **Athenaeus V 180c–d, 181a–d** and notes that Athenaeus omits the ἀοιδός-line himself when quoting the passage a second time at V 181a–b. | identification | Gregory Nagy, "A Sampling of Comments on *Iliad* Rhapsody 18," [Classical Inquiries](https://classical-inquiries.chs.harvard.edu/a-sampling-of-comments-on-iliad-rhapsody-18/), 25 November 2016 (updated 20 September 2018); Revermann, "Text of *Iliad* 18.603–6," 34 and 34 n. 18 | Nagy's page read in full; Revermann read in full from `research-cache/` |
| 2.2b | Aristarchus favoured the short version; Nagy reads the long version's singer as "a reference to Homer by Homer, as if he had left behind his own 'signature'". | prose | Nagy, "A Sampling of Comments" (as above) | Read in full on the CHS site |
| 2.2c | Our two printed columns **agree**: the Greek has no singer, and Murray's English reads "…a great company stood around the lovely dance, taking joy therein; and two tumblers whirled up and down through the midst of them as leaders in the dance." | geometry | Il. 18.603–6 (Allen); A. T. Murray, trans., *Homer: The Iliad*, 2 vols., Loeb Classical Library (Cambridge, MA: Harvard University Press, 1924–25) | Read both columns out of `book-18.json` (`segments[0].greek`, `segments[0].english.text`) |
| 2.2d | Perseus's Oxford text (1920) prints the same short version. | geometry | [Perseus, *Iliad* 18 card 590](https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.01.0133%3Abook%3D18%3Acard%3D590) | Fetched; independent witness to our corpus |
| 2.2e | **Revermann's verdict on Athenaeus: against authenticity.** Two objections combine. First, Athenaeus's Aristarchus "is reported to have done three rather peculiar things": he held the ἀοιδός-line spurious in the *Iliad* but genuine in the *Odyssey*; he inserted a passage from one poem into the other; and he explained the Iliadic line as cross-interpolation from the *Odyssey*. "None of this is very plausible. Thus, the quality of Athenaeus' testimony becomes more than dubious. The verse quoted, then, is on a footing with those afforded by the 'wild' papyri." Second, the `θεῖος ἀοιδός` is itself un-Iliadic: the epithet is "absent from the *Iliad*", where singers appear as "rather inconspicuous craftsmen at hand", so the figure is "strikingly at odds with the Iliadic picture" and is better regarded as "a conceptual intrusion in the spirit of the *Odyssey*", probably arising from **rhapsodic intervention**. | identification | Revermann, "Text of *Iliad* 18.603–6," 34–35, 37 | Read in full, `research-cache/revermann-1998-text-iliad.pdf` |
| 2.2f | **But Revermann does not defend our printed text as complete — this is the complication.** He argues the transmitted short text is *defective*: the closing dance is "not only unaccompanied but, apart from the mention of μολπή, even silent", and that silence is "unparalleled on the Shield, in the Homeric epics as a whole, in Ps.-Hesiod, and in the *Homeric Hymns*" (he surveys 101 geometric and early-archaic images in Wegner's catalogue and finds the iconographic evidence "quite inconclusive"). Conclusion: "a lacuna of uncertain length is to be postulated. Mention ought to be made of at least a **φόρμιγξ**… The instrumentalist(s) could be singled out, and there could be an ἀοιδός." He refuses to fill it — "The *lacuna* must remain" — and ends: "our tradition of a particular passage of this ecphrasis is lacunose. There are, however, no means of recovering the 'genuine version' of this passage. In fact, the quest for it would be misguided in principle." The gap sits "with equal plausibility either after τερπόμενοι or after the mention of the tumblers." | identification | Revermann, "Text of *Iliad* 18.603–6," 30–32, 35, 38 | as 2.2e |
| 2.2g | **Taplin leans the other way, and the dossier will not hide it.** "There are in addition a pair of tumblers and, if we are prepared to import a line from the otherwise identical formulae at *Od.* 4.17–19…, we would have a poet, the one and only ἀοιδός to appear in the *Iliad*. **We might feel that the shield would not be complete without him.**" His note: "Most editors since Wolf have included the line and believed that it was wrongly ejected by Aristarchus… But all the experts on Aristarchus are quite clear that Athenaeus cannot have got his facts right… The case for the line must stand or fall without Athenaeus." | prose | Oliver Taplin, "The Shield of Achilles within the *Iliad*," *Greece & Rome* 27, no. 1 (1980): 1–21, at 9 and 20 n. 27 | Read in full, `research-cache/taplin-1980-shield.pdf` |

**Drawing consequence, and it is a hard one. UNCHANGED after reading Revermann.**
*Do not draw a bard on the dancing floor.* The site's own printed text has no
singer; a plate that shows one would contradict the edition on the page beside
it. Revermann's philology now adds a second, independent ground: the specific
figure Athenaeus supplies — the `θεῖος ἀοιδός` — is un-Iliadic and probably
rhapsodic (2.2e). The two **tumblers** (`κυβιστητῆρε`) in the middle **are** in
our text and must be there. If the plate wants the crux, it belongs in a note,
never in the line work. The boy with the lyre at **569–71** is a different figure
in a different scene (the vineyard) and is fully in the text — draw him there
without hesitation; Revermann counts him among the Shield's instrumentalists and
notes that the vintage dance is the one Shield dance that *is* accompanied
(Revermann 30).

> **FLAG FOR JOHN — do not let a drawing lane resolve this.** The two scholars
> who have now actually been read on this passage **both hold that the text as we
> print it is incomplete**, and both put the gap exactly where the plate's dance
> scene is. Revermann would restore at least a `φόρμιγξ` and will not say what
> else; Taplin would restore the singer and thinks most editors since Wolf were
> right to. Neither licenses a bard on the plate. What they do mean is that a
> plate showing a **silent** dance reproduces a text two of its own sources call
> defective. Three responses, and the choice is editorial, not philological:
> (i) draw the dance as printed and say nothing; (ii) draw it as printed and let
> the caption carry the lacuna briefly — "some ancient copies gave instruments
> here, one gave a singer; the text we print gives neither, and Revermann 1998
> holds the passage lacunose"; (iii) draw instruments without a singer, which no
> text of ours prints. **Recommended: (ii). Not recommended: (iii).** The
> no-bard rule stands under all three.

---

## 3. Structure: how many zones does the evidence actually support?

### 3.1 What the text says about arrangement

| # | Claim | Kind | Citation | Verified how |
|---|---|---|---|---|
| 3.1a | **The poem never states a number of bands, and never says the scenes are concentric.** It marks nine `Ἐν` units and locates exactly **one** of them: Ocean, `ἄντυγα πὰρ πυμάτην` (607–8). Every other position on the disc is unstated. | geometry | Il. 18.478–608, esp. 607–8 | Full enumeration of the passage; §1.2/1.3 above |
| 3.1b | Ten bands in spectrum order is therefore **not a reading of the text**. It is one hypothesis (nine units, cities split) rendered as a ring chart. | geometry | as 3.1a | The current plate's own `bands[].ring` 0–9 in `apparatus/plates/shield-of-achilles.json` |
| 3.1c | The **only** compositional instruction the poem gives is a **scale hierarchy**: Ares and Athene are `καλὼ καὶ μεγάλω … ἀμφὶς ἀριζήλω`, "while the people were smaller" (`λαοὶ δ' ὑπολίζονες ἦσαν`, 519). Bronze Age and archaic images do this; a ring chart cannot. | geometry | Il. 18.517–19 | Corpus |
| 3.1d | Ten concentric `κύκλοι` **do** occur in Homer — on **Agamemnon's** shield (Il. 11.32–35: `κύκλοι δέκα χάλκεοι`, twenty white tin bosses, dark κύανος in the middle). Achilles' shield never gets a ring count. Importing the ten from Book 11 is a category error. | geometry | Il. 11.32–35 | Read in corpus, `book-11.json` |
| 3.1e | **Open question, still open — but the dossier had the attribution backwards, corrected 2026-07-29.** Taplin's n. 13 verbatim: "It would undoubtedly make most sense if line 483 ('land, heaven, sea') were a summary of the entire shield, and 484–9 the details of the first circle, showing only the heavens: **this is maintained by Fittschen, op. cit., p. 10.** But there are difficulties, above all the construction of line 484; this interpretation is impossible without emendation." So the summary reading is **Fittschen's**, and the emendation objection is **Taplin's** — the reverse of what this dossier said. In his own scheme Taplin takes 483–9 as the first circle entire, and holds that the microcosm "would… have been clear to the original audience from the first line (483)". | geometry | Taplin, "Shield of Achilles within the *Iliad*," 5, 11, 19 n. 13; Klaus Fittschen, *Bildkunst, Teil 1: Der Schild des Achilleus*, Archaeologia Homerica II N 1 (Göttingen: Vandenhoeck & Ruprecht, 1973), 10 (cited here at one remove — Fittschen still unread, §7) | **Read in full**, `research-cache/taplin-1980-shield.pdf` |
| 3.1f | **Hardie's frame is a two-group structure, and it is the strongest compositional constraint any read source gives.** "The scenes on the Homeric Shield of Achilles fall into two groups, defined both by their content and by the scale of their treatment. The first group (*Il.* xviii 483–9, 607 f.) consists of briefly detailed scenes of the main features of the universe… and, concluding the description (607 f.), the stream of Ocean running along the outer rim of the Shield. **The second group (490–606), framed by the first**, consists of scenes of human life in the town and country, and constitutes the great bulk of the ecphrasis." Cosmos and Ocean are **one frame around one field** — not two of N co-equal bands. This is directly drawable and it is not a ring chart. | geometry | Hardie, "*Imago Mundi*," 11 | **Read in full**, `research-cache/hardie-1985-imago-mundi.pdf` |
| 3.1g | **Hardie also denies that the human scenes schematise at all.** "The general impression of this group is of a teeming abundance, and schematization does not readily suggest itself; an unbiased observer might suspect that a simple principle of addition, rather than any more elaborate pattern of symmetry, had been responsible for the final conglomeration of subjects." And the reason schemes keep getting invented: the cosmic group, "by reason of both its positioning and its brevity, is the most easily remembered part of the Shield, and its universalizing character tends to determine the interpretation of the second group of scenes when these are brought under scrutiny." Independent confirmation of §3.4's verdict, from the paper the dossier previously cited *for* a cosmic scheme. | geometry | Hardie, "*Imago Mundi*," 11 | as 3.1f |
| 3.1h | **Taplin adopts a five-circle scheme and disowns it in the same breath.** His headings: I 483–9 earth, heavens and sea (inmost); II city life (both cities, 490–540); III rural life (541–89); IV the dance (590–606); V Ocean (outmost). His caveat, in full because it matters: "The precise plan of the shield is not made so clear by the poem that it is beyond doubt; and we should bear in mind Lessing's point that we are told of the making of the shield not given a map of the finished product. **It is not even clear that the shield is to be envisaged as decorated with five concentric circles.** Moreover it is not likely that our text is exactly as it left Homer… The divisions and arrangement which I shall adopt are widely accepted and make, I think, a coherent whole; but they are not essential to my argument." A published, *widely accepted* five-band concentric scheme therefore exists — held by its own author as a convenience, not as the poem's. | geometry | Taplin, "Shield of Achilles within the *Iliad*," 5, with the five headings at 5–11 | as 3.1e |
| 3.1i | **On the 509 boundary Taplin does not split the field: the two cities are one circle.** "The two cities are clearly set out as a pair—see 490–1, 509." He gives the peaceful city two members (491–6 wedding, 497–508 law case) and the war city three (509–19 siege, 520–34 ambush, 535–40 mêlée). **The pulled plate's split of the cities into two of ten co-equal rings has no warrant in the one first-hand structural source we now hold.** Taplin does read a compositional *contrast* between them, which is drawable: the war city's women, old men and children are **on the walls**, "rather than in their doorways or in the *agora* as in the city at peace" — porch and assembly against battlement, closest parallel Il. 8.518–22. | geometry | Taplin, "Shield of Achilles within the *Iliad*," 5, 6–7 | as 3.1e |
| 3.1j | **Taplin reads the four rural scenes as a cycle of the seasons:** 541–9 spring ("the emphasis on the fertility of the soil"), 550–6 summer ("The harvest is hot, hungry work"), 561–7 autumn (the grape harvest), and "Seeing that the first three clearly represent spring, summer and autumn, I take it that 573 ff. shows winter" — the cattle are kept in the midden-yard (`κόπρον`, 575) "during the winter nights". Against the objection that a four-season year post-dates Alcman he answers that "all four of Alcman's words—ἔαρ, θέρος, ὀπώρη, χεῖμα—are to be found in Homer." **Two consequences, neither adopted silently:** (i) his spans differ from ours — he writes 550–6 for our 550–60, 561–7 for our 561–72, and groups 573–89 as one winter scene, i.e. he folds the sheep pasture into the cattle scene while doubting its authenticity (§1.2); our spans are machine-checked against the `Ἐν`-boundaries and stand. (ii) See the contradiction logged in §3.4. | geometry | Taplin, "Shield of Achilles within the *Iliad*," 7–9, 19 n. 22 | as 3.1e |

### 3.2 What the commentators say

| # | Claim | Kind | Citation | Verified how |
|---|---|---|---|---|
| 3.2a | Edwards gives the shield a **ten-page introduction, pp. 200–209**, much of it on physical construction. | prose | Mark W. Edwards, *The Iliad: A Commentary*, vol. 5, *Books 17–20* (Cambridge: Cambridge University Press, 1991), 200–209 | **Second-hand**: Robert Schmiel, review of Edwards vol. 5, [*Bryn Mawr Classical Review* 1992.03.05](https://bmcr.brynmawr.edu/1992/1992.03.05/) |
| 3.2b | Edwards: "The poet *clearly visualizes* a round shield… There are *indications* that the layers of hide" were concentric, with a metal composition that "makes little *practical sense*" (Edwards 201–202). | geometry | Edwards, *Iliad* vol. 5, 201–2 | **Second-hand, quoted in** Schmiel, BMCR 1992.03.05. Treat as Edwards's words at one remove until the volume is checked |
| 3.2c | Edwards hazards that the **two armies of 18.509 were probably one army**, the doubling arising from "misinterpretation of a two-dimensional picture" (Edwards 207). **This is a live geometry claim about our scene 2b** and it contradicts the plain sense of `δύω στρατοὶ … λαῶν`. | geometry | Edwards, *Iliad* vol. 5, 207 | **Second-hand**, quoted in Schmiel, BMCR 1992.03.05, who reports it disapprovingly |
| 3.2d | Schmiel's counter-position: treating "the shield as if it were real … does not advance my understanding or appreciation of the poem one whit", turning Homer into "a how-to handbook for armourers". A named, citable objection to the whole reconstruct-it project. | prose | Schmiel, BMCR 1992.03.05 | Read in full |
| 3.2e | Edwards's own preferred interpretive authority is **Marg's essay** — now identified via Taplin n. 1 as *Homer über die Dichtung* (1957; 2nd edn. 1971), see §8.6 — which Schmiel notes warns against exactly the technical approach Edwards takes. | prose | Schmiel, BMCR 1992.03.05; Taplin, 18 n. 1 (the identification) | Read in full |
| 3.2f | Concentric decorated bands have **material parallels** in Cretan shields and Phoenician bowls, per Edwards. | identification | Edwards, *Iliad* vol. 5, ad 18.478–608 (page not established) | **Weak chain**: reported in a web-search synthesis of the Edwards commentary, not read in a source I can pin. Do not cite Edwards for this until checked. The underlying object classes are real and separately citable: Emil Kunze, *Kretische Bronzereliefs*, 2 vols. (Stuttgart: W. Kohlhammer, 1931) for the Idaean Cave shields; Glenn Markoe, *Phoenician Bronze and Silver Bowls from Cyprus and the Mediterranean*, University of California Publications in Classical Studies (Berkeley: University of California Press, 1985) |
| 3.2g | Fittschen's fascicle **catalogues attempts to reconstruct the shield from the sixteenth century onward** — it is the bibliography of every plate in §4, in 28 pages with 8 figures and 10 plates. **Pages now known from citations in the read papers, which sharpens the §7 request:** p. 1 n. 1 (whether the Athena Parthenos shield alludes to the Homeric one), p. 2 (artistic representations generally), pp. 4–5 (bibliography of the "shield was a real heirloom" views), p. 10 (Fittschen's own reading of 483 as a summary of the whole shield — 3.1e). | identification | Fittschen, *Der Schild des Achilleus* (1973), 1 n. 1, 2, 4–5, 10 | Bibliographic details and extent verified from the [Classical Review notice on Cambridge Core](https://www.cambridge.org/core/journals/classical-review/article/abs/klaus-fittschen-bildkunst-teil-1-der-schild-des-achilleus-archaeologia-homerica-bd-ii-kap-n-teil-1-pp-28-8-figs-10-pls-gottingen-vandenhoeck-ruprecht-1973-paper-dm-1650/B3CC8076D0903F547E13AD87EF65C5F7) and [Open Library](https://openlibrary.org/books/OL4828152M/Der_Schild_des_Achilleus.); the page references from Taplin 18 n. 5, 19 nn. 9 and 13, and Hardie 18 n. 49, 30 n. 132. Contents still **not read** |
| 3.2h | **Taplin, first-hand, on the two armies: two of them, and their relation obscure.** "On the shield there are *two* besieging armies (their relation to each other is obscure), but like the Achaeans they are not agreed among themselves." A read source therefore preserves the plain sense of `δύω στρατοὶ … λαῶν` while conceding the difficulty that Edwards is reported (3.2c) to solve by reduction. **Cite Taplin for this, not Edwards.** Taplin also identifies the war city as Troy — "The city on the shield stands for every threatened homeland: within the *Iliad* Troy is such a city" — with Hector's orders at Il. 8.518–22 as the closest parallel. | geometry | Taplin, "Shield of Achilles within the *Iliad*," 6–7 | Read in full, `research-cache/taplin-1980-shield.pdf` |
| 3.2i | **What the Shield omits** — Taplin's list, which is a drawing instruction in negative form: "The shield omits, for instance, poverty and misery; it omits trade and seafaring; it does not figure religion or cult, and it does not figure mythology or named heroes and places." **A tension inside his own claim, recorded not harmonised:** the dance simile names Daedalus, Ariadne and Knossos (591–2); Ares, Athene, Eris, Kydoimos and Ker are named (516–17, 535); an ox is sacrificed at 559 and the elders sit in a `ἱερὸς κύκλος` (504). Read the list as a claim about **proportion and emphasis** — no seafaring, no trade, no poverty, no temple, no hero-narrative — not as an absolute. It is still the sharpest available answer to "what must *not* be on this plate." | geometry | Taplin, "Shield of Achilles within the *Iliad*," 12 | as 3.2h; counter-instances read in corpus |
| 3.2j | **Proportion, stated by a scholar rather than inferred by us:** "On the shield the *Iliad* takes up, so to speak, **one half of one of the five circles.**" Independent confirmation of §3.4's arithmetic objection to equal-width rings, and a usable caption line. | geometry | Taplin, "Shield of Achilles within the *Iliad*," 12 | as 3.2h |
| 3.2k | **Which scene is the climax — a live dispute the plate must decide, and can now decide with citations.** Taplin: the dance's "length and unity… make it appear the climax of the whole shield"; "in several respects this section forms a 'ring' with the wedding scene at the beginning"; and, a geometry claim in its own right, "**It appears that the dance goes all the way round without subdivision.**" Kakridis supplies comparative material that "the main scene of an 'imagined ekphrasis' should come last"; Gaertner argues instead that the king's `τέμενος` (550–60) is the climactic scene, "but he does not refute Kakridis." | geometry | Taplin, "Shield of Achilles within the *Iliad*," 9 and 20 n. 26, citing J. T. Kakridis, *Homer Revisited* (Lund: Gleerup, 1971), 108ff., esp. 123, and H. A. Gaertner, "Beobachtungen zum Schild des Achilleus," in *Studien zum antiken Epos*, ed. H. Görgemanns and E. A. Schmidt (Meisenheim: Hain, 1976), 46ff., at 53 n. 18 | as 3.2h |
| 3.2l | **A drawable detail corrected.** At 558–60 the white barley is sprinkled **on the meat**, not served as barley mash: "The heralds have performed the slaughter and jointing; the women are actually cooking it, and this involves sprinkling the meat with barley, exactly as at *Od.* 14.77." That is **Leaf's** interpretation, which Taplin prefers **against Kirk's** (Kirk, *HOT* 12, has the king eating the roast beef while the workers get barley mash): Taplin "cannot see any reason for preferring this to the interpretation well argued for by Leaf." (A first draft of this row swapped Leaf and Kirk — caught at Grok verification against the PDF.) | identification | Taplin, "Shield of Achilles within the *Iliad*," 19–20 n. 23 | as 3.2h |
| 3.2m | **The Phoenician-bowl parallel no longer needs Edwards.** Revermann, read first-hand: the bowls, "produced over a period from about 850 to about 625", have an iconography "so similar to that of the Homeric Shield that they are regularly invoked as a model or inspiration for the Homeric description… here the correspondences are so great and unique that it is difficult not to see a connection." He also states both standard objections, after Erika Simon: "bowls are not shields. And the Phoenician bowls are chased work whereas **the decorations of the Shield must be inlaid work.**" Markoe's pages for the iconography are **56–59**; the dance bowls are Markoe's Cy3, Cr 7 and G8, his periods I–II. | identification | Revermann, "Text of *Iliad* 18.603–6," 31 and 31 nn. 10–12, 32 n. 12, citing Markoe, *Phoenician Bronze and Silver Bowls*, 56–59, and Erika Simon, "Der Schild des Achilleus," in *Beschreibungskunst — Kunstbeschreibung*, ed. Gottfried Boehm and Helmut Pfotenhauer (Munich: Fink, 1995), 129f. | Read in full, `research-cache/revermann-1998-text-iliad.pdf` |

### 3.3 The interpretive frame (for the plate's prose, not its geometry)

| # | Claim | Kind | Citation | Verified how |
|---|---|---|---|---|
| 3.3a | Taplin's question is the plate's subtitle if it wants one: "Why is the shield of Achilles, instrument of war in a poem of war, covered with scenes of delightful peace, of agriculture, festival, song, and dance?" His own answer, at the end: the shield "makes us think about war and see it in relation to peace… The shield of Achilles brings home the loss, the cost of the events of the *Iliad*" — the two finest things in the poem, Achilles and Troy, "will never again enjoy the existence portrayed on the shield: that is the price of war and of heroic glory." | prose | Taplin, "Shield of Achilles within the *Iliad*," 1, 15 | **Read in full**, `research-cache/taplin-1980-shield.pdf` (the sentence opens the article at p. 1) |
| 3.3b | Hardie reads the shield as an **imago mundi** — a cosmological and ideological whole, not a genre scene collection. Read first-hand, the warrant is sharper than the dossier claimed: it supports keeping cosmos and Ocean as a *frame* around the human scenes (3.1f), and it warns that the frame's memorability is what makes readers over-schematise the field inside it (3.1g). | prose | P. R. Hardie, "*Imago Mundi*: Cosmological and Ideological Aspects of the Shield of Achilles," *Journal of Hellenic Studies* 105 (1985): **11–31** | **Read in full**, `research-cache/hardie-1985-imago-mundi.pdf`. **START PAGE SETTLED: 11.** The JSTOR cover page, the article's own running head ("*Journal of Hellenic Studies* cv (1985) 11–31") and the printed page number on the opening page all give 11; the title, abstract-less opening and section I heading are all on p. 11. Every "12" in circulation is wrong — fix it wherever it appears |
| 3.3c | Becker's argument, which cuts against any tidy plate: Homeric ekphrasis works by a "double movement of illusion and disillusion" — oscillation between absorption in the depicted world and awareness of the material means. 548–49 (gold field that looks like dark earth, `περὶ θαῦμα`) is Homer doing this in two lines. | prose | Andrew Sprague Becker, *The Shield of Achilles and the Poetics of Ekphrasis*, Greek Studies: Interdisciplinary Approaches (Lanham, MD: Rowman & Littlefield, 1995) | Argument summary read from the [BMCR review 1995.11.02](https://bmcr.brynmawr.edu/1995/1995.11.02/) and the publisher/JHS notice; **book not read** |
| 3.3d | Lessing's objection is the oldest one on the record and the most dangerous for this plate: Homer describes the **making**, in motion, not a finished object; the ploughmen turn, the field darkens, the dogs bark and shrink. A still plate necessarily loses what the passage is doing. | prose | Gotthold Ephraim Lessing, *Laokoon, oder über die Grenzen der Malerei und Poesie* (Berlin: Voss, 1766), **chs. 17–19** | The attribution of this point to Lessing is confirmed by Gregory Nagy's essay ("In painting a picture through poetry, Lessing argues, the poet chooses not to confine himself to the limits of the art of making pictures"), [cyber.harvard.edu](https://cyber.harvard.edu/heroes/content/cybershield2.html), orig. in *New Light on a Dark Age*, ed. Susan Langdon (Columbia: University of Missouri Press, 1997), 194–207. **Chapters settled 2026-07-29:** Taplin cites the point as "Lessing, *Laocoon*, ch. 17–19" (Taplin 19 n. 12, read in full from `research-cache/`), and states it in his own text at p. 5: "we should bear in mind Lessing's point that we are told of the **making** of the shield not given a map of the finished product." Also there: H. A. Gaertner, "Beobachtungen zum Schild des Achilleus," 46ff. |
| 3.3e | Nagy reads the **lawsuit** itself as concentric — elders in an inner circle, the people around them judging which elder judges best, and the *Iliad*'s own audience as the outermost circle. If the plate wants a concentric idea with a scholarly warrant, this is one, and it is local to scene 2a. | prose | Nagy, in *New Light on a Dark Age*, 194–207; online at [cyber.harvard.edu](https://cyber.harvard.edu/heroes/content/cybershield2.html) | Read the online version in full |
| 3.3f | **"Imago mundi" is Ovid's phrase, not Hardie's coinage** — `nec clipeus vasti caelatus imagine mundi / conveniet timidae nataeque ad furta sinistrae`, Ajax on why Ulysses may not carry the shield (*Met.* 13.110–11); Silius echoes it of Achilles' arms, `clipeo amplexus terramque polumque / maternumque fretum totumque in imagine mundum` (*Pun.* 7.122). Hardie sets both beside the Greek `κόσμου μίμημα`, the phrase the Pergamene scholar **Crates of Mallos** applied to Homeric shields. Ovid, following the allegorists, selects out of the whole ecphrasis exactly two things: the cosmological representations and the two cities. Usable for the plate's caption — the microcosm reading is ancient and it has a Latin tag. | prose | Hardie, "*Imago Mundi*," 16–17, 24 | Read in full, `research-cache/hardie-1985-imago-mundi.pdf` |
| 3.3g | **The plate's own register question has an ancient precedent for both answers.** Hardie: representations of the Shield split into "that in which the universe is represented by an image of the heavens, and that in which divisions of the universe other than the sky are explicitly depicted" (i.e. celestial-diagram versus human-scene shields), and "**Schematic universality appears only in Roman works** which are likely to draw on an iconography developed in Hellenistic times." Early Greek vase-painting made no attempt at the Homeric scenes at all: "the device or devices on the Shield usually bear no relation to the Homeric text," and "over thirty separate devices are found on representations of the shield of Achilles in early Greek art." A plate that depicts the *scenes* is therefore doing something the Greeks themselves did not do — worth one honest sentence in the plate's note. | identification | Hardie, "*Imago Mundi*," 18 and 18 n. 49 | as 3.3f |

### 3.4 Verdict on zone count

**The evidence supports "nine units, one of them double" as the text's own
division, and supports NO statement about their arrangement except that Ocean is
at the rim.** Everything between the rim and the centre is a reconstructive
choice the plate must own as its own, in the schematic register, with the
`sources` field naming what it followed. Specifically:

- **9** — the `Ἐν`-marked units (483, 490, 541, 550, 561, 573, 587, 590, 607).
  Textual. Machine-checkable against the corpus.
- **10** — 9 with the two cities split at 509. Defensible as a design choice; what
  the pulled plate did. **Now known to have no support in the one first-hand
  structural source we hold:** Taplin makes the two cities a *pair inside one
  circle* (3.1i).
- **Fewer** — grouping 541/550/561 as one agricultural estate, or 573/587 as one
  pastoral. **CORRECTION, 2026-07-29:** this dossier said "the text does not
  license it, and it should be labelled as design if used." The first half stands;
  the second is too weak. Taplin groups exactly this way and gives a *reason* —
  the four rural scenes are the four **seasons** (3.1j) — so a plate that groups
  them is following published scholarship, not merely compressing for looks. Cite
  Taplin 7–9 and 19 n. 22 if you group; do not present the seasons as the poem's
  own statement, because they are not stated.
- **5** — the `πέντε πτύχες` are structural and give no zones (§1.1b–c), and that
  holds. But "5" is no longer a count with nothing behind it: **Taplin's own
  scheme is five concentric circles** (cosmos / cities / country / dance / Ocean,
  3.1h), derived thematically rather than from the layers, and he calls the
  divisions "widely accepted" while denying they are certain. The ancient
  allegorists also got five rings out of the layers (§1.1d). A five-band plate is
  therefore citable; a five-band plate that says *the poem gives five* is not.
- **2** — the count no one in this dossier proposed and the one the read
  scholarship best supports: **Hardie's cosmic frame around a single human field**
  (3.1f). If the plate wants an arrangement with a first-hand scholarly warrant
  rather than a reconstruction of its own, this is it.
- Proportion is a real problem no ring chart solves: **32 lines** for the besieged
  city against **3** for the sheep pasture, and **2** for Ocean. Equal-width rings
  misrepresent the poem by a factor of ten. Taplin says the same from the other
  end: "On the shield the *Iliad* takes up, so to speak, one half of one of the
  five circles" (3.2j).

**Contradictions logged, not harmonised** (per the brief; each is a place where a
newly-read paper disagrees with something this dossier or the pulled plate
asserted):

1. **§3.1e had Fittschen and Taplin the wrong way round** on the 483-as-summary
   reading. Fixed in place at 3.1e. The dossier's own error, not a source's.
2. **The city split at 509 into two co-equal rings** — contradicted by Taplin
   3.1i, who keeps the pair in one circle.
3. **"Grouping the rural scenes is unlicensed compression"** — contradicted by
   Taplin's seasonal reading, 3.1j. Corrected above.
4. **"The scene table's spans are what every scholar uses"** was never claimed,
   but note that Taplin's *are* different: 550–6, 561–7, 573–89 against our
   550–60, 561–72, 573–86, 587–9 (3.1j). Ours are machine-checked against the
   `Ἐν` boundaries and stand; the divergence is recorded so nobody "fixes" the
   table against Taplin.
5. **§4's "three historically distinct compositional schemes," all post-1715** —
   contradicted by Hardie 21: an **ancient** circular reconstruction survives
   (4h below), and it is neither a quadrant scheme nor concentric-per-scene.
6. **Both cities as bands of a ring chart at all** — Hardie 11 says the human
   scenes resist schematisation and that the impulse to schematise them is an
   artefact of the cosmic frame's memorability (3.1g). No source read so far
   endorses one-ring-per-scene.
7. **The metals reading is *not* contradicted** by any of the three. Revermann
   independently states the register: "the decorations of the Shield must be
   inlaid work" (3.2m, §5.3g).

---

## 4. Visual reconstructions: what has been tried, and what we may use

Three historically distinct compositional schemes, each with a public-domain
exemplar. This is the design menu, with provenance.

**Amended 2026-07-29: the menu does not begin in 1715.** Hardie, now read,
documents an **ancient** attempt to lay the whole ecphrasis out on a disc — the
Tabula Iliaca fragment Sadurska 4N, first half of the first century AD — and it
follows neither the quadrant family nor one-ring-per-scene. It is listed as **4h**
below, last only because it was found last; chronologically it is first, and it is
the only exemplar in this table made by someone for whom Homer was living
literature. **4i** records the other ancient family, the celestial-diagram shield
of the Pompeian paintings.

| # | Reconstruction | Scheme | Licence under US rules (pre-1931 = PD) | Kind | Verified how |
|---|---|---|---|---|---|
| 4a | **Boivin, 1715** — *Apologie d'Homère et bouclier d'Achille* (Paris, 1715), plate VII, p. 322; drawn by **Nicolas Vleughels** (1668–1737), engraved by **David Coster**. | Divided field; the ancestor of the "isolated by quadrant" family. | **PD.** On Wikimedia Commons under **CC0**; 1,893 × 1,958 px. [File page](https://commons.wikimedia.org/wiki/File:Bouclier_d%27Achille_drawing_by_Nicolas_Vleughels_engraving_by_David_Coster_plate_VII_pg_322_Apologie_d%27Homere_et_bouclier_d%27Achille_ca._1715_IMG_3239_Bouclier.jpg) (digitised by the ENS library) | identification | Fetched the Commons file page: publication, plate number, artist, engraver, licence, resolution all read there |
| 4b | **Pope, 1720** — "Observations on the Shield of Achilles," in *The Iliad of Homer*, vol. 5 (London, 1720), plate at p. 171; engraved by **Samuel Gribelin junior** after **Vleughels**. Pope's essay reprints **Boivin's** "regular plan and distribution" before offering his own reading of the shield as a work of painting. | Boivin's scheme, in English, in the volume whose 1716 map is already the acknowledged ancestor of our schematic register (`docs/TROAD-CARTOGRAPHY.md`). | **PD.** Two Commons files: `File:THE ILLIAD OF HOMER (translated by POPE) p5.171 The Shield of Achilles.jpg` and `File:1720 image from THE ILLIAD OF HOMER (translated by POPE) pg 171 Vol 5 The Shield of Achilles.png` (British Library via Commons) | identification | Commons category enumerated via the [MediaWiki API](https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Shield_of_Achilles&cmlimit=100&format=json); the essay's dependence on Boivin and Dacier and the Gribelin/Vleughels attribution from a [PMLA article landing page](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/1E9AB839279A713DB96B27C8337A601B/S0030812900048239a.pdf/achilles_shield_some_observations_on_popes_iliad.pdf) surfaced in search. **Pope's own text of the essay not read** (the ECCO copy returns 403) — §7 |
| 4c | **Quatremère de Quincy, 1809/1814** — reconstruction published in *Le Jupiter olympien, ou l'art de la sculpture antique* (Paris: Didot, 1814), plate 2 (INHA NUM FOL VA 328). | **Abandons quadrants**: two circles (city and country) carrying **eight continuous sequences** that run into one another, Apollo's chariot at the centre, a circle of stars with the sun and zodiac signs. Flat figures, no perspective or cast shadow, line-driven. | **PD.** Two Commons files: `File:The shield of Achilles according to the description of Homere by Quatremere de Quincy.jpg`, `File:The Shield of Achilles by Quatremere de Quincy ca. 1814.jpg` | geometry (as a proposal) + identification | Publication details and plate number fetched from the [Utpictura18 notice](https://utpictura18.univ-amu.fr/notice/15486-bouclier-dachille-quatremere-jupiter-olympien-1814); the compositional description (quadrants abandoned, two circles, eight continuous sequences, Apollo, zodiac) came from a **web-search synthesis of French sources including Utpictura18 and the BnF**, not from a single page I read in full — **treat the eight-sequence count as unconfirmed, §8** |
| 4d | **Flaxman / Rundell, 1810–23** — designed by **John Flaxman** (1755–1826) for Rundell, Bridge & Rundell; 24 drawings and 5 models between 1810 and 1818, design finished 1817, modelled and cast in plaster by Flaxman; silver-gilt cast bought by George IV, hallmarked 1821–22, shown at the coronation banquet 1821 (**RCIN 51266**, Royal Collection). Engraved by **A. R. Freebairn**, plates dated 15 March 1846. | **Centre + one broad frieze + wave rim**: Apollo driving the chariot of the sun on a rayed ground at the centre, surrounded by constellations; a **single broad low-relief border** carrying the human scenes in sequence (wedding and banquet, siege, ambush and engagement, harvest, judicial appeal, vintage, oxherds defending their beasts, a Cretan dance); an outer border of **stylised waves** and a broad reeded rim. | **Design PD** (Flaxman d. 1826; Freebairn's engraving 1846). **Photographs of the object are separately copyrighted** — RCT images are restricted; the Commons files that exist are CC0 photos by a third party (`File:Flaxman shield of achilles cc0 pub dom photo by Thad Zajdowicz …`). | geometry (as a proposal) + identification | Scheme and provenance from the [Royal Collection Carlton House entry, RCIN 51266](https://www.rct.uk/collection/publications/carlton-house/shield-of-achilles) and the [Royal Academy record of the Freebairn portfolio](https://www.royalacademy.org.uk/art-artists/book/the-shield-of-achilles-by-john-flaxman-r-a-dedicated-by-permission-to-the), read via search-result synthesis of both pages; Commons filenames from the API enumeration |
| 4e | **Angelo Monticelli** (early 19th c.) — `File:Angelo monticelli shield-of-achilles.jpg` on Commons. | Not examined. | Presumed PD (Monticelli d. 1837); **not verified**. | identification | Filename only, from the API enumeration — §8 |
| 4f | **Rijksmuseum engravings** — `File:Schild van Achilles Bouclier d'Achille, RP-P-1964-2426.jpg`, `File:Schild van Achilles, RP-P-OB-42.824.jpg`. | Not examined. | Rijksmuseum releases PD works openly; **not verified per file**. | identification | Filenames only — §8 |
| 4g | **Kathleen Vail**, *The Shield of Achilles* (1998–, [theshieldofachilles.net](https://theshieldofachilles.net/)) — a Bronze-Age-technique artistic reconstruction. | Not usable. | **IN COPYRIGHT.** The site states: "Copyright © 2018 Kathleen Vail. All images of Vail's reconstruction of the Shield of Achilles are under copyright, with all rights reserved," and explicitly forbids redistribution. **Consultable as a source; never reproduced, traced, or redrawn from.** | identification | Fetched the site's own copyright statement |
| 4h | **'Tabula Iliaca', Sadurska 4N** (Rome, Musei Capitolini; Hardie's PLATE Id) — a fragmentary **circular relief copy of the Shield of Achilles**, one of two independent such reliefs, both carrying the name of Theodorus in a magic square on the reverse, dated to the first half of the first century AD. Slightly more than half preserved, broken along a line from top left to bottom right. | **The earliest attested layout, and it is a fourth scheme.** Working inward: (i) a **sloping outer rim engraved with the Homeric text** of the Shield; (ii) a more sharply sloping band of **heavenly bodies** — Helios in his quadriga at the top, Selene in her biga at the bottom, both moving clockwise, with six rectangular panels at regular intervals between them for one half of the twelve zodiac signs; (iii) **Ocean as an incised elongated zig-zag of paired parallel lines** framing the central field (Sadurska's reading) — note that Ocean is thus brought *inside* the circle of heaven; (iv) the central field, of **activities on earth arranged in superimposed horizontal bands**, cut across the middle by an inscribed band reading `Ἀσπὶς Ἀχιλλῆος Θεοδώρησ καθ' Ὅμηρον`. Content as preserved: upper half left, the walls and porticoes of the **city at peace** with the lawsuit (497 ff.) above the marriage procession (491 ff.); upper half right, lost, "most plausibly occupied" by the **city at war**, completing the symmetry; lower half centre, the walled `ἀλωή` of 561 ff.; below and right of it ploughing, reaping and binding (541 ff.), sheaves loaded on a wagon (**not in Homer**) and the harvesters' meal under a tree (558 ff.); above the `ἀλωή`, **nine dancers arranged in a circle** for the chorus of 590 ff. Hardie's inferred scheme: "The upper half is divided between the contrasting scenes of the city at peace and the city at war, while a division between town and country determines the assignment of scenes to the upper and lower halves respectively." | **The object is ancient and out of copyright by age.** Hardie's PLATE Id photograph (JHS 1985) and Sadurska's drawings (1964) are **not** ours to reproduce; take the *scheme* only, per the posture note below. Jahn–Michaelis's 19th-c. drawings of the related Sarti (6B) and Chigi fragments — Hardie's FIGS. 1 and 2 — are PD by age but were reproduced from Jahn–Michaelis, so use the original publication if an image is ever wanted. | geometry (an attested composition, not a proposal) + identification | Hardie, "*Imago Mundi*," 21–22 with PLATE Id and FIG. 1, citing A. Sadurska, *Les Tables Iliaques* (Warsaw, 1964), 43ff., no. 4N; inscriptions at *IG* xiv 1296. **Read in full**, `research-cache/hardie-1985-imago-mundi.pdf` |
| 4i | **Pompeian 'Thetis in the forge' paintings, Fourth Style** — eight known versions; Hardie's type A (six examples) shows the finished Shield frontally on the anvil. Most elaborate: the 'Domus Uboni' (PLATE Ia); also Casa di Sirico (PLATE Ib). | **The celestial-diagram scheme — no human scenes at all.** A plain outer ring; the edge of the convex central field ringed with the **signs of the zodiac running anti-clockwise**; on the central field, three stars, four busts (Scherf: winds; Hardie: possibly seasons, but "four is an awkward number" inside a zodiac ring) and a long winding **snake, best understood as Draco**, "which separates the two Bears of the pole." Hardie: "This celestial diagram can be understood as a two-dimensional representation of the celestial *sphaira*," and the zodiac-ring probably derives from **Crates of Mallos**'s allegorisation. A shield of the cosmos with the whole human world left off — the exact opposite editorial choice from ours, and worth naming in the plate's note as the road not taken. | Objects ancient; the wall-paintings are ruined ("the painting has now deteriorated to the point where nothing can be made out on the surface of the shield" for the Domus Uboni example) and the plate photographs are from Herrmann–Bruckmann, *Denkmäler der Malerei des Altertums* — **not reproduced by us**. Scheme only. | geometry (as an ancient proposal) + identification | Hardie, "*Imago Mundi*," 18–20 with PLATES Ia–c and 18 n. 52; **read in full**, `research-cache/hardie-1985-imago-mundi.pdf` |

**Note on our own posture.** `app/src/pages/attribution.astro` (≈l. 329) already
asserts that the illustrated plates, *the Shield included*, are "original drawings
made for this project — … not a scan, trace, or redrawing of any published map or
figure." Anything the rebuild borrows from 4a–4f must therefore be **scheme and
craft, not line** — the same discipline the cartography lanes already run under.
If the plate ends up echoing Flaxman's centre-frieze-rim scheme, that is a
compositional idea and is fine; a traced figure is not.

---

## 5. The material register

### 5.1 What the poem assigns, line by line

Four metals go into the fire at 474–75; a fifth material, **κύανος**, appears only
as the adjective `κυανέην` at 564. (The brief's "five metals of 18.474-75" is
four; the correction matters because κύανος is **not a metal** — see 5.2b.)

```
474  χαλκὸν δ' ἐν πυρὶ βάλλεν ἀτειρέα κασσίτερόν τε
475  καὶ χρυσὸν τιμῆντα καὶ ἄργυρον· αὐτὰρ ἔπειτα
```

| Line | Detail | Material named | Kind |
|---|---|---|---|
| 474–75 | the crucible | **χαλκός, κασσίτερος, χρυσός, ἄργυρος** | geometry |
| 480 | baldric | **silver** (`ἀργύρεον τελαμῶνα`) | geometry |
| 507 | the two talents | **gold** | geometry |
| 517 | Ares and Athene, and their clothing | **gold** (`ἄμφω χρυσείω, χρύσεια … εἵματα`) | geometry |
| 522 | the ambushers | **bronze** (`εἰλυμένοι αἴθοπι χαλκῷ`) | geometry |
| 534 | their spears | **bronze** (`χαλκήρεσιν ἐγχείῃσιν`) | geometry |
| 548–49 | the ploughland | **gold** — and it *reads as dark earth anyway* (`ἣ δὲ μελαίνετ' ὄπισθεν … χρυσείη περ ἐοῦσα· τὸ δὴ περὶ θαῦμα τέτυκτο`) | geometry + prose |
| 562 | the vineyard | **gold** (`καλὴν χρυσείην`); the clusters **dark** (`μέλανες … βότρυες`, material unstated) | geometry |
| 563 | vine-poles | **silver** (`κάμαξι … ἀργυρέῃσιν`) | geometry |
| 564 | the ditch round the vineyard | **κυανέην** — see 5.2b | geometry |
| 564–65 | the fence | **tin** (`ἕρκος … κασσιτέρου`) | geometry |
| 574 | the cattle | **gold and tin** (`χρυσοῖο τετεύχατο κασσιτέρου τε`) | geometry |
| 577 | the herdsmen | **gold** (`χρύσειοι … νομῆες`) | geometry |
| 583 | the bull's entrails and blood | **`μέλαν αἷμα`** — colour named, material unstated | geometry |
| 598 | dancers' daggers and baldrics | **gold on silver** (`μαχαίρας χρυσείας ἐξ ἀργυρέων τελαμώνων`) | geometry |

Verified how: read line by line from `build/dist/iliad/book-18.json`. Outside the
shield but in the same forge sequence: greaves of tin (613), a gold crest (612).

**The pattern the register must honour:** the poem names a material only for
**selected details**, and twice it names one that fights what the eye sees — gold
ploughland that *looks black*, a golden vineyard hung with *dark* clusters. Homer
is not colouring a diagram; he is describing inlay in which colour comes from
which metal is set where. A plate that paints every zone a different hue does the
opposite thing.

*(The ancient allegorists read the metals as meaningful too, though not as
colour: Heraclitus and Eustathius made the four of 474–75 the **four elements**
and the two cities Empedocles' `Φιλία` and `Νεῖκος`. Reception, not description —
but it is evidence that nobody in antiquity took the metals for decoration.
Hardie, "*Imago Mundi*," 15; and note that the **order** of the metal layers was
already a problem in Aristotle, Poetics 1461b1, per Hardie 15 and 15 n. 25. Read
in full, `research-cache/hardie-1985-imago-mundi.pdf`.)*

### 5.2 κύανος — the one non-metal, and what it is

| # | Claim | Kind | Citation | Verified how |
|---|---|---|---|---|
| 5.2a | κύανος is **glass paste or enamel** coloured with a brilliant cobalt-hued pigment, of the kind used at Knossos — not a metal. Cunliffe s.v. κύανος: "Glass paste or enamel coloured with a pigment doubtless to be identified with the pigment of brilliant cobalt hue largely used in the palace at Cnossus (see Sir Arthur Evans's *The Palace of Minos*, 1921, vol. i. p. 534): θριγκὸς κυάνοιο Od. 7.87. Cf. Il. 11.24, 35." | identification | Cunliffe, *Lexicon*, s.v. κύανος, citing Arthur Evans, *The Palace of Minos*, vol. 1 (London: Macmillan, 1921), 534 | Queried `build/dist/cunliffe/k.json` — this is a PD lexicon **already shipped on our own site** |
| 5.2b | At **18.564** the adjective is used in its **material** sense, not merely "dark". Cunliffe s.v. κυάνεος sense 1, "Represented in κύανος", cites Il. 11.26, 11.39 and **Il. 18.564** — as against sense 2, "Dark in hue, dark", which gets the storm-clouds and the darkness of death. | identification | Cunliffe, *Lexicon*, s.v. κυάνεος | Queried `build/dist/cunliffe/k.json` |
| 5.2c | Homer's other κύανος passages describe **exactly the technique**: Agamemnon's corselet has **ten strips of dark κύανος, twelve of gold, twenty of tin** (Il. 11.24–25) and κυάνεοι serpents on it (11.26); his shield has twenty white tin bosses with dark κύανος in the middle (11.34–35); Alcinous's palace has a **κύανος frieze** over bronze walls with silver door-posts and a gold lintel (Od. 7.86–90). | identification | Il. 11.24–26, 34–35; Od. 7.86–90 | Read in corpus (`book-11.json`, `odyssey/book-07.json`) |

**Consequence:** the vineyard ditch is a **dark inlaid line**, and Homer's own
comparanda for polychrome metalwork are **strips and fields of contrasting metal
with a black inlay for the dark parts**. That is the register the text points at.

### 5.3 The Bronze Age precedent: inlaid daggers and "painting in metal"

| # | Claim | Kind | Citation | Verified how |
|---|---|---|---|---|
| 5.3a | The Mycenaean inlaid daggers from the Shaft Graves are the material analogue: gold and silver figures set into a bronze blade against a **black ground**, with incised interior detail. The technique has a name in the German literature, *Metallmalerei* — "painting in metal". | identification | Agnes Xenaki-Sakellariou and Christos Chatziliou, *"Peinture en métal" à l'époque mycénienne* (Athens, 1989); E. N. Davis, "Metal Inlaying in Minoan and Mycenaean Art," *Temple University Aegean Symposium* 1 (1976): 3–6 | Both citations verified from the [Dartmouth Aegean Prehistory bibliography, Lesson 16.14](https://sites.dartmouth.edu/aegean-prehistory/lessons/lesson-16-narrative/lesson-16-bibliography/metallmalerei-and-the-niello-technique/); **neither work read** |
| 5.3b | The black is **usually not niello**. Non-destructive XRF across daggers, silver vessels and fragments from Mycenae, Prosymna, Dendra, Routsi and Pylos (16th–14th c. BC) shows "great versatility in working with copper (or bronze)–gold–silver alloys. The black inlaid decoration is usually copper/bronze–gold alloy with small quantities of silver." | identification | K. Demakopoulou, E. Mangou, R. E. Jones, and E. Photos-Jones, "Mycenaean Black Inlaid Metalware in the National Archaeological Museum, Athens: A Technical Examination," *Annual of the British School at Athens* 90 (1995): 137–53, [doi:10.1017/S0068245400016117](https://doi.org/10.1017/S0068245400016117) | **Abstract read verbatim** on Cambridge Core; body paywalled. Objects listed on that page: NM 390, NM 2489, NM 7736, NM 7842, NM 1874, NM 1816 |
| 5.3c | Supporting technical literature on the niello / artificially black-patinated alloy distinction (a patinated surface shows no heat treatment; niello is a fused sulphide paste). | identification | E. Photos, "The Black Inlay Decoration on a Mycenaean Bronze Dagger," *Archaeometry* 36 (1994), [doi:10.1111/j.1475-4754.1994.tb00969.x](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1475-4754.1994.tb00969.x); Alessandra Giumlia-Mair, "Recognizing Niello: Three Aegean Daggers," in *Exotica in the Prehistoric Mediterranean*, ed. Andrea Vianello (Oxford: Oxbow, 2011), 146–61 | Bibliography verified from the publisher/repository records; **bodies not read**; Photos's exact issue and page range **not verified** — §7 |
| 5.3d | Two Shaft Grave subjects are **the shield's own subjects**. Shaft Grave IV, the lion-hunt dagger: hunters against a lion on one face, **lions bringing down prey** on the other — cf. Il. 18.579–86, the two lions on the bull. Shaft Grave V: a **river scene** in inlaid gold and silver — wild cats attacking waterfowl on a papyrus-covered riverbank, with fish breaking the water — cf. Il. 18.576, `πὰρ ποταμὸν κελάδοντα, παρὰ ῥοδανὸν δονακῆα`. | identification | Objects in the National Archaeological Museum, Athens, from Grave Circle A, Mycenae, LH I | Descriptions from search-result synthesis of museum and reference pages; the NAM's own object page returned 403. **Inventory numbers not verified — see §8.** The *comparison* to Il. 18 is mine and is offered as a register argument, not as anyone's published claim |
| 5.3e | The **Silver Siege Rhyton** from Shaft Grave IV shows an attack on a fortified town in worked silver — the closest Bronze Age object to Il. 18.509–40. | identification | Silver Siege Rhyton, Shaft Grave IV, Grave Circle A, Mycenae, c. 1600–1500 BC ([Wikipedia](https://en.wikipedia.org/wiki/Silver_Siege_Rhyton), citing Tim Everson, *Warfare in Ancient Greece* (2004) and Margaretha Kramer-Hajos, *Mycenaean Greece and the Aegean World* (2016)) | Fetched the Wikipedia article; it gives no inventory number and makes **no** Homeric claim. The Homeric comparison is mine |
| 5.3f | The **concentric figured band** as a real object type: the Idaean Cave bronze shields (Crete, 8th–7th c. BC) and the Cypro-Phoenician bowls, both of which carry figures in concentric zones. | identification | Kunze, *Kretische Bronzereliefs* (1931); Markoe, *Phoenician Bronze and Silver Bowls* (1985) | Bibliographic details verified from library and review records; **neither read**. This is the *material* warrant for a concentric scheme, independent of 3.2f's shaky attribution to Edwards. **Strengthened 2026-07-29:** the bowl parallel and its two standard objections are now citable first-hand from Revermann 31 — see 3.2m |
| 5.3g | **A scholar states the register decision's factual premise outright:** "the Phoenician bowls are chased work whereas **the decorations of the Shield must be inlaid work**." Revermann says this in passing, as the reason the bowls are an imperfect model — which is what makes it good evidence: it is a shared premise, not a thesis he is defending. Together with §5.1 (materials named for selected details), §5.2c (Homer's own polychrome-metalwork comparanda) and §5.3a–b (gold and silver on a black ground), this is the strongest available warrant for the literal-metallic side of the §5.4 decision. | identification | Revermann, "Text of *Iliad* 18.603–6," 31, following Erika Simon, "Der Schild des Achilleus" (1995), 129f. | Read in full, `research-cache/revermann-1998-text-iliad.pdf` |

### 5.4 The register decision (John's, not mine) — the evidence for each side

**Literal metallics.** For: the text names materials for fourteen details (§5.1),
and its own comparanda are inlay (§5.2c); a scholar states the premise flatly —
"the decorations of the Shield must be inlaid work" (§5.3g); the Bronze Age
objects are gold and silver figures on a black ground (§5.3a–b); it makes 548–49 and 562 legible as
*wit* rather than as inconsistency. Against: gold-and-silver on black is a narrow
value range, and WCAG AA in both themes is not optional; a metallic plate can
easily end up as the black Shield again in dark mode, which is the exact failure
already logged in `docs/TROY-MAPS-HANDOFF-2.md` §2.

**Site terracotta family.** For: it lands the Shield in the same visual family as
the Troad plates, and the linework conventions the cartography lanes have built
(waterlines, hachures, neatline, letterspaced caps) transfer unchanged. Against:
it discards the one thing the passage is most specific about, and there is no
textual warrant for it — it is house style.

**The one thing both must obey:** colour on this plate should come from *which
metal the poem assigns where* (§5.1), not from a spectrum sweep across rings.
Where the poem assigns nothing, the plate's own token layer decides, and the
caption may say so.

---

## 6. Incidental findings the rebuild lane will hit (out of my scope, reported not fixed)

1. **`apparatus/plates/shield-of-achilles.json` has no `sources` array.** Handoff
   §3.6 requires making `sources` mandatory in `validate_plate`; the Shield will
   fail that gate as authored. Every band in the rebuild can now cite: the line
   span (corpus), and for the arrangement, whichever of §3/§4 it follows.
2. **`ἴστωρ` is missing from both shipped lexicon slices.** `build/dist/lemma-map/i.json`
   lemmatises `istora → istwr`, but neither `build/dist/cunliffe/i.json` nor
   `build/dist/lsj/i.json` has an entry (each holds ~200 entries; only `ἵστημι`
   matches `i(/st`). A reader clicking `ἴστορι` at Il. 18.501 — the single most
   contested word in the trial scene — gets nothing. Verified by direct query.
3. **The current plate's summaries are accurate**, including the vineyard's "a boy
   plays and sings" (569–71, the right figure). The defect is the geometry and the
   spectrum, not the philology. Its `lines` spans match §1.2 exactly, including
   the city split at 509 and Ocean at 607–8.

---

## 7. Needs paywalled access

**Status, 2026-07-29: three obtained, read in full, and folded in.** Entries kept
below with what each actually settled, so the next reader can see the chain rather
than a blank.

| Work | Exact locus wanted | Which claim it settles |
|---|---|---|
| Edwards, *Iliad* vol. 5 (CUP, 1991) | **pp. 200–209** (shield introduction), and the notes on 18.481, 497–508, 507–8, 509, 604–5 | **STILL OPEN.** 3.2a–c and 3.2f. Above all: (i) whether Edwards really argues the two armies of 509 are one army, in his own words and at his own page; (ii) whether the Cretan-shield / Phoenician-bowl parallel is his, and where. Both are currently second-hand through BMCR or through a search synthesis, and 3.2f should not be cited until read. **Narrowed:** the bowl parallel itself no longer depends on Edwards (3.2m, Revermann 31), and the two-armies question now has a first-hand alternative source (3.2h, Taplin 6). Revermann 29 n. 3 confirms Edwards has a note **ad 604–6**, which is the remaining item of real value here. |
| ~~Taplin, "Shield of Achilles within the *Iliad*," *G&R* 27 (1980): 1–21~~ | the whole, esp. the footnote on 483 and whatever he says about arrangement | **OBTAINED** — `research-cache/taplin-1980-shield.pdf`, read in full including all 40 notes. Settled: 3.1e (the summary reading is **Fittschen's**, p. 10; the emendation objection is Taplin's, n. 13 — the dossier had it backwards); 3.1h (he adopts **five** concentric circles and disclaims them, p. 5); 3.1i (the two cities are **one** circle, p. 5); 3.1j (the rural scenes are the **four seasons**, pp. 7–9); 2.2g (he leans *for* the ἀοιδός, p. 9, n. 27); 3.2h–3.2l; §1.2's athetesis notes (Solmsen on 535–40, Leaf on 587–9); §8.4 (Lessing, *Laocoon* chs. 17–19) and §8.6 (Marg = *Homer über die Dichtung*). |
| Fittschen, *Der Schild des Achilleus* (1973) | pp. **1 n. 1, 2, 4–5, 10**, and the reconstruction history entire (28 pp., 8 figs., 10 pls.) | **STILL OPEN, and still the highest-value item for a drawing lane.** The **reconstruction history from the 16th century on** — whether §4's typology is the real taxonomy or my simplification. **Sharpened:** exact pages now known from Taplin 18 n. 5, 19 nn. 9 and 13 and Hardie 18 n. 49, 30 n. 132 (see 3.2g); p. 10 is the locus for 3.1e's Fittschen position, currently cited at one remove. |
| ~~Hardie, "*Imago Mundi*," *JHS* 105 (1985)~~ | the whole; and the correct **start page** | **OBTAINED** — `research-cache/hardie-1985-imago-mundi.pdf`, read in full including both plates. **START PAGE: 11**, not 12 (cover page, running head and printed folio all agree). Settled: 3.3b; 3.1f–3.1g (the two-group frame, and his denial that the human scenes schematise, p. 11); 1.1d (the ancient five-zone allegory, p. 15); 3.3f (imago mundi is Ovid's phrase, pp. 16–17); 3.3g and **4h–4i** (the ancient layouts, pp. 18–22). |
| ~~Revermann, "The Text of *Iliad* 18.603–6," *CQ* 48.1 (1998): 29–38~~ | the whole | **OBTAINED** — `research-cache/revermann-1998-text-iliad.pdf`, read in full. Settled 2.2a (the expanded tradition is **not** Athenaeus alone — 𝔓51 adds instruments, pp. 33–34), 2.2e (Athenaeus's testimony "more than dubious"; the θεῖος ἀοιδός un-Iliadic, pp. 34–35), 2.2f (**his own verdict: the passage is lacunose and unrecoverable**, pp. 32, 35, 38), 3.2m and 5.3g (the bowls, and "the decorations of the Shield must be inlaid work", p. 31). See the FLAG FOR JOHN at the end of §2.2. |
| Becker, *Shield of Achilles and the Poetics of Ekphrasis* (1995) | the chapter on 18.478–608 | **STILL OPEN.** 3.3c beyond the reviewer's summary. |
| Friis Johansen, *The Iliad in Early Greek Art* (Copenhagen: Munksgaard, 1967) | **pp. 92ff., 178ff., and the plates at 93–109 and 181–3** | **NEW, opened 2026-07-29.** The plate corpus of ancient representations of the shield, cited for exactly this purpose by both Taplin (18 n. 5) and Hardie (18 n. 49). Would let §4's ancient rows (4h–4i) rest on the standard picture-book rather than on two JHS plates we may not reproduce. |
| Sadurska, *Les Tables Iliaques* (Warsaw: PWN, 1964), 43ff. and no. 4N | the description and drawing of fragment 4N | **NEW, opened 2026-07-29.** 4h rests on Hardie's reading of Sadurska. The scheme is what we would borrow, so the primary description matters; and Hardie flags one disputed point — whether the incised zig-zag round the central field really is Oceanus (Sadurska's interpretation, adopted by Hardie). |
| Pope, "Observations on the Shield of Achilles," *Iliad* vol. 5 (1720) | Boivin's "regular plan and distribution" as Pope prints it | 4b — **how many divisions Boivin's scheme actually has, and what is in each.** The ECCO copy at `quod.lib.umich.edu` returns 403; the Commons plate image would answer it visually. |
| Photos, "Black Inlay Decoration," *Archaeometry* 36 (1994) | issue number and page range | 5.3c's citation. |
| Willcock, *A Companion to the Iliad* (Chicago, 1976) and *The Iliad of Homer, Books XIII–XXIV* (London: Macmillan, 1984) | notes on 18.478–608 | Requested by the brief; **both books verified bibliographically, neither consulted.** No claim in this dossier rests on Willcock. |

---

## 8. Unverified — do not claim publicly

**Updated 2026-07-29 after reading Taplin, Hardie and Revermann in full.** Items
4 and 6 are **settled** and struck; item 3 is better sourced but stays open; item
10 is rewritten, because the three papers change what can be said. Items 1, 2, 5,
7, 8 and 9 are untouched — nothing in these three papers bears on them.

1. **Quatremère de Quincy's "eight continuous sequences" and "two circles"**
   (4c). Read from a search synthesis of French sources, not from a page I read in
   full; the Utpictura18 notice I did fetch gives publication data and plate
   number but **no zone description**. Do not state the count until the plate
   itself or the BnF description is read.
2. **NAM inventory numbers for the two famous inlaid daggers** (5.3d). The
   commonly repeated numbers (394 for the Shaft Grave IV lion-hunt dagger, 765
   for the Shaft Grave V river dagger) could **not** be confirmed; the museum's
   own page returned 403, and the BSA technical study lists a different set (NM
   390, 2489, 7736, 7842, 1874, 1816) without matching numbers to named objects.
   Cite the objects by **findspot and subject**, not by number.
3. **Which layer of the shield is decorated.** Il. 20.269–72 gives the five
   layers' metals but never says which face carries the figures. Do not assert it.
   **Still open, and now known to be anciently open:** the order in which the
   metal layers were assembled was already a stated problem in Aristotle,
   *Poetics* 1461b1 (Hardie, "*Imago Mundi*," 15 and 15 n. 25). This is not an
   artefact of our reading; it is the oldest recorded question about the object.
4. ~~**Lessing's chapter number.**~~ **SETTLED 2026-07-29: *Laokoon*, chs. 17–19.**
   Taplin cites the point there (19 n. 12) and states it in his own text at p. 5.
   The commonly repeated "XVIII–XIX" was too narrow. Folded into 3.3d.
5. **Nagy's essay title.** The [cyber.harvard.edu](https://cyber.harvard.edu/heroes/content/cybershield2.html)
   page gives the venue and pages (*New Light on a Dark Age*, ed. Langdon, 1997,
   194–207) and calls itself "an essay-in-progress"; it does **not** state a
   title on the part I read. Cite venue and pages.
6. ~~**Marg's essay**~~ **SETTLED 2026-07-29** (3.2e). The guess was right:
   **Walter Marg, *Homer über die Dichtung* (1st edn. 1957;
   2nd edn. 1971)**. Taplin's n. 1 names it as one of the three essays that have
   "been pervasive and shall not try to single out every concurrence" in shield
   scholarship, beside Schadewaldt, *Von Homers Welt und Werk*, 4th edn.
   (Stuttgart, 1965), 352–74 (first published 1938) and K. Reinhardt, *Die Ilias
   und ihr Dichter* (Göttingen, 1961), 401–11. Read in full,
   `research-cache/taplin-1980-shield.pdf`.
7. **Monticelli and the two Rijksmuseum engravings** (4e–4f). Filenames only, from
   an API listing. Neither the images nor their licences were examined.
8. **The Il. 18 ↔ Shaft Grave subject correspondences** (5.3d–e: lions on prey,
   the reedy river, the besieged town) are **my** comparisons drawn from the text
   and the object descriptions. They are good register arguments. They are not
   attributed to any scholar here, and must not be presented as published
   scholarship.
9. **Boivin's scheme as "quadrants."** Inferred from a French description of
   Quatremère as having *abandoned* isolation by quadrant. Boivin's own plate was
   not read. See §7.
10. **Whether any concentric scheme is defensible as *Homeric*.** *Rewritten
    2026-07-29 — the answer got sharper, and it is still no.* The material
    parallels are real (5.3f, and now 3.2m first-hand) and the Ocean-at-rim datum
    is real (3.1a). What the three read papers add: a concentric scheme is
    defensible as **scholarship** — Taplin's five circles are in print and
    "widely accepted" (3.1h) — and a *frame* reading is defensible as
    **interpretation**: Hardie's cosmos-plus-Ocean around a single human field
    (3.1f). What none of them supplies is the poem saying so. Taplin explicitly
    denies it ("It is not even clear that the shield is to be envisaged as
    decorated with five concentric circles"), and Hardie denies that the human
    scenes schematise at all (3.1g). So: **a plate may draw concentric bands and
    cite Taplin; it may draw a cosmic frame and cite Hardie; it may not say the
    arrangement is Homer's.** The one arrangement now known to have an *ancient*
    exemplar is neither of those — superimposed bands (Hardie's word; the
    "horizontal registers" gloss is ours) with a town/country split, 4h.
11. **Whether the passage at 603–6 is complete** (NEW, 2026-07-29). Two read
    scholars say it is not (2.2f–2.2g), and they disagree about what is missing.
    Do not state publicly that our text is the whole of what Homer composed here;
    do not state that a bard belongs on the shield either. The honest public form
    is the caption in §2.2's flag. **This one is John's call, not a lane's.**
