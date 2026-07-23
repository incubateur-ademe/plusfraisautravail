import { useId, useRef, useState } from 'react';
import { fr } from '@codegouvfr/react-dsfr';
import './combobox.css';

export interface ComboboxOption {
  value: string;
  label: string;
}

interface CommuneComboboxProps {
  label: string;
  value: string;
  options: ComboboxOption[];
  loading?: boolean;
  onInputChange: (value: string) => void;
  onSelect: (option: ComboboxOption) => void;
}

// WAI-ARIA combobox pattern (listbox popup): one text input owns focus,
// the popup is a plain list controlled via aria-activedescendant.
// https://www.w3.org/WAI/ARIA/apg/patterns/combobox/
export const CommuneCombobox = ({
  label,
  value,
  options,
  loading,
  onInputChange,
  onSelect,
}: CommuneComboboxProps) => {
  const id = useId();
  const inputId = `${id}-input`;
  const listboxId = `${id}-listbox`;
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  const showPopup = open && (loading || options.length > 0);
  const activeOption = activeIndex >= 0 ? options[activeIndex] : undefined;

  const commit = (option: ComboboxOption) => {
    onSelect(option);
    setOpen(false);
    setActiveIndex(-1);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!options.length) return;
      setOpen(true);
      setActiveIndex((i) => (i + 1) % options.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (!options.length) return;
      setOpen(true);
      setActiveIndex((i) => (i <= 0 ? options.length - 1 : i - 1));
    } else if (e.key === 'Enter') {
      if (activeOption) {
        e.preventDefault();
        commit(activeOption);
      }
    } else if (e.key === 'Escape') {
      setOpen(false);
      setActiveIndex(-1);
    }
  };

  return (
    <div className="cd-combobox" role="search">
      <label className={fr.cx('fr-label')} htmlFor={inputId}>
        {label}
      </label>
      <div className="cd-combobox-shell">
        <input
          ref={inputRef}
          id={inputId}
          type="text"
          className={fr.cx('fr-input')}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={showPopup}
          aria-controls={listboxId}
          aria-activedescendant={activeOption ? `${id}-option-${activeOption.value}` : undefined}
          placeholder="Code postal, code INSEE, ou nom de commune"
          value={value}
          onChange={(e) => {
            onInputChange(e.target.value);
            setOpen(true);
            setActiveIndex(-1);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onKeyDown={onKeyDown}
        />
      </div>
      {showPopup && (
        <ul id={listboxId} role="listbox" className="cd-combobox-listbox">
          {loading && (
            <li className="cd-combobox-status" aria-live="polite">
              Recherche…
            </li>
          )}
          {!loading &&
            options.map((option, index) => (
              <li
                key={option.value}
                id={`${id}-option-${option.value}`}
                role="option"
                aria-selected={index === activeIndex}
                className={`cd-combobox-option${index === activeIndex ? ' cd-combobox-option--active' : ''}`}
                // onMouseDown (not onClick) fires before the input's onBlur closes the popup.
                onMouseDown={(e) => {
                  e.preventDefault();
                  commit(option);
                }}
              >
                {option.label}
              </li>
            ))}
        </ul>
      )}
    </div>
  );
};
