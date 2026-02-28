import { CallOut } from '@codegouvfr/react-dsfr/CallOut';
import { Button } from '@codegouvfr/react-dsfr/Button';
import { useNavigate } from 'react-router-dom';
import { QUESTIONS } from '../data/questions';
import { useFormContext } from '../context/FormContext';

const THEMES = [
  { icon: '🌱', label: 'Sol' },
  { icon: '💧', label: 'Eaux pluviales' },
  { icon: '🌳', label: 'Espaces verts' },
  { icon: '🏢', label: 'Bâtiments' },
];

export function WelcomePage() {
  const navigate = useNavigate();
  const { answers, isComplete } = useFormContext();
  const firstQuestion = QUESTIONS[0];

  // Find first unanswered question to resume
  const firstUnansweredQuestion = QUESTIONS.find((q) => answers[q.id] === undefined);
  const resumeRoute = firstUnansweredQuestion
    ? `/${firstUnansweredQuestion.id}`
    : `/${firstQuestion.id}`;

  const hasStarted = Object.keys(answers).length > 0;

  return (
    <div className="fr-container autodiag-welcome">
      <div className="fr-grid-row">
        <div className="fr-col-12">
          <h1>Auto-diagnostic îlot de fraîcheur</h1>
          <p className="fr-text--lead">
            Évaluez la capacité d'adaptation de votre site de travail face aux vagues de chaleur.
            Cet outil vous permet d'identifier les axes d'amélioration prioritaires.
          </p>

          <CallOut
            title="Comment fonctionne cet outil ?"
            iconId="fr-icon-information-line"
          >
            <p>
              Ce diagnostic comprend <strong>5 questions</strong> réparties en <strong>4 thèmes</strong>.
              Pour chaque question, sélectionnez la réponse qui correspond le mieux à la situation
              actuelle de votre site. Vous obtiendrez ensuite un score par thème et des recommandations
              personnalisées.
            </p>
            <p style={{ marginBottom: 0 }}>
              Durée estimée : <strong>5 minutes</strong>.
            </p>
          </CallOut>

          <div className="autodiag-welcome-themes">
            {THEMES.map((theme) => (
              <div key={theme.label} className="autodiag-theme-pill">
                <span className="autodiag-theme-icon">{theme.icon}</span>
                <span>{theme.label}</span>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '2rem' }}>
            {hasStarted ? (
              <>
                <Button
                  onClick={() => navigate(resumeRoute)}
                  iconId="fr-icon-arrow-right-line"
                  iconPosition="right"
                  size="large"
                >
                  Reprendre le diagnostic
                </Button>
                <Button
                  onClick={() => navigate(`/${firstQuestion.id}`)}
                  priority="secondary"
                  size="large"
                >
                  Recommencer depuis le début
                </Button>
              </>
            ) : (
              <Button
                onClick={() => navigate(`/${firstQuestion.id}`)}
                iconId="fr-icon-arrow-right-line"
                iconPosition="right"
                size="large"
              >
                Commencer le diagnostic
              </Button>
            )}
          </div>

          {isComplete && (
            <div style={{ marginTop: '1rem' }}>
              <Button
                onClick={() => navigate('/resultats')}
                priority="tertiary"
                iconId="fr-icon-award-line"
                iconPosition="left"
              >
                Voir mes résultats
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
