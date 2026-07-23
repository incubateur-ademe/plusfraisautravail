import type { CSSProperties } from 'react';
import { fr } from '@codegouvfr/react-dsfr';
import { useNavigate } from 'react-router-dom';
import type { Question, BlocDef } from '../data/questions';
import { QUESTIONS, QUESTION_IDS } from '../data/questions';
import { CONTENU } from '../data/contenu';

interface ProgressHeaderProps {
  question: Question;
  bloc?: BlocDef;
}

/**
 * Couleur d'accent par bloc — noms de la palette illustrative DSFR.
 * On utilise les tokens de décision (`--text-label-*`, `--background-contrast-*`)
 * fournis par le CSS DSFR, qui s'adaptent automatiquement au mode sombre.
 * @see https://www.systeme-de-design.gouv.fr/version-courante/fr/fondamentaux/couleurs-utilisation-dans-le-dsfr
 */
const BLOC_COLOR_NAMES: Record<string, string> = {
  'contexte': 'blue-france',
  'désimperméabilisation des sols': 'green-bourgeon',
  'eaux pluviales': 'blue-cumulus',
  'îlots de rafraîchissement': 'green-menthe',
  'bâtiments': 'orange-terre-battue',
};

const DEFAULT_COLOR_NAME = 'blue-france';

export function ProgressHeader({ question, bloc }: ProgressHeaderProps) {
  const navigate = useNavigate();
  const currentIndex = QUESTION_IDS.indexOf(question.id);
  const total = QUESTION_IDS.length;
  const progressPercent = total > 0 ? Math.round(((currentIndex + 1) / total) * 100) : 0;
  const c = CONTENU.navigation;

  const colorName = (bloc && BLOC_COLOR_NAMES[bloc.id]) ?? DEFAULT_COLOR_NAME;

  // Position de la question au sein de son thème (ex. « Question 2 sur 4 »)
  const blocQuestions = QUESTIONS.filter((q) => q.blocId === question.blocId);
  const indexInBloc = blocQuestions.findIndex((q) => q.id === question.id);

  return (
    <header
      className="autodiag-progress-header"
      style={
        {
          '--bloc-color': `var(--text-label-${colorName})`,
          '--bloc-bg': `var(--background-contrast-${colorName})`,
        } as CSSProperties
      }
    >
      <div
        className="autodiag-progress-header__bar"
        role="progressbar"
        aria-label={`Étape ${currentIndex + 1} sur ${total}`}
        aria-valuenow={progressPercent}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="autodiag-progress-header__bar-fill"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <div className={fr.cx('fr-container')}>
        <div className="autodiag-progress-header__top">
          <button
            className={fr.cx('fr-link', 'fr-link--sm')}
            onClick={() => navigate('/')}
          >
            {c.button_back_home}
          </button>
        </div>

        {bloc && (
          <div className="autodiag-progress-header__theme">
            <span className="autodiag-progress-header__theme-icon" aria-hidden="true">
              {bloc.icon}
            </span>
            <div className="autodiag-progress-header__theme-text">
              <p className="autodiag-progress-header__theme-label">{bloc.label}</p>
              {blocQuestions.length > 1 && indexInBloc >= 0 && (
                <p className="autodiag-progress-header__theme-count">
                  Question {indexInBloc + 1} sur {blocQuestions.length}
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
