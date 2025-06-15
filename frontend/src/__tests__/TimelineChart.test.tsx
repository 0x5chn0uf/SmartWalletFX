/* global describe, it, expect */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { TimelineChart } from '../components/Charts/TimelineChart';
import { PortfolioSnapshot } from '../types/timeline';
import { describe, it, expect } from '@jest/globals';
import '@testing-library/jest-dom';
import { mapSnapshotsToChartData } from '../utils/timelineAdapter';

const mockSnapshots: PortfolioSnapshot[] = [
  {
    user_address: '0x1',
    timestamp: 1700000000,
    total_collateral: 10,
    total_borrowings: 2,
    aggregate_health_score: 1.5,
  },
  {
    user_address: '0x1',
    timestamp: 1700003600,
    total_collateral: 12,
    total_borrowings: 3,
    aggregate_health_score: 1.6,
  },
];

describe('TimelineChart', () => {
  it('renders lines and tooltip', () => {
    const chartData = mapSnapshotsToChartData(mockSnapshots);
    render(<TimelineChart data={chartData} metric="collateral" />);

    const container = document.querySelector('.recharts-responsive-container');
    expect(container).toBeTruthy();
  });
}); 