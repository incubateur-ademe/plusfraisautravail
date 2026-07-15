import { useState } from 'react';
import { Select } from '@codegouvfr/react-dsfr/SelectNext';
import { Alert } from '@codegouvfr/react-dsfr/Alert';
import { ClimadiagIndicateurs } from './climadiag/Climadiag';
import { sampleClimadiag } from './sample-data';

export default function App() {
  const [selected, setSelected] = useState(sampleClimadiag[0]);

  return (
    <main className="fr-container fr-py-4w">
      <h1>Climadiag commune</h1>
      <Select
        label="Commune"
        options={sampleClimadiag.map((c) => ({
          value: String(c.id),
          label: `${c.nom} - ${c.code_postal}`,
        }))}
        nativeSelectProps={{
          value: String(selected.id),
          onChange: (e) => setSelected(sampleClimadiag.find((c) => c.id === +e.target.value)!),
        }}
      />
      <Alert
        className="fr-mb-2w"
        severity="warning"
        small
        description="Données d’exemple — en attente d’accès à l’API Climadiag."
      />
      <ClimadiagIndicateurs climadiagInfo={selected} />
    </main>
  );
}
