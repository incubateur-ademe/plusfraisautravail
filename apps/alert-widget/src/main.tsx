import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { startReactDsfr } from '@codegouvfr/react-dsfr/spa';

import '@codegouvfr/react-dsfr/main.css';

import { AlertWidget } from './AlertWidget';
import { buildFakeClient, detectScenario } from './demo';

startReactDsfr({ defaultColorScheme: 'system' });

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api';
const scenario = detectScenario(window.location.search);
const fakeClient = scenario ? buildFakeClient(scenario) : undefined;

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <main className="fr-container fr-py-4w">
      <h1>Alerte canicule</h1>
      <AlertWidget apiBaseUrl={apiBaseUrl} client={fakeClient} />
      {scenario && (
        <p className="fr-mt-3w fr-text--sm" style={{ color: '#666666' }}>
          Mode démo - données fictives (<code>?test={scenario}</code>).
        </p>
      )}
    </main>
  </StrictMode>,
);
