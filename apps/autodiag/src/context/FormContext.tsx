import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { Answers } from '../data/questions';
import { QUESTION_IDS } from '../data/questions';

const STORAGE_KEY = 'autodiag-answers';

interface FormContextValue {
  answers: Answers;
  setAnswer: (id: string, value: number) => void;
  resetAnswers: () => void;
  isComplete: boolean;
}

const FormContext = createContext<FormContextValue | null>(null);

function loadFromStorage(): Answers {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as Answers;
  } catch {
    // ignore
  }
  return {};
}

export function FormProvider({ children }: { children: React.ReactNode }) {
  const [answers, setAnswers] = useState<Answers>(loadFromStorage);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(answers));
    } catch {
      // ignore
    }
  }, [answers]);

  const setAnswer = useCallback((id: string, value: number) => {
    setAnswers((prev) => ({ ...prev, [id]: value }));
  }, []);

  const resetAnswers = useCallback(() => {
    setAnswers({});
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  }, []);

  const isComplete = QUESTION_IDS.every((id) => answers[id] !== undefined);

  return (
    <FormContext.Provider value={{ answers, setAnswer, resetAnswers, isComplete }}>
      {children}
    </FormContext.Provider>
  );
}

export function useFormContext(): FormContextValue {
  const ctx = useContext(FormContext);
  if (!ctx) throw new Error('useFormContext must be used inside FormProvider');
  return ctx;
}
