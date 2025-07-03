import React from 'react';
import { render, screen } from '@testing-library/react';
import LoadingSpinner from '../../components/LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders a progress indicator', () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows custom message and size', () => {
    render(<LoadingSpinner message="Fetching" size={60} />);
    expect(screen.getByText('Fetching')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders full screen overlay when fullScreen', () => {
    const { container } = render(<LoadingSpinner fullScreen />);
    expect(container.firstChild).toHaveStyle({ position: 'fixed' });
  });
});
