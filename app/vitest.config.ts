import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  // Resolve Svelte's browser (client) build so component mount() works under
  // happy-dom; without this Svelte 5 resolves its server build and throws
  // "mount(...) is not available on the server".
  resolve: {
    conditions: ['browser'],
    // Same @shared alias as astro.config.mjs's vite.resolve.alias -- needed
    // so a component test can import a component that reaches into
    // @shared/lib/* (e.g. PlatePanel.svelte), since vitest doesn't read
    // Astro's own config.
    alias: {
      '@shared': fileURLToPath(new URL('../shared', import.meta.url)),
    },
  },
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./src/__tests__/setup.ts'],
    include: ['src/**/*.{test,spec}.ts'],
    restoreMocks: true,
  },
});
