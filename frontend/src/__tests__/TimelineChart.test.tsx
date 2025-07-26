/* global describe, it, expect */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { TimelineChart } from '../components/Charts/TimelineChart';
import { PortfolioSnapshot } from '../types/timeline';

beforeAll(() => {
  global.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as any;
});

describe('TimelineChart', () => {
  it('renders without crashing', () => {
    const mockData: PortfolioSnapshot[] = [
      {
        timestamp: new Date('2023-01-01T00:00:00Z').getTime() / 1000,
        total_value: 10000,
        positions: [],
        cash: 10000,
      },
    ];
    render(<TimelineChart snapshots={mockData} />);
  });
});
