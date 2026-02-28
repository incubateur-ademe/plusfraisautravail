import { Badge } from '@codegouvfr/react-dsfr/Badge';
import { Button } from '@codegouvfr/react-dsfr/Button';
import type { ThemeScore } from '../data/questions';
import { useWagtail } from '../context/WagtailContext';

type BadgeSeverity = 'error' | 'warning' | 'info' | 'new' | 'success';

function getSeverity(score: number): BadgeSeverity {
  if (score <= 1) return 'error';
  if (score <= 2) return 'warning';
  if (score <= 3) return 'info';
  if (score <= 4) return 'new';
  return 'success';
}

function getSeverityLabel(score: number): string {
  if (score <= 1) return 'Urgent';
  if (score <= 2) return 'À améliorer';
  if (score <= 3) return 'Moyen';
  if (score <= 4) return 'Bon';
  return 'Excellent';
}

interface RecommendationCardProps {
  score: ThemeScore;
  rank: number;
}

export function RecommendationCard({ score, rank }: RecommendationCardProps) {
  const { pages } = useWagtail();
  const severity = getSeverity(score.score);
  const displayScore = Math.round(score.score * 10) / 10;
  const page = pages[score.themeId];

  const title = page ? page.title : null;
  const description = page?.searchDescription || score.description;
  const solutionUrl = page?.htmlUrl
    ? `https://plusfraisautravail.beta.gouv.fr${page.htmlUrl}`
    : null;

  return (
    <div className={`autodiag-reco-card autodiag-reco-card--${severity}`}>
      <div className="autodiag-reco-rank">#{rank}</div>
      <div className="autodiag-reco-content">
        <div className="autodiag-reco-header">
          <span className="autodiag-reco-theme">
            {score.themeIcon} {score.themeLabel}
          </span>
          <Badge severity={severity} small>
            {getSeverityLabel(score.score)}
          </Badge>
          <span className="autodiag-reco-score">{displayScore}/5</span>
        </div>
        {title && <p className="fr-text--bold" style={{ marginBottom: '0.25rem' }}>{title}</p>}
        <p className="autodiag-reco-description">{description}</p>
        {solutionUrl && (
          <Button
            linkProps={{
              href: solutionUrl,
              target: '_blank',
              rel: 'noopener noreferrer',
            }}
            size="small"
            priority="secondary"
            iconId="fr-icon-external-link-line"
            iconPosition="right"
          >
            Voir les solutions
          </Button>
        )}
      </div>
    </div>
  );
}
