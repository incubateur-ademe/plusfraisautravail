import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { startReactDsfr } from '@codegouvfr/react-dsfr/spa';

import { AlertWidget } from './AlertWidget';

const DSFR_CDN_URL = 'https://unpkg.com/@gouvfr/dsfr@1.14.2/dist/dsfr/dsfr.min.css';
const AUTO_CONTAINER_ID = 'pfat-alert-widget';

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
  target?: string | HTMLElement;
  apiBaseUrl: string;
  preventionUrl?: string;
  leversUrl?: string;
}

declare global {
  interface Window {
    PfatAlertWidget?: {
      mount: (options: MountOptions) => void;
      autoMount: (options: Omit<MountOptions, 'target'>) => void;
    };
  }
}

let dsfrStarted = false;

function resolveAutoTarget(): HTMLElement {
  const existing = document.getElementById(AUTO_CONTAINER_ID);
  if (existing) return existing;

  const container = document.createElement('div');
  container.id = AUTO_CONTAINER_ID;

  // Insert right after the existing fr-notice that follows the page header,
  // so it stacks naturally beneath the "Site en construction" banner.
  const existingNotice = document.querySelector('header + .fr-notice, header ~ .fr-notice');
  if (existingNotice?.parentNode) {
    existingNotice.parentNode.insertBefore(container, existingNotice.nextSibling);
    return container;
  }

  // Fallback: right after the page header.
  const header = document.querySelector('header');
  if (header?.parentNode) {
    header.parentNode.insertBefore(container, header.nextSibling);
    return container;
  }

  // Last resort: prepend to body so it stays above the fold.
  document.body.insertBefore(container, document.body.firstChild);
  return container;
}

function resolveTarget(target: MountOptions['target']): HTMLElement {
  if (target === undefined) return resolveAutoTarget();

  const el = typeof target === 'string' ? document.querySelector(target) : target;
  if (!el) {
    throw new Error(`PfatAlertWidget: target "${String(target)}" not found`);
  }
  return el as HTMLElement;
}

function mount(options: MountOptions): void {
  ensureDsfrCss();
  if (!dsfrStarted && !document.documentElement.dataset.frScheme) {
    startReactDsfr({ defaultColorScheme: 'system' });
    dsfrStarted = true;
  }
  const el = resolveTarget(options.target);
  createRoot(el).render(
    <StrictMode>
      <AlertWidget
        apiBaseUrl={options.apiBaseUrl}
        preventionUrl={options.preventionUrl}
        leversUrl={options.leversUrl}
      />
    </StrictMode>,
  );
}

function autoMount(options: Omit<MountOptions, 'target'>): void {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => mount(options), { once: true });
    return;
  }
  mount(options);
}

window.PfatAlertWidget = { mount, autoMount };

// Bootstrap from the script tag itself when it carries data-* attributes,
// so consumers can drop a single <script> tag without an inline setup block.
const currentScript = document.currentScript as HTMLScriptElement | null;
if (currentScript?.dataset.auto !== undefined) {
  const apiBaseUrl = currentScript.dataset.apiBaseUrl;
  if (!apiBaseUrl) {
    throw new Error('PfatAlertWidget: data-api-base-url is required when using data-auto');
  }
  autoMount({
    apiBaseUrl,
    preventionUrl: currentScript.dataset.preventionUrl,
    leversUrl: currentScript.dataset.leversUrl,
  });
}
