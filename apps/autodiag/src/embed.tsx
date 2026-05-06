import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { startReactDsfr } from '@codegouvfr/react-dsfr/spa';
import { Link } from 'react-router-dom';
import App from './App';
import { FormProvider } from './context/FormContext';
import './styles/index.css'; // Only custom CSS (~2KB), no DSFR

// Inject DSFR CSS only if not already present on the parent page
function ensureDsfrCss() {
  if (
    document.querySelector('link[href*="/dsfr"]') ||
    getComputedStyle(document.documentElement).getPropertyValue('--blue-france-sun-113-625').trim()
  ) {
    return; // DSFR already loaded
  }
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = 'https://unpkg.com/@gouvfr/dsfr@1.14.2/dist/dsfr/dsfr.min.css';
  document.head.appendChild(link);
}
ensureDsfrCss();

// Init DSFR JS only if not already initialized on the parent page
if (!document.documentElement.dataset.frScheme) {
  startReactDsfr({ defaultColorScheme: 'system', Link });
}

// Create mount point - insert after the current script tag, or append to body
const container = document.createElement('div');
container.id = 'autodiag-root';
const currentScript = document.currentScript;
if (currentScript?.parentNode) {
  currentScript.parentNode.insertBefore(container, currentScript.nextSibling);
} else {
  document.body.appendChild(container);
}

createRoot(container).render(
  <StrictMode>
    <MemoryRouter>
      <FormProvider>
        <App />
      </FormProvider>
    </MemoryRouter>
  </StrictMode>
);
