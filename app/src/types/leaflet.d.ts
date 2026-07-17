// Leaflet ships no bundled TypeScript types, and @types/leaflet is out of
// scope (CLAUDE.md pre-authorizes only the `leaflet` runtime package itself —
// "plain Leaflet only", no further new dependencies). This ambient module
// declaration silences "cannot find module 'leaflet'" for the plain-JS
// import; call sites treat the default export's surface as untyped. The
// actual Leaflet API contract is exercised by the Playwright verification
// pass on the built site, not by the type checker (this repo's `npm run
// build` does not run `astro check`/`tsc`, so this is a dev-ergonomics aid,
// not a build gate).
declare module 'leaflet';
