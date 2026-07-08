import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { Answers } from '../data/questions';

const STORAGE_KEY = 'autodiag-answers';
const LABELS_KEY = 'autodiag-labels';
const COMPLETED_KEY = 'autodiag-completed';

interface FormContextValue {
  answers: Answers;
  /** Maps questionId -> selected option label (for navigation routing) */
  answerLabels: Record<string, string>;
  setAnswer: (id: string, score: number, label: string) => void;
  resetAnswers: () => void;
  /**
   * True once the user reached the end of their questionnaire path.
   * With conditional navigation, some questions are legitimately skipped,
   * so completion = "hit a terminal question", not "answered everything".
   */
  isComplete: boolean;
  markCompleted: () => void;
}

const FormContext = createContext<FormContextValue | null>(null);

function loadFromStorage<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (raw) return JSON.parse(raw) as T;
  } catch {
    // ignore
  }
  return fallback;
}

export function FormProvider({ children }: { children: React.ReactNode }) {
  const [answers, setAnswers] = useState<Answers>(() => loadFromStorage(STORAGE_KEY, {}));
  const [answerLabels, setAnswerLabels] = useState<Record<string, string>>(() => loadFromStorage(LABELS_KEY, {}));
  const [isComplete, setIsComplete] = useState<boolean>(() => loadFromStorage(COMPLETED_KEY, false));

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(answers));
    } catch {
      // ignore
    }
  }, [answers]);

  useEffect(() => {
    try {
      localStorage.setItem(LABELS_KEY, JSON.stringify(answerLabels));
    } catch {
      // ignore
    }
  }, [answerLabels]);

  const setAnswer = useCallback((id: string, score: number, label: string) => {
    setAnswers((prev) => ({ ...prev, [id]: score }));
    if (label) {
      setAnswerLabels((prev) => ({ ...prev, [id]: label }));
    }
  }, []);

  const markCompleted = useCallback(() => {
    setIsComplete(true);
    try {
      localStorage.setItem(COMPLETED_KEY, 'true');
    } catch {
      // ignore
    }
  }, []);

  const resetAnswers = useCallback(() => {
    setAnswers({});
    setAnswerLabels({});
    setIsComplete(false);
    try {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(LABELS_KEY);
      localStorage.removeItem(COMPLETED_KEY);
    } catch {
      // ignore
    }
  }, []);

  return (
    <FormContext.Provider value={{ answers, answerLabels, setAnswer, resetAnswers, isComplete, markCompleted }}>
      {children}
    </FormContext.Provider>
  );
}

export function useFormContext(): FormContextValue {
  const ctx = useContext(FormContext);
  if (!ctx) throw new Error('useFormContext must be used inside FormProvider');
  return ctx;
}
