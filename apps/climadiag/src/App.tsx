import { useEffect, useRef, useState } from 'react';
import { Alert } from '@codegouvfr/react-dsfr/Alert';
import { ApiClient, type ClimadiagLieu } from '@pfat/api-client';
import { CommuneCombobox, type ComboboxOption } from './CommuneCombobox';
import { ClimadiagIndicateurs } from './climadiag/Climadiag';
import './climadiag/climadiag.css';

const SEARCH_DEBOUNCE_MS = 300;
const MIN_SEARCH_LENGTH = 2;

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api';
const client = new ApiClient({ baseUrl: apiBaseUrl });

export default function App() {
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
    if (query.length < MIN_SEARCH_LENGTH) {
      setResults([]);
      setError(undefined);
      return;
    }
    setLoading(true);
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
  }, [search]);

  const options: ComboboxOption[] = results.map((r) => ({
    value: String(r.id),
    label: `${r.nom} - ${r.code_postal}`,
  }));

  return (
    <main className="fr-container fr-py-4w">
      <h1>Climadiag commune</h1>
      <div className="cd-root">
        <CommuneCombobox
          label="Rechercher une commune"
          value={search}
          options={options}
          loading={loading}
          onInputChange={(value) => {
            setSearch(value);
            setSelected(undefined);
          }}
          onSelect={(option) => {
            const lieu = results.find((r) => String(r.id) === option.value);
            setSelected(lieu);
            skipNextSearch.current = true;
            setSearch(option.label);
          }}
        />
        {error && <Alert className="fr-mt-2w" severity="error" small description={error} />}
        {selected && <ClimadiagIndicateurs climadiagInfo={selected} />}
      </div>
    </main>
  );
}
