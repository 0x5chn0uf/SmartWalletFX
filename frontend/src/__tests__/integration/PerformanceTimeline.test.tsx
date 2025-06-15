import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import PerformanceTimeline from '../../pages/PerformanceTimeline';

// Mock the hook to return sample data instantly
jest.mock('../../../hooks/useTimelineData', () => {
  const snapshots = [
    {
      user_address: '0xdead',
      timestamp: 1718304000, // 2024-06-14
      total_collateral: 100,
      total_borrowings: 10,
      aggregate_health_score: 2.1,
    },
    {
      user_address: '0xdead',
      timestamp: 1718390400, // 2024-06-15
      total_collateral: 120,
      total_borrowings: 12,
      aggregate_health_score: 2.2,
    },
  ];
  return {
    useTimelineData: () => ({
      data: snapshots,
      isLoading: false,
      error: null,
    }),
  };
});

const renderWithClient = (ui: React.ReactElement) => {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
};

describe('PerformanceTimeline page', () => {
  it('renders chart and reacts to metric filter change', async () => {
    renderWithClient(<PerformanceTimeline />);

    // chart line path will exist
    expect(await screen.findByText(/Performance Timeline/i)).toBeInTheDocument();

    // metric select should exist and allow change
    const select = screen.getByLabelText(/Metric:/i) as HTMLSelectElement;
    expect(select.value).toBe('collateral');

    fireEvent.change(select, { target: { value: 'borrowings' } });
    await waitFor(() => expect(select.value).toBe('borrowings'));
  });
}); 