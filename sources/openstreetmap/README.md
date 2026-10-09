# sources/openstreetmap/ — river courses for the two Troad plates

**Provenance:** OpenStreetMap `waterway` ways, fetched from the Overpass API
on 2026-07-28 for the two plate bboxes.

```
https://overpass-api.de/api/interpreter
  way["waterway"~"^(river|stream)$"](<bbox>); out geom;
```

Four Homeric rivers are drawn from it: the **Scamander** (Karamenderes),
the **Simoeis** (Dümrek Su, OSM's "Dombrik Sou"), the **Granicus** (Biga
Çayı), the **Aesepus** (Gönen Çayı) and the **Satnioeis** (Tuzla Çayı).

## ⚠ Licence — ODbL 1.0, and it obliges us

OpenStreetMap data is licensed under the **Open Database License 1.0**
(https://opendatacommons.org/licenses/odbl/1-0/). Two obligations follow, and
neither is optional:

1. **Attribution.** "© OpenStreetMap contributors", reasonably prominent,
   wherever the data or a work produced from it is used. A rendered map is a
   *Produced Work* under ODbL §4.3 and needs only this notice.

2. **Share-alike on derivative databases (§4.4, §4.6).** A file containing
   OSM-derived geometry is a *Derivative Database*, and publicly using one
   obliges us to offer that database under ODbL. That covers:
   * `trojan-plain-rivers.json` and `troad-rivers.json` in this directory;
   * the `path` of the river layers inside
     `apparatus/plates/trojan-plain.json` and `apparatus/plates/troad.json`,
     and their copies under `build/dist/plates/`.

   It does **not** reach the site's code, its text, the gazetteer, or the
   Copernicus-derived coastlines — ODbL infects the database, not everything
   shipped alongside it.

**This is a decision for John, not for an agent.** The site is otherwise free
of copyleft obligations, and the Copernicus coastline in
`sources/copernicus-dem/` was chosen precisely to avoid one. Two ways out if
the obligation is unwanted:

* **Accept it.** Add "© OpenStreetMap contributors, ODbL 1.0" to
  `app/src/pages/attribution.astro` and state in this README that the two
  river files and the plates' river layers are offered under ODbL. This is
  what nearly every map on the web does.
* **Drop the rivers.** The plates would lose the Scamander, Simoeis,
  Granicus, Aesepus and Satnioeis. There is no public-domain substitute:
  Natural Earth 1:10m has **no watercourse at all** inside the Troad sheet
  (checked), and the Copernicus water mask classes the Karamenderes as river
  for only a few hundred pixels of its lowest reach — both measured, not
  assumed. AWMC's ODbL data was checked too: its `inland-water-OSM` layer is
  lake and swamp polygons, 419 vertices in the whole Troad sheet, and carries
  no named river here.

Until that call is made, the geometry is vendored, cited and flagged rather
than quietly shipped.

**US copyright status:** in the US, facts are not copyrightable (*Feist*) and
there is no sui generis database right, so the ODbL's force here is
contractual rather than copyright-based. That is a reason to comply with it
cleanly, not a reason to ignore it — this project's posture is to honour a
source's terms, and the attribution costs nothing.

## Derivation

Produced by `scripts/prep-troad-basemap.py`, which:

1. Queries Overpass for named `waterway=river|stream` ways in the sheet's
   bbox (for the Trojan plain, unnamed ways as well — see below).
2. Selects the ways whose `name` tag, folded for diacritics, matches the
   river wanted (`karamenderes`, `dombrik`, `biga cayi`, …).
3. Chains ways on coincident endpoints into one continuous course. OSM splits
   a river into dozens of ways at every bridge and boundary. On the Trojan
   plain the chain is also allowed to run through **unnamed** ways, because
   OSM's name tagging on the Dümrek Su stops after 7 km and without them the
   Simoeis is a stub floating mid-sheet; at a junction a named way always
   wins, so an unnamed tributary can never become the river. The chain kept
   is the one carrying the most vertices from named, matching ways.
4. Clips to the sheet and generalises with Douglas–Peucker at about half a
   pixel of the plate's render size.

## Files

| File | Courses | Vertices |
|---|---|---|
| `trojan-plain-rivers.json` | Scamander 170, Simoeis 91 | 261 |
| `troad-rivers.json` | Scamander 156, Granicus 140, Aesepus 85, Satnioeis 118 | 499 |

The layers they replace held 15 and 22 hand-typed vertices respectively.

Output shape is the same envelope as `sources/copernicus-dem/`, in this
project's `[lat, lon]` order.

**What the data does not give us, and is therefore not drawn:** the Bronze Age
channel of either river (both have shifted, and the delta has prograded), and
Homer's confluence of Scamander and Simoeis (*Il.* 5.774). The Simoeis stops
about a kilometre short of the Karamenderes because that is where the survey
stops, not where the river does; the layer note says so.
