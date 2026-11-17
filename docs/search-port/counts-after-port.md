# Search counts before and after the port

Old: the old page on main `05d0cd885` (`counts-base-2026-11-16.json`, from `search-counts.mjs`), which counted
"instances". New: the ported page on `claude/search-port` (`search-counts-new.mjs`, 16 Nov, 21:15), which counts
scenes and hits. The old page searched Murray only; the new one searches all four translations unless a
translation is chosen (`t=murray`), and its English defaults to "any form" (`ef=0` is exact form).

| Search | Old | New | Why it moved |
|---|---|---|---|
| μῆνις | 22 instances | 22 scenes · 22 hits | Same hits. |
| θάλασσα | 119 | 94 scenes · 119 hits | Same hits; now also counted in scenes. |
| θαλάσσης, exact form | 87 | 72 scenes · 87 hits | Same hits. |
| οἴνοπα πόντον, exact phrase | 20 | 10 scenes · 10 hits | The old page counted each word of a phrase (2 per match); the new one counts a match once. |
| ἄναξ ἀνδρῶν, any word | 1,276 | 546 scenes · 1,276 hits | Same hits. |
| θεά, accents exactly | "134 before accent filtering" | 30 scenes · 33 hits | The old bar showed the count before accents were matched; the new one after. |
| sea | 398 (Murray) | 298 scenes (four translations, any form) | Wider search by default. Murray, exact form: **225 scenes · 398 hits**, the same hits. |
| rosy-fingered dawn, exact phrase | 0 | 26 scenes | The hyphen bug is fixed (the old page folded the query to "rosyfingered"). |
| rosy fingered dawn, exact phrase | 6 | 26 scenes | The old phrase check read only the head of each book's English; the new one reads it all, in four translations. |
| fingered | 27 (Murray) | 28 scenes (four translations) | Wider search by default. |
| θάλασσα + sea, and | 498 (both words anywhere in the same book) | 94 scenes · 119 hits (four translations); **92 scenes · 117 hits** (Murray, exact) | John's ruling: "and" means the same scene, not the same book. Hits are the Greek words only. |
| θάλασσα + sea, or | 517 | 298 scenes · 119 hits | Counted by scene; hits are the Greek words. |
| Ὀδυσσεύς, Od. 9 | 6 | 3 scenes · 6 hits | Same hits. |
| θεός spoken by Achilles | 34 | 23 scenes · 34 hits | Same hits. |
| θεός, speeches only | 543 | 291 scenes · 543 hits | Same hits (`spo=1`; the old link `so=1` gives the same). |
| every form of ἔπεα | 452 | 319 scenes · 452 hits | Same hits. |
| πούς near ὠκύς, 3 words | 82 | 38 scenes · 41 hits | The old page counted both words of each match (2 × 41); the new one counts a match once. |
| optatives, Il. 1 | "54 words, 19 of them certainly opt." | 18 scenes · 54 hits | Same words. |

Not in this table: multi-word "All words" now means every word in one scene (lane C2). ἄναξ ἀνδρῶν with all
words gave 517 scenes before that change (both words anywhere in one book) and 140 after; tested in
`search-page-homer.test.ts`.

The θάλασσα + sea "and" count is 92 scenes (Murray, exact), not the 86 the first rulings page showed: the port
places each English word in the scene whose reader page shows it; the first measurement used a rougher rule.
