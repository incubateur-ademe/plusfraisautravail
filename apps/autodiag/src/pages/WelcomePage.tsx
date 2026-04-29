import { fr } from '@codegouvfr/react-dsfr';
import { CallOut } from '@codegouvfr/react-dsfr/CallOut';
import { Button } from '@codegouvfr/react-dsfr/Button';
import { useNavigate } from 'react-router-dom';
import { QUESTIONS, THEMES } from '../data/questions';
import { useFormContext } from '../context/FormContext';
import { CONTENU } from '../data/contenu';

export function WelcomePage() {
  const navigate = useNavigate();
  const { answers, isComplete, resetAnswers } = useFormContext();
  const firstQuestion = QUESTIONS[0];

  const firstUnansweredQuestion = QUESTIONS.find((q) => answers[q.id] === undefined);
  const resumeRoute = firstUnansweredQuestion
    ? `/${firstUnansweredQuestion.id}`
    : `/${firstQuestion.id}`;

  const hasStarted = Object.keys(answers).length > 0;
  const c = CONTENU.welcome;

  return (
    <div className={`${fr.cx('fr-container', 'fr-py-4w')} autodiag-welcome`}>
      <div className={fr.cx('fr-grid-row')}>
        <div className={fr.cx('fr-col-12')}>
          <h1>{c.title}</h1>
          <p className={fr.cx('fr-text--lead')}>{c.lead}</p>

          <CallOut title={c.callout_title} iconId="fr-icon-information-line">
            <p dangerouslySetInnerHTML={{ __html: c.callout_body }} />
            <p className={fr.cx('fr-mb-0')} dangerouslySetInnerHTML={{ __html: c.callout_duration }} />
          </CallOut>

          <ul className={`${fr.cx('fr-tags-group', 'fr-mt-3w')} autodiag-welcome-themes`} aria-label="Thèmes abordés">
            {THEMES.map((theme) => (
              <li key={theme.id}>
                <p className={fr.cx('fr-tag')}>
                  <span aria-hidden="true">{theme.icon}</span>{' '}
                  {theme.label}
                </p>
              </li>
            ))}
          </ul>

          <div className={fr.cx('fr-mt-4w')} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
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
                  onClick={() => { resetAnswers(); navigate(`/${firstQuestion.id}`); }}
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
            <div className={fr.cx('fr-mt-2w')}>
              <Button
                onClick={() => navigate('/resultats')}
                priority="tertiary no outline"
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
