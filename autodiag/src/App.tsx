import { Header } from '@codegouvfr/react-dsfr/Header';
import { Footer } from '@codegouvfr/react-dsfr/Footer';
import { Route, Routes } from 'react-router-dom';
import { WelcomePage } from './pages/WelcomePage';
import { QuestionPage } from './pages/QuestionPage';
import { ResultsPage } from './pages/ResultsPage';
import { WagtailProvider } from './context/WagtailContext';

export default function App() {
  return (
    <WagtailProvider>
      <Header
        brandTop={<>ADEME</>}
        homeLinkProps={{
          href: '/autodiag/',
          title: 'Accueil — Plus frais au travail',
        }}
        serviceTitle="Plus frais au travail"
        serviceTagline="Auto-diagnostic îlot de fraîcheur"
        quickAccessItems={[
          {
            text: 'Retour au site',
            linkProps: {
              href: 'https://plusfraisautravail.beta.gouv.fr/',
              target: '_blank',
              rel: 'noopener noreferrer',
            },
            iconId: 'fr-icon-external-link-line',
          },
        ]}
      />

      <main role="main" id="main-content" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<WelcomePage />} />
          <Route path="/resultats" element={<ResultsPage />} />
          <Route path="/:questionId" element={<QuestionPage />} />
        </Routes>
      </main>

      <Footer
        accessibility="non compliant"
        accessibilityLinkProps={{
          href: '/autodiag/accessibilite',
        }}
        contentDescription="Outil d'auto-diagnostic développé dans le cadre du programme Plus frais au travail, porté par l'ADEME."
        domains={['beta.gouv.fr']}
        license={
          <>
            Sauf mention contraire, tous les contenus de ce site sont sous{' '}
            <a
              href="https://github.com/etalab/licence-ouverte/blob/master/LO.md"
              target="_blank"
              rel="noopener noreferrer"
            >
              licence etalab-2.0
            </a>
          </>
        }
      />
    </WagtailProvider>
  );
}
