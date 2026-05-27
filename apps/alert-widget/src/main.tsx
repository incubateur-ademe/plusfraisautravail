import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import { startReactDsfr } from '@codegouvfr/react-dsfr/spa';

import '@codegouvfr/react-dsfr/main.css';

import { HomePage } from './pages/HomePage';
import { MapPage } from './pages/MapPage';
import { buildFakeClient, detectScenario } from './demo';

startReactDsfr({ defaultColorScheme: 'system', Link });

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api';
const scenario = detectScenario(window.location.search);
const fakeClient = scenario ? buildFakeClient(scenario) : undefined;
const scenarioBadge = scenario
  ? `Mode démo — données fictives (?test=${scenario}).`
  : undefined;
const basename = import.meta.env.BASE_URL.replace(/\/$/, '') || undefined;

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter basename={basename}>
      <Routes>
        <Route
          path="/"
          element={
            <>
              <nav className="fr-container fr-mt-4w" aria-label="Navigation">
                <ul className="fr-tags-group">
                  <li>
                    <Link className="fr-tag" to="/">
                      Alerte
                    </Link>
                  </li>
                  <li>
                    <Link className="fr-tag" to="/map">
                      Carte
                    </Link>
                  </li>
                </ul>
              </nav>
              <main className="fr-container fr-py-4w">
                <HomePage
                  apiBaseUrl={apiBaseUrl}
                  client={fakeClient}
                  scenarioBadge={scenarioBadge}
                />
              </main>
            </>
          }
        />
        <Route
          path="/map"
          element={
            <MapPage apiBaseUrl={apiBaseUrl} client={fakeClient} phenomena="canicule" />
          }
        />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
