import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { startReactDsfr } from '@codegouvfr/react-dsfr/spa';
import type { ApiClient } from '@pfat/api-client';

import { AlertWidget } from './AlertWidget';
import { buildFakeClient, type ScenarioName } from './demo';

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
  /** Render canned fixtures instead of hitting the API. Useful for demos and screenshots. */
  demo?: ScenarioName;
}

declare global {
  interface Window {
    PfatAlertWidget?: {
      mount: (options: MountOptions) => void;
      autoMount: (options: Omit<MountOptions, 'target'>) => void;
    };
  }
}

const KNOWN_SCENARIOS = new Set<ScenarioName>([
  'heatwave',
  'heatwave-orange',
  'heatwave-rouge',
  'quiet',
]);

function isScenarioName(value: string): value is ScenarioName {
  return (KNOWN_SCENARIOS as Set<string>).has(value);
}

function parseDemoAttr(value: string | undefined): ScenarioName | undefined {
  if (value === undefined) return undefined;
  // `data-demo` with no value (empty string) → default to heatwave.
  if (value === '') return 'heatwave';
  if (isScenarioName(value)) return value;
  // eslint-disable-next-line no-console
  console.warn(
    `PfatAlertWidget: unknown demo scenario "${value}", falling back to "heatwave"`,
  );
  return 'heatwave';
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
  const client: ApiClient | undefined = options.demo ? buildFakeClient(options.demo) : undefined;
  createRoot(el).render(
    <StrictMode>
      <AlertWidget
        apiBaseUrl={options.apiBaseUrl}
        preventionUrl={options.preventionUrl}
        leversUrl={options.leversUrl}
        client={client}
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
    demo: parseDemoAttr(currentScript.dataset.demo),
  });
}
