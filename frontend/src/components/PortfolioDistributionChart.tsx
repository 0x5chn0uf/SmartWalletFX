import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface Wallet {
  id: string;
  name: string;
  balance: number;
}

interface PortfolioDistributionChartProps {
  data: Wallet[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

const PortfolioDistributionChart: React.FC<PortfolioDistributionChartProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          outerRadius={80}
          fill="#8884d8"
          dataKey="balance"
          nameKey="name"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${entry.id}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number) =>
            `$${value.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}`
          }
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default PortfolioDistributionChart;
