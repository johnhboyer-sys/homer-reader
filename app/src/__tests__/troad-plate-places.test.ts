// Regression test for the 2026-07-28 Troad/Trojan-plain label pile-up: the
// Troad tab (regional, `troad`-tagged places, the `troad.json` plate) and the
// Trojan Plain tab (plain scale, `troad-plain`-tagged places, the
// `trojan-plain.json` plate) must draw genuinely different, scale-appropriate
// place sets -- see MapsPage.svelte's troadRegionalPlatePlaces /
// troadPlainPlatePlaces. This locks in the editorial call made in
// apparatus/places.json's `maps` arrays so a future edit can't silently pile
// plain-scale furniture back onto the regional sheet.
//
// Real apparatus/places.json, read the same way app/src/pages/maps/index.astro
// reads it -- process.cwd() is this package's own dir (app/) under `npx
// vitest run` here (see CLAUDE.md's shared/ vitest import.meta.url gotcha,
// 2026-07-27, for why this is fs + process.cwd() rather than a relative
// import.meta.url resolution).
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { placesForMap, type Place } from '@shared/lib/maps';

interface PlacesFile {
  status: string;
  places: Place[];
}

const placesRaw: PlacesFile = JSON.parse(
  readFileSync(path.resolve(process.cwd(), '../apparatus/places.json'), 'utf-8'),
);
const places = placesRaw.places;

const troad = placesForMap(places, 'troad');
const troadPlain = placesForMap(places, 'troad-plain');
const troadIds = new Set(troad.map((p) => p.id));
const troadPlainIds = new Set(troadPlain.map((p) => p.id));

describe('Troad vs Trojan Plain place sets (apparatus/places.json maps tags)', () => {
  it('does not tag Troy-citadel/plain furniture onto the regional Troad sheet', () => {
    // These read only at plain (or citadel) scale -- Homeric furniture right
    // at Hisarlık, or the later-Greek headlands/tumuli named in the
    // Trojan-plain plate's own note. On the regional `troad` sheet they
    // would all collapse onto the same few pixels around Troy -- the
    // original pile-up.
    const plainOnlyIds = [
      'pergamos',
      'wall-of-troy',
      'troy-lower-city',
      'scaean-gate',
      'dardanian-gates',
      'great-tower-of-ilios',
      'oak-of-zeus',
      'callicolone',
      'simoeis',
      'batieia',
      'thymbra',
      'thymbrios',
      'washing-troughs',
      'bay-of-troy',
      'sigeion',
      'rhoiteion',
      'kum-tepe',
      'kesik-tepe',
      'besik-sivritepe',
      'tomb-of-ajax-in-tepe',
      'uvecik-tepe',
      'besik-bay',
      'kesik-basin',
    ];
    for (const id of plainOnlyIds) {
      expect(troadIds.has(id), `${id} should not carry the regional 'troad' tag`).toBe(false);
    }
  });

  it('keeps the bay-closing promontories and plain tumuli on the Trojan Plain sheet (not stripped)', () => {
    // The brief this test guards: naively switching the plain tab to
    // 'troad-plain' without re-tagging would have dropped these five off
    // the plain sheet entirely. They must resolve on troad-plain.
    const mustBeOnPlain = ['sigeion', 'rhoiteion', 'kum-tepe', 'kesik-tepe', 'besik-sivritepe'];
    for (const id of mustBeOnPlain) {
      expect(troadPlainIds.has(id), `${id} must carry 'troad-plain'`).toBe(true);
    }
  });

  it('limits places carried at both scales to the deliberate short list', () => {
    // Troy and Scamander genuinely read at both the regional and plain
    // scale, and already carry the `sources` field the pipeline validator
    // requires of any place tagged for a plate. Ida and the Hellespont read
    // at both scales too (John, 2026-07-28 calibration) but fall outside the
    // Trojan-plain plate's small frame anyway (so tagging them troad-plain
    // would add nothing but an off-canvas honesty-list entry) and lack
    // `sources` -- adding that field is out of this fix's declared scope
    // (maps arrays only), so they stay troad-only. Any place appearing in
    // both sets beyond this list is either a clutter regression on the
    // regional sheet or an oversight -- this is a closed list, not a floor.
    const allowedBoth = new Set(['troy', 'scamander']);
    const both = [...troadIds].filter((id) => troadPlainIds.has(id)).sort();
    expect(both).toEqual([...allowedBoth].sort());
  });

  it('keeps the regional theatre (islands, Hellespont towns, sacked towns, Idaean rivers) on the Troad sheet', () => {
    const regionalTheatre = [
      'ida',
      'lekton',
      'tenedos',
      'imbros',
      'samothrace',
      'lemnos',
      'lesbos',
      'hellespont',
      'abydos',
      'sestos',
      'percote',
      'arisbe',
      'zeleia',
      'aisepos',
      'granikos',
      'adramyttion',
      'thebe-hypoplacia',
      'lyrnessus',
      'chryse',
      'cilla',
    ];
    for (const id of regionalTheatre) {
      expect(troadIds.has(id), `${id} should keep the regional 'troad' tag`).toBe(true);
    }
  });
});
