import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const isEmbed = process.env.BUILD_TARGET === 'embed';

export default defineConfig(
  isEmbed
    ? {
        plugins: [react()],
        base: process.env.VITE_BASE_URL ?? '/climadiag/',
        build: {
          outDir: 'dist',
          emptyOutDir: false,
          // Inline every asset (the Météo France PNG logo included) so the
          // embed ships as a single file with no co-located assets/ folder.
          assetsInlineLimit: Number.MAX_SAFE_INTEGER,
          rollupOptions: {
            input: 'src/embed.tsx',
            output: {
              format: 'iife',
              inlineDynamicImports: true,
              entryFileNames: 'climadiag-embed.js',
            },
          },
        },
      }
    : {
        plugins: [react()],
        base: process.env.VITE_BASE_URL ?? '/climadiag/',
        server: {
          proxy: {
            '/api': {
              target: process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:8000',
              changeOrigin: true,
              rewrite: (path) => path.replace(/^\/api/, ''),
            },
          },
        },
      },
);
