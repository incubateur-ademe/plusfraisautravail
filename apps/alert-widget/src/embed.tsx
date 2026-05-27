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

interface MountMapOptions {
  target?: string | HTMLElement;
  apiBaseUrl: string;
  /** Comma-separated phenomenon IDs ("6"), or the keyword "canicule" / "all". */
  phenomena?: string;
  demo?: ScenarioName;
}

declare global {
  interface Window {
    PfatAlertWidget?: {
      mount: (options: MountOptions) => void;
      autoMount: (options: Omit<MountOptions, 'target'>) => void;
    };
    PfatVigilanceMap?: { mount: (options: MountMapOptions) => void };
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

function deriveMapBundleUrl(scriptEl: HTMLScriptElement): string {
  // Map bundle ships alongside the embed bundle. We swap the filename so the
  // host can serve both from the same CDN path.
  const src = scriptEl.src;
  return src.replace(/alert-widget-embed\.js(?:\?.*)?$/, 'alert-widget-map.js');
}

function loadMapBundle(scriptEl: HTMLScriptElement): Promise<void> {
  if (window.PfatVigilanceMap) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = deriveMapBundleUrl(scriptEl);
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error(`Failed to load ${s.src}`));
    document.head.appendChild(s);
  });
}

async function autoMountMap(
  scriptEl: HTMLScriptElement,
  options: MountMapOptions,
): Promise<void> {
  await loadMapBundle(scriptEl);
  if (!window.PfatVigilanceMap) {
    throw new Error('PfatVigilanceMap bundle loaded but did not expose its API');
  }
  window.PfatVigilanceMap.mount(options);
}

// Bootstrap from the script tag itself when it carries data-* attributes,
// so consumers can drop a single <script> tag without an inline setup block.
const currentScript = document.currentScript as HTMLScriptElement | null;
if (currentScript?.dataset.auto !== undefined) {
  const apiBaseUrl = currentScript.dataset.apiBaseUrl;
  if (!apiBaseUrl) {
    throw new Error('PfatAlertWidget: data-api-base-url is required when using data-auto');
  }

  const route = currentScript.dataset.route ?? '/';
  if (route === '/map') {
    // Capture mount target synchronously while `document.currentScript` is
    // still valid: if the author didn't supply data-target, insert a
    // placeholder right next to the <script> tag so the map renders in place
    // (the map bundle loads async, by which point currentScript is gone).
    let target: string | HTMLElement | undefined = currentScript.dataset.target;
    if (target === undefined && currentScript.parentNode) {
      const placeholder = document.createElement('div');
      placeholder.className = 'pfat-vigilance-map-host';
      currentScript.parentNode.insertBefore(placeholder, currentScript);
      target = placeholder;
    }
    const mountWhenReady = () =>
      autoMountMap(currentScript, {
        target,
        apiBaseUrl,
        phenomena: currentScript.dataset.phenomena,
        demo: parseDemoAttr(currentScript.dataset.demo),
      }).catch((err: unknown) => {
        // eslint-disable-next-line no-console
        console.error('PfatVigilanceMap: failed to mount', err);
      });
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', mountWhenReady, { once: true });
    } else {
      mountWhenReady();
    }
  } else {
    autoMount({
      apiBaseUrl,
      preventionUrl: currentScript.dataset.preventionUrl,
      leversUrl: currentScript.dataset.leversUrl,
      demo: parseDemoAttr(currentScript.dataset.demo),
    });
  }
}
