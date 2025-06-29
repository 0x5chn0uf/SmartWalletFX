import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { ChartDatum } from '../../utils/timelineAdapter';

export interface TimelineChartProps {
  data: ChartDatum[];
  metric: 'collateral' | 'borrowings' | 'health_score';
}

export const TimelineChart: React.FC<TimelineChartProps> = ({ data, metric }) => {
  const colorMap = {
    collateral: '#4dabf7',
    borrowings: '#f77f00',
    health_score: '#82ca9d',
  } as const;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#444" />
        <XAxis dataKey="ts" tick={{ fill: '#ccc', fontSize: 12 }} />
        <YAxis tick={{ fill: '#ccc', fontSize: 12 }} />
        <Tooltip
          contentStyle={{ backgroundColor: '#222', border: 'none' }}
          labelStyle={{ color: '#fff' }}
          formatter={(value: any) => [value.toLocaleString(), metric.toUpperCase()]}
        />
        <Line
          type="monotone"
          dataKey={metric}
          stroke={colorMap[metric]}
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};
