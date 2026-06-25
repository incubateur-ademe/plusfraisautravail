import { fr } from '@codegouvfr/react-dsfr';
import { Badge } from '@codegouvfr/react-dsfr/Badge';
import { useNavigate } from 'react-router-dom';
import type { Question, BlocDef } from '../data/questions';
import { QUESTION_IDS } from '../data/questions';
import { CONTENU } from '../data/contenu';

interface ProgressHeaderProps {
  question: Question;
  bloc?: BlocDef;
}

export function ProgressHeader({ question, bloc }: ProgressHeaderProps) {
  const navigate = useNavigate();
  const currentIndex = QUESTION_IDS.indexOf(question.id);
  const total = QUESTION_IDS.length;
  const progressPercent = total > 0 ? Math.round(((currentIndex) / total) * 100) : 0;
  const c = CONTENU.navigation;

  return (
    <div className="autodiag-progress-header">
      <div className={fr.cx('fr-container')}>
        <div className="autodiag-progress-header__top">
          <button
            className={fr.cx('fr-link', 'fr-link--sm')}
            onClick={() => navigate('/')}
          >
            {c.button_back_home}
          </button>
          {bloc && (
            <Badge small>
              <span aria-hidden="true">{bloc.icon}</span> {bloc.label}
            </Badge>
          )}
        </div>
        <div className="autodiag-progress-header__bar" role="progressbar" aria-valuenow={progressPercent} aria-valuemin={0} aria-valuemax={100}>
          <div
            className="autodiag-progress-header__bar-fill"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <p className={fr.cx('fr-text--sm', 'fr-mb-0')}>
          Étape {currentIndex + 1} sur {total}
        </p>
      </div>
    </div>
  );
}
