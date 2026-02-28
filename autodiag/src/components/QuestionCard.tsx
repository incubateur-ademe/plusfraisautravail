import { fr } from '@codegouvfr/react-dsfr';
import { Badge } from '@codegouvfr/react-dsfr/Badge';
import type { Option } from '../data/questions';

interface QuestionCardProps {
  questionId: string;
  options: Option[];
  selectedScore: number | undefined;
  onSelect: (score: number) => void;
}

export function QuestionCard({ questionId, options, selectedScore, onSelect }: QuestionCardProps) {
  return (
    <div
      role="radiogroup"
      aria-label="Options de réponse"
      className="autodiag-options-group"
    >
      {options.map((option, index) => {
        const isSelected = selectedScore === option.score;
        const inputId = `${questionId}-option-${index}`;

        return (
          <div
            key={option.score}
            className={`autodiag-option-item${isSelected ? ' autodiag-option-item--selected' : ''}`}
            onClick={() => onSelect(option.score)}
          >
            <input
              type="radio"
              id={inputId}
              name={questionId}
              value={option.score}
              checked={isSelected}
              onChange={() => onSelect(option.score)}
              className={fr.cx('fr-sr-only')}
            />
            <label htmlFor={inputId}>
              <Badge
                severity={isSelected ? 'info' : undefined}
                small
                style={{ minWidth: '2rem', justifyContent: 'center' }}
              >
                {option.score}
              </Badge>
              <span className="autodiag-option-text">{option.label}</span>
            </label>
          </div>
        );
      })}
    </div>
  );
}
