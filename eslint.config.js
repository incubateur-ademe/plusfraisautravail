import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import creedengo from '@creedengo/eslint-plugin'
import { defineConfig, globalIgnores } from 'eslint/config'

// Shared lint config for every JS/TS workspace (apps/* and packages/*).
export default defineConfig([
  // ponytail: only apps/* and packages/* hold JS/TS; the rest is Python, infra or build output.
  globalIgnores(['*/', '!apps/', '!packages/', 'apps/cms/', '**/.venv/', '**/dist/', '**/.vite/','**/test-embed/']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
      // Éco-conception (Green Code Initiative), standard de l'incubateur ADEME.
      creedengo.configs.recommended,
    ],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
  },
  {
    files: ['**/*.{js,mjs}', '**/vite.config.ts', '**/playwright.config.ts', '**/e2e/**'],
    extends: [js.configs.recommended],
    languageOptions: {
      globals: globals.node,
    },
  },
])
