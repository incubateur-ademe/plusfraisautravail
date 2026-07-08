import { useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fr } from '@codegouvfr/react-dsfr';
import { Button } from '@codegouvfr/react-dsfr/Button';
import { ProgressHeader } from '../components/ProgressHeader';
import { QuestionCard } from '../components/QuestionCard';
import { useFormContext } from '../context/FormContext';
import { QUESTIONS, getNextQuestionId, BLOC_BY_ID } from '../data/questions';
import { CONTENU } from '../data/contenu';

export function QuestionPage() {
  const { questionId } = useParams<{ questionId: string }>();
  const navigate = useNavigate();
  const { setAnswer, answerLabels, markCompleted } = useFormContext();
  const containerRef = useRef<HTMLDivElement>(null);

  const question = QUESTIONS.find((q) => q.id === questionId);
  const bloc = question ? BLOC_BY_ID[question.blocId] : undefined;

  useEffect(() => {
    if (!question) {
      navigate('/');
      return;
    }

    const el = containerRef.current;
    if (el) {
      el.animate(
        [
          { opacity: 0, transform: 'translateX(40px)' },
          { opacity: 1, transform: 'translateX(0)' },
        ],
        { duration: 300, easing: 'ease-out', fill: 'both' }
      );
    }
  }, [question, navigate]);

  if (!question) return null;

  const selectedLabel = answerLabels[question.id];
  const hasSelection = selectedLabel !== undefined;
  const c = CONTENU.navigation;

  const dontKnowLabel = c.button_dont_know;

  function handleSelect(score: number, label: string) {
    setAnswer(question!.id, score, label);
  }

  function goToNext(labels: Record<string, string>) {
    // Prochaine question applicable selon le moteur Publicodes
    // (ordre fixe + « non applicable si », cf. model.ts).
    const nextId = getNextQuestionId(question!.id, labels);
    if (nextId === null) {
      markCompleted();
      navigate('/resultats');
    } else {
      navigate(`/${nextId}`);
    }
  }

  function handleDontKnow() {
    // Enregistre la réponse et passe directement à la question suivante.
    // setAnswer est asynchrone : on passe la réponse explicitement (le label
    // « Je ne sais pas » est ignoré par la situation Publicodes, mais il doit
    // écraser une éventuelle réponse précédente).
    setAnswer(question!.id, -1, dontKnowLabel);
    goToNext({ ...answerLabels, [question!.id]: dontKnowLabel });
  }

  function handleNext() {
    if (!selectedLabel) return;
    goToNext(answerLabels);
  }

  function handleBack() {
    // L'historique navigateur suit exactement le chemin parcouru (navigation
    // conditionnelle incluse), contrairement à l'ordre linéaire des questions.
    navigate(-1);
  }

  return (
    <div ref={containerRef} className="autodiag-question-page">
      <ProgressHeader question={question} bloc={bloc} />

      <div className={`${fr.cx('fr-container', 'fr-py-4w')} autodiag-question-body`}>
        <div className={fr.cx('fr-grid-row', 'fr-grid-row--center')}>
          <div className={fr.cx('fr-col-12', 'fr-col-md-10', 'fr-col-lg-8')}>
            <h2 className={fr.cx('fr-h3')}>{question.question}</h2>

            <QuestionCard
              questionId={question.id}
              options={question.options}
              selectedLabel={selectedLabel}
              onSelect={handleSelect}
            />

            <Button priority="tertiary" onClick={handleDontKnow}>
              {dontKnowLabel}
            </Button>
          </div>
        </div>
      </div>

      <div className="autodiag-bottom-nav">
        <div className={fr.cx('fr-container')}>
          <div className="autodiag-bottom-nav__inner">
            <Button
              priority={hasSelection ? 'primary' : 'secondary'}
              iconId="fr-icon-arrow-right-line"
              iconPosition="right"
              onClick={handleNext}
              disabled={!hasSelection}
            >
              {c.button_next}
            </Button>
            <Button
              priority="tertiary no outline"
              iconId="fr-icon-arrow-left-line"
              iconPosition="left"
              onClick={handleBack}
            >
              {c.button_back}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
