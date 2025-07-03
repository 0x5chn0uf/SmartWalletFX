import React from 'react';
import { render, screen } from '@testing-library/react';
import PerformanceTimeline from '../../pages/PerformanceTimeline';
import { vi } from 'vitest';

vi.mock('../../hooks/useTimelineData', () => ({
  useTimelineData: () => ({ data: [], isLoading: false, error: null }),
}));

describe('PerformanceTimeline', () => {
  it('renders performance timeline', () => {
    render(<PerformanceTimeline />);
    expect(screen.getByText(/performance/i)).toBeInTheDocument();
  });
});
