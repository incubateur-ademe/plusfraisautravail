import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { startReactDsfr } from '@codegouvfr/react-dsfr/spa';

import { AlertWidget } from './AlertWidget';

startReactDsfr({ defaultColorScheme: 'system' });

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <main className="fr-container fr-py-4w">
      <h1>Alerte canicule</h1>
      <AlertWidget apiBaseUrl={apiBaseUrl} />
    </main>
  </StrictMode>,
);
