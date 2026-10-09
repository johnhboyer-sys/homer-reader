# RESEARCH-CITADEL — scaled plans of the Troy citadel

Research lane, 2026-07-29. Consumed by: the `troy-citadel` plate rebuild
(`apparatus/plates/troy-citadel.json`). Brief: `docs/TROY-MAPS-HANDOFF-2.md` §3.6, §5.

Per CLAUDE.md: apparatus may draw on in-copyright scholarship as a SOURCE, cited
precisely. **Geometry authority and identification authority are kept apart in every
entry below.** Every claim carries `authority:` and `verified how:`.

---

## VERDICT

**YES. Scaled, licence-clean citadel geometry is obtainable, and it is georeferenceable.**

The source is Dörpfeld 1902 — not its prose, its **eight large plates**, which are
scanned, in the public domain in the US, drawn at declared scales (1:500 and 1:800),
and ruled with a **20 m coordinate grid**. Above all:

- **Tafel V — "Troja VI, die Burg der mykenischen Zeit, das Troja Homers"** — the
  ground plan of every Troy VI wall then uncovered, 1:800, on the 20 m grid, with
  contours and spot heights in metres.
- **Tafel III** — all layers, 1:500, same grid, heights on every wall.
- **Tafel II** — the Ritter von Wolff 1883 survey of mound and plateau: **true north**,
  metric scale bar, contours.
- **Figur 470, p. 610** — Dörpfeld's restored circuit with the missing north wall, north
  arrow and a 0–200 m scale bar. This is the honest schematic, drawn by the excavator.
- **Tafel VIII** — sections through the mound at true scale, labelled by layer.

And the georeferencing is already done for us by somebody else: the Troia project kept
**Dörpfeld's own 20 × 20 m grid** as its excavation net (SDK87) and tied it to **ITRF97**
by GPS in July 2000 to better than ±4 mm. Messmer's 2014 chapter is open access and
prints 36 control points in **both** SDK87 and Gauß-Krüger (WGS84, 27° meridian). I
fitted the two lists: a plane similarity, **rotation 5.0199°, scale 1.0000602, mean
residual 3 mm, max 12 mm**. So Dörpfeld's grid is a world coordinate system with a
published transform — **up to two gaps a rebuild must close**: the letter→easting half of
the grid mapping is unresolved (§6 item 1), and the tie from published control points to
visible structures is unverified (the ~65 m Odeon residual, §7). A rebuild therefore
georectifies on identifiable features and uses the net as a scale check, not the reverse.

What is **not** obtainable PD-clean is the **lower-city ditch**. Its only mapped form is
the Troia project's magnetometry interpretation (Blindow–Hübner–Jansen 2014, Abb. 13), a
2014 in-copyright figure. Its *facts* — ~700 m traced, ≤3 m wide, ~1.5 m deep, Troia
VI/VII, plus an inner and an outer ditch and a gate passage in the south — are citable
prose. Its *line* is not ours to trace. See §3.2 and §7.

**Consequence for the title.** "As the Spade Found It" is defensible for the *excavated*
register and is not defensible for the plate as it now stands (29 layers of ellipse arcs
and 4-vertex rectangles, no plate-level `sources`). Two honest routes, John's call:

1. **Rebuild geographic**, tracing Tafel V. Then the title may claim the spade — and the
   north side must be drawn as absent, because Dörpfeld refused to dot it in.
2. **Keep it schematic** and retitle so it stops claiming excavation. Suggested:
   *"The Citadel of Troy, after Dörpfeld's restored plan"* (Fig. 470 is exactly that), or
   *"Troy VI: the Citadel as Dörpfeld Planned It, pl. V"* if the traced circuit is used.
   Either way the register label — `schematic` vs `geographic` — must match the geometry
   actually under it.

**RULED (John, 2026-07-30 16:48/16:52/16:53) — see the DESIGN SPEC below.** The
two routes above are superseded by a split, not a choice between them: **two
plates**, Plate A (Troy VI, the poem's city — route 1's rebuild, reader-first)
and Plate B (the excavation history — route 2's territory, optional and
secondary). Plate A ships first.

**Sampling.** Dörpfeld 1902: the plate apparatus is covered in full (all 8 Tafeln
identified and looked at; the official *Erläuterung der Tafeln*, pp. 648–651, read from
the page images; the 58 Beilagen enumerated by OCR, captions sampled not verified — see
§7). Blegen, Rose and Studia Troica 1–19: catalogue-level only, no plate seen. Modern
GIS: four candidates run down (§4), all four measured or read. Not covered: Turkish
Ministry / Troya Museum holdings; the DAI photo archive; Schmidt's *Atlas trojanischer
Altertümer*.

## DESIGN SPEC (John, 2026-07-30 16:48; SPLIT 16:52): TWO plates, not one

**John, 16:52: "let's split the plate of what troy looked like at the time from
the archeological levels etc; that's separate."** So:

**Plate A — Troy VI: the city at the time of the poem. THE citadel plate.**
John, 16:53: **"this is a HOMER reader, not an archeology site"** — the
reader-facing plate is the poem's city, full stop. Tafel V's excavated Troy VI
walls as the authority; the missing north side handled per the VERDICT — either
drawn as absent (excavated register) or completed from Fig. 470's restored
circuit with the restoration **visibly distinguished** (the
`ergraben`/`rekonstruiert` split, carried by line style or tone, stated in the
layer note). Gates as Dörpfeld letters (2e-ii); dimensions from Tolman &
Scoggin 1903 (§3.4) as PD prose. This plate answers "what did Troy look like
when Hector ran its walls?" and never mixes other phases in. **Build this
first; it is the one the reader meets.**

**Plate B — the excavation history. Secondary, and it must earn its place.**
The phase-coloured sheet below is apparatus for the curious — the "nine
cities" story — not a reader-path plate. It is built only after Plate A
ships, if at all; John's call at that point.

## Plate B spec: the phase-coloured single sheet

The plate is **one sheet carrying the whole excavation history, linework
colour-coded by settlement phase over a neutral mound silhouette, with the
legend doubling as the phase filter** — the presentation idea of the AIA
*Uncovering Troy* interactive (§4.5), which may be **cited as inspiration,
never as source**: its geometry is unattributed and its gate names are
directional. Ours is built the lawful way:

- **Linework:** traced from Dörpfeld — Tafel III (all layers, 1:500) for the
  composite; Tafeln IV–VII for the per-settlement layers. **Troy VI is its own
  phase, never lumped** (the AIA page buries it in a III–VI band — that is the
  failure to avoid). North side of VI drawn as absent per the VERDICT.
- **Gates:** Dörpfeld letters (VI T, VI U, VI S) on the sheet; the Homeric
  pairing lives in the note only (John's 2e-ii ruling, TROY-MAPS-TODO).
- **Filter:** the existing plate layer/toggle machinery carries the phase
  legend (like the certainty filter on the geo plates); each layer's note
  names its Tafel.
- **Georeferencing:** §2's published transform, feature-rectified, grid as
  scale check; the §4.1 archived bounds as cross-check.
- **Every layer carries `sources`** (mandatory per the validate_plate
  hardening item), and the LOOK gate applies at render, both themes.

---

## 1. Dörpfeld 1902 — the geometry authority

**Citation (use verbatim).** Dörpfeld, Wilhelm. *Troja und Ilion: Ergebnisse der
Ausgrabungen in den vorhistorischen und historischen Schichten von Ilion, 1870–1894.*
2 vols. Athens: Beck & Barth, 1902.

**Licence.** Public domain in the United States. Published 1902; the maximum US term
available to a foreign work of that date is 95 years from publication, expiring 1997.
No renewal or URAA question survives that. Contributors (Brückner d. 1936, Wilberg,
Winnefeld) do not change it — the term runs from publication.
*verified how:* publication date read off the title page image of the Getty scan
(`trojaundilionerg01dorp`, leaf n5 region; title page OCR line 40–52 reads "Mit 471
Abbildungen im Text, 58 Beilagen, 8 Tafeln / ATHEN / BECK & BARTH / 1902").
*authority:* licence.

**Scans.** Three Internet Archive items, all full-view:

| Identifier | Volume | Leaves | Scanner | Holds |
|---|---|---|---|---|
| [`trojaundilionerg01dorp`](https://archive.org/details/trojaundilionerg01dorp) | 1 | 552 | Getty Research Institute | pp. i–xviii, 1–428; text figures; Beilagen 1–48 |
| [`trojaundilionerg02dorp`](https://archive.org/details/trojaundilionerg02dorp) | 2 | 290 | Getty Research Institute | pp. 429–652; Beilagen 49–68; **all seven plate foldouts** |
| [`trojaundilionerg00drpf`](https://archive.org/details/trojaundilionerg00drpf) | both, 832 pp. | 832 | Univ. of Toronto (Robarts) | 4 foldouts only — inferior for plates |

Also digitised at Heidelberg (`digi.ub.uni-heidelberg.de/diglit/doerpfeld1902ga`,
DOI 10.11588/diglit.1552; Band 2 at `.../doerpfeld1902bd2`). **Heidelberg blocked this
lane's requests** (Anubis challenge, error 9e4edb5b6b850c41) — untested, may serve
better foldout scans; see §6.
*verified how:* `archive.org/metadata/<id>` for each; foldout leaves read out of
`trojaundilionerg02dorp_scandata.xml` (`<pageType>Foldout</pageType>` at leaves 271,
273, 275, 277, 279, 281, 283, each `origWidth` 5616 × `origHeight` 3744).
*authority:* geometry (access).

### 1.1 The eight plates — what each one is

Titles are Dörpfeld's own, from **"ERLÄUTERUNG DER TAFELN", pp. 648–651**. Fetch URLs
give the leaf whose image I actually opened and read.

| Plate | Dörpfeld's title | Scale | Fetch (vol. 2) |
|---|---|---|---|
| **Tafel I** | *Karte der Ebene von Troja* | — | not in these scans (§7) |
| **Tafel II** | *Plan von Troja und Ilion* | metric bar, 100 m ticks | `page/n270_w1600.jpg` |
| **Tafel III** | *Grundriss aller auf der Akropolis ausgegrabenen Ruinen* | **1:500** | `page/n272_w1600.jpg` |
| **Tafel IV** | *Troja II, die prähistorische Burg* | 1:800 | `page/n274_w1600.jpg` |
| **Tafel V** | *Troja VI, die Burg der mykenischen Zeit, das Troja Homers* | 1:800 | `page/n276_w1600.jpg` |
| **Tafel VI** | *Troja VII und VIII. Die Ruinen der vorgriechischen und griechischen Zeit* | 1:800 | `page/n278_w1600.jpg` |
| **Tafel VII** | *Troja IX. Die Akropolis von Ilion in römischer Zeit* | 1:800 | `page/n280_w1600.jpg` |
| **Tafel VIII** | *Durchschnitte durch den Burghügel* | "im richtigen Maasstabe" | `page/n282_w1600.jpg` |

Base URL: `https://archive.org/download/trojaundilionerg02dorp/`. `_w4000` returns
3681 × 3117 px for Tafel V — roughly **7 cm ground per pixel** over the drawn area.
*verified how:* every plate image above opened and read in this lane; the running head
"W. DÖRPFELD, TROJA UND ILION" and "TAFEL <n>" read off each sheet; the *Erläuterung*
read from page images at `page/n263`–`n266_w1500.jpg` (printed pp. 648–651).
*authority:* geometry.

### 1.2 Tafel V is the citadel plan we want

**Claim.** Tafel V gives the ground plan of every Troy VI wall uncovered to 1894, in red,
with the fortification wall's stone substructure in light red and the thinner upper wall
in dark red, over a black underprint of all walls of all periods.
**Citation.** Dörpfeld 1902, 2:650 (*Erläuterung der Tafeln*, Tafel V); pl. V.
*authority:* geometry.
*verified how:* read verbatim from the page image of p. 650 — "Tafel V giebt den Grundriss
aller bisher aufgedeckten Mauern der VI. Schicht, also der Ruinen des homerischen Troja…
Bei der Festungsmauer ist der Unterbau hellrot, die dünnere Obermauer dunkelrot getönt."
Legend block on the sheet itself reads "TROJA VI. / BURG DER MYKEN. ZEIT. / DAS TROJA
HOMERS. / ▮ Ruinen der VI. Schicht."

**Claim — the north side is absent, by the excavator's own refusal.** "Den ganzen
nördlichen und nordwestlichen Teil der Burgmauer, von dem keine Spur erhalten ist, habe
ich deshalb auch nicht einmal durch punktirte Linien anzudeuten gewagt." The conjectural
completion is Figur 470, p. 610. In the north-west the Troy VI buildings are destroyed
for good; only deep wall footings might survive, and searching has failed.
**Citation.** Dörpfeld 1902, 2:650.
*authority:* geometry (a stated absence — the strongest kind of negative datum).
*verified how:* read from the p. 650 image; corroborated on the sheet, where the circuit
simply stops at the north-west and north-east.
**Plate consequence.** The current `lost-north-circuit` layer (11 vertices, `kind:route`)
is right in spirit. Drawn as a dotted guess it contradicts the source. Dörpfeld's own
convention is available and better: on Fig. 470 "was auf dem Plänchen nicht gesichert
ist, habe ich durch Fragezeichen oder durch Punktirung kenntlich gemacht" (2:630) — he
dots and question-marks the unsecured, and he does that only on the *restored* plan, never
on the survey plan.

**Claim — the grid is 20 m and it is a coordinate system.** "Der ganze Plan ist durch
Parallelen in kleine Quadrate von je 20 m eingeteilt, die nach einer bekannten Methode
durch Buchstaben und Zahlen bezeichnet werden können." Inscribed numbers are heights
above sea level in metres; two numbers on one wall are present top and (bracketed)
bottom. Double circles are pithoi; wells are B + a small letter — "Ba in J 4 und Bb in
K 4".
**Citation.** Dörpfeld 1902, 2:649 (Tafel III).
*authority:* geometry.
*verified how:* read from the p. 649 image. The grid is visible on Tafeln III–VII,
lettered **A–L** across (I skipped) and numbered **2–10** down, i.e. about 220 × 180 m of
ground, which matches an acropolis of c. 2 ha. Feature locations are given by square
throughout the text: "in K 3 … VI R" (1:—, OCR line 6936), "im Quadrate G 5 vor dem
Gebäude VI C", "in den Quadraten C 6 und D 6", "D 2 bis D 6", "E 8 bis G 9".

**Claim — the plates are oriented to magnetic north, not true north.** Every one of
Tafeln III–VII carries the printed note "DER PLAN IST NACH DER MAGNETISCHEN NORDLINIE
ORIENTIRT. DIE ZAHLEN GEBEN DIE HOEHEN UEBER DEM MEERE AN."
*authority:* geometry (a georeferencing constraint — a rebuild that assumes true north
will be wrong by several degrees).
*verified how:* read off the legend cartouche of Tafeln III, IV, V, VI and VII in the
scans. Tafel II by contrast carries a compass rose marked **N** and a metric bar — it is
the true-north bridge. The rotation is now measured, not guessed: §2.

### 1.3 Gates, towers, ramp — Dörpfeld's own labels and locations

All of the following are Dörpfeld's, from vol. 1's table of contents and text; all are
drawable on Tafel V.

| Feature | Dörpfeld | Where |
|---|---|---|
| East citadel gate **VI S** | "Das östliche Burgthor VI S" | vol. 1, p. 126; pl. V; Fig. 41 p. 129 (section) |
| South citadel gate **VI T** | "Das südliche Burgthor VI T" | vol. 1, p. 131; pl. V |
| West gate **VI U** | "Das West-Thor VI U" | vol. 1, Fig. 46; pl. V |
| East tower **VI h** | "Der Turm VI h an der östlichen Burgmauer" | vol. 1, pp. 121 ff.; pl. V |
| NE tower **VI g** | "Der grosse Nordost-Turm g der VI. Schicht" | pl. V (supporting Beilagen exist but are cited by number nowhere in this dossier until the leaf-check of §7) |
| Troy VI **ramp** | "die in D 7-8 erhaltene Rampe" | vol. 2, p. 651; photo cat. no. 291 |

*authority:* identification (the labels) + geometry (the plate).
*verified how:* contents lines read from the vol. 1 OCR ("Das östliche Burgthor VI S 126.
Das südliche Burgthor VI T 131. Das West-Thor VI U"); Fig. 41 opened at
`trojaundilionerg01dorp/page/n188_w1500.jpg` and read — a scaled section captioned "Das
Ost-Thor in der VI. Schicht (VI S) und in der VII. Schicht (VII S)", with its own 0–2 m
bar, a horizontal datum, and spot heights (32.00, 32.50, 33.50).

**Claim.** Tower **VI h** stands midway between gates VI S and VI T. — "Der Turm VI h
liegt in der Mitte zwischen den zwei Thoren VI S und VI T."
*authority:* identification. *verified how:* vol. 1 OCR, line 7462.

**Claim.** The **main gate** of Troy VI was probably the South Gate VI T. — "Das Hauptthor
der VI. Burg ist wahrscheinlich das Süd-Thor VI T gewesen." Dörpfeld notes independently
that in Roman times the main approach to the acropolis lay between the two theatres,
"fast genau an derselben Stelle, an der auch in mykenischer Zeit das Hauptthor der Burg
gelegen hat."
*authority:* identification. *verified how:* vol. 1 OCR line 7163; vol. 2 p. 651 image
(Tafel VII paragraph).

**Claim — the citadel wall is a polygon, and there is a ring street.** "Im Äusseren sehen
wir die Linie der Mauer als Polygon aus geraden Stücken von fast gleicher Länge gebildet;
im Innern finden wir eine breite Ringstrasse, mehrere zum Centrum der Burg gerichtete
Querstrassen."
**Citation.** Dörpfeld 1902, 2:611.
*authority:* geometry (a shape constraint: straight segments, not an ellipse — which is
precisely what the present plate gets wrong).
*verified how:* p. 611 image read (`trojaundilionerg02dorp/page/n224_w1500.jpg`).

**Claim — WARNING: the famous paved ramp is Troy II's, not Troy VI's.** Dörpfeld's
"gepflasterte Rampe" with its retaining walls belongs to the Troy II gate **FM**; the
ramp retaining wall **BC** is Troy II in square H 4. The Troy VI ramp is a separate,
smaller thing, preserved in squares **D 7–8**. A north gate, if restored, "würde durch
Rampen zugänglich sein", and a retaining wall of such a ramp survives beside the
north-east tower.
*authority:* identification (period attribution) + geometry (grid squares).
*verified how:* vol. 1 OCR lines 4032, 4267 (gate FM, paved ramp), 3914 (Fig. 13, "Die
Stützmauer BC im Quadrate H 4, zu einer Rampe der II. Schicht gehörig"); vol. 2 p. 651
image ("die in D 7-8 erhaltene Rampe"); vol. 2 photograph catalogue entries "291 Rampe
von VI in D 7-8", "Rampe in D 8, von W.", "Rampe des Thores FM von II".
**Plate consequence.** The `paved-ramp` layer (6 vertices) must declare which ramp it is.
On a Troy VI plate the answer is D 7–8, and it is not paved.

### 1.4 Figur 470 — the restored plan, and the honest model for a schematic

**Claim.** Dörpfeld 1902, 2:610, Figur 470, "Ergänzter Plan der Burg Troja mit Umgebung",
carries: contours, a **north arrow**, a **0–200 m scale bar**, and these labels —
SKÄISCHES THOR (north-west), DARDANISCHES THOR (south/south-east), ERINEOS-HUEGEL (west),
BURG TROJA, SIMOEIS-THAL, SKAMANDER-THAL, QUELLE (south-west), OBERE EBENE / SPAETERE
STADT, and three roads: FAHRWEG ZUM OBEREN SIMOEIS, FAHRWEG ZUR BURG, ZUR FURT DES
SKAMANDER.
*authority:* geometry (scaled, oriented) for the mound and roads; identification for the
gate names; **speculative** for the Scaean position, by Dörpfeld's own words.
*verified how:* page image read at `trojaundilionerg02dorp/page/n223_w1500.jpg`; every
label above transcribed from that image.

This figure does, in 1902, exactly what our schematic register is for. If John chooses
the schematic route, **"after Dörpfeld, Fig. 470"** is an accurate and honest subtitle, and
the plate can carry his roads and his Erineos hill as well as his gates.

---

## 2. Georeferencing — SDK87, ITRF97, and the 5.02° rotation

**Citation.** Messmer, Eberhard. "Die Vermessungsarbeiten in Troia seit 1987." In
*Troia 1987–2012: Grabungen und Forschungen*, Studia Troica Monographien 5, 2014.
Open access: <https://publikationen.uni-tuebingen.de/xmlui/handle/10900/73562>
(PDF: `StTrMonograph5_Messmer.pdf`).
Series editors Ernst Pernicka, Charles Brian Rose, Peter Jablonka.

**Claim 1 — the modern excavation grid *is* Dörpfeld's grid.** The 1987 task was "»nur«
das in den vorliegenden Plänen seit Schliemann und Dörpfeld eingezeichnete Rasternetz mit
20 × 20 m in die Örtlichkeit zu übertragen", so that new work could be referred to
Schliemann–Dörpfeld and Blegen. No marking of the old net survived on the ground, so it
was reconstructed: 26 identical points were identified on standing structures, measured
into a provisional local system, and **their coordinates in the Schliemann–Dörpfeld grid
were read graphically off the existing plans**; the resulting system is the
**Schliemann-Dörpfeld-Koordinatensystem 1987 (SDK87)**. Height datum: Propylon II C,
H = 30.79 m. Target accuracy in position and height better than ±1 cm.
*authority:* geometry (the whole chain).
*verified how:* `pdftotext -layout` of the OA PDF, lines 316–380.

**Claim 2 — SDK87 is tied to ITRF97.** GPS on 12–13 and 22–23 July 2000 at points
**100/005 (TROI, by the Odeion / Theatre C)** and **100/027 (TROA, in the excavation
village)**; Bernese software 4.2; result "eine Lagegenauigkeit von besser als ±4 mm und
eine Höhengenauigkeit von besser als ±6 mm", datum **ITRF97**. Sixteen further SDK87
control points were GPS-measured to fix the transformation; residual scatter 0.2–0.7 cm
in position. Messmer: since that 2000 georeferencing, "können heute problemlos digitale
Daten wie Satellitenbilder eingepasst oder georeferenziert werden."
*authority:* geometry. *verified how:* same PDF, lines 425–560.

**Claim 3 — the transform is published as coordinate pairs, and it fits.** Tab. 2
("Koordinatenliste Troia 2000") prints, for each control point, Gauß-Krüger coordinates
(**WGS84 ellipsoid, 27° meridian**) alongside the SDK87 running coordinates and the height.
I extracted 36 complete pairs and fitted a plane similarity SDK87 → GK:

```
scale     1.0000602
rotation  5.01987°
tx        426 605.463      ty  4 413 614.892      (GK metres, zone prefix 9 removed)
residuals mean 3 mm,  max 12 mm,  n = 36
```

*authority:* geometry (derived).
*verified how:* pairs parsed from the PDF text of Tab. 2 (e.g. `100014  9435280,779
4425017,849  35,632  9639,234  10599,48  35,632`); least-squares 4-parameter Helmert fit
computed in this lane; residuals as printed above. Independent sanity check: inverse
transverse-Mercator (WGS84, CM 27°, k=1, FE 500 000) on the same table puts all 36 points
between **39.9533–39.9593 N and 26.2331–26.2458 E** — on Hisarlık, inside the World
Heritage polygon's bounding box as traced in OpenStreetMap (§4.2).

**What this buys the rebuild.** Tafel V's 20 m grid is not decoration; it is the same net
that is now tied to ITRF97. A trace of Tafel V can be placed in WGS84 in either of two
ways:

- **Grid route (preferred, exact).** Assign SDK87 coordinates to grid intersections on the
  plate, then apply the transform above. This needs one more fact — the mapping from
  Dörpfeld's letters/numbers to SDK87 metres. The row half is already solved and verified
  (below). The column half is the single open item; see §6.
- **Feature route (no grid needed).** Georectify the plate against imagery on identifiable
  standing structures — the East Tower, the Odeion, Theatre C, the South Gate — and use
  the 20 m grid only as an internal scale check. Standard, and adequate for a plate.

**Claim 4 — the row mapping is solved up to the cyclic origin.** Rows are 20 m, numbered
1–60 cyclically, and the SDK87 northing decreases southward: for rows south of the
x = 10800 line, row *n* sits at **x = 10800 − 20·n**.
*authority:* geometry (derived). *verified how:* the margin labels of Blindow–Hübner–Jansen
2014 Abb. 13 were read at 450 dpi — "55 x=10900", "60 x=10800", "5 x=10700", "10 x=10600",
"30 x=10200", "35 x=10100". Formula checks at n = 5, 10, 30, 35. Independently confirmed
from that chapter's prose, which locates a wall widening "bei mn15 (N 10500, E 8950)" —
and 10800 − 20·15 = 10500 exactly. **But the labels 55 and 60 do NOT satisfy the naive
linear formula** (it would give 9700 and 9600): under the cyclic 1–60 numbering they
denote the rows at −5 and 0, i.e. x = 10800 − 20·(n − 60) = 10900 and 10800. So the
formula holds only after unwrapping, and fixing the absolute origin for an arbitrary row
label needs Messmer Abb. 2 (§6 item 1) — a plate rebuild must anchor on the labelled
x-values it can read, never on the row number alone.

**Claim 5 — the Dörpfeld system and the running coordinates are used interchangeably in
the modern literature.** "Für die Lokalisierung unterschiedlicher Strukturen wird dabei
wahlweise das Dörpfeld-System (Unterteilung der Fläche in Areale von 20 m mit zugeordneten
Buchstaben bzw. Zahlen) oder auch die laufenden Koordinaten des modernen
Vermessungssystems benutzt."
**Citation.** Blindow, Norbert, Christian Hübner, and Hans Günter Jansen.
"Geophysikalische Prospektion." In *Troia 1987–2012*, Studia Troica Monographien 5, 2014,
680. DOI [10.15496/publikation-14981](http://dx.doi.org/10.15496/publikation-14981);
open access <https://publikationen.uni-tuebingen.de/xmlui/handle/10900/73573>.
*authority:* geometry (the equivalence). *verified how:* PDF text, p. 680.

---

## 3. In-copyright plan sources

### 3.1 Blegen, *Troy* I–IV (Cincinnati / Princeton)

**Claim.** Blegen, Carl W., John L. Caskey, and Marion Rawson. *Troy III: The Sixth
Settlement*. 2 pts. Princeton: Princeton University Press, 1953. Part 1 text, xxix + 418
pp.; part 2 plates, 512 figures, "maps and plans (some folded)". Vol. I (general
introduction; first and second settlements) 1950; vol. II (third–fifth) 1951, xxii + 325
pp. and 318 plates; vol. IV (Troy VIIa etc.) 1958.
*authority:* identification (a catalogue fact about what exists). **No Blegen plate was
seen by this lane.**
*verified how:* the Cambridge Core review records for *Antiquity* and *Classical Review*
(vol. III, 1953, "Part 2 (Plates): 512 figs.") and the *JHS* combined review of vols. II
and III; dealer and library catalogue descriptions for the folded plans.
**Licence.** Presumed in copyright in the US. Books published 1950–1958 needed renewal in
their 28th year; whether Princeton renewed these was **not checked**. See §6.
**Use.** Source, cited, for gate/tower dimensions and phasing. Not a geometry source for
us unless John obtains it and decides the tracing question.

Blegen's own summary volume, *Troy and the Trojans* (London: Thames & Hudson, 1963),
carries the widely reproduced Troy VI plan. Also in copyright.

### 3.2 The lower-city ditch — Korfmann's magnetometry

**Claim (facts, citable).** Magnetometry across the lower city, 1988–2007, mapped over
40 ha at 8 readings/m². It revealed the orthogonal Hellenistic/Roman street grid, the main
course of the Hellenistic city wall, and **a rock-cut ditch of the Late Bronze Age (Troia
VI/VII), up to 3 m wide and about 1.5 m deep, traced for roughly 700 m**, interpreted as
a defensive ditch / approach obstacle around the lower settlement. The detailed account
adds: the rock cut is ~3 m wide and up to 2 m deep; it was followed **340 m** west–east;
a break is interpreted as a **gate passage**; in square **n28** it turns north-west, and
after some 120 m, at square **i25**, indistinctly north-east. A further, **outer** ditch
anomaly at **g28** was dated by its fill to Troia VII, later than the known "inner"
ditch — read as an enlargement as the settlement grew. Georadar failed to find the Bronze
Age ditch: its fill absorbs the signal.
**Citation.** Blindow, Hübner, and Jansen 2014 (as above), 666–67, 688–91.
*authority:* prose + identification. *verified how:* PDF text of the OA chapter, German
and English abstracts and pp. 688–91, read in this lane.

**Claim (the map).** Abb. 13, "Interpretation der Hauptstrukturen der Magnetik-Prospektion"
(credited "Troia-Projekt – Universität Tübingen 2010", compiled from the project GIS by
Peter Jablonka), is a scaled, oriented, grid-ruled plan. It carries the 20 m lettered grid
and the SDK87 running coordinates on its margins, a north arrow, a 0–500 m scale bar,
contours, and a legend distinguishing Troia VI (red), Troia VIIa, Troia VIII–IX (cyan),
modern tracks and field boundaries, high-temperature zones, and the old river bed. Labelled
on the sheet: *Stadtmauer (Troia VIII)*, *Graben (Troia VIII)*, *innerer Graben (Troia VI)*,
*Äußerer Graben (Troia VIIa?)*, *Abwasserkanäle (Troia VIII–IX)*.
*authority:* **geometry** — this is a real georeferenceable plan, the only mapped form of
the ditch I found.
*verified how:* PDF page rendered at 130 and 450 dpi and read in this lane; all labels
above transcribed from the image.
**Licence.** In copyright (2014). (The repository's own licence-terms URI 404s as of
2026-07-29, so the exact reuse terms could not be re-verified live — the conservative
posture below stands regardless.) Open access to read, which is not a licence to
redraw. Extracting the ditch's *course* as coordinates and redrawing it is arguably
fact-extraction, not copying; tracing the *line* produces a derivative of their
cartography. **John's call.** Note also the chapter's own warning: the printed
magnetogram is heavily compressed and "nicht gut geeignet" as a basis for planning — for
which "die detaillierte Datenbasis im GIS" should be used. That is an argument for asking
Tübingen (§6) rather than tracing the figure.

**Also.** Jansen, Hans Günter, and Norbert Blindow. "The Geophysical Mapping of the Lower
City of Troia/Ilion." In *Troia and the Troad: Scientific Approaches*, edited by Günther
A. Wagner, Ernst Pernicka, and Hans-Peter Uerpmann. Berlin: Springer, 2003, ch. 22.
<https://link.springer.com/chapter/10.1007/978-3-662-05308-9_22>. Paywalled; not seen.
*authority:* catalogue only.

**Studia Troica** 1–19 (Mainz: Philipp von Zabern, 1991–2012; ISSN 0942-7635) carries the
annual reports in which the citadel and lower-city plans first appeared. Not openly
digitised; HathiTrust catalogue record 002983437 is a catalogue record, not full view.
Specific figures the 2014 chapters cite, which a library visit should pull: **Korfmann
1991** (*Studia Troica* 1), 17, Abb. 17–21 and Abb. 23 (Sondage in K 13); **Jablonka
1996**, 84–86, Abb. 12 (ditch fill, up to 9 m wide in that sondage); **Becker et al.
1993**, 127–29, Abb. 9; **Hübner–Giese 2006**, Abb. 4; **Jansen 2006**, Abb. 12.
*authority:* catalogue only, from the 2014 footnotes. *verified how:* footnotes 31, 33,
64, 65, 35 read off the rendered PDF pages.

### 3.3 Rose 2014

**Claim.** Rose, Charles Brian. *The Archaeology of Greek and Roman Troy*. Cambridge:
Cambridge University Press, 2014. Illustrated with site plans and photographs, including
the Troy VI South Gate and the lower-city defensive ditches. In copyright.
*authority:* identification / catalogue. **No figure list confirmed.** The publisher's
preview PDF exists (api.pageplace.de) but was not opened by this lane; the AJA review
(120.4, 2016) is the other route in.
**Use.** Best modern English source for identifications and for the state of the
fortification question. Not a geometry source for us.

Rose also contributed to the 2014 final publication and is one of its editors, so a
chapter of his sits in the OA collection at
<https://publikationen.uni-tuebingen.de/xmlui/handle/10900/73269>.

### 3.4 A PD English source worth having

**Claim.** Tolman, Herbert Cushing, and Gilbert Campbell Scoggin. *Mycenaean Troy, Based
on Dörpfeld's Excavations in the Sixth of the Nine Buried Cities at Hissarlik*. New York:
American Book Company, 1903. **Public domain** (1903). Transcribed on Wikisource
(<https://en.wikisource.org/wiki/Mycenaean_Troy>); three IA scans
(`mycenaeantroybas00tolmuoft`, `cu31924028248650`, `mycenaeantroyba00drgoog`).
It gives metric dimensions in English:

- East Gate **VI S** — passage c. 2 m broad, opening c. 1.80 m
- South Gate **VI T** — 3.20 to 3.35 m broad, drainage canal 0.50 m deep, 0.30–0.40 m wide
- West Gate **VI U** — opening c. 2.50 m
- South Tower **VI i** — front wall 4.40 m broad, side walls 2.20 m thick
- East Tower **VI h** — juts 8 m beyond the wall, over 11 m broad, front wall c. 3 m thick
- NE Tower **VI g** — projects 8 m, 18 m broad, "the most stately tower"

*authority:* prose (dimensions), derivative of Dörpfeld.
*verified how:* the chapter "The Mycenaean City" fetched and the passages read.
Its **Plan I, "The Restored Citadel"** is on Commons
([File:Mycenaean Troy p008-Plan I.jpg](https://commons.wikimedia.org/wiki/File:Mycenaean_Troy_p008-Plan_I.jpg),
940 × 780) — I opened it: a **degraded reproduction of Dörpfeld's Fig. 470**, contours and
scale bar intact, labels lost. Use Dörpfeld's original, not this.

---

## 4. Modern georeferenced datasets — four candidates, all run down

### 4.1 The Tübingen Troia WebGIS — real, layer-coded, and dead

**Claim.** The Digital Humanities Center at Tübingen published an interactive plan of Troy
built in **QGIS with qgis2web and Leaflet** (summer semester 2016; students Michael
Albers, Marcel-Christian Hagner, Marcel Philipp; instructors **Peter Jablonka** and Dieta
Frauke Svoboda). It had one GeoJSON layer per period — `TroiaVI19.js`, `TroiaVIIa22.js`
and so on, plus German label layers — each feature carrying a `Phase` attribute and a
state of `ergraben` (excavated) or `rekonstruiert` (reconstructed), and two georeferenced
raster overlays: `Satellitenaufnahme0.png` and **`magnetischeProspektion1.png`**.
**Project page.** <https://uni-tuebingen.de/en/forschung/forschungsinfrastruktur/digital-humanities-center/projekte/troia/>
**Status: gone.** The host `escience-lehre.uni-tuebingen.de` no longer resolves, and the
Wayback Machine holds **only** the HTML page (20 Sep 2020) — none of the `data/*.js`
layers or the overlay PNGs was ever captured. A CDX sweep of the whole domain returns 31
URLs, one of them being the map page.
*authority:* geometry (would have been ideal); currently unavailable.
*verified how:* Wayback snapshot fetched and parsed in this lane; every `<script src>`
enumerated; each `data/*.js` fetch returns the Wayback "not archived" HTML page; CDX
queries for `…/troia/data/*` return nothing.

**What survives, and is useful.** The map's own configuration, in EPSG:4326:

```
citadel view          fitBounds  [[39.9557104771, 26.2348395456], [39.9590772823, 26.2416894616]]
satellite overlay     bounds     [[39.9476125731, 26.2252368453], [39.9644725275, 26.2543831006]]
magnetometry overlay  bounds     [[39.9497293146, 26.2311843651], [39.9599231548, 26.2505169762]]
```

The magnetometry bounds are a **published georeferenced footprint** for Korfmann's
prospection: about 1.13 km N–S by 1.65 km E–W. The citadel view is 374 m × 585 m.
*authority:* geometry. *verified how:* read out of the archived HTML.
**Action:** this is the single best thing to ask Jablonka for (§6). It existed, in QGIS,
in WGS84, with excavated/reconstructed already separated. That is the whole plate.

### 4.2 OpenStreetMap — measured, and not enough

**Claim.** OSM carries the World Heritage boundary way (`way/423938794`, "Archaeological
Site of Troy", `ref:whc=849`, 929 m perimeter, 26 vertices), a named Bronze Age **East
Tower** (`way/666487715`, `historic:period=bronze-age`, `man_made=tower`,
`tower:type=defensive`, centroid 39.957192, 26.239463), the Roman **Odeon**
(`way/244849576`), and **53 `barrier=wall`, `wall=dry_stone` ways** totalling **978 m over
199 vertices** inside a 358 × 327 m box (lat 39.955317–39.958530, lon 26.236172–26.240001).
Mean vertex spacing across all traced ways is 12.6 m.
**Licence.** ODbL. Attribution: "© OpenStreetMap contributors".
*authority:* geometry.
*verified how:* two Overpass queries in this lane (`around:1200–1500` of 39.9575,
26.2389), lengths and vertex counts computed, then **rendered to PNG and looked at**. The
picture is the finding: scattered short segments in three loose clusters, **no closed
circuit, no recognisable Troy VI plan**. It is a partial armchair trace of what shows on
imagery.
**Verdict.** Not usable as the citadel circuit. Usable as an independent check on a
georectification (the East Tower and the Odeon are control features) and as the source of
the World Heritage boundary if the plate wants one.

### 4.3 Wikimedia Commons — a PD vector plan of unverifiable descent

**Claim.** [File:Plan Troy-Hisarlik-en.svg](https://commons.wikimedia.org/wiki/File:Plan_Troy-Hisarlik-en.svg)
— "Plan of the archeological site of Troy/Hisarlik", by Bibi Saint-Pol, 12 September 2006,
**public domain**, 1280 × 1155 nominal. It is genuine vector: **128 `<path>` elements,
c. 1173 coordinate pairs, 85 text elements**, layer-coded Troy I / II / VI / VII / VIII–IX,
with a **north arrow** and a **0–25–50 m scale bar** and a 34-item numbered legend
(1 Gate, 2 City Wall, 3 Megarons, 4 FN Gate, 5 FO Gate, 6 FM Gate and Ramp, 7 FJ Gate …).
**Provenance is the problem.** The stated source is a page on `goddess-athena.org` and a
JPG from `clubachille.free.fr`. It names no excavation, no scholar and no scale authority.
*authority:* geometry that is *plausible but unattributable*. I rendered it and looked:
the Troy VI circuit is congruent with Dörpfeld's Tafel V — same polygon, same gates, same
absence on the north and north-west. So it is almost certainly a redrawing of a
Dörpfeld-descended plan. "Almost certainly" is not a citation.
*verified how:* SVG downloaded, paths and labels counted; Commons `imageinfo` API read for
licence, author and credit; the 1920 px raster rendered and compared with Tafel V by eye.
**Verdict.** Do not cite as the geometry authority. Legitimate uses: a fast sanity check
on a Tafel V trace, and a cross-check on the numbered feature labels.

### 4.4 UNESCO — a 1:5000 map exists

**Claim.** The World Heritage Centre holds the 1998 nomination file for the Archaeological
Site of Troy (849), c. 21 MB (`whc.unesco.org/uploads/nominations/849.pdf`), and a map
"Troia, scale 1:5000" dated 2009, on <https://whc.unesco.org/en/list/849/maps/>.
*authority:* catalogue only at first; **both OBTAINED and read 2026-07-30** (John's
click past the 403). Verdict in §6 item 8: boundary yes, site plan no — the sheet is
a cadastral base, not an excavation plan. Notes: `research-cache/unesco-849-notes.md`.

### 4.5 A trap to name

**Claim.** [Vici.org record 20632](https://vici.org/vici/20632/) publishes a point for the
"Scaean Gate" at **39.957352, 26.237906**, with a stated accuracy of "± 0–5 m", added by a
user in June 2015, **citing no source at all**.
*authority:* none. It is a fabricated coordinate with an accuracy claim attached, in a
gazetteer our tooling could plausibly harvest.
*verified how:* page fetched and read in this lane.
**Rule:** the Scaean Gate has no coordinate. Anything that offers one is wrong, and this
one is CC BY-SA so it will propagate. Do not place a point.

Similarly, *Archaeology* magazine's interactive Troy map
(<https://archaeology.org/travel/interactivemap-troy/>) credits only its funder, states no
base plan, no source and no licence, and uses directional gate names only ("South Gate",
"West Gate"), never VI T / VI S / VI U.
*authority:* none. *verified how:* page fetched and read.

---

## 5. The Scaean and Dardanian gates, as the scholarship states it

This pairing is contested. Below is the evidence; the verdict is John's.

**Dörpfeld (1902): VI T = the Dardanian Gate; the Scaean at the north-west corner,
conjecturally.**

- Contents heading, vol. 1, p. xviii: "Das Thor VI T ist das dardanische Thor Homers 629."
- p. 630: "Man wird hiernach verstehen, dass ich ohne Zögern das Thor VI T als das
  dardanische bezeichnet … habe."
- p. 610: "In meiner Reconstruction des Stadtbildes in homerischer Zeit (Fig. 470) lege ich
  das skäische Thor **vermutungsweise** an die Nordwest-Ecke der Burg, muss aber zugeben,
  dass es auch weiter östlich gelegen haben kann." He adds that since the north wall's
  foundations *may* survive under the spoil heaps, a further dig at the north-west corner
  would be worth doing.
- p. 630: "Das skäische Thor kann … weiter östlich gelegen haben und würde dann vielleicht
  mit dem Nordost-Thor zusammenfallen." Earlier (2:609) he notes that the great tower "beim
  skäischen Thore" could tempt one to look for the Scaean near **tower g**, the north-east
  tower, since Homer's tower there is called simply "the great tower".
- His argument is narrative: the wall-run of Hector and Achilles starts at the Scaean Gate
  on the north side of the city, so its far point, the Dardanian Gate, must be on the south;
  the springs lie between; Hector is killed behind the city, out of sight of the Trojans on
  the tower of the Scaean Gate; Priam means to use the Dardanian Gate at Il. 24.413.

*authority:* identification. *verified how:* pp. 610 and 630 read from the page images
(`page/n223`, `page/n245`); the contents line read from the p. xviii image (`vol. 1
page/n21`).

**Tolman and Scoggin (1903), following Dörpfeld, in English:** "Of the three gates
unearthed in our city, VI T must have formed the principal entrance … It is presumable
that the Dardanian Gate lay in the direction of the Ida range, toward the southeast, where
Dardania was situated, and where the excavations have brought to light the great South
Gate, VI T. … The Scaean Gate, on the other hand, must have been on the side of the hill
toward the Greek ships. If we restore a northwestern gate in the missing North Wall, we
should have a gate opening, as did the Scaean Gate, on the battlefield, and flanked on the
assailants' left by a mighty tower from which the beholder had an extensive view over the
plain."
*authority:* identification (derivative of Dörpfeld). *verified how:* Wikisource text of
the preface read.

**The site-guide tradition (not scholarship, but it is what visitors are told):** the South
Gate / South Tower complex is widely labelled Homer's Scaean Gate on the ground and in
guidebooks. This is the opposite of Dörpfeld's assignment for the same structure, which is
why our gazetteer entry for `scaean-gate` says the South Gate "is at least as often
identified with the Dardanian Gate."
*authority:* identification, popular. *verified how:* search results only; **no scholarly
statement of this position was located by this lane.** See §7.

**What no source supplies:** a physical gate identification that scholarship agrees on. The
one thing every source agrees about is the reason: the north and north-west wall, where the
poem's traffic runs, is destroyed. Dörpfeld's word for his own Scaean placement is
*vermutungsweise*.

**Plate consequence.** Tier `speculative` for `scaean-gate`, no point, and the note should
say what Dörpfeld says: the candidates are a *lost* north-west gate (his own preference),
the north-east gate beside tower g (his own alternative), and — against him — the surviving
South Gate VI T. `dardanian-gate` gets tier `traditional` with the tradition named:
"Dörpfeld 1902 and those following him identify the Dardanian Gate with the excavated South
Gate VI T."

---

## 6. Needs paywalled access

Ordered by what each settles.

1. **Messmer 2014, Abb. 2, "Übersichtsplan Grabungsnetz Troia"** (Studia Troica Mon. 5,
   p. 399) — at print resolution. **Settles the one open item in §2:** the mapping from
   Dörpfeld's grid **letters** to SDK87 eastings. The rows are already solved. With this,
   Tafel V can be georeferenced exactly rather than fitted. (The OA PDF has it, but the
   figure is too small to read the labels; a library copy or the original TIFF would do.)
2. **Blindow–Hübner–Jansen 2014, Abb. 12 and Abb. 13** (Studia Troica Mon. 5, pp. 679,
   681) at print resolution, or better, the underlying **Troia project GIS**. Settles the
   lower-city ditch geometry, inner and outer, and the south gate passage. The chapter
   itself says the printed magnetogram is unfit as a planning base and directs users to the
   GIS.
3. ~~**Direct approach to Peter Jablonka / the Troia project, Universität Tübingen**~~
   **DECLINED (John, 2026-07-30 16:46): not sending — "we're doing a plate, not an
   interactive thing."** The WGS84 GeoJSON layers would matter for a live GIS; a drawn
   plate traces Tafel V and takes its georeferencing from §2's published transform plus
   the archived bounds in §4.1. Do not re-flag as pending. (What the request would have
   been, for the record: the dead 2016 WebGIS layers with the `ergraben`/`rekonstruiert`
   split, and any project GIS releasable under a licence we may draw from.)
4. **Dörpfeld 1902, Tafel I** ("Karte der Ebene von Troja") — **FOUND (2026-07-29,
   superseding this dossier's "absent from all scans" claim):** it is in the Getty
   scan after all, at `trojaundilionerg02dorp` leaf **n268**, one leaf before
   Tafel II, hidden behind a blank protective interleaf. Full-colour plain-of-Troy
   map (Spratt 1840 survey, completed 1894), 3489×3501 px at `_w4000.jpg`,
   Grok-verified by download. See RESEARCH-PD-SCAN-HUNTS.md Hunt 3. Belongs to the
   plain dossier, but it is the same PD book.
5. ~~**Blegen, Caskey and Rawson, *Troy III: The Sixth Settlement* (1953), part 2**~~
   **CLOSED BY SCOPE (John, 2026-07-30 16:53): "if Blegen isn't needed for literary
   purposes, let's not be captured by scholarly drift into archeology."** The reader's
   plate (Plate A) traces Dörpfeld; Blegen's re-attributions and phasing are
   archaeology-internal refinements that do not change what a Homer reader sees. Do not
   re-flag. (Renewal search ran 2026-07-30 anyway, see item 6 — I–III renewed, so the
   question was moot in law as well as in scope.)
6. ~~**US copyright renewal search for Princeton University Press, *Troy* I–IV (1950–58).**~~
   **DONE (2026-07-30):** vols. I–III RENEWED (RE116 1978; RE14031 1979; RE107295 1981)
   — in US copyright to c. 2045–48, plates included. Vol. IV (1958): no renewal found in
   CPRS; the Stanford cross-check sits behind a human-verification gate and was not run.
   **Moot by the same scope ruling** — treat all four as in-copyright and move on.
   Full record: `research-cache/blegen-renewal-search-notes.md`.
7. **Rose, *The Archaeology of Greek and Roman Troy* (2014)** — the list of illustrations,
   to know which plans it reproduces and from whom.
8. ~~**UNESCO 849**~~ **OBTAINED (John's click, 2026-07-30; extracted same day —
   `research-cache/unesco-849-nomination-1998.pdf`, `unesco-849-troia-1to5000-2009.jpg`,
   notes at `unesco-849-notes.md`). Boundary delivered; site plan NOT delivered.**
   The 1:5000 sheet is a Turkish cadastral/topographic base with the World Heritage
   boundary hand-traced in red (158 ha stated) — contours and two buildings on the
   mound, no wall, trench or period line anywhere; no title block, agency, date or
   datum printed. The 96-pp nomination PDF's maps are the same cadastral base plus
   zoning diagrams, all uncredited. Usable geometry: the boundary polygon (~25–30
   vertices; confirms OSM way 423938794's 26-vertex trace is a coarse simplification)
   — an overlay option only, per the scope rule (a Homer reader gains nothing from
   heritage-administration zoning). **TRAP recorded:** the nomination form's own
   "Exact location: 26°19′E; 39°55′N" is ~8 km from the site — a clerical error;
   never harvest it. ICOMOS 1998 recommended deferral for want of precise boundary
   maps; the Committee inscribed on promise. Datum of the 2009 sheet's 5-point
   coordinate table unconfirmed.
9. **Jansen and Blindow, "The Geophysical Mapping of the Lower City of Troia/Ilion"** in
   Wagner, Pernicka and Uerpmann, eds., *Troia and the Troad* (Springer, 2003), ch. 22 —
   the earlier, fuller magnetometry publication.
10. **Studia Troica 1 (1991), 17, Abb. 17–21 and Abb. 23**, and **Jablonka 1996, 84–86,
    Abb. 12** — first publication of the ditch and the K 13 sondage.
11. **Heinrich Schliemann, *Atlas trojanischer Alterthümer* (Leipzig, 1874)** — Dörpfeld
    cites its Tafeln 112, 116, 117 and 214 for Schliemann's earlier excavation plans.
    (Not Hubert Schmidt, who catalogued the Schliemann collection in 1902 and contributed
    to *Troja und Ilion*; a first draft of this dossier mispaired author and title —
    caught at Grok verification.) 1874, so PD; not located.

---

## 7. Unverified — do not claim publicly

- **The Beilage captions.** Beilagen 1–68 were enumerated from OCR, and captions were
  extracted by a positional heuristic that cannot distinguish a plate caption from the
  facing page's running head. The ones that look like real captions — Beilage 17 (gate VI S
  photograph), 19 (east citadel gate VI S), 20/21/22 (the great NE tower g), 23 (VI A and
  VI B), 25 (VI E, VI Q, VI P), 26 (wells B c and B a), 28 (east citadel wall), 67 ("Hatte
  die Burg Troja eine Unterstadt?"), 68 ("Die Entfernung Trojas vom Hellespont") — **were
  not confirmed against the plate images.** Do not cite a Beilage number in the apparatus
  until someone opens that leaf.
- **The plate count.** The title page reads "471 Abbildungen im Text, 58 Beilagen, 8 Tafeln"
  (= 66). The *JHS* review of 1902 says "76 plates". Both are quoted here; the discrepancy
  is not resolved, and vol. 2's Beilage numbering runs to 68, past 58. Do not state a
  total.
- **Tafel VII's scale.** Dörpfeld's *Erläuterung* declares 1:800 for Tafeln **IV–VI**. The
  scale bar printed on Tafel VII reads 1:800 as I read it in the scan, but the text does not
  say so. Treat Tafel VII's scale as read-from-the-sheet, not declared.
- **Control point 100/005 versus the Odeon.** Messmer describes 100/005 (TROI) as "beim
  Odeion (Theater C)". My inverse projection of its published Gauß-Krüger coordinates gives
  39.956720, 26.237825; the OSM Odeon trace centroid is 39.956770, 26.238583 — about 65 m
  apart. That is consistent with a concrete marker set *near* a monument, and it is **not**
  a point-identity check. The §2 transform is verified internally (3 mm residuals on 36
  published pairs); the absolute tie to visible structures is **not** verified by this lane.
  A rebuild must fit control features itself.
- **The column half of the grid mapping.** "mn15 (N 10500, E 8950)" gives one square-to-metre
  pair, and the row formula checks against it exactly. The column reading depends on whether
  "mn" is one column or a span of two, and on where the 20 m column boundaries fall relative
  to E 8950. **Not resolved.** See §6 item 1.
- **The popular identification of the South Gate as the Scaean.** Widely stated on the
  ground and in guides; **no scholarly source for it was located by this lane.** Do not
  attribute it to a scholar until one is found. The `tradition` field must not be filled
  with "scholarly consensus".
- **What Blegen's plans depict.** No Blegen plate was seen. Nothing about Blegen's plans may
  be asserted beyond the catalogue facts in §3.1.
- **Whether the Troia project GIS can be licensed to us.** Unknown. Nothing in §4.1 or §3.2
  may be traced until John decides.
