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
  site: 'https://johnhboyer-sys.github.io', // project-pages launch (John, 2026-07-18 late: Homer is a SUBPAGE, /homer-reader/, not the user-site root)
  base: '/homer-reader/',
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