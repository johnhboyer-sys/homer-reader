# Who has already reconstructed the Homeric battlefield from the text — and how they drew it

**Date:** 2026-07-28

**What this is:** a cartographic-method and source dossier — the reconstruction
tradition, the camp's textual layout, battle-map convention, public-domain plates we
may trace, and drawing craft. Companion to `docs/TROAD-SOURCES.md`, which holds the
geoarchaeology, the gazetteer and the licensing position; this file deliberately does
not repeat them.

Every URL below was fetched. Every Iliad line was verified by script against
`build/dist/iliad/book-*.json`, not from memory.

---

## Defects this lane found in existing code

Being fixed in a separate lane. Recorded here so they are findable.

**1. `--scene-map-land` / `--scene-map-sea` fail WCAG 1.4.11, and the polarity flips
between themes.**

- `shared/styles/global.css:89` `--scene-map-sea: #DCE7EB` and
  `shared/styles/global.css:91` `--scene-map-land: #F1EEE6` (light) →
  **contrast 1.086:1**.
- `shared/styles/global.css:171` / `:173` and the duplicate block at `:195` / `:197`
  `--scene-map-sea: #132B3B`, `--scene-map-land: #2A2530` (dark) →
  **contrast 1.022:1**.
- (`shared/styles/global.css:222` / `:224` repeat the light pair.)
- WCAG 1.4.11 requires **3:1** for graphical objects, and explicitly covers "lines in
  line graphs" — so it covers a coastline. Both themes fail by a wide margin.
- Worse than the ratio: **the polarity inverts.** In light, land (L=0.8556) is *paler*
  than sea (L=0.7837). In dark, sea (L=0.0218) is *paler* than land (L=0.0203). A
  reader who learns "the pale side is land" learns the opposite on switching themes.
- Ratios computed with the WCAG relative-luminance formula from the literal hex values
  at those lines.

**2. `shared/lib/plate.ts:870` stacks `fill-opacity` on an already alpha-composited ink
token, so the same declaration buys nearly twice the contrast in light as in dark.**

```
markup = `<path … class="plate-layer plate-layer-relief" d="${d}" fill="var(--flaxman-ink)" fill-opacity="0.82" stroke="none"/>`;
```

- Light: `--flaxman-ink: #241827` (`global.css:90`, opaque) × 0.82 over
  `--scene-map-land #F1EEE6` → **8.71:1**.
- Dark: `--flaxman-ink: rgba(237,230,232,0.67)` (`global.css:172`, `:196`) × 0.82 →
  effective alpha **0.549** over `#2A2530` → **4.73:1**.
- Fix: give hachure ink its own per-theme token; stop multiplying opacities.

---

## Unverified — do not claim publicly

Three open items. Each would take a library visit. Until then we say less, not more.

1. **What Janko's single map in Cambridge vol. IV depicts.** Richard Janko, *The Iliad:
   A Commentary*, vol. IV, *Books 13–16* (Cambridge: CUP, 1992) is recorded as carrying
   **one map, subject unidentified**. It is the Battle-for-the-Ships volume and the
   likeliest place in the whole series for a plan of the Achaean camp. Nobody has
   opened it for us.
2. **Whether Luce 1998 charts the fighting scene by scene.** J. V. Luce, *Celebrating
   Homer's Landscapes* (Yale, 1998). The publisher's claim that he "traces the ebb and
   flow of the battle" is marketing copy. No accessible review describes his method at
   that resolution.
3. **What is in Oscar Mey, *Das Schlachtfeld vor Troja: eine Untersuchung* (Berlin and
   Leipzig: de Gruyter, 1926).** A public-domain monograph titled "The Battlefield
   before Troy" that appears never to have been scanned. Existence and PD status
   confirmed; contents, argument and whether it carries plates, all unknown.

Consequence for our copy: **do not claim we are doing something unprecedented.** The
defensible claim is narrower and still strong — *no standard commentary carries a
scene-by-scene battle map, and the last one anybody published was Pope's.*

---

**The headline finding:** the tradition exists, it is older than you'd guess, and its
founding document is by the translator we already ship. **Alexander Pope, in 1716,
published an engraved bird's-eye plate of the plain with a lettered key assigning each
stretch of ground to the books of the Iliad fought over it.** It is in the public
domain, it is high-resolution, and it is almost exactly the artefact this project set
out to build. Modern scholarship, by contrast, has largely *stopped* drawing the battle
— the six-volume Cambridge commentary has, so far as could be verified, no plan of the
plain and no plan of the camp at all.

---

## (1) The reconstruction tradition

### Alexander Pope, 1716 — the ancestor of our schematic plate

Pope prefixed "An Essay on Homer's Battels" to volume II of his Iliad. Two things sit in it.

**A prose per-book map of the fighting.** Pope works straight down the poem: Book 5 near
the confluence of Simois and Scamander; Book 6 "between the Rivers of Simois and
Scamander," the Greeks having crossed; Book 8 "evidently close to the Grecian
Fortification on the Shore"; Book 10, Hector lying at Ilus's tomb; Book 11 "chiefly
about Ilus's Tomb"; Books 12–14 about the fortification; Book 15 at the ships; Book 16
"between the Fleet, the River, and the Grecian Wall," then to the gates of Troy; Book 17
under the Trojan wall and back to the fortification; Book 18 outside the fortification;
Book 20 "still on that side next the Sea"; Book 21 in the river; Book 22 under the
walls. He also gives a numbered list of the seven places "about Troy" *in their order* —
a legend before there is a map.

**And then the map.** Facing p. 12 of that volume: an oblique bird's-eye plate engraved
by **John Harris**, looking inland from the Aegean. Legend, transcribed from the
full-resolution scan:

> TROJA cum Locis pertingentibus. 1. Porta Scæa & Fagus. 2. Caprificus. 3. Fontes
> Scamandri duo. 4. Callicolone prope Simoim. 5. Batiea seu Sepulcrum Myrinnes.
> 6. Ili Monimentum. 7. Tumulus Æsietis. AA. Murus Achivorum. B. Locus Pugnæ ante naves
> in lib. 8. 12. 13. 14. C. Gesta Diomedis hoc loco lib. 5. D. Achillis & Scamandri
> Certatio lib. 22. E. Locus Pugnæ in lib. 6. F. Pugnæ in lib. 11. G. Pugnæ in lib. 20.
> — I. Harris fecit.

Numbers 1–7 are the topography; **letters AA–G are the battle, keyed to book numbers.**
That is a phase map, in 1716.

**On `lib. 22`:** the plate really does read 22 for the Achilles–Scamander fight, which
is Iliad **21**. I checked at full resolution and the digit is unambiguous. **Reproduce
the error and footnote it; do not silently correct it.**

What the plate shows, visually: sea across the bottom (`MARE ÆGEVM`), the ships beached
prow-on in a long unbroken row with tents behind them and the Achaean wall (AA) with
towers and gates running landward of them; Scamander down the left, Simois down the
right, **joining** near the shore at `Ostia Scamandri`; Sigeum and Rhaeteum labelled at
the two ends of the beach; the plain between filled with small skirmishing figures and
three mound-and-pillar tumuli; Troy on rising ground at the top centre, drawn as a
domed early-modern walled city; `MONTES IDÆ` as a range of pictorial hill-profiles along
the horizon.

- Verified PD-US, British Library copy, 2,837 × 3,519 px: [File:THE ILLIAD OF HOMER (translated by POPE) p2.012 Troia.jpg](https://commons.wikimedia.org/wiki/File:THE_ILLIAD_OF_HOMER_(translated_by_POPE)_p2.012_Troia.jpg)
- Text of the essay, verified in the 1716 first edition scan: [archive.org/details/homerpopeiliad02](https://archive.org/details/homerpopeiliad02)

Pope, *The Iliad of Homer*, vol. 2 (London: Bowyer for Lintott, 1716), "An Essay on
Homer's Battels," 11–14 and plate facing 12.

**Anachronisms to be honest about:** Pope draws Troy as a Baroque city with domes; he
follows the Eastern (confluent-rivers) theory that Leaf would later demolish; and he has
no notion of the silted bay.

### Walter Leaf, 1912 — the classic textual reconstruction

Walter Leaf, *Troy: A Study in Homeric Geography* (London: Macmillan, 1912). xvi + 406
pp.; the *JHS* review records **27 plates and 6 maps**. Full text verified at
[archive.org/details/troyastudyinhom00leafgoog](https://archive.org/details/troyastudyinhom00leafgoog).

His six maps, from his own list (verified in the scan):

1. **The Plain of Troy according to the Iliad** (facing p. 44) — his own drawing, "to
   illustrate the principal localities mentioned in the *Iliad*, including the course of
   the Scamander, as explained in the text." **This is the one map in the whole
   tradition that is a purely Homeric reconstruction on a real base, drawn by an author
   who knew the poem line by line, and it is PD.**
2. The Homeric Geography of Greece and Asia Minor (facing p. 330).
3. The Dardanelles: "The Narrows," from Admiralty Chart 2429.
4. **The Plain of Troy, surveyed by Lieut. Spratt, R.N., in 1840**, Admiralty Chart 1608, at end.
5. The Excavations at Troy, from Dörpfeld's *Troja und Ilion*, at end.
6. General Map of the Troad, from the *Geographical Journal*, July 1912, at end.

Leaf's note on map 4 is itself a source: Spratt's survey is "the source of all
subsequent maps, and still the best representation of the natural features of the
country," and its lettering "shows the Bunarbashi (Bally Dagh) theory of Lechevalier in
its vogue" — Troy on the Bally Dagh, "Ilium Novum" at Hisarlık, the Mendere labelled
"Ancient Simois." His note on map 6 says it is founded on Philippson's *Topographische
Karte des westlichen Kleinasien* (1:300,000), itself largely a reproduction of
**Kiepert's *Karte von Kleinasien* (1:400,000)**, with his own uncertified corrections —
he says plainly they "are no more than approximations, and are not founded on any
survey."

**How Leaf lays it out.** He argues the *Western* theory of the Scamander against
Schliemann and Dörpfeld's *Eastern* one, on purely narrative grounds: if the river ran
between camp and city, the ford "must have been the very pivot upon which every battle
turned; neither side could even get into touch with the other until the ford had been
secured" — and the poem never mentions crossing it. He therefore puts the Scamander
through the *middle* of the plain, with the ford lying beside rather than across the
road, "just where the battlefield is narrowed by the two streams," making it the natural
boundary between the armies — which is why Hermes takes charge of Priam there and leaves
him there (24.349, 24.692). He excises 5.774 (the confluence) as an interpolation. He
puts the tomb of Ilos, and possibly that of Aesyetes, at the slight rise by Kum Köy; the
θρωσμὸς πεδίοιο (10.160, 11.56, 20.3) there too, following Dörpfeld; Callicolone not at
Strabo's five-stade point but at the "browy" hills of **Ophrynion (Eren Köy)**, chosen to
balance the pro-Greek gods' Wall of Herakles above Beşik Bay. He reads the Book 22 chase
physically off Dörpfeld's citadel plan: a runner from the lookout plateau, keeping level,
reaches the wagon-track "at a point just sixty yards north of a spring," and he marks
that track on his Fig. 8.

**What he got wrong, and it is the big one.** Leaf rejected the silted-bay theory
outright:

> "Careful investigations by Virchow and others have failed to produce any sign of
> marine deposits in the plain, and it may be taken as certain that the coast-line did
> not in the Mycenaean age materially differ from that which now exists. Hissarlik was
> as far from the sea then as it is now." (p. 30)

Kraft, Kayan and Erol (1980) and everything since refute this flatly. Leaf's whole plate
is drawn on a modern coastline. **Any tracing of Leaf must move the shore.** The irony
worth putting on the page: Leaf was dismissing "a learned lady, Histiaia of Alexandria
Troas," and Strabo after her — and Histiaia was right.

**Leaf, *Strabo on the Troad* (Cambridge: CUP, 1923).** Pre-1931, so PD-US; a
contemporary review records 20 plates and 8 maps. **No digital scan was found** on
archive.org, Gallica or Wikimedia; HathiTrust's catalogue record refused fetching. Treat
as PD-but-not-yet-obtainable.

### J. V. Luce — the fullest modern defence, and a camp in a different place

J. V. Luce, "The Homeric Topography of the Trojan Plain Reconsidered," *Oxford Journal
of Archaeology* 3 (1984): 31–43.
[Wiley DOI 10.1111/j.1468-0092.1984.tb00114.x](https://onlinelibrary.wiley.com/doi/10.1111/j.1468-0092.1984.tb00114.x).
Its abstract is precise and worth quoting because it is a drawable claim: in the Troy
VI/VII era the shoreline "appears to have run west by south of the site, with a broad
marine embayment between the city and the Sigeum ridge," and **Luce proposes a new site
for the camp on the lower slopes of the Sigeum ridge, about four miles west of
Hisarlık**, rejecting Beşik Bay.

That is a structural claim, not a detail. It rotates the battlefield: the fighting runs
roughly **east–west**, city to camp across the embayment's head, not north–south as
Pope, Leaf and every popular illustration have it. If we draw a geographic plate, we
must choose, and say we chose.

J. V. Luce, *Celebrating Homer's Landscapes: Troy and Ithaca Revisited* (New Haven: Yale
University Press, 1998) — in copyright, cite only. Reviewed by Carol G. Thomas, *AJA*
104, no. 2 (2000): 379–80. **See "Unverified" above** on whether he charts the fighting
scene by scene.

Precursor worth naming: **Albert Gruhn, *Das Schiffslager vor Troja*, Der Schauplatz der
Ilias und Odyssee 6 (Berlin: Selbstverlag, 1910), 102 pp.** — argued the camp onto the
**northern Sigeum ridge**, i.e. Luce's position, eighty-eight years earlier. Pre-1931 and
therefore PD-US, but **no scan found**.

### Oscar Mey, 1926 — a whole book on the battlefield, PD, and apparently lost to the web

**Oscar Mey, *Das Schlachtfeld vor Troja: eine Untersuchung* (Berlin and Leipzig: de
Gruyter, 1926).** Reviewed by A. Shewan, *Classical Review* 42, no. 1 (1928): 41. It is
cited in the modern Troia *Endpublikation*. **Published 1926 = public domain in the US.**
I could not find a digital copy anywhere, could not read the review past the paywall,
and cannot tell you what it argues or whether it carries plates. This is the single most
tantalising gap in the lane. A library request would settle it.

Also unscanned: **F. Nieberding, *Das Schiffslager der Achäer nach den Andeutungen der
Iliade Homer's*** (Google Books id `6VG7rtNYYsIC`, 19th-c. school programme). Existence
confirmed; contents not.

### J. M. Cook, and the modern archaeological baseline

J. M. Cook, *The Troad: An Archaeological and Topographical Study* (Oxford: Clarendon
Press, 1973), xviii + 443 pp. A 1973 *REA* review records **"23 cartes, plans et
dessins"** plus 73 photographic plates. In copyright — cite only, never trace. The
archive.org copy is a lending scan, not PD.

### The Cambridge commentaries — a near-total absence

Checked volume by volume against *Classical Review* physical descriptions and contents
captures:

| Vol. | Editor | Books | Maps |
|---|---|---|---|
| I | Kirk (1985) | 1–4 | **3 maps** — "Mainland Greece," "The Aegean and Asia Minor," "The east Aegean coast," supporting the Catalogue |
| II | Kirk (1990) | 5–8 | none recorded |
| III | Hainsworth (1993) | 9–12 | none recorded |
| IV | Janko (1992) | 13–16 | **1 map — subject unidentified.** The Battle for the Ships volume; the likeliest place in the whole series for a camp plan, and unverified |
| V | Edwards (1991) | 17–20 | none recorded; 3 b/w illustrations, probably the Shield |
| VI | Richardson (1993) | 21–24 | none recorded |

**No volume is confirmed to print a plan of the Achaean camp or a battle map of the
plain.** The standard modern commentary on the Iliad has, essentially, no cartography of
the fighting. That is our opening.

Others: Willcock, *A Companion to the Iliad* (Chicago, 1976) — catalogue description
lists no maps. Latacz, *Troy and Homer* (Oxford: OUP, 2004) — "illus., maps" per *JHS*;
itemisation unverified. **Correction to the brief that commissioned this lane:** there is
no OUP 2006 Bryce titled *The Trojan War: Is There Truth Behind the Legend?* — that
title is an article, *Near Eastern Archaeology* 65, no. 3 (2002): 182–95. The 2006 book
is *The Trojans and Their Neighbours* (London: Routledge), with maps. Michael Wood, *In
Search of the Trojan War* (London: BBC Books, 1985) — the hardback reproduces **Spratt's
1839 map** and carries plans; the paperback drops nearly all of it to a single map.

**Jonathan Burgess, "Tumuli of Achilles," *Classics@* 3 (Center for Hellenic Studies),
open access and verified:
[classics-at.chs.harvard.edu/classics3-jonathan-s-burgess-tumuli-of-achilles/](https://classics-at.chs.harvard.edu/classics3-jonathan-s-burgess-tumuli-of-achilles/).**
He reproduces **Lechevalier's 1791 map** of Cape Sigeion and **Gell's 1804 watercolours**
of the tumuli. His argument is the right one for our data model: the tomb of Achilles is
a *plurality*, not a place — rival candidates at Cape Sigeion and Sivri Tepe serving
different cultic, political and archaeological purposes across time, and he declines to
name a real one. This is exactly `tier: traditional` with the tradition named, and it is
linkable.

### The 19th century and the Bunarbashi war

The controversy is worth a panel of its own, and all of it is PD. **Jean-Baptiste
Lechevalier** claimed in the 1780s–90s to have found Homer's hot and cold springs at
Bunarbashi (Bally Dagh) and put Troy there; the identification held for roughly a
century. Leaf's demolition is quotable and free: the Bally Dagh site is eight miles from
the sea, so "no fleet-footed Polites would be of service"; the chase round the walls
becomes "so impossible a feat as to raise Homer's description quite beyond any human
interest"; and the theory forces the great Mendere to be the *Simois* and the Scamander
to be a brook that "trickles for half a mile or so till it loses itself in reedy
swamps." As for the springs: "Unfortunately thermometers are not enthusiastic, and
obstinately refuse to recognise any difference of temperature between the thirty or
forty springs which here gush out from the rocks." Spratt's 1840 Admiralty chart is the
fossil of the losing theory — it letters Troy onto the Bally Dagh — and it is also the
chart that led Calvert and Schliemann to Hisarlık.

Also PD and relevant: **Carl Robert** in *Hermes* 24 (1889): 78ff., whom Leaf cites
approvingly on the ford; **P. W. Forchhammer, *Achill: Mit einer Karte der Ebene von
Troia* (1853)**; **Rudolf Virchow, *Beiträge zur Landeskunde der Troas* (1879)**.

### Has anyone mapped the fighting day by day?

Honest verdict: **Pope did it in 1716, in prose and in one plate — and nobody in the
modern scholarly literature appears to have done it since.** The closest modern
candidate found is Elizabeth Minchin, "Homer's Landscape of War: Spatial Mental Model
and Cognitive Collage," in *Landscapes of War in Greek and Roman Literature* (London:
Bloomsbury Academic, 2021), 25–37, which has a section on "the topography of the Trojan
plain: Homer's locative information" — paywalled, and I could not confirm whether it
contains a figure. Janko's single unidentified map in vol. IV remains the one loose end.

---

## (2) The camp — what the poem actually specifies

Every line below verified against the local corpus.

**Stated by the poem, not inferred:**

- **Odysseus amidships.** 8.222–23 = 11.5–6, verbatim:
  `στῆ δ' ἐπ' Ὀδυσσῆος μεγακήτεϊ νηῒ μελαίνῃ, / ἥ ῥ' ἐν μεσσάτῳ ἔσκε γεγωνέμεν ἀμφοτέρωσε`
  — "in the very middle, to carry a shout both ways."
- **Ajax and Achilles at the two ends.** 8.224–26 = 11.7–9:
  `ἠμὲν ἐπ' Αἴαντος κλισίας Τελαμωνιάδαο / ἠδ' ἐπ' Ἀχιλλῆος, τοί ῥ' ἔσχατα νῆας ἐΐσας /
  εἴρυσαν, ἠνορέῃ πίσυνοι καὶ κάρτεϊ χειρῶν` — hauled up at the extremes "trusting in
  their manhood and the strength of their hands."
- **Ajax and Idomeneus furthest off.** 10.112–13:
  `ἀντίθεόν τ' Αἴαντα καὶ Ἰδομενῆα ἄνακτα· / τῶν γὰρ νῆες ἔασιν ἑκαστάτω, οὐδὲ μάλ' ἐγγύς`
  — a *third* named extreme, which complicates any two-ended diagram.
- **The agora and the altars at Odysseus's ships.** 11.806–8:
  `κατὰ νῆας Ὀδυσσῆος θείοιο / ... ἵνά σφ' ἀγορή τε θέμις τε / ἤην, τῇ δὴ καί σφι θεῶν
  ἐτετεύχατο βωμοί` — assembly, law-place and the gods' altars, all at the centre.
- **Ships in receding rows, wall behind the sterns.** 14.30–36: the ships lie far from
  the fighting `θῖν' ἔφ' ἁλὸς πολιῆς`; `τὰς γὰρ πρώτας πεδίον δὲ / εἴρυσαν, αὐτὰρ τεῖχος
  ἐπὶ πρύμνῃσιν ἔδειμαν` — **the first-hauled ships lie furthest inland, toward the
  plain, and the wall was built at their sterns**; the beach could not hold them all,
  `τώ ῥα προκρόσσας ἔρυσαν` (in echelon/tiers), and they filled `ἠϊόνος στόμα μακρόν,
  ὅσον συνεέργαθον ἄκραι` — the long mouth of the shore, as much as the headlands
  enclosed. This is the single most under-drawn fact in the tradition: **the camp has
  depth, not just length**, and the front rank facing the plain is the *first* rank
  hauled.
- **The front rank fights first.** 15.653–54: `περὶ δ' ἔσχεθον ἄκραι / νῆες ὅσαι πρῶται
  εἰρύατο` — the foremost ships hold the Trojans off.
- **The left of the ships is the chariot gate.** 12.118–19: Asius attacked
  `νηῶν ἐπ' ἀριστερά, τῇ περ Ἀχαιοὶ / ἐκ πεδίου νίσοντο σὺν ἵπποισιν καὶ ὄχεσφι` — "at
  the left of the ships, where the Achaeans used to come back from the plain with horses
  and chariots." The main wagon gate through the wall is on the left.
- **The left is Ajax's and Protesilaus's end.** 13.675 `νηῶν ἐπ' ἀριστερὰ`, 13.679–81:
  Hector held where he first leapt the gates and wall, `ἔνθ' ἔσαν Αἴαντός τε νέες καὶ
  Πρωτεσιλάου`. Ajax is fighting `μάχης ἐπ' ἀριστερὰ πάσης` at 11.498, 17.116, 17.682
  (formulaic), 13.765; Ares at 5.355.
- **The poem itself divides the line in three.** 13.308–9: Idomeneus asks whether to go
  `ἐπὶ δεξιόφιν παντὸς στρατοῦ, ἦ ἀνὰ μέσσους, / ἦ ἐπ' ἀριστερόφιν` — right, centre,
  left. That is a schematic the poem hands us.

**Scholarly inference, not stated:** that "left" and "right" are consistently from the
Achaean side facing Troy (the standard view, and the subject of Joseph Cuillandre, *La
droite et la gauche dans les poèmes homériques* [Paris: Les Belles Lettres, 1944]); that
Achilles therefore holds the right; that Nestor, Diomedes and Agamemnon lie centrally.
**There is a real crux here and we should not paper over it:** Protesilaus's ship is at
Ajax's extreme (13.681) and is the one Hector fires (15.704–6), yet Patroclus, sallying
from Achilles' ships at the *other* extreme, reaches it immediately (16.286). Either the
poet holds two incompatible camp pictures or the narrative compresses. Say so; do not
resolve it by drawing.

**Pure convention, with no textual warrant:** any placement of the remaining twenty-six
Catalogue contingents along the shore. **I found no scholarly reconstruction that places
the Catalogue contingents on the beach**, and I looked hard. The Scholars' Lab's
[Mapping the Catalogue of Ships](https://ships.lib.virginia.edu/) (University of
Virginia Library, CC BY) maps the contingents' *homelands* in Greece and explicitly not
the camp. Pope's plate draws an undifferentiated row of ships. Gruhn 1910 and Mey 1926
argue about *where* the camp was, not about who lay next to whom.

**So the answer is: nobody has, and we should not either.** What we can draw, and what
nobody has drawn cleanly, is the order the poem *does* give: a beach closed by two
headlands; ships in ranks receding from the water with the wall at the rearmost sterns;
the wagon gate at the left; Ajax + Protesilaus at the left end where the breach comes;
Odysseus, the agora, the law-place and the altars dead centre; Achilles at the right
end; Idomeneus also far out. Everything else stays a repeating anonymous ship glyph.
That is honest, it is drawable, and it is more than any published diagram gives.

Ancient authority worth citing for the *reasoning*, which Pope relays from Eustathius
and Spondanus: Achilles and Ajax, "the strongest Heroes of the Army, were placed to
defend either end of the Fleet as most obnoxious to the Incursions or Surprizes of the
Enemy; and Ulysses being the ablest Head, was allotted the middle Place, as more safe
and convenient for the Council."

---

## (3) How battles are conventionally drawn

The Landmark conventions were verified from the publisher's own sample PDF — the "Key to
Maps," p. lxiv of *The Landmark Herodotus*:
[thelandmarkancienthistories.com/sample_pdfs/LandmarkHerodotusSamples.pdf](https://thelandmarkancienthistories.com/sample_pdfs/LandmarkHerodotusSamples.pdf).
This is a primary legend, not a description of one.

- **Maps are numbered by Book.Chapter of the text, never sequentially** — `Map 1.204`,
  `Map 2.6`, `Map Intro.1`. A marginal reference resolves to *(map id, tier, named
  inset)*: `2.6.1b Plinthine Gulf: Map 2.6, Egypt inset.` ·
  `Intro.1.2b Asia Minor (Asia): Map Intro.1, locator.` **This is a data schema and we
  should copy it exactly.**
- **Three tiers:** locator map → main map → *named* (not numbered) inset.
- **Symbol set, in legend order.** Cultural: settlements · deme · fortified place ·
  temple · **battle site** · road · city walls and fortifications. Natural: mountain /
  range · cliff or escarpment · river · marsh · seas and lakes **"(approximate extent in
  Classical Period)"** — the legend carries its own honesty caveat, which is a device we
  should steal outright.
- **Five type classes.** Letterspaced caps `A S I A` / `AEOLIS` for continents and
  regions; roman in two *weights*, `Athens` for large cities and `Heliopolis` for
  others; italic `Kadousians` for peoples; italic `Halys R.` for water, islands,
  promontories; `MT. OLYMPUS` for mountains. Note: rank among settlements is carried by
  **weight, not size**, which keeps the size ladder short.
- **Colour:** black line and type on white plus **one spot colour**, a pale blue for
  seas and lakes. Not greyscale, not full colour.
- **Cartographer:** *Herodotus* colophon credits **Topaz Maps, Inc.**; *Landmark Arrian*
  credits J. Wyss and K. Sandefer, following Barrington spellings, and uses shaded relief
  on its per-book maps ([BMCR 2011.05.58](https://bmcr.brynmawr.edu/2011/2011.05.58/)).
  Map density in the *Thucydides* is "on nearly every third page of text."

**What the Landmark does *not* appear to do** — and this matters for us — is animate.
Its battle maps are static single-state plates with a battle-site symbol, not phase
overlays with movement arrows. Unit blocks, phase overlays and numbered stages are the
*modern military-history* vocabulary (Osprey, West Point atlases), not the Landmark's.
Pope's lettered-by-book key is closer to what we want than anything the Landmark prints,
and it needs no arrows at all: a lettered zone per phase, keyed to book and line, is both
period-appropriate and honest about the fact that we know *regions* of the plain, never
vectors.

Barrington and Pleiades supply the uncertainty grammar. Barrington: a trailing **`?`**
doubts that the *name* belongs to the mapped feature; an **italicised name** means only
the approximate *location* is known — two orthogonal doubts, two devices. Modern
equivalents go in a distinct **sans-serif** face. Pleiades models three separate axes
([pleiades.stoa.org/help/uncertainty](https://pleiades.stoa.org/help/uncertainty)): name
attestation, location confidence (Known / Approximate / Weak), and name–location
association. Our `certain | traditional | speculative | mythical` maps onto the
*location* axis and must be kept distinct from the association axis. **Not verified:**
Barrington's actual relief colour ramp — do not let anyone quote a green-to-brown ramp
as Barrington's.

Openly licensed base data: **AWMC** publishes coastlines, rivers and roads as GeoJSON
under **ODbL 1.0** ([awmc.unc.edu/gis-data](https://awmc.unc.edu/gis-data/),
[github.com/AWMC/geodata](https://github.com/AWMC/geodata)) — usable with attribution
and share-alike on derivatives. There is no public AWMC style guide.

---

## (4) Public-domain images we may actually study or trace

All fetched. US rule applied: pre-1931 publication = PD.

| Item | Year | Verified URL | What it gives us | Quality |
|---|---|---|---|---|
| **Pope, *Iliad* vol. II, "Troja cum Locis pertingentibus," engr. John Harris** | 1716 | [Commons file page](https://commons.wikimedia.org/wiki/File:THE_ILLIAD_OF_HOMER_(translated_by_POPE)_p2.012_Troia.jpg) · direct: `upload.wikimedia.org/wikipedia/commons/1/10/THE_ILLIAD_OF_HOMER_%28translated_by_POPE%29_p2.012_Troia.jpg` | **The per-book battle key.** BL copy, explicit PD-US tag | 2,837 × 3,519, legend legible at full res |
| **Spratt & Graves, Admiralty Chart 1608**, "Entrance of the Dardanelles, with the Plain of Troy and Tenedos" | surv. 1840, publ. 1844 | Commons; direct JPEG confirmed as a real 6.5 MB file | The primary survey; "the source of all subsequent maps" (Leaf); shows the Bunarbashi theory in its vogue | **4,469 × 6,000 px**, PNG and 274 MB TIFF also offered |
| **Leaf, *Troy*, Toronto/Robarts scan** | 1912 | [archive.org/details/troystudyinhomer00leaf](https://archive.org/details/troystudyinhomer00leaf) | **Foldoutcount 4** — the only one of four scans whose folding maps appear physically present, including "The Plain of Troy according to the Iliad" | 500 pp at 500 PPI |
| Leaf, *Troy*, Google/Michigan scan | 1912 | [troyastudyinhom00leafgoog](https://archive.org/details/troyastudyinhom00leafgoog) | Text only — **Foldoutcount 0.** Good for quoting, useless for the maps | The classic missing-foldout trap; the Trent scan `troystudyinhomer0000leaf` is the same trap |
| **Lechevalier, *Voyage de la Troade*, atlas volume** | 1802 (1st ed. 1799) | [archive.org/details/voyagedelatroade00lech](https://archive.org/details/voyagedelatroade00lech) | 45 leaves of plates, 37 numbered illustrations, **16 double folding plates**, incl. the 42 × 58 cm Troy plan that anchored the Bunarbashi theory | Getty copy, full access |
| **Dörpfeld, *Troja und Ilion*** vols 1–2 | 1902 | [vol. 1](https://archive.org/details/trojaundilionerg00drpf) (foldouts 4) · [vol. 2](https://archive.org/details/trojaundilionerg02dorp) (foldouts 7) | Citadel plans; Brückner's topography | Full access, JP2 originals |
| **Schliemann, *Ilios*** | 1880 | [ilioscitycountry1880schl](https://archive.org/details/ilioscitycountry1880schl) | **Foldoutcount 9** — the strongest signal of any item that its Troad maps survived scanning | 881 pp |
| Schliemann, *Troja* | 1884 | [trojaresultsofla00schl_0](https://archive.org/details/trojaresultsofla00schl_0) | Foldouts 2 | |
| **Forchhammer, *Achill: Mit einer Karte der Ebene von Troia*** | 1853 | [archive.org/details/10254332bsb](https://archive.org/details/10254332bsb) (BSB scan) | A dedicated map of the plain | 75 pp |
| **Lechevalier, *Beschreibung der Ebene von Troja*, "mit einer auf der Stelle aufgenommenen Charte"** | 1792 | [archive.org/details/11233025bsb](https://archive.org/details/11233025bsb) | The German edition with the on-the-spot chart | |
| Kiepert, "Graecia … (with) **Troas et Hellespontus**" | 1903 | [dr_graecia-cum-insulis…-0405005](https://archive.org/details/dr_graecia-cum-insulis-et-oris-maris-aegaei-with-troas-et-hellespontus-auc-0405005) | A dedicated Kiepert Troas inset | **Caveat:** David Rumsey asserts CC BY-NC-SA on the *scan*. The 1903 map is PD; under *Bridgeman v. Corel* a faithful 2-D scan gains no new US copyright. Usable, but if we want no argument, trace from Spratt instead |
| Kiepert, *Atlas Antiquus* | 1876 | [atlasantiquustwe00kiep](https://archive.org/details/atlasantiquustwe00kiep) | Foldouts 11 | |
| Virchow, *Beiträge zur Landeskunde der Troas* | 1879 | [bub_gb_soXUAAAAMAAJ](https://archive.org/details/bub_gb_soXUAAAAMAAJ) | The negative evidence Leaf leaned on | Foldouts unconfirmed |

**Not obtained, despite being PD:** Leaf, *Strabo on the Troad* (1923; 20 plates, 8
maps); Mey, *Das Schlachtfeld vor Troja* (1926); Gruhn, *Das Schiffslager vor Troja*
(1910); Nieberding's *Schiffslager*; Dörpfeld's separate **76-plate Beilagen atlas** —
Heidelberg's digi.ub blocked every fetch behind an "Anubis" bot-wall, and no standalone
atlas item exists on archive.org. Gallica returned 403 to every attempt, so no Gallica
link is certified here. **No lending-only ("Borrow") items were mistaken for PD in this
sweep.**

**In copyright — sources, never reproduced or traced:** Cook 1973; Luce 1984 and 1998;
Latacz 2004; Bryce 2006; Wood 1985/96; Minchin 2021; the Cambridge commentaries.

---

## (5) What makes a scholarly map beautiful

Concrete technique, with the numbers.

**Water-lining is the technique to invest in.** The definitive modern treatment is
Daniel P. Huffman, "On Waterlines: Arguments for their Employment, Advice on their
Generation," *Cartographic Perspectives* 66 (Fall 2010): 23–30
([PDF](https://cartographicperspectives.org/index.php/journal/article/download/cp66-huffman/pdf/815)).
Rules, from the article: the ICA definition requires lines that "decrease in proximity
and strength away from that edge"; Huffman's rule of thumb is to **multiply each gap by
1.3** (2 pt, then 2.6, then 3.38), because monospaced gaps read stylised while growing
gaps read as waves compressing against the shore; **the gap between shore and first line
is the critical variable**; confine the lines to a shore band rather than filling the
basin, as Victorian plates did, "which reduces their subtlety and makes it more
difficult to place other map features on the water"; and **never waterline rivers**,
since "waves do not generally begin in the center of a river and push against the banks."

The payoff is the reason it matters here: "The land and water polygons themselves are
both filled white, though the waterlines can create an optical illusion that makes the
water appear to be filled in with a darker color than the land… In grayscale or other
constrained-palette work, this can be a significant advantage." That is exactly the fix
for the contrast defect recorded at the top of this file — waterlines stop the land/sea
reading depending on fill luminance at all.

**Relief without a DEM — and which options are honest.** **Form lines** are the right
default: a real surveying convention for relief "sketched from visual observation, or
from inadequate or unreliable map sources," representing no actual elevations, and
**drawn broken or dotted where contours are solid**. The dash pattern *is* the honesty
claim, legible without a legend. **Pictorial hill profiles ("molehills")** are honest by
being obviously pictorial — and they are what Pope's plate uses, which settles the
register question. **Lehmann hachures (1799)** assume *vertical* illumination, so
darkness encodes steepness, not shadow: black:white = slope : (45° − slope) in 5° steps,
slopes under 5° left blank; Imhof's physical rules are downslope, perpendicular to
contours, **max 4 mm**, length ≥ the gap to the neighbour, rows offset never aligned.
**Oblique/Dufour hachures and hill shading are the dishonest option for us** — they
assert a light source and therefore a surface normal, i.e. a DEM we do not have — and
they are also the ones that break on inversion: a low or inverted light source triggers
"multistable perception illusions, in which the topography appears inverted"
([Terrain cartography](https://en.wikipedia.org/wiki/Terrain_cartography)).
Vertical-illumination hachures and stipple are immune, because they encode density, not
shadow.

> **SUPERSEDED, 2026-07-28 — we have a DEM now.** The clause above, "a DEM we do not
> have," is the whole of the objection to hill shading, and it has stopped being true.
> `scripts/prep-terrain-contours.py` pulls the SRTM-derived terrarium tiles from AWS
> Open Data (`sources/terrain-tiles/`, public domain, one credit line owed) and both
> Troy plates now carry relief cut from real contours: 200 m on the Troad, 20–50 m on
> the plain, checked against Kaz Dağı at 1757 m, Hisarlık at 36 m and sea at 0. A
> surface normal is one finite difference away. **The honesty objection to hillshade is
> withdrawn.**
>
> The *perceptual* objection in the second half stands untouched, and it is why this
> lane shipped contours and hachures rather than shading: relief inversion under a low
> or inverted light is a property of shaded relief itself, not of where the data came
> from, and it bites hardest in dark theme, where "parchment does not invert" already
> forces the ink to change. Vertical illumination has no light source to invert. So the
> register is unchanged — hachures and contour-cut bodies — but it is now a
> **choice between two honest options** rather than the only one available.
>
> Two consequences worth writing down. First, **form lines are retired on these two
> sheets**: `shading: "form-lines"` said "sketched, not contoured," and the bodies it
> was on are contoured now, so the field is gone from them rather than left lying as a
> false claim. Second, the DEM contradicted a hand-drawn feature and the DEM won: no
> contour isolates the "Troy ridge," because the ground rises continuously eastward
> from the mound (36 m at Hisarlık, 58 m a kilometre and a half east). It is a spur off
> the eastern upland, not a hill, which is exactly why the city commands the plain to
> its west and south and nothing to its east.

> **REVISED AGAIN, 2026-07-29 — hachures are retired on these two sheets, and
> hillshade is still not the answer.** The verdict on the contoured-and-hachured
> version was "it's better but still too crude, not pretty enough," and on a zoomed
> crop, "the hatching is also too crude — looks fine in a thumbnail, but when you zoom
> in, it's just big old lines." Both are correct, and they have the same cause.
>
> The section above treats the choice as *hachures versus hill shading*. That framing
> is the mistake. **Hachuring is the historical SUBSTITUTE for hypsometric tinting** —
> what a surveyor drew when he had relative steepness and no elevations. We have
> elevations. So the two Troy sheets now carry **graduated hypsometric bands**: ten
> levels on the Troad (50 m, then 100 m to 400, then 200 m to the summit) and eleven on
> the plain (5 m to 30, then widening — six of the eleven under 45 m, because the
> subject of that sheet is a battlefield 20 to 40 m above the sea), each filled from a
> twelve-step per-theme ramp and separated by a hairline contour. No hachures, no
> stipple, no texture of any kind on the relief. Depth comes from the ramp.
>
> That also disposes of the resolution problem for good, and it is worth being explicit
> about why. **Every relief technique built out of discrete marks has a scale at which
> it stops integrating into tone and resolves into countable marks** — hachures at
> 1.5 px weight and 4.5 px spacing did so at about 2x, and this SVG is rendered at
> 100% of a browser column, so it reaches 3x routinely. Fills and hairlines have no
> such scale: they are the same drawing at every magnification. That is a stronger
> argument for tinting on a screen than any of the ones in the print literature, and
> it applies to the whole class. The coast `stipple` register survives because it is a
> *boundary* claim ("reconstructed — approximate extent") rather than a tonal one, but
> its dots were retuned four times finer for exactly this reason, and any future
> texture on these sheets must pass the same test: a 3x crop with no countable marks.
>
> **Hill shading: still no, and now for the perceptual reason alone.** The surface
> normal is one finite difference away and the honesty objection is withdrawn (above),
> but the multistable-inversion objection stands, and a second, purely practical one
> joins it here: a shaded relief is a raster, and this project's plates emit **no
> colour that is not a `var()` token**, so that both themes and both contrast
> requirements are satisfied by a stylesheet. A baked PNG cannot be re-themed, and an
> SVG filter's light source cannot be either. The ramp needs neither.
>
> What replaces the plastic depth shading would have given is **contour density**: the
> hairlines between bands bunch where the ground is steep and spread where it is flat,
> which is Lehmann's vertical-illumination principle arrived at from the other
> direction — darkness encoding steepness, with no light source to invert. It is
> visible on Ida's flanks at 3x and it costs nothing.
>
> **THIRD PASS, 2026-07-29 — the relief was the crudest thing on the sheet
> until it wasn't, and then everything beside it was.** Book-quality
> hypsometric bands at 3.5x exposed four hand-made marks the previous lane had
> left standing, and the fix for all four is one idea: *put the uncertainty in
> the drawing, not in a crisp line and an apology.*
>
> **1. Every measured line is now drawn as a curve, not just relief.** The
> argument that held coastlines back — "a coastline is a surveyed line and
> keeps its vertices" — is exactly backwards for a reconstruction. The Bronze
> Age shore declares itself accurate to about a kilometre and is stored
> generalised to 275 m; drawn as straight facets meeting at sharp corners it
> asserted a precision the data does not have, and the facets were an artefact
> of Douglas-Peucker, not a claim about the ground. **Smoothing it is the more
> honest drawing.** The proof that it did not move the line is measured, in
> metres, in `shared/__tests__/plate.test.ts`: worst-case deviation of the
> drawn curve from the stored polyline is **215 m**, inside the 275 m
> generalisation the line already carries, and the calibration the 10 m level
> was chosen for still holds — the curve passes **1,241 m** north of Hisarlık
> where the polygon passed 1,223 m, both "1.2 km", against 2.8 km for the 8 m
> contour and 0.7 km for the 12 m. Two kinds of vertex are exempt: the
> endpoints of an open line, and any vertex on the neatline, which is where
> the clip cut the geometry rather than where the ground turns.
>
> **2. Stipple is retired, and this is the general rule.** The coast stipple
> survived the last pass on the argument that it was a *boundary* claim rather
> than a tonal one. It was not enough: at 3.5x it read as a scatter of
> countable dots however fine it was tuned, and it had been tuned four times.
> **Every treatment built out of discrete marks has a magnification at which it
> stops being tone — the class has no exceptions, boundaries included.** What
> replaced it is a blurred wide stroke with an opaque hairline down its middle:
> the same drawing at every scale, plainly distinct from the crisp solid
> modern shoreline, and a fuzzy edge is what "approximate extent" looks like.
> The hairline stays fully opaque and is what carries WCAG 1.4.11 — a wash
> may not be relied on for contrast.
>
> **3. A wetland has no boundary, so it is not drawn with one.** `delta-swamp`
> had been cut with literal latitude and longitude filters; three of its four
> sides were the filter rather than the ground, which made the sharpest lines
> on the sheet an artefact of how the data was sliced. It is re-derived from
> the DEM as a contour band (10–15 m, the shoreline's own level to one step
> above it) plus a **slope threshold** of 1.2 %, which is what separates
> aggraded floodplain (10 m over 5 km) from the foot of the Sigeion ridge
> (36 m in under a kilometre), minus the lagoon, keeping only the component
> connected to the bay head. About 15 km², and it reaches neither Troy nor the
> dry plain the poem fights over. It then draws with **no outline at all** and
> a blur twice the shoreline's, because the margin is genuinely more indefinite
> than the shoreline's position is: a gradational edge, not a smoothed one.
> Smoothing alone would have bought a curvy hard edge, which is the same lie
> with nicer manners.
>
> **4. The dry-plain wash is gone, and the ramp carries the ground.**
> `scamandrian-plain` was eleven hand-drawn vertices with a ruler-straight
> diagonal, painted at full opacity over contoured relief — so it was not only
> the crudest outline on the sheet, it flattened measured terrain across the
> middle of it. It is now `fill: "none"`: a lettering zone, drawing nothing,
> carrying the name. That is how an atlas letters a tract of country whose
> extent nobody surveyed, and it is the right answer whenever the honest
> options are "invent an edge" or "say nothing" — **letter it and draw
> nothing.**

> One measured caution for whoever cuts the next contoured sheet. **A contour is only
> as smooth as the ground under it.** Simplifying a traced line at 685 m while the grid
> still carries 124 m wiggles does not generalise it — Douglas-Peucker keeps the
> outliers and drops everything between them, so every wiggle becomes a spike, and the
> Troad's relief read as torn paper at 3x. Two fixes, both needed: extra smoothing
> applied to the grid *after* decimation (`post_blur` in
> `scripts/prep-terrain-contours.py`, tuned to sigma at roughly half the simplification
> tolerance), and drawing the band as a curve rather than as the polygon it is stored
> as (`smoothClosedPathD` in `shared/lib/plate.ts`). The second is free and does most
> of the work; the first is what stops the geometry lying about the shape of the hill.

**Typography.** Imhof's label-position ranking, via a
[2024 reassessment](https://arxiv.org/html/2407.11996v1): **top-right > right > top >
bottom > left**, shifting to TR, L, B, T, R under dense labelling; his reason is that
Latin ascenders outnumber descenders, so a label above a point sits visually closer than
one below. [Axis Maps](https://www.axismaps.com/guide/labeling): hierarchy levels must
differ by **at least 2 pt** at small sizes; minimum readable **9–10 pt on screen**; area
features uppercase, letter-spaced, visually centred; letterspacing and grey *demote*,
size and weight *promote*. In SVG, `paint-order="stroke"` as an **attribute** (not the
CSS property) gives one-element haloes and has shipped far longer;
`<textPath method="align" spacing="exact">` is Baseline since 2015; set
`font-variant-ligatures: none` on curved labels; avoid `side="right"` and reverse the
path instead. Collision detection and automatic deconfliction need a real label engine —
**for hand-authored plates, author the anchors by hand and skip it, which is what the
Landmark did.**

**Parchment does not invert.** A dark-mode "aged paper" is a contradiction in terms: the
aging *is* the yellowing of a pale ground. Carry the historical register in the
*linework* — waterlines, hachures, neatline, spaced caps — which inverts fine, and let
the dark ground be a plain deep neutral. The repo already reaches the right answer for
ink (`--flaxman-ink` in dark is `rgba(237,230,232,0.67)`, commented "bone, subtle, **not
inverted**"). The one real bug is the opacity stacking at `shared/lib/plate.ts:870`,
recorded at the top of this file.

**Frame.** Double neatline, outer 1.2 px / inner 0.4 px, 3 px apart. **No graticule
across the map face** — ticks and numerals in the margin only, as on Cary's 1794 plate;
it is the cleanest option and leaves the field free. Bar scale with alternating filled
and open segments, stades over kilometres with coincident zeros. Plain title block; by
the mid-19th century the plates had dropped the Baroque cartouche.

---

## What we should actually do

**Draw Pope's plate again, properly, and say so.**

1. **Adopt Pope 1716 as the acknowledged model for the schematic register.** He is
   already one of our PD translations; his plate is PD-US at 2,837 × 3,519; his
   lettered-by-book key is precisely the per-scene apparatus we are building; and
   crediting him turns "we made a diagram" into "we are continuing a three-hundred-year-old
   apparatus that modern commentaries abandoned." Put the plate itself on an "About these
   maps" page with its legend transcribed and its `lib. 22` error footnoted. Do **not**
   trace his coastline or his confluent rivers — both are wrong.

2. **Two plates, as already decided, but orient them differently from each other,
   deliberately.** The geographic plate takes the modern north-up frame with the
   reconstructed shoreline band. The schematic plate takes **Pope's viewpoint: sea at the
   bottom, Troy at the top, Ida on the horizon** — because that is the poem's own vantage
   (the poet stands with the Achaeans) and because it makes the camp's left/right
   unambiguous.

3. **Camp schematic — the layout an illustrator can draw.** Beach across the bottom,
   closed at both ends by headland glyphs (unnamed: Sigeion and Rhoiteion are not in the
   Iliad). Ships as a repeating anonymous prow glyph in **three receding ranks**, the
   rearmost rank furthest inland, per 14.31–32; the Achaean wall drawn along the sterns of
   that rearmost rank with the ditch outside it; **the wagon gate at the left end**
   (12.118–19). Five and only five named positions: **Ajax + Protesilaus at the left end**
   (13.681, and the breach point), **Odysseus dead centre with the agora, law-place and
   altars** (11.806–8), **Achilles at the right end** (8.225–26), **Idomeneus far out**
   (10.112–13). Everything else stays an anonymous glyph. A short marginal note carries
   the 13.681/16.286 crux — say the poem is inconsistent, do not draw over it.

4. **Battle phases: lettered zones, not arrows.** Follow Pope, not Osprey. Each scene
   gets a translucent zone on the plain with a letter, keyed to book and line in the
   margin — because we know *regions* of the plain, never vectors, and an arrow claims a
   direction we cannot source. The zones we can defend from the poem: **camp / ditch and
   wall / mid-plain at the tomb of Ilos / the ford / under the walls at the Scaean Gate**,
   plus **left, centre and right** of the line (13.308–9, the poem's own division).

5. **Key the maps the Landmark way.** `Map <Book>.<Line>`, three tiers (locator → main →
   *named* inset), and marginal references that resolve to *(map id, tier, inset name)*.
   Put it in the apparatus JSON, not in prose.

6. **Uncertainty grammar, borrowed whole.** `certain` = normal. `traditional`/
   `speculative` = **italic name** plus `--plate-uncertain` symbol stroke. Name doubtfully
   attached to the feature = **trailing `?`** — a separate axis from location, kept
   separate as Pleiades keeps it. `mythical` = dashed symbol outline. Every sea outline
   carries the Landmark's own caveat verbatim in the legend: *"approximate extent."* The
   washing-troughs get a labelled *absence*, not a dot.

7. **Style, concretely.** Coast stroke down to 1.6 px, `stroke-linejoin="round"`.
   **Four waterlines** at cumulative offsets 2 / 2.6 / 3.4 / 4.4 px, weights tapering
   0.55 → 0.42 → 0.30 → 0.20 and opacity 0.85 → 0.65 → 0.48 → 0.32, generated by repeated
   coast offset then hand-smoothed; none on rivers. Relief: **form lines**
   (`stroke-dasharray="5 4"`, 0.6 px) wherever we are guessing at the ridge, which is
   everywhere; Lehmann hachures only where an authored ridge exists; **never hill
   shading**. Marsh as stipple at radius 0.9 so it reads lighter than relief. Type: four
   sizes, ≥ 2 pt apart, never below 9.5 px, rank by weight not size — letterspaced caps
   for regions, roman for settlements, italic for water and peoples, sans for modern
   names. Haloes via the `paint-order` **attribute** at 2.5 px. Double neatline; margin
   ticks only; stades-over-kilometres bar scale.

8. **Add a contrast unit test.** Every new map token must clear **3:1 against both
   `--scene-map-land` and `--scene-map-sea` in its own theme**.
   `shared/__tests__/scenemap.test.ts` is the place to hang it. See "Defects this lane
   found in existing code" above — the current land/sea pair fails at 1.086:1 and 1.022:1
   and the polarity flips between themes. That is a real accessibility defect today, and
   waterlines are the fix, not decoration.
