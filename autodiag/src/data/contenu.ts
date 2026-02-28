import raw from '../../../contenu.yaml'

interface SeverityLabel {
  max_score?: number;
  label: string;
}

interface Contenu {
  welcome: {
    title: string;
    lead: string;
    callout_title: string;
    callout_body: string;
    callout_duration: string;
    button_start: string;
    button_resume: string;
    button_restart: string;
    button_results: string;
  };
  results: {
    title: string;
    lead: string;
    score_global_label: string;
    score_max: number;
    section_overview: string;
    radar_sr_prefix: string;
    section_recommendations: string;
    recommendations_lead: string;
    button_restart: string;
    button_all_solutions: string;
    all_solutions_url: string;
  };
  navigation: {
    button_back: string;
    button_back_home: string;
    button_next: string;
    button_dont_know: string;
  };
  card: {
    score_suffix: string;
    button_loading: string;
    button_solutions: string;
    severity_labels: SeverityLabel[];
  };
}

export const CONTENU = raw as Contenu;

export function getSeverityLabel(score: number): string {
  for (const entry of CONTENU.card.severity_labels) {
    if (entry.max_score === undefined || score <= entry.max_score) {
      return entry.label;
    }
  }
  return '';
}
