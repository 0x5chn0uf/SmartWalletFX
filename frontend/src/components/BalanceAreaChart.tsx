import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts';

interface BalancePoint {
  date: string;
  balance: number;
}

interface BalanceAreaChartProps {
  data: BalancePoint[];
}

const CustomTooltip: React.FC<TooltipProps<number, string>> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const original = payload[0].payload.originalBalance as number;
    return (
      <div className="rounded bg-gray-800 text-white p-2 text-sm shadow">
        $
        {original.toLocaleString(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}
      </div>
    );
  }
  return null;
};

const BalanceAreaChart: React.FC<BalanceAreaChartProps> = ({ data }) => {
  if (!data || data.length === 0) return null;

  // Normalize balances so small fluctuations are visible on the chart
  const minBalance = Math.min(...data.map(d => d.balance));
  const normalizedData = data.map(d => ({
    date: d.date,
    balance: d.balance - minBalance, // relative difference
    originalBalance: d.balance,
  }));

  return (
    <div className="h-[250px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={normalizedData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="date" hide />
          <YAxis hide />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="balance"
            stroke="#6366f1"
            fillOpacity={1}
            fill="url(#colorBalance)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default BalanceAreaChart;
