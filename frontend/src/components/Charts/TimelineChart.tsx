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

interface Props {
  snapshots: PortfolioSnapshot[];
}

export const TimelineChart: React.FC<Props> = ({ snapshots }) => {
  const data = snapshots.map((s) => ({
    ts: dayjs.unix(s.timestamp).format('YYYY-MM-DD'),
    collateral: s.total_collateral,
    borrowings: s.total_borrowings,
  }));

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="ts" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="collateral" stroke="#82ca9d" name="Collateral" />
        <Line type="monotone" dataKey="borrowings" stroke="#8884d8" name="Borrowings" />
      </LineChart>
    </ResponsiveContainer>
  );
}; 