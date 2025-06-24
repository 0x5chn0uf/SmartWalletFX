import React from 'react';
import { render, screen } from '@testing-library/react';
import PerformanceTimeline from '../../pages/PerformanceTimeline';

describe('PerformanceTimeline', () => {
  it('renders performance timeline', () => {
    render(<PerformanceTimeline />);
    expect(screen.getByText(/performance/i)).toBeInTheDocument();
  });
}); 