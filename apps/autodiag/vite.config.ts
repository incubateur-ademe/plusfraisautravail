import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import yaml from '@rollup/plugin-yaml'
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Plugin } from 'vite'

const isEmbed = process.env.BUILD_TARGET === 'embed';
const base = process.env.VITE_BASE_URL ?? '/autodiag/';

const __dirname = dirname(fileURLToPath(import.meta.url));

/**
 * Vite plugin to load .publicodes files as ESM modules.
 * Publicodes files are valid YAML; this plugin returns their content
 * as raw string exports so they can be parsed by js-yaml at runtime.
 */
function publicodesPlugin(): Plugin {
  return {
    name: 'publicodes',
    enforce: 'pre',

    resolveId(source, importer) {
      if (source.endsWith('.publicodes')) {
        // Resolve relative imports to absolute paths
        const absolute = resolve(dirname(importer ?? __dirname), source)
        return absolute
      }
      return null
    },

    load(id) {
      if (id.endsWith('.publicodes')) {
        const content = readFileSync(id, 'utf-8')
        return {
          code: `export default ${JSON.stringify(content)};`,
          map: null,
        }
      }
      return null
    },
  }
}

// https://vite.dev/config/
export default defineConfig(isEmbed
  ? // ── Embed build: single self-contained IIFE ──────────────────────────
    {
      plugins: [react(), yaml(), publicodesPlugin()],
      base,
      build: {
        outDir: 'dist',
        emptyOutDir: false, // Don't wipe the main build output
        rollupOptions: {
          input: 'src/embed.tsx',
          output: {
            format: 'iife',
            inlineDynamicImports: true,
            entryFileNames: 'autodiag-embed.js',
          },
        },
      },
    }
  : // ── Standard build: index.html SPA ───────────────────────────────────
    {
      plugins: [react(), yaml(), publicodesPlugin()],
      base,
      server: {
        proxy: {
          '/api': {
            target: 'https://plusfraisautravail.beta.gouv.fr',
            changeOrigin: true,
            secure: true,
          },
        },
      },
    }
);
