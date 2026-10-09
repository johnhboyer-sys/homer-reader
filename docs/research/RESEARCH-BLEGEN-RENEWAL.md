# RESEARCH-BLEGEN-RENEWAL — US renewal status of Blegen's *Troy* I–IV

Research lane, 2026-07-29. Answers RESEARCH-CITADEL.md §6 item 6. Consumed by: the
`troy-citadel` plate rebuild decision (whether Blegen's excavation plans are a
PD-clean geometry source alongside Dörpfeld 1902).

Per CLAUDE.md: a wrong PD claim is worse than no claim. Every verdict below states
the exact database, the exact query, and the exact result. **John makes the PD
call — this dossier only reports what the public record shows.**

---

## VERDICT (summary table)

| Vol | Title (short) | Pub. | Original reg. | Renewal window | Renewal found? | Term consequence |
|---|---|---|---|---|---|---|
| **I** | *General Introduction; the First and Second Settlements* | 1950 | A47363, 4 Sep 1950 | 1977–78 | **YES** — RE0000000116, 16 Jan 1978 | In copyright to 31 Dec 2045 |
| **II** | *The Third, Fourth and Fifth Settlements* | 1951 | A59983, 2 Oct 1951 | 1978–79 | **YES** — RE0000014031, 16 Jan 1979 | In copyright to 31 Dec 2046 |
| **III** | *The Sixth Settlement* (= **Troy VI, "Homer's Troy"**) | 1953 | A96182, 28 May 1953 | 1980–81 | **YES** — RE0000107295, 20 Nov 1981 | In copyright to 31 Dec 2048 |
| **IV** | *Settlements VIIa, VIIb and VIII* | 1958 | not located in this system | 1985–86 | **NO RENEWAL FOUND** after an extensive, multi-strategy search | Consistent with PD as of 1 Jan 1987 — **not proven** |

**The volume that matters most for the citadel plate — Vol. III, the Sixth
Settlement, Blegen's Troy VI — was renewed and is under US copyright through
2048.** It is not an available PD source. Only Vol. IV (the post-Homeric strata,
VIIa/VIIb/VIII) shows no renewal record, and VIIa is the layer some modern
scholars (not Blegen) associate with the Trojan War instead of VI — a different,
narrower relevance to this citadel plate than it might first appear.

---

## Method and the primary source actually used

The brief specified the Stanford Copyright Renewal Database and the Copyright
Office's `cocatalog.loc.gov` / `publicrecords.copyright.gov`. In practice:

- **Stanford's exhibit search (`exhibits.stanford.edu/copyrightrenewals`) is
  behind an Akamai bot challenge (`TSPD` token, `bobcmn`/`failureConfig` payload
  in the returned HTML) that blocked every fetch this lane made** — both the
  no-browser `WebFetch` tool and a plain `curl` with a standard desktop user
  agent got the same challenge page, never search results. Stanford's dataset
  is itself compiled from the same Catalog of Copyright Entries and Copyright
  Office records used below, so this is a corroboration gap, not a
  primary-evidence gap. See "Unverified" below.
  *verified how:* `curl -A "Mozilla/5.0 ..." "https://exhibits.stanford.edu/copyrightrenewals/catalog?q=Blegen+Troy&search_field=all_fields"` → 200 OK, body is the Akamai challenge page (`window["bobcmn"]`, `window["failureConfig"]`), no result markup.
- **`cocatalog.loc.gov` (the old LOC catalog UI) 301-redirects to
  `publicrecords.copyright.gov`**, the Copyright Office's current public search
  system. Its landing page is a client-rendered Angular app with no server-side
  content, so a plain fetch returns only the shell.
  *verified how:* `curl https://cocatalog.loc.gov/cgi-bin/Pwebrecon.cgi?...` → `301 Moved Permanently` to `https://publicrecords.copyright.gov/`.
- **The workaround: `publicrecords.copyright.gov`'s own backend API is
  unauthenticated and directly queryable over plain HTTPS**, and this became the
  primary source for this dossier. Its config
  (`https://publicrecords.copyright.gov/environments/env.js`) names
  `searchServiceUrl: 'https://api.publicrecords.copyright.gov/search_service_external'`;
  the compiled Angular bundle (`main.c95d1836ace1686a.js`) shows the simple-search
  call is `GET {searchServiceUrl}/simple_search_dsl?query=<terms>` (plus optional
  `size`, `registration_class`, etc. as query params, confirmed by trial — an
  unrecognized/missing `query` param returns
  `{"detail": "Missing query parameter 'query'"}`, which is how the parameter
  name was confirmed rather than guessed). This is the **live, current-production
  Copyright Office public record**, not a cached snapshot — it is the same data
  a person would see by typing into the search box at
  <https://publicrecords.copyright.gov/search>, just reached without executing
  the page's JavaScript.
  *authority:* this whole dossier's evidentiary basis for Vols II, III (renewed) and the negative search for Vol IV.
  *verified how:* every query URL below is a working, re-runnable GET request; result JSON saved and parsed in this lane.
- **The printed Catalog of Copyright Entries (pre-1978 series) was used as an
  independent cross-check for Vol. I**, since 1978 renewals sit right at the
  boundary the brief flagged. Internet Archive's OCR text of *Catalog of
  Copyright Entries, Fourth Series, Part 8: Renewals, Jan–June 1978* —
  <https://archive.org/details/catalogofcopyrig18libr> (full text:
  <https://archive.org/stream/catalogofcopyrig18libr/catalogofcopyrig18libr_djvu.txt>)
  — was downloaded and grepped for "Blegen" and "Troy". Project Gutenberg's OCR
  editions of the 1977 half-year renewal catalogs (
  <https://www.gutenberg.org/ebooks/11855> Jan–Jun 1977,
  <https://www.gutenberg.org/ebooks/11856> Jul–Dec 1977) were checked the same
  way and came up empty for Blegen/Troy — consistent with the renewal actually
  landing in Jan 1978, not 1977.
  *verified how:* `grep -in "blegen\|^troy"` on the downloaded plain-text files, in this lane.
- **HathiTrust's rights determination (method item 3) could not be checked.**
  Both `catalog.hathitrust.org` search and direct record pages 403'd every
  fetch this lane made (WebFetch and `curl` with a standard user agent alike),
  independent of query — this looks like categorical bot-blocking on that host,
  not a query problem. See "Unverified."

---

## 1. Volume I — RENEWED

**Citation (renewal).** U.S. Copyright Office, Public Records System, registration
`RE0000000116`, registration date **16 Jan 1978**. Title as indexed: "Troy. Vol. 1,
pt. 1 (text) & 2 (plates) By John L. Caskey, Marion Rawson & Jerome Sperling."
Renewal claimants: **John L. Caskey, Marion Rawson & Jerome Sperling (A)**
[= renewing as surviving Authors — Blegen died in 1971 and is not himself a
claimant on this filing, though he is listed as an author of the underlying
work elsewhere]. Renews the original registration **A00000047363, dated
4 Sep 1950** — i.e., Vol. I, *General Introduction; the First and Second
Settlements*.
*authority:* licence (renewal fact). *verified how:* two independent sources agree —

1. Live query: `GET https://api.publicrecords.copyright.gov/search_service_external/simple_search_dsl?query=Troy%20Caskey%20Sperling` → `hit_count: 1`, the record above (full JSON captured in this lane).
2. Printed record: Internet Archive OCR of *Catalog of Copyright Entries, Fourth Series Part 8, Renewals Jan–June 1978* (<https://archive.org/stream/catalogofcopyrig18libr/catalogofcopyrig18libr_djvu.txt>), (OCR line numbers vary between renders of the stream — Grok's re-download found the identical text near line 42219; locate by searching the quoted text, not by line): *"TROY. / Troy- Vol. 1, pt. 1 (text) & 2 (plates) By John L. Caskey, Marion Rawson & Jerome Sperling. © 4Sep50; A47363. John L. Caskey, Marion Rawson & Jerome Sperling (A); 16Jan78; RE 116."* Cross-referenced under the author index at the same volume: "Caskey, John L. / Troy. (RE 116.)", "Rawson, Marion. / Troy. (RE 116.)", "Sperling, Jerome. / Troy. (RE 116.)" (same caveat on line numbers; search the strings).

**Consequence.** RE 116 = registration `RE0000000116` — same renewal, printed source and live database agree exactly (number, date, title, claimants). **Vol. I is under US copyright.** Under the pre-1978 term as extended twice (1976 Act's 47-year renewal term, then the 1998 Sonny Bono Act's 67-year renewal term), total term is 95 years from publication: **protected through 31 December 2045.**

---

## 2. Volume II — RENEWED

**Citation (renewal).** `RE0000014031`, registration date **16 Jan 1979**. Title as
indexed: "Troy, the third, fourth and fifth settlements. Vol. 2, pt. 1: text,
pt. 2: plates. By Carl W. Blegen, John L. Caskey & Marion Rawson." Renewal
claimants: **John L. Caskey & Marion Rawson (A)**. Renews **A00000059983, dated
2 Oct 1951**.
*authority:* licence. *verified how:* `GET .../simple_search_dsl?query=Troy%20Blegen` (`hit_count: 4`) and the tighter `query=Troy%20Caskey%20Sperling`-style checks below; full record JSON captured.

**Corroborating recordation.** The same database separately records an
**assignment of copyright**, executed 2 Jan 1979 / 5 Jan 1979, recorded
16 Jan 1979 as `V1706P396`: "Marion Rawson & John L. Caskey" (party 1) to
**"Princeton University Press"** (party 2), referencing "A59983 (1951)" — i.e.,
Rawson and Caskey renewed the copyright and assigned it to Princeton University
Press the same week. This is independent, structurally different evidence
(a different record type, `recordation` not `registration`) landing on the exact
same date and title, which is strong internal corroboration that the renewal is
real and not a database artifact.
*verified how:* same query, same JSON response, second hit; control number `73367`.

**Consequence.** **In copyright, currently held (by assignment) by Princeton
University Press, protected through 31 December 2046.**

---

## 3. Volume III — RENEWED (the volume that covers Troy VI)

**Citation (renewal).** `RE0000107295`, registration date **20 Nov 1981**. Title
as indexed: "Troy, the sixth settlement. Vol. 3, pt. 1: text, pt. 2: plates. By
Carl W. Blegen, John L. Caskey & Marion Rawson." Renewal claimant: **John L.
Caskey (A)**. Renews **A00000096182, dated 28 May 1953**.
*authority:* licence. *verified how:* same `query=Troy%20Blegen` response, third hit; full JSON captured.

**Corroborating recordation.** Assignment of copyright, executed 14 Nov 1981,
recorded 20 Nov 1981 as `V1877P173`: "John L. Caskey" (party 1) to **"Princeton
University Press"** (party 2), referencing "A96182 (1953)". Same pattern as
Vol. II — renewal and assignment to the publisher within days of each other.
*verified how:* same query, fourth hit; control number `276847`.

**Consequence.** *The Sixth Settlement* is Dörpfeld's counterpart layer to
Troy VI — Blegen's own volume title for "the ruins of Homer's Troy." **This
volume is renewed, currently held by Princeton University Press, and protected
through 31 December 2048.** It is not a PD source. This is the direct answer to
the citadel-plate question: Blegen's Troy VI plans do not become available by
this route.

---

## 4. Volume IV — NO RENEWAL FOUND

**What was searched.** Vol. IV is *Troy: Settlements VIIa, VIIb and VIII*,
Volume IV, Parts 1 (text) & 2 (plates), by **Carl W. Blegen, Cedric G. Boulter,
John L. Caskey, and Marion Rawson** (Princeton University Press for the
University of Cincinnati, 1958) — confirmed from the contemporary reviews in
*The American Historical Review* 64.2 and *The Classical Review* (Cambridge
Core), not from this database.
*verified how (title/authorship):* WebSearch, <https://academic.oup.com/ahr/article/64/2/341/102878>; <https://www.cambridge.org/core/services/aop-cambridge-core/content/view/5974808A49E8A55FFBBD092A18BCE3EC/S0009840X00173500a.pdf/...>

**Searches run against the live Copyright Office database, all against the same
`simple_search_dsl` endpoint that correctly surfaced Vols. I–III above:**

| Query | Hit count | Result |
|---|---|---|
| [`query=Troy Boulter`](https://api.publicrecords.copyright.gov/search_service_external/simple_search_dsl?query=Troy%20Boulter) | 0 | nothing |
| [`query=Cedric Boulter`](https://api.publicrecords.copyright.gov/search_service_external/simple_search_dsl?query=Cedric%20Boulter) | 0 | nothing |
| [`query=Troy Blegen Boulter Caskey Rawson`](https://api.publicrecords.copyright.gov/search_service_external/simple_search_dsl?query=Troy%20Blegen%20Boulter%20Caskey%20Rawson) | 0 | nothing |
| [`query=Troy settlements VIIa VIIb VIII`](https://api.publicrecords.copyright.gov/search_service_external/simple_search_dsl?query=Troy%20settlements%20VIIa%20VIIb%20VIII) | 0 | nothing |
| [`query=Troy seventh settlement`](https://api.publicrecords.copyright.gov/search_service_external/simple_search_dsl?query=Troy%20seventh%20settlement) | 0 | nothing |
| [`query=Troy eighth settlement`](https://api.publicrecords.copyright.gov/search_service_external/simple_search_dsl?query=Troy%20eighth%20settlement) | 0 | nothing |
| [`query=Troy Cincinnati`](https://api.publicrecords.copyright.gov/search_service_external/simple_search_dsl?query=Troy%20Cincinnati&registration_class=RE) (RE class only) | 0 | nothing |
| [`query=Troy Princeton`](https://api.publicrecords.copyright.gov/search_service_external/simple_search_dsl?query=Troy%20Princeton&registration_class=RE) (RE class only) | 1 | a *different* Troy title (see below) |
| [`query=Troy pt. 1 text pt. 2 plates`](https://api.publicrecords.copyright.gov/search_service_external/simple_search_dsl?query=Troy%20pt.%201%20text%20pt.%202%20plates) — the exact title-template all three renewed volumes share | 5 | only Vols. I, II, III (3 registrations + their 2 assignments) — **no fourth entry** |
| [`query=Blegen`](https://api.publicrecords.copyright.gov/search_service_external/simple_search_dsl?query=Blegen&registration_class=RE&size=100) filtered to `registration_class=RE` | 14 | all 14 examined by hand: 2 are Vols. II/III, the other 12 are Theodore C. Blegen (historian, unrelated), Judith Blegen (soprano, unrelated) — **no Vol. IV, and Vol. I doesn't appear either because its renewal wasn't filed under the Blegen name** (consistent with §1) |

The `Troy Princeton` (RE-class) hit is a different, related work: `RE0000018432`,
registered 3 Jan 1979, "Troy, the human remains. Supplementary monograph 1. By
J. Lawrence Angel" — one of the Troy *Supplementary Monographs*, not one of the
four main excavation volumes. Noted for completeness; out of scope for this
question.

**Why this is meaningful and not just "didn't try hard enough."** The same
query family — author-surname combinations, and the literal title template
("Troy … pt. 1 (text) … pt. 2 (plates) … By …") — found Vols. I, II, and III on
the first or second attempt each, including a filing (Vol. I's) that omitted
Blegen's own name. Vol. IV shares two of its four authors (Caskey, Rawson) with
every renewed volume, and Vol. IV's renewal window (the 27th–28th years, 1985–86) falls
squarely inside the era this live database indexes without gap (it holds
Blegen's other renewed 1980s filings for Vols. II and III at full detail). No
combination of author name, title fragment, or publisher name surfaced a
matching `RE`-class record.

**Verdict: NO RENEWAL FOUND.** This is evidence for non-renewal, not proof.
Possible explanations other than "never renewed" that this lane could not rule
out: a renewal filed under a name string with an OCR/data-entry error in the
underlying card-catalog scan (the pre-1978 half of this database is drawn from
scanned catalog cards, per its own `system_of_origin: card_catalog` /
`system_of_origin: voyager` split, and card-catalog OCR is known to be
imperfect — see the "Beilage caption" caveat pattern in RESEARCH-CITADEL.md
§7 for a parallel failure mode in this same research lane); a renewal filed
by the **University of Cincinnati** or **Princeton University Press** as sole
claimant, with none of the four authors' names in the indexed text (a
`Troy Cincinnati` / `Troy Princeton` search targeting exactly that came up
empty for Vol. IV specifically, which weighs against this, but does not
eliminate it — a claimant name search restricted more tightly to
`registration_class=RE` combined with `Cincinnati` might miss a record if
"University of Cincinnati" isn't in a field this fuzzy search reaches).

**Consequence, if John accepts this as sufficient.** Publication 1958 + 28
unrenewed years → **public domain as of 1 January 1987**, on the standard
pre-1964 renewal rule. This would make Vol. IV's plates (Troy VIIa, VIIb, VIII —
strata later than Blegen's own Troy VI) usable outright. **Its practical value
to the current citadel-plate work is limited**, since that plate's subject is
Troy VI, which is Vol. III's territory and Vol. III is renewed.

---

## Overall assessment

- **Vols. I–III are renewed, confirmed by two independent sources for Vol. I
  and by the live Copyright Office system (with self-corroborating assignment
  records) for Vols. II and III.** These are not usable as a PD geometry
  source. In particular, **Vol. III — the Sixth Settlement, Blegen's Troy
  VI — remains under copyright until 2048**, which is the volume that would
  have mattered most to the citadel plate.
- **Vol. IV shows no renewal record after an extensive, multi-strategy search
  of the live, current Copyright Office public database** — the same database,
  same endpoint, same query family that correctly found the other three. Absence
  of a renewal record in the Copyright Office's own public system for a
  pre-1964 work is **strong evidence of non-renewal and probable public-domain
  status**, but it is not a certificate: card-catalog-era data entry error and
  atypical claimant naming are both live possibilities this lane could not
  close out, and the two databases the brief specifically asked for
  (**Stanford's Copyright Renewal Database and HathiTrust's rights
  determination**) could not be reached at all to cross-check, for reasons
  documented above (bot-blocking, not absence of data). **John makes the PD
  call, not this dossier** — and if he wants Vol. IV usable, the clean way to
  close the gap is a targeted records request to the Copyright Office (a
  renewal-search certificate) or a further attempt at the Stanford database
  from a real browser session.

---

## Unverified — do not claim publicly

- **Stanford Copyright Renewal Database — not queried.** Every attempt (WebFetch
  and `curl` with a standard browser user agent) hit an Akamai bot challenge
  page, not search results. <https://exhibits.stanford.edu/copyrightrenewals>
  itself loads fine as a static page; its *search* endpoint is what challenges.
  A real browser session would likely pass. Not attempted here (browser MCP
  tools were out of scope for this task).
- **HathiTrust rights determination ("pd"/"ic") for any of the four
  volumes — not obtained.** `catalog.hathitrust.org` returned HTTP 403 to every
  fetch in this lane, search and direct record page alike
  (attempted: <https://catalog.hathitrust.org/Record/000351340>, the Vol. I
  general-collection record found via WebSearch). Whatever access determination
  HathiTrust displays for these volumes is unknown to this dossier.
- **archive.org rights statements on any Blegen *Troy* scan — not checked.** No
  archive.org item for these volumes was located or examined; unclear whether
  one exists (Princeton/Cincinnati university press books of this era are not
  reliably digitized full-view on IA even where renewal-unencumbered).
  Search was not exhaustive.
- **Whether Vol. IV's renewal (if any) was filed under "University of
  Cincinnati" or "Princeton University Press" as sole claimant, with none of
  the four authors' names appearing in the indexed renewal text** — the closest
  check run (`Troy Cincinnati`, `Troy Princeton`, both `registration_class=RE`)
  came up empty for Vol. IV, but this does not positively rule out an
  indexing/OCR gap on that specific record the way the author-name searches
  argue against a same-pattern renewal existing.
- **The exact calendar-day renewal deadline convention** (whether a given
  volume's 28th year runs to the end of the year of publication + 28, or +27,
  or is governed by the exact anniversary date) was not independently derived
  from the statute in this lane — the windows in the table above are read off
  the *actual* renewal dates found for Vols. I–III (which is more reliable than
  deriving the rule abstractly), extrapolated by the same +28 pattern to Vol.
  IV's 1958 publication. This extrapolation, not statutory research, is the
  basis for "renewal window 1985–86" and "PD as of 1 Jan 1987" above.
- **Whether any *other* claimant name (an heir, an executor, a different co-author
  spelling) might surface a Vol. IV renewal under a query this lane didn't
  think to try.** The negative search here is thorough but not exhaustive by
  construction — a full page-by-page read of the printed 1985–86 Catalog of
  Copyright Entries renewal volumes (equivalent to what was done for Vol. I via
  the 1978 volume) was not performed, because those years are only available
  through the live database used above, not through the OCR'd printed series
  this lane could grep directly.
