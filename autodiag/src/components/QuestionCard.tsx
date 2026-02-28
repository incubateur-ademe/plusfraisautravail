import { RadioButtons } from '@codegouvfr/react-dsfr/RadioButtons';
import type { Option } from '../data/questions';

interface QuestionCardProps {
  questionId: string;
  options: Option[];
  selectedScore: number | undefined;
  onSelect: (score: number) => void;
}

export function QuestionCard({ questionId, options, selectedScore, onSelect }: QuestionCardProps) {
  return (
    <RadioButtons
      name={questionId}
      legend="Sélectionnez votre situation"
      options={options.map((option) => ({
        label: option.label,
        value: String(option.score),
        nativeInputProps: {
          checked: selectedScore === option.score,
          onChange: () => onSelect(option.score),
        },
      }))}
    />
  );
}
