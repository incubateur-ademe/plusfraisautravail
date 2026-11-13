import { useEffect, useMemo, useRef, useState } from 'react';
import { Alert } from '@codegouvfr/react-dsfr/Alert';
import { ApiClient, type ClimadiagLieu } from '@pfat/api-client';
import { CommuneCombobox, type ComboboxOption } from './CommuneCombobox';
import { ClimadiagIndicateurs } from './climadiag/Climadiag';
import './climadiag/climadiag.css';

const SEARCH_DEBOUNCE_MS = 300;
// PlusFraîcheMaVille rejects queries shorter than 3 characters (our API relays that as a 502).
const MIN_SEARCH_LENGTH = 3;

export interface ClimadiagWidgetProps {
  apiBaseUrl: string;
  client?: ApiClient;
}

export const ClimadiagWidget = ({ apiBaseUrl, client: clientProp }: ClimadiagWidgetProps) => {
  const client = useMemo(
    () => clientProp ?? new ApiClient({ baseUrl: apiBaseUrl }),
    [clientProp, apiBaseUrl],
  );

  const [search, setSearch] = useState('');
  const [results, setResults] = useState<ClimadiagLieu[]>([]);
  const [selected, setSelected] = useState<ClimadiagLieu>();
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(false);
  const skipNextSearch = useRef(false);

  useEffect(() => {
    if (skipNextSearch.current) {
      skipNextSearch.current = false;
      return;
    }
    const query = search.trim();
    if (query.length < MIN_SEARCH_LENGTH) return;
    const timer = setTimeout(() => {
      client
        .searchClimadiag(query, { communesOnly: true })
        .then((lieux) => {
          setResults(lieux);
          setError(undefined);
        })
        .catch(() => setError('Impossible de récupérer les données Climadiag.'))
        .finally(() => setLoading(false));
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [client, search]);

  // Short queries show nothing, without clearing state from inside the effect.
  const isTooShort = search.trim().length < MIN_SEARCH_LENGTH;
  const visibleResults = isTooShort ? [] : results;
  const visibleError = isTooShort ? undefined : error;

  const options: ComboboxOption[] = visibleResults.map((r) => ({
    value: String(r.id),
    label: `${r.nom} - ${r.code_postal}`,
  }));

  return (
    <div className="cd-root">
      <CommuneCombobox
        label="Rechercher une commune"
        value={search}
        options={options}
        loading={loading}
        onInputChange={(value) => {
          setSearch(value);
          setSelected(undefined);
          // Set here, not in the effect: the debounced search below clears it.
          setLoading(value.trim().length >= MIN_SEARCH_LENGTH);
        }}
        onSelect={(option) => {
          const lieu = results.find((r) => String(r.id) === option.value);
          setSelected(lieu);
          skipNextSearch.current = true;
          setSearch(option.label);
        }}
      />
      {visibleError && (
        <Alert className="fr-mt-2w" severity="error" small description={visibleError} />
      )}
      {selected && <ClimadiagIndicateurs climadiagInfo={selected} />}
    </div>
  );
};
