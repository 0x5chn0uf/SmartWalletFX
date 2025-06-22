import type { Meta, StoryObj } from '@storybook/react';
import { TimelineChart, TimelineChartProps } from './TimelineChart';
import { ChartDatum } from '../../utils/timelineAdapter';

const mockData: ChartDatum[] = [
  {
    ts: '2023-01-01',
    collateral: 10000,
    borrowings: 5000,
    health_score: 1.5,
  },
  {
    ts: '2023-01-02',
    collateral: 10200,
    borrowings: 4800,
    health_score: 1.6,
  },
];

const meta: Meta<TimelineChartProps> = {
  title: 'Charts/TimelineChart',
  component: TimelineChart,
  tags: ['autodocs'],
  args: {
    data: mockData,
    metric: 'collateral',
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Borrowings: Story = {
  args: {
    metric: 'borrowings',
  },
};

export const HealthScore: Story = {
  args: {
    metric: 'health_score',
  },
};
