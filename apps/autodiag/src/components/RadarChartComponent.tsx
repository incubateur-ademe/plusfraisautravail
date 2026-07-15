import { fr } from '@codegouvfr/react-dsfr';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import type { ThemeScore } from '../data/questions';

interface RadarChartComponentProps {
  scores: ThemeScore[];
}

export function RadarChartComponent({ scores }: RadarChartComponentProps) {
  const chartData = scores.map((s) => ({
    theme: `${s.blocIcon} ${s.blocLabel}`,
    score: Math.round(s.score * 10) / 10,
    max: s.maxScore,
  }));

  const maxVal = Math.max(...scores.map((s) => s.maxScore), 100);

  return (
    <div className={fr.cx('fr-mb-4w')} style={{ width: '100%', height: 350 }}>
      <ResponsiveContainer>
        <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="60%">
          <PolarGrid stroke="#ddd" />
          <PolarAngleAxis dataKey="theme" tick={{ fontSize: 12 }} />
          <PolarRadiusAxis angle={30} domain={[0, maxVal]} tickCount={5} />
          <Radar name="Score" dataKey="score" stroke="#0063cb" fill="#0063cb" fillOpacity={0.2} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
