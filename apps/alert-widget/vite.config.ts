import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const isEmbed = process.env.BUILD_TARGET === 'embed';
const base = process.env.VITE_BASE_URL ?? '/alert-widget/';

export default defineConfig(
  isEmbed
    ? {
        plugins: [react()],
        base,
        build: {
          outDir: 'dist',
          emptyOutDir: false,
          rollupOptions: {
            input: 'src/embed.tsx',
            output: {
              format: 'iife',
              inlineDynamicImports: true,
              entryFileNames: 'alert-widget-embed.js',
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
