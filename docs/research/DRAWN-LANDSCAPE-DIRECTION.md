# The Drawn Landscape — Direction for the Troy Panorama

Research lane, 2026-08-14. Findings and art direction only. No code changed, no
image downloaded, traced or embedded. Every plate cited by stable URL with its US
rights status.

---

## 0. What the plate does now, and what that tells us

I looked at `stage3-full-takeA.png` and `stage3-zoom8-troy-takeA.png` before
reading anything. Six observations, because they set the whole brief:

1. **There is not one line on the sheet.** The plate is built entirely of soft
   tonal fill. Every landscape print in the tradition surveyed below — engraving,
   lithograph, hachured survey, bird's-eye view, even Berann's paintings — is
   line-dominant and earns its tone from mark density.
2. **The value range is compressed into the middle.** Nothing is near-black
   except the ship glyphs; nothing is near-white except the sky. A drawn plate
   holds its full range and *spends* the darks.
3. **The plain reads as a dome.** Low-frequency shading over near-flat ground
   makes a bulge. This is the briefed problem and it is real.
4. **Ilios is a smudge with a leader line.** The subject of the plate is not the
   focus of the plate.
5. **At 8× there is nothing there.** The zoom does not reveal a finer grain; it
   reveals that tone-without-mark has no interior. This is the strongest single
   piece of evidence in the whole investigation.
6. **The ship glyphs are one stamp on a lattice.** A tiled asset, not a crowd.

**Verdict on the "selective versus uniform detail" diagnosis: confirmed, and it
needs one correction.** Selectivity is necessary but it is not the mechanism. The
mechanism is that a drawn landscape is made of *discrete marks whose density is
the tone*; selectivity is what you get for free once tone is made of marks,
because you can stop making them. Our plate cannot be selective, because a
continuous gradient has no unit to withhold. Turn tone into marks and selectivity
becomes available; leave it as gradient and no amount of restraint will read as
drawing. The practitioners say the same thing from the other end — Greg Harlin,
who paints these for the US National Park Service: "I spend a lot of time making
it look like I didn't spend a lot of time" (Patterson 2005, 7).

---

## 1. The survey, by problem solved

### 1.1 Where does the detail go, and where does it stop?

The tradition is unanimous and it is not where you would guess. **Detail peaks in
the middle ground.** Not the foreground.

- Philips Koninck, in the flat-land panoramas of the 1650s–60s, "made the figure
  in the middle ground the most prominent and painted the landscape around it in
  a more detailed way than the foreground and far distance" ([National Gallery,
  London](https://www.nationalgallery.org.uk/paintings/philips-koninck-an-extensive-landscape-with-a-road-by-a-river)).
  The foreground is deliberately *coarser* than the middle distance — it is a
  dark, summarily-drawn threshold you look over, not into.
- The Victorian bird's-eye views do the same by other means: the town centre is
  worked building by building, and the edges of the sheet dissolve into open
  ground within a few hundred metres. T. M. Fowler's sheets "showcase a town
  centre where potential map buyers lived" and carry "no labelled depictions of
  other towns in the distance."
- Berann applied outright cartographic generalization: "reinforcement of
  important features and omission of unimportant detail" (Patterson 2000).

**Quantified, with the honest caveat that this is my estimate from looking at
plates and not a published figure:** on a typical guidebook panorama or bird's-eye
sheet, roughly **15–30% of the image area is genuinely worked**. Sky is 25–35%
and is nearly or completely empty. Margin, title, key and scale take 10–15%. The
remaining ~30% is flat tone or bare paper carrying nothing but a boundary. Our
plate works ~100% of its non-sky area at one strength.

### 1.2 Foreground to distance — tone, mark, weight, or omission?

All four, applied together and in a fixed order. The engraved tradition ramps
them in lockstep:

- **Line weight** drops. This is the primary cue and the one we have none of.
- **Mark density** drops, then the mark class drops out entirely — a hachured
  near slope becomes an outlined far slope becomes a bare ruled ridgeline.
- **Contrast collapses**, and this is Imhof's real point about aerial
  perspective: it is not haze, it is *contrast range*. "The highest elevations
  are shown with strong contrast between dark, shaded slopes and bright,
  illuminated slopes, while lowlands... are shown with reduced contrast." Note
  that in a panorama read at a shallow angle, "distant" and "low" coincide.
- **Omission.** The guidebook summit panoramas — Heinrich Keller's Rigi sheets,
  Xaver Imfeld's after them — reduce the far third to a **single ruled outline
  with names above it and nothing below**. No tone at all. The convention is that
  the horizon is a profile, not a picture.

That last is the important one for us. Mount Ida currently gets a grey wash and
a label. The tradition would give it a ruled profile line, a name, and empty
paper — and it would read as *further away*, not as less finished.

### 1.3 Flat ground — the hard problem

This is where the tradition is most useful and most emphatic. Four independent
answers that agree:

**(a) Do not shade it, and do not cast shadows on it.** Imhof is explicit: flat
areas take a bright, even grey tone, "brighter than the physically correct
value," and cast shadows are excluded from the whole system. Our plate does the
opposite — it computes real cast shadows from a low sun and lets low-frequency
relief shading run across a 1.2% slope, which is exactly how you manufacture a
dome out of a plain.

**(b) The hachure system solves it automatically, from the DEM.** Imhof's five
rules for slope hachures (as summarized in Kimerling 2000, *Cartographic
Perspectives* 37): hachures follow the steepest gradient; are arranged in
horizontal rows; length corresponds to the horizontal distance between assumed
contours; **width is thicker for steeper slopes**; density stays constant. Run
that on the Trojan plain and the marks go to hairline — present, even, quiet.
Run it on the Sigeion ridge and they thicken. The plain becomes flat *because the
data says so*, with no threshold to argue about and nothing invented.

**(c) On flat ground, value variation comes from what is on the ground, not from
the ground.** The Victorian bird's-eye views are the proof, because most of those
towns are dead flat and the sheets are gorgeous. Ruger and Fowler drew a
perspective street grid, then walked the town sketching façades. The ground is
never modelled. Interest is entirely: the grid, the blocks, the watercourse, the
tree line, the rail, the smoke. Patterson's account of how the NPS made its
"map-like" views is the vector recipe stated outright — "a framework of casing
lines for roads, pathways, trees, and buildings that were filled with flat
colors" (Patterson 2005, 7).

**(d) Band it horizontally.** Koninck's flat Holland is read as "a series of
ripple-like horizontals formed by hedges, fields, patches of water and distant
hills" — "narrow ribbons of darkness and brightness laid across the canvas"
([Met](https://www.metmuseum.org/art/collection/search/436830);
[Thyssen](https://www.museothyssen.org/en/collection/artists/koninck-philips/panoramic-landscape-city-background)).
Depth in a flat scene is carried by *alternating value bands crossing the line of
sight*, not by modelling. The Japanese woodblock tradition reaches the same
result with `bokashi` — banded gradient laid across the sheet, over flat colour,
with no modelling underneath.

**We already own the data for (d) and are throwing it away.** The plate has
ground-cover classes — dry delta fan, wet delta, ridge scrub — which lie in bands
roughly across the sightline. Drawn as crisp-edged flat tones with distinct mark
textures instead of airbrushed blends, they *are* Koninck's ribbons, derived
entirely from source, fabricating nothing.

### 1.4 What carries the eye, and where does the darkest mark go?

**The darkest mark goes on the subject, and there is almost none of it.** In the
engraved tradition true black is scarce — a few percent of the area — and it is
spent on the thing the plate exists to show, usually where a hard vertical meets
a lit ground.

Our plate spends its only black on a lattice of ship stamps in the mid-foreground
and gives the city a pale ellipse. That is backwards. The plate is called *The
Ships, the Bay, and Ilios*; the eye currently goes to the ships and stops.

The secondary devices, all cheap and all vector:

- **A dark, summary foreground threshold** (Koninck, and every Picturesque plate)
  — a band of near-black across the bottom that the eye jumps to get past. It
  makes everything beyond it read as distance for free.
- **A line that leads.** The wagon-road and the Scamander are the two natural
  leaders on this sheet, and both are currently thin, pale and interrupted.
- **The lit face against the shadowed one.** On the city's spur this is one
  hard-edged tonal step, not a gradient.

### 1.5 Bare page — unfinished, or confident?

Confident, and it is the single most legible marker of a drawn plate. Sky in the
guidebook panoramas is *paper*: no gradient, no tone, occasionally a ruled
horizon and nothing else. Humboldt's *Tableau physique* (1807) sets its
mountain profile in a void and stacks a hundred plant names in the empty margin —
the drawing stays a drawing precisely because the annotation went into the blank,
not onto the landform.

The rule the tradition follows: **bare paper reads as confidence when it is
bounded.** A neatline, a ruled horizon, a crisp coast — one committed edge — and
the emptiness inside reads as chosen. Unbounded emptiness reads as unfinished.
Our sky is a smooth vertical gradient, which is neither: too much to be paper,
too little to be sky.

### 1.6 Place versus diagram

The difference is **evidence of a particular hour and a particular scale**, and
it is carried by very few marks:

- **Scale figures with real variety.** Not one glyph tiled. The bird's-eye
  artists drew each façade; Patterson notes readers spotting "the horse and
  carriage crossing the South Fork Dam." Two or three individuated marks at
  human scale convert a diagram into a place.
- **One asymmetry that no system would produce** — a river that braids on one
  side only, a beach line that breaks, a stand of trees where the swamp meets the
  fan. Systems are read as diagrams; exceptions are read as observation.
- **Hard edges where the world has hard edges.** Coast, wall, ridgeline. Soft
  everywhere is the render tell.

Conversely, what makes a diagram is exactly what we currently have: uniform
treatment, one glyph repeated on a lattice, leader lines doing the work the
drawing should do, and continuous tone with no unit.

---

## 2. Shortlist — eight worth John's own eyes

| # | Work | Rights (US, 2026) | What it teaches |
|---|---|---|---|
| 1 | **Heinrich Berann, US National Park panoramas** (North Cascades 1987, Yosemite 1989, Yellowstone 1991, Denali 1994) — [shadedrelief.com/berann-panoramas](https://www.shadedrelief.com/berann-panoramas/) | Hosted on an NPS server and declared **public domain**; verify before any reproduction (Berann was a foreign contractor). | Generalization as method: reinforce, omit, exaggerate — and still be trusted. Forest and rock are *marks*, never texture. Closest living relative of what we are making. |
| 2 | **Library of Congress, Panoramic Maps** (~1,800 sheets; Ruger, Fowler, Bailey, Wellge, Burleigh, 1860s–1920s) — [loc.gov/collections/panoramic-maps](https://www.loc.gov/collections/panoramic-maps/) | **PD** (pre-1931); LoC states the digitized G&M collections are free to use absent a rights advisory. | **The flat-ground answer in practice.** Dead-flat towns, never a shaded ground, carried entirely by casing line + flat tone + drawn content. Our exact projection. Start here. |
| 3 | **Dufour Map** (1845–64) and **Siegfried Atlas / Topographic Atlas of Switzerland** (1870–1926) — [Topographic Atlas of Switzerland](https://en.wikipedia.org/wiki/Topographic_Atlas_of_Switzerland); sheets at [ETHeritage](https://etheritage.ethz.ch/2008/11/21/guillaume-henri-dufour-topographical-map-of-switzerland-1100-000-page-8-aarau-lucerne-zug-zurich-printed-in-1926/?lang=en) | **PD**. | Hachures: slope-derived marks, thicker where steeper, that *vanish on flat ground by construction*. Directly implementable and it never fabricates. |
| 4 | **Philips Koninck, panoramic landscapes** (1650s–60s) — [National Gallery NG6398](https://www.nationalgallery.org.uk/paintings/philips-koninck-an-extensive-landscape-with-a-road-by-a-river); [Met 436830](https://www.metmuseum.org/art/collection/search/436830) (Open Access) | Paintings **PD**; Met images CC0, NG images non-commercial — study only from NG. | Flat land as horizontal ribbons of light and dark; detail peaking in the **middle** ground; the coarse dark foreground threshold. |
| 5 | **Heinrich Keller, *Panorama vom Rigi-Berg*** (1815/1820), and **Xaver Imfeld's** Rigi-Kulm panorama (1881) — [David Rumsey](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~293033~90064005); [ETH on Imfeld](https://ikgrelief.ethz.ch/cartographers/imfeld/) | **PD**. | The guidebook summit plate: long thin strip, near-zero foreground, the far third reduced to a ruled outline with names and *nothing below it*. |
| 6 | **Choiseul-Gouffier, *Voyage pittoresque de la Grèce*** (Paris, 1782) — [travelogues.gr, collection 117](https://eng.travelogues.gr/collection.php?view=117); [Troad plates](http://eng.travelogues.gr/travelogue.php?creator=1159869&tag=12976&tag1=12980&view=117) | **PD**. | The outline-profile convention applied to *this landscape* — Pınarbaşı, the Scamander springs, the tumuli. Cite for technique; a sibling lane owns Troy iconography. |
| 7 | **Alexander von Humboldt, *Tableau physique des Andes*** (1807) — [PNAS 2019 study with the plate](https://www.pnas.org/doi/10.1073/pnas.1904585116) | **PD**. | How a drawn landform carries very heavy annotation and stays a drawing: the text goes into the void beside the form, never onto it. Our label problem, solved in 1807. |
| 8 | **Eduard Imhof, *Cartographic Relief Presentation*** (Berlin: de Gruyter, 1982; repr. Redlands, CA: ESRI Press, 2007) — [Google Books record](https://books.google.com/books/about/Cartographic_Relief_Presentation.html?id=cVy1Ms43fFYC) | **IN COPYRIGHT — study only.** Scans circulate on archive.org; do not reproduce or excerpt at length. | The two rules that indict our current render: flat areas get a bright even tone, and **cast shadows are excluded**. Aerial perspective is contrast range, not haze. |

Practitioner literature, open access and free to read: Tom Patterson, "A View From
On High: Heinrich Berann's Panoramas and Landscape Visualization Techniques for
the U.S. National Park Service," *Cartographic Perspectives* 36 (Spring 2000):
38–65, [cartographicperspectives.org](https://cartographicperspectives.org/index.php/journal/article/view/cp36-patterson);
and Patterson, "Looking Closer: A Guide to Making Bird's-eye Views of National
Park Service Cultural and Historical Sites," *Cartographic Perspectives* 52 (Fall
2005), [shadedrelief.com PDF](https://www.shadedrelief.com/birds_eye/birdseye.pdf).
A. Jon Kimerling, "Hachures Revisited," *Cartographic Perspectives* 37 (Fall
2000): 78–81, [PDF](https://mbmg.mtech.edu/pdf/gis_hachure.pdf) — carries Imhof's
five hachure rules in usable form.

---

## 3. Style direction for our plate

**The governing sentence: stop rendering the surface and start drawing what is
on it.** Height stays in the geometry, where it already is and where it is
honest. Tone stops being a computed gradient and becomes a countable mark.

**Value.** Adopt a five-step value scale per theme token, not a continuum. Near-
black is rationed to about 2% of the sheet and is spent on the city's shadowed
wall and the foreground threshold. Everything between is one of five steps, and
the steps are edged, not blended. The plate should be readable at thumbnail size
as four or five shapes.

**The plain.** Flat, and *drawn on*. No relief shading below a stated slope
threshold; no cast shadows anywhere. The three ground-cover classes become three
crisp-edged flat tones running as bands across the sightline — Koninck's ribbons,
straight out of our own data. Their interiors are differentiated by mark class,
not by colour alone: open stipple on the dry fan, short horizontal rules on the
wet delta, sparse scrub ticks on the ridge. The Scamander gets real weight and a
real waterline. The wagon-road becomes a continuous drawn line running from the
camp to the gate — it is the plate's spine and should read as one gesture.

**Depth.** Three declared bands with different mark vocabularies, and the
vocabulary itself is the depth cue. Foreground: full weight, dark, coarse,
summary — ships and camp, individuated. Middle: the worked band, finest line, the
most information, the plain and its waypoints. Distance: outline only. Ida
becomes a ruled profile with a name and bare ground beneath it. Sky becomes flat
paper with one ruled horizon.

**Focus.** Ilios is the darkest, most-worked, hardest-edged object on the sheet,
and it is the only place where three mark classes meet — wall, shadowed face, lit
ground. It should be findable without the leader line, and then the leader line
comes off.

**Bare page.** Between a third and a half of the sheet carries nothing but a
boundary, and every empty area is *bounded* — neatline, ruled horizon, hard
coast. Annotation stacks into the emptiness, Humboldt-fashion, and never onto the
worked band.

---

## 4. Ranked implementable changes

Each with the four constraint checks: **V** vector-only, **T** re-themeable via
`var()`, **Z** survives zoom (regenerable per tier), **F** fabricates nothing.

**1. Kill the cast shadows and clamp relief shading on the plain.**
Imhof's rule, and it is one parameter. Below a stated slope threshold, ground
takes flat class colour and nothing else. Delete the drop shadow under the Ilios
disc. *V yes (removes fills). T yes. Z yes — flat tone is scale-free. F yes; this
removes an interpretation rather than adding one. Declare the threshold in the
note.* **Highest value per unit of work on the whole list.**

**2. Give the sheet a line vocabulary — casing lines and a five-step value
scale.** Every region gets an edge: coast, ground-cover boundary, ridgeline,
wall, road, river. Weight steps down by depth band. This is Patterson's stated
NPS vector recipe, "casing lines... filled with flat colors."
*V yes — `<path>` with `stroke`. T yes — stroke tokens. Z yes; regenerate stroke
widths per tier, or `vector-effect: non-scaling-stroke` where a hairline is
wanted. F yes — every casing line traces a DEM or class boundary already
computed.*

**3. Replace relief shading with DEM-derived hachures in the near and middle
bands.** Imhof's five rules, from the slope/aspect grid we already have. On the
plain they self-extinguish; on the ridges they build tone. This is the single
change that most converts render into drawing.
*V yes — short `<line>`/`<path>` runs. T yes — stroke token, and density gives
tone in both themes without a second palette. Z yes, and this is exactly the case
the earlier zoom-tier finding anticipated: regenerate at each tier's sample
density, holding apparent spacing constant. F yes — orientation from aspect,
width from slope, nothing invented.* **Highest craft payoff; largest build.**

**4. Rebuild the focus hierarchy on Ilios.** Move the darkest value and the
finest work to the city; give it a hard tonal step between lit and shadowed
faces; drop the leader line once it is findable. Simultaneously de-weight the
ships from black to the second-darkest step.
*V yes. T yes. Z yes. F yes — a redistribution of emphasis, and every mark still
sits where it already sits.*

**5. Flatten the sky to paper and reduce Ida to a ruled profile.**
Remove the vertical gradient; one ruled horizon; names above the line, bare
ground below.
*V yes. T yes. Z yes. F yes — a profile line is strictly less claim than a tonal
wash.*

**6. Individuate the ships and the camp.** Three or four hull glyphs with varied
length, spacing jittered from a seeded deterministic function rather than a
lattice, a handful of huts, the wall and ditch as one drawn line with a hachured
scarp.
*V yes. T yes. Z yes — regenerate per tier so the crowd gains members rather than
scaling up. F — needs care: the ships are `positionBasis: "conjectural"` already
and the note says so; varying a glyph adds no locational claim, but the ditch's
hachured scarp must stay inside the existing conjectural declaration.*

**7. Mark-differentiate the ground-cover bands and crisp their edges.**
Stipple / horizontal rule / scrub tick per class; hard boundaries.
*V yes. T yes. Z yes — regenerate; density is the tone. F yes — the classes are
sourced (Kayan) and already on the sheet.*

**8. A dark, summary foreground threshold across the bottom edge.**
Cheapest depth cue in the tradition.
*V yes. T yes. Z yes. F — flag it: this is a compositional device, not evidence.
It is legitimate only if the foreground band coincides with real near ground and
carries no waypoint. If it would require inventing near terrain, drop it.*

**Not recommended:** cloud-shadow banding across the plain. It is how Koninck and
the Dutch panoramists get their ribbons, it is beautiful, and it would work — but
it asserts a specific sky on a specific afternoon and would sit badly beside a
plate whose note is scrupulous about what it does and does not know. The
ground-cover bands give us the same rhythm from data. Recorded here so the option
is on file rather than rediscovered.

---

## 5. Rights summary

Public domain by US rules (pre-1931): items 2, 3, 4, 5, 6, 7. Declared public
domain by the holding agency but worth one verification before any reproduction:
item 1 (Berann/NPS). In copyright, **study only, reproduce nothing**: item 8
(Imhof 1982/2007), and modern panorama work generally — James Niehues and the
current ski-map illustrators are all rights-held.

Nothing in this lane was downloaded, embedded or traced. Two open-access PDFs
were read for their text (Patterson 2005; Kimerling 2000) and are cited, not
reproduced.
