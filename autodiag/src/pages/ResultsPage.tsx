import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@codegouvfr/react-dsfr/Button';
import { RadarChartComponent } from '../components/RadarChartComponent';
import { RecommendationCard } from '../components/RecommendationCard';
import { useFormContext } from '../context/FormContext';
import { computeScores } from '../data/questions';

export function ResultsPage() {
  const navigate = useNavigate();
  const { answers, isComplete, resetAnswers } = useFormContext();

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
    <div className="fr-container autodiag-results">
      <div className="fr-grid-row">
        <div className="fr-col-12">
          <h1>Vos résultats</h1>
          <p className="fr-text--lead">
            Voici l'évaluation de la capacité de votre site à faire face aux vagues de chaleur,
            basée sur vos réponses.
          </p>

          <div className="autodiag-score-global">
            Score global : {Math.round(globalAverage * 10) / 10}/5
          </div>

          <h2 className="fr-h3">Vue d'ensemble</h2>
          <p className="fr-sr-only">
            Graphique en radar présentant vos scores par thème. Les scores sont :{' '}
            {scores.map((s) => `${s.themeLabel} : ${Math.round(s.score * 10) / 10}/5`).join(', ')}.
          </p>
          <RadarChartComponent scores={scores} />

          <h2 className="fr-h3">Recommandations prioritaires</h2>
          <p>
            Les thèmes sont classés du plus urgent au moins urgent. Commencez par les thèmes avec
            les scores les plus faibles.
          </p>

          <div className="autodiag-recommendations">
            {sortedScores.map((score, index) => (
              <RecommendationCard key={score.themeId} score={score} rank={index + 1} />
            ))}
          </div>

          <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem', flexWrap: 'wrap' }}>
            <Button
              onClick={handleRestart}
              priority="secondary"
              iconId="fr-icon-refresh-line"
              iconPosition="left"
            >
              Recommencer
            </Button>
            <Button
              linkProps={{
                href: 'https://plusfraisautravail.beta.gouv.fr/agir/',
                target: '_blank',
                rel: 'noopener noreferrer',
              }}
              iconId="fr-icon-external-link-line"
              iconPosition="right"
            >
              Découvrir toutes les solutions
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
