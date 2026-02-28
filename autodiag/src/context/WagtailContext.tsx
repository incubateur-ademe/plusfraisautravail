import { createContext, useContext, useRef, useState } from 'react';
import type { Question } from '../data/questions';

export interface WagtailPage {
  id: number;
  title: string;
  searchDescription: string;
  htmlUrl: string;
}

interface WagtailContextValue {
  pages: Record<string, WagtailPage>;
  prefetchSolutionPages: (questions: Question[]) => void;
}

const WagtailContext = createContext<WagtailContextValue | null>(null);

export function WagtailProvider({ children }: { children: React.ReactNode }) {
  const [pages, setPages] = useState<Record<string, WagtailPage>>({});
  const fetchedIds = useRef<Set<number>>(new Set());

  function prefetchSolutionPages(questions: Question[]) {
    // Collect unique (themeId, solutionPageId) pairs not yet fetched
    const toFetch: { themeId: string; pageId: number }[] = [];
    const seenPageIds = new Set<number>();

    for (const q of questions) {
      if (!fetchedIds.current.has(q.solutionPageId) && !seenPageIds.has(q.solutionPageId)) {
        toFetch.push({ themeId: q.themeId, pageId: q.solutionPageId });
        seenPageIds.add(q.solutionPageId);
      }
    }

    if (toFetch.length === 0) return;

    // Mark as in-flight immediately to avoid duplicate fetches
    for (const { pageId } of toFetch) {
      fetchedIds.current.add(pageId);
    }

    Promise.all(
      toFetch.map(async ({ themeId, pageId }) => {
        try {
          const res = await fetch(
            `https://plusfraisautravail.beta.gouv.fr/api/v2/pages/${pageId}/?fields=title,meta`
          );
          if (!res.ok) return null;
          const json = await res.json();
          const page: WagtailPage = {
            id: json.id,
            title: json.title,
            searchDescription: json.meta?.search_description ?? '',
            htmlUrl: json.meta?.html_url ?? '',
          };
          return { themeId, page };
        } catch {
          return null;
        }
      })
    ).then((results) => {
      const updates: Record<string, WagtailPage> = {};
      for (const result of results) {
        if (result) updates[result.themeId] = result.page;
      }
      if (Object.keys(updates).length > 0) {
        setPages((prev) => ({ ...prev, ...updates }));
      }
    });
  }

  return (
    <WagtailContext.Provider value={{ pages, prefetchSolutionPages }}>
      {children}
    </WagtailContext.Provider>
  );
}

export function useWagtail(): WagtailContextValue {
  const ctx = useContext(WagtailContext);
  if (!ctx) throw new Error('useWagtail must be used inside WagtailProvider');
  return ctx;
}
