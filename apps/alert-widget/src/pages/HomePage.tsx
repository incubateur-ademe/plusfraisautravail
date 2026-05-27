import type { ApiClient } from '@pfat/api-client';

import { AlertWidget } from '../AlertWidget';

export interface HomePageProps {
  apiBaseUrl: string;
  client?: ApiClient;
  scenarioBadge?: string;
}

export function HomePage({ apiBaseUrl, client, scenarioBadge }: HomePageProps) {
  return (
    <>
      <h1>Alerte canicule</h1>
      <AlertWidget apiBaseUrl={apiBaseUrl} client={client} />
      {scenarioBadge && (
        <p className="fr-mt-3w fr-text--sm" style={{ color: '#666666' }}>
          {scenarioBadge}
        </p>
      )}
    </>
  );
}
