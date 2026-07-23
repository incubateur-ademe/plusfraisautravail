import { ClimadiagWidget } from './ClimadiagWidget';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api';

export default function App() {
  return (
    <main className="fr-container fr-py-4w">
      <h1>Climadiag commune</h1>
      <ClimadiagWidget apiBaseUrl={apiBaseUrl} />
    </main>
  );
}
