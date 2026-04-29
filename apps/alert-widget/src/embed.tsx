import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { startReactDsfr } from '@codegouvfr/react-dsfr/spa';

import { AlertWidget } from './AlertWidget';

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
  if (!dsfrStarted) {
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
