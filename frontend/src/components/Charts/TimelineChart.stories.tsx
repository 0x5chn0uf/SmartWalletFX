import type { Meta, StoryObj } from '@storybook/react';
import { TimelineChart, TimelineChartProps } from './TimelineChart';
import { PortfolioSnapshot } from '../../types/timeline';

const mockData: PortfolioSnapshot[] = [
  {
    timestamp: new Date('2023-01-01T00:00:00Z').getTime() / 1000,
    total_value: 10000,
    positions: [],
    cash: 10000,
  },
  {
    timestamp: new Date('2023-01-02T00:00:00Z').getTime() / 1000,
    total_value: 10200,
    positions: [],
    cash: 10200,
  },
];

const meta: Meta<TimelineChartProps> = {
  title: 'Charts/TimelineChart',
  component: TimelineChart,
  tags: ['autodocs'],
  args: {
    snapshots: mockData,
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
