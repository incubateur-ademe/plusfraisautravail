import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const buildTarget = process.env.BUILD_TARGET;
const isEmbed = buildTarget === 'embed' || buildTarget === 'embed-map';
const base = process.env.VITE_BASE_URL ?? '/alert-widget/';

const embedEntry =
  buildTarget === 'embed-map'
    ? { input: 'src/mount-map.tsx', name: 'alert-widget-map.js' }
    : { input: 'src/embed.tsx', name: 'alert-widget-embed.js' };

export default defineConfig(
  isEmbed
    ? {
        plugins: [react()],
        base,
        build: {
          outDir: 'dist',
          emptyOutDir: false,
          rollupOptions: {
            // Single IIFE per invocation. BUILD_TARGET=embed produces the
            // bootstrap; BUILD_TARGET=embed-map produces the on-demand map
            // bundle that the bootstrap injects when data-route="/map".
            input: embedEntry.input,
            output: {
              format: 'iife',
              inlineDynamicImports: true,
              entryFileNames: embedEntry.name,
            },
          },
        },
      }
    : {
        plugins: [react()],
        base,
        server: {
          proxy: {
            '/api': {
              target:
                process.env.VITE_API_PROXY_TARGET ??
                'https://apiprodedce25f6-api-prod.functions.fnc.fr-par.scw.cloud',
              changeOrigin: true,
              rewrite: (path) => path.replace(/^\/api/, ''),
            },
          },
        },
      },
);
