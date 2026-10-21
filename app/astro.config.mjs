// @ts-check
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';

import sitemap from '@astrojs/sitemap';

export default defineConfig({
  // GitHub Pages one-off build served at the domain root (no Cloudflare/R2 on
  // this project — John, 2026-07-17). `base` prefixes every app path; app
  // code reads import.meta.env.BASE_URL so it works at any base. `site` is
  // the canonical origin — set only so @astrojs/sitemap can emit absolute
  // URLs (site + base + path). App UI still uses base-relative URLs, not
  // Astro.site, so this changes no existing links.
  // Custom domain (John, 2026-10-21): GitHub Pages serves the site at the
  // root of homer.johnhboyer.com; app/public/CNAME holds the domain so every
  // deploy keeps it. The old github.io/homer-reader/ URLs redirect here.
  site: 'https://homer.johnhboyer.com',
  base: '/',
  // Astro 7 changed the default to 'jsx', which strips whitespace between
  // inline elements on separate lines — it ran words together on every page
  // ("Back to the corpusSearch"). `true` keeps the Astro 6 behaviour.
  compressHTML: true,
  integrations: [
    svelte(),
    sitemap(),
  ],
  vite: {
    server: {
      fs: { allow: ['..'] },
    },
    resolve: {
      // The reader core (components, libs, global.css) lives in ../shared and
      // is consumed by both this site and the desktop app. See shared/README.md.
      alias: {
        '@shared': fileURLToPath(new URL('../shared', import.meta.url)),
      },
    },
  },
});