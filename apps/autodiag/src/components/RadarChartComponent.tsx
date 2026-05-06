import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import type { ThemeScore } from '../data/questions';

interface RadarChartComponentProps {
  scores: ThemeScore[];
}

export function RadarChartComponent({ scores }: RadarChartComponentProps) {
  const data = scores.map((s) => ({
    theme: `${s.themeIcon} ${s.themeLabel}`,
    score: Math.round(s.score * 10) / 10,
    max: 5,
  }));

  return (
    <div className="autodiag-radar-container" aria-hidden="true">
      <ResponsiveContainer width="100%" height={380}>
        <RadarChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
          <PolarGrid />
          <PolarAngleAxis
            dataKey="theme"
            tick={{ fontSize: 13, fill: '#3a3a3a' }}
          />
          <PolarRadiusAxis
            domain={[0, 5]}
            tickCount={6}
            tick={{ fontSize: 11, fill: '#666' }}
          />
          {/* Reference pentagon at score 5 */}
          <Radar
            name="Référence"
            dataKey="max"
            stroke="#e5e5e5"
            fill="#e5e5e5"
            fillOpacity={0.4}
          />
          {/* User scores */}
          <Radar
            name="Votre score"
            dataKey="score"
            stroke="#000091"
            fill="#000091"
            fillOpacity={0.3}
          />
          <Tooltip
            formatter={(value, name) =>
              name === 'Votre score' ? [`${value}/5`, String(name)] : [null, null]
            }
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
