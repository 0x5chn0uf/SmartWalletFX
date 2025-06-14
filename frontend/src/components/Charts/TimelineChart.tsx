import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import dayjs from 'dayjs';
import { PortfolioSnapshot } from '../../types/timeline';
import { ChartDatum } from '../../utils/timelineAdapter';

interface Props {
  data: ChartDatum[];
  metric: 'collateral' | 'borrowings' | 'health_score';
}

export const TimelineChart: React.FC<Props> = ({ data, metric }) => {
  const metricColor: Record<string, string> = {
    collateral: '#82ca9d',
    borrowings: '#8884d8',
    health_score: '#ff7300',
  };

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="ts" />
        <YAxis />
        <Tooltip />
        <Line
          type="monotone"
          dataKey={metric}
          stroke={metricColor[metric]}
          name={metric.replace('_', ' ').toUpperCase()}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}; 