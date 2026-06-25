import { RadioButtons } from '@codegouvfr/react-dsfr/RadioButtons';
import type { Option } from '../data/questions';

interface QuestionCardProps {
  questionId: string;
  options: Option[];
  selectedLabel: string | undefined;
  onSelect: (score: number, label: string) => void;
}

export function QuestionCard({ questionId, options, selectedLabel, onSelect }: QuestionCardProps) {
  return (
    <RadioButtons
      name={questionId}
      legend="Sélectionnez votre situation"
      options={options.map((option) => ({
        label: option.label,
        value: String(option.score),
        nativeInputProps: {
          checked: selectedLabel === option.label,
          onChange: () => onSelect(option.score, option.label),
        },
      }))}
    />
  );
}
