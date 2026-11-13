import * as Sentry from '@sentry/react';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { startReactDsfr } from '@codegouvfr/react-dsfr/spa';
import App from './App';
import '@codegouvfr/react-dsfr/main.css';

// Errors, performance traces and logs (console warn/error). No DSN = disabled.
Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.consoleLoggingIntegration({ levels: ['warn', 'error'] }),
  ],
  tracesSampleRate: 0.1,
});

startReactDsfr({ defaultColorScheme: 'system' });

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
