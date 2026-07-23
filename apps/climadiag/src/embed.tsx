import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { startReactDsfr } from '@codegouvfr/react-dsfr/spa';

import { ClimadiagWidget } from './ClimadiagWidget';

const DSFR_CDN_URL = 'https://unpkg.com/@gouvfr/dsfr@1.14.2/dist/dsfr/dsfr.min.css';
const AUTO_CONTAINER_ID = 'pfat-climadiag';

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
}

declare global {
  interface Window {
    PfatClimadiag?: {
      mount: (options: MountOptions) => void;
      autoMount: (options: Omit<MountOptions, 'target'>) => void;
    };
  }
}

let dsfrStarted = false;

function resolveTarget(target: MountOptions['target']): HTMLElement {
  if (target === undefined) {
    // document.currentScript is only valid during the synchronous initial
    // execution of *this* script - it's already null by the time autoMount()
    // runs (deferred to DOMContentLoaded, or just async React/module work).
    // Fall back to appending at the end of body, which visually orphans the
    // widget below the footer - callers should prefer passing an explicit
    // target or placeholder element instead of relying on this fallback.
    const existing = document.getElementById(AUTO_CONTAINER_ID);
    if (existing) return existing;
    const container = document.createElement('div');
    container.id = AUTO_CONTAINER_ID;
    document.body.appendChild(container);
    return container;
  }
  const el = typeof target === 'string' ? document.querySelector(target) : target;
  if (!el) {
    throw new Error(`PfatClimadiag: target "${String(target)}" not found`);
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
      <ClimadiagWidget apiBaseUrl={options.apiBaseUrl} />
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

window.PfatClimadiag = { mount, autoMount };

// Bootstrap from the script tag itself when it carries data-* attributes,
// so consumers can drop a single <script> tag without an inline setup block.
const currentScript = document.currentScript as HTMLScriptElement | null;
if (currentScript?.dataset.auto !== undefined) {
  const apiBaseUrl = currentScript.dataset.apiBaseUrl;
  if (!apiBaseUrl) {
    throw new Error('PfatClimadiag: data-api-base-url is required when using data-auto');
  }
  // Capture the mount position synchronously - document.currentScript is
  // only valid right now, not once mount() actually runs (deferred to
  // DOMContentLoaded, or just async React/module work).
  let target: HTMLElement | undefined;
  if (currentScript.parentNode) {
    const placeholder = document.createElement('div');
    placeholder.id = AUTO_CONTAINER_ID;
    currentScript.parentNode.insertBefore(placeholder, currentScript);
    target = placeholder;
  }
  const mountWhenReady = () => mount({ apiBaseUrl, target });
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountWhenReady, { once: true });
  } else {
    mountWhenReady();
  }
}
