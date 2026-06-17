# design-sync notes — 1829 Ventures CRM UI

Repo-specific gotchas for syncing `frontend/src/components/ui` to claude.ai/design.

- **No library build.** `frontend`'s `build` script compiles the whole app (`tsc -b && vite build`), not a component library. The converter runs in **synth-entry mode** (no `dist`, no `.d.ts`) — entry is synthesized from `src/`. No `buildCmd`.
- **Discovery is scoped** via `srcDir: src/components/ui` so the converter only picks up the UI kit, not the entire app (pages, layout, etc.).
- **Tailwind DS — styles are NOT in a shipped stylesheet.** Component styles are Tailwind utility classes generated at app-build time. `src/index.css` only has `@tailwind` directives + the `:root` HSL token vars. So `cssEntry` points at `.ds-compiled.css`, a **statically compiled Tailwind stylesheet** produced by running the Tailwind CLI against `src/` before each build. Regenerate it on every re-sync (see command below). It is gitignored.
  - Regen: `cd frontend && npx tailwindcss -i src/index.css -o .ds-compiled.css --config tailwind.config.js --minify`
- **Tokens** are HSL CSS custom properties in `src/index.css` `:root` (`--primary`, `--background`, `--muted`, etc.), consumed by Tailwind via `hsl(var(--token))`. They are emitted into the compiled CSS's `:root`.
- **`@/` path alias** → `./src/*`, declared in `tsconfig.app.json` (`cfg.tsconfig`). esbuild needs it to resolve `@/lib/utils` and `@/components/ui/button` in synth-entry mode.
- **`buttonVariants`** is a CVA function exported from `button.tsx`, not a component — excluded via `componentSrcMap: {"buttonVariants": null}`.

## Build command (exact)
First sync / re-sync (run from repo root):
```
cd frontend && npx tailwindcss -i src/index.css -o .ds-compiled.css --config tailwind.config.js --minify && cd ..
node .ds-sync/package-build.mjs --config .design-sync/config.json --node-modules frontend/node_modules --entry ./frontend/__synth__.js --out ./ds-bundle
node .ds-sync/package-validate.mjs ./ds-bundle
```
`--entry ./frontend/__synth__.js` is a deliberately non-existent path: its only job is to make the converter's PKG_DIR walk-up land on `frontend/package.json` (named pkg). Because the file doesn't exist, the converter falls back to synth-from-src. No real dist is built.

## Verify loop learnings
- **ConfirmDialog (and any `fixed inset-0` overlay) clips in the card grid.** Each preview cell wrapper has `transform:translateZ(0)`, which re-anchors `position:fixed` to the (short) cell box instead of the viewport, so a centered modal's top (its title) gets clipped and `overflow:hidden` cuts it. Fix used: wrap the dialog in a flow-height spacer (`<div style={{height:360}}>`) so the cell grows tall enough to contain the centered modal. Also set `cfg.overrides.ConfirmDialog = {cardMode:"single", viewport:"520x480"}`.
- **`bg-accent` / `text-accent-foreground` are only emitted in `hover:` form** because the components only use them on hover. The base utilities are absent from the compiled CSS — expected, not a bug.

## Known render warns
- None outstanding. All 10 components are authored and graded good; no floor cards.

## Re-sync risks
- The compiled Tailwind CSS (`.ds-compiled.css`) is generated, not committed — re-sync MUST regenerate it or the bundle ships with stale/missing utilities.
- Tailwind only emits utilities it sees used in `content` (src). If a component starts using a new utility, regenerate before building.
- **The shipped `_ds_bundle.css` is a snapshot of only the utilities the components use — NOT a full Tailwind build.** Documented for the design agent in `conventions.md` (style custom layout via `hsl(var(--token))`, not arbitrary utility classes). If the kit grows and the agent needs more utilities, consider a `safelist` in `tailwind.config.js` before compiling.
- Synth-entry mode produces weak `.d.ts` (`[key:string]:unknown`); real prop contracts are hand-maintained in `cfg.dtsPropsFor`. Keep them in sync if a component's props change.
- `dtsPropsFor`, `overrides`, and `previews/` are committed and accumulate fixes — only add, never blindly replace.
