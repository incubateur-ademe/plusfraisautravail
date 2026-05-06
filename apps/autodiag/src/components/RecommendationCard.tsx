import { fr } from '@codegouvfr/react-dsfr';
import { Badge } from '@codegouvfr/react-dsfr/Badge';
import { Button } from '@codegouvfr/react-dsfr/Button';
import type { ThemeScore } from '../data/questions';
import { useWagtail } from '../context/WagtailContext';
import { CONTENU, getSeverityLabel } from '../data/contenu';

type BadgeSeverity = 'error' | 'warning' | 'info' | 'new' | 'success';

function getSeverity(score: number): BadgeSeverity {
  if (score <= 1) return 'error';
  if (score <= 2) return 'warning';
  if (score <= 3) return 'info';
  if (score <= 4) return 'new';
  return 'success';
}

interface RecommendationCardProps {
  score: ThemeScore;
  rank: number;
}

export function RecommendationCard({ score, rank }: RecommendationCardProps) {
  const { pages, loading } = useWagtail();
  const severity = getSeverity(score.score);
  const displayScore = Math.round(score.score * 10) / 10;
  const page = pages[score.themeId];
  const c = CONTENU.card;

  const title = page?.title || null;
  const description = page?.searchDescription || score.description;
  const solutionUrl = page?.htmlUrl || null;

  return (
    <div className={fr.cx('fr-card', 'fr-card--no-arrow')} aria-label={`Priorité ${rank} : ${score.themeLabel}`}>
      <div className={fr.cx('fr-card__body')}>
        <div className={fr.cx('fr-card__content')}>
          <div className={fr.cx('fr-grid-row', 'fr-grid-row--middle', 'fr-mb-1w')} style={{ gap: '0.75rem', flexWrap: 'wrap' }}>
            <p className={fr.cx('fr-badge', 'fr-badge--blue-cumulus')} aria-hidden="true">
              #{rank}
            </p>
            <span>
              {score.themeIcon} <strong>{score.themeLabel}</strong>
            </span>
            <Badge severity={severity} small>
              {getSeverityLabel(score.score)}
            </Badge>
            <span className={fr.cx('fr-ml-auto', 'fr-text--sm', 'fr-hint-text')}>
              <span className={fr.cx('fr-sr-only')}>Score : </span>
              {displayScore}{c.score_suffix}
            </span>
          </div>

          {title && <p className={fr.cx('fr-text--bold', 'fr-mb-1v')}>{title}</p>}
          <p className={fr.cx('fr-mb-2w')}>{description}</p>

          {loading && !solutionUrl ? (
            <Button size="small" priority="secondary" disabled>
              {c.button_loading}
            </Button>
          ) : solutionUrl ? (
            <Button
              linkProps={{ href: solutionUrl, target: '_blank', rel: 'noopener noreferrer' }}
              size="small"
              priority="secondary"
              iconId="fr-icon-external-link-line"
              iconPosition="right"
            >
              {c.button_solutions}
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
