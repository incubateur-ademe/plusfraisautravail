import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { startReactDsfr } from '@codegouvfr/react-dsfr/spa';
import App from './App';
import '@codegouvfr/react-dsfr/main.css';

startReactDsfr({ defaultColorScheme: 'system' });

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
