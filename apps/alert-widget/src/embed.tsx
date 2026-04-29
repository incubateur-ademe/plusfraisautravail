import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { startReactDsfr } from '@codegouvfr/react-dsfr/spa';

import { AlertWidget } from './AlertWidget';

const DSFR_CDN_URL = 'https://unpkg.com/@gouvfr/dsfr@1.14.2/dist/dsfr/dsfr.min.css';

function ensureDsfrCss(): void {
  const alreadyPresent =
    document.querySelector('link[href*="/dsfr"]') ||
    getComputedStyle(document.documentElement)
      .getPropertyValue('--blue-france-sun-113-625')
      .trim() !== '';
  if (alreadyPresent) return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = DSFR_CDN_URL;
  document.head.appendChild(link);
}

interface MountOptions {
  target: string | HTMLElement;
  apiBaseUrl: string;
  preventionUrl?: string;
  leversUrl?: string;
  initialDepartment?: string;
}

declare global {
  interface Window {
    PfatAlertWidget?: { mount: (options: MountOptions) => void };
  }
}

let dsfrStarted = false;

function mount(options: MountOptions): void {
  ensureDsfrCss();
  if (!dsfrStarted && !document.documentElement.dataset.frScheme) {
    startReactDsfr({ defaultColorScheme: 'system' });
    dsfrStarted = true;
  }
  const el =
    typeof options.target === 'string' ? document.querySelector(options.target) : options.target;
  if (!el) {
    throw new Error(`PfatAlertWidget: target "${String(options.target)}" not found`);
  }
  createRoot(el as HTMLElement).render(
    <StrictMode>
      <AlertWidget
        apiBaseUrl={options.apiBaseUrl}
        preventionUrl={options.preventionUrl}
        leversUrl={options.leversUrl}
        initialDepartment={options.initialDepartment}
      />
    </StrictMode>,
  );
}

window.PfatAlertWidget = { mount };
