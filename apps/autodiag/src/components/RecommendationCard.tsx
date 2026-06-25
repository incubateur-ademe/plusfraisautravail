import { fr } from '@codegouvfr/react-dsfr';
import { Badge } from '@codegouvfr/react-dsfr/Badge';
import type { ThemeScore } from '../data/questions';
import { CONTENU } from '../data/contenu';

type BadgeSeverity = 'error' | 'warning' | 'info' | 'new' | 'success';

function getSeverity(score: number, maxScore: number): BadgeSeverity {
  const ratio = maxScore > 0 ? score / maxScore : 0;
  if (ratio <= 0.2) return 'error';
  if (ratio <= 0.4) return 'warning';
  if (ratio <= 0.6) return 'info';
  if (ratio <= 0.8) return 'new';
  return 'success';
}

interface RecommendationCardProps {
  score: ThemeScore;
  rank: number;
}

export function RecommendationCard({ score, rank }: RecommendationCardProps) {
  const severity = getSeverity(score.score, score.maxScore);
  const displayScore = Math.round(score.score * 10) / 10;
  const c = CONTENU.card;

  return (
    <div className={fr.cx('fr-card', 'fr-card--no-arrow')} aria-label={`Priorité ${rank} : ${score.blocLabel}`}>
      <div className={fr.cx('fr-card__body')}>
        <div className={fr.cx('fr-card__content')}>
          <div className={fr.cx('fr-grid-row', 'fr-grid-row--middle', 'fr-mb-1w')} style={{ gap: '0.75rem', flexWrap: 'wrap' }}>
            <p className={fr.cx('fr-badge', 'fr-badge--blue-cumulus')} aria-hidden="true">
              #{rank}
            </p>
            <span>
              {score.blocIcon} <strong>{score.blocLabel}</strong>
            </span>
            <Badge severity={severity} small>
              {c.severity_labels.find((l: { max_score?: number }) => l.max_score === undefined || displayScore <= l.max_score)?.label ?? ''}
            </Badge>
            <span className={fr.cx('fr-ml-auto', 'fr-text--sm', 'fr-hint-text')}>
              <span className={fr.cx('fr-sr-only')}>Score : </span>
              {displayScore}/{score.maxScore}
            </span>
          </div>

          <p className={fr.cx('fr-mb-2w')}>{score.description}</p>
        </div>
      </div>
    </div>
  );
}
