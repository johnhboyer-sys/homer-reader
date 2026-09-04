# Audit: plate label classes (Trojan Plain + Troad)

**Status:** findings only — no data or renderer changes.  
**Date:** 2026-08-10  
**Scope:** places tagged `troad-plain` (sheet `trojan-plain`) and/or `troad` (sheet `troad`) in `apparatus/places.json`.  
**MAP_TAG** (`scripts/render-plates.mjs:62–67`): `trojan-plain` ← `troad-plain`; `troad` ← `troad`.  
**Counts in gazetteer:** 47 places with `troad-plain`; 28 with `troad`; 2 on both (`scamander`, `troy`); **73 unique**.

**Certainty → marker (this audit):**

| certainty    | marker |
|--------------|--------|
| certain      | solid  |
| traditional  | open   |
| speculative  | ring   |
| mythical     | open   |

Mythical → open is an audit mapping choice (same visual family as traditional); the data do not define a separate mythical pin. Regions, water, and rivers take **marker = none** regardless of certainty.

**Print name** = short map form (head of catalogue name before first parenthesis/comma; leading “The” dropped), matching `mapLabelText` in `shared/lib/plate.ts:1478–1486`. Full catalogue names stay in tooltips/lists.

**Geographic vs schematic:** of 47 plain-tagged places, only **11** currently carry `coords`. The rest resolve only via `plateAnchors['trojan-plain-schematic']` (or not at all). They still need a label class for when the schematic sheet (or a future anchor) draws them. Column **note** flags `geo-coords` / `schematic-only` / `layer-geometry` / `unlocated`.

**Rank** applies only to `settlement` (1 = Troy; 2 = often met in the Iliad; 3 = minor). Rank is editorial hierarchy for type size, not a certainty claim.

---

## Part 1 — label-class table

### 1a. Trojan Plain (`troad-plain` → sheet `trojan-plain`) — 47 places

| place id | name as it should print | sheet(s) | LABEL CLASS | rank | marker | note |
|----------|-------------------------|----------|-------------|------|--------|------|
| achaean-assembly-place | Assembly and law-place | trojan-plain | feature | — | ring | schematic-only; camp interior |
| achaean-camp | Achaean camp | trojan-plain | region | — | none | schematic + layer `achaean-camp-zone`; areal, not a pin |
| achaean-wall-and-ditch | Achaean wall and ditch | trojan-plain | feature | — | ring | schematic-only; linear earthwork |
| batieia | Batieia | trojan-plain | feature | — | ring | schematic-only; barrow of Myrine |
| bay-of-troy | Bay of Troy | trojan-plain | water | — | none | layer `lagoon-bronze`; areal embayment; no coords |
| besik-bay | Beşik Bay | trojan-plain | water | — | none | areal; no coords; modern Turkish form in name |
| besik-sivritepe | Beşik-Sivritepe | trojan-plain | feature | — | open | geo-coords; claimed Achilles tumulus (cult, not BA burial) |
| callicolone | Callicolone | trojan-plain | feature | — | open | geo-coords; hill/rise, not a town |
| dardanian-gates | Dardanian Gates | trojan-plain | feature | — | ring | schematic-only; also `troy-citadel` |
| fig-tree | Fig tree | trojan-plain | feature | — | ring | schematic-only |
| ford-of-the-scamander | Ford of the Scamander | trojan-plain | feature | — | ring | schematic-only; point-on-river, not a pin class of its own beyond feature |
| funeral-games-ground | Ground of Patroclus's funeral games | trojan-plain | region | — | none | schematic-only; areal gathering ground |
| great-tower-of-ilios | Great tower of Ilios | trojan-plain | feature | — | ring | schematic-only; also citadel |
| hut-of-achilles | Hut of Achilles | trojan-plain | feature | — | ring | schematic-only; camp furniture |
| hut-of-agamemnon | Hut of Agamemnon | trojan-plain | feature | — | ring | schematic-only |
| hut-of-ajax | Huts of Ajax | trojan-plain | feature | — | ring | schematic-only |
| hut-of-nestor | Hut of Nestor | trojan-plain | feature | — | ring | schematic-only |
| hut-of-odysseus | Hut of Odysseus | trojan-plain | feature | — | ring | schematic-only |
| kesik-basin | Kesik cut | trojan-plain | feature | — | ring | linear/areal cut; no coords; contested reading |
| kesik-tepe | Kesik Tepe | trojan-plain | feature | — | open | geo-coords; Demetrius tumulus / claimed Achilles |
| kum-tepe | Kum Tepe | trojan-plain | settlement | 3 | open | geo-coords; höyük (settlement mound), not a heroic tumulus — see places note/tradition |
| lookout-skopie | Lookout | trojan-plain | feature | — | ring | schematic-only |
| oak-of-zeus | Oak | trojan-plain | feature | — | ring | schematic-only; also citadel |
| pyre-of-patroclus | Pyre of Patroclus | trojan-plain | feature | — | ring | schematic-only |
| rhoiteion | Rhoiteion | trojan-plain | settlement | 2 | solid | geo-coords; bay-closing headland city (later Greek) |
| scaean-gate | Scaean Gate | trojan-plain | feature | — | ring | schematic-only; also citadel |
| scamander | Scamander | trojan-plain, troad | river | — | none | **category error today:** has point coords + teardrop; must be path label only |
| scamander-simoeis-confluence | Confluence of Simoeis and Scamander | trojan-plain | feature | — | ring | schematic-only; junction, not a town |
| scamandrian-plain | Scamandrian plain | trojan-plain | region | — | none | letterspaced area; layer + gazetteer; no pin |
| sigeion | Sigeion | trojan-plain | settlement | 2 | solid | geo-coords; NW corner of plain (later Greek) |
| simoeis | Simoeis | trojan-plain | river | — | none | **category error today:** point coords + teardrop; path label only |
| thracian-camp | Camp of Rhesus | trojan-plain | region | — | none | schematic-only; areal bivouac |
| thymbra | Thymbra | trojan-plain | region | — | none | geo-coords exist but note: district/bearing, not a polis pin; prefer area or omit marker |
| thymbrios | Thymbrios | trojan-plain | river | — | none | no coords; path when channel drawn |
| tomb-of-achilles-and-patroclus | Tomb of Achilles and Patroclus | trojan-plain | feature | — | ring | schematic-only; poem barrow, not a modern mound ID |
| tomb-of-aesyetes | Tomb of Aesyetes | trojan-plain | feature | — | ring | schematic-only |
| tomb-of-ajax-in-tepe | Tomb of Ajax | trojan-plain | feature | — | open | no coords; anchor conceptually to Rhoiteion |
| tomb-of-hector | Tomb of Hector | trojan-plain | feature | — | ring | schematic-only |
| tomb-of-ilos | Tomb of Ilus | trojan-plain | feature | — | ring | schematic-only |
| trojan-camp | Trojan bivouac | trojan-plain | region | — | none | schematic-only |
| troy | Troy | trojan-plain, troad | settlement | 1 | solid | geo-coords Hisarlık; sole rank 1 |
| troy-lower-city | Lower city of Troy | trojan-plain | region | — | none | areal Korfmann circuit; no pin; also citadel tag |
| two-springs-of-scamander | Two springs of the Scamander | trojan-plain | feature | — | ring | schematic-only |
| uvecik-tepe | Üvecik Tepe | trojan-plain | feature | — | solid | geo-coords; **Roman** tumulus of Festus (c. 214 AD) — cut candidate on Homeric sheet |
| wagon-road | Wagon-road | trojan-plain | feature | — | ring | schematic-only; linear |
| wall-of-heracles | Wall of Heracles | trojan-plain | feature | — | open | mythical → open; schematic-only |
| washing-troughs | Washing-troughs | trojan-plain | feature | — | ring | schematic-only |

### 1b. Troad (`troad` → sheet `troad`) — 28 places

| place id | name as it should print | sheet(s) | LABEL CLASS | rank | marker | note |
|----------|-------------------------|----------|-------------|------|--------|------|
| abydos | Abydos | troad | settlement | 2 | solid | geo-coords; Hellespont narrows |
| adramyttion | Adramyttium | troad | settlement | 3 | solid | not Homeric; Strabo measuring-point — cut candidate |
| aisepos | Aesepus | troad | river | — | none | no point coords; path label on layer (SVG: `Aesepus river`) |
| arisbe | Arisbe | troad | settlement | 3 | open | geo-coords; catalogue/allied city |
| chryse | Chryse | troad | settlement | 2 | ring | geo-coords **suspect** (see Part 2.3); poem-opening town |
| cilla | Cilla | troad | settlement | 3 | ring | unlocated; no coords |
| dardania | Dardania | troad | region | — | none | territory name; **today pinned as settlement** — reclass; or John: city Dardanos as settlement-3 |
| gargaron | Gargaron | troad | feature | — | open | peak of Ida; no separate summit coords in gaz |
| granikos | Granicus | troad | river | — | none | path label (SVG: `Granicus river`); id `granikos` vs Latin name |
| hellespont | Hellespont | troad | water | — | none | **category error today:** point coords + teardrop in the strait |
| ida | Mount Ida | troad | feature | — | none | mountain massif; **today teardrop pin** — area/peak treatment, no settlement pin |
| imbros | Imbros | troad | region | — | none | island landmass; letterspaced; drop teardrop |
| lekton | Cape Lekton | troad | feature | — | solid | cape/headland marker (small), not town pin |
| lemnos | Lemnos | troad | region | — | none | island; plate note: mostly west of neatline |
| lesbos | Lesbos | troad | region | — | none | large island; representative point today → pin (wrong class) |
| lyrnessus | Lyrnessus | troad | settlement | 3 | ring | geo-coords = BAtlas representative, not a surveyed site |
| pedasus-troad | Pedasus | troad | settlement | 3 | ring | unlocated; no coords; anchor is Satnioeis |
| percote | Percote | troad | settlement | 3 | open | geo-coords; Hellespont/allied |
| rhesos-heptaporos-karesos | Rhesus / Heptaporus / Caresus | troad | river | — | none | three unlocated Idaean streams; do not invent points; optional small italic list off-map |
| rhodios | Rhodius | troad | river | — | none | unlocated; no coords |
| samothrace | Thracian Samos | troad | region | — | none | island; dual English name — pick one system |
| satnioeis | Satnioeis | troad | river | — | none | path label (SVG: `Satnioeis river`) |
| scamander | Scamander | troad, trojan-plain | river | — | none | same category error as plain: point pin at mouth area |
| sestos | Sestos | troad | settlement | 2 | solid | European shore opposite Abydos |
| tenedos | Tenedos | troad | settlement | 2 | solid | small island-city; rank 2 per brief example; alt: region if letterspaced island style preferred — **John** |
| thebe-hypoplacia | Thebe | troad | settlement | 2 | open | Andromache’s city; no coords in gaz |
| troy | Troy | troad, trojan-plain | settlement | 1 | solid | sole rank 1 on both sheets |
| zeleia | Zeleia | troad | settlement | 3 | open | geo-coords east of plate neatline lon 27.5 — off-canvas risk |

### Class distribution (by sheet membership)

| class | trojan-plain (47) | troad (28) |
|-------|-------------------|------------|
| region | 7 | 5 |
| water | 2 | 1 |
| river | 3 | 6 |
| settlement | 4 (r1:1, r2:2, r3:1) | 13 (r1:1, r2:5, r3:7) |
| feature | 31 | 3 |

*Dual-tagged `troy` and `scamander` appear in both section tables (one row per sheet membership). Tenedos = settlement-2; large islands = region; Dardania = region. Huts/gates/tombs/camp furniture = feature or region as tabled.*

---

## Part 2 — defect list

### 2.1 Category errors (point treatment of linear/areal features)

**Mechanism (renderer):** `renderPlate` pins **every** place that resolves to on-canvas coords with `role: 'settlement'` (`shared/lib/plate.ts:3648–3656`). Layer path labels for a `placeId` are emitted only when that id is **not** already pinned (`:3669–3676`). So a river that still carries a representative point gets a teardrop and **loses** its channel label; rivers without coords (Aesepus, Granicus, Satnioeis) correctly path-label.

| id | evidence | correct class |
|----|----------|---------------|
| **scamander** | `"coords": [39.93, 26.24]` + maps `troad`, `troad-plain`; note: “principal river… Modern Karamenderes”. Pin on both sheets: `build/plate-shots/trojan-plain.svg` and `troad.svg` `data-place-id="scamander"`. Layer `river-scamander` / plain `scamander` exist with path geometry. | river — path only, no marker |
| **simoeis** | `"coords": [39.94, 26.25]`, maps `troad-plain`; note: “partner river… Dümrek Su”. Plain pin in SVG titles + crop. Layer `simoeis` is `kind: "river"`. | river |
| **hellespont** | `"coords": [40.15, 26.4]`; note: “modern Dardanelles”. Troad SVG pin mid-strait between Sestos and Abydos (`after-full-troad.png`). Pleiades 501434 is a strait, not a town (`RESEARCH-TROAD-TOPOGRAPHY.md` §3 table). | water — letterspaced in sea, no marker |
| **ida** | `"coords": [39.7, 26.9]`; massif “many-fountained Ida”. Troad pin on summit area. Relief layer `relief-ida` already carries `placeId: ida`. | feature (mountain) — area/peak type, no teardrop settlement pin |
| **aisepos / granikos / satnioeis** | No coords; path labels in `troad.svg` textPaths: `Aesepus river`, `Granicus river`, `Satnioeis river`. **Correct class** already; listed as contrast to Scamander. | river (keep) |
| **bay-of-troy** | No coords; note: marine embayment. Layer `lagoon-bronze` + region label `BAY OF TROY` in plain SVG. Not pinned — good. | water |
| **scamandrian-plain** | No coords; note: “the ground itself… a pin would put the plain at one point of itself”. Region caps in SVG. | region |
| **besik-bay** | No coords; areal bay. | water |
| **thymbra** | `"coords": [39.8997, 26.2933]` but note: “In the Iliad it is not a settlement at all but a bearing… a district”. Point will read as a town if pinned. | region (or omit pin) |
| **dardania** | Territory in the poem (“founded Dardania”); pinned as settlement on troad. | region (or rename pin to Dardanos — **John**) |
| **lesbos / imbros / lemnos / samothrace** | Island landmasses with representative points; all currently settlement pins on troad SVG. Lesbos note: “Coordinate is a representative point on the island, not a single settlement.” | region (letterspaced across island) |
| **wagon-road**, **achaean-wall-and-ditch**, **kesik-basin** | Linear/areal; schematic-only today — do not invent point pins on the geographic sheet. | feature / feature / feature |
| **rhodios**, **rhesos-heptaporos-karesos** | Rivers; no coords; unlocated — do not add representative points. | river |
| **lekton** | Cape (headland), not a town; currently settlement-style pin. | feature |

**Known triple from the brief (Wall of Troy / Troy / Pergamos):** see §2.2 — co-location + category (wall and citadel name are not separate settlements on the plain sheet).

### 2.2 Co-located names

#### A. Troy / Wall of Troy / Pergamos — identical coordinates

**Evidence (gazetteer, still true 2026-08-10):**

```json
// troy, wall-of-troy, pergamos — all three:
"coords": [39.957, 26.239]
```

- `troy` maps: `["troad","troad-plain","troy-citadel","wanderings","ships"]`
- `wall-of-troy` maps: `["troy-citadel"]` only
- `pergamos` maps: `["troy-citadel"]` only

**Evidence (renders of the plain sheet, Jul 2026):**  
`build/plate-shots/crop-trojan-plain-troy-light.png` and `after-full-plain.png` / `trojan-plain.svg` still letter **Wall of Troy**, **Troy**, and **Pergamos** on one pin cluster. SVG pin ids: `troy`, `pergamos`, `wall-of-troy`.

**Interpretation:** maps tags were later tightened (wall/pergamos citadel-only — see `troad-plate-places.test.ts:42–45` still listing them as plain-scale furniture that must not land on regional `troad`). The **coordinate collision remains** for any sheet that loads all three (citadel; and any stale plain bundle).

**Recommendation:**

| name | plain geographic | plain schematic | citadel |
|------|------------------|-----------------|---------|
| **Troy** | sole settlement label (rank 1) | same | optional short “Troy” or omit if plan is self-evident |
| **Pergamos** | **drop** | only if summit is drawn as its own region | region label on summit geometry, **no** second pin |
| **Wall of Troy** | **drop** | omit (wall is linework) | label via wall circuit layers only (`drawnByLayer`), never a pin |

Do not print three names at one lat/lon on any sheet.

#### B. Hellespont narrows cluster (troad)

Places with coords within ~2–6 km:

| id | coords | distance notes |
|----|--------|----------------|
| hellespont | [40.15, 26.4] | mid-strait pin |
| dardania | [40.14, 26.42] | ~2.0 km from hellespont pin |
| abydos | [40.19, 26.41] | ~4.5 km from hellespont pin |
| sestos | [40.2, 26.4] | ~5.6 km from hellespont pin |
| arisbe | [40.1943, 26.5358] | east along coast; labels still fight at scale |

**Evidence:** `after-full-troad.png` — Sestos / Abydos / Hellespont / Dardania stacked at the crossing.

**Recommendation:** print **Abydos** + **Sestos** (settlement-2); set **Hellespont** as water lettering in the strait (no pin); **Dardania** as region caps or drop at this scale; **Arisbe** / **Percote** only if label budget allows (else cut to catalogue inset).

#### C. Scamander pin vs Simoeis pin vs Troy (plain)

| pair | approx separation |
|------|-------------------|
| scamander [39.93, 26.24] ↔ simoeis [39.94, 26.25] | ~1.4 km |
| scamander ↔ troy [39.957, 26.239] | ~3.0 km |
| simoeis ↔ troy | ~2.1 km |

**Evidence:** plain crop — Troy cluster + Simoeis teardrop + Scamander teardrop south of the city.

**Recommendation:** no river pins; path labels along channels; Troy alone as settlement at Hisarlık.

#### D. Sigeion ridge cluster (plain)

| pair | approx separation |
|------|-------------------|
| sigeion [39.9835, 26.1809] ↔ kum-tepe [39.9936, 26.1926] | ~1.5 km |
| sigeion ↔ kesik-tepe [39.9608, 26.1682] | ~2.7 km |

**Recommendation:** print **Sigeion** (settlement-2); **Kum Tepe** only if zoom/panel; **Kesik Tepe** as one open feature if a single “claimed Achilles” mound is wanted — not both Kesik and Beşik-Sivritepe at full label size (see §2.5).

#### E. Achilles-tomb claimants (plain) — conceptual co-location of claim, not coords

Three separate mounds, one legendary identity:

- `kesik-tepe` — Demetrius tumulus, traditional Achilles  
- `besik-sivritepe` — Achilleion / Beşik, traditional Achilles  
- `tomb-of-achilles-and-patroclus` — poem’s barrow (schematic)

**Recommendation:** geographic sheet: at most **one** open-marker tumulus label, or none (put the dispute in a note/panel). Schematic: poem barrow only. **John** chooses which mound (if any) carries the name.

### 2.3 Coordinate suspects

Do **not** fix here. Evidence only.

| id | gaz coords | issue | evidence |
|----|------------|-------|----------|
| **chryse** | [39.55, 26.17] | ~65 km from Pleiades 550501 (near Thebe/Akçay 39.5851, 26.9281); ~8 km from rival Chrysa Göztepe 39.5213, 26.0829. Gaz **tradition** quotes Strabo 13.1.63 placing Homer’s Chryse **near Thebe**, not Hamaxitos — but coords sit on the **Hamaxitos/Göztepe** side of the Troad. | `places.json` chryse; `RESEARCH-TROAD-TOPOGRAPHY.md` §3 row chryse Δ **65.16** km; §4.7 Strabo quote |
| **zeleia** | [40.2036, 27.5961] | Matches Pleiades Sarıköy, but plate `troad` bbox east edge is **lon 27.5** (`apparatus/plates/troad.json` bbox). Point is ~8 km **east of the neatline** → off-canvas / edge clamp. | bbox `[38.95, 25.35, 40.6, 27.5]`; RESEARCH §3 zeleia |
| **scamander** point | [39.93, 26.24] | Not “wrong land,” but a **single point on a long river**; Pleiades river rep 39.8287, 26.4784 is **23.29 km** from gaz point (RESEARCH §3). Point is mid-plain near Troy, which forces the teardrop onto the battlefield. | RESEARCH Δ 23.29; plain/troad pins |
| **simoeis** point | [39.94, 26.25] | Pleiades 39.9681, 26.2434, Δ ~3.2 km — plausible channel area, still wrong **as a pin**. | RESEARCH §3 |
| **hellespont** point | [40.15, 26.4] | Pleiades 40.2188, 26.4769, Δ ~10 km; any point is inside water. | RESEARCH §3 |
| **ida** point | [39.7, 26.9] | vs Pleiades Kaz Dağ 39.6927, 26.8192, Δ ~7 km — OK as massif centroid, not as town pin. | RESEARCH §3 |
| **dardania** | [40.14, 26.42] | vs Pleiades Dardanos 40.0797, 26.3744, Δ ~7.8 km; name is territory, point is city-ish. | RESEARCH §3 |
| **lyrnessus** | [39.508, 27.082] | Gaz note: “Pleiades 550703… Barrington 1:500,000 representative point, not a surveyed site.” Speculative pin honesty is OK; do not promote to solid. | places.json lyrnessus note |
| **lemnos** | [39.92, 25.24] | Plate note: “Lemnos… lies mostly west of this sheet.” Expected off-canvas or edge. | `troad.json` plate note |
| **wall-of-troy / pergamos** | same as troy | Not geographic features with independent survey points — citadel synonyms / structure names. | coords identity §2.2 |
| **uvecik-tepe** | [39.9003, 26.1992] | Coordinate fine; **identity** wrong for a Homeric battlefield sheet (tomb of Festus, c. 214 AD). | places note: “not a heroic tomb at all… built c. 214 AD” |

Callicolone [39.9565, 26.3395] is **~8.55 km** east of Troy — consistent with Cook’s Kara Tepe ~8.5 km (tradition field). Not a coord defect; keep as feature-open.

### 2.4 Name-form inconsistency

**Script:** Current committed SVGs letter **Latin only** (no Greek codepoints in `build/plate-shots/troad.svg` / `trojan-plain.svg` text). River textPaths: `Granicus river`, `Aesepus river`, `Satnioeis river`. If an earlier build mixed Greek `greek` fields onto paths, it is not what these SVGs show. The live inconsistencies are **orthographic systems**, not Greek vs Latin script.

| issue | examples | evidence |
|-------|----------|----------|
| **Latinate -ium / -us vs Hellenizing -ion / -os / -eis** | Adramyttium (-ium) vs Rhoiteion, Sigeion, Lekton; Lyrnessus (-us) vs Abydos, Sestos, Tenedos, Simoeis, Satnioeis | places `name` fields |
| **id vs printed name** | id `granikos`, `aisepos` (k/transliteration) vs labels “Granicus”, “Aesepus” | ids + SVG textPaths |
| **“river” suffix on path labels only** | path: “Granicus river”; settlements: bare “Troy”, “Abydos” | `troad.svg` textPaths vs pin labels; comes from `mapLabelText("The Granicus river")` → “Granicus river” |
| **Parenthetical double names** | catalogue “Scamander (Xanthus)”, “Troy (Ilios)”, “Thracian Samos (Samothrace)” — map strips paren → Scamander, Troy, Thracian Samos | mapLabelText; dual tradition remains in data |
| **Ilios vs Ilium** | `great-tower-of-ilios` “Ilios”; Latin tradition Ilium | place names |
| **Modern Turkish with diacritics vs bare ancient** | Beşik Bay, Beşik-Sivritepe, Üvecik Tepe, İn Tepe vs Sigeion, Rhoiteion | plain sheet name fields |
| **English gloss in label head** | “Callicolone, 'Fair Hill'” → mapLabelText stops at comma → “Callicolone” (OK); “Cape Lekton” keeps Cape | mapLabelText |
| **Missing `greek` on several** | adramyttion, uvecik-tepe, besik-*, thymbrios, bay-of-troy, troy-lower-city | places.json |

**Recommended single system (editorial — for John):**

1. **Ancient places:** Latin-letter Hellenizing forms used in classical scholarship for Homer readers — **-os / -on / -eis / -ion** (Abydos, Sigeion, Rhoiteion, Simoeis, Satnioeis, Lyrnessos not Lyrnessus, Adramyttion not Adramyttium).  
2. **Rivers:** bare name on path — **Scamander**, **Aesepus**, **Granicus**, **Satnioeis** — no trailing “river”; italic water style does the work.  
3. **Modern survey names** (Beşik, Üvecik, Kesik, Kum Tepe): keep Turkish orthography when the label is the modern mound name; do not mix into ancient river/settlement set without a clear “modern” type.  
4. **Dual Homeric names:** print **Scamander** on the map; keep Xanthus in note/tooltip. Print **Troy**; keep Ilios in tooltip. Print **Samothrace** *or* **Thracian Samos** consistently (poem’s “Thracian Samos” is defensible).  
5. Do **not** put Greek script on the sheet unless the whole apparatus switches to bilingual labels.

### 2.5 Label-budget overflow

#### Trojan Plain (geographic) — size 880×779

| | count |
|---|------|
| Tagged places | 47 |
| With geo coords (potential pins today) | 11 |
| Schematic-only / no coords | 36 |
| Region/water that should letter without pins | ~4 (plain, bay, Beşik Bay, camps if drawn) |

**Verdict: over-labelled if every tagged place or every coord pin prints.** The failure mode in `after-full-plain.png` is not 47 names — it is **same-size bold haloed settlement treatment** on rivers + tumuli + Troy cluster. Hierarchy is missing more than raw count.

**Geographic plain — recommended print set (~12–14 labels):**

| keep | class |
|------|--------|
| Scamandrian plain | region |
| Bay of Troy | water |
| Beşik Bay | water (optional if clutter) |
| Scamander, Simoeis | river paths |
| Troy | settlement-1 |
| Sigeion, Rhoiteion | settlement-2 |
| Callicolone | feature |
| Thymbra | region light or cut |
| one tumulus max (or none) | feature-open |

**Cut from geographic plain (willing):**

| cut | why |
|-----|-----|
| **Üvecik Tepe** | Roman Festus tumulus (214 AD); not Homeric topography |
| **Kesik Tepe + Beşik-Sivritepe together** | two “Achilles” claimants; keep ≤1 or move to note |
| **Kum Tepe** | minor höyük at this scale; panel/zoom |
| **Wall of Troy, Pergamos** | synonym stack; citadel sheet only |
| **All huts, gates, oak, fig, lookout, ford, springs, washing-troughs, wagon-road, camps, pyre, games** | schematic register; poem furniture without survey coords |
| **Thymbrios** | only if channel is drawn; else omit |
| **troy-lower-city** | outline or omit; no name stack on Troy |

**Schematic plain:** higher budget for poem furniture, but still rank: region/camp first, then features; never all huts at full size.

#### Troad (regional) — size 840×839

| | count |
|---|------|
| Tagged places | 28 |
| Pins in current SVG | 17 |
| Path river labels | 3 (Granicus, Aesepus, Satnioeis) |

**Verdict: over-labelled at the Hellespont crossing and along the south coast; class errors inflate clutter.** A Landmark regional sheet at this scale wants roughly **14–18** names, not 20+ equal pins.

**Recommended print set (~15–17):**

| keep | class |
|------|--------|
| Hellespont | water |
| Scamander, Granicus, Aesepus, Satnioeis | river paths |
| Troy | settlement-1 |
| Abydos, Sestos, Tenedos | settlement-2 |
| Chryse (if coord fixed), Thebe | settlement-2 when located |
| Mount Ida, Cape Lekton, Gargaron (if distinct) | feature |
| Lesbos, Imbros, Thracian Samos / Samothrace | region |
| Lemnos | only if on-canvas fragment |

**Cut / demote:**

| cut | why |
|-----|-----|
| **Adramyttium** | not in Homer; measuring point only |
| **Hellespont pin** | water lettering replaces pin |
| **Scamander pin** | path replaces pin |
| **Mount Ida pin** | feature/area treatment |
| **Dardania pin** | region or drop at scale |
| **Percote + Arisbe both** | keep one or neither; catalogue detail |
| **Lyrnessus, Pedasus, Cilla, Zeleia** | minor/speculative/off-map; Zeleia off neatline |
| **Rhesus/Heptaporus/Caresus, Rhodius** | unlocated — legend note, not map pins |
| **Island teardrops** | letterspace island names; drop pins |

---

## Part 3 — recommendations

### Trojan Plain

| | |
|--|--|
| **How many labels should print (geographic)** | **~12–14** (not 47; not 11 equal pins) |
| **Classes that should dominate** | **region** (plain) + **water** (bay) + **river** (two channels) + **one** settlement-1 (Troy) + few settlement-2 headlands + sparse **feature** |
| **Three changes that most improve legibility** | **1.** Reclass rivers: strip coords-as-pins from Scamander/Simoeis; path labels only. **2.** One name at Hisarlık: Troy only; Wall/Pergamos off this sheet. **3.** Type hierarchy: letterspaced plain/bay; smaller open features for hills/tumuli; stop using one bold haloed settlement face for everything. |

### Troad

| | |
|--|--|
| **How many labels should print** | **~15–17** |
| **Classes that should dominate** | **water** (Hellespont) + **river** paths + **region** (large islands, Ida massif as area) + sparse **settlement** (Troy, narrows pair, Tenedos) + few **feature** (Lekton, peaks) |
| **Three changes that most improve legibility** | **1.** Hellespont as water type in the strait — delete the mid-channel teardrop that collides with Abydos/Sestos. **2.** Same river fix as plain for Scamander; keep Aesepus/Granicus/Satnioeis path style; drop “ river” suffix. **3.** Ruthless cut of non-Homeric and off-map minors (Adramyttium, Zeleia off-frame, unlocated triple rivers as pins) so rank-2 places can breathe. |

### Cross-cutting (both sheets)

1. **Add a label-class (and settlement rank) field to the gazetteer** — the renderer cannot invent hierarchy from certainty alone (every pin is already “settlement” in code).  
2. **Pins only for settlement (and small feature markers); never for river/water/region.**  
3. **Orthography pass** under one system (§2.4) before the next LOOK gate.  
4. **Chryse coordinates** are a data defect, not a styling one — fix or unlocate before promoting the label.  
5. **John decisions flagged:** mythical marker mapping (open); Tenedos settlement vs island-region; Dardania region vs Dardanos settlement; which Achilles mound (if any) prints; Samothrace vs Thracian Samos; whether Üvecik belongs on any Homeric plate.

---

## Appendix A — sheet tag confirmation

```62:67:scripts/render-plates.mjs
const MAP_TAG = {
  troad: 'troad',
  'trojan-plain': 'troad-plain',
  'trojan-plain-schematic': 'troad-plain',
  'troy-citadel': 'troy-citadel',
};
```

## Appendix B — plain places with coordinates (geographic pin candidates today)

```
troy              [39.957, 26.239]   certain
scamander         [39.93, 26.24]     certain   ← should not pin
simoeis           [39.94, 26.25]     traditional ← should not pin
callicolone       [39.9565, 26.3395] traditional
thymbra           [39.8997, 26.2933] traditional ← region, not town pin
kesik-tepe        [39.9608, 26.1682] traditional
besik-sivritepe   [39.9171, 26.1591] traditional
kum-tepe          [39.9936, 26.1926] traditional
uvecik-tepe       [39.9003, 26.1992] certain
sigeion           [39.9835, 26.1809] certain
rhoiteion         [40.01, 26.303]    certain
```

## Appendix C — visual failure modes inspected

- `build/plate-shots/after-full-plain.png` — teardrops on Scamander & Simoeis; Troy name stack; uniform type.  
- `build/plate-shots/crop-trojan-plain-troy-light.png` — Wall of Troy / Troy / Pergamos on one pin.  
- `build/plate-shots/after-full-troad.png` — Hellespont pin in water; Scamander pin; island pins; narrows pile-up; path labels on three rivers only.

---

*End of audit. No tracked files modified.*
