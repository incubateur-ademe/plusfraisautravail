import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fr } from '@codegouvfr/react-dsfr';
import { Button } from '@codegouvfr/react-dsfr/Button';
import { RadarChartComponent } from '../components/RadarChartComponent';
import { RecommendationCard } from '../components/RecommendationCard';
import { useFormContext } from '../context/FormContext';
import { computeScores } from '../data/questions';
import { CONTENU } from '../data/contenu';

export function ResultsPage() {
  const navigate = useNavigate();
  const { answers, isComplete, resetAnswers } = useFormContext();
  const c = CONTENU.results;

  useEffect(() => {
    if (!isComplete) {
      navigate('/');
    }
  }, [isComplete, navigate]);

  if (!isComplete) return null;

  const scores = computeScores(answers);
  const sortedScores = [...scores].sort((a, b) => a.score - b.score);
  const globalAverage = scores.reduce((sum, s) => sum + s.score, 0) / scores.length;

  function handleRestart() {
    resetAnswers();
    navigate('/');
  }

  return (
    <div className={`${fr.cx('fr-container', 'fr-py-4w')} autodiag-results`}>
      <div className={fr.cx('fr-grid-row')}>
        <div className={fr.cx('fr-col-12')}>
          <h1>{c.title}</h1>
          <p className={fr.cx('fr-text--lead')}>{c.lead}</p>

          <p className={fr.cx('fr-display--xs', 'fr-my-3w')} style={{ textAlign: 'center' }}>
            <span className={fr.cx('fr-sr-only')}>{c.score_global_label} : </span>
            {Math.round(globalAverage * 10) / 10}/{c.score_max}
          </p>

          <h2 className={fr.cx('fr-h3')}>{c.section_overview}</h2>
          <p className={fr.cx('fr-sr-only')}>
            {c.radar_sr_prefix}{' '}
            {scores.map((s) => `${s.themeLabel} : ${Math.round(s.score * 10) / 10}/${c.score_max}`).join(', ')}.
          </p>
          <RadarChartComponent scores={scores} />

          <h2 className={fr.cx('fr-h3')}>{c.section_recommendations}</h2>
          <p>{c.recommendations_lead}</p>

          <div className={fr.cx('fr-mt-3w')} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {sortedScores.map((score, index) => (
              <RecommendationCard key={score.themeId} score={score} rank={index + 1} />
            ))}
          </div>

          <div className={fr.cx('fr-mt-4w')} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <Button
              onClick={handleRestart}
              priority="secondary"
              iconId="fr-icon-refresh-line"
              iconPosition="left"
            >
              {c.button_restart}
            </Button>
            <Button
              linkProps={{
                href: c.all_solutions_url,
                target: '_blank',
                rel: 'noopener noreferrer',
              }}
              iconId="fr-icon-external-link-line"
              iconPosition="right"
            >
              {c.button_all_solutions}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
