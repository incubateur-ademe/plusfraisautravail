import { CallOut } from '@codegouvfr/react-dsfr/CallOut';
import { Button } from '@codegouvfr/react-dsfr/Button';
import { useNavigate } from 'react-router-dom';
import { QUESTIONS, THEMES } from '../data/questions';
import { useFormContext } from '../context/FormContext';
import { CONTENU } from '../data/contenu';

export function WelcomePage() {
  const navigate = useNavigate();
  const { answers, isComplete } = useFormContext();
  const firstQuestion = QUESTIONS[0];

  const firstUnansweredQuestion = QUESTIONS.find((q) => answers[q.id] === undefined);
  const resumeRoute = firstUnansweredQuestion
    ? `/${firstUnansweredQuestion.id}`
    : `/${firstQuestion.id}`;

  const hasStarted = Object.keys(answers).length > 0;
  const c = CONTENU.welcome;

  return (
    <div className="fr-container autodiag-welcome">
      <div className="fr-grid-row">
        <div className="fr-col-12">
          <h1>{c.title}</h1>
          <p className="fr-text--lead">{c.lead}</p>

          <CallOut title={c.callout_title} iconId="fr-icon-information-line">
            <p dangerouslySetInnerHTML={{ __html: c.callout_body }} />
            <p style={{ marginBottom: 0 }} dangerouslySetInnerHTML={{ __html: c.callout_duration }} />
          </CallOut>

          <div className="autodiag-welcome-themes">
            {THEMES.map((theme) => (
              <div key={theme.id} className="autodiag-theme-pill">
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
                  {c.button_resume}
                </Button>
                <Button
                  onClick={() => navigate(`/${firstQuestion.id}`)}
                  priority="secondary"
                  size="large"
                >
                  {c.button_restart}
                </Button>
              </>
            ) : (
              <Button
                onClick={() => navigate(`/${firstQuestion.id}`)}
                iconId="fr-icon-arrow-right-line"
                iconPosition="right"
                size="large"
              >
                {c.button_start}
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
                {c.button_results}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
