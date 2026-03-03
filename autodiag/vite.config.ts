import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import yaml from '@rollup/plugin-yaml'

const isEmbed = process.env.BUILD_TARGET === 'embed';
const base = process.env.VITE_BASE_URL ?? '/autodiag/';

// https://vite.dev/config/
export default defineConfig(isEmbed
  ? // ── Embed build: single self-contained IIFE ──────────────────────────
    {
      plugins: [react(), yaml()],
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
      plugins: [react(), yaml()],
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
